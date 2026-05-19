# CAM Pipeline — Developer Handoff

**Date:** 2026-05-06  
**Scope:** Full CAM pipeline audit — simulation system, workspace views, DXF-to-G-code flow  
**Purpose:** Annotated reference for developers working on CAM production readiness

---

## Executive Summary

The CAM pipeline has **two parallel paths** at different maturity levels:

| Path | View | Simulation | RMOS | Production Ready |
|------|------|------------|------|------------------|
| DXF-to-G-code | DxfToGcodeView | ToolpathPlayer integrated | Full artifacts | 90% |
| Neck Pipeline | CamWorkspaceView | **Not integrated** | None | 70% |

**The simulation system (ToolpathPlayer) is production-ready.** It's not "inactive" — it's fully wired to `DxfToGcodeView`. The gap is that `CamWorkspaceView` never integrated it.

---

## Part 1: Simulation System Status

### What Works

The G-code simulation infrastructure is solid:

| Component | Location | Status |
|-----------|----------|--------|
| G-code state machine | `services/api/app/util/gcode/simulator.py` (375 LOC) | Production-ready |
| G-code lexer | `services/api/app/util/gcode/lexer.py` (62 LOC) | Production-ready |
| Arc geometry | `services/api/app/util/gcode/geometry.py` | Production-ready |
| ToolpathPlayer | `packages/client/src/components/cam/ToolpathPlayer.vue` (393 LOC) | Production-ready |
| ToolpathCanvas 2D | `packages/client/src/components/cam/ToolpathCanvas.vue` (798 LOC) | Production-ready |
| ToolpathCanvas 3D | `packages/client/src/components/cam/ToolpathCanvas3D.vue` (997 LOC) | Production-ready |
| Player store | `packages/client/src/stores/useToolpathPlayerStore.ts` (526 LOC) | Production-ready |
| Subcomponents | `packages/client/src/components/cam/toolpath-player/` (35 files) | Production-ready |

**Backend tests:** 28 passing tests in `test_gcode_simulate.py`

### What's Broken

#### 1. Metrics Endpoint — Production Bug

```
Location: services/api/app/routers/simulation_consolidated_router.py
Endpoint: POST /api/cam/sim/metrics
Issue: Router/schema mismatch
```

8 tests in `test_simulation_endpoint_smoke.py` are marked xfail:

```python
# Lines 26-30
metrics_production_bug = pytest.mark.xfail(
    reason="Production bug: router/schema mismatch in metrics endpoint",
    raises=(AttributeError, TypeError, PydanticValidationError, Exception),
    strict=False
)
```

Applied at lines: 65, 294, 301, 308, 316, 327, 335, 345

**Resolution options:**
- (A) Fix the schema mismatch in `SimMetricsIn`/`SimMetricsOut` models
- (B) Remove `/sim/metrics` endpoint if energy/time metrics aren't needed

#### 2. Dead Duplicate Router

Two files with the same name exist:

| Location | LOC | Status |
|----------|-----|--------|
| `services/api/app/routers/simulation_consolidated_router.py` | 273 | LIVE — registered via manifest |
| `services/api/app/cam/routers/simulation/simulation_consolidated_router.py` | 115 | DEAD — aggregator import commented out |

**Action:** Delete `services/api/app/cam/routers/simulation/` directory entirely.

The dead router exists because `app/cam/routers/aggregator.py` has the import commented out:
```python
# from .simulation import router as simulation_router
```

#### 3. Working Endpoints

These work correctly:
- `POST /api/cam/sim/gcode` — JSON body simulation
- `POST /api/cam/sim/upload` — File upload simulation

---

## Part 2: CAM Workspace Views

### DxfToGcodeView — PRODUCTION READY

**Location:** `packages/client/src/views/DxfToGcodeView.vue`

This is the gold standard for CAM integration:

```
User Flow:
Upload DXF → Configure params → Generate G-code → ToolpathPlayer preview → Download

Integration Points:
├── POST /api/rmos/wrap/mvp/dxf-to-grbl (generation)
├── ToolpathPlayer (simulation)
├── RMOS artifacts (DXF input, G-code, CAM plan)
├── Risk badge + override governance
└── Run comparison with history
```

**Composable:** `packages/client/src/components/dxf/useDxfToGcode.ts` — handles full workflow

**Minor gaps:**
- Risk level always GREEN (feasibility engine not wired)
- No timeout handling if ToolpathPlayer service unavailable

### CamWorkspaceView — NEEDS SIMULATION INTEGRATION

**Location:** `packages/client/src/views/cam/CamWorkspaceView.vue`

