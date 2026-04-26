# Generator System Status Assessment

**Date:** 2026-04-25
**Purpose:** Ground truth inventory before DXF reconciliation
**Status:** AUDIT COMPLETE — no changes made

---

## Recent Commits (Last 30 Days)

| Date | Hash | Summary |
|------|------|---------|
| 2026-04-17 | c12fa44b | fix(ibg): reject centerline noise in waist landmark extraction |
| 2026-04-17 | f7793b6f | feat(ibg): Sprint 5 — replace hardcoded sagitta with circle fitting |
| 2026-04-15 | f59e3c72 | feat(ibg): Sprint 4 — move IBG to production |
| 2026-04-08 | ce795cf2 | fix(archtop): use allsegs for matplotlib >= 3.8 compatibility |
| 2026-04-06 | db2b8ba1 | feat(archtop): add archtop API router |
| 2026-03-28 | 25c46e71 | feat(generators): add unified BodyGenerator dispatcher (GEN-1) |

---

## Generator Inventory

### services/api/app/generators/ (4,672 lines total)

| File | Lines | Output Type | Status | DXF Interface |
|------|-------|-------------|--------|---------------|
| body_generator.py | 245 | Dispatcher | ACTIVE | N/A (routes only) |
| acoustic_body_generator.py | 732 | Outline + G-code | ACTIVE | No DXF output |
| stratocaster_body_generator.py | 632 | Parametric G-code | ACTIVE | No DXF output |
| bezier_body.py | 595 | DXF outline | ACTIVE | **DIRECT ezdxf.new("R2010")** |
| neck_headstock_generator.py | 397 | Neck outline | ACTIVE | No DXF output |
| neck_headstock_geometry.py | 481 | Geometry math | ACTIVE | N/A |
| electric_body_generator.py | 257 | Body outline | ACTIVE | No DXF output |
| lespaul_body_generator.py | 130 | DXF-based G-code | ACTIVE | Reads DXF only |
| lespaul_dxf_reader.py | 193 | DXF parsing | ACTIVE | Reads only |
| lespaul_config.py | 206 | Config | ACTIVE | N/A |
| stratocaster_config.py | 282 | Config | ACTIVE | N/A |
| neck_headstock_presets.py | 222 | Presets | ACTIVE | N/A |
| cam_utils.py | 81 | Utilities | ACTIVE | N/A |
| neck_headstock_config.py | 32 | Config | ACTIVE | N/A |
| neck_headstock_enums.py | 28 | Enums | ACTIVE | N/A |

**Known Issues:** None (no TODO/FIXME comments found)

---

### services/api/app/instrument_geometry/body/ibg/ (3,798 lines total)

| File | Lines | Output Type | Status | DXF Interface |
|------|-------|-------------|--------|---------------|
| arc_reconstructor.py | 1,611 | Arc geometry + DXF | ACTIVE | **DIRECT ezdxf.new("R12")** ×3 |
| body_contour_solver.py | 913 | Contour solving + DXF | ACTIVE | **DIRECT ezdxf.new("R12")** |
| reference_outline_bridge.py | 484 | Outline bridge | ACTIVE | No DXF output |
| instrument_body_generator.py | 432 | Body generation | ACTIVE | No DXF output |
| constraint_extractor.py | 304 | Landmark extraction | ACTIVE | N/A |

**Known Issues:**
- `reference_outline_bridge.py:326` — TODO: auto-detect spec by comparing extracted body width

---

### services/api/app/art_studio/services/generators/ (3,200 lines total)

| File | Lines | Output Type | Status | DXF Interface |
|------|-------|-------------|--------|---------------|
| inlay_patterns.py | 625 | Pattern geometry | ACTIVE | No DXF output |
| inlay_geometry_svg.py | 478 | SVG generation | ACTIVE | N/A |
| inlay_import.py | 414 | DXF/SVG/CSV import | ACTIVE | Reads only |
| inlay_primitives.py | 321 | Geometric primitives | ACTIVE | N/A |
| inlay_geometry_rope.py | 191 | Rope patterns | ACTIVE | N/A |
| inlay_geometry_transforms.py | 181 | Transforms | ACTIVE | N/A |
| inlay_geometry_bom.py | 170 | BOM generation | ACTIVE | N/A |
| mosaic_band.py | 128 | Mosaic patterns | ACTIVE | N/A |
| inlay_geometry.py | 128 | Geometry facade | ACTIVE | N/A |
| inlay_geometry_bezier.py | 124 | Bezier curves | ACTIVE | N/A |
| inlay_export.py | 116 | DXF export | ACTIVE | **DIRECT ezdxf.new("R12")** |
| basic_rings.py | 91 | Ring patterns | ACTIVE | N/A |
| registry.py | 88 | Pattern registry | ACTIVE | N/A |
| inlay_geometry_core.py | 58 | Core geometry | ACTIVE | N/A |
| inlay_engines.py | 46 | Engine facade | ACTIVE | N/A |

**Known Issues:** None

---

### services/api/app/art_studio/services/generators/engines/ (1,340 lines total)

| File | Lines | Output Type | Status |
|------|-------|-------------|--------|
| path_engine.py | 409 | Path-following inlay | ACTIVE |
| radial_engine.py | 335 | Radial inlay | ACTIVE |
| grid_engine.py | 294 | Grid inlay | ACTIVE |
| medallion_engine.py | 249 | Medallion inlay | ACTIVE |

**Known Issues:** None

---

### services/api/app/cam/archtop/ (2,004 lines total)

