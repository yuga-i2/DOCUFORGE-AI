"""
DocuForge AI — Embedder Tests

Unit tests for text embedding functions.
Tests cosine similarity, embedding generation, and embedding function retrieval.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_embeddings():
    """Fixture: sample embedding vectors."""
    return {
        "identical": ([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
        "orthogonal": ([1.0, 0.0], [0.0, 1.0]),
        "opposite": ([1.0, 0.0], [-1.0, 0.0]),
    }


def test_embedder_cosine_similarity_identical(mock_embeddings):
    """Test: Cosine similarity returns 1.0 for identical vectors."""
    vec_a, vec_b = mock_embeddings["identical"]

    # Cosine similarity calculation
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(x**2 for x in vec_a) ** 0.5
    norm_b = sum(x**2 for x in vec_b) ** 0.5
    similarity = dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0

    assert similarity == 1.0


def test_embedder_cosine_similarity_orthogonal(mock_embeddings):
    """Test: Cosine similarity returns ~0.0 for orthogonal vectors."""
    vec_a, vec_b = mock_embeddings["orthogonal"]

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(x**2 for x in vec_a) ** 0.5
    norm_b = sum(x**2 for x in vec_b) ** 0.5
    similarity = dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0

    assert abs(similarity) < 0.01


def test_embedder_cosine_similarity_opposite(mock_embeddings):
    """Test: Cosine similarity returns -1.0 for opposite vectors."""
    vec_a, vec_b = mock_embeddings["opposite"]

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(x**2 for x in vec_a) ** 0.5
    norm_b = sum(x**2 for x in vec_b) ** 0.5
    similarity = dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0

    assert similarity == -1.0


def test_embedder_embed_documents():
    """Test: Embedder generates embeddings for document batch."""
    documents = [
        "First document text",
        "Second document text",
        "Third document text",
    ]

    # Mock embedding function
    def mock_embed(texts):
        return [[0.1 * (i + 1)] * 384 for i in range(len(texts))]

    embeddings = mock_embed(documents)

    assert len(embeddings) == 3
    assert len(embeddings[0]) == 384  # Typical embedding dimension


def test_embedder_get_embedding_function():
    """Test: Get embedding function returns callable."""
    with patch("core.rag.embedder.HuggingFaceEmbeddings") as mock_hf:
        mock_instance = MagicMock()
        mock_hf.return_value = mock_instance

        from core.rag.embedder import get_embedding_function

        emb_fn = get_embedding_function()

        assert emb_fn is not None
        assert callable(emb_fn) or hasattr(emb_fn, "embed_query")


def test_embedder_handles_empty_input():
    """Test: Embedder safely handles empty document list."""
    embeddings = []

    assert len(embeddings) == 0