6-step wizard for neck operations:
1. OP10 Truss rod channel
2. OP40 Profile rough
3. OP45 Profile finish
4. OP50 Fret slots
5. Summary & download
6. (Configuration sidebar)

**What works:**
- All backend endpoints pass (16/16 smoke tests)
- Gate evaluation via `/api/cam-workspace/neck/evaluate`
- G-code generation via `/api/cam-workspace/neck/generate/{op}`
- Full program via `/api/cam-workspace/neck/generate-full`

**Critical gap:** `GcodePreviewPanel` shows raw G-code text, not ToolpathPlayer visualization.

```
Current:
┌─────────────────────────────────────┐
│  G0 X0 Y0 Z5                        │
│  G1 Z-2 F500                        │
│  G1 X100 F1000                      │
│  ...                                │
└─────────────────────────────────────┘

Should be:
┌─────────────────────────────────────┐
│  ┌───────────────────────────────┐  │
│  │   ToolpathPlayer              │  │
│  │   [▶] [||] ─────●───── 2:34   │  │
│  │   3D visualization            │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Other gaps:**
- No RMOS run creation (no artifact trail)
- State lost on page refresh (no localStorage)
- No comparison feature
- Error handling lacks user feedback (silent failures)

### DxfToGcodeWizard — BROKEN STUB

**Location:** `packages/client/src/components/wizards/DxfToGcodeWizard.vue`

**Status:** Calls non-existent endpoints:
- `POST /api/v1/dxf/upload` — 404
- `POST /api/v1/dxf/cam/gcode` — 404

**Action:** Either wire to real endpoints or delete. Currently a trap for users who navigate to it.

---

## Part 3: Backend Pipeline

### DXF-to-GRBL Pipeline

**Location:** `services/api/app/rmos/mvp_router.py`  
**Endpoint:** `POST /api/rmos/wrap/mvp/dxf-to-grbl`

```python
# Flow:
1. Read DXF via ezdxf
2. Extract closed polylines from layer
3. Call adaptive/plan_router.plan() for toolpath
4. Emit GRBL G-code
5. Attach artifacts to RMOS run
```

**Limitations:**
- Only LWPOLYLINE + POLYLINE (no arcs, splines)
- Layer filtering simplistic (hardcoded "0" or exact match)
- Tool diameter fixed in form (no tool library lookup)
- No geometry validation (self-intersections, gaps)

### CamWorkspace Router

**Location:** `services/api/app/routers/cam/cam_workspace_router.py`

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /machines` | List machines | Hardcoded list |
| `GET /status` | Pipeline availability | Works |
| `GET /neck/operations` | List ops | Works |
| `POST /neck/evaluate` | Gate checks | Works |
| `POST /neck/generate/{op}` | Single op G-code | Works |
| `POST /neck/generate-full` | Full assembly | Works |

**Test coverage:** `test_cam_workspace_smoke.py` — 16/16 passing

---

## Part 4: File Reference

### Frontend — Production Ready

```
packages/client/src/
├── views/
│   ├── DxfToGcodeView.vue              ← PRODUCTION READY
│   └── cam/CamWorkspaceView.vue        ← Needs ToolpathPlayer
├── components/
│   ├── cam/
│   │   ├── ToolpathPlayer.vue          ← PRODUCTION READY
│   │   ├── ToolpathCanvas.vue          ← PRODUCTION READY (798 LOC)
│   │   ├── ToolpathCanvas3D.vue        ← PRODUCTION READY (997 LOC)
│   │   ├── GcodePreviewPanel.vue       ← Needs ToolpathPlayer integration
│   │   └── toolpath-player/            ← 35 subcomponents
│   ├── dxf/
│   │   └── useDxfToGcode.ts            ← PRODUCTION READY
│   └── wizards/
│       └── DxfToGcodeWizard.vue        ← BROKEN STUB, delete or fix
└── stores/
    └── useToolpathPlayerStore.ts       ← PRODUCTION READY (526 LOC)
```

### Backend — Production Ready (with noted exceptions)

```
services/api/app/
├── routers/
│   ├── simulation_consolidated_router.py   ← LIVE (metrics endpoint broken)
│   └── cam/
│       └── cam_workspace_router.py         ← PRODUCTION READY
├── cam/routers/simulation/
│   └── simulation_consolidated_router.py   ← DEAD, DELETE THIS
├── rmos/
│   └── mvp_router.py                       ← DXF-to-GRBL pipeline
└── util/gcode/
    ├── simulator.py                        ← PRODUCTION READY
    ├── lexer.py                            ← PRODUCTION READY
    └── geometry.py                         ← PRODUCTION READY
```

### Tests

```
services/api/tests/
├── test_gcode_simulate.py              ← 28 passing
├── test_cam_workspace_smoke.py         ← 16 passing
└── test_simulation_endpoint_smoke.py   ← 8 xfail (metrics bug)
```

