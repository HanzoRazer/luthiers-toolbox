# The Production Shop — Sprint Registry
Last updated: 2026-04-07
Maintained by: Ross Echols (HanzoRazer)

---

## NEXT SESSION OPENS WITH (2026-04-07)

1. **Re-upload 3 missing archtop scripts:**
   - `archtop_stiffness_map.py`
   - `archtop_surface_tools.py`
   - `archtop_modal_analysis.py`
   → commit to `services/api/app/cam/archtop/`

2. **Digitize 12-string dreadnought plans**
   via `blueprint-reader.html`.
   Emperor plans in transit — digitize on receipt.

3. **Archtop Free Tier Phase 1**
   Wire `daquisto_measurements.json` into pipeline.
   Add API endpoints:
   - `POST /api/archtop/contours`
   - `POST /api/archtop/stiffness_map`
   - `POST /api/archtop/modal_analysis`

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

**Phase 5 — Classified mode root cause fixes (2026-04-05):**
Commit `722cc03d` addressing 4 of 5 root causes:
- Phase 5B: Add `_compute_scale_from_spec()` spec-based scale fallback
- Phase 5C: Rewrite `_detect_instrument_type()` with spec inference + pickup detection
- Phase 5D: Add instrument_type guards for RHYTHM_CIRCUIT, CONTROL_CAVITY, NECK_POCKET
- Phase 5E: Add `_safe_dxf_save()` with explicit fsync + EOF verification

**Quality scorecard (Phase 5):**
```
TYPE DETECTION:       3/3 PASS — Dreadnought→acoustic, Les Paul→electric, Cuatro→acoustic
CROSS-CONTAMINATION:  3/3 PASS — No electric features on acoustics, no BRACING on electrics
SCALE CALIBRATION:    0/3 PASS — Validation firing but correction not propagating
                      Width close (4-18% error), height consistently off (24-33%)
```


**Phase 4b — Docker deploy hardening (2026-04-05):**
Commit chain fixing Railway deploy blockers:
- `67c4b68b` fix: libgl1-mesa-glx → libgl1 (Debian Trixie)
- `78c44886` fix: unterminated f-string in photo_vectorizer_router
- `cf162d9f` fix: remove broken sys.stderr.write lines
- `782dea1e` fix: explicit uvicorn+fastapi install before requirements
- `b6159dca` fix: comment out emergentintegrations (not on PyPI)
- `4334e378` fix: libgl1 in docker/api/Dockerfile
- `49ba3547` fix: uvicorn port 8000 → 8080 (Railway)
- `4674720c` fix: add RMOS_RUNS_DIR env var
- `5a145e90` fix: correct data paths — app/data not data at root

**Phase 4c — Docker Debian Trixie + Railway PORT (2026-04-06):**
Commit chain fixing CI build and Railway deployment:
- `19a6dd26` fix: libgdk-pixbuf2.0-0 → libgdk-pixbuf-2.0-0 (Debian Trixie package rename)
- `81cb815b` fix: uvicorn port 8080 → 8000 (match CI healthcheck)
- `ebffbd53` fix: use $PORT env var for Railway compatibility (shell form CMD)

Production verified:
- `/health` → `{"status":"ok","version":"2.0.0-clean"}`
- `/api/vectorizer/status` → `{"available":true}`

**graceful-luck service:** CLOSED — deleted from Railway 2026-04-05.

**Phase 5 root causes — status after 722cc03d:**
| Root Cause | Description | Status |
|------------|-------------|--------|
| RC1 | Scale detection — API key absent | ✅ FIXED: spec fallback added |
| RC2 | Feature cross-contamination | ✅ FIXED: instrument_type guards |
| RC3 | Instrument type misdetection | ✅ FIXED: spec inference + pickup detection |
| RC4 | Scale correction not propagating | ❌ OPEN: validation fires, dimensions unchanged |
| RC5 | DXF truncation on large files | ✅ FIXED: fsync + EOF verification |

**Quality Test Verdict (Phase 5):**
```
RAW MODE:    PASS — production ready. 3/3 files.
             1.99M segments (Dreadnought), 277K (Les Paul), 1.15M (Cuatro).
             AC1009, CONTOURS layer, zero open endpoints.

CLASSIFIED:  PARTIAL — type + contamination fixed, scale still unreliable.
             Type detection: 3/3 PASS
             Cross-contamination: 3/3 PASS
             Scale: 0/3 PASS (width close, height off)
```

**Strategic decision:** Ship raw mode via Docker fix (Phase 4).
Classified mode progressing — Phase 5 delivered 4/5 fixes.

**Key decisions recorded:**
- R12 (AC1009) is project-wide DXF standard — enforced in CLAUDE.md
- Raw mode bypasses all classification — produces CONTOURS layer, LINE entities only
- BlueprintAnalyzer uses PNG already in memory from PDF rasterization (no dual upload required)
- CHAIN_APPROX_NONE is non-negotiable for full fidelity extraction
- Instrument type detector is geometric pre-classifier — Phase 3 will replace with vision analysis
- Classification layer bugs were at Stage 6, not Stage 9-10 — fixes applied at correct location

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
| HanzoRazer/blueprint-reader | PDF → DXF pipeline (vectorizer) | **BLOCKED** — Hostinger billing/coupon issue |

