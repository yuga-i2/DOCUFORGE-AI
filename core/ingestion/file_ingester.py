"""
DocuForge AI — File Ingester

Handles initial file upload, validation, and format detection.
Routes files to appropriate format-specific parsers.
"""

import logging
from pathlib import Path

import yaml

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
    Ingest a file by detecting its format and routing to the appropriate parser.
    Returns cleaned, normalised text string. Raises ValueError on unsupported format.
    """
    file = Path(file_path)
    extension = file.suffix.lstrip(".").lower()

    logger.info("Ingesting file: %s (format: %s)", file.name, extension)

    if extension == "pdf":
        return parse_pdf(file_path)
    elif extension in ("png", "jpg", "jpeg"):
        return parse_image(file_path)
    elif extension in ("mp3", "wav"):
        return parse_audio(file_path)
    elif extension == "xlsx":
        return parse_excel(file_path)
    elif extension == "pptx":
        return parse_pptx(file_path)
    else:
        raise ValueError(f"No parser available for extension: {extension}")
