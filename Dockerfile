# ResolveAI - Multi-stage Dockerfile
# Production-ready container for AI support agent

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Create virtual environment using the container's Python
RUN uv venv --python /usr/local/bin/python3.12 /app/.venv

# Install dependencies (production only)
RUN . /app/.venv/bin/activate && uv sync --frozen --no-dev

# ============================================
# Stage 2: Production Runtime
# ============================================
FROM python:3.12-slim AS runtime

# Install curl for healthcheck (must be before USER switch)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Security: Create non-root user
RUN groupadd --gid 1000 resolveai && \
    useradd --uid 1000 --gid resolveai --shell /bin/bash --create-home resolveai

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=resolveai:resolveai /app/.venv /app/.venv

# Copy application code
COPY --chown=resolveai:resolveai . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    VIRTUAL_ENV=/app/.venv

# Create data directories
RUN mkdir -p /app/data/vector_index && \
    chown -R resolveai:resolveai /app/data

# Switch to non-root user
USER resolveai

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "2"]
