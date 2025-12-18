# AI_RMOS_Generator System Evaluation

**Evaluated:** December 2024
**Location:** `AI_RMOS_Generator/`
**Status:** AI-generated, submitted for integration review

---

## Executive Summary

`AI_RMOS_Generator` is an AI-generated implementation of governance-compliant RMOS run artifact storage. It claims compliance with `RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md`.

**Before adopting:** This code requires human review. This evaluation documents what the code *claims* to do, not whether it's correct or production-ready.

---

## 1. Architecture & Flow

### 1.1 Module Structure (10 files, ~2,170 lines)

```
AI_RMOS_Generator/
├── __init__.py          (68 lines)   - Re-exports with __all__
├── schemas.py          (150 lines)   - Pydantic models
├── store.py            (418 lines)   - Date-partitioned storage
├── api_runs.py         (342 lines)   - FastAPI router
├── hashing.py           (75 lines)   - SHA256 utilities
├── diff.py             (192 lines)   - Run comparison
├── attachments.py      (115 lines)   - Content-addressed storage
├── compat.py           (257 lines)   - v1 ↔ v2 conversion
├── migration_utils.py  (326 lines)   - Migration tooling
└── cli_migrate.py      (227 lines)   - CLI for migration
```

### 1.2 Data Flow

```
POST /api/rmos/runs
    │
    ├─→ Compute feasibility_sha256 from payload
    ├─→ Build RunDecision with risk_level
    ├─→ Create RunArtifact (Pydantic validation)
    └─→ store.put()
            │
            ├─→ FileLock acquire
            ├─→ Check exists → ImmutabilityViolation if true
            └─→ Atomic write (.tmp + os.replace)

POST /runs/{id}/attach-advisory
    │
    └─→ Creates SEPARATE _advisory_*.json file (immutability preserved)

POST /runs/{id}/explanation
    │
    └─→ Creates SEPARATE _explanation.json file (immutability preserved)

GET /runs/{id}
    │
    ├─→ Load core artifact
    ├─→ Merge advisory links from _advisory_*.json files
    └─→ Merge explanation from _explanation.json file
```

### 1.3 Storage Layout

```
{RMOS_RUNS_GOV_DIR}/                    # Default: data/runs/rmos
├── 2025-12-17/
│   ├── run_abc123def456.json           # Core artifact (immutable)
│   ├── run_abc123def456_advisory_adv_001.json
│   └── run_abc123def456_explanation.json
└── 2025-12-18/
    └── run_xyz789...json
```

---

## 2. Edge Cases

### 2.1 Concurrency

**Implementation:** `filelock.FileLock` per file

```python
with FileLock(self._lock_path(path)):
    if path.exists():
        raise ImmutabilityViolation(...)
    self._atomic_write(path, data)
```

**Risk:** Requires `filelock` package in dependencies.

### 2.2 Duplicate Writes

```python
except ImmutabilityViolation as e:
    raise HTTPException(status_code=409, detail={"error": "ARTIFACT_EXISTS", ...})
```

**Behavior:** Returns 409 Conflict.

### 2.3 Path Traversal

```python
_RUN_ID_PATTERN = re.compile(r'^run_[a-f0-9]{12}$')
```

**Protection:** Rejects anything not matching `run_[12 hex chars]`.

### 2.4 Empty Required Fields

```python
@field_validator("feasibility_sha256")
@classmethod
def feasibility_sha256_not_empty(cls, v: str) -> str:
    if not v or not v.strip():
        raise ValueError("feasibility_sha256 is REQUIRED and cannot be empty")
    return v
```

**Behavior:** Fails on empty string, not just None.

### 2.5 Advisory Idempotency

```python
if link_path.exists():
    logger.debug(f"Advisory {advisory_id} already attached to {run_id}")
    return self.get(run_id)
```

**Behavior:** Silent success if already attached.

### 2.6 Corrupt File Handling

```python
except Exception as e:
    logger.warning(f"Skipping corrupt run file {path}: {e}")
    continue
```

**Behavior:** Logs and skips, doesn't crash.

---

## 3. Observability & Testing

### 3.1 Logging

| Event | Level | Fields |
|-------|-------|--------|
| `run.created` | INFO | run_id, status, risk_level |
| `advisory.attached` | INFO | run_id, advisory_id |
| `explanation.set` | INFO | run_id, status |
| Corrupt file | WARNING | path, error |
| Read error | ERROR | run_id, exception |

### 3.2 Testing Support

```python
def reset_store() -> None:
    """Reset the store singleton (for testing)."""
    global _store
    _store = None
```

**Use:** Call between tests to reset singleton state.

### 3.3 Diff for Auditing

```python
def diff_runs(a: RunArtifact, b: RunArtifact) -> Dict[str, Any]:
    """
    Severity levels:
    - CRITICAL: Hash mismatch, status change to/from ERROR
    - WARNING: Risk level change, significant score drift
    - INFO: Metadata differences
    """
```

---

## 4. Operational Risks

### 4.1 Dependencies

