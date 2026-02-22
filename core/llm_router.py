"""
DocuForge AI — LLM Router (Groq-First Architecture)

Provider fallback chain: Groq (14,400 req/day free) → Gemini → Ollama (local, unlimited)

** Why Groq primary: **
- 100% free tier: 14,400 requests/day (vs Gemini's 10-200 limit)
- OpenAI-compatible API: fewer surprises
- No model deprecation issues
- Clean error handling: no retry madness
- Runs on custom LPU hardware: 50% faster than Gemini

** Get Groq key: ** https://console.groq.com (30 seconds)

SDK retries disabled everywhere (max_retries=0) — each retry burns a quota slot.
"""

import logging
import os
from pathlib import Path

import yaml

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# ── LangSmith tracing ────────────────────────────────────────────────────────
if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() != "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

_TRACING_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def is_quota_error(e: Exception) -> bool:
    """True if exception is a 429 quota/rate-limit error from any provider."""
    msg = str(e).upper()
    return any(
        x in msg
        for x in [
            "429",
            "RESOURCE_EXHAUSTED",
            "QUOTA",
            "RATE_LIMIT",
            "TOO_MANY_REQUESTS",
            "RATE LIMIT",
        ]
    )


def is_not_found_error(e: Exception) -> bool:
    """True if model not found / deprecated (404)."""
    msg = str(e).upper()
    return "404" in msg or "NOT_FOUND" in msg or "DOES_NOT_EXIST" in msg


def _build_groq(model: str, api_key: str, temperature: float, max_tokens: int):
    """
    Groq (OpenAI-compatible API).
    All retries disabled — clean, fast failure on errors.
    """
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=model,
        groq_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=30,
        max_retries=0,
    )


def _build_gemini(model: str, api_key: str, temperature: float, max_tokens: int):
    """
    Gemini fallback (Google Generative AI).
    max_retries=0 disables LangChain retries, but Google SDK may retry internally.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_tokens,
        max_retries=0,
        request_timeout=30,
    )


def _build_ollama(model: str, temperature: float, max_tokens: int):
    """
    Ollama (local LLM, fallback last resort).
    Unlimited requests, runs on localhost:11434.
    """
    from langchain_community.chat_models import ChatOllama

    return ChatOllama(
        model=model,
        temperature=temperature,
        num_predict=max_tokens,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# Groq free tier models (best to worst)
_GROQ_MODELS = [
    "llama-3.1-8b-instant",  # fastest, 14400 req/day
    "llama-3.3-70b-versatile",  # smarter + fast, same quota
    "mixtral-8x7b-32768",  # older but capable
]

# Gemini fallback models (updated list with current models)
_GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b-latest",
]


class _FallbackLLM:
    """
    LLM with automatic multi-provider fallback chain:
      Groq (best free tier) → Gemini (fallback) → Ollama (local, unlimited)

    Each provider tried once per model in its list. If all fail with quota/not-found,
    moves to next provider. Non-quota errors (validation, parsing, etc.) propagate immediately.
    """

    def __init__(
        self,
        groq_key: str,
        gemini_key: str,
        ollama_model: str,
        temperature: float,
        max_tokens: int,
    ):
        self._groq_key = groq_key
        self._gemini_key = gemini_key
        self._ollama_model = ollama_model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def invoke(self, prompt: str):
        """Invoke with automatic fallback chain. First success returns; first real error propagates."""

        # Try Groq first (best free tier: 14400 req/day)
        if self._groq_key:
            for model in _GROQ_MODELS:
                try:
                    llm = _build_groq(
                        model,
                        self._groq_key,
                        self._temperature,
                        self._max_tokens,
                    )
                    logger.info("LLM routing: trying Groq %s", model)
                    result = llm.invoke(prompt)
                    logger.info("LLM routing: Groq %s succeeded ✓", model)
                    return result
                except Exception as e:
                    if is_quota_error(e) or is_not_found_error(e):
                        logger.warning(
                            "LLM routing: Groq %s failed (%s) → trying next",
                            model,
                            type(e).__name__,
                        )
                        continue
                    # Non-quota error: propagate immediately
                    logger.error("LLM routing: Groq %s error (non-quota): %s", model, str(e))
                    raise

        # Try Gemini as fallback
        if self._gemini_key:
            for model in _GEMINI_MODELS:
                try:
                    llm = _build_gemini(
                        model,
                        self._gemini_key,
                        self._temperature,
                        self._max_tokens,
                    )
                    logger.info("LLM routing: trying Gemini %s", model)
                    result = llm.invoke(prompt)
                    logger.info("LLM routing: Gemini %s succeeded ✓", model)
                    return result
                except Exception as e:
                    if is_quota_error(e) or is_not_found_error(e):
                        logger.warning(
                            "LLM routing: Gemini %s failed (%s) → trying next",
                            model,
                            type(e).__name__,
                        )
                        continue
                    logger.error("LLM routing: Gemini %s error (non-quota): %s", model, str(e))
                    raise

        # Ollama last resort (unlimited, local)
        logger.warning(
            "LLM routing: all cloud providers failed → Ollama %s (local)",
            self._ollama_model,
        )
        return _build_ollama(
            self._ollama_model, self._temperature, self._max_tokens
        ).invoke(prompt)

    @property
    def _llm_type(self):
        return "fallback-chain"


def get_llm(task_type: str = "general", has_image: bool = False):
    """
    Returns _FallbackLLM that tries: Groq → Gemini → Ollama.
    For multimodal tasks (images), uses Gemini directly (best multimodal support).
    """
    config = _load_config()
    llm_config = config.get("llm", {})
    fallback_ollama = llm_config.get("fallback_model", "llama3.2")
    temperature = llm_config.get("temperature", 0.2)
    max_tokens = llm_config.get("max_tokens", 4096)

    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    # Multimodal (images) → Gemini only (best multimodal support)
    if task_type == "multimodal" or has_image:
        if gemini_key:
            logger.info("LLM routing: Gemini gemini-2.0-flash (multimodal task)")
            return _build_gemini("gemini-2.0-flash", gemini_key, temperature, max_tokens)
        else:
            logger.warning("No Gemini key for multimodal → Ollama (images not supported)")
            return _build_ollama(fallback_ollama, temperature, max_tokens)

    # No API keys at all → Ollama local only
    if not groq_key and not gemini_key:
        logger.warning("No API keys (Groq/Gemini) found → Ollama %s (local)", fallback_ollama)
        return _build_ollama(fallback_ollama, temperature, max_tokens)

    # Normal tasks → Fallback chain (Groq → Gemini → Ollama)
    return _FallbackLLM(
        groq_key=groq_key,
        gemini_key=gemini_key,
        ollama_model=fallback_ollama,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    HuggingFace embeddings — runs locally, zero API calls.
    sentence-transformers/all-MiniLM-L6-v2 by default (40MB, fast).
    """
    config = _load_config()
    rag_config = config.get("rag", {})
    model_name = rag_config.get(
        "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
    )
    logger.debug("Initializing embedding model: %s", model_name)
    return HuggingFaceEmbeddings(model_name=model_name)


def get_traced_llm(task_type: str, run_name: str, has_image: bool = False):
    """Get LLM with optional LangSmith tracing (usually disabled)."""
    return get_llm(task_type=task_type, has_image=has_image)