**blueprint-reader Hostinger deploy — BLOCKED:**
- **Reason:** Hostinger billing/coupon issue
- **Expected:** Resolved within 24 hours
- **Next action:** Resume after support response

**Strategic note:** Standalone repos are a moat — free tools that establish
The Production Shop as the authoritative lutherie calculator source.
All tools also exist embedded in Pro and Enterprise tiers.
luthiers-toolbox is the source of truth — standalones are published from it.

**Repo visibility policy:**
```
FREE TIER → PUBLIC repos
  Open source builds trust, community finds bugs,
  makers contribute edge cases, SEO discoverability.
  The code IS the marketing.

PRO/ENTERPRISE → PRIVATE permanently
  Deployed apps only, source never exposed.
  Competitive advantage: physics implementations,
  RMOS architecture, three-feedback-loop system.
```

**PUBLIC (free tier tools):**
- ltb-rosette-designer ✅ LIVE
- ltb-acoustic-design-studio → ready to flip
- ltb-woodworking-studio → ready to flip
- blueprint-reader → ready to flip
- ltb-fingerboard-designer → after population
- ltb-bridge-designer → POPULATED, ready to flip

**PRIVATE FOREVER:**
- luthiers-toolbox (monorepo source of truth)
- RMOS implementation (safety system)
- photo_vectorizer_v2.py (proprietary pipeline)
- tap_tone_pi (measurement platform)
- Learning Vectorizer (future competitive moat)
- ltb-pro (CAM workstation)
- ltb-enterprise (shop OS)

**BLOCKER:** No publish workflow defined (subtree push or CI-based).

**Critical path:**
```
Step 1 → Define publish workflow (subtree or CI)
Step 2 → Clean ltb-express (remove contamination)
Step 3 → Populate 3 priority repos:
           ltb-acoustic-design-studio
           ltb-fingerboard-designer
           ltb-bridge-designer
Step 4 → Flip those 3 repos public
Step 5 → Remaining repos follow same pattern
```

**Step 1 COMPLETE — Publish workflow defined (2026-04-06):**

Git subtree not viable — source files scattered across multiple directories.
Recommended: **Staged Copy Publish** workflow.

```
For each standalone repo:
1. Create standalone package structure in target repo
2. Copy source files (manual or script)
3. Adapt imports for standalone structure
4. Add standalone entry point
5. Commit and push
```

**Execution plan — ltb-acoustic-design-studio:**

Source paths (luthiers-toolbox):
```
services/api/app/calculators/soundhole_calc.py
services/api/app/calculators/soundhole_physics.py
services/api/app/calculators/soundhole_resonator.py
services/api/app/calculators/soundhole_facade.py
services/api/app/calculators/soundhole_presets.py
services/api/app/calculators/soundhole_stiffness.py
services/api/app/calculators/soundhole_climate.py
services/api/app/calculators/soundhole_extended.py
services/api/app/calculators/soundhole_ports.py
services/api/app/calculators/acoustic_body_volume.py
services/api/app/instrument_geometry/soundhole/spiral_geometry.py
services/api/app/instrument_geometry/soundhole/__init__.py
services/api/app/routers/instrument/soundhole_router.py
packages/client/src/views/calculators/acoustics/SoundholeCalculator.vue
```

Target structure (ltb-acoustic-design-studio):
```
├── src/
│   ├── calculators/     ← Python modules
│   └── api/             ← FastAPI router
├── frontend/            ← Vue component (optional)
├── requirements.txt
├── pyproject.toml
└── README.md
```

**Execution plan — ltb-fingerboard-designer:**

Source paths:
```
services/api/app/calculators/fret_slots_cam.py
services/api/app/calculators/fret_slots_export.py
services/api/app/calculators/fret_slots_fan_cam.py
services/api/app/calculators/fret_leveling_calc.py
services/api/app/calculators/fret_wire_calc.py
services/api/app/calculators/fret_wire_physics.py
services/api/app/instrument_geometry/neck/fret_math.py
services/api/app/instrument_geometry/neck/radius_profiles.py
services/api/app/instrument_geometry/body/fretboard_geometry.py
services/api/app/routers/instrument/fretwork_router.py
packages/client/src/components/toolbox/ScaleLengthDesigner.vue
packages/client/src/components/toolbox/FretboardCompoundRadius.vue
packages/client/src/components/FretboardPreviewSvg.vue
```

**Execution plan — ltb-bridge-designer:**

Source paths:
```
services/api/app/calculators/bridge_calc.py
services/api/app/calculators/bridge_break_angle.py
services/api/app/calculators/acoustic_bridge_calc.py
services/api/app/calculators/string_tension.py
services/api/app/instrument_geometry/bridge/geometry.py
services/api/app/instrument_geometry/bridge/placement.py
services/api/app/instrument_geometry/bridge/compensation.py
services/api/app/instrument_geometry/bridge/__init__.py
services/api/app/routers/instrument_geometry/bridge_router.py
packages/client/src/components/toolbox/BridgeCalculator.vue
```

