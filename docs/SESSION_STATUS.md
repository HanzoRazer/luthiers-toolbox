# Session Status — 2026-03-12

**Branch:** main
**Last Commit:** `af4c1017` feat(rosette): wave/spanish/celtic pattern engines, build simulation, prototypes
**Pushed:** Yes (origin/main up to date)

---

## Session Timeline

| Time | Action | Commit | Details |
|------|--------|--------|---------|
| Session start | Checkpoint + orientation | — | 3-repo workspace: luthiers-toolbox, code-analysis-tool, sg-spec |
| — | Reviewed uncommitted work | — | 8 modified + 3 untracked in luthiers-toolbox (616 lines) |
| — | Rosette system audit | — | Full-stack audit of rosette creation pipeline (2 engines, ~30 endpoints, 25+ presets) |
| — | Commit + push | `af4c1017` | 33 files, 13,759 insertions — wave/spanish/celtic patterns, prototypes, simulation endpoint |

---

## What Was Committed (af4c1017)

### Pattern Engine Expansion
- **`_grid_to_annulus_paths()`** — shared grid→annulus mapping (cols→angular, rows→radial)
- **Wave pattern** — asymmetric crashing arch formula (amplitude, skew, chase, strands)
- **Spanish right-angle** — 23×15 mosaic grid (black/white/blue)
- **Celtic knot** — 4 tile libraries (square8, braid8, step12, rosette16)
- Dispatch wiring + BOM calculation for grid-based patterns

### New Endpoints
- `POST /api/art/rosette/pattern/simulate-build` — billet assembly + CNC channel routing simulation
- Router registered in manifest

### Prototypes Committed
- 13 Python prototype scripts (`prototypes/` directory)
- 11 JSX rosette grid designer prototypes (`docs/rosette-prototypes/jsx/`)
- `scripts/extract_herringbone_quads.py` utility

### Spec Updates
- Smart Guitar `cover_plate_screws` added to 2 cavities (4× #4 screws each, positioned from center)
- 10 rosette "Safe Default" presets in art_presets.json
- Test lane in learned overrides

---

## Current State

### Repos
| Repo | Branch | Status |
|------|--------|--------|
| luthiers-toolbox | main | Clean (all committed + pushed) |
| code-analysis-tool | main | 43 modified + 30 untracked (separate work) |
| sg-spec | main | Clean |

### Test Status (last known)
```
2395 passed, 16 failed, 37 skipped, 19 xfailed
```
16 pre-existing failures (auth/decision tests) — not caused by this session.

---

## Active Work Queue

- [x] Full rosette system audit (2 engines, ~30 endpoints, 7 pattern types)
- [x] Commit + push af4c1017 (33 files, 13,759 insertions)
- [x] Consolidation strategy — 6-phase roadmap delivered
- [x] Batch 2 JSX prototypes examined + classified (8 files)
- [x] Created `docs/rosette-prototypes/placeholder.md` — addendum with lineage map
- [ ] File 8 JSX prototypes into `docs/rosette-prototypes/jsx/` (rename per addendum)
- [ ] Begin consolidation Phase 1 (dead module cleanup)

---

## Batch 2 JSX Prototypes (8 files at repo root — not yet filed)

| File | Lines | Classification |
|------|------:|----------------|
| `shape-compositor.jsx` | 732 | Compositor v1 — **superseded** by v3 |
| `shape-compositor (1).jsx` | 759 | Compositor v2 (+hyperbolic_wave) — **superseded** by v3 |
| `shape-compositor (2).jsx` | 880 | Compositor v3 (+braid_trenza) — **LATEST** |
| `rosette-designer.jsx` | 544 | Multi-ring v1 (color-index) — **superseded** by Studio |
| `rosette-studio.jsx` | 636 | Multi-ring v2 (wood materials) — **LATEST** |
| `rosette-wheel.jsx` | 511 | Cell Painter — **UNIQUE** (symmetry painting paradigm) |
| `hyperbolic-rosette.jsx` | 643 | Dedicated Hyp Wave Composer — **UNIQUE** |
| `diamond-chevron-rosette.jsx` | 657 | Dedicated Diamond+Chevron Composer — **UNIQUE** |

Full details: `docs/rosette-prototypes/placeholder.md`

---

## Key Files Modified This Session

| File | Change |
|------|--------|
| `services/api/app/cam/rosette/modern_pattern_generator.py` | +309 lines: wave, spanish, celtic engines |
| `services/api/app/art_studio/api/rosette_pattern_routes.py` | +81 lines: simulate-build endpoint |
| `services/api/app/cam/rosette/prototypes/` | 13 new prototype scripts |
| `docs/rosette-prototypes/jsx/` | 11 JSX grid designer prototypes |
| `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json` | +50 lines: cover plate screws |
| `services/api/app/router_registry/manifest.py` | +6 lines: route registration |
| `services/api/data/art_presets.json` | +100 lines: 10 rosette presets |
| `scripts/extract_herringbone_quads.py` | New utility script |

---

## Notes

- Rosette system has 2 generation engines: **Traditional Matrix** (25+ presets, luthier schools) and **Modern Parametric** (7 pattern types)
- Pattern types now: solid, rope, herringbone, checkerboard, wave, spanish, celtic_knot
- CAM pipeline is governed: feasibility gate → toolpath → G-code → run artifact with SHA256 provenance
- Bridge break angle derivation document open in editor (external to repos)
