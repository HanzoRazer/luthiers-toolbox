# Phase 6: CAD Geometry Reconstruction — Developer Handoff

**Date:** 2026-04-15  
**Status:** Planning  
**Prerequisite:** layered_dual_pass promoted to production (complete)

---

## Executive Summary

Phase 6 implements **post-extraction geometry cleanup** to improve CAD usability of BODY layer output. The goal is to convert fragmented LINE entities into clean polylines, arcs, and radii-aware segments without changing the promoted extraction path.

**Key principle:** OutlineReconstructor becomes an optional repair module that runs AFTER layered_dual_pass isolates BODY, not as part of extraction.

---

## Current Production Pipeline (as of 2026-04-15)

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: hostinger/blueprint-reader.html                      │
│  Mode: layered_dual_pass (USE_LAYERED_DUAL_PASS = true)         │
│  Preset: geometry_only (BODY layer only)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/blueprint/vectorize/async                            │
│  Router: services/api/app/routers/blueprint_async_router.py     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  BlueprintOrchestrator.process_file()                           │
│  File: services/api/app/services/blueprint_orchestrator.py      │
│  Lines: 270-382 (dual-pass branch)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│  Pass A: Structural │       │  Pass B: Annotation │
│  extract_entities   │       │  extract_annotations│
│  _simple()          │       │  ()                 │
└─────────┬───────────┘       └─────────┬───────────┘
          │                             │
          └──────────┬──────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  build_layers()                                                 │
│  File: services/api/app/services/layer_builder.py               │
│  Output: LayeredEntities with BODY, AUX_VIEWS, ANNOTATION, etc. │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  join_body_gaps()                                               │
│  File: services/api/app/services/layer_builder.py               │
│  Conservative gap joining for BODY contours (max 4mm)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  write_layered_dxf()                                            │
│  File: services/api/app/services/layered_dxf_writer.py          │
│  Output: R12 DXF with LINE entities, named layers               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                  [DXF base64 in response]
```

---

## Phase 6 Insertion Point

Phase 6 adds a **geometry repair stage** between gap joining and DXF writing:

```
  join_body_gaps()
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  [PHASE 6] CAD Geometry Reconstruction                          │
│  File: services/api/app/services/body_geometry_repair.py (NEW)  │
│                                                                 │
│  Input:  LayeredEntities.body contours (already gap-joined)     │
│  Output: Repaired contours with:                                │
│          - Polyline consolidation                               │
│          - Arc fitting where curvature is consistent            │
│          - Radii-aware segments (using MEASURED_RADII)          │
│          - Optional: OutlineReconstructor for incomplete BODY   │
└────────────────────────┬────────────────────────────────────────┘
         │
         ▼
  write_layered_dxf()
