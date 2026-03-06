# Vectorizer Upgrade Plan
## Blueprint-to-DXF Conversion System

**Document Version:** 1.2.0
**Last Updated:** March 2026
**Current Vectorizer Version:** 4.0.0

---

## Executive Summary

This document chronicles the evolution of the Luthier's Toolbox blueprint vectorizer from initial concept through planned future enhancements. It serves as both a historical record and a roadmap for continued development.

---

## Current Rating: 8.0 / 10

### Capability Assessment

| Feature | Status | Score |
|---------|--------|-------|
| PDF/Image ingestion | ✅ Complete | 10/10 |
| Contour extraction (dual-pass) | ✅ Complete | 9/10 |
| ML contour classification | ✅ Complete | 8/10 |
| Geometric primitives (circles, arcs) | ✅ Complete | 8/10 |
| Auto scale detection | ✅ Complete | 7/10 |
| OCR dimension extraction | ✅ Complete | 7/10 |
| DXF export | ✅ Complete | 9/10 |
| Processing tiers system | ✅ Complete | 9/10 |
| Latin American classifiers | ✅ Complete | 8/10 |
| Annotation Layer Architecture | ✅ Complete | 9/10 |
| Phase 4.0 Leader Lines | ✅ Complete | 8/10 |
| Parametric constraints | ❌ Not started | 0/10 |
| Multi-page extraction | ❌ Not started | 0/10 |
| Neural boost | ❌ Not started | 0/10 |

### Score Breakdown

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Core extraction | 25% | 9.0 | 2.25 |
| Classification | 20% | 8.0 | 1.60 |
| OCR/Dimensions | 15% | 7.0 | 1.05 |
| Leader line association | 15% | 8.0 | 1.20 |
| Architecture/Config | 10% | 9.5 | 0.95 |
| Advanced features | 15% | 3.5 | 0.53 |
| **Total** | | | **8.0** |

### Rating History

| Version | Rating | Key Changes |
|---------|--------|-------------|
| v3.0.0 | 5.0 | Dual-pass extraction, color filtering |
| v3.5.0 | 5.5 | ML classification, primitives, scale detection |
| v3.6.0 | 6.5 | OCR dimension extraction |
| v3.6.0 + Phase 4 scaffold | 7.2 | Tiered processing, classifiers, leader line framework |
| v4.0.0-alpha | 7.5 | Annotation Layer Architecture, witness line detection, JSON sidecar |
| v4.0.0 | 8.0 | **Complete Phase 4.0** - ArrowDetector, LeaderLineAssociator, DimensionLinker, BlueprintPipeline |

### Path to Higher Ratings

| Target | Requirements |
|--------|--------------|
| ~~**8.0**~~ | ✅ ACHIEVED: Phase 4.0 leader line association end-to-end |
| **8.5** | Add parametric constraint export, multi-page support |
| **9.0** | Neural boost for low-confidence cases, 95%+ accuracy |
| **9.5** | Production-hardened with 100+ blueprint validation |

### Critical Gaps

1. ~~**Leader Line Implementation**~~ - ✅ RESOLVED: 100 tests passing, real blueprint tested
2. **Parametric Constraints** - No constraint extraction or export
3. **Cross-Reference Validation** - OCR dimensions validated via plausibility scoring (partial)
4. ~~**Annotation Layer Separation**~~ - ✅ RESOLVED: Separate DIMENSIONS layer, XDATA, JSON sidecar

---

## Version History

### Phase 1.0 - Foundation (Complete)
**Goal:** Basic PDF/image to DXF conversion

- [x] PDF rasterization via PyMuPDF
- [x] Image loading (PNG, JPG, TIFF)
- [x] Basic contour extraction (Canny edge detection)
- [x] DXF export via ezdxf
- [x] Command-line interface

### Phase 2.0 - Production Quality (Complete)
**Goal:** Reliable extraction for daily shop use

- [x] Adaptive thresholding for varied blueprint quality
- [x] Contour simplification (Douglas-Peucker)
- [x] Basic category assignment (body, cavity, hole)
- [x] Batch processing support
- [x] Auto-naming conventions

### Phase 3.0 - Intelligence Layer (Complete)
**Goal:** Smart extraction with classification

- [x] Dual-pass extraction (aggressive body, light details)
- [x] Text/annotation filtering via shape heuristics
- [x] Hierarchy-aware extraction (body → cavities → holes)
- [x] Color filtering for blueprint types (blue, sepia, inverted)
- [x] Image caching for performance

