# IBG Code Lineage

**Sprint:** IBG/AGE Precursor Forensic Sprint (read-only)  
**Anchor commit:** `ca2b2347642932609eab28ac400dd6368848f07d` (2026-04-17) — first git add of `sandbox/arc_reconstructor/instrument_body_generator.py`  
**Production promotion:** `471bc902cfc27024e5299e837666c8820b0143da` (2026-04-17)  
**Sandbox deletion:** `261436ae099e740a0c894e4a33536097d637a193` (2026-04-20 21:18 / authored 2026-05-20) — copies claimed migrated to `vectorizer-sandbox` (**UNAVAILABLE this run**)

IBG = **Instrument Body Generator**. Do not read May “Image Body Generator” back into these symbols.

Confidence: High / Medium / Low. Classifications match the sprint vocabulary.

---

## What `ca2b2347` actually introduced

`git show --stat ca2b2347`: **two paths** — new `sandbox/arc_reconstructor/instrument_body_generator.py` (+419) and a small `layer_consolidator.py` wiring diff.

`git ls-tree ca2b2347^ -- sandbox/arc_reconstructor/` is **empty**. The directory is created in this commit.

The new file’s header (excerpt):

```text
Instrument Body Generator — Complete Body from Partial Vectorizer Output
Date: 2026-04-16
Sprint: 9 — InstrumentBodyGenerator
```

It imports siblings that **do not exist in `ca2b2347`:**

- `from body_contour_solver import BodyConstraints, BodyContourSolver, LandmarkPoint, …`
- `from constraint_extractor import ConstraintExtractor`

and production CAM:

- `from app.cam.layer_consolidator import LayerConsolidator`

**Inference:** the first IBG commit is an integrator that assumes local uncommitted modules. It is not a git-squash of prior IBG commits (no such parents). Classification: `HISTORY_PROVEN` incomplete tree; `SUPPORTED_INFERENCE` that sibling files existed on disk before they were committed.

---

## Lineage table

| IBG symbol/concept | First proven implementation | Precursor | Later descendant | Evidence | Confidence |
| ------------------ | --------------------------- | --------- | ---------------- | -------- | ---------- |
| **InstrumentBodyGenerator** (class) | `ca2b2347` `sandbox/arc_reconstructor/instrument_body_generator.py:127` | Dev Order Step 6 in `docs/planning/instrument_body_generator.md` (git add `95385be9` 2026-04-19, document date 2026-04-16) — planning, not code | Production `services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py` (`471bc902`); still present on `origin/main` | `git log -S 'class InstrumentBodyGenerator' -- '*.py'` first add `ca2b2347` | High |
| **complete_from_dxf** | Same file `ca2b2347` | Dev Order Step 6 sketch | Body Solver `POST /api/body/solve-from-dxf` (`c9ebf8a8`) calls the production class | Pickaxe `complete_from_dxf` first `ca2b2347` | High |
| **Layer consolidation / DXF intake “step zero”** | `LayerConsolidator` `d6bcd03f` 2026-04-17 01:59 `services/api/app/cam/layer_consolidator.py` (286 lines; 352K LINE → 189 polylines) | None found under that name before `d6bcd03f` | Wired into IBG `_consolidate_if_needed` in `ca2b2347` (same day, evening) | Separate CAM commit hours before IBG; IBG commit message describes this wiring | High |
| **BodyContourSolver / body reconstruction** | `33aaf3d3` `sandbox/arc_reconstructor/body_contour_solver.py` (header Date 2026-04-16, Sprint 9) | Dev Order Step 1 (planning). Imports `from arc_reconstructor import falloff, radius_from_chord_sagitta, fit_circle_3pts` **before that module is tracked** | Production copy `471bc902` `…/ibg/body_contour_solver.py` | First `class BodyContourSolver` `33aaf3d3` | High |
| **ArcReconstructor / gap bridging** | Production file `471bc902` `…/ibg/arc_reconstructor.py` (1611 lines; header **Date: 2026-04-15**) | Claimed in Dev Order as copy of `body_side_arc_solver.py` `falloff()` — **that filename has no April add in git** (`git log --all -- '**/body_side_arc_solver.py'` empty for an implementation add). Untracked sandbox sibling inferred from `33aaf3d3` import | Same production path on HEAD; sandbox never contained a tracked `arc_reconstructor.py` | First pickaxe `class ArcReconstructor` / `def falloff` in IBG tree is `471bc902`. Docstring date is not a commit | Medium (code at Sprint 4; authorship date unverified) |
| **LandmarkPoint** | `33aaf3d3` `body_contour_solver.py` dataclass | Dev Order Section A | Still in production solver; API `LandmarkInput` (`c9ebf8a8`) | Pickaxe `class LandmarkPoint` | High |
| **ConstraintExtractor / DXF landmarks** | `471bc902` `…/ibg/constraint_extractor.py` | Dev Order Step 5 (planning). Imported by IBG file at `ca2b2347` before the extractor is committed | Waist/centerline filter `6816cd7f` | First `class ConstraintExtractor` `471bc902` | High |
| **Waist landmark handling** | Extractor in `471bc902` (waist_min from middle Y / min X) | Dev Order Step 3/5 text (widest/narrowest X heuristics) | `6816cd7f` “reject centerline noise in waist landmark extraction” | Commit `6816cd7f` is a bounded patch on the extractor | High |
| **Centerline rejection** | `6816cd7f` | None earlier under that description | Remains in production extractor | Single-purpose commit | High |
| **Hardcoded sagitta (chord × 0.05)** | `body_contour_solver._measure_chord_sagitta` as of production `471bc902` / sandbox `33aaf3d3` | None | Replaced `3ed636a9` Sprint 5 | Commit message of `3ed636a9` states the replacement | High |
| **Circle fitting for sagitta** | `3ed636a9` (`_fit_sagitta_from_band`, `_sagitta_from_radius`, `fit_arc_segment`) | IBG `fit_circle_3pts` in `arc_reconstructor.py` (`471bc902`). Vectorizer `96410500` (2026-04-16) has a **different** `fit_circle_3pts` (other determinant). **Not a copy.** | Production solver on HEAD | Side-by-side of the two `fit_circle_3pts` bodies | High they are independent; Medium on why the name collided |
| **Reference outline bridge** | `33aaf3d3` `reference_outline_bridge.py` | Not in the 2026-04-16 Dev Order step table | Production `471bc902` | Added in “Sprint 3” commit alongside solver | High |
| **FAMILY_DEFAULTS / instrument specs** | `INSTRUMENT_SPECS` dict in IBG file `ca2b2347` (dreadnought, cuatro_venezolano, …) | Dev Order Cuatro/dreadnought numeric examples | Later jumbo-family fixes (May–Aug, out of primary window) | First file content | High |
| **DXF output `outline_to_dxf` / `save_dxf`** | Solver/IBG `33aaf3d3` / `ca2b2347` | Dev Order Step 4 (ezdxf R12 LINE loop) | Body Solver JSON + optional base64 DXF `40d5e3f9` | Code + Week 2 commit | High |
| **HTTP Body Solver** | `c9ebf8a8` `body_solver_router.py` | Not in sandbox Dev Order (API was explicitly out of sandbox scope) | OpenAPI `118e7850`; BOE client wiring `70a0d3ee` | Router imports `InstrumentBodyGenerator` | High |
| **Sevy / Mottola / woodworker radius formulas** | `body_contour_solver.py` `33aaf3d3` (`falloff` imported; `woodworker_radius`; high-point / side-height) | Dev Order “Core Math (already in repo — do not rewrite)” citing missing `body_side_arc_solver.py` | Unmerged curvature tech-debt `107900eb` (2026-04-19) is a *different* file (`body_curvature_correction.py` → docs/reference) — not shown to be the IBG source | Formula comments cite AL#58 / AL#78 | Medium for “already in repo” claim (`NOT_FOUND` for that filename) |

