# Thin-Stroke PDF Vectorization: Developer Handoff Document

**Status:** Open diagnostic case — requires architectural solution  
**Date:** 2026-04-14  
**Author:** Production Shop  
**Priority:** Medium — affects Pass A structural extraction reliability

---

## 1. Executive Summary

The blueprint vectorizer pipeline experiences degraded reliability on a specific class of PDF inputs: those whose body/profile geometry is defined by extremely thin, partially discontinuous strokes. These files produce fragmented structural contours even at higher DPI settings.

**Business impact:**  
- Estimated 10-15% of historical blueprint PDFs fall into this class
- Current workaround: manual DXF cleanup in CAD software (30-60 min per file)
- Blocks production-ready output for affected files

**Root cause:**  
The extraction pipeline applies a single global simplification epsilon (0.001) to all contours. This value optimizes for annotation text fidelity but under-simplifies thin profile strokes, preserving fragmentation artifacts from the source rasterization.

**Proposed solution:**  
Radius-based contour classification using the existing `radius_profiles.py` infrastructure. Profile curves exhibit stable local curvature; thin/fragmented strokes show curvature instability. Classify before simplification; apply regime-specific epsilon values.

**Estimated effort:** 3-5 days engineering time  
**Risk if unaddressed:** Continued manual intervention, user frustration, potential scope creep into ad-hoc fixes

---

## 2. System Architecture

### 2.1 Dual-Pass Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PDF INPUT                                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Rasterization (pdf2image, configurable DPI)                         │
│  Location: blueprint_orchestrator.py                                 │
│  Current: 200 DPI platform-wide                                      │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   PASS A            │       │   PASS B            │
│   Structural        │       │   Annotation        │
│                     │       │                     │
│ • SIMPLE threshold  │       │ • Finer threshold   │
│ • epsilon=0.001     │       │ • epsilon=0.0005    │
│ • min_area=50px     │       │ • min_area=12px     │
│ • Layer: BODY,      │       │ • Layer: ANNOTATION │
│   AUX_VIEWS,        │       │   only              │
│   PAGE_FRAME        │       │                     │
└─────────┬───────────┘       └─────────┬───────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer Classification (layer_builder.py)                             │
│  BODY_CORE, BODY_SUPPORT, AUX_VIEWS, ANNOTATION, TITLE_BLOCK,       │
│  PAGE_FRAME                                                          │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Gap Joining (layer_builder.py: join_body_gaps)                      │
│  • 2.0mm endpoint distance                                           │
│  • 25° tangent alignment                                             │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Acceptance Grading                                                  │
│  STARTER (BODY≥1) → USABLE (BODY≥3, >20%) → PRODUCTION_READY        │
│  (BODY≥10, >40%)                                                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DXF Export (R12 AC1009, LINE only)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Where Thin-Stroke Fragmentation Occurs

The problem manifests at **three points** in the pipeline:

1. **Rasterization** — Thin strokes (1-2px at 300 DPI) suffer aliasing; stroke continuity depends on source construction quality
2. **Adaptive threshold** — `cv2.adaptiveThreshold()` with fixed block_size (21) may fragment thin strokes differently than thick ones
3. **Simplification** — `cv2.approxPolyDP(epsilon=0.001 * perimeter)` is tuned for text; profile curves need lower epsilon

---

## 3. Code Surface Area

### 3.1 Core Extraction Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `services/photo-vectorizer/edge_to_dxf.py` | SIMPLE extraction engine | `extract_entities_simple()` (line 475), `vectorize_entities_to_dxf()` (line 557) |
| `services/api/app/services/blueprint_extract.py` | Pass A orchestration | `extract_structural_pass()` (line 417) |
| `services/api/app/services/annotation_extract.py` | Pass B extraction | `extract_annotations()` (line 139), `_classify_annotation()` (line 75) |
| `services/api/app/services/blueprint_orchestrator.py` | Pipeline coordinator | `run_dual_pass_extraction()`, DPI settings |
| `services/api/app/services/layer_builder.py` | Layer classification | `build_layers()`, `join_body_gaps()`, `evaluate_layered_acceptance()` |
| `services/api/app/services/dual_pass_overlay.py` | Debug visualization | `create_layered_overlay()` (line 247) |

