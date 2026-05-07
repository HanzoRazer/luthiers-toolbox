# CAM Animated Simulation — Build Status

**Date:** 2026-05-06  
**Status:** Production-ready with mature feature set

---

## Executive Summary

The CAM animated simulation system is **substantially complete** with a full vertical slice from G-code parsing through animated 3D visualization. The system has gone through P1-P6 enhancement phases and includes memory management, caching, multi-tool support, and Three.js 3D rendering.

---

## Test Status

```
67 passed, 8 xfailed
Coverage: 21.99%
```

All critical paths tested. The 8 xfailed are expected failures (edge cases deferred).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend                                  │
├─────────────────────────────────────────────────────────────────┤
│  ToolpathPlayer.vue          ← Main orchestrator                │
│    ├─ ToolpathCanvas.vue     ← 2D canvas (LOD, heatmap)        │
│    ├─ ToolpathCanvas3D.vue   ← Three.js 3D (orbit, depth)      │
│    ├─ ControlsBarWrapper     ← Play/pause/scrub/speed          │
│    ├─ PlayerHudBar           ← G-code line, Z, feed, M-code    │
│    └─ PanelsLayer            ← Tool legend, export, audio      │
│                                                                  │
│  useToolpathPlayerStore.ts   ← Playback state (RAF animation)  │
│    ├─ segments, bounds       ← Parsed move data                │
│    ├─ playState, currentTimeMs, speed                          │
│    ├─ toolPosition (computed)                                   │
│    └─ memoryInfo, parseProgress                                │
├─────────────────────────────────────────────────────────────────┤
│                        Backend                                   │
├─────────────────────────────────────────────────────────────────┤
│  simulation_consolidated_router.py                              │
│    ├─ POST /sim/gcode        ← JSON body simulation            │
│    ├─ POST /sim/upload       ← File upload simulation          │
│    └─ POST /sim/metrics      ← Energy/time metrics             │
│                                                                  │
│  app/util/gcode/simulator.py ← State machine simulator         │
│    ├─ Modal state tracking (G/F/T/S/M codes)                   │
│    ├─ Arc interpolation (G2/G3)                                │
│    └─ Multi-tool support (P6)                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Phases Completed

| Phase | Feature | Status |
|-------|---------|--------|
| P1 | Memory management, progress tracking, downsampling | Complete |
| P2 | SessionStorage caching, LOD rendering | Complete |
| P3 | M-code HUD, tool visualization, time estimates | Complete |
| P4 | Collision detection, optimization suggestions, stock simulation | Complete |
| P5 | Three.js 3D visualization with orbit controls | Complete |
| P6 | Multi-tool color coding, T/S/M code parsing | Complete |

---

## Key Components

### Frontend

| File | Purpose | LOC |
|------|---------|-----|
| `components/cam/ToolpathPlayer.vue` | Main player, composes all features | ~300 |
| `components/cam/ToolpathCanvas.vue` | 2D canvas renderer with LOD | ~400 |
| `components/cam/ToolpathCanvas3D.vue` | Three.js 3D renderer | ~350 |
| `stores/useToolpathPlayerStore.ts` | Playback state, RAF animation | ~400 |
| `components/cam/toolpath-player/*` | Extracted subcomponents (12 files) | ~800 |

Subcomponents:
```
toolpath-player/
├── ControlsBarWrapper.vue
├── ExportAnimationPanel.vue
├── index.ts
├── KeyboardShortcutsOverlay.vue
├── LoadingOverlay.vue
├── MeasureModeIndicator.vue
├── ModalPanelsLayer.vue
├── PanelsLayer.vue
├── ToolbarButtonGroup.vue
├── useToolpathAudio.ts
├── useToolpathExport.ts
├── useToolpathMultiTool.ts
└── useToolpathPanelState.ts
```

### Backend

