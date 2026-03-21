# Production Shop — CAM Section Survey
## Landscape Analysis + Interactive Module Architecture Plan

---

## 1. Scale

| Layer | Files | Notes |
|-------|-------|-------|
| `services/api/app/cam/` | 160 Python files | Core engines + routers |
| `services/api/app/cam_core/` | ~25 files | Feeds/speeds, tool registry, G-code models |
| `services/api/app/calculators/` | 20 files | Pure math, no G-code |
| `services/api/app/saw_lab/` | 40+ files | Saw-specific ops, learning, batch |
| API routes (cam routers alone) | 52 endpoints | Does not count api_v1, rmos, saw_lab |
| G-code-emitting engines | 37 distinct modules | Parallel existence, no unified interface |

---

## 2. Three-Tier Structure (exists implicitly, not surfaced to user)

The CAM code has a clear logical stratification that was never made explicit:

```
┌──────────────────────────────────────────────────────┐
│  Tier 1 — Calculator layer  (pure math, no G-code)   │
│  Tier 2 — Engine layer      (G-code generators)      │
│  Tier 3 — Post-processor    (machine dialect output) │
└──────────────────────────────────────────────────────┘
```

The interactive module's job is to make all three tiers visible and composable in a single workspace.

---

## 3. Tier 1 — Calculator Layer (pure math)

All of these are stateless pure functions. Zero FastAPI dependency. All testable in isolation.

### 3.1 Cutting physics
**`calculators/cam_cutting_evaluator.py`** — `evaluate_cut_operation()`
- Chipload: `feed / (rpm × flutes)` → range check (0.05–0.25mm)
- Heat risk: chipload factor + RPM factor + DOC factor → COOL / WARM / HOT
- Deflection: Euler-Bernoulli beam, stickout ratio³ × force proxy → GREEN / YELLOW / RED
- Rim speed: `π × D × RPM / 1000` → within limits check
- Kickback risk (saw): depth ratio + feed factor + tooth factor → LOW / MEDIUM / HIGH
- Bite per tooth (saw): equivalent of chipload for saw blades
- **Returns a unified `overall_risk` = RED / YELLOW / GREEN**

**`cam_core/feeds_speeds/calculator.py`** — `resolve_feeds_speeds(tool, material, mode, machine_profile)`
- Looks up preset (tool_id + material + mode), computes chipload, heat, deflection from geometry
- Returns full bundle: RPM, feed, stepdown, stepover, strategy, finish quality, all derived values
- **This is the correct entry point for any tool+material+machine combination**

**`cam_core/feeds_speeds/chipload_calc.py`** — `calc_chipload_mm()` (3 lines)  
**`cam_core/feeds_speeds/deflection_model.py`** — `estimate_deflection_mm()` (Euler-Bernoulli)  
**`cam_core/feeds_speeds/heat_model.py`** — heat rating  
**`cam/feedtime.py`** — `estimate_time(moves, feed_xy, plunge_f, rapid_f)` → seconds (±10% accuracy)  
**`cam/feedtime_l3.py`** — jerk-aware time estimator, physics-accurate, for production planning

### 3.2 Geometry calculators
**`calculators/fret_slots_cam.py`** — `generate_fret_slot_toolpaths()`, `compute_radius_blended_depth()`
- ET fret positions, radius-blended slot depth across compound radius, DXF/G-code output
- Also in `cam/neck/fret_slots.py` (slightly different — compound radius aware with station offsets)

**`calculators/fret_slots_fan_cam.py`** — fan fret (multiscale) slot positions

**`calculators/rosette_calc.py`** — soundhole channel: inner/outer radius, channel width from purfling stack

**`calculators/inlay_calc.py`** — fretboard inlay positions: dot, diamond, block, parallelogram; DXF export

**`calculators/binding_geometry.py`** — binding bend radius validation, miter joint angles, `calculate_headstock_binding_geometry()`

### 3.3 Duplication flag 🔴
`chipload_calc.py` exists in three locations:
- `cam_core/feeds_speeds/chipload_calc.py` ← canonical
- `_experimental/cnc_production/feeds_speeds/core/chipload_calc.py` ← copy
- `_experimental/cnc_production/feeds_speeds/core/feeds_speeds_resolver.py` ← partial overlap

