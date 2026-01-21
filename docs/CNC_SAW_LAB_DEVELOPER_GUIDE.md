# CNC Saw Lab Batch System - Developer Guide

## Executive Summary

The CNC Saw Lab system provides a **governed, auditable batch workflow** for CNC saw operations. It transforms cut specifications into machine-ready G-code while enforcing feasibility checks, capturing operator feedback, and enabling machine learning from production data.

**Key Achievement:** End-to-end pipeline from cut spec to downloadable G-code with full governance trail.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CNC SAW LAB BATCH PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐ │
│  │   SPEC   │ -> │   PLAN   │ -> │ DECISION │ -> │ EXECUTE  │ -> │G-CODE │ │
│  │          │    │          │    │ (Approve)│    │(Toolpath)│    │Export │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └───────┘ │
│       │               │               │               │              │      │
│       v               v               v               v              v      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    GOVERNED RUN ARTIFACTS                            │   │
│  │  (Immutable, Auditable, Queryable by kind/session/label)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                       │
│                    v               v               v                        │
│              ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│              │ Job Logs │   │ Learning │   │ Metrics  │                    │
│              │(Operator)│   │  Events  │   │ Rollups  │                    │
│              └──────────┘   └──────────┘   └──────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Governed Run Artifacts

Every operation produces **immutable artifacts** stored with:
- `artifact_id` - Unique identifier
- `kind` - Type classification (e.g., `saw_batch_execution`)
- `status` - OK | BLOCKED | ERROR
- `index_meta` - Queryable metadata (tool_id, material_id, session_id, batch_label)
- `payload` - Full data including toolpaths
- `created_utc` - Timestamp

**Artifact Kinds:**
| Kind | Description |
|------|-------------|
| `saw_batch_spec` | Input specification (items to cut) |
| `saw_batch_plan` | Grouped setups with feasibility scores |
| `saw_batch_decision` | Approved execution order |
| `saw_batch_execution` | Parent execution with summary |
| `saw_batch_op_toolpaths` | Individual op toolpaths (G-code moves) |
| `saw_batch_job_log` | Operator feedback per execution |
| `saw_batch_execution_abort` | Terminal state: execution aborted |
| `saw_batch_execution_complete` | Terminal state: execution completed |
| `saw_lab_learning_event` | Proposed parameter adjustments |
| `saw_lab_learning_decision` | ACCEPT/REJECT of learning events |
| `saw_batch_execution_metrics_rollup` | Aggregated execution metrics |
| `saw_batch_decision_metrics_rollup` | Aggregated decision metrics |

### 2. Execution Lifecycle (Terminal States)

An execution can reach exactly one terminal state:

| State | Artifact Kind | Meaning |
|-------|---------------|---------|
| **ABORTED** | `saw_batch_execution_abort` | Operator stopped execution early (jam, burn, kickback, etc.) |
| **COMPLETED** | `saw_batch_execution_complete` | Execution finished; operator recorded outcome |

**Invariants:**
- An execution cannot be both ABORTED and COMPLETED
- COMPLETED requires at least one qualifying job log (non-ABORTED status, metrics showing work)
- Abort and Complete are symmetric: same 404/409 codes, same detail strings

**Outcome values for COMPLETED:**
- `SUCCESS` — All cuts completed as planned
- `PARTIAL` — Some cuts completed, others skipped
- `REWORK_NEEDED` — Completed but quality issues detected

### 3. Feature Flags

All advanced features are **off by default** for safety:

| Flag | Purpose | Default |
|------|---------|---------|
| `SAW_LAB_LEARNING_HOOK_ENABLED` | Auto-emit learning events on job log | `false` |
| `SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED` | Auto-persist rollups on job log | `false` |
| `SAW_LAB_APPLY_ACCEPTED_OVERRIDES` | Apply learned multipliers to execution | `false` |

### 3. Server-Side Feasibility

**Mandatory governance requirement:** Feasibility is always recomputed server-side before toolpath generation. Client-provided scores are logged but never trusted.

Risk buckets: `GREEN` | `YELLOW` | `RED` (blocked)

---

## API Endpoints

### Batch Workflow (Core)