### 3.2 Radius/Curvature Infrastructure

| File | Purpose | Key Functions |
|------|---------|---------------|
| `services/api/app/instrument_geometry/neck/radius_profiles.py` | Radius mathematics | `compute_radius_arc_points()`, `compute_radius_drop_mm()` |
| `services/api/app/exports/curvemath_biarc.py` | Arc fitting | `_arc_from_A_T_to_B()`, `biarc_entities()` |
| `services/api/app/routers/radius_dish_router.py` | Dish geometry | `dish_z_at()`, `brace_camber_mm()` |
| `services/photo-vectorizer/contour_plausibility.py` | Contour scoring | `ContourPlausibilityScorer`, `body_ownership_score()` |

### 3.3 Critical Code Sections

#### Simplification (edge_to_dxf.py:534)
```python
# Current: single global epsilon
epsilon = approx_epsilon_factor * perimeter  # approx_epsilon_factor=0.001
simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
```

#### Adaptive Threshold (edge_to_dxf.py:513-518)
```python
thresh = cv2.adaptiveThreshold(
    gray,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV,
    block_size=21,  # Fixed — affects thin stroke response
    C=10
)
```

---

## 4. Data Schemas

### 4.1 Layer Enum
```python
class Layer(str, Enum):
    BODY = "body"
    AUX_VIEWS = "aux_views"
    ANNOTATION = "annotation"
    TITLE_BLOCK = "title_block"
    PAGE_FRAME = "page_frame"
```

### 4.2 AcceptanceGrade Enum
```python
class AcceptanceGrade(str, Enum):
    STARTER = "starter"           # BODY >= 1
    USABLE = "usable"             # BODY >= 3, structural_pct > 20%
    PRODUCTION_READY = "production_ready"  # BODY >= 10, structural_pct > 40%
    REJECT = "reject"             # BODY == 0
```

### 4.3 LayeredEntity
```python
@dataclass
class LayeredEntity:
    contour: np.ndarray      # OpenCV contour
    layer: Layer             # Classified layer
    area_px: float           # Contour area in pixels
    centroid: Tuple[float, float]
    bbox: Tuple[int, int, int, int]  # x, y, w, h
```

### 4.4 Proposed: ContourCurvatureProfile
```python
@dataclass
class ContourCurvatureProfile:
    """Per-contour curvature analysis for classification"""
    contour: np.ndarray
    local_radii: List[float]      # Radius at each vertex
    radius_stability: float       # std(radii) / mean(radii)
    min_radius_mm: float
    max_radius_mm: float
    classification: str           # "profile_curve" | "thin_stroke" | "annotation"
    recommended_epsilon: float    # 0.0005 for profile, 0.001 for annotation
```

---

## 5. Tests and Experiments Conducted

### 5.1 Approaches Tested

| Approach | Configuration | Result | Why Rejected |
|----------|---------------|--------|--------------|
| Morphological close | `cv2.MORPH_CLOSE(3x3)` | Made fragmentation worse | Merged adjacent strokes, destroyed detail |
| Lower epsilon | 0.001 → 0.00075 | Improved profile continuity | Regressed text fidelity on OM PDF |
| Higher DPI | 200 → 250 → 300 | Marginal stroke width gain | Gaps remained; processing time increased 2x |
| Increased gap join threshold | 2.0mm → 5.0mm | Some gaps closed | Over-aggressive; merged unrelated contours |

### 5.2 Diagnostic Overlay Analysis

Created 4-stage overlay comparing:
1. Source grayscale
2. Post-threshold binary
3. Pre-simplification contours
4. Post-simplification BODY contours