Fret slot logic in four locations:
- `calculators/fret_slots_cam.py` (standalone)
- `calculators/fret_slots_export.py` (DXF-only variant)
- `cam/neck/fret_slots.py` (compound-radius-aware, part of neck pipeline)
- `cam/routers/fret_slots_router.py` (API wrapper, calls the above)

---

## 4. Tier 2 — G-code Engine Layer

### 4.1 Neck suite (most complete pipeline in the codebase)

**`cam/neck/orchestrator.py`** — `NeckPipeline.generate()`

```
OP10: TrussRodChannelGenerator
OP40: ProfileCarvingGenerator (roughing)  
OP45: ProfileCarvingGenerator (finishing)
OP50: FretSlotGenerator
```

Config: `NeckToolSpec` (4 tools), `TrussRodConfig` (6.35mm wide, 9.525mm deep, 406.4mm long), `ProfileCarvingConfig` (C/D/U/V shapes), `FretSlotConfig`

Coordinate convention: **VINE-05** — Y=0 at nut, +Y toward bridge, X=0 centreline, Z=0 top face

**`cam/neck/truss_rod_channel.py`** — Multi-pass zigzag, configurable stepdown, access pocket variant

**`cam/neck/fret_slots.py`** — Compound-radius slot depth per station (edge vs centre depth differs)

**`cam/neck/profile_carving.py`** — C/D/U/V + asymmetric profiles, roughing + finishing passes

### 4.2 Body suite

**`cam/profiling/profile_toolpath.py`** — `ProfileToolpath`
- Input: closed polygon (body outline), `ProfileConfig` (tool dia, cut depth, stepdown, tabs, lead-in arc)
- Output: G-code + toolpath points, estimated time, pass count, warnings
- Supports climb/conventional, outside/inside compensation, lead-in arcs, hold-down tabs

**`cam/adaptive_core.py`** + `adaptive_core_l1.py` + `adaptive_core_l2.py` — Adaptive pocketing
- L0: vector normal offset (legacy, kept for reference)
- L1: pyclipper-based (production)
- L2: true spiral (smooth, lowest stepover variation)
- Input: closed loops (outer + islands), tool diameter, stepover, stepdown
- API entry: `api_v1/cam_operations.py` `/adaptive`, `/pocket`

**`cam/flying_v/pocket_generator.py`** — Flying V specific
- `generate_control_cavity_toolpath()` — zigzag pocket clearing
- `generate_neck_pocket_toolpath()` — heel pocket
- `generate_pickup_cavity_toolpath()` — humbucker/single-coil

**`cam/carving/orchestrator.py`** — `CarvingPipeline` for archtop graduation
- Input: `GraduationMap` (apex/edge thickness, bounds), `CarvingConfig`
- Generates 3D surface toolpath following thickness gradient

**`cam/fhole/toolpath.py`** — `FHoleToolpathGenerator`
- F-hole geometry (violin/archtop style)
- Contour routing with compound curves

### 4.3 Inlay / decorative

**`cam/rosette/cnc/cnc_ring_toolpath.py`** — `build_ring_arc_toolpaths()`, `build_ring_arc_toolpaths_multipass()`
- Polar → Cartesian arc segments, multi-pass depth, ring-by-ring

**`cam/vcarve/toolpath.py`** — `VCarveToolpath`
- V-bit angle, tip diameter, target line width → auto-calculated depth
- Chipload-aware feed from material preset
- Corner slowdown: reduces feed at angles sharper than threshold
- Multi-pass, path order optimization

**`calculators/inlay_calc.py`** — Dot/diamond/block/parallelogram shapes with DXF export

### 4.4 Drilling

**`cam/drilling/peck_cycle.py`** — `PeckDrill`
- Configurable peck depth, retract mode (full / partial), chip break interval
- Input: `DrillHole` list (x, y, depth, diameter), `DrillConfig`

**`cam/drilling/patterns.py`** — Pattern generators: linear, grid, circular, bolt circle

**`cam/probe_patterns.py`** — Probing cycles
- `generate_corner_probe()` — WCS origin from outside corner
- `generate_boss_probe()` / hole probe — circular boss/hole finding
- `generate_surface_z_probe()` — Z-zero touch-off

### 4.5 Binding

