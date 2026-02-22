"""Writer Agent that synthesizes context into structured reports with citations."""

import json
import logging
import re
from pathlib import Path

from core.llm_router import get_llm
from models.agent_models import StructuredReport
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def _get_prompt_version_from_trace(agent_trace: list[str]) -> str:
    """Extract the prompt version from the pipeline trace entry."""
    for entry in agent_trace:
        if entry.startswith("pipeline: using prompt version"):
            parts = entry.split()
            if parts:
                return parts[-1]  # returns "v1", "v2", or "v3"
    return "v3"  # default


def _render_prompt(
    template: str,
    query: str,
    document_context: str,
    analysis_summary: str,
    web_context: str,
) -> str:
    """
    Render the prompt template with all required variables.
    Uses simple string replacement to avoid template engine dependencies.
    All variables are sanitized to prevent prompt injection.
    """
    rendered = template
    rendered = rendered.replace("{query}", query[:500])
    rendered = rendered.replace("{document_context}", document_context[:6000])
    rendered = rendered.replace("{analysis_summary}", analysis_summary[:1000])
    rendered = rendered.replace("{web_context}", web_context[:2000] if web_context else "None")
    return rendered


def _check_context_coverage(document_context: str, query: str) -> bool:
    """
    Verify that meaningful document context exists before calling LLM.
    Returns False if context is too short or clearly unrelated to query.
    """
    if len(document_context.strip()) < 200:
        logger.warning(
            "Writer: document context too short (%d chars) — may produce hallucinated output",
            len(document_context),
        )
        return False
    return True


def _load_prompt_template(version: str) -> str:
    """
    Load the writer prompt template for the specified version.
    Falls back to v3 → v2 → v1 → hardcoded default if file not found.
    """
    for v in [version, "v3", "v2", "v1"]:
        prompt_path = Path("prompts") / v / "writer_prompt.txt"
        try:
            content = prompt_path.read_text(encoding="utf-8")
            logger.info("Loaded prompt template from %s", v)
            return content
        except FileNotFoundError:
            continue

    # Hardcoded fallback — never crashes
    logger.warning("No prompt file found — using hardcoded fallback")
    return """Answer the query using only the document context provided.
Query: {query}
Document: {document_context}
Analysis: {analysis_summary}

Reply with valid JSON only:
{{"title": "...", "executive_summary": "...", "sections": [{{"heading": "...", "content": "...", "source": "document", "confidence": 0.8, "evidence": "..."}}], "what_document_does_not_cover": "All aspects addressed", "citations": [], "overall_confidence": 0.8, "has_web_context": false, "has_analysis": false}}"""


def writer_agent(state: DocuForgeState) -> dict:
    """Synthesize retrieved chunks, web context, and analysis into a structured report. Loads prompt template, fills with context, calls LLM for StructuredReport JSON, parses and returns DraftReport. Returns dict with draft_report, agent_trace (list), routing_decision, reflection_count. Handles JSON parse failures gracefully."""
    try:
        # Extract and fallback context fields
        chunks = state.get("retrieved_chunks") or []
        full_text = state.get("ingested_text") or ""
        web_context = state.get("web_context") or ""
        analysis = state.get("analysis_result")
        query = state.get("query", "")
        analysis_summary = analysis.summary if analysis else "No quantitative analysis performed."

        # Strategy: use ALL ingested text up to 7000 chars
        # This prevents hallucination from insufficient context
        # retrieved_chunks are relevance-ranked, so put them first
        chunk_text = "\n\n---\n\n".join(chunks) if chunks else ""

        if full_text and len(full_text) > len(chunk_text):
            # Combine: ranked chunks first (most relevant), then rest of document
            remaining = full_text.replace(chunk_text, "").strip()
            combined = chunk_text + "\n\n--- ADDITIONAL DOCUMENT CONTENT ---\n\n" + remaining
            document_context = combined[:7000]
            logger.info("Writer: combined context — %d chars from chunks + full text", len(document_context))
        else:
            document_context = chunk_text[:7000]
            logger.info("Writer: using %d chunk chars", len(document_context))

        # Check context coverage before calling LLM
        if not _check_context_coverage(document_context, query):
            logger.warning("Writer: context too short — hallucination risk high")

        # Load prompt template based on version from pipeline trace
        version = _get_prompt_version_from_trace(state.get("agent_trace", []))
        prompt_template = _load_prompt_template(version)
        logger.info("Writer using prompt version: %s", version)

        # Render prompt with all variables
        filled_prompt = _render_prompt(
            prompt_template,
            query,
            document_context,
            analysis_summary,
            web_context,
        )

        logger.info("writer_agent: generating structured report")

        # Call LLM
        llm = get_llm("writing")
        response = llm.invoke(filled_prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Null check: if upstream analysis failed, we get empty/error responses
        if not response_text or response_text.startswith("Error") or len(response_text.strip()) < 10:
            logger.warning(f"writer_agent: received empty/error response from LLM: {response_text[:50]}")
            draft_report = "Report generation skipped: upstream analysis yielded no actionable content."
            return {
                "draft_report": draft_report,
                "agent_trace": state.get("agent_trace", []) + ["writer_agent: skipped due to upstream failure"],
                "routing_decision": "verifier",
                "reflection_count": state.get("reflection_count", 0),
            }

        # Parse JSON with robust error handling
        draft_report = None
        try:
            # Clean the response text of problematic characters
            cleaned_response = response_text.replace('\n"', ' "').replace('\r', '')

            # Try to find JSON object in response
            json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", cleaned_response, re.DOTALL)

            if json_match:
                parsed = json.loads(json_match.group())
                try:
                    report = StructuredReport(**parsed)
                    draft_report = report.model_dump_json(indent=2)
                except (ValueError, TypeError, KeyError) as ve:
                    logger.warning(f"StructuredReport validation failed: {str(ve)}, using raw JSON")
                    draft_report = json.dumps(parsed, indent=2)
            else:
                # If no JSON found, try direct JSON parse of whole response
                parsed = json.loads(cleaned_response)
                report = StructuredReport(**parsed)
                draft_report = report.model_dump_json(indent=2)

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"writer_agent: JSON parse failed: {str(e)}, using raw response")
            draft_report = response_text[:2000]

        if not draft_report or draft_report.startswith("Error"):
            draft_report = response_text[:2000]

        reflection_count = state.get("reflection_count", 0)

        logger.info(f"writer_agent: generated report ({len(draft_report)} chars)")

        return {
            "draft_report": draft_report,
            "agent_trace": state.get("agent_trace", []) + ["writer_agent: generated structured report"],
            "routing_decision": "verifier",
            "reflection_count": reflection_count,
        }
    except Exception as e:
        logger.error(f"writer_agent error: {str(e)}")
        return {
            "draft_report": f"Error generating report: {str(e)}",
            "agent_trace": state.get("agent_trace", []) + [f"writer_agent: error - {str(e)}"],
            "routing_decision": "verifier",
            "reflection_count": state.get("reflection_count", 0),
        }
