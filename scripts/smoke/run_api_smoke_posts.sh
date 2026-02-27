#!/usr/bin/env bash
# Run API smoke posts test
# Usage: run_api_smoke_posts.sh <API_BASE> <API_HOST> <API_PORT>

set -e

API_BASE="${1:-http://127.0.0.1:8000}"
API_HOST="${2:-127.0.0.1}"
API_PORT="${3:-8000}"

echo "Starting API server on $API_HOST:$API_PORT..."
cd services/api
python -m uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" &
PID=$!

# Wait for server to start
sleep 4

# Run smoke test
cd ../..
python scripts/smoke/api_smoke_posts.py "$API_BASE"
RESULT=$?

# Cleanup
kill $PID 2>/dev/null || true

exit $RESULT
