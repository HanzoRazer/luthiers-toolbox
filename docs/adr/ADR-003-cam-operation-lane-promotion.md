# ADR-003: CAM Endpoint OPERATION Lane Promotion Plan

## Status
Accepted

## Date
2025-12-29

## Accepted
2025-12-29

## Context

The `OPERATION_EXECUTION_GOVERNANCE_v1.md` contract established a two-lane model for
machine-executing endpoints:

| Lane | Purpose | Characteristics |
|------|---------|-----------------|
| **OPERATION** | Governed execution | Artifacts, feasibility gate, audit trail |
| **UTILITY** | Legacy/preview | Stateless, no governance guarantees |

The CNC Saw Lab Batch implementation (`feature/cnc-saw-labs`) serves as the
**reference implementation** for OPERATION lane, demonstrating:

- SPEC → PLAN → DECISION → EXECUTE → EXPORT pipeline
- Immutable artifacts at each stage
- Server-side feasibility with RED blocking
- GCodeMove canonical structure
- Operator feedback loop (job logs, learning events)

Currently, ~12 CAM endpoints produce G-code in UTILITY lane (direct return, no
artifacts, no feasibility enforcement). These represent production risk if used
for shop-floor machining.

### The Problem

1. **No audit trail** — G-code generated, executed, part fails. No record of parameters.
2. **No feasibility gate** — Dangerous operations can proceed without safety checks.
3. **No deterministic replay** — Cannot reproduce exact G-code from parameters.
4. **Inconsistent interfaces** — Each CAM module has different request/response shapes.

## Decision

**Incrementally promote CAM endpoints to OPERATION lane following the governance
contract migration path.**

### Promotion Tiers

#### Tier 1: High Priority (Wave 9)

| Target | Current State | Effort |
|--------|---------------|--------|
| **Rosette CNC** | Has job store, plan/post separation | 3-5 days |
| **RMOS Toolpaths** | 80% compliant (has artifacts, feasibility, RED blocking) | 1-2 days |
| **V-Carve** | Clean SVG→toolpath→G-code architecture | 2-3 days |

#### Tier 2: Medium Priority (Wave 10)

| Target | Current State | Effort |
|--------|---------------|--------|
| **Roughing Intent** | Has intent model, normalization, metrics | 1-2 days |
| **Drilling** | Simple canned cycles | 2-3 days |
| **Drilling Pattern** | Array of holes | 2-3 days |
| **Bi-Arc Contour** | Simple path following | 2-3 days |

#### Tier 3: Lower Priority (Wave 11+)

| Target | Blocker |
|--------|---------|
| **Relief Carving** | Complex 3D heightfield |
| **Adaptive Clearing** | Complex toolpath strategies |
| **Helical Entry** | Often used as sub-operation |

#### Permanent UTILITY Lane

These remain in UTILITY by design:

- Preview/simulation endpoints (`/preview`, `/sim`)
- Metadata endpoints (`/info`)
- Root-mounted legacy (`/feasibility`, `/toolpaths`)
- DXF/SVG export (not machine-executable)

### Migration Path Per Endpoint

Following governance contract Section 18:

```
Phase 1: Artifact Wrapper (1-2 days)
├── Wrap existing generation in artifact persistence
├── Add request_id correlation
└── Hash all outputs (SHA256)

Phase 2: Feasibility Gate (2-3 days)
├── Add server-side feasibility check
├── Implement RED blocking (HTTP 409)
└── Record blocked artifacts

Phase 3: Move Standardization (1-2 days)
├── Convert output to canonical GCodeMove format
├── Add post-processor interface
└── Support multiple dialects (grbl, fanuc, linuxcnc)

Phase 4: Full Pipeline (3-5 days)
├── Implement SPEC → PLAN → DECISION → EXECUTE stages
├── Add approval checkpoints
└── Enable deterministic replay

Phase 5: Feedback Loop (2-3 days)
├── Add job logging endpoint
├── Emit learning events (optional)
└── Wire metrics rollups (optional)
```

### Endpoint Transformations