**Finding:** Simplification is NOT the primary culprit. 
- Dreadnought: 1269 raw → 1266 simplified (only 3 lost)
- The fragmentation exists at the binary threshold stage

### 5.3 Two-Regime Observation

The core insight from testing:

| Contour Type | Optimal Epsilon | Behavior at 0.001 | Behavior at 0.00075 |
|--------------|-----------------|-------------------|---------------------|
| Profile curves | 0.0005-0.00075 | Preserves noise | Clean, continuous |
| Fine drafting/text | 0.001-0.002 | Clean, readable | Over-detailed, artifacts |

**A single flat epsilon cannot optimize both simultaneously.**

---

## 6. Blueprint Processing Techniques

### 6.1 Current Adaptive Threshold

```python
cv2.adaptiveThreshold(
    gray,
    maxValue=255,
    adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    thresholdType=cv2.THRESH_BINARY_INV,
    blockSize=21,    # 21px neighborhood
    C=10             # Subtraction constant
)
```

- **blockSize=21**: Fixed; good for typical stroke weights
- **C=10**: Offset for noise rejection
- **Problem**: Thin strokes (1-2px) may fall below the local threshold in some neighborhoods

### 6.2 Contour Simplification

```python
epsilon = approx_epsilon_factor * cv2.arcLength(contour, closed=True)
simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
```

- **Ramer-Douglas-Peucker algorithm**
- **epsilon** controls maximum deviation from original
- Lower epsilon = more vertices preserved = finer detail

### 6.3 Gap Joining (Current Implementation)

```python
def join_body_gaps(
    layered: LayeredEntities,
    max_gap_mm: float = 2.0,
    max_angle_deg: float = 25.0,
) -> Tuple[LayeredEntities, GapJoinResult]:
```

- Operates on BODY layer only
- Checks endpoint proximity and tangent alignment
- Creates LINE segments to bridge gaps
- **Limitation**: Cannot reconstruct curvature; creates straight bridges

---

## 7. The Contour Classification Problem

### 7.1 Current Classification Logic

Layer assignment happens in `layer_builder.py:build_layers()`:

1. **PAGE_FRAME**: Touches 3+ edges, large area
2. **TITLE_BLOCK**: Bottom 15%, right 25% region
3. **BODY_CORE**: Largest non-frame contour in central region
4. **BODY_SUPPORT**: Overlaps BODY_CORE region by >30%
5. **AUX_VIEWS**: Everything else from Pass A
6. **ANNOTATION**: All Pass B contours

### 7.2 Why Current Classification Fails for Thin Strokes

The classification is **geometry-based** (position, area, overlap) not **structural-based** (curvature, continuity). A thin profile stroke fragment:

- May be small area → classified as AUX_VIEWS or ANNOTATION
- May not overlap BODY_CORE → excluded from BODY_SUPPORT
- May have endpoint gaps → fails join_body_gaps() tangent check

### 7.3 The Missing Signal: Curvature Stability

Profile curves have a defining characteristic: **stable local curvature**. A guitar body outline:
- Smooth transitions between bouts
- Radius changes gradually (no sharp kinks)
- Local radius in range 50mm-500mm typically

Thin stroke fragments:
- Erratic curvature (noise from rasterization)
- May have near-infinite radius (straight segments)
- Sharp angle changes at fragment boundaries

**This is a classifiable signal.**

---

## 8. Luthiery Domain Insight: Radius Calculator Integration

The codebase already has robust radius calculation infrastructure for fretboard and brace work. This same mathematics applies to contour curvature analysis.

### 8.1 Radius Profiles Module

**File:** `services/api/app/instrument_geometry/neck/radius_profiles.py`