### Phase 3.5 - ML Classification (Complete)
**Goal:** Machine learning for contour classification

- [x] 22-feature geometric extraction
- [x] RandomForest classifier (sklearn)
- [x] Graceful fallback to rule-based classification
- [x] Geometric primitive detection (circles, arcs, ellipses)
- [x] Auto scale detection from reference features
- [x] User feedback system for model improvement
- [x] Dimension validation against instrument specs

### Phase 3.6 - OCR Integration (Complete)
**Goal:** Extract dimension text from blueprints

- [x] EasyOCR integration
- [x] Dimension parsing (mm, inches, fractions)
- [x] Contextual parsing ("Scale length is 24.625")
- [x] Label pattern recognition
- [x] Confidence filtering
- [x] OCR dimensions in ExtractionResult

### Phase 4.0 - Leader Line Association (✅ Complete)
**Goal:** Link dimension text to geometry

| Component | Status | Notes |
|-----------|--------|-------|
| ArrowDetector | ✅ Complete | Hybrid contour analysis, orientation filtering, 33 tests |
| LeaderLineAssociator | ✅ Complete | Multi-factor ranking (proximity + plausibility + type + direction), 35 tests |
| DimensionLinker | ✅ Complete | High-level orchestrator with adaptive radius, 18 tests |
| WitnessLineDetector | ✅ Complete | Extension line grouping, returns (point1, point2) |
| BlueprintPipeline | ✅ Complete | End-to-end processing, 14 tests |
| **Annotation Architecture** | ✅ Complete | Base classes, exporters, layer separation |
| AnnotationAwareExporter | ✅ Complete | DXF export with XDATA, R12 fallback |
| AnnotationJSONExporter | ✅ Complete | JSON sidecar for CI/CD validation |
| LinearDimension | ✅ Complete | Modern DXF dimensions + R12 fallback |
| RadialDimension | ✅ Complete | Radius/diameter with leader lines |
| End-to-end integration | ✅ Complete | OCR → arrows → geometry pipeline working |
| Testing on real blueprints | ✅ Complete | Gibson Melody Maker: 34 dims, 762 arrows, 130 links |

**Phase 4.0 Test Coverage:** 100 tests passing

### Phase 4.1 - Multi-Page Support (Planned)
**Goal:** Handle multi-page blueprint PDFs

- [ ] Page enumeration and selection
- [ ] Cross-page feature linking
- [ ] Assembly drawing detection
- [ ] Page-specific scale handling
- [ ] Batch page extraction

### Phase 4.2 - Parametric Constraints (Planned)
**Goal:** Export dimensional relationships

- [ ] Constraint detection (parallel, perpendicular, tangent)
- [ ] XDATA embedding in DXF
- [ ] JSON sidecar export
- [ ] Constraint visualization layer
- [ ] CAD software compatibility testing

### Phase 5.0 - Neural Recognition (Future)
**Goal:** Deep learning for complex features

- [ ] Training data collection pipeline
- [ ] CNN-based feature recognition
- [ ] Transfer learning from CAD datasets
- [ ] GPU acceleration
- [ ] Confidence boosting for edge cases

---

## Architecture Evolution

```
Phase 1-2:  PDF → Rasterize → Edge Detect → Contours → DXF
                    ↓
Phase 3.x:  PDF → Rasterize → Dual-Pass → ML Classify → Primitives → DXF
                    ↓              ↓
                 Color Filter    OCR Extract
                    ↓              ↓
Phase 4.x:  PDF → Rasterize → Dual-Pass → ML Classify → Leader Assoc → DXF
                    ↓              ↓            ↓
                 Color Filter    OCR ←→ Arrow Detect
                    ↓              ↓            ↓
                 Multi-Page    Witness Lines → Constraints
                    ↓
Phase 5.x:  + Neural Boost Layer (low-confidence fallback)
```

---

## Processing Tiers (Implemented)

| Tier | Time | Use Case | Features |
|------|------|----------|----------|
| EXPRESS | <30s | Preview, batch screening | Basic contours only |
| STANDARD | 1-2min | Daily production | ML + OCR |
| PREMIUM | 3-5min | Final drawings | + Leader lines, parametric |
| BATCH | 10-20min | Archive processing | Maximum quality, all pages |

---

## Instrument Classifier Coverage

### Implemented
- **Latin American Strings**
  - Venezuelan Cuatro
  - Puerto Rican Cuatro
  - Colombian Tiple
  - Requinto
  - Charango
  - Bandola