#### Before (UTILITY)

```
POST /api/cam/roughing/gcode
Request: { width, height, stepdown, feed, ... }
Response: "G21\nG90\nG0 Z5.0\n..."
```

#### After (OPERATION)

```
POST /api/cam/roughing/spec
Request: { batch_label, session_id, design: { width, height, ... }, context: { tool_id, ... } }
Response: { artifact_id: "spec_xxx", status: "CREATED", ... }

POST /api/cam/roughing/plan
Request: { spec_artifact_id: "spec_xxx" }
Response: { artifact_id: "plan_xxx", feasibility: { score: 85, bucket: "GREEN" }, ... }

POST /api/cam/roughing/approve
Request: { plan_artifact_id: "plan_xxx" }
Response: { artifact_id: "decision_xxx", status: "APPROVED", ... }

POST /api/cam/roughing/toolpaths
Request: { decision_artifact_id: "decision_xxx" }
Response: { artifact_id: "execution_xxx", ops: [...], ... }

GET /api/cam/roughing/executions/{id}/gcode
Response: "G21\nG90\nG0 Z5.0\n..." (with headers)
```

### Lane Declaration

All promoted endpoints MUST declare their lane:

```python
# Option 1: Decorator (preferred)
@router.post("/roughing/spec")
@operation_lane  # Enforces artifact persistence
def create_roughing_spec(req: RoughingSpecRequest):
    ...

# Option 2: Explicit annotation (fallback)
# LANE=OPERATION
@router.post("/roughing/spec")
def create_roughing_spec(req: RoughingSpecRequest):
    ...
```

Legacy endpoints retain:

```python
# LANE=UTILITY
@router.post("/roughing/gcode")
def roughing_gcode_legacy(req: RoughReq):
    ...
```

### Artifact Kind Naming

Per governance contract Section 11:

```
{tool_type}_{stage}[_{sub_type}]

Examples:
  roughing_spec
  roughing_plan
  roughing_decision
  roughing_execution
  roughing_op_toolpaths

  rosette_spec
  rosette_plan
  rosette_decision
  rosette_execution

  vcarve_spec
  vcarve_execution

  drill_spec
  drill_execution
```

## Consequences

### Positive

1. **Audit trail** — Every G-code generation is traceable to artifacts
2. **Safety enforcement** — RED feasibility blocks dangerous operations
3. **Deterministic replay** — Re-run any execution from stored artifacts
4. **Unified interface** — All CAM follows same pipeline pattern
5. **Learning capability** — Can capture feedback, improve parameters over time
6. **Production confidence** — Shop-floor use backed by governance

### Negative

1. **More API calls** — Multi-stage pipeline vs. single endpoint
2. **Migration effort** — ~10-15 days per tool type
3. **Storage overhead** — Artifacts persist (mitigated by cleanup policies)
4. **Learning curve** — Developers must understand pipeline model

### Neutral

1. **Legacy endpoints remain** — Backward compatibility preserved
2. **Optional features** — Learning, rollups are opt-in via feature flags
3. **Incremental adoption** — Each tool type migrates independently

## Risks

| Risk | Mitigation |
|------|------------|
| Breaking existing integrations | Legacy endpoints preserved, deprecation warnings only |
| Feasibility false positives | Tunable thresholds, YELLOW bucket allows proceed-with-warning |
| Storage growth | Artifact retention policies, archive/purge old runs |
| Performance overhead | Artifacts are lightweight JSON, async persistence |

## Alternatives Considered

### 1. Keep All UTILITY
**Rejected.** No governance for production machining is unacceptable.

### 2. Force All OPERATION Immediately
**Rejected.** Breaking change, high risk, no migration path.

### 3. Hybrid Per-Request
**Rejected.** Complexity explosion, inconsistent behavior.

### 4. Gradual Promotion (Selected)
Preserves backward compatibility, allows validation per tool type.

## Implementation Notes

### Shared Infrastructure

Reuse from Saw Lab reference implementation:

