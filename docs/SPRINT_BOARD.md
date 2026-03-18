# Sprint Board

**Last Updated:** 2026-03-18
**Gap Count:** 112/120 resolved (8 remaining)

---

## Current Sprint: Binding & Purfling Completion

### Completed This Session

| Gap | Description | Status |
|-----|-------------|--------|
| OM-PURF-03 | Purfling ledge second-pass + neck purfling | DONE |
| OM-PURF-05 | Binding corner miter G-code | DONE |
| OM-PURF-08 | Channel depth probe cycle (G38.2) | DONE |

### MEDIUM Priority Gaps - Status

| Gap | Description | Status |
|-----|-------------|--------|
| BIND-GAP-04 | Binding strip length calculator | **DONE** ✓ |
| CCEX-GAP-05 | Archtop graduation thickness map | Deferred (need reference measurements) |
| CCEX-GAP-06 | Tap tone frequency targets | Deferred (need reference measurements) |
| CCEX-GAP-07 | Bracing pattern library | Deferred (need reference measurements) |
| CCEX-GAP-08 | Sound port placement calculator | Deferred (need reference measurements) |
| INLAY-07 | Inlay pocket depth control | Done |
| VEC-GAP-06 | Vectorizer contour election | Done |

### Next Up

> **All 8 remaining gaps are blocked on external data:**
> - 6 Explorer reference measurements (EX-GAP-05 through EX-GAP-10)
> - 1 VEC-GAP-08: Wire OCR dimensions from Phase 3.6 (LOW priority)
> - 1 Other: miscellaneous blocked item
>
> **Actionable work:** Test coverage improvements, refactoring, documentation.

---

## TRACK 10 — Acoustic Plate Design System

**Source:** tap-tone-pi design package + D'Aquisto data

| Task | Description | Status | Owner |
|------|-------------|--------|-------|
| PORT-001 | Copy tap_tone_pi/design/ to calculators/plate_design/ | **DONE** ✓ | CC |
| PORT-002 | Create POST /api/acoustics/plate/analyze endpoint | **DONE** ✓ | CC |
| PORT-003 | Create POST /api/acoustics/plate/coupled endpoint | **DONE** ✓ | CC |
| PORT-004 | Create POST /api/acoustics/plate/solve endpoint | **DONE** ✓ (via /analyze) | CC |
| ARCH-001 | D'Aquisto graduation data digitized to JSON | **DONE** ✓ (0d65d043) | CC |
| ARCH-002 | Normalized archtop graduation template | **DONE** ✓ (0d65d043) | CC |
| ARCH-003 | archtop_graduation.py connecting graduation profile to plate physics | **DONE** ✓ (ac56ec6b) | CC |
| ARCH-004 | Wire plate thickness calculator into Smart Guitar module body design | **DONE** ✓ | CC |

**Key insight (documented):** Archtop graduation proportions are consistent across instruments (D'Aquisto, Benedetto, D'Angelico). Shape = normalized template (edge=0.0 → apex=1.0). Scale = set by plate_design thickness calculator from wood properties and target frequency. `arch_height` is a separate parameter (approx 1:15 to 1:18 body width ratio) — not derived from thickness.

**D'Aquisto reference data:**
- **Top:** edge 3mm, lower bout 4-4.5mm, apex 5/8" arch height
- **Back:** edge 3mm, lower bout 4-4.5mm, arch 3/4" below waist

**Gate before implementation:** PORT-001 must be verified in repo first. If not there, port from tap-tone-pi before anything else.

---

## Session Log