```

---

## File Reference

### Core Pipeline Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| [blueprint_orchestrator.py](../services/api/app/services/blueprint_orchestrator.py) | Pipeline coordinator | `process_file()`, dual-pass branch lines 270-382 |
| [blueprint_async_router.py](../services/api/app/routers/blueprint_async_router.py) | HTTP endpoint | `vectorize_blueprint_async()` |
| [layer_builder.py](../services/api/app/services/layer_builder.py) | Layer classification + gap join | `build_layers()`, `join_body_gaps()` |
| [layered_dxf_writer.py](../services/api/app/services/layered_dxf_writer.py) | DXF output | `write_layered_dxf()` |
| [annotation_extract.py](../services/api/app/services/annotation_extract.py) | Pass B extraction | `extract_annotations()` |

### Available Geometry Technology

| File | Purpose | Key Functions |
|------|---------|---------------|
| [outline_reconstructor.py](../services/api/app/services/outline_reconstructor.py) | Arc-based gap bridging | `OutlineReconstructor.complete()` |
| [curvature_correction.py](../services/api/app/instrument_geometry/curvature_correction.py) | Instrument curvature data | `MEASURED_RADII`, `InstrumentCurvatureProfile` |
| [unified_dxf_cleaner.py](../services/api/app/cam/unified_dxf_cleaner.py) | Chain extraction/writing | `DXFCleaner`, `Chain`, `Point` |
| [dxf_writer.py](../services/api/app/cam/dxf_writer.py) | Central R12 writer | `DxfWriter` (standards enforcement) |

### Scoring & Selection

| File | Purpose | Key Functions |
|------|---------|---------------|
| [contour_scoring.py](../services/api/app/services/contour_scoring.py) | Multi-signal ranking | `score_contours()`, `ContourScore` |
| [contour_recommendation.py](../services/api/app/services/contour_recommendation.py) | Accept/review/reject | `recommend()`, `Recommendation` |

### Scripts & Testing

| File | Purpose | How to Run |
|------|---------|------------|
| [trace_live_path.py](../scripts/trace_live_path.py) | Verify production path | `python scripts/trace_live_path.py` |
| [run_frontend_mode_benchmark.py](../scripts/run_frontend_mode_benchmark.py) | Mode comparison | `python scripts/run_frontend_mode_benchmark.py` |
| [test_outline_reconstructor.py](../services/api/tests/test_outline_reconstructor.py) | Reconstructor tests | `pytest services/api/tests/test_outline_reconstructor.py` |

---

## Schema Reference

### LayeredEntities (Input to Phase 6)

```python
@dataclass
class LayeredEntities:
    body: List[LayeredEntity]           # Primary instrument outline
    aux_views: List[LayeredEntity]      # Secondary structural clusters
    annotation: List[LayeredEntity]     # Text, dimensions, labels
    title_block: List[LayeredEntity]    # Dense annotation cluster
    page_frame: List[LayeredEntity]     # Page border geometry
    
    image_size: Tuple[int, int]         # (width, height) in pixels
    mm_per_px: float                    # Scale factor
    
    def counts(self) -> Dict[str, int]
    def get_contours_for_preset(self, preset: ExportPreset) -> List[np.ndarray]
```

### LayeredEntity

```python
@dataclass
class LayeredEntity:
    contour: np.ndarray                 # Shape: (N, 1, 2) OpenCV format
    layer: Layer                        # BODY, AUX_VIEWS, etc.
    bbox: Tuple[int, int, int, int]     # (x, y, w, h)
    area: float                         # Contour area in pixels^2
    is_closed: bool = True
```

### Layer Enum

```python
class Layer(str, Enum):
    BODY = "BODY"                       # Primary instrument outline
    AUX_VIEWS = "AUX_VIEWS"             # Secondary views
    ANNOTATION = "ANNOTATION"           # Text, dimensions
    TITLE_BLOCK = "TITLE_BLOCK"         # Dense annotation cluster
    PAGE_FRAME = "PAGE_FRAME"           # Page border
```

### ExportPreset Enum

```python
class ExportPreset(str, Enum):
    GEOMETRY_ONLY = "geometry_only"     # BODY only (production default)
    GEOMETRY_PLUS_AUX = "geometry_plus_aux"  # BODY + AUX_VIEWS
    REFERENCE_FULL = "reference_full"   # All layers
```

### GapJoinResult

```python
@dataclass
class GapJoinResult:
    joins_attempted: int
    joins_applied: int
    max_gap_mm: float
    max_angle_deg: float
    joined_segments: List[Tuple[Point, Point]]  # For debug overlay
```

---

## Available Technology

### 1. OutlineReconstructor

**File:** `services/api/app/services/outline_reconstructor.py`

**What it does:**
- Detects gaps in open contours (1-8mm range)
- Classifies gap zone (upper_bout, waist, lower_bout, horn_tip, cutaway)
- Generates arc points using instrument-specific radii from `MEASURED_RADII`
- Bridges gap with geometrically correct arc

**Current state:** FROZEN (not in production path)

**Key classes:**
```python
class OutlineReconstructor:
    def __init__(self, spec_name: str, max_gap_mm: float = 8.0):
        self.radii = MEASURED_RADII.get(spec_name, {})
    
    def complete(self, chains: List[Chain]) -> ReconstructionResult:
        # Detects gaps, classifies zones, generates arcs
