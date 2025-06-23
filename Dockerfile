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

# Set up UV environment
ENV UV_PYTHON=3.11
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Set pip timeout and retry options for better network stability
ENV UV_HTTP_TIMEOUT=300
ENV UV_INDEX_STRATEGY=unsafe-best-match

# Copy only dependency-related files first to leverage Docker cache
COPY pyproject.toml uv.toml .python-version uv.lock ./

# Install dependencies using UV as root with temporary cache
# This layer will be cached as long as dependency files don't change
RUN UV_CACHE_DIR=/tmp/uv-build-cache uv sync --no-dev || UV_CACHE_DIR=/tmp/uv-build-cache uv sync

# Clean up build cache immediately after installation
RUN rm -rf /tmp/uv-build-cache

# Now copy the rest of the application source code
COPY src/ ./src/
COPY README.md CLAUDE.md ./
COPY cli.py hello.py ./
COPY data/ ./data/

# Create LICENSE file for build
RUN echo "Apache License 2.0" > LICENSE

# Create non-root user
RUN useradd -m -u 1000 ragtrace

# Set runtime cache directory for non-root user
ENV UV_CACHE_DIR=/home/ragtrace/.cache/uv

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