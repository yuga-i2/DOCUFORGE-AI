"""
DocuForge AI — Multimodal Parser

Extracts content from various document formats including PDFs, images
with OCR, and audio files with transcription. Returns normalized text
suitable for downstream processing.
"""

import base64
import logging
from pathlib import Path

import pandas as pd
import yaml
from langchain_core.messages import HumanMessage
from pptx import Presentation

import whisper

from core.llm_router import get_llm

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def parse_pdf(file_path: str) -> str:
    """
    Extract all text from a PDF file using PyMuPDF (fitz). Returns
    concatenated text from all pages.
    """
    import fitz

    text_parts = []
    with fitz.open(file_path) as pdf:
        for page_num, page in enumerate(pdf):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"[Page {page_num + 1}]\n{text}")

    result = "\n".join(text_parts)
    logger.info("Parsed PDF with %d pages, extracted %d chars", len(pdf), len(result))
    return result


def parse_image(file_path: str) -> str:
    """
    Extract text and visual content from an image using the configured LLM
    with multimodal (vision) capability. Returns descriptive text of image content.
    """
    with open(file_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    file_ext = Path(file_path).suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(file_ext, "image/jpeg")

    llm = get_llm(task_type="multimodal", has_image=True)

    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_data}"},
            },
            {
                "type": "text",
                "text": "Extract and describe all text and visual content visible in this image. "
                "Provide a detailed description of what you see, including any text."
            },
        ]
    )

    response = llm.invoke([message])
    result = response.content if isinstance(response.content, str) else str(response.content)

    logger.info("Parsed image, extracted text from vision model")
    return result


def parse_audio(file_path: str) -> str:
    """
    Transcribe audio file to text using OpenAI Whisper. Loads the base model
    and transcribes the entire audio file.
    """
    logger.info("Loading Whisper model for transcription")
    model = whisper.load_model("base")

    result = model.transcribe(file_path)
    transcript = result.get("text", "")

    logger.info("Transcribed audio, extracted %d chars", len(transcript))
    return transcript


def parse_excel(file_path: str) -> str:
    """
    Extract data from Excel file using pandas. Reads all sheets and converts
    each to a markdown-style table representation.
    """
    excel_file = pd.ExcelFile(file_path)
    sheet_texts = []

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        markdown = df.to_markdown(index=False)
        sheet_texts.append(f"Sheet: {sheet_name}\n{markdown}")

    result = "\n\n".join(sheet_texts)
    logger.info("Parsed Excel with %d sheets", len(excel_file.sheet_names))
    return result


def parse_pptx(file_path: str) -> str:
    """
    Extract text from PowerPoint presentation using python-pptx. Returns
    all text found in text frames across all slides.
    """
    prs = Presentation(file_path)
    slide_texts = []

    for slide_num, slide in enumerate(prs.slides):
        slide_content = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_content.append(shape.text)

        if slide_content:
            slide_text = "\n".join(slide_content)
            slide_texts.append(f"Slide {slide_num + 1}:\n{slide_text}")

    result = "\n\n".join(slide_texts)
    logger.info("Parsed PPTX with %d slides, extracted %d chars", len(prs.slides), len(result))
    return result