**Task list:**
- [x] Move archtop_floating_bridge.py → app/instrument_geometry/bridge/ *(already in correct location)*
- [x] ~~Move wooden_floating_bridge.py~~ → Removed as redundant *(commit 1b61f219)*
- [x] Reconcile floating_bridge.py — resolved by removing redundant file; bridge module complete
- [ ] Define publish workflow for 8 standalone repos
- [x] Populate ltb-acoustic-design-studio (Staged Copy Publish, 2026-04-06) — commit `129c4a6` on HanzoRazer/ltb-acoustic-design-studio
- [x] Populate ltb-fingerboard-designer (Staged Copy Publish, 2026-04-06) — `5a016a6` (Python) + `577f983` (ScaleLengthDesigner deps) on HanzoRazer/ltb-fingerboard-designer (`master`)
- [x] Populate ltb-bridge-designer (Staged Copy Publish, 2026-04-06) — commit `55c17a6` on HanzoRazer/ltb-bridge-designer
- [ ] Sync blueprint-reader with Sprint 1 Phase 1-3 commits
- [ ] Wire BlueprintAnalyzer scale pre-pass into photo_vectorizer_v2.py
      (same pattern as blueprint reader Phase 3 — PNG already in memory)
- [ ] Build body isolation pre-processor (neck-to-body crop before edge detection)
- [ ] Wire INSTRUMENT_CATALOG Tier 1 working set into photo_vectorizer_v2.py
- [ ] Confirm edge_to_dxf.py is available as high-fidelity fallback path
      for photo inputs where classification fails
- [ ] Install ODA File Converter locally to convert DWG files to DXF.
      Batch convert Guitar Plans/ DWG inventory: 59_Flying_V.dwg,
      Flying_V_11.dwg, Classical-02-MM.dwg, DWG-00/01/02/03-Gibson-SG.dwg,
      Acoustic Guitar Neck Profiles DWGs.
- [ ] Fix flying_v_1958.json schema mismatch with loader.py.
      load_model_spec("flying_v_1958") crashes on KeyError for "scale" key.
      Needs scale_length_mm → scale.scale_length_in conversion,
      body_height_mm array → loader expected format. (Committed 9cdad75b)
- [ ] Fix instrument_model_registry.json phantom entry: flying_v points to
      specs/gibson_flying_v_1958.json which does not exist. Align registry
      path with flying_v_1958.json committed at 9cdad75b.
- [ ] Create docs/VECTORIZER_ACCURACY.md (technical disclaimer)
- [ ] Create blueprint-reader plain language accuracy section
      for landing page
- [ ] Add one-paragraph accuracy summary to main README.md
      linking to VECTORIZER_ACCURACY.md

---

## QUEUED

### Sprint 3 — Remediation and Gap Closure
**Status:** In progress

**Task list:**
- [x] Build dxf_writer.py — central DXF writer enforcing R12, sentinel EXTMIN/EXTMAX,
      ≤3dp coordinates, no LWPOLYLINE. Commit 4c4f1a52. Blocks all new DXF generators.
- [x] Fix PatternRenderer import error in production (commit a7f0f614)
- [x] Fix FastAPI regex deprecation warning — pattern= replacement (commit 131b1cfd)
- [x] Add WeasyPrint dependencies to Docker — PDF export (commit ff958c9a)
- [ ] Migrate Priority 1 generators to dxf_writer.py: archtop_floating_bridge.py,
      spiral_geometry.py, curve_export_router.py (per REFACTORING POLICY)
- [ ] Fix 13 pre-existing test failures (10 soundhole spiral Python 3.14/ezdxf,
      2 debt gate ratchet, 1 vision integration)
- [ ] Resolve 8 gaps awaiting physical measurements
- [ ] libxcb Docker fix (shared with Sprint 1 Phase 4)

---

### Sprint 4 — Photo Vectorizer Production Readiness
**Status:** In Progress

**Completed:**
- [x] spec_name wire-up: VectorizeRequest → PhotoVectorizerV2.extract()
      Commit: 5de45310
- [x] Auto-rotate for AI images: landscape image + portrait spec → auto-rotate 90°
      Commit: d45e213a
- [x] Dimension swap fix: router unpacking (height, width) as (width, height)
      Fix: h_mm, w_mm = result.body_dimensions_mm
      Commit: d45e213a
- [x] AI pipeline validated across 4 specs:
      smart_guitar (368×444mm), les_paul (340×450mm),
      dreadnought (381×520mm), stratocaster (408×406mm)
      All returned: ok=True, contour_count=1, scale_source=instrument_spec
- [x] Unknown instrument test (Gibson EDS-1275):
      Test case: AI-rendered image of instrument NOT in spec catalog

      | Test | Pipeline | Spec | Result |
      |------|----------|------|--------|
      | 1 | AI | None | BLOCKED ✓ — no spec = no calibration |
      | 2 | AI | gibson_eds_1275 | BLOCKED ✓ — spec not in catalog |
      | 3 | Photo | Auto | 206×321mm — wrong scale (173s) |
      | 4 | Blueprint PDF | N/A | 431×388mm ✓ — accurate extraction |

      **Conclusion:** For instruments not in spec catalog, blueprint vectorizer
      (Phase 3) is the correct path. AI pipeline correctly rejects unknown specs
      rather than producing garbage dimensions.

      Output files: C:/Users/thepr/Downloads/gibson_eds1275_dxf/
      - gibson_eds1275_body.dxf (2,331 LINE entities)
      - gibson_eds1275_primitives.dxf (73,271 LINE entities)

