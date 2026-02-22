"""
DocuForge AI — Short-Term Memory System

Implements LangGraph in-context short-term memory for session state management.
Handles session initialization, safe state merging, and session summary generation.
All data persists only for the duration of a single pipeline execution.
"""

import logging
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def initialise_session_state(session_id: str, query: str, file_path: str) -> DocuForgeState:
    """
    Initialize a fresh DocuForgeState with all fields set to their zero values
    plus the provided session_id, query, and uploaded_file_path. Called at the
    start of each pipeline execution to ensure a clean slate.
    """
    logger.info("Initializing session state: session_id=%s, query_len=%d", session_id, len(query))

    state: DocuForgeState = {
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
        "error_log": [],
    }

    return state


def merge_state_update(current: DocuForgeState, update: dict) -> DocuForgeState:
    """
    Safely merge a partial state update dict into the current state without
    overwriting Annotated append-only list fields. The agent_trace and error_log
    lists always append new entries; they are never replaced or truncated.
    """
    merged = current.copy()

    for key, value in update.items():
        if key == "agent_trace" and isinstance(value, list):
            merged["agent_trace"] = merged.get("agent_trace", []) + value
        elif key == "error_log" and isinstance(value, list):
            merged["error_log"] = merged.get("error_log", []) + value
        else:
            merged[key] = value

    return merged


def get_session_summary(state: DocuForgeState) -> dict[str, str | int]:
    """
    Return a lightweight summary dict of the current session including session_id,
    truncated query, agent run count, verification status, and faithfulness score.
    Used for logging and dashboard display without exposing full state.
    """
    query_truncated = state.get("query", "")[:80]
    agent_trace = state.get("agent_trace", [])
    agents_run = len(agent_trace)
    has_verified_report = bool(state.get("verified_report", ""))
    faithfulness_score = state.get("faithfulness_score", 0.0)

    summary = {
        "session_id": state.get("session_id", "unknown"),
        "query_truncated": query_truncated,
        "agents_run": agents_run,
        "has_verified_report": str(has_verified_report),
        "faithfulness_score": faithfulness_score,
    }

    return summary
