# DXF Policy Compliance Audit

**Date:** 2026-04-29  
**Trigger:** Post-PR-10 repo-wide audit  
**Policy:** CLAUDE.md requires all DXF generators route through `dxf_compat`

---

## Executive Summary

Repo-wide grep found **35 files** with direct `ezdxf.new()` calls that bypass the `dxf_compat` wrapper. This violates the DXF policy established in CLAUDE.md.

| Location | Count | Criticality |
|----------|-------|-------------|
| services/api/app/ | 21 | Production code |
| services/photo-vectorizer/ | 14 | Standalone tools |

---

## Version Distribution

The violations use three different DXF versions, suggesting legitimate version needs per file:

| Version | Use Case | Files |
|---------|----------|-------|
| R2010 | CAM surfaces, LWPOLYLINE needed | archtop CAM, headstock, neck profile |
| R2000 | Middle ground | blueprint_cam, smart_guitar |
| R12 | Consumer-facing, legacy compat | inlay, cleaner, helpers |

**Implication:** Future cleanup requires version-per-file decision, not uniform refactor.

---

## Full File List

### services/api/app/ (21 files)

| File | Line | Version |
|------|------|---------|
| art_studio/services/generators/inlay_export.py | 79 | R12 |
| calculators/inlay_calc.py | 390 | R12 |
| cam/archtop/archtop_contour_generator.py | 133, 169 | R2010 |
| cam/archtop/archtop_surface_tools.py | 143 | R2010 |
| cam/archtop_bridge_generator.py | 54 | R2010 |
| cam/archtop_saddle_generator.py | 60 | R2010 |
| cam/dxf_advanced_validation.py | 574, 602 | R2010 |
| cam/dxf_consolidator.py | 241 | R2000 |
| cam/layer_consolidator.py | 177 | R2000 |
| cam/unified_dxf_cleaner.py | 212, 354 | R12 |
| exports/dxf_helpers.py | 145 | R12 |
| instrument_geometry/body/smart_guitar_dxf.py | 297 | R2000 |
| routers/blueprint_cam/contour_reconstruction.py | 372, 451 | R2000 |
| routers/blueprint_cam/dxf_preprocessor.py | 131 | R2000 |
| routers/dxf_preflight_router.py | 283 | R12 |
| routers/export/curve_export_router.py | 54 | R2010 |
| routers/headstock/dxf_export.py | 272 | R2010 |
| routers/instruments/guitar/smart_guitar_dxf_router.py | 77 | R2010 |
| routers/neck/export.py | 35 | R12 |
| routers/neck/headstock_transition_export.py | 145 | R2010 |
| routers/neck/neck_profile_export.py | 246 | R2010 |

### services/photo-vectorizer/ (14 files)

| File | Line | Version |
|------|------|---------|
| ai_render_extractor.py | 327 | R12 |
| cognitive_extraction_engine.py | 1464 | R12 |
| cognitive_extractor.py | 1450 | R12 |
| edge_to_dxf.py | 788, 1684, 1920, 2075, 2573 | R12 |
| extract_body_grid.py | 173 | R12 |
| extract_body_grid_v2.py | 185 | R12 |
| extract_body_grid_v3.py | 178 | R12 |
| extract_body_grid_v4.py | 179 | R12 |
| extract_body_grid_v5.py | 147 | R12 |
| generate_carlos_jumbo_dxf.py | 144 | R12 |
| generate_carlos_jumbo_dxf_enhanced.py | 282, 304 | R12 |
| light_line_body_extractor.py | 525 | R12 |
| march_pipeline_restore.py | 393, 492 | R12 |
| multi_view_reconstructor.py | 786 | R12 |
| photo_silhouette_extractor.py | 357 | R12 |
| photo_vectorizer_v2.py | 3420 | varies |

---

## Excluded from Count

- `.venv/` — third-party library code
- `dxf_compat.py` — the wrapper itself (legitimate use)
- `dxf_writer.py` — comment/docstring reference only
- `test_*.py` — test files

---

## Resolution Options

**A.** Refactor in batches by priority (production routers first, scripts last)

**B.** Tighten CI to reject new `ezdxf.new()` additions, accept existing as debt

**C.** Some endpoints may have legitimate need for non-default versions — refactor with version awareness

**Recommendation:** B + A in batches. CI check stops the bleed; backfill when bandwidth allows.

---

## Grep Command Used

```bash
grep -rn "ezdxf.new(" services/ --include="*.py" | grep -v test_ | grep -v __pycache__
```