```python
"""
Instrument Geometry: Radius Profiles

Functions for computing fretboard and bridge radius curves.

Radius Theory:
    The fretboard radius is the radius of the cylindrical surface
    that forms the fretboard's cross-section. A smaller radius
    creates a more curved surface (easier for barre chords),
    while a larger radius is flatter (better for bending).

Common Radius Values:
    - 7.25" (184mm): Vintage Fender - very curved
    - 9.5" (241mm): Modern Fender - moderate curve
    - 10" (254mm): PRS, some Gibsons
    - 12" (305mm): Gibson standard - flatter
    - 14" (356mm): Ibanez JEM
    - 16" (406mm): Martin acoustic, some shred guitars
    - 20" (508mm): Very flat, almost classical feel
    - Flat/Infinite: Classical guitars
"""

from math import sqrt, asin, pi
from typing import List, Tuple, Optional


def compute_radius_arc_points(
    radius_mm: float,
    width_mm: float,
    num_points: int = 50,
) -> List[Tuple[float, float]]:
    """
    Generate points along a radius arc for visualization or CNC.

    The arc is centered at (0, 0) with the center of the arc
    at (0, -radius_mm). Points span from -width/2 to +width/2.

    Args:
        radius_mm: Radius of the arc.
        width_mm: Total width to span.
        num_points: Number of points to generate.

    Returns:
        List of (x, y) points along the arc.
        X ranges from -width/2 to +width/2.
        Y is the height above the chord (0 at edges).
    """
    if radius_mm <= 0 or width_mm <= 0 or num_points < 2:
        return []

    half_width = width_mm / 2.0

    # Check if width exceeds possible arc
    if half_width >= radius_mm:
        half_width = radius_mm * 0.99

    points: List[Tuple[float, float]] = []

    for i in range(num_points):
        t = i / (num_points - 1)
        x = -half_width + (width_mm * t)

        # Circle equation: x^2 + (y - r)^2 = r^2
        # Solving for y: y = r - sqrt(r^2 - x^2)
        y = radius_mm - sqrt(radius_mm**2 - x**2)

        points.append((x, y))

    return points


def compute_radius_drop_mm(radius_mm: float, offset_mm: float) -> float:
    """
    Compute the height drop at a given offset from center on a radius.

    This is useful for calculating how much lower the fretboard edge
    is compared to the center, or saddle height adjustments.

    Args:
        radius_mm: Radius of the curve.
        offset_mm: Distance from center (e.g., half the string spread).

    Returns:
        Height drop in mm.

    Example:
        >>> drop = compute_radius_drop_mm(241.3, 21.0)  # 9.5" radius, 42mm board
        >>> round(drop, 2)
        0.92  # Almost 1mm drop at the edge
    """
    if radius_mm <= 0 or offset_mm < 0:
        return 0.0

    if offset_mm >= radius_mm:
        return radius_mm

    # Height drop = r - sqrt(r^2 - x^2)
    return radius_mm - sqrt(radius_mm**2 - offset_mm**2)


def compute_compound_radius_at_fret(
    fret_index: int,
    total_frets: int,
    start_radius_mm: float,
    end_radius_mm: float,
) -> float:
    """
    Compute the fretboard radius at a specific fret for compound radius.

    Uses linear interpolation between start and end radius.

    Args:
        fret_index: Fret number (0 = nut, 1 = first fret, etc.)
        total_frets: Total number of frets on the instrument.
        start_radius_mm: Radius at the nut.
        end_radius_mm: Radius at the last fret.

    Returns:
        Radius in mm at the specified fret.
    """
    if total_frets <= 0:
        return start_radius_mm

    ratio = fret_index / total_frets
    ratio = max(0.0, min(1.0, ratio))

    return start_radius_mm + (end_radius_mm - start_radius_mm) * ratio
```

### 8.2 Bi-Arc Construction Module

**File:** `services/api/app/exports/curvemath_biarc.py`

