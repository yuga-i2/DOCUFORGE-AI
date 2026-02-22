"""
DocuForge AI — File Ingester

Handles initial file upload, validation, and format detection.
Routes files to appropriate format-specific parsers.
"""

import logging
from pathlib import Path

import yaml

from core.ingestion.format_normalizer import normalise_document_text
from core.ingestion.multimodal_parser import (
    parse_audio,
    parse_excel,
    parse_image,
    parse_pdf,
    parse_pptx,
)

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def validate_file(file_path: str) -> tuple[bool, str]:
    """
    Validate that a file exists, has a supported format, and is not empty.
    Returns (True, "") on success or (False, reason_string) on failure.
    """
    config = _load_config()
    ingestion_config = config.get("ingestion", {})
    supported_formats = ingestion_config.get("supported_formats", [])
    max_file_size_mb = ingestion_config.get("max_file_size_mb", 50)

    file = Path(file_path)

    if not file.exists():
        return False, f"File does not exist: {file_path}"

    extension = file.suffix.lstrip(".").lower()
    if extension not in supported_formats:
        return False, f"Unsupported file format: {extension}. Supported: {', '.join(supported_formats)}"

    file_size_mb = file.stat().st_size / (1024 * 1024)
    if file_size_mb > max_file_size_mb:
        return False, f"File exceeds maximum size of {max_file_size_mb}MB"

    if file.stat().st_size == 0:
        return False, "File is empty"

    return True, ""


def ingest_file(file_path: str) -> str:
    """
    Detect file format from extension and route to the correct parser.
    Returns normalised, clean text regardless of input format.
    Applies text normalisation after parsing.
    
    Args:
        file_path: Path to document file
        
    Returns:
        Normalized and truncated document text
        
    Raises:
        ValueError: If file format is not supported
    """
    path = Path(file_path)
    extension = path.suffix.lower().lstrip(".")
    
    format_map = {
        "pdf": parse_pdf,
        "png": parse_image,
        "jpg": parse_image,
        "jpeg": parse_image,
        "mp3": parse_audio,
        "wav": parse_audio,
        "xlsx": parse_excel,
        "xls": parse_excel,
        "csv": parse_excel,
        "pptx": parse_pptx,
        "ppt": parse_pptx,
    }

    parser = format_map.get(extension)
    if parser is None:
        raise ValueError(f"Unsupported format: .{extension}")

    logger.info("Ingesting file: %s (format: %s)", path.name, extension)
    raw_text = parser(str(file_path))
    normalised = normalise_document_text(raw_text)

    logger.debug("Text normalization: %d chars → %d chars", len(raw_text), len(normalised))
    return normalised
