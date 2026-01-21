# Art Studio Workflow Integration

**Date:** December 19, 2025
**Purpose:** Connect Pattern Library generators to Workflow State Machine
**Location:** `services/api/app/art_studio/`

---

## Overview

The Art Studio Workflow Integration bridges the Pattern Library (generators, patterns, snapshots) with the governance-compliant Workflow State Machine. This enables:

- Creating workflow sessions from saved patterns
- Generating designs directly from parametric generators
- Restoring work-in-progress from snapshots
- Server-side feasibility evaluation
- Human approval workflow before toolpath generation

---

## Files Created

### 1. Integration Service

**Path:** `services/api/app/art_studio/services/workflow_integration.py`

| Function | Purpose |
|----------|---------|
| `create_workflow_from_pattern()` | Create session from pattern library item |
| `create_workflow_from_generator()` | Create session directly from generator |
| `create_workflow_from_snapshot()` | Restore session from saved snapshot |
| `evaluate_session_feasibility()` | Run server-side feasibility (stub - wire to RMOS) |
| `approve_session()` | Approve for toolpath generation |
| `reject_session()` | Reject session |
| `request_session_revision()` | Request design changes |
| `update_session_design()` | Update design parameters |
| `save_session_as_snapshot()` | Save work-in-progress |
| `list_active_sessions()` | List non-archived sessions |
| `get_session_status()` | Get detailed session state |
| `get_available_generators()` | List generators for UI |

### 2. API Routes

**Path:** `services/api/app/art_studio/api/workflow_routes.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/art-studio/workflow/from-pattern` | POST | Create from pattern |
| `/api/art-studio/workflow/from-generator` | POST | Create from generator |
| `/api/art-studio/workflow/from-snapshot` | POST | Restore from snapshot |
| `/api/art-studio/workflow/sessions` | GET | List active sessions |
| `/api/art-studio/workflow/sessions/{id}` | GET | Get session status |
| `/api/art-studio/workflow/sessions/{id}/design` | PUT | Update design |
| `/api/art-studio/workflow/sessions/{id}/feasibility` | POST | Evaluate feasibility |
| `/api/art-studio/workflow/sessions/{id}/approve` | POST | Approve session |
| `/api/art-studio/workflow/sessions/{id}/reject` | POST | Reject session |
| `/api/art-studio/workflow/sessions/{id}/request-revision` | POST | Request revision |
| `/api/art-studio/workflow/sessions/{id}/save-snapshot` | POST | Save snapshot |
| `/api/art-studio/workflow/generators` | GET | List generators |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ART STUDIO WORKFLOW INTEGRATION                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   Pattern    │     │  Workflow    │     │   Snapshot   │        │
│  │    Store     │────▶│ Integration  │◀────│    Store     │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│         │                    │                    │                 │
│         │                    ▼                    │                 │
│         │           ┌──────────────┐              │                 │
│         │           │  Workflow    │              │                 │
│         └──────────▶│   State      │◀─────────────┘                 │
│                     │   Machine    │                                │
│  ┌──────────────┐   └──────────────┘                                │
│  │  Generator   │          │                                        │
│  │  Registry    │──────────┘                                        │
│  └──────────────┘          │                                        │
│                            ▼                                        │
│                    ┌──────────────┐                                 │
│                    │ Feasibility  │                                 │
│                    │   Engine     │                                 │
│                    │   (RMOS)     │                                 │
│                    └──────────────┘                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Workflow States

The integration follows the canonical workflow state machine:

```
DRAFT → CONTEXT_READY → FEASIBILITY_REQUESTED → FEASIBILITY_READY
                                                       │
                              ┌────────────────────────┼────────────────┐
                              │                        │                │
                              ▼                        ▼                ▼
                    DESIGN_REVISION_REQUIRED      APPROVED          REJECTED
                              │                        │                │
                              │                        ▼                │
                              │              TOOLPATHS_REQUESTED        │
                              │                        │                │
                              │                        ▼                │
                              │               TOOLPATHS_READY           │
                              │                        │                │
                              └────────────────────────┼────────────────┘
                                                       │
                                                       ▼
                                                   ARCHIVED
```