| File | Lines | Output Type | Status | DXF Interface |
|------|-------|-------------|--------|---------------|
| archtop_modal_analysis.py | 536 | Modal analysis | ACTIVE | N/A |
| archtop_stiffness_map.py | 464 | Stiffness mapping | ACTIVE | N/A |
| archtop_surface_tools.py | 368 | Surface tooling | ACTIVE | **DIRECT ezdxf.new("R2010")** |
| archtop_contour_generator.py | 204 | Contour DXF | ACTIVE | **dxf_writer.py** ✅ |
| archtop_pipeline.py | 92 | Pipeline orchestrator | ACTIVE | N/A |

### services/api/app/cam/ (archtop generators at root)

| File | Lines | Output Type | Status | DXF Interface |
|------|-------|-------------|--------|---------------|
| archtop_bridge_generator.py | 160 | Bridge DXF | ACTIVE | **dxf_writer.py** ✅ |
| archtop_saddle_generator.py | 180 | Saddle DXF | ACTIVE | **dxf_writer.py** ✅ |

**Known Issues:** None

---

## DXF Interface Compliance (Sprint 3 Architecture Rule)

### Migrated to dxf_writer.py ✅

Per Sprint 3 audit (12/12 production generators):
- archtop_contour_generator.py
- archtop_bridge_generator.py
- archtop_saddle_generator.py
- soundhole/spiral_geometry.py
- bridge/archtop_floating_bridge.py
- headstock/dxf_export.py
- blueprint_cam/dxf_preprocessor.py
- blueprint_cam/contour_reconstruction.py
- export/curve_export_router.py
- body/smart_guitar_dxf.py
- neck/headstock_transition_export.py
- neck/neck_profile_export.py

### Still Using Direct ezdxf.new() — NOT MIGRATED

| File | Version | Location |
|------|---------|----------|
| bezier_body.py | R2010 | generators/ |
| arc_reconstructor.py | R12 (×3) | ibg/ |
| body_contour_solver.py | R12 | ibg/ |
| inlay_export.py | R12 | art_studio/ |
| archtop_surface_tools.py | R2010 | cam/archtop/ |
| dxf_consolidator.py | R2000 | cam/ |
| dxf_advanced_validation.py | R2010 (×2) | cam/ |
| layer_consolidator.py | R2000 | cam/ |
| layered_dxf_writer.py | R12 | services/ |
| neck/export.py | R12 | routers/neck/ |
| dxf_preflight_router.py | R12 | routers/ |
| smart_guitar_dxf_router.py | R2010 | routers/instruments/ |
| inlay_calc.py | R12 | calculators/ |

**Total:** 13 files still using direct ezdxf calls

---

## Sprint Closeout Check

### IBG Sprints
- **Sprint 4:** feat(ibg): Sprint 4 — move IBG to production (f59e3c72, 2026-04-15)
- **Sprint 5:** feat(ibg): Sprint 5 — replace hardcoded sagitta with circle fitting (f7793b6f, 2026-04-17)

No formal closeout document found for IBG sprints. Commits exist but no docs/audit entry.

### Generator Consolidation
- **GEN-1:** BodyGenerator dispatcher landed (25c46e71, 2026-03-28)
- **GEN-5:** GENERATOR_REMEDIATION_PLAN.md exists — focused on model description consolidation, NOT DXF output

### Sprint 3 DXF Consolidation
- Closeout: docs/audit/sprints_audit_2026-04-23.md
- Status: 12/12 production generators migrated to dxf_writer.py
- **Gap:** 13 additional files using direct ezdxf.new() were not in Sprint 3 scope

---

## Known Broken Outputs

No explicitly broken outputs identified in:
- Issue tracker (not present)
- TODO/FIXME comments (only 1 minor TODO in reference_outline_bridge.py)
- Recent commit messages

---

## Test Coverage

| Test File | Coverage Target |
|-----------|-----------------|
| test_body_generator_router.py | body_generator.py dispatch |
| test_bezier_body_generator.py | bezier_body.py |
| test_acoustic_body_generator_smoke.py | acoustic_body_generator.py |

**Gap:** No dedicated tests for IBG, archtop generators, or inlay generators visible.

---

## Recommendations for DXF Reconciliation

### High Priority (Production Path)
1. **bezier_body.py** — Uses R2010, production body generator
2. **arc_reconstructor.py** — Uses R12 ×3, IBG core component
3. **body_contour_solver.py** — Uses R12, IBG core component

### Medium Priority (Active Features)
4. **inlay_export.py** — Uses R12, inlay system export
5. **archtop_surface_tools.py** — Uses R2010, archtop CAM
6. **smart_guitar_dxf_router.py** — Uses R2010, Smart Guitar feature

### Lower Priority (Utilities/Validation)
7. **dxf_consolidator.py** — Uses R2000, utility
8. **dxf_advanced_validation.py** — Uses R2010, validation tooling
9. **layer_consolidator.py** — Uses R2000, utility
10. **layered_dxf_writer.py** — Uses R12, may be superseded
11. **neck/export.py** — Uses R12, neck export
12. **dxf_preflight_router.py** — Uses R12, preflight
13. **inlay_calc.py** — Uses R12, calculator

---

## Summary

| Category | Count |
|----------|-------|
| Generator files inventoried | 47 |
| Lines of generator code | ~15,000 |
| Migrated to dxf_writer.py | 12 (Sprint 3) |
| Still using direct ezdxf | 13 |
| Known broken outputs | 0 |
| TODO/FIXME items | 1 |
| Missing sprint closeouts | IBG Sprint 4, Sprint 5 |

**Conclusion:** Generator system is functional but DXF output is fragmented. Sprint 3 migrated 12 files but 13 remain using direct ezdxf calls. No known broken outputs but architectural debt exists.
