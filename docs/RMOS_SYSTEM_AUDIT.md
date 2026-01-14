# RMOS System Audit

**Version:** 1.0.0
**Date:** 2026-01-13
**Status:** ~80% Production-Ready

---

## Executive Summary

The **Rosette Manufacturing Orchestration System (RMOS)** is the governance backbone of luthiers-toolbox. It manages run lifecycles, feasibility scoring, safety policies, and manufacturing workflow state. The core infrastructure is robust with immutable run artifacts, production-ready feasibility scoring, and a mature 10-state workflow machine. The primary gaps are test coverage and CAM feasibility engine completion.

---

## 1. Architecture Overview

### Core Principle: Manufacturing Governance

RMOS ensures that manufacturing operations are:
- **Tracked** via immutable run artifacts
- **Assessed** via feasibility scoring engines
- **Gated** via safety policies
- **Orchestrated** via workflow state machines

```
┌─────────────────────────────────────────────────────────────────┐
│                           RMOS Core                              │
├─────────────────────────────────────────────────────────────────┤
│  Run Management                                                  │
│  ├── Immutable Artifacts (date-partitioned JSON)                 │
│  ├── SHA256 Content Addressing                                   │
│  └── Lifecycle Tracking (create → archive)                       │
├─────────────────────────────────────────────────────────────────┤
│  Feasibility Engines                                             │
│  ├── Baseline V1 (production)                                    │
│  ├── CAM Mode Stubs (vcarve, roughing, drilling, etc.)           │
│  └── Risk Bucketing (GREEN/YELLOW/RED/UNKNOWN)                   │
├─────────────────────────────────────────────────────────────────┤
│  Safety Policy                                                   │
│  ├── Environment-Driven (CI_STRICT_SAFETY)                       │
│  ├── RED Blocking (mandatory)                                    │
│  └── UNKNOWN → RED Normalization                                 │
├─────────────────────────────────────────────────────────────────┤
│  Workflow State Machine                                          │
│  ├── 10 States (DRAFT → ARCHIVED)                                │
│  ├── 3 Modes (Design-First, Constraint-First, AI-Assisted)       │
│  └── Session Management                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Separation

| Layer | Responsibility | NOT Responsible For |
|-------|----------------|---------------------|
| **Runs V2** | Artifact storage, lifecycle, querying | Feasibility decisions |
| **Feasibility Engines** | Risk scoring, warnings | Safety enforcement |
| **Safety Policy** | Gate/block decisions | Workflow advancement |
| **Workflow** | State transitions, sessions | Artifact storage |

---

## 2. Backend Structure

### Directory Layout

```
services/api/app/rmos/
├── __init__.py
├── runs_v2/                          # Primary run management
│   ├── __init__.py
│   ├── api_runs.py                   ✅ 15+ endpoints
│   ├── store.py                      ✅ Date-partitioned immutable storage
│   ├── schemas.py                    ✅ Governance-compliant Pydantic models
│   ├── query.py                      ✅ Filtering, pagination
│   └── handoff.py                    ✅ Cross-system handoff
├── engines/
│   ├── feasibility_baseline_v1.py    ✅ Production engine
│   ├── feasibility_stub.py           ⚠️ Dev-only placeholder
│   ├── cam_feasibility.py            🟡 Stubs for CAM modes
│   └── registry.py                   ✅ Engine dispatch
├── policies/
│   ├── safety_policy.py              ✅ Central safety gate
│   ├── saw_safety_gate.py            ✅ Saw-specific wrapper
│   └── policy_loader.py              ✅ JSON policy ingestion
├── workflow/
│   ├── state_machine.py              ✅ 10-state FSM
│   ├── session_manager.py            ✅ Session lifecycle
│   ├── schemas_workflow.py           ✅ WorkflowSession model
│   └── transitions.py                ✅ State transition logic
├── api/
│   ├── rmos_runs_router.py           ✅ /api/rmos/runs/*
│   ├── feasibility_router.py         ✅ /api/rmos/feasibility/*
│   ├── saw_routes.py                 ✅ /api/saw/*
│   └── workflow_router.py            ✅ /api/rmos/workflow/*
├── cam/                              # CAM integration layer
│   ├── normalize_intent.py           ✅ Intent normalization
│   ├── schemas_intent.py             ✅ CAM intent schemas
│   └── mode_dispatcher.py            🟡 Stub dispatcher
├── saw_lab/                          # Saw operation subsystem
│   ├── service.py                    ✅ Saw operations
│   ├── schemas_compare.py            ✅ Comparison schemas
│   └── store.py                      ✅ Saw artifact storage
└── tests/                            ⚠️ Only 3 test files
    ├── test_runs_v2_store.py
    ├── test_feasibility_baseline.py
    └── test_safety_policy.py
```

---

## 3. Component Status

### Tier 1: Production-Ready

| Component | Location | Features |
|-----------|----------|----------|
| **Run Artifact Store** | `runs_v2/store.py` | Immutable JSON, date partitioning, SHA256 |
| **Baseline V1 Engine** | `engines/feasibility_baseline_v1.py` | Weighted scoring (0-100), risk bucketing |
| **Safety Policy** | `policies/safety_policy.py` | Environment gating, RED blocking |
| **Workflow FSM** | `workflow/state_machine.py` | 10 states, 3 modes, session management |
| **Saw Operations** | `saw_lab/service.py` | Batch processing, comparison |
| **Runs API** | `api/rmos_runs_router.py` | Full CRUD, filtering, pagination |

### Tier 2: Functional with Gaps

| Component | Status | Gap |
|-----------|--------|-----|
| **CAM Feasibility Engines** | Stubs only | 6 modes return GREEN by default |
| **Intent Normalization** | 80% | Some CAM intents not mapped |
| **FANUC Scheduling** | Planned | Not implemented |

### Tier 3: Development Only

| Component | Status | Notes |
|-----------|--------|-------|
| **Feasibility Stub** | Dev only | Returns GREEN for all inputs |
| **Mode Dispatcher** | Skeleton | Routes to stubs |

---

## 4. Run Artifact System

### Storage Architecture

```
data/rmos/runs/
├── 2026/
│   ├── 01/
│   │   ├── 13/
│   │   │   ├── run_abc123.json
│   │   │   ├── run_def456.json
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── index.json                        # Quick lookup index
```

### Immutability Guarantees

| Property | Implementation |
|----------|----------------|
| **Content Hash** | SHA256 of JSON payload |
| **Write-Once** | No update after creation |
| **Date Partitioning** | `YYYY/MM/DD/` structure |
| **Audit Trail** | `created_at`, `updated_at` timestamps |

### RunArtifact Schema

```python
class RunArtifact:
    run_id: str                       # UUID
    parent_run_id: Optional[str]      # For derived runs
    artifact_type: str                # rosette, cam, saw, etc.
    status: RunStatus                 # PENDING, RUNNING, COMPLETED, FAILED
    feasibility: FeasibilitySummary   # Score + bucket + warnings
    payload: Dict[str, Any]           # Type-specific data
    content_hash: str                 # SHA256
    created_at: datetime
    updated_at: datetime
```

---

## 5. Feasibility Scoring

### Baseline V1 Engine (Production)

**Location:** `engines/feasibility_baseline_v1.py`

| Feature | Implementation |
|---------|----------------|
| **Scoring Range** | 0-100 (integer) |
| **Weighted Factors** | Material, tooling, geometry, thermal |
| **Risk Buckets** | GREEN (≥80), YELLOW (50-79), RED (<50), UNKNOWN |
| **Warnings** | String list with severity hints |

### Risk Bucketing Logic

```python
def bucket_from_score(score: int) -> RiskBucket:
    if score >= 80:
        return RiskBucket.GREEN
    elif score >= 50:
        return RiskBucket.YELLOW
    else:
        return RiskBucket.RED
```

### CAM Mode Stubs

| Mode | Engine File | Status |
|------|-------------|--------|
| **vcarve** | `cam_feasibility.py` | 🟡 Returns GREEN |
| **roughing** | `cam_feasibility.py` | 🟡 Returns GREEN |
| **drilling** | `cam_feasibility.py` | 🟡 Returns GREEN |
| **biarc** | `cam_feasibility.py` | 🟡 Returns GREEN |
| **relief** | `cam_feasibility.py` | 🟡 Returns GREEN |
| **adaptive** | `cam_feasibility.py` | 🟡 Returns GREEN |

**Impact:** All CAM operations pass feasibility by default - no real risk assessment until engines are implemented.

---

## 6. Safety Policy

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Safety Policy Gate                           │
├─────────────────────────────────────────────────────────────────┤
│  Input: FeasibilitySummary                                       │
│    ├── score: int (0-100)                                        │
│    ├── bucket: RiskBucket (GREEN/YELLOW/RED/UNKNOWN)             │
│    └── warnings: List[str]                                       │
├─────────────────────────────────────────────────────────────────┤
│  Environment Checks                                              │
│    ├── CI_STRICT_SAFETY: bool (default True in CI)               │
│    ├── RMOS_ALLOW_YELLOW: bool (default False)                   │
│    └── RMOS_ALLOW_UNKNOWN: bool (default False)                  │
├─────────────────────────────────────────────────────────────────┤
│  Output: SafetyDecision                                          │
│    ├── allowed: bool                                             │
│    ├── reason: str                                               │
│    └── override_required: bool                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Decision Matrix

| Bucket | CI_STRICT=True | CI_STRICT=False | Override Available |
|--------|----------------|-----------------|-------------------|
| **GREEN** | ✅ ALLOW | ✅ ALLOW | N/A |
| **YELLOW** | ❌ BLOCK | ⚠️ WARN | Yes |
| **RED** | ❌ BLOCK | ❌ BLOCK | No |
| **UNKNOWN** | ❌ BLOCK | ❌ BLOCK | No |

### UNKNOWN Normalization

The safety policy **normalizes UNKNOWN → RED** before decision:

```python
def normalize_bucket(bucket: RiskBucket) -> RiskBucket:
    if bucket == RiskBucket.UNKNOWN:
        return RiskBucket.RED
    return bucket
```

---

## 7. Workflow State Machine

### States (10)

```
DRAFT → PENDING_REVIEW → IN_REVIEW → APPROVED → SCHEDULED →
    IN_PROGRESS → COMPLETED → ARCHIVED

Alternative paths:
    IN_REVIEW → REJECTED
    IN_REVIEW → REVISION_REQUESTED → DRAFT
```

| State | Description | Allowed Transitions |
|-------|-------------|---------------------|
| **DRAFT** | Initial design state | PENDING_REVIEW |
| **PENDING_REVIEW** | Awaiting reviewer | IN_REVIEW |
| **IN_REVIEW** | Active review | APPROVED, REJECTED, REVISION_REQUESTED |
| **REVISION_REQUESTED** | Returned for changes | DRAFT |
| **APPROVED** | Design approved | SCHEDULED |
| **REJECTED** | Design rejected | (terminal) |
| **SCHEDULED** | Queued for execution | IN_PROGRESS |
| **IN_PROGRESS** | Currently executing | COMPLETED, FAILED |
| **COMPLETED** | Successfully finished | ARCHIVED |
| **ARCHIVED** | Historical record | (terminal) |

### Workflow Modes (3)

| Mode | Description | Primary Use Case |
|------|-------------|------------------|
| **Design-First** | Design → Feasibility → Execution | Art Studio patterns |
| **Constraint-First** | Constraints → Design → Execution | CAM operations |
| **AI-Assisted** | AI suggestions → Human review → Execution | Blueprint analysis |

### WorkflowSession Schema

```python
class WorkflowSession:
    session_id: str
    run_id: str                       # Associated run artifact
    state: WorkflowState
    mode: WorkflowMode
    transitions: List[StateTransition]
    created_by: str
    created_at: datetime
    updated_at: datetime
```

---

## 8. API Endpoints

### Runs V2 (`/api/rmos/runs`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/` | GET | ✅ List runs with filtering |
| `/` | POST | ✅ Create run |
| `/{run_id}` | GET | ✅ Get run |
| `/{run_id}` | DELETE | ✅ Delete run |
| `/{run_id}/feasibility` | POST | ✅ Score feasibility |
| `/{run_id}/status` | PATCH | ✅ Update status |
| `/batch` | POST | ✅ Batch create |
| `/batch/feasibility` | POST | ✅ Batch scoring |
| `/search` | POST | ✅ Advanced search |
| `/stats` | GET | ✅ Aggregate statistics |

### Feasibility (`/api/rmos/feasibility`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/score` | POST | ✅ Score design |
| `/batch` | POST | ✅ Batch scoring |
| `/engines` | GET | ✅ List available engines |
| `/engines/{engine_id}/status` | GET | ✅ Engine health |

### Workflow (`/api/rmos/workflow`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/sessions` | GET | ✅ List sessions |
| `/sessions` | POST | ✅ Create session |
| `/sessions/{id}` | GET | ✅ Get session |
| `/sessions/{id}/transition` | POST | ✅ Advance state |
| `/sessions/{id}/transitions` | GET | ✅ Get history |
| `/modes` | GET | ✅ List modes |

### Saw Operations (`/api/saw`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/operations` | GET | ✅ List operations |
| `/operations` | POST | ✅ Create operation |
| `/operations/{id}` | GET | ✅ Get operation |
| `/operations/batch` | POST | ✅ Batch create |
| `/compare` | POST | ✅ Compare operations |
| `/compare/snapshots` | GET | ✅ List comparisons |

### Safety (`/api/rmos/safety`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/check` | POST | ✅ Check safety |
| `/policy` | GET | ✅ Get active policy |
| `/override` | POST | ⚠️ Requires admin |

**Total: 50+ endpoints, ~95% functional**

---

## 9. Frontend Components

### Vue Components (47 identified)

| Category | Components | Status |
|----------|------------|--------|
| **Run Management** | RunList, RunDetail, RunCreate | ✅ Functional |
| **Feasibility** | FeasibilityScore, RiskBadge, WarningList | ✅ Functional |
| **Workflow** | WorkflowStatus, StateTransition, SessionView | ✅ Functional |
| **Saw Lab** | SawOperation, SawCompare, SawBatch | ✅ Functional |
| **Safety** | SafetyGate, OverrideModal, PolicyView | ✅ Functional |

### API Integration

| Module | Location | Status |
|--------|----------|--------|
| `runs.ts` | `client/src/api/rmos/` | ✅ Complete |
| `feasibility.ts` | `client/src/api/rmos/` | ✅ Complete |
| `workflow.ts` | `client/src/api/rmos/` | ✅ Complete |
| `saw.ts` | `client/src/api/` | ✅ Complete |

---

## 10. Test Coverage

### Current State

| Test File | Components | Tests |
|-----------|-----------|-------|
| `test_runs_v2_store.py` | Run storage | ~15 tests |
| `test_feasibility_baseline.py` | Baseline V1 | ~12 tests |
| `test_safety_policy.py` | Safety gate | ~10 tests |

**Total: ~37 tests across 3 files**

### Coverage Gaps

| Component | Test File | Status |
|-----------|-----------|--------|
| **Workflow FSM** | (missing) | ❌ No tests |
| **Session Manager** | (missing) | ❌ No tests |
| **CAM Feasibility** | (missing) | ❌ No tests |
| **Saw Operations** | (missing) | ❌ No tests |
| **Intent Normalization** | (missing) | ❌ No tests |
| **API Routers** | (missing) | ❌ No integration tests |

**Assessment: 6 major components lack tests**

---

## 11. Integration Points

### Art Studio Integration

- **Service:** `art_studio_run_service.py`
- **Function:** Creates RunArtifact for rosette designs
- **Flow:** Art Studio → RunArtifact → Feasibility → Workflow

### CAM Integration

- **Service:** `cam/mode_dispatcher.py`
- **Function:** Routes CAM intents to feasibility engines
- **Gap:** All CAM engines return GREEN (stubs)

### Blueprint Integration

- **Status:** Planned, not implemented
- **Goal:** Blueprint analysis → RunArtifact → Feasibility

### Telemetry Integration

- **Status:** Complete
- **Flow:** Manufacturing events → Telemetry → Cost Attribution

---

## 12. Identified Gaps

### Gap 1: Test Coverage

**Issue:** Only 3 test files for 15+ modules
**Impact:** Refactoring risk, regression potential
**Effort:** 16 hours
**Priority:** HIGH

### Gap 2: CAM Feasibility Engines

**Issue:** 6 CAM modes return GREEN by default
**Impact:** No real risk assessment for CAM operations
**Effort:** 20 hours (4h per engine)
**Priority:** HIGH

### Gap 3: FANUC Scheduling

**Issue:** Not implemented
**Impact:** Industrial CNC integration blocked
**Effort:** 12 hours
**Priority:** MEDIUM

### Gap 4: Blueprint RMOS Bridge

**Issue:** Blueprint analysis doesn't create runs
**Impact:** Blueprint-to-CAM workflow ungoverned
**Effort:** 8 hours
**Priority:** MEDIUM

### Gap 5: Intent Normalization Completion

**Issue:** Some CAM intents not mapped
**Impact:** Edge cases may fail silently
**Effort:** 4 hours
**Priority:** LOW

---

## 13. Path to Full Completion

### Phase 1: Test Coverage (~20 hours)

| Task | Hours | Outcome |
|------|-------|---------|
| Workflow FSM tests | 4h | State transition coverage |
| Session Manager tests | 3h | Session lifecycle coverage |
| CAM Feasibility tests | 4h | Stub behavior verification |
| Saw Operations tests | 3h | Batch processing coverage |
| API Integration tests | 6h | Router behavior coverage |

### Phase 2: CAM Engine Implementation (~24 hours)

| Task | Hours | Outcome |
|------|-------|---------|
| VCarve feasibility engine | 4h | Real toolpath risk assessment |
| Roughing feasibility engine | 4h | Material removal risk |
| Drilling feasibility engine | 3h | Hole operation risk |
| Biarc feasibility engine | 4h | Curve fitting risk |
| Relief feasibility engine | 4h | 3D carving risk |
| Adaptive feasibility engine | 5h | Pocketing risk |

### Phase 3: Remaining Features (~8 hours)

| Task | Hours | Outcome |
|------|-------|---------|
| Blueprint RMOS bridge | 4h | Governed blueprint workflow |
| Intent normalization completion | 2h | Full CAM coverage |
| FANUC scheduling stub | 2h | Industrial integration ready |

**Total: ~52 hours to full completion**

---

## 14. Summary

**RMOS is 80% production-ready and serves as the governance backbone of luthiers-toolbox.**

### What Works

- ✅ Immutable run artifact storage with SHA256 content addressing
- ✅ Date-partitioned JSON persistence with quick lookup index
- ✅ Baseline V1 feasibility scoring (0-100 weighted, 4-bucket risk)
- ✅ Environment-driven safety policy with RED/UNKNOWN blocking
- ✅ 10-state workflow state machine with 3 modes
- ✅ Session management with transition history
- ✅ 50+ API endpoints across 4 router categories
- ✅ 47 Vue frontend components
- ✅ Saw operation subsystem with batch processing

### What's Missing

- ⚠️ Test coverage (only 3 of 15+ modules tested)
- ⚠️ CAM feasibility engines (6 modes return GREEN by default)
- ⚠️ FANUC industrial scheduling
- ⚠️ Blueprint RMOS bridge

### Comparison to Other Systems

| Aspect | RMOS | Blueprint | Art Studio | CAM |
|--------|------|-----------|------------|-----|
| Core Algorithms | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| API Endpoints | ✅ 95% | ✅ 93% | ✅ 90% | ⚠️ 65% |
| Persistence | ✅ Complete | ✅ Complete | ✅ Complete | ❌ Missing |
| Test Coverage | ⚠️ 20% | ⚠️ Partial | ✅ Good | ⚠️ Gaps |
| Hours to MVP | ~48h | ~24h | ~30h | ~50h |

**RMOS provides the governance foundation that all other systems depend on. Completing its test coverage and CAM engines should precede or parallel other MVP work.**

---

*Document generated as part of luthiers-toolbox system audit.*
