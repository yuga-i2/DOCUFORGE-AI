"""
DocuForge AI — Supervisor Agent

Orchestrates the overall execution flow by routing to appropriate agents
based on the current state. Monitors task progress and determines when
the pipeline has completed successfully.
"""

import logging

from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def supervisor_agent(state: DocuForgeState) -> dict:
    """
    Inspect the current state and decide routing based on query content. Does
    not perform LLM calls in this phase. Sets routing_decision based on keywords
    in the query that suggest external research is needed.
    
    CRITICAL: Do not override error state set by upstream agents.
    """
    session_id = state.get("session_id", "unknown")
    logger.info(f"[SUPERVISOR] Processing session {session_id}")
    
    # If an error occurred, don't override it — let router handle error_handler routing
    if state.get("routing_decision") == "error":
        error_log = state.get("error_log", [])
        logger.debug("[SUPERVISOR] [ERROR] Error detected in state")
        logger.debug(f"[SUPERVISOR] [ERROR] Message: {error_log[-1] if error_log else 'unknown'}")
        logger.debug("[SUPERVISOR] [ACTION] PRESERVING error state (not routing again)")
        logger.warning(f"Supervisor: Error state detected for session {session_id}, preserving error routing")
        return {}  # Return empty dict to preserve error state in pipeline
    
    query = state.get("query", "").lower()
    logger.debug(f"[SUPERVISOR] Query: {query[:100]}..." if len(query) > 100 else f"[SUPERVISOR] Query: {query}")

    research_keywords = {"industry", "market", "competitor", "trend", "benchmark", "external", "current"}
    needs_research = any(keyword in query for keyword in research_keywords)

    routing_decision = "needs_research" if needs_research else "continue"
    logger.debug(f"[SUPERVISOR] Routing decision: {routing_decision}")

    trace_entry = f"supervisor_agent: routing decision = {routing_decision}"
    logger.info(f"Supervisor: {trace_entry} (session {session_id})")

    return {
        "routing_decision": routing_decision,
        "agent_trace": [trace_entry],
    }
