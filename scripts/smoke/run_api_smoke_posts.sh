#!/usr/bin/env bash
# Run API smoke posts test (CI-RED-020-A: readiness-gated).
# Usage: run_api_smoke_posts.sh <API_BASE> <API_HOST> <API_PORT>
#
# Boots uvicorn with log capture, waits for readiness via the shared utility
# (replacing a fixed `sleep 4`), then runs the POST smoke. Readiness and
# endpoint behavior are checked separately so a startup failure is reported as
# such (with the uvicorn log tail), not mislabeled as a smoke failure.

set -uo pipefail

API_BASE="${1:-http://127.0.0.1:8000}"
API_HOST="${2:-127.0.0.1}"
API_PORT="${3:-8000}"

# Resolve repo root from this script's location so paths hold regardless of CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UVICORN_LOG="${REPO_ROOT}/uvicorn.log"
UVICORN_PID_FILE="${REPO_ROOT}/uvicorn.pid"

cleanup() {
  if [ -f "$UVICORN_PID_FILE" ]; then
    kill "$(cat "$UVICORN_PID_FILE")" 2>/dev/null || true
    rm -f "$UVICORN_PID_FILE"
  fi
}
trap cleanup EXIT

echo "Starting API server on ${API_HOST}:${API_PORT} (log: ${UVICORN_LOG})..."
cd "$REPO_ROOT/services/api"
python -m uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" --log-level info \
  > "$UVICORN_LOG" 2>&1 &
echo $! > "$UVICORN_PID_FILE"
cd "$REPO_ROOT"

# Readiness gate (diagnostic on failure: attempted paths + uvicorn log tail).
if ! python "$REPO_ROOT/scripts/ci/wait_for_api_ready.py" \
      --base-url "$API_BASE" \
      --paths /api/health,/health \
      --timeout-seconds 60 \
      --pid-file "$UVICORN_PID_FILE" \
      --log-file "$UVICORN_LOG"; then
  echo "API did not become ready; aborting smoke (see uvicorn log tail above)." >&2
  exit 1
fi

# Endpoint behavior (separate from readiness).
python "$REPO_ROOT/scripts/smoke/api_smoke_posts.py" "$API_BASE"
exit $?
