# Operation Execution Governance Contract

**Version:** 1.0
**Status:** Canonical
**Applies to:** All machine-executing operations (CNC, Saw, CAM toolpaths)
**Effective:** Wave 8+ (non-breaking; additive)

---

## Part I: Governance Contract

### 1. Purpose

This contract defines **how machine-executing operations must behave** inside Luthier's ToolBox.

Its goal is to ensure:

- Deterministic, auditable execution
- Uniform points of operation across subsystems
- Safe evolution from stateless generators to governed execution pipelines
- Clear separation between *design utilities* and *manufacturing operations*

This contract does **not** replace existing CAM or RMOS schemas.
It **wraps them** with operational guarantees.

---

### 2. Definitions

#### Operation

A request that **produces machine-executable output**, such as:

- G-code
- Toolpaths
- Cut lists
- CNC programs
- Saw execution plans

#### Utility

A stateless helper that:

- Computes geometry
- Simulates toolpaths
- Calculates feeds/speeds
- Produces previews only

Utilities are **out of scope** for this contract.

---

### 3. Operation Lanes

Every endpoint that produces machine-executable output MUST belong to one of the following lanes.

#### 3.1 Utility Lane (Legacy / Preview)

**Characteristics:**

- Stateless
- No persistence required
- No approvals
- No audit guarantees
- May return G-code directly

**Allowed for:**

- Development
- Simulation
- Preview
- Backward compatibility

**Example:**
```
POST /api/cam/roughing_gcode
POST /saw_gcode/generate
```

---

#### 3.2 Operation Lane (Governed)

**Characteristics:**

- Server-side feasibility enforcement
- Persistent execution artifacts
- Optional approval checkpoints
- Auditable lifecycle
- Deterministic re-runs

**Required for:**

- Production machining
- Shop-floor execution
- Batch jobs
- Saw operations
- Any operation with safety or material risk

**Example:**
```
POST /api/saw/batch/spec
POST /api/saw/batch/plan
POST /api/saw/batch/approve
POST /api/saw/batch/toolpaths
GET  /api/saw/batch/executions/{id}/gcode
```

---

### 4. Required Guarantees (Operation Lane)

Any **Operation Lane** implementation MUST satisfy the following.

#### 4.1 Request Correlation

- Every request MUST carry an `X-Request-Id`
- The server MUST echo the same ID in the response
- All artifacts MUST record `request_id`

#### 4.2 Execution Artifact

An operation MUST produce a **Run Artifact** with minimum fields:

```json
{
  "artifact_id": "art_xxx",
  "kind": "{tool}_{stage}",
  "status": "PLANNED | APPROVED | EXECUTED | BLOCKED | FAILED",
  "created_utc": "ISO8601",
  "request_id": "req_xxx",
  "index_meta": {
    "tool_kind": "saw | cam | drill | ...",
    "session_id": "optional"
  }
}
```

Artifacts are immutable except for **explicit lifecycle transitions**.

#### 4.3 Feasibility Gate

Operations SHOULD require:

- Explicit feasibility evaluation
- Risk scoring (GREEN / YELLOW / RED)
- Human or automated approval

If present:

- G-code/toolpath generation MUST NOT occur before approval
- RED feasibility MUST block generation
- Approval decisions MUST be recorded as artifacts

#### 4.4 Execution Output Handling

Machine outputs (e.g., G-code) MUST be produced via one of:

1. **Execution artifact payload**
2. **Content-addressed attachment**
3. **Export endpoint referencing artifact**

Direct inline responses are allowed **only** for:

- Legacy endpoints
- Utility lane endpoints

---

### 5. Backward Compatibility Rules

- Existing endpoints MAY continue to exist
- No endpoint must be removed to adopt this contract
- Legacy endpoints SHOULD internally delegate to the same execution engine used by Operation Lane

**Rule of thumb:**

> "Legacy endpoints may bypass governance, but they must not bypass logic."

---

### 6. Non-Goals (Explicit)

This contract does NOT:

