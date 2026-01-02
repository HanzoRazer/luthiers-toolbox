# syntax=docker/dockerfile:1.6
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# leverage docker layer caching
COPY services/api/requirements.txt ./services/api/requirements.txt
RUN pip install --no-cache-dir -r services/api/requirements.txt

# app
COPY services/api /app/services/api

# non-root
RUN useradd -m app
USER app

ENV UVICORN_HOST=0.0.0.0 UVICORN_PORT=${SERVER_PORT:-8000}
ENV PYTHONPATH=/app/services/api
EXPOSE 8000

# health endpoint baked in app
HEALTHCHECK --interval=10s --timeout=3s --retries=10 \
  CMD curl -fsS http://127.0.0.1:${UVICORN_PORT}/health || exit 1

CMD ["python","-m","uvicorn","services.api.app.main:app","--host","0.0.0.0","--port","8000"]
