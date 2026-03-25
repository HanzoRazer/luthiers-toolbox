# DECOMPOSITION RECOVERY — Annotated Executive Summary

> **Date:** 2026-03-07
> **Scope:** All substantive files lost during repository decomposition (Dec 2025 – Feb 2026)
> **Recovered:** 88 files / 18,927 lines / 628 KB across 10 categories
> **Action Required:** Engineering triage — classify each file as RESTORE, MINE, or DISCARD

---

## Situation

Between December 2025 and February 2026, the luthiers-toolbox repository underwent four waves of aggressive cleanup aimed at reducing the endpoint count from ~1,060 toward a target of <300 and removing dead code. The cleanup deleted **~64,800 lines across ~280 files** via:

| Wave | Commit | Action | Scale |
|------|--------|--------|-------|
| 1. Archive | `046a2aca` | Moved 9 routers to `_archive/` | 0 lines (rename only) |
| 2. Delete archives | `cc144aab` | Deleted the archived routers | 2,275 lines / 12 files |
| 3. Cascade cleanup | `19a4d33e` | "Remove 65 orphaned files" | 11,683 lines / 65 files |
| 4. __REFERENCE__ purge | `e1929a57` | Bulk-deleted `__REFERENCE__/` directory | 50,854 lines / 196 files |

**Precedent for error:** Wave 27.1 (`d3a0b92b`) had to restore 9 incorrectly deleted modules (1,407 lines), proving the cleanup process was scope-aggressive. The modules restored included `cam_dxf_adaptive_router.py`, `cam_relief_router.py`, `SawLabQueue`, CNC presets, WebSocket monitor, and AI prompt templates.

An additional **27 phantom references** exist in the registry and spec files — paths that claim files exist but the files were either never created or were deleted without updating the references.

---

## What This Folder Contains

All 88 files have been extracted from git history using `git show` and organized into 10 functional categories. Every `.py` file parses cleanly (2 reference archive files excepted — encoding artifacts). The import-check script (`check_imports.py`) can be run from `services/api/` to see which dependencies each file still satisfies.

```
__RECOVERED__/
├── check_imports.py                    # Dependency checker (run from services/api/)
├── README.md                           # This document
├── A_cam_core/                         # Core CAM algorithms (4 files, 1,567 lines)
├── B_instrument_data/                  # Measured instrument specs (2 files, 352 lines)
├── C_archtop_pipeline/                 # Archtop carving system (2 files, 1,048 lines)
├── D_guitar_cam_routers/               # Model-specific CAM routers (7 files, 1,440 lines)
├── E_rosette_fabrication/              # Rosette manufacturing (5 files, 1,747 lines)
├── F_validation_tooling/               # DXF/CAM validation (4 files, 1,024 lines)
├── G_rmos_orchestration/               # RMOS APIs and adapters (10 files, 2,708 lines)
├── H_services_utilities/               # Support services & hooks (16 files, 2,714 lines)
├── I_experimental/                     # Art studio, mesh, runs_v2, migrations (25 files, 2,734 lines)
└── J_reference_archive_samples/        # Best of the __REFERENCE__ purge (11 files, 4,593 lines)
```

---

## Category Assessments

### A. CAM Core — **RECOVER or MINE** — 4 files, 1,567 lines

These are production-grade CAM algorithms. All parse cleanly. Most dependencies still exist in the codebase.

