# Changelog

All notable changes to Luthier's Tool Box will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### 🔧 Changed

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

### 🆕 Added

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

## [Unreleased]

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

## Version History Legend

- **A_N.x**: Alpha releases (A_N.1, A_N.2, ...)
- **B_x**: Beta releases (B_1, B_2, ...)
- **1.x**: Stable releases (1.0, 1.1, ...)

---

## Links

- **Roadmap**: [A_N_BUILD_ROADMAP.md](./A_N_BUILD_ROADMAP.md)
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Contributing**: [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Quick Start**: [README.md](./README.md#-quick-start)

---

**A_N.1 Release Date**: November 20, 2025  
**Priority 1 Status**: ✅ 100% Complete (P1.1-P1.4)  
**Test Coverage**: 12/12 CAM Essentials tests passing  
**Production Ready**: CAM Core, Multi-Post Export, Adaptive Pocketing