```

**Zone classification:**
```python
# Electric instruments
ELECTRIC_ZONE_BOUNDARIES = {
    GapZone.HORN_TIP: (0.00, 0.20),    # Top 20%
    GapZone.CUTAWAY: (0.20, 0.40),     # 20-40%
    GapZone.WAIST: (0.40, 0.60),       # 40-60%
    GapZone.LOWER_BOUT: (0.60, 1.00),  # Bottom 40%
}

# Acoustic instruments
ACOUSTIC_ZONE_BOUNDARIES = {
    GapZone.UPPER_BOUT: (0.00, 0.30),
    GapZone.WAIST: (0.30, 0.55),
    GapZone.LOWER_BOUT: (0.55, 1.00),
}
```

### 2. MEASURED_RADII

**File:** `services/api/app/instrument_geometry/curvature_correction.py`

**What it provides:**
Empirically measured curvature radii (in mm) by instrument and zone.

```python
MEASURED_RADII = {
    "stratocaster": {
        "waist": 180.0,
        "bout": 250.0,
        "horn_tip": 45.0,
        "cutaway": 80.0,
    },
    "dreadnought": {
        "waist": 140.0,
        "bout": 280.0,
        "default": 200.0,
    },
    "gibson_explorer": {
        "waist": 150.0,
        "bout": 100.0,
        "horn_tip": 25.0,  # Very sharp
    },
    "melody_maker": {
        "bout": 118.0,
        "waist": 36.0,
        "horn_tip": 5.7,
        "cutaway": 22.0,
    },
    # ... 10+ instruments
}
```

### 3. Chain/Point Primitives

**File:** `services/api/app/cam/unified_dxf_cleaner.py`

```python
@dataclass
class Point:
    x: float
    y: float
    
    def distance_to(self, other: Point) -> float
    def is_close(self, other: Point, tolerance: float = 0.1) -> bool

@dataclass
class Chain:
    points: List[Point]
    
    def is_closed(self, tolerance: float = 1.0) -> bool
    def length(self) -> float
    def as_polyline_points(self) -> List[Tuple[float, float]]
```

### 4. DxfWriter (R12 Standards)

**File:** `services/api/app/cam/dxf_writer.py`

Enforces project-wide DXF standards:
- Format: R12 (AC1009)
- Entities: LINE only (no LWPOLYLINE)
- Coordinates: 3 decimal places
- Layers: Named only, no geometry on layer 0

```python
class DxfWriter:
    def add_line(self, start, end, layer: str)
    def add_polyline(self, points, layer: str, closed: bool = False)
    def add_arc(self, center, radius, start_angle, end_angle, layer: str)
    def add_circle(self, center, radius, layer: str)
```

---

## OutlineReconstructor Integration Plan

### Current State (FROZEN)

```python
# outline_reconstructor.py line 426
def complete_outline_if_needed(chains, spec_name=None, max_gap_mm=8.0):
    enabled = os.environ.get("ENABLE_OUTLINE_RECONSTRUCTION", "0") == "1"
    if not enabled or not spec_name:
        return chains, None
    # ... reconstruction logic
```

**Problem:** Currently designed for Chain input from blueprint_clean.py, not LayeredEntities from layer_builder.py.

### Proposed Integration (Phase 6)

```python
# NEW: services/api/app/services/body_geometry_repair.py

