# Sprint Board — Living Kanban

**Last updated:** 2026-03-16  
**Rule:** Update this board at the end of every session.  
**Owner:** CC = Claude Code | CU = Cursor | BOTH = either

---

## Columns

| Column       | Meaning |
|-------------|---------|
| **BLOCKED** | Unresolved dependency; cannot start |
| **IN PROGRESS** | Actively being worked |
| **READY**   | Dependency met; can start now |
| **DONE**    | Complete, tested |

Every bundle, gap, and decomposition target has one row. Staging folder path when applicable.

---

## TRACK 1 — Platform / Architecture Bundles

*Source: docs/DEVELOPER_HANDOFF_2026_03_16.md*

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| B4 Instrument Project Graph (Layer 0) | DONE | CC | None | `schemas/instrument_project.py` |
| B8 Tonewood Materials System (Layer 1) | DONE | CC | B4 | `materials/` domain |
| B1 String Tension Calculator (Layer 3) | DONE | CU | B4 | `design-utilities/lutherie/string-tension/` |
| B2 Lutherie Geometry Panel (Layer 3) | DONE | CU | B4 | `design-utilities/lutherie/` |
| B3 Stiffness Index Panel (Layer 3) | DONE | CU | B8 | `design-utilities/wood-intelligence/stiffness/` |
| B9 Calculator Panel Revisions (Layer 3) | DONE | CU | B1, B2, B3 | `design-utilities/` |
| B6 Instrument Hub Shell (Layer 2) | DONE | CC | B4, B8 | `instrument-workspace/hub/` |
| B7 Bridge Lab Workspace (Layer 2) | DONE | CC | B6 | `instrument-workspace/acoustic/bridge/` |
| B5 Blueprint Save Feature (Layer 2) | DONE | CC | B4 | `design-intake/blueprint/` |
| B10 Router Wiring Final | DONE | CC | B4–B9 | `router_registry/manifest.py` (94 routers) |
| B11 Rosette/Inlay Design Tools | DEFERRED | CU | Art Studio consolidation | — |

---

## TRACK 2 — Gaps (GAP_ANALYSIS_MASTER / REMEDIATION_MASTER)

### HIGH (0 remaining — Binding & Purfling System ✅)

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| VINE-08 Bracing UI → route | DONE | CU | — | `router/index.ts`, `AppDashboardView.vue` |
| INLAY-02 HeadstockDesignerView → API | DONE | CU | — | `HeadstockDesignerView.vue`, `api/art-studio.ts` |
| INLAY-06 InlayWorkspaceShell | DONE | CU | — | `InlayWorkspaceShell.vue`, `/art-studio/inlay-workspace` |
| VEC-GAP-06 Phase 3 vectorizer frontend | DONE | CU | — | `useBlueprintWorkflow.ts`, `VectorizationControls.vue` |
| BIND-GAP-01 abalone_shell BindingMaterial | DONE | CC | — | `calculators/binding_geometry.py` enum + min_bend_radius=8mm |
| BIND-GAP-02 spanish_wave pattern registry | DONE | CC | — | purfling pattern catalog; 2.2mm × 6.0mm sinusoidal |
| BIND-GAP-03 POST /api/binding/design | DONE | CC | — | `routers/binding_design_router.py` design orchestrator |

### MEDIUM (remaining)

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| FV-GAP-05 Flying V pocket toolpath | DONE | CU | — | cam/flying_v, routers/cam/guitar/flying_v_cam_router.py |
| FV-GAP-10 Flying V neck pocket depth | DONE | CU | — | depth_validator + preflight_gate; POST /flying_v/validate |
| GAP-NEW-1 Multi-ring rosette API | DONE | CU | — | POST /api/rmos/rosette/design (rmos/rosette_cam_router.py) |
| GAP-NEW-2 Spanish wave pattern | DONE | CU | — | cam/rosette/tile_segmentation.py TilePattern.SPANISH_WAVE |
| OM-PURF-03 Purfling ledge second-pass | READY | CC | — | CAM purfling |
| OM-PURF-05 Binding corner miter G-code | READY | CC | — | CAM binding |
| OM-PURF-08 Binding width validation | READY | CC | — | Validation |
| INLAY-03 Inlay pocket depth control | DONE | CU | — | Art Studio inlay |
| BIND-GAP-04 Multi-layer channel model | READY | CC | — | binding_geometry.py MultiLayerChannel class |
| BIND-GAP-05 body-style-to-outline resolver | DONE | CC | — | binding_design_router.py resolve_body_outline() |
| EX-GAP-05..08 Explorer ref data | DEFERRED | — | Reference data | — |

