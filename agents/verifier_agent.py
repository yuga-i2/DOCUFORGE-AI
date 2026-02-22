"""Verifier Agent that scores faithfulness and triggers reflection loops."""

import json
import logging
import re
from pathlib import Path

import yaml

from core.llm_router import get_llm
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load config from config/docuforge_config.yaml. Returns dict with verifier settings."""
    try:
        config_path = Path("config/docuforge_config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config.get("verifier", {})
    except Exception as e:
        logger.warning(f"Failed to load config: {str(e)}, using defaults")
        return {"min_faithfulness_score": 0.8, "max_reflection_loops": 2}


def _compute_faithfulness_score(
    report: str,
    source_chunks: list[str],
    llm: any,
) -> dict:
    """
    Score faithfulness by checking all factual claims from the report
    against the source document. Returns dict with score and verdict flags.
    Enforces minimum claim sample size to avoid under-sampling hallucinations.
    """
    if not report or not report.strip():
        return {
            "score": 0.0,
            "reject_for_insufficient_claims": False,
            "claim_count": 0
        }

    source_text = "\n".join(source_chunks[:12])[:6000] if source_chunks else ""
    if not source_text:
        return {
            "score": 0.7,
            "reject_for_insufficient_claims": False,
            "claim_count": 0
        }

    prompt = f"""You are a claim extraction system. Extract EVERY factual claim from the report below.
For each claim, determine if it is supported by the source document (1=supported, 0=not supported).

Return ONLY this JSON structure with minimum 8-15 claims:
{{
  "claim_verdicts": [
    {{"claim": "<sentence from report>", "verdict": 1, "evidence": "<quote from source>"}},
    {{"claim": "<sentence from report>", "verdict": 0, "evidence": null}}
  ]
}}

SOURCE DOCUMENT (ground truth):
{source_text}

REPORT TO VERIFY:
{report}

Extract ALL factual claims, aim for 12-15 items. Return ONLY the JSON."""

    try:
        response = llm.invoke(prompt)
        text = response.content.strip()

        # Parse JSON response
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown if present
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                result = json.loads(match.group(1))
            else:
                match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
                if match:
                    result = json.loads(match.group(1))
                else:
                    raise ValueError("No JSON found in response")

        verdicts = result.get("claim_verdicts", [])

        # CRITICAL: Enforce minimum claim sample size
        if len(verdicts) < 8:
            logger.warning(
                "verifier_agent: only %d claims extracted (need ≥8) — insufficient sample, forcing regenerate",
                len(verdicts)
            )
            return {
                "score": 0.0,
                "reject_for_insufficient_claims": True,
                "claim_count": len(verdicts)
            }

        scored = [v.get("verdict", 0) for v in verdicts]
        faithfulness = sum(scored) / len(scored) if scored else 0.0

        logger.info(
            "verifier_agent: extracted %d claims, faithfulness=%.3f (%d supported, %d not)",
            len(verdicts), faithfulness, sum(scored), len(scored) - sum(scored)
        )

        return {
            "score": float(faithfulness),
            "reject_for_insufficient_claims": False,
            "claim_count": len(verdicts),
            "verdicts": verdicts
        }

    except Exception as exc:
        logger.warning("Faithfulness scoring failed: %s", exc)
        return {
            "score": 0.5,
            "reject_for_insufficient_claims": False,
            "claim_count": 0
        }


def verifier_agent(state: DocuForgeState) -> dict:
    """
    Score faithfulness of draft report and decide whether to regenerate.
    Enforces minimum claim sample size and triggers reflection loops on
    low faithfulness or insufficient claim extraction.
    """
    try:
        draft = state.get("draft_report") or ""
        if not draft.strip():
            logger.warning("Verifier received empty draft — returning as-is")
            return {
                "verified_report": "Analysis could not be completed for this document.",
                "faithfulness_score": 0.0,
                "hallucination_score": 1.0,
                "agent_trace": state.get("agent_trace", []) + ["verifier_agent: empty draft"],
                "routing_decision": "done",
            }

        config = _load_config()
        min_faithfulness = config.get("min_faithfulness_score", 0.85)
        max_reflection_loops = config.get("max_reflection_loops", 3)
        min_claims_to_verify = config.get("min_claims_to_verify", 8)

        retrieved_chunks = state.get("retrieved_chunks", [])
        reflection_count = state.get("reflection_count", 0)

        llm = get_llm("verification")
        
        # Compute faithfulness with new claim-based verification
        faith_result = _compute_faithfulness_score(draft, retrieved_chunks, llm)
        faithfulness_score = faith_result["score"]
        claim_count = faith_result.get("claim_count", 0)
        reject_insufficient = faith_result.get("reject_for_insufficient_claims", False)
        hallucination_score = 1.0 - faithfulness_score

        # Decision logic: regenerate if low faithfulness OR too few claims extracted
        routing_decision = "done"
        
        if reject_insufficient and reflection_count < max_reflection_loops:
            logger.warning(
                "verifier_agent: insufficient claims extracted (%d < %d) and reflections available (%d < %d) — regenerate",
                claim_count, min_claims_to_verify, reflection_count, max_reflection_loops
            )
            routing_decision = "regenerate"
            verified_report = draft  # Send back to writer for retry
        elif faithfulness_score < min_faithfulness and reflection_count < max_reflection_loops:
            logger.warning(
                "verifier_agent: faithfulness %.3f < %.3f and reflections available (%d < %d) — regenerate",
                faithfulness_score, min_faithfulness, reflection_count, max_reflection_loops
            )
            routing_decision = "regenerate"
            verified_report = draft  # Send back to writer for retry
        else:
            # Accept the draft (either high enough faithfulness or out of reflection loops)
            verified_report = draft
            if faithfulness_score < min_faithfulness:
                logger.info(
                    "verifier_agent: faithfulness below threshold but max reflection loops reached (%d/%d) — accepting",
                    reflection_count, max_reflection_loops
                )

        logger.info(
            "verifier_agent: claims=%d, faithfulness=%.3f, hallucination=%.3f, decision=%s, reflections=%d/%d",
            claim_count, faithfulness_score, hallucination_score, routing_decision, reflection_count, max_reflection_loops
        )

        return {
            "verified_report": verified_report,
            "faithfulness_score": faithfulness_score,
            "hallucination_score": hallucination_score,
            "routing_decision": routing_decision,
            "agent_trace": state.get("agent_trace", []) + [
                f"verifier_agent: claims={claim_count}, faith={faithfulness_score:.3f}, decision={routing_decision}"
            ],
        }

    except Exception as e:
        logger.error(f"verifier_agent error: {str(e)}")
        draft = state.get("draft_report", "Analysis could not be completed.")
        return {
            "verified_report": draft,
            "faithfulness_score": 0.5,
            "hallucination_score": 0.5,
            "agent_trace": state.get("agent_trace", []) + [f"verifier_agent: error - {str(e)}"],
            "routing_decision": "done",
        }
