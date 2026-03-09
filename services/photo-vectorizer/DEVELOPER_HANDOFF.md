# Photo Vectorizer V2 — Developer Handoff

> **Status:** Working prototype — NOT commercial-ready  
> **Rating:** 4/10 for production use  
> **Created:** March 9, 2026  
> **Repo origin:** `luthiers-toolbox/services/photo-vectorizer/`  
> **Target:** Standalone sandbox for isolated development

---

## What This Is

A 12-stage computer vision pipeline that takes a **photograph of a guitar** and extracts its body outline (and internal features) into **SVG + DXF vector files**. Designed for the Express tier — beginners and hobbyists who have a concept photo but no CAD drawings.

The pipeline also includes a **STEM Guitar grid zone classifier** that maps contour positions onto a 24×32 normalized body grid for position-aware feature identification.

---

## Files to Extract

```
photo_vectorizer_v2.py    # Main pipeline (~1,290 lines)
grid_classify.py          # Grid zone classifier (~380 lines)
__init__.py               # Package init (empty)
```

### Dependencies

```
opencv-python>=4.8
numpy>=1.24
Pillow>=10.0        # EXIF extraction
ezdxf>=0.18         # DXF R12 export
```

Optional (graceful fallback if missing):
```
rembg               # Neural background removal (better than GrabCut)
segment-anything    # SAM-based background removal (best quality)
PyMuPDF             # PDF input support
```

### Zero cross-service imports

The photo-vectorizer has **no imports from any other service** in the monorepo. The grid zone data from `services/blueprint-import/classifiers/grid_zone/` was embedded directly into `grid_classify.py`. It is fully standalone and can be extracted as-is.

---

## Pipeline Architecture

```
Photo In
  │
  ├── Stage 0:  Dark background detection (border pixel sampling)
  ├── Stage 1:  EXIF DPI extraction (Pillow)
  ├── Stage 2:  Input classification (photo vs blueprint vs scan)
  ├── Stage 3:  Perspective correction (quad detection + warp)
  ├── Stage 4:  Background removal (GrabCut / rembg / SAM / threshold)
  ├── Stage 5:  Edge detection (Canny + Sobel + Laplacian fusion)
  ├── Stage 6:  Reference object detection (coins via HoughCircles, cards via contour)
  ├── Stage 7:  Scale calibration (priority chain: user > ref obj > EXIF > spec > assumed)
  ├── Stage 8:  Contour assembly + dimension-based classification
  ├── Stage 8.5: Grid zone re-classification (position-based, merges with dimension)
  ├── Stage 9:  Convert to mm coordinates (centered on body)
  ├── Stage 10: (Reserved — confidence heatmap / manual correction hooks)
  └── Stage 11: Export (SVG, DXF R12, JSON)
      │
      Photo Out: SVG + DXF + optional JSON + debug images
```

### Data flow through the pipeline

```
cv2.imread() → np.ndarray
  → detect_dark_background() → bool (invert if dark)
  → EXIFExtractor.get_dpi() → Optional[float]
  → InputClassifier.classify() → (InputType, confidence, metadata)
  → PerspectiveCorrector.correct() → (image, corrected_bool)
  → BackgroundRemover.remove() → (foreground, alpha_mask, method_str)
  → PhotoEdgeDetector.detect() → edge_binary_image
  → ScaleCalibrator.calibrate() → CalibrationResult(mm_per_px, source, conf)
  → ContourAssembler.assemble() → List[FeatureContour]
  → PhotoGridClassifier.classify_contour_px() → GridClassification per contour
  → merge_classifications() → (final_feature, confidence, reason) per contour
  → _to_mm() + cv2.approxPolyDP() → simplified mm-space contours
  → write_svg() / write_dxf() / write_features_json()
```

---

## Key Data Structures

### FeatureContour
```python
@dataclass
class FeatureContour:
    points_px: np.ndarray              # Raw pixel contour
    points_mm: Optional[np.ndarray]    # After scale conversion
    feature_type: FeatureType          # body_outline, neck_pocket, pickup_route, etc.
    confidence: float                  # 0–1
    parent_idx: int                    # Hierarchy parent (-1 = root)
    child_indices: List[int]
    area_px: float
    perimeter_px: float
    circularity: float                 # 4πA/P² (1.0 = perfect circle)
    aspect_ratio: float                # max(w,h) / min(w,h)
    solidity: float                    # area / convex_hull_area
    bbox_px: Tuple[int, int, int, int] # (x, y, w, h)
    hash_id: str                       # MD5 of contour bytes
    manually_corrected: bool
    grid_zone: Optional[str]           # Grid zone name after Stage 8.5
    grid_confidence: float             # Grid classification confidence
    grid_notes: List[str]              # Grid debug notes
```