- Define CAM Intent schemas
- Define blade/tool geometry
- Define UI workflows
- Enforce approval UI

Those are covered by separate contracts.

---

### 7. Enforcement

CI checks MAY:

- Warn when machine-executing endpoints lack execution artifacts
- Flag new G-code endpoints that bypass governance without justification
- Require explicit annotation: `LANE=UTILITY` or `LANE=OPERATION`

---

### 8. Design Principle

> **"Utilities compute. Operations decide."**
>
> The ToolBox may compute freely — but it must *decide* deliberately.

---

## Part II: Implementation Standard

### 9. Governed Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     GOVERNED OPERATION EXECUTION PIPELINE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐ │
│  │   SPEC   │ -> │   PLAN   │ -> │ DECISION │ -> │ EXECUTE  │ -> │EXPORT │ │
│  │          │    │          │    │          │    │          │    │       │ │
│  │ - Input  │    │ - Group  │    │ - Approve│    │ - Feas.  │    │- Post │ │
│  │ - Validate    │ - Sequence    │ - Order  │    │ - Gen    │    │- Emit │ │
│  │ - Hash   │    │ - Score  │    │ - Sign   │    │ - Store  │    │- File │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └───────┘ │
│       │               │               │               │              │      │
│       v               v               v               v              v      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ARTIFACT STORE                               │   │
│  │  kind: {tool}_spec | {tool}_plan | {tool}_decision | {tool}_execution│   │
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

### 10. Pipeline Stage Definitions

| Stage | Input | Output Artifact | Governance Check |
|-------|-------|-----------------|------------------|
| **SPEC** | User request | `{tool}_spec` | Input validation, schema conformance |
| **PLAN** | Spec artifact | `{tool}_plan` | Feasibility scoring, operation grouping |
| **DECISION** | Plan artifact | `{tool}_decision` | Human approval, execution order |
| **EXECUTE** | Decision artifact | `{tool}_execution` + `{tool}_op_toolpaths` | Server-side feasibility recompute |
| **EXPORT** | Execution artifact | G-code file | Post-processing, dialect conversion |

---

### 11. Artifact Kind Naming Convention

```
{tool_type}_{stage}[_{sub_type}]

Examples:
  saw_batch_spec
  saw_batch_plan
  saw_batch_decision
  saw_batch_execution
  saw_batch_op_toolpaths
  saw_batch_job_log
  saw_batch_execution_metrics_rollup

  rosette_spec
  rosette_plan
  rosette_decision
  rosette_execution

  vcarve_spec
  vcarve_execution
```

---

### 12. Feasibility Requirements

#### 12.1 Risk Buckets

| Bucket | Score Range | Action |
|--------|-------------|--------|
| **GREEN** | 70-100 | Proceed with toolpath generation |
| **YELLOW** | 40-69 | Proceed with warnings logged |
| **RED** | 0-39 | **BLOCK** toolpath generation |

#### 12.2 Server-Side Feasibility (Mandatory)

```python
# REQUIRED before ANY toolpath generation
feasibility = compute_feasibility_server_side(
    design=design,
    context=context,
    tool_profile=get_tool_profile(context.tool_id),
    material_profile=get_material_profile(context.material_id),
)

if feasibility.risk_bucket == "RED":
    # MUST NOT generate toolpaths
    # MUST persist artifact with blocked_reason
    return BlockedResult(reason=feasibility.blocking_reason)
```

#### 12.3 Mandatory Feasibility Factors

All tool types MUST evaluate:

| Factor | Description |
|--------|-------------|
| Tool capability | Can the tool physically perform this operation? |
| Material compatibility | Is the tool suitable for this material? |
| Machine limits | Within travel, speed, acceleration limits? |
| Geometric validity | Is the geometry machinable? |
| Safety margins | Adequate clearance, no collisions? |

---

### 13. G-Code Move Standard

#### 13.1 Canonical Move Structure

All G-code moves MUST use this structure:

