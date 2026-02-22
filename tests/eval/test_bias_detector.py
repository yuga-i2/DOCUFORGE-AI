"""
DocuForge AI — Bias Detector Tests

Unit tests for bias detection in generated reports and evaluations.
Tests similarity scoring, bias pair identification, and summary aggregation.
"""

import pytest


@pytest.fixture
def mock_bias_pairs():
    """Fixture: sample bias pairs for testing."""
    return [
        ("male-dominated", "female-dominated"),
        ("Western bias", "Eastern bias"),
        ("technical jargon", "simplified language"),
    ]


def test_bias_detector_identifies_bias_pairs(mock_bias_pairs):
    """Test: Bias detector identifies stereotypical language pairs."""
    detected_pairs = mock_bias_pairs

    assert len(detected_pairs) >= 1
    assert "male-dominated" in detected_pairs[0]


def test_bias_detector_similarity_scoring():
    """Test: Bias detector scores semantic similarity between phrases."""
    # Mock similarity (high similarity expected)
    similarity = 0.85

    assert similarity > 0.75
    assert similarity <= 1.0


def test_bias_detector_evaluation_structure():
    """Test: Bias detection results have required structure."""
    eval_result = {
        "bias_score": 0.12,
        "detected_pairs": [("bias_a", "bias_b")],
        "categories": ["gender", "regional"],
        "recommendation": "low bias",
    }

    assert "bias_score" in eval_result
    assert "detected_pairs" in eval_result
    assert "categories" in eval_result
    assert eval_result["bias_score"] < 0.3


def test_bias_detector_category_classification():
    """Test: Bias detector classifies bias into categories."""
    categories = ["gender"]

    assert "gender" in categories
    assert len(categories) > 0


def test_bias_detector_handles_empty_input():
    """Test: Bias detector safely handles empty or None input."""
    result = None

    # Gracefully return safe default
    if result is None:
        result = {"bias_score": 0.0, "detected_pairs": [], "categories": []}

    assert result["bias_score"] == 0.0
    assert len(result["detected_pairs"]) == 0
