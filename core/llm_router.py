"""
DocuForge AI — LLM Router

Centralizes all LLM invocations and routes them through a single abstraction
layer. Handles model selection, fallback logic, and retry behavior. This
abstraction enables swapping the primary LLM with a single config change.
"""

import logging
import os
from pathlib import Path

import yaml
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_llm(task_type: str = "general", has_image: bool = False) -> BaseChatModel:
    """
    Get an LLM instance routed through the abstraction layer. Returns either
    ChatGoogleGenerativeAI (Gemini) if available, or falls back to ChatOllama
    (LLaMA 3) running locally. For multimodal tasks or when images are involved,
    always returns Gemini.
    """
    config = _load_config()
    llm_config = config.get("llm", {})
    primary_model = llm_config.get("primary_model", "gemini-1.5-flash")
    fallback_model = llm_config.get("fallback_model", "llama3")
    temperature = llm_config.get("temperature", 0.2)
    max_tokens = llm_config.get("max_tokens", 4096)

    api_key = os.getenv("GEMINI_API_KEY")

    if task_type == "multimodal" or has_image:
        if api_key:
            logger.info("Routing to Gemini for multimodal task (image/video support required)")
            return ChatGoogleGenerativeAI(
                model=primary_model,
                api_key=api_key,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        else:
            logger.warning("Gemini API key not available for multimodal task, falling back to Ollama (limited capability)")
            return ChatOllama(
                model=fallback_model,
                temperature=temperature,
                num_predict=max_tokens,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )

    if api_key:
        logger.info("LLM routing: using Gemini %s", primary_model)
        return ChatGoogleGenerativeAI(
            model=primary_model,
            api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    else:
        logger.warning("Gemini API key missing, falling back to local Ollama %s", fallback_model)
        return ChatOllama(
            model=fallback_model,
            temperature=temperature,
            num_predict=max_tokens,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Get an embedding model instance. Returns a HuggingFace Sentence Transformer
    specified in config, running entirely locally with no API calls.
    """
    config = _load_config()
    rag_config = config.get("rag", {})
    model_name = rag_config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")

    logger.debug("Initializing embedding model: %s", model_name)
    return HuggingFaceEmbeddings(model_name=model_name)
