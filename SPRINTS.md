# The Production Shop — Sprint Registry
Last updated: 2026-04-21
Maintained by: Ross Echols (HanzoRazer)

---

## NEXT SESSION OPENS WITH (2026-04-16)

1. **InstrumentBodyGenerator sandbox** — new sprint (dev order written 2026-04-16)
   File: `sandbox/arc_reconstructor/body_contour_solver.py`
   First test case: Cuatro Venezolano Quibor (complete spec available)
   Dev order: `InstrumentBodyGenerator_DevOrder.md`

**Completed this session:**
- Sprint 3 DXF Compliance: `spiral_geometry.py` and `archtop_floating_bridge.py` migrated to dxf_writer.py
- Arc Reconstructor bulge fix: 56.7% arc coverage now working (was 0%)

**Acquisitions pending:**
- Benedetto *Making an Archtop Guitar* (book)
- Epiphone Emperor plans (in mail)

**Physical access pending:**
- 1941 Gibson L-37 — requires deflection jig build first

---

## ACTIVE

### Sprint 1 — Vectorizer Reconciliation
**Status:** COMPLETE — all phases done
**Branch:** main

| Phase | Description | Commit | Status |
|-------|-------------|--------|--------|
| 1 | Raw mode restoration — `--raw` flag, CHAIN_APPROX_NONE, CONTOURS layer, R12 | 04735bd4 | ✅ Done |
| 2 | Classification layer fixes — jack route guard, body size ceiling, solidity scoring, instrument detector | 72bfffc9 | ✅ Done |
| 3 | BlueprintAnalyzer wire-in — scale pre-pass, async wrapper, DPI fallback | 059cf5b0 | ✅ Done |
| 4 | Docker fix — raw mode → production | a76102c2 | ✅ Done |
| 4b | Docker deploy hardening (2026-04-05) | 5a145e90 | ✅ Done |
| 4c | Docker Trixie + Railway PORT (2026-04-06) | ebffbd53 | ✅ Done |
| 5 | Classified mode root cause fixes (4/5) | 722cc03d | ✅ Done |
| 5F | Scale correction propagation | — | ✅ Done |
| 5G | Body contour height ceiling | cb0761ed | ✅ Done |

**Vectorizer ceiling declared (2026-04-16) — REVERSED (2026-04-20):**
~~Blueprint vectorizer produces 82-88% complete outlines consistently on clean
engineering drawings. This is the practical ceiling of the current technology.~~
**Ceiling reversed:** Commit `3db07c62` restored morphological gap closing capability
that was missing from enhanced mode. Benchmark output exceeded March 6 baseline.
The ceiling was an artifact of missing capability, not a fundamental limit.
Blueprint vectorizer v3.6 is the primary extraction path. InstrumentBodyGenerator
remains a parallel effort for body completion from partial outlines.
Photo vectorizer (Sprint 4 items) remains set aside — poor results on L-1 images
and AI renders.

**Phase 5F — Scale correction propagation (2026-04-05):**
Confirmed working. Correction factor from `validate_scale_before_export()`
propagates correctly to `export_to_dxf()`.
- Dreadnought: 4.4% W, 4.8% L — **PASS** (within ±20%)

**Phase 5G — Body contour height ceiling (2026-04-05):**
Commit `cb0761ed` — height ceiling validation in rerank_body_candidates():
- Add spec_name parameter through call chain
- Add cuatro_puertorriqueno spec to INSTRUMENT_SPECS
- Reject candidates where height > 1.5× max_expected_height
- Loop to next candidate on rejection

Quality scorecard (3/3 PASS):
- Dreadnought: W=7.1%, H=2.5% ✅
- Les Paul: W=16.5%, H=19.7% ✅ (was 28.6% H error)
- Cuatro: W=2.6%, H=2.6% ✅ (was 33.3% H error)

---

### Sprint 2 — Repo Split and Standalone Products
**Status:** In progress
**Branch:** main

**Standalone repo inventory (all created on GitHub):**

