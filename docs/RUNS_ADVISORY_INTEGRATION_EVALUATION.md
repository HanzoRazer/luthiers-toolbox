# Runs Advisory Integration - System Evaluation

**Date:** December 18, 2025
**Status:** Review Required Before Implementation
**Location:** `docs/Runs_Advisory_Integration/`

---

## Executive Summary

The Runs Advisory Integration patch provides a **Pydantic-based implementation** for connecting advisory/explanation assets with RMOS Runs. It introduces valuable patterns for the advisory attachment workflow but has **critical gaps** that must be addressed before deployment.

| Aspect | Assessment |
|--------|------------|
| **Core Concept** | Sound - advisory linking is needed |
| **Implementation Safety** | Insufficient - no thread safety |
| **Architecture Fit** | Conflicts with existing dataclass-based impl |
| **Governance** | Concern - auto-approval bypasses review |

**Recommendation:** Extract the advisory integration patterns and adapt them to the existing thread-safe implementation rather than replacing it.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Analysis](#2-component-analysis)
3. [Data Flow](#3-data-flow)
4. [Edge Cases & Vulnerabilities](#4-edge-cases--vulnerabilities)
5. [Observability & Testing](#5-observability--testing)
6. [Operational Risks](#6-operational-risks)
7. [Graceful Failure Analysis](#7-graceful-failure-analysis)
8. [Comparison with Existing Implementation](#8-comparison-with-existing-implementation)
9. [Governance Concerns](#9-governance-concerns)
10. [Implementation Recommendation](#10-implementation-recommendation)
11. [Re-Review Checklist](#11-re-review-checklist)

---

## 1. Architecture Overview

### System Purpose

The Runs Advisory Integration connects two RMOS subsystems:

- **RMOS Runs**: Immutable audit records of manufacturing operations
- **Advisory Store**: AI-generated explanations and recommendations

This integration enables:
- Attaching explanations to run artifacts
- Generating explanations on-demand (suggest-and-attach)
- Tracking explanation status and provenance

### File Structure

```
docs/Runs_Advisory_Integration/
├── __init__.py      # Package exports
├── schemas.py       # Pydantic models (RunArtifact, AdvisoryInputRef, etc.)
├── hashing.py       # Deterministic hashing utilities
├── store.py         # Filesystem-backed RunStore class
└── router.py        # FastAPI endpoints
```

### Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Schema | Pydantic BaseModel | Conflicts with existing dataclass approach |
| Storage | Per-file JSON | One file per run: `<run_id>.json` |
| API | FastAPI | Standard REST endpoints |
| Hashing | SHA256 | Deterministic JSON serialization |

---

## 2. Component Analysis

### 2.1 Schemas (`schemas.py`)

#### RunArtifact (Core Record)

```python
class RunArtifact(BaseModel):
    run_id: str
    created_at_utc: datetime
    mode: str
    tool_id: str
    status: Literal["OK", "BLOCKED", "ERROR"]

    # Core payloads
    request_summary: Dict[str, Any]
    feasibility: Dict[str, Any]
    decision: RunDecision
    hashes: Hashes
    outputs: RunOutputs

    # Advisory integration
    advisory_inputs: List[AdvisoryInputRef]  # Append-only
    explanation_status: Literal["NONE", "PENDING", "READY", "ERROR"]
    explanation_summary: Optional[str]

    # Extensibility
    meta: Dict[str, Any]
```

#### Supporting Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `RunDecision` | Structured feasibility result | `risk_level`, `score`, `block_reason`, `warnings` |
| `Hashes` | Content integrity | `feasibility_sha256`, `toolpaths_sha256`, `gcode_sha256` |
| `RunOutputs` | Output references | `gcode_path`, `opplan_path`, `preview_svg_path` |
| `AdvisoryInputRef` | Advisory link | `advisory_id`, `kind`, `engine_id`, `engine_version` |

### 2.2 Storage (`store.py`)

#### RunStore Class

```python
class RunStore:
    def __init__(self, root_dir: str)
    def put(self, run: RunArtifact) -> None
    def get(self, run_id: str) -> Optional[RunArtifact]
    def patch_meta(self, run_id: str, meta_updates: Dict) -> Optional[RunArtifact]
    def attach_advisory(self, run_id: str, advisory_id: str, ...) -> Optional[RunArtifact]
    def set_explanation(self, run_id: str, status: str, summary: str) -> Optional[RunArtifact]
    def list_all(self, limit: int) -> List[RunArtifact]
```

#### Storage Pattern

- **Per-file storage**: Each run stored as `data/rmos_runs/<run_id>.json`
- **Atomic writes**: Uses `.tmp` file + `os.replace()` pattern
- **No thread safety**: Missing `threading.Lock` protection

### 2.3 Router (`router.py`)

#### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rmos/runs` | POST | Create new run artifact |
| `/api/rmos/runs/{id}` | GET | Retrieve run by ID |
| `/api/rmos/runs/{id}/meta` | PATCH | Update run metadata |
| `/api/rmos/runs/{id}/attach-advisory` | POST | Attach advisory reference |
| `/api/rmos/runs/{id}/advisories` | GET | List attached advisories |
| `/api/rmos/runs/{id}/suggest-and-attach` | POST | Generate and attach explanation |

### 2.4 Hashing (`hashing.py`)

| Function | Purpose |
|----------|---------|
| `sha256_text()` | Hash text with null handling |
| `sha256_json()` | Deterministic JSON hash (sorted keys) |
| `sha256_toolpaths_payload()` | Alias for specialized hashing |
| `summarize_request()` | Redaction-friendly request summary |

---

## 3. Data Flow

### Run Creation Flow

```
Client                    Router                    Store                    Disk
  │                         │                         │                        │
  │  POST /api/rmos/runs    │                         │                        │
  │────────────────────────>│                         │                        │
  │                         │  RunArtifact()          │                        │
  │                         │────────────────────────>│                        │
  │                         │                         │  write .json.tmp       │
  │                         │                         │───────────────────────>│
  │                         │                         │  os.replace()          │
  │                         │                         │───────────────────────>│
  │                         │<────────────────────────│                        │
  │<────────────────────────│                         │                        │
  │  RunArtifact response   │                         │                        │
```

### Suggest-and-Attach Flow

```
Client                Router              Store           AdvisoryStore
  │                     │                   │                   │
  │  POST suggest-and-  │                   │                   │
  │  attach             │                   │                   │
  │────────────────────>│                   │                   │
  │                     │  get(run_id)      │                   │
  │                     │──────────────────>│                   │
  │                     │<──────────────────│                   │
  │                     │                   │                   │
  │                     │  set_explanation  │                   │
  │                     │  (PENDING)        │                   │
  │                     │──────────────────>│                   │
  │                     │                   │                   │
  │                     │  Generate explanation from            │
  │                     │  run.decision data                    │
  │                     │                   │                   │
  │                     │  Create AdvisoryAsset ───────────────>│
  │                     │                   │                   │
  │                     │  Auto-approve ───────────────────────>│
  │                     │                   │                   │
  │                     │  attach_advisory  │                   │
  │                     │──────────────────>│                   │
  │                     │                   │                   │
  │                     │  set_explanation  │                   │
  │                     │  (READY)          │                   │
  │                     │──────────────────>│                   │
  │                     │<──────────────────│                   │
  │<────────────────────│                   │                   │
  │  RunArtifact        │                   │                   │
```

---

## 4. Edge Cases & Vulnerabilities

### Critical Issues

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| **No thread safety** | HIGH | `store.py` | Concurrent writes can corrupt data |
| **Path traversal risk** | MEDIUM | `store.py:24-27` | Incomplete sanitization |
| **Race condition** | HIGH | `router.py:165-231` | Multiple read-write cycles in suggest-and-attach |
| **Silent data loss** | MEDIUM | `store.py:108-112` | Corrupt files silently skipped |

### Thread Safety Gap

```python
# store.py - NO LOCKING
def put(self, run: RunArtifact) -> None:
    path = self._path_for(run.run_id)
    tmp = path.with_suffix(".json.tmp")
    # ... write ...
    os.replace(tmp, path)  # Not protected!
```

**Existing implementation has:**
```python
# Existing store.py - HAS LOCKING
_LOCK = threading.Lock()

def persist_run(artifact: RunArtifact) -> RunArtifact:
    with _LOCK:
        data = _read_all()
        data[artifact.run_id] = _serialize_artifact(artifact)
        _write_all(data)
    return artifact
```

### Path Sanitization Gap

```python
def _path_for(self, run_id: str) -> Path:
    safe = run_id.replace("/", "_").replace("\\", "_")
    return self.root / f"{safe}.json"
```

**Only sanitizes `/` and `\`.** Should validate format:

```python
import re

def _path_for(self, run_id: str) -> Path:
    if not re.match(r'^run_[a-f0-9]{12}$', run_id):
        raise ValueError(f"Invalid run_id format: {run_id}")
    return self.root / f"{run_id}.json"
```

### Race Condition in suggest-and-attach

```python
st.set_explanation(run_id, "PENDING")     # Write 1
# ... external API calls ...
run = st.attach_advisory(...)              # Read + Write 2
run = st.set_explanation(run_id, "READY")  # Read + Write 3
```

**Three separate read-write cycles** with no transaction semantics.

---

## 5. Observability & Testing

### Current Observability

| Aspect | Status | Notes |
|--------|--------|-------|
| Request ID correlation | ✅ | Captured in meta and advisory refs |
| Timestamps | ✅ | `created_at_utc` on all records |
| Engine provenance | ✅ | `engine_id`, `engine_version` tracked |
| Error states | ✅ | `explanation_status` = ERROR with message |
| Logging | ❌ | No log statements |
| Metrics | ❌ | No counters or timing |
| Tracing | ❌ | No distributed tracing |

### Missing Observability

Add structured logging:

```python
import logging
import time

logger = logging.getLogger(__name__)

@router.post("/{run_id}/suggest-and-attach")
def suggest_and_attach(run_id: str, ...):
    start = time.perf_counter()
    logger.info("suggest_and_attach.start", extra={"run_id": run_id})

    try:
        # ... existing code ...
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("suggest_and_attach.success", extra={
            "run_id": run_id,
            "elapsed_ms": elapsed_ms,
            "advisory_id": asset.asset_id,
        })
    except Exception as e:
        logger.error("suggest_and_attach.error", extra={
            "run_id": run_id,
            "error": str(e),
        })
        raise
```

### Testing Requirements

| Test Type | Priority | Coverage |
|-----------|----------|----------|
| Unit: Schema validation | HIGH | All field constraints |
| Unit: Hash determinism | HIGH | Same input = same hash |
| Unit: Store CRUD | HIGH | put, get, patch, attach |
| Unit: Idempotency | HIGH | Duplicate attach handling |
| Integration: Full flow | MEDIUM | Create → attach → retrieve |
| Integration: Advisory | MEDIUM | Mock advisory store |
| Chaos: Concurrency | HIGH | Parallel writes |
| Chaos: Corrupt files | MEDIUM | Malformed JSON handling |

---

## 6. Operational Risks

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss from concurrent writes | HIGH | HIGH | Add thread safety |
| Architecture conflict | CERTAIN | MEDIUM | Adapt patterns, don't replace |
| Advisory store unavailable | MEDIUM | LOW | Already handled gracefully |
| Disk space exhaustion | LOW | HIGH | Add pre-write check |
| Orphaned .tmp files | MEDIUM | LOW | Cleanup on startup |
| Schema migration | MEDIUM | MEDIUM | Plan Pydantic ↔ dataclass |
| Auto-approve governance | HIGH | MEDIUM | Review policy |

### Deployment Risk

**This patch cannot be deployed as-is** because:

1. **Schema conflict**: Pydantic vs existing dataclass
2. **Storage conflict**: Per-file vs single-file model
3. **Import conflict**: Same module paths, different implementations
4. **Safety regression**: Loses existing thread safety

---

## 7. Graceful Failure Analysis

### Failure Handling Summary

| Failure Mode | Detection | Recovery | Result |
|--------------|-----------|----------|--------|
| Run not found | `get()` returns None | 404 response | Clear error |
| Advisory store unavailable | ImportError | Status → ERROR | Run still returned |
| Explanation fails | Exception | Status → ERROR | Run still returned |
| File write fails | Exception | 500 error | Needs retry |
| Corrupt JSON | Parse error | Silent skip | **Data loss risk** |

### Good Pattern: Graceful Degradation

```python
# router.py:235-242
except ImportError as e:
    st.set_explanation(run_id, "ERROR", f"Advisory store unavailable: {e}")
    run = st.get(run_id)
    return run  # Still returns the run!

except Exception as e:
    st.set_explanation(run_id, "ERROR", str(e))
    run = st.get(run_id)
    return run  # Still returns the run!
```

**Strength:** Never throws to client for explanation failures.

### Bad Pattern: Silent Data Loss

```python
# store.py:108-112
for p in self.root.glob("*.json"):
    try:
        raw = json.loads(p.read_text(...))
        runs.append(RunArtifact.model_validate(raw))
    except Exception:
        continue  # SILENT! No logging!
```

**Fix:**
```python
except Exception as e:
    logger.warning(f"Skipping corrupt run file: {p}", exc_info=e)
    continue
```

---

## 8. Comparison with Existing Implementation

| Feature | This Patch | Existing (Extended) | Winner |
|---------|-----------|---------------------|--------|
| Thread safety | ❌ None | ✅ `threading.Lock` | **Existing** |
| Atomic writes | ✅ .tmp + replace | ❌ Direct write | **Patch** |
| Schema type | Pydantic | dataclass | Tie |
| Storage model | Per-file (scalable) | Single file | **Patch** |
| Advisory attach | ✅ Full impl | ❌ Schema only | **Patch** |
| suggest-and-attach | ✅ Full impl | ❌ Not present | **Patch** |
| Filtering | ❌ None | ✅ `list_runs_filtered` | **Existing** |
| Attachments | ❌ None | ✅ Content-addressed | **Existing** |
| Diff capability | ❌ None | ✅ `diff_runs` | **Existing** |
| Verification | ❌ None | ✅ SHA256 verify | **Existing** |

### Summary

- **Patch strengths:** Advisory integration patterns, atomic writes, scalable storage
- **Existing strengths:** Thread safety, filtering, attachments, diffing, verification
- **Best approach:** Merge patch patterns into existing implementation

---

## 9. Governance Concerns

### Auto-Approval Issue

```python
# router.py:213-217
# Auto-approve analysis (it's explanatory, not prescriptive)
asset.reviewed = True
asset.approved_for_workflow = True
asset.reviewed_by = "system"
advisory_store.update_asset(asset)
```

### Concerns

1. **Bypasses human review** - All explanations auto-approved
2. **"system" reviewer** - No accountability trail
3. **Audit implications** - Can downstream processes distinguish auto vs human approval?

### Recommendations

| Option | Description | Tradeoff |
|--------|-------------|----------|
| **A: Keep auto-approve** | Document as "informational only" | Fast, but governance gap |
| **B: Require review** | Set `approved_for_workflow=False` | Slower, but full governance |
| **C: Tiered approval** | Auto-approve GREEN, require review for YELLOW/RED | Balanced |

---

## 10. Implementation Recommendation

### Do NOT Deploy As-Is

The patch introduces valuable patterns but cannot be deployed directly due to:
- Thread safety regression
- Architecture conflicts
- Schema type mismatch

### Recommended Approach

**Phase 1: Extract Patterns**
```python
# Add to existing store.py
def attach_advisory(run_id: str, advisory_id: str, ...) -> RunArtifact:
    """Attach advisory reference to run (thread-safe)."""
    with _LOCK:
        data = _read_all()
        if run_id not in data:
            raise KeyError(f"Run {run_id} not found")

        raw = data[run_id]
        advisory_inputs = raw.get("advisory_inputs") or []

        # Idempotency check
        if any(ref["advisory_id"] == advisory_id for ref in advisory_inputs):
            return _deserialize_artifact(raw)

        advisory_inputs.append({
            "advisory_id": advisory_id,
            "kind": kind,
            "engine_id": engine_id,
            "engine_version": engine_version,
            "request_id": request_id,
            "created_at_utc": _now_utc_iso(),
        })
        raw["advisory_inputs"] = advisory_inputs

        _write_all(data)
    return _deserialize_artifact(raw)
```

**Phase 2: Add Router Endpoints**
- Add `POST /{run_id}/attach-advisory` to existing `api_runs.py`
- Add `GET /{run_id}/advisories` to existing `api_runs.py`
- Add `POST /{run_id}/suggest-and-attach` with proper locking

**Phase 3: Consider Storage Migration**
- Evaluate per-file vs single-file tradeoffs at scale
- Plan migration path if per-file is preferred

---

## 11. Re-Review Checklist

Use this checklist after making changes:

### Schema Integrity
- [ ] `RunArtifact` validates all required fields
- [ ] `status` only accepts "OK", "BLOCKED", "ERROR"
- [ ] `explanation_status` only accepts "NONE", "PENDING", "READY", "ERROR"
- [ ] `AdvisoryInputRef.kind` validates against allowed values
- [ ] Default factories don't share mutable state

### Storage Safety
- [ ] Thread safety: Lock protects ALL read-modify-write operations
- [ ] Atomic writes: .tmp file pattern used consistently
- [ ] Path sanitization: run_id validated against pattern `^run_[a-f0-9]+$`
- [ ] No path traversal possible with malicious run_id
- [ ] Corrupt files logged, not silently skipped

### Advisory Integration
- [ ] `attach_advisory` is idempotent (duplicate check works)
- [ ] `suggest-and-attach` sets PENDING before external calls
- [ ] `suggest-and-attach` always sets final status (READY or ERROR)
- [ ] ImportError for advisory_store handled gracefully
- [ ] Auto-approval policy documented and reviewed

### API Contract
- [ ] All endpoints return consistent error format
- [ ] 404 returned for missing run_id (not 500)
- [ ] Request ID captured from header or state
- [ ] Response includes all expected fields

### Observability
- [ ] Request ID flows through to advisory refs
- [ ] Timestamps present on all created records
- [ ] Engine provenance captured (engine_id, engine_version)
- [ ] Errors logged with context (not just swallowed)
- [ ] Timing metrics added for slow operations

### Integration Points
- [ ] Compatible with existing RMOS runs store
- [ ] Advisory store import path correct
- [ ] No circular imports
- [ ] Environment variables documented (RMOS_RUNS_DIR)

### Testing
- [ ] Unit tests for schema validation
- [ ] Unit tests for hashing determinism
- [ ] Unit tests for store CRUD operations
- [ ] Integration test for suggest-and-attach flow
- [ ] Chaos test for concurrent writes
- [ ] Test for idempotent advisory attach

### Governance
- [ ] Auto-approval policy documented and justified
- [ ] Audit trail complete (who approved, when)
- [ ] `reviewed_by="system"` distinguishable from human review

---

## Appendix: Quick Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RMOS_RUNS_DIR` | `data/rmos_runs` | Directory for run artifact storage |

### Status Values

| Field | Values |
|-------|--------|
| `status` | `OK`, `BLOCKED`, `ERROR` |
| `explanation_status` | `NONE`, `PENDING`, `READY`, `ERROR` |
| `AdvisoryInputRef.kind` | `explanation`, `advisory`, `note`, `unknown` |
| `RunDecision.risk_level` | `GREEN`, `YELLOW`, `RED`, `ERROR` (convention) |

### API Quick Reference

```bash
# Create run
curl -X POST http://localhost:8000/api/rmos/runs \
  -H "Content-Type: application/json" \
  -d '{"mode":"cam","tool_id":"T102","status":"OK"}'

# Get run
curl http://localhost:8000/api/rmos/runs/{run_id}

# Attach advisory
curl -X POST http://localhost:8000/api/rmos/runs/{run_id}/attach-advisory \
  -H "Content-Type: application/json" \
  -d '{"advisory_id":"adv_123","kind":"explanation"}'

# Generate explanation
curl -X POST http://localhost:8000/api/rmos/runs/{run_id}/suggest-and-attach \
  -H "Content-Type: application/json" \
  -d '{"generate_explanation":true}'
```

---

*Document generated: December 18, 2025*
