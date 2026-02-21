"""
DocuForge AI — Text Chunker

Splits large text documents into smaller chunks using configurable size
and overlap parameters. Ensures chunks are semantically meaningful and
properly tokenized for embedding.
"""

import logging
from pathlib import Path

import yaml
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def chunk_text(text: str) -> list[str]:
    """
    Split text into chunks using RecursiveCharacterTextSplitter with configurable
    chunk_size and chunk_overlap from config. Returns a list of text strings.
    """
    config = _load_config()
    rag_config = config.get("rag", {})
    chunk_size = rag_config.get("chunk_size", 512)
    chunk_overlap = rag_config.get("chunk_overlap", 50)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def chunk_document(text: str, source_label: str) -> list[Document]:
    """
    Chunk a document and return LangChain Document objects with metadata
    containing source_label and chunk_index. Filters out chunks shorter
    than 50 characters.
    """
    chunks = chunk_text(text)
    documents = []

    for idx, chunk in enumerate(chunks):
        if len(chunk) >= 50:
            doc = Document(
                page_content=chunk,
                metadata={"source": source_label, "chunk_index": idx},
            )
            documents.append(doc)

    logger.info("Chunked document into %d chunks (minimum 50 chars)", len(documents))
    return documents
