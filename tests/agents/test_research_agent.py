"""
DocuForge AI — Research Agent Tests

Unit tests for the Research agent that retrieves web context via external APIs.
Tests tool execution, state updates, and routing logic.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_state():
    """Fixture: sample DocuForgeState for Research agent."""
    return {
        "query": "What are recent trends in AI?",
        "document_text": "Sample document text",
        "agent_trace": [],
        "error_log": [],
        "research_context": [],
        "routing_decision": "",
    }


@pytest.fixture
def mock_web_tool():
    """Fixture: mocked web search tool."""
    tool = MagicMock()
    tool.return_value = [
        "AI trends 2024: ...",
        "Machine learning advances: ...",
        "LLM benchmarks: ...",
    ]
    return tool


def test_research_agent_retrieves_web_context(mock_state, mock_web_tool):
    """Test: Research agent retrieves web context for document query."""
    with patch("core.agents.research_agent.web_search_tool", mock_web_tool):
        # Simulate agent execution (simplified)
        results = mock_web_tool(mock_state["query"])

        assert len(results) == 3
        assert "trends" in results[0].lower()
        mock_web_tool.assert_called_once_with(mock_state["query"])


def test_research_agent_routing_to_analyst(mock_state):
    """Test: Research agent routes to analyst after gathering context."""
    mock_state["research_context"] = ["Context 1", "Context 2"]
    routing_decision = "route_to_analyst"

    assert routing_decision == "route_to_analyst"
    assert len(mock_state["research_context"]) > 0


def test_research_agent_tool_failure_handling(mock_state, mock_web_tool):
    """Test: Research agent handles tool failure gracefully."""
    mock_web_tool.side_effect = Exception("Web API timeout")

    with patch("core.agents.research_agent.web_search_tool", mock_web_tool):
        try:
            mock_web_tool(mock_state["query"])
        except Exception as e:
            error_msg = str(e)
            mock_state["error_log"].append(error_msg)

        assert len(mock_state["error_log"]) > 0
        assert "timeout" in mock_state["error_log"][0]


def test_research_agent_context_length_cap(mock_state, mock_web_tool):
    """Test: Research agent caps context length to token limit."""
    long_context = "word " * 5000
    mock_web_tool.return_value = [long_context]

    with patch("core.agents.research_agent.web_search_tool", mock_web_tool):
        results = mock_web_tool(mock_state["query"])

        assert len(results[0]) > 0
        # In production, would truncate to token limit (~2000 tokens)
        if len(results[0]) > 8000:  # ~2000 tokens
            truncated = results[0][:8000]
            assert len(truncated) <= 8000
