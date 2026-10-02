#!/usr/bin/env bash
# Boot the Production Shop dev servers. Idempotent: a healthy listener is left
# alone, and a session that is still starting is not killed and replaced.
# API listens on 8010 because packages/client/vite.config.ts proxies /api there.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ -x /usr/local/lib/nodejs/bin/node ]; then
  export PATH="/usr/local/lib/nodejs/bin:${PATH}"
elif [ -x "${HOME}/.nvm/versions/node/v22.22.2/bin/node" ]; then
  export PATH="${HOME}/.nvm/versions/node/v22.22.2/bin:${PATH}"
fi

mkdir -p "$REPO_ROOT/data/runs" /tmp

wait_http() {
  local url="$1"
  local name="$2"
  local tries="${3:-90}"
  local i
  for i in $(seq 1 "$tries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "==> ${name} ready (${url})"
      return 0
    fi
    sleep 2
  done
  echo "==> ${name} not ready after $((tries * 2))s: ${url}" >&2
  return 1
}

start_api() {
  if curl -fsS http://127.0.0.1:8010/api/health >/dev/null 2>&1; then
    echo "==> API already listening on :8010"
    return 0
  fi
  if tmux has-session -t api 2>/dev/null; then
    echo "==> API tmux session exists; waiting for health"
  else
    echo "==> Starting API on 127.0.0.1:8010"
    tmux new-session -d -s api -c "$REPO_ROOT/services/api" -- \
      bash -lc "source .venv/bin/activate && export ART_STUDIO_DB_PATH=/tmp/art_studio.db RMOS_RUNS_DIR='${REPO_ROOT}/data/runs' RMOS_RUNS_V2_ENABLED=true PYTHONPATH='${REPO_ROOT}/services/api:${REPO_ROOT}' AUTH_MODE=header && exec uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload >> /tmp/luthiers-api.log 2>&1"
  fi
  wait_http http://127.0.0.1:8010/api/health "API" 90
}

start_client() {
  if curl -fsS http://127.0.0.1:5173/ >/dev/null 2>&1; then
    echo "==> Client already listening on :5173"
    return 0
  fi
  if tmux has-session -t client 2>/dev/null; then
    echo "==> Client tmux session exists; waiting for the dev server"
  else
    echo "==> Starting Vue client on 127.0.0.1:5173"
    tmux new-session -d -s client -c "$REPO_ROOT/packages/client" -- \
      bash -lc "export PATH='/usr/local/lib/nodejs/bin:${HOME}/.nvm/versions/node/v22.22.2/bin:'\"\$PATH\" && exec npm run dev -- --host 127.0.0.1 --port 5173 >> /tmp/luthiers-client.log 2>&1"
  fi
  wait_http http://127.0.0.1:5173/ "Client" 45
}

start_api
start_client
echo "==> start.sh complete"