---

## Vectorizer / photo-vectorizer boundary (IBG-facing)

| Apparent relationship | Classification | Notes |
| --------------------- | -------------- | ----- |
| IBG Python `import` of `vectorizer_phase3` / `photo-vectorizer` | **NO CONNECTION FOUND** | `git grep` on `471bc902` IBG package and HEAD IBG `*.py`: no hits |
| IBG consuming a DXF file described as vectorizer output | **DATA CONSUMER** | Docstring and `complete_from_dxf`; no shared types |
| `fit_circle_3pts` name in both trees | **CONCEPTUAL SIMILARITY** | Different implementations; vectorizer `96410500` vs IBG `471bc902` |
| `40d5e3f9` touching `light_line_body_extractor.py` | **TEMPORAL_ADJACENCY_ONLY** | Mixed commit with Body Solver Week 2; no IBG symbol in that hunk |
| README/governance “vectorizer → IBG” diagrams | **DOCUMENT REFERENCE** | From 2026-04-19 review onward; not code ancestry |
| Layer consolidator shared with CAM DXF pipeline | **SHARED UTILITY** | `d6bcd03f` then IBG call |

Photo Vectorizer is **not** a parent of IBG. Blueprint vectorizer is an **upstream file producer** in the documented workflow, not an imported library.

---

## Deleted sandbox recovery (inspect-only)

Recoverable at `33aaf3d3` / `ca2b2347` without restoring to production:

```text
git show ca2b2347:sandbox/arc_reconstructor/instrument_body_generator.py
git show 33aaf3d3:sandbox/arc_reconstructor/body_contour_solver.py
git show 33aaf3d3:sandbox/arc_reconstructor/reference_outline_bridge.py
```

Never tracked in `sandbox/arc_reconstructor/` before deletion:

- `arc_reconstructor.py` (only production path)
- `constraint_extractor.py` (only production path)
- `SESSION_AUDITS.md` (Dev Order required; `git log --all -- '**/SESSION_AUDITS.md'` empty)

`261436ae` handoff claims copies now live at `vectorizer-sandbox/src/archaeology/arc_reconstructor/`. **This run cannot confirm.** Production package `services/api/app/instrument_geometry/body/ibg/` was **not** deleted.

---

## What is not a precursor

| Candidate | Ruling |
| --------- | ------ |
| AGE / `VectorizerAGE` | No shared symbols. See relationship matrix. |
| GeometryCoachV2 | Photo-vectorizer retry coach (2026-03-15). No IBG import. Behavioral analogy only — not lineage. |
| Body Outline Editor HTML (2026-04-05) | Independent tool; later *client* of Body Solver. |
| Shop SPRINTS.md Sprint 1–4 (vectorizer/repo-split) | Parallel numbering. |