```
POST /api/saw/batch/spec
  Body: { batch_label, session_id, tool_id, items: [{part_id, qty, material_id, thickness_mm, length_mm, width_mm}] }
  Returns: { batch_spec_artifact_id }

POST /api/saw/batch/plan
  Body: { batch_spec_artifact_id }
  Returns: { batch_plan_artifact_id, setups: [{setup_key, ops: [{op_id, feasibility}]}] }

POST /api/saw/batch/approve
  Body: { batch_plan_artifact_id, approved_by, reason, setup_order, op_order }
  Returns: { batch_decision_artifact_id }

POST /api/saw/batch/toolpaths
  Body: { batch_decision_artifact_id }
  Returns: { batch_execution_artifact_id, results: [{op_id, status, toolpaths_artifact_id}] }
```

### Terminal States

```
POST /api/saw/batch/execution/abort
  Body: { batch_execution_artifact_id, session_id, batch_label, reason, notes?, operator_id? }
  Returns: { batch_execution_artifact_id, abort_artifact_id, state: "ABORTED" }
  Errors: 404 (execution not found), 400 (missing required fields)

POST /api/saw/batch/execution/complete
  Body: { batch_execution_artifact_id, session_id, batch_label, outcome, notes?, operator_id?, checklist?, statistics? }
  Returns: { batch_execution_artifact_id, complete_artifact_id, state: "COMPLETED" }
  Errors: 404 (execution not found), 409 (already aborted/completed, no job logs, latest job log not qualifying)
```

### G-Code Export (MVP)

```
GET /api/saw/batch/op-toolpaths/{artifact_id}/gcode
  Returns: Single op G-code file (.ngc)

GET /api/saw/batch/executions/{artifact_id}/gcode
  Returns: Combined G-code for all OK ops (.ngc)
```

### Operator Feedback

```
POST /api/saw/batch/job-log
  Params: batch_execution_artifact_id, operator, notes, status
  Body: { metrics: { parts_ok, parts_scrap, cut_time_s, setup_time_s } }
  Returns: { job_log artifact + optional learning_event + optional rollups }
```

### Learning System

```
GET  /api/saw/batch/learning-events/by-execution?batch_execution_artifact_id=...
POST /api/saw/batch/learning-events/approve?learning_event_artifact_id=...&policy_decision=ACCEPT&approved_by=...
GET  /api/saw/batch/learning-overrides/resolve?tool_id=...&material_id=...
POST /api/saw/batch/learning-overrides/apply (preview tuned context)
GET  /api/saw/batch/executions/with-learning?only_applied=true
```

### Metrics & Analytics

```
GET  /api/saw/batch/executions/metrics-rollup/by-execution?batch_execution_artifact_id=...
POST /api/saw/batch/executions/metrics-rollup/by-execution (persist rollup)
GET  /api/saw/batch/decisions/metrics-rollup/by-decision?batch_decision_artifact_id=...
GET  /api/saw/batch/decisions/trends?batch_decision_artifact_id=...&window=20
GET  /api/saw/batch/executions/metrics-rollup/history?batch_execution_artifact_id=...
GET  /api/saw/batch/decisions/metrics-rollup/latest-vs-prev?batch_decision_artifact_id=...
GET  /api/saw/batch/rollups/diff?left_rollup_artifact_id=...&right_rollup_artifact_id=...
```

### CSV Exports

```
GET /api/saw/batch/executions/job-logs.csv?batch_execution_artifact_id=...
GET /api/saw/batch/decisions/execution-rollups.csv?batch_decision_artifact_id=...
```

### Status & Lookups

```
GET /api/saw/batch/learning-hook/status
GET /api/saw/batch/rollups/hook/status
GET /api/saw/batch/learning-overrides/apply/status
GET /api/saw/batch/execution?batch_decision_artifact_id=...
GET /api/saw/batch/executions/by-decision?batch_decision_artifact_id=...
GET /api/saw/batch/links?batch_label=...&session_id=...
```

---

## File Structure

