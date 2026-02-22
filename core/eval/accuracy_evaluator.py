"""Accuracy evaluation pipeline for golden test dataset."""

import json
import logging
from pathlib import Path

from core.llm_router import get_llm
from models.agent_models import GoldenQAPair

logger = logging.getLogger(__name__)


def load_golden_dataset(path: str | None = None) -> list[GoldenQAPair]:
    """Load golden dataset from JSON file. Uses eval/test_dataset.json if path not provided. Returns list of GoldenQAPair. On failure, returns empty list."""
    try:
        if path is None:
            path = Path("eval/test_dataset.json")
        else:
            path = Path(path)
        
        with open(path) as f:
            data = json.load(f)
        
        pairs = [GoldenQAPair(**item) for item in data]
        logger.info(f"Loaded {len(pairs)} golden QA pairs")
        return pairs
    except Exception as e:
        logger.error(f"Failed to load golden dataset: {str(e)}")
        return []


def score_single_response(expected: str, actual: str, llm) -> float:
    """Score how well actual answer matches expected answer (0.0-1.0). Prompts LLM for evaluation. Returns score float, or 0.0 on parse failure. Logs result at DEBUG level."""
    try:
        prompt = f"""Score how well the actual answer matches the expected answer.

EXPECTED: {expected}

ACTUAL: {actual}

Return ONLY JSON: {{"score": 0.85, "reasoning": "string"}}"""
        
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        parsed = json.loads(response_text)
        score = float(parsed.get("score", 0.0))
        
        logger.debug(f"Response score: {score:.2f}")
        return score
    except Exception as e:
        logger.debug(f"Score parse failed: {str(e)}")
        return 0.0


def run_accuracy_evaluation(responses: list[dict]) -> dict[str, float]:
    """Run accuracy evaluation on responses. Each response dict has: id, question, actual_answer. Returns dict with mean_accuracy, min_accuracy, max_accuracy, passed_threshold, total_evaluated. Logs each score at DEBUG, summary at INFO."""
    try:
        dataset = load_golden_dataset()
        if not dataset:
            return {
                "mean_accuracy": 0.0,
                "min_accuracy": 0.0,
                "max_accuracy": 0.0,
                "passed_threshold": 0,
                "total_evaluated": 0,
            }
        
        llm = get_llm("evaluation")
        scores = []
        
        for response in responses:
            # Find matching golden pair
            matching_pair = None
            for pair in dataset:
                if pair.question.lower() in response.get("question", "").lower():
                    matching_pair = pair
                    break
            
            if not matching_pair:
                logger.warning(f"No matching golden pair for: {response.get('question')}")
                continue
            
            actual = response.get("actual_answer", "")
            score = score_single_response(matching_pair.expected_answer, actual, llm)
            scores.append(score)
        
        if not scores:
            return {
                "mean_accuracy": 0.0,
                "min_accuracy": 0.0,
                "max_accuracy": 0.0,
                "passed_threshold": 0,
                "total_evaluated": 0,
            }
        
        mean_acc = sum(scores) / len(scores)
        min_acc = min(scores)
        max_acc = max(scores)
        passed = sum(1 for s in scores if s >= 0.8)
        
        logger.info(
            f"Accuracy evaluation: mean={mean_acc:.3f}, min={min_acc:.3f}, max={max_acc:.3f}, passed={passed}/{len(scores)}"
        )
        
        return {
            "mean_accuracy": mean_acc,
            "min_accuracy": min_acc,
            "max_accuracy": max_acc,
            "passed_threshold": passed,
            "total_evaluated": len(scores),
        }
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return {
            "mean_accuracy": 0.0,
            "min_accuracy": 0.0,
            "max_accuracy": 0.0,
            "passed_threshold": 0,
            "total_evaluated": 0,
        }

