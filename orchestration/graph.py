"""
DocuForge AI — LangGraph Pipeline Definition

Defines the complete LangGraph workflow that connects all agents
through the shared state object. Contains graph construction and
edge routing logic.
"""

import logging

from langgraph.graph import END, StateGraph

from agents.ingestion_agent import ingestion_agent
from agents.rag_agent import rag_agent
from agents.supervisor_agent import supervisor_agent
from orchestration.router import route_from_supervisor, should_reflect
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)

_graph = None


def _create_error_handler(state: DocuForgeState) -> dict:
    """Handle errors from the pipeline by logging and ending execution."""
    error_log = state.get("error_log", [])
    if error_log:
        logger.error("Pipeline error: %s", error_log[-1])
    return {"routing_decision": "error"}


def build_graph():
    """
    Build and return the complete LangGraph StateGraph that defines the
    multi-agent pipeline. Includes all nodes, edges, and conditional routing.
    """
    graph = StateGraph(DocuForgeState)

    # Add nodes
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("ingestion_agent", ingestion_agent)
    graph.add_node("rag_agent", rag_agent)
    graph.add_node("error_handler", _create_error_handler)

    # Stub agents - wrapped with lambda to avoid execution errors
    graph.add_node("research_agent", lambda state: {"agent_trace": ["research_agent: stub not implemented"]})
    graph.add_node("analyst_agent", lambda state: {"agent_trace": ["analyst_agent: stub not implemented"]})
    graph.add_node("writer_agent", lambda state: {"agent_trace": ["writer_agent: stub not implemented"]})
    graph.add_node("verifier_agent", lambda state: {"agent_trace": ["verifier_agent: stub not implemented"]})

    # Set entry point
    graph.set_entry_point("supervisor")

    # Add edges
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "ingestion_agent": "ingestion_agent",
            "rag_agent": "rag_agent",
            "research_agent": "research_agent",
            "analyst_agent": "analyst_agent",
            "writer_agent": "writer_agent",
            "verifier_agent": "verifier_agent",
            "error_handler": "error_handler",
            "done": END,
        },
    )

    # Edges from ingestion, RAG back to supervisor for next decision
    graph.add_edge("ingestion_agent", "supervisor")
    graph.add_edge("rag_agent", "supervisor")

    # Stub edges - these will be improved when agents are implemented
    graph.add_edge("research_agent", "supervisor")
    graph.add_edge("analyst_agent", "supervisor")
    graph.add_edge("writer_agent", "supervisor")

    # Verifier has its own reflection logic
    graph.add_conditional_edges(
        "verifier_agent",
        should_reflect,
        {
            "writer_agent": "writer_agent",
            "done": END,
        },
    )

    # Error handler always ends
    graph.add_edge("error_handler", END)

    compiled_graph = graph.compile()
    logger.info("LangGraph compiled successfully")
    return compiled_graph


def get_graph():
    """
    Get or build the compiled LangGraph. Uses lazy initialization to build
    the graph once and cache it for reuse.
    """
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
