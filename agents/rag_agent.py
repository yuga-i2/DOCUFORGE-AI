"""
DocuForge AI — RAG Agent

Implements hybrid retrieval combining semantic vector search and BM25
keyword matching. Retrieves relevant document chunks and ranks them by
a weighted ensemble score for context passing to downstream agents.
"""

import logging

from core.rag.chunker import chunk_document
from core.rag.retriever import compute_hybrid_retrieval
from core.rag.vectorstore import add_documents_to_store, get_vectorstore
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def rag_agent(state: DocuForgeState) -> dict:
    """
    Chunk ingested text, store embeddings, and retrieve relevant chunks via
    hybrid search. Returns list of retrieved chunk contents and updates agent trace.
    On failure, logs error and returns error state without raising exceptions.
    """
    ingested_text = state.get("ingested_text", "").strip()

    if not ingested_text:
        error_msg = "No ingested text available for RAG"
        logger.warning(error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": ["rag_agent: error - no ingested text"],
        }

    query = state.get("query", "").strip()
    session_id = state.get("session_id", "unknown")

    try:
        # Chunk the document with session_id as source label
        documents = chunk_document(ingested_text, source_label=session_id)

        if not documents:
            error_msg = "Failed to chunk document"
            logger.error(error_msg)
            return {
                "error_log": [error_msg],
                "routing_decision": "error",
                "agent_trace": ["rag_agent: chunking failed"],
            }

        # get vectorstore and add documents
        vectorstore = get_vectorstore(session_id)
        add_documents_to_store(documents, session_id)

        # Run hybrid retrieval
        retrieved_docs = compute_hybrid_retrieval(query, vectorstore, documents)
        retrieved_chunks = [doc.page_content for doc in retrieved_docs]

        trace_entry = f"rag_agent: chunked into {len(documents)} chunks, retrieved {len(retrieved_chunks)} relevant chunks"
        logger.info(trace_entry)

        return {
            "retrieved_chunks": retrieved_chunks,
            "agent_trace": [trace_entry],
            "routing_decision": "analyst",
        }
    except Exception as e:
        error_msg = f"RAG pipeline failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": [f"rag_agent: {error_msg}"],
        }
