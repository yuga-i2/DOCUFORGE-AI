"""
DocuForge AI — Analyst Agent

Computes statistics, identifies patterns, and generates visualizations
from structured data. Produces quantitative analysis results that supplement
qualitative document insights.
"""

import json
import logging
import re
from io import StringIO

import pandas as pd

from core.llm_router import get_llm
from models.agent_models import AnalysisResult
from orchestration.state import DocuForgeState

logger = logging.getLogger(__name__)


def _extract_table_from_chunks(chunks: list[str]) -> pd.DataFrame | None:
    """
    Attempt to extract tabular data from retrieved chunks. Looks for markdown
    tables or structured lists that can be converted to DataFrames.
    """
    for chunk in chunks:
        if "|" in chunk and "-" in chunk:
            try:
                # Try to parse markdown table
                lines = chunk.split("\n")
                table_lines = [l for l in lines if "|" in l]
                if len(table_lines) > 2:
                    df_text = "\n".join(table_lines)
                    df = pd.read_csv(StringIO(df_text), sep="|", skipinitialspace=True)
                    df = df.dropna(axis=1, how="all")
                    if len(df) > 0:
                        return df
            except Exception:
                continue
    return None


def _extract_numbers_from_chunks(chunks: list[str]) -> list[float]:
    """
    Extract all numeric values from chunks using regex. Returns floats for
    basic statistical analysis.
    """
    numbers = []
    for chunk in chunks:
        matches = re.findall(r"-?\d+\.?\d*", chunk)
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                pass
    return numbers


def _compute_statistics(numbers: list[float]) -> dict[str, float]:
    """
    Compute basic descriptive statistics from a list of numbers.
    Returns dict with mean, median, std, min, max.
    """
    if not numbers:
        return {}

    series = pd.Series(numbers)
    return {
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()),
        "min": float(series.min()),
        "max": float(series.max()),
        "count": int(len(numbers)),
    }


def analyst_agent(state: DocuForgeState) -> dict:
    """
    Analyze retrieved document chunks to extract structured insights. Computes
    statistics from numeric data and identifies patterns. Returns AnalysisResult
    with metrics and summary. On failure, logs error and returns empty result.
    """
    retrieved_chunks = state.get("retrieved_chunks", [])
    query = state.get("query", "").strip()

    if not retrieved_chunks:
        logger.warning("No retrieved chunks available for analysis")
        return {
            "analysis_result": AnalysisResult(
                summary="No quantitative data available in document.",
                key_metrics={},
                chart_path=None,
                anomalies=[],
            ),
            "agent_trace": ["analyst_agent: no retrieved chunks available"],
        }

    try:
        # Attempt to extract tabular data
        df = _extract_table_from_chunks(retrieved_chunks)

        # Extract numeric values as fallback
        numbers = _extract_numbers_from_chunks(retrieved_chunks)
        metrics = _compute_statistics(numbers)

        anomalies = []
        if "anomal" in query.lower() or "outlier" in query.lower():
            if numbers and len(numbers) > 1:
                series = pd.Series(numbers)
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                anomalies = [str(n) for n in numbers if n < lower_bound or n > upper_bound]

        summary_parts = []
        if df is not None:
            summary_parts.append(f"Found table with {len(df)} rows and {len(df.columns)} columns.")
        if metrics:
            summary_parts.append(f"Extracted {metrics.get('count', 0)} numeric values with mean {metrics.get('mean', 0):.2f}.")
        if anomalies:
            summary_parts.append(f"Detected {len(anomalies)} anomalous values.")

        summary = " ".join(summary_parts) if summary_parts else "Analysis complete but no structured data found."

        trace_entry = f"analyst_agent: extracted {len(metrics)} metrics, {len(anomalies)} anomalies, processed {len(retrieved_chunks)} chunks"
        logger.info(trace_entry)

        return {
            "analysis_result": AnalysisResult(
                summary=summary,
                key_metrics=metrics,
                chart_path=None,
                anomalies=anomalies,
            ),
            "agent_trace": [trace_entry],
        }
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(error_msg)
        return {
            "analysis_result": AnalysisResult(
                summary=f"Analysis encountered an error: {error_msg}",
                key_metrics={},
                chart_path=None,
                anomalies=[],
            ),
            "error_log": [error_msg],
            "agent_trace": [f"analyst_agent: {error_msg}"],
        }
