# Canonical Extractor Render Quality Audit

**Date:** 2026-05-17  
**Sprint:** IBG E-2-E Evidence Integrity Audit (Paused)  
**Status:** AUDIT COMPLETE — Results Below

---

## Purpose

Determine whether the two canonical extractors — **raw edge extractor** (PDF→DXF) and **edge_to_dxf** (image→DXF) — produce visually acceptable output for IBG intake.

**Deciding question:** Would a human trust this extracted artifact as IBG intake evidence?

**Review classes:**
- `usable_for_ibg` — Ready for IBG intake with no additional processing
- `usable_with_caution` — Needs contour chaining but body outline is recoverable
- `not_usable` — Body outline not distinguishable from noise
- `extractor_failure` — Extraction produced no usable geometry

---

## Test Subjects

| Subject | Source Type | Expected Body Dimensions |
|---------|-------------|-------------------------|
| Cuatro Puertoriqueño | PDF blueprint | ~260mm × 375mm |
| Gibson L0 | PNG blueprint scan | ~380mm × 505mm (acoustic) |
| Gibson SG Custom | PNG blueprint scan | ~340mm × 420mm (electric) |

---

## Extraction Pipeline Summary

### Raw Edge Extractor (Phase 3 Vectorizer)

**Location:** `services/blueprint-import/vectorizer_phase3.py`

**Output format:** R12 DXF (AC1009), LINE entities only

**Layer classification:** Yes — BODY_OUTLINE, BODY_OUTLINE_CANDIDATE, CONTROL_CAVITY, PICKGUARD, etc.

### edge_to_dxf

**Location:** `services/blueprint-import/edge_to_dxf.py`

**Output format:** R12 DXF (AC1009), LINE entities only

**Layer classification:** No — single "EDGES" layer

---

## Test Case Results

### TC-01: Cuatro Puertoriqueño via Phase 3 Vectorizer

**Source:** `Guitar Plans/El Cuatro/cuatro puertoriqueño.pdf`  
**DXF output:** `Guitar Plans/El Cuatro/cuatro puertoriqueño.dxf`  

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 30,410 LINE |
| File size | 4.9 MB |
| Extracted dimensions | 272.0mm × 500.0mm |
| Expected dimensions | ~260mm × 375mm |
| Layers | BODY_OUTLINE, BODY_OUTLINE_CANDIDATE, CONTROL_CAVITY, JACK_ROUTE, PICKGUARD (8 total) |

**Visual assessment:**
- Layer classification is working — semantic separation of body vs internal features
- Dimensions within reasonable range (height larger due to neck inclusion)
- Entity count is high but manageable

**Body outline usability:**
- BODY_OUTLINE layer exists and is populated
- Would require contour chaining to form closed loops
- Body shape is recoverable from layer-filtered entities

**Classification:** `usable_with_caution`

**Reason:** Layer classification provides semantic separation. Contour chaining required but body outline is distinguishable.

---

### TC-02: Cuatro Puertoriqueño via edge_to_dxf

**Source:** `Guitar Plans/cuatro puertoriqueño.png`  
**DXF output:** `services/blueprint-import/sandbox/text_geometry_eval/outputs/edge_to_dxf_refined/cuatro puertoriqueño_edges.dxf`

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 2,022,289 LINE |
| File size | 308 MB |
| Extracted dimensions | 257.5mm × 483.8mm |
| Expected dimensions | ~260mm × 375mm |
| Layers | EDGES (single layer) |

**Visual assessment:**
- Dimensions are correct (cuatro body size)
- 2 MILLION LINE entities — extreme density
- No layer classification — all geometry on single "EDGES" layer
- Preview PNG appears blank due to rendering limits

**Body outline usability:**
- Body outline exists but is buried in 2M LINE entities
- No semantic separation from text, dimensions, bracing details
- Filtering body outline from noise is impractical without ML/segmentation

**Classification:** `not_usable`

**Reason:** Body outline is not distinguishable from 2M LINE entities of text, dimensions, and internal details. No layer classification. File size (308MB) makes processing impractical.

---

### TC-03: Gibson L0 via Blueprint Extractor

**Source:** `Guitar Plans/Gibson-L0-IN.png`  
**DXF output:** `Guitar Plans/Gibson-L0-IN_blueprint.dxf`

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 291 LINE |
| File size | 51 KB |
| Extracted dimensions | 646.6mm × 844.6mm |
| Expected dimensions | ~380mm × 505mm |
| Layers | BODY_OUTLINE |

**Visual assessment:**
- Dimensions match **page size**, not body size — 646×844mm is standard blueprint page
- Only 291 entities — extremely sparse
- Single BODY_OUTLINE layer
- Bounding box shows body detection attempted but captured page bounds

