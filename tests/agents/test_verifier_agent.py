"""
Unit tests for the Verifier Agent.

Tests cover high-faithfulness passages, reflection triggering, max loop handling,
and score storage functionality.
"""

import pytest
from unittest.mock import patch
from orchestration.state import DocuForgeState


@pytest.fixture
def base_state() -> DocuForgeState:
    """Provide a base state with draft report and retrieved chunks."""
    return {
        "query": "What is the capital of France?",
        "uploaded_file_path": "/tmp/test.pdf",
        "file_format": "pdf",
        "ingested_text": "France is a country. Paris is the capital.",
        "retrieved_chunks": ["source chunk one", "source chunk two"],
        "web_context": "",
        "analysis_result": None,
        "draft_report": "Test report content about France and Paris.",
        "verified_report": "",
        "hallucination_score": 0.0,
        "faithfulness_score": 0.0,
        "routing_decision": "",
        "reflection_count": 0,
        "agent_trace": [],
        "error_log": [],
        "session_id": "test_session_123",
    }


def test_verifier_passes_high_score(base_state):
    """When faithfulness score >= 0.85, verifier accepts draft and routes to done."""
    from agents.verifier_agent import verifier_agent

    with patch("agents.verifier_agent._compute_faithfulness_score", return_value=0.92):
        result = verifier_agent(base_state)

        assert result.get("routing_decision") == "done"
        assert result.get("verified_report") == base_state["draft_report"]
        assert result.get("faithfulness_score") >= 0.85


def test_verifier_triggers_reflection(base_state):
    """When score < 0.85 and reflections < max, verifier routes back to writer."""
    from agents.verifier_agent import verifier_agent

    base_state["reflection_count"] = 0

    with patch("agents.verifier_agent._compute_faithfulness_score", return_value=0.60):
        result = verifier_agent(base_state)

        assert result.get("routing_decision") == "writer"
        assert result.get("reflection_count") == 1


def test_verifier_accepts_at_max_loops(base_state):
    """When reflections == max, verifier accepts draft even with low score."""
    from agents.verifier_agent import verifier_agent

    base_state["reflection_count"] = 3  # Assume max is 3

    with patch("agents.verifier_agent._compute_faithfulness_score", return_value=0.60):
        result = verifier_agent(base_state)

        assert result.get("routing_decision") == "done"


def test_verifier_scores_stored_in_state(base_state):
    """Verifier stores both faithfulness and hallucination scores in state."""
    from agents.verifier_agent import verifier_agent

    faithfulness = 0.92
    hallucination = 0.08

    with patch("agents.verifier_agent._compute_faithfulness_score", return_value=faithfulness):
        with patch("agents.verifier_agent._compute_hallucination_score", return_value=hallucination):
            result = verifier_agent(base_state)

            assert result.get("faithfulness_score") == faithfulness
            assert result.get("hallucination_score") == hallucination
            assert (
                abs(
                    (result.get("faithfulness_score", 0) + result.get("hallucination_score", 0))
                    - 1.0
                )
                < 0.01
            )
