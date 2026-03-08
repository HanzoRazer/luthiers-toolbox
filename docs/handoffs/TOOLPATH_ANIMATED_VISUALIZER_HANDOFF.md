# Toolpath Animated Path Visualizer — Developer Handoff

**Document Type:** Annotated Executive Summary  
**Created:** 2026-03-06  
**Status:** Ready for Implementation  
**Priority:** Medium-High  
**Estimated Scope:** 1 backend file, 4 frontend files, 1 SDK endpoint  

---

## Executive Summary

Users generate G-code through the CAM pipeline but have **no way to preview the toolpath in motion** before sending it to the machine. The current backplot (`/api/cam/gcode/plot.svg`) produces a static SVG — useful for shape verification, but it doesn't show move sequence, rapids vs cuts, depth passes, or timing.

**Goal:** Build an animated toolpath player that lets users **watch the G-code execute visually** — see the tool trace the path in real time (or accelerated), distinguish rapid moves from cuts, observe depth changes, and scrub to any point in the program.

**Why it matters:** Guitar CNC work is low-volume, high-value. A $300 mahogany body blank ruined by a toolpath error is painful. Visual verification before the first cut builds confidence and catches mistakes that static plots miss (wrong cut order, unexpected rapids through material, missed depth passes).

---

## Current State Assessment

### What's Built (Backend — Simulation Infrastructure)

| Component | Path | Status |
|-----------|------|--------|
| gcode_parser.py | `app/util/gcode_parser.py` | ✅ Full modal G-code state machine |
| simulate() | `app/util/gcode_parser.py` | ✅ XY path + aggregate time/distance |
| svg_from_points() | `app/util/gcode_parser.py` | ✅ Static SVG polyline renderer |
| gcode_backplot_router.py | `app/routers/gcode_backplot_router.py` | ✅ `/api/cam/gcode/plot.svg` + `/estimate` |

> **Annotation:** The G-code parser is mature — handles G0/G1/G2/G3, modal state, arc interpolation (IJ and R methods), unit switching (G20/G21). The `simulate()` function already walks every line and tracks XYZ position. The gap is that it collapses everything into aggregates (`travel_mm`, `cut_mm`, `points_xy`) instead of emitting **per-segment move data** needed for animation.

### What's Built (Frontend — CAM SDK & Stores)

| Component | Path | Status |
|-----------|------|--------|
| cam.ts (SDK aggregator) | `src/sdk/endpoints/cam/cam.ts` | ✅ Exports `roughing`, `pipeline` |
| roughing.ts | `src/sdk/endpoints/cam/roughing.ts` | ✅ G-code generation endpoint |
| types.ts | `src/sdk/endpoints/cam/types.ts` | ✅ Typed CAM payloads |
| camAdvisorStore.ts | `src/stores/camAdvisorStore.ts` | ✅ CAM advisory state |
| useExportStore.ts | `src/stores/useExportStore.ts` | ✅ Post-processor selection |
| useManufacturingPlanStore.ts | `src/stores/useManufacturingPlanStore.ts` | ✅ Manufacturing orchestration |

> **Annotation:** The SDK pattern is well-established — typed functions wrapping API calls, never raw `fetch()`. The new simulate endpoint slots in cleanly. Pinia stores use composition API (setup store syntax). Three.js types (`@types/three`) are in `package.json` but Three.js itself is NOT installed — the initial build should use **2D Canvas**, with Three.js as a future upgrade toggle.

### What's NOT Built (The Gap)

| Missing Piece | Description |
|---------------|-------------|
| Per-segment simulation endpoint | Backend returns individual moves with type, coordinates, feed, duration |
| SDK simulate function | Typed frontend caller for the new endpoint |
| Toolpath player store | Playback state: segments, position, speed, play/pause |
| Canvas renderer | Animated drawing: trail, tool dot, color-coded moves, depth shading |
| Player controls UI | Play/pause, speed selector, scrub bar, HUD overlay |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  User generates or pastes G-code (from roughing, pipeline, etc) │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Frontend SDK: cam.simulate(gcode, options)                      │
│  src/sdk/endpoints/cam/simulate.ts                               │
└──────────────────────────┬───────────────────────────────────────┘
                           │ POST /api/cam/gcode/simulate
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Backend: gcode_simulate_router.py                               │
│  ├─ Calls enhanced simulate() from gcode_parser.py              │
│  ├─ Emits per-segment move objects (type, from, to, feed, ms)   │
│  ├─ Computes bounding box for viewport fitting                  │
│  └─ Returns segments[] + bounds + totals                        │
└──────────────────────────┬───────────────────────────────────────┘
                           │ JSON response
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Pinia Store: useToolpathPlayerStore.ts                          │
│  ├─ segments: Segment[]          (loaded from API)              │
│  ├─ playState: 'idle'|'playing'|'paused'                        │
│  ├─ currentTime: number          (ms elapsed in simulation)     │
│  ├─ speed: number                (0.5x, 1x, 2x, 5x, 10x)      │
│  ├─ currentSegmentIndex: number  (computed from currentTime)    │
│  ├─ toolPosition: [x, y, z]     (computed, interpolated)        │
│  └─ totalDuration: number        (computed, sum of all ms)       │
└──────────────────────────┬───────────────────────────────────────┘
                           │ reactive state
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  ToolpathPlayer.vue (wrapper component)                          │
│  ├─ ToolpathCanvas.vue           (canvas renderer)              │
│  │   ├─ requestAnimationFrame loop                              │
│  │   ├─ Draw completed segments as colored trail                │
│  │   ├─ Draw tool dot at interpolated position                  │
│  │   ├─ Color code: gray dashed = rapid, blue = cut, green = arc│
│  │   └─ Depth shading: darker/thicker at lower Z               │
│  ├─ Playback controls bar                                       │
│  │   ├─ ◀◀  ▶ Play/Pause  ▶▶                                   │
│  │   ├─ Speed selector: 0.5x  1x  2x  5x  10x                  │
│  │   └─ Scrub bar (click/drag to seek)                          │
│  └─ HUD overlay                                                 │
│      ├─ Current G-code line text                                │
│      ├─ XYZ position readout                                    │
│      ├─ Feed rate (mm/min)                                      │
│      └─ Elapsed / total time                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Backend Implementation

