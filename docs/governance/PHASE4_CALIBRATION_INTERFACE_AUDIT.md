# Phase 4 & Calibration Interface Audit

**Date:** 2026-05-17
**Sprint:** IBG Morphology Harvest 1B-FIX
**Purpose:** Assess integration readiness before adapter wiring

---

## Executive Summary

| System | Status | Classification |
|--------|--------|----------------|
| Phase 4 | Implemented, API-wired | `implemented_needs_phase3` |
| Calibration | Implemented, standalone | `production_ready` |
| Phase 3 | Required dependency | `production_dependency` |

**Key Finding:** Phase 4 dimension linking is operational but depends on Phase 3 vectorizer for extraction. Phase 4 does NOT own contour geometry — it links OCR text to geometry from Phase 3.

---

## Section A: Phase 4 Dimension Linker

### 1. Does Phase 4 exist?

**YES** — Located at `services/blueprint-import/phase4/`

```
services/blueprint-import/phase4/
├── __init__.py
├── pipeline.py          # BlueprintPipeline, process_blueprint()
├── dimension_linker.py  # DimensionLinker, LinkedDimensions
├── arrow_detector.py    # ArrowDetector
├── leader_associator.py # LeaderLineAssociator
└── annotations/         # Export utilities
```

### 2. Is it complete?

**PARTIAL** — Core dimension-to-geometry linking is complete. However:
- Requires Phase 3 vectorizer for extraction
- Arrow detection is heuristic-based
- Leader line association uses proximity + plausibility scoring

Version: `4.0.0-alpha` (per dimension_linker.py)

### 3. Is it tested?

**YES** — Tests exist at `services/blueprint-import/tests/`:
- `test_dimension_linker.py`
- `test_arrow_detector.py`
- `test_leader_associator.py`
- `test_pipeline.py`

Tests use mock extraction results, indicating Phase 4 is designed to work with pre-extracted data.

### 4. Is it wired into production?

**YES** — Wired via `services/api/app/routers/blueprint/phase4_router.py`:
- Endpoint: `POST /blueprint/phase4/link`
- Feature flag: `PHASE4_AVAILABLE` (in constants.py)
- Import: `from phase4 import process_blueprint, BlueprintPipeline, PipelineResult`

The import works because `constants.py` adds `services/blueprint-import` to `sys.path`.

### 5. What does Phase 4 own?

**Dimension-to-geometry association only:**
- Arrow/arrowhead detection in contours
- Leader line association (text → arrow → geometry)
- Multi-factor ranking (proximity + plausibility + type match)
- OCR text parsing (coordinates with Phase 3)

**Does NOT own:**
- PDF extraction (Phase 3)
- OCR text detection (Phase 3)
- Contour extraction (Phase 3)
- Calibration/scale detection (Calibration module)

### 6. Does it provide contour geometry?

**NO** — Phase 4 consumes geometry from Phase 3 `ExtractionResult`:
```python
extraction_result.contours_by_category  # From Phase 3
extraction_result.ocr_dimensions        # From Phase 3
extraction_result.dimensions_mm         # From Phase 3
```

Phase 4 links OCR text to this pre-existing geometry.

### 7. Callable interface

**Entry point:** `BlueprintPipeline.process(pdf_path, instrument_type, extraction_result)`

**Returns:** `PipelineResult`
```python
@dataclass
class PipelineResult:
    source_file: str
    extraction_time_ms: float
    linking_time_ms: float
    total_time_ms: float
    dimensions_mm: tuple              # (width, height)
    features_count: Dict[str, int]    # Contours by category
    ocr_dimensions_found: int
    arrows_detected: int
    dimensions_linked: int
    unmatched_dimensions: int
    association_rate: float
    linked_dimensions: LinkedDimensions
    extraction_result: ExtractionResult  # Full Phase 3 result
```

**LinkedDimensions:**
```python
@dataclass
class LinkedDimensions:
    source_file: str
    dimensions: List[AssociatedDimension]
    unmatched_texts: List[TextRegion]
    arrows_detected: int
    association_rate: float
    processing_time_ms: float
```

### 8. Safe to import from morphology_harvest?

**CONDITIONAL** — Requires `sys.path` modification because `blueprint-import` is not a valid Python package name (hyphen).

Current pattern (from constants.py):
```python
BLUEPRINT_SERVICE_PATH = Path(__file__).parent.parent.parent.parent.parent / "blueprint-import"
sys.path.insert(0, str(BLUEPRINT_SERVICE_PATH))
from phase4 import BlueprintPipeline
```

**Recommendation:** Copy this pattern into `morphology_harvest/adapters.py` for consistency.

---

## Section B: Calibration Module

### 1. Does Calibration exist?

**YES** — Located at `services/blueprint-import/calibration/`

```
services/blueprint-import/calibration/
├── __init__.py
├── pixel_calibrator.py    # PixelCalibrator, CalibrationResult
├── scale_detector.py
└── dimension_extractor.py
```

### 2. Is it complete?

**YES** — Standalone utility with multiple calibration methods:
- `SCALE_LENGTH` — from scale length text
- `RULER` — from detected ruler markings
- `PAPER_SIZE` — from assumed paper size
- `GRID` — from grid cell spacing
- `BODY_HEURISTIC` — from body outline (low confidence)
- `KNOWN_DIMENSION` — from user reference

### 3. Is it tested?

**YES** — Test at `services/blueprint-import/tests/test_pixel_calibration.py`

Tests cover real blueprint collection with known scale lengths.

### 4. Is it wired into production?

**YES** — Wired via `services/api/app/routers/blueprint/calibration_router.py`:
- Feature flag: `CALIBRATION_AVAILABLE`
- Also used via `calibration_integration.py` (EnhancedCalibrationPipeline)

