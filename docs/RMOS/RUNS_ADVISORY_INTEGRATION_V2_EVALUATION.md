# Runs_Advisory_Integration_v2 System Evaluation

**Date:** December 18, 2025
**Evaluator:** Claude Code
**Source:** `Runs_Advisory_Integration_v2/`
**Status:** Draft/Proposal (NOT the production implementation)

---

## Executive Summary

This directory contains a **draft implementation** of a runs + advisory integration system. It was likely created as a proposal before the governance-compliant `runs_v2/` module was built.

**Verdict:** This implementation has several compliance gaps and should NOT be used as-is. The production implementation is in `services/api/app/rmos/runs_v2/`.

---

## 1. Architecture & Flow

### 1.1 Components

```
Runs_Advisory_Integration_v2/
├── schemas.py      # Pydantic models (73 lines)
├── store.py        # Per-file storage with global lock (133 lines)
├── router.py       # FastAPI endpoints (277 lines)
├── hashing.py      # SHA256 utilities (50 lines)
└── __init__.py     # Package exports (4 lines)
```

**Total:** 537 lines

### 1.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API REQUEST                                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  POST /api/rmos/runs                                                 │
│  ├─ Generate run_id: run_{uuid12}                                    │
│  ├─ Create RunArtifact (Pydantic model)                             │
│  └─ Store to: data/rmos_runs/{run_id}.json                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  POST /api/rmos/runs/{id}/suggest-and-attach                        │
│  ├─ Get run from store                                               │
│  ├─ Generate explanation from feasibility                            │
│  ├─ Create AdvisoryAsset (external _experimental module)             │
│  ├─ POLICY B: Auto-approve if GREEN, else require review             │
│  ├─ Attach advisory reference to run                                 │
│  └─ Update explanation_status/summary                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Filesystem: data/rmos_runs/                                         │
│  ├── run_abc123def456.json                                           │
│  ├── run_def456789abc.json                                           │
│  └── ...                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/rmos/runs` | Create run artifact |
| GET | `/api/rmos/runs/{id}` | Get run details |
| PATCH | `/api/rmos/runs/{id}/meta` | Update metadata |
| POST | `/api/rmos/runs/{id}/attach-advisory` | Attach advisory reference |
| GET | `/api/rmos/runs/{id}/advisories` | List advisories |
| POST | `/api/rmos/runs/{id}/suggest-and-attach` | Generate + attach explanation |

---

## 2. Compliance Gap Analysis

### Comparison with Governance Contract

| Requirement | Contract | This Implementation | Compliant? |
|-------------|----------|---------------------|------------|
| Schema | Pydantic BaseModel | ✅ Pydantic | ✅ |
| `feasibility_sha256` | REQUIRED | ❌ Optional (None default) | ❌ |
| `risk_level` | REQUIRED | ❌ Optional (None default) | ❌ |
| Storage | Date-partitioned | ❌ Flat directory | ❌ |
| Immutability | Write-once | ❌ Has `patch_meta()` | ❌ |
| Atomic writes | .tmp + os.replace() | ✅ Implemented | ✅ |
| Thread safety | Per-file or global | ⚠️ Global RLock | ⚠️ |
| Path traversal | Validate run_id | ✅ Regex validation | ✅ |

### Specific Issues

#### Issue 1: Required Fields Are Optional

```python
# schemas.py lines 13-17
class Hashes(BaseModel):
    feasibility_sha256: Optional[str] = None  # ❌ Should be REQUIRED
    toolpaths_sha256: Optional[str] = None
    ...

# schemas.py line 21
class RunDecision(BaseModel):
    risk_level: Optional[str] = None  # ❌ Should be REQUIRED
```

**Impact:** Artifacts can be created without critical audit data.

#### Issue 2: Mutability Violation

```python
# store.py lines 57-64
def patch_meta(self, run_id: str, meta_updates: Dict[str, Any]) -> Optional[RunArtifact]:
    with _LOCK:
        run = self.get(run_id)
        if run is None:
            return None
        run.meta.update(meta_updates)  # ❌ Modifies existing artifact
        self.put(run)
        return run