```
services/api/app/rmos/run_artifacts/store.py   # Artifact persistence
services/api/app/rmos/runs.py                  # Run artifact model
services/api/app/services/saw_lab_batch_*.py   # Pipeline patterns
```

### Feature Flags

Per governance contract Section 17:

```python
{TOOL}_LEARNING_HOOK_ENABLED = False      # Auto-emit learning events
{TOOL}_METRICS_ROLLUP_HOOK_ENABLED = False # Auto-persist rollups
{TOOL}_APPLY_ACCEPTED_OVERRIDES = False    # Apply learned multipliers
```

### CI Enforcement

Future CI checks (per governance Section 7):

```yaml
# .github/workflows/lane-check.yml
- name: Check lane annotations
  run: |
    python scripts/check_lane_annotations.py
    # Warns on new G-code endpoints without LANE declaration
```

## Tracking

| Milestone | Target | Status |
|-----------|--------|--------|
| Saw Lab reference complete | Wave 8 | ✅ Done |
| RMOS Toolpaths promoted (Phase 1) | Wave 9 | ✅ Done |
| Rosette CNC promoted (Phase 1) | Wave 9 | ✅ Done |
| V-Carve promoted (Phase 1) | Wave 9 | ✅ Done |
| Tier 2 endpoints (Phase 1) | Wave 10 | ✅ Done |
| Tier 3 endpoints (Phase 1) | Wave 11 | ✅ Done |
| CI enforcement | Wave 12 | Planned |
| Phase 2: Feasibility gates | Wave 12 | ✅ Done (2025-12-30) |
| Phase 3: Move standardization | Wave 13+ | ✅ Done (2025-12-31) |
| Phase 4: Full pipeline | Wave 14+ | ✅ Done (2025-12-31) |
| Phase 5: Feedback loops | Wave 15+ | ✅ Done (2025-12-31) |

### Phase 3 Progress (Move Standardization) ✅ Complete

**Infrastructure Complete:**
- ✅ `rmos/moves.py` - Canonical GCodeMove model (TypedDict + Pydantic)
- ✅ `rmos/posts/base.py` - PostProcessor protocol and DialectConfig
- ✅ `rmos/posts/linuxcnc.py` - LinuxCNC post-processor (G64 path blending)
- ✅ Updated `rmos/posts/__init__.py` - Unified exports

**Router Migration (Optional - Routers Already Functional):**
- helical_router.py - Already uses move dict pattern (close to canonical)
- drilling_router.py - Works as-is, can adopt canonical moves later
- biarc_router.py - Works as-is, can adopt canonical moves later
- roughing_router.py - Works as-is, can adopt canonical moves later

### Phase 4 Progress (Full Pipeline) ✅ Complete

**Infrastructure Complete:**
- ✅ `rmos/pipeline/__init__.py` - Package exports
- ✅ `rmos/pipeline/schemas.py` - Full Pydantic models for 4-stage pipeline:
  - `PipelineStage` enum (SPEC, PLAN, DECISION, EXECUTE)
  - `PipelineStatus` enum (CREATED, OK, BLOCKED, ERROR, APPROVED, REJECTED)
  - `SpecArtifact`, `PlanArtifact`, `DecisionArtifact`, `ExecutionArtifact`
  - `PlanOperation`, `ExecutionResult` for operation tracking
  - Request/Response types for each stage
- ✅ `rmos/pipeline/store.py` - Artifact persistence layer:
  - `PipelineStore` protocol
  - `write_artifact()`, `read_artifact()`, `query_artifacts()`
  - `list_executions_for_decision()` - Deterministic replay support
  - `get_artifact_lineage()` - Ancestry tracking
- ✅ `rmos/pipeline/services.py` - Service layer:
  - `PipelineService` class with FeasibilityChecker/ToolpathGenerator protocols
  - `create_spec()` - Create SPEC artifact
  - `create_plan()` - Generate feasibility-scored plan
  - `create_decision()` - Approval checkpoint
  - `create_execution()` - Generate toolpaths with server-side recompute
  - `retry_execution()` - Immutable retry pattern