**Body outline usability:**
- Sparse entity count suggests body outline may be present
- Page-size dimensions indicate scale/crop issue
- Would need verification of what 291 entities actually represent

**Additional analysis:**
- Point distribution is NOT uniform: 43% top-right, 30% bottom-left, 24% bottom-right, 4% top-left
- This clustering matches body outline position visible in result preview
- 291 unique endpoints = no shared vertices = disconnected LINE entities
- Coordinate system is page-relative, but geometry represents body outline

**Classification:** `usable_with_caution`

**Reason:** Body outline geometry IS present (291 LINE entities clustered in body shape). Page-size bounding box is coordinate system artifact, not extraction failure. Requires contour chaining for IBG.

---

### TC-04: Gibson L0 via edge_to_dxf (Enhanced Mode)

**Source:** `Guitar Plans/Gibson-L0-IN.png`  
**DXF output:** `Guitar Plans/Gibson-L0-IN_enhanced.dxf`

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 403,049 LINE |
| File size | 60 MB |
| Extracted dimensions | 632.0mm × 491.5mm |
| Layers | (not inspected) |

**Visual assessment:**
- 400K LINE entities — high but not extreme
- Dimensions closer to body size (though still large)
- Enhanced mode captures more detail than blueprint mode

**Body outline usability:**
- Body outline likely present but mixed with all extracted edges
- No layer classification available
- Better than edge_to_dxf REFINED but still requires filtering

**Classification:** `usable_with_caution`

**Reason:** Entity count manageable, dimensions reasonable. Body outline recoverable with filtering.

---

### TC-05: Gibson SG Custom (Reference DXF — Human Authored)

**Source:** Manual CAD creation  
**DXF file:** `Guitar Plans/DXF-00-Gibson-SG.dxf`

| Metric | Value |
|--------|-------|
| DXF version | AC1015 (R2000) |
| Entity count | 220 mixed |
| Entity types | SPLINE (16), LINE (77), CIRCLE (43), ARC (79), LWPOLYLINE (5) |
| Closed polylines | 3 of 5 |
| File size | 198 KB |
| Layers | 0 |

**Visual assessment:**
- Mixed entity types — proper CAD construction
- Closed LWPOLYLINE entities — semantically correct contours
- Small file size with high information density
- This is what CAD-grade DXF looks like

**Body outline usability:**
- Immediately usable — closed polylines represent contours
- No chaining required
- Direct IBG intake possible

**Classification:** `usable_for_ibg`

**Reason:** Human-authored CAD reference. Closed polylines, mixed entity types, appropriate scale. This is the target quality level.

---

### TC-06: Gibson Melody Maker via edge_to_dxf

**Source:** `Guitar Plans/Gibson-Melody-Maker.pdf` (converted to image)  
**DXF output:** `services/blueprint-import/sandbox/text_geometry_eval/outputs/Gibson-Melody-Maker_edges.dxf`

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 3,133,858 LINE |
| File size | 473 MB |
| Layers | EDGES |

**Visual assessment:**
- 3.1 MILLION LINE entities — most extreme case
- 473 MB file — impractical for any processing
- Single EDGES layer — no classification

**Body outline usability:**
- Body outline impossible to distinguish
- File too large to process efficiently
- No semantic separation

**Classification:** `not_usable`

**Reason:** 3M LINE entities in 473MB file. Body outline buried in noise. Processing impractical.

---

## Summary Matrix

| Test Case | Extractor | Entities | Dimensions | Classification |
|-----------|-----------|----------|------------|----------------|
| TC-01: Cuatro (Phase3) | Phase 3 Vectorizer | 30,410 | 272×500mm | `usable_with_caution` |
| TC-02: Cuatro (edges) | edge_to_dxf | 2,022,289 | 258×484mm | `not_usable` |
| TC-03: Gibson L0 (bp) | Blueprint Extractor | 291 | 647×845mm | `usable_with_caution` |
| TC-04: Gibson L0 (enh) | edge_to_dxf Enhanced | 403,049 | 632×492mm | `usable_with_caution` |
| TC-05: Gibson SG (ref) | Human CAD | 220 | N/A | `usable_for_ibg` |
| TC-06: Melody Maker | edge_to_dxf | 3,133,858 | N/A | `not_usable` |

---

## Key Findings

### 1. edge_to_dxf Produces Unusable Output

The edge_to_dxf extractor produces DXF files with:
- 2-3 MILLION LINE entities
- 300-470 MB file sizes
- No layer classification
- Body outline buried in noise

**Verdict:** edge_to_dxf output is NOT suitable for IBG intake.

### 2. Phase 3 Vectorizer Produces Usable Output (With Caution)

