# Vectorizer Upgrade - Developer Handoff

**Document Type:** Annotated Executive Summary
**Created:** 2026-03-06
**Status:** Ready for Implementation
**Priority:** High
**Prerequisite:** BLUEPRINT_VECTORIZER_INTEGRATION_HANDOFF.md

---

## Executive Summary

The current Phase 2 vectorizer (`phase2_router.py`) uses basic OpenCV edge detection. Testing on 33 guitar blueprints showed **0% good detections** - the system finds wrong elements (logos, legends) instead of guitar bodies.

**Goal:** Upgrade the vectorizer with multi-view detection, intelligent contour selection, and the advanced `vectorizer_phase3.py` capabilities.

---

## Current Problems

### Test Results (33 Blueprints)

| Result | Count | Root Cause |
|--------|-------|------------|
| Good | 0 | - |
| Small Contour | 11 | Found logo/legend instead of body |
| Undersized | 22 | PPI estimation wrong |

> **Annotation:** The vectorizer grabs the largest contour, but in multi-view PDFs, that's often not the guitar body. Need smarter selection.

### Current Phase 2 Pipeline (Basic)

```python
# phase2_router.py - Current approach
1. Canny edge detection (thresholds: 50, 150)
2. Find contours
3. Take largest contour  # <-- PROBLEM: Often wrong element
4. Export to DXF
```

### Problems with Current Approach

1. **No view classification** - Doesn't know front view from side view
2. **Largest != Body** - Legends, borders, title blocks are often larger
3. **No aspect ratio filtering** - Guitars have specific proportions (~1.3:1)
4. **No calibration integration** - Exports at arbitrary scale
5. **No confidence scoring** - User doesn't know if result is trustworthy

---

## Upgrade Strategy

### Strategy 1: Multi-View Detection (HIGH PRIORITY)

Use GridZoneClassifier to identify views in multi-view PDFs:

```python
from classifiers.grid_zone import GridZoneClassifier

classifier = GridZoneClassifier()
zones = classifier.classify(image)

# zones = [
#   {"type": "body_front", "bbox": (x, y, w, h), "confidence": 0.92},
#   {"type": "neck_front", "bbox": (x, y, w, h), "confidence": 0.88},
#   {"type": "side_view", "bbox": (x, y, w, h), "confidence": 0.76},
# ]

# Select body_front zone for body extraction
body_zone = next(z for z in zones if z["type"] == "body_front")
```

> **Annotation:** GridZoneClassifier was built and tested (89% confident on 28 blueprints). Just needs to be wired in.

### Strategy 2: Aspect Ratio Filtering (MEDIUM PRIORITY)

Guitar bodies have predictable aspect ratios:

| Type | Aspect Ratio (L:W) |
|------|--------------------|
| Stratocaster | 1.30 - 1.40 |
| Les Paul | 1.25 - 1.35 |
| Explorer | 1.10 - 1.20 |
| Flying V | 1.00 - 1.15 |

```python
def is_likely_body_contour(contour):
    x, y, w, h = cv2.boundingRect(contour)
    aspect = max(h, w) / min(h, w)
    return 1.0 < aspect < 1.8  # Guitar body range
```

### Strategy 3: Contour Scoring (MEDIUM PRIORITY)

Rank contours by multiple factors:

```python
def score_contour(contour, image_shape):
    area = cv2.contourArea(contour)
    x, y, w, h = cv2.boundingRect(contour)

    # Factor 1: Size (should be significant portion of image)
    area_ratio = area / (image_shape[0] * image_shape[1])
    size_score = min(area_ratio * 10, 1.0)  # 10% of image = 1.0

    # Factor 2: Aspect ratio (should be guitar-like)
    aspect = max(h, w) / min(h, w)
    aspect_score = 1.0 if 1.1 < aspect < 1.6 else 0.5

    # Factor 3: Position (body usually centered)
    cx, cy = x + w/2, y + h/2
    center_dist = abs(cx - image_shape[1]/2) / image_shape[1]
    position_score = 1.0 - center_dist

    # Factor 4: Solidity (body should be solid, not hollow)
    hull = cv2.convexHull(contour)
    solidity = area / cv2.contourArea(hull)
    solidity_score = solidity

    return (size_score * 0.3 +
            aspect_score * 0.3 +
            position_score * 0.2 +
            solidity_score * 0.2)
```

### Strategy 4: OCR Dimension Extraction (HIGH IMPACT)

Many blueprints have printed dimensions. Extract with Tesseract:

