"""Unit tests for the Ingestion Agent."""

import pytest
from unittest.mock import patch

from agents.ingestion_agent import ingestion_agent
from orchestration.state import DocuForgeState


@pytest.fixture
def base_state() -> DocuForgeState:
    """Fixture providing a base state with required fields initialized."""
    return {
        "file_path": "/tmp/test_doc.pdf",
        "query": "What is the content?",
        "ingested_text": "",
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


def test_ingestion_success(base_state):
    """Test successful document ingestion with valid file."""
    with patch("agents.ingestion_agent.validate_file") as mock_validate, \
         patch("agents.ingestion_agent.ingest_file") as mock_ingest:
        
        mock_validate.return_value = (True, "")
        mock_ingest.return_value = "sample text content"
        
        result = ingestion_agent(base_state)
        
        assert result.get("ingested_text") == "sample text content"
        assert result.get("routing_decision") == "rag"
        assert isinstance(result.get("agent_trace"), list)


def test_ingestion_validation_failure(base_state):
    """Test ingestion failure when file validation fails."""
    with patch("agents.ingestion_agent.validate_file") as mock_validate:
        mock_validate.return_value = (False, "file not found")
        
        result = ingestion_agent(base_state)
        
        assert result.get("routing_decision") == "error"
        assert len(result.get("error_log", [])) > 0


def test_ingestion_state_update_format(base_state):
    """Test that agent trace is properly formatted."""
    with patch("agents.ingestion_agent.validate_file") as mock_validate, \
         patch("agents.ingestion_agent.ingest_file") as mock_ingest:
        
        mock_validate.return_value = (True, "")
        mock_ingest.return_value = "test content"
        
        result = ingestion_agent(base_state)
        
        agent_trace = result.get("agent_trace", [])
        assert isinstance(agent_trace, list)
        assert any("ingestion_agent" in str(entry) for entry in agent_trace)


def test_ingestion_no_direct_imports():
    """Verify ingestion_agent module does not import from other agent modules."""
    import agents.ingestion_agent as ingestion_module
    
    # List of agent modules that should not be imported
    forbidden_imports = [
        "rag_agent", "supervisor_agent", "research_agent",
        "analyst_agent", "writer_agent", "verifier_agent"
    ]
    
    for forbidden in forbidden_imports:
        assert forbidden not in str(ingestion_module.__dict__), \
            f"ingestion_agent should not import {forbidden}"
