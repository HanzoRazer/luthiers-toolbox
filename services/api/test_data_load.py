#!/usr/bin/env python
import sys
sys.path.insert(0, 'app')

from cnc_production.joblog.storage import list_runs, _load_json, RUNS_PATH
from cnc_production.joblog.models import SawRunRecord

# Check file load
print(f"Loading from: {RUNS_PATH}")
print(f"File exists: {RUNS_PATH.exists()}")

data = _load_json(RUNS_PATH)
print(f"Data keys: {list(data.keys())}")
print(f"Runs dict size: {len(data.get('runs', {}))}")

# Try to validate each run
for run_id, run_dict in data.get('runs', {}).items():
    print(f"\nTrying to validate run: {run_id}")
    try:
        run = SawRunRecord.model_validate(run_dict)
        print(f"  ✓ Valid: {run.status}, {run.meta.op_type}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

# Try list_runs
print("\nCalling list_runs():")
runs = list_runs()
print(f"Returned {len(runs)} runs")
for run in runs:
    print(f"  - {run.run_id}: {run.status}")
