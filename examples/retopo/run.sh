#!/usr/bin/env bash
set -euo pipefail
# Mesh Pipeline example runner.
# Usage: bash examples/retopo/run.sh [qrm|miq]

PRESET="${1:-qrm}"
OUT="examples/retopo/out_${PRESET}"
mkdir -p "$OUT"

echo "=== Running Mesh Pipeline with preset: $PRESET ==="
echo ""

# Run the pipeline via Python
python -c "
import sys
sys.path.insert(0, 'services/api')
from app.retopo.run import run_pipeline

result = run_pipeline(
    input_mesh='examples/retopo/intake.obj',
    model_id='DEMO_MODEL',
    preset='${PRESET}',
    out_dir='${OUT}',
    session_id='demo_session_001'
)

if 'error' in result:
    print(f'ERROR: {result[\"error\"]}')
    print(f'Detail: {result.get(\"detail\", \"\")}')
    sys.exit(1)

print(f'QA Core:    {result[\"qa_core_path\"]}')
print(f'CAM Policy: {result[\"cam_policy_path\"]}')
"

echo ""
echo "Artifacts in $OUT:"
ls -1 "$OUT"
