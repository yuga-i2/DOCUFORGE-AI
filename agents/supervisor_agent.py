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
    """
    query = state.get("query", "").lower()

    research_keywords = {"industry", "market", "competitor", "trend", "benchmark", "external", "current"}
    needs_research = any(keyword in query for keyword in research_keywords)

    routing_decision = "needs_research" if needs_research else "continue"

    trace_entry = f"supervisor_agent: routing decision = {routing_decision}"
    logger.debug(trace_entry)

    return {
        "routing_decision": routing_decision,
        "agent_trace": [trace_entry],
    }
