"""Performance benchmarks for fraud scoring orchestrator."""

import asyncio
import time
from statistics import mean, stdev
from typing import Any, Dict, List

import pytest

from core.fraud.risk_scoring_orchestrator import RiskScoringOrchestrator
from core.interfaces.detection_plugin import (
    DetectionPlugin,
    DetectionResult,
    RiskSignal,
)


class BenchmarkPlugin(DetectionPlugin):
    """Plugin for benchmarking with configurable processing time."""

    def __init__(self, plugin_id: str, processing_delay_ms: float = 1.0) -> None:
        self.plugin_id = plugin_id
        self.processing_delay = processing_delay_ms / 1000.0  # Convert to seconds

    def get_metadata(self) -> Dict[str, str]:
        return {
            "id": self.plugin_id,
            "name": f"Benchmark Plugin {self.plugin_id}",
            "version": "1.0.0",
        }

    async def analyze(self, listing: Dict[str, Any]) -> DetectionResult:
        # Simulate processing time
        await asyncio.sleep(self.processing_delay)

        return DetectionResult(
            plugin_id=self.plugin_id,
            signals=[
                RiskSignal(
                    signal_type="test_signal",
                    score=0.5,
                    confidence=0.8,
                    reason="Benchmark signal",
                )
            ],
            overall_score=0.5,
            processing_time_ms=self.processing_delay * 1000,
        )

    def get_weight(self) -> float:
        return 1.0


