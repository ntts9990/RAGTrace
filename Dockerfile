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

# Create non-root user
RUN useradd -m -u 1000 ragtrace

# Set working directory
WORKDIR /app

# Copy project configuration
COPY --chown=ragtrace:ragtrace pyproject.toml ./
COPY --chown=ragtrace:ragtrace uv.toml ./
COPY --chown=ragtrace:ragtrace .python-version ./
COPY --chown=ragtrace:ragtrace uv.lock ./

# Copy application files
COPY --chown=ragtrace:ragtrace src/ ./src/
COPY --chown=ragtrace:ragtrace data/ ./data/
COPY --chown=ragtrace:ragtrace cli.py hello.py ./
COPY --chown=ragtrace:ragtrace README.md CLAUDE.md ./

# Create data directories
RUN mkdir -p /app/data/db /app/data/temp && \
    chown -R ragtrace:ragtrace /app/data

# Switch to non-root user
USER ragtrace

# Set up UV environment
ENV UV_PYTHON=3.11
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies using UV
RUN uv sync --no-dev || uv sync

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