### File: `services/api/app/routers/gcode_simulate_router.py`

> **Annotation:** This is a UTILITY lane endpoint (stateless preview, no governance). Register in `main.py` alongside the existing backplot router. No boundary fence issues — stays within `app/routers/` calling `app/util/`.

**Endpoint:** `POST /api/cam/gcode/simulate`

**Request Schema:**

```python
class SimulateRequest(BaseModel):
    gcode: str                          # Raw G-code program text
    units: str = "mm"                   # "mm" or "inch"
    rapid_mm_min: float = 3000.0        # Machine rapid rate
    default_feed_mm_min: float = 500.0  # Default cutting feed if F not specified
    arc_resolution_deg: float = 5.0     # Arc interpolation step (degrees)
```

> **Annotation:** `arc_resolution_deg` controls how many points are emitted for G2/G3 arcs. 5° gives smooth curves without blowing up segment count. Frontend draws smooth arcs from these interpolated points.

**Response Schema:**

```python
class MoveSegment(BaseModel):
    type: str           # "rapid" | "cut" | "arc_cw" | "arc_ccw"
    from_pos: list      # [x, y, z] in mm
    to_pos: list        # [x, y, z] in mm
    feed: float         # mm/min (actual feed for this move)
    duration_ms: float  # Real-time duration of this move
    line_number: int    # Source G-code line (1-based)
    line_text: str      # Raw G-code text for HUD display

class SimulateResponse(BaseModel):
    segments: list[MoveSegment]
    bounds: dict        # {x_min, x_max, y_min, y_max, z_min, z_max}
    totals: dict        # {rapid_mm, cut_mm, time_min, segment_count}
```

> **Annotation:** Each `MoveSegment` is one atomic motion command. Arcs are broken into small linear segments (per `arc_resolution_deg`) so the frontend doesn't need arc math — just `lineTo()` calls. The `line_number` and `line_text` fields let the HUD show exactly which G-code line is executing.

**Implementation approach:**

1. Extend `gcode_parser.py` with a new function `simulate_segments()` that returns per-move data instead of aggregates.
2. Walk the same state machine loop as existing `simulate()`, but instead of accumulating totals, emit a `MoveSegment` dict for each G0/G1/G2/G3 command.
3. For G2/G3 arcs: interpolate the arc into N linear sub-segments (N = sweep_angle / arc_resolution_deg), each emitted as a separate segment with `type: "arc_cw"` or `"arc_ccw"`.
4. Track bounding box as segments are emitted.
5. The router calls `simulate_segments()` and returns the response.

> **Annotation:** Do NOT modify the existing `simulate()` function — it's used by the backplot and estimate endpoints. Add `simulate_segments()` as a sibling function that shares the same parsing logic. Consider extracting the shared state-machine loop into a generator that both functions consume.

**Registration in `main.py`:**

```python
from app.routers.gcode_simulate_router import router as gcode_simulate_router
app.include_router(gcode_simulate_router, tags=["cam", "gcode"])
```

---

## Frontend Implementation

### File 1: `src/sdk/endpoints/cam/simulate.ts`

> **Annotation:** Follow the exact pattern in `roughing.ts`. Use the SDK's typed HTTP helpers, never raw `fetch()`.

