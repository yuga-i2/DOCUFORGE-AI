"""
DocuForge AI — Routing Logic

Centralized routing decisions for the LangGraph pipeline. All conditional
routing logic lives in this file only — no routing decisions should be
scattered inside individual agent files or API routes.
"""

import logging
from pathlib import Path

import yaml

from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def route_from_supervisor(state: DocuForgeState) -> str:
    """
    Determine the next agent to invoke based on current task state.
    Returns the name of the next LangGraph node to execute. Follows a
    strict priority order to ensure all requisite steps are completed.
    """
    # Check for errors first
    error_log = state.get("error_log", [])
    routing_decision = state.get("routing_decision", "")
    if error_log and routing_decision == "error":
        logger.debug("Routing to error handler due to errors in pipeline")
        return "error_handler"

    # Ingestion must happen first
    ingested_text = state.get("ingested_text", "")
    if not ingested_text:
        logger.debug("Routing to ingestion agent (no ingested text)")
        return "ingestion_agent"

    # RAG must happen before analysis
    retrieved_chunks = state.get("retrieved_chunks", [])
    if not retrieved_chunks:
        logger.debug("Routing to RAG agent (no retrieved chunks)")
        return "rag_agent"

    # Check if supervisor recommended research
    if routing_decision == "needs_research":
        logger.debug("Routing to research agent (supervisor decision)")
        return "research_agent"

    # Analysis must happen before writing
    analysis_result = state.get("analysis_result")
    if analysis_result is None:
        logger.debug("Routing to analyst agent (no analysis result)")
        return "analyst_agent"

    # Writing must happen before verification
    draft_report = state.get("draft_report", "")
    if not draft_report:
        logger.debug("Routing to writer agent (no draft report)")
        return "writer_agent"

    # Verification is the last step
    verified_report = state.get("verified_report", "")
    if not verified_report:
        logger.debug("Routing to verifier agent (no verified report)")
        return "verifier_agent"

    # All steps complete
    logger.debug("Routing to done (all pipeline steps completed)")
    return "done"


def should_reflect(state: DocuForgeState) -> str:
    """
    Determine if the Verifier Agent's output should trigger a reflection loop
    (Writer Agent regeneration) or if the pipeline is complete. Uses max reflection
    loop count from config to prevent infinite reflection loops.
    """
    config = _load_config()
    verifier_config = config.get("verifier", {})
    max_loops = verifier_config.get("max_reflection_loops", 3)

    reflection_count = state.get("reflection_count", 0)

    if reflection_count >= max_loops:
        logger.warning("Max reflection loops (%d) reached, proceeding to done", max_loops)
        return "done"

    # In this phase, we don't have regenerate flag logic yet (verifier is stub)
    # So we always proceed to done. Will be implemented when verifier agent is built.
    logger.debug("Reflection check: proceeding to done")
    return "done"