| File | Lines | What It Does | Deps Satisfied | Triage |
|------|-------|-------------|----------------|--------|
| **cam_post_v155_router.py** | 521 | Full G-code post-processor: GRBL/Mach3/Haas/Marlin presets, tangent/arc lead-in/out, G41/42 CRC, corner fillet smoothing via `biarc_math`, axis modal optimization | 7/8 (needs `cam.biarc_math`) | **RECOVER** — `biarc_math` exists at `app/cam/biarc_math.py`; import path just needs updating. This is the most sophisticated post-processor in the codebase. |
| **modal_cycles.py** | 411 | G81-G89 canned drilling cycles with expanded move support. Modal and non-modal flavors. | 1/1 | **RECOVER** — Self-contained, no missing deps. Only drilling cycle implementation ever written. |
| **saw_gcode_generator.py** | 351 | Multi-pass DOC planning, feed rate IPM→mm/min conversion, safe entry/exit path generation, path length estimation | 3/4 (needs `gcode_models`) | **MINE** — The DOC planning and feed rate math are valuable. The `gcode_models` dependency may have been renamed. Check `app/cam_core/gcode/`. |
| **advanced_offset.py** | 284 | Shapely-based polygon offsetting: miter/round/bevel join styles, arc tessellation, self-intersection cleanup | 5/6 (needs `geometry_models`) | **MINE** — The Shapely offset logic is production-grade. The `geometry_models` import is a local schema that likely still exists under a different name. |

> **Engineer note:** `cam_post_v155_router.py` uses `from ..cam.biarc_math import vec_len, vec_dot, fillet_between, angle_to_point, arc_center_from_radius, arc_tessellate`. Verify these still exist at that path — if so, the router can likely be restored with just a prefix change.

---

### B. Instrument Data — **RECOVER** — 2 files, 352 lines

| File | Lines | What It Does | Triage |
|------|-------|-------------|--------|
| **martin_d28_1937.py** | 66 | **Real measurements from John Arnold technical drawings.** Side depth profile at 12 points (raw + with kerfing: 97.3→101.3mm at lower bout to 95.0→99.0mm at waist). Back brace dimensions (BB1: 286×14×7mm through BB4: 349×12×6mm). Scalloped X-brace flag. | **RECOVER immediately** — This is measured physical data from copyrighted technical drawings. Cannot be regenerated by code. Irreplaceable. |
| **selmer_maccaferri_dhole.py** | 286 | Template spec for Selmer Maccaferri D-hole model. Scale length 670mm, headstock 155mm, heel 8mm. Mostly TODO/None placeholders. | **MINE** — The few real values (scale length, headstock, heel) are worth extracting. The template structure itself is expendable. |

> **Risk:** The Martin D-28 data was deleted in the "cascade cleanup" as an "orphaned file." It has zero imports and zero dependents — it's pure reference data that got caught in an import-graph-based deletion sweep. Import graph analysis is the wrong tool for data files.

---

### C. Archtop Pipeline — **RECOVER** — 2 files, 1,048 lines

| File | Lines | What It Does | Deps Satisfied | Triage |
|------|-------|-------------|----------------|--------|
| **archtop_cam_router.py** | 271 | 6 endpoints: contour CSV→DXF (`/contours/csv`), contour outline (`/contours/outline`), bridge fit calculator with real neck-angle math (`/fit`), floating bridge DXF generator (`/bridge`), saddle profile (`/saddle`). Bridge fit computation: `bridge_height = scale_length * sin(neck_angle)` with ±tolerance range. | 8/8 | **RECOVER** — All dependencies satisfied. The only archtop CAM path that ever existed. Shells out to `archtop_contour_generator.py` which itself was never in git (see legacy doc). |
| **ARCHTOP_LEGACY_DISCOVERY_SUMMARY.md** | 777 | Complete inventory of the pre-git Archtop folder: 4 Python scripts (contour generator, bridge, shop, calculator), 1 Vue component (537 lines), 4 integrated app versions, 6 contour kit variants, 7 PDF field manuals, 2 SVG graduation maps. Integration roadmap with 6-day estimate vs 6-week rebuild. | — | **REFERENCE** — The master inventory doc for the archtop legacy. Essential reading before any archtop work. |

> **Key insight:** The archtop contour generator (`archtop_contour_generator.py`, 143 lines, IDW interpolation → DXF contour rings) was **never committed to git**. It exists only in the pre-git Archtop folder referenced by this discovery doc. The router calls it via `subprocess`. Recovery requires locating the original source folder on disk or in the `ltb-reference-archive` repo.

---

### D. Guitar CAM Routers — **MINE** — 7 files, 1,440 lines

Model-specific CAM routers that were archived then deleted. Most are scaffolding/stubs, but some contain real logic.

