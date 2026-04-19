# InstrumentBodyGenerator — Dev Order
**Date:** 2026-04-16
**Location:** sandbox/arc_reconstructor/
**Sprint:** Sprint 9

---

## Ground Rules

- All new files go in `sandbox/arc_reconstructor/`
- Zero imports from `services/`
- Zero changes to production pipeline
- Each step has a pass/fail test before proceeding
- Append session audit to `SESSION_AUDITS.md` at end of each session

---

## The Problem This Solves

The blueprint vectorizer produces 82-88% complete outlines consistently.
The remaining 12-18% is missing geometry — gaps in the upper bout, waist
transition, or neck heel where the extraction failed.

The InstrumentBodyGenerator does not trace the missing sections.
It calculates them mathematically from known instrument geometry constraints
and a small number of landmark points visible in the partial outline.

---

## Core Math (already in repo — do not rewrite)

**Woodworker's radius formula** (chord and sagitta → radius):
```python
R = (C**2 / (8 * S)) + (S / 2)
# C = chord length across the curve
# S = sagitta (height of arc above chord midpoint)
```

**Sevy/Mottola side height formula:**
```python
H = (B + (R - sqrt(R**2 - P**2))) - (R - sqrt(R**2 - D**2)) - (M + N)
# H = side height at point D
# B = butt depth
# R = back arch radius
# P = distance from high point to butt
# D = distance from high point to current point
# M = top thickness, N = back thickness
```

**High point location:**
```python
P = (L/2) - (E/2) * sqrt((4*R**2) / (L**2 + E**2) - 1)
# L = body length
# E = butt depth - shoulder depth
```

**Falloff** (already in body_side_arc_solver.py — copy standalone):
```python
def falloff(R, D):
    if D >= R: return R
    return R - sqrt(R**2 - D**2)
```

---

## Step 1 — Scaffold body_contour_solver.py

Create `sandbox/arc_reconstructor/body_contour_solver.py`.

Build in sections. Verify each before proceeding.

### Section A — Data structures

```python
@dataclass
class LandmarkPoint:
    label: str          # "lower_bout_max", "waist_min", "upper_bout_max", etc.
    x_mm: float
    y_mm: float
    source: str         # "vectorizer_extracted" | "user_input" | "calculated"
    confidence: float   # 0.0-1.0

@dataclass
class BodyConstraints:
    # Physical constraints — from spec or user input
    back_radius_mm: float       # R — back arch radius
    butt_depth_mm: float        # B — depth at tail
    shoulder_depth_mm: float    # S — depth at neck
    top_thickness_mm: float     # M
    back_thickness_mm: float    # N
    scale_length_mm: float      # for saddle position verification

@dataclass
class SolvedBodyModel:
    # Outputs
    body_length_mm: float
    lower_bout_width_mm: float
    upper_bout_width_mm: float
    waist_width_mm: float
    waist_y_norm: float             # 0.0-1.0
    outline_points: List[Tuple[float, float]]   # full perimeter, clockwise
    side_heights_mm: List[float]                # height at each outline point
    radii_by_zone: Dict[str, float]             # waist, bout, horn_tip etc.
    confidence: float
    missing_landmarks: List[str]
```

Verify:
```bash
python -c "from body_contour_solver import LandmarkPoint, BodyConstraints, SolvedBodyModel; print('A OK')"
```

---

### Section B — Sevy formula implementation

