#!/usr/bin/env bash
# Idempotent bootstrap for the Production Shop (luthiers-toolbox) Cloud Agent
# environment. Safe to run repeatedly: apt installs are no-ops when satisfied,
# the Python venv is reused, and `npm ci` reproduces the client tree from the
# lockfile.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Installing system dependencies"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
# build-essential/libpq/sqlite: backend build + DB tooling.
# poppler-utils + pango/cairo/gdk-pixbuf/ffi: runtime deps for pdf2image and
# weasyprint (operator-report PDF export). python3-venv follows the image's
# default python3 minor and supplies ensurepip for that interpreter.
sudo apt-get install -y --no-install-recommends \
  build-essential curl git jq libpq-dev sqlite3 \
  python3-venv python3-dev python3-pip \
  poppler-utils shared-mime-info fonts-dejavu-core \
  libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
  libcairo2 libffi-dev libjpeg-dev

echo "==> Installing Python backend dependencies (services/api)"
cd "$REPO_ROOT/services/api"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
deactivate

echo "==> Installing Vue client dependencies (packages/client)"
cd "$REPO_ROOT/packages/client"
# The Cloud Agent base image's default `node` (currently 22.14.0) is below this
# workspace's declared engine floor (packages/client/package.json
# "engines.node"). Select a Node that satisfies the floor WITHOUT bypassing the
# repo's own guard and WITHOUT `sudo npm` (npm is not on root's secure PATH on
# this image, which is the defect this fix corrects). Prefer an already-installed
# nvm Node; otherwise install the exact supported version via user-level nvm, so
# node/npm stay on PATH and no privilege escalation is needed.
select_supported_node() {
  # 1. Active node already satisfies the declared floor.
  if node scripts/check-node-engine.mjs >/dev/null 2>&1; then
    echo "==> Active node $(node --version) satisfies the engine floor"
    return 0
  fi
  # 2. Prefer an already-installed nvm Node that satisfies the floor (newest first).
  local nvm_versions="${NVM_DIR:-$HOME/.nvm}/versions/node"
  local bindir
  if [ -d "$nvm_versions" ]; then
    while IFS= read -r bindir; do
      [ -x "$bindir/node" ] || continue
      if PATH="$bindir:$PATH" node scripts/check-node-engine.mjs >/dev/null 2>&1; then
        export PATH="$bindir:$PATH"
        echo "==> Selected installed node $(node --version) from $bindir"
        return 0
      fi
    done < <(ls -1d "$nvm_versions"/v*/bin 2>/dev/null | sort -rV || true)
  fi
  # 3. Otherwise install the exact supported version 22.22.2 via user-level nvm.
  echo "==> No installed Node satisfies the floor; installing pinned Node 22.22.2 via nvm"
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  fi
  set +u
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh"
  nvm install 22.22.2
  set -u
  export PATH="$NVM_DIR/versions/node/v22.22.2/bin:$PATH"
}

select_supported_node
# 4. Refresh the shell's command hash table so the resolved node/npm are used.
hash -r
# 5. Prove the resolved runtime is supported.
echo "==> Resolved node $(node --version) / npm $(npm --version) from $(command -v node)"
# 6. Re-run the repository's own guard against the resolved runtime.
npm run check:node
# 7. Reproduce the client dependency tree from the lockfile.
npm ci

echo "==> Preparing local config and data directories"
cd "$REPO_ROOT"
[ -f .env ] || cp .env.example .env
mkdir -p data/runs logs

echo "==> install.sh complete"
