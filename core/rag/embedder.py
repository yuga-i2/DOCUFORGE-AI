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
    Returns the HuggingFaceEmbeddings instance configured in llm_router.
    """
    logger.debug("Initializing embedding function")
    return get_embedding_model()


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
