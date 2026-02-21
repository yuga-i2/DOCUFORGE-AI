"""
DocuForge AI — Hybrid Retriever

Implements hybrid retrieval combining BM25 keyword matching and semantic
vector similarity. Returns ranked results using a weighted ensemble of
both retrieval methods.
"""

import logging
from pathlib import Path

import yaml
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_bm25_retriever(documents: list[Document], top_k: int) -> BM25Retriever:
    """
    Build a BM25 keyword-based retriever from documents. BM25 excels at finding
    documents containing specific keywords and phrases.
    """
    return BM25Retriever.from_documents(documents, k=top_k)


def build_semantic_retriever(vectorstore: Chroma, top_k: int) -> VectorStoreRetriever:
    """
    Build a semantic vector similarity retriever from a vectorstore. Returns a
    VectorStoreRetriever configured for the specified top_k results.
    """
    return vectorstore.as_retriever(search_kwargs={"k": top_k})


def compute_hybrid_retrieval(
    query: str,
    vectorstore: Chroma,
    documents: list[Document],
    top_k: int | None = None,
) -> list[Document]:
    """
    Retrieve documents using a hybrid ensemble of semantic and keyword search.
    Combines BM25 retriever and semantic vector retriever with configurable weights,
    deduplicates results, and returns them ranked by ensemble score.
    """
    config = _load_config()
    rag_config = config.get("rag", {})

    if top_k is None:
        top_k = rag_config.get("top_k_results", 4)

    semantic_weight = rag_config.get("semantic_weight", 0.6)
    keyword_weight = rag_config.get("keyword_weight", 0.4)

    bm25_retriever = build_bm25_retriever(documents, top_k=top_k)
    semantic_retriever = build_semantic_retriever(vectorstore, top_k=top_k)

    # Run both retrievers and combine results manually
    bm25_results = bm25_retriever.invoke(query)
    semantic_results = semantic_retriever.invoke(query)

    # Combine with weighted deduplication
    combined_dict: dict[str, tuple[Document, float]] = {}

    for doc in semantic_results:
        content = doc.page_content
        if content not in combined_dict:
            combined_dict[content] = (doc, 0.0)
        score, _ = combined_dict[content]
        combined_dict[content] = (doc, score + semantic_weight)

    for doc in bm25_results:
        content = doc.page_content
        if content not in combined_dict:
            combined_dict[content] = (doc, 0.0)
        doc_obj, score = combined_dict[content]
        combined_dict[content] = (doc_obj, score + keyword_weight)

    # Sort by combined score and return
    sorted_results = sorted(combined_dict.items(), key=lambda x: x[1][1], reverse=True)
    deduplicated = [doc for _, (doc, _) in sorted_results]

    logger.info("Hybrid retrieval for query '%s': retrieved %d unique results", query[:80], len(deduplicated))
    return deduplicated