**Remaining:**
- [ ] Body isolation filter (SVG shows 4 paths, should be 1)
- [ ] Scale output discrepancy (SVG canvas 1087×949mm vs spec 368×444mm)
- [ ] Neck crop pre-processor
- [ ] INSTRUMENT_CATALOG Tier 1 integration

**Note:** edge_to_dxf.py is the proven high-fidelity path for photos.
photo_vectorizer_v2.py classification path is supplementary.
AI render path (4-stage) is now preferred for AI-generated images.
---

### SPRINT: LUTHERIE_MATH.md Completion

**Status:** QUEUED
**Priority:** Medium
**Triggered by:** Peer review preparation
**Document:** docs/LUTHERIE_MATH.md (1,160 lines, 25 sections)

**What exists (acoustic physics — complete enough for peer review):**
1. Fret Position Geometry
2. Neck Join Position and Bridge Coupling
3. Saddle Slant Angle
4. Helmholtz Air Resonance — Single Port
5. Effective Neck Length and Perimeter Correction
6. Multi-Port Helmholtz
7. Plate-Air Coupling Correction
8. Body Volume from Dimensions
9. Soundhole Structural Ring Width
10. Soundhole Placement Validation
11. Inverse Helmholtz Solver
12. Orthotropic Plate Modal Frequency
13. Plate Thickness Inverse Solver
14. Archtop Arch Geometric Stiffness
15. Archtop Volume Correction for Arch Height
16. C-Bout Radius (Sagitta Formula)
17. Nut Slot Depth
18. Setup Cascade
19. String Tension
20. Acoustic Impedance
21. Kerfing Geometry
22. Fretboard Extension Mass Loading
23. Side Port Perimeter Factor
24. Two-Cavity Helmholtz
25. Neck Angle Calculation
26. Error Log (3 documented corrections)

**What is missing (CAM geometry — next sections to write):**
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

**Acceptance criteria:**
All 10 missing sections written with:
- Formula with full variable definitions
- Source citation
- Conditions under which formula holds
- Known edge cases and failure modes
- Implementation reference (which Python file)

Document ready for external peer review
of both acoustic and CAM geometry sections.

**Peer review targets (when complete):**
- Option 1: University of New South Wales musical acoustics program
- Option 2: Trevor Gore / Gore & Gilet forum
- Option 3: Liutalab development team


---

## COMPLETED

### Sprint 1 Phases 1-3 — Vectorizer Reconciliation
Completed: 2026-04-04
Commits: 04735bd4, 72bfffc9, 059cf5b0

**R12 Enforcement sweep** (part of Phase 1):
Files corrected: vectorizer_phase3.py, dxf_postprocessor.py,
phase4/annotations/exporter.py, CLAUDE.md
Config corrected: config/shop_config.yaml (version: R2018 → R12)

**Production environment restored:**
- DATABASE_URL: Supabase postgresql:// connection string set in Railway
- ANTHROPIC_API_KEY: Set in Railway shared variables
- luthiers-toolbox service: Online (was marked for deletion — recovered)
- graceful-luck service: Online
- @luthiers-toolbox/client: Online

---

## ARCHITECTURAL DECISIONS LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-04 | R12 (AC1009) is project-wide DXF standard | CAM compatibility, Fusion 360 freeze prevention, genesis of The Production Shop |
| 2026-04-04 | dxf_writer.py blocks all new DXF generators | Central enforcement of R12 standards until it exists |
| 2026-04-04 | BlueprintAnalyzer uses in-memory PNG from PDF rasterization | No dual upload required — PDF already rasterized internally |
| 2026-04-04 | Standalone repos are a moat, not a code split | Copycats exist — free tools protect the integrated product |
| 2026-04-04 | ltb-woodworking-studio is the canonical woodworking module | app/woodworking/ in main repo is a seam — instrument geometry never goes there |
| 2026-04-04 | Instrument catalog uses tiered schema | Tier 1: validated plans in repo. Tier 2: community submitted. Tier 3: ethno/orchestral |
| 2026-04-04 | ltb-acoustic-design-studio combines Helmholtz calculator + soundhole designer | Physics-to-geometry pipeline is the product — separating breaks the workflow |
| 2026-04-05 | Refactor when already in a file, not for refactoring's sake | Bulk refactoring breaks working code — tiered priority keeps risk controlled |
| 2026-04-06 | Brand manifesto committed as founding document | docs/MANIFESTO.md (049603ac) — homepage, README, pitch deck use |
| 2026-04-07 | Strict endpoint separation: blueprint vs photo-vectorizer | Never route photos to blueprint endpoint, never route drawings to photo endpoint |

---

## DECISION: Strict Endpoint Separation (2026-04-07)

**Problem:** blueprint-reader.html was calling `/api/vectorizer/extract` which uses
`photo_vectorizer_v2.py` — a pipeline designed for photographs and AI renders.
When fed technical drawings (scanned PDFs, vector plans), it fails to find
body-sized contours because the extraction heuristics assume photographic input.

**Decision:** Two completely separate tools, two completely separate endpoints.

| Tool | Endpoint | Backend | Input Type |
|------|----------|---------|------------|
| `blueprint-reader.html` | `POST /api/blueprint/extract` | `edge_to_dxf.py` | Scanned PDFs, vector drawings |
| `photo-vectorizer.html` | `POST /api/vectorizer/extract` | `photo_vectorizer_v2.py` | Photographs, AI renders |