### 5. What does Calibration own?

**Scale detection and pixel-to-mm conversion:**
- Pixels per inch (PPI)
- Pixels per mm (PPMM)
- Calibration confidence
- Reference dimension used

### 6. Callable interface

**Entry point:** `PixelCalibrator.calibrate(image, method, paper_size, known_scale_length)`

**Returns:** `CalibrationResult`
```python
@dataclass
class CalibrationResult:
    method: CalibrationMethod
    ppi: float                    # Pixels per inch
    ppmm: float                   # Pixels per mm
    confidence: float             # 0-1
    reference_name: str
    reference_value_inches: float
    reference_pixels: float
    orientation: str
    notes: List[str]
```

**Utility methods:**
```python
result.pixels_to_inches(pixels) -> float
result.pixels_to_mm(pixels) -> float
result.inches_to_pixels(inches) -> float
```

### 7. Safe to import from morphology_harvest?

**YES** — Same `sys.path` pattern as Phase 4.

---

## Section C: Contour Ownership

### Key Question: Where does contour geometry come from?

| Source | What it provides |
|--------|------------------|
| Phase 3 Vectorizer | `contours_by_category`, `outline_points`, `ocr_dimensions` |
| Phase 4 Linker | Links OCR to existing geometry, no new contours |
| Calibration | Scale/unit conversion only, no geometry |
| Vectorizer output | DXF file with LWPOLYLINE entities |

**Phase 3 `ExtractionResult` contains:**
```python
contours_by_category: Dict[str, List[ContourInfo]]
dimensions_mm: Tuple[float, float]
ocr_dimensions: List[Dict]
```

**For Body Grid morphology classification, we need:**
- Contour segments (from Phase 3)
- Landmarks (derived from OCR dimensions)
- Scale (from Calibration)

---

## Section D: Safe Adapter Strategy

### Adapter Wiring Recommendations

#### Phase4DimensionAssociationAdapter

**Status:** Wire with graceful degradation

**Implementation:**
```python
def check_availability(self) -> AdapterResult:
    try:
        # Add blueprint-import to path
        import sys
        from pathlib import Path
        bp_path = Path(__file__).parents[7] / "blueprint-import"
        if str(bp_path) not in sys.path:
            sys.path.insert(0, str(bp_path))
        
        from phase4 import BlueprintPipeline
        self._pipeline = BlueprintPipeline()
        return AdapterResult.ok({"status": "wired"})
    except ImportError as e:
        return AdapterResult.not_available(f"phase4_import_failed: {e}")
```

**Output mapping:**
```python
PipelineResult.linked_dimensions.dimensions → dimension evidence
PipelineResult.extraction_result.contours_by_category → contour evidence
PipelineResult.extraction_result.dimensions_mm → body dimensions
```

#### CalibrationMetadataAdapter

**Status:** Wire with graceful degradation

**Implementation:**
```python
def check_availability(self) -> AdapterResult:
    try:
        import sys
        from pathlib import Path
        bp_path = Path(__file__).parents[7] / "blueprint-import"
        if str(bp_path) not in sys.path:
            sys.path.insert(0, str(bp_path))
        
        from calibration import PixelCalibrator
        self._calibrator = PixelCalibrator()
        return AdapterResult.ok({"status": "wired"})
    except ImportError as e:
        return AdapterResult.not_available(f"calibration_import_failed: {e}")
```

**Output mapping:**
```python
CalibrationResult.ppmm → pixels_per_mm
CalibrationResult.confidence → calibration_confidence
CalibrationResult.method.value → calibration_method
CalibrationResult.reference_name → reference_dimension_source
```

---

## Section E: Overlay Utility Ownership

### Existing utilities

| Location | Purpose |
|----------|---------|
| `services/blueprint-import/export_svg.py` | SVG export |
| `services/blueprint-import/sandbox/text_geometry_eval/metrics/render_dxf_to_png.py` | DXF to PNG |
| `morphology_harvest/overlay_wrapper.py` | Stubbed overlay generation |

### Recommendation

For 1B-FIX validation overlays:
1. Use `render_dxf_to_png.py` if DXF output exists
2. Else generate minimal matplotlib/PIL overlay from landmarks
3. Document overlay authority in `overlay_wrapper.py`

---

## Section F: Summary Classification

| Component | Classification | Safe to Wire? |
|-----------|---------------|---------------|
| Phase 4 pipeline | `implemented_needs_phase3` | YES (with path setup) |
| Phase 4 dimension linking | `production_ready` | YES |
| Calibration | `production_ready` | YES |
| Phase 3 vectorizer | `production_dependency` | Required by Phase 4 |
| Contour geometry | `phase3_owned` | Access via Phase 4 result |
| Overlay generation | `partial_scaffold` | Use existing or minimal |

---

## Section G: Blocked Items

### Phase 3 Availability

Phase 4's `BlueprintPipeline.process()` internally calls Phase 3 vectorizer:
```python
def _extract(self, pdf_path, instrument_type):
    if self.vectorizer is None:
        raise RuntimeError("Phase3Vectorizer not available")
    return self.vectorizer.extract(pdf_path, instrument_type)
```

If Phase 3 is unavailable, Phase 4 can still work with pre-extracted results:
```python
result = pipeline.process(pdf_path, extraction_result=pre_extracted)
```

**Recommendation:** Check Phase 3 availability separately and report if blocked.

---

## Next Steps

1. **Wire adapters** using the safe patterns documented above
2. **Add Phase 3 availability check** to adapter status reporting
3. **Map Phase 4 output** to HarvestRecord evidence categories
4. **Implement primitive inference** from landmarks (separate from adapter wiring)
5. **Re-run 10 representative validation** with wired adapters
