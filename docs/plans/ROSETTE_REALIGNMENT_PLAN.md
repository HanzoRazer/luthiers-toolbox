# Luthier's Toolbox Architecture Realignment Plan

**Date:** 2026-01-30
**Status:** Draft
**Scope:** Unify demo architecture with proper naming and hierarchy

---

## Target Navigation Structure

```
Luthier's Toolbox
├── Home
├── Blueprint Reader        [Import & Vectorize | DXF Viewer]
├── Art Studio              [Rosette Builder | Headstock Art | Inlay Designer]
├── Guitar Designer         [Body Designer | Fret Calculator | Body Shape Library]
├── CNC Studio              [Saw Lab | Toolpaths | G-code Export]
└── Calculator Suite        [Basic | Scientific | Fraction | Financial | Luthier]
```

### Naming Decisions

| Old Name | New Name | Rationale |
|----------|----------|-----------|
| (unnamed CAM) | **CNC Studio** | Encompasses Saw Lab, toolpaths, G-code |
| Body templates | **Body Shape Library** | Under Guitar Designer, templates + AI |
| Rosette/Headstock separate | **Art Studio tabs** | Already consolidated |

---

## Rosette System Realignment

---

## Current State Analysis

### File Inventory

| File | Purpose | Status | Lines |
|------|---------|--------|-------|
| `calculators/rosette_calc.py` | Channel dimensions façade | Complete but limited | 260 |
| `pipelines/rosette/rosette_calc.py` | Legacy channel calc | Complete | 48 |
| `pipelines/rosette/rosette_to_dxf.py` | DXF circle export | Complete | ~100 |
| `cam/rosette/pattern_generator.py` | **REAL** matrix formulas | Complete | 1500+ |
| `cam/rosette/traditional_builder.py` | Craftsman interface | Complete | 400+ |
| `cam/rosette/pattern_renderer.py` | Visual rendering | Complete | ~300 |
| `cam/rosette/tile_segmentation.py` | Tile geometry | **STUB** | 40 |
| `cam/rosette/ring_engine.py` | Ring orchestration | **SKELETON** | 42 |
| `cam/rosette/slice_engine.py` | Slice generation | Partial | ~100 |
| `cam/rosette/kerf_engine.py` | Kerf compensation | Partial | ~80 |
| `art_studio/rosette_router.py` | REST API | Routes to façade | ~200 |

### Architecture Diagram (Current)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURRENT ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Streamlit Demo ──────► pattern_generator.py (DIRECT - works)           │
│                              │                                          │
│                              ▼                                          │
│                    PRESET_MATRICES (Torres, Hauser, etc.)               │
│                              │                                          │
│                              ▼                                          │
│                    TraditionalPatternGenerator                          │
│                              │                                          │
│                              ▼                                          │
│                    TraditionalPatternResult                             │
│                         (BOM, assembly, cut lists)                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Art Studio Router ──► rosette_calc.py (FAÇADE)                         │
│         │                    │                                          │
│         │                    ▼                                          │
│         │          pipelines/rosette_calc.py (LEGACY)                   │
│         │                    │                                          │
│         │                    ▼                                          │
│         │          Channel dimensions ONLY                              │
│         │          (no tile geometry!)                                  │
│         │                                                               │
│         └──────────► rosette_to_dxf.py                                  │
│                            │                                            │
│                            ▼                                            │
│                    Concentric circles (no pattern!)                     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ORPHANED (not wired):                                                  │
│     - tile_segmentation.py (STUB)                                       │
│     - ring_engine.py (SKELETON)                                         │
│     - slice_engine.py                                                   │
│     - kerf_engine.py                                                    │
│     - traditional_builder.py (has CutList, Sticks, but not in API)      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Problems Identified

