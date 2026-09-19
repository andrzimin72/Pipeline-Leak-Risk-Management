# ==============================================================================
# Pipeline Leak Risk Management Physical AI Platform - Makefile
# ==============================================================================

.PHONY: help install test lint demo up down train export clean

## help: Show this help message
help:
	@echo "Pipeline Leak Risk Management Physical AI Platform - Available Commands:"
	@echo ""
	@grep -E '^## [a-zA-Z_-]+:.*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = "^## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

## install: Install all Python dependencies
install:
	pip install -r requirements.txt
	@echo "✅ Dependencies installed."

## test: Run the complete test suite (Unit, Integration, E2E, Security)
test:
	pytest tests/ -v --cov=cloud --cov=edge --cov-report=term-missing
	@echo "✅ Tests complete."

## lint: Run code formatting and linting checks
lint:
	black . --check
	flake8 . --max-line-length=120
	isort . --check-only
	@echo "✅ Linting complete."

## demo: Run the interactive executive demonstration script
demo:
	python demo_mustang_segment_v3.py

## up: Start the full stack using Docker Compose
up:
	docker-compose up --build -d
	@echo "🚀 Platform started. Dashboard: http://localhost:8501"

## down: Stop the Docker Compose stack
down:
	docker-compose down
	@echo "🛑 Platform stopped."

## train: Train the Sentinel Transformer model (Cloud)
train:
	python cloud/training/train_sentinel_transformer.py

## export: Export PyTorch model to ONNX/TensorRT for Jetson
export:
	python cloud/deployment/export_to_jetson.py

## clean: Remove Python cache and build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage *.egg-info
	@echo "🧹 Project cleaned."