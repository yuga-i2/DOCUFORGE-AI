"""
DocuForge AI — Long-Term Memory System

Persistent storage of sessions, documents, and analysis results in PostgreSQL
via Supabase. Provides graceful degradation if Supabase is unavailable.
"""

import json
import logging
import os
from datetime import datetime

from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def save_session_result(state: DocuForgeState, db_url: str | None = None) -> bool:
    """
    Upsert a session record to Supabase with session data and scores.
    Returns True on success, False on failure. Never raises exceptions.
    """
    supabase_url = db_url or os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not configured — skipping long-term save")
        return False

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)

        session_id = state.get("session_id", "unknown")
        query = state.get("query", "")
        verified_report = state.get("verified_report", "") or state.get("draft_report", "")
        faithfulness_score = state.get("faithfulness_score", 0.0)
        hallucination_score = state.get("hallucination_score", 0.0)
        agent_trace = state.get("agent_trace", [])

        record = {
            "session_id": session_id,
            "query": query,
            "verified_report": verified_report,
            "faithfulness_score": float(faithfulness_score),
            "hallucination_score": float(hallucination_score),
            "agent_trace_json": json.dumps(agent_trace),
            "created_at": datetime.utcnow().isoformat(),
        }

        client.table("sessions").upsert(record).execute()
        logger.info("Session saved to long-term memory: session_id=%s", session_id)
        return True
    except Exception as e:
        logger.warning("Failed to save session to Supabase: %s", str(e))
        return False


def fetch_similar_sessions(query: str, limit: int = 5) -> list[dict]:
    """
    Fetch the most recent sessions from Supabase ordered by created_at descending.
    Returns a list of session dicts with no semantic search, just recency.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not configured — returning empty sessions")
        return []

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)
        response = (
            client.table("sessions")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        logger.debug("Fetched %d recent sessions from long-term memory", len(response.data))
        return response.data
    except Exception as e:
        logger.warning("Failed to fetch sessions from Supabase: %s", str(e))
        return []


def get_session_by_id(session_id: str) -> dict | None:
    """
    Fetch a single session record by session_id from Supabase.
    Returns the session dict or None if not found.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not configured — cannot fetch session")
        return None

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)
        response = (
            client.table("sessions")
            .select("*")
            .eq("session_id", session_id)
            .single()
            .execute()
        )
        logger.debug("Fetched session from long-term memory: session_id=%s", session_id)
        return response.data
    except Exception as e:
        logger.warning("Failed to fetch session %s from Supabase: %s", session_id, str(e))
        return None