### PhotoExtractionResult
```python
@dataclass
class PhotoExtractionResult:
    source_path: str
    input_type: InputType
    output_dxf: Optional[str]
    output_svg: Optional[str]
    output_json: Optional[str]
    features: Dict[FeatureType, List[FeatureContour]]
    body_contour: Optional[FeatureContour]
    body_dimensions_mm: Tuple[float, float]
    body_dimensions_inch: Tuple[float, float]
    calibration: Optional[CalibrationResult]
    bg_method_used: str
    perspective_corrected: bool
    dark_background_detected: bool
    grid_reclassified: int             # Count of contours changed by grid
    grid_overlay_path: Optional[str]   # Debug overlay image path
    warnings: List[str]
    processing_time_ms: float
    debug_images: Dict[str, str]
```

### GridClassification (from grid_classify.py)
```python
@dataclass
class GridClassification:
    primary_zone: Optional[GridZone]
    primary_category: str       # "NECK_POCKET", "BRIDGE_ROUTE", "BODY_OUTLINE", etc.
    mapped_feature: str         # Maps to FeatureType values
    all_zones: List[ZoneMatch]  # All overlapping zones with overlap %
    symmetry_score: float       # 0–1, 1.0 = centered on body axis
    grid_confidence: float      # 0–1
    notes: List[str]
```

---

## STEM Guitar Grid Zone System

The grid divides a guitar body bounding box into 10 normalized zones (0→1 coordinate system):

| Zone | X range | Y range | Priority | Maps to |
|------|---------|---------|----------|---------|
| NECK_POCKET | 0.417–0.583 | 0.0–0.25 | 10 | neck_pocket |
| UPPER_BOUT_LEFT | 0.0–0.417 | 0.0–0.188 | 5 | body_outline |
| UPPER_BOUT_RIGHT | 0.583–1.0 | 0.0–0.188 | 5 | body_outline |
| WING_LIMIT_LEFT | 0.0–0.125 | 0.188–0.813 | 3 | body_outline |
| WING_LIMIT_RIGHT | 0.875–1.0 | 0.188–0.813 | 3 | body_outline |
| BRIDGE_ZONE | 0.375–0.625 | 0.688–0.813 | 8 | bridge_route |
| BODY_CANVAS | 0.125–0.875 | 0.188–1.0 | 1 | body_outline (catch-all) |
| WAIST_LEFT | 0.125–0.35 | 0.35–0.55 | 2 | body_outline |
| WAIST_RIGHT | 0.65–0.875 | 0.35–0.55 | 2 | body_outline |
| LOWER_BOUT | 0.125–0.875 | 0.813–1.0 | 2 | body_outline |

**Coordinate system:** Origin (0,0) = top-left of body bounding box, Y increases downward, centerline at x=0.5.

**Classification flow:** Contour bbox (px) → normalize to body bbox (0→1) → calculate overlap with each zone → pick highest-priority zone with ≥5% overlap → merge with dimension-based classification.

**Merge rules** (in `merge_classifications()`):
1. If grid + dimension **agree** → boost confidence by 0.15
2. If grid says high-priority zone (neck_pocket, bridge_route) with >0.5 confidence → **grid overrides**
3. If grid says body_outline but dimension identified something specific with >0.5 confidence → **dimension wins** (internal features are small, often inside BODY_CANVAS)
4. If dimension says unknown and grid has a real answer at >0.3 confidence → **grid resolves**
5. Fallback: pick whichever has higher confidence

---

## Instrument Specs Database

```python
INSTRUMENT_SPECS = {
    "stratocaster": {"body": (406, 325), ...},
    "telecaster":   {"body": (406, 325), ...},
    "les_paul":     {"body": (450, 340), ...},
    "es335":        {"body": (500, 420), ...},
    "dreadnought":  {"body": (520, 400), ...},
    "smart_guitar": {"body": (444.5, 368.3), ...},  # Canonical from smart_guitar_v1.json
    "reference_objects": {
        "us_quarter": (24.26, 24.26),
        "credit_card": (85.6, 53.98),
        "business_card": (88.9, 50.8),
    },
}
```

Body tuples are `(length_mm, width_mm)`. The smart_guitar spec was corrected from (500, 370) to (444.5, 368.3) to match the canonical repo spec at `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json`.

---

## Observed Test Results

### Test 1: Smart Guitar_1.png (real photo, dark background)