```
services/api/app/
├── saw_lab/
│   ├── __init__.py              # SawLabService orchestrator
│   ├── batch_router.py          # All /api/saw/batch/* endpoints
│   ├── models.py                # SawToolpathMove, SawToolpathPlan
│   ├── toolpath_builder.py      # Converts segments to G-code moves
│   ├── path_planner.py          # Plans cut sequences
│   ├── schemas_batch.py         # Pydantic request/response models
│   └── calculators/             # Feasibility calculators
│
├── services/
│   ├── saw_lab_batch_spec_service.py
│   ├── saw_lab_batch_plan_service.py
│   ├── saw_lab_batch_decision_service.py
│   ├── saw_lab_batch_toolpaths_service.py    # Main execution service
│   ├── saw_lab_batch_job_log_service.py      # Job log + hooks
│   ├── saw_lab_gcode_emit_service.py         # G-code export (MVP)
│   ├── saw_lab_learning_hook_config.py       # Feature flag
│   ├── saw_lab_operator_feedback_learning_hook.py
│   ├── saw_lab_learning_decision_service.py
│   ├── saw_lab_learned_overrides_resolver.py
│   ├── saw_lab_learning_apply_service.py
│   ├── saw_lab_execution_metrics_rollup_service.py
│   ├── saw_lab_decision_metrics_rollup_service.py
│   ├── saw_lab_metrics_rollup_hook_config.py
│   ├── saw_lab_rollup_lookup_service.py
│   ├── saw_lab_rollup_history_service.py
│   ├── saw_lab_rollup_diff_service.py
│   ├── saw_lab_metrics_trends_service.py
│   └── saw_lab_export_service.py             # CSV exports
│
└── rmos/run_artifacts/
    ├── store.py                 # read_run_artifact, write_run_artifact, query_run_artifacts
    └── index.py                 # Artifact indexing
```

---

## Typical Usage Flow

### 1. Create and Execute a Batch

```python
import requests

BASE = "http://localhost:8000/api/saw/batch"

# Step 1: Spec
spec = requests.post(f"{BASE}/spec", json={
    "batch_label": "guitar-braces-001",
    "session_id": "session_abc",
    "tool_id": "saw:thin_140",
    "items": [
        {"part_id": "brace1", "qty": 4, "material_id": "spruce",
         "thickness_mm": 6.0, "length_mm": 400.0, "width_mm": 12.0},
        {"part_id": "brace2", "qty": 2, "material_id": "spruce",
         "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 10.0},
    ]
}).json()

# Step 2: Plan
plan = requests.post(f"{BASE}/plan", json={
    "batch_spec_artifact_id": spec["batch_spec_artifact_id"]
}).json()

# Step 3: Approve
decision = requests.post(f"{BASE}/approve", json={
    "batch_plan_artifact_id": plan["batch_plan_artifact_id"],
    "approved_by": "john_doe",
    "reason": "Production run",
    "setup_order": [s["setup_key"] for s in plan["setups"]],
    "op_order": [op["op_id"] for s in plan["setups"] for op in s["ops"]],
}).json()

# Step 4: Execute (generate toolpaths)
execution = requests.post(f"{BASE}/toolpaths", json={
    "batch_decision_artifact_id": decision["batch_decision_artifact_id"]
}).json()

# Step 5: Download G-code
gcode = requests.get(
    f"{BASE}/executions/{execution['batch_execution_artifact_id']}/gcode"
).text

# Save to file
with open("batch_output.ngc", "w") as f:
    f.write(gcode)
```

### 2. Record Operator Feedback

```python
# After running the batch on the machine
requests.post(f"{BASE}/job-log", params={
    "batch_execution_artifact_id": execution["batch_execution_artifact_id"],
    "operator": "jane_smith",
    "notes": "Slight tearout on brace2, reduced feed helped",
    "status": "COMPLETED"
}, json={
    "metrics": {
        "parts_ok": 5,
        "parts_scrap": 1,
        "cut_time_s": 180,
        "setup_time_s": 45,
        "tearout": True
    }
})
```

### 3. Review Learning Events (if hook enabled)

```python
# Get proposed learning events
events = requests.get(f"{BASE}/learning-events/by-execution", params={
    "batch_execution_artifact_id": execution["batch_execution_artifact_id"]
}).json()

# Accept a learning event
for event in events:
    requests.post(f"{BASE}/learning-events/approve", params={
        "learning_event_artifact_id": event["artifact_id"],
        "policy_decision": "ACCEPT",
        "approved_by": "supervisor",
        "reason": "Validated in production"
    })
```

