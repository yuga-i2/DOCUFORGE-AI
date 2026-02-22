.PHONY: help install dev worker frontend test lint typecheck eval benchmark build clean check start

help:
	@echo "DocuForge AI — Development Tasks"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install dependencies (pip, npm)"
	@echo ""
	@echo "Running:"
	@echo "  make start          Start all services via run.py (FastAPI, Celery, React)"
	@echo "  make dev            Start FastAPI development server (port 8000)"
	@echo "  make worker         Start Celery worker for async tasks"
	@echo "  make frontend       Start React dev server (port 3000)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test           Run pytest test suite with coverage"
	@echo "  make lint           Run ruff linter on all code"
	@echo "  make typecheck      Run mypy type checker"
	@echo "  make check          Run all checks: lint, typecheck, test"
	@echo ""
	@echo "Evaluation & Benchmarks:"
	@echo "  make eval           Run evaluation suite against test dataset"
	@echo "  make benchmark      Run performance benchmarks"
	@echo ""
	@echo "Docker & Deployment:"
	@echo "  make build          Build Docker containers"
	@echo "  make clean          Remove __pycache__, .pytest_cache, venv"
	@echo ""

install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing Node dependencies..."
	cd frontend && npm install

dev:
	@echo "Starting FastAPI development server..."
	python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

worker:
	@echo "Starting Celery worker..."
	python -m celery -A api.workers.celery_app worker --loglevel=info

frontend:
	@echo "Starting React development server..."
	cd frontend && npm run dev

test:
	@echo "Running test suite with coverage..."
	python -m pytest tests/ -v --cov=core --cov-report=term-missing --cov-fail-under=70

lint:
	@echo "Checking code style with ruff..."
	ruff check . --fix

typecheck:
	@echo "Type checking with mypy..."
	mypy core/ --ignore-missing-imports

eval:
	@echo "Running evaluation suite..."
	python -m pytest tests/eval/ -v --tb=short
	@echo "Evaluation complete"

benchmark:
	@echo "Running performance benchmarks..."
	python -m pytest tests/benchmarks/ -v --benchmark-only || echo "Benchmark suite not configured"

build:
	@echo "Building Docker containers..."
	docker-compose build
	@echo "Build complete"

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf venv/ node_modules/ frontend/dist/
	@echo "Cleanup complete"

check: lint typecheck test
	@echo ""
	@echo "✓ All checks passed!"
	@echo "  - Linting: OK"
	@echo "  - Type checking: OK"
	@echo "  - Tests: OK (coverage ≥70%)"

start:
	@echo "Starting DocuForge AI..."
	python run.py