```

**Impact:** Audit trail can be altered after creation.

#### Issue 3: No Date Partitioning

```python
# store.py line 38
def _path_for(self, run_id: str) -> Path:
    return self.root / f"{run_id}.json"  # ❌ Flat structure
```

**Impact:**
- All files in one directory (doesn't scale)
- No efficient date-range queries
- Harder to archive old data

#### Issue 4: Hardcoded Experimental Dependency

```python
# router.py lines 181-185
from app._experimental.ai_graphics.advisory_store import get_advisory_store
from app._experimental.ai_graphics.schemas.advisory_schemas import (
    AdvisoryAsset,
    AdvisoryAssetType,
)
```

**Impact:**
- Tight coupling to experimental code
- Import errors if module moves/changes
- Circular dependency risk

#### Issue 5: Auto-Approval Logic in Router

```python
# router.py lines 227-238
# POLICY B: Auto-approve GREEN only
is_green = risk_level == "GREEN"
if is_green:
    asset.reviewed = True
    asset.approved_for_workflow = True
    asset.reviewed_by = "system:auto_explanation_green"
```

**Impact:**
- Policy logic embedded in API layer (should be in service layer)
- Hard to change policy without modifying router
- Not testable in isolation

---

## 3. Edge Cases

### 3.1 Handled Edge Cases ✅

| Case | Handling | Location |
|------|----------|----------|
| Invalid run_id format | Regex validation raises ValueError | `store.py:31-34` |
| Run not found | Returns None / raises 404 | `store.py:52`, `router.py:84` |
| Duplicate advisory attach | Idempotent skip | `store.py:86-89` |
| Corrupt JSON file | Logs warning, skips | `store.py:128-130` |
| Missing request_id | Graceful fallback | `router.py:62` |

### 3.2 Unhandled Edge Cases ❌

| Case | Risk | Recommendation |
|------|------|----------------|
| Concurrent writes to same run | Data corruption possible with RLock + read-modify-write | Use file locking per run |
| Disk full during write | Partial .tmp file left behind | Catch OSError, cleanup .tmp |
| Very large feasibility payload | Memory pressure, slow hashing | Stream hashing, size limits |
| Unicode in run_id | Regex only allows hex | Explicitly document constraint |
| Timezone-naive datetime | Inconsistent timestamps | Enforce UTC in validation |
| Advisory store unavailable | Explanation marked ERROR but no retry | Add retry mechanism |

---

## 4. Observability & Testing

### 4.1 Current Observability

| Aspect | Implementation | Quality |
|--------|----------------|---------|
| Logging | `logger.info/error` in suggest_and_attach | ⚠️ Partial |
| Metrics | None | ❌ Missing |
| Tracing | request_id propagation | ✅ Good |
| Error details | Stored in explanation_summary | ⚠️ Basic |

### 4.2 Missing Observability

- [ ] Structured logging for all operations (not just suggest_and_attach)
- [ ] Latency histograms per endpoint
- [ ] Error rate counters
- [ ] Storage utilization metrics
- [ ] Advisory approval rate tracking

### 4.3 Testability Assessment

| Component | Unit Testable? | Notes |
|-----------|----------------|-------|
| schemas.py | ✅ Yes | Pure Pydantic models |
| hashing.py | ✅ Yes | Pure functions |
| store.py | ⚠️ Partially | Needs filesystem mocking |
| router.py | ❌ Difficult | Hardcoded _store(), external deps |

**Recommendations:**
- Inject store dependency instead of `_store()` function
- Mock advisory_store for router tests
- Add integration tests with temp directory

---

## 5. Operational Risks

### 5.1 High Risk ⛔

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Audit trail tampering | Medium | Critical | Remove patch_meta |
| Missing required fields | High | High | Make fields non-optional |
| Data loss on crash | Low | Critical | Already uses atomic writes |

### 5.2 Medium Risk ⚠️

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Directory doesn't scale | Medium | Medium | Add date partitioning |
| Global lock contention | Medium | Medium | Per-file locking |
| _experimental module changes | High | Medium | Decouple or vendor |

### 5.3 Low Risk ℹ️

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Path traversal | Low | High | Already validates run_id |
| JSON corruption | Low | Medium | Already logs and skips |

---

## 6. Graceful Failure Analysis

### 6.1 Failure Modes

| Failure | Current Behavior | Graceful? |
|---------|------------------|-----------|
| Store directory missing | Created on init | ✅ Yes |
| Run not found | 404 with message | ✅ Yes |
| Invalid run_id | ValueError raised | ⚠️ Returns 500 |
| Advisory store import fails | Sets ERROR status, returns run | ✅ Yes |
| Explanation generation fails | Sets ERROR status with message | ✅ Yes |
| Disk write fails | Exception propagates | ❌ No |
| Corrupt file read | Logs warning, skips in list_all | ✅ Yes |

### 6.2 Recovery Capabilities

| Scenario | Recovery Path |
|----------|---------------|
| Server restart | Store reloads from disk | ✅ |
| Partial write (.tmp left) | Ignored by glob pattern | ✅ |
| Corrupt single file | Other files unaffected | ✅ |
| Full disk | No recovery mechanism | ❌ |

---

## 7. Comparison with Production runs_v2

| Feature | This Draft | Production runs_v2 |
|---------|------------|-------------------|
| Required fields | Optional | Enforced |
| Storage | Flat directory | Date-partitioned |
| Immutability | Violated (patch_meta) | Strict (append-only advisory) |
| Thread safety | Global RLock | Per-file atomic |
| Advisory integration | Embedded in router | Separate link files |
| Migration tools | None | Full CLI |
| Lines of code | 537 | ~2,700 |
| Tests | None | Designed for testing |

---

## 8. Re-Review Checklist

Use this checklist after any changes to the system:

### Schema Compliance
- [ ] `Hashes.feasibility_sha256` is REQUIRED (not Optional)
- [ ] `RunDecision.risk_level` is REQUIRED (not Optional)
- [ ] All datetime fields use UTC
- [ ] Pydantic validation runs on creation

### Storage Compliance
- [ ] Date-partitioned structure: `{YYYY-MM-DD}/{run_id}.json`
- [ ] No modification after creation (no patch_meta)
- [ ] Atomic writes via .tmp + os.replace()
- [ ] Path traversal protection on all inputs

### API Compliance
- [ ] POST /runs creates immutable artifact
- [ ] No PATCH endpoint for core data
- [ ] Advisory attachment is append-only
- [ ] All endpoints return proper error codes

### Thread Safety
- [ ] Concurrent writes to different runs work
- [ ] Concurrent reads during write are safe
- [ ] No race conditions in read-modify-write patterns

### Observability
- [ ] All endpoints log start/end with timing
- [ ] Error conditions include context
- [ ] request_id propagated through stack
- [ ] Corrupt files logged with path

### Error Handling
- [ ] Disk full handled gracefully
- [ ] External service failures don't crash
- [ ] Validation errors return 400, not 500
- [ ] Partial operations are rolled back

### Testing
- [ ] Unit tests for schemas
- [ ] Unit tests for hashing
- [ ] Integration tests for store
- [ ] API tests for router
- [ ] Load tests for concurrency

---

## 9. Recommendation

**Do NOT use this implementation.**

Use the production-ready `services/api/app/rmos/runs_v2/` module instead, which:
- Enforces required fields
- Implements date-partitioned storage
- Maintains strict immutability
- Has migration tooling
- Is governance-compliant

If this draft must be kept for reference, move it to `docs/archive/` or `_experimental/`.

---

*Evaluation completed: December 18, 2025*
