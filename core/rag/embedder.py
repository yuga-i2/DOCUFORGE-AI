"""
DocuForge AI — Embeddings

Generates dense vector embeddings for text chunks using a configured
embedding model. Handles batch processing and embedding caching.
"""

import logging

import numpy as np
from langchain_core.documents import Document

from core.llm_router import get_embedding_model

logger = logging.getLogger(__name__)


class EmbeddingWrapper:
    """
    Wrapper around HuggingFaceEmbeddings to add a 'name' attribute
    required by ChromaDB without modifying the original model.
    """
    
    def __init__(self, model):
        self._model = model
        self.name = "sentence-transformers/all-MiniLM-L6-v2"
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        return self._model.embed_documents(texts)
    
    def embed_query(self, text: str) -> list[float]:
        """Embed a query."""
        return self._model.embed_query(text)
    
    def __call__(self, texts: list[str]) -> list[list[float]]:
        """Make the wrapper callable for ChromaDB."""
        return self.embed_documents(texts)


def embed_documents(documents: list[Document]) -> list[Document]:
    """
    Validate that documents are ready for embedding. Does not compute embeddings,
    only ensures documents are properly formatted with required metadata fields.
    """
    if not documents:
        logger.warning("No documents provided for embedding validation")
        return []

    for i, doc in enumerate(documents):
        if not doc.page_content:
            logger.warning("Document %d has empty page_content", i)

    logger.debug("Validated %d documents for embedding", len(documents))
    return documents


def get_embedding_function():
    """
    Get the embedding function by initializing the embedding model.
    Returns the HuggingFaceEmbeddings instance wrapped for ChromaDB compatibility.
    The wrapper exposes a 'name' attribute required by ChromaDB.
    """
    logger.debug("Initializing embedding function")
    model = get_embedding_model()
    
    # Wrap the model to add 'name' attribute for ChromaDB
    wrapped = EmbeddingWrapper(model)
    logger.debug("Wrapped embeddings model with name attribute: %s", wrapped.name)
    
    return wrapped


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors using numpy. Returns a
    float between -1 and 1, where 1 means identical direction.
    """
    arr_a = np.array(vec_a)
    arr_b = np.array(vec_b)

    dot_product = np.dot(arr_a, arr_b)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))
