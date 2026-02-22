"""
DocuForge AI — Multi-Agent Orchestration Demo

Standalone demonstration of running the full agent pipeline:
Ingestion → RAG → Analysis → Writing → Verification.
"""

import logging
from pathlib import Path

from core.agent_graph import DocuForgeState, compile_docuforge_graph
from core.ingestion.file_ingester import ingest_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Multi-agent orchestration demo: load file → initialize state → run graph.
    """

    logger.info("=== Multi-Agent Orchestration Demo ===")

    # 1. Load sample document
    logger.info("\nStep 1: Load sample document")

    sample_doc_path = Path("sample_document.pdf")  # Update with actual path
    if not sample_doc_path.exists():
        logger.error("Sample document not found: %s", sample_doc_path)
        logger.info("Create a sample_document.pdf in the project root to run this example.")
        return

    document_text = ingest_file(str(sample_doc_path))
    logger.info("Document loaded: %d characters", len(document_text))

    # 2. Initialize state
    logger.info("\nStep 2: Initialize agent state")

    query = "Summarize the key findings in this document"
    state = DocuForgeState(
        session_id="demo-session-001",
        query=query,
        file_path=str(sample_doc_path),
        document_text=document_text[:5000],  # Truncate for demo
        agent_trace=[],
        error_log=[],
        ingestion_result={"status": "success", "chunks": 1},
        rag_context=[],
        research_context=[],
        draft_report="",
        verified_report="",
        reflection_count=0,
        routing_decision="",
    )

    logger.info("State initialized: session_id=%s, query=%s", state["session_id"], state["query"])

    # 3. Compile and run graph
    logger.info("\nStep 3: Compile and run agent graph")

    graph = compile_docuforge_graph()
    logger.info("Graph compiled with %d nodes", len(graph.nodes))

    # Run the graph with streaming
    logger.info("\nGraph execution:")
    logger.info("-" * 60)

    for step in graph.stream(state, config={"recursion_limit": 100}):
        logger.info("Step: %s", step)

    logger.info("-" * 60)
    logger.info("\nFinal state:")
    logger.info("  Routing decision: %s", state.get("routing_decision"))
    logger.info("  Verified report length: %d chars", len(state.get("verified_report", "")))
    logger.info("  Error count: %d", len(state.get("error_log", [])))
    logger.info("  Trace entries: %d", len(state.get("agent_trace", [])))

    # 4. Display results
    logger.info("\nStep 4: Display results")

    logger.info("\nAgent Trace:")
    for i, trace_entry in enumerate(state.get("agent_trace", [])):
        logger.info("  [%d] %s: %s", i + 1, trace_entry.get("agent", "unknown"), trace_entry.get("message", ""))

    if state.get("error_log"):
        logger.warning("\nErrors encountered:")
        for error in state.get("error_log", []):
            logger.warning("  - %s", error)

    logger.info("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
