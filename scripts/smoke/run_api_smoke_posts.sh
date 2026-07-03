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

# CI-RED-020-B: the EXIT trap already preserved the smoke exit code implicitly
# (no `exit` in the body). Adding deterministic TERM->wait->escalate->reap makes
# that fragile, so preservation is now EXPLICIT: capture rc first, restore it last.
# Every signal/reap is `|| true` so a cleanup failure can never flip a real
# smoke/readiness result. See docs/handoffs/CI_RED_020B_addendum.md item 2.
cleanup() {
  rc=$?
  if [ -f "$UVICORN_PID_FILE" ]; then
    pid="$(cat "$UVICORN_PID_FILE" 2>/dev/null || true)"
    if [ -n "${pid:-}" ]; then
      kill -TERM "$pid" 2>/dev/null || true
      # Wait briefly (~5s) for graceful exit before escalating.
      for _ in 1 2 3 4 5 6 7 8 9 10; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.5
      done
      kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
    rm -f "$UVICORN_PID_FILE"
  fi
  exit "$rc"
}
trap cleanup EXIT

# Readiness timeout is overridable per caller (slow CI cold starts); default 60s.
API_READY_TIMEOUT="${API_READY_TIMEOUT:-60}"

echo "Starting API server on ${API_HOST}:${API_PORT} (log: ${UVICORN_LOG})..."
# Guard the cd: with `set -e` dropped, an unguarded cd failure would otherwise
# boot uvicorn from the wrong directory and silently fail the import.
cd "$REPO_ROOT/services/api" || { echo "FATAL: cannot cd to services/api" >&2; exit 1; }
python -m uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" --log-level info \
  > "$UVICORN_LOG" 2>&1 &
echo $! > "$UVICORN_PID_FILE"
cd "$REPO_ROOT" || { echo "FATAL: cannot cd to repo root" >&2; exit 1; }

# Readiness gate (diagnostic on failure: attempted paths + uvicorn log tail).
if ! python "$REPO_ROOT/scripts/ci/wait_for_api_ready.py" \
      --base-url "$API_BASE" \
      --paths /api/health \
      --require 'router_count>0' \
      --timeout-seconds "$API_READY_TIMEOUT" \
      --pid-file "$UVICORN_PID_FILE" \
      --log-file "$UVICORN_LOG"; then
  echo "API did not become ready; aborting smoke (see uvicorn log tail above)." >&2
  exit 1
fi

# Endpoint behavior (separate from readiness).
python "$REPO_ROOT/scripts/smoke/api_smoke_posts.py" "$API_BASE"
exit $?
