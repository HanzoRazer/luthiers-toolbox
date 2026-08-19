#!/usr/bin/env bash
set -euo pipefail
# Mesh Pipeline scaffold example runner.
# Usage: bash examples/retopo/run.sh [qrm|miq]

PRESET="${1:-qrm}"
OUT="examples/retopo/out_${PRESET}"
mkdir -p "$OUT"

echo "=== Running Mesh Pipeline scaffold with preset: $PRESET ==="

# Run the pipeline via Python. If the historical retopo module is unavailable,
# emit schema-valid scaffold artifacts so CI can still exercise validation.
PRESET_ENV="$PRESET" OUT_ENV="$OUT" python - <<'PY'
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "services/api")

preset = os.environ["PRESET_ENV"]
out_dir = Path(os.environ["OUT_ENV"])
out_dir.mkdir(parents=True, exist_ok=True)
input_mesh = "examples/retopo/intake.obj"
model_id = "DEMO_MODEL"
session_id = "demo_session_001"
timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

try:
    from app.retopo.run import run_pipeline  # type: ignore
except ImportError:
    qa_core_path = out_dir / "qa_core.json"
    cam_policy_path = out_dir / "cam_policy.json"
    qa_core = {
        "version": "1.0.0",
        "timestamp_utc": timestamp,
        "model_id": model_id,
        "session_id": session_id,
        "overall_status": "review_required",
        "notes": "Scaffold fallback: app.retopo module not available in this repository snapshot.",
        "provenance": {
            "preset": preset,
            "source_mesh": input_mesh,
            "commit": None,
        },
    }
    cam_policy = {
        "version": "1.0.0",
        "timestamp_utc": timestamp,
        "model_id": model_id,
        "source_qa_id": f"{model_id}:{session_id}",
        "global_defaults": {},
        "regions": [],
        "provenance": {
            "preset": preset,
            "runner": "examples/retopo/run.sh",
            "commit": None,
        },
    }
    qa_core_path.write_text(json.dumps(qa_core, indent=2), encoding="utf-8")
    cam_policy_path.write_text(json.dumps(cam_policy, indent=2), encoding="utf-8")
    print("retopo pipeline unavailable; wrote scaffold artifacts instead.")
    print(f"QA Core: {qa_core_path}")
    print(f"CAM Policy: {cam_policy_path}")
else:
    result = run_pipeline(
        input_mesh=input_mesh,
        model_id=model_id,
        preset=preset,
        out_dir=str(out_dir),
        session_id=session_id,
    )
    print(f"QA Core: {result['qa_core_path']}")
    print(f"CAM Policy: {result['cam_policy_path']}")
PY

echo ""
echo "Artifacts in $OUT:"
ls -1 "$OUT"
