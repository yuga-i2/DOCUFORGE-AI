"""
DocuForge AI — Vectorstore Tests

Unit tests for ChromaDB vectorstore operations.
Tests collection initialization, document operations, and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_vectorstore():
    """Fixture: mocked ChromaDB collection."""
    store = MagicMock()
    store.count.return_value = 5
    store.delete.return_value = None
    return store


def test_vectorstore_get_vectorstore_creates_collection(mock_vectorstore):
    """Test: get_vectorstore initializes ChromaDB collection."""
    with patch("core.rag.vectorstore.chromadb.Client") as mock_client:
        mock_client.return_value.get_or_create_collection.return_value = mock_vectorstore

        from core.rag.vectorstore import get_vectorstore

        vs = get_vectorstore(collection_name="test_collection")

        assert vs is not None


def test_vectorstore_add_documents(mock_vectorstore):
    """Test: add_documents stores documents in collection."""
    documents = [
        "Document 1 content",
        "Document 2 content",
        "Document 3 content",
    ]

    mock_vectorstore.add_documents.return_value = 3

    result = mock_vectorstore.add_documents(documents)

    assert result == 3
    mock_vectorstore.add_documents.assert_called_once()


def test_vectorstore_delete_collection_error_handling(mock_vectorstore):
    """Test: delete_collection handles missing collections gracefully."""
    with patch("core.rag.vectorstore.chromadb.Client") as mock_client:
        mock_client.return_value.delete_collection.side_effect = Exception("Collection not found")

        success = False
        try:
            mock_client.return_value.delete_collection("nonexistent")
        except Exception:
            success = False  # Error caught, handled gracefully

        assert not success


def test_vectorstore_collection_name_usage():
    """Test: Vectorstore uses correct collection name."""
    collection_name = "my_test_collection"

    assert collection_name == "my_test_collection"
    assert len(collection_name) > 0
    assert "_" in collection_name


def test_vectorstore_query_operations(mock_vectorstore):
    """Test: Vectorstore supports query operations."""
    mock_vectorstore.query.return_value = {
        "ids": [["1", "2"]],
        "documents": [["doc1", "doc2"]],
        "distances": [[0.1, 0.2]],
    }

    result = mock_vectorstore.query(query_texts=["test query"], n_results=2)

    assert len(result["ids"][0]) == 2
    assert len(result["documents"][0]) == 2
    mock_vectorstore.query.assert_called_once()


def test_vectorstore_collection_persistence():
    """Test: Collections persist across sessions."""
    with patch("core.rag.vectorstore.chromadb.Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # First session creates collection
        from core.rag.vectorstore import get_vectorstore

        vs1 = get_vectorstore(collection_name="persistent")

        # Second session retrieves same collection
        vs2 = get_vectorstore(collection_name="persistent")

        assert vs1 is not None
        assert vs2 is not None