```python
import math

def falloff(R: float, D: float) -> float:
    if D >= R: return R
    return R - math.sqrt(R**2 - D**2)

def solve_high_point(L: float, B: float, S: float, R: float) -> float:
    """P = distance from high point to butt."""
    E = B - S
    if abs(E) < 0.001:
        return L / 2  # symmetric — high point at center
    inner = (4 * R**2) / (L**2 + E**2) - 1
    if inner < 0:
        return L / 2  # fallback
    return (L / 2) - (E / 2) * math.sqrt(inner)

def solve_side_height(B: float, R: float, P: float, D: float,
                       M: float, N: float) -> float:
    """H = side height at distance D from high point."""
    return (B + (R - math.sqrt(R**2 - P**2))) - (R - math.sqrt(R**2 - D**2)) - (M + N)

def woodworker_radius(chord_mm: float, sagitta_mm: float) -> float:
    """R from chord and sagitta."""
    if sagitta_mm <= 0:
        return float('inf')
    return (chord_mm**2 / (8 * sagitta_mm)) + (sagitta_mm / 2)
```

Verify against published values:
```bash
python -c "
from body_contour_solver import solve_side_height, solve_high_point, falloff

# Test values from Mottola article sidecalc.xls:
# R=180in, L=19.25in, B=4.0in, S=3.3in, M=0.11in, N=0.09in
# P=3.093in, H at D=1.0in should be 3.824in

R = 180 * 25.4   # convert to mm
L = 19.25 * 25.4
B = 4.0 * 25.4
S = 3.3 * 25.4
M = 0.11 * 25.4
N = 0.09 * 25.4
D = 1.0 * 25.4

P = solve_high_point(L, B, S, R)
H = solve_side_height(B, R, P, D, M, N)

print(f'P = {P/25.4:.3f} in (expect 3.093)')
print(f'H = {H/25.4:.3f} in (expect 3.824)')
"
```

Pass condition: P within 0.01in of 3.093, H within 0.01in of 3.824.

---

### Section C — Body contour solver

```python
class BodyContourSolver:
    """
    Solves complete body outline from landmark points + constraints.
    
    Minimum viable input:
      - lower_bout_max (x, y)
      - waist_min (x, y)  
      - constraints.back_radius_mm
      - constraints.butt_depth_mm
      - constraints.shoulder_depth_mm
    
    Additional landmarks improve accuracy:
      - upper_bout_max (x, y)
      - neck_block_edge (x, y)
      - end_block_center (x, y)
      - bridge_plate_center (x, y)
    """

    def __init__(self, constraints: BodyConstraints):
        self.constraints = constraints
        self.landmarks: Dict[str, LandmarkPoint] = {}

    def add_landmark(self, point: LandmarkPoint):
        self.landmarks[point.label] = point

    def solve(self) -> SolvedBodyModel:
        """Main solver — runs constraint satisfaction then Sevy."""
        
        # Step 1: derive body dimensions from landmarks
        dims = self._solve_dimensions()
        
        # Step 2: generate outline points from dimensions
        outline = self._generate_outline(dims)
        
        # Step 3: solve side heights at each outline point
        side_heights = self._solve_side_heights(outline, dims)
        
        # Step 4: compute arc radii at each body zone
        radii = self._compute_zone_radii(outline, dims)
        
        return SolvedBodyModel(
            body_length_mm=dims['body_length'],
            lower_bout_width_mm=dims['lower_bout'],
            upper_bout_width_mm=dims['upper_bout'],
            waist_width_mm=dims['waist'],
            waist_y_norm=dims['waist_y_norm'],
            outline_points=outline,
            side_heights_mm=side_heights,
            radii_by_zone=radii,
            confidence=self._compute_confidence(),
            missing_landmarks=self._missing_landmarks(),
        )
```

---

### Section D — Dimension solver

Derives body_length, lower_bout, upper_bout, waist from available landmarks.
Uses available landmarks first, falls back to instrument family defaults.

