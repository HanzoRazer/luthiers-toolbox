# Edge Detection Strategy Handoff

## Problem Statement

The current vectorizer produces body outlines with **148 open endpoints** - disconnected curve segments that should form a single closed loop. These gaps are **structural**, not pixel-level artifacts that morphological closing can fix.

### Current Pipeline (vectorizer_phase3.py)

```
Image → Canny/Adaptive Threshold → Morphological Close → Find Contours → Classify → Export
```

**Why it fails:**

1. Edge detection finds edges only where there's sufficient gradient
2. Blueprint paper texture, folds, or faded ink create areas with no detectable edge
3. Morphological closing bridges small gaps (1-15px) but not large ones (50-200px)
4. Result: Multiple disconnected curve segments instead of one closed body outline

### Evidence from cuatro puertoriqueño.pdf

| Metric | Value |
|--------|-------|
| Body segments | 15,703 |
| Open endpoints | 148 |
| Gap-bridging segments filtered | 78 (segments >10mm) |
| Structural gaps | ~74 (148 endpoints / 2) |

The 74 structural gaps represent areas where **no edge was detected at all**.

---

## The Paradigm Shift: From Edge Detection to Region Segmentation

### Current Approach: "Find edges, hope they connect"

```
[Image] → [Edge pixels] → [Contours] → [Body outline]
           ↑ FAILS HERE
           Edges don't exist where ink faded or paper textured
```

### Proposed Approach: "Find the body region, extract its boundary"

```
[Image] → [Body REGION mask] → [Boundary of region] → [Body outline]
           ↑ DIFFERENT QUESTION
           "Where is the guitar body?" not "Where are the edges?"
```

---

## Three Alternative Strategies

### Strategy A: Foreground Segmentation + Boundary Extraction

**Concept:** The guitar body is a distinct foreground region against the paper background. Segment it as a filled region first, then extract the boundary.

**Implementation:**

```python
def extract_body_via_segmentation(image):
    """
    Instead of finding edges, find the REGION that is the body.
    """
    # 1. Background removal (already exists: GrabCut, threshold)
    fg_mask = remove_background(image)  # Binary: body=255, background=0

    # 2. Fill holes in the foreground mask
    #    This closes internal gaps that edge detection misses
    filled = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE,
                               kernel=np.ones((25, 25), np.uint8))

    # 3. Extract boundary of the filled region
    #    This is guaranteed to be a CLOSED contour
    contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_NONE)

    # 4. The largest contour IS the body outline - fully closed
    body_contour = max(contours, key=cv2.contourArea)

    return body_contour  # Guaranteed: 0 open endpoints
```

**Why this works:**
- Segmentation asks "is this pixel body or background?" - a fill question
- Boundary extraction from a filled region is always closed
- No edge signal needed - works even where ink faded

**Trade-off:**
- Loses fine edge detail (smooths over small features)
- Need to combine with edge-based detail extraction

---

### Strategy B: Active Contours (Snakes)

**Concept:** Start with a rough closed shape and evolve it to fit the detected edges. The contour stays closed throughout evolution.

**Implementation:**

```python
from skimage.segmentation import active_contour

def extract_body_via_snake(image, edges):
    """
    Initialize a closed contour and evolve it to fit edges.
    """
    # 1. Initialize with bounding ellipse of detected body region
    #    (from current BodyIsolator output)
    init_contour = create_ellipse_contour(body_bbox, n_points=500)

    # 2. Create edge potential field
    #    Edges attract the contour; smooth areas repel
    edge_potential = cv2.GaussianBlur(edges, (5, 5), 0)

    # 3. Evolve the contour
    #    alpha: elasticity (keeps contour smooth)
    #    beta: rigidity (prevents sharp corners)
    #    gamma: attraction to edges
    final_contour = active_contour(
        edge_potential,
        init_contour,
        alpha=0.01,  # Low elasticity - follow edges closely
        beta=0.1,    # Some rigidity - smooth over small gaps
        gamma=0.01,  # Edge attraction strength
        max_iterations=2500
    )

    return final_contour  # Guaranteed closed (it started closed)
```

**Why this works:**
- Contour is closed by construction
- Gaps in edges are smoothed over by contour rigidity (beta parameter)
- Fine detail preserved where edges exist

