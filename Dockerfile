# Multi-stage build for RAGTrace with UV
FROM python:3.11-slim as builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.toml uv.lock .python-version ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim as production

# Install system dependencies and UV
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Create non-root user
RUN useradd -m -u 1000 ragtrace

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=ragtrace:ragtrace /app/.venv /app/.venv

# Copy application files
COPY --chown=ragtrace:ragtrace pyproject.toml uv.toml .python-version ./
COPY --chown=ragtrace:ragtrace src/ ./src/
COPY --chown=ragtrace:ragtrace data/ ./data/
COPY --chown=ragtrace:ragtrace cli.py hello.py ./
COPY --chown=ragtrace:ragtrace README.md CLAUDE.md ./

# Create data directories with proper permissions
RUN mkdir -p /app/data/db /app/data/temp && \
    chown -R ragtrace:ragtrace /app/data

# Switch to non-root user
USER ragtrace

# Environment variables
ENV PYTHONPATH=/app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose port
EXPOSE 8501

# Default command - can be overridden
CMD ["uv", "run", "streamlit", "run", "src/presentation/web/main.py", "--server.port=8501", "--server.address=0.0.0.0"]