| Repo | Description | Status |
|------|-------------|--------|
| HanzoRazer/ltb-rosette-designer | Rosette Designer — full UI, BOM engine, 8 presets, Manufacturing Intelligence, Amsterdam/Spiro engine | **LIVE** |
| HanzoRazer/ltb-acoustic-design-studio | Helmholtz + Gore P:A calculator + soundhole geometry designer | Empty — needs content |
| HanzoRazer/ltb-bridge-designer | Bridge geometry + string spacing | POPULATED — commit `55c17a6` |
| HanzoRazer/ltb-fingerboard-designer | Scale length, radius, multiscale | Existing — needs audit |
| HanzoRazer/ltb-headstock-designer | Tuner layout, headstock templates | Existing — needs audit |
| HanzoRazer/ltb-neck-designer | Neck profiles, tapers | Existing — needs audit |
| HanzoRazer/ltb-parametric-guitar | Body shape generator | Existing — needs audit |
| HanzoRazer/ltb-woodworking-studio | Joinery, wood movement, bench woodworking | woodworking_v2 committed |
| HanzoRazer/ltb-express | String tension calculator + quick tools | **CONTAMINATED** — needs cleanup |
| HanzoRazer/blueprint-reader | PDF → DXF pipeline (vectorizer) | Deployed to Hostinger |

**Open items:**
- [ ] Install ODA File Converter locally — batch convert DWG inventory:
      59_Flying_V.dwg, Flying_V_11.dwg, Classical-02-MM.dwg,
      DWG-00/01/02/03-Gibson-SG.dwg, Acoustic Guitar Neck Profiles DWGs
- [ ] Fix flying_v_1958.json schema mismatch with loader.py (committed 9cdad75b)
      load_model_spec("flying_v_1958") crashes on KeyError "scale"
- [ ] Fix instrument_model_registry.json phantom entry: flying_v points to
      specs/gibson_flying_v_1958.json which does not exist
- [ ] Create docs/VECTORIZER_ACCURACY.md (technical disclaimer)
- [ ] Add accuracy summary to README.md and blueprint-reader landing page
- [ ] Sync blueprint-reader with Sprint 1 Phase 1-3 commits
- [ ] Clean ltb-express (contamination)
- [ ] Define publish workflow for remaining standalone repos
- [ ] Digitize 12-string dreadnought plans via blueprint-reader.html
- [ ] Emperor plans — digitize on receipt

---

### Sprint 3 — Remediation and Gap Closure
**Status:** In progress
**Branch:** main

**Task list:**
- [x] Build dxf_writer.py — central DXF writer enforcing R12, sentinel EXTMIN/EXTMAX,
      ≤3dp coordinates, no LWPOLYLINE. Commit 4c4f1a52. Blocks all new DXF generators.
- [x] Fix PatternRenderer import error in production (commit a7f0f614)
- [x] Fix FastAPI regex deprecation warning — pattern= replacement (commit 131b1cfd)
- [x] Add WeasyPrint dependencies to Docker — PDF export (commit ff958c9a)
- [x] Migrate spiral_geometry.py to dxf_writer.py (2026-04-16)
- [x] Migrate archtop_floating_bridge.py to dxf_writer.py (2026-04-16)
- [ ] Migrate curve_export_router.py to dxf_writer.py
- [ ] Fix 13 pre-existing test failures (10 soundhole spiral Python 3.14/ezdxf,
      2 debt gate ratchet, 1 vision integration)
- [ ] Resolve 8 gaps awaiting physical measurements
- [ ] Text-masking preprocessing pass for blueprint vectorizer (2026-04-20)
      **Context:** Multi-scale Canny + 7px morphological closing (commit 3db07c62)
      restores geometry extraction but degrades text quality. A 7×7 kernel applied
      to text glyphs bridges strokes and fills counters, producing solid blobs
      that fail size filters or merge with adjacent geometry.
      **Solution:** Text-detection pass before edge extraction that masks text
      regions, allowing gap closing to run on geometry only. Text extracted
      separately with no closing or smaller kernel.
      **Diagnostic data:** gap_close_size=0 produces 435K entities (text present
      but fragmented); gap_close_size=7 produces 204K (text merged/missing).
      **Note:** This does not regress text quality relative to pre-fix enhanced
      mode — both had poor text output. Geometry restoration was the priority.

**DXF Compliance status (from REPO_DATA_AUDIT.json 2026-04-16):**