| File | Lines | Deps | Triage |
|------|-------|------|--------|
| **om_cam_router.py** | 246 | 5/5 | **MINE** — `OMGraduationMap` model and SVG graduation scanner are reusable. Path traversal protection pattern is production-quality. |
| **registry_cam_router.py** | 396 | 5/5 | **MINE** — Dynamic router generation from `instrument_model_registry.json`. The pattern is reusable even if the exact routes aren't. |
| **stratocaster_cam_router.py** | 279 | 6/6 | **MINE** — Template download, BOM, SVG preview endpoints. The BOM structure has real Stratocaster part lists. |
| **smart_cam_router.py** | 154 | 3/3 | **DISCARD** — Thin wrapper around other routers. No unique logic. |
| **cam_pipeline_router.py** | 79 | 5/5 | **DISCARD** — Simple pipeline status endpoint. Trivially recreatable. |
| **learn_router.py** | 185 | 2/6 | **DISCARD** — Heavy dependency on deleted experimental modules. Would need full subsystem to function. |
| **posts_router.py** | 101 | 5/5 | **MINE** — Post-processor preset CRUD. The preset loading pattern is useful. |

---

### E. Rosette Fabrication — **MINE** — 5 files, 1,747 lines

The rosette manufacturing subsystem. Substantial code, but heavily interconnected with other deleted modules.

| File | Lines | Deps | Triage |
|------|-------|------|--------|
| **traditional_builder.py** | 483 | 5/7 | **MINE** — `WoodSpecies` enum (9 species: ebony, rosewood, walnut, wenge, holly, maple, spruce, boxwood, mahogany), pattern generator integration, PIL rendering. Needs `pattern_generator` and `pattern_renderer` which may still exist somewhere. |
| **rosette_rmos_adapter.py** | 483 | 8/14 | **MINE** — Adapter between rosette operations and RMOS runs. The adaptation pattern is valuable; 6 missing deps make direct restore hard. |
| **rmos_rosette_api.py** | 484 | 4/13 | **DISCARD** — 9 missing dependencies. Would need most of the rosette subsystem restored to function. |
| **image_prompts.py** | 204 | 1/1 | **MINE** — AI image prompt templates for rosette design. Self-contained. |
| **rosette_design_sheet_api.py** | 93 | 5/7 | **DISCARD** — Thin API layer, 2 missing deps. |

---

### F. Validation & Tooling — **RECOVER or MINE** — 4 files, 1,024 lines

| File | Lines | Deps | Triage |
|------|-------|------|--------|
| **dxf_advanced_validation.py** | 344 | 9/10 | **MINE** — Advanced DXF validation (arc integrity, polyline closure, layer checks). One missing dep (`dxf_preflight`) may be renamed. |
| **cam_cutting_evaluator.py** | 284 | 4/5 | **MINE** — Cutting operation feasibility evaluation against tool/material constraints. One missing dep (`core.safety`). |
| **pipeline_spec_validator.py** | 273 | 3/3 | **RECOVER** — All deps satisfied. Pipeline specification validation. |
| **test_mvp_dxf_to_gcode_grbl_golden.py** | 123 | 6/6 | **RECOVER** — Integration test for DXF→G-code GRBL golden path. All deps satisfied. Testing infrastructure. |

---

### G. RMOS Orchestration — **MINE selectively** — 10 files, 2,708 lines

RMOS (Rosette Manufacturing Operations System) API modules. Mixed — some have full deps, some are heavily orphaned.

