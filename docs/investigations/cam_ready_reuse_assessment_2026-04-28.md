# CAM-Ready Reuse Assessment

**Date:** 2026-04-28  
**Scope:** Read-only investigation of Phase 3 `cam_ready` for potential EdgeToDXF reuse

---

## 1. What does Phase 3's `cam_ready` actually produce?

**Parameter location:** [vectorizer_phase3.py:3279](../services/blueprint-import/vectorizer_phase3.py#L3279)

**Branch point:** [vectorizer_phase3.py:3582](../services/blueprint-import/vectorizer_phase3.py#L3582)
```python
if cam_ready and CAM_EXPORT_AVAILABLE:
    export_cam_ready_dxf(classified, cam_dxf_path, ...)
```

**Export function:** [dxf_postprocessor.py:227](../services/blueprint-import/dxf_postprocessor.py#L227)

**Output differences when `cam_ready=True`:**
- Creates separate `_cam.dxf` file alongside normal output
- R12 format default (LINE segments via `dxf_compat.add_polyline`)
- For R13+: optional ARC entities if `fit_arcs=True` (line 319)
- Multiple layers based on classification (BODY_OUTLINE, PICKGUARD, etc.)
- Applies `scale_factor` and `simplify_tolerance` to coordinates
- Centers geometry on body outline if found

---

## 2. Where does primitive detection live?

**Class location:** [vectorizer_phase3.py:903](../services/blueprint-import/vectorizer_phase3.py#L903)

**Detection capabilities:**
| Primitive | Method | Confidence check |
|-----------|--------|------------------|
| Circle | `detect_circle()` line 911 | circularity >= 0.85 |
| Ellipse | `detect_ellipse()` line 938 | fit_ratio > 0.85 |
| Arc | `detect_arc()` line 972 | radius error < 10% |

**No spline detection.** Only circles, ellipses, and arcs.

**Call interface:**
```python
detector = PrimitiveDetector(mm_per_px: float)
primitives = detector.detect_all(
    contours: List[np.ndarray],  # raw OpenCV contours
    min_confidence: float = 0.8,
    max_size_mm: float = 300.0
) -> List[GeometricPrimitive]
```

**DXF export:** [vectorizer_phase3.py:2627](../services/blueprint-import/vectorizer_phase3.py#L2627) `export_primitives_to_dxf()` approximates all primitives as polylines (no native CIRCLE/ELLIPSE/ARC entities in R12 output).

---

## 3. Is primitive detection callable from outside Phase 3?

**Yes — standalone class.**

Dependencies of `PrimitiveDetector`:
- `cv2` (OpenCV)
- `numpy`
- `math`
- `GeometricPrimitive` dataclass (same file, lines 212-227)
- `PrimitiveType` enum (same file, lines 191-196)

**No coupling to Phase3Vectorizer state.** The only initialization parameter is `mm_per_px`. The `detect_all()` method takes a raw `List[np.ndarray]` — the same format EdgeToDXF already produces from `cv2.findContours()`.

**Reuse path:** Extract `PrimitiveDetector`, `GeometricPrimitive`, and `PrimitiveType` to a shared module. Call from EdgeToDXF after contour extraction.

---

## 4. What's the LWPOLYLINE / layer separation story?

**Entity types:**
- R12 (default): LINE segments only via `add_polyline(version='R12')` ([dxf_postprocessor.py:381](../services/blueprint-import/dxf_postprocessor.py#L381))
- R13+: LWPOLYLINE + ARC entities if `fit_arcs=True` ([dxf_postprocessor.py:363-368](../services/blueprint-import/dxf_postprocessor.py#L363))

**Layer separation:** Yes, multiple layers.
- Layer names from `ContourCategory.value.upper()` ([line 330](../services/blueprint-import/dxf_postprocessor.py#L330))
- Color mapping at [lines 311-316](../services/blueprint-import/dxf_postprocessor.py#L311)

**Classification logic:** Hybrid ML + rules.
- ML-first if classifier available and confidence > 0.75 ([line 1747](../services/blueprint-import/vectorizer_phase3.py#L1747))
- Rule-based fallback: dimension thresholds ([lines 1770-1844](../services/blueprint-import/vectorizer_phase3.py#L1770))
- Rules are hardcoded mm ranges per category (e.g., body: 180-700mm, soundhole: 80-130mm circular)
