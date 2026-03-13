# Session Status — 2026-03-13

**Branch:** main
**Last Commit:** `108b8cad` feat(inlay): port 3 generators from amsterdam_spiro_engine prototype
**Pushed:** Yes (origin/main up to date)

---

## Session 1 — Rosette Pattern Engines (2026-03-12)

**Commit:** `af4c1017` — 33 files, 13,759 insertions

| Action | Details |
|--------|---------|
| Checkpoint + orientation | 3-repo workspace: luthiers-toolbox, code-analysis-tool, sg-spec |
| Reviewed uncommitted work | 8 modified + 3 untracked (616 lines) |
| Rosette system audit | Full-stack audit: 2 engines, ~30 endpoints, 25+ presets |
| Commit + push | `af4c1017` — wave/spanish/celtic patterns, prototypes, simulation endpoint |

### What Was Committed
- **`_grid_to_annulus_paths()`** — shared grid→annulus mapping (cols→angular, rows→radial)
- **Wave pattern** — asymmetric crashing arch formula (amplitude, skew, chase, strands)
- **Spanish right-angle** — 23×15 mosaic grid (black/white/blue)
- **Celtic knot** — 4 tile libraries (square8, braid8, step12, rosette16)
- `POST /api/art/rosette/pattern/simulate-build` — billet assembly + CNC channel routing simulation
- 13 Python prototype scripts, 11 JSX grid designer prototypes
- Smart Guitar `cover_plate_screws` added to 2 cavities
- 10 rosette "Safe Default" presets in art_presets.json

---

## Session 2 — Remediation Sprint + Platform Hardening (2026-03-12)

**Commits:** `6f86018b` through `ba7538fe` — 159 files changed, 24,116 insertions, 2,145 deletions

This was the largest session by commit count (~40 commits). Systematic remediation of codebase health score from 4.7/10 toward production readiness.

| Phase | Commit(s) | Details |
|-------|-----------|---------|
| Exception hardening | `6e397cb6` | 0 unmarked broad exceptions remaining |
| God-object decomposition | `51ed4f6b` | neck_router.py 1,139→205 LOC |
| CNC safety fail-closed | `6f86018b` | Preflight validation gate |
| Store singleton DI | `c79dd1a7` | Centralized StoreRegistry for testability |
| Security fix | `da6f3330` | defusedxml for SVG parsing (XXE prevention) |
| Dead import cleanup | `afd72185` | 15 unused imports removed (vulture) |
| Radon baseline | `c5890a6e` | Complexity metrics documented |
| Inlay engine v1 | `9bcd373a` | Python backend — 10 generators, 61 tests |
| Prototype consolidation | `854b1052` | HTML prototypes → unified engine |
| RMOS UI tests | `38038ade` | 52 unit tests for RMOS components |
| Gap analysis resolution | `9fc8b865`, `57dbbc72`, `eeaff824` | 67 gaps resolved, GAP-02/05/07/08 closed |
| Strat body generator | `0642b77c` | Stratocaster body outline generator (GAP-07) |
| Deprecated cleanup | `ba7538fe` | `_experimental/ai_core` deleted + status docs |

### Issue Tracker Closures
Issues resolved: #1 (exceptions), #2 (god-objects ~90%), #6 (Vue decomposition), #7 (Score 7 ~50%), #9 (frontend tests), #14 (singleton store), #16 (CNC safety), #17 (auth infra), #19, #20, #21, #22, #23, #24, #28, #29, #30, #31

---

## Session 3 — Geo Band & Rope Generator Integration (2026-03-12)

**Commit:** `e2a1b7f4` — 5 files changed, 1,159 insertions, 13 deletions
**Tests:** 61 → 100 passing

Ported algorithms from `geo_band_generator.html` into the unified Python inlay engine with true geometric CNC offsets.

### Math Infrastructure (`inlay_geometry.py`)
- `compute_tangent_normal_arclen` — per-vertex T/N/s for polylines
- `build_centerline` — 5 shapes: straight, cscroll, swave, spiral, custom
- `generate_strand_paths` — N-strand phase-based rope weaving
- `split_strand_at_crossings` — depth sign-change detection
- MATERIALS expanded to 14 entries with grain colors