```typescript
// Types
export interface SimulateRequest {
  gcode: string
  units?: 'mm' | 'inch'
  rapid_mm_min?: number
  default_feed_mm_min?: number
  arc_resolution_deg?: number
}

export interface MoveSegment {
  type: 'rapid' | 'cut' | 'arc_cw' | 'arc_ccw'
  from_pos: [number, number, number]
  to_pos: [number, number, number]
  feed: number
  duration_ms: number
  line_number: number
  line_text: string
}

export interface SimulateBounds {
  x_min: number; x_max: number
  y_min: number; y_max: number
  z_min: number; z_max: number
}

export interface SimulateResponse {
  segments: MoveSegment[]
  bounds: SimulateBounds
  totals: {
    rapid_mm: number
    cut_mm: number
    time_min: number
    segment_count: number
  }
}
```

> **Annotation:** Export from the `cam.ts` aggregator so consumers import as `import { cam } from "@/sdk/endpoints"` then call `cam.simulate(...)`.

---

### File 2: `src/stores/useToolpathPlayerStore.ts`

> **Annotation:** Composition API setup store (per project convention). This store owns ALL playback state — the canvas component is a pure renderer that reads from the store.

**State:**

| Field | Type | Purpose |
|-------|------|---------|
| `segments` | `MoveSegment[]` | Loaded from API response |
| `bounds` | `SimulateBounds` | Viewport fitting |
| `playState` | `'idle' \| 'playing' \| 'paused'` | Playback control |
| `currentTimeMs` | `number` | Elapsed simulation time |
| `speed` | `number` | Playback multiplier (0.5, 1, 2, 5, 10) |
| `totalDurationMs` | `computed<number>` | Sum of all `segment.duration_ms` |
| `currentSegmentIndex` | `computed<number>` | Which segment the tool is on |
| `toolPosition` | `computed<[number, number, number]>` | Interpolated XYZ |
| `progress` | `computed<number>` | 0.0 – 1.0 for scrub bar |

**Actions:**

| Action | Behavior |
|--------|----------|
| `loadGcode(gcode: string)` | Calls `cam.simulate()`, populates segments/bounds |
| `play()` | Sets `playState = 'playing'`, starts animation frame loop |
| `pause()` | Sets `playState = 'paused'`, stops animation loop |
| `stop()` | Resets `currentTimeMs = 0`, sets `playState = 'idle'` |
| `setSpeed(s: number)` | Updates speed multiplier |
| `seek(progress: number)` | Sets `currentTimeMs = progress * totalDurationMs` |
| `stepForward()` | Advances to next segment start |
| `stepBackward()` | Jumps to previous segment start |

> **Annotation:** The animation loop lives in the store (not the component) so playback state persists across component mounts. Use `requestAnimationFrame` with a `lastTimestamp` ref. Each frame: `currentTimeMs += deltaTime * speed`. The computed `currentSegmentIndex` and `toolPosition` derive from `currentTimeMs` by walking the segments array and summing durations.

**Tool position interpolation (critical logic):**

```
Given currentTimeMs, find the active segment:
  accumulated = 0
  for each segment:
    if accumulated + segment.duration_ms > currentTimeMs:
      t = (currentTimeMs - accumulated) / segment.duration_ms  // 0.0 → 1.0
      position = lerp(segment.from_pos, segment.to_pos, t)
      return position
    accumulated += segment.duration_ms
```

> **Annotation:** This is a simple linear scan. For programs with thousands of segments, precompute a cumulative duration array for O(log n) binary search. But for typical guitar G-code (500–2000 segments), linear scan is fine.

---

### File 3: `src/components/cam/ToolpathCanvas.vue`

> **Annotation:** `<script setup lang="ts">` per project convention. Uses a raw `<canvas>` element with 2D context. No Three.js in v1 — keep it simple.

**Rendering pipeline (every animation frame):**

1. **Clear canvas**
2. **Apply viewport transform** — scale/translate from mm coordinates to canvas pixels using `bounds`. Fit entire toolpath with 10% padding. Flip Y axis (canvas Y is downward, CNC Y is upward).
3. **Draw completed segments** (trail behind tool):
   - Rapid moves: `strokeStyle = '#999'`, `setLineDash([4, 4])`, thin line
   - Cut moves: `strokeStyle` varies by Z depth (shallow = `#4A90D9` light blue, deep = `#1B3A6B` dark blue), solid line, thicker
   - Arc moves: same as cut but rendered in `#2ECC71` (green) to distinguish
4. **Draw upcoming segments** (ahead of tool): very faint (`globalAlpha = 0.15`), gives user spatial awareness
5. **Draw tool dot**: filled circle at `toolPosition`, size = tool diameter if known, else fixed 6px radius. Red fill with white stroke for visibility.
6. **Draw Z indicator**: small vertical bar or number showing current Z depth next to the tool dot.

**Interaction:**

| Input | Action |
|-------|--------|
| Mouse wheel | Zoom in/out (scale canvas transform) |
| Click + drag | Pan viewport |
| Double-click | Reset zoom/pan to fit-all |

> **Annotation:** Store the viewport transform as `{ scale, offsetX, offsetY }` in a local ref (not in Pinia — this is view-only state). The mm→pixel conversion function is: `px_x = (mm_x - bounds.x_min) * scale + offsetX`, `px_y = canvasHeight - (mm_y - bounds.y_min) * scale + offsetY` (Y-flip).

