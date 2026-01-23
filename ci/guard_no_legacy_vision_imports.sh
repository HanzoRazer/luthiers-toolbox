#!/usr/bin/env bash
set -euo pipefail

echo "Checking for forbidden legacy vision imports..."

# Only check .py files, exclude _experimental directory itself (internal imports OK)
FORBIDDEN="from app._experimental.ai_graphics"

# Baselined files - existing debt, allowed until migrated
BASELINE_FILES=(
  "services/api/app/rmos/rosette_rmos_adapter.py"
  "services/api/app/tests/test_e2e_workflow_integration.py"
)

# Build grep exclusion pattern
EXCLUDE_PATTERN=$(printf "|%s" "${BASELINE_FILES[@]}")
EXCLUDE_PATTERN="${EXCLUDE_PATTERN:1}"  # Remove leading |

# Find violations: actual import statements outside the legacy module and baseline
violations=$(grep -r --include="*.py" "${FORBIDDEN}" services/api/app \
  | grep -v "services/api/app/_experimental/ai_graphics/" \
  | grep -v "Moved from app._experimental" \
  | grep -E -v "(${EXCLUDE_PATTERN})" \
  || true)

if [ -n "$violations" ]; then
  echo "ERROR: New legacy vision imports detected:"
  echo "$violations"
  echo ""
  echo "These imports should use the canonical vision stack:"
  echo "  - app.vision.router"
  echo "  - app.ai.transport.image_client"
  echo ""
  echo "If this is existing code being moved, add to BASELINE_FILES in this script."
  exit 1
fi

echo "OK: No forbidden legacy vision imports found."