**Action items:**

1. **Create `POST /api/blueprint/extract`**
   - Wire to `edge_to_dxf.py` (already has `/blueprint/edge-to-dxf/convert`)
   - Match request format to current blueprint-reader.html expectations
   - Return DXF + SVG outputs

2. **Update `blueprint-reader.html`**
   - Call `/api/blueprint/extract` only
   - Remove `/api/vectorizer/extract` call entirely
   - Source type dropdown: remove "Photo" and "AI Render" options

3. **Create separate `photo-vectorizer.html`**
   - Calls `/api/vectorizer/extract` only
   - For photographs and AI renders
   - Different UI optimized for photo input (background removal preview, etc.)

4. **Update `BLUEPRINT_READER_INPUT_SPEC.md`**
   - Remove all photo/AI render guidance
   - Blueprint Reader = technical drawings only
   - Photo guidance belongs in separate photo-vectorizer spec

**Rationale:** Mixing input types in one tool creates confusion and bugs.
A scanned plan sheet is fundamentally different from a photograph —
different preprocessing, different edge detection, different scale inference.
Clean separation prevents "why doesn't my photo work" support tickets.

---

## REFACTORING POLICY — STANDING RULE

**Rule:** Refactor a file when you are already in it for another reason.
Do not refactor for refactoring's sake — that is how working code gets broken.

**Priority tiers:**
- **Priority 1:** Active development files only (archtop_floating_bridge.py, spiral_geometry.py, curve_export_router.py)
- **Priority 2:** When touched for other reasons
- **Priority 3:** Never if stable

**Application:** This policy applies to all refactoring tasks, not just DXF consolidation.
The dxf_writer.py blocking rule in CLAUDE.md is satisfied by having the central writer
available — existing generators are migrated opportunistically per this policy.

---

## INSTRUMENT CATALOG — TIER 1 WORKING SET
27 instruments confirmed TIER_1_READY (both PDF and DXF present):
acoustic_steel: A003-Dreadnought-MM, OM, Jumbo, Gibson L-00, J-45
acoustic_classical: Classical-Etienne-Corbet-MM
electric_solid: Gibson Les Paul 59, Les Paul Custom, Moderne, JS1000, RedSpecial
ukulele: Soprano (x2)
latin_american: cuatro puertoriqueño, plano cuatro venezolano, El Cuatro 1-8

97 PDF-only instruments identified as vectorizer candidates.
Full catalog in: services/api/app/instrument_geometry/models/

---

## POST-DEPLOYMENT RESEARCH

### AI Visual Training — Decorative Element Recognition

**Target recognition categories:**
- Rosettes (concentric rings, mosaic patterns, spiral slots)
- Inlays (position markers, headstock logos, vine patterns)
- Binding patterns (herringbone, checkered, multi-ply)
- Materials (abalone, mother of pearl, wood species, plastic)

**Training corpus:**
- Source: 97 PDF-only instruments + Guitar Plans archive
- Ground truth: Manual annotation by Ross during vectorizer QA
- Delivery: JSON annotation files alongside source PDFs

**Implementation path:**
1. BlueprintAnalyzer prompt extension (Sprint 4 task)
2. Vision API structured output capture
3. Annotation validation UI (compare AI vs manual)
4. Fine-tuning data export for future model specialization

**Strategic value:** Decorative element recognition enables automatic
layer separation in DXF output — rosette geometry, inlay pockets, and
binding channels become distinct CAM-ready layers without manual editing.

---

### Physical Template Scanner Workflow
**Status:** Technically complete — documentation and UI surface needed
**Depends on:** Sprint 4 photo vectorizer production readiness

**The insight:**
Physical templates are the dominant reference format across all
hand-craft instrument making traditions — not just violin family.
This includes guitar, lute, oud, saz, kora, archtop, cello, bass,
and every non-Western tradition where template-based building
predates CAD by centuries.

**The product statement:**
"Upload a photo of your template. Get a CNC-ready DXF."

**Technical status:**
edge_to_dxf.py already handles this today.
Flatbed scan at 300 DPI → PNG → edge_to_dxf --raw
--height [known_height_mm] → R12 DXF at correct physical scale.
mm_per_px = 25.4/300 = 0.0847 — no BlueprintAnalyzer needed.
Scale is known from scan resolution.

**What is missing:**
- One-page workflow guide for non-CAD users
- UI surface in Blueprint Lab: "Scan a Template" intake path
- Validation step: compare DXF bounding box against
  user-entered physical measurements from calipers
- Documentation in docs/ covering the scanner workflow

**Catalog implications:**
Enables Tier 3 bowed string entries from physical templates:
  violin_strad_model, violin_guarneri_del_gesu,
  violin_montagnana, viola_strad, cello_strad,
  double_bass_flat_back, double_bass_carved_back

**Strategic value:**
No other lutherie software tool makes this offer to all
instrument making traditions simultaneously. The scanner
workflow is the universal onramp for non-Western and
traditional instrument makers who have no digital workflow.

---

---

### SPRINT: General Soundhole Scanner

**Status:** QUEUED
**Priority:** Medium
**Triggered by:** Sunburst archtop f-hole detection failure