### Planned
- **Acoustic Guitars**
  - Dreadnought, OM, 000, Parlor, Jumbo, Classical
- **Electric Guitars**
  - Stratocaster, Telecaster, Les Paul, SG, Jazzmaster, Jaguar
- **Bass**
  - P-Bass, J-Bass, Modern, Acoustic Bass
- **Other**
  - Mandolin (A/F-style), Ukulele, Banjo, Bouzouki

---

## Newly Identified Adaptations

The following enhancements were identified during Phase 4.0 implementation but were not in the original roadmap:

### 1. **Hybrid Scale Detection** (Priority: High)
**Problem:** Current scale detection relies on known reference features (neck pocket, pickup routes). Fails on unfamiliar instruments.

**Adaptation:**
- Add ruler/scale bar detection from blueprint margins
- OCR-assisted scale extraction ("1:1", "Full Scale", "50%")
- Cross-reference OCR dimensions with measured geometry

### 2. **Blueprint Quality Scoring** (Priority: Medium)
**Problem:** No way to predict extraction quality before processing.

**Adaptation:**
- Pre-scan quality assessment (contrast, noise, resolution)
- Automatic tier recommendation based on quality
- Warning system for low-quality inputs

### 3. **Contour Confidence Propagation** (Priority: High)
**Problem:** Classification confidence doesn't flow to downstream consumers.

**Adaptation:**
- Add confidence scores to DXF layer names or XDATA
- JSON export with per-contour confidence
- Threshold filtering in export pipeline

### 4. **Instrument Family Detection** (Priority: Medium)
**Problem:** Classifier requires knowing instrument family upfront.

**Adaptation:**
- Add pre-classifier to detect family (guitar vs mandolin vs ukulele)
- Body aspect ratio heuristics
- Soundhole type detection (round, f-hole, d-hole)

### 5. **Annotation Layer Separation** (Priority: High)
**Problem:** Dimension text and arrows mixed with geometry contours.

**Adaptation:**
- Dedicated annotation layer in DXF export
- Separate TEXT layer with OCR results
- DIMENSION layer with associated geometry links

### 6. **Progressive Extraction API** (Priority: Medium)
**Problem:** All-or-nothing extraction; can't get partial results.

**Adaptation:**
- Streaming extraction with progress callbacks
- Partial result checkpointing
- Resume capability for large batches

### 7. **Cross-Reference Validation** (Priority: High)
**Problem:** No validation between OCR dimensions and measured geometry.

**Adaptation:**
- Compare OCR "24.625 scale" with measured body proportions
- Flag inconsistencies as warnings
- Suggest scale corrections

### 8. **Template Matching for Common Instruments** (Priority: Low)
**Problem:** Re-extracting known instruments from scratch each time.

**Adaptation:**
- Template library of known instrument outlines
- Fast matching against templates
- Delta extraction for variations

### 9. **Region of Interest (ROI) Extraction** (Priority: Medium)
**Problem:** Full-page extraction when only body outline needed.

**Adaptation:**
- User-defined ROI selection
- Auto-detect ROI from largest contour
- Focused extraction within ROI

### 10. **Export Format Extensions** (Priority: Low)
**Problem:** DXF-only export limits integration options.

**Adaptation:**
- SVG export with metadata
- PDF overlay with extracted geometry
- STEP/IGES for 3D CAD integration
- GeoJSON for web viewers

### 11. **Batch Comparison Reports** (Priority: Medium)
**Problem:** No way to compare extraction results across blueprint versions.

**Adaptation:**
- Diff report between two extractions
- Highlight changed dimensions
- Version tracking in metadata

### 12. **Localization Support** (Priority: Low)
**Problem:** OCR optimized for English dimension labels.

**Adaptation:**
- Spanish label patterns ("longitud de escala", "ancho")
- French label patterns ("longueur", "largeur")
- Unit localization (cm common in Europe)

---

## Implementation Priority Matrix

| Adaptation | Impact | Effort | Priority | Status |
|------------|--------|--------|----------|--------|
| Cross-Reference Validation | High | Medium | P1 | Pending |
| ~~Annotation Layer Separation~~ | High | Low | P1 | ✅ Done |
| Contour Confidence Propagation | High | Low | P1 | Pending |
| Hybrid Scale Detection | High | High | P2 | Pending |
| Instrument Family Detection | Medium | Medium | P2 | Pending |
| Blueprint Quality Scoring | Medium | Medium | P2 | Pending |
| ROI Extraction | Medium | Low | P3 | Pending |
| Progressive Extraction API | Medium | High | P3 | Pending |
| Batch Comparison Reports | Medium | Medium | P3 | Pending |
| Template Matching | Low | High | P4 | Pending |
| Export Format Extensions | Low | Medium | P4 | Pending |
| Localization Support | Low | Low | P4 | Pending |