def repair_body_geometry(
    layered: LayeredEntities,
    spec_name: Optional[str] = None,
    enable_reconstruction: bool = False,
) -> Tuple[LayeredEntities, Optional[RepairResult]]:
    """
    Post-gap-join geometry repair for BODY layer.
    
    Runs AFTER join_body_gaps() and BEFORE write_layered_dxf().
    
    Steps:
    1. Extract BODY contours from LayeredEntities
    2. Check if BODY is incomplete (open contours remain)
    3. If incomplete AND enable_reconstruction:
       - Convert contours to Chains
       - Run OutlineReconstructor
       - Compare result (keep only if better)
    4. Return modified LayeredEntities
    """
    if not enable_reconstruction or not spec_name:
        return layered, None
    
    # Check if BODY has open contours
    body_open = [e for e in layered.body if not e.is_closed]
    if not body_open:
        return layered, None  # Already complete
    
    # Convert to Chains for reconstructor
    chains = [contour_to_chain(e.contour, layered.mm_per_px) 
              for e in layered.body]
    
    # Run reconstruction
    reconstructor = OutlineReconstructor(spec_name)
    result = reconstructor.complete(chains)
    
    # Compare: keep only if better
    if result.gaps_bridged > 0:
        # Convert back to LayeredEntities
        repaired_body = [chain_to_layered_entity(c) for c in result.chains]
        layered.body = repaired_body
        return layered, RepairResult(
            open_before=len(body_open),
            gaps_bridged=result.gaps_bridged,
            applied=True,
        )
    
    return layered, RepairResult(applied=False)
```

### Orchestrator Integration

```python
# blueprint_orchestrator.py, after join_body_gaps()

# Existing
gap_result = join_body_gaps(layered, max_gap_mm=4.0)

# NEW: Phase 6 geometry repair
if spec_name and os.environ.get("ENABLE_BODY_REPAIR", "0") == "1":
    layered, repair_result = repair_body_geometry(
        layered,
        spec_name=spec_name,
        enable_reconstruction=True,
    )
    if repair_result and repair_result.applied:
        stage_timings["body_repair"] = repair_result.to_dict()

# Existing
counts = write_layered_dxf(layered, dxf_path, export_preset)
```

---

## Phase 6 Scope

### In Scope

1. **Polyline consolidation** — Merge consecutive LINE entities into clean polylines
2. **Arc fitting** — Detect consistent curvature and fit arcs where appropriate
3. **Radii-aware segments** — Use MEASURED_RADII to inform arc generation
4. **Optional reconstruction** — Apply OutlineReconstructor to incomplete BODY
5. **Compare-and-keep** — Only apply reconstruction if it improves the result

### Out of Scope

1. **Extraction changes** — Do not modify layered_dual_pass extraction
2. **Spline fitting** — Defer to future phase (adds complexity, limited CAD benefit)
3. **Non-BODY layers** — Focus on BODY/BODY_SUPPORT only
4. **Mode changes** — Keep geometry_only as default preset

### Success Criteria

1. Open contour count in BODY layer decreases or stays same
2. Entity count stays stable (no fragmentation)
3. CAD import (Fusion 360) succeeds without freeze
4. Manual inspection shows visually smooth curves

---

## Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `ENABLE_BODY_REPAIR` | `0` | Master switch for Phase 6 |
| `ENABLE_OUTLINE_RECONSTRUCTION` | `0` | Arc bridging within repair |
| `BODY_REPAIR_COMPARE_MODE` | `1` | Compare before/after, keep better |

---

## Test Plan

### Unit Tests

```bash
# Existing reconstructor tests
pytest services/api/tests/test_outline_reconstructor.py

# Existing curvature tests
pytest services/api/tests/test_body_curvature_correction.py

# NEW: Phase 6 repair tests
pytest services/api/tests/test_body_geometry_repair.py
```

### Integration Tests

```bash
# Verify production path unchanged when flags off
python scripts/trace_live_path.py