**`cam/binding/channel_toolpath.py`** — `BindingChannel`
- Input: `BindingConfig` (width, depth, tool dia, stepdown)
- Inward-offset perimeter pass, multi-depth

**`cam/binding/purfling_ledge.py`** — Second inward offset for purfling inset

**`cam/binding/offset_geometry.py`** — Polygon offset shared between binding and purfling

### 4.6 Helical plunge

**`cam/helical_core.py`** — `helical_plunge(cx, cy, radius, direction, start_z, z_target, pitch, feed_xy)`
- CW/CCW G2/G3 arc sequence descending from start_z to z_target
- Used for any operation that needs a helical entry (avoids plunge marking)

---

## 5. Tier 3 — Post-Processor

**`cam/post_processor.py`** — `PostProcessor(config: PostConfig)`

PostConfig fields: dialect (GRBL/LinuxCNC/Fanuc), units (mm/inch), arc mode (IJ/R), cutter comp mode, spindle direction, safe Z

Operations:
- `tool_change(tool_number, rpm, tool_name)` → lines
- `cutter_comp_start(tool_diameter, climb)` → G41/G42 sequence
- `cutter_comp_cancel()` → G40
- Program header/footer

**`rmos/posts/grbl.py`**, `fanuc.py`, `linuxcnc.py` — Full post implementations

**`cam/rosette/cnc/cnc_machine_profiles.py`** — `MachineConfig`
- BCAM 2030A: `bcm_2030ca` / `bcamcnc_2030ca` — 48×24×4" work envelope, GRBL-style, 0.6mm/0.2mm tolerances
- The `lespaul_config.py` also has `bcamcnc_2030ca` → confirms your machine is known to the codebase

---

## 6. What's Scattered vs What's Connected

### Connected (works end-to-end now)
- `NeckPipeline` → all 4 neck ops in sequence with shared config
- `resolve_feeds_speeds()` → chipload + heat + deflection from one call
- `evaluate_cut_operation()` → full risk assessment from one call
- `FretSlotGenerator` → compound-radius-aware slots

### Scattered (not connected to each other)
- `ProfileToolpath` (body outline) has no feeds/speeds validation — uses hardcoded defaults
- `VCarveToolpath` has its own internal chipload calc, separate from `cam_cutting_evaluator`
- `CarvingPipeline` (archtop) has no link to the neck pipeline
- Helical plunge (`helical_core.py`) is a utility called by some engines but not available to others
- `estimate_time()` exists but nothing in the UI calls it to show cycle time before cutting
- Post-processor dialect selection is per-engine, not global — you can't say "use BCAM 2030A" once

### Missing (no implementation found)
- No unified parameter entry point: you can't say "maple, 6mm ball-nose, roughing" and have all engines get those values
- No operation sequencer: nothing that says "neck program = OP10 + OP40 + OP45 + OP50 in order, with tool change between each"
- No G-code preview in Production Shop frontend — the toolpath visualizer (`TOOLPATH_VISUALIZER_IMPLEMENTATION_PLAN/`) exists as a plan but the Vue module isn't wired
- No single "validate before cut" gate that runs all four risk checks (chipload + heat + deflection + time)

---

## 7. Interactive Module Architecture

### Concept: CAM Workspace

A single Vue view (`CamWorkspaceView.vue`) with four zones:

```
┌─────────────────┬──────────────────────────────┬──────────────────┐
│  Operations     │  Parameter panels             │  Output          │
│  sidebar        │  (context-sensitive)          │  (G-code +       │
│                 │                               │  visualizer)     │
│  ┌───────────┐  │  ┌──────────────────────┐    │                  │
│  │ ● Neck    │  │  │  Tool + Machine       │    │  G-code preview  │
│  │   ├ Truss │  │  │  ─────────────────── │    │  (read-only,     │
│  │   ├ Rough │  │  │  Material            │    │   syntax-hl)     │
│  │   ├ Finish│  │  │  ─────────────────── │    │                  │
│  │   └ Frets │  │  │  Op-specific params  │    │  ─────────────── │
│  │ ○ Body    │  │  │  ─────────────────── │    │                  │
│  │ ○ Binding │  │  │  Gate summary        │    │  Feeds/speeds    │
│  │ ○ Rosette │  │  │  (chipload/heat/     │    │  validation      │
│  │ ○ Inlay   │  │  │   deflection/time)   │    │  panel           │
│  │ ○ Drill   │  │  └──────────────────────┘    │                  │
│  └───────────┘  │                               │  Cycle time est. │
└─────────────────┴──────────────────────────────┴──────────────────┘
```