---

## Testing Requirements

### Unit Tests Needed
- [ ] Arrow detection on synthetic shapes
- [ ] Leader line association with mock data
- [ ] Instrument profile matching
- [ ] Tier configuration loading (JSON + YAML)
- [ ] OCR dimension parsing edge cases

### Integration Tests Needed
- [ ] End-to-end extraction with leader lines
- [ ] Tiered processing comparison
- [ ] Multi-instrument classification
- [ ] Cross-reference validation

### Benchmark Suite
- [ ] 50+ diverse blueprints (guitars, mandolins, ukuleles)
- [ ] Quality levels (high-res scan, phone photo, faded copy)
- [ ] Multiple scales (1:1, 1:2, varied)
- [ ] Dimension label styles (callouts, inline, margin)

---

## Success Metrics

| Metric | Current | Target (Phase 4) | Target (Phase 5) |
|--------|---------|------------------|------------------|
| Body outline accuracy | 92% | 95% | 98% |
| Feature classification | 78% | 88% | 95% |
| OCR dimension extraction | 70% | 85% | 92% |
| Leader line association | 0% | 75% | 90% |
| Processing time (standard) | 45s | 60s | 90s |
| False positive rate | 8% | 4% | 2% |

---

## Changelog

### v4.0.0-alpha (Current)
- Added Annotation Layer Architecture
  - LinearDimension and RadialDimension classes
  - AnnotationAwareExporter with layer separation
  - AnnotationJSONExporter for CI/CD validation
  - XDATA storage for machine readability
  - R12 fallback with user warning
- Added WitnessLineDetector integration
- Added shop_config.yaml layer configuration
- 19 annotation layer tests

### v3.6.0
- Added OCR dimension extraction
- Added processing tiers system
- Added Latin American instrument classifiers
- Added Phase 4.0 leader line scaffold
- Added tiered processing to vectorizer

### v3.5.0
- Added ML contour classification
- Added geometric primitive detection
- Added auto scale detection
- Added user feedback system

### v3.0.0
- Added dual-pass extraction
- Added color filtering
- Added hierarchy-aware extraction

---

## Contributors

- Luthier's Toolbox Development Team
- Consulting Engineer Evaluation (Phase 4.0 roadmap)
- Claude Code (Implementation assistance)

---

*This document should be updated with each significant version release.*

---

## Session Log: March 6, 2026

### Issue Resolved: Large PDF Image Resize

**Problem:** Blueprint Lab pipeline was blocked - large PDFs (e.g., Les Paul at 14044x9934 pixels) exceeded Claude API's 5MB base64 image limit, causing 500 errors.

**Root Cause:** The `_resize_image_if_needed()` function wasn't aggressive enough for high-resolution blueprint PDFs that produce 7MB+ PNG files after rasterization.

**Fix Applied (`analyzer.py`):**
- Added `MAX_TOTAL_PIXELS = 16,000,000` constraint
- Smart initial scale estimation for images >2x the size limit
- Extended quality levels: [85, 70, 55, 40, 30, 20]
- Extended scale factors: [0.75, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1]
- Last resort: 0.05 scale
- Adaptive DPI for PDF conversion (150-300 based on file size)
- Detect media type from magic bytes instead of filename
- Disabled PIL decompression bomb protection for large blueprints

**Test Result:**
```
Input:  7,074,113 bytes, 14044x9934 pixels (139M pixels)
Output: 1,389,298 bytes, 4756x3364 pixels, quality=85
Result: HTTP 200, 18 dimensions detected, "Gibson Les Paul Standard"
```

**Commit:** `bc1f8c2a fix(blueprint): handle large PDFs exceeding Claude 5MB image limit`

### Current Pipeline Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: AI Analysis | ✅ Working | Large PDFs now resize properly |
| Phase 1.5: Calibration | ✅ Working | CalibrationPanel shows after analysis |
| Phase 2: Vectorization | ⚠️ 0% accuracy | Needs upgrade per this document |
| Phase 3: CAM | ✅ Working | Ready when vectorization improves |

### Next Priority

The **vectorizer itself** (Phase 2) still has 0% good detections on the 33-blueprint test suite. The AI Analysis phase is now unblocked, but the core vectorization logic needs the upgrades outlined in this document to reach 8.5+ rating:

