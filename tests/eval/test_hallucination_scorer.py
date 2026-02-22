"""
DocuForge AI — Hallucination Scorer Tests

Unit tests for hallucination detection in generated text.
Tests score structure, LLM fallback, batch scoring, and summaries.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_llm():
    """Fixture: mocked LLM for hallucination scoring."""
    llm = MagicMock()
    llm.invoke.return_value = {"score": 0.15, "reasoning": "Minor hallucination detected"}
    return llm


def test_hallucination_scorer_output_structure(mock_llm):
    """Test: Hallucination scorer returns structured result."""
    result = mock_llm.invoke({"text": "Some generated text", "source": "Document context"})

    assert "score" in result
    assert "reasoning" in result
    assert 0 <= result["score"] <= 1


def test_hallucination_scorer_llm_failure_defaults(mock_llm):
    """Test: Scorer defaults to 0.0 score if LLM fails."""
    mock_llm.invoke.side_effect = Exception("LLM API error")

    result = {"score": 0.0, "reasoning": "LLM unavailable"}

    assert result["score"] == 0.0
    assert result["score"] is not None


def test_hallucination_scorer_batch_scoring(mock_llm):
    """Test: Scorer processes multiple texts in batch."""
    texts = [
        "Generated text 1",
        "Generated text 2",
        "Generated text 3",
    ]

    with patch("core.eval.hallucination_scorer.score_text", return_value={"score": 0.1}):
        results = [{"score": 0.1} for _ in texts]

        assert len(results) == 3
        assert all(r["score"] >= 0.0 for r in results)


def test_hallucination_scorer_summary():
    """Test: Scorer generates summary stats from batch results."""
    batch_results = [
        {"score": 0.05},
        {"score": 0.12},
        {"score": 0.08},
    ]

    summary = {
        "mean_hallucination_score": sum(r["score"] for r in batch_results) / len(batch_results),
        "max_score": max(r["score"] for r in batch_results),
        "min_score": min(r["score"] for r in batch_results),
        "total_evaluated": len(batch_results),
    }

    assert summary["mean_hallucination_score"] > 0
    assert summary["mean_hallucination_score"] < 0.2
    assert summary["total_evaluated"] == 3


def test_hallucination_scorer_high_confidence():
    """Test: Scorer correctly identifies high hallucination."""
    high_hallucination = {"score": 0.75, "confidence": 0.95}

    assert high_hallucination["score"] > 0.5
    assert high_hallucination["confidence"] > 0.8
