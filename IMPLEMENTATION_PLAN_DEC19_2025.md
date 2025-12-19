# Phased Implementation Plan: RMOS Infrastructure Completion

**Date:** December 19, 2025  
**Estimated Total Effort:** 3-5 development days  
**Risk Level:** Medium-High (broken imports blocking features)

---

## Executive Summary

This plan addresses **critical infrastructure gaps** identified in the December 19, 2025 audit. The implementation is structured in four phases, prioritized by dependency order and risk mitigation.

### Phase Overview

| Phase | Focus | Duration | Risk if Skipped |
|-------|-------|----------|-----------------|
| **Phase 1** | Fix broken imports (RunArtifact) | 2-4 hours | 🔴 Critical — blocks all artifact features |
| **Phase 2** | Database migrations infrastructure | 4-6 hours | 🔴 Critical — blocks WorkflowSession |
| **Phase 3** | Advisory Assets foundation | 4-8 hours | 🟡 Medium — blocks Vision Engine |
| **Phase 4** | Integration & validation | 2-4 hours | 🟠 High — ensures system coherence |

---

## Phase 1: Fix Broken Imports (RunArtifact System)

### 1.1 Objective

Create the three missing files that `runs/__init__.py` imports from, restoring import chain integrity.

### 1.2 Files to Create

```
services/api/app/rmos/runs/
├── __init__.py          # ✅ EXISTS (but imports broken)
├── schemas.py           # 🆕 CREATE
├── hashing.py           # 🆕 CREATE
└── store.py             # 🆕 CREATE
```

### 1.3 Implementation Steps

| Step | Action | Est. Time |
|------|--------|-----------|
| 1.1 | Create `schemas.py` with `RunArtifact`, `RunDecision`, `Hashes`, `RunOutputs` | 30 min |
| 1.2 | Create `hashing.py` with `sha256_text`, `sha256_json`, `sha256_toolpaths_payload`, `summarize_request` | 30 min |
| 1.3 | Create `store.py` with `RunStore` class (file-based persistence) | 45 min |
| 1.4 | Verify imports: `from app.rmos.runs import RunStore, RunArtifact` | 15 min |
| 1.5 | Run existing tests to ensure no regressions | 30 min |

### 1.4 Implications

#### ✅ Pros
- **Immediate**: Unblocks all artifact-dependent features
- **Low risk**: Self-contained change with no external dependencies
- **Spec exists**: Implementation defined in `rmos_runs_schemas.md`

#### ⚠️ Cons
- **File-based storage**: Initial implementation uses JSON files, not SQLite
- **Migration path**: May need to migrate to SQLite later (Phase 2 dependency)

### 1.5 Validation Criteria

```bash
# From services/api/ directory
python -c "from app.rmos.runs import RunStore, RunArtifact, sha256_json; print('✅ Imports OK')"
```

### 1.6 Rollback Strategy

If issues arise, revert to empty `__init__.py` with commented exports:

```python
# Temporarily disabled until implementation complete
# from .schemas import RunArtifact, RunDecision, Hashes, RunOutputs
# from .hashing import sha256_text, sha256_json, ...
# from .store import RunStore
__all__ = []
```

---

## Phase 2: Database Migrations Infrastructure

### 2.1 Objective

Create the `app/db/migrations/` infrastructure to support `WorkflowSession` persistence and future schema evolution.

### 2.2 Files to Create

```
services/api/app/db/
├── __init__.py                    # 🆕 CREATE
└── migrations/
    ├── __init__.py                # 🆕 CREATE
    ├── runner.py                  # 🆕 CREATE
    ├── 0001_init_workflow_sessions.sql  # 🆕 CREATE
    └── 0002_add_indexes.sql       # 🆕 CREATE
```

### 2.3 Implementation Steps

| Step | Action | Est. Time |
|------|--------|-----------|
| 2.1 | **Fix `.gitignore`**: Change `migrations/` → `/migrations/` | 5 min |
| 2.2 | Create `app/db/__init__.py` with `run_migrations()` export | 10 min |
| 2.3 | Create `app/db/migrations/__init__.py` with `get_migration_files()` | 15 min |
| 2.4 | Create `app/db/migrations/runner.py` with idempotent executor | 45 min |
| 2.5 | Create `0001_init_workflow_sessions.sql` | 30 min |
| 2.6 | Create `0002_add_indexes.sql` | 15 min |
| 2.7 | Add startup hook in `app/main.py` | 15 min |
| 2.8 | Test migration runner with fresh database | 30 min |

