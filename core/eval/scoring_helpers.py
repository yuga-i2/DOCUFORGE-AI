"""
DocuForge AI — Scoring Utilities

Shared helper functions for computing evaluation metrics across accuracy,
faithfulness, hallucination, and bias evaluators.
"""

import logging
import re
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from docuforge_config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "docuforge_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    Compute Jaccard similarity between two texts by tokenizing to lowercase word sets.
    Returns intersection over union. Returns 0.0 if both texts are empty.
    """
    words_a = set(re.findall(r"\b\w+\b", text_a.lower()))
    words_b = set(re.findall(r"\b\w+\b", text_b.lower()))

    if not words_a and not words_b:
        return 0.0

    intersection = len(words_a & words_b)
    union = len(words_a | words_b)

    return intersection / union if union > 0 else 0.0


def normalise_score(raw: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a float value to the specified range [min_val, max_val]."""
    return max(min_val, min(max_val, raw))


def weighted_average(scores: list[float], weights: list[float]) -> float:
    """
    Compute the weighted mean of scores. Raises ValueError if list lengths differ
    or if weights sum to zero.
    """
    if len(scores) != len(weights):
        raise ValueError(f"Scores ({len(scores)}) and weights ({len(weights)}) length mismatch")

    weight_sum = sum(weights)
    if weight_sum == 0:
        raise ValueError("Weights sum to zero — cannot compute weighted average")

    return sum(s * w for s, w in zip(scores, weights)) / weight_sum


def format_score_for_display(score: float, label: str) -> str:
    """
    Format a score for display with label and PASS/FAIL status based on config threshold.
    Example: "Faithfulness: 0.923 (PASS)" or "Accuracy: 0.643 (FAIL)".
    """
    config = _load_config()
    threshold = config.get("eval", {}).get("min_accuracy_threshold", 0.80)

    status = "PASS" if score >= threshold else "FAIL"
    return f"{label}: {score:.3f} ({status})"


def aggregate_eval_summary(eval_results: list[dict]) -> dict[str, float | int | bool]:
    """
    Aggregate evaluation results into a summary dict with mean scores, pass/fail
    counts, and overall success status. Expects each result dict to have
    accuracy_score and faithfulness_score keys.
    """
    if not eval_results:
        return {
            "mean_accuracy": 0.0,
            "mean_faithfulness": 0.0,
            "total": 0,
            "passed_count": 0,
            "failed_count": 0,
            "overall_pass": False,
        }

    config = _load_config()
    threshold = config.get("eval", {}).get("min_accuracy_threshold", 0.80)

    accuracy_scores = [r.get("accuracy_score", 0.0) for r in eval_results]
    faithfulness_scores = [r.get("faithfulness_score", 0.0) for r in eval_results]

    mean_accuracy = sum(accuracy_scores) / len(accuracy_scores)
    mean_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)

    passed_count = sum(1 for s in accuracy_scores if s >= threshold)
    failed_count = len(eval_results) - passed_count

    overall_pass = mean_accuracy >= threshold

    logger.info(
        "Eval summary: mean_accuracy=%.3f, mean_faithfulness=%.3f, "
        "passed=%d/%d, overall_pass=%s",
        mean_accuracy,
        mean_faithfulness,
        passed_count,
        len(eval_results),
        overall_pass,
    )

    return {
        "mean_accuracy": mean_accuracy,
        "mean_faithfulness": mean_faithfulness,
        "total": len(eval_results),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "overall_pass": overall_pass,
    }
