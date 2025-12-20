# How to Add a New Calculation

**Luthier's Toolbox - Developer Guide**
**Version:** 1.0
**Date:** December 20, 2025

---

## Before You Start

1. Read `ARCHITECTURE_INVARIANTS.md` - the placement constitution
2. Identify which layer your calculation belongs in
3. Check if a similar function already exists

---

## Quick Decision: Where Does It Go?

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHERE DOES MY CALCULATION GO?                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Is it pure geometry (arc, circle, point, vector)?             │
│  └── YES → geometry/arc_utils.py                               │
│                                                                 │
│  Is it instrument-specific (fret, bridge, body, neck)?         │
│  └── YES → instrument_geometry/{subdomain}/                    │
│                                                                 │
│  Is it CAM-specific (toolpath, biarc, trochoid)?               │
│  └── YES → cam/{module}.py                                     │
│                                                                 │
│  Is it domain-specific (RMOS scoring, Saw Lab risk)?           │
│  └── YES → {domain}/calculators/ or {domain}/{module}.py       │
│                                                                 │
│  Does it orchestrate multiple calculations?                     │
│  └── YES → calculators/{module}.py                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: Adding a Pure Math Function

### Example: Arc Length from Chord and Height

**Step 1: Identify the layer**

This is pure geometry → `geometry/arc_utils.py`

**Step 2: Write the function**

```python
# geometry/arc_utils.py

def arc_length_from_chord_and_height(chord: float, height: float) -> float:
    """
    Calculate arc length from chord length and sagitta (height).

    Uses the formula: L = 2 * R * arcsin(c / (2 * R))
    where R = (c² + 4h²) / (8h) and c = chord, h = height

    Args:
        chord: Chord length (straight-line distance)
        height: Sagitta (perpendicular distance from chord to arc)

    Returns:
        Arc length

    Example:
        >>> arc_length_from_chord_and_height(10.0, 2.0)
        10.883...
    """
    from math import sqrt, asin

    if height <= 0:
        return chord  # Flat line

    # Calculate radius from chord and height
    c, h = chord, height
    radius = (c * c + 4 * h * h) / (8 * h)

    # Calculate arc length
    half_chord = c / 2
    if half_chord > radius:
        half_chord = radius  # Clamp to valid range

    arc_length = 2 * radius * asin(half_chord / radius)
    return arc_length
```

**Step 3: Export from `__init__.py`**

```python
# geometry/__init__.py

from .arc_utils import (
    # ... existing exports ...
    arc_length_from_chord_and_height,  # NEW
)

__all__ = [
    # ... existing exports ...
    "arc_length_from_chord_and_height",  # NEW
]
```

**Step 4: Write a test**

```python
# tests/test_geometry_arc_utils.py

def test_arc_length_from_chord_and_height():
    # Flat case
    assert arc_length_from_chord_and_height(10.0, 0.0) == 10.0

    # Known case: semicircle with diameter 10
    # chord = 10, height = 5 (radius), arc = π * 5 ≈ 15.708
    result = arc_length_from_chord_and_height(10.0, 5.0)
    assert abs(result - 15.708) < 0.01
```

**Step 5: Run governance tests**

```bash
pytest tests/test_route_governance.py -v
```

---

## Step-by-Step: Adding an Instrument Calculation

### Example: Multi-Scale Fret Positions

**Step 1: Identify the layer**

This is instrument-specific math → `instrument_geometry/neck/fret_math.py`

**Step 2: Write the function**

```python
# instrument_geometry/neck/fret_math.py

def compute_multiscale_fret_positions(
    bass_scale_mm: float,
    treble_scale_mm: float,
    num_frets: int,
    perpendicular_fret: int = 0,
) -> List[Tuple[float, float]]:
    """
    Calculate fret positions for a fanned (multi-scale) fretboard.

    Args:
        bass_scale_mm: Scale length on bass side (mm)
        treble_scale_mm: Scale length on treble side (mm)
        num_frets: Number of frets to calculate
        perpendicular_fret: Which fret is perpendicular (0 = nut)

    Returns:
        List of (bass_position, treble_position) tuples in mm

    Example:
        >>> positions = compute_multiscale_fret_positions(686, 648, 24, 7)
        >>> len(positions)
        24
    """
    positions = []

    for fret in range(1, num_frets + 1):
        # Equal temperament formula for each side
        bass_pos = bass_scale_mm * (1 - 2 ** (-fret / 12))
        treble_pos = treble_scale_mm * (1 - 2 ** (-fret / 12))
        positions.append((bass_pos, treble_pos))

    return positions
```

**Step 3: Export and test** (same pattern as above)

---

## Step-by-Step: Adding a CAM Calculation

### Example: Trochoid Step-Over

**Step 1: Identify the layer**

This is CAM-specific → `cam/trochoid_l3.py` or new `cam/trochoid_utils.py`

**Step 2: Write the function**

```python
# cam/trochoid_utils.py

def calculate_trochoid_stepover(
    tool_diameter: float,
    engagement_percent: float,
) -> float:
    """
    Calculate trochoid milling step-over distance.

    Args:
        tool_diameter: Tool diameter in mm
        engagement_percent: Radial engagement as percentage (0-100)

    Returns:
        Step-over distance in mm
    """
    engagement = engagement_percent / 100.0
    return tool_diameter * engagement
```