| Date | Gaps Closed | Notes | Next |
|------|-------------|-------|------|
| 2026-03-18 | — | **docs(sprint): reconcile gap count + test coverage.** SPRINT_BOARD.md aligned with GAP_ANALYSIS_MASTER: 112/120 (8 remaining). Categories table fixed. GEN-5 phantom documented. Added 53 tests: test_rmos_lineage_service.py (28 tests, lineage.py 0%→100%), test_rmos_store_completeness.py (25 tests, store_completeness.py 23%→85%). Fixed bridge_break_angle.py CARRUTH_MIN_DEG import. | — |
| 2026-03-18 | — | **test(coverage): RMOS domain test suite expansion.** Added 125 tests across 3 modules: test_saw_cam_guard.py (28 tests, saw_cam_guard.py 0%→100%), test_constraint_search.py (21 tests, constraint_search.py 0%→100%), test_store_filter.py (76 tests, store_filter.py 34%→100%). Tests cover: saw safety guards (rim speed, bite, heat, deflection, kickback), constraint-first rosette search (Mode B), index metadata filtering. | — |
| 2026-03-18 | BIND-GAP-04 | **feat(binding): add binding strip length calculator.** calculate_binding_strip_length() in binding_geometry.py: InstallationMethod enum (SINGLE_CONTINUOUS, TOP_AND_BACK, SECTIONAL, TRADITIONAL_ACOUSTIC), BindingStripEstimate dataclass, miter/overlap/handling waste allowances, order length rounding to 50mm. POST /api/binding/strip-length endpoint in binding_design_router.py. 15 tests passing. | doc cleanup |
| 2026-03-18 | — | **feat(cam-workspace): wire machine selector to live backend.** CamWorkspaceView.vue: add MachineInfo interface, machines ref, fetchMachines() on mount. Dynamic machine dropdown from GET /api/cam-workspace/machines. Machine specs (envelope, z_travel, spindle RPM, dialect) displayed from selectedMachine computed. Pre-selects bcam_2030a. Evaluate/generate/download endpoints already wired. npm run build pass. | — |
| 2026-03-18 | — | **INLAY-03/INLAY-07 labeling fix:** GAP_ANALYSIS_MASTER: INLAY-07 added to New Gaps Resolved and MEDIUM list (pocket depth control — pocketDepth/pocket_depth_mm wired). INLAY-03 confirmed Resolved (FretMarkersView superseded by InlayWorkspaceShell Stage 2). FretMarkersView.vue deprecation comment updated. No FretMarkers route or nav link present. SPRINT_BOARD: INLAY-07 \| pocket depth \| Done already correct. | — |
| 2026-03-18 | — | **fix(reliability): consolidate safety_critical, wire router health, add coverage floor** (c0340737). app/core/safety.py: merged signature preservation + _is_safety_critical marker. app/safety/__init__.py: pure re-export (deprecated). health_router.py: GET /health/routers + router_count/errors in /health. pytest.ini: --cov-fail-under=60 for safety paths. Coverage: 57% (cnc_preflight 0%, explain 28%). | — |
| 2026-03-18 | — | **fix(ux): usability improvements from systems review.** useConfirm composable replaces 12 window.confirm call sites in 10 files (injectable, modal-ready). Global error boundary in App.vue (onErrorCaptured). Toast consolidation: 3 duplicate systems deprecated, useToastStore canonical (uiToastStore, Toast.vue, rmos/useToast + ToastHost). useHeadstockTransition.ts: ** → Math.pow for esbuild compat. npm run build pass. | — |
| 2026-03-18 | PORT-001 | **PORT-001 executed:** plate_design already in calculators/plate_design/. plate_router aligned with spec: POST /analyze (material, body_style, target_hz, plate top\|back) → analyze_plate() → PlateThicknessResult; POST /coupled → CoupledSystemResult. GET /materials, GET /body-styles. test_thickness_calculator.py added. Router tags acoustics-plate; manifest registered. Import verify: sitka E_L, OM target. | Run pytest; commit |
| 2026-03-18 | ARCH-001, ARCH-002 | **TRACK 10 archtop graduation data:** instrument_geometry/models/archtop/ added: daquisto_graduation_measurements.json (digitized from DAquisto-Measurements-2.jpg; top 3–4.5mm, back 2–4.5mm, top arch 5/8 in, back arch 3/4 in), archtop_graduation_template.json (normalized zones 0–1, usage formula edge + (apex-edge)*norm, arch_height_ratio 1:15–1:18). | — |
| 2026-03-18 | — | **E_C_gpa + calculator context:** TonewoodEntry: E_C_gpa field and R_anis computed (E_L/E_C). 14 species in luthier_tonewood_reference.json with E_C_gpa (tap-tone-pi values). calculator-registry.ts + useContextTools; CamWorkspaceView collapsed Tools slot; Calculator Hub removed from primary nav (still at /calculators). npm run build pass. | — |
| 2026-03-18 | — | **Interactive_Neck and Cam _Modules integrated:** Neck composables (useNeckTaper, useNeckProfile, useCamSpec, useFretboard, useHeadstockTransition, drawCamOverlay) → design-utilities/lutherie/neck/. Neck panels (NeckTaperPanel, FretboardPanel, NeckProfilePanel, HeadstockTransitionPanel, CamSpecPanel) → components/cam/neck/. NeckView.vue, NeckOpPanel.vue, GateStatusBadge.vue, GcodePreviewPanel.vue; useDxfImport.ts, useExportDxf.ts; headstock views (ImportView, WorkspaceView, ParametricView, ConfiguratorView) → views/cam/headstock/. stores/neck.ts + useKonvaCanvas.ts added for NeckView. Route /cam/neck (CamNeck); nav "Neck Designer" after CAM Workspace. Backend files (cam_workspace_router, neck_profile_export, fretboard_export, headstock_transition_export, dxf_export, photo_vectorizer_router) flagged for Claude Code — not integrated. npm run build pass. | — |
| 2026-03-18 | — | **CAM Workspace Phase 1:** CamWorkspaceView.vue 5-step wizard (machine context, OP10/40/45/50, summary). GateStatusBadge.vue, GcodePreviewPanel.vue. Route /cam/workspace; CAM Workspace first in CAM nav. Mock GREEN on generate; YELLOW acknowledge; RMOS placeholder Phase 4. npm run build pass. | — |
| 2026-03-17 | — | **SmartGuitarShell.vue:** Module 5 shell at views/smart-guitar/SmartGuitarShell.vue with 5 tabs (Body Design → Instrument Hub, Electronics Layout, RPi5 Cavity, WiFi & Antenna, Export & BOM). Route /smart-guitar (SmartGuitar) in place. Nav: Smart Guitar → /smart-guitar. Added alias /instrument-hub → InstrumentGeometry for shell link. npm run build pass. | — |
| 2026-03-17 | — | **INLAY-03/INLAY-07 labeling fix:** GAP_ANALYSIS_MASTER: Added INLAY-07 (Inlay pocket depth control, Resolved). INLAY-03 marked Resolved (FretMarkersView superseded by InlayWorkspaceShell Stage 2). FretMarkersView.vue deprecated (comment only); route /art-studio/fret-markers removed from router. No Fret Markers nav link in AppDashboardView. SPRINT_BOARD: INLAY-03→INLAY-07 for pocket depth. npm run build pass. | — |
| 2026-03-17 | — | **router_registry/manifest.py decomposed** into domain manifests: cam_manifest.py (35), art_studio_manifest.py (14), rmos_manifest.py (15), business_manifest.py (15), system_manifest.py (16). manifest.py assembles ROUTER_REGISTRY/ROUTER_MANIFEST in &lt;80 lines. 95 RouterSpec entries unchanged; load_all_routers verified. | — |
| 2026-03-17 | — | **Audit Log nav:** No shop-floor audit route in router (only /tools/audio-analyzer/ingest). Removed Audit Log link from Shop Floor; kept Manufacturing Runs, Job Queue. **presets.py split:** preset_definitions.py (580 lines), preset_registry.py (41 lines), presets.py shim (18 lines). Imports unchanged. | — |
| 2026-03-17 | — | **FILE 2:** job_queue split into queue_storage.py (persistence, CRUD), queue_execution.py (workers, handlers, retries), queue.py orchestrator (~190 lines). All queue tests passing. **Nav:** AppDashboardView.vue reorganized into 5 modules: Design, Art Studio, CAM, Shop Floor, Smart Guitar. Routes unchanged; npm run build pass. | — |
| 2026-03-17 | — | useWoodGrain.ts: import moved to top (composables). InlayWorkspaceShell: Stage 0 Headstock Design (template + species + DXF import + preview + Next). useDxfImport composable; grain provided for children. npm run build pass. | — |
| 2026-03-17 | OM-PURF-03/05/08 | Purfling second-pass, corner miter G-code, G38.2 channel depth probe. 27 tests passing. | — |
| 2026-03-16 | BIND-GAP-01/02/03/05 | Binding design orchestration endpoint, body outline resolver, material bend radius validation | OM-PURF gaps |
| 2026-03-15 | 93 gaps | Major sprint day - platform architecture integrated | Binding module |