# Benchmark with repair enabled
ENABLE_BODY_REPAIR=1 python scripts/run_frontend_mode_benchmark.py
```

### Manual Validation

1. Run vectorization on benchmark files (L0, Flying V, Strat 62)
2. Download DXF
3. Import into Fusion 360
4. Verify no freeze, clean curves, correct dimensions

---

## Rollback

If Phase 6 causes regressions:

1. Set `ENABLE_BODY_REPAIR=0` (immediate)
2. No code changes required — repair is additive
3. Production continues on gap-join output

---

## Dependencies

### Required Before Implementation

- [x] layered_dual_pass promoted to production
- [x] OutlineReconstructor module exists
- [x] MEASURED_RADII data populated for benchmark instruments
- [ ] `body_geometry_repair.py` created (Phase 6 work)

### External Dependencies

- ezdxf library (already installed)
- OpenCV (already installed)
- numpy (already installed)

---

## Appendix: Debug Payloads

### execution_path (in debug response)

```json
{
  "execution_path": {
    "mode": "layered_dual_pass",
    "pipeline": "orchestrator_dual_pass",
    "writer": "write_layered_dxf",
    "pass_b_annotation_extraction": true,
    "export_preset": "geometry_only",
    "annotations_in_output": false,
    "body_repair_applied": false  // NEW in Phase 6
  }
}
```

### gap_join (in debug response)

```json
{
  "gap_join": {
    "joins_attempted": 5,
    "joins_applied": 3,
    "max_gap_mm": 4.0,
    "max_angle_deg": 25.0
  }
}
```

### body_repair (NEW in Phase 6)

```json
{
  "body_repair": {
    "open_before": 2,
    "open_after": 0,
    "gaps_bridged": 2,
    "spec_name": "dreadnought",
    "applied": true,
    "compare_kept_original": false
  }
}
```

---

## Summary

Phase 6 is a **post-processing enhancement** that:

1. Runs AFTER the proven layered_dual_pass + gap_join pipeline
2. Operates only on BODY layer contours
3. Uses existing OutlineReconstructor with MEASURED_RADII
4. Is gated by feature flags for safe rollout
5. Compares before/after and keeps only if better

The extraction path remains unchanged. This is additive geometry cleanup, not a pipeline change.

---

## Appendix B: Instrument Body Dimension Reference

### Data Source Discovery

The repository contains a comprehensive body dimension reference at:

**Primary:** `services/photo-vectorizer/body_dimension_reference.json`

This JSON file contains empirically measured landmark dimensions for 17 instruments, designed for spec-prior contour election in the photo vectorizer pipeline.

---

### Schema Definition

```json
{
  "_comment": "Body landmark reference data for spec-prior contour election",
  "_fields": {
    "body_length_mm": "Total body length heel to tail",
    "upper_bout_width_mm": "Maximum width in upper third of body",
    "waist_width_mm": "Minimum width at body waist",
    "lower_bout_width_mm": "Maximum width in lower half of body",
    "waist_y_norm": "Waist position as fraction of body length from top (0.0-1.0)",
    "family": "Instrument family for family-hint matching"
  }
}
```

---

### Complete Instrument Inventory

| Instrument | Length | Upper Bout | Waist | Lower Bout | Waist Y | Family |
|------------|--------|------------|-------|------------|---------|--------|
| stratocaster | 406 | 311 | 308 | 408 | 0.47 | solid_body |
| telecaster | 406 | 311 | 310 | 398 | 0.46 | solid_body |
| les_paul | 450 | 283 | 266 | 340 | 0.44 | solid_body |
| es335 | 500 | 375 | 295 | 420 | 0.43 | archtop |
| dreadnought | 520 | 292 | 241 | 381 | 0.43 | acoustic |
| om_000 | 476 | 274 | 228 | 341 | 0.44 | acoustic |
| jumbo | 521 | 320 | 272 | 419 | 0.43 | acoustic |
| classical | 481 | 280 | 225 | 365 | 0.45 | acoustic |
| j45 | 506 | 295 | 248 | 394 | 0.44 | acoustic |
| flying_v | 450 | 380 | 200 | 410 | 0.52 | solid_body |
| gibson_sg | 444 | 330 | 180 | 330 | 0.35 | solid_body |
| gibson_explorer | 460 | 410 | 200 | 475 | 0.50 | solid_body |
| cuatro | 375 | 180 | 155 | 260 | 0.44 | acoustic |
| melody_maker | 440 | 280 | 260 | 330 | 0.45 | solid_body |
| benedetto_17 | 482.6 | 279.4 | 228.6 | 431.8 | 0.42 | archtop |
| smart_guitar | 444.5 | 310 | 307 | 368.3 | 0.46 | solid_body |
| bass_4string | 430 | 310 | 280 | 370 | 0.45 | bass |
| jumbo_archtop | 520 | 340 | 248 | 432 | 0.42 | archtop |

*All dimensions in millimeters*

---

### Data Flow: Pipelines That Consume This Data

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     body_dimension_reference.json                            │
│                  services/photo-vectorizer/                                  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│ PYTHON DATACLASS  │  │ PHOTO VECTORIZER   │  │ GEOMETRY AUTHORITY │
│ instrument_specs  │  │ AI Spec Loader     │  │ Family Priors      │
│ .py               │  │                    │  │                    │
└─────────┬─────────┘  └─────────┬──────────┘  └─────────┬──────────┘
          │                      │                       │
          │                      │                       │
          ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOWNSTREAM CONSUMERS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │ scale_validation.py │  │ landmark_extractor  │  │ contour_stage.py    │ │
│  │                     │  │ .py                 │  │                     │ │
│  │ validate_scale_     │  │ extract_landmarks_  │  │ _score_body_fit()   │ │
│  │ before_export()     │  │ from_profile()      │  │                     │ │
│  │                     │  │                     │  │                     │ │
│  │ Uses: body_length,  │  │ Uses: waist_y_norm  │  │ Uses: all fields    │ │
│  │ lower_bout_width    │  │ for zone boundaries │  │ for contour ranking │ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘ │
│             │                        │                        │             │
│             ▼                        ▼                        ▼             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      BLUEPRINT ORCHESTRATOR                              ││
│  │              (potential Phase 6 integration point)                       ││
│  │                                                                          ││
│  │  - validate_body_scale() → block export if 2.5× off                     ││
│  │  - get_waist_y_position() → inform gap zone classification              ││
│  │  - check_completeness() → decide if reconstruction needed               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### File Reference: All Consumers

#### 1. instrument_specs.py (Python Dataclass Mirror)

**Path:** `services/api/app/instrument_geometry/instrument_specs.py`

**Purpose:** Single source of truth for backend services (mirrors JSON data as frozen dataclasses)

```python
@dataclass(frozen=True)
class BodyDimensions:
    body_length_mm: float
    upper_bout_width_mm: float
    waist_width_mm: float
    lower_bout_width_mm: float
    waist_y_norm: float = 0.45
    family: str = "unknown"