### PHYS (tabled)

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| PHYS-02 Body centerline calculator | BLOCKED | CC | Hardware/data | `body/centerline.py` |
| PHYS-03 Pickup cavity mapper | BLOCKED | CC | Hardware/data | `pickup/cavity_placement.py` |

---

## TRACK 3 — Generator Remediation (GEN)

*Source: GENERATOR_REMEDIATION_PLAN (or equivalent)*

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| GEN-1 Spec stubs → project creation | DONE | CC | None | service.py, router.py |
| GEN-2 BodyConfig + acoustic_body_style_id | DONE | CC | None | instrument_project.py, service.py |
| GEN-3 from_project() factories | DONE | CC | GEN-2 | generators/cam_utils.py, stratocaster_body_generator.py, neck_headstock_config.py |
| GEN-4 CAM REST: Strat, LP, Flying V, Neck | DONE | CC | GEN-3 | routers/cam/guitar/body_gcode_router.py |
| GEN-5 Consolidate description systems | READY | CC | GEN-4 | — |
| GEN-6 Acoustic body orchestration | BLOCKED | CC | GEN-5 | — |

---

## TRACK 4 — Decomposition (files >500 LOC)

*Source: docs/DECOMPOSITION_BACKLOG_2026_03_16.md, REMEDIATION_MASTER Part 3*

### Python

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| herringbone_embedded_quads.py (1241 LOC) | READY | CU | None | Archive / split |
| generative_explorer_viewer.py (674) | READY | CU | None | Archive |
| router_registry/manifest.py (684) | READY | CC | None | Split by domain |
| modern_pattern_generator.py (682) | READY | CC | None | Geometry vs rendering |
| neck_headstock_config.py (661) | READY | CC | GEN-3 | Extract presets to JSON |
| job_queue/queue.py (631) | READY | CC | None | Split queue vs execution |
| binding_geometry.py (781) | READY | CC | None | Extract helpers |
| cavity_position_validator.py (705) | READY | CC | None | Split validation |
| Remaining >500 LOC (per backlog) | READY | BOTH | — | See DECOMPOSITION_BACKLOG |

### Vue

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| RosetteWheelView.vue (1240) | READY | CU | None | SoundholeRosetteShell |
| MachineManagerView.vue (1014) | READY | CU | None | Extract panels |
| ToolpathCanvas3D.vue (997) | READY | CU | None | Extract camera/mesh |
| ToolpathAnnotations.vue (893) | READY | CU | None | Sub-components |
| VCarveView.vue (878) | READY | CU | None | Manufacturing layer |
| Remaining >500 LOC (per backlog) | READY | CU | — | See DECOMPOSITION_BACKLOG |

---

## TRACK 5 — Art Studio / Cursor consolidation

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| SoundholeRosetteShell (consolidate rosette/soundhole/purfling/binding) | DONE | CU | None | views/art-studio |
| B11-A v5 rosette features → SoundholeRosetteShell | BLOCKED | CU | SoundholeRosetteShell | — |
| VCarveView + ReliefCarvingView → manufacturing layer | DONE | CU | None | — |
| Lab cleanup: DELETE (CadLayoutDemo, NavProto, etc.) | DONE | CU | None | views/ |
| Lab cleanup: DEDUPLICATE (AdaptivePocketLab, CandidateList) | DONE | CU | None | — |
| Lab cleanup: PROMOTE (HelicalRampLab, PolygonOffsetLab) | DONE | CU | None | — |

---

## TRACK 6 — AI / Blueprint pipeline

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| Phase 3 static file check (serve outputs like Phase 2) | READY | CC | VEC-GAP-06 done | services/api blueprint router |
| POST /api/blueprint/from-generated-image (CAS → blueprint) | READY | CC | Vision router | — |
| B11-B POST /api/vision/generate-rosette-svg | DEFERRED | CC | AI-1, AI-2 | — |

---

## TRACK 7 — Build Chronicle / Event log

*Gate: after GEN-1..GEN-5 and generator decomposition*

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| BC-1 Alembic 0002_project_event_log.sql | READY | CC | B4 done | db/migrations |
| BC-2 project_events/ event log service | BLOCKED | CC | BC-1 | — |
| BC-3 acoustic_engine/ prediction + dataset | BLOCKED | CC | BC-2 | — |
| BC-4 BuildChronicleShell.vue | BLOCKED | CU | BC-2 | — |
| BC-5 AcousticPredictionPanel.vue | BLOCKED | CU | BC-3 | — |

---

## TRACK 8 — Safety / Technical debt

