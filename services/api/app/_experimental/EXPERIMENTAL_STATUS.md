# _experimental/ Module Status

> Last updated: 2026-03-12

This directory contains modules that are under active development but not yet ready
for graduation to canonical production paths.

## Module Status Summary

| Module | Status | Used in Production | Graduation Target |
|--------|--------|-------------------|-------------------|
| `ai_core/` | **DELETED** | No | Migrated to `app/rmos/ai/` |
| `ai_cam/` | In Development | Limited | `app/cam/ai/` |
| `analytics/` | Stable, Active | Yes | `app/analytics/` |
| `cnc_production/` | Stable, Active | Yes | `app/cam_core/cnc/` |
| `infra/` | Stub | No | TBD or Delete |

---

## Detailed Status

### `ai_core/` (DELETED - March 2026)

**Status:** Removed

Migration completed:
- Canonical location: `app/rmos/ai/`
- All exports migrated: `generators`, `coercion`, `constraints`, `clients`
- CI guard `ban_experimental_ai_core_imports.py` removed

---

### `ai_cam/` - AI-Assisted CAM Optimization

**Status:** In Development

**Files:**
- `advisor.py` - AI-powered CAM parameter suggestions
- `explain_gcode.py` - G-code explanation service
- `models.py` - Pydantic schemas for AI CAM
- `optimize.py` - Optimization algorithms

**Dependencies:**
- Used by: `ai_cam_router.py` (experimental router)
- Imports from: `app/ai/`, `app/cam/`

**Graduation Criteria:**
- [ ] Integration tests covering advisor recommendations
- [ ] Validation that optimize.py handles edge cases
- [ ] Documentation of explain_gcode outputs
- [ ] Move to `app/cam/ai/` when stable

---

### `analytics/` - Advanced Analytics Services

**Status:** Stable, Production-Used

**Files:**
- `advanced_analytics.py` - Cross-domain aggregate analytics
- `job_analytics.py` - Job execution statistics
- `material_analytics.py` - Material usage tracking
- `pattern_analytics.py` - Pattern frequency analysis

**Dependencies:**
- Used by:
  - `app/routers/analytics_router.py`
  - `app/routers/advanced_analytics_router.py`
- Actively serving production endpoints

**Graduation Criteria:**
- [ ] Create `app/analytics/` directory
- [ ] Move files with updated imports
- [ ] Update dependent routers
- [ ] Add deprecation shim for 1 release cycle

**Risk:** Medium - Active production usage requires careful migration

---

### `cnc_production/` - CNC Production Learning System

**Status:** Stable, Production-Used

**Structure:**
```
cnc_production/
  data/           - JSON configuration files
  feeds_speeds/   - Feed/speed calculation and learning
    core/
      learned_overrides.py - Operator override learning
  joblog/         - Job execution logging
  learn/          - ML-based parameter learning
  routers.py      - Internal routing
```

**Dependencies:**
- Used by:
  - `app/core/store_registry.py` (LearnedOverridesStore)
  - `app/routers/learned_overrides_router.py`
  - `app/cam_core/saw_lab/learning.py`
  - `app/cam_core/saw_lab/operations.py`
  - `app/cam_core/saw_lab/models.py`

**Graduation Criteria:**
- [ ] Create `app/cam_core/cnc/` or merge into `app/cam_core/`
- [ ] Refactor learned_overrides to standalone module
- [ ] Update 5+ dependent files
- [ ] Add deprecation shim for 1 release cycle

**Risk:** High - Deep integration with saw_lab and store_registry

---

### `infra/` - Infrastructure Stubs

**Status:** Stub (Minimal Implementation)

**Files:**
- `__init__.py` - Empty exports
- `live_monitor.py` - WebSocket live monitoring stub

**Dependencies:**
- Imported by `app/infra/live_monitor.py` and `app/infra/__init__.py`

**Decision Needed:**
- Option A: Delete if truly unused (verify no active WebSocket features)
- Option B: Graduate to `app/infra/` if live monitoring is needed
- Option C: Keep as experimental for future development

**Graduation Criteria:**
- [ ] Determine if live_monitor is actively used
- [ ] If yes, complete implementation and graduate
- [ ] If no, delete module

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
| 2026-03-12 | Deleted `ai_core/`, updated ai_search.py imports |
| 2025-12 | Created initial status documentation |