| Metric | Expected | Actual |
|--------|----------|--------|
| Body dimensions | 444.5 × 368.3 mm | **51.6 × 76.5 mm** |
| Scale source | instrument_spec | **assumed_dpi (300)** |
| Total contours | Many | **4** |
| Grid reclassified | Expected some | **1** |
| Layers | Multiple features | BODY_OUTLINE, NECK_POCKET (wrong), UNKNOWN |

**Root cause:** No reference object in photo, no EXIF DPI → fell back to assumed 300 DPI → 0.085 mm/px. At that scale, the body measures ~77mm so the FeatureClassifier sees everything as tiny and can't match any rule except "UNKNOWN". The spec-based calibration path sets `mm_per_px=0.0` initially (it needs the body contour height to compute scale), but the FeatureClassifier already ran with the wrong mm/px during contour assembly. The post-hoc refinement fixes mm/px but doesn't re-classify.

**The NECK_POCKET contour** is actually the inner edge trace of the body outline — same shape, slightly smaller bbox. Not a neck pocket at all. The grid tagged it `grid_zone=UPPER_BOUT` (correct position) but the merge kept the dimension label because dimension confidence (0.80) exceeded grid confidence (0.04).

### Test 2: ChatGPT Image (AI-generated guitar, dark background)

| Metric | Expected | Actual |
|--------|----------|--------|
| Body dimensions | 444.5 × 368.3 mm | **76.7 × 37.1 mm** |
| Scale source | instrument_spec | **reference_object (false positive)** |
| Total contours | Many | **7** |
| Grid reclassified | Expected some | **0** |

**Root cause:** `ReferenceObjectDetector` false-triggered on a circular feature in the AI-generated image (probably a knob or rendering artifact), returning "US quarter" at 0.5 confidence. Since reference_object has higher priority than instrument_spec in the calibration chain, the spec was never used. Body measures ~77mm at this scale.

The grid correctly placed contours (one in NECK_POCKET zone centered on axis, several in WAIST_LEFT, one in BRIDGE_ZONE), but at 7 mm/px equivalent all dimension thresholds were wrong so everything classified as UNKNOWN or JACK_ROUTE.

---

## Blocking Issues (Priority Order)

### BLOCKER 1: Scale calibration pipeline is broken

**The problem:** Scale is computed BEFORE contour assembly, but the best scale source (instrument spec) needs the body contour's pixel height to compute mm/px. Current flow:

```
calibrate() → mm_per_px (often wrong at this point)
  → assemble(edges, alpha, mm_per_px) → contours classified with WRONG scale
  → find body contour
  → refine mm_per_px using body height vs spec  ← TOO LATE, classification already done
```

**The fix — two-pass calibration:**

```
Pass 1: assemble contours with mm_per_px=1.0 (pixel-space only, no classification)
  → find body contour → get body_height_px
  → if spec_name: mm_per_px = spec_body_mm / body_height_px
  → else: use reference obj / EXIF / assumed DPI

Pass 2: re-classify all contours using CORRECT mm_per_px
  → then run grid re-classification
```

**Effort:** Small (restructure ~30 lines in `extract()`).  
**Impact:** Fixes the #1 problem — every output will have correct dimensions when a spec is provided.

### BLOCKER 2: Reference object detector has high false-positive rate

**The problem:** `ReferenceObjectDetector.detect()` uses `cv2.HoughCircles` with loose thresholds (`param2=30, minRadius=20, maxRadius=200`). Any vaguely circular feature triggers it — guitar knobs, tuners, body curves, AI artifacts. When it fires, it overrides the instrument spec (higher priority in calibration chain).

**The fix:**
1. Tighten HoughCircles parameters (`param2=50`, `minRadius=30`, `maxRadius=100`)
2. Add circularity validation on the detected region (crop, check actual roundness)
3. When `spec_name` is explicitly provided by the user, demote reference_object below instrument_spec in the priority chain. User explicitly saying "this is a smart guitar" should outrank a speculative circle detection.
4. Add size-ratio sanity check: if detected "quarter" diameter is >15% of body height, it's not a quarter.

**Effort:** Small.  
**Impact:** Eliminates the ChatGPT image failure mode and any casually-shot guitar photo with knobs visible.

### BLOCKER 3: Contour deduplication missing

**The problem:** Body outline produces both an outer and inner edge trace. Both survive assembly with nearly identical bboxes. The inner trace gets misclassified as NECK_POCKET or UNKNOWN because it's slightly smaller.