| Item | Status | Owner | Dependency | Staging / path |
|------|--------|-------|-------------|----------------|
| Test collection errors (13 → 0) | IN PROGRESS | — | — | — |
| Broad exceptions in safety paths (11 files) | DONE | CU | None | cam/ + rmos/ (dxf_advanced_validation, fret_slots_router, rosette_cam_router, mvp_router, safety_router; store_delete intentional + comment) |
| Test Collection Errors baseline | READY | — | — | CI |

---

## SESSION LOG

*Append one line per session. Never delete.*

| Date | Session | Completed | Next |
|------|---------|-----------|------|
| 2026-03-16 | Gap sprint (VINE-08, INLAY-02, INLAY-06) | InlayWorkspaceShell, bracing route, headstock API | Commit Session 7 |
| 2026-03-16 | VEC-GAP-06 Phase 3 frontend | useBlueprintWorkflow Phase 3 call, pipeline toggle, phase3/info | Phase 3 static file check (AI-1) |
| 2026-03-16 | Sprint board creation | docs/SPRINT_BOARD.md added | Update at end of every session |
| 2026-03-16 | INLAY-03 + CU-A4 | Pocket depth control (ArtStudioInlay); routes/nav removed for dev scratch views; deprecation comments added | — |
| 2026-03-16 | CU-A5 + CU-A6 | DEDUPLICATE: deprecated AdaptivePocketLab, ManufacturingCandidateList; useKeyboardShortcuts canonical. PROMOTE: HelicalRampLab → CAM nav, PolygonOffsetLab → Design nav; routes added | — |
| 2026-03-16 | CU-A1 SoundholeRosetteShell | SoundholeRosetteShell.vue at /art-studio/soundhole-rosette-workspace; 4 tabs (Rosette, Soundhole, Purfling, Binding); nav + deprecation notes; build passed | — |
| 2026-03-16 | CU-A3 VCarve/Relief → CAM nav | V-Carve and Relief Carving nav moved from Art Studio to CAM Tools; route paths unchanged; comments added | — |
| 2026-03-16 | Bundle integration 4789a448 | B4-B10 all integrated, 45 files +11689 lines, staging folders deleted, 94 routers registered | GEN-1 ready to start |

---
| 2026-03-16 | GEN-1 complete | model_id param, 19 guitar specs, dcad0976 | GEN-2 ready |
| 2026-03-16 | GEN-2 complete | BodyConfig schema, body_config seeding, v1.1, 909ecfed | GEN-3 blocked on GEN-2 |
| 2026-03-16 | Broad exception cleanup (Files 4–6 + board) | mvp_router, safety_router narrowed; store_delete intentional comment; pytest safety/override/dxf-to-grbl; TRACK 8 + gate updated | — |
| 2026-03-17 | FV-GAP-05, FV-GAP-10 | Flying V CAM router (spec, control_cavity, neck_pocket, pickup, validate); depth validation + preflight; pytest -k flying 19 passed | — |
| 2026-03-17 | GAP-NEW-1, GAP-NEW-2 | POST /api/rmos/rosette/design multi-ring; spanish_wave in TilePattern; Martin OO 3-ring: 3 job_ids, 1114+646+994 lines | — |

| 2026-03-16 | GEN-3 complete | cam_utils.py, from_project() on StratocasterBodyGenerator + NeckDimensions; tests pass | GEN-4 ready |
| 2026-03-16 | GEN-4 complete | body_gcode_router.py (4 endpoints); CAM_READY_MODELS; registry updated; Strat+LP+FV+Neck | GEN-5 ready |
| 2026-03-17 | BIND-GAP-01..05 added | 5 gaps: abalone_shell, spanish_wave, /api/binding/design, multi-layer channel, body-outline resolver | — |
| 2026-03-17 | BIND-GAP-01, BIND-GAP-02 impl | ABALONE_SHELL enum + 8mm bend radius; PurflingStripPattern enum + spanish_wave (2.2×6.0mm sinusoidal); 6 binding tests pass | GEN-5 needs spec |
| 2026-03-17 | BIND-GAP-03, BIND-GAP-05 impl | POST /api/binding/design orchestrator + resolve_body_outline(); 95 routers; om_000→1739mm perimeter | — |

## DEPLOYMENT GATE

| Item | Status |
|------|--------|
| 0 HIGH gaps remaining | ✅ |
| B4 Instrument Project Graph integrated | ✅ |
| GEN-1 connected | ✅ |
| Phase 3 static file check | 🟡 Next |
| Safety-path broad exceptions fixed | ✅ |
| No test collection errors | 🟡 Verify |
| MEDIUM gaps ≤5 (excl. deferred) | 🟡 |

---

*Updated at the end of every session. This is the follow-up mechanism.*
