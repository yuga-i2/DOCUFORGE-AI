"""Unit tests for the accuracy evaluator."""

from unittest.mock import patch, MagicMock
import json

from core.eval.accuracy_evaluator import load_golden_dataset, score_single_response, run_accuracy_evaluation


def test_load_golden_dataset_returns_list():
    """Test that load_golden_dataset returns list of GoldenQAPair."""
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps([
            {
                "id": "eval_001",
                "question": "What is Q4 revenue?",
                "expected_answer": "$15.2M",
                "document_source": "report.pdf",
                "category": "factual",
                "difficulty": "easy"
            }
        ])
        
        with patch("pathlib.Path.exists", return_value=True):
            result = load_golden_dataset()
        
        assert isinstance(result, list)
        assert len(result) > 0


def test_score_single_response_range():
    """Test that score_single_response returns float in valid range."""
    llm = MagicMock()
    response = MagicMock()
    response.content = '{"score": 0.85, "reasoning": "good match"}'
    llm.invoke.return_value = response
    
    score = score_single_response("expected", "actual", llm)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_score_on_llm_failure():
    """Test that score_single_response returns 0.0 on LLM failure."""
    llm = MagicMock()
    llm.invoke.side_effect = Exception("LLM error")
    
    score = score_single_response("expected", "actual", llm)
    
    assert score == 0.0


def test_run_accuracy_evaluation_structure():
    """Test that run_accuracy_evaluation returns correct structure."""
    with patch("core.eval.accuracy_evaluator.load_golden_dataset") as mock_load:
        
        mock_load.return_value = []
        
        responses = [
            {"id": "eval_001", "question": "Q4 revenue?", "actual_answer": "$15M"}
        ]
        
        result = run_accuracy_evaluation(responses)
        
        assert isinstance(result, dict)
        assert "mean_accuracy" in result
        assert "min_accuracy" in result
        assert "max_accuracy" in result
        assert "passed_threshold" in result
        assert "total_evaluated" in result
