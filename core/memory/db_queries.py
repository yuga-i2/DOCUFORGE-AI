"""
DocuForge AI — Database Queries

All PostgreSQL and Supabase queries for the memory system. Centralizes database
access and provides SQL migration functions for schema initialization.
"""

import logging

logger = logging.getLogger(__name__)


def create_sessions_table_sql() -> str:
    """
    Return the CREATE TABLE IF NOT EXISTS SQL for the sessions table.
    Stores session records with query, verified report, scores, and agent trace.
    """
    return """
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(36) UNIQUE NOT NULL,
        query TEXT,
        verified_report TEXT,
        faithfulness_score FLOAT,
        hallucination_score FLOAT,
        agent_trace_json JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
    """


def create_documents_table_sql() -> str:
    """
    Return the CREATE TABLE IF NOT EXISTS SQL for the documents table.
    Tracks ingested documents per session with format and size metadata.
    """
    return """
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(36) NOT NULL,
        filename VARCHAR(255),
        format VARCHAR(20),
        char_count INTEGER,
        ingested_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_documents_session ON documents(session_id);
    """


def create_agent_traces_table_sql() -> str:
    """
    Return the CREATE TABLE IF NOT EXISTS SQL for the agent_traces table.
    Stores detailed per-agent execution logs for debugging and audit trails.
    """
    return """
    CREATE TABLE IF NOT EXISTS agent_traces (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(36) NOT NULL,
        agent_name VARCHAR(100),
        trace_entry TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_traces_session ON agent_traces(session_id);
    """


def create_eval_results_table_sql() -> str:
    """
    Return the CREATE TABLE IF NOT EXISTS SQL for the eval_results table.
    Stores accuracy, faithfulness, and bias evaluation results with scores.
    """
    return """
    CREATE TABLE IF NOT EXISTS eval_results (
        id SERIAL PRIMARY KEY,
        eval_id VARCHAR(20),
        question TEXT,
        expected_answer TEXT,
        actual_answer TEXT,
        accuracy_score FLOAT,
        faithfulness_score FLOAT,
        ran_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_eval_ran_at ON eval_results(ran_at);
    """


def run_migrations(db_url: str) -> bool:
    """
    Execute all CREATE TABLE statements in order using psycopg2.
    Returns True on success, False on failure. Never raises exceptions.
    """
    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        migrations = [
            ("sessions", create_sessions_table_sql()),
            ("documents", create_documents_table_sql()),
            ("agent_traces", create_agent_traces_table_sql()),
            ("eval_results", create_eval_results_table_sql()),
        ]

        for table_name, sql in migrations:
            try:
                cursor.execute(sql)
                logger.info("Migration successful: %s table", table_name)
            except Exception as e:
                logger.error("Migration failed for %s: %s", table_name, str(e))
                conn.rollback()
                cursor.close()
                conn.close()
                return False

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("All database migrations completed successfully")
        return True
    except Exception as e:
        logger.error("Database connection failed: %s", str(e))
        return False
