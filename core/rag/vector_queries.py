"""
DocuForge AI — Vector Store Queries

Query interface for ChromaDB vectorstore: collection management, document queries,
and semantic similarity operations.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def query_collection(
    collection, query_text: str, n_results: int = 5, where: dict | None = None
) -> list[dict]:
    """
    Query a ChromaDB collection for semantically similar documents.
    Returns list of result dicts with keys: id, document, distance (0.0-1.0).
    Never raises exceptions; returns empty list on failure.
    """
    if not collection or not query_text:
        logger.warning("Invalid query parameters")
        return []

    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=["documents", "distances", "metadatas"],
        )

        formatted_results = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "id": doc_id,
                        "document": results["documents"][0][i] if results.get("documents") else "",
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    }
                )

        logger.debug("Query returned %d results", len(formatted_results))
        return formatted_results
    except Exception as e:
        logger.warning("Query failed: %s", str(e))
        return []


def collection_exists(client: Any, collection_name: str) -> bool:
    """
    Check if a ChromaDB collection exists. Returns True/False, never raises.
    """
    if not client or not collection_name:
        return False

    try:
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        exists = collection_name in collection_names

        logger.debug("Collection '%s' exists: %s", collection_name, exists)
        return exists
    except Exception as e:
        logger.warning("Failed to check collection existence: %s", str(e))
        return False


def count_documents_in_collection(collection) -> int:
    """
    Count number of documents in a ChromaDB collection.
    Returns count or 0 if collection is None or query fails.
    """
    if not collection:
        return 0

    try:
        count = collection.count()
        logger.debug("Collection has %d documents", count)
        return count
    except Exception as e:
        logger.warning("Failed to count documents: %s", str(e))
        return 0


def list_all_collections(client: Any) -> list[str]:
    """
    List all ChromaDB collections in the client.
    Returns list of collection names or empty list on failure.
    """
    if not client:
        return []

    try:
        collections = client.list_collections()
        names = [c.name for c in collections]

        logger.debug("Found %d collections", len(names))
        return names
    except Exception as e:
        logger.warning("Failed to list collections: %s", str(e))
        return []
