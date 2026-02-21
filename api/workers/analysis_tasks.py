"""
DocuForge AI — Analysis Pipeline Celery Tasks

Implements background tasks for running the full document analysis pipeline.
The pipeline is executed asynchronously via Celery, allowing the API to
return immediately while processing happens in the background.
"""

import logging

from orchestration.graph import get_graph
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def run_analysis_pipeline(file_path: str, query: str, session_id: str) -> dict:
    """
    Run the complete DocuForge analysis pipeline. Initializes state, invokes
    the LangGraph, and returns the final verified report and agent trace.
    This is a Celery task decorated in celery_app config.
    """
    logger.info("Starting analysis pipeline: session=%s, query=%s", session_id, query[:80])

    try:
        # Initialize state with input parameters
        initial_state: DocuForgeState = {
            "query": query,
            "uploaded_file_path": file_path,
            "file_format": "",
            "ingested_text": "",
            "retrieved_chunks": [],
            "web_context": "",
            "analysis_result": None,
            "draft_report": "",
            "verified_report": "",
            "hallucination_score": 0.0,
            "faithfulness_score": 0.0,
            "routing_decision": "",
            "reflection_count": 0,
            "agent_trace": [],
            "error_log": [],
            "session_id": session_id,
        }

        # Get compiled graph and invoke
        graph = get_graph()
        final_state = graph.invoke(initial_state)

        # Extract results
        verified_report = final_state.get("verified_report", "") or final_state.get("draft_report", "")
        agent_trace = final_state.get("agent_trace", [])
        error_log = final_state.get("error_log", [])

        result = {
            "verified_report": verified_report,
            "agent_trace": agent_trace,
            "error_log": error_log,
            "status": "success" if not error_log else "partial_success",
        }

        logger.info("Pipeline completed: session=%s, status=%s", session_id, result["status"])
        return result
    except Exception as e:
        error_msg = f"Pipeline execution failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "status": "failed",
            "verified_report": "",
            "agent_trace": [],
            "error_log": [error_msg],
        }
