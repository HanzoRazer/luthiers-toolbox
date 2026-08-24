# Changelog

All notable changes to **The Production Shop** (this repository, `luthiers-toolbox`) are
documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Refreshed 2026-08-24.** The file had drifted badly and was rebuilt against the
> repository's own history. What changed, and why you can trust the result:
>
> - **Eleven shipped releases were missing.** `toolbox-v0.33.0-wave22.1` through
>   `toolbox-v0.39.1` are all tagged and published on GitHub, but the newest entry
>   here was `toolbox-v0.32.0`. They are now filed, sourced from their release notes
>   where those carry content and from the commit range between tags where they do
>   not (v0.35.0–v0.38.0 and v0.39.1 shipped with deploy-boilerplate release notes
>   only, so their entries are reconstructed from commits and say so).
> - **Three `[Unreleased]` sections existed**, one of them below a released version
>   and one of them a roadmap. There is now exactly one, at the top, where the format
>   requires it.
> - **Work filed as "unreleased" had shipped months earlier.** Entries were dated and
>   attributed by proving ancestry against the tags — see the note on each. Entries
>   that could not be attributed are grouped under *Unattributed* rather than guessed at.
> - The roadmap has been separated from the changelog; a changelog records what
>   shipped, not what is planned.
>
> Every claim above is reproducible. [How this file was reconstructed](#how-this-file-was-reconstructed)
> gives the exact commands and the decision rules — attribution by ancestry, marking
> reconstructions as reconstructions, refusing to date unprovable work into a release —
> so the next refresh extends this work instead of re-deriving it.

---

## [Unreleased]

Covers `toolbox-v0.39.1` (2026-02-28) → `main` at **`7d134c36`** (2026-08-24):
**1,734 commits across 281 merged pull requests**, with no release cut in that window.

Both numbers are pinned to that commit and were re-derived there — not carried over from
an earlier measurement. They move whenever `main` does; re-derive rather than trust them
(see [How this file was reconstructed](#how-this-file-was-reconstructed)).

Because that is far too much to enumerate faithfully, the summary below is grouped by
area and derived from commit scopes and merged PR titles. It is **representative, not
exhaustive** — the tag range is the authoritative record. Item counts are commit counts
for that scope, not feature counts. The one exception is the breaking change immediately
below: capability removals are always listed individually, never summarised.

### Removed — BREAKING

- **All four retract G-code routes now fail closed** (RMOS-CONVERGE-001B, #314,
  merged 2026-08-24 as `e1365198`). `POST /api/cam/retract/gcode`,
  `/gcode/download`, `/gcode_governed` and `/gcode/download_governed` no longer
  emit G-code; every one returns **`409 SAFETY_BLOCKED`** and will until a
  substantive retract feasibility evaluator exists.

  Listed explicitly rather than folded into the summary below, because it is the
  one change in this window that removes a capability callers were using. Two of
  those routes previously built G-code and then minted their own
  `RunDecision(risk_level="GREEN")` around output no evaluator had assessed; the
  other two bypassed RMOS entirely and served a `.nc` download with no run,
  decision or hash. The `_governed` suffix is now a retained alias, not a second
  lane.

  Consumer-facing detail, including the before/after table per route and what a
  caller must change: [`docs/api/endpoints.md`](./docs/api/endpoints.md).
  Full census and the findings it surfaced but did not fix:
  `docs/audit/rmos_prod_output_census_001b.md`.

### Added

- **CAM** (82 commits) — canonical process authorization anchor; process-exclusive
  canonical geometry authority (C2, ratified 2026-07-04); review-queue architecture
  readiness check; production views wired to real intent–G-code endpoints
  (contour/profiling, drilling) in place of stubs.
- **Calculators** (35) — Soundhole Calculator (Helmholtz + P:A), Scala `.scl` file
  parser, cantilever armrest, inverse brace sizing from a deflection target, and the
  acoustic chain wired into the build sequence.
- **Vectorizer / blueprint intake** (32 + 23 + 22) — V2_RAW and PHOTO_V2 recovery modes
  exposed on the API; text-masking preprocessing for blueprint extraction; grid
  reclassification; async job pipeline for production deployment; soundhole-based
  calibration for DXF scaling; multi-view blueprint segmentation; flag-gated geometry
  deduplication (default OFF).
- **IBG** (19) — canonical repository proposal pipeline, worktree isolation layer,
  descriptive execution planning, observational proposal evaluation, provenance bridge.
- **Acoustics** (15) — ingest audit log and UI panel, experimental drift timeline
  workspace and session synthesis, measurement-lab session panel.
- **Governance / RMOS** (13 + others) — namespace authority drift detector,
  `ConfidenceEnvelopeV1` cross-repo interoperability layer, DXF lifecycle guards across
  neck and remaining routers, cross-repo governance normalization contracts.
- **Smart Guitar** (14) — traced body outline, control-cavity spec with CNC operations,
  neck length fields, `GET /api/instruments/smart-guitar/dxf`.

### Changed

- **RMOS stub retirement** — safety evaluate/mode, rosette segment-ring, slice
  generation and preview, live-monitor drilldown, and the DXF→GRBL wrap were all moved
  off placeholder implementations onto real engines and the `runs_v2` store.
- **Materials data** (54 docs commits) — substantial wood-species and tonewood
  reference work.
- **Documentation** (230 docs commits, incl. 56 sprint and 18 audit) — the single
  largest category in the window.

### Fixed

- CI (43), tests (28), Docker (17), CAM (16), vectorizer (13).

### Instrument geometry, neck, headstock and photo-vectorizer work (March 2026)

The entries below were previously filed under a mid-file `[Unreleased]` heading. They
are genuinely unreleased — the files they describe were added on 2026-03-18/19,
after the `toolbox-v0.39.1` tag (2026-02-28) — so they belong here, verbatim.

### Refactor

- **CLEANUP-001**: Graduated `app/_experimental/analytics/` to production `app/analytics/`; analytics sub-routers now import `app.analytics.*` (no experimental path).

### 🎸 Instrument Geometry

- **ARCH-002**: Added `arch_height_mm: 16.0` and `arch_height_note` to Benedetto 17" graduation map (instrument_geometry/models/benedetto_17/graduation_map.json)

- **GEOMETRY-010**: Side bending parameters calculator (`calculators/side_bending_calc.py`)
  - Bending temp/moisture by species (mahogany, rosewood, maple, koa, sapele, walnut, cedar, spruce)
  - Min bend radius safety check with GREEN/YELLOW/RED risk gate
  - Spring-back estimation (5-8° typical)
  - Side thickness targets by instrument type (steel string, classical, archtop, hollow-body, ukulele)
  - `POST /api/instrument/side-bending` — bending plan with risk assessment
  - `POST /api/instrument/side-thickness` — thickness recommendation
  - `GET /api/instrument/side-bending/options` — supported species and instrument types

- **CONSTRUCTION-001**: Nut slot depth schedule calculator (`calculators/nut_slot_calc.py`)
  - String diameter + fret crown height → slot depth formula
  - 6 fret types (vintage_narrow, medium, medium_jumbo, jumbo, extra_jumbo, evo_gold)
  - 4 preset string sets (light electric, regular electric, light acoustic, medium acoustic)
  - GREEN/YELLOW/RED clearance gate (optimal: 0.3-0.5mm above first fret)
  - `POST /api/instrument/nut-slots` — complete slot schedule with gate assessment
  - `GET /api/instrument/nut-slots/options` — supported fret types and string presets

- **GEOMETRY-005**: Neck block and tail block sizing calculator (`calculators/neck_block_calc.py`)
  - Block dimensions from side depth and body style
  - Standard side depths for 7 body styles (dreadnought, om_000, parlor, classical, archtop, jumbo, concert)
  - Neck block: height=side depth, width=heel+12mm, depth=50-65mm
  - Tail block: height=side depth, width=65-90mm, depth=30-40mm
  - GREEN/YELLOW/RED gate for structural adequacy
  - `POST /api/instrument/blocks` — both neck and tail block specs
  - `GET /api/instrument/blocks/options` — supported body styles

- **GEOMETRY-006**: Fret wire selection calculator (`calculators/fret_wire_calc.py`)
  - 7 fret profiles (vintage_narrow, medium, medium_jumbo, jumbo, extra_jumbo, evo_6105, stainless_6105)
  - 3 materials (nickel_silver, stainless, evo_gold) with hardness and wear factor
  - Selection based on playing style (fingerstyle, flatpick, shred, jazz)
  - Compatibility with fretboard materials and neck profiles
  - `POST /api/instrument/fret-wire/recommend` — ranked recommendations
  - `GET /api/instrument/fret-wire/catalog` — full catalog
  - `GET /api/instrument/fret-wire/options` — available options

- **CONSTRUCTION-008**: Electronics physical layout calculator (`calculators/electronics_layout_calc.py`)
  - Pickup cavity dimensions: humbucker (50×40×45mm), single_coil (90×15×45mm), p90 (90×50×45mm), mini_humbucker (67×34×40mm)
  - Control cavity sizing with pot count adjustment (19mm minimum spacing)
  - Switch cavity specs (3way_toggle, 5way_blade, rotary)
  - Jack cavity specs (side, top, endpin)
  - Body style presets (les_paul, stratocaster, telecaster, sg)
  - Shielding area calculation
  - GREEN/YELLOW/RED gate for cavity clearance vs body thickness
  - `POST /api/instrument/electronics-layout` — complete electronics layout
  - `POST /api/instrument/electronics-layout/pickup-cavity` — single pickup cavity
  - `POST /api/instrument/electronics-layout/control-layout` — control/switch/jack layout
  - `GET /api/instrument/electronics-layout/options` — available options

### 🔬 Acoustics / Plate Design

- **PORT-001**: Ported tap-tone-pi plate thickness design module to `calculators/plate_design/`
  - `thickness_calculator.py`, `calibration.py`, `inverse_solver.py`, `rayleigh_ritz.py`, `alpha_beta.py`, `gamma_calibration.py`, `coupled_2osc.py`, `archtop_graduation.py`

### 🛠️ Neck Suite

- **GEOMETRY-001**: Neck angle promoted to first-class calculator
  - `instrument_geometry/neck/neck_angle.py`: `NeckAngleInput`, `NeckAngleResult`, `compute_neck_angle()`
  - Gates: GREEN 1.0-3.5°, YELLOW 0.5-1.0° / 3.5-5.0°, RED <0.5° or >5.0°
  - POST `/api/neck/angle` endpoint wired in neck_router.py
  - Phase 2 of bridge geometry chain: neck_angle → break_angle → compensation → setup

- Added `routers/neck/headstock_transition_export.py` — DXF + G-code for headstock transition zone with volute geometry
- Added `routers/neck/neck_profile_export.py` — DXF export for neck profile cross-sections

### 🪚 Headstock DXF Export

- **HEADSTOCK-001**: Added `routers/headstock/dxf_export.py` (30KB) — BCAMCNC 2030A DXF export with:
  - `VeneerSpec` model — face veneer as inward-offset layer
  - `BindingSpec` model — binding rabbet with material bend radius warnings
  - 7-section `build_dxf()`: outline, tuners, nut, inlay, truss rod, veneer, binding
  - Material cost estimate endpoint

### 🖼️ Photo Vectorizer

- **VECTORIZER-001**: Added `routers/photo_vectorizer_router.py` (9KB) — FastAPI router wrapping `PhotoVectorizerV2`
  - `POST /api/vectorizer/extract` — base64 image → SVG path + bounding box + warnings
  - Graceful fallback when cv2/rembg/potrace deps unavailable

### 📋 Documentation

- Added `docs/BACKLOG.md` — implementation backlog with scoped tasks from code analysis

---

## [toolbox-v0.39.1] - 2026-02-28

**Documentation fixes.** Reconstructed from the three commits in
`toolbox-v0.39.0..toolbox-v0.39.1`; the published release notes contain only Docker
deploy boilerplate.

#### Fixed
- Renamed `README.md` to `DEVELOPMENT.md` to resolve an MkDocs file conflict
- Removed broken links that were failing MkDocs strict mode

#### Docs
- Added CBSP21 protocol documentation

---

## [toolbox-v0.39.0] - 2026-02-28

### Wave 27.1 Dead Code Recovery + Design Review

**Focus:** Recovery and UI decomposition
**Type:** Restoration + refactor release (475 commits since v0.38.0)

#### Fixed
Nine functional modules deleted in error during an aggressive dead-code cleanup were
restored — **1,407 lines across 9 files**:

| Priority | File | Lines |
|----------|------|-------|
| P0-CRITICAL | `app/post_injection_helpers.py` | 488 (import chain repaired) |
| P1-HIGH | `cam_dxf_adaptive_router.py` | 147 (DXF → Adaptive workflow) |
| P1-HIGH | `cam_relief_router.py` | 160 (CAM relief operations) |
| P1-HIGH | `cam_core/saw_lab/queue.py` | 265 |
| P2-MEDIUM | `cnc_production/presets_router.py` | 77 |
| P2-MEDIUM | `websocket/monitor.py` | 131 |
| P2-MEDIUM | `schemas/job_log.py` | 81 |
| P2-MEDIUM | `services/rmos_stores.py` | 130 |
| P3-LOW | `ai/prompts/templates.py` | 235 |
| P3-LOW | `workflow_schemas.py` | 181 |

#### Changed
- Largest UI refactor in the project's history: **127 `refactor(ui)` commits**, including
  god-object decomposition of `CompareLabView` and `AdaptivePocketLab`
- Client Phase 1 code quality: `useAsyncAction` composable (5 stores refactored), named
  timing and dimension constants replacing magic numbers across 13 files

#### Added
- **Security:** `eval()` removed from `ScientificCalculator.vue`, replaced with a safe
  `parseFraction()` — eliminated an XSS vector
- **Safety:** mandatory simulation gate for G-code exports
- Business Startup Suite and Engineering Cost Estimator modules (+ Vue wrapper)
- Analyzer interpretation layer for `tap_tone_pi` integration
- `/api/_meta/routing-truth` endpoint backing a CI gate
- CI tooling: Vue decomposition analyzer (LOC enforcement), API wiring verification,
  stub-endpoint scanner
- Wood species database expanded to 472 species (v4.0.0)
- Bézier body outline generator for acoustic guitars
- DXF preflight validator composables; `useSavedViews` with versioning and statistics
- Rosette Photo Batch Processor wired up (Wave 27)

#### Docs
- Critical systems design review (2026-02-28) with scorecard

---

## [toolbox-v0.38.0] - 2026-02-09

### Phase 9 God-Object Decomposition Complete

Reconstructed from the three commits in `toolbox-v0.37.0..toolbox-v0.38.0`; the
published release notes contain only Docker deploy boilerplate.

#### Changed
- `main.py` simplified using `router_registry`: **915 → 207 lines**
- Phase 9 schema extraction for `geometry` and `blueprint_cam_bridge`

---

## [toolbox-v0.37.0] - 2026-02-09

Reconstructed from the seven commits in `toolbox-v0.36.1..toolbox-v0.37.0`; the
published release notes contain only Docker deploy boilerplate.

#### Added
- Phase 10 startup validation for safety-critical modules (`feat(health)`)

#### Changed
- Phase 9 god-object decomposition — schemas and router registry extracted
- Phase 8 exception hardening — broad catches documented, types added
- Phase 7 root directory cleanup
- Removed an accidental `tap_tone_pi` copy (−2 MB, 282 files)

#### Docs
- Phase 11 API surface documentation; review remediation plan (Phases 7–11)

---

## [toolbox-v0.36.1] - 2026-02-09

Documentation only — two bookmark updates recording the v0.36.0 tag/release and a
cross-repo cleanup summary. No code change in `toolbox-v0.36.0..toolbox-v0.36.1`.

---

## [toolbox-v0.36.0] - 2026-02-09

### Remediation Complete + WP-3 Decomposition

Reconstructed from the 48 commits in `toolbox-v0.35.0..toolbox-v0.36.0`; the published
release notes contain only Docker deploy boilerplate.

#### Added
- Safety and health features; UI and API additions

#### Changed
- WP-3 decomposition (this is the work that split `store_completeness.py` out of
  `store.py` in `rmos/runs_v2`)

#### Fixed
- Test stability (3), agentic policy (2), RMOS (1)

#### Docs
- 15 documentation commits — the bulk of the release

---

## [toolbox-v0.35.0] - 2026-02-07

**131 commits since v0.34.1.** The published release notes contain only Docker deploy
boilerplate; the content below is reconstructed from commits, plus the WP-2 entry that
had been mis-filed as unreleased.

#### Added
- **Agentic spine** (10 commits) — cross-repo contracts for agent orchestration, spine
  reference implementation (moments + policy), UWSM update engine and shadow replay
  harness, replay-determinism test suite, session-level directive gating with
  `FIRST_SIGNAL` grace selector and cooldown, `make verify-policy`
- **Rosette** (6) — real tile segmentation geometry, formula-accurate pattern renderer,
  traditional builder interface, beginner-friendly presets, corrected AI image prompts
- **Smart Guitar** (4) and **demo surfaces** (4) — Blueprint Reader with DXF
  import/export and GPT-4o Vision analysis, CNC Studio, Fret Calculator tab
- Saw Lab and job-log placeholders wired to the real SQLite `cnc_production` stores
- Real feeds & speeds implementation wired into CAM
- Headstock inlay art prompt module; `dragon_dreadnought` template
- M1 Advisory Mode — CoachBubble + directive store

#### Changed

##### WP-2: API Surface Reduction (2026-02-06)

> **Attribution note.** This block was filed under `[Unreleased]` until 2026-08-24. It
> is in this release: `57d4ff73` is an ancestor of `toolbox-v0.35.0`, and
> `services/api/ROUTE_AUDIT_PHASE2_RESULTS.md` is absent at `toolbox-v0.34.1`.

#### **WP-2: API Surface Reduction** - 2026-02-06
Major API cleanup reducing route count by 51% to improve maintainability and startup performance.

**Summary:**
- Routes reduced: 530 → 259 (271 routes removed)
- Routers disabled: 62
- Target <300: Achieved (41 under target)
- Tests: 982 passing, 0 regressions

**Methodology:**
- Grep audit across `packages/client/src/**/*.{ts,vue}` for frontend usage
- Zero-usage routers disabled with `# WP-2 2026-02-06: DISABLED` markers
- Path mismatches identified (e.g., frontend uses `/api/cam/posts` but router exposed `/api/cam/post`)

**Key Disabled Router Groups:**
- RMOS: workflow, profiles, history, AI, feasibility, toolpaths (6 routers)
- Saw Lab: batch sub-routers, debug, compare (8 routers)
- CAM: post processor, smoke tests, backplot, adaptive preview (6 routers)
- Art Studio: rosette patterns v2, preview, feasibility (4 routers)
- Calculators, Jobs, Presets, Governance (12+ routers)

**Documentation:**
- Full audit trail: `services/api/ROUTE_AUDIT_PHASE2_RESULTS.md`
- All disabled routers retain code for future re-enablement

**Compatibility:** No frontend-facing changes. All disabled routes had zero frontend usage.

---

## [toolbox-v0.34.1] - 2026-01-27

### Physics Audit Documentation

#### Docs
- **`docs/PHYSICS_AUDIT_v0.34.md`** — formal audit of all 15 manufacturing physics
  modules

**CAM pipeline (8 modules)** — `energy_model` (SCE × MRR, heat partition),
`feedtime_l3` (jerk-limited S-curve), `adaptive_spiralizer_utils` (Menger curvature),
`trochoid_l3` (G2/G3 arc pair insertion), `whatif_opt` (chipload grid search),
`helical_core` (parametric helix), `cnc_kerf_physics` (small-angle kerf drift),
`time_estimator_v2` (multi-pass cycle time) — all ✓ Correct.

**Saw Lab calculators (7 modules)** — `saw_heat` (1D transient conduction,
Carslaw–Jaeger), `saw_deflection` (Euler–Bernoulli cantilever), `saw_rimspeed`,
`saw_bite_load`, `saw_kickback`, `saw_cutting_force`, `saw_blade_dynamics` (annular
plate vibration modes) — all ✓ Correct.

**Result:** 0 critical errors, 0 blocking issues, 7 conservative approximations (all
safe-side). References: Altintas *Manufacturing Automation*; Tlusty *Manufacturing
Processes*; Sandvik Coromant *Technical Guide*; Carslaw & Jaeger *Conduction of Heat in
Solids*.

---

## [toolbox-v0.34.0] - 2026-01-27

### Physics, Feasibility, Legacy Cleanup, Test Stability

#### Added
- **Saw Lab physics layer** — 7 feasibility calculators (heat, deflection, rim speed,
  bite load, kickback, cutting force, blade dynamics); beam theory for blade deflection;
  thermodynamic heat-buildup model; weighted aggregation via
  `FeasibilityCalculatorBundle`
- **RMOS feasibility rules — 30/30 validation PASSED**
  - Adversarial blocking (F020–F029): excessive DOC in hardwood, tool breakage risk,
    depth exceeds material, zero/negative geometry, missing material, tool larger than
    pocket, chatter/deflection, thermal risk, structural wall failure, combined
    adversarial
  - Edge pressure (F030–F037): near-limit warnings for boundary-pushing scenarios
  - **Zero RED leaks across all 30 validation scenarios**
- **AI advisory integration** — `AiExplainSelectionButton`, `AiAdvisoryPanel`,
  `AiAdvisoryRenderer`; advisory store, context builder, evidence extractors; mock RMOS
  dev server for frontend work
- **Run log audit surface (Wave 22.2)** — flattened append-only audit log for
  manufacturing runs; JSONL (authoritative) + CSV (convenience) export; endpoints for
  latest, `export.csv`, `export.json`, summary, overrides

#### Changed
- **Fret math (PATCH-001)** — explicit 12-TET default plus opt-in `custom_ratios`
  intonation model; named ratio sets (`JUST_MAJOR`, `PYTHAGOREAN`, `MEANTONE`); CAM
  export rejects `ratio_set_id` without explicit per-fret ratios; manufacturability
  validation for all intonation models
- **Vision stack unification** — canonical `app.vision` prompt engine and vocabulary
  endpoints, with backward-compatible re-exports from deprecated paths

#### Removed
- `_experimental/ai_graphics/` deleted — all Layer 1 legacy debt resolved
- Layers 2+3 resolved — compat mounts and redirect routers deleted
- Vision debt lock CI guard added to prevent new legacy imports

#### Tests
- All 8 skipped tests resolved with real implementations
- 2 flaky tests stabilized (subprocess timeout, non-deterministic ordering)
- **Final: 1201 passed, 0 failed, 0 skipped**

---

## [toolbox-mesh-pipeline-v0.1.0] - 2026-01-21

### Mesh Pipeline (Preview)

> Component release on its own tag series, not part of the `toolbox-vX.Y.Z` line.

#### Added
- `services/api/app/mesh/` — mesh healing and topology helpers
- `services/api/app/retopo/` — retopology runner with QRM/MIQ presets
- `services/api/app/fields/` — field analysis utilities
- `presets/retopo/`, `examples/retopo/` — preset configurations and worked examples

#### Contracts
- `qa_core.schema.json` v1.0 — quality assessment coupling mesh healing, thickness,
  grain and brace graph
- `cam_policy.schema.json` v1.0 — per-region manufacturing constraints

Usage: `cd examples/retopo && python -m app.retopo.run --preset qrm intake.obj`

---

## [toolbox-v0.33.0-wave22.1] - 2026-01-21

### Wave 22.1 — Acoustics Ingest Audit

#### Added
- Append-only ingest audit log (accepted / rejected)
- `GET /api/rmos/acoustics/ingest/events`
- `GET /api/rmos/acoustics/ingest/events/{event_id}`
- UI viewer for ingest history

#### Changed
- Import pipeline instrumented to emit audit records

#### Tests
- Acceptance tests added and passing

Finalizes ingest traceability and closes the acoustics validation loop.

---

## [toolbox-v0.32.0] - 2026-01-20

### Art Studio Promotion Contracts & CAM Bridge

**Focus:** Art Studio (Design-First Workflow)  
**Type:** Contract + Orchestration release (non-execution)

#### Added
- Canonical approval-gated PromotionIntentV1 export:
  - `GET /api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json`
- UI-friendly PromotionIntentV1 wrapper:
  - `POST /api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1`
- CAM orchestration bridge:
  - `POST /api/art/design-first-workflow/sessions/{session_id}/promote_to_cam`
- New orchestration artifact:
  - `CamPromotionRequestV1` (idempotent, file-backed persistence)

#### Changed
- Frontend export URL preview updated to canonical design-first workflow route
- Added UI button to copy a full GitHub Actions workflow for export + strict validation
- Added UI button to promote approved intent to a queued CAM request

#### Tests
- Added pytest contract tests enforcing:
  - Approval gating (403 for canonical export when not approved)
  - Strict PromotionIntentV1 shape when approved
  - Wrapper ok/blocked semantics
  - Promotion idempotency (stable request ID)

#### CI / Tooling
- `make api-verify` runs scope checks, boundary checks, and API contract tests
- CI runs `make api-verify` on push/PR

#### Docs
- Updated workflow integration docs with new section describing PromotionIntentV1 → CamPromotionRequestV1 bridge

---

> **Attribution note.** The Saw Lab block below was filed under `[Unreleased]` until
> 2026-08-24. It is in this release: `c35a6936` ("Ship Execution Complete", 2026-01-20)
> is an ancestor of `toolbox-v0.32.0`.

#### **CNC Saw Lab Execution Completion** - 2026-01-19
Completes the CNC Saw Lab execution lifecycle with explicit, auditable terminal states.

**New Endpoint:**
- `POST /api/saw/batch/execution/complete` — Explicit execution closure
- Terminal artifact: `saw_batch_execution_complete`
- Outcomes: `SUCCESS`, `PARTIAL`, `REWORK_REQUIRED`, `SCRAP`
- Optional operator ID and notes captured at completion

**Execution Lifecycle:**
- All execution paths now terminate explicitly and deterministically
- Terminal states: `saw_batch_execution_abort` or `saw_batch_execution_complete`
- Eliminates implicit "success by absence of abort"

**Safety Guardrails:**
- Completion rejected unless:
  - Execution artifact exists
  - Execution not already aborted or completed
  - At least one job log exists
  - Latest job log is not `ABORTED` and shows evidence of work (yield or time)
- Deterministic tie-break when timestamps collide (insertion order)

**Audit & Observability:**
- Every execution ends with a terminal artifact
- Parent/child lineage enforced
- Timelines, dashboards, and audit ZIPs include explicit closure context

**Compatibility:** No schema migrations, no breaking changes, fully backward compatible.

---

## [A_N.1] - 2025-11-20

### ✅ Priority 1 Complete - Production CAM Core

First alpha release candidate with complete foundational CAM capabilities.

**Status:** 100% Priority 1 tasks complete  
**Test Results:** 12/12 CAM Essentials tests passing  
**CI/CD:** GitHub Actions workflows for all Priority 1 features

---

### 🆕 Added

#### **P1.1: Helical Ramping (v16.1)**
- Helical Z-ramping for spiral pocket entry
- 50% tool life improvement vs plunge entry
- 3 ramping strategies: direct plunge, ramped feed, helical spiral
- Configurable pitch (0.5-3.0mm) and feed rates
- Post-processor integration with 5 platforms
- **API**: `/api/cam/toolpath/helical_entry`
- **UI**: Helical Ramp Lab with real-time preview
- **Docs**: `ART_STUDIO_V16_1_HELICAL_INTEGRATION.md`, `ART_STUDIO_V16_1_QUICKREF.md`

#### **P1.2: Polygon Offset (N17)**
- Robust polygon offsetting with pyclipper
- Arc linkers for smooth transitions (G2/G3 commands)
- Island/hole handling with keepout zones
- Min-radius smoothing controls (0.05-1.0mm tolerance)
- Vector normal fallback for simple geometry
- **API**: `/api/cam/offset/plan`, `/api/cam/offset/gcode`, `/api/cam/offset/preview`
- **UI**: Polygon Offset Lab with visual canvas
- **Docs**: `POLYGON_OFFSET_N17_INTEGRATION.md`, `POLYGON_OFFSET_N17_QUICKREF.md`

#### **P1.3: Trochoidal Benchmark (N16)**
- Performance comparison: adaptive vs conventional pocketing
- Real-time metrics: length, time, volume, engagement
- Visual comparison with heatmap overlays
- 15-20% time savings in complex pockets
- **API**: `/api/cam/pocket/benchmark/run`, `/api/cam/pocket/benchmark/compare`
- **UI**: Adaptive Benchmark Lab with side-by-side view
- **Docs**: `TROCHOIDAL_BENCHMARK_N16_COMPLETE.md`, `TROCHOIDAL_BENCHMARK_N16_QUICKREF.md`

#### **P1.4: CAM Essentials Rollup (N0-N10)**

**Roughing (N01)**
- Rectangular pocketing with zigzag patterns
- 5-post processor support (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
- Climb/conventional milling selection
- Real-time statistics (length, area, time, volume)
- **API**: `/api/cam/roughing/plan`, `/api/cam/roughing/gcode`

**Drilling (N06)**
- Modal drilling cycles (G81-G89)
- Supported cycles: G81 (drill), G83 (peck), G73 (chip break), G84 (tap), G85 (bore), G89 (ream)
- Visual hole editor with CSV import
- Dwell time configuration
- **API**: `/api/cam/drilling/plan`, `/api/cam/drilling/gcode`, `/api/cam/drilling/cycles`

**Drill Patterns (N07)**
- Pattern types: grid, circle, line
- Grid: rows × columns with spacing
- Circle: count + radius with optional start angle
- Line: count + length with even spacing
- **API**: `/api/cam/drill/pattern/generate`, `/api/cam/drill/pattern/gcode`

**Retract Patterns (N08)** 🆕
- 3 retract strategies: direct (G0), ramped (G1), helical (G2/G3)
- Simple query-param endpoint for UI integration
- Configurable ramp feed and helix pitch
- **API**: `/api/cam/retract/gcode` (new), `/api/cam/retract/gcode/download`

**Probe Patterns (N09)**
- Corner finding (2-edge, 3-edge, 4-edge)
- Boss/pocket probing (circular features)
- Surface Z measurement (grid or single point)
- G31 probe commands with SVG setup sheets
- Work offset calculations (G54-G59)
- **API**: `/api/cam/probe/generate`, `/api/cam/probe/setup_sheet`, `/api/cam/probe/strategies`

**CAM Essentials Hub (N10)**
- Unified UI in CAMEssentialsLab.vue (699 lines)
- DrillingLab.vue visual hole editor (688 lines)
- Post-processor chooser integration
- Real-time G-code preview
- Multi-post export bundles
- **UI**: Accessible via CAM Tools → CAM Studio Dashboard

#### **Infrastructure**
- GitHub Actions CI for CAM Essentials (`.github/workflows/cam_essentials.yml`)
- PowerShell smoke test suite (`test_cam_essentials_n0_n10.ps1` - 12/12 passing)
- Production-ready multi-post processor system (7 platforms)
- Badge generation for build status

---

### 🔧 Fixed

- **N08 Retract Endpoint**: Added simple `/gcode` POST endpoint matching UI expectations (was returning 404)
- **Test Script**: Updated N08 tests to use correct endpoint with query params (was using wrong endpoint)
- **Scientific Calculator**: Fixed expression overwrite bug preventing addition/multiplication (calculator now functional)
- **Navigation**: Fixed 7-button issue (consolidated to 5 buttons as designed)
- **Router State**: Fixed Guitar Design Tools, Calculators, CNC Business not rendering after navigating to routed views

---

### 📖 Documentation

**New Documents** (A_N.1 Release):
- `P1_4_CAM_ESSENTIALS_PRODUCTION_RELEASE.md` - Production release summary
- `A_N_BUILD_ROADMAP.md` - Updated with Priority 1 complete (100%)
- `README.md` - Updated with A_N.1 features, badges, Quick Start
- `CHANGELOG.md` - This file

**Updated Documents**:
- `CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md` - Full integration details
- `CAM_ESSENTIALS_N0_N10_QUICKREF.md` - API and UI reference
- `CAM_ESSENTIALS_N0_N10_STATUS.md` - Completion metrics

**Testing**:
- `.github/workflows/cam_essentials.yml` - CI workflow (126 lines)
- `test_cam_essentials_n0_n10.ps1` - Smoke tests (12 tests, all passing)

---

### 🎯 Module Status

**Module L: Adaptive Pocketing**
- **L.0**: Core offset engine (legacy)
- **L.1**: Robust pyclipper offsetting + island handling ✅
- **L.2**: True spiralizer + adaptive stepover + min-fillet + HUD ✅
- **L.3**: Trochoidal insertion + jerk-aware time estimation ✅
- **Status**: Production-ready, all versions available

**Module M: Machine Profiles**
- **M.1**: CRUD operations for machine configs ✅
- **M.2**: Learning system for feed optimization ✅
- **M.3**: Real-time feed rate optimizer ✅
- **M.4**: Quick reference and UI integration ✅
- **Status**: Production-ready, 5 platforms supported

**Module N: CAM Operations**
- **N01**: Roughing ✅
- **N06**: Drilling (modal cycles) ✅
- **N07**: Drill patterns ✅
- **N08**: Retract patterns ✅
- **N09**: Probe patterns ✅
- **N10**: CAM Essentials unified hub ✅
- **N16**: Trochoidal benchmark ✅
- **N17**: Polygon offset ✅
- **Status**: N0-N10 production-ready, N16-N17 complete

---

## Unattributed

Entries that shipped but whose release could not be established from the repository's
own history. Recorded here rather than guessed into a version.

> **Superseded 2026-08-24.** Every artifact this entry names is absent from the current
> tree — `docs/B22_16_GOLDEN_REPORT_FUSION.md`, `docs/COMPARELAB_REPORTS.md`,
> `tools/compare_golden_cli.py`, `.github/workflows/comparelab-golden.yml`. The
> workflows were deleted by `f74d4487 chore(ci): remove broken CompareLab workflows`,
> and `CompareLabView.vue` was later decomposed and partly removed. The **Status:
> ✅ … Operational** line below was true when written and is not true now. The entry is
> kept as a historical record; a changelog is not rewritten when the code moves on.

#### **B22.16: Golden + Report Fusion** - 2025-12-03
Complete visual QA pipeline connecting golden baseline validation with automatic HTML report generation.

**Features:**
- Automatic HTML report generation for every golden check (pass or drift)
- Reports include PNG preview, bounding boxes, layer table, full JSON payload
- CI artifact upload for all reports (30-day retention)
- Visual drift diagnosis without local reproduction
- Clear filename pattern: `<left>__vs__<right>__PASS/DRIFT.html`

**Enhanced Components:**
- `tools/compare_golden_cli.py` - Report generation in `check` and `check-all` commands
- `.github/workflows/comparelab-golden.yml` - Artifact upload step
- `docs/COMPARELAB_REPORTS.md` - Golden integration documentation section

**Benefits:**
- ✅ Golden check fails → Operator gets HTML report automatically
- ✅ Visual diff shows exact geometry changes
- ✅ Fast diagnosis from CI artifacts (no local setup needed)
- ✅ Self-contained reports with embedded PNG previews

**Docs:**
- Complete spec: `docs/B22_16_GOLDEN_REPORT_FUSION.md`
- Quick reference: `docs/B22_16_GOLDEN_REPORT_FUSION_QUICKREF.md`

**Status:** ✅ B22.8 → B22.16 Complete - Full CompareLab QA Pipeline Operational

---

## Roadmap — planned, not shipped

> Retained here rather than deleted, but flagged: **a changelog records what shipped, a
> roadmap records what is planned**, and mixing them is what produced the three
> `[Unreleased]` sections this refresh removed. This belongs in a roadmap document;
> the one the Links section used to point at (`A_N_BUILD_ROADMAP.md`) does not exist.
> Nothing below has shipped.

### 🔜 Priority 2 (Design Tools Enhancement)
- **P2.1**: Neck Calculator production-ready (geometry, CNC paths, templates)
- **P2.2**: Bracing Pattern Library (X-bracing, lattice, fan with DXF export)
- **P2.3**: Bridge Calculator enhancement (intonation, saddle compensation, G-code)
- **P2.4**: Hardware Layout Wizard (pickup routing, control cavity)
- **P2.5**: Wiring Workbench (electronics diagrams, cavity planning)
- **P2.6**: Finish Planner (coating schedules, drying times)

### 🔜 Priority 3 (Advanced CAM Features)
- **P3.1**: 3D Surfacing (ball nose, constant Z)
- **P3.2**: Multi-Axis Preview (4-axis rotary, 5-axis simultaneous)
- **P3.3**: Toolpath Optimization (sorting, lead-in/out, collision avoidance)
- **P3.4**: Simulation Engine (material removal, tool visualization)

---

## How this file was reconstructed

Added 2026-08-24. This file is authoritative again, so the claims in it must be
auditable and the next refresh must not have to re-litigate them from scratch. Every
rule below is executable; run it and you should reproduce what is written above.

### Which releases exist

```bash
gh release list --limit 50 --json tagName --jq '.[].tagName'   # published Releases
git tag --list 'toolbox-v*'                                    # tags, superset
```

**A tag is not a release.** `toolbox-v0.32.0` has a tag but no GitHub Release object, so
it never appears in `gh release list`. The "eleven releases were missing" claim means
precisely: every entry in `gh release list` had no matching `## [<tag>]` section here.
Check with:

```bash
for t in $(gh release list --limit 50 --json tagName --jq '.[].tagName'); do
  grep -q "^## \[$t\]" CHANGELOG.md || echo "MISSING: $t"
done
```

### Which entries are reconstructed, and why they say so

Five releases — `v0.35.0`, `v0.36.0`, `v0.36.1`, `v0.37.0`, `v0.38.0`, `v0.39.1` —
published Docker deploy boilerplate as their entire release notes and said nothing about
what changed. Their entries were rebuilt from the commit range between tags:

```bash
gh release view <tag> --json body --jq .body        # is there real content?
git log --no-merges --format='%s' <prev>..<tag>     # what actually landed
git rev-list --count <prev>..<tag>
```

**Rule:** an entry not derived from its own release notes must say so in its own body
text. Do not silently present a reconstruction as a source. Every such entry here carries
a line naming the exact commit range it came from.

### How work is attributed to a release

**Rule: ancestry, never date proximity.** A block is filed under a release only if a
commit that introduces it is provably contained in that tag:

```bash
git merge-base --is-ancestor <commit> <tag>          # is it in?
git cat-file -e <earlier-tag>:<path-it-adds>         # and not in the one before?
```

Worked examples, both re-runnable:

```bash
git merge-base --is-ancestor 57d4ff73 toolbox-v0.35.0     # WP-2 -> v0.35.0
git cat-file -e toolbox-v0.34.1:services/api/ROUTE_AUDIT_PHASE2_RESULTS.md  # absent
git merge-base --is-ancestor c35a6936 toolbox-v0.32.0     # Saw Lab -> v0.32.0
```

**Rule: what cannot be proved goes under `Unattributed`.** It is not dated into a
plausible release. B22.16 is the worked example — see that section.

**Rule: still-unreleased work is proved too, not assumed.** An entry stays in
`[Unreleased]` only if the files it describes postdate the newest tag:

```bash
git log --diff-filter=A --format=%ad --date=short -1 -- <path>
git log -1 --format=%ad --date=short toolbox-v0.39.1
```

### How superseded entries are handled

**Rule: annotate, never delete.** An entry describing work that has since been removed
keeps its text and gains a dated superseded note naming the removing commit. Find one:

```bash
git log --all --oneline --diff-filter=A -- <path-the-entry-names>
git log --all --oneline --grep='<subject>' -i
```

### The `[Unreleased]` counts

```bash
git rev-list --count toolbox-v0.39.1..origin/main
gh pr list --state merged --limit 500 --json mergedAt \
  --jq '[.[] | select(.mergedAt > "2026-02-28")] | length'
```

**Rule: pin counts to a stated commit.** They change whenever `main` does. Re-derive at
the new SHA and restate both the number and the SHA; never carry a number forward.

**Rule: a summary says it is a summary.** Grouping ~1,700 commits by area is the only
honest option at that volume, and the text must say it is representative rather than
exhaustive. **Capability removals are the exception** — they are listed individually, no
matter how large the window, because a summary is unreadable to someone asking "what
will break me".

### Links

```bash
python - <<'PY'
import re, os
s = open('CHANGELOG.md', encoding='utf-8').read()
for m in re.finditer(r'\]\(\./([^)#]+)\)', s):
    print(('OK   ' if os.path.exists(m.group(1)) else 'BROKEN'), m.group(1))
PY
```

This file is **not** in the MkDocs nav, so broken links here do not fail the docs build.
They have to be checked deliberately — three were dead before this refresh.

### Why release entries are not uniformly formatted

Deliberate, not accidental. An entry's shape reflects the evidence behind it: entries
sourced from substantial release notes keep that structure (`Focus`/`Type`, feature
sections); entries rebuilt from commits are terser and carry their range statement;
documentation-only releases have a `Docs` section and nothing else. Flattening them into
one template would make a reconstruction look exactly like a sourced entry, which is the
distinction this file exists to preserve.

### Structural invariants

One `[Unreleased]`, at the top. Releases in reverse-chronological order below it.
Component tags (`toolbox-<component>-vX.Y.Z`) sit in date order alongside the main line
and say which component they belong to. Roadmap material does not live in this file —
a changelog records what shipped.

```bash
python - <<'PY'
s = open('CHANGELOG.md', encoding='utf-8').read()
h2 = [l for l in s.split('\n') if l.startswith('## ')]
print('H2:', len(h2), '| duplicates:', len(h2) - len(set(h2)),
      '| [Unreleased]:', s.count('\n## [Unreleased]'))
PY
```

---

## Versioning

Releases are cut as **Git tags**, and the tag series is the record of what shipped:

- **`toolbox-vX.Y.Z`** — the main application line. Current: `toolbox-v0.39.1`
  (2026-02-28).
- **`toolbox-<component>-vX.Y.Z`** — independently versioned components, e.g.
  `toolbox-mesh-pipeline-v0.1.0`.
- **`A_N.x`** — historical alpha series, superseded by the `toolbox-v` line. Retained
  for the `A_N.1` entry below; not used for new releases.

> **Known inconsistency (2026-08-24).** Five surfaces report five different versions:
> the newest release tag is `toolbox-v0.39.1`; `services/api/app/main.py` and `/health`
> report `2.0.0-clean`; `services/api/pyproject.toml` says `2.0.0`;
> `packages/client/package.json` says `1.0.0`; and the example response in
> `docs/api/endpoints.md` shows `0.33.0`. Nothing reconciles them. Treat the tag series
> as authoritative for *releases* until a single source of truth is chosen.
>
> Tracked as **`VERSION-AUTHORITY-001`** in the `SPRINTS.md` `QUEUED` section, which
> carries the four owner decisions a resolution needs and the order they have to be
> taken in. Any release-automation work should start there rather than aligning a
> surface unilaterally — correcting one surface alone just moves the inconsistency.

---

## Links

- **README**: [README.md](./README.md)
- **Development guide**: [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)
- **API reference**: [docs/api/endpoints.md](./docs/api/endpoints.md) ·
  [overview](./docs/api/overview.md)
- **Project instructions**: [CLAUDE.md](./CLAUDE.md)
- **Governance authority hierarchy**:
  [docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md](./docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md)
- **Migration policy**:
  [FEATURE_PARITY_MIGRATION_POLICY.md](./FEATURE_PARITY_MIGRATION_POLICY.md)

> The previous Links section pointed at `A_N_BUILD_ROADMAP.md`, `ARCHITECTURE.md` and
> `CONTRIBUTING.md`. **None of the three exists**; all were dead links. They are
> replaced above with targets verified present on `main`.

---

**A_N.1 Release Date**: November 20, 2025
**Priority 1 Status**: ✅ 100% Complete (P1.1–P1.4)
**Test Coverage**: 12/12 CAM Essentials tests passing
**Production Ready**: CAM Core, Multi-Post Export, Adaptive Pocketing
