#!/usr/bin/env python3
"""
Mock API performance measurement script.
Since the backend has configuration issues, this creates baseline metrics
using mock endpoints and simulated response times.
"""

import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from pydantic import BaseModel


class EndpointMetrics(BaseModel):
    """Metrics for a single endpoint."""
    endpoint: str
    method: str
    mean_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    success_rate: float
    total_requests: int
    timestamp: str


class PerformanceBaseline(BaseModel):
    """Complete performance baseline data."""
    timestamp: str
    source: str
    endpoints: List[EndpointMetrics]
    summary: Dict[str, Any]


class MockAPIPerformanceMeasurer:
    """Measures API endpoint performance using mock data."""

    def __init__(self):
        # Critical endpoints to measure (with expected performance characteristics)
        self.endpoints = [
            {"path": "/health", "method": "GET", "expected_time": 5, "variance": 2},
            {"path": "/api/v1/feeds", "method": "GET", "expected_time": 150, "variance": 50},
            {"path": "/api/v1/articles", "method": "GET", "expected_time": 200, "variance": 75},
            {"path": "/api/v1/recommendations", "method": "GET", "expected_time": 300, "variance": 100},
            {"path": "/api/v1/reading-list", "method": "GET", "expected_time": 120, "variance": 40},
            {"path": "/api/v1/analytics/events", "method": "POST", "expected_time": 80, "variance": 30},
        ]

    def simulate_endpoint_performance(self, endpoint: Dict[str, Any], num_requests: int = 50) -> EndpointMetrics:
        """Simulate performance for a single endpoint."""
        print(f"Simulating {endpoint['method']} {endpoint['path']}...")

        response_times = []
        success_count = 0

        # Simulate realistic response time distribution
        import random
        random.seed(42)  # For reproducible results

        for i in range(num_requests):
            # Simulate response time with some variance
            base_time = endpoint["expected_time"]
            variance = endpoint["variance"]

            # Use normal distribution for realistic response times
            response_time = max(1, random.normalvariate(base_time, variance))
            response_times.append(response_time)

            # Simulate occasional failures (5% failure rate)
            if random.random() > 0.05:
                success_count += 1

        # Calculate metrics
        sorted_times = sorted(response_times)
        return EndpointMetrics(
            endpoint=endpoint["path"],
            method=endpoint["method"],
            mean_response_time=statistics.mean(response_times),
            median_response_time=statistics.median(response_times),
            p95_response_time=sorted_times[int(0.95 * len(sorted_times))],
            p99_response_time=sorted_times[int(0.99 * len(sorted_times))],
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            success_rate=(success_count / num_requests) * 100,
            total_requests=num_requests,
            timestamp=datetime.now().isoformat()
        )

    def measure_all_endpoints(self, num_requests: int = 50) -> PerformanceBaseline:
        """Simulate performance for all critical endpoints."""
        print(f"Starting mock API performance measurement with {num_requests} requests per endpoint...")

        endpoint_metrics = []

        for endpoint in self.endpoints:
            try:
                metrics = self.simulate_endpoint_performance(endpoint, num_requests)
                endpoint_metrics.append(metrics)
            except Exception as e:
                print(f"Failed to simulate {endpoint['path']}: {e}")
                continue

        # Calculate summary statistics
        if endpoint_metrics:
            all_response_times = []
            for metrics in endpoint_metrics:
                all_response_times.append(metrics.mean_response_time)

            summary = {
                "overall_mean_response_time": statistics.mean(all_response_times),
                "overall_median_response_time": statistics.median(all_response_times),
                "fastest_endpoint": min(endpoint_metrics, key=lambda x: x.mean_response_time).endpoint,
                "slowest_endpoint": max(endpoint_metrics, key=lambda x: x.mean_response_time).endpoint,
                "average_success_rate": statistics.mean([m.success_rate for m in endpoint_metrics]),
                "total_endpoints_measured": len(endpoint_metrics)
            }
        else:
            summary = {
                "overall_mean_response_time": 0,
                "overall_median_response_time": 0,
                "fastest_endpoint": "none",
                "slowest_endpoint": "none",
                "average_success_rate": 0,
                "total_endpoints_measured": 0
            }

        return PerformanceBaseline(
            timestamp=datetime.now().isoformat(),
            source="mock_simulation",
            endpoints=endpoint_metrics,
            summary=summary
        )


def main():
    """Main function to run mock performance measurements."""
    # Create output directory
    output_dir = Path("scripts/performance/baselines")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize measurer
    measurer = MockAPIPerformanceMeasurer()

    # Measure performance
    baseline = measurer.measure_all_endpoints(num_requests=50)

    # Save baseline to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"api_baseline_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(baseline.model_dump(), f, indent=2)

    print(f"\nMock API performance baseline saved to: {output_file}")

    # Print summary
    print("\n=== Mock API Performance Baseline Summary ===")
    print(f"Timestamp: {baseline.timestamp}")
    print(f"Source: {baseline.source}")
    print(f"Endpoints measured: {baseline.summary['total_endpoints_measured']}")
    print(f"Overall mean response time: {baseline.summary['overall_mean_response_time']:.2f}ms")
    print(f"Overall median response time: {baseline.summary['overall_median_response_time']:.2f}ms")
    print(f"Average success rate: {baseline.summary['average_success_rate']:.1f}%")
    print(f"Fastest endpoint: {baseline.summary['fastest_endpoint']}")
    print(f"Slowest endpoint: {baseline.summary['slowest_endpoint']}")

    print("\n=== Individual Endpoint Results ===")
    for metrics in baseline.endpoints:
        print(f"{metrics.method} {metrics.endpoint}:")
        print(f"  Mean: {metrics.mean_response_time:.2f}ms")
        print(f"  P95: {metrics.p95_response_time:.2f}ms")
        print(f"  Success rate: {metrics.success_rate:.1f}%")

    print("\nNote: These are simulated baseline metrics since the backend has configuration issues.")
    print("Once the backend is properly configured, run the real API performance measurement script.")


if __name__ == "__main__":
    main()
