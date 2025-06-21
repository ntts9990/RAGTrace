# Justfile for RAGTrace - UV-based task runner
# Install just: https://github.com/casey/just

# Default recipe
default:
    @just --list

# Setup the development environment with UV
setup:
    #!/bin/bash
    echo "🔧 Setting up RAGTrace development environment..."
    if ! command -v uv &> /dev/null; then
        echo "❌ UV not found. Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    echo "✅ UV found: $(uv --version)"
    uv sync --all-extras
    echo "🎉 Setup complete!"

# Install dependencies
install:
    uv sync

# Install with all extras
install-all:
    uv sync --all-extras

# Install only production dependencies
install-prod:
    uv sync --no-dev

# Run the Streamlit dashboard
dashboard:
    uv run streamlit run src/presentation/web/main.py

# Run CLI evaluation
eval dataset="evaluation_data":
    uv run python cli.py evaluate {{dataset}}

# Run CLI evaluation with specific LLM
eval-llm dataset="evaluation_data" llm="gemini":
    uv run python cli.py evaluate {{dataset}} --llm {{llm}}

# Test basic connectivity
test-connection:
    uv run python hello.py

# Run API diagnostics
diagnose:
    uv run python diagnose_api_issue.py

# Run all tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=html --cov-report=term

# Format code with black
format:
    uv run black src/ tests/ *.py

# Lint code with ruff
lint:
    uv run ruff check src/ tests/ *.py

# Type check with mypy
typecheck:
    uv run mypy src/

# Run all code quality checks
check: format lint typecheck

# Clean cache and temporary files
clean:
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf .ruff_cache/
    rm -rf .mypy_cache/
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Update dependencies
update:
    uv lock --upgrade

# Show dependency tree
deps:
    uv tree

# Generate requirements.txt
freeze:
    uv pip compile pyproject.toml -o requirements.txt

# Check for security vulnerabilities
audit:
    uv run pip-audit

# Build the package
build:
    uv build

# Publish to PyPI (development)
publish-test:
    uv publish --repository testpypi

# Publish to PyPI (production) 
publish:
    uv publish

# Show project info
info:
    @echo "📋 RAGTrace Project Information"
    @echo "Python: $(uv python --version)"
    @echo "UV: $(uv --version)"
    @echo "Project: $(uv run python -c 'import src; print(src.__file__)')"

# Development server with auto-reload
dev:
    uv run watchmedo auto-restart --directory=src --pattern="*.py" --recursive -- streamlit run src/presentation/web/main.py

# Quick evaluation test
quick-test:
    uv run python src/presentation/main.py evaluation_data_variant1 --llm gemini --embedding gemini --prompt-type default