async def run_benchmark(
    num_plugins: int, plugin_delay_ms: float, num_iterations: int = 100
) -> Dict[str, Any]:
    """Run benchmark with specified configuration.

    Args:
        num_plugins: Number of detection plugins
        plugin_delay_ms: Processing delay per plugin in milliseconds
        num_iterations: Number of iterations to run

    Returns:
        Dictionary with benchmark results
    """
    # Create orchestrator with plugins
    plugins: List[DetectionPlugin] = [
        BenchmarkPlugin(f"plugin-{i}", plugin_delay_ms) for i in range(num_plugins)
    ]
    orchestrator = RiskScoringOrchestrator(detection_plugins=plugins)

    # Sample listing
    listing = {
        "listing_id": "benchmark-test",
        "price": 1000000,
        "location": "Test City",
    }

    # Warm up
    await orchestrator.run(listing)

    # Run benchmark
    times = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        result = await orchestrator.run(listing)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times.append(elapsed)

    return {
        "num_plugins": num_plugins,
        "plugin_delay_ms": plugin_delay_ms,
        "iterations": num_iterations,
        "mean_ms": mean(times),
        "stdev_ms": stdev(times) if len(times) > 1 else 0,
        "min_ms": min(times),
        "max_ms": max(times),
        "p50_ms": sorted(times)[len(times) // 2],
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "p99_ms": sorted(times)[int(len(times) * 0.99)],
    }


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for fraud scoring."""

    async def test_benchmark_single_plugin_fast(self) -> None:
        """Benchmark with single fast plugin."""
        result = await run_benchmark(
            num_plugins=1, plugin_delay_ms=1.0, num_iterations=100
        )

        print(f"\n=== Single Plugin (1ms delay) ===")
        print(f"Mean: {result['mean_ms']:.2f}ms")
        print(f"StdDev: {result['stdev_ms']:.2f}ms")
        print(f"P50: {result['p50_ms']:.2f}ms")
        print(f"P95: {result['p95_ms']:.2f}ms")
        print(f"P99: {result['p99_ms']:.2f}ms")

        # Overhead should be minimal (< 5ms for single plugin)
        assert result["mean_ms"] < 10.0

    async def test_benchmark_multiple_plugins_concurrent(self) -> None:
        """Benchmark with multiple plugins running concurrently."""
        result = await run_benchmark(
            num_plugins=5, plugin_delay_ms=10.0, num_iterations=50
        )

        print(f"\n=== 5 Plugins Concurrent (10ms delay each) ===")
        print(f"Mean: {result['mean_ms']:.2f}ms")
        print(f"StdDev: {result['stdev_ms']:.2f}ms")
        print(f"P50: {result['p50_ms']:.2f}ms")
        print(f"P95: {result['p95_ms']:.2f}ms")

        # With concurrent execution, should be ~10ms + overhead, not 50ms
        # Allow some variance for system scheduling
        assert (
            result["mean_ms"] < 25.0
        ), f"Concurrent execution too slow: {result['mean_ms']:.2f}ms"

    async def test_benchmark_many_plugins(self) -> None:
        """Benchmark with many plugins to test scalability."""
        result = await run_benchmark(
            num_plugins=20, plugin_delay_ms=5.0, num_iterations=30
        )

        print(f"\n=== 20 Plugins Concurrent (5ms delay each) ===")
        print(f"Mean: {result['mean_ms']:.2f}ms")
        print(f"StdDev: {result['stdev_ms']:.2f}ms")
        print(f"P95: {result['p95_ms']:.2f}ms")

        # Should still be fast with concurrent execution
        assert result["mean_ms"] < 50.0

    async def test_benchmark_no_plugins(self) -> None:
        """Benchmark with no plugins (edge case)."""
        orchestrator = RiskScoringOrchestrator()
        listing = {"listing_id": "test"}

        times = []
        for _ in range(100):
            start = time.perf_counter()
            await orchestrator.run(listing)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        mean_time = mean(times)
        print(f"\n=== No Plugins (edge case) ===")
        print(f"Mean: {mean_time:.2f}ms")

        # Should be extremely fast with no plugins
        assert mean_time < 1.0


@pytest.mark.asyncio
async def test_compare_sequential_vs_concurrent() -> None:
    """Compare sequential vs concurrent plugin execution."""
    num_plugins = 5
    plugin_delay_ms = 10.0

    # Concurrent (actual implementation)
    concurrent_result = await run_benchmark(
        num_plugins=num_plugins, plugin_delay_ms=plugin_delay_ms, num_iterations=20
    )

    # Calculate expected sequential time
    expected_sequential_ms = num_plugins * plugin_delay_ms

    print(f"\n=== Sequential vs Concurrent Comparison ===")
    print(f"Expected Sequential: {expected_sequential_ms:.2f}ms")
    print(f"Actual Concurrent: {concurrent_result['mean_ms']:.2f}ms")
    print(f"Speedup: {expected_sequential_ms / concurrent_result['mean_ms']:.2f}x")

    # Concurrent should be significantly faster than sequential
    # (at least 2x speedup with 5 plugins)
    assert concurrent_result["mean_ms"] < expected_sequential_ms / 2


if __name__ == "__main__":
    """Run benchmarks directly."""

    async def run_all_benchmarks() -> None:
        print("=" * 60)
        print("Fraud Scoring Orchestrator Performance Benchmarks")
        print("=" * 60)

        benchmarks = [
            ("Single Fast Plugin", 1, 1.0, 100),
            ("5 Plugins Concurrent", 5, 10.0, 50),
            ("10 Plugins Concurrent", 10, 10.0, 30),
            ("20 Plugins Concurrent", 20, 5.0, 20),
        ]

        results = []
        for name, num_plugins, delay, iterations in benchmarks:
            result = await run_benchmark(num_plugins, delay, iterations)
            results.append((name, result))

            print(f"\n{name}:")
            print(f"  Mean:   {result['mean_ms']:.2f}ms")
            print(f"  StdDev: {result['stdev_ms']:.2f}ms")
            print(f"  P50:    {result['p50_ms']:.2f}ms")
            print(f"  P95:    {result['p95_ms']:.2f}ms")
            print(f"  P99:    {result['p99_ms']:.2f}ms")

        print("\n" + "=" * 60)
        print("Summary Table:")
        print("=" * 60)
        print(f"{'Scenario':<30} {'Mean':<10} {'P95':<10} {'P99':<10}")
        print("-" * 60)
        for name, result in results:
            print(
                f"{name:<30} {result['mean_ms']:>8.2f}ms {result['p95_ms']:>8.2f}ms {result['p99_ms']:>8.2f}ms"
            )

    asyncio.run(run_all_benchmarks())