```python
def _solve_dimensions(self) -> Dict[str, float]:
    dims = {}

    # Lower bout — from landmark or constraints
    if 'lower_bout_max' in self.landmarks:
        lm = self.landmarks['lower_bout_max']
        dims['lower_bout'] = abs(lm.x_mm) * 2  # half-body × 2
    else:
        dims['lower_bout'] = self._family_default('lower_bout')

    # Body length — from end_block + neck_block if available
    if 'end_block_center' in self.landmarks and 'neck_block_edge' in self.landmarks:
        end_y = self.landmarks['end_block_center'].y_mm
        neck_y = self.landmarks['neck_block_edge'].y_mm
        dims['body_length'] = abs(end_y - neck_y)
    elif 'lower_bout_max' in self.landmarks:
        # Estimate from lower bout — typical acoustic ratio
        dims['body_length'] = dims['lower_bout'] * 1.36
    else:
        dims['body_length'] = self._family_default('body_length')

    # Waist — from landmark or calculated
    if 'waist_min' in self.landmarks:
        wm = self.landmarks['waist_min']
        dims['waist'] = abs(wm.x_mm) * 2
        # waist_y_norm from waist Y relative to body extents
        dims['waist_y_norm'] = self._compute_waist_y_norm(wm.y_mm, dims['body_length'])
    else:
        dims['waist'] = dims['lower_bout'] * 0.63  # typical ratio
        dims['waist_y_norm'] = 0.44

    # Upper bout — from neck_block or landmark
    if 'upper_bout_max' in self.landmarks:
        ub = self.landmarks['upper_bout_max']
        dims['upper_bout'] = abs(ub.x_mm) * 2
    elif 'neck_block_edge' in self.landmarks:
        nb = self.landmarks['neck_block_edge']
        dims['upper_bout'] = abs(nb.x_mm) * 2 + self.constraints.top_thickness_mm * 2
    else:
        dims['upper_bout'] = dims['lower_bout'] * 0.76  # typical ratio

    return dims
```

---

### Section E — Outline generator

Generates full perimeter point set from solved dimensions.
Uses circular arc segments between bout and waist anchor points.

```python
def _generate_outline(self, dims: Dict, n_points: int = 200) -> List[Tuple[float, float]]:
    """
    Generate body outline as ordered point set.
    Origin: body center at butt end.
    Orientation: neck end at positive Y.
    """
    # Four anchor points (half-body, right side):
    #   P_butt:      (0, 0)
    #   P_lower_max: (lower_bout/2, waist_y * body_length * 0.3)
    #   P_waist:     (waist/2, waist_y * body_length)
    #   P_upper_max: (upper_bout/2, waist_y * body_length + ...)
    #   P_neck:      (upper_bout/2, body_length)

    # Fit circular arcs through each adjacent triple of anchor points
    # Lower curve: butt → lower_bout_max → waist
    # Upper curve: waist → upper_bout_max → neck
    
    # Generate points along each arc, mirror for left side, close at butt and neck
    ...
```

---

### Section F — Side height solver

Calls Sevy formula at each perimeter point.

```python
def _solve_side_heights(self, outline, dims) -> List[float]:
    c = self.constraints
    L = dims['body_length']
    B = c.butt_depth_mm
    S = c.shoulder_depth_mm
    R = c.back_radius_mm
    M = c.top_thickness_mm
    N = c.back_thickness_mm

    P = solve_high_point(L, B, S, R)
    heights = []

    for x, y in outline:
        # D = distance from high point (high point is on centerline at y=P from butt)
        high_point_y = P
        D = math.hypot(x, y - high_point_y)
        H = solve_side_height(B, R, P, D, M, N)
        heights.append(max(0.0, H))

    return heights
```

---

### Section G — Zone radius computation

Computes arc radius at waist, lower bout, upper bout using woodworker formula.

```python
def _compute_zone_radii(self, outline, dims) -> Dict[str, float]:
    # At waist: measure chord across waist, sagitta from adjacent points
    # At lower bout: same approach
    # At upper bout: same approach
    # Returns dict for MEASURED_RADII in curvature_correction.py
    ...
```

---

## Step 2 — First Test: Cuatro Venezolano Quibor

All 10 constraint values are in `cuatro_instrument_library.json` from today's session.
This is a pure math test — no vectorizer input, no partial outline, just known spec.