### New Generators (`inlay_patterns.py`)
- `hex_chain`, `chevron_panel`, `parquet_panel`, `nested_diamond`, `rope_border_motif`
- `twisted_rope` — parametric N-strand with 4 presets (purfling, binding, headstock, fret)
- `compose_band` — multi-layer band compositor with gap/repeat/mirror

### API
- `POST /api/art/inlay/compose` — band composition endpoint
- Schema: `InlayShape` Literal expanded 10→17, `ComposeBandRequest` model added

---

## Session 4 — Generator Expansion + BOM + Blueprint Bridge (2026-03-13)

**Part of commit:** `a7228c89` (backend portion)
**Tests:** 100 → 123 passing (then → 141 after session 5 additions)

### 5 New Generators
| Generator | Description |
|-----------|-------------|
| `checker_chevron` | Alternating chevron rows with 2-material index cycling |
| `block_pin` | Rectangular blocks with round pin accent inlays |
| `amsterdam_flower` | Radial petal rosette with polygon centre |
| `spiro_arc` | Spirograph-inspired arcing fan patterns |
| `sq_floral` | Square-framed floral motif with n-fold symmetry |

### Infrastructure
- **`grain_angle`** parameter added to all generators — sets wood grain orientation per element
- **BOM calculator** (`calculate_bom`) — aggregates shape_type × material_key with area_mm² and piece counts
- **Blueprint bridge** — `InlayBlueprintV1` schema for downstream CAM/CNC consumption
- **`fretboard_trapezoid`**, **`rosette_ring`**, **`binding_strip`** — 3 spacing utility generators
- `InlayShape` Literal expanded 17→22

### API Additions
- `POST /api/art/inlay/bom` — BOM calculation endpoint
- `GET /api/art/inlay/generators` — list available generators with metadata
- All generators registered in router with parameter schemas

---

## Session 5 — Frontend View + Undo/Redo + Measure Tool (2026-03-13)

**Commit:** `a7228c89` — 28 files, 10,289 insertions, 15 deletions
**Tests:** 141 passing (inlay), full suite not re-run

