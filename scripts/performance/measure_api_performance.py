#!/usr/bin/env python3
"""
Performance measurement script for API endpoints.
Measures response times for critical endpoints and generates baseline metrics.
"""

import asyncio
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import httpx
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
    endpoints: List[EndpointMetrics]
    summary: Dict[str, Any]


class APIPerformanceMeasurer:
    """Measures API endpoint performance."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

        # Critical endpoints to measure
        self.endpoints = [
            {"path": "/health", "method": "GET"},
            {"path": "/api/v1/feeds", "method": "GET"},
            {"path": "/api/v1/articles", "method": "GET"},
            {"path": "/api/v1/recommendations", "method": "GET"},
            {"path": "/api/v1/reading-list", "method": "GET"},
            {"path": "/api/v1/analytics/events", "method": "POST"},
        ]

    async def measure_endpoint(self, endpoint: Dict[str, str], num_requests: int = 50) -> EndpointMetrics:
        """Measure performance for a single endpoint."""
        print(f"Measuring {endpoint['method']} {endpoint['path']}...")

        response_times = []
        success_count = 0

        for i in range(num_requests):
            start_time = time.perf_counter()

            try:
                if endpoint["method"] == "GET":
                    response = await self.client.get(f"{self.base_url}{endpoint['path']}")
                elif endpoint["method"] == "POST":
                    # For POST endpoints, send minimal valid data
                    test_data = self._get_test_data(endpoint["path"])
                    response = await self.client.post(
                        f"{self.base_url}{endpoint['path']}",
                        json=test_data
                    )

                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds

                response_times.append(response_time)

                if response.status_code < 400:
                    success_count += 1

            except Exception as e:
                print(f"Request {i+1} failed: {e}")
                # Still record the time for failed requests
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)

        # Calculate metrics
        if response_times:
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
        else:
            # Fallback for no successful requests
            return EndpointMetrics(
                endpoint=endpoint["path"],
                method=endpoint["method"],
                mean_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                min_response_time=0,
                max_response_time=0,
                success_rate=0,
                total_requests=num_requests,
                timestamp=datetime.now().isoformat()
            )

    def _get_test_data(self, endpoint_path: str) -> Dict[str, Any]:
        """Get test data for POST endpoints."""
        if "analytics/events" in endpoint_path:
            return {
                "event_type": "page_view",
                "user_id": "test-user",
                "metadata": {"page": "test"}
            }
        return {}

    async def measure_all_endpoints(self, num_requests: int = 50) -> PerformanceBaseline:
        """Measure performance for all critical endpoints."""
        print(f"Starting API performance measurement with {num_requests} requests per endpoint...")

        endpoint_metrics = []

        for endpoint in self.endpoints:
            try:
                metrics = await self.measure_endpoint(endpoint, num_requests)
                endpoint_metrics.append(metrics)
            except Exception as e:
                print(f"Failed to measure {endpoint['path']}: {e}")
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
            endpoints=endpoint_metrics,
            summary=summary
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main function to run performance measurements."""
    # Create output directory
    output_dir = Path("scripts/performance/baselines")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize measurer
    measurer = APIPerformanceMeasurer()

    try:
        # Measure performance
        baseline = await measurer.measure_all_endpoints(num_requests=50)

        # Save baseline to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"api_baseline_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(baseline.model_dump(), f, indent=2)

        print(f"\nPerformance baseline saved to: {output_file}")

        # Print summary
        print("\n=== API Performance Baseline Summary ===")
        print(f"Timestamp: {baseline.timestamp}")
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

    finally:
        await measurer.close()


if __name__ == "__main__":
    asyncio.run(main())
