# RAGTrace Docker Image with UV
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy project configuration and source code for package build
COPY pyproject.toml ./
COPY uv.toml ./
COPY .python-version ./
COPY uv.lock ./
COPY src/ ./src/
COPY README.md CLAUDE.md ./

# Create LICENSE file for build
RUN echo "Apache License 2.0" > LICENSE

# Set up UV environment
ENV UV_PYTHON=3.11
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_CACHE_DIR=/tmp/.uv-cache

# Install dependencies using UV (as root to avoid permission issues)
RUN uv sync --no-dev || uv sync

# Create non-root user
RUN useradd -m -u 1000 ragtrace

# Copy remaining application files with correct ownership
COPY --chown=ragtrace:ragtrace data/ ./data/
COPY --chown=ragtrace:ragtrace cli.py hello.py ./

# Create data directories and fix ownership
RUN mkdir -p /app/data/db /app/data/temp && \
    chown -R ragtrace:ragtrace /app

# Switch to non-root user
USER ragtrace

# Streamlit configuration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose port
EXPOSE 8501

# Default command
CMD ["uv", "run", "streamlit", "run", "src/presentation/web/main.py", "--server.port=8501", "--server.address=0.0.0.0"]