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
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

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
    Retrieve relevant document chunks using weighted BM25 and semantic search.
    Safely extracts Document objects from ensemble results regardless of whether
    the retriever returns plain Documents or (Document, score) tuples.
    """
    config_data = _load_config()
    k = top_k or config_data["rag"]["top_k_results"]
    semantic_weight = float(config_data["rag"]["semantic_weight"])
    keyword_weight = float(config_data["rag"]["keyword_weight"])

    logger.info("Hybrid retrieval for query: %.80s", query)

    def _extract_doc(item) -> Document | None:
        """Extract a Document from either a plain Document or a (Document, score) tuple."""
        if isinstance(item, Document):
            return item
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], Document):
            return item[0]
        return None

    try:
        bm25 = build_bm25_retriever(documents, k)
        semantic = build_semantic_retriever(vectorstore, k)

        # Try to import EnsembleRetriever with fallback chain
        EnsembleRetriever = None
        try:
            from langchain.retrievers import EnsembleRetriever
        except (ImportError, ModuleNotFoundError):
            try:
                from langchain_community.retrievers import EnsembleRetriever
            except (ImportError, ModuleNotFoundError):
                try:
                    from langchain_core.retrievers import EnsembleRetriever
                except (ImportError, ModuleNotFoundError):
                    EnsembleRetriever = None
        
        # If EnsembleRetriever available, use it; otherwise use semantic only
        if EnsembleRetriever is not None:
            ensemble = EnsembleRetriever(
                retrievers=[bm25, semantic],
                weights=[keyword_weight, semantic_weight],
            )
            raw_results = ensemble.invoke(query)
        else:
            # Fallback: semantic retrieval only
            logger.warning("EnsembleRetriever not available — using semantic retrieval only")
            raw_results = semantic.invoke(query)

        seen: set[str] = set()
        deduped: list[Document] = []
        for item in raw_results:
            doc = _extract_doc(item)
            if doc is not None and doc.page_content not in seen:
                seen.add(doc.page_content)
                deduped.append(doc)

        logger.info("Hybrid retrieval returned %d unique chunks", len(deduped))
        return deduped[:k]

    except Exception as exc:
        logger.error("Ensemble retrieval failed: %s — falling back to semantic only", exc)
        try:
            semantic = build_semantic_retriever(vectorstore, k)
            raw = semantic.invoke(query)
            return [_extract_doc(i) for i in raw if _extract_doc(i) is not None][:k]
        except Exception as exc2:
            logger.error("Semantic fallback also failed: %s", exc2)
            return []
