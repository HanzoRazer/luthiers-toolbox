# Railway Dockerfile for FastAPI Backend
# syntax=docker/dockerfile:1.6
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

# system deps (git needed for private repo install)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates build-essential git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Build arg for private repo access (sg-spec)
ARG SG_SPEC_TOKEN=""

# leverage docker layer caching
COPY requirements.txt ./
RUN if [ -n "$SG_SPEC_TOKEN" ]; then \
      git config --global url."https://${SG_SPEC_TOKEN}@github.com/".insteadOf "https://github.com/"; \
    fi && \
    pip install --no-cache-dir -r requirements.txt && \
    git config --global --unset-all url."https://${SG_SPEC_TOKEN}@github.com/".insteadOf || true

# app code
COPY . /app

# Create non-root user first (needed for chown below)
RUN useradd -m app

# Ensure data directories exist and are writable by app user
RUN mkdir -p /app/app/data/runs/rmos /app/app/data/backups/cam && chown -R app:app /app/app/data

# Set data directories to writable paths (not the repo-relative defaults)
ENV RMOS_RUNS_DIR=/app/app/data/runs/rmos
ENV CAM_BACKUP_DIR=/app/app/data/backups/cam

# Switch to non-root user
USER app

# Railway provides $PORT dynamically - default to 8080 for Railway compatibility
ENV PORT=8080
ENV PYTHONPATH=/app
EXPOSE 8080

# health endpoint baked in app
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=10 \
  CMD curl -fsS http://127.0.0.1:${PORT}/health || exit 1

# CRITICAL: Use shell form to allow $PORT expansion at runtime
# Railway injects PORT env var - we MUST use it
CMD python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