### 2.4 `.gitignore` Change (CRITICAL)

**Before (Line 110):**
```gitignore
migrations/
```

**After:**
```gitignore
/migrations/
```

> ⚠️ **Why This Matters**: Without anchoring, Git ignores `app/db/migrations/*.sql` files, making them invisible to version control.

### 2.5 Implications

#### ✅ Pros
- **Future-proof**: Supports schema evolution without manual intervention
- **Idempotent**: Safe to run multiple times (tracks applied migrations)
- **Integrated**: Uses existing `RMOSDatabase` infrastructure

#### ⚠️ Cons
- **Startup cost**: Adds ~50-100ms to cold start (migration check)
- **SQLite limitation**: No concurrent migration support (single-writer)
- **Schema drift risk**: Inline schema in `rmos_db.py` may diverge from migrations

### 2.6 Alternative Considered: Alembic

| Factor | Custom Runner | Alembic |
|--------|---------------|---------|
| **Complexity** | Low | Medium |
| **Dependencies** | None | `alembic` package |
| **Auto-generation** | No | Yes |
| **Team familiarity** | High (plain SQL) | Variable |

**Decision**: Custom runner chosen for simplicity and zero new dependencies.

### 2.7 Validation Criteria

```bash
# From services/api/ directory
cd services/api
python -c "from app.db import run_migrations; print(f'Applied: {run_migrations()}')"

# Verify table exists
sqlite3 data/rmos.db "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_sessions';"
```

### 2.8 Rollback Strategy

1. Delete `app/db/` directory
2. Revert `.gitignore` change
3. Drop `workflow_sessions` and `applied_migrations` tables if created

---

## Phase 3: Advisory Assets Foundation

### 3.1 Objective

Create the `AdvisoryAsset` schema and storage layer to support the Vision Engine integration pattern.

### 3.2 Files to Create

```
services/api/app/_experimental/ai_graphics/
├── advisory_store.py              # 🆕 CREATE
├── advisory_extensions.py         # 🆕 CREATE (optional, can defer)
└── schemas/
    ├── ai_schemas.py              # ✅ EXISTS
    └── advisory_schemas.py        # 🆕 CREATE
```

### 3.3 Implementation Steps

| Step | Action | Est. Time |
|------|--------|-----------|
| 3.1 | Create `advisory_schemas.py` with `AdvisoryAsset`, `AdvisoryAssetType` | 45 min |
| 3.2 | Create `advisory_store.py` with `AdvisoryStore` class | 60 min |
| 3.3 | Update `__init__.py` exports | 15 min |
| 3.4 | (Optional) Create `advisory_extensions.py` for type-specific handlers | 45 min |
| 3.5 | Write unit tests for asset CRUD | 45 min |

### 3.4 Schema Design

```python
class AdvisoryAssetType(str, Enum):
    IMAGE = "IMAGE"           # Generated images
    EXPLANATION = "EXPLANATION"  # LLM explanations
    SUGGESTION = "SUGGESTION"    # Parameter suggestions
    VALIDATION = "VALIDATION"    # Feasibility results

class AdvisoryAsset(BaseModel):
    asset_id: str = Field(default_factory=lambda: str(uuid4()))
    asset_type: AdvisoryAssetType
    source: str                    # e.g., "guitar_vision_engine"
    provider: str                  # e.g., "dalle3", "gpt-4"
    content_hash: str              # SHA256 of content
    suggestion_data: Dict[str, Any]
    approved_for_workflow: bool = False  # Human review gate
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
```

### 3.5 Implications

#### ✅ Pros
- **Governance**: All AI-generated content requires explicit approval
- **Auditability**: Full trail of what was generated and when
- **Extensible**: `asset_type` enum supports future asset categories

#### ⚠️ Cons
- **Overhead**: Every AI output requires explicit storage call
- **Review bottleneck**: Human approval required before workflow integration
- **Storage growth**: Images can be large; need cleanup policy

### 3.6 Dependencies

- **Phase 1**: Uses `sha256_text` from `runs/hashing.py` for content hashing
- **Phase 2**: May migrate to SQLite storage (currently in-memory/file)

### 3.7 Validation Criteria

```python
from app._experimental.ai_graphics.advisory_store import AdvisoryStore
from app._experimental.ai_graphics.schemas.advisory_schemas import AdvisoryAsset, AdvisoryAssetType

store = AdvisoryStore()
asset = AdvisoryAsset(
    asset_type=AdvisoryAssetType.IMAGE,
    source="test",
    provider="test",
    content_hash="abc123",
    suggestion_data={"url": "http://example.com/image.png"},
)
saved = store.save_asset(asset)
retrieved = store.get_asset(saved.asset_id)
assert retrieved is not None
print("✅ Advisory store working")
```

