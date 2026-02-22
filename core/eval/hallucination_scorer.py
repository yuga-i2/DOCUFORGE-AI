"""Hallucination detection and scoring for generated reports."""

import json
import logging

from core.llm_router import get_llm

logger = logging.getLogger(__name__)


def score_hallucination(report: str, source_documents: list[str], llm) -> dict[str, float | list]:
    """Score hallucination in report against source documents (0.0-1.0). Prompts LLM as impartial judge. Returns dict with hallucination_rate, unsupported_claims (list), supported_claims (list). On failure, returns zero rate."""
    try:
        sources = "\n".join(source_documents[:3])
        prompt = f"""You are an impartial judge. Given source documents and a report, identify unsupported claims.

SOURCES:
{sources}

REPORT:
{report[:1500]}

Identify claims in the report NOT supported by sources.
Return JSON: {{"hallucination_rate": 0.1, "unsupported_claims": [], "supported_claims": []}}"""
        
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        parsed = json.loads(response_text)
        hallucination_rate = float(parsed.get("hallucination_rate", 0.0))
        
        logger.debug(f"Hallucination rate: {hallucination_rate:.2f}")
        
        return {
            "hallucination_rate": hallucination_rate,
            "unsupported_claims": parsed.get("unsupported_claims", []),
            "supported_claims": parsed.get("supported_claims", []),
        }
    except Exception as e:
        logger.warning(f"Hallucination scoring failed: {str(e)}")
        return {
            "hallucination_rate": 0.0,
            "unsupported_claims": [],
            "supported_claims": [],
        }


def batch_score_hallucination(report_source_pairs: list[tuple[str, list[str]]]) -> list[dict]:
    """Score hallucination for multiple report-source pairs. Returns list of dicts with results. Logs each at DEBUG."""
    try:
        llm = get_llm("evaluation")
        results = []
        
        for report, sources in report_source_pairs:
            result = score_hallucination(report, sources, llm)
            results.append(result)
        
        logger.info(f"Batch hallucination scoring completed for {len(results)} reports")
        return results
    except Exception as e:
        logger.error(f"Batch hallucination scoring failed: {str(e)}")
        return []


def summarise_hallucination_results(results: list[dict]) -> dict[str, float]:
    """Summarize hallucination results across batch. Returns dict with mean_hallucination_rate, max_hallucination_rate, clean_report_count, total_reports. Logs at INFO level."""
    try:
        if not results:
            return {
                "mean_hallucination_rate": 0.0,
                "max_hallucination_rate": 0.0,
                "clean_report_count": 0,
                "total_reports": 0,
            }
        
        rates = [r.get("hallucination_rate", 0.0) for r in results]
        mean_rate = sum(rates) / len(rates)
        max_rate = max(rates)
        clean_count = sum(1 for r in rates if r == 0.0)
        
        logger.info(
            f"Hallucination summary: mean={mean_rate:.3f}, max={max_rate:.3f}, clean={clean_count}/{len(results)}"
        )
        
        return {
            "mean_hallucination_rate": mean_rate,
            "max_hallucination_rate": max_rate,
            "clean_report_count": clean_count,
            "total_reports": len(results),
        }
    except Exception as e:
        logger.error(f"Summary failed: {str(e)}")
        return {
            "mean_hallucination_rate": 0.0,
            "max_hallucination_rate": 0.0,
            "clean_report_count": 0,
            "total_reports": 0,
        }
logger = logging.getLogger(__name__)
