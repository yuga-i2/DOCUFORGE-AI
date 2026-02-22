"""
DocuForge AI — Episodic Memory System

ChromaDB-backed episodic memory for conversation history and interaction storage.
Enables retrieval of similar past interactions for context enrichment.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def store_interaction(
    session_id: str, query: str, response: str, collection_name: str = "episodic_memory"
) -> None:
    """
    Store an interaction (query + response) in ChromaDB with metadata including
    session_id, timestamp, and query_snippet. Creates embeddings automatically.
    Graceful degradation if ChromaDB is unavailable.
    """
    try:
        import chromadb

        client = chromadb.Client()
        # ChromaDB will use default embeddings if None is passed
        # This avoids compatibility issues with wrapped embedding functions
        collection = client.get_or_create_collection(
            name=collection_name,
        )

        interaction_text = f"{query}\n{response}"
        query_snippet = query[:100]
        timestamp = datetime.utcnow().isoformat()

        collection.add(
            ids=[f"{session_id}_{timestamp}"],
            documents=[interaction_text],
            metadatas=[
                {
                    "session_id": session_id,
                    "query_snippet": query_snippet,
                    "timestamp": timestamp,
                }
            ],
        )

        logger.debug("Stored interaction in episodic memory: session_id=%s", session_id)
    except Exception as e:
        logger.warning("Failed to store episodic memory: %s", str(e))


def retrieve_similar_interactions(query: str, top_k: int = 3) -> list[dict]:
    """
    Query ChromaDB for similar interactions matching the input query.
    Returns a list of dicts with session_id, query_snippet, and timestamp.
    """
    try:
        import chromadb
        from core.rag.embedder import get_embedding_function

        client = chromadb.Client()
        collection = client.get_or_create_collection(
            name="episodic_memory",
            embedding_function=get_embedding_function(),
        )

        results = collection.query(query_texts=[query], n_results=top_k)

        interactions = []
        if results and results.get("metadatas"):
            for metadata_list in results["metadatas"]:
                for metadata in metadata_list:
                    interactions.append(
                        {
                            "session_id": metadata.get("session_id", ""),
                            "query_snippet": metadata.get("query_snippet", ""),
                            "timestamp": metadata.get("timestamp", ""),
                        }
                    )

        logger.debug(
            "Retrieved %d similar interactions from episodic memory", len(interactions)
        )
        return interactions
    except Exception as e:
        logger.warning("Failed to retrieve episodic memory: %s", str(e))
        return []


def clear_episodic_memory(session_id: str) -> None:
    """
    Remove all episodic memory records for a given session_id.
    """
    try:
        import chromadb

        client = chromadb.Client()
        collection = client.get_or_create_collection(name="episodic_memory")

        results = collection.get(where={"session_id": session_id})
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])
            logger.info("Cleared episodic memory for session_id=%s", session_id)
    except Exception as e:
        logger.warning("Failed to clear episodic memory: %s", str(e))
