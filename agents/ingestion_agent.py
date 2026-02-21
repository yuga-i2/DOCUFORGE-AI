"""
DocuForge AI — Ingestion Agent

Parses multimodal documents (PDF, images, audio) into normalized text format.
Handles format-specific extraction logic and normalizes output to a clean
text representation suitable for downstream processing.
"""

import logging

from core.ingestion.file_ingester import ingest_file, validate_file
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def ingestion_agent(state: DocuForgeState) -> dict:
    """
    Parse uploaded document into clean text. Validates file, ingests it,
    and updates state with extracted text and format. On failure, logs error
    and returns error state without raising exceptions.
    """
    file_path = state.get("uploaded_file_path", "")

    if not file_path:
        error_msg = "No file path provided in state"
        logger.error(error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": ["ingestion_agent: error - no file path"],
        }

    is_valid, error_msg = validate_file(file_path)
    if not is_valid:
        logger.error("File validation failed: %s", error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": [f"ingestion_agent: validation failed - {error_msg}"],
        }

    try:
        ingested_text = ingest_file(file_path)
        file_format = file_path.split(".")[-1].lower()

        trace_entry = f"ingestion_agent: parsed {file_format} file, {len(ingested_text)} chars extracted"
        logger.info(trace_entry)

        return {
            "ingested_text": ingested_text,
            "file_format": file_format,
            "agent_trace": [trace_entry],
            "routing_decision": "rag",
        }
    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": [f"ingestion_agent: {error_msg}"],
        }
