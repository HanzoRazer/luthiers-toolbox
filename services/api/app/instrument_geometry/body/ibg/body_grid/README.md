# Body Grid — Semantic Morphology System

**Location:** `services/api/app/instrument_geometry/body/ibg/body_grid/`  
**Sprint:** IBG Body Grid Semantic Encoding  
**Status:** Implementation Complete  
**Date:** 2026-05-15

---

## Purpose

The Body Grid is a semantic morphology system that allows IBG to reason about musical instrument body variants through a stable deterministic coordinate system.

It separates **invariants** (what all guitar bodies share) from **variant expressions** (how different body shapes behave).

The system does NOT memorize silhouettes — it learns body behavior inside a semantic coordinate frame.

---

## Coordinate System

```
Centerline-relative normalized coordinates:

y_norm = 0.0 at butt/tail end
y_norm = 1.0 at neck end

x_norm = signed distance from centerline
x_norm < 0 = bass/left side
x_norm > 0 = treble/right side
```

Raw pixel/mm coordinates are preserved for traceability.

---

## Module Structure

```
body_grid/
├── __init__.py              # Public API exports
├── body_grid_schema.py      # Core data structures
├── zones.py                 # Zone definitions (15 zones)
├── primitives.py            # Morphology primitive classes
├── variant_grammar.py       # Variant classification grammar
├── grid_normalizer.py       # Coordinate normalization
├── morphology_descriptor.py # Main output container
├── overlay_exporter.py      # PNG overlay generation
└── README.md                # This file
```

---

## Usage

### Basic Analysis

```python
from app.instrument_geometry.body.ibg.body_grid import (
    MorphologyAnalyzer,
    BodyEvidence,
    export_overlay,
)

# Create evidence from outline points
evidence = BodyEvidence(
    outline_points=[(x1, y1), (x2, y2), ...],
)

# Analyze
analyzer = MorphologyAnalyzer()
descriptor = analyzer.analyze(evidence)

# Get classification
print(descriptor.variant_match.morphology_class)  # e.g., ROUNDED_SINGLE_CUT
print(descriptor.variant_match.horn_behavior)     # e.g., SINGLE_CUT_TREBLE
print(descriptor.asymmetry.asymmetry_score)       # 0.0 to 1.0

# Export human review overlay
export_overlay(descriptor, "body_grid_review.png")
```

### From constraint_extractor Landmarks

```python
from app.instrument_geometry.body.ibg.body_grid import analyze_from_dxf_landmarks

landmarks = [
    ("lower_bout_max", 190.5, 130.0),
    ("waist_min", 120.5, 230.0),
    ("upper_bout_max", 146.0, 340.0),
]

descriptor = analyze_from_dxf_landmarks(landmarks)
```

---

## Zone Definitions

| Zone | Y Range | Semantic Role |
|------|---------|---------------|
| butt_end | 0.00-0.08 | Tail termination |
| lower_bout | 0.08-0.40 | Maximum width, primary resonance |
| waist | 0.35-0.55 | Minimum width, ergonomic |
| upper_bout | 0.50-0.75 | Secondary width, horn attachment |
| horn_left/right | 0.60-0.85 | Upper body projections |
| cutaway_left/right | 0.55-0.80 | Access cutaways |
| shoulder | 0.75-0.90 | Bout-to-neck transition |
| neck_pocket | 0.80-1.00 | Neck attachment |

Zones have **fuzzy boundaries** — a point can belong to multiple zones with weights.

---

## Variant Grammar

The grammar classifies bodies by **behavior**, not by brand:

| Class | Description | Examples |
|-------|-------------|----------|
| ROUNDED_ACOUSTIC | Rounded bouts, smooth waist | Dreadnought, Jumbo |
| ROUNDED_SINGLE_CUT | Rounded with treble cutaway | LP-style |
| DOUBLE_CUT | Symmetric horns | SG, Stratocaster |
| OFFSET_WAIST | Asymmetric waist position | Jazzmaster, Mustang |
| ANGULAR_WEDGE | Line-dominant, suppressed waist | Explorer, Flying V |
| SLAB_BODY | Continuous outline, shallow waist | Telecaster |

---

## MorphologyDescriptor Output

The main output contains:

```python
@dataclass
class MorphologyDescriptor:
    centerline: CenterlineDescriptor      # Centerline with symmetry score
    asymmetry: AsymmetryDescriptor        # Asymmetry characteristics
    left_flank: FlankProfile              # Left side profile
    right_flank: FlankProfile             # Right side profile
    primitives: List[MorphologyPrimitive] # Detected primitives
    zone_coverage: Dict[str, float]       # Evidence per zone
    variant_match: VariantMatch           # Grammar classification
    confidence: float                     # Overall confidence
    missing_regions: List[str]            # Zones without evidence
    extensions: Dict                      # Reserved for future adaptive
```

---

## Integration with IBG

The Body Grid does NOT replace or modify the existing IBG solver.

IBG can consume `MorphologyDescriptor` as **optional advisory evidence**:

```python
from app.instrument_geometry.body.ibg import InstrumentBodyGenerator
from app.instrument_geometry.body.ibg.body_grid import MorphologyAnalyzer

# Existing IBG usage (unchanged)
gen = InstrumentBodyGenerator("dreadnought")
model = gen.complete_from_dxf("partial.dxf")

# Optional: Get morphology descriptor for advisory info
analyzer = MorphologyAnalyzer()
descriptor = analyzer.analyze(evidence)

# Descriptor provides advisory context but does not change solver output
print(f"Variant type: {descriptor.variant_match.morphology_class}")
print(f"Asymmetry: {descriptor.asymmetry.asymmetry_score}")
```

---

## Human Review

The system generates PNG overlays for human review:

```python
from app.instrument_geometry.body.ibg.body_grid import export_overlay, OverlayConfig

config = OverlayConfig(
    width=800,
    height=1000,
    show_zones=True,
    show_primitives=True,
    show_centerline=True,
    show_missing=True,
)

export_overlay(descriptor, "review.png", config)
```

The overlay shows:
- Zone regions (color-coded)
- Centerline with symmetry score
- Detected primitives (color by type)
- Missing regions (hatched)
- Classification legend

**Human reviewer remains the deciding authority.**

---

## Boundaries

**Allowed:**
- Deterministic coordinate normalization
- Fuzzy zone assignment
- Primitive detection from geometry
- Variant grammar classification
- PNG overlay generation

**Forbidden:**
- LLM calls
- ML model inference
- Adaptive mutation
- Production geometry modification
- Autonomous decisions

---

## Archaeological Sources

This implementation references existing sandbox material:

- `sandbox/arc_reconstructor/` — gap bridging, constraint extraction
- `services/blueprint-import/sandbox/text_geometry_eval/` — evaluation framework
- `services/photo-vectorizer/live_test_output/` — photo extraction pipelines
- `benchmark_outputs/` — gap closure tests
- `phase4_output/` — dimension linking artifacts

---

## Testing

```bash
pytest services/api/tests/test_ibg_body_grid*.py -v
```

Test fixtures at: `services/api/tests/fixtures/ibg_body_grid/`