- ✅ Updated `rmos/__init__.py` - Exports for pipeline module

**Key Features:**
- Immutable artifact chain (SPEC → PLAN → DECISION → EXECUTE)
- Approval checkpoint with operator attribution (`approved_by`, `reason`)
- Deterministic replay via `list_executions_for_decision()`
- Server-side feasibility recompute on every execution
- Immutable retry pattern (creates new artifacts, preserves originals)
- Parent-child linking for lineage tracking

### Phase 5 Progress (Feedback Loops) ✅ Complete

**Infrastructure Complete:**
- ✅ `rmos/pipeline/feedback/__init__.py` - Package exports
- ✅ `rmos/pipeline/feedback/schemas.py` - Full Pydantic models:
  - `JobLogStatus` enum (OK, PARTIAL, SCRAP, ABORTED)
  - `JobLogMetrics` - Time, yield, quality signals (burn, tearout, kickback, chatter)
  - `QualitySignal` enum - Signal types for learning detection
  - `LearningMultipliers` - Parameter adjustment factors (rpm, feed, doc, woc)
  - `LearningSuggestion` - Signal-based suggestion with confidence
  - `LearningEvent`, `LearningDecision` - Learning artifacts
  - `TimeMetrics`, `YieldMetrics`, `EventCounts` - Rollup aggregates
  - `MetricsRollup` - Aggregated execution statistics
- ✅ `rmos/pipeline/feedback/config.py` - Feature flag configuration:
  - `{TOOL}_LEARNING_HOOK_ENABLED` - Auto-emit learning events
  - `{TOOL}_METRICS_ROLLUP_HOOK_ENABLED` - Auto-persist rollups
  - `{TOOL}_APPLY_ACCEPTED_OVERRIDES` - Apply learned multipliers
  - All hooks default to OFF for safety
- ✅ `rmos/pipeline/feedback/job_log.py` - Job log service:
  - `JobLogService.write_log()` - Persist job log with auto-hooks
  - Auto-triggers learning event emission if enabled
  - Auto-triggers metrics rollup if enabled
- ✅ `rmos/pipeline/feedback/learning.py` - Learning service:
  - `detect_signals()` - Detect quality signals from metrics/notes
  - `generate_suggestions()` - Generate parameter adjustments per signal
  - `LearningService.emit_event()` - Create learning event artifact
  - `LearningService.create_decision()` - Accept/reject gate
  - `resolve_learned_multipliers()` - Query accepted overrides
  - `apply_multipliers_to_context()` - Apply to machining context
  - JSONL persistence for learned overrides
- ✅ `rmos/pipeline/feedback/rollups.py` - Metrics rollup service:
  - `RollupService.compute_execution_rollup()` - Aggregate metrics
  - Time metrics (setup, cut, total)
  - Yield metrics (parts_ok, parts_scrap, yield_rate)
  - Event counts (burn, tearout, kickback, chatter, tool_wear)
  - Operator and status breakdowns
- ✅ Updated `rmos/pipeline/__init__.py` - Exports feedback module
- ✅ Updated `rmos/__init__.py` - Exports feedback infrastructure

**Key Features:**
- Feature flags for opt-in learning and rollups (default OFF)
- Quality signal detection from metrics and operator notes
- Confidence-weighted suggestions per signal type
- Accept/reject gate before applying learned multipliers
- JSONL persistence for learned overrides (tool/material/operation key)
- Metrics rollups aggregate time, yield, and event counts

## Related

- [OPERATION_EXECUTION_GOVERNANCE_v1.md](../OPERATION_EXECUTION_GOVERNANCE_v1.md)
- [ENDPOINT_TRUTH_MAP.md](../ENDPOINT_TRUTH_MAP.md)
- [CNC_SAW_LAB_DEVELOPER_GUIDE.md](../CNC_SAW_LAB_DEVELOPER_GUIDE.md)
- [TECHNICAL_DEBT_HANDOFF_2025-12.md](../handoffs/TECHNICAL_DEBT_HANDOFF_2025-12.md)
