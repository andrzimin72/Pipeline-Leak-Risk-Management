# tests/performance/test_load_simulation.py
"""
Performance and Load Tests for the Pipeline Leak Risk Management Physical AI Platform.
Simulates 1,000+ edge nodes sending concurrent telemetry to the Cloud API.
Uses Locust for realistic load simulation and pytest for threshold validation.

Install: pip install locust pytest-benchmark
"""

import pytest
import time
import json
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# ==============================================================================
# Configuration
# ==============================================================================
API_BASE_URL = os.getenv("PERF_TEST_API_URL", "http://localhost:8000")
NUM_VIRTUAL_NODES = int(os.getenv("PERF_TEST_NODES", "1000"))
REQUESTS_PER_NODE = int(os.getenv("PERF_TEST_REQUESTS", "10"))
CONCURRENCY = int(os.getenv("PERF_TEST_CONCURRENCY", "100"))


def generate_mock_payload(node_id: int) -> dict:
    """Generates a realistic 11-modal fusion payload."""
    import random
    return {
        "event_id": f"perf-event-{node_id}-{random.randint(1000, 9999)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "node_id": f"NODE-{node_id:04d}",
        "scores": {
            "acoustic": random.uniform(0.0, 0.3),
            "pressure": random.uniform(0.0, 0.4),
            "coriolis_mass": random.uniform(0.0, 0.2),
            "fiber_dts": random.uniform(0.0, 0.3),
            "point_temp": random.uniform(0.0, 0.2),
            "soil_moisture": random.uniform(0.0, 0.3),
            "capacitance": random.uniform(0.0, 0.2),
            "vibration": random.uniform(0.0, 0.4),
            "corrosion": random.uniform(0.0, 0.3),
            "standard_flow": random.uniform(0.0, 0.2),
            "physics_residual": random.uniform(0.0, 0.5)
        },
        "final_confidence": random.uniform(0.5, 0.99),
        "decision": random.choice(["SAFE", "ANOMALY_DETECTED", "CRITICAL_FAILURE"]),
        "action_required": "MONITOR"
    }


class LoadTestResult:
    """Aggregates results from load test runs."""
    def __init__(self):
        self.successes = 0
        self.failures = 0
        self.latencies = []
        self.errors = []

    @property
    def total_requests(self):
        return self.successes + self.failures

    @property
    def success_rate(self):
        if self.total_requests == 0:
            return 0.0
        return (self.successes / self.total_requests) * 100

    @property
    def avg_latency_ms(self):
        if not self.latencies:
            return 0.0
        return statistics.mean(self.latencies) * 1000

    @property
    def p95_latency_ms(self):
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx] * 1000

    @property
    def p99_latency_ms(self):
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)] * 1000

    @property
    def requests_per_second(self):
        if not self.latencies:
            return 0.0
        total_time = sum(self.latencies)
        return self.total_requests / total_time if total_time > 0 else 0.0


def send_request(node_id: int, result: LoadTestResult):
    """Sends a single request and records metrics."""
    payload = generate_mock_payload(node_id)
    start = time.time()
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/alerts",
            json=payload,
            timeout=10
        )
        latency = time.time() - start
        result.latencies.append(latency)
        
        if response.status_code in [200, 201, 202]:
            result.successes += 1
        else:
            result.failures += 1
            result.errors.append(f"Node {node_id}: HTTP {response.status_code}")
    except Exception as e:
        latency = time.time() - start
        result.latencies.append(latency)
        result.failures += 1
        result.errors.append(f"Node {node_id}: {str(e)}")