| Priority | File | Format | Reason |
|----------|------|--------|--------|
| 1 — BLOCKING | `soundhole/spiral_geometry.py` | R2000 | CLAUDE.md blocking |
| 2 — BLOCKING | `bridge/archtop_floating_bridge.py` | R2000 | CLAUDE.md blocking |
| 3 | `headstock/dxf_export.py` | R2010 | User-facing export |
| 3 | `blueprint_cam/dxf_preprocessor.py` | R2000 | Active vectorizer pipeline |
| 3 | `blueprint_cam/contour_reconstruction.py` | R2000 | Active vectorizer pipeline |
| 4 | `body/smart_guitar_dxf.py` | R2000 | Smart Guitar export |
| 4 | `neck/headstock_transition_export.py` | R2010 | Manifest registered |
| 4 | `neck/neck_profile_export.py` | R2010 | Manifest registered |
| 5 | `archtop/archtop_contour_generator.py` | R2010 | Archtop CAM |
| 5 | `cam/archtop_bridge_generator.py` | R2010 | Archtop CAM |
| 5 | `cam/archtop_saddle_generator.py` | R2010 | Archtop CAM |

---

### Sprint 4 — Photo Vectorizer Production Readiness
**Status:** In Progress — PARTIALLY SUSPENDED

**Completed:**
- [x] spec_name wire-up: VectorizeRequest → PhotoVectorizerV2.extract() (5de45310)
- [x] Auto-rotate for AI images (d45e213a)
- [x] Dimension swap fix (d45e213a)
- [x] AI pipeline validated across 4 specs
- [x] Unknown instrument test (Gibson EDS-1275)

**Suspended (2026-04-16):**
Photo vectorizer on L-1 historical images and AI renders produced poor results.
Photo vectorizer is set aside. InstrumentBodyGenerator is the forward path
for outline completion from partial vectorizer output.

**Remaining (if resumed):**
- [ ] Body isolation filter (SVG shows 4 paths, should be 1)
- [ ] Scale output discrepancy (SVG canvas 1087×949mm vs spec 368×444mm)
- [ ] Neck crop pre-processor
- [ ] INSTRUMENT_CATALOG Tier 1 integration

---

### Sprint 5 — Scale Validation Gate + Curvature Profiler
**Status:** COMPLETE (2026-04-16)
**Commits:** db713cc7, 3b18e852 (gap join), plus scale gate sprint

**Delivered:**
- Scale validation gate: blocks DXF export when dimensions fail spec check
- Gap join thresholds raised: max_gap_mm 2.0→4.0, scale_factor_limit 3.0→4.0
- instrument_specs.py: single source of truth (18 specs + features)
- curvature_correction.py: MEASURED_RADII consolidated
- body_curvature_correction.py → instrument_geometry/curvature_correction.py (moved)
- DEV_GUARDRAILS.md: live-path verification checklist (3 locations)

**Benchmark results:**
- Melody Maker: 9.6-9.8/10 PRODUCTION_READY ✅
- Dreadnought: 8.0-8.5/10 USABLE ✅
- OM: 7.8-8.2/10 (slight regression from 2.49mm join — upstream issue)

**Known issues:**
- OM join at 2.49mm: BODY-to-BODY join confirmed legitimate but
  quality dropped — upstream issue not gap joiner
- OutlineReconstructor inserted into dead code path (_clean_blueprint_restored_baseline)
  instead of production path (_clean_blueprint_refined) — never executed

---

### Sprint 6 — Arc Reconstructor Sandbox
**Status:** IN PROGRESS
**Location:** sandbox/arc_reconstructor/
**SESSION_AUDITS.md:** Active audit log in sandbox

**Files:**
```
sandbox/arc_reconstructor/
├── arc_reconstructor.py           — Tier 0-3 gap bridging + LWPOLYLINE bulge output
├── reference_outline_bridge.py    — Tier 0: reference geometry from body_outlines.json
├── SESSION_AUDITS.md              — append each session
└── results/
    ├── dreadnought_phase5b_tier0.dxf
    └── dreadnought_phase5b_tier0_final.dxf
```

**Tier priority chain:**
| Tier | Method | Condition |
|------|--------|-----------|
| 0 | Reference outline from body_outlines.json | gap endpoints < 50mm from aligned reference |
| 1 | Measured radius from adjacent chain | adjacent chain measurable |
| 2 | Spherical arch formula | arch_radius_mm provided |
| 3 | Zone lookup table | fallback |

