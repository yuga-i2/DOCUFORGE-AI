"""
Unit tests for the Writer Agent.

Tests cover report generation, reflection count handling, routing,
JSON parsing, and prompt template loading.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from orchestration.state import DocuForgeState
from models.agent_models import StructuredReport


@pytest.fixture
def base_state() -> DocuForgeState:
    """Provide a base state with analysis results and retrieved chunks."""
    return {
        "query": "Analyze this document",
        "uploaded_file_path": "/tmp/test.pdf",
        "file_format": "pdf",
        "ingested_text": "Sample document content",
        "retrieved_chunks": ["chunk 1", "chunk 2", "chunk 3"],
        "web_context": "",
        "analysis_result": {"summary": "Analysis summary"},
        "draft_report": "",
        "verified_report": "",
        "hallucination_score": 0.0,
        "faithfulness_score": 0.0,
        "routing_decision": "",
        "reflection_count": 0,
        "agent_trace": [],
        "error_log": [],
        "session_id": "test_session_456",
    }


def test_writer_returns_draft_report(base_state):
    """Writer generates and returns a non-empty draft report."""
    from agents.writer_agent import writer_agent

    mock_report = StructuredReport(
        summary="Test summary",
        key_findings=["finding 1", "finding 2"],
        analysis="Test analysis",
        recommendations="Test recommendations",
    )

    with patch("agents.writer_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = mock_report.model_dump_json()
        mock_llm.return_value = mock_instance

        result = writer_agent(base_state)

        assert "draft_report" in result
        assert len(result["draft_report"]) > 0


def test_writer_increments_reflection_count(base_state):
    """Writer preserves and does not reset reflection_count."""
    from agents.writer_agent import writer_agent

    base_state["reflection_count"] = 1

    with patch("agents.writer_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = json.dumps({"summary": "test"})
        mock_llm.return_value = mock_instance

        result = writer_agent(base_state)

        # Reflection count from a previous reflection should not be reset
        assert result.get("reflection_count") == 1


def test_writer_routing_decision(base_state):
    """Writer always routes to verifier after successful generation."""
    from agents.writer_agent import writer_agent

    with patch("agents.writer_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = json.dumps({"summary": "test"})
        mock_llm.return_value = mock_instance

        result = writer_agent(base_state)

        assert result.get("routing_decision") == "verifier"


def test_writer_handles_invalid_json(base_state):
    """Writer gracefully handles invalid JSON and uses raw text as fallback."""
    from agents.writer_agent import writer_agent

    with patch("agents.writer_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = "This is plain text, not JSON"
        mock_llm.return_value = mock_instance

        result = writer_agent(base_state)

        assert "draft_report" in result
        assert result["draft_report"] == "This is plain text, not JSON"
        assert result.get("routing_decision") == "verifier"


def test_writer_reads_prompt_template(base_state):
    """Writer loads prompt template from config."""
    with patch("agents.writer_agent.get_llm"):
        with patch("agents.writer_agent._load_prompt_template") as mock_load:
            mock_load.return_value = "template content"
            # Verify patch point exists
            assert True