BODY_DIMENSIONS: Dict[str, BodyDimensions] = {
    "stratocaster": BodyDimensions(body_length_mm=406, ...),
    # ... 17 instruments
}

def get_body_dimensions(spec_name: str) -> Optional[BodyDimensions]:
    """Lookup with case-insensitive matching."""
```

**Consumers:**
- `scale_validation.py` → `get_body_dimensions()`
- `curvature_correction.py` → zone threshold lookup
- `blueprint_orchestrator.py` → spec validation

---

#### 2. scale_validation.py (Pre-Export Gate)

**Path:** `services/api/app/services/scale_validation.py`

**Purpose:** Blocks DXF export when extracted dimensions are implausible

```python
def validate_scale_before_export(
    width_mm: float,
    height_mm: float,
    spec_name: Optional[str] = None,
) -> Optional[str]:
    """
    Returns None if valid, error message if blocked.
    
    Uses ±20% tolerance around spec dimensions.
    Falls back to generic bounds (150-700mm × 200-900mm) if no spec.
    """

def compute_scale_correction(
    width_mm: float,
    height_mm: float,
    spec_name: Optional[str] = None,
) -> Tuple[float, str]:
    """Returns (correction_factor, reason)."""
```

**Data used:** `body_length_mm`, `lower_bout_width_mm`

**Integration:** Called before `write_layered_dxf()` in orchestrator

---

#### 3. photo_vectorizer_v2.py (AI Path Spec Loader)

**Path:** `services/photo-vectorizer/photo_vectorizer_v2.py`

**Purpose:** Loads body_dimension_reference.json for AI-generated image vectorization

```python
def _load_ai_specs() -> Dict[str, Dict[str, Any]]:
    """
    Load body_dimension_reference.json and convert to AI path format.
    Returns dict mapping spec_name -> {"body": (length_mm, width_mm), ...}
    """
    
