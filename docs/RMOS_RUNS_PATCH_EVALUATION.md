# RMOS Runs Patch Evaluation
## System Analysis for The Luthier's ToolBox Project

**Document Version:** 1.0.0
**Evaluation Date:** December 18, 2025
**Patch Source:** `rmos_runs__init__Patch.txt`
**Status:** Pending Implementation - Dry Run Recommended

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture & Data Flow](#3-architecture--data-flow)
4. [Data Model](#4-data-model)
5. [Edge Cases Analysis](#5-edge-cases-analysis)
6. [Observability & Testing](#6-observability--testing)
7. [Operational Risks](#7-operational-risks)
8. [Graceful Failure Analysis](#8-graceful-failure-analysis)
9. [Security Considerations](#9-security-considerations)
10. [API Endpoints](#10-api-endpoints)
11. [Implementation Checklist](#11-implementation-checklist)
12. [Dry Run Plan](#12-dry-run-plan)
13. [Overall Assessment](#13-overall-assessment)

---

## 1. Executive Summary

### What This Patch Does

The RMOS Runs patch implements a **run artifact storage and retrieval system** for tracking CNC manufacturing operations. It provides:

- **Persistent storage** of manufacturing run records
- **Audit trail** with request summaries and feasibility snapshots
- **Content integrity** via SHA256 hashing utilities
- **Advisory hooks** for attaching explanations and notes to runs

### Files Included in Patch

| File | Purpose | Status |
|------|---------|--------|
| `schemas.py` | Pydantic models for RunArtifact and related types | NEW |
| `hashing.py` | SHA256 utilities for content integrity | NEW |
| `store.py` | Filesystem-backed JSON storage | NEW |
| `router.py` | FastAPI endpoints for CRUD operations | NEW |
| `__init__.py` | Fix broken imports, export public API | FIX |

### Key Findings

| Aspect | Rating | Summary |
|--------|--------|---------|
| Architecture | ✅ Good | Clean separation of concerns |
| Simplicity | ✅ Good | Easy to debug filesystem store |
| Error Handling | ⚠️ Needs Work | Exceptions bubble up unstructured |
| Security | ⚠️ Needs Work | Path traversal vulnerability |
| Concurrency | 🔴 Risk | No locking on load-modify-save |

---

## 2. System Overview

### Purpose

RMOS Runs serves as the **persistent record** of manufacturing operations. Each "run" captures:

- What was requested (design parameters, context)
- What the feasibility engine decided (risk level, score, warnings)
- What was produced (G-code, operation plans, previews)
- What advisories were attached (explanations, notes)

### Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    RMOS ECOSYSTEM                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Feasibility Engine ───────┐                                    │
│    (evaluates risk)        │                                    │
│                            ▼                                    │
│                      ┌──────────┐                               │
│  User Request ──────▶│  RUNS    │◀────── Advisory System        │
│                      │  STORE   │         (explanations)        │
│                      └────┬─────┘                               │
│                           │                                     │
│                           ▼                                     │
│                    Run Artifacts                                │
│                    (JSON files)                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Architecture & Data Flow

### Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT REQUEST                                     │
│  POST /api/rmos/runs                                                        │
│  {mode: "cam", tool_id: "T102", status: "OK", request_summary: {...}}       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            router.py                                         │
│                                                                             │
│  create_run():                                                              │
│    1. Generate run_id = "run_" + uuid4().hex[:12]                          │
│    2. Extract request_id from headers/state                                 │
│    3. Construct RunArtifact with defaults                                   │
│    4. _store().put(run)                                                     │
│    5. Return RunArtifact                                                    │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            store.py                                          │
│                     RunStore (Filesystem-backed)                             │
│                                                                             │
│  put(run):                                                                  │
│    1. Sanitize run_id for filename                                          │
│    2. Serialize to JSON with model_dump(mode="json")                        │
│    3. Write to .tmp file                                                    │
│    4. Atomic rename via os.replace()                                        │
│                                                                             │
│  Storage: data/rmos_runs/{run_id}.json                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| `schemas.py` | Data models, validation | Pydantic |
| `hashing.py` | Content integrity, request summarization | hashlib, json |
| `store.py` | Persistence, CRUD operations | schemas.py |
| `router.py` | HTTP interface, request handling | store.py, schemas.py |

---

## 4. Data Model

### RunArtifact Schema

```
RunArtifact
├── run_id: str                          # "run_abc123def456"
├── created_at_utc: datetime             # Auto-set to UTC now
├── mode: str                            # "cam", "feasibility", etc.
├── tool_id: str                         # Tool identifier
├── status: Literal["OK","BLOCKED","ERROR"]
│
├── request_summary: Dict                # Redacted request for audit
├── feasibility: Dict                    # Engine result snapshot
│
├── decision: RunDecision
│   ├── risk_level: str                  # GREEN/YELLOW/RED/ERROR
│   ├── score: float                     # 0-100
│   ├── block_reason: str                # Why blocked (if applicable)
│   ├── warnings: List[str]              # Warning messages
│   └── details: Dict                    # Additional context
│
├── hashes: Hashes
│   ├── feasibility_sha256: str          # Hash of feasibility payload
│   ├── toolpaths_sha256: str            # Hash of toolpath data
│   ├── gcode_sha256: str                # Hash of generated G-code
│   └── opplan_sha256: str               # Hash of operation plan
│
├── outputs: RunOutputs
│   ├── gcode_text: str                  # Inline G-code (small files)
│   ├── opplan_json: Dict                # Operation plan data
│   ├── gcode_path: str                  # Path to G-code file
│   ├── opplan_path: str                 # Path to opplan file
│   └── preview_svg_path: str            # Path to preview image
│
├── advisory_inputs: List[AdvisoryInputRef]  # Append-only list
│   └── AdvisoryInputRef
│       ├── advisory_id: str
│       ├── kind: "explanation"|"advisory"|"note"|"unknown"
│       ├── created_at_utc: datetime
│       ├── request_id: str              # Correlation ID
│       ├── engine_id: str               # Which engine produced it
│       └── engine_version: str          # Engine version
│
├── explanation_status: "NONE"|"PENDING"|"READY"|"ERROR"
├── explanation_summary: str             # Brief explanation text
│
└── meta: Dict                           # Free-form extras
```

### Supporting Models

```python
class Hashes(BaseModel):
    feasibility_sha256: Optional[str] = None
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    opplan_sha256: Optional[str] = None

class RunDecision(BaseModel):
    risk_level: Optional[str] = None
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

class RunOutputs(BaseModel):
    gcode_text: Optional[str] = None
    opplan_json: Optional[Dict[str, Any]] = None
    gcode_path: Optional[str] = None
    opplan_path: Optional[str] = None
    preview_svg_path: Optional[str] = None
```

---

## 5. Edge Cases Analysis

### Handled Edge Cases

| Edge Case | Handling | Location |
|-----------|----------|----------|
| Invalid `status` value | Pydantic Literal validation → 422 | `schemas.py:84` |
| Missing run on GET | Returns `None` → 404 | `store.py:201-204` |
| Missing run on PATCH | Returns `None` → 404 | `store.py:208-211` |
| Non-existent storage dir | Auto-created with `mkdir(parents=True)` | `store.py:186` |
| `/` and `\` in run_id | Sanitized to `_` | `store.py:190` |
| Unicode in content | `ensure_ascii=False` in JSON dump | `store.py:198` |
| Empty `meta_updates` | Applied as no-op | `router.py:305` |

### Unhandled Edge Cases (Risks)

| Edge Case | Current Behavior | Risk Level | Recommendation |
|-----------|------------------|------------|----------------|
| **Path traversal in run_id** | Partial sanitization only | 🔴 Critical | Strict regex validation |
| **Concurrent writes** | Last-write-wins, data loss possible | 🔴 High | File locking or SQLite |
| **Disk full** | Exception bubbles up as 500 | ⚠️ Medium | Catch, return 507 |
| **Corrupt JSON file** | `json.loads()` raises exception | ⚠️ Medium | Try/except, return None |
| **Very large gcode_text** | Stored inline, slow reads | ⚠️ Medium | External file reference |
| **run_id collision** | UUID-based, very low risk | ✅ Low | Acceptable |

### Path Traversal Vulnerability

```python
# CURRENT: Incomplete sanitization
def _path_for(self, run_id: str) -> Path:
    safe = run_id.replace("/", "_").replace("\\", "_")
    return self.root / f"{safe}.json"

# ATTACK:
run_id = ".._.._etc_passwd"  # After sanitization, still problematic

# RECOMMENDED FIX:
import re
_RUN_ID_RE = re.compile(r"^run_[a-f0-9]{12}$")

def _path_for(self, run_id: str) -> Path:
    if not _RUN_ID_RE.match(run_id):
        raise ValueError(f"Invalid run_id format: {run_id}")
    return self.root / f"{run_id}.json"
```

---

## 6. Observability & Testing

### Current Observability

| Aspect | Status | Implementation |
|--------|--------|----------------|
| Request correlation | ✅ Implemented | `request_id` stored in meta |
| Timestamps | ✅ Implemented | `created_at_utc` auto-populated |
| Content hashes | ⚠️ Schema only | `Hashes` model defined, not auto-computed |
| Advisory provenance | ✅ Designed | `AdvisoryInputRef` has engine tracking |
| Error logging | ❌ Missing | No structured error logging |
| Performance timing | ❌ Missing | No operation timing |

### Recommended Logging

```python
import logging
logger = logging.getLogger("rmos.runs")

# In store.py
def put(self, run: RunArtifact) -> bool:
    logger.info("Saving run %s", run.run_id)
    try:
        # ... existing code ...
        logger.debug("Run %s saved to %s", run.run_id, path)
        return True
    except Exception as e:
        logger.error("Failed to save run %s: %s", run.run_id, e)
        return False
```

### Test Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      TEST PYRAMID                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌─────────────┐                              │
│                    │   E2E API   │  ← curl commands             │
│                    │   Tests     │    (manual verification)     │
│                    └──────┬──────┘                              │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │ Integration │  ← Router + Store + FS       │
│                    │   Tests     │    (TestClient)              │
│                    └──────┬──────┘                              │
│                           │                                     │
│              ┌────────────▼────────────┐                        │
│              │      Unit Tests         │  ← Individual funcs    │
│              │  (hashing, schemas)     │    (pytest + tmp_path) │
│              └─────────────────────────┘                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Unit Tests

```python
# tests/rmos/runs/test_hashing.py

def test_sha256_text_deterministic():
    """Same input should always produce same hash."""
    assert sha256_text("hello") == sha256_text("hello")
    assert sha256_text("hello") != sha256_text("world")

def test_sha256_text_none_returns_none():
    """None input should return None, not crash."""
    assert sha256_text(None) is None

def test_sha256_json_key_order_independent():
    """JSON hashing should be deterministic regardless of key order."""
    a = sha256_json({"b": 2, "a": 1})
    b = sha256_json({"a": 1, "b": 2})
    assert a == b

def test_summarize_request_limits_keys():
    """Request summary should limit exposed keys for privacy."""
    big_request = {f"key_{i}": i for i in range(100)}
    summary = summarize_request(big_request)
    assert len(summary["keys"]) <= 50

def test_summarize_request_handles_non_dict():
    """Non-dict input should not crash."""
    summary = summarize_request("not a dict")
    assert summary["note"] == "non-dict request"
```

```python
# tests/rmos/runs/test_store.py

def test_put_get_roundtrip(tmp_path):
    """Store should preserve run data through save/load cycle."""
    store = RunStore(str(tmp_path))
    run = RunArtifact(
        run_id="run_test123456",
        mode="cam",
        tool_id="T1",
        status="OK"
    )
    store.put(run)
    retrieved = store.get("run_test123456")
    assert retrieved is not None
    assert retrieved.run_id == "run_test123456"
    assert retrieved.mode == "cam"

def test_get_nonexistent_returns_none(tmp_path):
    """Getting non-existent run should return None, not raise."""
    store = RunStore(str(tmp_path))
    assert store.get("nonexistent") is None

def test_patch_meta_updates_and_preserves(tmp_path):
    """Patch should update meta while preserving other fields."""
    store = RunStore(str(tmp_path))
    run = RunArtifact(
        run_id="run_test123456",
        mode="cam",
        tool_id="T1",
        status="OK",
        meta={"existing": "value"}
    )
    store.put(run)
    updated = store.patch_meta("run_test123456", {"new_key": "new_value"})
    assert updated.meta["existing"] == "value"
    assert updated.meta["new_key"] == "new_value"

def test_atomic_write_creates_no_orphan_tmp(tmp_path):
    """Successful write should not leave .tmp files."""
    store = RunStore(str(tmp_path))
    run = RunArtifact(run_id="run_test123456", mode="x", tool_id="y", status="OK")
    store.put(run)
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0
```

```python
# tests/rmos/runs/test_schemas.py

def test_run_artifact_status_validation():
    """Invalid status should raise ValidationError."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RunArtifact(
            run_id="test",
            mode="x",
            tool_id="y",
            status="INVALID"  # Not in Literal["OK", "BLOCKED", "ERROR"]
        )

def test_run_artifact_defaults():
    """RunArtifact should have sensible defaults."""
    run = RunArtifact(run_id="test", mode="x", tool_id="y", status="OK")
    assert run.request_summary == {}
    assert run.feasibility == {}
    assert run.advisory_inputs == []
    assert run.explanation_status == "NONE"
```

---

## 7. Operational Risks

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Filesystem fills up** | Medium | High | Monitor disk, rotate old runs |
| **Concurrent write corruption** | Medium | High | File locking or SQLite |
| **Path traversal attack** | Low | Critical | Strict run_id regex |
| **Large runs slow reads** | Medium | Medium | Compress or external refs |
| **No backup/replication** | High | High | Define backup strategy |
| **Sensitive data exposure** | Medium | High | Audit `summarize_request()` |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RMOS_RUNS_DIR` | `data/rmos_runs` | Storage directory path |

### Disk Space Considerations

```
Average run file size: ~2-5 KB (metadata only)
With inline gcode_text: ~50-500 KB
With large opplan_json: ~100 KB - 1 MB

Estimated storage:
- 1,000 runs/day × 5 KB = 5 MB/day
- 1,000 runs/day × 100 KB = 100 MB/day

Recommendation: Implement rotation policy for runs older than 90 days
```

---

## 8. Graceful Failure Analysis

### Current Failure Cascade

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         FAILURE CASCADE                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Request arrives at router                                                │
│       │                                                                   │
│       ▼                                                                   │
│  Pydantic validation                                                      │
│       ├── Invalid status ──────────────▶ 422 Unprocessable (GOOD)        │
│       └── Valid ──────────────────────▶ Continue                          │
│                                                                           │
│  _store().put(run)                                                        │
│       ├── mkdir fails ─────────────────▶ 500 Internal Error (BAD)        │
│       ├── write fails (disk full) ─────▶ 500 Internal Error (BAD)        │
│       ├── rename fails ────────────────▶ 500 Internal Error (BAD)        │
│       └── success ─────────────────────▶ Return RunArtifact               │
│                                                                           │
│  _store().get(run_id)                                                     │
│       ├── file not found ──────────────▶ None → 404 (GOOD)               │
│       ├── JSON parse error ────────────▶ 500 Internal Error (BAD)        │
│       ├── Pydantic validation error ───▶ 500 Internal Error (BAD)        │
│       └── success ─────────────────────▶ Return RunArtifact               │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### Recommended Hardening

```python
# store.py - Hardened version

import logging
logger = logging.getLogger("rmos.runs.store")

class RunStore:
    def get(self, run_id: str) -> Optional[RunArtifact]:
        path = self._path_for(run_id)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return RunArtifact.model_validate(raw)
        except json.JSONDecodeError as e:
            logger.error("Corrupt JSON in run file %s: %s", path, e)
            return None
        except ValidationError as e:
            logger.error("Invalid run data in %s: %s", path, e)
            return None
        except Exception as e:
            logger.error("Unexpected error loading run %s: %s", run_id, e)
            return None

    def put(self, run: RunArtifact) -> bool:
        """Returns True on success, False on failure."""
        try:
            path = self._path_for(run.run_id)
            tmp = path.with_suffix(".json.tmp")
            payload = run.model_dump(mode="json")
            tmp.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            os.replace(tmp, path)
            return True
        except OSError as e:
            logger.error("OS error saving run %s: %s", run.run_id, e)
            # Clean up tmp file if it exists
            if tmp.exists():
                tmp.unlink()
            return False
        except Exception as e:
            logger.error("Unexpected error saving run %s: %s", run.run_id, e)
            return False
```

---

## 9. Security Considerations

### Security Checklist

| Concern | Status | Notes |
|---------|--------|-------|
| **Input validation** | ⚠️ Partial | Pydantic validates types, run_id needs stricter checks |
| **Path traversal** | 🔴 Vulnerable | Current sanitization is incomplete |
| **Data at rest** | ❌ Unencrypted | JSON files readable with filesystem access |
| **Authentication** | ❌ None | Assumed behind auth middleware |
| **Authorization** | ❌ None | No per-run access control |
| **Audit logging** | ⚠️ Partial | request_id tracked, no write audit log |
| **Sensitive data** | ⚠️ Risk | `request_summary` may contain PII |

### Path Traversal Fix

```python
# Add to store.py
import re

_RUN_ID_RE = re.compile(r"^run_[a-f0-9]{12}$")

def _validate_run_id(self, run_id: str) -> None:
    """Validate run_id format to prevent path traversal."""
    if not _RUN_ID_RE.match(run_id):
        raise ValueError(
            f"Invalid run_id format: {run_id}. "
            f"Expected: run_<12 hex chars>"
        )

def _path_for(self, run_id: str) -> Path:
    self._validate_run_id(run_id)
    return self.root / f"{run_id}.json"
```

### Data Redaction Policy

```python
# In hashing.py - strengthen summarize_request()

REDACT_KEYS = {"password", "token", "secret", "api_key", "credentials"}

def summarize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Produce redacted summary for audit logging."""
    if not isinstance(request, dict):
        return {"type": str(type(request)), "note": "non-dict request"}

    # Filter out sensitive keys
    safe_keys = [k for k in request.keys() if k.lower() not in REDACT_KEYS]
    summary: Dict[str, Any] = {"keys": safe_keys[:50]}

    # ... rest of function
```

---

## 10. API Endpoints

### Implemented Endpoints

| Method | Path | Request Body | Response | Description |
|--------|------|--------------|----------|-------------|
| POST | `/api/rmos/runs` | `RunCreateRequest` | `RunArtifact` | Create new run |
| GET | `/api/rmos/runs/{run_id}` | - | `RunArtifact` | Get run by ID |
| PATCH | `/api/rmos/runs/{run_id}/meta` | `RunPatchMetaRequest` | `RunArtifact` | Update run meta |

### Request/Response Models

```python
# POST /api/rmos/runs
class RunCreateRequest(BaseModel):
    mode: str = "unknown"
    tool_id: str = "unknown"
    status: str = "OK"
    request_summary: Dict[str, Any] = Field(default_factory=dict)
    feasibility: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)

# PATCH /api/rmos/runs/{run_id}/meta
class RunPatchMetaRequest(BaseModel):
    meta_updates: Dict[str, Any] = Field(default_factory=dict)
```

### Future Endpoints (Not in Patch)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/rmos/runs` | List runs with pagination |
| DELETE | `/api/rmos/runs/{run_id}` | Delete run |
| POST | `/api/rmos/runs/{run_id}/advisory` | Attach advisory |
| GET | `/api/rmos/runs/{run_id}/hashes` | Get integrity hashes |
| POST | `/api/rmos/runs/{run_id}/suggest-and-attach` | Generate and attach explanation |

---

## 11. Implementation Checklist

### Pre-Implementation

- [ ] Verify `services/api/app/rmos/runs/` directory exists
- [ ] Check current `__init__.py` exports (preserve if needed)
- [ ] Verify `data/rmos_runs/` doesn't conflict with existing data
- [ ] Review `main.py` router registration pattern

### File Creation

#### schemas.py
- [ ] `utc_now()` returns timezone-aware datetime
- [ ] `Hashes` model with all hash fields optional
- [ ] `RunDecision` with risk_level, score, block_reason, warnings, details
- [ ] `RunOutputs` with inline and path fields
- [ ] `AdvisoryInputRef` with provenance fields
- [ ] `RunArtifact` with status Literal validation
- [ ] All default factories use `Field(default_factory=...)`

#### hashing.py
- [ ] `sha256_text(None)` returns `None`
- [ ] `sha256_json()` uses `sort_keys=True`
- [ ] `summarize_request()` limits key exposure
- [ ] `summarize_request()` handles non-dict gracefully

#### store.py
- [ ] `RunStore.__init__()` creates directory
- [ ] `_path_for()` validates run_id format (add regex)
- [ ] `put()` uses atomic write pattern
- [ ] `put()` wrapped in try/except (add)
- [ ] `get()` returns None for missing files
- [ ] `get()` wrapped in try/except (add)
- [ ] `patch_meta()` returns None for missing run

#### router.py
- [ ] Prefix is `/api/rmos/runs`
- [ ] `create_run()` generates UUID-based run_id
- [ ] `create_run()` extracts request_id
- [ ] `get_run()` returns 404 for missing
- [ ] `patch_run_meta()` returns 404 for missing
- [ ] `RMOS_RUNS_DIR` env var with default

#### __init__.py
- [ ] Exports all schema classes
- [ ] Exports all hashing functions
- [ ] Exports `RunStore`

### Integration

- [ ] Router registered in `main.py`
- [ ] No import errors on startup
- [ ] Manual curl test: create run
- [ ] Manual curl test: get run
- [ ] Manual curl test: patch meta
- [ ] Verify JSON file created in `data/rmos_runs/`

### Security Hardening

- [ ] Run ID regex validation added
- [ ] Sensitive key redaction in summarize_request()
- [ ] Error handling added to store operations

### Testing

- [ ] Unit tests for hashing functions
- [ ] Unit tests for store CRUD
- [ ] Unit tests for schema validation
- [ ] Integration test for router

### Documentation

- [ ] API endpoints documented
- [ ] Environment variables documented
- [ ] Backup strategy defined

---

## 12. Dry Run Plan

### Phase 1: Reconnaissance

```bash
# Check existing runs folder state
ls -la services/api/app/rmos/runs/

# Check current __init__.py
cat services/api/app/rmos/runs/__init__.py

# Check if data directory exists
ls -la data/

# Check main.py router pattern
grep -n "include_router" services/api/app/main.py
```

### Phase 2: Isolated Implementation

1. Create files WITHOUT router wiring
2. Add hardened run_id validation
3. Add try/except wrappers
4. Run syntax checks: `python -m py_compile <file>`
5. Create test file
6. Run unit tests with temp directory

### Phase 3: Integration

1. Create router.py
2. Update __init__.py
3. Wire into main.py
4. Restart API server
5. Execute curl tests

### Phase 4: Verification

```bash
# Create a run
curl -X POST http://127.0.0.1:8000/api/rmos/runs \
  -H "Content-Type: application/json" \
  -H "x-request-id: test-001" \
  -d '{"mode":"cam","tool_id":"T102","status":"OK"}'

# Get the run (replace RUN_ID)
curl http://127.0.0.1:8000/api/rmos/runs/<RUN_ID>

# Patch meta
curl -X PATCH http://127.0.0.1:8000/api/rmos/runs/<RUN_ID>/meta \
  -H "Content-Type: application/json" \
  -d '{"meta_updates":{"verified":true}}'

# Verify file exists
cat data/rmos_runs/<RUN_ID>.json
```

---

## 13. Overall Assessment

### Summary Ratings

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Architecture** | ✅ Good | Clean separation: schemas, hashing, store, router |
| **Simplicity** | ✅ Good | Filesystem store is easy to debug and inspect |
| **Extensibility** | ✅ Good | Clear path to SQLite/DB migration |
| **Error Handling** | ⚠️ Needs Work | Exceptions bubble up unstructured |
| **Security** | ⚠️ Needs Work | Path traversal vulnerability in run_id |
| **Concurrency** | 🔴 Risk | No locking on load-modify-save |
| **Observability** | ⚠️ Partial | request_id tracked, but no timing/logging |

### Recommendation

**Safe to implement for development and testing.**

Before production deployment, address:

1. **Critical:** Add strict run_id regex validation
2. **High:** Add try/except wrappers in store operations
3. **High:** Implement file locking or migrate to SQLite
4. **Medium:** Add structured logging
5. **Medium:** Define backup/rotation policy

### Next Steps After Implementation

Per the patch document, the next bundle will add:

- `AdvisoryAsset` schema + store
- `POST /api/rmos/runs/{run_id}/suggest-and-attach` endpoint
- Sync explanation path integration

---

**Document Prepared By:** Claude Code
**Review Status:** Ready for Implementation Review
**Recommended Action:** Execute Dry Run Phase 1