---

## Gap Categories Summary

| Category | Resolved | Remaining |
|----------|----------|-----------|
| CAM Core | 28 | 0 |
| Binding/Purfling | 12 | 0 |
| Generators | 11 | 0 |
| Instrument Geometry | 15 | 0 |
| Art Studio | 14 | 0 |
| Vision/Vectorizer | 9 | 1 |
| RMOS | 8 | 0 |
| Acoustics (TRACK 10) | 8 | 0 |
| Other | 6 | 1 |
| Explorer (blocked) | 0 | 6 |
| **Total** | **112** | **8** |

---

## Deferred Items

### CCEX (Carved/Carved Expert) Gaps
These gaps require physical reference measurements from actual instruments:
- CCEX-GAP-05: Archtop graduation thickness maps
- CCEX-GAP-06: Tap tone frequency targets for various body sizes
- CCEX-GAP-07: Bracing pattern dimensional data
- CCEX-GAP-08: Sound port acoustic modeling data

**Action Required:** Capture measurements from reference instruments before implementation.

### Explorer Reference Measurements (EX-GAP-05 through EX-GAP-10)
Blocked on physical reference measurements from actual Explorer instruments.

### Hardware Manufacturer Specs (PHYS-05, PHYS-06)
Blocked on manufacturer data sheets for specific hardware components.

### Phantom Gap IDs
The following gap IDs appeared in planning documents but were never formally defined:
- **GEN-5** ("Generator factory pattern completion"): Referenced in Next Up for 14+ sessions but never existed in GAP_ANALYSIS_MASTER. All 11 generator gaps (GEN-01 through GEN-11) were resolved. This was a placeholder that escaped cleanup.