1. **Two Parallel Systems**: `pattern_generator.py` has the real math, but `rosette_calc.py` façade doesn't use it
2. **Façade Too Limited**: Only calculates channel dimensions, not tile patterns
3. **Stubs Not Implemented**: `tile_segmentation.py` and `ring_engine.py` are placeholders
4. **DXF Export Incomplete**: `rosette_to_dxf.py` only exports circles, not actual pattern geometry
5. **Art Studio Router Bypasses Pattern Generator**: Uses façade → legacy → channels only
6. **Streamlit Works By Accident**: Directly imports `pattern_generator.py`, bypassing the broken façade

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TARGET ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  Streamlit  │    │  Vue Client │    │    RMOS     │                 │
│  │    Demo     │    │ (Art Studio)│    │   System    │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            ▼                                            │
│              ┌─────────────────────────────┐                            │
│              │   /art-studio/rosette/*     │                            │
│              │      (REST API Router)      │                            │
│              └──────────────┬──────────────┘                            │
│                             ▼                                           │
│              ┌─────────────────────────────┐                            │
│              │   calculators/rosette_calc  │                            │
│              │   (UNIFIED FAÇADE)          │                            │
│              │                             │                            │
│              │   - calculate_channel()     │  ◄── Channel dimensions    │
│              │   - calculate_pattern()     │  ◄── NEW: Full pattern     │
│              │   - get_preset_pattern()    │  ◄── NEW: Matrix presets   │
│              │   - generate_cut_list()     │  ◄── NEW: BOM/cuts         │
│              │   - export_pattern_dxf()    │  ◄── NEW: Pattern DXF      │
│              └──────────────┬──────────────┘                            │
│                             │                                           │
│         ┌───────────────────┼───────────────────┐                       │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Channel   │    │   Pattern   │    │ Traditional │                 │
│  │    Math     │    │  Generator  │    │   Builder   │                 │
│  │  (legacy)   │    │  (matrix)   │    │ (craftsman) │                 │
│  └─────────────┘    └──────┬──────┘    └─────────────┘                 │
│                            │                                            │
│                            ▼                                            │
│              ┌─────────────────────────────┐                            │
│              │      Ring Engine            │                            │
│              │   (orchestrates per-ring)   │                            │
│              └──────────────┬──────────────┘                            │
│                             │                                           │
│         ┌───────────────────┼───────────────────┐                       │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │    Tile     │    │    Slice    │    │    Kerf     │                 │
│  │ Segmentation│    │   Engine    │    │   Engine    │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Expand the Façade (No Breaking Changes)

**Goal:** Add pattern generation to `rosette_calc.py` without breaking existing channel calculation.

**File:** `services/api/app/calculators/rosette_calc.py`

```python
# ADD these imports
from ..cam.rosette.pattern_generator import (
    MatrixFormula,
    TraditionalPatternGenerator,
    TraditionalPatternResult,
    PRESET_MATRICES,
    RosettePatternEngine,
)
from ..cam.rosette.traditional_builder import (
    TraditionalProject,
    CutList,
)

# ADD new functions (keep existing calculate_rosette_channel)

def get_pattern_presets() -> Dict[str, str]:
    """List available matrix presets with descriptions."""
    return {
        name: formula.notes or formula.name
        for name, formula in PRESET_MATRICES.items()
    }

def calculate_pattern(
    preset_name: str = None,
    custom_matrix: MatrixFormula = None,
    ring_inner_radius_mm: float = 45.0,
    ring_outer_radius_mm: float = 55.0,
) -> TraditionalPatternResult:
    """
    Calculate full rosette pattern from matrix formula.

    Either provide preset_name OR custom_matrix.
    """
    generator = TraditionalPatternGenerator()

    if preset_name:
        matrix = PRESET_MATRICES.get(preset_name)
        if not matrix:
            raise ValueError(f"Unknown preset: {preset_name}")
    elif custom_matrix:
        matrix = custom_matrix
    else:
        raise ValueError("Must provide preset_name or custom_matrix")

    return generator.generate_pattern(
        matrix=matrix,
        ring_inner_radius_mm=ring_inner_radius_mm,
        ring_outer_radius_mm=ring_outer_radius_mm,
    )

def generate_pattern_dxf(
    result: TraditionalPatternResult,
    include_tiles: bool = True,
) -> str:
    """Generate DXF with actual tile geometry, not just circles."""
    # Implementation pulls from pattern_generator's DXF export
    ...
```

### Phase 2: Complete the Stubs

**Goal:** Implement real tile segmentation math in the skeleton files.

| File | Current | Action |
|------|---------|--------|
| `tile_segmentation.py` | 8 fixed tiles | Calculate tiles from ring geometry |
| `ring_engine.py` | No-op passes | Wire to real kerf/twist engines |
| `slice_engine.py` | Basic | Add proper slice positioning |

**Key Math Needed:**
```python
def compute_tile_count(ring_radius_mm: float, tile_length_mm: float) -> int:
    """Calculate how many tiles fit around the ring circumference."""
    circumference = 2 * math.pi * ring_radius_mm
    return max(1, round(circumference / tile_length_mm))

def compute_tile_geometry(
    ring_inner_r: float,
    ring_outer_r: float,
    tile_index: int,
    tile_count: int,
) -> TileGeometry:
    """Calculate exact polygon for one tile."""
    theta_start = (tile_index / tile_count) * 2 * math.pi
    theta_end = ((tile_index + 1) / tile_count) * 2 * math.pi

    # Four corners of the tile (trapezoid in polar coordinates)
    return TileGeometry(
        inner_start=(ring_inner_r * cos(theta_start), ring_inner_r * sin(theta_start)),
        inner_end=(ring_inner_r * cos(theta_end), ring_inner_r * sin(theta_end)),
        outer_start=(ring_outer_r * cos(theta_start), ring_outer_r * sin(theta_start)),
        outer_end=(ring_outer_r * cos(theta_end), ring_outer_r * sin(theta_end)),
    )
```

### Phase 3: Update Art Studio Router

**Goal:** Expose pattern generation through REST API.

**File:** `services/api/app/art_studio/rosette_router.py`

Add endpoints:
- `GET /art-studio/rosette/patterns` - List preset patterns
- `GET /art-studio/rosette/patterns/{name}` - Get preset details
- `POST /art-studio/rosette/pattern/preview` - Generate pattern with SVG
- `POST /art-studio/rosette/pattern/export-dxf` - Export pattern to DXF

### Phase 4: Update Streamlit Demo

**Goal:** Use the unified façade instead of direct imports.

**File:** `streamlit_demo/app.py`

Change from:
```python
from app.cam.rosette.pattern_generator import PRESET_MATRICES, TraditionalPatternGenerator
```

To:
```python
from app.calculators.rosette_calc import (
    get_pattern_presets,
    calculate_pattern,
    generate_pattern_dxf,
)
```

---

## Files to Modify

| File | Action | Priority |
|------|--------|----------|
| `calculators/rosette_calc.py` | Expand façade | P1 |
| `cam/rosette/tile_segmentation.py` | Implement real math | P2 |
| `cam/rosette/ring_engine.py` | Wire to engines | P2 |
| `art_studio/rosette_router.py` | Add pattern endpoints | P3 |
| `streamlit_demo/app.py` | Use façade | P4 |

---

## Success Criteria

1. **Single Entry Point:** All rosette functionality accessible through `rosette_calc.py` façade
2. **Pattern Generation:** Can generate Torres, Hauser, etc. patterns via API
3. **Real Tile Geometry:** DXF export includes actual tile polygons, not just circles
4. **BOM/Cut Lists:** API returns material requirements and cutting instructions
5. **Backward Compatible:** Existing channel calculation unchanged
6. **Demo Aligned:** Streamlit uses same code path as Vue client

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing channel calc | Keep `calculate_rosette_channel()` unchanged |
| Pattern generator complexity | Façade wraps, doesn't rewrite |
| Missing tile math | Stub files already have interfaces defined |
| Router changes | Add new endpoints, don't modify existing |

---

## Estimated Effort

| Phase | Hours | Dependencies |
|-------|-------|--------------|
| Phase 1: Expand Façade | 4h | None |
| Phase 2: Complete Stubs | 8h | Phase 1 |
| Phase 3: Router Updates | 4h | Phase 1 |
| Phase 4: Demo Alignment | 2h | Phase 1 |
| **Total** | **18h** | |

---

## Decision Required

Before proceeding:
1. Should the façade also wrap CAM/G-code generation, or keep that separate?
2. Should `traditional_builder.py` craftsman interface be exposed in API, or just the generator?
3. Priority: Pattern DXF export vs. completing tile segmentation math?