Built the complete frontend for the 22-generator inlay pattern engine.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/views/art-studio/InlayPatternView.vue` | Main view (~510 lines) — generator picker, param forms, SVG preview, export |
| `packages/client/src/stores/useInlayHistoryStore.ts` | Pinia snapshot stack — undo/redo with MAX_HISTORY=50 |
| `packages/client/src/components/art/inlay_patterns/InlayMeasurePanel.vue` | Measurement results display (distance, angle, deltas) |
| `packages/client/src/components/art/inlay_patterns/InlayBomPanel.vue` | BOM table display (shape_type, material_key, count, area_mm²) |

### Features
- **Route:** `/art-studio/inlay-patterns` → `ArtStudioInlayPatterns`
- **Generator selection** with dynamic parameter forms built from API metadata
- **SVG preview** with viewBox→mm coordinate mapping
- **Measurement tool** — click-to-measure on SVG (distance in mm, angle, dx/dy)
- **Undo/redo** — Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y with snapshot history
- **Export** — SVG, DXF, layered SVG downloads
- **BOM panel** — material breakdown with totals
- **Material/offset controls** — male offset, pocket offset, background material

### Modified Files
- `packages/client/src/router/index.ts` — added inlay patterns route
- `services/api/data/art_presets.json` — new preset data
- Various backend test and schema files

---

## Session 6 — Amsterdam Spiro Engine Port (2026-03-13)

**Commit:** `108b8cad` — 4 files changed, 2,245 insertions, 2 deletions
**Tests:** 141 → 158 passing

Analyzed the 1,525-line `amsterdam_spiro_engine.html` standalone prototype and ported its remaining generators into the Python backend.

### HTML Prototype Fixes
- Fixed typo: `exportSraySVG()` → `exportSpraySVG()` onclick handler
- Fixed flower tab: second button now calls `exportFlowerOSCAD()` (was `exportFlowerSVG()`)
- Added missing JS functions: `exportSpraySVG()`, `exportSprayOSCAD()`, `exportFlowerOSCAD()`

### 3 New Generators (inlay_patterns.py)

| Generator | Description | Key Math |
|-----------|-------------|----------|
| `oak_medallion` | N-fold kite-ring medallion with 1–3 concentric layers | 4-cubic-Bézier kite approximation, multi-ring offsets |
| `floral_spray` | Cubic Bézier stem with tangent-following lens petals | `_cubic_bezier_eval/tangent`, `_lens_polygon` |
| `open_flower_oval` | Hook/comma petals around elliptical frame with pip accents | `_hook_petal_polygon`, ellipse-adjusted petal placement |

### Helper Functions Added
- `_kite_path()` — 4-cubic-Bézier kite as closed polygon with configurable curvature
- `_cubic_bezier_eval()` / `_cubic_bezier_tangent()` — generic cubic Bézier evaluation
- `_lens_polygon()` — eye/lens shape from two Bézier arcs
- `_hook_petal_polygon()` — hook/comma petal with curl depth control

### Schema & Registry
- `InlayShape` Literal expanded 22→25
- `INLAY_GENERATORS` dict: 22→25 entries
- 17 new tests across `TestOakMedallion` (7), `TestFloralSpray` (5), `TestOpenFlowerOval` (5)

### Material Palette Note
- HTML prototype has 12 materials (`blk_mop` key)
- Python backend has 14 materials (`black_mop` key, plus `bone`, `cedar`)
- Backend is the superset — no reconciliation needed

---

## Current State

### Repos
| Repo | Branch | Status |
|------|--------|--------|
| luthiers-toolbox | main | Clean (amsterdam_spiro_engine.html now tracked) |
| code-analysis-tool | main | Separate work in progress |
| sg-spec | main | Clean |

### Test Status
```
Inlay tests: 158 passed (0 failed)
Full suite: not re-run since session 2
```

### Inlay Engine Summary
- **25 generators** across geometric, rope, floral, medallion, and utility categories
- **14 wood materials** with grain color data
- **BOM calculator** with area estimation
- **Full frontend** with undo/redo, measure tool, export
- **158 tests** covering all generators, geometry math, BOM, spacing utilities

---

## Active Work Queue

### Completed
- [x] Rosette system audit + commit (Session 1)
- [x] Remediation sprint — exceptions, god-objects, security, CNC safety (Session 2)
- [x] 67 gap analysis items resolved (Session 2)
- [x] Router consolidation 132→87 (Session 2)
- [x] API v1 curation 17→43 endpoints (Session 2)
- [x] Guided workflows + agentic spine + async job queue (Session 2)
- [x] Geo band & rope generator integration — 7 new generators (Session 3)
- [x] 5 more generators + BOM + blueprint bridge (Session 4)
- [x] Frontend InlayPatternView with undo/redo + measure tool (Session 5)
- [x] Amsterdam spiro engine analysis + 3 generator port (Session 6)

### Open
- [ ] File 8 JSX rosette prototypes into `docs/rosette-prototypes/jsx/` (from Session 1)
- [ ] Begin consolidation Phase 1 (dead module cleanup)
- [ ] Re-run full test suite and update pass/fail counts
- [ ] Wire inlay view into art-studio sidebar navigation

---

## Commit Log (all sessions)

| Session | Commit | Files | Insertions | Deletions | Summary |
|---------|--------|------:|----------:|---------:|---------|
| 1 | `af4c1017` | 33 | 13,759 | — | Rosette wave/spanish/celtic engines |
| 2 | `6f86018b`…`ba7538fe` | 159 | 24,116 | 2,145 | Remediation sprint + platform hardening |
| 3 | `e2a1b7f4` | 5 | 1,159 | 13 | Geo band & rope generators |
| 4–5 | `a7228c89` | 28 | 10,289 | 15 | 5 generators + BOM + frontend view |
| **Total** | | **225** | **49,323** | **2,173** | |

---

## Notes

- Rosette system: 2 engines — **Traditional Matrix** (25+ presets) and **Modern Parametric** (7 types)
- Inlay engine: 22 generators, unified API, CNC-ready (male/pocket offsets, DXF R12 export)
- CAM pipeline: governed — feasibility gate → toolpath → G-code → run artifact with SHA256 provenance
- Codebase remediation score improved from 4.7/10 baseline (exact re-score pending)
- `amsterdam_spiro_engine.html` at repo root is an uncommitted prototype (candidate for `prototypes/` directory)
