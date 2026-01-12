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
COPY services/api/requirements.txt ./services/api/requirements.txt
RUN if [ -n "$SG_SPEC_TOKEN" ]; then \
      git config --global url."https://${SG_SPEC_TOKEN}@github.com/".insteadOf "https://github.com/"; \
    fi && \
    pip install --no-cache-dir -r services/api/requirements.txt && \
    git config --global --unset-all url."https://${SG_SPEC_TOKEN}@github.com/".insteadOf || true

# app
COPY services/api /app/services/api

# Create non-root user first (needed for chown below)
RUN useradd -m app

# Ensure data directory exists and is writable by app user
RUN mkdir -p /app/services/api/app/data && chown -R app:app /app/services/api/app/data

# Switch to non-root user
USER app

ENV UVICORN_HOST=0.0.0.0 UVICORN_PORT=${SERVER_PORT:-8000}
ENV PYTHONPATH=/app/services/api
EXPOSE 8000

# health endpoint baked in app
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=10 \
  CMD curl -fsS http://127.0.0.1:${UVICORN_PORT}/health || exit 1

CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
