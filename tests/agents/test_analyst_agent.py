"""
Unit tests for the Analyst Agent.

Tests cover analysis with numerical data, text-only skipping code execution,
error handling, and state update keys.
"""

import pytest
from unittest.mock import patch, MagicMock
from orchestration.state import DocuForgeState
from models.agent_models import AnalysisResult


@pytest.fixture
def base_state_with_numbers() -> DocuForgeState:
    """Provide a state with numerical data in chunks."""
    return {
        "query": "Analyze revenue trends",
        "uploaded_file_path": "/tmp/test.xlsx",
        "file_format": "xlsx",
        "ingested_text": "Revenue 2022: $100M, 2023: $150M, 2024: $200M",
        "retrieved_chunks": ["Revenue 2022: 100000000", "2023: 150000000", "2024: 200000000"],
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
        "session_id": "analyst_test_123",
    }


@pytest.fixture
def base_state_no_numbers() -> DocuForgeState:
    """Provide a state with text-only content."""
    return {
        "query": "Summarize this document",
        "uploaded_file_path": "/tmp/test.pdf",
        "file_format": "pdf",
        "ingested_text": "This is a text document about philosophy",
        "retrieved_chunks": ["Philosophy is the study of thought", "Key concepts in philosophy"],
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
        "session_id": "analyst_test_456",
    }


def test_analyst_with_numerical_data(base_state_with_numbers):
    """Analyst executes Python code when numerical data is detected."""
    from agents.analyst_agent import analyst_agent

    mock_analysis = AnalysisResult(
        summary="Revenue increased 100% over 2 years",
        key_insight="Strong growth trajectory",
    )

    with patch("agents.analyst_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = mock_analysis.model_dump_json()
        mock_llm.return_value = mock_instance

        with patch("agents.analyst_agent.execute_python_code") as mock_execute:
            mock_execute.return_value = {"success": True, "stdout": "Analysis complete"}

            result = analyst_agent(base_state_with_numbers)

            assert result.get("analysis_result") is not None
            assert result.get("routing_decision") == "writer"
            assert mock_execute.called


def test_analyst_skips_code_for_text_only(base_state_no_numbers):
    """Analyst skips code execution for text-only chunks."""
    from agents.analyst_agent import analyst_agent

    with patch("agents.analyst_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = '{"summary": "test", "key_insight": "test"}'
        mock_llm.return_value = mock_instance

        with patch("agents.analyst_agent.execute_python_code") as mock_execute:
            result = analyst_agent(base_state_no_numbers)

            assert not mock_execute.called
            assert result.get("routing_decision") == "writer"


def test_analyst_handles_execution_failure(base_state_with_numbers):
    """Analyst handles code execution failure gracefully."""
    from agents.analyst_agent import analyst_agent

    with patch("agents.analyst_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = '{"summary": "test", "key_insight": "test"}'
        mock_llm.return_value = mock_instance

        with patch("agents.analyst_agent.execute_python_code") as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "stderr": "Error in code execution",
                "stdout": "",
            }

            result = analyst_agent(base_state_with_numbers)

            assert result.get("analysis_result") is not None
            assert result.get("routing_decision") == "writer"
            # No exception should be raised


def test_analyst_state_update_keys(base_state_with_numbers):
    """Analyst returns dict with required keys."""
    from agents.analyst_agent import analyst_agent

    with patch("agents.analyst_agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = '{"summary": "test", "key_insight": "test"}'
        mock_llm.return_value = mock_instance

        with patch("agents.analyst_agent.execute_python_code") as mock_execute:
            mock_execute.return_value = {"success": True, "stdout": ""}

            result = analyst_agent(base_state_with_numbers)

            required_keys = ["analysis_result", "agent_trace", "routing_decision"]
            for key in required_keys:
                assert key in result