```python
import pytesseract

def extract_dimension_text(image):
    # OCR the image
    text = pytesseract.image_to_string(image)

    # Find dimension patterns
    patterns = [
        r'(\d+\.?\d*)\s*"',           # 25.5"
        r'(\d+\.?\d*)\s*inch',        # 25.5 inch
        r'(\d+\.?\d*)\s*mm',          # 648mm
        r'scale.*?(\d+\.?\d*)',       # scale: 25.5
    ]

    dimensions = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dimensions.extend(matches)

    return dimensions
```

> **Annotation:** Requires Tesseract OCR engine installed on system. pytesseract Python package already installed.

### Strategy 5: Template Matching (LONG-TERM)

Pre-compute body silhouette templates for common models:

```python
TEMPLATES = {
    "stratocaster": load_template("templates/strat_silhouette.png"),
    "les_paul": load_template("templates/lp_silhouette.png"),
    "telecaster": load_template("templates/tele_silhouette.png"),
}

def match_template(contour):
    for name, template in TEMPLATES.items():
        score = cv2.matchShapes(contour, template, cv2.CONTOURS_MATCH_I1, 0)
        if score < 0.1:  # Good match
            return name, score
    return None, 1.0
```

---

## Implementation Plan

### Phase A: Wire Existing Modules (This Session)

1. **Create calibration_router.py** - Expose calibration endpoints
2. **Update phase2_router.py** - Import and use calibration
3. **Add GridZoneClassifier** - Use for view detection
4. **Add contour scoring** - Replace "largest contour" logic

### Phase B: Add New Capabilities (Next Session)

1. **Install Tesseract** - Enable OCR extraction
2. **Add OCR endpoint** - Extract printed dimensions
3. **Build CalibrationPanel.vue** - UI for manual calibration
4. **Add template matching** - For common guitar models

### Phase C: Polish and Test (Future)

1. **Re-run 33 blueprint test** - Measure improvement
2. **Add confidence thresholds** - Warn user when uncertain
3. **Build template library** - Common guitar silhouettes
4. **Add undo/retry** - Let user correct bad detections

---

## Files to Modify

### Backend Changes

| File | Change |
|------|--------|
| `routers/blueprint/calibration_router.py` | **NEW** - Calibration endpoints |
| `routers/blueprint/phase2_router.py` | Add calibration + contour scoring |
| `routers/blueprint/__init__.py` | Register calibration router |
| `routers/blueprint/constants.py` | Add calibration imports |

### Frontend Changes

| File | Change |
|------|--------|
| `components/blueprint/CalibrationPanel.vue` | **NEW** - Calibration UI |
| `components/blueprint/Phase2VectorizationPanel.vue` | Add calibration display |
| `composables/useBlueprintWorkflow.ts` | Add calibration state |
| `views/BlueprintLab.vue` | Wire CalibrationPanel |

---

## Code Snippets for Implementation

### Upgraded Contour Selection

```python
def select_best_contour(contours, image_shape):
    """Select the most likely guitar body contour."""
    if not contours:
        return None

    scored = []
    for contour in contours:
        # Skip tiny contours
        area = cv2.contourArea(contour)
        if area < image_shape[0] * image_shape[1] * 0.01:
            continue

        score = score_contour(contour, image_shape)
        scored.append((score, contour))

    if not scored:
        return max(contours, key=cv2.contourArea)  # Fallback

    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[0][1]
```

### Calibration-Aware Export

```python
def export_dxf_calibrated(contours, calibration, output_path):
    """Export DXF with real-world dimensions."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Convert pixels to mm using calibration
    scale = 25.4 / calibration.ppi  # mm per pixel

    for contour in contours:
        points = [(p[0][0] * scale, p[0][1] * scale) for p in contour]
        msp.add_lwpolyline(points, close=True)

    doc.saveas(output_path)
```

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Good detections (33 blueprints) | 0% | >50% |
| Correct body identification | ~30% | >80% |
| Dimension accuracy (with calibration) | Unknown | Within 5% |
| User override rate | N/A | <20% |

---

## Dependencies

### Required (Already Installed)
- opencv-python
- ezdxf
- numpy
- Pillow

### Required (Need Installation)
- **Tesseract OCR** - For dimension text extraction
  ```bash
  # Windows
  winget install UB-Mannheim.TesseractOCR
  ```

### Optional
- scikit-image (for advanced morphology)
- scipy (for curve fitting)

---

## References

- `services/blueprint-import/calibration/` - Calibration module
- `services/blueprint-import/classifiers/grid_zone/` - Zone classifier
- `services/blueprint-import/vectorizer_phase3.py` - Advanced vectorizer
- `services/blueprint-import/CALIBRATION_REPORT.md` - Test results
- `docs/ORIGIN_STORY.md` - Why accuracy matters

---

*Production Shop - Vectorizer Upgrade Handoff*