```python
# test_cuatro_solver.py

from body_contour_solver import BodyContourSolver, BodyConstraints, LandmarkPoint

# All values from cuatro_instrument_library.json (IMCUA 000 Quibor)
constraints = BodyConstraints(
    back_radius_mm=1000.0,      # estimated — not in spec, use generic small-body
    butt_depth_mm=95.0,         # from Sheet 2: 9.5cm
    shoulder_depth_mm=80.0,     # estimated from proportions
    top_thickness_mm=1.9,       # from Sheet 4/5: 1.8-2.0mm
    back_thickness_mm=2.0,      # from Sheet 6
    scale_length_mm=556.5,      # from Sheet 1
)

solver = BodyContourSolver(constraints)

# Known landmark points from the 8-sheet plan
solver.add_landmark(LandmarkPoint(
    label='lower_bout_max',
    x_mm=125.05,    # half of 250.1mm lower bout
    y_mm=80.0,      # estimated Y position
    source='spec',
    confidence=1.0,
))
solver.add_landmark(LandmarkPoint(
    label='upper_bout_max',
    x_mm=78.45,     # half of 156.9mm upper bout
    y_mm=270.0,
    source='spec',
    confidence=1.0,
))

result = solver.solve()

print(f"Body length:    {result.body_length_mm:.1f}mm  (expect 350.0)")
print(f"Lower bout:     {result.lower_bout_width_mm:.1f}mm (expect 250.1)")
print(f"Upper bout:     {result.upper_bout_width_mm:.1f}mm (expect 156.9)")
print(f"Waist (solved): {result.waist_width_mm:.1f}mm  (expect ~130mm)")
print(f"Waist Y norm:   {result.waist_y_norm:.3f}    (expect ~0.43)")
print(f"Outline points: {len(result.outline_points)}")
print(f"Confidence:     {result.confidence:.2f}")
print(f"\nZone radii:")
for zone, R in result.radii_by_zone.items():
    print(f"  {zone}: {R:.1f}mm")
```

Pass condition:
- Body length within 5% of 350mm
- Lower bout within 1% of 250.1mm (it was input — should be exact)
- Waist solved to 120-145mm range (no spec value — solver estimates)
- Outline has 200 points
- Side heights all positive and in range 80-100mm

---

## Step 3 — Second Test: Partial Vectorizer Output

Take `dreadnought_phase5b_tier0_final.dxf` from the arc reconstructor sandbox.
Extract the landmark points from the 17 closed chains:
- Widest X point = lower_bout_max
- Narrowest X point in middle Y range = waist_min
- Widest X point in upper Y range = upper_bout_max

Run the solver with dreadnought constraints:

```python
constraints = BodyConstraints(
    back_radius_mm=7620.0,      # 25-foot Martin standard
    butt_depth_mm=121.0,        # standard dreadnought
    shoulder_depth_mm=105.0,
    top_thickness_mm=2.8,
    back_thickness_mm=2.5,
    scale_length_mm=645.0,
)
```

Compare solver output against known dreadnought spec:
- Lower bout: 381mm expected
- Body length: 520mm expected
- Waist: 241mm expected

---

## Step 4 — DXF Output

Write the solved outline as a clean DXF to validate visually in Fusion 360.

```python
def outline_to_dxf(result: SolvedBodyModel, output_path: str, spec_name: str):
    """Write solved body outline to R12 DXF."""
    import ezdxf
    doc = ezdxf.new('R12')
    msp = doc.modelspace()
    
    pts = result.outline_points
    for i in range(len(pts) - 1):
        msp.add_line(pts[i], pts[i+1], dxfattribs={'layer': 'BODY_SOLVED'})
    # Close the outline
    msp.add_line(pts[-1], pts[0], dxfattribs={'layer': 'BODY_SOLVED'})
    
    # Centerline
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    msp.add_line((0, min_y), (0, max_y), dxfattribs={'layer': 'CENTERLINE'})
    
    doc.saveas(output_path)
    print(f"Saved: {output_path}")
```