**Depth shading formula:**

```
z_range = bounds.z_max - bounds.z_min
z_normalized = (segment.to_pos[2] - bounds.z_min) / z_range  // 0 = deepest, 1 = shallowest
line_width = 1 + (1 - z_normalized) * 3                      // 1px shallow → 4px deep
opacity = 0.4 + (1 - z_normalized) * 0.6                     // 40% shallow → 100% deep
```

> **Annotation:** This gives an intuitive visual: deeper cuts render bolder and more opaque. Users immediately see which passes are roughing vs finishing depth.

---

### File 4: `src/components/cam/ToolpathPlayer.vue`

> **Annotation:** This is the user-facing wrapper. Composes `ToolpathCanvas` with controls and HUD. Should be drop-in embeddable anywhere G-code is generated.

**Layout:**

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    ToolpathCanvas.vue                         │
│               (fills available space, min 400px)             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  ◀◀  ▶ Play  ▶▶  │ ████████░░░░░░░░░░ 42%  │ ×1  ×2  ×10  │
├──────────────────────────────────────────────────────────────┤
│  Line 47: G1 X50.2 Y32.8 F1200   │  Z: -1.50mm  │  0:03.2  │
└──────────────────────────────────────────────────────────────┘
```

**Props:**

```typescript
interface Props {
  gcode?: string           // If provided, auto-loads on mount
  showHud?: boolean        // Show the bottom info bar (default true)
  showControls?: boolean   // Show playback controls (default true)
  autoPlay?: boolean       // Start playing immediately (default false)
  height?: string          // CSS height (default '500px')
}
```

**Controls bar elements:**

| Element | Behavior |
|---------|----------|
| ◀◀ Step back | `store.stepBackward()` |
| ▶ Play / ⏸ Pause | Toggle `store.play()` / `store.pause()` |
| ▶▶ Step forward | `store.stepForward()` |
| Scrub bar | `<input type="range">` bound to `store.progress`, `@input → store.seek()` |
| Speed buttons | Highlight active speed, `@click → store.setSpeed(n)` |

**HUD bar elements (read from store computed values):**

| Field | Source |
|-------|--------|
| G-code line | `segments[currentSegmentIndex].line_text` |
| Z depth | `toolPosition[2]` formatted to 2 decimal places |
| Elapsed time | `currentTimeMs` formatted as `M:SS.s` |
| Total time | `totalDurationMs` formatted |

---

## Integration Points

### Where to Embed the Player

> **Annotation:** The player should appear anywhere the user has G-code available. These are the primary integration sites, ordered by priority.

| Location | File | How |
|----------|------|-----|
| **Post-roughing result** | Component that displays roughing output | Add `<ToolpathPlayer :gcode="result.gcode" />` below the G-code text area |
| **G-code export preview** | Export/download flow | Show player before user downloads .nc file |
| **Blueprint Lab Phase 3** | `Phase3CamPanel.vue` | After DXF→G-code pipeline completes |
| **Manufacturing Plan view** | Manufacturing plan step detail | Visualize each operation's toolpath |

### Updating the SDK Aggregator

In `src/sdk/endpoints/cam/cam.ts`, add:

```typescript
export { simulate } from './simulate'
// or re-export within the cam namespace object
```

---

## Performance Considerations

| Concern | Threshold | Mitigation |
|---------|-----------|------------|
| Segment count | >5,000 segments | Precompute cumulative duration array for binary search seek |
| Canvas redraw | 60fps target | Only redraw if `currentTimeMs` changed; offscreen canvas for completed trail |
| Large G-code programs | >50,000 lines | Consider server-side segment decimation (emit every Nth point for rapid moves) |
| Arc resolution | 5° default | Adjustable via request; 2° for smooth preview, 10° for performance |
| Memory | Segment JSON payload | Typical guitar program: ~2,000 segments ≈ 200KB — no concern |

> **Annotation:** Guitar G-code is inherently modest in size. A full body roughing program is typically 2,000–8,000 lines of G-code, producing 1,000–4,000 segments after arc interpolation. Canvas handles this without breaking a sweat. Don't over-engineer for scale — this isn't a 5-axis aerospace visualizer.

---

## Visual Design Spec

### Color Palette

| Move Type | Stroke Color | Line Style | Width |
|-----------|-------------|------------|-------|
| Rapid (G0) | `#999999` (gray) | Dashed `[4, 4]` | 1px |
| Cut (G1) | `#4A90D9` → `#1B3A6B` (depth gradient) | Solid | 1–4px (depth) |
| Arc CW (G2) | `#2ECC71` → `#1A7A42` (depth gradient) | Solid | 1–4px (depth) |
| Arc CCW (G3) | `#2ECC71` → `#1A7A42` (depth gradient) | Solid | 1–4px (depth) |
| Future path | Same as type | Same | Same, but `alpha = 0.15` |
| Tool dot | `#E74C3C` (red) fill, `#FFFFFF` stroke | — | 6px radius |

