# _experimental/ Module Status

> Last updated: 2026-03-19
> **STATUS: FULLY CLEARED** — All modules graduated or deleted.

This directory is now empty except for this status file.
All experimental modules have been graduated to production paths or deleted.

## Module Status Summary

| Module | Status | Used in Production | Graduation Target |
|--------|--------|-------------------|-------------------|
| `ai_core/` | **DELETED** | No | Migrated to `app/rmos/ai/` |
| `ai_cam/` | **DELETED** | No | Was unused - permanently deleted |
| `ai_cam_router.py` | **DELETED** | No | Was unused - permanently deleted |
| `joblog_router.py` | **DELETED** | No | Was unused - permanently deleted |
| `analytics/` | **GRADUATED** | Yes | Graduated to `app/analytics/` |
| `cnc_production/` | **GRADUATED** | Yes | Graduated to `app/cam_core/` |
| `infra/` | **GRADUATED** | Yes | Migrated to `app/infra/` |

---

## Detailed Status

### `ai_core/` (DELETED - March 2026)

**Status:** Removed

Migration completed:
- Canonical location: `app/rmos/ai/`
- All exports migrated: `generators`, `coercion`, `constraints`, `clients`
- CI guard `ban_experimental_ai_core_imports.py` removed

---

### `ai_cam/` (DELETED - March 2026)

**Status:** Permanently deleted

**Reason:** Audit found zero imports in codebase. Was archived on 2026-03-15, then
permanently deleted on 2026-03-19 after confirming no restoration requests.

The module contained (now gone):
- `advisor.py` - AI-powered CAM parameter suggestions
- `explain_gcode.py` - G-code explanation service
- `models.py` - Pydantic schemas for AI CAM
- `optimize.py` - Optimization algorithms

---

### `ai_cam_router.py` (DELETED - March 2026)

**Status:** Permanently deleted

**Reason:** Not registered in main.py, zero imports found.

---

### `joblog_router.py` (DELETED - March 2026)

**Status:** Permanently deleted

**Reason:** Not registered in main.py, zero imports found.

---

### `analytics/` (GRADUATED - March 2026)

**Status:** Graduated to `app/analytics/`

Migration completed (CLEANUP-001; tracked in `CHANGELOG.md` [Unreleased]):
- `advanced_analytics.py` moved to `app/analytics/advanced_analytics.py`
- `job_analytics.py` moved to `app/analytics/job_analytics.py`
- `material_analytics.py` moved to `app/analytics/material_analytics.py`
- `pattern_analytics.py` moved to `app/analytics/pattern_analytics.py`

4 consumer routers updated:
- `app/routers/analytics_jobs_router.py`
- `app/routers/analytics_advanced_router.py`
- `app/routers/analytics_materials_router.py`
- `app/routers/analytics_patterns_router.py`

Experimental `analytics/` directory deleted

---

### `cnc_production/` (GRADUATED - March 2026)

**Status:** Graduated to `app/cam_core/`

Migration completed:
- `joblog/` moved to `app/cam_core/joblog/`
- `learn/` moved to `app/cam_core/learn/`
- `data/` moved to `app/cam_core/data/`
- `feeds_speeds/core/learned_overrides.py` moved to `app/cam_core/feeds_speeds/learned_overrides.py`
- `feeds_speeds/core/learned_overrides_models.py` moved to `app/cam_core/feeds_speeds/learned_overrides_models.py`

6 consumer files updated:
- `app/core/store_registry.py`
- `app/routers/learned_overrides_router.py`
- `app/cam_core/api/saw_lab_router.py`
- `app/cam_core/saw_lab/learning.py`
- `app/cam_core/saw_lab/operations.py`
- `app/cam_core/saw_lab/models.py`

Experimental `cnc_production/` directory deleted

---

### `infra/` (GRADUATED - March 2026)

**Status:** Graduated to `app/infra/`

Migration completed:
- `live_monitor.py` moved to `app/infra/live_monitor.py`
- `app/infra/__init__.py` updated to import locally
- Experimental `infra/` directory deleted

---

## Migration Process

When graduating a module:

1. **Create canonical directory** (e.g., `app/analytics/`)
2. **Move files** with `git mv` to preserve history
3. **Update imports** in all dependent files
4. **Add deprecation shim** in `_experimental/` that re-exports from canonical
5. **Document migration** in this file
6. **After 1 release cycle**, delete the shim

Example deprecation shim:
```python
# _experimental/analytics/__init__.py
"""DEPRECATED: Import from app.analytics instead."""
import warnings
warnings.warn("Import from app.analytics instead", DeprecationWarning)
from app.analytics import *  # noqa
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-03-19 | **FULLY CLEARED** — all modules graduated or deleted |
| 2026-03-19 | Graduated `analytics/` to `app/analytics/` (CLEANUP-001, cf025a1e) |
| 2026-03-19 | Graduated `cnc_production/` to `app/cam_core/` (CLEANUP-002, f090ec73) |
| 2026-03-19 | Permanently deleted `__ARCHIVED__/` directory (ai_cam/, ai_cam_router.py, joblog_router.py) |
| 2026-03-19 | Removed stale manifest entries from system_manifest.py |
| 2026-03-15 | Archived `ai_cam/`, `ai_cam_router.py`, `joblog_router.py` (no imports found) |
| 2026-03-15 | Graduated `infra/` to `app/infra/` |
| 2026-03-12 | Deleted `ai_core/`, updated ai_search.py imports |
| 2025-12 | Created initial status documentation |