**Problem:**
Current photo vectorizer loses soundhole/f-hole
contours during edge detection when:
- Sunburst finish creates false graduation edges
- F-hole boundaries weaker than graduation ring
- Pickguard partially covers soundhole boundary

**Scope:**
Build SoundholeScanner class that works INWARD
from the detected body outline rather than
outward from raw edges.

**Target soundhole types:**
- `round` → acoustic/classical (circle)
- `oval` → oval soundhole guitars
- `f_hole` → archtop (elongated S-curve)
- `f_hole_pair` → symmetric archtop pair
- `d_hole` → D-shaped soundhole
- `multi` → harp guitar (multiple openings)
- `resonator` → resonator cone opening

**Architecture:**
1. Receive body_outline from existing pipeline
2. Crop image to body bbox + 10% margin
3. Apply local adaptive threshold inside crop
4. findContours on thresholded interior
5. Filter: must be inside body, not neck pocket
6. Classify by circularity + aspect ratio
7. Validate symmetric pairs for f_hole_pair
8. Return as SOUNDHOLE layer in DXF/SVG output

**Known test cases:**
- Sunburst archtop (f-holes) → current failure
- Dreadnought (round soundhole) → should improve
- Classical (round soundhole) → should improve
- Oval soundhole guitar → new capability

**Files to create/modify:**
- NEW: `services/photo-vectorizer/soundhole_scanner.py`
- MOD: `photo_vectorizer_v2.py` — wire in after body election
- MOD: `photo_vectorizer_router.py` — expose soundhole results

**Acceptance criteria:**
- Both f-holes detected on sunburst archtop test image
- Round soundhole detected on dreadnought scan
- No false positives on solid body electrics
- DXF output includes SOUNDHOLE layer with correct geometry

**Known limitation until sprint completes:**
Sunburst finish guitars → f-holes not detected
Workaround: `source_type: "ai"` + `spec_name`
or manual placement in CAM software

---

### SPRINT: Archtop Free Tier

**Status:** QUEUED
**Priority:** Medium
**Tier:** FREE — public repo (ltb-archtop-designer)
**Dependency:** none

**Phase 1 — Pipeline (backend foundation)**

Commit 4 scripts to `services/api/app/cam/archtop/`:
- `archtop_contour_generator.py` — CSV/DXF → contour rings
- `archtop_stiffness_map.py` — z(x,y) → K_shell stiffness map
- `archtop_surface_tools.py` — combined contour + stiffness
- `archtop_modal_analysis.py` — stiffness map → modal frequencies

Wire existing D'Aquisto data:
- `services/api/app/instrument_geometry/models/archtop/daquisto_graduation_measurements.json` (32 zones: 14 top + 18 back)
- Convert to CSV format pipeline expects: x_mm, y_mm, height_mm
- **Conversion gap:** JSON has named zones without x,y coordinates.
  Requires coordinate mapping file before pipeline can consume
  D'Aquisto data directly. Interim: synthetic dome from arch_height scalar.

Add API endpoints:
- `POST /api/archtop/contours` — generate contour rings DXF/SVG
- `POST /api/archtop/stiffness_map` — generate K_eff heatmap PNG
- `POST /api/archtop/modal_analysis` — predict mode frequencies

**Phase 2 — Graduation Studio (frontend)**

Standalone HTML: `tools/archtop-graduation-studio.html`

```
ARCHTOP GRADUATION STUDIO

Step 1 — Enter plate measurements
  [ Interactive grid overlay on guitar body outline ]
  Click any point → enter thickness (mm)
  Or: Upload CSV directly
  Measurement form printable → PDF download

Step 2 — Choose material properties
  Wood species dropdown → E, nu, density auto-filled
  Or manual entry (calibration.py values)

Step 3 — Generate
  [ Generate Contours ]      → DXF download
  [ Generate Stiffness Map ] → PNG heatmap
  [ Predict Modes ]          → frequency table

Step 4 — Results
  Contour rings preview (SVG inline)
  Stiffness heatmap (PNG inline)
  Mode 1, 2, 3 predicted frequencies
  Compare to D'Aquisto reference overlay
```

**Phase 3 — Companion form**

`docs/forms/Arched_Plate_Graduation_Form.pdf`
- Convert existing .txt to printable PDF
- Matches web grid point layout exactly
- The measurement form IS the onramp:
  Print form → measure with calipers → fill in numbers → enter in web grid → generate

**Strategic position:**
This is the tap_tone_pi bridge for people without hardware.
tap_tone_pi measures acoustically. Graduation Studio measures mechanically with calipers.
Both feed the same acoustic model. One requires hardware, one requires only a caliper and 15 minutes.

**Theory connection:**
- LUTHERIE_MATH.md §40: D(x,y) brace stiffness field
- LUTHERIE_MATH.md §43: Dome radius shell stiffness
- LUTHERIE_MATH.md §44: Archtop spatial stiffness field
- The curved surface IS the bracing — K_shell = α·E·h·k_eff²

**Note:** 4 Python scripts exist in sandbox but NOT committed to repo yet.

---

### SPRINT: Archtop CAM Toolkit

**Status:** QUEUED — blocked on dependencies
**Priority:** Medium
**Tier:** PRO — private repo
**Dependency:** Archtop Free Tier complete, Toolpath Visualizer wired, RMOS operational