| File | Lines | Deps | Triage |
|------|-------|------|--------|
| **rmos_stores_api.py** | 497 | 6/8 | **MINE** — Pattern/job log CRUD. 2 missing deps (`rmos_stores`, `websocket.monitor`). |
| **mvp_wrapper.py** | 477 | 7/16 | **DISCARD** — 9 missing deps. Orchestration wrapper for MVP workflow; too entangled. |
| **api_profile_history.py** | 358 | 5/7 | **MINE** — Profile versioning/history. 2 missing deps. |
| **rmos_presets_api.py** | 271 | 8/8 | **RECOVER** — All deps satisfied. Preset CRUD for RMOS. |
| **rmos_pattern_api.py** | 264 | 3/5 | **MINE** — Pattern management. 2 missing store deps. |
| **rmos_safety_api.py** | 202 | 3/5 | **MINE** — Safety checks for operations. 2 missing deps. |
| **rmos_pipeline_run_api.py** | 179 | 8/8 | **RECOVER** — All deps satisfied. Pipeline run management. |
| **api_ai_snapshots.py** | 141 | 4/8 | **DISCARD** — 4 missing deps in AI subsystem. |
| **api_logs_viewer.py** | 141 | 3/5 | **MINE** — Log viewer for operations. 2 missing deps. |
| **api_presets.py** | 116 | 3/4 | **MINE** — Preset management. 1 missing dep. |
| **rmos_analytics_api.py** | 62 | 3/3 | **RECOVER** — All deps satisfied. Analytics endpoint. |

---

### H. Services & Utilities — **MINE selectively** — 16 files, 2,714 lines

Support services, learning hooks, notification systems. Mostly infrastructure.

| Triage | Files | Total Lines | Notes |
|--------|-------|-------------|-------|
| **RECOVER** (all deps met) | `cam_notifier.py`, `compare_automation_helpers.py`, `metrics_registry.py`, `pipeline_handoff.py`, `job_int_favorites.py`, `rmos_gcode_materials.py` | 1,095 | Self-contained utility modules. |
| **MINE** (1-2 missing deps) | `template_engine.py`, `job_risk_store.py`, `risk_reports_store.py`, `tool_db.py` | 646 | Useful patterns, minor dep gaps. |
| **DISCARD** (hooks for deleted systems) | `saw_lab_*` (6 files) | 973 | Learning hooks, metrics rollup, feedback processing — all tied to the deleted Saw Lab learning subsystem. If that system is rebuilt, these provide the template. |

---

### I. Experimental — **MINE selectively** — 25 files, 2,734 lines

Art studio, mesh operations, RMOS runs_v2, migrations, CNC production experiments.

| Triage | Files | Total Lines | Notes |
|--------|-------|-------------|-------|
| **MINE** | `o3d_heal.py` (206), `pocket_sidewall_mesh.py` (77), `mesh_obj.py` (26), `ig_export.py` (92) | 401 | Mesh/geometry utilities — Open3D mesh healing, OBJ export, sidewall generation. Unique capabilities. |
| **MINE** | `saw_joblog_models.py` (340) | 340 | Comprehensive Pydantic models for saw job logging. Well-structured schema. |
| **REFERENCE** | `runs_v2_*` (8 files) | 876 | RMOS runs v2 subsystem. Complete but depends on deleted store layer. Template for v3 if needed. |
| **DISCARD** | Remaining (10 files) | 1,117 | Migrations, sample data creators, thin schemas, experimental dashboards. |

---

### J. Reference Archive Samples — **MINE** — 11 files, 4,593 lines

The most valuable files from the 196-file `__REFERENCE__/` purge. These were prototypes and design documents for systems that may still need building.

| File | Lines | Triage |
|------|-------|--------|
| **rmos_ai_constraint_profiles.yaml** | 807 | **MINE** — Complete RMOS AI constraint profile definitions. This is configuration/policy data, not code. |
| **saw_lab_2_0_code_skeleton.py** | 597 | **MINE** — Architecture skeleton for Saw Lab 2.0. Shows the intended design for the next-gen saw system. |
| **gcode_reader.py** | 511 | **RECOVER** — G-code parser/reader. All 11 deps satisfied. Self-contained utility. |
| **ai_rmos_constraint_profiles.yaml** | 423 | **MINE** — AI-specific RMOS constraints (subset of the 807-line version). |
| **art_studio_feasibility.py** | 411 | **REFERENCE** — Parse error (encoding artifact). Contains feasibility analysis logic for art studio. |
| **validate_saw_blade_library.py** | 384 | **MINE** — Saw blade library validation with comprehensive checks. |
| **saw_lab_2_0_testable.py** | 320 | **MINE** — Testable version of Saw Lab 2.0 skeleton. |
| **rmos_2_0_api_contracts.py** | 276 | **REFERENCE** — Parse error (encoding). RMOS 2.0 API contract definitions. |
| **ARTSTUDIO_Unified.vue** | 102 | **REFERENCE** — Vue component for unified art studio view. Small but shows intended UI layout. |
| **validate_blade_json.py** | 93 | **MINE** — JSON schema validation for blade definitions. |
| **generate_gallery.py** | 88 | **MINE** — Gallery/showcase generation script. All deps satisfied. |

