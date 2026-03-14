# Rosette Wheel Designer → Engine Integration Plan (Consolidation-First)

**Source:** Interactive Rosette Wheel Designer + existing CAM rosette pipeline  
**Strategy:** Consolidate first, integrate second. One engine, one store, fewer files.  
**Date:** March 14, 2026

---

## Executive Summary

The rosette subsystem has **~41 Python files** across `cam/rosette/`, `cam/rosette/cnc/`, and `art_studio/`. A full audit reveals that **8 of those files are pure skeleton or dead code** (≤20 lines of pass-through logic, no real callers), and **3 frontend stores** serve overlapping roles. The original integration plan proposed adding 4 more files on top of this pile — making the problem worse.

This revised plan **consolidates first**: delete dead code, absorb micro-skeletons, merge redundant stores, then build integration on a clean foundation. The target is **one unified rosette engine** that handles design → geometry → manufacturing → export from a single call chain.

### Can we get to ONE engine?

**Yes — with a clear definition of "engine."** The rosette subsystem touches three concerns:

1. **Design** — grid layout, symmetry, tile placement, SVG preview  
2. **Geometry** — ring segmentation, tile trapezoid math, kerf compensation  
3. **Manufacturing** — toolpath generation, G-code export, safety validation, BOM

These can live in **one orchestrator** (`RosetteEngine`) that delegates to focused internal modules. The key insight: the boundary fence between `art_studio` and `cam` is **not enforced** — `FENCE_REGISTRY.json` only walls off `RMOS ↔ CAM`, `AI sandbox`, and `Saw Lab`. Art studio can freely import CAM types and functions. This means no HTTP bridge is needed; the engine can call CAM geometry directly.

### File count: Before → After

| Layer | Before | After | Reduction |
|---|---:|---:|---|
| `cam/rosette/` root | 23 .py files | 11 .py files | Delete 3, absorb 6, keep 3 standalone |
| `cam/rosette/cnc/` | 12 .py files | 7 .py files | Absorb 5 into neighbors |
| `art_studio/` rosette services | 4 .py files | 3 .py files | Absorb feasibility wrapper |
| Frontend stores | 3 stores | 1 store | Merge all three |
| **Integration (new)** | — | 0 new files | Bridge methods live on the engine |
| **Total** | ~42 | ~22 | **−20 files (48% reduction)** |

### Target Architecture

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                      RosetteEngine                              │
 │          (art_studio/services/rosette_engine.py)                │
 │                                                                 │
 │  DESIGN ─────────── GEOMETRY ──────────── MANUFACTURING         │
 │  ┌──────────────┐   ┌────────────────┐   ┌──────────────────┐  │
 │  │ place_tile() │   │ segment_ring() │   │ plan_toolpaths() │  │
 │  │ symmetry()   │──▶│ tile_geometry() │──▶│ export_gcode()   │  │
 │  │ render_svg() │   │ kerf_adjust()  │   │ compute_bom()    │  │
 │  │ load_recipe()│   │                │   │ check_mfg()      │  │
 │  └──────────────┘   └────────────────┘   │ check_feasib()   │  │
 │                                          │ save_snapshot()   │  │
 │                                          └──────────────────┘  │
 │                                                                 │
 │  Delegates to:                                                  │
 │  cam/rosette/tile_segmentation.py  (real trapezoid geometry)    │
 │  cam/rosette/cnc/cnc_ring_toolpath.py  (arc-based toolpaths)   │
 │  cam/rosette/cnc/cnc_gcode_exporter.py (GRBL/FANUC G-code)    │
 │  cam/rosette/cnc/cnc_safety_validator.py (safety gates)        │
 │  cam/rosette/rosette_cnc_wiring.py (multi-pass orchestration)  │
 └─────────────────────────────────────────────────────────────────┘

 ┌─────────────────────────────────────────────────────────────────┐
 │  useRosetteStore (Pinia — single unified store)                 │
 │  Design tab → Geometry tab → Manufacturing tab → Export tab     │
 └─────────────────────────────────────────────────────────────────┘
