"""Unit tests for the RAG Agent."""

import pytest
from unittest.mock import patch, MagicMock

from agents.rag_agent import rag_agent
from orchestration.state import DocuForgeState


@pytest.fixture
def base_state() -> DocuForgeState:
    """Fixture with base state including sample document text."""
    return {
        "file_path": "/tmp/test.pdf",
        "query": "What are the key metrics?",
        "ingested_text": "This is sample content with numbers 123 and 456 revenue data.",
        "retrieved_chunks": [],
        "web_context": "",
        "analysis_result": None,
        "draft_report": "",
        "verified_report": "",
        "agent_trace": [],
        "error_log": [],
        "routing_decision": "",
        "reflection_count": 0,
    }


def test_rag_success(base_state):
    """Test successful RAG retrieval and storage."""
    with patch("agents.rag_agent.chunk_document") as mock_chunk, \
         patch("agents.rag_agent.get_vectorstore") as mock_vectorstore, \
         patch("agents.rag_agent.add_documents_to_store") as mock_add, \
         patch("agents.rag_agent.compute_hybrid_retrieval") as mock_retrieval:
        
        mock_chunk.return_value = [MagicMock(page_content="chunk1"), MagicMock(page_content="chunk2")]
        mock_vectorstore.return_value = MagicMock()
        mock_add.return_value = 2
        mock_retrieval.return_value = [MagicMock(page_content="relevant chunk")]
        
        result = rag_agent(base_state)
        
        assert isinstance(result.get("retrieved_chunks"), list)
        assert len(result.get("retrieved_chunks", [])) > 0
        assert result.get("routing_decision") == "analyst"


def test_rag_empty_ingested_text(base_state):
    """Test RAG agent with empty ingested text."""
    base_state["ingested_text"] = ""
    
    result = rag_agent(base_state)
    
    assert result.get("routing_decision") == "error"


def test_rag_state_isolation(base_state):
    """Verify RAG agent returns dict, not full state object."""
    with patch("agents.rag_agent.chunk_document"), \
         patch("agents.rag_agent.get_vectorstore"), \
         patch("agents.rag_agent.add_documents_to_store"), \
         patch("agents.rag_agent.compute_hybrid_retrieval"):
        
        result = rag_agent(base_state)
        
        # Result should be a dict with specific keys, not the full state
        assert isinstance(result, dict)
        assert "retrieved_chunks" in result or "routing_decision" in result


def test_rag_agent_trace_format(base_state):
    """Verify agent trace entry contains proper prefix."""
    with patch("agents.rag_agent.chunk_document") as mock_chunk, \
         patch("agents.rag_agent.get_vectorstore") as mock_vectorstore, \
         patch("agents.rag_agent.add_documents_to_store") as mock_add, \
         patch("agents.rag_agent.compute_hybrid_retrieval") as mock_retrieval:
        
        mock_chunk.return_value = [MagicMock(page_content="test")]
        mock_vectorstore.return_value = MagicMock()
        mock_add.return_value = 1
        mock_retrieval.return_value = [MagicMock(page_content="chunk")]
        
        result = rag_agent(base_state)
        
        agent_trace = result.get("agent_trace", [])
        assert any("rag_agent:" in str(entry) for entry in agent_trace)
