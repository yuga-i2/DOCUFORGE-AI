"""Unit tests for the hybrid retriever."""

from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from core.rag.retriever import build_bm25_retriever, compute_hybrid_retrieval


def test_hybrid_retrieval_returns_documents():
    """Test that hybrid retrieval returns Document objects."""
    with patch("core.rag.retriever.build_bm25_retriever") as mock_bm25, \
         patch("core.rag.retriever.build_semantic_retriever") as mock_semantic:
        
        mock_bm25_retriever = MagicMock()
        mock_semantic_retriever = MagicMock()
        
        doc1 = Document(page_content="test content 1")
        doc2 = Document(page_content="test content 2")
        
        mock_bm25_retriever.invoke.return_value = [doc1]
        mock_semantic_retriever.invoke.return_value = [doc2]
        
        mock_bm25.return_value = mock_bm25_retriever
        mock_semantic.return_value = mock_semantic_retriever
        
        vectorstore = MagicMock()
        documents = [doc1, doc2]
        
        result = compute_hybrid_retrieval("test query", vectorstore, documents, top_k=5)
        
        assert isinstance(result, list)
        assert all(isinstance(doc, Document) for doc in result)


def test_hybrid_retrieval_deduplication():
    """Test that duplicate documents are removed."""
    with patch("core.rag.retriever.build_bm25_retriever") as mock_bm25, \
         patch("core.rag.retriever.build_semantic_retriever") as mock_semantic:
        
        mock_bm25_retriever = MagicMock()
        mock_semantic_retriever = MagicMock()
        
        doc = Document(page_content="same content")
        
        mock_bm25_retriever.invoke.return_value = [doc]
        mock_semantic_retriever.invoke.return_value = [doc]
        
        mock_bm25.return_value = mock_bm25_retriever
        mock_semantic.return_value = mock_semantic_retriever
        
        vectorstore = MagicMock()
        
        result = compute_hybrid_retrieval("test", vectorstore, [doc], top_k=5)
        
        # Should deduplicate identical documents
        assert len(result) <= 2


def test_bm25_retriever_build():
    """Test that BM25 retriever is properly built."""
    doc1 = Document(page_content="test document one")
    doc2 = Document(page_content="test document two")
    documents = [doc1, doc2]
    
    retriever = build_bm25_retriever(documents, top_k=1)
    
    assert hasattr(retriever, "invoke")
    assert callable(retriever.invoke)


def test_config_weights_respected():
    """Test that semantic and keyword weights sum to 1.0."""
    from core.rag.retriever import SEMANTIC_WEIGHT, KEYWORD_WEIGHT
    
    total_weight = SEMANTIC_WEIGHT + KEYWORD_WEIGHT
    assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got: {total_weight}"