---

## G-Code Output Format

### Single Operation
```gcode
G21  (Units: mm)
G90  (Absolute positioning)
G17  (XY plane selection)
S5000  (Spindle speed)
M3  (Spindle on CW)
G0 Z40.0000  (Move to safe height)
G0 X0.0000 Y-20.0000  (Rapid to start)
G1 Z-3.0000 F900.0  (Plunge)
G1 X0.0000 Y320.0000 F3000.0  (Cut)
G0 Z40.0000  (Retract)
M5  (Spindle stop)
M30  (Program end)
```

### Combined Execution (Multiple Ops)
```gcode
( Batch: guitar-braces-001 )
( Execution: art_abc12345 )
( Ops: 6 OK, 0 BLOCKED )

( ========== Op: op_001 ========== )
G21  (Units: mm)
G90  (Absolute positioning)
...
M5  (Spindle stop)

( ========== Op: op_002 ========== )
G21  (Units: mm)
G90  (Absolute positioning)
...
M5  (Spindle stop)

...

( ========== Op: op_006 ========== )
...
M5  (Spindle stop)
M30  (Program end)
```

---

## Testing

### Run Tests
```bash
cd services/api
pytest tests/test_saw_*.py -v
```

### Key Test Files
- `test_saw_batch_execution_toolpaths.py` - Core workflow
- `test_saw_gcode_export_end_to_end.py` - G-code export
- `test_saw_job_log_rollup_hook_persists_rollups_when_enabled.py` - Rollup hooks
- `test_saw_rollup_latest_endpoints_return_found_false_when_none.py` - Edge cases
- `test_saw_decision_trends_endpoint_shape.py` - Trends API
- `test_saw_rollup_history_and_diff_end_to_end.py` - History/diff
- `test_saw_csv_exports_end_to_end.py` - CSV exports

### Test Isolation
Tests use `monkeypatch` to set feature flags and `conftest.py` ensures:
- `SAW_LAB_LEARNING_HOOK_ENABLED=false`
- `SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED=false`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SAW_LAB_LEARNING_HOOK_ENABLED` | `false` | Auto-emit learning events on job log |
| `SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED` | `false` | Auto-persist rollups on job log |
| `SAW_LAB_APPLY_ACCEPTED_OVERRIDES` | `false` | Apply learned multipliers during execution |
| `RMOS_DATA_DIR` | `./data` | Artifact storage directory |

---

## Key Design Decisions

1. **Immutable Artifacts** - All operations create new artifacts; nothing is updated in place. This provides full audit trail.

2. **Server-Side Feasibility** - Client cannot bypass safety checks. All feasibility is recomputed server-side before toolpath generation.

3. **Feature Flags Off by Default** - Learning and rollup hooks must be explicitly enabled. Safe for production.

4. **Best-Effort Hooks** - Hooks (learning, rollup) never fail the parent operation. Errors are logged but job logs always succeed.

5. **Governance-First** - Every decision point (plan approval, learning acceptance) creates a new artifact with approver identity.

6. **G-Code Moves Native** - `SawToolpathMove` objects already contain G-code commands (G0, G1, M3, etc.). Export is just serialization.

---

## Migration Notes

If upgrading from an older saw lab system:

1. **Artifact Schema** - New artifacts use `index_meta` for queryable fields. Old queries may need updating.

2. **Endpoint Paths** - All batch endpoints are under `/api/saw/batch/*`. Check for hardcoded paths.

3. **Feature Flags** - New flags default to `false`. Enable explicitly in environment if needed.

4. **G-Code Export** - New endpoints at `/op-toolpaths/{id}/gcode` and `/executions/{id}/gcode`. Replaces any manual toolpath extraction.

---

## Support

- **Repository:** `luthiers-toolbox/services/api/`
- **Branch:** `feature/cnc-saw-labs`
- **Tests:** `pytest tests/test_saw_*.py`

For questions about the learning system, rollup aggregation, or G-code generation, see the inline docstrings in the service files.
