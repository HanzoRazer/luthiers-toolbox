#!/usr/bin/env bash
set -euo pipefail
# Mesh Pipeline scaffold example runner.
# Usage: bash examples/retopo/run.sh [qrm|miq]
#
# This runner executes the REAL retopo pipeline or it fails. It must never
# fabricate qa_core.json / cam_policy.json on its own: artifacts written by this
# script rather than by app.retopo.run cannot evidence that the pipeline ran,
# and a downstream schema check against them certifies nothing (MAINT-DEFER-013).
#
# `services/api/app/retopo/` was deleted from main by ee36ddf1 (2026-02-10), so
# on current main this script is expected to exit 3 (pipeline unavailable). The
# workflow gates the demo steps on the module's presence and reports them as
# NOT RUN rather than invoking this script and interpreting a stub as success.

PRESET="${1:-qrm}"
OUT="examples/retopo/out_${PRESET}"

# The output directory is created only once the pipeline is known to be
# importable. An empty out_*/ left behind by an unavailable run is what lets
# `validate_schemas.py --out-root examples/retopo` report "Validated 0
# artifacts ... [OK] All schemas valid" and exit 0 over nothing.
echo "=== Running Mesh Pipeline scaffold with preset: $PRESET ==="

PRESET_ENV="$PRESET" OUT_ENV="$OUT" python - <<'PY'
import sys
from pathlib import Path
import os

sys.path.insert(0, "services/api")

preset = os.environ["PRESET_ENV"]
out_dir = Path(os.environ["OUT_ENV"])

try:
    from app.retopo.run import run_pipeline  # type: ignore
except ImportError as exc:
    print(
        "ERROR: the retopo pipeline is unavailable in this checkout "
        f"({exc.__class__.__name__}: {exc}).",
        file=sys.stderr,
    )
    print(
        "services/api/app/retopo/ was deleted by ee36ddf1 (2026-02-10). "
        "Whether to reverse that deletion is an open disposition "
        "(MAINT-DEFER-013); this runner will not fabricate artifacts to "
        "stand in for it.",
        file=sys.stderr,
    )
    raise SystemExit(3)

out_dir.mkdir(parents=True, exist_ok=True)
result = run_pipeline(
    input_mesh="examples/retopo/intake.obj",
    model_id="DEMO_MODEL",
    preset=preset,
    out_dir=str(out_dir),
    session_id="demo_session_001",
)
print(f"QA Core: {result['qa_core_path']}")
print(f"CAM Policy: {result['cam_policy_path']}")
PY

echo ""
echo "Artifacts in $OUT:"
ls -1 "$OUT"