```python
"""
Bi-arc Construction Algorithm for G1-Continuous Curve Blending

A bi-arc blend uses two circular arcs (or lines if degenerate) to create
a smooth transition between two points with specified tangent directions.
"""

import math
from typing import List, Tuple, Dict, Optional


def _arc_from_A_T_to_B(
    A: Tuple[float, float],
    TA: Tuple[float, float],
    B: Tuple[float, float]
) -> Optional[Dict]:
    """
    Construct circular arc from point A with tangent TA to point B

    Returns:
        Dict with keys: 'type', 'center', 'radius', 'start_angle', 'end_angle'
        Returns None if degenerate
    """
    TA_unit = _unit(TA)

    AB = _sub(B, A)
    dist_AB = math.sqrt(AB[0]**2 + AB[1]**2)
    if dist_AB < 1e-9:
        return None

    NA = _normal(TA_unit)
    M = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)

    AB_unit = (AB[0] / dist_AB, AB[1] / dist_AB)
    perp_bisector = _normal(AB_unit)

    det = NA[0] * (-perp_bisector[1]) - NA[1] * (-perp_bisector[0])
    if abs(det) < 1e-9:
        return None

    rhs = _sub(M, A)
    s = (rhs[0] * (-perp_bisector[1]) - rhs[1] * (-perp_bisector[0])) / det

    C = _add(A, _scale(NA, s))
    radius = math.sqrt((A[0] - C[0])**2 + (A[1] - C[1])**2)

    start_angle = math.degrees(math.atan2(A[1] - C[1], A[0] - C[0]))
    end_angle = math.degrees(math.atan2(B[1] - C[1], B[0] - C[0]))

    return {
        'type': 'arc',
        'center': C,
        'radius': radius,
        'start_angle': start_angle,
        'end_angle': end_angle
    }


def biarc_entities(
    p0: Tuple[float, float],
    t0: Tuple[float, float],
    p1: Tuple[float, float],
    t1: Tuple[float, float]
) -> List[Dict]:
    """
    Construct bi-arc G1-continuous blend between two points with tangents

    Args:
        p0: Start point (x, y) in mm
        t0: Tangent direction at start
        p1: End point (x, y) in mm
        t1: Tangent direction at end

    Returns:
        List of entity dictionaries (arc or line)
    """
    # ... implementation handles tangent intersection, arc fitting
```

### 8.3 Radius Dish Router (Spherical Geometry)

**File:** `services/api/app/routers/radius_dish_router.py`

```python
"""
Radius Dish Router — parametric G-code generator.

The toolpath traces a spherical surface using the equation:
    Z(x, y) = R - sqrt(R² - x² - y²)

This is the exact spherical surface equation.
"""

def dish_z_at(x_mm: float, y_mm: float, radius_mm: float) -> float:
    """
    Z depth at point (x, y) on a spherical dish surface.
    Z = R - sqrt(R² - x² - y²)
    """
    r2  = radius_mm ** 2
    xy2 = x_mm ** 2 + y_mm ** 2
    if xy2 > r2:
        return 0.0
    return radius_mm - math.sqrt(r2 - xy2)


def brace_camber_mm(length_mm: float, radius_mm: float) -> float:
    """
    Pre-bend camber required for a brace to sit flush on a dished plate.
    camber = L² / (8R)   [chord-sagitta, exact geometry]
    """
    if radius_mm <= 0:
        return 0.0
    return length_mm ** 2 / (8.0 * radius_mm)
```

---

## 9. Proposed Solution: Radius-Based Contour Classification

### 9.1 Core Algorithm

Before simplification, analyze each contour's local curvature:

