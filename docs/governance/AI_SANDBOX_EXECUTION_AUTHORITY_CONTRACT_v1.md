# AI Sandbox & Execution Authority Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 16, 2025
**Status:** AUTHORITATIVE
**Source:** Vision Engine Bundle - GOVERNANCE.md

---

## Governance Statement

This document defines the **canonical separation of authority** between AI advisory systems and RMOS execution authority within the Luthier's ToolBox platform. This separation is **non-negotiable** and enforced at compile-time, CI-time, and runtime.

### Core Principle

> **AI is advisory. RMOS is authoritative.**
>
> AI may suggest, analyze, and propose. Only RMOS may approve, execute, and persist.

---

## Role Definitions

### RMOS (Execution Authority)

RMOS is the **sole execution authority** for manufacturing decisions.

| Capability | Description | Authority Level |
|------------|-------------|-----------------|
| Compute Feasibility | Evaluate design safety and manufacturability | EXCLUSIVE |
| Enforce Safety Policy | Apply safety rules and constraints | EXCLUSIVE |
| Control Workflow State | Manage state transitions (DRAFT → APPROVED) | EXCLUSIVE |
| Generate Toolpaths | Produce manufacturing outputs (G-code) | EXCLUSIVE |
| Write Run Artifacts | Persist immutable audit records | EXCLUSIVE |

### AI Sandbox (Advisory Only)

AI operates in a **sandbox with strict limitations**.

| Capability | Description | Authority Level |
|------------|-------------|-----------------|
| Propose Candidates | Suggest parameter adjustments | ADVISORY |
| Request Feasibility | Query RMOS via public APIs | ADVISORY |
| Analyze Artifacts | Read logs, snapshots, run history | ADVISORY |
| Generate Images | Create visualization assets | ADVISORY |

### AI MUST NEVER:

| Forbidden Action | Reason |
|------------------|--------|
| Approve workflows | Execution authority violation |
| Generate toolpaths | Manufacturing output violation |
| Write/modify run artifacts | Audit integrity violation |
| Bypass server-side feasibility | Safety enforcement violation |
| Import RMOS internals | Coupling prevention |

---

## Directory Contract

### Authoritative Zone (Deterministic)

**Path:** `services/api/app/rmos/**`

All code in this zone MUST be:
- Deterministic (same inputs → same outputs)
- Type-safe (full Pydantic/typing coverage)
- Test-covered (minimum 90% coverage)
- Audit-grade (all decisions logged)

### Advisory Zone (Experimental)

**Path:** `services/api/app/_experimental/ai/**`
**Path:** `services/api/app/_experimental/ai_graphics/**`

All code in this zone:
- MAY be non-deterministic
- MAY use external AI services
- MUST NOT import from RMOS internals
- MUST NOT call authority functions
- MUST NOT write to authoritative paths

---

## Promotion Policy

AI code may be promoted to production status **only if** it meets all criteria:

### Promotion Requirements

| Requirement | Threshold | Verification |
|-------------|-----------|--------------|
| Deterministic | 100% | Golden file tests |
| Type-safe | 100% | mypy strict mode |
| Test coverage | 100% | pytest --cov |
| Contract tests | Pass | Golden file matching |
| Code review | Approved | Maintainer sign-off |

### Promotion Target

Promoted AI code goes to:
```
services/api/app/rmos/assist/**
```

**NEVER** to core execution modules:
- `rmos/workflow/`
- `rmos/toolpaths/`
- `rmos/runs/`
- `rmos/feasibility/`

---

## Required Execution Spine

AI suggestions do not grant authority. The execution spine is **mandatory**:

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ AI Suggest  │ ──▶ │ RMOS Feasibility│ ──▶ │ Workflow     │ ──▶ │ RMOS        │ ──▶ │ Run Artifact │
│ (advisory)  │     │ (authoritative) │     │ APPROVED     │     │ Toolpaths   │     │ (immutable)  │
└─────────────┘     └─────────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
      │                    │                      │                    │                    │
      │                    │                      │                    │                    │
   Optional            REQUIRED              REQUIRED             REQUIRED            REQUIRED