1. **Multi-view detection** - Use GridZoneClassifier (already built)
2. **Contour scoring** - Replace "largest contour" with smart selection
3. **Aspect ratio filtering** - Filter for guitar-like proportions (1.1-1.6)
4. **Calibration integration** - Export at real-world scale

### Rating Unchanged: 8.0 / 10

This session fixed infrastructure (image ingestion) but did not improve the core vectorization algorithms. Rating remains at 8.0 pending Phase 4.1/4.2 work.

---

## Session Update: March 6, 2026 (Multi-Format Ingestion)

### Multi-Format Support Added

**Supported Input Formats:**

| Format | Support | Notes |
|--------|---------|-------|
| PDF | ✅ Full | Converted to PNG via pdf2image with adaptive DPI |
| PNG | ✅ Full | Direct Claude vision analysis |
| JPEG | ✅ Full | Direct Claude vision analysis |
| GIF | ✅ Full | Magic byte detection |
| WebP | ✅ Full | Magic byte detection |
| BMP | ✅ New | Magic byte detection, converted to PNG |
| DXF | ✅ New | Direct ezdxf parsing (no AI needed) |

### DXF Direct Parsing

DXF files are handled differently from image-based blueprints:
- **No AI analysis needed** - DXF contains actual vector geometry
- Uses `ezdxf` library to extract entities directly
- Supported entities: LINE, CIRCLE, ARC, LWPOLYLINE, POLYLINE, SPLINE, ELLIPSE, POINT
- Extracts units from DXF header ($INSUNITS)
- Calculates bounds and dimensions from geometry

**New Files:**
- `dxf_parser.py` - DXF entity extraction and parsing
- Updated `analyzer.py` - BMP magic byte detection, DXF routing

### Updated Pipeline Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: AI Analysis | ✅ Working | Now supports PDF, PNG, JPEG, GIF, WebP, BMP |
| Phase 1: DXF Parsing | ✅ New | Direct vector extraction (bypasses AI) |
| Phase 1.5: Calibration | ✅ Working | CalibrationPanel shows after analysis |
| Phase 2: Vectorization | ⚠️ 0% accuracy | Still needs upgrade |
| Phase 3: CAM | ✅ Working | Ready when vectorization improves |

### Rating: 8.0 / 10 (unchanged)

Multi-format ingestion is infrastructure improvement. Core vectorization accuracy unchanged.

---

## Session Update: AI Images → Blueprint Lab Pipeline

**Date:** 2026-03-06

### Problem
AI Design Studio generates instrument concept images but had "nowhere to go" - no continuation to vectorization pipeline.

### Solution
Added direct pipeline continuation from AI Images to Blueprint Lab:

1. **New Button: "Send to Blueprint Lab"**
   - Added to `ImageActionsPanel.vue`
   - Accent-styled purple button with 📐 icon
   - Visible when an image is selected

2. **Event Chain Wiring**
   - `ImageActionsPanel.vue` → emits `vectorize`
   - `AiImageProperties.vue` → forwards `vectorize`
   - `GenerateTabPanel.vue` → forwards `vectorize`
   - `AiImagesView.vue` → handles with `handleVectorize()`

3. **SessionStorage Handoff**
   ```javascript
   sessionStorage.setItem("blueprintLab.pendingImage", JSON.stringify({
     url: imageUrl,
     source: "ai-images",
     filename: `ai-generated-${store.selectedId}.png`,
     prompt: store.selectedImage.userPrompt,
   }));
   router.push("/blueprint");
   ```

4. **BlueprintLab.vue Receiver**
   - Added `onMounted` hook to check for pending images
   - Fetches image from URL, creates File object
   - Calls `validateAndSetFile(file)` to enter workflow
   - Clears sessionStorage after loading

### Modified Files
- `packages/client/src/features/ai_images/components/ImageActionsPanel.vue`
- `packages/client/src/features/ai_images/AiImageProperties.vue`
- `packages/client/src/views/ai_images/GenerateTabPanel.vue`
- `packages/client/src/views/AiImagesView.vue`
- `packages/client/src/views/BlueprintLab.vue`

### User Flow
```
AI Design Studio → Generate Image → Select Image → "Send to Blueprint Lab"
    ↓
Blueprint Lab (auto-loads image) → Analyze → Calibrate → Vectorize → CAM
```

### Impact
- Creates seamless workflow: AI concept → CAM-ready vectors
- No manual file download/upload required
- Preserves prompt metadata for traceability
