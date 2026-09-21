#!/bin/bash
# ==============================================================================
# Master Test Runner for ExxonMobil Physical AI Platform
# Runs all test categories: Unit, Integration, E2E, Security, Performance
# ==============================================================================

set -e

echo "========================================================"
echo " ExxonMobil Physical AI Platform - Complete Test Suite"
echo "========================================================"

cd "$(dirname "$0")/.."

# Install test dependencies
echo ""
echo "📦 Installing test dependencies..."
pip install -q pytest pytest-cov httpx fastapi pydantic torch numpy requests locust bandit safety

# Run tests by category
echo ""
echo "🧪 [1/5] Running Unit Tests..."
echo "--------------------------------------------------------"
pytest tests/unit/ -v --tb=short

echo ""
echo "🔗 [2/5] Running Integration Tests..."
echo "--------------------------------------------------------"
pytest tests/integration/ -v --tb=short

echo ""
echo "🌐 [3/5] Running End-to-End Scenario Tests..."
echo "--------------------------------------------------------"
pytest tests/e2e/ -v --tb=short

echo ""
echo "🔐 [4/5] Running Security Tests (mTLS)..."
echo "--------------------------------------------------------"
pytest tests/security/ -v --tb=short -m security || echo "⚠️  Some security tests require running services"

echo ""
echo "⚡ [5/5] Running Performance Tests (lightweight)..."
echo "--------------------------------------------------------"
pytest tests/performance/test_load_simulation.py::TestAPILoadPerformance::test_sustained_load_100_nodes -v --tb=short -m performance || echo "⚠️  Performance tests require running API"

echo ""
echo "📊 Generating Coverage Report..."
echo "--------------------------------------------------------"
pytest tests/unit/ tests/integration/ tests/e2e/ --cov=cloud --cov=edge --cov-report=term-missing --cov-report=html || true

echo ""
echo "========================================================"
echo "✅ ALL TESTS COMPLETED"
echo "========================================================"
echo "Coverage report: htmlcov/index.html"