### HUD Styling

- Background: `rgba(0, 0, 0, 0.75)` — dark overlay
- Text: `#FFFFFF`, monospace font (`font-family: 'JetBrains Mono', 'Fira Code', monospace`)
- Font size: 13px for values, 11px for labels
- Layout: flexbox row, space-between

### Canvas Background

- Default: `#1E1E2E` (dark) — high contrast with toolpath colors
- Optional: `#FFFFFF` (light) — togglable for print/screenshot

---

## Testing Strategy

### Backend Tests

| Test | File | Validates |
|------|------|-----------|
| Empty G-code | `tests/test_gcode_simulate.py` | Returns empty segments, zero bounds |
| Linear moves only | same | G0 → `type: "rapid"`, G1 → `type: "cut"`, correct from/to |
| Arc interpolation | same | G2/G3 produce multiple sub-segments, sweep covers full arc |
| Unit switching | same | G20 (inch) mid-program converts correctly |
| Duration accuracy | same | `sum(segment.duration_ms)` matches existing `simulate()` `t_total_min * 60000` |
| Line numbering | same | Each segment's `line_number` maps to correct source line |
| Bounding box | same | `bounds` encompasses all segment endpoints |

> **Annotation:** The existing `simulate()` function serves as ground truth. The new `simulate_segments()` must produce the same total distances and times when aggregated. Write a cross-validation test that runs both and compares.

### Frontend Tests (Vitest)

| Test | Validates |
|------|-----------|
| Store: loadGcode | Calls SDK, populates segments |
| Store: play/pause/stop | State transitions correct |
| Store: seek | `currentTimeMs` set correctly, `progress` computes |
| Store: tool interpolation | Position lerps correctly within segment |
| Store: segment boundary crossing | Tool transitions between segments smoothly |
| Component: renders canvas | `<canvas>` element exists |
| Component: controls visible | Play button, scrub bar, speed buttons render |
| Component: HUD displays | Line text, Z depth, time shown |

---

## Future Enhancements (Out of Scope for v1)

> **Annotation:** Document these so they don't creep into v1. Each is a separate PR.

| Enhancement | Description | Complexity |
|-------------|-------------|------------|
| **3D view toggle** | Three.js renderer showing Z depth as actual 3D | Medium — types already installed, add `three` package |
| **Tool engagement heatmap** | Color by material removal rate (stepover × stepdown × feed) | Low — computed from adjacent segments |
| **Collision detection overlay** | Highlight segments where tool may hit clamps/fixtures | High — needs fixture model import |
| **Side-by-side comparison** | Compare two G-code programs (before/after optimization) | Medium — two canvases, synchronized playback |
| **G-code line sync** | Click a segment on canvas → highlight line in G-code editor | Low — use `line_number` from segment |
| **Export animation** | Record canvas frames → GIF/MP4 for sharing | Medium — use `canvas.captureStream()` or frame-by-frame |
| **Machine sounds** | Audio feedback simulating spindle RPM and cutting | Low (novelty) — Web Audio API tone generation |

---

## File Checklist

### New Files to Create

| # | File | Type | Purpose |
|---|------|------|---------|
| 1 | `services/api/app/routers/gcode_simulate_router.py` | Backend | Simulate endpoint returning per-segment data |
| 2 | `packages/client/src/sdk/endpoints/cam/simulate.ts` | SDK | Typed API caller |
| 3 | `packages/client/src/stores/useToolpathPlayerStore.ts` | Store | Playback state management |
| 4 | `packages/client/src/components/cam/ToolpathCanvas.vue` | Component | Canvas renderer |
| 5 | `packages/client/src/components/cam/ToolpathPlayer.vue` | Component | Controls + HUD wrapper |

### Existing Files to Modify

| # | File | Change |
|---|------|--------|
| 1 | `services/api/app/util/gcode_parser.py` | Add `simulate_segments()` function |
| 2 | `services/api/app/main.py` | Register `gcode_simulate_router` |
| 3 | `packages/client/src/sdk/endpoints/cam/cam.ts` | Re-export `simulate` |

### Test Files to Create

| # | File | Coverage |
|---|------|----------|
| 1 | `services/api/tests/test_gcode_simulate.py` | Backend endpoint + segment accuracy |
| 2 | `packages/client/src/stores/__tests__/useToolpathPlayerStore.test.ts` | Store logic + interpolation |

---

## Boundary Compliance

> **Annotation:** This feature stays cleanly within existing boundaries. No RMOS↔CAM cross-imports, no external repo dependencies, no governance lane violations.

- **Backend:** `app/routers/` → `app/util/` (same pattern as existing backplot router) ✅
- **Frontend:** `sdk/endpoints/cam/` → `stores/` → `components/cam/` (standard Vue data flow) ✅
- **Lane:** UTILITY (stateless preview endpoint, no governance or audit trail needed) ✅
- **Fence check:** No cross-domain imports. Run `make check-boundaries` to confirm ✅

