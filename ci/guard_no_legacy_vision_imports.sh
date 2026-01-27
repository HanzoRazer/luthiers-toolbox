#!/usr/bin/env bash
set -euo pipefail

echo "Checking for forbidden legacy vision imports..."

# The _experimental/ai_graphics/ folder has been DELETED (PR2 cleanup, Jan 2026).
# This guard remains as defense-in-depth to prevent re-introduction.
FORBIDDEN="from app._experimental.ai_graphics"

# No baseline exceptions — all legacy debt is resolved.
violations=$(grep -r --include="*.py" "${FORBIDDEN}" services/api/app || true)

if [ -n "$violations" ]; then
  echo "ERROR: Legacy _experimental.ai_graphics imports detected:"
  echo "$violations"
  echo ""
  echo "The _experimental/ai_graphics/ module has been DELETED."
  echo "Use the canonical stack:"
  echo "  - app.vision.router"
  echo "  - app.ai.transport.image_client"
  echo "  - RMOS CAS for storage"
  exit 1
fi

echo "OK: No forbidden legacy vision imports found."
