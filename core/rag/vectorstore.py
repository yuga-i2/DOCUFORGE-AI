"""
DocuForge AI — Vector Store

Manages ChromaDB instance for storing and querying document embeddings.
Handles initialization, persistence, and high-level CRUD operations.
"""

import logging
from pathlib import Path

import yaml
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
    Get or create a persistent ChromaDB vector store collection. Reuses existing
    instances if already loaded, avoiding redundant initializations.
    """
    if collection_name in _vectorstores:
        return _vectorstores[collection_name]

    persist_dir = Path("chroma_db")
    persist_dir.mkdir(exist_ok=True)

    embedding_fn = get_embedding_function()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_fn,
        persist_directory=str(persist_dir),
    )

    _vectorstores[collection_name] = vectorstore
    logger.info("Loaded vectorstore collection: %s", collection_name)
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
    """
    if collection_name in _vectorstores:
        del _vectorstores[collection_name]

    vectorstore = get_vectorstore(collection_name)
    vectorstore._client.delete_collection(name=collection_name)

    logger.info("Deleted collection: %s", collection_name)