# ==============================================================================
# Load Test Scenarios
# ==============================================================================
class TestAPILoadPerformance:
    """Load tests for the FastAPI Cloud Backend."""

    @pytest.mark.performance
    def test_sustained_load_100_nodes(self):
        """
        GIVEN: 100 virtual edge nodes
        WHEN: Each sends 10 requests concurrently
        THEN: Success rate should be >= 99% and avg latency < 500ms
        """
        result = LoadTestResult()
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for node_id in range(100):
                for _ in range(10):
                    futures.append(executor.submit(send_request, node_id, result))
            
            for future in as_completed(futures):
                future.result()  # Raise any exceptions
        
        print(f"\n--- Load Test: 100 Nodes ---")
        print(f"Total Requests: {result.total_requests}")
        print(f"Success Rate: {result.success_rate:.2f}%")
        print(f"Avg Latency: {result.avg_latency_ms:.2f}ms")
        print(f"P95 Latency: {result.p95_latency_ms:.2f}ms")
        
        assert result.success_rate >= 99.0, \
            f"Success rate too low: {result.success_rate:.2f}%"
        assert result.avg_latency_ms < 500, \
            f"Avg latency too high: {result.avg_latency_ms:.2f}ms"

    @pytest.mark.performance
    def test_peak_load_1000_nodes(self):
        """
        GIVEN: 1,000 virtual edge nodes
        WHEN: Each sends 5 requests with 100 concurrent workers
        THEN: Success rate should be >= 95% and P95 latency < 2000ms
        """
        result = LoadTestResult()
        
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = []
            for node_id in range(NUM_VIRTUAL_NODES):
                for _ in range(REQUESTS_PER_NODE):
                    futures.append(executor.submit(send_request, node_id, result))
            
            for future in as_completed(futures):
                future.result()
        
        print(f"\n--- Load Test: {NUM_VIRTUAL_NODES} Nodes ---")
        print(f"Total Requests: {result.total_requests}")
        print(f"Success Rate: {result.success_rate:.2f}%")
        print(f"Avg Latency: {result.avg_latency_ms:.2f}ms")
        print(f"P95 Latency: {result.p95_latency_ms:.2f}ms")
        print(f"P99 Latency: {result.p99_latency_ms:.2f}ms")
        print(f"RPS: {result.requests_per_second:.2f}")
        
        assert result.success_rate >= 95.0, \
            f"Success rate too low under peak load: {result.success_rate:.2f}%"
        assert result.p95_latency_ms < 2000, \
            f"P95 latency too high: {result.p95_latency_ms:.2f}ms"

    @pytest.mark.performance
    def test_burst_load_5000_nodes(self):
        """
        GIVEN: 5,000 virtual edge nodes (extreme burst scenario)
        WHEN: All send requests simultaneously
        THEN: System should not crash; success rate >= 80%
        """
        result = LoadTestResult()
        
        with ThreadPoolExecutor(max_workers=500) as executor:
            futures = [
                executor.submit(send_request, node_id, result)
                for node_id in range(5000)
            ]
            for future in as_completed(futures):
                future.result()
        
        print(f"\n--- Burst Test: 5,000 Nodes ---")
        print(f"Total Requests: {result.total_requests}")
        print(f"Success Rate: {result.success_rate:.2f}%")
        print(f"Failures: {result.failures}")
        
        assert result.success_rate >= 80.0, \
            f"System should handle burst load: {result.success_rate:.2f}%"
        assert result.failures < 1000, \
            f"Too many failures under burst: {result.failures}"


# ==============================================================================
# Locust Integration (Optional Advanced Load Testing)
# ==============================================================================
"""
For more sophisticated load testing, install and run Locust:

    pip install locust
    
Create a locustfile.py with the following content:

    from locust import HttpUser, task, between
    
    class PipelineEdgeNode(HttpUser):
        wait_time = between(1, 3)
        
        @task(8)
        def send_safe_telemetry(self):
            payload = generate_mock_payload(random.randint(1, 1000))
            payload["decision"] = "SAFE"
            self.client.post("/api/v1/alerts", json=payload)
        
        @task(2)
        def send_critical_telemetry(self):
            payload = generate_mock_payload(random.randint(1, 1000))
            payload["decision"] = "CRITICAL_FAILURE"
            self.client.post("/api/v1/alerts", json=payload)

Run with:
    locust -f tests/performance/locustfile.py --host=http://localhost:8000
    
Then open http://localhost:8089 to start the load test with a web UI.
"""
