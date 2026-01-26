# Legacy Code Cleanup Bookmark

**Created:** 2026-01-26
**Purpose:** Bookmark for revisiting legacy router cleanup before standalone product extraction
**Context:** Migrating to standalone products (e.g., blueprint-reader) revealed legacy router contamination

---

## Quick Links - Updated Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| [`docs/LEGACY_CODE_STATUS.md`](./LEGACY_CODE_STATUS.md) | **Source of Truth** - P1/P2/P3 status, consolidation, sunset schedule | ✅ Current |
| [`docs/ROUTER_INVENTORY_AND_DEPRECATION_PLAN.md`](./ROUTER_INVENTORY_AND_DEPRECATION_PLAN.md) | Router inventory, Option C migration status | Current |
| [`ROUTER_MAP.md`](../ROUTER_MAP.md) | 116 routers across 22 waves, canonical vs legacy lanes | Current |
| [`docs/VISION_AI_ARCHITECTURE_CLEANUP.md`](./VISION_AI_ARCHITECTURE_CLEANUP.md) | PR1 orphan code cleanup (vision stack) | ✅ Complete |
| [`docs/handoffs/TECHNICAL_DEBT_HANDOFF_2025-12.md`](./handoffs/TECHNICAL_DEBT_HANDOFF_2025-12.md) | Historical handoff (superseded) | Archived |

---

## Current Technical Debt Status

### Resolved ✅

| Category | Original | Current | Notes |
|----------|----------|---------|-------|
| **P1 Critical Stubs** | 5 | **0** | Feasibility + toolpaths wired to real engines |
| **P2 Incomplete Features** | 5 | **0** | DXF, compare, spacing all implemented |
| **P3 Enhancements** | 3 | **2** | 1 fixed, 2 remain (ML optimization, non-blocking) |
| **Deprecated Routers** | 5 | **0** | Removed via Option C restructuring |

### Outstanding

| Category | Count | Details |
|----------|-------|---------|
| **Consolidation Candidates** | 17 routers → 6 | 4,203 lines, ~2,500 potential savings |
| **Legacy Lane Endpoints** | 17 | UTILITY lane, awaiting OPERATION promotion |
| **Frontend Legacy API Calls** | 8 | In 4 files |
| **PR2 Remaining** | 1 folder | Delete `_experimental/ai_graphics/` after rosette adapter migration |

---

## Sunset Schedule

| Category | Date | Status |
|----------|------|--------|
| Guitar legacy endpoints | **2026-03-01** | Legacy redirects active |
| Temperament legacy | **2026-04-01** | Legacy redirects active |
| Compat mounts | **2026-06-01** | Legacy redirects active |

---

## Consolidation Candidates (17 → 6)

For standalone product extraction, these routers have overlapping functionality:

### Pipeline (5 → 2) — 1,792 lines
- `pipeline_router.py` (1,380)
- `pipeline_presets_router.py` (178)
- `cam_pipeline_preset_run_router.py` (82)
- `cam_pipeline_router.py` (79)
- `pipeline_preset_router.py` (73)

### Calculators (2 → 1) — 829 lines
- `calculators_router.py` (546)
- `ltb_calculator_router.py` (283)

### Posts (3 → 1) — 837 lines
- `post_router.py` (374)
- `cam_post_v155_router.py` (362)
- `posts_router.py` (101)

### Machines (3 → 1) — 392 lines
- `machines_tools_router.py` (200)
- `machine_router.py` (107)
- `machines_router.py` (85)

### Simulation (4 → 1) — 353 lines
- `sim_metrics_router.py` (178)
- `cam_simulate_router.py` (72)
- `gcode_sim_router.py` (65)
- `cam_sim_router.py` (38)

---

## Standalone Product Extraction Checklist

When extracting to standalone products (like blueprint-reader):

### Before Extraction
- [ ] Check if router is in consolidation candidates list
- [ ] Verify router uses canonical patterns (not legacy)
- [ ] Check for `_experimental/` dependencies
- [ ] Verify no hardcoded stubs remain

### Canonical Patterns to Use
```python
# ✅ Canonical: Pattern A (self-prefixing router)
router = APIRouter(prefix="/api/vision", tags=["Vision"])

# ✅ Canonical: Real engine calls
from ..feasibility_scorer import score_design_feasibility
result = score_design_feasibility(design, ctx)

# ❌ Legacy: Hardcoded returns
return {"risk_level": "GREEN"}  # DON'T DO THIS

# ❌ Legacy: _experimental imports
from app._experimental.ai_graphics import ...  # DON'T DO THIS
```

### Key Files to Check
- `services/api/app/main.py` — Is router mounted?
- `services/api/app/ci/deprecation_registry.json` — Sunset dates
- `services/api/app/ci/fence_baseline.json` — Import violations

---

## Blueprint-Reader Discovery

**Issue Found:** During blueprint-reader extraction, discovered:
- `vision_service.py` had `_experimental/ai_graphics/` dependencies
- Legacy `vision_router.py` was orphan code (never mounted in main.py)

**Resolution:** PR1 "Stop the Bleeding" — deleted orphan code, added fence rules

**Lesson:** Always verify routers are actually mounted before extraction.

---

## Commands for Investigation

```bash
# Check if router is mounted in main.py
grep -n "include_router" services/api/app/main.py | grep "<router_name>"

# Check for legacy imports
python -m app.ci.check_boundary_imports --profile toolbox

# Check deprecation registry
cat services/api/app/ci/deprecation_registry.json

# Run fence checks
python -m app.ci.check_all_fences
```

---

## Next Actions (When Revisiting)

1. **Consolidate routers before extraction** — Reduces duplication in standalone products
2. **Complete PR2** — Delete `_experimental/ai_graphics/` after rosette adapter migration
3. **Promote UTILITY → OPERATION** — 17 endpoints need governance wiring
4. **Update frontend legacy API calls** — 8 calls in 4 files

---

*Bookmark created by Claude Code - January 26, 2026*
