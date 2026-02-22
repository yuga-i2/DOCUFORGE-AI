"""
DocuForge AI — Vector Store

Uses Chroma EphemeralClient directly: pure in-memory, no SQLite, no Rust panics, no Windows issues.
Zero persistence — vectors cleared after session. Perfect for stateless analysis tasks.
PostHog telemetry disabled to avoid SSL noise.
"""

import logging
import os
from pathlib import Path

import yaml

# Disable ALL Chroma telemetry BEFORE any imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import chromadb
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from core.rag.embedder import get_embedding_function

logger = logging.getLogger(__name__)

_vectorstores: dict[str, Chroma] = {}


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_vectorstore(collection_name: str) -> Chroma:
    """
    Get or create an in-memory ChromaDB vector store (ephemeral per session).
    Uses chromadb.EphemeralClient directly — pure Python, no SQLite, no Rust.
    Avoids all Windows-specific SQLite panics like "range start index N out of range".
    Reuses existing instances during same session (cached in _vectorstores dict).
    """
    if collection_name in _vectorstores:
        return _vectorstores[collection_name]

    embedding_fn = get_embedding_function()

    try:
        # EphemeralClient = in-memory only, no disk, no SQLite
        # Perfect for session-based analysis: vectors persist during task, cleared after
        client = chromadb.EphemeralClient()
        
        vectorstore = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embedding_fn,
        )
        logger.info("Created in-memory vectorstore: %s (EphemeralClient)", collection_name)
    except Exception as e:
        logger.error("Failed to initialize Chroma vectorstore: %s", str(e))
        raise

    _vectorstores[collection_name] = vectorstore
    return vectorstore


def add_documents_to_store(documents: list[Document], collection_name: str) -> int:
    """
    Add documents to a vectorstore collection and return the count of documents added.
    """
    if not documents:
        logger.warning("No documents to add to collection %s", collection_name)
        return 0

    vectorstore = get_vectorstore(collection_name)
    vectorstore.add_documents(documents)

    logger.info("Added %d documents to collection: %s", len(documents), collection_name)
    return len(documents)


def delete_collection(collection_name: str) -> None:
    """
    Delete an entire collection from the vectorstore and remove from memory cache.
    Safely handles cases where collection already deleted.
    """
    # Remove from cache first
    if collection_name in _vectorstores:
        try:
            _vectorstores[collection_name]._client.delete_collection(name=collection_name)
        except Exception as e:
            logger.debug("Collection delete failed (may not exist): %s", str(e))
        del _vectorstores[collection_name]
    
    logger.info("Deleted collection: %s", collection_name)