```python
def compute_contour_curvature_profile(
    contour: np.ndarray,
    mm_per_px: float,
    window_size: int = 5,
) -> ContourCurvatureProfile:
    """
    Compute local radius at each vertex using three-point circle fitting.
    
    For three consecutive points P1, P2, P3:
    - Fit a circle through all three
    - The radius of that circle is the local radius at P2
    
    Uses the existing radius math from radius_profiles.py
    """
    points = contour.reshape(-1, 2)
    n = len(points)
    
    if n < window_size:
        return ContourCurvatureProfile(
            contour=contour,
            local_radii=[],
            radius_stability=float('inf'),
            min_radius_mm=0,
            max_radius_mm=0,
            classification="annotation",
            recommended_epsilon=0.001,
        )
    
    local_radii = []
    half_w = window_size // 2
    
    for i in range(half_w, n - half_w):
        # Get points for circle fitting
        p1 = points[i - half_w] * mm_per_px
        p2 = points[i] * mm_per_px
        p3 = points[i + half_w] * mm_per_px
        
        radius = fit_circle_radius(p1, p2, p3)
        local_radii.append(radius)
    
    # Compute stability metric
    radii_array = np.array([r for r in local_radii if r < 10000])  # Filter near-linear
    if len(radii_array) == 0:
        stability = float('inf')
        mean_radius = float('inf')
    else:
        mean_radius = np.mean(radii_array)
        stability = np.std(radii_array) / mean_radius if mean_radius > 0 else float('inf')
    
    # Classification thresholds (tuned for guitar body profiles)
    if stability < 0.5 and 30 < mean_radius < 800:
        classification = "profile_curve"
        epsilon = 0.0005
    elif stability < 1.0:
        classification = "thin_stroke"
        epsilon = 0.00075
    else:
        classification = "annotation"
        epsilon = 0.001
    
    return ContourCurvatureProfile(
        contour=contour,
        local_radii=local_radii,
        radius_stability=stability,
        min_radius_mm=min(radii_array) if len(radii_array) > 0 else 0,
        max_radius_mm=max(radii_array) if len(radii_array) > 0 else 0,
        classification=classification,
        recommended_epsilon=epsilon,
    )


def fit_circle_radius(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
) -> float:
    """
    Fit circle through three points, return radius.
    Uses circumradius formula: R = (a*b*c) / (4*area)
    """
    # Side lengths
    a = math.sqrt((p2[0]-p3[0])**2 + (p2[1]-p3[1])**2)
    b = math.sqrt((p1[0]-p3[0])**2 + (p1[1]-p3[1])**2)
    c = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    
    # Triangle area via cross product
    area = abs((p2[0]-p1[0])*(p3[1]-p1[1]) - (p3[0]-p1[0])*(p2[1]-p1[1])) / 2
    
    if area < 1e-9:
        return float('inf')  # Collinear points = infinite radius
    
    return (a * b * c) / (4 * area)
```

### 9.2 Integration Point

Modify `edge_to_dxf.py:extract_entities_simple()`:

```python
# BEFORE (current):
epsilon = approx_epsilon_factor * perimeter
simplified = cv2.approxPolyDP(contour, epsilon, closed=True)

# AFTER (proposed):
profile = compute_contour_curvature_profile(contour, mm_per_px)
epsilon = profile.recommended_epsilon * perimeter
simplified = cv2.approxPolyDP(contour, epsilon, closed=True)

# Optional: store classification for downstream layer assignment
contour_metadata.append({
    'contour': simplified,
    'curvature_class': profile.classification,
    'radius_stability': profile.radius_stability,
})
```

### 9.3 Expected Outcomes

| Contour Type | Current Behavior | Expected After |
|--------------|------------------|----------------|
| Body profile curves | Fragmented at thin strokes | Continuous with lower epsilon |
| Annotation text | Clean | Unchanged (same epsilon) |
| Dimension lines | Clean | Unchanged |
| Thin stroke fragments | Treated same as text | Identified, lower epsilon applied |

---

## 10. Risks and Mitigations

### 10.1 Performance Risk

**Risk:** Per-contour curvature analysis adds O(n) computation per contour.

**Mitigation:**
- Only analyze contours above minimum area threshold (already filtered)
- Use numpy vectorization for radius computation
- Cache results; curvature profile is computed once per contour

**Estimated impact:** <100ms additional per page at 200 DPI

### 10.2 False Classification Risk

**Risk:** Some annotation curves may be misclassified as profile curves.

**Mitigation:**
- Use area threshold: profile curves are typically >500px area
- Use position: profile curves are central, not in title block region
- Combine with existing layer classification; curvature is additive signal