---

## Phantom References Audit

These 27 entries exist in the instrument model registry and spec files, claiming assets that **do not exist on disk and never have in git history**:

### Critical (Referenced by active specs)

| Phantom File | Referenced By | Line | Impact |
|-------------|--------------|------|--------|
| `benedetto_17/graduation_map.json` | `instrument_model_registry.json` | 182 | Registry claims this is an asset of the Benedetto model |
| `benedetto_17/graduation_map.json` | `benedetto_archtop_rope.json` | 127, 246 | Spec references it for top/back carving |
| `benedetto_17/body_outline.dxf` | `benedetto_archtop_rope.json` | — | Body outline DXF for Benedetto 17" |
| `benedetto_17/f_holes.dxf` | `benedetto_archtop_rope.json` | — | F-hole cutting template |
| `generators/lespaul_gcode/` | `instrument_model_registry.json` | 50 | CNC generator directory (never created) |
| `generators/lespaul_config.py` | `instrument_model_registry.json` | 51 | Les Paul CNC config |
| `generators/neck_headstock_config.py` | `instrument_model_registry.json` | 49 | Neck/headstock CNC config |
| `Les Paul_Project/LesPaul_CAM_Closed.dxf` | `instrument_model_registry.json` | 54 | CAM DXF for Les Paul |
| `Les Paul_Project/LesPaul_CAM_Closed_ALL.dxf` | `instrument_model_registry.json` | 55 | Multi-layer CAM DXF |

### High (Referenced by unused or partial specs)

| Phantom File | Referenced By | Notes |
|-------------|--------------|-------|
| `Gibson Plans/Flying V/Flying V 58.dwg` | `instrument_model_registry.json` | No Flying V directory exists |
| `Gibson Plans/Flying V/Flying V 59.dwg` | `instrument_model_registry.json` | |
| `Gibson Plans/Flying V/Flying V 83.dwg` | `instrument_model_registry.json` | |
| `Gibson Plans/L-00/Gibson L-00.pdf` | `instrument_model_registry.json` | No L-00 directory exists |
| `Guitar Plans/Jumbo/J-200 Plans.pdf` | `instrument_model_registry.json` | No Jumbo directory exists |
| `Soprano Ukuele/Body_Outline.dxf` | `instrument_model_registry.json` | **Misspelled** — "Ukuele" vs "Ukulele". Body DXF exists at different path. |
| `Soprano Ukuele/Fret_Slots.dxf` | `instrument_model_registry.json` | Missing entirely |
| `Soprano Ukuele/Headstock_Outline.dxf` | `instrument_model_registry.json` | Missing entirely |

### Medium (External reference docs)

| Phantom File | Referenced By | Notes |
|-------------|--------------|-------|
| `Fender-Stratocaster-62.pdf` | `stratocaster.json` | Blueprint scan — never committed |
| `Strat-Body-Front.pdf` | `stratocaster.json` | Front view reference |
| `All-Fender-Headstocks.pdf` | `stratocaster.json` | Headstock reference vault |
| `Les-Paul-Isolines.pdf` | `gibson_les_paul.json` | Top carve contour reference |
| `Les-Paul-Front-Front-Side-Profile-Carved-Top.pdf` | `gibson_les_paul.json` | 3-view carve profile |

### Path Mismatches

| Claimed Path | Actual Location | Fix |
|-------------|-----------------|-----|
| `folk/Cuatro_Venezolano_body.dxf` | `body/dxf/other/Cuatro_Venezolano_body.dxf` | Update registry path |