---

## Integration with Main App

Add the following to `services/api/app/main.py`:

```python
from app.art_studio.api.workflow_routes import router as art_studio_workflow_router

app.include_router(art_studio_workflow_router)
```

---

## Usage Examples

### Create Workflow from Pattern

```bash
curl -X POST http://localhost:8000/api/art-studio/workflow/from-pattern \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "pat_abc123def456",
    "mode": "design_first",
    "context_refs": {
      "material_preset_id": "sitka_spruce",
      "tool_preset_id": "1mm_endmill"
    }
  }'
```

### Create Workflow from Generator

```bash
curl -X POST http://localhost:8000/api/art-studio/workflow/from-generator \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "basic_rings",
    "outer_diameter_mm": 100.0,
    "inner_diameter_mm": 10.0,
    "params": {"ring_count": 5},
    "mode": "design_first"
  }'
```

### Evaluate Feasibility

```bash
curl -X POST http://localhost:8000/api/art-studio/workflow/sessions/{session_id}/feasibility
```

### Approve Session

```bash
curl -X POST http://localhost:8000/api/art-studio/workflow/sessions/{session_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"note": "Approved for production"}'
```

### Save as Snapshot

```bash
curl -X POST http://localhost:8000/api/art-studio/workflow/sessions/{session_id}/save-snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Torres-style rosette v2",
    "notes": "Updated ring spacing",
    "tags": ["torres", "classical", "wip"]
  }'
```

---

## TODO: Required Integrations

The following integrations are marked with `# TODO` in the code:

### 1. RMOS Feasibility Integration

**Location:** `workflow_integration.py:~280`

```python
# Replace stub with actual RMOS integration:
from app.rmos.feasibility_fusion import evaluate_feasibility
from app.rmos.context import RmosContext

context = request.context_override or session.context
rmos_ctx = RmosContext.from_dict(context)
report = evaluate_feasibility(session.design, rmos_ctx)

result = FeasibilityResult(
    score=report.overall_score,
    risk_bucket=RiskBucket(report.overall_risk.value),
    warnings=report.recommendations,
    meta={
        "source": "server_recompute",
        "feasibility_hash": compute_hash(report),
    }
)
```

### 2. Preset Registry Integration

**Location:** `workflow_integration.py:~420`

```python
# Replace stub with actual preset loading:
from app.rmos.presets import get_preset_registry

registry = get_preset_registry()
material = registry.get_material(refs.material_preset_id)
context["material"] = material.to_dict()
```

---

## Governance Compliance

This integration enforces the following governance requirements:

| Requirement | Implementation |
|-------------|----------------|
| Server-side feasibility | All feasibility computed server-side, never from client |
| Artifact persistence | Run artifacts created at each state change |
| Risk bucket enforcement | RED/UNKNOWN blocks unless explicitly overridden |
| Explicit approval | Toolpaths require explicit user approval |
| Audit trail | All state transitions logged in session events |

---

## Key Imports

```python
# Integration Service
from app.art_studio.services.workflow_integration import (
    create_workflow_from_pattern,
    create_workflow_from_generator,
    create_workflow_from_snapshot,
    evaluate_session_feasibility,
    approve_session,
    get_session_status,
)

# Workflow State Machine
from app.workflow.state_machine import (
    WorkflowSession,
    WorkflowMode,
    WorkflowState,
    ActorRole,
)

# Pattern Library
from app.art_studio.services.pattern_store import PatternStore
from app.art_studio.services.generators.registry import generate_spec

# Snapshots
from app.art_studio.services.design_snapshot_store import DesignSnapshotStore
```

---

## Related Files

| Component | Path |
|-----------|------|
| Workflow State Machine | `app/workflow/state_machine.py` |
| Generator Registry | `app/art_studio/services/generators/registry.py` |
| Pattern Store | `app/art_studio/services/pattern_store.py` |
| Snapshot Store | `app/art_studio/services/design_snapshot_store.py` |
| RMOS Feasibility | `app/rmos/feasibility_fusion.py` |
| RMOS Context | `app/rmos/context.py` |

