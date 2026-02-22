"""
DocuForge AI — Database Tool

LangGraph tool for agents to query PostgreSQL database.
Wraps Supabase connection in a safe, agent-callable interface with type validation.
"""

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DatabaseToolInput(BaseModel):
    """Input schema for database query tool."""

    query: str = Field(..., description="SQL query to execute (SELECT only)")
    params: list[Any] = Field(default_factory=list, description="Query parameters for parameterized queries")


def query_supabase(query: str, params: list[Any] | None = None) -> list[dict] | None:
    """
    Execute a SELECT query on Supabase PostgreSQL database.
    Returns list of result rows as dicts or None on failure. Never raises exceptions.
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        logger.warning("DATABASE_URL not set — database tool unavailable")
        return None

    params = params or []

    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Allow only SELECT to prevent accidental writes
        if not query.strip().upper().startswith("SELECT"):
            logger.warning("Database tool only allows SELECT queries")
            cursor.close()
            conn.close()
            return None

        cursor.execute(query, params)

        # Fetch column names
        column_names = [desc[0] for desc in cursor.description] if cursor.description else []

        # Convert rows to dicts
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(column_names, row)))

        cursor.close()
        conn.close()

        logger.debug("Database query executed: %d rows returned", len(results))
        return results
    except Exception as e:
        logger.warning("Database query failed: %s", str(e))
        return None


def get_database_tool() -> dict:
    """
    Return a LangGraph tool dict for database queries.
    Use in agent: tool_choice = {"type": "function", "function": {"name": "database"}}
    """
    return {
        "name": "database",
        "description": "Query the PostgreSQL database using SQL SELECT queries. Useful for retrieving session history, evaluation results, or document metadata.",
        "input_schema": DatabaseToolInput.model_json_schema(),
        "function": lambda input_data: query_supabase(input_data.get("query", ""), input_data.get("params", [])),
    }