---

## Dependency Satisfaction Summary

From the import-check script run:

| Category | Files | Total Imports | Satisfied | Missing | Rate |
|----------|-------|---------------|-----------|---------|------|
| A. CAM Core | 4 | 19 | 16 | 3 | **84%** |
| B. Instrument Data | 2 | 0 | 0 | 0 | **100%** (no deps) |
| C. Archtop Pipeline | 1 (.py) | 8 | 8 | 0 | **100%** |
| D. Guitar CAM Routers | 7 | 37 | 33 | 4 | **89%** |
| E. Rosette Fabrication | 5 | 42 | 22 | 20 | **52%** |
| F. Validation Tooling | 4 | 24 | 22 | 2 | **92%** |
| G. RMOS Orchestration | 10 | 72 | 50 | 22 | **69%** |
| H. Services/Utilities | 16 | 72 | 64 | 8 | **89%** |
| I. Experimental | 25 | 92 | 60 | 32 | **65%** |
| J. Reference Archive | 9 (.py) | 39 | 36 | 3 | **92%** |

**Overall: 311 satisfied / 405 total = 77% dependency satisfaction rate**

Categories A, B, C, D, F, and H are largely restorable with minor import path fixes. Categories E and G need selective mining. Category I is mostly reference material.

---

## Triage Summary for Engineer

| Decision | File Count | Lines | Action |
|----------|-----------|-------|--------|
| **RECOVER** (restore to codebase) | ~20 files | ~4,500 lines | Update import paths, re-register routers, write tests |
| **MINE** (extract algorithms/data) | ~30 files | ~7,000 lines | Pull out reusable functions, schemas, data into current modules |
| **REFERENCE** (keep for design context) | ~10 files | ~3,500 lines | Architecture skeletons, legacy discovery docs, prototype designs |
| **DISCARD** (correctly removed) | ~28 files | ~3,900 lines | Thin wrappers, orphaned hooks, experimental dashboards |

### Priority Order for Engineer Review

1. **B/martin_d28_1937.py** — Irreplaceable measured data. Restore immediately.
2. **A/cam_post_v155_router.py** — Production post-processor. Check `biarc_math` import path and restore.
3. **A/modal_cycles.py** — Only drilling cycle implementation. No missing deps. Restore.
4. **C/archtop_cam_router.py** — Only archtop CAM path. All deps met. Restore.
5. **F/test_mvp_dxf_to_gcode_grbl_golden.py** — Golden-path integration test. All deps met.
6. **A/advanced_offset.py + saw_gcode_generator.py** — Core CAM math. Minor dep gaps.
7. **J/gcode_reader.py** — G-code parser. All deps met. Useful utility.
8. **D/om_cam_router.py + registry_cam_router.py** — Graduation scanner + dynamic router pattern.
9. **Fix 27 phantom references** — Update `instrument_model_registry.json` and spec files.
10. **Everything else** — Mine algorithms as needed during feature work.

---

## How to Use This Recovery

```powershell
# Run the import checker (from services/api/)
cd services/api
python ../../__RECOVERED__/check_imports.py

# Browse by category
ls ../../__RECOVERED__/A_cam_core/        # Core CAM algorithms
ls ../../__RECOVERED__/B_instrument_data/  # Measured instrument specs

# Restore a file (example)
cp ../../__RECOVERED__/A_cam_core/modal_cycles.py app/cam/modal_cycles.py
# Then update imports in the file and register in main.py
```

---

## External Archive Note

Commit `e1929a57` claims the full `__REFERENCE__/` directory (196 files / 50,854 lines) was archived to `https://github.com/HanzoRazer/ltb-reference-archive`. The 11 files in `J_reference_archive_samples/` are a curated subset. If the external repo is accessible, an additional **~135 PowerShell scripts** (wave test runners, setup automation) and **~26 more Python files** (test scripts, validators) could be recovered from there.

---

*Recovery performed 2026-03-07 via git forensics. All files extracted with `git show <commit>~1:<path>` from intact local history.*