**Trade-off:**
- Sensitive to initialization
- Can get stuck in local minima
- Slower than direct contour extraction

---

### Strategy C: Multi-Scale Edge Fusion

**Concept:** Detect edges at multiple scales and combine them. Large-scale edges bridge gaps; small-scale edges preserve detail.

**Implementation:**

```python
def extract_body_multiscale(image):
    """
    Combine edge detection at multiple scales.
    """
    scales = [1.0, 0.5, 0.25]  # Original, half, quarter resolution
    edge_maps = []

    for scale in scales:
        # Resize image
        scaled = cv2.resize(image, None, fx=scale, fy=scale)

        # Detect edges (Canny thresholds adjust with scale)
        edges = cv2.Canny(scaled, 50 * scale, 150 * scale)

        # Resize edges back to original size
        edges_full = cv2.resize(edges, (image.shape[1], image.shape[0]))
        edge_maps.append(edges_full)

    # Combine: OR operation preserves edges from all scales
    combined = np.zeros_like(edge_maps[0])
    for em in edge_maps:
        combined = cv2.bitwise_or(combined, em)

    # Large-scale edges bridge gaps that small-scale missed
    # Small-scale edges preserve fine detail

    return combined
```

**Why this works:**
- Small gaps invisible at 0.25x scale become bridged
- Fine detail preserved at 1.0x scale
- Combined edge map has fewer gaps

**Trade-off:**
- Still edge-based, still may have some gaps
- Needs careful threshold tuning per scale

---

## Recommended Implementation Order

### Phase 1: Strategy A (Segmentation) - Immediate Win

**Implement first** because:
- Guarantees closed contour (0 open endpoints)
- Minimal code change - reuse existing background removal
- Fast to implement and test

**Integration point:**
```python
# In Phase3Vectorizer.extract(), after body isolation:

if use_segmentation_for_body:
    # New path: segment → boundary
    body_contour = extract_body_via_segmentation(fg_mask)
else:
    # Existing path: edge detect → contours
    body_contour = extract_via_edges(image)
```

**Add feature flag:** `--body-method segmentation|edges|hybrid`

### Phase 2: Hybrid Approach

Combine segmentation (closed boundary) with edge detection (fine detail):

```python
def extract_body_hybrid(image, fg_mask, edges):
    """
    1. Get closed boundary from segmentation
    2. Refine boundary using edge attraction
    3. Preserve fine detail from edges
    """
    # Closed base contour
    base_contour = extract_body_via_segmentation(fg_mask)

    # Refine using edges (snap to nearby edges)
    refined = snap_to_edges(base_contour, edges, max_distance=5)

    return refined
```

### Phase 3: Strategy B (Active Contours) - If Needed

Only if segmentation doesn't capture enough detail. More complex but more accurate.

---

## Files to Modify

| File | Change |
|------|--------|
| `vectorizer_phase3.py` | Add `extract_body_via_segmentation()` function |
| `vectorizer_phase3.py` | Add `--body-method` CLI argument |
| `vectorizer_phase3.py` | Branch in `extract()` method based on body-method |
| `CLAUDE.md` | Document new body extraction strategy |

## Test Cases

1. **cuatro puertoriqueño.pdf** - Current: 148 open endpoints, Target: 0
2. **Gibson Explorer blueprint** - Verify complex shapes work
3. **Clean blueprint (no texture)** - Verify no regression on easy cases

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Open endpoints | 148 | **0** |
| Max segment | 9.9mm | <10mm |
| Segment count | 15,703 | >5,000 |
| Bounds accuracy | 257×500mm | ±5% |

---

## Reference: Current Code Locations

| Function | Line | Purpose |
|----------|------|---------|
| `BodyIsolator.isolate()` | ~1050 | Finds body region bbox |
| `extract_dark_lines()` | ~1485 | Edge detection |
| `extract_auto()` | ~1521 | Combined edge extraction |
| `assemble_body_and_details()` | ~1553 | Combines body + detail masks |
| `export_to_dxf()` | ~2284 | Exports to DXF |

## Contact

Questions: See `CLAUDE.md` vectorizer architecture section.