**The fix:**
1. After assembly, compare all contour bboxes pairwise
2. If two contours have IoU > 0.85 (bounding box intersection over union), keep only the larger one
3. Alternatively, use contour hierarchy: if a contour's parent is the body and it spatially covers >80% of the body bbox, discard it as a duplicate trace

**Effort:** Small (~20 lines).  
**Impact:** Eliminates the false NECK_POCKET ghost contour.

### BLOCKER 4: FeatureClassifier is too simplistic for real photos

**The problem:** Classification is a single if/else chain on mm bounding box dimensions. Overlapping size ranges cause misclassification. No shape analysis beyond basic circularity. Works okay for clean blueprints where cavities are clearly defined, fails on photos where edge detection produces noisy, fragmented contours.

**What the classifier has:**
- Bounding box width/height in mm
- Circularity (4πA/P²)
- That's it

**What it needs (incremental additions):**
1. **Hu moments** — rotation/scale-invariant shape descriptors. A neck pocket and a control cavity have very different Hu signatures even at similar sizes.
2. **Solidity + convexity defects** — already computed in `ContourAssembler` but never passed to the classifier
3. **Relative position via grid** — partially done, but the merge function should be more aggressive when scale is uncertain
4. **Contour hierarchy depth** — a cavity inside a body has hierarchy depth 1; a noise trace inside another contour has depth 2+
5. **Aspect ratio constraints per feature type** — a neck pocket is always taller than wide; a pickup route is always wider than tall

**Effort:** Medium.  
**Impact:** Significantly reduces misclassification. Combined with grid, this would give a two-signal (shape + position) classifier that's much more robust.

---

## Non-Blocking Issues

### Background removal quality

GrabCut works for clean studio photos with solid backgrounds. Real-world photos have hands, stands, straps, reflections, wood grain texture. When backgrounds are complex, the alpha mask is noisy and edge detection picks up background features as contours.

**Mitigation:** `rembg` (neural net) handles this much better. It's already supported in the pipeline — just needs to be installed. For production, make `rembg` the default when available, with GrabCut as fallback.

### Perspective correction false-triggers

`PerspectiveCorrector` looks for quadrilaterals >15% of image area. On images with rectangular backgrounds (tables, floors), it can warp the guitar into the wrong perspective. The check for "did the quad actually improve things" is missing.

**Mitigation:** Add a pre/post comparison — if the corrected image has fewer edge pixels or a smaller largest contour area, undo the correction.

### Edge detection over-sensitivity