| File | Purpose |
|------|---------|
| `routers/simulation_consolidated_router.py` | Unified simulation endpoints |
| `util/gcode/simulator.py` | G-code state machine |
| `util/gcode/lexer.py` | G-code tokenizer |
| `util/gcode/geometry.py` | Arc center/length calculations |
| `util/gcode/types.py` | Modal state types |
| `services/sim_energy.py` | Energy/time calculations |

### SDK Layer

| File | Purpose |
|------|---------|
| `sdk/endpoints/cam/simulate.ts` | Frontend API client |
| `sdk/endpoints/cam/cam.ts` | CAM endpoint definitions |

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/cam/sim/gcode` | Simulate G-code from JSON body |
| POST | `/api/cam/sim/upload` | Simulate G-code from file upload |
| POST | `/api/cam/sim/metrics` | Calculate energy/time metrics |
| POST | `/api/cam/sim/simulate_gcode` | Legacy endpoint (alias) |

### Response Shape (simulate)

```json
{
  "ok": true,
  "units": "mm",
  "move_count": 1234,
  "length_mm": 5678.9,
  "time_s": 120.5,
  "moves": [
    {
      "type": "rapid" | "linear" | "arc_cw" | "arc_ccw",
      "from_pos": [x, y, z],
      "to_pos": [x, y, z],
      "duration_ms": 100,
      "feed_rate": 1000,
      "tool": 1,
      "spindle_rpm": 12000,
      "line_number": 42
    }
  ],
  "bounds": {
    "min": [x, y, z],
    "max": [x, y, z]
  },
  "issues": []
}
```

---

## Key Capabilities

### Playback
- RAF-based animation loop
- Variable speed (0.1x to 10x)
- Scrub bar with precise seeking
- Binary search for time→segment mapping

### Rendering
- 2D canvas with viewport culling
- Three.js 3D with orbit/zoom/pan
- LOD downsampling for large files (>10k segments)
- Heatmap mode (engagement visualization)
- Multi-tool color coding

### Memory Management
- Warning at 75k segments
- Critical at 100k segments
- Adaptive downsampling
- SessionStorage caching (FNV-1a hash keys)

### Analysis
- Collision detection
- Optimization suggestions
- Engagement analysis
- Time/energy estimates

### Export
- Animation GIF/video export
- Measurement overlay
- G-code line highlighting

---

## Views Using This System

| View | Usage |
|------|-------|
| `ToolpathSimulatorView.vue` | Standalone simulator page |
| `CamWorkspaceView.vue` | CAM workspace integration |
| `DxfToGcodeWizard.vue` | G-code preview step |
| `BridgeLabView.vue` | Bridge simulation panel |

---

## Known Limitations

1. **Arc interpolation precision** — High curvature arcs may show slight deviations at very high zoom
2. **Large file performance** — Files >100k moves trigger downsampling; full fidelity not guaranteed
3. **3D stock removal** — Stock simulation is 2D heightmap, not true volumetric
4. **No multi-axis** — Only 3-axis (XYZ); no A/B/C rotary support

---

## Integration Points

### With NECK-A
None currently. NECK-A is setup reasoning; CAM is machining visualization. They are separate vertical slices.

### With Aperture Workspace
The Aperture sprint may eventually generate DXF → G-code that feeds into this simulation system.

### With Blueprint Vectorizer
Vectorized blueprints can flow through DXF → CAM pipeline → this simulator.

---

## Archived Planning Documents

```
docs/archive/toolpath_visualizer_plan/
├── ToolpathPlayer.vue       (original design)
├── ToolpathCanvas.vue       (original design)
├── useToolpathPlayerStore.ts
├── simulate.ts
├── gcode_simulate_router.py
├── gcode_parser.py
├── cam.ts
└── test_gcode_simulate.py
```

These are superseded by the production implementations.

---

## Recommendation

**The CAM animated simulation system is production-ready.**

No immediate work required. Future enhancements could include:
- 4th axis (rotary) support
- True volumetric stock removal
- WebGPU rendering for very large files
- Real-time streaming from CNC controller

These are post-migration enhancements, not blockers.
