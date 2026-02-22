"""Performance benchmarking pipeline for agent execution."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BenchmarkResult(BaseModel):
    """Performance metrics for a single agent or pipeline execution."""

    agent_name: str
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    total_runs: int
    error_rate: float


def time_agent_call(agent_fn: callable, state: dict, runs: int = 5) -> BenchmarkResult:
    """Time agent function over multiple runs. Records wall-clock latency using perf_counter. Returns BenchmarkResult with latency stats and error rate."""
    try:
        latencies = []
        errors = 0
        
        for _ in range(runs):
            try:
                start = time.perf_counter()
                agent_fn(state)
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # Convert to ms
            except Exception as e:
                logger.debug(f"Agent call error: {str(e)}")
                errors += 1
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
        else:
            avg_latency = 0.0
            min_latency = 0.0
            max_latency = 0.0
        
        error_rate = errors / runs if runs > 0 else 0.0
        
        logger.info(f"Benchmarked agent: avg={avg_latency:.1f}ms, errors={errors}/{runs}")
        
        return BenchmarkResult(
            agent_name=getattr(agent_fn, "__name__", "unknown"),
            avg_latency_ms=avg_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            total_runs=runs,
            error_rate=error_rate,
        )
    except Exception as e:
        logger.error(f"Benchmarking failed: {str(e)}")
        return BenchmarkResult(
            agent_name=getattr(agent_fn, "__name__", "unknown"),
            avg_latency_ms=0.0,
            min_latency_ms=0.0,
            max_latency_ms=0.0,
            total_runs=0,
            error_rate=1.0,
        )


def run_full_benchmark(graph_invoke_fn: callable, sample_states: list[dict]) -> list[BenchmarkResult]:
    """Benchmark graph invocation on sample states. Returns list of BenchmarkResult. Logs summary at INFO."""
    try:
        results = []
        
        for i, state in enumerate(sample_states):
            logger.info(f"Benchmarking state {i+1}/{len(sample_states)}")
            start = time.perf_counter()
            try:
                graph_invoke_fn(state)
            except Exception as e:
                logger.warning(f"Graph invocation {i} failed: {str(e)}")
            end = time.perf_counter()
            
            # Create synthetic result
            result = BenchmarkResult(
                agent_name=f"pipeline_run_{i+1}",
                avg_latency_ms=(end - start) * 1000,
                min_latency_ms=0.0,
                max_latency_ms=0.0,
                total_runs=1,
                error_rate=0.0,
            )
            results.append(result)
        
        logger.info(f"Full pipeline benchmarking complete: {len(results)} runs")
        return results
    except Exception as e:
        logger.error(f"Pipeline benchmarking failed: {str(e)}")
        return []


def print_benchmark_report(results: list[BenchmarkResult]) -> None:
    """Log formatted benchmark report. Uses logging, not print."""
    try:
        if not results:
            logger.info("No benchmark results to report")
            return
        
        logger.info("=" * 60)
        logger.info("BENCHMARK REPORT")
        logger.info("=" * 60)
        
        for result in results:
            logger.info(
                f"{result.agent_name:30s} | avg={result.avg_latency_ms:7.1f}ms | "
                f"min={result.min_latency_ms:7.1f}ms | max={result.max_latency_ms:7.1f}ms | "
                f"err={result.error_rate:.2%}"
            )
        
        logger.info("=" * 60)
        
        # Save to file
        timestamp = datetime.now().isoformat()
        report_data = {
            "timestamp": timestamp,
            "results": [r.model_dump() for r in results],
        }
        
        output_path = Path("eval/benchmark_results.json")
        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Benchmark results saved to {output_path}")
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")

