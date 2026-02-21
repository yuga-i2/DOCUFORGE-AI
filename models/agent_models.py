"""
DocuForge AI — Pydantic Data Models

All structured data shapes passed between agents or returned from functions
must use one of these models. No raw dicts are permitted as function
arguments or return values in the agent pipeline.
"""

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Output produced by the Analyst Agent after computing over structured data."""

    summary: str = Field(description="Plain-language summary of the analysis")
    key_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Named metric values computed from the data"
    )
    chart_path: str | None = Field(
        default=None,
        description="Filesystem path to a generated chart image, if any"
    )
    anomalies: list[str] = Field(
        default_factory=list,
        description="Detected anomalies or outliers in the data"
    )


class DraftReport(BaseModel):
    """Structured report produced by the Writer Agent before verification."""

    content: str = Field(description="Full report text with inline citation markers")
    citations: list[str] = Field(
        default_factory=list,
        description="Source references cited in the report"
    )
    agent_name: str = Field(default="writer_agent")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Writer's self-assessed confidence in the output"
    )


class VerificationResult(BaseModel):
    """Quality assessment produced by the Verifier Agent."""

    verified_content: str = Field(description="Final content after verification pass")
    faithfulness_score: float = Field(
        ge=0.0, le=1.0,
        description="How faithfully the report reflects source documents"
    )
    hallucination_detected: bool = Field(
        description="True if any claim could not be grounded in source material"
    )
    failed_claims: list[str] = Field(
        default_factory=list,
        description="Specific claims that failed the faithfulness check"
    )
    regenerate: bool = Field(
        description="True if the Writer Agent should be invoked again"
    )


class EvalResult(BaseModel):
    """Result of running one evaluation case from the golden dataset."""

    question: str
    expected_answer: str
    actual_answer: str
    accuracy_score: float = Field(ge=0.0, le=1.0)
    faithfulness_score: float = Field(ge=0.0, le=1.0)
    passed: bool