---

## Implementation Order

> **Annotation:** Build bottom-up. Each step is independently testable.

1. **`simulate_segments()` in gcode_parser.py** — Core logic. Test against existing `simulate()` for parity.
2. **`gcode_simulate_router.py`** — Expose the endpoint. Test with curl/httpie.
3. **`simulate.ts` SDK endpoint** — Wire the frontend to the backend. Test with a manual API call.
4. **`useToolpathPlayerStore.ts`** — All playback logic. Unit test the interpolation math.
5. **`ToolpathCanvas.vue`** — Visual rendering. Manual testing with sample G-code.
6. **`ToolpathPlayer.vue`** — Assemble controls + canvas. Integration test.
7. **Embed in primary view** — Drop `<ToolpathPlayer>` into the roughing result panel.

---

## GAP REGISTRY — Trackable Code & Architecture Deficits

> **Purpose:** Each gap has a unique ID, the exact file and line range where the problem lives, what's broken, what "fixed" looks like, dependencies on other gaps, and test expectations. A remediation team can work through these top-to-bottom.

### Summary Dashboard

| ID | Area | Severity | Effort | Status | Blocks |
|----|------|----------|--------|--------|--------|
| VIS-01 | Per-segment simulate function | **Critical** | Medium | ❌ Missing | VIS-02, VIS-03, VIS-04 |
| VIS-02 | Simulate API endpoint + router | **Critical** | Low | ❌ Missing | VIS-03, VIS-04 |
| VIS-03 | Frontend SDK simulate caller | **High** | Low | ❌ Missing | VIS-04, VIS-05 |
| VIS-04 | Toolpath player Pinia store | **High** | Medium | ❌ Missing | VIS-05, VIS-06 |
| VIS-05 | Canvas renderer component | **High** | Medium | ❌ Missing | VIS-06 |
| VIS-06 | Player wrapper + controls | **Medium** | Low | ❌ Missing | — |
| VIS-07 | Main.py router registration | **Low** | Trivial | ❌ Missing | — |

---

### VIS-01: `simulate_segments()` — Per-Segment Simulation Function

**Severity:** Critical — all downstream components depend on this data  
**Status:** Does not exist in production code. An implementation plan exists in `TOOLPATH_VISUALIZER_IMPLEMENTATION_PLAN/gcode_parser.py` line 534, but production code only has the aggregate `simulate()`.  

**Where the problem is:**
- **File:** `services/api/app/util/gcode_parser.py`
- **Function:** `simulate()` at line ~327
- **Current signature:**
```python
def simulate(
    gcode: str,
    *,
    rapid_mm_min: float = 3000.0,
    default_feed_mm_min: float = 500.0,
    units: str = "mm"
) -> Dict[str, Any]:
```
- **Returns:** `{travel_mm, cut_mm, t_rapid_min, t_feed_min, t_total_min, points_xy}` — aggregates only. No per-segment move type, no per-segment duration, no line number tracking.

**What "fixed" looks like:**
Add a sibling function `simulate_segments()` (do NOT modify existing `simulate()`):
```python
def simulate_segments(
    gcode: str,
    *,
    rapid_mm_min: float = 3000.0,
    default_feed_mm_min: float = 500.0,
    units: str = "mm",
    arc_resolution_deg: float = 5.0,
) -> Dict[str, Any]:
    """Returns per-segment move data for animation.
    
    Returns:
        {
            "segments": [{"type": "rapid"|"cut"|"arc_cw"|"arc_ccw",
                         "from_pos": [x,y,z], "to_pos": [x,y,z],
                         "feed": float, "duration_ms": float,
                         "line_number": int, "line_text": str}, ...],
            "bounds": {"x_min": ..., "x_max": ..., ...},
            "totals": {"rapid_mm": ..., "cut_mm": ..., "time_min": ..., "segment_count": ...}
        }
    """
```

Shares the same state-machine parsing loop as `simulate()` but emits per-move dicts instead of accumulating totals. For G2/G3 arcs, interpolate into N linear sub-segments (N = sweep_angle / arc_resolution_deg), each emitted as type `"arc_cw"` or `"arc_ccw"`.

**Test expectations:**
- `simulate_segments("G0 X10\nG1 X20 F500")` returns 2 segments — first `type:"rapid"`, second `type:"cut"`
- `sum(seg["duration_ms"] for seg in result["segments"])` matches `simulate()["t_total_min"] * 60000` within 1ms tolerance
- `result["totals"]["rapid_mm"] + result["totals"]["cut_mm"]` matches `simulate()` totals
- Arc G2/G3 code produces multiple sub-segments, all with correct `type`
- Each segment has `line_number` mapping back to the correct source line (1-indexed)
- Bounding box `bounds` encompasses all segment endpoints
- Empty G-code returns `{"segments": [], "bounds": {...zero...}, "totals": {...zero...}}`

