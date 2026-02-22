"""
DocuForge AI — Analysis Pipeline Celery Tasks

Implements background tasks for running the full document analysis pipeline.
The pipeline is executed asynchronously via Celery, allowing the API to
return immediately while processing happens in the background.
"""

import logging

from api.workers.celery_app import celery_app
from orchestration.graph import get_graph
from orchestration.state import DocuForgeState
from core.memory.long_term import save_session_result
from core.memory.episodic import store_interaction

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, soft_time_limit=300)
def run_analysis_pipeline(
    self, file_path: str, query: str, session_id: str, prompt_version: str = "v3"
) -> dict:
    """
    Execute the full DocuForge agent pipeline as a Celery background task.
    Accepts file_path, query, and session_id, runs the complete LangGraph
    pipeline, saves results to memory systems, and returns the verified report.
    
    Args:
        self: Celery task instance (bind=True)
        file_path: Path to uploaded document
        query: User query for analysis
        session_id: Unique session identifier
        
    Returns:
        Dict with verified_report, agent_trace, scores, and session_id
    """
    print(f"\n{'='*70}")
    print("[PIPELINE] Starting analysis pipeline")
    print(f"[PIPELINE] Session ID: {session_id}")
    print(f"[PIPELINE] Prompt Version: {prompt_version}")
    print(f"[PIPELINE] Query: {query[:80]}..." if len(query) > 80 else f"[PIPELINE] Query: {query}")
    print(f"[PIPELINE] File: {file_path}")
    print(f"{'='*70}")
    
    logger.info("Using prompt version: %s", prompt_version)
    
    logger.info(
        "Starting analysis pipeline: session=%s, query=%s",
        session_id,
        query[:80]
    )

    try:
        # Initialize state with input parameters
        logger.info("[PIPELINE] Initializing state...")
        initial_trace_entry = f"pipeline: using prompt version {prompt_version}"
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
            "agent_trace": [initial_trace_entry],
            "error_log": [],
            "session_id": session_id,
        }
        logger.info("[PIPELINE] [OK] State initialized with %d keys", len(initial_state))

        # Get compiled graph and invoke with increased recursion limit
        logger.info("[PIPELINE] Getting compiled graph...")
        graph = get_graph()
        logger.info("[PIPELINE] [OK] Graph loaded")
        logger.info("[PIPELINE] Invoking graph (recursion_limit=25000)...")
        logger.info("[PIPELINE] " + "-"*66)
        
        final_state = graph.invoke(
            initial_state,
            config={"recursion_limit": 25000}
        )
        logger.info("[PIPELINE] " + "-"*66)
        logger.info("[PIPELINE] [COMPLETE] Graph execution complete")

        # Extract results
        verified_report = (
            final_state.get("verified_report", "")
            or final_state.get("draft_report", "")
        )
        agent_trace = final_state.get("agent_trace", [])
        error_log = final_state.get("error_log", [])
        faithfulness_score = final_state.get("faithfulness_score", 0.0)
        hallucination_score = final_state.get("hallucination_score", 0.0)

        result = {
            "verified_report": verified_report,
            "agent_trace": agent_trace,
            "error_log": error_log,
            "faithfulness_score": faithfulness_score,
            "hallucination_score": hallucination_score,
            "session_id": session_id,
            "status": "success" if not error_log else "partial_success",
        }

        # Save to long-term memory
        try:
            save_session_result(final_state)
        except Exception as e:
            logger.warning(
                "Failed to save session to long-term memory: %s", str(e)
            )

        # Store interaction in episodic memory
        try:
            store_interaction(session_id, query, verified_report)
        except Exception as e:
            logger.warning(
                "Failed to store interaction in episodic memory: %s", str(e)
            )

        logger.info(
            "Pipeline completed: session=%s, status=%s",
            session_id,
            result["status"]
        )
        return result

    except Exception as e:
        logger.error("Pipeline execution failed: %s", str(e), exc_info=True)
        
        # Attempt to save partial session record
        try:
            partial_state: DocuForgeState = {
                "session_id": session_id,
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
                "error_log": [str(e)],
            }
            save_session_result(partial_state)
        except Exception as save_error:
            logger.warning("Failed to save partial session: %s", str(save_error))
        
        return {
            "error": str(e),
            "status": "failed",
            "verified_report": "",
            "agent_trace": [],
            "error_log": [str(e)],
            "faithfulness_score": 0.0,
            "hallucination_score": 0.0,
            "session_id": session_id,
        }
