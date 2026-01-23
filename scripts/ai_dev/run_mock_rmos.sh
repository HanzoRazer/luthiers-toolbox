#!/usr/bin/env bash
set -e

echo "Starting Mock RMOS on http://localhost:8000"
uvicorn scripts.mock_rmos.main:app --reload --port 8000