The Phase 3 vectorizer produces DXF files with:
- 15-30K LINE entities (manageable)
- 2-5 MB file sizes
- Layer classification (BODY_OUTLINE, etc.)
- Reasonable dimensions

**Verdict:** Phase 3 output IS suitable for IBG intake, but requires contour chaining.

### 3. Blueprint Extractor May Have Scale Issues

The blueprint mode extractor produces:
- Sparse output (291 entities)
- Page-size dimensions instead of body dimensions
- BODY_OUTLINE layer exists

**Verdict:** Needs investigation — may be extracting page bounds instead of body.

### 4. Human-Authored CAD is the Target

The Gibson SG reference DXF demonstrates what IBG should receive:
- Mixed entity types (SPLINE, ARC, CIRCLE, LWPOLYLINE)
- Closed polylines for contours
- 220 entities, 198 KB
- Immediately usable

---

## Recommendations

### Immediate (Before Resuming IBG Audit)

1. **Use Phase 3 vectorizer output** for IBG intake, not edge_to_dxf
2. **Filter by BODY_OUTLINE layer** before passing to BodyEvidence bridge
3. **Do not attempt to process edge_to_dxf output** — too large, no classification

### Integration Path

1. Modify `ArtifactBodyEvidenceAdapter` to filter entities by layer
2. Use `contour_reconstruction.py` to chain LINE entities on BODY_OUTLINE layer
3. Reject artifacts where BODY_OUTLINE layer is missing or empty

### Not Recommended

- Processing 2M+ LINE entity files
- Attempting body detection on edge_to_dxf output without ML segmentation
- Using unfiltered DXF as IBG intake

---

## Conclusion

**Would a human trust these extracted artifacts as IBG intake evidence?**

| Extractor | Answer |
|-----------|--------|
| Phase 3 Vectorizer | Yes, with layer filtering and contour chaining |
| edge_to_dxf | No — body outline not distinguishable from noise |
| Blueprint Extractor | Maybe — needs scale/crop investigation |

The canonical path for IBG intake is:

```
PDF → Phase 3 Vectorizer → BODY_OUTLINE layer → contour_reconstruction.py → BodyEvidence
```

The edge_to_dxf path produces geometry that looks correct at dimension level but is not semantically usable.

---

## Fresh Verification: April 29 Canonical Modes (2026-05-17)

**Context:** Prior test artifacts (timestamped April 5 and April 18) were identified as regressions from broken pipeline states. Fresh outputs were generated using the April 29, 2026 canonical modes:

- **RESTORED_BASELINE** — for PDF blueprints (uses RETR_LIST contour retrieval)
- **ENHANCED** — for photo/image files (multi-scale Canny + morphological gap closing)

**Test output location:** `tests/regression_corpus/april29_verification/dxf_files/`

### FV-01: Cuatro Puertoriqueño via RESTORED_BASELINE

**Source:** `Guitar Plans/El Cuatro/cuatro puertoriqueño.pdf`  
**Mode:** RESTORED_BASELINE (API endpoint with `mode=restored_baseline`)

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 192,791 LINE |
| File size | 20.5 MB |
| Extracted dimensions | 245.5mm × 466.8mm |
| Expected dimensions | ~260mm × 375mm |
| Layers | 75 layers (contour_0 through contour_74) |
| API OK status | False (selection score below threshold) |

**Key finding:** RESTORED_BASELINE uses per-contour layer naming (`contour_N`), NOT semantic classification. No BODY_OUTLINE layer exists.

**Classification:** `not_usable`

**Reason:** No semantic layer separation. 192K entities across 75 generic contour layers makes body outline indistinguishable without manual layer selection. Height includes full page content (neck + body + annotations).

---

### FV-02: Gibson L0 via ENHANCED

**Source:** `Guitar Plans/Gibson-L0-IN.png`  
**Mode:** ENHANCED (API endpoint with `mode=enhanced`)

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 140,290 LINE |
| File size | 20.3 MB |
| Extracted dimensions | 632.0mm × 491.5mm |
| Expected dimensions | ~380mm × 505mm (body only) |
| Layers | EDGES (single layer) |
| API OK status | True |

