# Phase B+C Rehabilitation Bundle — Evaluation Report

**Date:** December 15, 2025  
**Bundle Path:** `phase_bc_for_repo/`  
**Evaluator:** Copilot Agent

---

## Executive Summary

**Finding: The bundle is PARTIALLY REDUNDANT.** Several files from the bundle already exist in the repo with different implementations. The repo already has a functioning Phase B+C implementation, but the bundle contains a more comprehensive version.

### Quick Decision Matrix

| File | Bundle Size | Repo Size | Status | Recommended Action |
|------|-------------|-----------|--------|-------------------|
| `__init__.py` | 4,281 | 762 | DIFFERENT | ⚠️ **MERGE** - Bundle has more exports |
| `ai_search.py` | 12,908 | N/A | **NEW** | ✅ **ADD** - Core search loop |
| `api_ai_routes.py` | 8,082 | N/A | **NEW** | ✅ **ADD** - 5 AI endpoints |
| `schemas_ai.py` | 7,120 | N/A | **NEW** | ✅ **ADD** - Request/response models |
| `constraint_profiles.py` | 12,929 | 10,075 | DIFFERENT | ⚠️ **COMPARE** - Structural changes |
| `profile_history.py` | 13,387 | 8,997 | DIFFERENT | ⚠️ **COMPARE** - Expanded implementation |
| `api_constraint_profiles.py` | 13,069 | 2,560 | DIFFERENT | ⚠️ **COMPARE** - 6 vs 2 endpoints |
| `api_profile_history.py` | 11,150 | 3,575 | DIFFERENT | ⚠️ **COMPARE** - 5 vs 2 endpoints |
| `rmos_constraint_profiles.yaml` | 8,415 | 1,177 | DIFFERENT | ⚠️ **COMPARE** - 14 vs 4 profiles |

---

## Detailed Analysis

### 1. Files That Are Genuinely NEW (Safe to Add)

These files don't exist in the repo and represent new Phase B functionality:

#### `ai_search.py` (12.9 KB) — ✅ ADD
- Core `run_constraint_first_search()` loop
- Integrates with `ai_core/generators.py` and `feasibility_scorer.py`
- Required for `/api/rmos/ai/constraint-search` endpoint

#### `api_ai_routes.py` (8.1 KB) — ✅ ADD
Five new endpoints:
```
POST /api/rmos/ai/constraint-search    # Full search
POST /api/rmos/ai/quick-check          # 5-attempt preview
GET  /api/rmos/ai/status/{code}        # Status descriptions
GET  /api/rmos/ai/workflows            # List workflow modes
GET  /api/rmos/ai/health               # Subsystem health
```

#### `schemas_ai.py` (7.1 KB) — ✅ ADD
Pydantic models:
- `SearchStatus`, `WorkflowMode` (enums)
- `SearchContext`, `SearchBudget`
- `AiSearchRequest`, `AiSearchResponse`
- `AiSearchSummary`, `SearchAttemptSummary`

---

### 2. Files That Need COMPARISON (Different Implementations)

#### `__init__.py` — MERGE REQUIRED

**Repo version (762 bytes):** Minimal exports
```python
from .api_contracts import (RmosContext, RmosFeasibilityResult, ...)
from .api_routes import router as rmos_router
__all__ = ["RmosContext", "RmosFeasibilityResult", ...]
```

**Bundle version (4,281 bytes):** Comprehensive exports including Phase B+C
```python
# Core contracts
from .api_contracts import (...)

# AI Search (Phase B)
from .schemas_ai import (SearchStatus, WorkflowMode, ...)
from .ai_search import (run_constraint_first_search, ...)

# Profiles (Phase C)
from .constraint_profiles import (ConstraintProfile, ProfileStore, ...)
from .profile_history import (ProfileHistoryStore, ...)

# Three routers
from .api_ai_routes import router as ai_router
from .api_constraint_profiles import router as profiles_router
from .api_profile_history import router as history_router
```

**Recommendation:** Merge bundle's exports into repo `__init__.py`, keeping existing exports.

---

#### `constraint_profiles.py` — STRUCTURAL DIFFERENCES

**Repo version (10,075 bytes):**
- `RosetteGeneratorConstraints` dataclass
- `_BASE_PROFILES` dict with 6+ hardcoded profiles
- `get_profile()`, `list_profiles()` functions
- YAML loading but simpler structure

**Bundle version (12,929 bytes):**
- Same `RosetteGeneratorConstraints` dataclass
- `ProfileMetadata` dataclass (tags, author, is_system)
- `ConstraintProfile` wrapper class
- `ProfileStore` class with CRUD operations
- YAML schema includes `version`, `metadata`, `profiles` hierarchy

**Key Difference:** Bundle introduces `ProfileStore` class pattern with metadata; repo uses simpler function-based approach.

---

#### `profile_history.py` — EXPANDED IMPLEMENTATION

**Repo version (8,997 bytes):**
- Basic JSONL journal
- `record_change()`, `get_history()` functions

**Bundle version (13,387 bytes):**
- `ChangeType` enum (CREATE, UPDATE, DELETE, ROLLBACK)
- `ProfileHistoryEntry` dataclass
- `ProfileHistoryStore` class with:
  - `record()`, `get_entries()`, `get_by_id()`
  - `rollback_to()` functionality
  - Entry ID generation

---

#### `api_constraint_profiles.py` — MORE ENDPOINTS

**Repo version (2,560 bytes):** 2 endpoints
```
GET  /profiles
GET  /profiles/{id}
```

**Bundle version (13,069 bytes):** 8 endpoints
```
GET    /profiles              # List all
GET    /profiles/ids          # ID list only
GET    /profiles/tags/{tag}   # Filter by tag
GET    /profiles/{id}         # Get one
POST   /profiles              # Create
PUT    /profiles/{id}         # Update
DELETE /profiles/{id}         # Delete
GET    /profiles/{id}/constraints  # Constraints only
```

