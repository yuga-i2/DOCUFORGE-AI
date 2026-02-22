"""Analyst Agent that computes statistics and executes code for data analysis."""

import json
import logging
import re

from core.llm_router import get_llm, is_quota_error
from models.agent_models import AnalysisResult
from orchestration.state import DocuForgeState
from tools.code_executor_tool import execute_python_code

logger = logging.getLogger(__name__)


def _safe_parse_json(raw: str) -> dict:
    """
    Parse JSON from LLM response, handling all common Groq formatting issues.
    Strips markdown fences, finds JSON boundaries, returns parsed dict.
    Raises ValueError if no valid JSON found after all cleanup attempts.
    """
    text = raw.strip()

    # Strip markdown code fences
    text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Try parsing cleaned text directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Find outermost JSON array
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in LLM response: {raw[:200]}")


def analyst_agent(state: DocuForgeState) -> dict:
    """
    Analyze retrieved chunks. For text-only documents with no numerical data,
    returns a lightweight text summary WITHOUT calling the LLM (saves quota).
    For documents with numerical data, calls LLM once (no retries).
    On quota error, fails fast and returns a graceful fallback.
    """
    try:
        retrieved_chunks = state.get("retrieved_chunks", [])
        query = state.get("query", "")

        if not retrieved_chunks:
            logger.warning("analyst_agent: no retrieved chunks available")
            analysis_result = AnalysisResult(
                summary="No data available for analysis.",
                key_metrics={},
                chart_path=None,
                anomalies=[],
            )
            return {
                "analysis_result": analysis_result,
                "agent_trace": state.get("agent_trace", []) + ["analyst_agent: no retrieved chunks"],
                "routing_decision": "writer",
            }

        context = "\n".join(retrieved_chunks)

        # ── Fast path: text-only document, no LLM call needed ────────────────
        # Count distinct numeric patterns (not just any digit)
        numeric_patterns = re.findall(r"\b\d+(?:\.\d+)?(?:%|kg|km|ms|mb|gb|usd|inr)?\b", context.lower())
        has_meaningful_numbers = len(numeric_patterns) >= 5  # threshold: at least 5 numbers

        if not has_meaningful_numbers:
            logger.info("analyst_agent: text-only document — skipping LLM call, generating summary from chunks")
            # Build a summary directly from the chunks without any LLM call
            first_chunk = retrieved_chunks[0] if retrieved_chunks else ""
            summary = (
                f"Document analysis complete. The document contains {len(retrieved_chunks)} "
                f"relevant sections addressing the query '{query}'. "
                f"Content overview: {first_chunk[:300]}..."
            )
            analysis_result = AnalysisResult(
                summary=summary,
                key_metrics={},
                chart_path=None,
                anomalies=[],
            )
            return {
                "analysis_result": analysis_result,
                "agent_trace": state.get("agent_trace", []) + ["analyst_agent: text-only doc, LLM skipped"],
                "routing_decision": "writer",
            }

        # ── LLM path: document has numerical data ────────────────────────────
        prompt = f"""You are a data analyst. Given the following document context, identify numerical data and write Python code to analyze it.

DOCUMENT CONTEXT:
{context[:2000]}

Instructions:
1. Identify tables, numbers, or measurements in the context
2. Write Python code that computes statistics and relevant metrics
3. Return ONLY a valid JSON object with these exact keys:
   - "code": Python code string to execute
   - "summary": Brief analysis summary (1-2 sentences)
   - "metrics": Dict of metric_name -> float value

No other text. Valid JSON only."""

        llm = get_llm("analysis")

        try:
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, "content") else str(response)
        except Exception as llm_err:
            if is_quota_error(llm_err):
                logger.error("analyst_agent: Gemini quota exhausted — using fallback summary (no more retries)")
                analysis_result = AnalysisResult(
                    summary=f"Quantitative analysis skipped (API quota reached). Document has {len(retrieved_chunks)} relevant sections.",
                    key_metrics={},
                    chart_path=None,
                    anomalies=[],
                )
                return {
                    "analysis_result": analysis_result,
                    "agent_trace": state.get("agent_trace", []) + ["analyst_agent: quota exhausted, fallback used"],
                    "routing_decision": "writer",
                }
            raise  # re-raise non-quota errors

        # Parse LLM response using safe JSON parser
        try:
            parsed = _safe_parse_json(response_text)
            code = parsed.get("code", "")
            summary = parsed.get("summary", "Analysis complete.")
            metrics = parsed.get("metrics", {})
        except (ValueError, json.JSONDecodeError) as parse_err:
            logger.warning("analyst_agent: JSON parse failed — extracting summary from raw response")
            # Use raw LLM response as summary — better than nothing
            raw_text = response_text[:800] if response_text else str(parse_err)
            analysis_result = AnalysisResult(
                summary=f"Document analysis: {raw_text}",
                key_metrics={},
                chart_path=None,
                anomalies=[]
            )
            return {
                "analysis_result": analysis_result,
                "agent_trace": state.get("agent_trace", []) + ["analyst_agent: used raw LLM summary (JSON parse fallback)"],
                "routing_decision": "writer"
            }

        # Execute code if available
        success = False
        if code and code.strip():
            exec_result = execute_python_code(code)
            success = exec_result.get("success") == "true"
            if success and exec_result.get("stdout"):
                summary += f"\n[Execution output: {exec_result['stdout'][:500]}]"

        analysis_result = AnalysisResult(
            summary=summary,
            key_metrics=metrics,
            chart_path=None,
            anomalies=[],
        )

        logger.info(f"analyst_agent: computed {len(metrics)} metrics, code execution success={success}")

        return {
            "analysis_result": analysis_result,
            "agent_trace": state.get("agent_trace", []) + [
                f"analyst_agent: computed {len(metrics)} metrics"
            ],
            "routing_decision": "writer",
        }

    except Exception as e:
        logger.error(f"analyst_agent error: {str(e)}")
        analysis_result = AnalysisResult(
            summary=f"Analysis error: {str(e)}",
            key_metrics={},
            chart_path=None,
            anomalies=[],
        )
        return {
            "analysis_result": analysis_result,
            "agent_trace": state.get("agent_trace", []) + [f"analyst_agent: error - {str(e)}"],
            "routing_decision": "writer",
        }