```

### Spine Invariants

1. **Feasibility is server-computed** — Client feasibility is stripped/ignored
2. **Approval requires GREEN feasibility** — No shortcuts
3. **Toolpaths require APPROVED state** — No direct generation
4. **All outcomes create artifacts** — Success AND failure recorded

---

## Automated Guards

### CI Enforcement

CI runs on every PR and enforces:

| Check | Script | Failure = Block PR |
|-------|--------|-------------------|
| Import boundaries | `check_ai_import_boundaries.py` | YES |
| Forbidden calls | `check_ai_forbidden_calls.py` | YES |
| Write paths | `check_ai_write_paths.py` | YES |

### Pre-commit Hooks

Local enforcement before push:

```bash
pip install pre-commit
pre-commit install
```

### Runtime Guards

Server-side enforcement:

- Workflow state machine rejects invalid transitions
- Feasibility gate blocks non-GREEN approvals
- Run store validates artifact integrity

---

## Forbidden Patterns

### AI Sandbox MUST NOT Import:

```python
# These imports are FORBIDDEN in _experimental/ai/**

from rmos.workflow import ...           # ❌ FORBIDDEN
from rmos.toolpaths import ...          # ❌ FORBIDDEN
from rmos.runs import ...               # ❌ FORBIDDEN
from rmos.api_workflow import ...       # ❌ FORBIDDEN
from rmos.api_toolpaths import ...      # ❌ FORBIDDEN

from app.rmos.workflow import ...       # ❌ FORBIDDEN
from app.rmos.toolpaths import ...      # ❌ FORBIDDEN
from app.rmos.runs import ...           # ❌ FORBIDDEN
```

### AI Sandbox MUST NOT Call:

```python
# These function calls are FORBIDDEN

approve(...)                # ❌ FORBIDDEN - execution authority
generate_toolpaths(...)     # ❌ FORBIDDEN - manufacturing output
create_run(...)             # ❌ FORBIDDEN - artifact creation
persist_run(...)            # ❌ FORBIDDEN - artifact persistence
transition_workflow(...)    # ❌ FORBIDDEN - state control
```

### AI Sandbox MUST NOT Write To:

```
app/rmos/**                 # ❌ FORBIDDEN
rmos/runs/**                # ❌ FORBIDDEN
rmos/toolpaths/**           # ❌ FORBIDDEN
rmos/workflow/**            # ❌ FORBIDDEN
data/runs/**                # ❌ FORBIDDEN
data/run_attachments/**     # ❌ FORBIDDEN
```

---

## Version Stamping Contract

All run artifacts MUST include version stamps:

| Field | Description | Required |
|-------|-------------|----------|
| `engine_version` | Feasibility engine version | YES |
| `toolchain_version` | Toolpath generator version | YES |
| `post_processor_version` | G-code post-processor version | YES |
| `config_fingerprint` | Hash of configuration state | YES |

This enables:
- Deterministic replay
- Drift detection
- Audit trail integrity

---

## Drift Detection Contract

Replay endpoints (dev-only) detect when:

| Drift Type | Detection Method | Action |
|------------|------------------|--------|
| Code drift | Output hash mismatch | Block + require override |
| Config drift | Config fingerprint mismatch | Warn + log |
| Engine drift | Version mismatch | Block + require upgrade |

**Drift requires explicit human override** to accept forked runs.

---

## Compliance Matrix

| Rule ID | Rule | Enforcement | Severity |
|---------|------|-------------|----------|
| G1 | AI must not import RMOS | CI + pre-commit | CRITICAL |
| G2 | AI must not call authority functions | CI + pre-commit | CRITICAL |
| G3 | AI must not write to RMOS paths | CI + pre-commit | CRITICAL |
| G4 | AI must use public APIs only | Code review | HIGH |
| G5 | All runs must have version stamps | Schema validation | HIGH |
| G6 | Feasibility must be server-computed | Runtime guard | CRITICAL |
| G7 | Toolpaths require APPROVED state | Runtime guard | CRITICAL |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-16 | Claude Opus 4.5 | Initial canonical specification |

---

## Amendment Process

Changes to this contract require:

1. **Proposal** — Written specification with rationale
2. **Security Review** — Assessment of authority implications
3. **Impact Analysis** — Downstream effects on CI, runtime
4. **Maintainer Approval** — Unanimous consent required
5. **Version Increment** — Major version for authority changes

---

*This document is the authoritative specification for AI Sandbox and RMOS execution authority.*
*Violations are treated as security incidents.*