**Scope:**

Full CAM pipeline for archtop plate machining:

Roughing strategy:
- Parallel passes removing bulk material
- Step-over and depth from arch height
- Largest ball end mill that fits curvature

Finishing strategy:
- Radial or parallel finish passes
- Ball end mill sized to minimum R_eff(x,y)
- Stiffness map tells WHERE tightest curvature is

Scallop control:
- Target surface finish in microns
- Back-calculate step-over from tool radius
- Output adaptive step-over map

Rest machining:
- After large roughing tool
- Identify regions big tool cannot reach
- Queue smaller tool for those regions

**Integration:**
- RMOS safety gate before G-code release
- Toolpath Visualizer preview before cut
- BCAM 2030A post processor
- Machine profile validation

**Strategic position:**
No competitor has this pipeline. VCarve machines archtops but doesn't understand
acoustic stiffness. Fusion 360 generates toolpaths but knows nothing about lutherie.
Production Shop is the only platform where:
  Measure plate → predict acoustics → generate CAM → cut wood
is one connected workflow.

---

## RESEARCH TRACK: Learning Vectorizer

**Strategic insight:** Every extraction builds the training dataset.

The specialized detectors (SoundholeScanner, SunburstGraduationFilter,
NeckCropPreprocessor) are not dead ends — they are the labeled curriculum
for the universal model. Each one solves a class of failure modes AND
generates ground truth for the next phase.

**Phase 1 (current): Specialized detectors**
- SoundholeScanner — QUEUED (see: POST-DEPLOYMENT RESEARCH > General Soundhole Scanner)
- SunburstGraduationFilter — future work
- NeckCropPreprocessor — future work

**Phase 2 (ongoing): Implicit dataset collection**
Every extraction logged with:
- source image hash
- parameters used
- output contour count
- dimension accuracy vs spec
- failure mode if any

Storage format TBD — candidates are SQLite in RMOS or standalone
extractions.db. Decision when Phase 1 is 80% complete.

**Phase 3 (future): Model training**
Train on accumulated extractions. Specialized detectors become
feature extractors. Model learns parameter selection per image type.

**Phase 4 (goal): Universal instrument recognition**
- Japanese Koto
- Turkish Ud
- Persian Tar
- Indian Sitar
- Any instrument with strings and a body

---

## PRODUCT POSITIONING

### Blueprint Reader — Founding Story & Landing Page Opening

**Status:** Approved — use as landing page opening paragraph

**Copy:**

I paid $525 for a Les Paul CNC file set that wouldn't open.

The files were all there — body outline, neck pocket, pickup
routes, cavity depths. But the DXF version was wrong for
Fusion 360. The layers were a mess. The contours weren't
closed. AutoCAD choked on the geometry. Five hundred and
twenty-five dollars for files I couldn't use.

That was the beginning of The Production Shop.

Every decision in this platform traces back to that moment.
The R12 DXF standard. The validated contour closure. The
clean layer separation. The accuracy scorecard against known
instrument dimensions. These are not features — they are the
specific failures from that $525 file set, solved one by one.

What we deliver:

A DXF file that opens correctly in Fusion 360, VCarve,
AutoCAD, and FreeCAD. A body outline that closes. Layers
you can understand. Dimensions you can verify. A file you
can actually cut.

We validate every output against known instrument
specifications before it leaves the pipeline. We document
the accuracy. We tell you exactly what the file contains
and what it does not.

If the file does not work in your CAM software, that is
our problem to fix — not yours to work around.

**Use in:**
- blueprint-reader standalone landing page (opening)
- README.md founding story section
- Product marketing materials
- Any investor or partner introduction

**The one-sentence version:**
"I paid $525 for a Les Paul CNC file set that looked
complete but wouldn't open in Fusion 360 or AutoCAD.
The Production Shop produces clean, verified DXF files
that actually work."

---

## Research Tracks

### RESEARCH TRACK: Guitar Body as Speaker Enclosure

Coupling layer between geometry editor and acoustic stack:
  1. Body outline area integral → air volume V
  2. V → Helmholtz inverse solver → soundhole size
  3. Soundhole suggestion overlaid on canvas

Missing math sections for LUTHERIE_MATH.md:
  §37 Body outline → air volume
  §38 Depth profile model by body style

This closes the loop between outline and acoustics.
Priority: High — core product promise.
Prerequisite: Body outline editor stable.

---

### RESEARCH TRACK: Chladni Pattern Measurement

**Status:** QUEUED
**Priority:** High — unlocks mode shape data for radiation efficiency
**Repository:** tap_tone_pi

**The insight:**
tap_tone_pi currently measures frequency (eigenvalues) but not mode shape (eigenvectors).
Mode shape determines radiation efficiency via the modal area coefficient A_n.
Two guitars with identical tap tone frequencies can sound radically different
if their mode shapes differ.

**Key physics:**
- Modal area coefficient: A_n = ∫ φ_n(x,y) dS
- This is analogous to Sd (speaker diaphragm area) in loudspeaker design
- Piston-like modes (large A_n) radiate strongly
- Dipole/checkerboard modes (A_n ≈ 0) cancel and radiate weakly

