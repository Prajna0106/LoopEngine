.PHONY: help lint format typecheck test test-unit test-integration test-acceptance check coverage clean install

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint:  ## Run ruff linter
	ruff check src tests
	ruff format --check src tests

format:  ## Auto-format code
	ruff check --fix src tests
	ruff format src tests

typecheck:  ## Run mypy type checker
	mypy src/loopengine

test:  ## Run all tests
	pytest

test-unit:  ## Run unit tests only
	pytest -m unit

test-integration:  ## Run integration tests only
	pytest -m integration

test-acceptance:  ## Run acceptance tests only
	pytest -m acceptance

coverage:  ## Run tests with coverage report
	pytest --cov --cov-report=term-missing --cov-report=html

check: lint typecheck test  ## Run all checks (lint + typecheck + test)

clean:  ## Remove build artifacts
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install:  ## Install in editable mode with all extras
	pip install -e ".[all]"
