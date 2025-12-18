# Runs Advisory Integration - Clarification Responses

**Date:** December 18, 2025
**Status:** Awaiting Team Decision
**Related Documents:**
- `docs/RUNS_ADVISORY_INTEGRATION_EVALUATION.md`
- `docs/RMOS_RUNS_GAP_ANALYSIS.md`
- `docs/Runs_Advisory_Integration/` (proposed patch)

---

## Overview

This document provides formal responses to clarification questions raised during the review of the Runs Advisory Integration patch. Each question requires a team decision to establish the canonical direction for the RMOS Runs subsystem.

---

## Table of Contents

1. [Canonical Architecture Direction](#1-canonical-architecture-direction)
2. [Existing Implementation Status](#2-existing-implementation-status)
3. [Thread Safety Approach](#3-thread-safety-approach)
4. [Evaluation Document Provenance](#4-evaluation-document-provenance)
5. [Governance Auto-Approval Policy](#5-governance-auto-approval-policy)
6. [Decision Matrix](#6-decision-matrix)
7. [Recommended Next Steps](#7-recommended-next-steps)

---

## 1. Canonical Architecture Direction

### Question

> Is the Pydantic/per-file foundation the canonical direction? The document used Pydantic BaseModel and per-file storage. The evaluation compares against the old dataclass/single-file store as if that's authoritative. Which is the target architecture going forward?

### Response

**Decision Required:** This is an architectural decision that must be made by the team.

### Comparison Matrix

| Aspect | Pydantic + Per-File (Patch) | Dataclass + Single-File (Existing) |
|--------|----------------------------|-----------------------------------|
| **Schema Validation** | Built-in, declarative | Manual or via post-init |
| **Serialization** | `model_dump()` / `model_validate()` | `asdict()` + manual deserialization |
| **Storage Scalability** | O(1) per-run operations | O(n) read-all for any operation |
| **Atomic Writes** | Per-file `.tmp` + `os.replace()` | Full file rewrite |
| **Thread Safety** | Not implemented | `threading.Lock` in place |
| **Existing Features** | None (new implementation) | Attachments, diff, filtering, verification |
| **Migration Effort** | High (replace all) | Low (extend existing) |

### Options

#### Option A: Adopt Pydantic + Per-File (Full Migration)

**Implications:**
- Rewrite `attachments.py`, `diff.py` to use Pydantic schemas
- Add thread safety to new `RunStore` class
- Migrate existing data from single JSON to per-file structure
- Update all import paths and dependent code

**Timeline:** Significant effort required

#### Option B: Keep Dataclass + Single-File (Extend Existing)

**Implications:**
- Extract advisory patterns from patch into existing code
- Maintain backward compatibility
- Existing features (attachments, diff, filtering) continue working
- Thread safety already in place

**Timeline:** Incremental, lower risk

#### Option C: Hybrid Approach

**Implications:**
- Keep dataclass schemas but migrate to per-file storage
- Add Pydantic validation layer for API boundaries only
- Best of both worlds but increased complexity

**Timeline:** Medium effort

### Recommendation

**Option B (Extend Existing)** is recommended for the following reasons:

1. The existing implementation is production code with proven features
2. Thread safety is already implemented and tested
3. The valuable parts of the patch (advisory integration patterns) can be extracted
4. Lower risk of regression
5. Faster time to delivery

---

## 2. Existing Implementation Status

### Question

> What's the status of the existing dataclass implementation? `api_runs.py` (266 lines) uses the old patterns. `attachments.py` and `diff.py` have dependencies on old schemas. Are these being deprecated, migrated, or maintained in parallel?

### Response

**Status: Active and Recently Extended**

The existing implementation in `services/api/app/rmos/runs/` is the **production codebase** and was extended on December 18, 2025 with features identified in the gap analysis.

### Current State Summary

| File | Lines | Status | Recent Changes |
|------|-------|--------|----------------|
| `schemas.py` | 141 | **Active** | Added `RunDecision`, `AdvisoryInputRef`, `ExplanationStatus`, extended `RunArtifact` |
| `store.py` | 196 | **Active** | Added `patch_run_meta()` with thread safety |
| `api_runs.py` | 380+ | **Active** | Added `POST /runs`, `PATCH /runs/{id}/meta` endpoints |
| `hashing.py` | 102 | **Active** | Added `sha256_of_text_safe()`, `summarize_request()` |
| `attachments.py` | ~100 | **Active** | Unchanged, fully functional |
| `diff.py` | ~80 | **Active** | Unchanged, fully functional |
| `__init__.py` | 79 | **Active** | Updated exports for new symbols |

### Dependency Graph

```
__init__.py
    ├── schemas.py (RunArtifact, RunDecision, AdvisoryInputRef, ...)
    ├── store.py (depends on schemas.py)
    ├── hashing.py (standalone)
    ├── attachments.py (depends on hashing.py)
    ├── diff.py (depends on schemas.py)
    └── api_runs.py (depends on all above)
```

### Clarification

- **NOT deprecated:** The existing implementation is canonical
- **NOT migrating:** No plans to replace with Pydantic version
- **NOT parallel:** The patch in `docs/Runs_Advisory_Integration/` is a proposal only

### What Remains to Integrate

The following patterns from the patch should be added to the existing implementation:

| Pattern | Source | Target | Status |
|---------|--------|--------|--------|
| `attach_advisory()` | `patch/store.py:52-85` | `existing/store.py` | Pending |
| `set_explanation()` | `patch/store.py:87-101` | `existing/store.py` | Pending |
| `POST /attach-advisory` | `patch/router.py:101-124` | `existing/api_runs.py` | Pending |
| `GET /advisories` | `patch/router.py:127-141` | `existing/api_runs.py` | Pending |
| `POST /suggest-and-attach` | `patch/router.py:144-242` | `existing/api_runs.py` | Pending |

---

## 3. Thread Safety Approach

### Question

> Thread safety approach for per-file storage: Single-file store used one global lock for everything. Per-file storage could use per-file locks (more granular) or one global lock (simpler). Which do you prefer?

### Response

**Decision Required:** If per-file storage is adopted, a locking strategy must be chosen.

### Options Analysis

#### Option 1: Global Lock (Recommended for RMOS Runs)

```python
import threading

_LOCK = threading.Lock()

class RunStore:
    def put(self, run: RunArtifact) -> None:
        with _LOCK:
            # Write to per-file storage
            ...

    def get(self, run_id: str) -> Optional[RunArtifact]:
        with _LOCK:
            # Read from per-file storage
            ...
```

| Pros | Cons |
|------|------|
| Simple implementation | All operations serialize |
| No lock management overhead | Potential bottleneck at scale |
| Proven pattern (existing code) | Less granular than possible |

**Best for:** Low-to-medium concurrency (< 100 concurrent operations)

#### Option 2: Per-File Locks

```python
import threading
from typing import Dict

class RunStore:
    def __init__(self, root_dir: str):
        self._locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()  # Lock for the locks dict

    def _get_lock(self, run_id: str) -> threading.Lock:
        with self._locks_lock:
            if run_id not in self._locks:
                self._locks[run_id] = threading.Lock()
            return self._locks[run_id]

    def put(self, run: RunArtifact) -> None:
        with self._get_lock(run.run_id):
            # Write to specific file
            ...
```

| Pros | Cons |
|------|------|
| Maximum concurrency | Complex lock management |
| Operations on different runs don't block | Memory growth (lock per run) |
| Better for high throughput | Need lock cleanup strategy |

**Best for:** High concurrency (> 100 concurrent operations)

#### Option 3: File-Based Locking (OS-Level)

```python
import fcntl  # Unix
# or
import msvcrt  # Windows

def put(self, run: RunArtifact) -> None:
    path = self._path_for(run.run_id)
    with open(path, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(json.dumps(run.model_dump()))
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

| Pros | Cons |
|------|------|
| Works across processes | Platform-specific code |
| No in-memory lock state | More I/O overhead |
| Survives process crashes | Complexity for cross-platform |

**Best for:** Multi-process deployments

### Recommendation

**Global Lock (Option 1)** is recommended for RMOS Runs because:

1. Run operations are infrequent (not high-throughput)
2. Simplicity reduces bugs
3. Matches existing proven pattern
4. Can upgrade to per-file locks later if needed

### Decision Criteria

Choose **per-file locks** only if:
- Measured lock contention exceeds acceptable threshold
- Concurrent operations on different runs must not block each other
- Team has capacity to maintain more complex locking code

---

## 4. Evaluation Document Provenance

### Question

> Who generated this evaluation document? Was this your assessment of my code? Or AI-generated review you're using to test my response? Or a template/checklist you apply to all patches?

### Response

**Provenance:** The evaluation document (`RUNS_ADVISORY_INTEGRATION_EVALUATION.md`) was generated by Claude (AI assistant) during this working session.

### Generation Process

| Step | Action |
|------|--------|
| 1 | User requested evaluation of `docs/Runs_Advisory_Integration/` |
| 2 | Claude read all 5 files in the directory |
| 3 | Claude read existing implementation in `services/api/app/rmos/runs/` |
| 4 | Claude performed comparative analysis |
| 5 | Claude generated evaluation following requested structure |
| 6 | User requested markdown document |
| 7 | Claude created formal document |

### Evaluation Structure Source

The evaluation structure was specified in the user's request:

> "Evaluate ... as a system. Include: architecture/flow, edge cases, observability/testing, operational risks, and how it fails gracefully. Provide a checklist I can use to re-review after changes."

This is not a pre-existing template but a custom analysis following the requested framework.

### Verification

The evaluation can be verified by:
1. Reading the source files in `docs/Runs_Advisory_Integration/`
2. Comparing against the existing implementation
3. Validating the technical claims (thread safety gaps, path traversal concerns, etc.)

---

## 5. Governance Auto-Approval Policy

### Question

> The evaluation flags `reviewed_by="system"` as a concern. For explanatory content (not prescriptive suggestions), is auto-approval acceptable? Or should all advisory assets require human review regardless of type?

### Response

**Decision Required:** This is a governance policy decision that affects audit compliance and operational workflow.

### Risk Analysis by Content Type

| Content Type | Definition | Risk Level | Auto-Approval? |
|--------------|------------|------------|----------------|
| **Explanatory (GREEN)** | Why parameters passed checks | Very Low | Acceptable |
| **Explanatory (YELLOW)** | Why caution is advised | Low | Acceptable with logging |
| **Explanatory (RED)** | Why operation was blocked | Medium | Consider review |
| **Prescriptive** | Suggested parameter changes | High | Require review |
| **Override Request** | Request to bypass block | Very High | Always require review |

### Policy Options

#### Policy A: Auto-Approve All Explanations

```python
if asset.asset_type == AdvisoryAssetType.ANALYSIS:
    asset.reviewed = True
    asset.approved_for_workflow = True
    asset.reviewed_by = "system:auto_explanation"
```

| Pros | Cons |
|------|------|
| Fast workflow | No human oversight |
| No bottleneck | Audit may question |
| Consistent | Can't catch AI errors |

#### Policy B: Auto-Approve GREEN Only

```python
if asset.asset_type == AdvisoryAssetType.ANALYSIS:
    if decision.risk_level == "GREEN":
        asset.approved_for_workflow = True
        asset.reviewed_by = "system:auto_green"
    else:
        asset.approved_for_workflow = False
        asset.reviewed_by = None  # Requires human
```

| Pros | Cons |
|------|------|
| Low-risk auto-approval | YELLOW/RED delays |
| Human review for concerns | More workflow steps |
| Balanced approach | Complexity |

#### Policy C: No Auto-Approval

```python
asset.reviewed = False
asset.approved_for_workflow = False
asset.reviewed_by = None  # Always requires human
```

| Pros | Cons |
|------|------|
| Full human oversight | Workflow bottleneck |
| Maximum audit compliance | Slower operations |
| Catches all errors | May be overkill |

### Recommendation

**Policy B (Auto-Approve GREEN Only)** is recommended as a balanced approach:

1. GREEN results are low-risk (operation already approved)
2. YELLOW/RED warrant human attention anyway
3. Clear audit trail (`reviewed_by` distinguishes auto vs human)
4. Can adjust thresholds based on experience

### Implementation

```python
def auto_approve_policy(asset: AdvisoryAsset, decision: RunDecision) -> None:
    """
    Apply governance auto-approval policy.

    Policy: Auto-approve explanatory content for GREEN results only.
    All other content requires human review.
    """
    is_explanatory = asset.asset_type == AdvisoryAssetType.ANALYSIS
    is_green = decision.risk_level == "GREEN"

    if is_explanatory and is_green:
        asset.reviewed = True
        asset.approved_for_workflow = True
        asset.reviewed_by = "system:auto_explanation_green"
        asset.review_notes = "Auto-approved: explanatory content for GREEN result"
    else:
        asset.reviewed = False
        asset.approved_for_workflow = False
        asset.reviewed_by = None
        asset.review_notes = f"Requires human review: {asset.asset_type}, risk={decision.risk_level}"
```

### Audit Trail Requirements

Regardless of policy chosen, ensure:

| Requirement | Implementation |
|-------------|----------------|
| Distinguish auto from human | Use `system:` prefix in `reviewed_by` |
| Log all approvals | Structured logging with advisory_id, run_id, policy |
| Queryable history | Store approval timestamp and policy version |
| Policy versioning | Include policy ID in `review_notes` |

---

## 6. Decision Matrix

The following decisions are required to proceed:

| # | Decision | Options | Recommended | Owner | Status |
|---|----------|---------|-------------|-------|--------|
| 1 | Canonical architecture | Pydantic/Per-file vs Dataclass/Single-file vs Hybrid | Dataclass (extend existing) | Team | Pending |
| 2 | Existing code status | Deprecate vs Migrate vs Extend | Extend | Team | Pending |
| 3 | Thread safety approach | Global lock vs Per-file locks vs OS-level | Global lock | Team | Pending |
| 4 | Auto-approval policy | All vs GREEN-only vs None | GREEN-only | Team | Pending |
| 5 | Migration timeline | Immediate vs Phased vs Deferred | Phased | Team | Pending |

---

## 7. Recommended Next Steps

### If Decision: Extend Existing (Recommended)

```
Phase 1: Add Advisory Store Functions (Low Risk)
├── Add attach_advisory() to store.py with Lock
├── Add set_explanation() to store.py with Lock
├── Update __init__.py exports
└── Validate with unit tests

Phase 2: Add Advisory API Endpoints (Medium Risk)
├── Add POST /{run_id}/attach-advisory
├── Add GET /{run_id}/advisories
├── Add POST /{run_id}/suggest-and-attach
└── Integration test with mock advisory store

Phase 3: Governance Implementation (Policy-Dependent)
├── Implement chosen auto-approval policy
├── Add structured logging for audit
├── Document policy in governance contracts
└── Review with compliance team
```

### If Decision: Full Migration to Pydantic/Per-File

```
Phase 1: Foundation (High Risk)
├── Add thread safety to RunStore class
├── Add run_id validation regex
├── Add logging for corrupt file handling
└── Comprehensive testing

Phase 2: Feature Parity (High Effort)
├── Port attachments.py to Pydantic
├── Port diff.py to Pydantic
├── Port filtering to per-file queries
└── Verification endpoints

Phase 3: Migration (High Risk)
├── Data migration script (single-file → per-file)
├── Dual-write period for validation
├── Cutover with rollback plan
└── Deprecate old implementation
```

---

## Appendix: File References

### Existing Implementation
- `services/api/app/rmos/runs/schemas.py`
- `services/api/app/rmos/runs/store.py`
- `services/api/app/rmos/runs/api_runs.py`
- `services/api/app/rmos/runs/hashing.py`
- `services/api/app/rmos/runs/attachments.py`
- `services/api/app/rmos/runs/diff.py`
- `services/api/app/rmos/runs/__init__.py`

### Proposed Patch
- `docs/Runs_Advisory_Integration/schemas.py`
- `docs/Runs_Advisory_Integration/store.py`
- `docs/Runs_Advisory_Integration/router.py`
- `docs/Runs_Advisory_Integration/hashing.py`
- `docs/Runs_Advisory_Integration/__init__.py`

### Related Documentation
- `docs/RUNS_ADVISORY_INTEGRATION_EVALUATION.md`
- `docs/RMOS_RUNS_GAP_ANALYSIS.md`
- `docs/RMOS_RUNS_PATCH_EVALUATION.md`

---

*Document generated: December 18, 2025*
*Awaiting team decisions on items in Decision Matrix (Section 6)*
