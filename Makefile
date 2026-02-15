.PHONY: help install test lint format build deploy local clean coverage security setup

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make setup            - Install dependencies and pre-commit hooks"
	@echo "  make test             - Run tests with coverage"
	@echo "  make coverage         - Generate and display coverage report"
	@echo "  make lint             - Run linting checks"
	@echo "  make format           - Format code with black and ruff"
	@echo "  make format-check     - Check code formatting without changes"
	@echo "  make type-check       - Run type checking with mypy"
	@echo "  make security         - Run security checks with bandit"
	@echo "  make build            - Build Lambda deployment package"
	@echo "  make deploy           - Build and deploy with SAM"
	@echo "  make local            - Run Lambda locally with SAM"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make clean-all        - Clean all artifacts including venv"

install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements-dev.txt

setup: install
	@echo "Setting up pre-commit hooks..."
	@if command -v pre-commit &> /dev/null; then \
		pre-commit install; \
	else \
		echo "pre-commit not installed. Install with: pip install pre-commit"; \
	fi

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=100

coverage: test
	@echo "\n✓ Coverage report generated at htmlcov/index.html"

lint:
	pylint src/
	mypy src/ --ignore-missing-imports
	ruff check src/ tests/

format-check:
	black --check src/ tests/
	ruff format --check src/ tests/
	ruff check --select I src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/
	ruff format src/ tests/

type-check:
	mypy src/ --ignore-missing-imports --strict

security:
	bandit -r src/ -v
	ruff check --select S src/
	@echo "\nRunning pip check for vulnerable dependencies..."
	pip check || true

build:
	sam build

deploy: build
	sam deploy --guided

local:
	sam local start-api

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage
	rm -rf .aws-sam/ build/ dist/
	rm -rf *.egg-info/

clean-all: clean
	rm -rf .venv/ venv/ env/