```

---

## Audit Results: What's Real vs. Dead

### Files to DELETE (pure skeleton, no callers, no real logic)

| File | Lines | Why |
|---|---:|---|
| `cam/rosette/herringbone.py` | 24 | Pass-through dict copy. Zero imports across codebase. Comment says "prefer twist_engine." |
| `cam/rosette/kerf_compensation.py` | 18 | Dict copy, no angle compensation. Superseded by `cnc/cnc_kerf_physics.py`. |
| `cam/rosette/saw_batch_generator.py` | 24 | Trivial SliceBatch builder. Comment: "scaffolding only… geometry is not real." Zero callers. |

### Files to ABSORB (≤35 lines of logic, merge into parent)

| File | Lines | Logic | Absorb Into | What Moves |
|---|---:|---|---|---|
| `cam/rosette/kerf_engine.py` | 31 | Stores kerf_mm, no angle adjustment | `tile_segmentation.py` (already has real kerf math) | The `apply_kerf_physics()` signature becomes a thin call to `tile_segmentation.compute_tile_geometry(kerf_mm=...)` |
| `cam/rosette/twist_engine.py` | 30 | Sets herringbone_flip flag only | `tile_segmentation.py` | `apply_twist()` + `apply_herringbone()` become methods on `RingSegmentation` |
| `cam/rosette/segmentation_engine.py` | 37 | Hardcoded tile_count=8 | `tile_segmentation.py` (already has `compute_ring_segmentation()` with real geometry) | Delete entirely — `tile_segmentation.py` does everything this file claims to |
| `cam/rosette/slice_engine.py` | 35 | Angle = tile center, no twist/kerf | `tile_segmentation.py` | Slice generation is a trivial transform of tile geometry |
| `cam/rosette/ring_engine.py` | 35 | Orchestrator calling 4 skeletons above | **Becomes the engine's geometry method** | 20 lines of orchestration move into `RosetteEngine.segment_ring()` |
| `cam/rosette/preview_engine.py` | 39 | Returns tile/slice count summary | `RosetteEngine.render_svg()` already does this | Delete — wheel designer SVG renderer supersedes |
| `art_studio/services/rosette_feasibility_scorer.py` | 60 | Thin wrapper over RMOS scorer | `RosetteEngine.check_feasibility()` | 10 lines of RMOS delegation move into engine |

### CNC files to consolidate

| File | Lines | Action |
|---|---:|---|
| `cnc/cnc_toolpath.py` | 62 | **KEEP** — `ToolpathSegment` + `ToolpathPlan` are canonical types used everywhere |
| `cnc/cnc_ring_toolpath.py` | 250 | **KEEP** — real arc-based geometry, multi-pass Z stepping |
| `cnc/cnc_gcode_exporter.py` | 150 | **KEEP** — complete GRBL/FANUC G-code generation |
| `cnc/cnc_safety_validator.py` | 150 | **KEEP** — real envelope/feed/kerf validation |
| `cnc/cnc_exporter.py` | 38 | **KEEP** — export bundle container |
| `cnc/cnc_kerf_physics.py` | 36 | **ABSORB** → `cnc_safety_validator.py` (20 lines of kerf angle math) |
| `cnc/cnc_simulation.py` | 45 | **ABSORB** → `cnc_exporter.py` (25-line heuristic estimator) |
| `cnc/cnc_feed_table.py` | 47 | **ABSORB** → `cnc_materials.py` (3 feed rules + dataclass) |
| `cnc/cnc_blade_model.py` | 22 | **ABSORB** → `cnc_materials.py` (2 dataclasses) |
| `cnc/cnc_jig_geometry.py` | 32 | **ABSORB** → `cnc_exporter.py` (2 dataclasses) |
| `cnc/cnc_machine_profiles.py` | 75 | **KEEP** — machine config data, referenced by ID in config |
| `cnc/cnc_materials.py` | 42 | **KEEP** (becomes home for absorbed feed_table + blade_model) |

### Files that are REAL and stay untouched

| File | Lines | Why Keep |
|---|---:|---|
| `cam/rosette/tile_segmentation.py` | 320 | Real trapezoid geometry — `TileGeometry`, `RingSegmentation`, kerf compensation |
| `cam/rosette/pattern_generator.py` | 350 | `RosettePatternEngine` — traditional + modern + combined generation |
| `cam/rosette/modern_pattern_generator.py` | 800 | Wave, Spanish, Celtic pattern geometry with DXF/SVG |
| `cam/rosette/pattern_renderer.py` | 550 | PIL-based matrix-to-annulus visualization |
| `cam/rosette/pattern_schemas.py` | 400 | Enums + dataclasses used everywhere |
| `cam/rosette/models.py` | 100 | `RosetteRingConfig`, `Tile`, `SliceBatch`, `MultiRingAssembly` |
| `cam/rosette/presets.py` | 850 | 30+ named preset matrices (Torres, Hauser, etc.) — data, not logic |
| `cam/rosette/rosette_bom.py` | 200 | BOM computation + veneer cut bills |
| `cam/rosette/rosette_cnc_wiring.py` | 250 | Multi-pass orchestration, the real CNC bridge |
| `cam/rosette/traditional_builder.py` | 150 | Dataclasses + assembly logic (keep, don't absorb — has unique domain) |
| `cam/rosette/photo_converter.py` | 500 | OpenCV image → SVG/DXF pipeline |
| `cam/rosette/photo_batch.py` + `photo_batch_router.py` | 750 | Batch photo processing |
| `cam/rosette/image_prompts.py` | 370 | AI image generation prompts |
| `art_studio/services/rosette_snapshot_store.py` | 200 | Atomic persistence, SHA256 dedup |
| `art_studio/services/rosette_preview_renderer.py` | 200 | Art Studio SVG preview |

---

## Phase 0 — Consolidation (Do First, Before Any Integration)

**Goal:** Delete dead code, absorb skeletons, merge stores. Zero new features — pure cleanup.

### 0A. Delete dead files

Remove 3 files with zero callers and zero real logic:

```
DELETE  cam/rosette/herringbone.py          (24 lines, 0 callers)
DELETE  cam/rosette/kerf_compensation.py    (18 lines, 0 callers)  
DELETE  cam/rosette/saw_batch_generator.py  (24 lines, 0 callers)
```

**Verification:** `grep -r "herringbone\|kerf_compensation\|saw_batch_generator" services/api/app/ --include="*.py"` confirms no imports. Run `pytest` after deletion to verify nothing breaks.

### 0B. Absorb skeleton engines into `tile_segmentation.py`

The existing `tile_segmentation.py` already has real implementations of everything the skeleton engines claim to do:

| Skeleton function | Real replacement already in `tile_segmentation.py` |
|---|---|
| `segmentation_engine.compute_tile_segmentation()` | `compute_ring_segmentation()` — real circumference-based tile count |
| `slice_engine.generate_slices_for_ring()` | Tile angles come directly from `TileGeometry.theta_start_rad` / `theta_end_rad` |
| `kerf_engine.apply_kerf_physics()` | `compute_tile_geometry(kerf_mm=...)` already does kerf compensation |
| `twist_engine.apply_twist()` / `apply_herringbone()` | Add `rotate_tiles()` method to `RingSegmentation` (10 lines) |
| `preview_engine.generate_preview()` | Superseded by wheel designer SVG renderer |

**After absorption, delete:**
```
DELETE  cam/rosette/segmentation_engine.py
DELETE  cam/rosette/slice_engine.py
DELETE  cam/rosette/kerf_engine.py
DELETE  cam/rosette/twist_engine.py
DELETE  cam/rosette/preview_engine.py
DELETE  cam/rosette/ring_engine.py          (orchestrator of deleted files)
```

**Update `rosette_cnc_wiring.py`:** This is the only real consumer. Change its imports from the skeleton chain to call `tile_segmentation.compute_ring_segmentation()` directly. The wiring module already receives `RosetteRingConfig` + `SliceBatch` — it doesn't care which engine produced them.

### 0C. Consolidate CNC micro-files

Absorb 5 tiny CNC files into their natural neighbors:

| Source | → Destination | What moves |
|---|---|---|
| `cnc_kerf_physics.py` (36 lines) | `cnc_safety_validator.py` | `compute_kerf_physics()` — called right before `evaluate_cnc_safety()` anyway |
| `cnc_simulation.py` (45 lines) | `cnc_exporter.py` | `simulate_toolpaths()` — heuristic estimator, 25 lines |
| `cnc_feed_table.py` (47 lines) | `cnc_materials.py` | `FeedRule` + 3 material rules |
| `cnc_blade_model.py` (22 lines) | `cnc_materials.py` | `SawBladeModel`, `RouterBitModel` dataclasses |
| `cnc_jig_geometry.py` (32 lines) | `cnc_exporter.py` | `JigAlignment`, `MachineEnvelope` dataclasses |

**After consolidation:** `cnc/` goes from 12 files to 7:
```
cnc/__init__.py          (update re-exports)
cnc/cnc_toolpath.py      (types: ToolpathSegment, ToolpathPlan)
cnc/cnc_ring_toolpath.py (real arc geometry)
cnc/cnc_gcode_exporter.py (GRBL/FANUC G-code)
cnc/cnc_safety_validator.py (+ kerf physics)
cnc/cnc_exporter.py      (+ simulation + jig geometry)
cnc/cnc_materials.py     (+ feed table + blade model)
cnc/cnc_machine_profiles.py (machine config data)
```

**Update `cnc/__init__.py`** re-exports and `rosette_cnc_wiring.py` imports to match new locations.

### 0D. Absorb feasibility scorer

Move the 10 lines of RMOS delegation from `rosette_feasibility_scorer.py` into the engine (Phase 1). Delete the wrapper file.

### 0E. Merge frontend stores into one

**Current state: 3 stores, overlapping responsibilities**

| Store | Lines | State |
|---|---:|---|
| `rosetteStore.ts` | ~800 | ParamSpec, patterns, generators, snapshots, feasibility, undo/redo |
| `useRosetteDesignerStore.ts` | ~300 | Rings, segmentation, slices, CNC export |
| `useRosetteWheelStore.ts` | ~400 | Grid, BOM, MFG checks, recipes, SVG |

**Merged store: `useRosetteStore.ts`** (composition API / setup store syntax)

The unified store uses tabs/phases as conceptual sections, not separate stores:

```typescript
export const useRosetteStore = defineStore('rosette', () => {
    // ─── DESIGN (from wheel store) ───
    const grid = ref<Record<string, string>>({})
    const numSegs = ref(12)
    const symMode = ref<SymmetryMode>('rotational')
    const ringActive = ref([true, true, true, true, true])
    const designName = ref('Untitled Design')

    // ─── GEOMETRY (from designer store) ───
    const rings = ref<RosetteRing[]>([])
    const segmentation = ref<SegmentationResult | null>(null)
    const sliceBatch = ref<SliceBatch | null>(null)

    // ─── MANUFACTURING (from both stores) ───
    const bom = ref<BomResponse | null>(null)
    const mfgChecks = ref<MfgCheckResponse | null>(null)
    const feasibility = ref<FeasibilitySummary | null>(null)
    const toolpathPlans = ref<ToolpathPlan[]>([])
    const gcodeResult = ref<string | null>(null)

    // ─── PERSISTENCE (from rosette store) ───
    const snapshots = ref<SnapshotSummary[]>([])
    const patterns = ref<PatternSummary[]>([])
    const selectedPattern = ref<PatternRecord | null>(null)

    // ─── PREVIEW ───
    const previewSvg = ref<string>('')

    // ─── UNDO/REDO (from rosette store) ───
    const historyStack = ref<HistoryEntry[]>([])
    const redoStack = ref<HistoryEntry[]>([])

    // Actions span the full workflow...
    async function placeTile(...) { }
    async function segmentRings() { }
    async function generateToolpaths() { }
    async function exportGcode() { }
    async function saveSnapshot() { }
    async function checkFeasibility() { }

    return { /* all state + actions */ }
})
```

**Migration strategy:**
1. Create new unified `useRosetteStore.ts` (setup store syntax per copilot-instructions rule 13)
2. Move state + actions from all 3 stores, resolving overlaps
3. Update all Vue components to use the single store
4. Delete old `rosetteStore.ts`, `useRosetteDesignerStore.ts`, `useRosetteWheelStore.ts`

### Phase 0 verification

```bash
# After all deletions/absorptions:
cd services/api && pytest tests/ -v --tb=short     # All existing tests pass
make check-boundaries                               # No fence violations
cd packages/client && npm run test                  # Frontend tests pass
grep -r "from.*kerf_engine\|from.*slice_engine\|from.*segmentation_engine\|from.*twist_engine\|from.*herringbone\|from.*kerf_compensation\|from.*saw_batch_gen\|from.*preview_engine\|from.*ring_engine" services/api/app/ --include="*.py"
# ^ Must return 0 results (no stale imports)
```

### Phase 0 net result

| Metric | Before | After |
|---|---:|---:|
| `cam/rosette/*.py` | 23 | 14 |
| `cam/rosette/cnc/*.py` | 12 | 7 |
| `art_studio/` rosette services | 4 | 3 |
| Frontend stores | 3 | 1 |
| Total rosette files | ~42 | ~25 |
| Skeleton Python LoC deleted | — | ~350 |

---

## Phase 1 — Unified Rosette Engine

**Goal:** Create `RosetteEngine` — a single orchestrator that owns the complete design → geometry → manufacturing pipeline. Zero new files in `cam/rosette/`; the engine lives in `art_studio/` and calls into CAM functions directly (no fence violation per `FENCE_REGISTRY.json` audit).

### Why one engine works

The fence registry only blocks:
- `RMOS → CAM` and `CAM → RMOS` (cross-domain)
- `AI sandbox → RMOS/CAM` (isolation)
- `Saw Lab → CAM` (must use CamIntentV1)

**`art_studio` has no fence restrictions.** It can freely import from `cam.rosette.tile_segmentation`, `cam.rosette.cnc`, and `cam.rosette.rosette_cnc_wiring`. This makes a unified engine in `art_studio` architecturally clean.

### Engine design

**File:** `art_studio/services/rosette_engine.py`

This replaces the current `art_studio/services/generators/rosette_designer.py` (which becomes a submodule of the engine for SVG rendering).

```python
class RosetteEngine:
    """
    Unified rosette engine: design → geometry → manufacturing → export.
    
    Single orchestrator that delegates to CAM geometry modules for
    real math and CNC modules for toolpath/G-code generation.
    """
    
    # ─── DESIGN (ported from rosette_designer.py generator) ───
    
    def place_tile(self, grid, ring_idx, seg_idx, tile_id, sym_mode, num_segs, ring_active):
        """Place tile respecting symmetry. Returns (new_grid, affected_keys)."""

    def get_symmetry_cells(self, ring_idx, seg_idx, sym_mode, num_segs):
        """Return cells affected by symmetry mode."""

    def cell_info(self, ring_idx, seg_idx, num_segs, grid):
        """Return info about a hovered cell."""

    def load_recipe(self, recipe_id):
        """Load a recipe preset or a saved pattern."""

    def render_preview_svg(self, state, width=620, height=620):
        """Generate full SVG preview with tile fills, tabs, annotations."""

    # ─── GEOMETRY (calls cam/rosette/tile_segmentation.py) ───

    def segment_ring(self, ring_def, num_segs, kerf_mm=0.3):
        """Segment one ring into tiles with real trapezoid geometry.
        Delegates to tile_segmentation.compute_ring_segmentation()."""

    def segment_all_rings(self, state, kerf_mm=0.3):
        """Segment all active rings from a design state.
        Returns dict[ring_idx → RingSegmentation]."""

    # ─── UNIT BRIDGE (SVG units ↔ mm) ───

    def ring_def_to_mm(self, ring_def):
        """Convert RingDef SVG units to mm. (r * 0.254)"""

    def state_to_ring_configs(self, state, kerf_mm=0.3):
        """Convert RosetteDesignState → list[RosetteRingConfig].
        This is the Phase 1 bridge — eliminates need for wheel_cam_bridge.py."""

    def state_to_param_spec(self, state):
        """Convert RosetteDesignState → RosetteParamSpec.
        For snapshot/feasibility compatibility."""

    # ─── MANUFACTURING ───

    def compute_bom(self, state):
        """BOM computation (ported from rosette_designer.py)."""

    def check_manufacturing(self, state):
        """Run 6 MFG intelligence checks (ported from rosette_designer.py)."""

    def check_feasibility(self, state):
        """Feasibility scoring via RMOS (absorbs rosette_feasibility_scorer.py)."""

    def plan_toolpaths(self, state, material='hardwood', jig_alignment=None, envelope=None):
        """Generate toolpath plans for all active rings.
        Calls rosette_cnc_wiring.build_ring_cnc_export() per ring."""

    def export_gcode(self, toolpath_plans, profile='grbl'):
        """Generate G-code from toolpath plans.
        Calls cnc_gcode_exporter.generate_gcode_from_toolpaths()."""

    # ─── PERSISTENCE ───

    def save_snapshot(self, state, name=None, tags=None):
        """Save design as RosetteDesignSnapshot with full grid in metadata."""

    def load_snapshot(self, snapshot_id):
        """Load snapshot, reconstruct grid from metadata if available."""

    # ─── TRADITIONAL / PRESETS ───

    def build_traditional_project(self, state):
        """Generate craftsman project sheet from design."""

    def list_presets(self):
        """Unified preset list: wheel recipes + CAM preset matrices."""
```

### What the engine absorbs vs. delegates

| Responsibility | Absorbs (inline) | Delegates to (external call) |
|---|---|---|
| Tile placement + symmetry | From `rosette_designer.py` generator | — |
| SVG preview rendering | From `rosette_designer.py` generator | — |
| BOM + MFG checks | From `rosette_designer.py` generator | — |
| Recipe/preset loading | From `rosette_designer.py` generator + `presets.py` | `presets.py` for matrix data |
| Unit conversion (SVG→mm) | New bridge methods | — |
| Ring segmentation | — | `tile_segmentation.compute_ring_segmentation()` |
| Toolpath generation | — | `rosette_cnc_wiring.build_ring_cnc_export()` |
| G-code export | — | `cnc_gcode_exporter.generate_gcode_from_toolpaths()` |
| Feasibility scoring | From `rosette_feasibility_scorer.py` | RMOS `score_design_feasibility()` |
| Snapshot persistence | — | `rosette_snapshot_store.save_snapshot()` / `load_snapshot()` |
| Pattern generation (matrix) | — | `pattern_generator.RosettePatternEngine` |
| Safety validation | — | `cnc_safety_validator.evaluate_cnc_safety()` |

### Route consolidation

The 13 existing wheel designer endpoints stay at `/api/art/rosette-designer/`. New manufacturing endpoints are added to the same router, not a separate one:

```python
# Existing (keep):
POST /place-tile
POST /symmetry-cells
GET  /cell-info
POST /bom
POST /mfg-check
GET  /recipes
POST /preview
POST /export-svg
POST /export-bom-csv
GET  /catalog

# New (add to same router — engine handles full pipeline):
POST /segment-rings          # Returns RingSegmentation[] for all active rings
POST /plan-toolpaths         # Returns ToolpathPlan[] with safety decision
POST /export-gcode           # Returns G-code string (GRBL/FANUC)
POST /check-feasibility      # Returns FeasibilitySummary + merged MFG flags  
POST /save-snapshot          # Persists design with full grid round-trip
GET  /snapshots              # List saved snapshots
POST /traditional-project    # Generate craftsman project sheet
GET  /presets                # Unified preset list (recipes + CAM matrices)
```

**Net effect:** 0 new router files. 0 new bridge files. 0 new adapter files. All integration is methods on the engine.

### Files to create

| File | Purpose |
|---|---|
| `art_studio/services/rosette_engine.py` | **THE** unified engine |

### Files to modify

| File | Change |
|---|---|
| `art_studio/api/rosette_designer_routes.py` | Add 8 new endpoints, switch from calling generator functions to calling `RosetteEngine` methods |
| `art_studio/schemas/rosette_designer.py` | Add request/response models for new endpoints |

### Files to delete (after engine absorbs their logic)

| File | Absorbed by |
|---|---|
| `art_studio/services/generators/rosette_designer.py` | Ported into `RosetteEngine` design methods |
| `art_studio/services/rosette_feasibility_scorer.py` | Ported into `RosetteEngine.check_feasibility()` |

### Key design decisions

1. **`RosetteEngine` is stateless.** It takes a `RosetteDesignState` as input and returns results. State lives in the Pinia store (frontend) or the snapshot store (persistence). The engine is a pure function machine.

2. **SVG unit conversion happens in exactly one place:** `ring_def_to_mm()`. Every method that touches real geometry calls this first. No conversion math leaks into CAM modules.

3. **Tile → material mapping is a dict on the engine**, not a separate module. 19 entries, static data.

4. **The engine doesn't subclass or inherit.** It's a plain class with methods. CAM modules are called as functions, not as base classes.

### Tests

Tests for the new engine replace and extend the existing 65 tests:

- All existing wheel designer tests pass through the engine (same API contract)
- Unit conversion: `ring_def_to_mm()` for all 5 rings matches hand-computed values
- `state_to_ring_configs()` produces valid RosetteRingConfig for each ring
- `state_to_param_spec()` round-trips through snapshot store
- `segment_all_rings()` calls real tile_segmentation and returns TileGeometry with correct trapezoid corners
- `plan_toolpaths()` produces non-empty ToolpathPlan with valid segment coordinates
- `export_gcode()` output starts with header, ends with M30, coordinates in mm
- `check_feasibility()` returns valid score for each recipe preset
- `save_snapshot()` → `load_snapshot()` round-trips with grid preservation
- Integration: recipe → engine → toolpaths → gcode end-to-end

---

## Phase 2 — Unified Frontend Store

**Goal:** Replace 3 stores with 1. The new store mirrors the engine's workflow phases.

**Depends on:** Phase 0E (store merge) + Phase 1 (engine endpoints exist)

### Store design

**File:** `client/src/stores/useRosetteStore.ts` (setup store / composition API)

```typescript
export const useRosetteStore = defineStore('rosette', () => {
    // ─── WORKFLOW PHASE ───
    const phase = ref<'design' | 'geometry' | 'manufacturing' | 'export'>('design')
    
    // ─── DESIGN STATE (from useRosetteWheelStore) ───
    const designState = ref<RosetteDesignState>(defaultDesignState())
    const previewSvg = ref('')
    const bom = ref<BomResponse | null>(null)
    const mfgChecks = ref<MfgCheckResponse | null>(null)
    
    // ─── GEOMETRY STATE (from useRosetteDesignerStore) ───
    const ringSegmentations = ref<Record<number, RingSegmentation>>({})
    
    // ─── MANUFACTURING STATE ───
    const feasibility = ref<FeasibilitySummary | null>(null)
    const toolpathPlans = ref<ToolpathPlan[]>([])
    const gcodeResult = ref<string | null>(null)
    const safetyDecision = ref<SafetyDecision | null>(null)

    // ─── PERSISTENCE (from rosetteStore) ───  
    const snapshots = ref<SnapshotSummary[]>([])
    const patterns = ref<PatternSummary[]>([])

    // ─── UNDO/REDO (from rosetteStore) ───
    const historyStack = ref<HistoryEntry[]>([])
    const redoStack = ref<HistoryEntry[]>([])

    // ─── LOADING STATES (one per phase, not per action) ───
    const designLoading = ref(false)
    const geometryLoading = ref(false)
    const manufacturingLoading = ref(false)

    // Actions call engine endpoints via SDK
    async function placeTile(ringIdx: number, segIdx: number, tileId: string) { }
    async function segmentRings() { }
    async function planToolpaths(material: string, profile: string) { }
    async function exportGcode() { }
    async function checkFeasibility() { }
    async function saveSnapshot(name?: string) { }
    async function loadRecipe(recipeId: string) { }

    return { phase, designState, previewSvg, bom, mfgChecks, 
             ringSegmentations, feasibility, toolpathPlans, gcodeResult,
             safetyDecision, snapshots, patterns, historyStack, redoStack,
             designLoading, geometryLoading, manufacturingLoading,
             placeTile, segmentRings, planToolpaths, exportGcode,
             checkFeasibility, saveSnapshot, loadRecipe }
})
```

### SDK consolidation

All rosette SDK calls go through one namespace. No separate `cam` vs `art` namespaces for rosette operations:

```typescript
// src/sdk/endpoints/art.ts (or rosette.ts if split by domain)
export const rosette = {
    placeTile: (req: PlaceTileRequest) => post('/api/art/rosette-designer/place-tile', req),
    preview: (req: PreviewRequest) => post('/api/art/rosette-designer/preview', req),
    bom: (req: BomRequest) => post('/api/art/rosette-designer/bom', req),
    mfgCheck: (req: MfgCheckRequest) => post('/api/art/rosette-designer/mfg-check', req),
    segmentRings: (req: SegmentRequest) => post('/api/art/rosette-designer/segment-rings', req),
    planToolpaths: (req: ToolpathRequest) => post('/api/art/rosette-designer/plan-toolpaths', req),
    exportGcode: (req: GcodeRequest) => post('/api/art/rosette-designer/export-gcode', req),
    checkFeasibility: (req: FeasibilityRequest) => post('/api/art/rosette-designer/check-feasibility', req),
    saveSnapshot: (req: SnapshotRequest) => post('/api/art/rosette-designer/save-snapshot', req),
    listSnapshots: () => get('/api/art/rosette-designer/snapshots'),
    recipes: () => get('/api/art/rosette-designer/recipes'),
    presets: () => get('/api/art/rosette-designer/presets'),
    catalog: () => get('/api/art/rosette-designer/catalog'),
}
```

### View update

`RosetteWheelView.vue` adds workflow tabs and manufacturing controls. No new view files needed — the existing view expands to cover the full pipeline:

| Tab | Content | Backed by |
|---|---|---|
| Design | Current wheel + tile palette + symmetry controls | `placeTile()`, `preview()` |
| Analysis | BOM + MFG checks + feasibility score | `bom()`, `mfgCheck()`, `checkFeasibility()` |
| Manufacturing | Ring segmentation, toolpath preview, safety status | `segmentRings()`, `planToolpaths()` |
| Export | G-code download, traditional project sheet, save snapshot | `exportGcode()`, `saveSnapshot()` |

### Files to create

| File | Purpose |
|---|---|
| `client/src/stores/useRosetteStore.ts` | Unified store (replaces 3 stores) |

### Files to delete

| File | Replaced by |
|---|---|
| `client/src/stores/rosetteStore.ts` | Unified store |
| `client/src/stores/useRosetteDesignerStore.ts` | Unified store |
| `client/src/stores/useRosetteWheelStore.ts` | Unified store |

### Files to modify

| File | Change |
|---|---|
| `client/src/sdk/endpoints/art.ts` | Add unified rosette SDK namespace |
| `client/src/types/rosetteDesigner.ts` | Add geometry + manufacturing types |
| `client/src/views/art-studio/RosetteWheelView.vue` | Add workflow tabs + manufacturing UI |

---

## Phase 3 — Preset & Pattern Unification

**Goal:** Merge wheel recipes + CAM preset matrices into a single pattern catalog.

**Depends on:** Phase 1 (engine has `list_presets()` and `load_recipe()`)

### Unified preset format

Both systems describe "a rosette design" differently:
- **Wheel recipes:** grid dict + segment count + symmetry mode (visual)
- **CAM presets:** matrix formula + strip dimensions (manufacturing)

The engine stores both in a unified format:

```python
class RosettePreset:
    id: str                          # "torres_simple_rope" or "wheel_classical"
    name: str                        # "Torres Simple Rope" or "Classical Guitar"
    source: Literal["cam", "wheel"]  # Where it came from
    tags: list[str]                  # ["classical", "spanish", "beginner"]
    # Visual representation (for wheel editor)
    wheel_grid: Optional[dict]       # Grid dict, if available
    num_segs: Optional[int]
    sym_mode: Optional[str]
    # Manufacturing representation (for CAM pipeline)  
    matrix_formula: Optional[MatrixFormula]  # Matrix, if available
    # Computed on demand
    param_spec: Optional[RosetteParamSpec]   # Derived from either source
```

**Bidirectional conversion:**
- Wheel → CAM: `engine.recipe_to_matrix(recipe)` — maps grid tiles to matrix rows
- CAM → Wheel: `engine.matrix_to_grid(preset)` — best-effort (lossy for complex matrices)

### Pattern library integration

Saved wheel designs and saved CAM patterns share one storage endpoint:

```
POST /api/art/rosette-designer/patterns          # Save a pattern
GET  /api/art/rosette-designer/patterns          # List all (both sources)
GET  /api/art/rosette-designer/patterns/{id}     # Get one
DELETE /api/art/rosette-designer/patterns/{id}   # Delete one
```

### Files to modify

| File | Change |
|---|---|
| `art_studio/services/rosette_engine.py` | Add `recipe_to_matrix()`, `matrix_to_grid()`, unified preset loading |
| `art_studio/schemas/rosette_designer.py` | Add `RosettePreset` model |
| `art_studio/api/rosette_designer_routes.py` | Add pattern CRUD endpoints |

---

## Implementation Sequence

```
Phase 0 (Consolidation)  ← No features, pure cleanup
    Delete 3 dead files
    Absorb 6 skeleton engines into tile_segmentation.py
    Consolidate 5 CNC micro-files
    Merge 3 frontend stores → 1
    │
    └──→ Phase 1 (Unified Engine)  ← The integration
             Create RosetteEngine with design + geometry + manufacturing + export
             Add 8 new API endpoints to existing router
             │
             ├──→ Phase 2 (Unified Store + UI)  ← Frontend wiring
             │        Replace 3 stores with 1
             │        Add workflow tabs to view
             │
             └──→ Phase 3 (Presets)  ← Enrichment
                      Merge recipes + CAM presets
                      Pattern library CRUD
```

### Sprint plan

| Sprint | Phase | Net File Change | Deliverable |
|---|---|---:|---|
| Sprint 1 | Phase 0A + 0B | −9 Python files | Delete dead + absorb skeletons |
| Sprint 2 | Phase 0C + 0D | −6 Python files | Consolidate CNC + absorb feasibility |
| Sprint 3 | Phase 0E | −2 TS files | Merge 3 stores → 1 |
| Sprint 4 | Phase 1 | +1 Python file, −2 Python files | `RosetteEngine` (absorbs generator + feasibility) |
| Sprint 5 | Phase 2 | 0 net new files | Unified store, SDK, workflow UI |
| Sprint 6 | Phase 3 | 0 net new files | Preset unification |

**Total across all sprints: −18 files net**

---

## Unit Conversion Reference

| From | To | Formula | Example |
|---|---|---|---|
| SVG units | mm | `× 0.254` | RING_DEFS[0].r1=150 → 38.1mm |
| SVG units | inches | `× 0.01` | RING_DEFS[0].r1=150 → 1.50" |
| mm | SVG units | `÷ 0.254` | 38.1mm → 150 |
| inches | mm | `× 25.4` | 1.50" → 38.1mm |

Conversion happens in **one method only**: `RosetteEngine.ring_def_to_mm()`.

## Tile-to-CAM Compatibility Matrix

| Tile ID | Tile Type | Material Class | CAM Strategy | Notes |
|---|---|---|---|---|
| `maple` | solid | Tonewood | Standard | Good for all patterns |
| `rosewood` | solid | Tonewood | Hardwood | CITES: document sourcing |
| `ebony` | solid | Tonewood | Hardwood | Brittle: reduce feed |
| `mahogany` | solid | Tonewood | Standard | |
| `spruce` | solid | Tonewood | Softwood | Rare in rosettes |
| `walnut` | solid | Tonewood | Standard | |
| `abalone` | abalone | Shell | Inlay | Fragile: ultra-light cuts |
| `mop` | mop | Shell | Inlay | Fragile: ultra-light cuts |
| `burl` | burl | Tonewood | Hardwood | Irregular grain: variable |
| `cream` | solid | Tonewood | Standard | Holly or bleached maple |
| `bwb` | stripes | Purfling | Mosaic | Pre-made strip: no CAM |
| `rbr` | stripes2 | Purfling | Mosaic | Pre-made strip: no CAM |
| `wbw` | stripes3 | Purfling | Mosaic | Pre-made strip: no CAM |
| `herringbone` | herringbone | Mosaic | Grain-aware | Angle-sensitive cuts |
| `checker` | checker | Mosaic | Standard | Alternating grain |
| `celtic` | celtic | Mosaic | Complex | Multi-pass precision |
| `diagonal` | diagonal | Mosaic | Grain-aware | Angled strip assembly |
| `dots` | dots | Inlay | Drill cycle | Dot inlay = drill holes |
| `clear` | clear | None | Skip | No material |

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Engine class grows too large | God-object creation (>1000 lines) | Cap at ~600 lines. Design + SVG methods stay in a private `_rendering.py` mixin. |
| Store merge breaks existing views | Components reference old store names | Sed/grep rename pass + TypeScript compiler catches all references |
| Absorbed skeleton tests break | Tests import deleted module names | Update imports to new locations. Tests verify same behavior. |
| `tile_segmentation.py` becomes overloaded | Too many responsibilities | It only absorbs type aliases, not logic. Real new logic is minimal (10-line `rotate_tiles()`). |
| Rosette CNC wiring breaks on import changes | CNC export pipeline disrupted | Run CNC-specific tests after every absorption: `pytest -m cam` |

## Boundary Fence Compliance

```
art_studio/services/rosette_engine.py
  IMPORTS (all legal per FENCE_REGISTRY.json):
    ✅ from app.art_studio.schemas.rosette_designer import ...    (own domain)
    ✅ from app.art_studio.schemas.rosette_params import ...      (own domain)
    ✅ from app.cam.rosette.tile_segmentation import ...          (art_studio has NO fence)
    ✅ from app.cam.rosette.rosette_cnc_wiring import ...         (art_studio has NO fence)
    ✅ from app.cam.rosette.cnc.cnc_gcode_exporter import ...     (art_studio has NO fence)
    ✅ from app.cam.rosette.models import RosetteRingConfig       (art_studio has NO fence)
    ✅ from app.rmos.api_contracts import RmosContext              (for feasibility delegation)
    ❌ WOULD BE BLOCKED IF: this file lived in app/rmos/ or app/cam/ (but it doesn't)
```

The key architectural insight enabling one engine: **`art_studio/` is unfenced.** It can import from anywhere except external repos (`tap_tone.*`, `modes.*`). The engine lives in art_studio and freely calls CAM functions as an integration layer.