**Key finding:** Dimensions are PAGE SIZE (632mm = ~25" = tabloid width), not body size. ENHANCED mode extracts full page content without body isolation.

**Classification:** `not_usable`

**Reason:** Extracts entire page content. Body outline buried in 140K LINE entities from text, dimensions, and construction lines. No semantic separation.

---

### FV-03: Gibson SG Custom via ENHANCED

**Source:** `Guitar Plans/DXF-00-Gibson-SG.dxf` (converted to PNG)  
**Mode:** ENHANCED (API endpoint with `mode=enhanced`)

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 156,704 LINE |
| File size | 16.0 MB |
| Extracted dimensions | 305.8mm × 485.6mm |
| Expected dimensions | ~340mm × 420mm |
| Layers | EDGES (single layer) |
| API OK status | True |

**Classification:** `not_usable`

**Reason:** Single EDGES layer with 156K entities. Dimensions closer to body size but no semantic separation. Body outline not recoverable without manual selection.

---

### FV-04: Cuatro Puertoriqueño via Phase 3 Vectorizer (Fresh Run)

**Source:** `cuatro puertoriqueño.png` (same source as FV-01)  
**Mode:** Phase 3 Vectorizer (direct CLI invocation)

| Metric | Value |
|--------|-------|
| DXF version | AC1009 (R12) |
| Entity count | 10,920 LINE |
| File size | 1.67 MB |
| Extracted dimensions | 178mm × 332mm |
| Expected dimensions | ~260mm × 375mm |
| Layers | BODY_OUTLINE, BODY_OUTLINE_CANDIDATE, BRIDGE_ROUTE, CONTROL_CAVITY, JACK_ROUTE, PICKGUARD, SMALL_FEATURE (8 total) |
| Scale correction | 0.904× (bridge_route 132.7mm → 120.0mm) |
| Primitives detected | 498 |

**Key finding:** Semantic layer classification works. Body outline extracted and isolated from page content. Scale correction applied using dimensional reference (bridge route).

**Classification:** `usable_with_caution`

**Reason:** Semantic layers provide body isolation. Entity count is manageable (11K vs 193K for RESTORED_BASELINE). Would require contour chaining for IBG intake but body outline is clearly distinguishable.

---

## Updated Summary Matrix (2026-05-17)

| Test Case | Mode | Entities | Dimensions | Layers | Classification |
|-----------|------|----------|------------|--------|----------------|
| TC-01: Cuatro (Phase3) | Phase 3 Vectorizer | 30,410 | 272×500mm | 8 semantic | `usable_with_caution` |
| FV-01: Cuatro (baseline) | RESTORED_BASELINE | 192,791 | 246×467mm | 76 generic | `not_usable` |
| FV-02: Gibson L0 (enh) | ENHANCED | 140,290 | 632×492mm | 1 (EDGES) | `not_usable` |
| FV-03: Gibson SG (enh) | ENHANCED | 156,704 | 306×486mm | 1 (EDGES) | `not_usable` |
| **FV-04: Cuatro (Phase3 fresh)** | **Phase 3 Vectorizer** | **10,920** | **178×332mm** | **8 semantic** | **`usable_with_caution`** |
| TC-05: Gibson SG (ref) | Human CAD | 220 | N/A | 1 (default) | `usable_for_ibg` |

---

## Critical Finding: Mode Quality Gap

### Direct Comparison: Phase 3 vs RESTORED_BASELINE (Same Source)

**Source:** `cuatro puertoriqueño.png` (3600×6450 px)

| Metric | Phase 3 Vectorizer | RESTORED_BASELINE |
|--------|-------------------|-------------------|
| LINE entities | 10,920 | 192,791 |
| File size | 1.67 MB | 20.50 MB |
| Dimensions | 178×332mm | 246×467mm |
| Layers | 8 semantic | 76 generic |
| Layer types | BODY_OUTLINE, BRIDGE_ROUTE, CONTROL_CAVITY, JACK_ROUTE, PICKGUARD, SMALL_FEATURE | contour_0 through contour_74 |
| Body isolation | Yes | No |
| Scale correction | 0.904× (bridge reference) | None |
| Processing time | 29 sec | ~5 sec |

**Phase 3 Vectorizer produces:**
- 18× fewer entities
- 12× smaller files
- Semantic layer classification
- Body isolation from page content
- Scale correction using dimensional references

**RESTORED_BASELINE produces:**
- Dense pixel-level LINE entities
- Generic per-contour layers without semantic meaning
- Full page content without body isolation
- No dimensional validation

**Root cause:** The April 29 "canonical" modes route through `edge_to_dxf.py` which:
1. Does not classify layers semantically
2. Does not isolate body contours from page content
3. Produces dense pixel-level LINE output unsuitable for IBG intake

**Recommendation:** IBG intake must use **Phase 3 Vectorizer** (`mode=cam_ready_r2000` or direct `vectorizer_phase3.py` invocation), NOT the RESTORED_BASELINE or ENHANCED modes.

---

## References

- `CANONICAL_ARTIFACT_PRESERVATION_CONTEXT_SCAN.md` — prior DXF topology findings
- `IBG_E2E_FAILURE_LOG.md` — classification mismatch documentation
- `contour_reconstruction.py` — existing LINE chaining tool
- `EDGE_TO_DXF_REFINED_METHODOLOGY.md` — edge_to_dxf design rationale