Output to: `sandbox/arc_reconstructor/results/cuatro_quibor_solved.dxf`

---

## Step 5 — ConstraintExtractor

Reads a partial DXF outline and extracts landmark points automatically.

```python
def extract_landmarks_from_dxf(dxf_path: str) -> List[LandmarkPoint]:
    """
    Extract body landmark points from a partial vectorizer output.
    
    Finds:
    - lower_bout_max: point of maximum X extent in lower body region
    - waist_min: point of minimum X in middle body region  
    - upper_bout_max: point of maximum X in upper body region
    - end_block: lowest Y extent
    - neck_block: highest Y extent with significant width
    """
    ...
```

---

## Step 6 — InstrumentBodyGenerator (couples everything)

```python
class InstrumentBodyGenerator:
    """
    Takes partial vectorizer DXF output + instrument class.
    Returns complete parametric body model.
    
    Usage:
        gen = InstrumentBodyGenerator(spec_name='dreadnought')
        model = gen.complete_from_dxf('partial_outline.dxf')
        model.save_dxf('completed_outline.dxf')
        model.export_spec_json('completed_spec.json')
    """
    
    def __init__(self, spec_name: str):
        self.spec_name = spec_name
        self.constraints = self._load_constraints(spec_name)
    
    def complete_from_dxf(self, dxf_path: str) -> SolvedBodyModel:
        # Step 1: extract landmarks from partial DXF
        extractor = ConstraintExtractor()
        landmarks = extractor.extract_landmarks_from_dxf(dxf_path)
        
        # Step 2: solve complete body
        solver = BodyContourSolver(self.constraints)
        for lm in landmarks:
            solver.add_landmark(lm)
        
        return solver.solve()
    
    def complete_from_landmarks(self, landmarks: List[LandmarkPoint]) -> SolvedBodyModel:
        """For user-provided landmark points (paid tier override)."""
        solver = BodyContourSolver(self.constraints)
        for lm in landmarks:
            solver.add_landmark(lm)
        return solver.solve()
    
    def _load_constraints(self, spec_name: str) -> BodyConstraints:
        """Load from instrument_library JSON or use family defaults."""
        ...
```

---

## Rollout Order

| Step | File | Test | Pass Condition |
|------|------|------|----------------|
| 1A | body_contour_solver.py — data structures | import test | No errors |
| 1B | body_contour_solver.py — Sevy formulas | Mottola spreadsheet values | P=3.093in ±0.01, H=3.824in ±0.01 |
| 1C | body_contour_solver.py — dimension solver | Cuatro spec input | Dimensions within 5% of spec |
| 1D | body_contour_solver.py — outline generator | Point count + closure | 200 points, first=last |
| 1E | body_contour_solver.py — side heights | All positive, in range | 0 < H < 200mm for all points |
| 2 | test_cuatro_solver.py | Full Cuatro solve | Waist 120-145mm, confidence > 0.7 |
| 3 | test_dreadnought_solver.py | Partial DXF input | Lower bout within 10% of 381mm |
| 4 | DXF output | Open in Fusion 360 | Recognizable guitar body, no artifacts |
| 5 | constraint_extractor.py | Extract from dreadnought DXF | Finds lower_bout_max, waist_min, upper_bout_max |
| 6 | instrument_body_generator.py | End-to-end | Partial DXF → complete spec JSON |

No step proceeds until previous step passes.
Append to SESSION_AUDITS.md after each work session.

---

## Session Audit Template

Add to SESSION_AUDITS.md:

```markdown
## Session YYYY-MM-DD — InstrumentBodyGenerator

### Items Built
| # | Item | Classification | File |
|---|------|----------------|------|
| N | Description | SANDBOX | body_contour_solver.py:lines |

### Test Results
| Test | Input | Expected | Actual | Pass/Fail |
|------|-------|----------|--------|-----------|

### Production Impact
None. All work sandbox-only.

### Open Items
- [ ] Next step
```
