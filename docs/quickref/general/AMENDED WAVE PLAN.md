## AMENDED WAVE PLAN

### Wave 0 — .gitignore fix (DONE)
- Commit: `.gitignore` anchoring

### Wave 0.5 — Modified Files Only (NEW)
- Commit separately: the 5 modified files
- `instrument_geometry/body/__init__.py`
- `instrument_geometry/body/outlines.py`
- `main.py`
- `rmos/__init__.py`
- `routers/rmos_patterns_router.py`

### Wave 1 — Core Spine
- `calculators/` (CRITICAL)
- `data/` (CRITICAL)
- `tools/` (CRITICAL)
- `core/`
- `util/`
- `config/`
- `schemas/`
- `stores/`
- `services/`

### Wave 2 — RMOS Complete
- `rmos/api/`
- `rmos/models/`
- `rmos/services/`

### Wave 3 — CAD/CAM
- `cad/`
- `cam_core/`
- `toolpath/`
- `art_studio/`
- `generators/`

### Wave 4 — Active Features
- `websocket/`
- `workflow/`
- `pipelines/`
- `tests/` → move to `services/api/tests/`

### Wave 5 — Isolate to _experimental/
- `ai_cam/`
- `ai_core/`
- `ai_graphics/`
- `analytics/`
- `cnc_production/`
- `infra/`

### Wave 6 — Archive/Delete
- `app/` — inspect first, likely delete
- `ltb_calculators/` — archive if `calculators/` is canonical
- `reports/` — if outputs only, add to .gitignore