```python
class GCodeMove:
    code: str           # G0, G1, G2, G3, M3, M5, etc.
    x: Optional[float]  # X coordinate (mm)
    y: Optional[float]  # Y coordinate (mm)
    z: Optional[float]  # Z coordinate (mm)
    f: Optional[float]  # Feed rate (mm/min)
    i: Optional[float]  # Arc center X offset (G2/G3)
    j: Optional[float]  # Arc center Y offset (G2/G3)
    s: Optional[int]    # Spindle speed (RPM)
    comment: Optional[str]
```

#### 13.2 Required Program Structure

```gcode
; HEADER (required)
G21       ; Units: mm
G90       ; Absolute positioning
G17       ; XY plane
S{rpm}    ; Spindle speed
M3        ; Spindle on

; SAFE START (required)
G0 Z{safe_z}  ; Move to safe height

; OPERATIONS
G0 X Y        ; Rapid to start
G1 Z{depth}   ; Plunge
G1 X Y F      ; Cut moves
G0 Z{safe_z}  ; Retract

; FOOTER (required)
G0 Z{safe_z}  ; Final retract
M5            ; Spindle stop
M30           ; Program end
```

#### 13.3 Multi-Operation Programs

```gcode
( Batch: {batch_label} )
( Execution: {artifact_id} )
( Ops: {ok_count} OK, {blocked_count} BLOCKED )

( ========== Op: {op_id_1} ========== )
G21  ; Units: mm
G90  ; Absolute
...
M5   ; Spindle stop

( ========== Op: {op_id_2} ========== )
G21  ; Units: mm
G90  ; Absolute
...
M5   ; Spindle stop

M30  ; Program end (final op only)
```

---

### 14. Post-Processor Standard

#### 14.1 Supported Dialects

| Dialect | Controller | Notes |
|---------|------------|-------|
| `grbl` | GRBL | Default. Simple M-codes, no O-numbers |
| `fanuc` | FANUC | O-numbers, canned cycles, G43 |
| `linuxcnc` | LinuxCNC | O-subs, named parameters |
| `mach4` | Mach4 | Similar to FANUC |

#### 14.2 Post-Processor Interface

```python
class PostProcessor(Protocol):
    dialect: str

    def process(self, moves: List[GCodeMove], metadata: ProgramMetadata) -> str:
        """Convert canonical moves to controller-specific G-code."""
        ...
```

Default dialect: `grbl` (most common hobby CNC)

---

### 15. Operator Feedback Standard

#### 15.1 Job Log Structure

```json
{
  "kind": "{tool}_job_log",
  "payload": {
    "execution_artifact_id": "reference",
    "operator": "identifier",
    "status": "COMPLETED | PARTIAL | FAILED",
    "notes": "free-form notes",
    "metrics": {
      "parts_ok": 0,
      "parts_scrap": 0,
      "cycle_time_s": 0,
      "setup_time_s": 0
    },
    "signals": {
      "burn": false,
      "tearout": false,
      "chatter": false,
      "tool_wear": false
    }
  }
}
```

#### 15.2 Learning Events

When job logs indicate issues, system MAY generate learning events:

```json
{
  "kind": "{tool}_learning_event",
  "payload": {
    "proposed_adjustments": {
      "feed_rate_multiplier": 0.9,
      "spindle_rpm_multiplier": 1.05
    },
    "policy_decision": "PROPOSE"
  }
}
```

Learning events MUST be approved (ACCEPT/REJECT) before application.

---

### 16. API Endpoint Standard

#### 16.1 Required Endpoints (Operation Lane)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/{tool}/spec` | POST | Create specification |
| `/{tool}/plan` | POST | Generate plan |
| `/{tool}/approve` | POST | Create decision |
| `/{tool}/execute` | POST | Generate toolpaths |
| `/{tool}/executions/{id}/gcode` | GET | Export G-code |
| `/{tool}/job-log` | POST | Record feedback |

