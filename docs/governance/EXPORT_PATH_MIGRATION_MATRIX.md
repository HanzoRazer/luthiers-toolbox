# Export Path Migration Matrix

**Date:** 2026-05-14  
**Sprint:** MRP-4B  
**Status:** ACTIVE

---

## Purpose

Inventory of all DXF/SVG/G-code export paths with classification and migration status toward the governed translator architecture (MRP-3A/4A).

---

## Classification Legend

| Status | Meaning |
|--------|---------|
| **GOVERNED** | Uses translator abstraction layer (MRP-4A) |
| **COMPLIANT** | Uses dxf_writer/dxf_compat, migration-ready |
| **LEGACY** | Uses dxf_helpers or direct ezdxf.new() |
| **EXEMPT** | Authorized legacy exemption (see policy) |

---

## Export Path Inventory

### Category A: Governed Translators (MRP-4A Target)

| Module | Endpoint | Target | Status | Notes |
|--------|----------|--------|--------|-------|
| `app.routers.export.translate_router` | `POST /api/translate/{target}` | DXF/SVG | **GOVERNED** | MRP-4A canonical endpoint |
| `app.routers.export.dxf_translate_router` | `POST /api/export/translate/dxf` | DXF | **GOVERNED** | MRP-3B (deprecated, use /api/translate) |
| `app.routers.export.body_export_router` | `POST /api/export/body` | Export Object | **GOVERNED** | MRP-2B BOE endpoint |

### Category B: Compliant (dxf_writer/dxf_compat)

| Module | Endpoint/Function | Target | Status | Migration Priority |
|--------|-------------------|--------|--------|-------------------|
| `app.cam.dxf_writer` | `DxfWriter` class | DXF | **COMPLIANT** | N/A (canonical writer) |
| `app.util.dxf_compat` | `create_document()` | DXF | **COMPLIANT** | N/A (compat layer) |
| `app.cam.translators.dxf.body_outline_translator` | `translate()` | DXF | **COMPLIANT** | Already governed |
| `app.calculators.inlay_calc` | `export_inlay_to_dxf()` | DXF | **COMPLIANT** | P2 |
| `app.cam.archtop.archtop_contour_generator` | contour generation | DXF | **COMPLIANT** | P2 |
| `app.cam.archtop.archtop_surface_tools` | surface export | DXF | **COMPLIANT** | P2 |
| `app.cam.archtop_bridge_generator` | bridge export | DXF | **COMPLIANT** | P2 |
| `app.cam.archtop_saddle_generator` | saddle export | DXF | **COMPLIANT** | P2 |
| `app.cam.dxf_advanced_validation` | validation | DXF | **COMPLIANT** | N/A (validation only) |
| `app.cam.dxf_consolidator` | consolidation | DXF | **RETIRED** | dead, superseded by `layer_consolidator` (BACKLOG item 9) |
| `app.cam.layer_consolidator` | layer ops | DXF | **COMPLIANT** | N/A (utility) |
| `app.cam.unified_dxf_cleaner` | cleanup | DXF | **COMPLIANT** | N/A (utility) |
| `app.routers.dxf_preflight_router` | preflight check | DXF | **COMPLIANT** | N/A (validation) |
| `app.routers.export.curve_export_router` | `POST /api/export/curve-dxf` | DXF | **COMPLIANT** | P3 |
| `app.routers.headstock.dxf_export` | `POST /api/export/headstock-dxf` | DXF | **COMPLIANT** | P2 |
| `app.routers.neck.export` | neck export | DXF | **COMPLIANT** | P3 |
| `app.routers.neck.headstock_transition_export` | transition export | DXF | **COMPLIANT** | P3 |
| `app.routers.neck.neck_profile_export` | profile export | DXF | **COMPLIANT** | P3 |
| `app.routers.blueprint_cam.contour_reconstruction` | contour export | DXF | **COMPLIANT** | P2 |
| `app.routers.blueprint_cam.dxf_preprocessor` | preprocessing | DXF | **COMPLIANT** | N/A (preprocessing) |
| `app.instrument_geometry.neck.fretboard_ecosphere` | fretboard export | DXF | **COMPLIANT** | P3 |

### Category C: Legacy (Direct ezdxf.new())