### Data flow

```
User picks operation + machine + tool + material
        ↓
Tool+material → resolve_feeds_speeds() → RPM, feed, stepdown
        ↓
Op-specific params + resolved feeds → engine.generate() → G-code
        ↓
G-code moves → estimate_time() → cycle time
        ↓
evaluate_cut_operation() → chipload/heat/deflection/overall_risk
        ↓
all gates pass? → enable "↓ Send to BCAM" button
```

### Machine context (global, not per-engine)

```typescript
interface MachineContext {
  machineId:    'bcam_2030ca' | 'grbl_generic' | 'linuxcnc'
  postDialect:  'grbl' | 'linuxcnc' | 'fanuc'
  workEnvelope: { x: number; y: number; z: number }  // mm
  maxRpm:       number
  maxFeedXY:    number
  maxFeedZ:     number
}
```

This gets injected into every operation. One machine config → all engines use it.

### Operation registry

Each operation is a descriptor:

```typescript
interface CamOperation {
  id:       string               // 'neck.truss_rod' | 'neck.profile' | 'body.profile' | etc.
  label:    string
  group:    OperationGroup
  engine:   string               // backend endpoint path
  params:   OperationParamDef[]  // drives the parameter panel dynamically
  tools:    ToolKind[]           // which tool types this op accepts
  gateKeys: string[]             // which evaluator gates apply
}
```

### Phased build

**Phase 1** (next sprint — minimal viable workspace):
- Neck suite only: wire `NeckPipeline` to a Vue parameter panel + G-code output panel
- Global machine context selector (BCAM 2030A / GRBL generic)
- `evaluate_cut_operation()` called on every param change → gate lights
- `estimate_time()` called on G-code output → cycle time display
- G-code preview (syntax-highlighted `<pre>`)

**Phase 2** (body suite):
- `ProfileToolpath` for body perimeter
- `VCarveToolpath` for inlay pockets
- `PeckDrill` for hardware holes
- Helical plunge toggle (entry strategy choice per op)

**Phase 3** (archtop / specialised):
- `CarvingPipeline` for archtop graduation maps
- `FHoleToolpathGenerator`
- `BindingChannel` + purfling offset
- Rosette ring arcs

**Phase 4** (full integration):
- Operation sequencer: order ops, insert tool changes between them
- Full program output: combined G-code with headers/footers from `PostProcessor`
- Toolpath visualizer wired (the `TOOLPATH_VISUALIZER_IMPLEMENTATION_PLAN/` G-code simulator)
- Save to variant library

---

## 8. Deduplication Recommendations

Before building, three quick cleanup steps that make the module cleaner:

1. **Chipload**: Delete `_experimental/cnc_production/feeds_speeds/core/chipload_calc.py`. All callers point to `cam_core/feeds_speeds/chipload_calc.py`.

2. **Fret slots**: `calculators/fret_slots_cam.py` and `cam/neck/fret_slots.py` should be unified. The neck version is strictly better (compound-radius-aware). The calculators version should become a thin wrapper or be retired.

3. **Feeds/speeds entry point**: `resolve_feeds_speeds()` in `cam_core/feeds_speeds/calculator.py` is the right canonical function. `_experimental/cnc_production/feeds_speeds/core/feeds_speeds_resolver.py` should be removed.

---

## 9. Key Constants (for the Vue param panels)

From the repo — these are the defaults the interactive module should pre-populate:

```
Truss rod:      width=6.35mm  depth=9.525mm  length=406.4mm  T2=3.175mm flat end mill
BCAM 2030A:     envelope 48"×24"×4" (1219×609×101mm)  GRBL dialect
Chipload range: 0.05–0.25mm (router bit hardwood)
Fret slot:      width=0.56mm  depth=0.55mm  T4=thin kerf saw
Ball-nose step: 15% diameter = 0.9mm for 6mm ball-nose (finishing)
Profile tabs:   4 tabs, 10mm wide, 3mm tall
Safe Z default: 5mm
V-bit default:  60°, 18000 RPM
```
