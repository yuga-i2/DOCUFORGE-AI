"""
DocuForge AI — Evaluation Database Queries

Persistence layer for evaluation results to PostgreSQL via psycopg2.
Includes trend analysis and history retrieval.
"""


import logging
import os
from datetime import datetime, timedelta

from models.agent_models import EvalResult

logger = logging.getLogger(__name__)


def save_eval_result_to_db(result: EvalResult, db_url: str | None = None) -> bool:
    """
    Upsert an evaluation result to the eval_results table. Returns True on success,
    False on failure. Never raises exceptions.
    """
    db_url = db_url or os.getenv("DATABASE_URL")

    if not db_url:
        logger.warning("DATABASE_URL not set — skipping eval result persistence")
        return False

    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO eval_results
            (eval_id, question, expected_answer, actual_answer, accuracy_score, faithfulness_score, ran_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                result.eval_id,
                result.question,
                result.expected_answer,
                result.actual_answer,
                result.accuracy_score,
                result.faithfulness_score,
                datetime.utcnow(),
            ),
        )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("Eval result saved: eval_id=%s, accuracy=%.3f", result.eval_id, result.accuracy_score)
        return True
    except Exception as e:
        logger.warning("Failed to save eval result: %s", str(e))
        return False


def fetch_eval_history(limit: int = 50) -> list[dict]:
    """
    Fetch recent evaluation results from the database ordered by ran_at descending.
    Returns list of result dicts or empty list if DB unavailable.
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        logger.warning("DATABASE_URL not set — no eval history available")
        return []

    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT eval_id, question, expected_answer, actual_answer, accuracy_score, faithfulness_score, ran_at
            FROM eval_results
            ORDER BY ran_at DESC
            LIMIT %s
            """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "eval_id": row[0],
                    "question": row[1],
                    "expected_answer": row[2],
                    "actual_answer": row[3],
                    "accuracy_score": row[4],
                    "faithfulness_score": row[5],
                    "ran_at": row[6].isoformat() if row[6] else None,
                }
            )

        cursor.close()
        conn.close()

        logger.debug("Fetched %d eval results from history", len(results))
        return results
    except Exception as e:
        logger.warning("Failed to fetch eval history: %s", str(e))
        return []


def compute_eval_trend(days: int = 30) -> dict[str, list]:
    """
    Compute daily aggregated evaluation metrics over the past N days.
    Returns dict with keys: dates, accuracy_scores, faithfulness_scores.
    Each list has one entry per day, most recent first.
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        logger.warning("DATABASE_URL not set — no trend data available")
        return {"dates": [], "accuracy_scores": [], "faithfulness_scores": []}

    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        cutoff = datetime.utcnow() - timedelta(days=days)

        cursor.execute(
            """
            SELECT DATE(ran_at) as day, AVG(accuracy_score), AVG(faithfulness_score)
            FROM eval_results
            WHERE ran_at >= %s
            GROUP BY DATE(ran_at)
            ORDER BY day DESC
            """,
            (cutoff,),
        )

        dates = []
        accuracy_scores = []
        faithfulness_scores = []

        for row in cursor.fetchall():
            dates.append(row[0].isoformat())
            accuracy_scores.append(float(row[1]) if row[1] else 0.0)
            faithfulness_scores.append(float(row[2]) if row[2] else 0.0)

        cursor.close()
        conn.close()

        logger.debug("Computed trend: %d days of data", len(dates))
        return {
            "dates": dates,
            "accuracy_scores": accuracy_scores,
            "faithfulness_scores": faithfulness_scores,
        }
    except Exception as e:
        logger.warning("Failed to compute eval trend: %s", str(e))
        return {"dates": [], "accuracy_scores": [], "faithfulness_scores": []}
