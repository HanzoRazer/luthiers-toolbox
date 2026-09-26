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
# The Cloud Agent base image currently ships Node 22.14.0, below this
# workspace's declared 22.x floor. This is an agent-only image bootstrap, so
# install a supported Node release globally instead of bypassing the repo's
# own guard. Pin the installer; float within Node 22 like
# packages/client/.nvmrc and CI so Cloud Agent rebuilds continue receiving
# security patch releases. The guard below rejects any resolved patch below
# the workspace's declared engine floor.
if ! node scripts/check-node-engine.mjs; then
  echo "==> Installing a supported Node 22 release for the Cloud Agent"
  sudo npm install --global n@10.2.0
  sudo n 22
  hash -r
fi
npm run check:node
npm ci

echo "==> Preparing local config and data directories"
cd "$REPO_ROOT"
[ -f .env ] || cp .env.example .env
mkdir -p data/runs logs

echo "==> install.sh complete"
