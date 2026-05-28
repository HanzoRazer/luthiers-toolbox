# The Production Shop — Sprint Registry
Last updated: 2026-05-26
Maintained by: Ross Echols (HanzoRazer)
Maintenance discipline: docs/SPRINTS_MAINTENANCE.md

**Deferred maintenance depository:** Intentional hold-outs (held out of a merge, infra/process deferrals, known-incomplete routes) are registered in **[DEFERRED MAINTENANCE](#deferred-maintenance)** below — not in orphan docs. Held out of a PR is fine; untracked is not.

---

## NEXT SESSION OPENS WITH (2026-05-26)

**PR #45 and #46 merged to `main`.**

**CAM Intent (H7) — CLOSED on `main` (PR #46).** Routers deleted in `545fccad` recovered; frontend 404s on normalize + roughing intent resolved. Blocking CI guard: `check_execution_class_compliance.py`. Live smoke: `python scripts/dev/verify_cam_intent_live.py` (API must be running).

**IBG Provenance R2 — on `main` (PR #45).** Export fail-closed until R1 governance ratification — scheduling question, not engineering.

**MVP bar:** Design → platform → G-code → cut on BCAM 2030CA. No test suite substitutes for this.

**Tracked deferral (not omitted):** `ART-STUDIO-DEFER-001` — see [DEFERRED MAINTENANCE](#deferred-maintenance).

---

## NEXT SESSION OPENS WITH (2026-05-02) — superseded

**Sprint FRET-CONSOLIDATION-1 complete** — CAM toolpath generation now consumes FretboardEcosphere as canonical source. No more duplicate fret math.

**Engineer at rest after data integrity and consolidation sprints.** No active work in flight.

**Shop setup is the gating critical path** — clearout target 2026-05-15, lab rig fabrication start ~2026-07.

**CAD work on Smart Guitar in parallel** (romantic route chosen; Fusion 360 license renewed).

**Completed 2026-04-30 through 2026-05-02:**
- Sprint M1 wood shrinkage data integrity remediation (commits 37f29bc6, 477758eb)
- Sprint M2 silent fallback elimination across 6 files (commit 477758eb)
- Sprint NDS Phase 1+1.5 foundation (commits 9d37f1ea, d72d9744, e260f365, ac96430f)
- Sprint NDS Phase 2 router and endpoints (commits 4f8a3209, ab1ed8a2, 6b719fc3) — delivered as FRET-A Phase 2
- Sprint FRET-CONSOLIDATION-1 CAM-consumes-ecosphere (commits e4220537, fa009184)
- African Padauk wood_species.json entry update (Janka correction, shrinkage values, CITES warning)
- Data file sync boundary documented (wood_species.json vs luthier_tonewood_reference.json)
- Sprint M4 queued: MOE data gaps (spruce_sitka, spruce_engelmann, douglas_fir)

**Pending pickup when bandwidth allows:**
- Sprint M2.5 — Deferred silent fallback cleanup (4 items)
- Sprint M3a — CITES lookup tool
- Sprint M5 — CIRAD Reference Database API (expose 34K specimens + density data)
- Sprint M6 — Unfinished Work Audit (BOE, IBG, stale sprints, sandboxed experiments)
- Active Inventory Species Audit (Padauk as template)

**Strategy update (2026-05-02):** Single-property marketing strategy supersedes standalone-repos-as-moat. All standalone repos except ltb-woodworking-studio collapse back to luthiers-toolbox. Privatization of all standalone repos in flight as separate operational task.

---

**Sprint 3 — REOPENED (2026-04-26)**

Sprint 3 verification audit (docs/audit/sprints_md_verification_2026-04-25.md) found:
- **2/12 DXF generators actually migrated** — 10 false claims identified
- **BOE backend endpoint does not exist** — documented but never implemented
- Sprint 3 "CLOSED" status was based on false completion claims

**Corrections applied:**
- 10 files marked NOT MIGRATED in DXF Compliance table
- BOE endpoint marked MISSING — resolution TBD
- Sprint status changed to REOPENED
- See docs/audit/sprints_md_verification_2026-04-25.md for full verification

**Remaining Sprint 3 work:**
- 10 DXF migrations scheduled in Sprint 3B PR 2B
- BOE endpoint: implement, remove claim, or identify alternate (decision pending)

**Next sprint candidates (Ross to direct):**
1. BOE v3.7 — Refine Curves (scope doc: BOE_v3_7_REFINE_CURVES_SPRINT.md)
2. Calculator module separation (Ross's December 2025 pre-ship TODO)
3. BOE v3.8 — Stylus input support (noted, not yet scoped)
4. Sprint 3B PR 2B — DXF migration completion (10 files scheduled, see DXF Compliance table below)
5. BOE STEM Grid Restoration — Restore STEM grid coordinate system for cavity validation
6. Constructive Proportional Design System — Zone-based geometry primitives for parametric instruments
7. Body Cutaway Designer — Cutaway shape generation (coordinates with #6 for zone placement)
8. Bevel Cut Calc Module — Edge bevel calculations for body contouring

**Sprint candidates from Instrument Model Coverage Audit (2026-04-26):**
Reference: docs/audit/instrument_model_coverage_2026-04-26.md

9. End-to-End Instrument Completion — Stratocaster (CLOSEST TO COMPLETE)
   - Gap: Contour carving CAM (belly cut, arm contour) missing
   - Investigation needed: Is contour carving instrument-specific or reusable infrastructure 
     that would also unlock Telecaster, Les Paul variants, etc.?
   - Status: SCOPABLE (~2 sprints)
   - Audience: Customer-facing

10. End-to-End Instrument Completion — Telecaster
    - Gap: Dedicated router missing (single-coil + bridge plate routing)
    - May benefit from Stratocaster contour carving work if shared infrastructure
    - Status: SCOPABLE (~1 sprint)
    - Audience: Customer-facing

11. End-to-End Instrument Completion — Flying V
    - Gap: pocket_generator.py exists but not wired to router
    - Smaller scope than Strat/Tele — wiring rather than building
    - Status: SCOPABLE (~1 sprint)
    - Audience: Customer-facing

12. Feature Route Sprint A: EXPLICIT Plan Data Extraction (~40% of plans)
    - Gap: Many plans have labeled cavity dimensions but no extraction pipeline
    - Sample analysis: Gibson 335, Carlos Jumbo have explicit pickup/control cavity labels
    - Work: OCR + template matching to extract labeled dimensions from PDFs
    - Coordinates with: Blueprint import pipeline, vectorizer feedback loops
    - Status: SCOPABLE (~1 sprint)
    - Audience: Customer-facing

13. Feature Route Sprint B: Cavity Measurement Workflow (~50% of plans)
    - Gap: Plans show cavities at scale but without labels — requires measurement
    - Sample analysis: Gibson Flying V, Fender Strat show cavities but no dimensions
    - Work: Interactive measurement UI or automated contour extraction with scale reference
    - Architecture decision: measurement UI vs automated extraction vs hybrid
    - Coordinates with: #12 (can share extraction pipeline), Body Outline Editor measurement tools
    - Status: NEEDS ARCHITECTURE DECISION before scoping
    - Audience: Customer-facing

14. Feature Route Sprint C: Standards Library (~10% of plans)
    - Gap: Some plans omit cavities entirely — need industry standard dimensions
    - Sample analysis: Cuatro puertoriqueño has no cavity definitions
    - Work: Curated library of standard pickup/control cavity dimensions by type
    - Data sources: Manufacturer specs, StewMac/LMII templates, community measurements
    - Lightweight: data entry sprint, not code-heavy
    - Status: SCOPABLE (~0.5 sprint)
    - Audience: Customer-facing

15. Build Documentation Generation Sprint (NEW CATEGORY — affects all instruments)
    - Gap: Zero instruments have assembly instructions or BOMs
    - Different category of work — templating + content layer rather than code pipeline
    - Mechanically simpler than CAM completion but breadth-wide (all instruments need it)
    - Could leverage existing instrument specs to auto-generate BOM
    - Assembly instructions may need per-instrument authoring
    - Status: SCOPABLE
    - Audience: Customer-facing (build-day reference)

16. Instrument Scope Decision (STRATEGIC — not a sprint)
    - Question: Which instruments should the system actually support?
    - 24 instruments identified, several flagged for deferral:
      EDS-1275 (zero implementation), Bass 4-String (different family),
      Ukuleles/Mandolins (outside primary scope)
    - Decision: Complete priority instruments, mark deferred ones explicitly,
      or remove from claims entirely
    - Worth holding for explicit consideration later

17. Sprint FRET-CONSOLIDATION — Unify Fret Pipelines
    **Decided:** 2026-04-30
    **Estimated effort:** 25-35 hours total across 4 sub-sprints
    
    Strategic decision: eliminate parallel fret pipelines so the canonical
    ecosphere is the single source of truth for fret geometry across all
    consumers (FRET-A export, CAM toolpath, frontend preview).
    
    Six months from now, instrument production must not depend on three
    parallel implementations of fret math. The consolidation pays its cost
    now to avoid debugging "which pipeline did this guitar use" later.
    
    Sub-sprints in execution order:
    
    17a. FRET-CONSOLIDATION-1 — CAM consumes ecosphere (6-10h)
         Refactor CAM toolpath generation to source fret geometry from
         FretboardEcosphere instead of recomputing via fret_slots_cam.py.
         Affected: fret_slots_cam.py, fret_slots_fan_cam.py, fret_slots_router.py
         Open question: ecosphere carries CAM concerns or CAM adds params separately?
    
    17b. FRET-CONSOLIDATION-2 — FretboardWizard migration (3-4h)
         Update FretboardWizard.vue to call /fretboard/compute instead of /frets/positions.
         After: deprecate /frets/positions, remove api_v1/fret_math.py router.
    
    17c. FRET-CONSOLIDATION-3 — FretSlottingView refactor (6-8h)
         Refactor FretSlottingView.vue and fretSlotsCamStore.ts to consume ecosphere.
         Eliminates /api/cam/fret_slots/preview endpoint.
         After: remove cam/routers/fret_slots_router.py.
    
    17d. FRET-CONSOLIDATION-4 — Interactive widget (8-12h)
         Live-update fretboard playground with sliders, reactive SVG, tier-aware DXF.
         Target: /design/fretboard/playground or embedded section.
    
    Quick wins (independent, <1h each):
    - Remove FanFretPointLegacy class (only test_wave_e1.py uses it)
    - Remove compute_fan_fret_positions (already marked DEPRECATED)

**Cross-reference note (Sprint 3B vs Instrument Audit):**
The 10 files in Sprint 3B PR 2B are the authoritative DXF generator migration list.
The instrument model audit confirmed 4 of these (neck/headstock, smart guitar) and found
3 additional DXF *readers* (lespaul_dxf_reader, arc_reconstructor, instrument_body_generator)
that use direct ezdxf for input. The 6 remaining files (blueprint_cam/*, archtop/*, curve_export)
were not in the audit agents' scope but are correctly scheduled in Sprint 3B.
Sprint 3B PR 2B execution resolves DXF output compliance; DXF readers are a separate concern.

**Workaround available:**
- json_to_dxf_r12.py verified working (2026-04-23)
- smart_guitar_body_outline_r12.dxf ready for Fusion import

**Acquisitions pending:**
- Benedetto *Making an Archtop Guitar* (book)
- Epiphone Emperor plans (in mail)

**Physical access pending:**
- 1941 Gibson L-37 — requires deflection jig build first

---

## ACTIVE

### Sprint 1 — Vectorizer Reconciliation
**Status:** COMPLETE — all phases done
**last_verified:** 2026-04-23
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
**last_verified:** 2026-04-23
**Branch:** main

**Standalone repo inventory (reduced per 2026-05-02 single-property strategy):**

| Repo | Description | Status |
|------|-------------|--------|
| HanzoRazer/ltb-woodworking-studio | Joinery, bending, panel work, bandsaw — separate domain from lutherie | Migration target — push pending verification |
| HanzoRazer/blueprint-reader | PDF → DXF pipeline (vectorizer) | Deployed to Hostinger — separate due to deployment, not strategic |

**Open items:**
- [ ] Install ODA File Converter locally — batch convert DWG inventory:
      59_Flying_V.dwg, Flying_V_11.dwg, Classical-02-MM.dwg,
      DWG-00/01/02/03-Gibson-SG.dwg, Acoustic Guitar Neck Profiles DWGs
- [ ] Fix flying_v_1958.json schema mismatch with loader.py (committed 9cdad75b)
      load_model_spec("flying_v_1958") crashes on KeyError "scale"
- [x] Fix instrument_model_registry.json phantom entry — RESOLVED (specs/gibson_flying_v_1958.json now exists)
- [x] Create docs/VECTORIZER_ACCURACY.md — RESOLVED (docs/VECTORIZER_ACCURACY.md exists)
- [ ] Add accuracy summary to README.md and blueprint-reader landing page
- [ ] Sync blueprint-reader with Sprint 1 Phase 1-3 commits
- [ ] Digitize 12-string dreadnought plans via blueprint-reader.html
- [ ] Emperor plans — digitize on receipt
- [ ] ltb-woodworking-studio migration verification and push:
      - Verify current GitHub state of HanzoRazer/ltb-woodworking-studio
      - If empty or partial, push local woodworking_v2/ contents to repo
      - Update luthiers-toolbox imports to reference woodworking as separate dependency
      - Privatize the repo

---

### Sprint 3 — Remediation and Gap Closure
**Status:** REOPENED (2026-04-26) — verification audit found 10/12 false migration claims
**last_verified:** 2026-04-26
**Branch:** main

**Task list:**
- [x] Build dxf_writer.py — central DXF writer enforcing R12, sentinel EXTMIN/EXTMAX,
      ≤3dp coordinates, no LWPOLYLINE. Commit 4c4f1a52. Blocks all new DXF generators.
- [x] Fix PatternRenderer import error in production (commit a7f0f614)
- [x] Fix FastAPI regex deprecation warning — pattern= replacement (commit 131b1cfd)
- [x] Add WeasyPrint dependencies to Docker — PDF export (commit ff958c9a)
- [x] Migrate spiral_geometry.py to dxf_writer.py (2026-04-16, re-migrated 2026-04-23 — regression fixed)
- [x] Migrate archtop_floating_bridge.py to dxf_writer.py (2026-04-16, re-migrated 2026-04-23 — regression fixed)
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

**DXF Consolidation — BOE + remaining migrations (2026-04-23 expansion):**

- [ ] BOE DXF Export Compliance (Option B — backend endpoint)
      Root cause: hostinger/body-outline-editor.html DXF export added AFTER
      Sprint 3 began, implemented using Paper.js native output instead of
      routing through dxf_writer.py. Produces LWPOLYLINE in R2000+ format,
      causing Fusion 360 freeze (reproduced 2026-04-23 during Smart Guitar
      trace import). Violates architectural rule at dxf_svg_generation_
      architecture.md line 713.
      **Implementation:** new backend endpoint (e.g., POST /api/editor/export-dxf)
      accepts BOE geometry JSON, returns R12 DXF via dxf_writer.py.
      BOE frontend wires Export DXF button to this endpoint.
      **Reference:** json_to_dxf_r12.py (working R12 reference, verified 2026-04-23)

- [x] Verify json_to_dxf_r12.py runs in engineer environment (2026-04-23)
      Confirmed: 2241 points → 221.5 KB R12 LINE-only DXF

- [x] Migrate body/smart_guitar_dxf.py to dxf_writer.py (Priority 4 — HIGH IMPACT)
      Migrate only — do NOT generalize. Scope is tight. (2026-04-23)
- [x] Migrate headstock/dxf_export.py to dxf_writer.py (Priority 3) (2026-04-23)
- [x] Migrate blueprint_cam/dxf_preprocessor.py to dxf_writer.py (Priority 3) (2026-04-23)
- [x] Migrate blueprint_cam/contour_reconstruction.py to dxf_writer.py (Priority 3) (2026-04-23)
- [x] Migrate curve_export_router.py to dxf_writer.py (Priority 3) (2026-04-23)
- [x] Migrate neck/headstock_transition_export.py to dxf_writer.py (Priority 4) (2026-04-23)
- [x] Migrate neck/neck_profile_export.py to dxf_writer.py (Priority 4) (2026-04-23)
- [x] Migrate archtop/archtop_contour_generator.py to dxf_writer.py (Priority 5) (2026-04-23)
- [x] Migrate cam/archtop_bridge_generator.py to dxf_writer.py (Priority 5) (2026-04-23)
- [x] Migrate cam/archtop_saddle_generator.py to dxf_writer.py (Priority 5) (2026-04-23)

**SPRINTS.md Cleanup (2026-04-23 scope addition):**

- [x] Phase 1 — Mechanical audit of all sprints (status vs reality)
      Output: docs/audit/sprints_audit_2026-04-23.md
- [x] Phase 2 — Ross triage session on audit findings (6 recommendations approved)
- [x] Phase 3 — Execute cleanup per triage decisions (completed 2026-04-23):
      • Re-migrated spiral_geometry.py and archtop_floating_bridge.py (tech debt fixed)
      • Updated Sprint 2 stale items (flying_v phantom, VECTORIZER_ACCURACY.md marked resolved)
      • Updated Sprint 3 compliance table (10/12 → 12/12 with re-migration notes)
      • Updated Sprint 8 location (docs/instrument_library/ → app/instrument_geometry/models/)
      • Updated Sprint 9 status (PLANNED → IN PROGRESS scaffolded)
      • Updated Archtop Free Tier (noted scripts already exist)
- [x] Phase 4 — Establish maintenance discipline (completed 2026-04-23):
      • Created docs/SPRINTS_MAINTENANCE.md with update rules
      • Added last_verified timestamps to all sprint sections
      • Documented recurring audit process (90-day or 800-line trigger)
      • CI enforcement deferred (solo-dev project)

**DXF Compliance status (CORRECTED 2026-04-26 — 2/12 MIGRATED, 10 FALSE CLAIMS):**

Verification audit: docs/audit/sprints_md_verification_2026-04-25.md

| Priority | File | Format | Status |
|----------|------|--------|--------|
| 1 | `soundhole/spiral_geometry.py` | R12 | ✅ Migrated (verified: imports DxfWriter, 0 ezdxf.new calls) |
| 2 | `bridge/archtop_floating_bridge.py` | R12 | ✅ Migrated (verified: imports DxfWriter, 0 ezdxf.new calls) |
| 3 | `headstock/dxf_export.py` | R2010 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 3 | `blueprint_cam/dxf_preprocessor.py` | R2000 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 3 | `blueprint_cam/contour_reconstruction.py` | R2000 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 3 | `export/curve_export_router.py` | R2010 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 4 | `body/smart_guitar_dxf.py` | R2000 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 4 | `neck/headstock_transition_export.py` | R2010 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 4 | `neck/neck_profile_export.py` | R2010 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 5 | `archtop/archtop_contour_generator.py` | R2010 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 5 | `cam/archtop_bridge_generator.py` | R2010 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |
| 5 | `cam/archtop_saddle_generator.py` | R2010 | ❌ NOT MIGRATED — false claim, scheduled Sprint 3B PR 2B |

**BOE Backend Endpoint:**
- Claim: "POST /api/editor/export-dxf" exists and BOE routes through it
- Reality: **MISSING** — endpoint does not exist in codebase
- Resolution: TBD (implement / remove claim / identify alternate)

---

### Sprint 4 — Photo Vectorizer Production Readiness
**Status:** In Progress — PARTIALLY SUSPENDED
**last_verified:** 2026-04-23

**Completed:**
- [x] spec_name wire-up: VectorizeRequest → PhotoVectorizerV2.extract() (5de45310)
- [x] Auto-rotate for AI images (d45e213a)
- [x] Dimension swap fix (d45e213a)
- [x] AI pipeline validated across 4 specs
- [x] Unknown instrument test (Gibson EDS-1275)

**Status Clarification (2026-04-21):**

The file `photo_vectorizer_v2.py` is internally "Photo Vectorizer v3.0" with three extraction paths:

| Path | Entry Point | Status | Input Class |
|------|-------------|--------|-------------|
| **Blueprint path** | `source_type="blueprint"` | **LIVE** | Scanned PNG/JPEG of blueprint drawings |
| **Photo path** | `source_type="photo"` (12-stage) | **Suspended** | L-1 historical images — poor results |
| **AI path** | `source_type="ai"` (4-stage, v3 feature) | **Suspended** | AI-generated renders — poor results |

**Blueprint path — LIVE.** Uses `light_line_body_extractor.py` for scanned blueprint PNG/JPEG.
Validated at 85-90% grade DXF/SVG output in last-session testing. This is the path that
routes to IBG for second-pass correction.

**Photo/AI paths — SUSPENDED.** Remaining Sprint 4 items are specific to these paths:
- Body isolation filter (SVG shows 4 paths, should be 1) — Photo path
- Scale output discrepancy (1087×949mm vs spec 368×444mm) — Photo path
- Neck crop pre-processor — Photo path
- INSTRUMENT_CATALOG Tier 1 integration — Both paths
- AI render handling — AI path
- L-1 historical image handling — Photo path

**Downstream wiring — SCAFFOLDED.** Blueprint path output → IBG for second-pass
correction is not yet connected. To be implemented in IBG + ML Repo Extraction sprint.

**Remaining (if resumed):**
- [ ] Body isolation filter (SVG shows 4 paths, should be 1)
- [ ] Scale output discrepancy (SVG canvas 1087×949mm vs spec 368×444mm)
- [ ] Neck crop pre-processor
- [ ] INSTRUMENT_CATALOG Tier 1 integration

---

### Sprint 5 — Scale Validation Gate + Curvature Profiler
**Status:** COMPLETE (2026-04-16)
**last_verified:** 2026-04-23
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
**last_verified:** 2026-04-23
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
**last_verified:** 2026-04-23
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
**Status:** COMPLETE (2026-04-21, revised to v3 methodology)
**last_verified:** 2026-04-23
**Output:** docs/audits/SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS_v3.md

**v3 Methodology:** Per-file classification (not directory-wide assumptions).

**Summary:**
| Category | v1 | v3 | v3.1 | Notes |
|----------|----|----|------|-------|
| Live (Blueprint path) | — | 42 | 14 | Blueprint extraction + test infra |
| Suspended (Photo path) | — | — | 15 | 12-stage photo pipeline |
| Suspended (AI path) | — | 8 | 8 | 4-stage AI pipeline |
| Scaffolded | — | 5 | 5 | ML training layer |
| Library/Foundational | 24 | 24 | 24 | Unchanged |
| Orphaned | 4 | 2 | 2 | TrainingDataCollector → Scaffolded |
| Duplicate | 3 | 2 | 2 | Archtop CAM confirmed distinct |

**Key findings (v3.1 — path distinction clarified 2026-04-21):**
1. `inverse_solver.py` confirmed **Library** — imported by brace_prescription.py
2. `photo_vectorizer_v2.py` has THREE extraction paths with different statuses:
   - **Blueprint path** (`source_type="blueprint"`) — **LIVE** (85-90% grade)
   - **Photo path** (`source_type="photo"`, 12-stage) — **Suspended** (L-1 poor)
   - **AI path** (`source_type="ai"`, 4-stage) — **Suspended** (AI renders poor)
3. **No code sharing** between photo_vectorizer_v2.py and vectorizer_phase3.py
4. `TrainingDataCollector` / `GeometryCoachV2` reclassified **Scaffolded** — ML training layer
5. IBG wiring target: `PhotoVectorizerV2.extract(source_type="blueprint")`
6. sg.coach deprecated (2026-02-02) — not a destination for any forward-path component

**Deliverables:**
- `docs/audits/SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS_v3.md` — Full per-file + per-path classification
- `docs/audits/photo_vectorizer_path_distinction.md` — Photo vectorizer path documentation
- `docs/audits/audit_survivors_v3.txt` — 52 files confirmed active
- `docs/audits/audit_deletion_candidates_v3.txt` — 25 files (23 suspended, 1 orphaned, 1 archived)
- `docs/audits/audit_duplicate_pairs.txt` — 2 consolidation targets

**Unblocks:**
- GEN-5 Data Consolidation (intersection table ready)
- Sprint 3 DXF Compliance (confirms 12 production files, 6 sandbox)
- IBG extraction sprint (files classified as Library, new repo planned)
- Photo vectorizer scanned-blueprint work (NOT blocked)
- ML training layer planning (Scaffolded files identified)

---

### Sprint 8 — Instrument Library JSON Population
**Status:** IN PROGRESS (2026-04-16)
**last_verified:** 2026-04-23
**Location:** services/api/app/instrument_geometry/models/
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
**Status:** IN PROGRESS (scaffolded — code exists in sandbox and production paths)
**last_verified:** 2026-04-23
**Location:** sandbox/arc_reconstructor/ + services/api/app/instrument_geometry/body/ibg/

**Scaffolded files:**
- sandbox/arc_reconstructor/instrument_body_generator.py
- services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py
- services/api/app/instrument_geometry/body/ibg/body_contour_solver.py
- services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py

**Remaining:** API endpoint wiring, vectorizer output → IBG pipeline connection

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

## DEFERRED MAINTENANCE

**Canonical registry** for work that is intentionally not done yet. Engineers log deferrals here at session end (see `docs/SPRINTS_MAINTENANCE.md` Rule 6).

| Field | Required |
|-------|----------|
| **ID** | `{DOMAIN}-DEFER-{NNN}` or `MAINT-DEFER-{NNN}` for process/infra |
| **Status** | `DEFERRED` \| `QUEUED` \| `BLOCKED` |
| **Why deferred** | One sentence — cause, not symptom |
| **Restore trigger** | Concrete done-condition |
| **last_verified** | Date status confirmed against repo |

Domain handoffs and governance docs may add detail but **must cite the SPRINTS ID**.

### Index

| ID | Title | Category | Status | last_verified |
|----|-------|----------|--------|---------------|
| ART-STUDIO-DEFER-001 | Design-first-workflow + promotion intent export | API / Art Studio | QUEUED | 2026-05-26 |
| MAINT-DEFER-001 | SPRINTS.md CI enforcement (pre-commit / PR advisory) | Process | DEFERRED | 2026-04-23 |
| CI-RED-001 | sg-spec clone auth — api-verify dead | CI / infra | CLOSED | 2026-05-28 |
| CI-RED-002 | legacy-usage gate 131/10 | CI / API hygiene | OPEN | 2026-05-27 |
| CI-RED-003 | debt-gates complexity ratchet (113 violations) | CI / quality | OPEN | 2026-05-27 |
| CI-RED-004 | Fence Checks frontend boundary violations | CI / boundaries | OPEN | 2026-05-27 |
| CI-RED-005 | Container build swallows sg-spec install failure | CI / containers | CLOSED | 2026-05-28 |
| CI-RED-006 | api-verify: missing `app.ci.domain_boundaries` | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-007 | api-verify: missing `app.ci.operation_lane_compliance` | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-008 | api-verify: missing `ci/rmos/check_no_direct_runartifact.py` | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-009 | api-verify: missing `app.cam.cam_lifecycle_audit_ledger` | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-010 | api-verify: pytest `tests.helpers` import path | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-011 | api-verify: missing `aiosqlite` test dep | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-012 | api-verify: missing `app.calculators.saw` compat shims | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-013 | api-verify: missing `app.woodworking.wooden_floating_bridge` | CI / api-verify | CLOSED | 2026-05-28 |
| CI-RED-014 | api-verify: missing `DXF_R12_TRANSLATOR_ID` registry constants | CI / api-verify | CLOSED | 2026-05-28 |

---

### ART-STUDIO-DEFER-001 — Design-first-workflow + promotion intent export

**Status:** QUEUED  
**last_verified:** 2026-05-26  
**Priority:** LOW — not on CAM Intent / MVP cut-path critical path  
**Held out of:** PR #46 (CAM Intent H7 restore) — tests would be red on `main`

**Why deferred:** `design_first_workflow_routes` and related art-studio session routes removed in `545fccad` (same orphan batch as CAM intent routers). Routes absent on `main`.

**Symptom:** `test_promotion_intent_export_endpoint.py` fails 8/8 (404 on session start).

**Paths required (minimum):**
- `POST /api/art/design-first-workflow/sessions/start`
- `POST /api/art/design-first-workflow/sessions/{session_id}/transition`
- `GET /api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json`
- `POST /api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1`

**Recover via git:**
- Router: `545fccad^` → `services/api/app/art_studio/api/design_first_workflow_routes.py`
- Test: `2645b0de^` → `services/api/tests/test_promotion_intent_export_endpoint.py`

**Restore trigger:** Re-mount workflow router in `router_registry`; recover test; 8/8 green.

**Origin:** CAM intent investigation 2026-05-26 — prevents repeat of `545fccad` silent deletion pattern.

---

### MAINT-DEFER-001 — SPRINTS.md CI enforcement

**Status:** DEFERRED  
**last_verified:** 2026-04-23  
**Why deferred:** Solo-dev project; implementation cost not justified yet.  
**Restore trigger:** Second developer on repo, or repeated sprint status drift.  
**Detail:** `docs/SPRINTS_MAINTENANCE.md` → CI Enforcement section (Options A/B).

---

### MAINT-DEFER-002 — Post–PR #46 closure artifacts on `main`

**Status:** COMPLETE (2026-05-27)  
**last_verified:** 2026-05-27  
**Closed by:** PR #47 (MAINT-DEFER-002), PR #49 (DO85)

---

### CI-RED-001 — sg-spec clone auth (api-verify dead)

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** Preflight + **Install API deps** green on `main` (api-verify run `26553328753`) after dedicated PAT in repository secret `SG_SPEC_TOKEN`.  
**Layers:** PR #51 (gate runs) → #52 (credential-store + token rotation) → #55 (preflight in credential step) → PAT under **HanzoRazer** org fine-grained token in Actions secrets.  
**Durability:** `docs/ci/SG_SPEC_TOKEN.md` rotation log + preflight in `api_verify.yml`.  
**Out of scope (separate ledger):** `make api-verify` contract/fence reds; **CI-RED-005** container swallow (next).

---

### CI-RED-002 — legacy-usage gate (131/10)

**Status:** OPEN  
**last_verified:** 2026-05-27  
**Why open:** Budget 10; observed 131 legacy endpoint usages. Gate is structurally exceeded — not a drift blip.  
**Restore trigger:** `legacy-usage` check green on `main`, or budget honestly reset with migration plan.

---

### CI-RED-003 — debt-gates complexity ratchet

**Status:** OPEN  
**last_verified:** 2026-05-27  
**Why open:** 113 complexity violations; fails on post-merge `main` (run `26490386636`).  
**Restore trigger:** `debt-gates` job green on `main`.

---

### CI-RED-004 — Fence Checks frontend boundary

**Status:** OPEN  
**last_verified:** 2026-05-27  
**Why open:** `patterns: FAIL` — legacy `/api/rmos/runs` references in client SDK/tests.  
**Restore trigger:** Fence Checks (Blocking) green on `main`.

---

### CI-RED-005 — Container build swallows sg-spec install failure

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR #57 — `docker/api/Dockerfile` fails build if `SG_SPEC_TOKEN` missing or sg-spec install fails. Containers build-and-test green on PR #57; **reliable-elegance** API deploy green after `SG_SPEC_TOKEN` on Railway env `f7a14a29` (`luthiers-toolbox-production.up.railway.app`, 2026-05-28).  
**Was:** WARNING swallow shipped API images without declared `sg-spec` dependency.

**Note:** Permanently red CI camouflages real regressions (CBSP21 on PR #49 nearly filed as "drift"). Remaining CI-RED items are **old, not acceptable, not closed.**

---

### CI-RED-006 — api-verify: missing `app.ci.domain_boundaries`

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — `app.ci.domain_boundaries` shim delegates to `fence_runner` for `rmos_cam_boundary`; Makefile step [2/7] no longer ModuleNotFoundError.  
**Was:** `make check-boundaries` step [2/7] invoked missing module (run `26553328753`).

---

### CI-RED-007 — api-verify: missing `app.ci.operation_lane_compliance`

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — `app.ci.operation_lane_compliance` shim delegates to `fence_runner` for `operation_lane_boundary`; Makefile step [3/7] no longer ModuleNotFoundError.  
**Was:** Step [3/7] invoked missing module (run `26553328753`).

---

### CI-RED-008 — api-verify: missing `ci/rmos/check_no_direct_runartifact.py`

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — restore `ci/rmos/check_no_direct_runartifact.py` (artifact authority scan with baseline); un-ignore `ci/rmos/**` in `.gitignore` so fence scripts are tracked.  
**Was:** Step [5/7] file-not-found; entire `/ci/` tree was gitignored (run `26553328753`).

**Parking lot order:** **CI-RED-006–008** cleared; structural reds **CI-RED-002–004** remain separate until budgeted.

---

### CI-RED-009 — api-verify: missing `app.cam.cam_lifecycle_audit_ledger`

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — restore `cam_lifecycle_audit_ledger.py` (6K audit snapshots for export lifecycle orchestrator).  
**Was:** 5 CAM lifecycle tests + export lifecycle router blocked at import (run `26564053999`).

---

### CI-RED-010 — api-verify: pytest `tests.helpers` import path

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — `test_support/` package for helper imports (pytest 9 importlib mode); Makefile `PYTHONPATH=.:tests`.  
**Was:** `test_adaptive_router`, `test_saw_lab_fixture_compat` collection errors (runs `26564053999`–`26566417730`).

---

### CI-RED-011 — api-verify: missing `aiosqlite` test dep

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — add `aiosqlite` to `services/api/requirements.txt` for `test_pg_pool`.  
**Was:** `ModuleNotFoundError: aiosqlite` (run `26564053999`).

---

### CI-RED-012 — api-verify: missing `app.calculators.saw` compat shims

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — `app.calculators.saw.*` re-exports from `saw_adapters` after migration.  
**Was:** `test_saw_adapters` collection error (run `26564053999`).

---

### CI-RED-013 — api-verify: missing `app.woodworking.wooden_floating_bridge`

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — restore compat module for `compute_saddle_height_from_twelfth_action` (tests only).  
**Was:** `test_woodworking_and_bandsaw` collection error (run `26564053999`).

---

### CI-RED-014 — api-verify: missing `DXF_R12_TRANSLATOR_ID` registry constants

**Status:** CLOSED  
**last_verified:** 2026-05-28  
**Closed:** PR — export stable translator ID constants from `translator_capability_registry`.  
**Was:** `test_dxf_translate_endpoint` import error (run `26564053999`).

---

## QUEUED

### ART-STUDIO-DEFER-001

Tracked under [DEFERRED MAINTENANCE](#art-studio-defer-001--design-first-workflow--promotion-intent-export). Schedule when Art Studio promotion path is in scope — not blocking MVP cut.

---

### Sprint: tap_tone_pi Real-Time Plate Tuning Mode
**Status:** QUEUED
**last_verified:** 2026-04-23
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
**last_verified:** 2026-04-23
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
**last_verified:** 2026-04-23
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
**last_verified:** 2026-04-23
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
**Status:** QUEUED — scripts shipped, endpoint wiring remaining
**last_verified:** 2026-04-23

**Completed (2026-04-23 audit):**
- [x] archtop_stiffness_map.py — EXISTS at services/api/app/cam/archtop/
- [x] archtop_surface_tools.py — EXISTS at services/api/app/cam/archtop/
- [x] archtop_modal_analysis.py — EXISTS at services/api/app/cam/archtop/

**Remaining:**
- [ ] Wire daquisto_measurements.json into pipeline
- [ ] Add API endpoints:
      POST /api/archtop/contours
      POST /api/archtop/stiffness_map
      POST /api/archtop/modal_analysis

---

### Sprint: GEN-5 Data Consolidation
**Status:** QUEUED
**last_verified:** 2026-04-23
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
**last_verified:** 2026-04-23

POST /api/projects does not seed with model_id defaults.
Projects created without instrument-specific configuration.
Every instrument project starts blank — builder re-enters spec data every session.

---

### Sprint: ML Design Layer Consumer Expansion
**Status:** QUEUED — deferred pending IBG extraction completion
**last_verified:** 2026-04-23
**Priority:** Medium — product quality improvement, not blocker
**Blocked by:** IBG + ML Repo Extraction (must complete first so the pipeline pattern is concrete)

**Premise:**

IBG in `ltb-instrument-modeling-ai` establishes a pattern: ML-powered authenticity correction for instrument geometry that the parametric math produces but doesn't render authentically. The pattern applies to multiple instrument design features beyond body outlines.

Known consumers with the same architectural shape (math correct, output doesn't match authentic traditional examples):

- **Rosettes** — 80+ patterns in `ltb-rosette-designer`. Issue reported October-December 2025. Mathematically correct geometry, visually inauthentic compared to real traditional rosettes.
- **Headstocks** — potential consumer. Template-based designs that may need style authentication against real instrument references.
- **Inlays and fret markers** — potential consumer. Pattern authenticity against traditional decorative styles.
- **Sound hole designs** — potential consumer. Shape authenticity beyond acoustic physics targets.
- **Marquetry patterns** — potential consumer. Traditional pattern authenticity.

**Scope (decide when work begins, not now):**

For each candidate consumer, evaluate whether it belongs:

- In `ltb-instrument-modeling-ai` (same repo as IBG) — if the ML pattern is clearly identical, same training data structure, same correction interface
- In a shared ML infrastructure package (new repo, consumed by both IBG and the new consumer) — if the pattern is mostly shared but with domain-specific variations
- In a parallel dedicated repo — if the variations are significant enough that sharing creates more coupling than benefit

Making this architectural decision requires two concrete use cases (IBG + one other) in front of the decision-maker, not one and speculation.

**Rosette authenticity is the likely first expansion candidate:**

The problem is concrete and long-standing. The pattern matches IBG's structure: collect corpus of authentic traditional rosettes, train recognition layer, use to authenticate or correct mathematically-generated output. 50-100 reference examples needed initially across the 80+ pattern families.

When this sprint activates, rosette authenticity is the natural first use case. Scope it as its own sub-sprint with the architectural placement decision made at that point.

**Success criteria:**

- Pattern from IBG extraction is concrete and stable (meaning IBG has been shipping for enough time to prove the architecture works)
- At least one consumer beyond IBG has been evaluated and scoped
- Architectural placement decision for that consumer is informed by two concrete use cases, not speculation
- If the consumer lands in `ltb-instrument-modeling-ai`, the repo's naming and scope remain coherent; if a separate architectural home is chosen, that home is documented

**Do not start before:**

- IBG + ML Repo Extraction sprint complete
- IBG is connected to its upstream consumers (BOE, vectorizer v3.6, photo vectorizer scanned-image path) and producing corrected output
- ML training layer has at least the scaffolded components wired (TrainingDataCollector, GeometryCoachV2, FeedbackSystem operating in their intended roles even if not yet trained on the full 275-plan corpus)

**Related documents:**

- ADR entry 2026-04-20 (ceiling reversal + IBG architecture)
- IBG + ML Repo Extraction sprint (when written)
- `ltb-rosette-designer` repo (primary candidate consumer)

---

## TECH DEBT

| Item | Location | Description | Status |
|------|----------|-------------|--------|
| Bi-arc joining math | `docs/reference/curvature_correction_unmerged.py` | 467 lines of gap-correction math, chord/sagitta utilities, detailed MEASURED_RADII with derivation notes. Not integrated into services/api version. | OPEN — merge target: `services/api/app/instrument_geometry/curvature_correction.py` |
| ~~DXF migration regression~~ | ~~`instrument_geometry/soundhole/spiral_geometry.py`~~ | ~~Marked migrated 2026-04-16 but still had ezdxf.new("R2000")~~ | ✅ FIXED 2026-04-23 — re-migrated to dxf_writer.py |
| ~~DXF migration regression~~ | ~~`instrument_geometry/bridge/archtop_floating_bridge.py`~~ | ~~Marked migrated 2026-04-16 but still had ezdxf.new("R2000")~~ | ✅ FIXED 2026-04-23 — re-migrated to dxf_writer.py |
| DXF reader migration | `lespaul_dxf_reader.py`, `arc_reconstructor.py`, `instrument_body_generator.py` | 3 files use direct ezdxf for DXF parsing/reading (input operations). Not blocking — readers don't have the same R12 enforcement concern as writers. | OPEN — future work if canonical reader pattern emerges |

---

## BACKLOG — CAM Enhancements (2026-04-25 audit)

### CAM Materials Profile Expansion
**Priority:** LOW — enhancement, not blocker
**Location:** `cam_core/feeds_speeds/materials.py` (19 lines, placeholder)

`materials.py` has only hardwood/softwood placeholders. Expand with lutherie-specific woods:
- mahogany, maple, rosewood, ebony, koa, walnut (body/neck)
- spruce, cedar, redwood (tops)
- bone, plastic, graphite (nuts/saddles)

**Source data:** `data/cam_core/saw_blades.json` already has better material coverage (hardwood, softwood, veneer with preset modes). May be able to consolidate or extract from there.

**Scope:** Small focused work. Not a full sprint.

### CAM TODO Cleanup
**Priority:** LOW — backlog items, not blockers
**Location:** `app/cam/` directory

3 TODO comments identified in CAM audit:

| File | Line | Item |
|------|------|------|
| adaptive_core.py | 296 | Island subtraction uses simple expansion |
| adaptive_core_l1.py | 172 | Island subtraction may not handle complex cases |
| archtop_modal_analysis.py | 370 | Implement simply_supported when solver supports it |

**Assessment:** Enhancement notes. Current implementations work with simplified approach.
Track as backlog — address when touching those files for other reasons.


### ~~Orphaned curvature test file~~

**Status:** ✅ RESOLVED 2026-05-01
**Resolution:** Option B — deleted test file (speculative test for unshipped integration)
**File deleted:** `services/api/tests/test_layer_builder_curvature.py`

The test imported symbols (`_is_curvature_body_candidate`, `curvature_body_promotion_enabled`,
`CURVATURE_PROFILER_AVAILABLE`) for layer_builder integration that was never implemented.
Original commit 944aefc6 preserved in git history if needed.

### FRET-A schema/kernel math duplication

**Status:** RESOLVED (Phase 1.5)
**Priority:** Technical debt — blocking alt-temperament feature
**Discovered:** 2026-04-29 during FRET-A Phase 1 retrospective
**Resolved:** 2026-04-29 in Phase 1.5
**File:** services/api/app/instrument_geometry/neck/fretboard_ecosphere.py

~~The FretboardEcosphere schema implements `_fret_position_temperament()`
internally, duplicating ~30 lines of math from `fret_math.py`.~~

**Resolution (Path 1 executed):**
  1. Extended alternative_temperaments.py with resolve_temperament_ratios()
  2. Created scala_loader.py for .scl parsing
  3. Refactored schema methods to delegate to the kernel

All temperaments now produce mathematically correct positions:
  - Equal temperaments (12/19/24/31-TET): true N-TET math
  - Non-equal temperaments (Pythagorean, Just, Meantone): real ratio math
  - Custom Scala: parsed and applied via scala_loader

Round-trip tests confirm compute → scala → parse → compute identity
within 1e-3 mm tolerance (accounts for Scala format precision).

### DXF policy compliance gap

**Status:** Backlog
**Priority:** Hygiene — non-blocking
**Discovered:** 2026-04-29 during post-PR-10 audit
**Source:** docs/investigations/dxf_policy_compliance_audit_2026-04-29.md

CLAUDE.md DXF policy requires all DXF generators route through `dxf_compat`.
Repo-wide grep found **35 files** with direct `ezdxf.new()` calls:

  - 21 files in services/api/ (production code, varied versions R12/R2000/R2010)
  - 14 files in services/photo-vectorizer/ (mostly standalone scripts, less critical)

PR #10 refactored 3 critical bypass files. The remaining 32 are pre-existing
violations that predate PR #10 — not regressions from R2000 work.

**Version distribution is historical drift, not deliberate design.** Files use
R12, R2000, and R2010 inconsistently. Future cleanup should default to policy
versions: R12 (free tier, consumer-facing) or R2000 (paid tier, CAM-ready).

Resolution options:

  A. Refactor in batches by priority (production routers first, scripts last)
  B. Tighten CI to reject new `ezdxf.new()` additions, accept existing as debt
  C. Some endpoints may have legitimate need for non-default versions —
     refactor with version awareness

Recommend B + A in batches. Adding a CI check stops the bleed; backfill
happens when team has bandwidth.

Not blocking FRET-A or any current sprint. Triage when DXF hygiene sprint scheduled.

---

## CLEANUP

### Sprint CL-1 — Security Remediation (COMPLETE 2026-05-03)

**Scope:** Address exposed API credentials surfaced by codebase scan.

**Completed actions:**
- Repository privatized at HanzoRazer/luthiers-toolbox
- Anthropic API key rotated (old key revoked, new key issued)
- OpenAI API key rotated (old key revoked, new key issued)
- New keys saved to local .env files, verified in VS Code

**Pending follow-through (separate small task):**
- [x] Add `.env` entries to `.gitignore` if not already present (2026-05-26 — added explicit `services/api/.env`, `packages/client/.env.local`, `packages/client/.env.production.local`)
- [x] Verify `.env` and `services/api/.env` not tracked (confirmed — never in index)
- [x] Commit prevention changes (feat/repo-remediation-hygiene)

**Status:** COMPLETE (2026-05-26). Acute exposure closed; prevention follow-through landed.

---

### Sprint CL-2 — Root Artifact Directory Cleanup

**Priority:** HIGH (low effort, immediate disk reclaim)
**Effort:** 30 minutes
**Status:** COMPLETE (2026-05-26)

**Scope:** Remove timestamped download directories and benchmark output directories at repo root.

**Executed (2026-05-26):**
- Timestamped `files - 2026-*` dirs — already absent (gitignore pattern `files - */` in place)
- Removed local (gitignored) benchmark dirs: `benchmark_exports/`, `benchmark_outputs/`, `benchmark_results/`
- Removed local gitignored root artifacts: `benchmark_comparison.json`, `benchmark_*.svg`
- **Kept:** `benchmark_manifest.json` (tracked; used by benchmark scripts)

**Verification:** Grep confirmed no production imports of deleted paths; `dxf_consolidator.py` `__main__` CLI references only (graceful `Not found` if absent).

---

### Sprint CL-3 — Photo Vectorizer Test Output Cleanup

**Priority:** MEDIUM (volume issue, not structural)
**Effort:** 1-2 hours including curation review
**Status:** Queued — requires Ross input on artifact preservation

**Scope:** services/photo-vectorizer has 14+ test output directories accumulated during development. Some likely contain meaningful artifacts (calibration runs, validation outputs that informed subsequent decisions). Volume is prohibitive but blanket deletion risks losing useful reference material.

**Approach:**
1. Engineer surveys the 14+ test output directories
2. Identifies which contain unique artifacts vs. which are redundant
3. Produces a brief disposition list: keep (and where to archive), delete (volume artifacts only)
4. Ross reviews disposition list before any deletion
5. Engineer executes per Ross's review

**Likely outcome:** Most test outputs delete; a small subset of validated reference outputs (the ones that informed the vectorizer architecture) preserve to docs/archive/2026/photo_vectorizer_validation/.

**Deferred decision:** Whether photo-vectorizer should establish a permanent test-fixture directory pattern going forward (so future test outputs land in a designated location with retention rules) — separate sprint if pursued.

---

### Sprint CL-4 — Photo Vectorizer Version Consolidation

**Priority:** MEDIUM (real architectural decision)
**Effort:** 4-8 hours
**Status:** Queued

**Scope:** services/photo-vectorizer has multiple versioned files (extract_body_grid_v2 through v5) suggesting incomplete consolidation. The newest version is presumably canonical but older versions remain.

**Tasks:**
1. Confirm v5 is canonical (or identify which version is)
2. Verify no current code imports from older versions
3. Archive older versions to archive/code/photo_vectorizer/ with brief notes on what changed between versions
4. Update any documentation that references older versions
5. Single commit removing legacy versions

---

### Sprint CL-5 — Obvious Orphan Removal

**Priority:** HIGH (low effort, low risk)
**Effort:** 30 minutes
**Status:** COMPLETE (2026-05-26)

**Scope:** Several directories appear to be one-time migration artifacts or accidental commits with no current purpose.

**Removed (2026-05-26):**
- `services/api/app/router_rewire_report/` — one-time migration artifact (2 files)
- `services/api/app/routers/_archived/` — archived pipeline code (5 files)

**Already absent:** `services/api/app/Users/` (accidental directory)

**Verification:** Grep found zero production imports of `_archived` modules; only docs/audit references.

---

### Sprint CL-6 — util/ + utils/ Merge

**Priority:** LOW (minor cleanup)
**Effort:** 1-2 hours
**Status:** Queued

**Scope:** services/api/app has both `util/` and `utils/` directories — duplication that should consolidate.

**Tasks:**
1. Survey contents of both directories
2. Decide canonical name (utils/ is more conventional)
3. Move contents from non-canonical to canonical
4. Update all imports in the codebase
5. Verify tests still pass
6. Remove the empty directory

**Risk:** Import updates need to be comprehensive. A single missed import causes runtime failure. Worth running test suite after to verify.

---

### Sprint CL-7 — Landing Page Disposition

**Priority:** MEDIUM
**Effort:** 30 minutes after Ross identifies which are abandoned
**Status:** Awaiting Ross confirmation

**Scope:** Resolve abandoned landing pages identified by scan.

**Hostinger HTML pages (4 candidates):**
- `production-shop-hub.html` — main marketing landing
- `blueprint-reader.html` — Blueprint Reader tool landing
- `archtop-graduation-studio.html` — Archtop graduation studio
- `body-outline-editor.html` — Body outline editor landing

**Unrouted Vue views (12 candidates):**
- ArtStudioPhase15_5.vue
- ArtStudioDashboard.vue
- ArtJobDetail.vue
- ArtJobTimeline.vue
- ArtStudioUnified.vue
- ArtPresetManager.vue
- MachineListView.vue
- PostListView.vue
- CamProductionView.vue
- MultiRunComparisonView.vue
- OffsetLabView.vue
- LabsIndex.vue

**Pattern observation:** The Art Studio variants (6 of the 12 Vue views) suggest a refactoring that consolidated the Art Studio interface but left old views in place. Likely all 6 archive together.

**Ross action:** Open each candidate, confirm abandoned status, mark for archive or removal.

**Engineer execution:** After Ross's disposition decisions, archive abandoned pages to docs/archive/2026/landing_pages/ and remove from active codebase.

---

### Sprint CL-8 — api/ vs api_v1/ Resolution

**Priority:** MEDIUM (architectural decision needed)
**Effort:** 1 day after decision
**Status:** Awaiting architectural clarification

**Scope:** services/api/app has both `api/` (3 files, mostly deps) and `api_v1/` (11 files, domain modules). Unclear whether this is intentional API versioning or incomplete migration.

**Resolution paths:**
- **If intentional versioning:** Document the versioning strategy. Confirm what should live in api/ vs api_v1/. Update CLAUDE.md to make the boundary explicit. Move misplaced files if needed.
- **If incomplete migration:** Decide forward direction (collapse to api/ or complete migration to api_v1/). Execute the chosen direction. Single sprint of focused work.

**Ross action:** Provide context on original intent. If memory is unclear, engineer can investigate git history of when api_v1/ was created and what was in commit messages.

---

### Sprint CL-9 — Dockerfile Consolidation

**Priority:** MEDIUM
**Effort:** 1 day
**Status:** Queued

**Scope:** 7 Dockerfiles exist across the repo with apparent duplication.

**Locations:**
- `docker/api/Dockerfile`
- `docker/client/Dockerfile`
- `docker/client/Dockerfile.railway`
- `docker/client/Dockerfile.production`
- `docker/nginx/Dockerfile`
- `packages/client/Dockerfile` (possible duplicate)
- `services/api/Dockerfile` (possible duplicate)

**Tasks:**
1. Identify which Dockerfiles are actively used in deployment
2. Confirm duplicates by content comparison
3. Consolidate to one canonical Dockerfile per service (probably 3 total: api, client, nginx)
4. Update docker-compose files and CI workflows to reference canonical paths
5. Remove redundant Dockerfiles

**Risk:** Deployment pipelines may break if references aren't updated correctly. Test deploy on staging or local docker-compose before pushing.

---

### Sprint CL-10 — CI Workflow Audit and Consolidation

**Priority:** LOW (works currently, just maintenance burden)
**Effort:** 2-3 days
**Status:** Queued — defer until other cleanup completes

**Scope:** 52+ CI workflows is substantial. Some likely have overlapping responsibilities or are no longer relevant.

**Approach:**
1. Survey all 52+ workflows, categorize by purpose
2. Identify overlaps (multiple workflows running similar tests)
3. Identify obsolete workflows (testing systems that no longer exist)
4. Consolidate where reasonable
5. Document remaining workflow purposes in .github/README.md or similar

**Realistic outcome:** Probably 20-25 active workflows after consolidation. Reduction in maintenance surface and CI run time.

**Defer rationale:** CI workflows function correctly today. Consolidation is housekeeping that should happen when other higher-priority cleanup is done. Worth scheduling as the final cleanup sprint rather than first.

---

### Sprint CL-11 — Configuration File Consolidation

**Priority:** LOW
**Effort:** 1-2 days
**Status:** Queued

**Scope:** 12 .env files exist across the repo. Most are appropriate (templates, examples, tier-specific configs). Worth auditing whether any are redundant or could consolidate.

**Approach:**
1. Survey all 12 .env files and document each one's purpose
2. Identify redundancy (multiple files providing same configuration)
3. Document the canonical configuration pattern
4. Consolidate where redundancy exists
5. Update CLAUDE.md with the configuration documentation

**Defer rationale:** Configuration sprawl is annoying but functional. Higher-impact cleanup should happen first.

---

### Sprint CL-12 — Standalone Tools Integration Decision

**Priority:** STRATEGIC (decision, not execution)
**Effort:** Variable based on decision
**Status:** Awaiting Ross decision

**Scope:** Several "standalone tool" directories exist at repo root with unclear current status:
- `Interactive_Headstock_Generator/` (23 files)
- `Interactive_Neck and Cam _Modules/` (97 files)
- `Rosette Designer/` (1 file)
- `Guitar Plans/` (567 files — confirmed reference data, off-limits)

**Decision required:** For each (excluding Guitar Plans), are they:
- (A) Active code that should integrate into packages/client as features
- (B) Reference material that should move to docs/reference/
- (C) Legacy code that should archive
- (D) Foundation for future products that should preserve as-is

**Ross action:** Apply judgment to each based on current strategy. The single-property marketing strategy and BOE+IBG product concept (per 2026-05-02 decisions) inform some of these decisions but not all.

**Engineer execution:** After Ross's decisions, execute the chosen disposition for each.

---

### Sprint CL-13 — production_shop_agent Placement

**Priority:** LOW (works correctly, just architectural inconsistency)
**Effort:** 4-8 hours if integration chosen, 0 if status quo accepted
**Status:** Awaiting decision

**Scope:** production_shop_agent/ exists at repo root as a separate subproject (Claude-powered static website generator). It functions correctly but its placement at root rather than under services/ is architecturally inconsistent.

**Options:**
- (A) Leave at root as-is — minor inconsistency but no functional issue
- (B) Move to services/site-generator/ for consistency with other services
- (C) Integrate functionality into services/api/ as a sub-module

**Ross action:** Decide which option. If (A), close the sprint as "decision made, no action needed."

---

### Sprint CL-14 — Photo Vectorizer Test Fixture Convention

**Priority:** LOW (process improvement)
**Effort:** 2-4 hours
**Status:** Optional, deferred

**Scope:** After Sprint CL-3 completes the test output cleanup, establish a standing convention for where photo-vectorizer test outputs live going forward, so future test runs don't recreate the volume problem.

**Tasks:**
1. Define a tests/fixtures/outputs/ directory pattern (or similar)
2. Add .gitignore entries that prevent test outputs from accumulating in git
3. Document the convention in services/photo-vectorizer/README.md
4. Update test scripts to use the new convention

**Defer rationale:** Process improvement that prevents future occurrence. Worth doing eventually but not urgent.

---

### Cleanup Sprint Sequencing Recommendation

**Immediate (this week):**
- CL-1 follow-through (.gitignore + untrack)
- CL-2 (root artifacts) — fast win, immediate disk reclaim
- CL-5 (obvious orphans) — fast win, low risk

**Near-term (this month):**
- CL-3 (photo-vectorizer test outputs) — needs Ross input
- CL-7 (landing page disposition) — needs Ross input
- CL-12 (standalone tools decision) — needs Ross input

**Medium-term (next 2-3 months):**
- CL-4 (photo-vectorizer version consolidation)
- CL-6 (util/ + utils/ merge)
- CL-8 (api/ vs api_v1/ resolution) — needs architectural input

**Longer-term (deferred):**
- CL-9 (Dockerfile consolidation)
- CL-10 (CI workflow audit)
- CL-11 (configuration consolidation)
- CL-13 (production_shop_agent placement)
- CL-14 (test fixture convention)

**Total scope:** 14 cleanup sprints (1 complete, 13 queued). Realistic execution timeline: 2-4 months at sustainable pace, depending on which sprints actually get prioritized vs. which get deferred indefinitely.

---

## DATA INTEGRITY

Data sourcing, silent fallback elimination, and verified calculation inputs.
This section tracks both completed and queued sprints in the data integrity category.

### Sprint M1 — Wood Shrinkage Data Integrity

**Status:** COMPLETE
**Completed:** 2026-04-30
**Commits:** 37f29bc6, 477758eb

Replaced unsourced shrinkage coefficients in wood_species.json with verified data.

**Deliverables:**
- CLAUDE.md sourcing policy
- wood_species.json: 18 species updated (8 N. American from FPL Table 5-3, 10 tropical from Wood Database Eric Meier)
- Per-field source attribution in JSON
- wood_movement_calc.py: migrated to JSON loading with ALIAS_MAP, _load_shrinkage_data(), _resolve_species_id(), get_shrinkage_data(), _LegacyShrinkageDict
- side_bending_calc.py: raises ValueError on unknown species

**Verification:**

| Species | Old | New | Error |
|---------|-----|-----|-------|
| Hard maple | 0.00198 | 0.0033 | -40% |
| Walnut | 0.00185 | 0.0026 | -29% |
| Cedar Western Red | 0.00155 | 0.00167 | -7% |
| Mahogany Honduran | 0.00146 | 0.00143 | +2% |

38 tests pass.

---

### Sprint M2 — Silent Fallback Elimination

**Status:** COMPLETE
**Completed:** 2026-04-30
**Commits:** 477758eb

Eliminated silent fallback behavior where calculators returned plausible but wrong results for unknown inputs.

**Fixed (6 files):**
- soundhole_extended.py: unknown species → ValueError
- back_brace_calc.py: unknown material → ValueError
- finish_calc.py (2 places): unknown species → ValueError
- binding_materials.py: added get_minimum_bend_radius() helper
- binding_geometry.py: uses validated helper at 4 places
- headstock_break_angle_calc.py: added get_nut_friction() helper

**Tests:** tests/test_silent_fallback_elimination.py — 12 tests pass

**Deferred to M2.5:**
- glue_joint_calc.py:80 — MIN_SURFACE_MM2.get(glue_type, 400.0)
- top_deflection_calc.py:42 — density_kg_m3 = 400.0
- pickup_position_calc.py:441 — PICKUP_WIDTHS_MM.get(pickup_type, 25.0)
- Various CAM/service defaults in service.py

---

### Sprint NDS Phase 1+1.5 — Neck Design Studio Foundation

**Status:** COMPLETE
**Completed:** 2026-04-30
**Commits:** 9d37f1ea (Phase 1), d72d9744, e260f365, ac96430f (Phase 1.5)
**Cross-reference:** Sprint FRET-A in COMPLETED section

Foundation work for Neck Design Studio with honest temperament math.

**Phase 1 deliverables:**
- services/api/app/instrument_geometry/neck/fretboard_ecosphere.py (462 lines)
- tests/test_fretboard_ecosphere.py (247 lines)
- 24 tests passing

**Phase 1.5 deliverables (silent fallback to 12-TET eliminated):**
- alternative_temperaments.py: resolve_temperament_ratios()
- scala_loader.py: .scl file parser
- Schema refactored to delegate to kernel

All temperaments now produce mathematically correct positions:
- Equal temperaments (12/19/24/31-TET): true N-TET math
- Non-equal temperaments (Pythagorean, Just, Meantone): real ratio math
- Custom Scala: parsed and applied

Round-trip tests pass within 1e-3 mm tolerance.

---

### Sprint NDS Phase 2 — Router and Endpoints

**Status:** COMPLETE (delivered as FRET-A Phase 2)
**Completed:** 2026-04-30
**Commits:** 4f8a3209, ab1ed8a2, 6b719fc3
**Cross-reference:** Sprint FRET-A in COMPLETED section

NDS Phase 2 scope was delivered under the FRET-A sprint name. Both names refer to the same work.

**Delivered:**
- Router at app/api_v1/fretboard.py
- POST /api/v1/fretboard/compute
- POST /api/v1/fretboard/scala (content-negotiated)
- POST /api/v1/fretboard/dxf (tier-gated: R12 free, R2000 pro)
- GET /api/v1/fretboard/presets, /api/v1/fretboard/presets/{name}
- GET /api/v1/fretboard/schema
- Presets module at app/instrument_geometry/neck/fretboard_presets.py
- Round-trip integration tests at app/tests/integration/test_fretboard_ecosphere_roundtrip.py

**Minor gap:** signal_logic_version bump to signals_v5 not done (backlog).

---

### Sprint FRET-CONSOLIDATION-1 — CAM Consumes Ecosphere

**Status:** COMPLETE
**Completed:** 2026-05-02
**Commits:** e4220537 (Commit 1), fa009184 (Commit 2)

CAM toolpath generation now consumes FretboardEcosphere as canonical source,
eliminating duplicate fret position math across the system.

**Deliverables:**
- app/cam/fret_slots_from_ecosphere.py (bridge module)
- extract_slot_geometry(), ecosphere_to_fretboard_spec(), validate_ecosphere_for_cam()
- fret_slots_cam.py: generate_fret_slot_toolpaths_from_ecosphere(), generate_fret_slot_cam_from_ecosphere()
- tests/cam/test_fret_slots_from_ecosphere.py (35 tests, 1e-9 mm tolerance)

**Architecture:**
```
FretboardEcosphere (canonical) → extract_slot_geometry() → FretSlotToolpath
                                  No duplicate fret math
```

**Tests:** 35 passing (31 extraction + 4 integration)

---

### Sprint M2.5 — Deferred Silent Fallback Cleanup

**Status:** QUEUED
**Priority:** LOW

Items deferred from M2:
- glue_joint_calc.py:80 — MIN_SURFACE_MM2.get(glue_type, 400.0)
- top_deflection_calc.py:42 — density_kg_m3 = 400.0 (unused in calculations)
- pickup_position_calc.py:441 — PICKUP_WIDTHS_MM.get(pickup_type, 25.0)
- Various CAM/service defaults in service.py

---

### Sprint M3a — CITES Status Field with Lookup Tool

**Status:** QUEUED
**Priority:** MEDIUM

**Scope:**
- cites_lookup.py at app/utils/cites_lookup.py — parses CITES checklist JSON
- cites_status field added to wood_species.json entries
- Values populated from cites_lookup output

Pattern matches shrinkage_*_source fields from M1.

---

### Sprint: Active Inventory Species Audit

**Status:** QUEUED
**Priority:** HIGH
**Template:** Padauk update (2026-05-01)

Apply M1 data integrity pattern to species in active shop inventory:
- 60 mahogany B&S sets (honduran_mahogany)
- 25 rosewood (east_indian_rosewood, plus laotian_rosewood entry)
- 10 walnut/maple (black_walnut, acer_macrophyllum)
- 3 ziricote
- 10 tiger flame mahogany (species TBD)
- 20 spruce tops (sitka_spruce)
- 24 mahogany necks
- 20 ebony fretboards (diospyros_crassiflora)
- 100 BF Padauk (african_padauk — DONE)
- 100 BF black walnut heritage (juglans_nigra)
- 100 BF Douglas fir heritage (pseudotsuga_menziesii)
- 10 assorted body blanks (cherry, walnut, khaya)

Each species gets: Janka correction, shrinkage values with sources, naming caveats, CITES genus warning where applicable.

---

### Data File Sync Boundary Documentation

**Status:** DOCUMENTED
**Date:** 2026-04-30

Two JSON files serve different purposes — not duplicates, not alternatives:

| File | Species Count | Purpose | Scope |
|------|---------------|---------|-------|
| `wood_species.json` | 473 | Full CNC/thermal/shrinkage reference | All wood properties: Janka, density, shrinkage, thermal conductivity, MOE, hardness_category, naming_caveats |
| `luthier_tonewood_reference.json` | 71 | Curated acoustic subset | Acoustic-specific: stiffness_index, damping_coefficient, tap_tone_character, plus core fields |

**Sync policy:**
- Core fields (Janka, density, specific_gravity, shrinkage) must match between files when a species appears in both
- luthier_tonewood_reference.json adds computed acoustic indices not present in wood_species.json
- wood_species.json is the source of truth for physical/mechanical properties
- Updates to species in active inventory (Padauk template) touch both files

**Verification:** Padauk entry confirmed in sync 2026-04-30 (Janka 1725, SG 0.74, shrinkage R=3.1% T=5.0%).

---

### Sprint M4 — MOE Data Gap Remediation

**Status:** QUEUED
**Priority:** MEDIUM
**Discovered:** 2026-04-30 during Active Inventory audit

Three critical species have missing or incorrect MOE (modulus of elasticity) data:

| Species | Current Value | Issue | Expected |
|---------|---------------|-------|----------|
| spruce_sitka | `null` | Missing | ~10.3-11.9 GPa (FPL Table 5-1) |
| spruce_engelmann | `null` | Missing | ~8.9 GPa (FPL Table 5-1) |
| douglas_fir | 10.0 GPa | Low | ~13.5 GPa for old-growth (FPL shows 13.4 clear, small) |

**Context:**
- MOE drives stiffness calculations for tops, braces, and structural analysis
- Douglas fir discrepancy: 10.0 GPa may represent plantation/second-growth; old-growth heritage stock (100 BF in inventory) closer to ~13.5 GPa
- Spruce null values cause silent fallback in any calculator that doesn't guard

**Scope:**
- Verify FPL Table 5-1 values for all three species
- Add species-specific notes for growth-type variation (plantation vs old-growth)
- Update wood_species.json entries
- Cross-check luthier_tonewood_reference.json for acoustic-derived stiffness_index

---

### Sprint M5 — CIRAD Reference Database API

**Status:** QUEUED
**Priority:** MEDIUM
**Discovered:** 2026-05-03 during wood species audit
**Scope:** luthiers-toolbox internal only — not designed for cross-repo consumption

Expose CIRAD reference databases to luthiers-toolbox users via read-only API endpoints. Currently these databases exist in `docs/reference/` but are only used internally for data sourcing validation. Woodworking-studio has its own data; no HTTP dependency on this API (see ADR 2026-05-03).

**Current State:**
- CIRAD Wood Collection: 34,395 specimens, 9,212 species, 169 countries — no API access
- CIRAD Wood Density: 4,022 specimens, 872 species with D12/R/S/Db — no API access
- Users can query wood_species.json (473 species) but cannot access underlying reference data

**Deliverables:**

1. **CIRAD Collection Loader** (`app/materials/registry/cirad.py`)
   - `load_cirad_collection()` — parses CSV, returns typed records
   - `search_collection(species=, family=, country=, genus=)` — filtered search
   - `get_specimen(ctft_id)` — single specimen lookup

2. **CIRAD Density Loader** (`app/materials/registry/cirad_density.py`)
   - `load_cirad_density()` — parses CSV, returns typed records
   - `get_density_by_species(species)` — D12, R, S, Db values
   - `search_density(family=, country=, continent=)` — filtered search

3. **API Router** (`app/materials/cirad_router.py`)
   ```
   GET  /api/reference/cirad/collection           — paginated collection (34,395 records)
   GET  /api/reference/cirad/collection/{ctft_id} — single specimen
   GET  /api/reference/cirad/collection/search    — filtered search
   GET  /api/reference/cirad/density              — paginated density data (4,022 records)
   GET  /api/reference/cirad/density/{code}       — single density record
   GET  /api/reference/cirad/density/search       — filtered search
   GET  /api/reference/cirad/stats                — collection statistics
   ```

4. **Pydantic Schemas** (`app/materials/schemas.py` additions)
   - `CiradSpecimen` — CTFT id, family, species, SG, country, sub-continent, herbarium, samples
   - `CiradDensityRecord` — code, taxa, family, country, D12, R, S, Db
   - `CiradSearchParams` — species, family, country, genus, continent filters
   - `CiradStatsResponse` — counts by family, country, continent

**Data Fields Exposed:**

| CIRAD Collection | CIRAD Density |
|------------------|---------------|
| CTFT id | Code |
| Family | Taxa |
| Species | Family |
| Specific gravity | Country |
| Country | Continent |
| Sub-continent | D12 (density at 12% MC) |
| Herbarium occurrence | R (volumetric shrinkage %) |
| Number of samples | S (fiber saturation point %) |
| Collector's name | Db (basic density) |
| Notes on origin | |

**Query Examples:**
```
GET /api/reference/cirad/collection/search?family=LEGUMINOSAE&country=Brazil
GET /api/reference/cirad/density/search?continent=South-America&min_db=0.7
GET /api/reference/cirad/stats
```

**Use Cases:**
- Cross-validate wood_species.json entries against CIRAD specimens
- Research species by geographic origin
- Find alternative species from same region/family
- Access raw density physics data (D12, R, S, Db) for acoustic modeling
- Verify specific gravity values against 34,395-specimen reference

**Pagination:**
- Default page size: 100
- Max page size: 500
- Required for collection endpoint (34K records)

**Scope Exclusions:**
- No write operations (read-only reference data)
- No CITES integration (separate sprint M3a)
- No automatic sync to wood_species.json (manual curation process)

**Estimated Effort:** 8-12 hours
- CSV loaders with caching: 2h
- Pydantic schemas: 1h
- Router with pagination: 3h
- Search/filter logic: 2h
- Tests: 2h

**Dependencies:** None — standalone feature

---

### Sprint M6 — Unfinished Work Audit

**Status:** QUEUED
**Priority:** MEDIUM
**Discovered:** 2026-05-03

Systematic audit to identify code that was developed for purposes that may have been superseded but was never formally paused or archived.

**Known Examples:**
- Body Outline Editor (BOE) — backend endpoint claim (Sprint 3) marked MISSING
- InstrumentBodyGenerator (IBG) — scaffolded in sandbox/ and production paths, wiring incomplete

**Scan Categories:**

1. **Scaffolded but incomplete subsystems**
   - Code structure exists but core functionality not wired
   - Imports present but never called
   - Endpoints documented but not implemented

2. **Sandboxed experiments not touched recently**
   - `sandbox/` directory contents with no recent commits
   - Prototype code that never graduated to production
   - Test harnesses for features that didn't ship

3. **Sprint work marked "in flight" that hasn't progressed**
   - SPRINTS.md entries with IN PROGRESS status but no commits in 30+ days
   - Task lists with unchecked items and no activity
   - Branches that diverged and were abandoned

4. **Superseded implementations**
   - Code paths replaced by newer architecture but not removed
   - Parallel implementations where one became canonical
   - Features that shipped via different approach

**Output Per Finding:**

| Field | Description |
|-------|-------------|
| Location | File path(s) or directory |
| Original purpose | What the code was built to do (from comments, commit messages, sprint docs) |
| Current state | SCAFFOLDED, SUSPENDED, ORPHANED, SUPERSEDED |
| Last activity | Most recent commit date touching this code |
| Reconstruction burden | LOW (<4h), MEDIUM (4-16h), HIGH (>16h), UNKNOWN |
| Dependencies | Other code that imports/calls this, or nothing |
| Disposition candidates | ARCHIVE, DELETE, COMPLETE, DOCUMENT-AND-DEFER |

**Scope Exclusions:**
- This sprint surfaces candidates for disposition decisions — it does not fix, complete, or archive anything
- Code actively worked in past 30 days is not considered stale
- Suspended work with documented rationale (e.g., Sprint 4 photo/AI paths) is acknowledged, not re-audited

**Deliverable:** `docs/audit/unfinished_work_audit_2026-05.md`

**Estimated Effort:** 4-6 hours
- Codebase scan: 2h
- Sprint/commit cross-reference: 1h
- Documentation: 1-2h

**Dependencies:** None — read-only audit

---

## COMPLETED

### CAM Intent H7 HTTP Surface Restore (PR #46)

**Status:** COMPLETE
**Completed:** 2026-05-26 (merged PR #46)
**Branch:** `feat/cam-intent-restore` → `main`

**Problem:** `cam_roughing_intent_router` and `rmos_cam_intent_router` deleted in `545fccad` as "orphaned" while `CAMPreview.vue` and SDK still called the endpoints → 404.

**Deliverables:**
- Routers recovered via `git checkout 545fccad^` (no reimplementation)
- `router_registry` manifest registration (`prefix=/api`; roughing intent **after** `app.cam.routers` — import-order constraint documented in `cam_manifest.py`)
- Canonical path: `POST /api/cam/roughing/gcode_intent` (SDK fixed from wrong `roughing_gcode_intent`)
- 16 H7 pytest files restored; `test_promotion_intent_export_endpoint.py` **excluded** → `ART-STUDIO-DEFER-001`
- Blocking CI: `services/api/app/ci/check_execution_class_compliance.py` + `core_ci.yml` + `check_all.py` CI tier
- Live smoke: `scripts/dev/verify_cam_intent_live.py`

**Verification:**
- `pytest` — 16/16 H7 intent tests
- Live — normalize + roughing intent → 200; legacy underscore path → 404

---

### IBG Provenance R2 Export Guards (PR #45)

**Status:** COMPLETE (code on `main`; operational export blocked by design until R1)
**Completed:** 2026-05-26 (merged PR #45)
**Handoff:** `docs/handoffs/DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED_HANDOFF.md`

**Next:** R1 governance ratification session, then Phase E ratified export.

---

### Sprint A — GRBL Spindle Command Emission

**Status:** COMPLETED
**Completed:** 2026-04-30
**Branch:** feat/grbl-spindle-emission-sprint-a
**Commit:** ba17ba68

DXF-to-GRBL pipeline now emits spindle commands for live cutting on BCAM 2030A.

**Changes:**
  - `POST /api/rmos/wrap/mvp/dxf-to-grbl` gains `spindle_rpm` (default 18000) and
    `spindle_dwell_ms` (default 2000) parameters
  - G-code emits `M3 S{rpm}` after safe-Z, `G4 P{sec}` dwell, `M5` before program end
  - `spindle_rpm=0` omits all spindle commands (backward-compatible dry-run mode)

**Verification:**
  - 6 spindle-specific tests added to test_dxf_to_grbl_endpoint_smoke.py
  - All 23 endpoint tests pass; coverage 23.04%
  - Sample output verified: `M3 S18000`, `G4 P2.0`, `M5` in correct positions

**Remaining (separate sprints):**
  - Coolant control (M8/M9) — file as new backlog entry when needed
  - Tool change commands (Tn M6) — single-tool assumption holds for now

---

### Sprint FRET-A — Fretboard Ecosphere API

**Status:** COMPLETED (Phase 8)
**Tag:** v2.5.0-alpha.1-phase7 (Phase 7), 95b92f8a (Phase 8)
**Completed:** 2026-04-30
**Branch:** sprint/fret-ecosphere-a

Canonical Pydantic-validated fretboard geometry with honest temperament math,
full nine-layer DXF projection verified through GRBL pipeline, and frontend
wire-up with tier-aware DXF version selection.

**Phase summary:**
  - Phase 1: Schema (FretboardInput, FretboardEcosphere, FretLine, StringPath)
  - Phase 1.5: Math kernel honesty refactor (real N-TET, Pythagorean, Scala)
  - Phase 2: FastAPI router (/compute, /dxf, /scala, /presets, /schema)
  - Phase 7: Nine-layer DXF projection with R2000 LWPOLYLINE CAM verification
  - Phase 8: Frontend wire-up — API client, composable, tier badge (R12 free, R2000 pro)

**Phase 7 verification results (R2000):**

| Layer | Entities | Notes |
|-------|----------|-------|
| FRET_SLOTS | 22 LWPOLYLINE | Closed rectangles, CAM-ready |
| FRETS | 22 LINE | Bass-to-treble per fret |
| STRINGS | 6 LINE | Nut-to-bridge per string |
| NUT | 1 LINE + 6 CIRCLE | Nut line + string slot markers |
| BRIDGE | 1 LINE | Theoretical saddle position |
| FRETBOARD_OUTLINE | 1 LWPOLYLINE | Closed 4-point contour |
| ANNOTATIONS | 23 TEXT | 22 fret numbers + scale label |
| BRIDGE_COMPENSATED | 0 | Empty (no offsets in test) |
| HARMONICS_OVERLAY | 0 | Empty (future Sprint FRET-D) |

GRBL pipeline test confirms closed LWPOLYLINE emission avoids the 2-point
loop-assembly gap identified in cam_pipeline_r2000_compat 2026-04-29.

**Phase 8 deliverables (2026-04-30):**
  - packages/client/src/api/fretboardEcosphere.ts — typed client, camelCase↔snake_case
  - packages/client/src/design-utilities/lutherie/neck/useFretboardEcosphere.ts — composable
  - FretSlottingView.vue, FretboardWizard.vue — alert stubs replaced with real DXF download
  - Tier badge shows "Free (R12)" or "Pro (R2000)" based on useAuthStore

**Remaining sprints (separate):**
  - Sprint FRET-D: Harmonics overlay (Zone-Tritone integration)
  - Fusion add-in: Standalone sprint

---

### ~~Sprint 3 — Remediation and Gap Closure (DXF Consolidation)~~
**Status:** MOVED BACK TO ACTIVE — see Sprint 3 in ACTIVE section
**Reason:** Verification audit (2026-04-26) found 10/12 migration claims were false.
See docs/audit/sprints_md_verification_2026-04-25.md for details.

---

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
| 2026-04-20 | Blueprint vectorizer ceiling declaration (2026-04-16) reversed | v3.6 restored morphological gap closing from vectorizer_phase2.py (commit 3db07c62). Benchmark exceeded March 6 baseline (cuatro: 21.8MB/204K entities vs 16.3MB/128K). The "ceiling" was artifact of missing capability, not fundamental limit. 22 commits of active vectorizer development followed in 04/16-04/21. **Architecture:** Blueprint vectorizer v3.6 is primary production path. Photo vectorizer functional for scanned blueprint PNG/JPEG inputs at 85-90% grade; Sprint 4 suspension applies to specific input classes (AI renders, L-1 historical images), not photo vectorizer files as a whole. IBG is a completion library (no direct API endpoint, connected via imports) — analogous to inverse_solver.py. IBG has learning dependency on ML training layer (TrainingDataCollector, FeedbackSystem, GeometryCoachV2 scaffolded in vectorizer_phase3.py). **Destinations:** IBG → new standalone repo (name TBD, stays in luthiers-toolbox until scaffolded). ML training layer → home TBD. sg.coach deprecated 2026-02-02, superseded by sg-agentd, not a candidate for any role. |
| 2026-04-30 | FRET-CONSOLIDATION: canonical ecosphere is single source of truth | Three parallel fret pipelines (api_v1/fret_math, cam/fret_slots, FRET-A ecosphere) converge to ecosphere. CAM consumes ecosphere geometry; legacy endpoints deprecated after frontend migration. Prevents "which pipeline did this guitar use" debugging at scale. |
| 2026-05-02 | Standalone repos as moat strategy superseded by single-property marketing | All previously planned standalone repos except ltb-woodworking-studio (different domain) and blueprint-reader (deployment-driven separation) collapse back to luthiers-toolbox. Production Shop website presents tools as named features regardless of repo organization. SEO and brand authority concentrate on single property. ltb-woodworking-studio retains separate status due to conceptual domain boundary (woodworking ≠ lutherie). |
| 2026-05-03 | Woodworking-studio operates completely independently from luthiers-toolbox | No HTTP cross-repo dependencies at runtime. Each repo has its own wood data (wood_species.json), its own schema (lutherie needs acoustic properties; woodworking needs machining/joinery properties), its own data integrity work. Furniture makers shouldn't need a luthier's platform running to calculate panel movement. Operational independence matches eventual deployment reality — two products, two failure modes. Sprint M5 CIRAD API is luthiers-toolbox internal only; not designed for cross-repo consumption. Initial woodworking-studio data population: 30-40 species with woodworking-specific schema, ~12-20h work. |
