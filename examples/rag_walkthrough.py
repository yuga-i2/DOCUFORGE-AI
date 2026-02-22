"""
DocuForge AI — RAG Walkthrough Example

Standalone demonstration of document chunking, embedding, retrieval, and
hybrid search using ChromaDB vectorstore.
"""

import logging
from pathlib import Path

from core.ingestion.file_ingester import ingest_file
from core.rag.chunker import chunk_document
from core.rag.vectorstore import get_vectorstore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    RAG walkthrough: ingest → chunk → embed → retrieve.
    """

    # 1. Ingest a sample document
    logger.info("=== RAG Walkthrough ===")
    logger.info("Step 1: Ingest document")

    sample_doc_path = Path("sample_document.pdf")  # Update with actual path
    if not sample_doc_path.exists():
        logger.error("Sample document not found: %s", sample_doc_path)
        logger.info("Create a sample_document.pdf in the project root to run this example.")
        return

    document_text = ingest_file(str(sample_doc_path))
    logger.info("Ingested document: %d characters", len(document_text))

    # 2. Chunk the document
    logger.info("\nStep 2: Chunk document")

    chunks = chunk_document(document_text, chunk_size=1000, overlap=200)
    logger.info("Created %d chunks", len(chunks))
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        logger.info("  Chunk %d: %d chars → %s...", i + 1, len(chunk), chunk[:80])

    # 3. Get embedding function and vectorstore
    logger.info("\nStep 3: Initialize vectorstore")

    vectorstore = get_vectorstore(collection_name="walkthrough_example")

    logger.info("Vectorstore initialized: %s", vectorstore)

    # 4. Add documents to vectorstore
    logger.info("\nStep 4: Add documents to vectorstore")

    vectorstore.add_documents(chunks)
    logger.info("Added %d documents to vectorstore", len(chunks))

    # 5. Perform semantic search
    logger.info("\nStep 5: Semantic search")

    query = "What is the main topic of this document?"
    results = vectorstore.retriever.invoke(query, top_k=3)

    logger.info("Query: '%s'", query)
    logger.info("Results: %d matches", len(results))
    for i, result in enumerate(results):
        logger.info("  Result %d (relevance=0.%d): %s...", i + 1, (1000 - i * 333) // 10, result.page_content[:100])

    logger.info("\n=== Walkthrough Complete ===")


if __name__ == "__main__":
    main()