| Module | Function | Target | Status | Migration Priority | Exemption? |
|--------|----------|--------|--------|-------------------|------------|
| `app.instrument_geometry.body.smart_guitar_dxf` | `generate_smart_guitar_dxf()` | DXF | **LEGACY** | P1 | No |
| `app.routers.instruments.guitar.smart_guitar_dxf_router` | `POST /api/guitar/smart-guitar/dxf` | DXF | **LEGACY** | P1 | No |
| `app.instrument_geometry.bridge.archtop_floating_bridge` | bridge DXF | DXF | **LEGACY** | P1 | No |
| `app.instrument_geometry.soundhole.spiral_geometry` | spiral DXF | DXF | **LEGACY** | P1 | No |
| `app.exports.dxf_helpers` | ASCII R12 fallback | DXF | **LEGACY** | P2 | EXEMPT |
| `app.routers.legacy_dxf_exports_router` | `/exports/polyline_dxf`, `/exports/biarc_dxf` | DXF | **LEGACY** | P3 | EXEMPT |
| `scripts.generate_smart_guitar_v3_dxf` | CLI script | DXF | **LEGACY** | P3 | EXEMPT |
| `app.toolpath.dxf_io_legacy` | legacy I/O | DXF | **LEGACY** | P4 | EXEMPT |
| `app.instrument_geometry.neck_taper.dxf_exporter` | taper export | DXF | **LEGACY** | P3 | No |

### Category D: Blueprint/Vectorizer (Special Case)

| Module | Function | Target | Status | Migration Priority | Notes |
|--------|----------|--------|--------|-------------------|-------|
| `app.routers.blueprint.edge_to_dxf_router` | vectorizer export | DXF | **LEGACY** | P1 | Three-loop architecture |
| `app.routers.blueprint.phase2_router` | phase2 export | DXF | **LEGACY** | P1 | Vectorizer pipeline |
| `app.routers.blueprint.phase3_router` | phase3 export | DXF | **LEGACY** | P1 | Vectorizer pipeline |
| `app.services.blueprint_extract` | extraction | DXF | **LEGACY** | P1 | Core vectorizer |
| `app.services.text_reinsertion` | text overlay | DXF | **LEGACY** | P2 | Post-processing |

### Category E: G-code Export (Manufacturing Lane)

| Module | Endpoint | Target | Status | Notes |
|--------|----------|--------|--------|-------|
| `app.routers.geometry.export_router` | `POST /api/geometry/export_gcode` | G-code | **GOVERNED** | RMOS artifact |
| `app.routers.geometry.export_router` | `POST /api/geometry/export_gcode_governed` | G-code | **GOVERNED** | Simulation gate |
| `app.routers.adaptive.gcode_router` | adaptive G-code | G-code | **COMPLIANT** | Safety-critical |
| `app.routers.adaptive.batch_router` | batch export | ZIP/G-code | **COMPLIANT** | Multi-file |
| `app.routers.cam.guitar.body_gcode_router` | body G-code | G-code | **COMPLIANT** | Model-specific |
| `app.routers.cam.guitar.acoustic_cam_router` | acoustic G-code | G-code | **COMPLIANT** | Acoustic models |

### Category F: Other Formats

| Module | Endpoint | Target | Status | Notes |
|--------|----------|--------|--------|-------|
| `app.cam.translators.svg.translator` | SVG export | SVG | **GOVERNED** | MRP-4A |
| `app.routers.export.rosette_pdf_router` | rosette PDF | PDF | **COMPLIANT** | Documentation |
| `app.routers.geometry.bundle_router` | ZIP bundle | ZIP | **COMPLIANT** | Multi-format |
| `app.routers.blueprint.phase1_router` | SVG export | SVG | **COMPLIANT** | Vectorizer output |

---

## Migration Priority Definitions

| Priority | Definition | Target Timeline |
|----------|------------|-----------------|
| **P1** | Direct ezdxf.new() in production endpoints | MRP-5A |
| **P2** | Compliant modules ready for translator upgrade | MRP-5B |
| **P3** | Lower-traffic or utility endpoints | MRP-6A |
| **P4** | Legacy utilities, scripts, archived code | As-needed |

---

## Statistics

| Category | Count |
|----------|-------|
| Governed (MRP-4A) | 4 |
| Compliant (dxf_writer/compat) | 20 |
| Legacy (needs migration) | 14 |
| Exempt (authorized legacy) | 4 |
| **Total Export Paths** | **42** |

---

## References

- `docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md` — exemption criteria
- `docs/governance/TRANSLATOR_ONBOARDING_RULES.md` — adding new translators
- `docs/handoffs/MRP_4A_MULTI_TARGET_TRANSLATOR_HANDOFF.md` — translator architecture