---

#### `api_profile_history.py` — MORE ENDPOINTS

**Repo version (3,575 bytes):** 2 endpoints
```
GET  /profiles/history
GET  /profiles/{id}/history
```

**Bundle version (11,150 bytes):** 5 endpoints
```
GET  /profiles/history              # All history
GET  /profiles/history/{entry_id}   # Entry detail
GET  /profiles/{id}/history         # Profile history
POST /profiles/{id}/rollback        # Rollback to entry
POST /profiles/history/prune        # Cleanup old entries
```

---

#### `rmos_constraint_profiles.yaml` — 14 vs 4 PROFILES

**Repo version (1,177 bytes):** 4 profiles
- `default`, `thin_saw`, `proto_machine`, `premium_shell`
- Simple flat structure (no metadata)

**Bundle version (8,415 bytes):** 14 profiles with metadata
- `default`, `beginner`, `first_rosette`
- `classical`, `steel_string`
- `advanced`, `master`
- `herringbone`, `abalone`, `minimalist`
- `exotic_woods`
- `cnc_3018`, `production`
- Each has `name`, `description`, `constraints`, `metadata` (tags, author, is_system)

---

## Questions for You

### Integration Strategy

1. **Which implementation style do you prefer?**
   - **Option A:** Bundle's `ProfileStore` class pattern (OOP, more features)
   - **Option B:** Repo's function-based pattern (simpler, already working)

2. **Should we keep both sets of profiles?**
   - Repo has `thin_saw`, `proto_machine`, `premium_shell` (CAM-focused)
   - Bundle has `beginner`, `classical`, `master`, `herringbone` (luthier-focused)
   - These are **complementary**, not conflicting

3. **Full replacement or surgical merge?**
   - **Full replacement:** Copy all bundle files, overwrite existing
   - **Surgical merge:** Extract only the new functionality (search loop + new endpoints)

### Router Wiring

4. **The bundle adds 3 new routers. Confirm the wiring:**
   ```python
   # In main.py
   from app.rmos.api_ai_routes import router as rmos_ai_router
   from app.rmos.api_constraint_profiles import router as rmos_profiles_router
   from app.rmos.api_profile_history import router as rmos_history_router

   app.include_router(rmos_ai_router, prefix="/api/rmos")
   app.include_router(rmos_profiles_router, prefix="/api/rmos")
   app.include_router(rmos_history_router, prefix="/api/rmos")
   ```
   Note: Repo already has `rmos_router` at `/api/rmos` — confirm no route conflicts.

### Testing

5. **Before integration, should I:**
   - [ ] Compare the two `constraint_profiles.py` files line-by-line
   - [ ] Check if repo endpoints still work
   - [ ] Verify `ai_core/` is properly wired for the search loop

---

## Recommended Integration Path

### Option A: Full Bundle Integration (Recommended)

```powershell
# 1. Backup existing files
Copy-Item "services\api\app\rmos\__init__.py" "services\api\app\rmos\__init__.py.bak"
Copy-Item "services\api\app\rmos\constraint_profiles.py" "services\api\app\rmos\constraint_profiles.py.bak"
# ... etc

# 2. Copy bundle files (overwrites existing)
Copy-Item "phase_bc_for_repo\services\api\app\rmos\*" "services\api\app\rmos\" -Force
Copy-Item "phase_bc_for_repo\services\api\app\config\*" "services\api\app\config\" -Force

# 3. Wire routers in main.py (manual edit)

# 4. Test
uvicorn app.main:app --reload
curl http://localhost:8000/api/rmos/ai/health
curl http://localhost:8000/api/rmos/profiles
```

### Option B: Surgical Merge (More Conservative)

1. Add NEW files only: `ai_search.py`, `api_ai_routes.py`, `schemas_ai.py`
2. Manually merge `__init__.py` exports
3. Keep existing `constraint_profiles.py` and `profile_history.py`
4. Wire only `rmos_ai_router` (skip profiles/history routers)

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Route conflicts with existing `/api/rmos` | Medium | Check all route paths before wiring |
| Breaking existing profile YAML consumers | Low | Repo YAML has simpler schema; bundle's is superset |
| Import errors in `__init__.py` | Medium | Test imports after merge |
| `ai_search.py` depends on `ai_core/` | Medium | Verify `ai_core/generators.py` exports match |

---

## Files NOT in Bundle (Already in Repo)

The bundle correctly excludes files you already have:
- `logging_ai.py` ✅
- `schemas_logs_ai.py` ✅
- `ai_policy.py` ✅
- `api_contracts.py` ✅
- `feasibility_scorer.py` ✅
- `api_routes.py` ✅
- `feasibility_fusion.py` ✅
- `feasibility_router.py` ✅

---

## Summary

| Phase | Status | Files in Bundle |
|-------|--------|-----------------|
| Phase B (AI Search) | 3 NEW files | `schemas_ai.py`, `ai_search.py`, `api_ai_routes.py` |
| Phase C (Profiles) | 4 DIFFERENT files | `constraint_profiles.py`, `profile_history.py`, `api_*.py` |
| Config | 1 DIFFERENT file | `rmos_constraint_profiles.yaml` (14 vs 4 profiles) |
| Docs | 2 files | `INTEGRATION_INSTRUCTIONS.md`, `AI_SYSTEM_REHABILITATION_PLAN_v2.md` |

**Bottom Line:** The bundle is a **superset** of what's in the repo. Integration will add AI search capabilities and expand profile management from 4 → 14 profiles with full CRUD.

---

Awaiting your decision on integration strategy.