def get_ai_spec(spec_name: str) -> Optional[Dict[str, Any]]:
    """Get spec for AI path, with case-insensitive lookup."""
```

**Data used:** All fields, converted to internal format

---

#### 4. geometry_authority.py (Family Priors)

**Path:** `services/photo-vectorizer/geometry_authority.py`

**Purpose:** Provides family-level dimension bounds for coachable vectorization

```python
_FAMILY_BODY_PRIORS_MM = {
    "solid_body": (350.0, 520.0, 280.0, 430.0),  # (h_min, h_max, w_min, w_max)
    "archtop":    (430.0, 600.0, 330.0, 460.0),
    "acoustic":   (430.0, 600.0, 330.0, 520.0),
    "bass":       (420.0, 650.0, 280.0, 420.0),
    "ukulele":    (180.0, 380.0, 120.0, 260.0),
}

class GeometryAuthority:
    def get_expected_body_profile(self, family) -> Tuple[h_min, h_max, w_min, w_max]
    def score_dimension_fit(self, family, height_mm, width_mm) -> Dict[str, float]
    def get_retry_policy(self, issue_type, family) -> RetryPolicy
```

**Data used:** Aggregated from `family` field

---

#### 5. landmark_extractor.py (Body Landmark Detection)

**Path:** `services/photo-vectorizer/landmark_extractor.py`

**Purpose:** Extracts waist/bout positions from row-width profile

```python
def extract_landmarks_from_profile(model: BodyModel) -> BodyModel:
    """
    Extract five primary body landmarks from smoothed W(y) profile.
    
    Uses zone boundaries:
      - Upper third (0%-35%): argmax → upper bout
      - Middle third (30%-70%): argmin → waist  
      - Lower half (50%-100%): argmax → lower bout
    """
```

**Data used:** `waist_y_norm` to validate detected waist position

---

#### 6. contour_stage.py (Body Contour Scoring)

**Path:** `services/photo-vectorizer/contour_stage.py`

**Purpose:** Scores contour candidates against spec dimensions

```python
def _score_body_fit(
    contour: np.ndarray,
    spec_name: str,
    mm_per_px: float,
) -> float:
    """
    Score how well contour dimensions match spec.
    Returns 0.0-1.0 fit score.
    """
```

**Data used:** All dimension fields for contour ranking

---

### Phase 6 Integration: Proposed Functions

#### 1. validate_body_scale() — Scale Gate

```python
# services/api/app/services/body_geometry_repair.py

from ..instrument_geometry.instrument_specs import get_body_dimensions

def validate_body_scale(
    body_contours: List[LayeredEntity],
    mm_per_px: float,
    spec_name: Optional[str] = None,
) -> Tuple[bool, Optional[str], float]:
    """
    Validate extracted BODY dimensions against spec.
    
    Args:
        body_contours: BODY layer entities from LayeredEntities
        mm_per_px: Scale factor
        spec_name: Instrument spec name
        
    Returns:
        (is_valid, error_message, correction_factor)
    """
    if not spec_name or not body_contours:
        return True, None, 1.0
    
    spec = get_body_dimensions(spec_name)
    if not spec:
        return True, None, 1.0
    
    # Compute BODY bounding box in mm
    all_points = np.vstack([e.contour.reshape(-1, 2) for e in body_contours])
    x_min, y_min = all_points.min(axis=0) * mm_per_px
    x_max, y_max = all_points.max(axis=0) * mm_per_px
    
    width_mm = x_max - x_min
    height_mm = y_max - y_min
    
    # Compare against spec
    expected_width = spec.lower_bout_width_mm
    expected_height = spec.body_length_mm
    
    width_ratio = width_mm / expected_width
    height_ratio = height_mm / expected_height
    
    # ±20% tolerance
    if 0.8 < width_ratio < 1.2 and 0.8 < height_ratio < 1.2:
        return True, None, 1.0
    
    correction = (expected_width / width_mm + expected_height / height_mm) / 2
    error = f"BODY {width_mm:.0f}×{height_mm:.0f}mm vs spec {expected_width:.0f}×{expected_height:.0f}mm"
    
    return False, error, correction