**Dependencies:** Blocks VIS-02, VIS-03, VIS-04 (everything consumes this data)  
**Blocked by:** Nothing — pure Python function, no external dependencies. **Start here.**

---

### VIS-02: `gcode_simulate_router.py` — API Endpoint

**Severity:** Critical — frontend cannot access simulation data without this  
**Status:** Does not exist in production. Plan file exists at `TOOLPATH_VISUALIZER_IMPLEMENTATION_PLAN/gcode_simulate_router.py`.  

**Where the problem is:**
- **Expected file:** `services/api/app/routers/gcode_simulate_router.py` — does not exist
- **Router manifest:** `services/api/app/router_registry/manifest.py` — no entry for `gcode_simulate_router`
- **Existing related router:** `services/api/app/routers/gcode_backplot_router.py` — returns static SVG + aggregates (model for the new router)

**What "fixed" looks like:**
```python
# services/api/app/routers/gcode_simulate_router.py
router = APIRouter()

class SimulateRequest(BaseModel):
    gcode: str
    units: str = "mm"
    rapid_mm_min: float = 3000.0
    default_feed_mm_min: float = 500.0
    arc_resolution_deg: float = 5.0

@router.post("/api/cam/gcode/simulate")
def simulate_gcode(req: SimulateRequest) -> dict:
    from app.util.gcode_parser import simulate_segments
    return simulate_segments(
        req.gcode,
        rapid_mm_min=req.rapid_mm_min,
        default_feed_mm_min=req.default_feed_mm_min,
        units=req.units,
        arc_resolution_deg=req.arc_resolution_deg,
    )
```

**Lane:** UTILITY (stateless preview, no governance). Same pattern as existing backplot router.

**Test expectations:**
- `POST /api/cam/gcode/simulate` with valid G-code returns 200 with `segments[]`, `bounds{}`, `totals{}`
- Empty gcode string returns 200 with empty segments
- Invalid `units` value returns 422 validation error
- Response includes `X-Request-Id` header (per project convention)

**Dependencies:** Blocks VIS-03 (SDK needs an endpoint to call)  
**Blocked by:** VIS-01 (`simulate_segments()` must exist)

---

### VIS-03: Frontend SDK `simulate.ts`

**Severity:** High — SDK is the only allowed way to call backend (never raw `fetch()`)  
**Status:** Does not exist. No `simulate.ts` in `packages/client/src/sdk/endpoints/cam/`.  

**Where the problem is:**
- **Expected file:** `packages/client/src/sdk/endpoints/cam/simulate.ts` — does not exist
- **SDK aggregator:** `packages/client/src/sdk/endpoints/cam/cam.ts` — currently exports `roughing`, `pipeline` — no `simulate`

**What "fixed" looks like:**
1. Create `packages/client/src/sdk/endpoints/cam/simulate.ts` with typed request/response interfaces and a `simulate()` function using the SDK HTTP helpers (follow pattern in `roughing.ts`)
2. Re-export from `packages/client/src/sdk/endpoints/cam/cam.ts`

**Test expectations:**
- `import { cam } from "@/sdk/endpoints"` — `cam.simulate` is defined
- `cam.simulate({ gcode: "G0 X10" })` calls `POST /api/cam/gcode/simulate`
- Response is typed as `SimulateResponse`

**Dependencies:** Blocks VIS-04, VIS-05  
**Blocked by:** VIS-02 (endpoint must exist)

---

### VIS-04: `useToolpathPlayerStore.ts` — Playback State Store

**Severity:** High — animation logic and interpolation live here  
**Status:** Does not exist. No toolpath player store in `packages/client/src/stores/`.  

**Where the problem is:**
- **Expected file:** `packages/client/src/stores/useToolpathPlayerStore.ts` — does not exist
- **Existing reference store:** `packages/client/src/stores/camAdvisorStore.ts` — composition API setup store pattern to follow

**What "fixed" looks like:**
Pinia composition API store with:
- **State:** `segments`, `bounds`, `playState` (`idle|playing|paused`), `currentTimeMs`, `speed` (0.5–10x)
- **Computed:** `totalDurationMs`, `currentSegmentIndex`, `toolPosition` (XYZ interpolated), `progress` (0–1)
- **Actions:** `loadGcode(gcode)`, `play()`, `pause()`, `stop()`, `setSpeed(n)`, `seek(progress)`, `stepForward()`, `stepBackward()`
- **Animation:** `requestAnimationFrame` loop that advances `currentTimeMs += deltaTime * speed` each frame

**Critical interpolation logic:**
```
Walk segments array, accumulate duration. When accumulated > currentTimeMs,
interpolate position: t = (currentTimeMs - accumulated_before) / segment.duration_ms
position = lerp(segment.from_pos, segment.to_pos, t)
```

**Test expectations:**
- `loadGcode()` calls SDK, populates segments with correct count
- `play()` sets playState to `'playing'`; `pause()` sets to `'paused'`; `stop()` resets time to 0
- `seek(0.5)` sets `currentTimeMs` to half of `totalDurationMs`
- `toolPosition` returns correct interpolated XYZ for a known `currentTimeMs` value
- Segment boundary crossing (end of one segment, start of next) produces smooth position transition