**Benchmark results (dreadnought_phase5b_tier0_final.dxf):**
- 17/18 chains closed (94.4%)
- Full width coverage: w=1166mm h=779mm (100%)
- Arc segments: 56.7% (fixed 2026-04-16)
- One remaining open chain: 80.6mm gap on 86mm chain (leave open — gap IS the chain)

**Completed:**
- [x] Fix bulge values not writing to POLYLINE vertices (2026-04-16)
      Added calculate_bulge(), promote_chain_to_arcs(), chains_to_dxf(promote_arcs=True)
      Result: 56.7% arc coverage, 1387 vertices with bulge values

**Open items:**
- [ ] Visual validation: open tier0_final.dxf in Fusion 360
      confirm arc smoothness vs LINE baseline
- [ ] Complete SESSION_AUDITS.md entry for tier0 final work

**Architecture decision:**
System 1 (existing pipeline) → LINE entity DXF output
System 2 (arc_reconstructor sandbox) → LWPOLYLINE with bulge → "Promote to CAD"
"Promote to CAD" is a paid tier feature — optional, on-demand, never modifies System 1.

---

### Sprint 7 — Repository Data Audit
**Status:** COMPLETE (2026-04-16)
**Output:** docs/REPO_DATA_AUDIT.json (1329 lines)

**Summary:**
| Metric | Value |
|--------|-------|
| Files scanned | 1,847 |
| Instruments with complete E2E pipeline | 3 (stratocaster, les_paul, dreadnought) |
| Instruments with partial pipeline | 8 |
| Instruments stub only | 6 |
| Missing entirely | 1 (EDS-1275) |
| Orphaned data files | 12 |
| Phantom assets | 8 |
| DXF compliant files | 6/30 (20%) |
| Standalone features integrated | 3/6 |
| GEN phases complete | 2/6 (GEN-3, GEN-6) |

**Top 5 gaps:**
1. DXF Writer bypass — 12 production files use ezdxf.new() directly
2. GEN-5 fragmentation — 19 MODEL_SPECS vs 31 registry entries, no single source of truth
3. EDS-1275 — zero data, no generator, no endpoint
4. GEN-1 — POST /api/projects seeding not implemented
5. 8 partial pipeline instruments missing body generators or untested G-code

**Consolidation targets identified:**
1. Five flat registries → one instrument_library.json (three-level hierarchy)
2. Cuatro 8 regional traditions → 8 separate MODELS within Latin American family
3. Rosette + soundhole + Gore/Helmholtz → one acoustic design calculator suite
4. Three neck export files → one module with mode parameter
5. Nine stale docs → docs/archive/

---

### Sprint 7.5 — Supersession and Orphan Audit
**Status:** COMPLETE (2026-04-21)
**Output:** docs/audits/SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS.md

**Summary:**
| Category | Count |
|----------|-------|
| Items classified | 55 |
| Survivors (Library + Distinct) | 33 |
| Deletion candidates (Superseded + Orphaned) | 21 |
| Duplicate groups | 3 |

**Key findings:**
1. `inverse_solver.py` confirmed **Library** (not orphaned) — imported by brace_prescription.py
2. Photo vectorizer (18 files) confirmed **Superseded** — Sprint 4 suspension formal
3. `TrainingDataCollector` confirmed **Orphaned** — defined but never instantiated
4. `validate_scale_before_export` is **Duplicate** — exists in vectorizer_phase3.py and scale_validation.py
5. Registry intersection table produced — 10 instruments canonical (in all 3 main registries)

**Deliverables:**
- `docs/audits/SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS.md` — Full classification matrix
- `docs/audits/audit_survivors.txt` — 33 files confirmed active
- `docs/audits/audit_deletion_candidates.txt` — 21 files for review
- `docs/audits/audit_duplicate_pairs.txt` — 3 consolidation targets

**Unblocks:**
- GEN-5 Data Consolidation (intersection table ready)
- Sprint 3 DXF Compliance (confirms 12 production files, 6 sandbox)
- Repo split work (photo-vectorizer can archive)
- Library extraction (inverse_solver confirmed foundational)

---