The three-method fusion (Canny + Sobel + Laplacian OR'd together) produces very dense edge maps. The ChatGPT image yielded 98,481 edge pixels but only 7 surviving contours from 453. Most raw contours are too small (< min_area_px) or are edge fragments.

**Mitigation:** Weight the fusion — Canny should dominate, with Sobel/Laplacian only contributing where Canny gaps exist. Or threshold each method independently and AND the top two instead of OR'ing all three.

### Grid confidence formula is too conservative

Grid confidence = `overlap × (zone.priority / 10)`. For small internal features sitting inside the large BODY_CANVAS zone, the canvas always has higher overlap. Even when a contour sits dead-center in NECK_POCKET zone, if it also overlaps BODY_CANVAS (which it will, since canvas is a superset), the confidence is diluted.

**Fix:** The priority-based sorting already handles this (NECK_POCKET priority=10 > BODY_CANVAS priority=1), but the confidence value itself should also reflect containment: if a contour is fully inside a high-priority zone, confidence should be near 1.0 regardless of canvas overlap.

### Processing time

~55 seconds for a 1536×1024 image. Most of the time is in GrabCut (iterative graph-cut algorithm). For a web product, this needs to be <5 seconds.

**Mitigation:** Downscale image before GrabCut (to 800px max dimension), compute mask, then upscale mask to original resolution. GrabCut time is O(n²) on pixel count — halving resolution gives ~4x speedup.

---

## The Grid Concept — Why It Matters

The key insight: **a guitar body has predictable anatomy.** The neck pocket is always top-center. The bridge is always lower-center. Pickups are always between them. Waist cutaways are always on the sides.

By normalizing any contour's position to the body bounding box (0→1), we can use the STEM Guitar grid to say "this contour sits in the neck pocket zone" regardless of image scale, rotation, or resolution. This is a **second classification signal independent of dimension**.

When dimension classification is uncertain (wrong scale, overlapping size ranges), grid position can resolve ambiguity. When the grid is uncertain (small feature inside large BODY_CANVAS), dimensions can resolve. The two together are much stronger than either alone.

**Current state:** The grid works correctly — it assigns the right zones. The merge function is the weak link. It trusts dimension confidence too much and grid confidence too little, especially when the scale pipeline is broken (which inflates dimension confidence on wrong answers).

**Fix:** When `CalibrationResult.confidence < 0.5` (i.e., scale is uncertain), the merge should weight grid position more heavily than dimension classification. A contour that sits in the bridge zone on the grid is very likely a bridge feature, even if the broken scale says it's "jack route" sized.

---

## Recommended Next Steps (in order)

### Step 1: Two-pass calibration (fixes Scale)
Restructure `extract()` so contour assembly runs in pixel-space first, then scale is computed from body height + spec, then classification runs with correct mm/px. This alone fixes both test failures.

### Step 2: Dedup concentric contours
After assembly, remove contours whose bbox IoU with the body contour exceeds 0.85. Eliminates the phantom inner-edge traces.

### Step 3: Demote reference_object when spec is provided
If the user explicitly passes `spec_name`, trust it over speculative HoughCircles detections. Reorder the priority chain in `ScaleCalibrator.calibrate()`.

### Step 4: Scale-aware merge weighting
In `merge_classifications()`, check `CalibrationResult.confidence`. When scale confidence is low, increase grid weight in the merge formula.

### Step 5: Body-outline-only mode for Express
For the Express product tier, skip internal feature classification entirely. Just extract and export the body outline as a single clean layer. This is the simplest path to a commercially useful output — a hobbyist with a guitar photo gets a cuttable body template.

### Step 6: Make rembg the default
When available, rembg produces dramatically better segmentation than GrabCut on real photos. Change the `AUTO` selection to prefer rembg > SAM > GrabCut > threshold.

### Step 7: Shape descriptors in FeatureClassifier
Add Hu moments, solidity, and hierarchy depth to the classifier. This doesn't need ML — simple threshold ranges per feature type using these richer descriptors would significantly improve accuracy.

---

## CLI Usage

```bash
# Basic extraction
python photo_vectorizer_v2.py "photo.jpg"

# With instrument spec for scale
python photo_vectorizer_v2.py "guitar.png" --spec smart_guitar

# With known dimension
python photo_vectorizer_v2.py "guitar.png" --mm 444.5 --px 850

# Full debug output
python photo_vectorizer_v2.py "guitar.png" --spec smart_guitar --debug -v

# All options
python photo_vectorizer_v2.py "guitar.png" \
    -o ./output \
    --spec stratocaster \
    --bg rembg \
    --no-perspective \
    --formats svg dxf json \
    --debug -v
```

### Debug images produced (when `--debug` flag is set)
```
{stem}_00_original.jpg        # Input after dark-bg inversion
{stem}_01_perspective.jpg     # After perspective correction (if applied)
{stem}_02_foreground.jpg      # After background removal
{stem}_03_alpha.png           # Binary foreground mask
{stem}_04_edges.png           # Fused edge detection output
{stem}_05_grid_overlay.jpg    # Grid zones + contour classifications
{stem}_photo_v2.svg           # Vector output
{stem}_photo_v2.dxf           # DXF R12 output
```

---

## Relationship to Upstream

### Origin: luthiers-toolbox monorepo

The photo-vectorizer sits at `services/photo-vectorizer/` in the Golden Master. It has **zero runtime dependencies** on the monorepo — no imports from `services/api/`, `services/blueprint-import/`, or any other service.

### Related systems (for context, not imported)

| System | Location | Relationship |
|--------|----------|-------------|
| Blueprint Vectorizer Phase 3 | `services/blueprint-import/vectorizer_phase3.py` | Older, blueprint-focused vectorizer. ML classifier, OCR. Different input type. |
| Grid Zone Classifier | `services/blueprint-import/classifiers/grid_zone/` | Original grid system. `grid_classify.py` embeds a copy of the zone data and classifier logic. |
| Smart Guitar Spec | `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json` | Canonical body dimensions (444.5 × 368.3 × 44.45 mm). Photo vectorizer's `INSTRUMENT_SPECS["smart_guitar"]` was corrected to match. |

### Extraction checklist

1. Copy `services/photo-vectorizer/{photo_vectorizer_v2.py, grid_classify.py, __init__.py}` to new sandbox
2. `pip install opencv-python numpy Pillow ezdxf` (core deps)
3. `pip install rembg` (recommended, better background removal)
4. Verify: `python photo_vectorizer_v2.py --help`
5. Test: `python photo_vectorizer_v2.py some_guitar_photo.jpg --spec stratocaster --debug -v`

No monorepo imports. No config files needed. No database. No API server. Fully self-contained.