### 3.8 Rollback Strategy

Delete new files; existing `ai_graphics/` functionality remains intact.

---

## Phase 4: Integration & Validation

### 4.1 Objective

Ensure all new components work together and don't break existing functionality.

### 4.2 Integration Points

| Component A | Component B | Integration |
|-------------|-------------|-------------|
| `RunArtifact` | `RunStore` | Artifact persistence |
| `RunStore` | Database migrations | SQLite storage (future) |
| `AdvisoryAsset` | `hashing.py` | Content hash generation |
| `workflow_sessions` table | `WorkflowSession` model | State persistence |

### 4.3 Implementation Steps

| Step | Action | Est. Time |
|------|--------|-----------|
| 4.1 | Create integration test: RunArtifact → RunStore → file | 30 min |
| 4.2 | Create integration test: Migration → workflow_sessions query | 30 min |
| 4.3 | Create integration test: AdvisoryAsset → hash → store | 30 min |
| 4.4 | Run full test suite, fix any regressions | 60 min |
| 4.5 | Update API documentation (if endpoints changed) | 30 min |

### 4.4 Test Script

```powershell
# test_infrastructure_integration.ps1

Write-Host "=== Phase 1: RunArtifact Imports ===" -ForegroundColor Cyan
python -c "from app.rmos.runs import RunStore, RunArtifact, sha256_json; print('✓ Imports OK')"

Write-Host "`n=== Phase 2: Database Migrations ===" -ForegroundColor Cyan
python -c "from app.db import run_migrations; run_migrations(); print('✓ Migrations OK')"

Write-Host "`n=== Phase 3: Advisory Store ===" -ForegroundColor Cyan
python -c "from app._experimental.ai_graphics.advisory_store import AdvisoryStore; print('✓ Advisory OK')"

Write-Host "`n=== Phase 4: Integration ===" -ForegroundColor Cyan
# Full pytest run
pytest tests/ -v --tb=short

Write-Host "`n=== All Phases Complete ===" -ForegroundColor Green
```

### 4.5 Validation Criteria

- [ ] All imports resolve without errors
- [ ] Migrations apply cleanly on fresh database
- [ ] Existing tests pass (no regressions)
- [ ] New integration tests pass
- [ ] API server starts without warnings

---

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Broken imports block startup** | High | Critical | Phase 1 first; quick rollback available |
| **Migration corrupts existing data** | Low | High | Migrations are additive only (CREATE IF NOT EXISTS) |
| **`.gitignore` change affects other files** | Low | Medium | Anchored pattern is more restrictive |
| **Performance regression from migration check** | Medium | Low | Lazy initialization; skip if no pending |
| **Schema drift between code and migrations** | Medium | Medium | Document schema source of truth |

---

## Decision Log

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| **Custom migration runner** | Zero dependencies, simple SQL | Alembic (overkill for SQLite) |
| **File-based RunStore first** | Match existing pattern in codebase | SQLite (adds Phase 2 dependency) |
| **Anchor `.gitignore` pattern** | Least disruptive fix | Remove pattern entirely (risky) |
| **In-memory AdvisoryStore first** | Faster iteration, can migrate later | SQLite (premature optimization) |

---

## Timeline

```
Week 1, Day 1-2:
├── Phase 1: RunArtifact system (CRITICAL)
└── Phase 2: Database migrations (CRITICAL)

Week 1, Day 3-4:
├── Phase 3: Advisory Assets foundation
└── Phase 4: Integration testing

Week 1, Day 5:
└── Documentation & cleanup
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Import errors** | 0 | `python -c "from app.rmos.runs import *"` |
| **Migration failures** | 0 | `run_migrations()` returns without exception |
| **Test pass rate** | 100% | `pytest` exit code 0 |
| **Startup time regression** | < 200ms | Benchmark before/after |

---

## Appendix: Quick Reference Commands

```bash
# Start API server
cd services/api && uvicorn app.main:app --reload

# Run all tests
cd services/api && pytest tests/ -v

# Check imports
python -c "from app.rmos.runs import RunArtifact, RunStore"
python -c "from app.db import run_migrations"

# Verify database
sqlite3 data/rmos.db ".tables"
sqlite3 data/rmos.db "SELECT * FROM applied_migrations;"
```

---

**Document Version:** 1.0  
**Author:** GitHub Copilot  
**Approval Required:** Technical Lead