---

## PromotionIntentV1 → CamPromotionRequestV1 Bridge (Phase 32.0 / 33.0)

This section documents the **promotion-layer artifacts** added in Phase 32.0 and Phase 33.0.
These artifacts are **layered on top of** the original design-first workflow and **do not replace**
the underlying workflow state machine described earlier in this document.

Art Studio remains an **ornamental authoring and orchestration system**.
It does not execute CAM, generate toolpaths, or make manufacturing decisions.

---

### Why this bridge exists

The design-first workflow culminates in an **APPROVED** session.
At that point, downstream systems need a **stable, automation-safe handoff** that:

- Is versioned and strictly validated
- Can be consumed by CI and external tooling
- Does not grant manufacturing authority

Phase 32.0 and 33.0 introduce two explicit artifacts to satisfy this need.

---

### Phase 32.0 — PromotionIntentV1 (Canonical Intent Export)

**PromotionIntentV1** is the canonical, strict representation of approved ornamental intent.

It is:
- Versioned (`intent_version: "v1"`)
- Approval-gated
- Deterministic
- Safe for CI and automation

#### Canonical export endpoint (hard-gated)

```
GET /api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json
```

- Returns raw `PromotionIntentV1`
- Returns **403** if the session is not `APPROVED`
- Intended for CI, automation, and downstream orchestration

#### UI wrapper endpoint (ergonomic)

```
POST /api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1
```

Returns:
```
{ ok, intent?, blocked_reason? }
```

- Never throws
- Used by UI for gating and messaging
- Does not change the canonical contract

This split is intentional:
- **Automation** uses the canonical `.json` export
- **UI** uses the wrapper

---

### Phase 33.0 — CamPromotionRequestV1 (CAM Orchestration Bridge)

**CamPromotionRequestV1** represents a **queued request** for downstream CAM systems
to prepare work based on an approved intent.

It is an orchestration artifact only.

#### Promotion endpoint

```
POST /api/art/design-first-workflow/sessions/{session_id}/promote_to_cam
```

Returns:
```
{ ok, request?, blocked_reason? }
```

- If session not approved → `{ ok:false, blocked_reason }`
- If approved → `{ ok:true, request: CamPromotionRequestV1 }`

#### Key properties

- `promotion_request_version: "v1"`
- `promotion_request_id` (UUID)
- `session_id`
- Embedded `intent: PromotionIntentV1` (traceability)
- `design_fingerprint`, `feasibility_fingerprint`
- `status: "QUEUED"`

This artifact **does not**:
- Execute CAM
- Generate toolpaths
- Generate G-code
- Decide manufacturability

---

### Idempotency contract

Re-promoting the same intent must not create duplicate requests.

Phase 33.0 enforces idempotency using a stable fingerprint key:

```
key = "{design_fingerprint}:{feasibility_fingerprint}"
```

If a request already exists for that key, the same
`promotion_request_id` is returned.

This allows safe retries from UI and CI.

---

### Persistence (release-safe)

Promotion requests are stored as file-backed JSON under the Art Studio data root:

```
art_studio/
  cam_promotion/
    requests/{promotion_request_id}.json
    index.json
```

This approach is:
- Auditable
- Deterministic
- Safe for early releases

Database backing may be added later **without changing the external contract**.

---

### Fencing and scope rules

The promotion bridge lives under:

```
services/api/app/art_studio/**
```

It must remain fenced from CAM engine internals:

- ✅ Allowed: schemas, workflow orchestration, persistence, API wrappers
- ❌ Disallowed: imports from `app.cam` or `app.cam_core`, toolpath logic, execution logic

If a change cannot be expressed as **ornamental intent** or **orchestration metadata**,
it does not belong in Art Studio.

---

### Test and release gate

These promotion artifacts are enforced by contract tests:

- Phase 32.0: PromotionIntentV1 export contract tests
- Phase 33.0: CAM promotion bridge tests (including idempotency)

Release gate:

```
make api-verify
```

CI must run `make api-verify` on push and pull requests to prevent drift.

---

**Document Version:** 1.1
**Last Updated:** January 20, 2026