### Sprint 8 — Instrument Library JSON Population
**Status:** IN PROGRESS (2026-04-16)
**Location:** docs/instrument_library/ (proposed)
**Current output:** JSON files extracted from uploaded plans

**Three-level hierarchy defined:**
```
FAMILY → MODEL → VARIANT
```

**Files produced this session:**
| File | Status | Source | Completeness |
|------|--------|--------|--------------|
| cuatro_instrument_library.json | Complete | El_Cuatro_1-8.pdf + cuatro_puertorriqueño.pdf | Venezuelan: COMPLETE, PR: PARTIAL |
| gibson_l0_spec.json | Complete | Gibson-L0-IN.pdf | COMPLETE spec, body outline pending Fusion 360 |
| acoustic_00_spec.json | Complete | Acoustic_guitar_00.dxf + pdf | COMPLETE |
| om_acoustic_spec.json | Complete | OM_acoustic_guitar.dxf + pdf | COMPLETE |
| selmer_maccaferri_d_hole_spec.json | Complete | Selmer-Maccaferri-D-hole-MM-01/02.pdf | COMPLETE spec, body outline pending |
| jumbo_fesselier_spec.json | Complete | Guitar-Jumbo-MM-A0/A4.pdf (18 pages) | COMPLETE |

**Instrument hierarchy defined (session 2026-04-16):**
Families established:
- Electric Solid Body (Les Paul, Stratocaster, Telecaster, SG, Explorer, Flying V, Melody Maker, ES-335, EDS-1275, Smart Guitar)
- Electric Semi-Hollow (ES-335, EDS-1275)
- Acoustic Flat Top (Dreadnought 3 variants, OM/000, Jumbo, Classical, J-45, Gibson L-0, L-1)
- Acoustic Archtop (Benedetto 17", Jumbo Archtop, Selmer-Maccaferri)
- Gypsy Jazz (Selmer-Maccaferri D-hole, O-hole)
- Latin American (10 Cuatro regional traditions — 2 documented, 8 pending)
- Smart Guitar (Production headless, Pro headless tremolo, Standard future)

**Open items:**
- [ ] Migrate JSON files to app/instrument_geometry/models/
- [ ] Replace existing cuatro_venezolano.json (scale 420mm is wrong — use 556.5mm from IMCUA 000)
- [ ] Add back_arch_radius_mm to acoustic specs in instrument_specs.py
- [ ] Split cuatro_instrument_library.json into two files:
      cuatro_venezolano_spec.json + cuatro_puertorriqueno_spec.json
- [ ] Create instrument_families.json as family metadata reference
- [ ] Create latin_american_family_overview.json with 8 pending model stubs documented
- [ ] Add cuatro_venezolano.py and cuatro_puertorriqueno.py to guitars/ module
- [ ] Body outline tracing in Fusion 360 for: Gibson L-0, Selmer-Maccaferri, Jumbo Fesselier
- [ ] Remaining 247 plans from 257-plan corpus — populate as acquired
- [ ] Gibson L-1: plans not available — defer to BodyContourSolver reconstruction

**Key decisions:**
- Plans are measurement sessions, not tracing targets
- Luthier will manually trace clean CAD outlines in Fusion 360 from plans
- Vectorizer is the onramp for unknown instruments without clean plans
- BodyContourSolver is the completion engine for all paths

---

### Sprint 9 — InstrumentBodyGenerator
**Status:** PLANNED (dev order written 2026-04-16)
**Location:** sandbox/arc_reconstructor/ (extend existing sandbox)

**Vision:**
Takes 82-88% complete vectorizer output and completes the body outline
mathematically from known instrument geometry constraints. After learning
from 275 open-source plans, can complete any common guitar design from
partial outline + a few known dimensional anchors.

**Architecture:**
```
Vectorizer output (82-88% complete)
    ↓
ConstraintExtractor — identifies landmark points in partial outline
    ↓
BodyContourSolver — completes outline from constraints + Sevy formula
    ↓
Complete parametric body model
    ↓
Soundhole Generator → Helmholtz Calculator → complete acoustic design
```

**Core math:**
- Woodworker's radius formula: R = (C²/8S) + (S/2)
- Sevy/Mottola side height: H = (B+(R-√(R²-P²)))-(R-√(R²-D²))-(M+N)
- High point: P = (L/2) - (E/2)√((4R²)/(L²+E²) - 1)
- body_side_arc_solver.py already implements falloff() and H formula

**Product tier:**
- Free tier: Vectorizer → 82-88% complete DXF → download
- Paid tier: Vectorizer → InstrumentBodyGenerator → complete outline
  → Soundhole Generator → Helmholtz Calculator → production templates
- "Promote to CAD" button is the entry point for paid tier

**Instrument classification:**
- Auto-classify from partial outline geometry (lower/upper bout ratio, waist_y_norm)
- Luthier confirms or overrides — always has final say
- Smart Guitar and cross-genre instruments: returns confidence + alternatives
- Override any solved dimension → system recalculates dependent geometry

**Dev order:** See separate InstrumentBodyGenerator Dev Order document (2026-04-16)

---

## QUEUED

### Sprint: tap_tone_pi Real-Time Plate Tuning Mode
**Status:** QUEUED
**Priority:** HIGH

**Target workflow:**
- Speaker excites plate continuously
- Pi captures two-channel transfer function
- Real-time FFT displays on screen
- Luthier removes wood from brace → watches peak shift in real time
- Before/after overlay shows delta
- Wolf severity indicator goes green

**Required additions:**
- Continuous excitation mode (Phase 2 architecture)
- Real-time H(f) display at 4-10 Hz refresh
- Peak tracker with musical note labels
- Before/after freeze overlay (one button)
- Wolf severity indicator live (WSI module wired)

**Hardware:** No new hardware needed — add small speaker + amp (~$30)

---

### Sprint: tap_tone_pi Mass-Frequency Tracking
**Status:** QUEUED
**Priority:** HIGH

**Workflow:**
- Sequential sessions on same instrument
- Weight recorded at each session
- Modal frequencies extracted per session

**Calculations:**
- dF/dM per mode per brace location
- Linear predictor: ΔM needed to reach target Hz
- Polynomial fit at 3+ points for nonlinear range

**Closes:** Cross-session comparison open item
**Connects:** archtop_stiffness_map.py validation

---

### Sprint: tap_tone_pi Reference Overlay
**Status:** QUEUED
**Priority:** MEDIUM

**Purpose:**
- Load reference plate from instrument database
- Overlay reference modal peaks on FFT display
- Delta display: measured vs reference per mode
- Feed delta to luthiers-toolbox inverse solver

**Database sources:**
- D'Aquisto measurements (in repo)
- Future: L-37 physical measurements
- Future: Benedetto graduation data

---

### Sprint: LUTHERIE_MATH.md Completion
**Status:** QUEUED
**Priority:** Medium

**Document:** docs/LUTHERIE_MATH.md (1,160 lines, 25 sections complete)

**Missing sections (10):**
27. Break Angle Geometry
28. Fan Fret Scale Length Interpolation
29. Compound Radius Mathematics
30. Binding Channel Geometry
31. Bridge Saddle Compensation (full derivation)
32. Brace E×I Flexural Rigidity
33. Rayleigh-Ritz Variational Solver (full)
34. Wood Movement / Moisture Coefficient Math
35. Spiral Soundhole Geometry
36. Floyd Rose Geometry

**Acceptance criteria:** All 10 sections with formula, variable definitions,
source citation, conditions, edge cases, implementation reference.
Document ready for external peer review.

**Peer review targets:**
- University of New South Wales musical acoustics program
- Trevor Gore / Gore & Gilet forum
- Liutalab development team

---

### Sprint: Archtop Free Tier Phase 1
**Status:** QUEUED

**Task list:**
- [ ] Re-upload 3 missing archtop scripts:
      archtop_stiffness_map.py, archtop_surface_tools.py, archtop_modal_analysis.py
      → commit to services/api/app/cam/archtop/
- [ ] Wire daquisto_measurements.json into pipeline
- [ ] Add API endpoints:
      POST /api/archtop/contours
      POST /api/archtop/stiffness_map
      POST /api/archtop/modal_analysis

---

### Sprint: GEN-5 Data Consolidation
**Status:** QUEUED
**Priority:** HIGH — blocks all instrument library work

**Problem:** Five conflicting flat registries with no single source of truth:
- guitars/__init__.py MODEL_SPECS: 19 entries
- instrument_model_registry.json: 31 entries
- body_dimension_reference.json: 18 entries
- body_templates.json: partial
- catalog.json: 23 entries

**Target:** One canonical instrument_library.json (three-level: family → model → variant)
All five registries read from this single source.

**Blocking:** All instrument library JSON work from Sprint 8 needs a home.

---

### Sprint: GEN-1 Project Seeding
**Status:** QUEUED

POST /api/projects does not seed with model_id defaults.
Projects created without instrument-specific configuration.
Every instrument project starts blank — builder re-enters spec data every session.

---

## TECH DEBT

| Item | Location | Description | Merge Target |
|------|----------|-------------|--------------|
| Bi-arc joining math | `docs/reference/curvature_correction_unmerged.py` | 467 lines of gap-correction math, chord/sagitta utilities, detailed MEASURED_RADII with derivation notes. Not integrated into services/api version. | `services/api/app/instrument_geometry/curvature_correction.py` |

---

## COMPLETED

### Sprint 1 Phases 1-3 — Vectorizer Reconciliation
Completed: 2026-04-04
Commits: 04735bd4, 72bfffc9, 059cf5b0

---

## ARCHITECTURAL DECISIONS LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-04 | R12 (AC1009) is project-wide DXF standard | CAM compatibility, Fusion 360 freeze prevention |
| 2026-04-04 | dxf_writer.py blocks all new DXF generators | Central enforcement of R12 standards |
| 2026-04-04 | BlueprintAnalyzer uses in-memory PNG from PDF rasterization | No dual upload required |
| 2026-04-04 | Standalone repos are a moat, not a code split | Free tools protect integrated product |
| 2026-04-04 | ltb-woodworking-studio is canonical woodworking module | instrument geometry never goes there |
| 2026-04-04 | Instrument catalog uses tiered schema | Tier 1: validated, Tier 2: community, Tier 3: ethno |
| 2026-04-04 | ltb-acoustic-design-studio combines Helmholtz + soundhole designer | Physics-to-geometry pipeline is the product |
| 2026-04-05 | Refactor when already in a file, not for refactoring's sake | Bulk refactoring breaks working code |
| 2026-04-06 | Brand manifesto committed as founding document | docs/MANIFESTO.md (049603ac) |
| 2026-04-07 | Strict endpoint separation: blueprint vs photo-vectorizer | Never route photos to blueprint endpoint |
| 2026-04-16 | Blueprint vectorizer ceiling declared at 82-88% | Photo vectorizer set aside — poor results on L-1 images and AI renders |
| 2026-04-16 | System 1 (vectorizer) / System 2 (arc promotion) separation | System 1 never modified — System 2 is additive post-processing |
| 2026-04-16 | "Promote to CAD" is paid tier entry point | Free: vectorizer DXF. Paid: InstrumentBodyGenerator + design suite |
| 2026-04-16 | InstrumentBodyGenerator uses constraint solver not tracing | 5-11 landmark points + math > thousands of line segments |
| 2026-04-16 | 275 plans are measurement sessions not tracing targets | Each plan populates known points for constraint solver |
| 2026-04-16 | Instrument library: three-level hierarchy (family → model → variant) | Flat registries cannot represent regional cuatro traditions or year variants |
| 2026-04-16 | Cuatro: 8 regional traditions = 8 separate MODELS in Latin American family | Venezolano and Puertorriqueño are not variants of each other |
| 2026-04-16 | cuatro_venezolano.json scale 420mm is wrong | Correct scale: 556.5mm from IMCUA 000 Quibor engineering drawings |
| 2026-04-16 | DEV_GUARDRAILS.md mandatory live-path verification | Prevents features landing in non-production code paths |
| 2026-04-16 | OutlineReconstructor was inserted into dead code path | Lesson: always verify router→orchestrator→mode→cleaner before writing code |
| 2026-04-20 | Blueprint vectorizer ceiling declaration (2026-04-16) reversed | v3.6 restored morphological gap closing from vectorizer_phase2.py (commit 3db07c62). Benchmark exceeded March 6 baseline (cuatro: 21MB/204K entities vs 16MB/128K). Ceiling was artifact of missing capability, not fundamental limit. Forward path: blueprint vectorizer v3.6 primary; InstrumentBodyGenerator parallel effort for body completion from partial outlines, not exclusive forward path. |