**Hardware addition:**
- Exciter driver mounted to plate edge (speaker driver, modal exciter)
- Sand or salt sprinkled on plate surface
- Camera captures nodal line pattern at each resonant frequency
- Image processing extracts mode shape approximation

**Implementation path:**
1. Add exciter output to existing tap_tone_pi hardware
2. Sweep frequency while capturing video
3. Detect resonance peaks from accelerometer + camera
4. Extract nodal pattern at each peak
5. Compute A_n approximation from segmented regions
6. Report (f_n, A_n) pairs instead of just f_n

**Strategic value:**
This moves tap_tone_pi from "tap tone meter" to "radiation efficiency predictor".
Builders can optimize for modes that radiate, not just modes that exist.

**Connection to LUTHERIE_MATH.md §39-42:**
The math for modal area coefficient, brace stiffness field, radiation power,
and brace pattern optimization is documented in those sections.

---

### LUTHERIE_MATH.md — New Sections §39-42

**Status:** QUEUED
**Priority:** High — completes the modal radiation theory stack
**Document:** docs/LUTHERIE_MATH.md

**§39 Modal Area Coefficient A_n**

The modal area coefficient measures how much air a mode pushes:

```
A_n = ∫∫_S φ_n(x,y) dS
```

Where φ_n(x,y) is the normalized mode shape (eigenvector) of mode n.

**Classification by A_n:**
- Piston-like modes: A_n large → strong radiation
- Dipole modes: A_n ≈ 0 → radiation cancels
- Distributed modes: A_n moderate → partial radiation

**Critical insight:** Mode shape matters more than frequency.
Two guitars with identical tap tone frequencies can sound radically
different if one has piston-like low modes and the other has dipole modes.

**Analogy:** A_n is the soundboard equivalent of Sd (speaker diaphragm area).
A large speaker cone moves more air. A piston-like mode moves more air.

---

**§40 Brace Pattern as Stiffness Field D(x,y)**

Braces are not discrete elements — they are a spatially varying stiffness field:

```
D_total(x,y) = D_plate(x,y) + Σ_k D_brace,k(x,y)
```

Where:
- D_plate = E×h³/12(1-ν²) for isotropic, or orthotropic tensor for wood
- D_brace,k = EI_k × δ(x - x_k) along brace k centerline

**Two design dials:**
1. Thickness → frequency dial (changes f_n)
2. Bracing → mode shape dial (changes φ_n, thus A_n)

**Design implication:**
Thickness tuning is frequency-first thinking.
Brace pattern tuning is radiation-first thinking.
The latter is more powerful but requires mode shape knowledge.

---

**§41 Radiation Power P_rad**

Total radiated acoustic power from a vibrating plate:

```
P_rad = ½ρ₀c₀ Σ_n σ_n |v_n|² A_n²
```

Where:
- ρ₀c₀ = acoustic impedance of air (~415 Pa·s/m)
- σ_n = radiation efficiency of mode n (frequency-dependent)
- v_n = modal velocity amplitude
- A_n = modal area coefficient

**Key insight:** Power scales with A_n². Doubling modal area quadruples radiation.

---

**§42 Brace Pattern Optimization**

The optimization problem:

```
maximize: Σ_n w_n × A_n² × σ_n(f_n)
subject to: f_1 ∈ [f_target - Δ, f_target + Δ]
           structural constraints (deflection, stress)
           mass budget
```

Where w_n are weighting factors by frequency band (bass emphasis, treble emphasis, etc.)

**Practical approach:**
1. Start with traditional brace pattern
2. Measure (f_n, A_n) pairs via Chladni method
3. Identify modes with low A_n that should radiate
4. Modify brace pattern to convert dipole → piston character
5. Re-measure and iterate

This is the closed-loop optimization path that connects
tap_tone_pi measurement to brace design decisions.

---


---

### RESEARCH TRACK: Physical Instrument Access

**Status:** QUEUED
**Priority:** High — first published measured C value for vintage archtop

**Instruments available for measurement:**

| Instrument | Status | Target Measurements | Tool Needed |
|------------|--------|---------------------|-------------|
| **1941 Gibson L-37 archtop** | Access pending deflection jig build | Arch heights, graduation map, f-hole geometry, body dimensions | Deflection jig (simple frame + dial indicator) |

**Data destination:** `data/archtop_samples/gibson_l37_1941/`

**Plans available for digitization:**

| Plan | Status | Tool | Data Destination |
|------|--------|------|------------------|
| **Epiphone Emperor archtop** | Purchased, ready to digitize | blueprint-reader.html | `data/instrument_plans/epiphone_emperor/` |
| **12-string dreadnought** | Purchased, ready to digitize | blueprint-reader.html | `data/instrument_plans/12string_dreadnought/` |

**New LUTHERIE_MATH.md section required:**
- §45 12-string loading and top plate stiffness requirements

**Calibration opportunity:**
L-37 deflection measurements → calibrate C in §43 (arch geometric stiffness).
First published measured C value for vintage archtop — peer review material.

**Deflection jig spec:**
- Simple frame with fixed support points
- Dial indicator at center of lower bout
- Known weight applied at bridge location
- Measures static deflection under load
- Cost: ~$50 in materials

*This file is updated at the end of every sprint session.*
*Source of truth for sprint status across all terminals and chat sessions.*
