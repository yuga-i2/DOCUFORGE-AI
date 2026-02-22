"""
DocuForge AI — Format Normalizer

Text normalization utilities for ingestion: whitespace handling, boilerplate removal,
language detection, and token truncation. Applied post-parsing to clean documents.
"""

import logging
import re

logger = logging.getLogger(__name__)


def normalise_whitespace(text: str) -> str:
    """
    Remove leading/trailing whitespace and collapse multiple spaces/newlines.
    Returns normalized text.
    """
    if not text or not isinstance(text, str):
        return ""

    # Collapse multiple spaces
    text = re.sub(r" +", " ", text)

    # Collapse multiple newlines to single newline
    text = re.sub(r"\n\n+", "\n", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    logger.debug("Normalised whitespace: %d chars → %d chars", len(text), len(text))
    return text


def remove_boilerplate(text: str) -> str:
    """
    Remove common boilerplate patterns: copyright notices, footer,
    header/navigation. Returns cleaned text.
    """
    if not text or not isinstance(text, str):
        return ""

    original_len = len(text)

    # Remove copyright year patterns (e.g., "© 2024")
    text = re.sub(r"©\s*\d{2,4}", "", text)

    # Remove common footer patterns
    text = re.sub(r"(?i)(all rights reserved|terms of service|privacy policy|contact us).*$", "", text)

    # Remove HTML/XML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Remove page break markers
    text = re.sub(r"\f|\x0c", "", text)

    # Re-normalize whitespace after removals
    text = normalise_whitespace(text)

    logger.debug("Removed boilerplate: %d chars → %d chars", original_len, len(text))
    return text


def normalise_document_text(text: str) -> str:
    """
    Full text normalization pipeline: whitespace → boilerplate → final trim.
    Safe entry point for all document normalizations.
    """
    if not text or not isinstance(text, str):
        return ""

    text = normalise_whitespace(text)
    text = remove_boilerplate(text)
    text = normalise_whitespace(text)  # Final pass

    logger.debug("Normalised document text: ready for ingestion")
    return text


def truncate_to_token_limit(text: str, token_limit: int = 8000, encode_fn=None) -> str:
    """
    Truncate text to approx token_limit. Defaults to splitting on spaces.
    If encode_fn provided (e.g., tiktoken.encoding_for_model('gpt-4').encode),
    uses tokenizer for precise truncation.
    """
    if not text or not isinstance(text, str):
        return ""

    if not encode_fn:
        # Rough estimate: 4 chars ≈ 1 token
        max_chars = token_limit * 4
        if len(text) <= max_chars:
            return text

        text = text[:max_chars]
        # Trim to last complete word
        text = text[: text.rfind(" ")] if " " in text else text

        logger.warning("Truncated to token limit (rough): %d tokens est.", token_limit)
        return text

    try:
        tokens = encode_fn(text)
        if len(tokens) <= token_limit:
            return text

        # Binary search for safe truncation point
        truncated_tokens = tokens[:token_limit]
        truncated_text = ""

        # Decode tokens back (this varies by tokenizer)
        if hasattr(encode_fn, "decode_single_token_bytes"):
            truncated_text = b"".join(
                [encode_fn.decode_single_token_bytes(t) for t in truncated_tokens]
            ).decode("utf-8", errors="ignore")
        else:
            # Fallback: regenerate via split
            truncated_text = " ".join(text.split()[: token_limit // 2])

        logger.warning("Truncated to token limit: %d → %d tokens", len(tokens), token_limit)
        return truncated_text
    except Exception as e:
        logger.warning("Token truncation failed, falling back to simple truncation: %s", str(e))
        max_chars = token_limit * 4
        return text[:max_chars]


def detect_language_hint(text: str) -> str:
    """
    Detect probable language from text. Returns ISO 639-1 code or 'unknown'.
    Uses simple heuristics: character patterns, common words.
    """
    if not text or not isinstance(text, str):
        return "unknown"

    text_lower = text.lower()
    text_sample = text_lower[:500]

    # Check for Unicode ranges (simplified)
    if re.search(r"[\u4e00-\u9fff]", text_sample):  # CJK Unified Ideographs
        return "zh"
    if re.search(r"[\u3040-\u309f]", text_sample):  # Hiragana
        return "ja"
    if re.search(r"[\u1100-\u11ff]", text_sample):  # Hangul
        return "ko"
    if re.search(r"[\u0600-\u06ff]", text_sample):  # Arabic
        return "ar"
    if re.search(r"[\u0400-\u04ff]", text_sample):  # Cyrillic
        return "ru"

    # Check for common English words
    english_words = {"the", "and", "is", "to", "in", "of", "a", "for", "on"}
    if len([w for w in english_words if w in text_sample.split()]) >= 3:
        return "en"

    # Check for common French words
    french_words = {"le", "la", "de", "et", "est", "un", "une", "les"}
    if len([w for w in french_words if w in text_sample.split()]) >= 3:
        return "fr"

    logger.debug("Language detection inconclusive, defaulting to 'en'")
    return "en"