---

## Step-by-Step: Using a Calculation in a Router

### Example: Exposing Fret Calculation via API

**Step 1: Create the router endpoint**

```python
# routers/fret_router.py

from ..instrument_geometry.neck.fret_math import compute_multiscale_fret_positions

@router.post("/multiscale")
async def calculate_multiscale_frets(request: MultiscaleRequest):
    """Calculate fanned fret positions."""
    # ONLY HTTP handling - delegate math
    positions = compute_multiscale_fret_positions(
        bass_scale_mm=request.bass_scale_mm,
        treble_scale_mm=request.treble_scale_mm,
        num_frets=request.num_frets,
        perpendicular_fret=request.perpendicular_fret,
    )

    return {
        "positions": [
            {"fret": i + 1, "bass_mm": p[0], "treble_mm": p[1]}
            for i, p in enumerate(positions)
        ]
    }
```

**What NOT to do:**

```python
# WRONG - math in router
@router.post("/multiscale")
async def calculate_multiscale_frets(request: MultiscaleRequest):
    positions = []
    for fret in range(1, request.num_frets + 1):
        # NO! This math should be in fret_math.py
        bass_pos = request.bass_scale_mm * (1 - 2 ** (-fret / 12))
        treble_pos = request.treble_scale_mm * (1 - 2 ** (-fret / 12))
        positions.append((bass_pos, treble_pos))
    return {"positions": positions}
```

---

## Step-by-Step: Cross-Domain Calculation

### Example: Saw Operation with RMOS Integration

**Step 1: Create the service** (in `services/`)

```python
# services/saw_lab_service.py

from ..saw_lab.risk_evaluator import evaluate_risk
from ..rmos.runs_v2 import validate_and_persist

def evaluate_saw_operation(params):
    """Orchestrate Saw Lab + RMOS."""
    # Delegate to domain modules
    risk = evaluate_risk(params)
    artifact = validate_and_persist(...)
    return artifact
```

**Step 2: Call from router**

```python
# routers/saw_router.py

from ..services.saw_lab_service import evaluate_saw_operation

@router.post("/evaluate")
async def evaluate(request: SawRequest):
    result = evaluate_saw_operation(request.dict())
    return {"artifact_id": result.run_id}
```

---

## Checklist Before PR

- [ ] Function is in the correct layer (see decision tree)
- [ ] Function uses `math.pi`, not `3.14159`
- [ ] Function has docstring with Args, Returns, Example
- [ ] Function is exported from `__init__.py`
- [ ] Test exists for the function
- [ ] Router delegates to function (no inline math)
- [ ] `pytest tests/test_route_governance.py -v` passes

---

## Common Mistakes

### Mistake 1: Math in Router

```python
# WRONG
@router.post("/circle")
async def calc_circle(req):
    circumference = 2 * 3.14159 * req.radius  # TWO violations!
    return {"circumference": circumference}
```

**Fix:** Move to `geometry/arc_utils.py`, use `math.pi`

---

### Mistake 2: Duplicate Function

```python
# WRONG - duplicating fret_math.py logic
# calculators/my_calculator.py
def fret_position(scale, fret):
    return scale * (1 - 2 ** (-fret / 12))  # Already exists!
```

**Fix:** Import from `instrument_geometry/neck/fret_math.py`

---

### Mistake 3: Cross-Domain Import in Domain Module

```python
# WRONG - saw_lab importing rmos
# saw_lab/risk_evaluator.py
from ..rmos.runs_v2 import persist_run  # NO!
```

**Fix:** Create `services/saw_lab_service.py` to bridge domains

---

### Mistake 4: Business Logic in Geometry

```python
# WRONG - domain knowledge in pure math
# geometry/arc_utils.py
def calculate_fret_arc(scale_length, fret_number):  # NO!
    # Fret knowledge doesn't belong in geometry
```

**Fix:** Put in `instrument_geometry/neck/fret_math.py`

---

## Canonical Modules Reference

| Need | Module | Layer |
|------|--------|-------|
| Arc/circle math | `geometry/arc_utils.py` | 1 |
| Fret positions | `instrument_geometry/neck/fret_math.py` | 2 |
| Body outlines | `instrument_geometry/body/parametric.py` | 2 |
| Bridge geometry | `instrument_geometry/bridge/geometry.py` | 2 |
| Biarc/fillet | `cam/biarc_math.py` | 4 |
| Toolpath generation | `cam/adaptive_core.py` | 4 |
| RMOS feasibility | `rmos/feasibility_scorer.py` | 4 |
| Saw risk | `saw_lab/risk_evaluator.py` | 4 |
| Cross-domain orchestration | `services/*.py` | 5 |

---

## Getting Help

1. Check `ARCHITECTURE_INVARIANTS.md` for the 6-layer map
2. Search existing modules for similar functions
3. Run `pytest tests/test_route_governance.py -v` to check compliance
4. If unsure, ask before implementing

---

*Follow this guide to keep the codebase clean and maintainable.*
