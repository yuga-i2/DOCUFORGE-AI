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
    session_id = state.get("session_id", "unknown")
    logger.info(f"[INGESTION] Starting ingestion for session {session_id}")
    
    file_path = state.get("uploaded_file_path", "")
    logger.debug(f"[INGESTION] File path: {file_path}")

    if not file_path:
        error_msg = "No file path provided in state"
        logger.error(f"[INGESTION] [ERROR] {error_msg}")
        logger.error(error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": ["ingestion_agent: error - no file path"],
        }

    logger.info("[INGESTION] Step 1: Validating file...")
    is_valid, error_msg = validate_file(file_path)
    if not is_valid:
        logger.error(f"[INGESTION] [FAILED] Validation: {error_msg}")
        logger.error("File validation failed: %s", error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": [f"ingestion_agent: validation failed - {error_msg}"],
        }
    logger.info("[INGESTION] [PASS] File validation passed")

    try:
        logger.info("[INGESTION] Step 2: Extracting text from file...")
        ingested_text = ingest_file(file_path)
        file_format = file_path.split(".")[-1].lower()
        text_length = len(ingested_text.strip()) if ingested_text else 0
        logger.info(f"[INGESTION] [DONE] Text extracted: {text_length} chars")

        # Check if extracted text is too small to process
        if not ingested_text or text_length < 50:
            error_msg = f"Extracted text too small ({text_length} chars) - file may be empty or parsing failed"
            logger.error(f"[INGESTION] [FAILED] {error_msg}")
            logger.warning(error_msg)
            return {
                "error_log": [error_msg],
                "routing_decision": "error",
                "agent_trace": [f"ingestion_agent: {error_msg}"],
            }

        logger.info("[INGESTION] [PASS] Text size validation (>= 50 chars)")
        trace_entry = f"ingestion_agent: parsed {file_format} file, {text_length} chars extracted"
        logger.info(f"[INGESTION] [COMPLETE] {trace_entry}")
        logger.info(trace_entry)

        return {
            "ingested_text": ingested_text,
            "file_format": file_format,
            "agent_trace": [trace_entry],
            "routing_decision": "rag",
        }
    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        logger.error(f"[INGESTION] EXCEPTION: {error_msg}")
        logger.error(error_msg)
        return {
            "error_log": [error_msg],
            "routing_decision": "error",
            "agent_trace": [f"ingestion_agent: {error_msg}"],
        }
