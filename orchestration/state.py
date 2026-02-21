"""
DocuForge AI — Shared LangGraph State Schema

This module defines the single source of truth for all data passed between
agents in the DocuForge pipeline. All agents read from and write to this
state object exclusively — no direct agent-to-agent communication is allowed.
"""

import operator
from typing import Annotated, Optional
from typing_extensions import TypedDict
from models.agent_models import AnalysisResult


class DocuForgeState(TypedDict):
    """
    Central state object for the DocuForge LangGraph pipeline.

    Every field must be declared here before any agent can use it.
    Annotated fields with operator.add are append-only lists — each agent
    adds to them without overwriting previous entries.
    """

    query: str
    uploaded_file_path: str
    file_format: str
    ingested_text: str
    retrieved_chunks: list[str]
    web_context: str
    analysis_result: Optional[AnalysisResult]
    draft_report: str
    verified_report: str
    hallucination_score: float
    faithfulness_score: float
    routing_decision: str
    reflection_count: int
    agent_trace: Annotated[list[str], operator.add]
    error_log: Annotated[list[str], operator.add]
    session_id: str