### 10.3 Regression Risk

**Risk:** Changes to epsilon may affect currently-working PDFs.

**Mitigation:**
- A/B test against benchmark suite (Gibson-Melody-Maker, OM_acoustic_guitar_en, Classical-Santos-Hernandez)
- Add curvature-based classification as parallel path, gate behind feature flag
- Validate acceptance grades remain stable on known-good files

### 10.4 Scope Creep Risk

**Risk:** Curvature analysis becomes complex feature with many edge cases.

**Mitigation:**
- Define success criteria upfront: Dreadnought-MM.pdf achieves USABLE grade
- Time-box implementation to 3 days; if not converging, re-evaluate approach
- Do not attempt to solve ALL thin-stroke cases in v1

---

## 11. Next Steps

### 11.1 Immediate (This Sprint)

1. **Add curvature profiler** — `services/api/app/services/curvature_profiler.py`
   - Implement `compute_contour_curvature_profile()`
   - Implement `fit_circle_radius()` using existing radius math patterns
   - Add unit tests with synthetic contours

2. **Create benchmark harness**
   - Script that runs all test PDFs through pipeline
   - Reports acceptance grade, BODY count, curvature classification distribution
   - Baseline current behavior before changes

3. **Wire curvature to simplification**
   - Modify `edge_to_dxf.py` to use per-contour epsilon
   - Gate behind environment variable `VECTORIZER_CURVATURE_EPSILON=1`

### 11.2 Validation (Next Sprint)

4. **Run benchmark suite**
   - Compare before/after on: Dreadnought-MM, Melody-Maker, OM, Santos-Hernandez
   - Target: Dreadnought improves to USABLE; others maintain grade

5. **Tune thresholds**
   - Adjust stability threshold (0.5) based on real data
   - Adjust radius range (30-800mm) based on body curve analysis

6. **Remove feature flag**
   - If validation passes, enable by default
   - Document in CLAUDE.md

### 11.3 Future Enhancements

7. **Curvature-aware gap joining**
   - Current gap join creates straight LINE segments
   - Could use bi-arc fitting to create curved bridges
   - Uses `curvemath_biarc.py` infrastructure

8. **Adaptive threshold tuning**
   - Per-region block_size based on stroke weight detection
   - Would address fragmentation at threshold stage, not just simplification

---

## Appendix A: Files in Thin-Stroke Class

| File | Status | Notes |
|------|--------|-------|
| A003-Dreadnought-MM.pdf | Confirmed | Thin strokes, fragmented body outline |

## Appendix B: Files NOT in Thin-Stroke Class

| File | Grade | Notes |
|------|-------|-------|
| Gibson-Melody-Maker.pdf | PRODUCTION_READY | Excellent quality |
| OM_acoustic_guitar_en.pdf | USABLE | Good text fidelity |
| Classical-Santos-Hernandez-MM.pdf | USABLE | Standard stroke weights |

---

## Appendix C: Quick Reference

### Run Diagnostic Overlay
```python
from app.services.dual_pass_overlay import generate_layered_overlay

path, meta = generate_layered_overlay(
    "path/to/blueprint.png",
    target_height_mm=500.0,
    apply_gap_join=True,
)
print(meta)
```

### Check Acceptance Grade
```python
from app.services.layer_builder import evaluate_layered_acceptance

grade, details = evaluate_layered_acceptance(layered_entities)
print(f"Grade: {grade.value}")
print(f"BODY count: {details['body_count']}")
```

### Compute Local Radius (Manual Test)
```python
from app.instrument_geometry.neck.radius_profiles import compute_radius_drop_mm

# For a 12" fretboard radius at 21mm offset from center:
drop = compute_radius_drop_mm(304.8, 21.0)
print(f"Edge drop: {drop:.2f}mm")
```

---

*Document generated: 2026-04-14*  
*Last updated: 2026-04-14*