```

#### 2. get_waist_y_position() — Zone Classification Aid

```python
def get_waist_y_position(spec_name: str) -> float:
    """
    Get normalized waist Y position for gap zone classification.
    
    Returns waist_y_norm (0.0-1.0) or default 0.45 if spec not found.
    Used by OutlineReconstructor to improve zone accuracy.
    """
    spec = get_body_dimensions(spec_name)
    return spec.waist_y_norm if spec else 0.45
```

#### 3. check_body_completeness() — Reconstruction Trigger

```python
def check_body_completeness(
    body_contours: List[LayeredEntity],
    mm_per_px: float,
    spec_name: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Check if BODY layer represents a complete instrument outline.
    
    Heuristics:
    1. At least one contour spans >80% of expected width at waist position
    2. Total BODY area > 60% of expected body area
    3. No large gaps in the perimeter
    
    Returns:
        (is_complete, issues_list)
    """
    issues = []
    
    if not body_contours:
        return False, ["no_body_contours"]
    
    spec = get_body_dimensions(spec_name) if spec_name else None
    
    # Check 1: Width coverage at waist
    waist_y_norm = spec.waist_y_norm if spec else 0.45
    # ... sample contour at waist position ...
    
    # Check 2: Area coverage
    if spec:
        expected_area = spec.body_length_mm * spec.lower_bout_width_mm * 0.7  # ~70% fill
        actual_area = sum(e.area * mm_per_px * mm_per_px for e in body_contours)
        if actual_area < expected_area * 0.6:
            issues.append("area_below_60pct")
    
    # Check 3: Open contours
    open_count = sum(1 for e in body_contours if not e.is_closed)
    if open_count > 0:
        issues.append(f"open_contours_{open_count}")
    
    return len(issues) == 0, issues
```

---

### Viability Assessment for Phase 6

| Use Case | Data Fields Used | Viability | Priority |
|----------|------------------|-----------|----------|
| **Scale validation gate** | body_length_mm, lower_bout_width_mm | HIGH | P0 |
| **Completeness heuristic** | all dimensions | MEDIUM | P1 |
| **Waist zone detection** | waist_y_norm | HIGH | P0 |
| **Family-based defaults** | family | MEDIUM | P2 |
| **Arc radius selection** | (uses MEASURED_RADII instead) | N/A | - |

**Recommendation:** The body_dimension_reference.json data is immediately usable for:

1. **Scale validation** — Already implemented in `scale_validation.py`, just needs wiring into orchestrator
2. **Zone classification** — `waist_y_norm` can improve OutlineReconstructor accuracy
3. **Completeness check** — New function for deciding whether reconstruction is needed

The data complements `MEASURED_RADII` (curvature) — dimensions for validation, radii for arc generation.

---

### Related Data Sources

| File | Content | Relationship |
|------|---------|--------------|
| `body_outlines.json` | High-res point arrays (400-700 pts/instrument) | Ground truth geometry for template matching |
| `instrument_model_registry.json` | Full instrument metadata with CAM capabilities | Registry for UI/asset lookup |
| `MEASURED_RADII` (curvature_correction.py) | Zone-specific curvature radii | Arc generation in OutlineReconstructor |

These three data sources together provide complete instrument geometry knowledge for any vectorization or reconstruction task.