| Dependency | Purpose | Risk |
|------------|---------|------|
| `filelock` | Per-file locking | Must be in requirements.txt |
| `pydantic` | Schema validation | Already in project |
| `fastapi` | API router | Already in project |

### 4.2 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RMOS_RUNS_GOV_DIR` | `data/runs/rmos` | Run storage root |
| `RMOS_ATTACHMENTS_DIR` | `data/runs/attachments` | Attachment storage |

**Note:** Different env var name than existing `runs_v2/` (`RMOS_RUNS_V2_DIR`).

### 4.3 Partition Scan Performance

**Issue:** `get()` scans all date partitions (newest first) to find a run.

**For large datasets:** May need index file.

### 4.4 Lock File Orphaning

**Risk:** Crash during write leaves `.lock` file.
**Mitigation:** `filelock` handles stale locks.

---

## 5. Graceful Failure

### 5.1 API Error Responses

| HTTP | Error Code | Meaning |
|------|------------|---------|
| 201 | - | Created successfully |
| 404 | `RUN_NOT_FOUND` | Run ID doesn't exist |
| 404 | `ATTACHMENT_NOT_FOUND` | Attachment SHA not found |
| 409 | `ARTIFACT_EXISTS` | Duplicate write attempt |
| 422 | (Pydantic) | Validation failure |

### 5.2 Migration Failures

```python
report.errors.append({
    "run_id": run_id,
    "error": str(e),
    "type": type(e).__name__,
})
report.error_count += 1
# Continues to next record
```

**Behavior:** Logs per-record errors, continues migration.

### 5.3 Hash Verification

```python
def verify_hash(expected: str, actual: str) -> bool:
    import hmac
    return hmac.compare_digest(expected.lower(), actual.lower())
```

**Security:** Constant-time comparison prevents timing attacks.

---

## 6. Comparison to Existing `runs_v2/`

| Feature | `runs_v2/` | `AI_RMOS_Generator` |
|---------|-----------|---------------------|
| Env var | `RMOS_RUNS_V2_DIR` | `RMOS_RUNS_GOV_DIR` |
| File count | 12 | 10 |
| Total lines | ~2,400 | ~2,170 |
| Lock mechanism | `filelock` | `filelock` |
| CLI commands | status/migrate/verify/rollback | Same |

**Key difference:** Environment variable name.

---

## 7. Integration Concerns

### 7.1 Before Adopting

1. **Add `filelock` to requirements.txt** if not present
2. **Decide env var naming**: Use `RMOS_RUNS_GOV_DIR` or change to match existing
3. **Test with actual data**: Run migration with `--dry-run` first
4. **Review for duplicates**: May overlap with `runs_v2/` in `services/api/app/rmos/`

### 7.2 Module Location

Currently at repo root. Needs to move to:
```
services/api/app/rmos/runs_gov/   # or replace runs_v2/
```

### 7.3 Router Registration

```python
# In main.py
from AI_RMOS_Generator import router as runs_gov_router
app.include_router(runs_gov_router)
```

---

## 8. Re-Review Checklist

Use after making changes:

### 8.1 Schema Compliance
- [ ] `feasibility_sha256` is `str` (not `Optional[str]`)
- [ ] `risk_level` is `str` (not `Optional[str]`)
- [ ] Field validators reject empty strings
- [ ] All models inherit from `BaseModel`

### 8.2 Storage Compliance
- [ ] Date partitions: `{YYYY-MM-DD}/{run_id}.json`
- [ ] Atomic writes: `.tmp` + `os.replace()`
- [ ] Per-file locking with `FileLock`
- [ ] `ImmutabilityViolation` on duplicate write
- [ ] Advisory links in separate files
- [ ] Explanation in separate file

### 8.3 API Compliance
- [ ] POST returns 201
- [ ] 409 on duplicate
- [ ] 404 with structured JSON
- [ ] NO PATCH endpoint
- [ ] `attach-advisory` creates link file
- [ ] `explanation` creates status file

### 8.4 Security
- [ ] `run_id` validated: `^run_[a-f0-9]{12}$`
- [ ] Advisory IDs sanitized
- [ ] Hash comparison uses `hmac.compare_digest`
- [ ] `sha256_json(None)` raises error

### 8.5 Migration CLI
- [ ] `--dry-run` validates without writing
- [ ] Backup created by default
- [ ] `verify` compares v1 and v2
- [ ] `rollback` restores from backup
- [ ] Errors logged per-record

### 8.6 Dependencies
- [ ] `filelock` in requirements.txt
- [ ] `pydantic` version compatible (v2 syntax used)

---

## 9. Verdict

**Status:** Requires human review before integration.

**Appears to implement:**
- Pydantic schemas with required field validation
- Date-partitioned immutable storage
- Append-only advisory/explanation pattern
- Migration tooling with backup/verify/rollback

**Action items before adoption:**
1. Verify `filelock` dependency
2. Decide final module location
3. Resolve env var naming (`RMOS_RUNS_GOV_DIR` vs `RMOS_RUNS_V2_DIR`)
4. Run migration with `--dry-run`
5. Write integration tests
6. Determine if this replaces or coexists with `runs_v2/`
