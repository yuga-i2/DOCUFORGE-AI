"""
DocuForge AI — LangGraph Pipeline Definition

Defines the complete LangGraph workflow that connects all agents
through the shared state object. Contains graph construction and
edge routing logic.
"""

import logging

from langgraph.graph import END, StateGraph

from agents.analyst_agent import analyst_agent
from agents.ingestion_agent import ingestion_agent
from agents.rag_agent import rag_agent
from agents.research_agent import research_agent
from agents.supervisor_agent import supervisor_agent
from agents.verifier_agent import verifier_agent
from agents.writer_agent import writer_agent
from orchestration.router import route_from_supervisor, should_reflect
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)

_graph = None


def _create_error_handler(state: DocuForgeState) -> dict:
    """Handle errors from the pipeline by logging and ending execution."""
    session_id = state.get("session_id", "unknown")
    error_log = state.get("error_log", [])
    
    logger.error(f"[ERROR_HANDLER] Processing error for session {session_id}")
    if error_log:
        logger.error(f"[ERROR_HANDLER] [ERROR] Pipeline Error: {error_log[-1]}")
        logger.error(f"[ERROR_HANDLER] [LOG] Full error log: {error_log}")
        logger.error(f"Pipeline error (session {session_id}): {error_log[-1]}")
    logger.error("[ERROR_HANDLER] [ACTION] Stopping pipeline (error state)")
    
    return {"routing_decision": "error"}


def build_graph():
    """
    Build and return the complete LangGraph StateGraph that defines the
    multi-agent pipeline. Includes all nodes, edges, and conditional routing.
    """
    logger.info("[GRAPH] Building LangGraph...")
    graph = StateGraph(DocuForgeState)

    # Add nodes
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("ingestion_agent", ingestion_agent)
    graph.add_node("rag_agent", rag_agent)
    graph.add_node("research_agent", research_agent)
    graph.add_node("analyst_agent", analyst_agent)
    graph.add_node("writer_agent", writer_agent)
    graph.add_node("verifier_agent", verifier_agent)
    graph.add_node("error_handler", _create_error_handler)

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
    graph.add_edge("research_agent", "supervisor")

    # Analyst, Writer route to next agent
    graph.add_edge("analyst_agent", "supervisor")
    graph.add_edge("writer_agent", "verifier_agent")

    # Verifier has reflection logic
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

    print("[GRAPH] Compiling graph...")
    compiled_graph = graph.compile()
    print("[GRAPH] [OK] LangGraph compiled successfully")
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
