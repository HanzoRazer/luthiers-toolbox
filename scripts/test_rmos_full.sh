#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${RMOS_BASE_URL:-http://127.0.0.1:8000/rmos}"

log() { echo "[RMOS-FULL] $*"; }

log "Base URL: $BASE_URL"

# 1) Simple health probe: /joblog
log "Checking /joblog..."
curl -fsS "${BASE_URL}/joblog" >/dev/null || {
  echo "[ERR] /joblog health check failed"
  exit 1
}

# 2) Minimal slice preview (circle)
log "Testing /saw-ops/slice/preview..."
curl -fsS -X POST "${BASE_URL}/saw-ops/slice/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "bash_ci_slice",
    "op_type": "saw_slice",
    "tool_id": "saw_default",
    "geometry_source": "circle_param",
    "circle": { "center_x_mm": 0, "center_y_mm": 0, "radius_mm": 50 },
    "line": null,
    "dxf_path": null,
    "slice_thickness_mm": 1.0,
    "passes": 1,
    "material": "hardwood",
    "workholding": "vacuum",
    "risk_options": {
      "allow_aggressive": false,
      "machine_gantry_span_mm": 1200
    }
  }' >/dev/null

log "Slice preview OK."

# 3) Minimal batch preview
log "Testing /saw-ops/batch/preview..."
curl -fsS -X POST "${BASE_URL}/saw-ops/batch/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "bash_ci_batch",
    "op_type": "saw_slice_batch",
    "tool_id": "saw_default",
    "geometry_source": "circle_param",
    "base_circle": { "center_x_mm": 0, "center_y_mm": 0, "radius_mm": 45 },
    "num_rings": 2,
    "radial_step_mm": 3,
    "radial_sign": 1,
    "slice_thickness_mm": 1.0,
    "passes": 1,
    "material": "hardwood",
    "workholding": "vacuum"
  }' >/dev/null

log "Batch preview OK."

log "RMOS bash smoke test completed successfully."