**Dependencies:** Blocks VIS-05, VIS-06  
**Blocked by:** VIS-03 (loads data via SDK)

---

### VIS-05: `ToolpathCanvas.vue` — Canvas Renderer

**Severity:** High — the visual output  
**Status:** Does not exist. No `packages/client/src/components/cam/` directory. A view stub `ToolpathSimulatorView.vue` exists in `packages/client/src/views/cam/` but is not the canvas renderer.  

**Where the problem is:**
- **Expected file:** `packages/client/src/components/cam/ToolpathCanvas.vue` — does not exist
- **Expected directory:** `packages/client/src/components/cam/` — does not exist

**What "fixed" looks like:**
`<script setup lang="ts">` component with:
- `<canvas>` element, 2D context (no Three.js in v1)
- `requestAnimationFrame` render loop reading from `useToolpathPlayerStore`
- Viewport transform: mm → pixels, Y-axis flip, fit-all with 10% padding
- Color-coded trail: gray dashed = rapid, blue = cut, green = arc (depth-shaded)
- Tool dot: red circle at interpolated position
- Interaction: mouse wheel zoom, click+drag pan, double-click reset

**Test expectations:**
- Component renders a `<canvas>` element
- Canvas draws without errors when store has segments loaded
- Zoom/pan state is local to component (not in Pinia)

**Dependencies:** Blocks VIS-06  
**Blocked by:** VIS-04 (reads from player store)

---

### VIS-06: `ToolpathPlayer.vue` — Controls + HUD Wrapper

**Severity:** Medium — user-facing wrapper  
**Status:** Does not exist  

**Where the problem is:**
- **Expected file:** `packages/client/src/components/cam/ToolpathPlayer.vue` — does not exist

**What "fixed" looks like:**
Wrapper component composing `ToolpathCanvas.vue` with:
- Playback controls: play/pause, step forward/back, scrub bar, speed selector (0.5x–10x)
- HUD overlay: current G-code line text, XYZ position, feed rate, elapsed/total time
- Props: `gcode?`, `showHud?`, `showControls?`, `autoPlay?`, `height?`

**Test expectations:**
- Play/pause/stop buttons call correct store actions
- Speed buttons update `store.speed`
- Scrub bar `@input` calls `store.seek()`
- HUD displays data from store computed values

**Dependencies:** None downstream  
**Blocked by:** VIS-04 (store), VIS-05 (canvas)

---

### VIS-07: Main.py Router Registration

**Severity:** Low — one line addition, but endpoint won't work without it  
**Status:** Not registered  

**Where the problem is:**
- **File:** `services/api/app/main.py`
- **Current state:** `gcode_backplot_router` is registered; `gcode_simulate_router` is not

**What "fixed" looks like:**
```python
from app.routers.gcode_simulate_router import router as gcode_simulate_router
app.include_router(gcode_simulate_router, tags=["cam", "gcode"])
```

**Test expectations:**
- `GET /openapi.json` includes `/api/cam/gcode/simulate` endpoint
- Endpoint is accessible and returns expected response

**Dependencies:** None  
**Blocked by:** VIS-02 (router module must exist first)

---

### REMEDIATION SEQUENCE

```
Phase 1: Backend Core
├── VIS-01: Add simulate_segments() to gcode_parser.py      ← START HERE
├── VIS-02: Create gcode_simulate_router.py
└── VIS-07: Register router in main.py

Phase 2: Frontend SDK
└── VIS-03: Create simulate.ts + re-export from cam.ts

Phase 3: Frontend Application
├── VIS-04: Create useToolpathPlayerStore.ts (interpolation logic)
├── VIS-05: Create ToolpathCanvas.vue (renderer)
└── VIS-06: Create ToolpathPlayer.vue (controls + HUD)
```

### Files to Create

| File | Gap(s) |
|------|--------|
| `services/api/app/routers/gcode_simulate_router.py` | VIS-02 |
| `packages/client/src/sdk/endpoints/cam/simulate.ts` | VIS-03 |
| `packages/client/src/stores/useToolpathPlayerStore.ts` | VIS-04 |
| `packages/client/src/components/cam/ToolpathCanvas.vue` | VIS-05 |
| `packages/client/src/components/cam/ToolpathPlayer.vue` | VIS-06 |

### Files to Modify

| File | Gap(s) | Change |
|------|--------|--------|
| `services/api/app/util/gcode_parser.py` | VIS-01 | Add `simulate_segments()` function |
| `services/api/app/main.py` | VIS-07 | Register simulate router |
| `packages/client/src/sdk/endpoints/cam/cam.ts` | VIS-03 | Re-export `simulate` |

---

*End of handoff. All measurements in mm. All coordinates in CNC convention (Y-up). All API calls through the SDK.*
