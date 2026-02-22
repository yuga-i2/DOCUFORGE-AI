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
    Determine the next agent based on current pipeline state.
    Checks each stage in order and routes to the first incomplete stage.
    Returns the node name string for LangGraph conditional edge routing.
    
    CRITICAL: Error state checked FIRST. If any agent returned an error,
    stop immediately instead of retrying agents.
    """
    session_id = state.get("session_id", "unknown")
    logger.debug(f"[ROUTER] Routing decision for session {session_id}")
    logger.debug(f"[ROUTER] Current state keys: {list(state.keys())}")
    
    # Error state — STOP PIPELINE IMMEDIATELY (check before all other conditions)
    if state.get("routing_decision") == "error":
        error_log = state.get("error_log", [])
        logger.error("[ROUTER] [ERROR STATE DETECTED]")
        logger.error(f"[ROUTER] Error: {error_log[-1] if error_log else 'unknown'}")
        logger.error(f"Router: Routing to error_handler. Error log: {error_log}")
        return "error_handler"

    # Stage 1: ingestion not done
    ingested_text = state.get("ingested_text", "")
    if not ingested_text:
        logger.info("[ROUTER] >> Stage 1: INGESTION needed (no ingested_text)")
        logger.info(f"Router: Routing to ingestion_agent (session {session_id})")
        return "ingestion_agent"

    logger.debug(f"[ROUTER] [DONE] Stage 1: Ingestion ({len(ingested_text)} chars)")

    # Stage 2: RAG not done — route if chunks don't exist or are empty
    # This ensures RAG runs even if it returns [] (empty list) initially
    retrieved_chunks = state.get("retrieved_chunks")
    if retrieved_chunks is None or retrieved_chunks == []:
        logger.info("[ROUTER] >> Stage 2: RAG needed (retrieved_chunks is None or empty)")
        logger.info(f"Router: Routing to rag_agent (session {session_id})")
        return "rag_agent"
    
    logger.debug(f"[ROUTER] [DONE] Stage 2: RAG ({len(retrieved_chunks) if isinstance(retrieved_chunks, list) else 'unknown'} chunks)")

    # Stage 3: external research needed
    if state.get("routing_decision") == "needs_research":
        logger.info("[ROUTER] >> Stage 3: RESEARCH needed (supervisor decision)")
        logger.info(f"Router: Routing to research_agent (session {session_id})")
        return "research_agent"

    # Stage 4: analysis not done
    analysis_result = state.get("analysis_result")
    if analysis_result is None:
        logger.info("[ROUTER] >> Stage 4: ANALYSIS needed (no analysis_result)")
        logger.info(f"Router: Routing to analyst_agent (session {session_id})")
        return "analyst_agent"

    logger.debug("[ROUTER] [DONE] Stage 4: Analysis")

    # Stage 5: report not written
    draft_report = state.get("draft_report", "")
    if not draft_report:
        logger.info("[ROUTER] >> Stage 5: WRITING needed (no draft_report)")
        logger.info(f"Router: Routing to writer_agent (session {session_id})")
        return "writer_agent"

    logger.debug("[ROUTER] [DONE] Stage 5: Draft Report")

    # Stage 6: report not verified
    verified_report = state.get("verified_report", "")
    if not verified_report:
        logger.info("[ROUTER] >> Stage 6: VERIFICATION needed (no verified_report)")
        logger.info(f"Router: Routing to verifier_agent (session {session_id})")
        return "verifier_agent"

    logger.debug("[ROUTER] [DONE] Stage 6: Verification")
    logger.info("[ROUTER] [ALL COMPLETE] PIPELINE DONE")
    
    # All stages complete
    logger.info(f"Router: All pipeline stages complete for session {session_id}")
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