---

## Part 5: Action Items by Priority

### P0 — Before Ship

| Task | Effort | Files |
|------|--------|-------|
| Integrate ToolpathPlayer into CamWorkspaceView | 4-8h | GcodePreviewPanel.vue |
| Delete dead router directory | 5min | `app/cam/routers/simulation/` |
| Delete or fix DxfToGcodeWizard | 1h | DxfToGcodeWizard.vue |

### P1 — Before Beta

| Task | Effort | Files |
|------|--------|-------|
| Fix metrics endpoint OR remove it | 2-4h | simulation_consolidated_router.py, sim_metrics.py |
| Remove xfail markers after metrics fix | 30min | test_simulation_endpoint_smoke.py |
| Add localStorage persistence to CamWorkspaceView | 2h | CamWorkspaceView.vue |
| Wire RMOS feasibility engine | 4h | mvp_router.py |
| Create RMOS runs for CamWorkspaceView | 4h | cam_workspace_router.py |

### P2 — Polish

| Task | Effort | Files |
|------|--------|-------|
| Add toast notifications for errors | 2h | Various |
| Support complex DXF entities (arcs, splines) | 8h | mvp_router.py |
| Add tool library lookup | 4h | cam_workspace_router.py |
| Integration tests for full pipeline | 8h | tests/ |

---

## Part 6: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────┐        ┌─────────────────────┐             │
│  │  DxfToGcodeView     │        │  CamWorkspaceView   │             │
│  │  ✓ ToolpathPlayer   │        │  ✗ ToolpathPlayer   │ ← FIX THIS  │
│  │  ✓ RMOS artifacts   │        │  ✗ RMOS artifacts   │             │
│  │  ✓ Risk governance  │        │  ✗ Persistence      │             │
│  └─────────┬───────────┘        └─────────┬───────────┘             │
│            │                              │                          │
│            ▼                              ▼                          │
│  ┌─────────────────────┐        ┌─────────────────────┐             │
│  │  useDxfToGcode.ts   │        │  (direct fetch)     │             │
│  └─────────┬───────────┘        └─────────┬───────────┘             │
│            │                              │                          │
├────────────┼──────────────────────────────┼──────────────────────────┤
│            │         BACKEND              │                          │
├────────────┼──────────────────────────────┼──────────────────────────┤
│            ▼                              ▼                          │
│  ┌─────────────────────┐        ┌─────────────────────┐             │
│  │  /api/rmos/wrap/    │        │  /api/cam-workspace │             │
│  │  mvp/dxf-to-grbl    │        │  /neck/generate/*   │             │
│  └─────────┬───────────┘        └─────────┬───────────┘             │
│            │                              │                          │
│            ▼                              ▼                          │
│  ┌─────────────────────────────────────────────────────┐            │
│  │              util/gcode/simulator.py                 │            │
│  │              (state machine, arc interp)             │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  /api/cam/sim/gcode     ← Works                     │            │
│  │  /api/cam/sim/upload    ← Works                     │            │
│  │  /api/cam/sim/metrics   ← BROKEN (xfail)            │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Decision Log

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Metrics endpoint | (A) Fix schema, (B) Remove endpoint | B if energy metrics not needed |
| DxfToGcodeWizard | (A) Wire to real endpoints, (B) Delete | B — DxfToGcodeView is the real UI |
| CamWorkspaceView simulation | (A) Integrate ToolpathPlayer, (B) Keep text preview | A — users need visual feedback |

---

## Appendix: Verification Commands

```bash
# Confirm working simulation tests
cd services/api
pytest tests/test_gcode_simulate.py -v

# Confirm workspace tests
pytest tests/test_cam_workspace_smoke.py -v

# See xfail markers
grep -n "metrics_production_bug" tests/test_simulation_endpoint_smoke.py

# Confirm dead router not wired
grep -rn "simulation_consolidated_router" app/cam/routers/

# Count ToolpathPlayer subcomponents
ls packages/client/src/components/cam/toolpath-player/ | wc -l

# Verify ToolpathPlayer integration in DxfToGcodeView
grep -n "ToolpathPlayer" packages/client/src/views/DxfToGcodeView.vue

# Verify ToolpathPlayer NOT in CamWorkspaceView
grep -n "ToolpathPlayer" packages/client/src/views/cam/CamWorkspaceView.vue
```

---

*Handoff created: 2026-05-06*  
*Supersedes: CAM_ANIMATED_SIMULATION_STATUS_2026-05-06.md (inaccurate claims)*  
*Reference: CAM_SIMULATION_AUDIT_2026-05-06.md (verification source)*
