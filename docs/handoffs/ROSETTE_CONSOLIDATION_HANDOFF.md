# Rosette Consolidation — Developer Handoff

**Purpose:** Exact coordinates of every file that needs to be decomposed, deleted, absorbed, or rewired for the consolidation-first engine plan.  
**Reference:** [ROSETTE_WHEEL_ENGINE_INTEGRATION_PLAN.md](ROSETTE_WHEEL_ENGINE_INTEGRATION_PLAN.md)  
**Date:** March 14, 2026

---

## Quick Navigation

| Section | What |
|---|---|
| [Section A](#a--delete-targets-3-files) | 3 files to delete outright |
| [Section B](#b--skeleton-engines-to-absorb-6-files) | 6 skeleton engines → absorb into `tile_segmentation.py` |
| [Section C](#c--cnc-micro-files-to-absorb-5-files) | 5 CNC micro-files → absorb into neighbors |
| [Section D](#d--art-studio-absorb-1-file) | 1 feasibility wrapper → absorb into engine |
| [Section E](#e--re-export-chains-to-rewire-3-files) | 3 files that re-export deleted symbols |
| [Section F](#f--frontend-stores-to-merge-3-files) | 3 Pinia stores → merge into 1 |
| [Section G](#g--receiver-files-absorb-destinations) | 4 files that receive absorbed code |
| [Section H](#h--engine-source-file-to-port) | 1 generator file (939 lines) → port into RosetteEngine |
| [Section I](#i--landing-spot-new-file) | 1 new file to create: `rosette_engine.py` |

---

## A — DELETE Targets (3 files)

Pure skeleton, zero real callers outside `__init__.py`. Safe to nuke after removing re-exports.

### A1. `herringbone.py`

```
Path:   services/api/app/cam/rosette/herringbone.py
Lines:  1–24 (24 total)
```

| Item | Lines | What |
|---|---|---|
| `apply_herringbone_stub()` | L7–L24 | Dict copy, returns input unchanged |

**Callers to update:**
| Caller | Line | Import to remove |
|---|---|---|
| `cam/rosette/__init__.py` | L27 | `from .herringbone import apply_herringbone_stub` |
| `cam/rosette/__init__.py` | L55 | `"apply_herringbone_stub"` in `__all__` |

---

### A2. `kerf_compensation.py`

```
Path:   services/api/app/cam/rosette/kerf_compensation.py
Lines:  1–22 (22 total)
```

| Item | Lines | What |
|---|---|---|
| `apply_kerf_compensation_stub()` | L7–L22 | Dict copy, no angle math |

**Callers to update:**
| Caller | Line | Import to remove |
|---|---|---|
| `cam/rosette/__init__.py` | L26 | `from .kerf_compensation import apply_kerf_compensation_stub` |
| `cam/rosette/__init__.py` | L54 | `"apply_kerf_compensation_stub"` in `__all__` |

---

### A3. `saw_batch_generator.py`

```
Path:   services/api/app/cam/rosette/saw_batch_generator.py
Lines:  1–38 (38 total)
```

| Item | Lines | What |
|---|---|---|
| `generate_saw_batch_stub()` | L7–L38 | Trivial SliceBatch builder |

**Callers to update:**
| Caller | Line | Import to remove |
|---|---|---|
| `cam/rosette/__init__.py` | L28 | `from .saw_batch_generator import generate_saw_batch_stub` |
| `cam/rosette/__init__.py` | L56 | `"generate_saw_batch_stub"` in `__all__` |

---

## B — Skeleton Engines to Absorb (6 files)

All 6 are called only by `ring_engine.py` (itself a skeleton) and re-exported from `__init__.py`. After absorbing their logic into `tile_segmentation.py`, delete all 6 plus `ring_engine.py`.

### B1. `segmentation_engine.py`

```
Path:   services/api/app/cam/rosette/segmentation_engine.py
Lines:  1–48 (48 total)
Imports: L7–L11
```

| Item | Lines | What | Absorb Into |
|---|---|---|---|
| `compute_tile_segmentation()` | L14–L48 | Hardcoded tile_count=8 | **Superseded** — `tile_segmentation.py` L221–L264 `compute_ring_segmentation()` already does real geometry |

**Callers to update:**
| Caller | Line | Import to change |
|---|---|---|
| `cam/rosette/__init__.py` | L39 | `from .segmentation_engine import ...` → redirect to `tile_segmentation` |
| `cam/rosette/ring_engine.py` | L10 | Dead after ring_engine is deleted |
| **`rmos/stub_routes.py`** | **L48** | `from ..cam.rosette.segmentation_engine import compute_tile_segmentation` → `from ..cam.rosette.tile_segmentation import compute_tile_segmentation` |

---

### B2. `slice_engine.py`

```
Path:   services/api/app/cam/rosette/slice_engine.py
Lines:  1–52 (52 total)
Imports: L7–L10
```

| Item | Lines | What | Absorb Into |
|---|---|---|---|
| `generate_slices_for_ring()` | L13–L52 | Angle = tile center, no twist/kerf | `tile_segmentation.py` — add as method on `RingSegmentation` or standalone function |

**Callers to update:**
| Caller | Line | Import to change |
|---|---|---|
| `cam/rosette/__init__.py` | L40 | Redirect to `tile_segmentation` |
| `cam/rosette/ring_engine.py` | L11 | Dead after ring_engine is deleted |
| **`rmos/stub_routes.py`** | **L49** | `from ..cam.rosette.slice_engine import ...` → `from ..cam.rosette.tile_segmentation import ...` |

---

### B3. `kerf_engine.py`

```
Path:   services/api/app/cam/rosette/kerf_engine.py
Lines:  1–35 (35 total)
Imports: L7–L10
```

| Item | Lines | What | Absorb Into |
|---|---|---|---|
| `apply_kerf_physics()` | L13–L35 | Stores kerf_mm, no angle compensation | **Superseded** — `tile_segmentation.py` L163–L218 `compute_tile_geometry()` already takes `kerf_mm` param and does real angular kerf compensation |

**Callers to update:**
| Caller | Line | Import to change |
|---|---|---|
| `cam/rosette/__init__.py` | L41 | Remove or redirect |
| `cam/rosette/ring_engine.py` | L12 | Dead after ring_engine is deleted |

---

### B4. `twist_engine.py`

```
Path:   services/api/app/cam/rosette/twist_engine.py
Lines:  1–55 (55 total)
Imports: L7–L10
```

| Item | Lines | What | Absorb Into |
|---|---|---|---|
| `apply_twist()` | L13–L32 | Sets offset on slices | `tile_segmentation.py` — add `rotate_tiles()` method to `RingSegmentation` (~10 lines) |
| `apply_herringbone()` | L35–L55 | Sets herringbone_flip flag | Same — add to `RingSegmentation` |

**Callers to update:**
| Caller | Line | Import to change |
|---|---|---|
| `cam/rosette/__init__.py` | L42 | Redirect to `tile_segmentation` |
| `cam/rosette/ring_engine.py` | L13 | Dead after ring_engine is deleted |

---

### B5. `ring_engine.py`

```
Path:   services/api/app/cam/rosette/ring_engine.py
Lines:  1–40 (40 total)
Imports: L7–L13 — imports all 4 skeletons above
```

| Item | Lines | What | Absorb Into |
|---|---|---|---|
| `compute_ring_geometry()` | L16–L40 | Orchestrator: segmentation → slices → kerf → twist | **Delete** — the 20 lines of orchestration become a method on `RosetteEngine` |

**Callers to update:**
| Caller | Line | Import to change |
|---|---|---|
| `cam/rosette/__init__.py` | L43 | Remove `from .ring_engine import compute_ring_geometry` |

---

### B6. `preview_engine.py`

```
Path:   services/api/app/cam/rosette/preview_engine.py
Lines:  1–52 (52 total)
Imports: L7–L14
```

| Item | Lines | What | Absorb Into |
|---|---|---|---|
| `build_preview_snapshot()` | L17–L52 | Returns tile/slice count summary | **Superseded** — wheel designer SVG renderer does real preview |

**Callers to update:**
| Caller | Line | Import to change |
|---|---|---|
| `cam/rosette/__init__.py` | L44 | Remove |
| **`rmos/stub_routes.py`** | **L50** | `from ..cam.rosette.preview_engine import build_preview_snapshot` → remove or redirect to engine |

---

## C — CNC Micro-Files to Absorb (5 files)

### C1. `cnc_kerf_physics.py` → absorb into `cnc_safety_validator.py`

```
Path:   services/api/app/cam/rosette/cnc/cnc_kerf_physics.py
Lines:  1–42 (42 total)
```

| Item | Lines | Destination | Destination Line |
|---|---|---|---|
| `KerfPhysicsResult` (dataclass) | L9–L12 | `cnc_safety_validator.py` before L14 | Insert at top of file after imports |
| `compute_kerf_physics()` | L15–L42 | `cnc_safety_validator.py` after L25 | After `_segment_length_mm`, before `evaluate_cnc_safety` |

**Callers to update:**
| Caller | Line | Change |
|---|---|---|
| `cnc/__init__.py` | L15 | `from .cnc_kerf_physics import ...` → `from .cnc_safety_validator import ...` |
| `cnc_safety_validator.py` | L11 | Remove `from .cnc_kerf_physics import KerfPhysicsResult` (now local) |

---

### C2. `cnc_simulation.py` → absorb into `cnc_exporter.py`

```
Path:   services/api/app/cam/rosette/cnc/cnc_simulation.py
Lines:  1–59 (59 total)
```

| Item | Lines | Destination |
|---|---|---|
| `CNCSimulationResult` (dataclass) | L10–L14 | `cnc_exporter.py` after `CNCExportBundle` class |
| `simulate_toolpaths()` | L17–L59 | `cnc_exporter.py` after `build_export_bundle_skeleton` |

**Callers to update:**
| Caller | Line | Change |
|---|---|---|
| `cnc/__init__.py` | L37 | `from .cnc_simulation import ...` → `from .cnc_exporter import ...` |

---

### C3. `cnc_feed_table.py` → absorb into `cnc_materials.py`

```
Path:   services/api/app/cam/rosette/cnc/cnc_feed_table.py
Lines:  1–59 (59 total)
```

| Item | Lines | Destination |
|---|---|---|
| `MaterialType` (Enum) | L8–L11 | `cnc_materials.py` at top (it already imports this) |
| `FeedRule` (dataclass) | L14–L18 | `cnc_materials.py` — **note: cnc_materials already has its own `FeedRule` (L15–L20) with extra fields.** Merge: keep the richer version, add simpler fields if missing |
| `HARDWOOD_RULE`, `SOFTWOOD_RULE`, `COMPOSITE_RULE` | L21–L40 | `cnc_materials.py` as constants |
| `select_feed_rule()` | L43–L59 | `cnc_materials.py` — rename to `select_basic_feed_rule()` to distinguish from existing `select_feed_rule()` (L59–L79) which is the richer version |

**Callers to update:**
| Caller | Line | Change |
|---|---|---|
| `cnc/__init__.py` | L19 | `from .cnc_feed_table import ...` → `from .cnc_materials import ...` |
| `cnc_materials.py` | L12 | Remove `from .cnc_feed_table import MaterialType` (now local) |

---

### C4. `cnc_blade_model.py` → absorb into `cnc_materials.py`

```
Path:   services/api/app/cam/rosette/cnc/cnc_blade_model.py
Lines:  1–37 (37 total)
```

| Item | Lines | Destination |
|---|---|---|
| `SawBladeModel` (dataclass) | L8–L17 | `cnc_materials.py` — add after FeedRule |
| `RouterBitModel` (dataclass) | L20–L29 | `cnc_materials.py` — add after SawBladeModel |
| `ToolMode` (Enum) | L32–L34 | `cnc_materials.py` — add near MaterialType |

**Callers to update:**
| Caller | Line | Change |
|---|---|---|
| `cnc/__init__.py` | L7 | `from .cnc_blade_model import ...` → `from .cnc_materials import ...` |

---

### C5. `cnc_jig_geometry.py` → absorb into `cnc_exporter.py`

```
Path:   services/api/app/cam/rosette/cnc/cnc_jig_geometry.py
Lines:  1–48 (48 total)
```

| Item | Lines | Destination |
|---|---|---|
| `JigAlignment` (dataclass with `as_dict`) | L7–L23 | `cnc_exporter.py` — add before `CNCExportBundle` |
| `MachineEnvelope` (dataclass with `contains`) | L26–L48 | `cnc_exporter.py` — add after `JigAlignment` |

**Callers to update:**
| Caller | Line | Change |
|---|---|---|
| `cnc/__init__.py` | L11 | `from .cnc_jig_geometry import ...` → `from .cnc_exporter import ...` |
| `cnc_safety_validator.py` | L9 | `from .cnc_jig_geometry import MachineEnvelope` → `from .cnc_exporter import MachineEnvelope` |
| `cnc_exporter.py` | L9 | Remove `from .cnc_jig_geometry import JigAlignment` (now local) |

---

## D — Art Studio Absorb (1 file)

### D1. `rosette_feasibility_scorer.py` → absorb into `RosetteEngine`

```
Path:   services/api/app/art_studio/services/rosette_feasibility_scorer.py
Lines:  1–68 (68 total)
Imports: L5–L9
```

| Item | Lines | Destination |
|---|---|---|
| `MaterialSpec` class | L13–L22 | `rosette_engine.py` (Phase 1) or inline in `check_feasibility()` |
| `ToolSpec` class | L25–L36 | Same |
| `estimate_rosette_feasibility()` | L39–L68 | Becomes `RosetteEngine.check_feasibility()` |

**Callers to update:**
| Caller | Line | Change |
|---|---|---|
| `art_studio/api/rosette_snapshot_routes.py` | L37 | Import from `rosette_engine` instead |

---

## E — Re-Export Chains to Rewire (3 files)

These files don't get deleted — they get **surgically edited** to point at new locations.

### E1. `cam/rosette/__init__.py`

```
Path:   services/api/app/cam/rosette/__init__.py
Lines:  1–76 (76 total)
```

**Lines to remove (imports of deleted/absorbed files):**

| Line | Current Import | Action |
|---:|---|---|
| L26 | `from .kerf_compensation import apply_kerf_compensation_stub` | DELETE |
| L27 | `from .herringbone import apply_herringbone_stub` | DELETE |
| L28 | `from .saw_batch_generator import generate_saw_batch_stub` | DELETE |
| L39 | `from .segmentation_engine import compute_tile_segmentation` | REDIRECT → `from .tile_segmentation import compute_tile_segmentation` |
| L40 | `from .slice_engine import generate_slices_for_ring` | REDIRECT → `from .tile_segmentation import generate_slices_for_ring` |
| L41 | `from .kerf_engine import apply_kerf_physics` | DELETE (superseded by tile_segmentation) |
| L42 | `from .twist_engine import apply_twist, apply_herringbone as apply_herringbone_engine` | REDIRECT → `from .tile_segmentation import apply_twist, apply_herringbone as apply_herringbone_engine` |
| L43 | `from .ring_engine import compute_ring_geometry` | DELETE |
| L44 | `from .preview_engine import build_preview_snapshot` | DELETE |

**`__all__` entries to remove/update (L48–L76):**

| Line | Symbol | Action |
|---:|---|---|
| L54 | `"apply_kerf_compensation_stub"` | DELETE |
| L55 | `"apply_herringbone_stub"` | DELETE |
| L56 | `"generate_saw_batch_stub"` | DELETE |
| L67 | `"apply_kerf_physics"` | DELETE |
| L69 | `"compute_ring_geometry"` | DELETE |
| L70 | `"build_preview_snapshot"` | DELETE |

---

### E2. `cam/rosette/cnc/__init__.py`

```
Path:   services/api/app/cam/rosette/cnc/__init__.py
Lines:  1–88 (88 total)
```

**Lines to update (imports from absorbed files):**

| Line | Current | Redirect To |
|---:|---|---|
| L7 | `from .cnc_blade_model import ...` | `from .cnc_materials import ...` |
| L11 | `from .cnc_jig_geometry import ...` | `from .cnc_exporter import ...` |
| L15 | `from .cnc_kerf_physics import ...` | `from .cnc_safety_validator import ...` |
| L19 | `from .cnc_feed_table import ...` | `from .cnc_materials import ...` |
| L37 | `from .cnc_simulation import ...` | `from .cnc_exporter import ...` |

**`__all__` — no changes needed** (symbols keep the same names, just sourced differently).

---

### E3. `rmos/stub_routes.py`

```
Path:   services/api/app/rmos/stub_routes.py
```

**Lines to update:**

| Line | Current | Change To |
|---:|---|---|
| L48 | `from ..cam.rosette.segmentation_engine import compute_tile_segmentation` | `from ..cam.rosette.tile_segmentation import compute_tile_segmentation` |
| L49 | `from ..cam.rosette.slice_engine import generate_slices_for_ring` | `from ..cam.rosette.tile_segmentation import generate_slices_for_ring` |
| L50 | `from ..cam.rosette.preview_engine import build_preview_snapshot` | **DELETE** or redirect to engine (preview_engine logic is superseded) |

---

## F — Frontend Stores to Merge (3 files → 1)

### F1. `rosetteStore.ts` (the big one — 836 lines)

```
Path:   packages/client/src/stores/rosetteStore.ts
Lines:  1–836 (836 total)
```

| Section | Lines | What Goes Into Unified Store |
|---|---|---|
| `HistoryEntry` interface | L33–L37 | Keep — undo/redo |
| `defaultSpec()` | L39–L44 | Keep — default state |
| State block | L47–L107 | Merge: `currentParams`, `patterns`, `mfgPatterns`, `generators`, `preview`, `snapshots`, `feasibility`, `history`, `redo` |
| Getters | L109–L178 | Merge: feasibility getters, ring focus, problem ring navigation |
| Actions (patterns) | L180–L310 | Merge: pattern CRUD |
| Actions (preview/feasibility) | L312–L420 | Merge: refresh actions |
| Actions (undo/redo) | L650–L836 | Merge: history management |

**Component callers to update:**
- `SnapshotComparePanel.vue`
- `artDesignFirstWorkflowStore.ts`
- `SnapshotPanel.vue`
- `RosettePreviewPanel.vue`
- `RosetteEditorView.vue`
- `useRosettePatternStore.ts` (shim — may be deletable)

---

### F2. `useRosetteDesignerStore.ts` (246 lines)

```
Path:   packages/client/src/stores/useRosetteDesignerStore.ts
Lines:  1–246 (246 total)
```

| Section | Lines | What Goes Into Unified Store |
|---|---|---|
| Interfaces (RosetteRing, etc.) | L7–L83 | Move to `types/rosetteDesigner.ts` |
| State refs | L89–L101 | Merge: `rings`, `selectedRingId`, `segmentation`, `sliceBatch`, CNC state |
| Actions | L103–L246 | Merge: `segmentSelectedRing`, `generateSlices`, `fetchPreview`, `exportCnc` |

**Component callers to update:**
- `RosetteDesignerView.vue`
- `TilePreviewCanvas.vue`
- `CNCExportPanel.vue`
- `RingConfigPanel.vue`
- `MultiRingPreviewPanel.vue`

---

### F3. `useRosetteWheelStore.ts` (538 lines)

```
Path:   packages/client/src/stores/useRosetteWheelStore.ts
Lines:  1–538 (538 total)
```

| Section | Lines | What Goes Into Unified Store |
|---|---|---|
| Constants (`SEG_OPTIONS`, `API_BASE`) | L24–L26 | Move to unified store |
| `DesignSnapshot` interface | L32–L41 | Move to types |
| `apiPost`/`apiGet` helpers | L47–L66 | **REPLACE** with SDK calls (currently raw `fetch()` — violates rule 3) |
| State refs | L80–L120 | Merge: grid, numSegs, symMode, ring toggles, BOM, MFG, SVG, undo/redo |
| Computed | L122–L139 | Merge: fillPercent, mfgBadge |
| Snapshot helpers | L142–L160 | Merge into unified undo/redo system |
| Actions | L163–L538 | Merge: tile operations, ring operations, BOM, MFG, import/export |

**Component callers to update:**
- `RosetteWheelView.vue`

**SDK violation to fix:** Lines L47–L66 use raw `fetch()` instead of SDK helpers. Must be replaced during merge.

---

## G — Receiver Files (Absorb Destinations)

These files get **bigger** as they absorb code from deleted files.

### G1. `tile_segmentation.py` — receives B1–B4 logic

```
Path:   services/api/app/cam/rosette/tile_segmentation.py
Lines:  1–303 (303 total)
```

| Current Structure | Lines |
|---|---|
| `TilePattern` enum | L19–L23 |
| `Point2D` dataclass | L26–L42 |
| `TileGeometry` dataclass (trapezoid corners, kerf) | L45–L114 |
| `RingSegmentation` dataclass | L117–L147 |
| `compute_tile_count()` | L150–L160 |
| `compute_tile_geometry()` (real kerf math) | L163–L218 |
| `compute_ring_segmentation()` | L221–L264 |
| `compute_tile_segmentation()` (facade) | L267–L297 |
| `compute_tile_segmentation_stub()` (alias) | L300 |

**What to add (after L300):**

| Function | Source | ~Lines to add |
|---|---|---|
| `generate_slices_for_ring()` | `slice_engine.py` L13–L52 | ~40 lines |
| `apply_twist()` | `twist_engine.py` L13–L32 | ~20 lines |
| `apply_herringbone()` | `twist_engine.py` L35–L55 | ~20 lines |

**What's already superseded (no code to add):**
- `segmentation_engine.compute_tile_segmentation()` → already have `compute_ring_segmentation()` (real geometry)
- `kerf_engine.apply_kerf_physics()` → already have `compute_tile_geometry(kerf_mm=...)` (real kerf)

**Expected final size:** ~380 lines (was 303)

---

### G2. `cnc_safety_validator.py` — receives C1

```
Path:   services/api/app/cam/rosette/cnc/cnc_safety_validator.py
Lines:  1–118 (118 total)
```

**What to add:**
| Item | Source | Add Where |
|---|---|---|
| `KerfPhysicsResult` dataclass | `cnc_kerf_physics.py` L9–L12 | After imports (L13) |
| `compute_kerf_physics()` | `cnc_kerf_physics.py` L15–L42 | After `_segment_length_mm` (L25) |

**Expected final size:** ~150 lines (was 118)

---

### G3. `cnc_exporter.py` — receives C2 + C5

```
Path:   services/api/app/cam/rosette/cnc/cnc_exporter.py
Lines:  1–57 (57 total)
```

**What to add:**
| Item | Source | Add Where |
|---|---|---|
| `JigAlignment` dataclass (with `as_dict`) | `cnc_jig_geometry.py` L7–L23 | Before `CNCExportBundle` (L13) |
| `MachineEnvelope` dataclass (with `contains`) | `cnc_jig_geometry.py` L26–L48 | After `JigAlignment` |
| `CNCSimulationResult` dataclass | `cnc_simulation.py` L10–L14 | After `CNCExportBundle` |
| `simulate_toolpaths()` | `cnc_simulation.py` L17–L59 | After `build_export_bundle_skeleton` |

**Expected final size:** ~170 lines (was 57)

---

### G4. `cnc_materials.py` — receives C3 + C4

```
Path:   services/api/app/cam/rosette/cnc/cnc_materials.py
Lines:  1–79 (79 total)
```

**What to add:**
| Item | Source | Add Where |
|---|---|---|
| `MaterialType` enum | `cnc_feed_table.py` L8–L11 | At top (currently imported from feed_table) |
| Basic `FeedRule` fields (if missing) | `cnc_feed_table.py` L14–L18 | Merge into existing FeedRule at L15 |
| `HARDWOOD_RULE`, `SOFTWOOD_RULE`, `COMPOSITE_RULE` | `cnc_feed_table.py` L21–L40 | After constants |
| `select_basic_feed_rule()` | `cnc_feed_table.py` L43–L59 | Rename from `select_feed_rule` to avoid clash |
| `SawBladeModel` dataclass | `cnc_blade_model.py` L8–L17 | After MaterialType |
| `RouterBitModel` dataclass | `cnc_blade_model.py` L20–L29 | After SawBladeModel |
| `ToolMode` enum | `cnc_blade_model.py` L32–L34 | Near MaterialType |

**Expected final size:** ~180 lines (was 79)

---

## H — Engine Source File to Port

### H1. `rosette_designer.py` (generator) → port into `RosetteEngine`

```
Path:   services/api/app/art_studio/services/generators/rosette_designer.py
Lines:  1–939 (939 total)
```

This file's logic becomes methods on `RosetteEngine`. Exact function map:

| Function | Lines | Engine Method |
|---|---|---|
| `_rad()` | L42 | Private helper on engine |
| `_pt_on_circle()` | L46 | Private helper on engine |
| `_fmt()` | L51 | Private helper on engine |
| `_arc_inches()` | L55 | Private helper on engine |
| `arc_cell_path()` | L62–L73 | `_arc_cell_path()` |
| `tab_path()` | L76–L86 | `_tab_path()` |
| `_TILE_FILL_MAP` dict | L92–L105 | Class constant |
| `_TILE_COLOR_HEX` dict | L107–L117 | Class constant |
| `get_tile_fill()` | L120–L127 | `_get_tile_fill()` |
| `get_tile_color_hex()` | L130–L136 | `_get_tile_color_hex()` |
| `get_sym_cells()` | L143–L166 | `get_symmetry_cells()` |
| `place_tile()` | L169–L182 | `place_tile()` |
| `cell_info()` | L189–L207 | `cell_info()` |
| `compute_bom()` | L214–L296 | `compute_bom()` |
| `bom_to_csv()` | L299–L313 | `bom_to_csv()` |
| `MFG_THRESHOLDS` dict | L320 | Class constant |
| `run_mfg_checks()` | L329–L535 | `check_manufacturing()` |
| `auto_fix_short_arcs()` | L542–L553 | `auto_fix_short_arcs()` |
| `auto_fix_shallow_rings()` | L556–L566 | `auto_fix_shallow_rings()` |
| `_make_grid()` | L573–L589 | `_make_grid()` |
| `_build_alternating()` | L592–L597 | `_build_alternating()` |
| `RECIPES` | L600–L720 | Class constant or loaded from presets module |
| `_SVG_DEFS` | L727–L803 | Class constant |
| `render_preview_svg()` | L806–L895 | `render_preview_svg()` |
| `_build_annotations_svg()` | L898–L939 | `_build_annotations_svg()` |

**Route file to update:**

```
Path:   services/api/app/art_studio/api/rosette_designer_routes.py
Lines:  1–155 (155 total)
```

| Line | Current Import | Change To |
|---:|---|---|
| L34–L45 | 11 functions from `generators.rosette_designer` | Import from `services.rosette_engine` instead |

---

## I — Landing Spot (New File)

### I1. `rosette_engine.py` — THE unified engine

```
Path:   services/api/app/art_studio/services/rosette_engine.py
Lines:  NEW FILE
```

**Expected structure:**
```
L1–L30    imports (from cam.rosette.tile_segmentation, cnc, rosette_cnc_wiring, etc.)
L32–L50   class constants (TILE_FILL_MAP, TILE_COLOR_HEX, MFG_THRESHOLDS, SVG_DEFS)
L52–L80   class RosetteEngine:
L80–L200   ─── DESIGN methods (ported from rosette_designer.py)
L200–L280  ─── GEOMETRY methods (delegates to tile_segmentation.py)
L280–L400  ─── MANUFACTURING methods (delegates to cnc pipeline)
L400–L450  ─── PERSISTENCE methods (delegates to snapshot store)
L450–L500  ─── PRESET/RECIPE methods
```

**Expected size:** ~500–600 lines (absorbs 939 lines from generator + 68 from feasibility scorer, minus duplication and data constants)

---

## Dependency Order (Build Sequence)

```
Step 1: Delete Section A files (3)
        Update __init__.py re-exports (Section E1)
        Run: pytest — verify nothing breaks
            
Step 2: Absorb CNC micro-files (Section C, 5 files)
        Update cnc/__init__.py re-exports (Section E2)
        Run: pytest -m cam — verify CNC pipeline intact

Step 3: Absorb skeleton engines (Section B, 6 files)
        Add absorbed functions to tile_segmentation.py (Section G1)
        Update __init__.py + rmos/stub_routes.py (Sections E1, E3)
        Run: pytest — verify segmentation/slice/preview still work

Step 4: Create RosetteEngine (Section I)
        Port generator functions (Section H)
        Absorb feasibility scorer (Section D)
        Update routes to call engine (Section H route update)
        Run: pytest tests/test_rosette_designer.py — all 65 tests pass

Step 5: Merge frontend stores (Section F)
        Replace raw fetch with SDK in wheel store
        Update all component imports
        Run: npm run test
```

---

## Files Summary Tables

### Files to DELETE (14 total)

| # | Path | Lines | Phase |
|---:|---|---:|---|
| 1 | `cam/rosette/herringbone.py` | 24 | Step 1 |
| 2 | `cam/rosette/kerf_compensation.py` | 22 | Step 1 |
| 3 | `cam/rosette/saw_batch_generator.py` | 38 | Step 1 |
| 4 | `cam/rosette/segmentation_engine.py` | 48 | Step 3 |
| 5 | `cam/rosette/slice_engine.py` | 52 | Step 3 |
| 6 | `cam/rosette/kerf_engine.py` | 35 | Step 3 |
| 7 | `cam/rosette/twist_engine.py` | 55 | Step 3 |
| 8 | `cam/rosette/ring_engine.py` | 40 | Step 3 |
| 9 | `cam/rosette/preview_engine.py` | 52 | Step 3 |
| 10 | `cam/rosette/cnc/cnc_kerf_physics.py` | 42 | Step 2 |
| 11 | `cam/rosette/cnc/cnc_simulation.py` | 59 | Step 2 |
| 12 | `cam/rosette/cnc/cnc_feed_table.py` | 59 | Step 2 |
| 13 | `cam/rosette/cnc/cnc_blade_model.py` | 37 | Step 2 |
| 14 | `cam/rosette/cnc/cnc_jig_geometry.py` | 48 | Step 2 |

### Files to CREATE (1)

| # | Path | Est. Lines | Phase |
|---:|---|---:|---|
| 1 | `art_studio/services/rosette_engine.py` | 500–600 | Step 4 |

### Files to MODIFY (7)

| # | Path | Current Lines | Change Type | Phase |
|---:|---|---:|---|---|
| 1 | `cam/rosette/__init__.py` | 76 | Remove 9 imports + 6 `__all__` entries | Steps 1/3 |
| 2 | `cam/rosette/cnc/__init__.py` | 88 | Redirect 5 import sources | Step 2 |
| 3 | `rmos/stub_routes.py` | ~200 | Fix 3 import paths | Step 3 |
| 4 | `cam/rosette/tile_segmentation.py` | 303 → ~380 | Add 3 absorbed functions | Step 3 |
| 5 | `cnc/cnc_safety_validator.py` | 118 → ~150 | Add kerf physics | Step 2 |
| 6 | `cnc/cnc_exporter.py` | 57 → ~170 | Add jig + simulation | Step 2 |
| 7 | `cnc/cnc_materials.py` | 79 → ~180 | Add feed_table + blade | Step 2 |

### Frontend Files to DELETE (3) and CREATE (1)

| # | Path | Lines | Phase |
|---:|---|---:|---|
| DEL | `stores/rosetteStore.ts` | 836 | Step 5 |
| DEL | `stores/useRosetteDesignerStore.ts` | 246 | Step 5 |
| DEL | `stores/useRosetteWheelStore.ts` | 538 | Step 5 |
| NEW | `stores/useRosetteStore.ts` | ~600 est | Step 5 |

### Files to also DELETE after engine absorbs them (2)

| # | Path | Lines | Phase |
|---:|---|---:|---|
| 1 | `art_studio/services/generators/rosette_designer.py` | 939 | Step 4 |
| 2 | `art_studio/services/rosette_feasibility_scorer.py` | 68 | Step 4 |