#### 16.2 Optional Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/{tool}/learning-events/*` | Learning system |
| `/{tool}/metrics-rollup/*` | Metrics aggregation |
| `/{tool}/trends` | Analytics |
| `/{tool}/*.csv` | CSV exports |

---

### 17. Feature Flags

All advanced features are **off by default**:

| Flag | Purpose | Default |
|------|---------|---------|
| `{TOOL}_LEARNING_HOOK_ENABLED` | Auto-emit learning events | `false` |
| `{TOOL}_METRICS_ROLLUP_HOOK_ENABLED` | Auto-persist rollups | `false` |
| `{TOOL}_APPLY_ACCEPTED_OVERRIDES` | Apply learned multipliers | `false` |

---

## Part III: Migration & Compliance

### 18. Migration Path for Existing Systems

#### Phase 1: Artifact Wrapper (1-2 days)
Wrap existing generation in artifact persistence.

#### Phase 2: Feasibility Gate (2-3 days)
Add server-side feasibility check before generation.

#### Phase 3: Move Standardization (1-2 days)
Convert output to canonical GCodeMove format.

#### Phase 4: Full Pipeline (3-5 days)
Implement spec → plan → decision → execute stages.

#### Phase 5: Feedback Loop (2-3 days)
Add job logging and learning system.

**Total: ~10-15 days per tool type**

---

### 19. Migration Priority

| Priority | Tool Type | Rationale |
|----------|-----------|-----------|
| 1 | **Saw Lab Batch** | Reference implementation (COMPLETE) |
| 2 | **Rosette CNC** | High production volume |
| 3 | **V-Carve** | Common decorative operation |
| 4 | **Adaptive Clearing** | Complex toolpaths |
| 5 | **Drilling** | Simple, quick win |
| 6 | **Relief Carving** | Complex 3D |

---

### 20. Compliance Checklist

For a tool type to be **Governance Compliant**:

- [ ] Endpoint declares `LANE=OPERATION`
- [ ] Produces immutable artifacts at each pipeline stage
- [ ] Server-side feasibility computed before toolpath generation
- [ ] RED feasibility blocks toolpath generation
- [ ] Execution artifacts reference parent decision/plan/spec
- [ ] Toolpath artifacts contain canonical GCodeMove structures
- [ ] G-code export endpoint available
- [ ] Job log endpoint available
- [ ] Post-processor dialect support (minimum: grbl)
- [ ] All artifacts queryable by kind, session_id
- [ ] Test coverage for full pipeline

---

### 21. Reference Implementation

**CNC Saw Lab Batch** (`feature/cnc-saw-labs` branch) is the reference implementation.

**Key Files:**
```
services/api/app/saw_lab/batch_router.py          # API endpoints
services/api/app/services/saw_lab_batch_*.py      # Pipeline services
services/api/app/services/saw_lab_gcode_emit_service.py  # G-code export
docs/CNC_SAW_LAB_DEVELOPER_GUIDE.md               # Developer guide
```

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Artifact** | Immutable record of a pipeline stage output |
| **Feasibility** | Server-computed safety/capability score |
| **Risk Bucket** | GREEN/YELLOW/RED classification |
| **Decision** | Human-approved execution order |
| **Execution** | Parent artifact containing toolpath generation results |
| **Job Log** | Operator feedback after production run |
| **Learning Event** | Proposed parameter adjustment from feedback |
| **Rollup** | Aggregated metrics across multiple artifacts |
| **Post-Processor** | Controller-specific G-code dialect converter |
| **Lane** | Classification: UTILITY (stateless) or OPERATION (governed) |

---

## Appendix B: Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial unified governance contract |

---

## Appendix C: Related Documents

| Document | Purpose |
|----------|---------|
| `CNC_SAW_LAB_DEVELOPER_GUIDE.md` | Detailed implementation guide for Saw Lab |
| `ENDPOINT_TRUTH_MAP.md` | Lane annotations for all endpoints (TODO) |
| `RMOS_GOVERNANCE_CONTRACT.md` | Parent RMOS governance (if exists) |
