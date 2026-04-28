# Blueprint-Import Sandbox Inventory — Phase 1

**Date:** 2026-04-27  
**Scope:** `services/blueprint-import/` (the vectorizer sandbox)  
**Purpose:** Characterize contents before integration/retirement decisions

---

## Executive Summary

The blueprint-import sandbox contains **22,282 lines** of Python across **48 modules**, organized into a tiered processing system for blueprint vectorization. The codebase spans three major version tracks:

| Version | Primary File | Status |
|---------|--------------|--------|
| Phase 2 | `vectorizer_phase2.py` | **Superseded** — not imported anywhere |
| Phase 3.6 | `vectorizer_phase3.py` | **Current production vectorizer** |
| Phase 3.7 | `vectorizer_enhancements.py` | Optional enhancements, imported by Phase 3.6 |
| Phase 4.0 | `phase4/` directory | Leader line association, complete per docs |

**Key finding:** The VECTORIZER_UPGRADE_PLAN.md declares version 4.0.0, but `vectorizer_phase3.py` declares version 3.6.0. The "v4.0.0" components live in `phase4/` as a separate module, not integrated into the main vectorizer file.

---

## Task 1.1 — Module Inventory (Grouped by Classification)

### Core Extraction (PDF/Image Rasterization, Contour Detection)

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `vectorizer_phase3.py` | 4,148 | 2026-04-05 | "Phase 3.6 Vectorizer - Production-Grade Blueprint Extraction with ML + OCR" | `dxf_compat`, `vectorizer_enhancements`, `export_svg`, `dxf_postprocessor`, `classifiers.grid_zone` |
| `vectorizer_phase2.py` | 1,684 | 2026-03-04 | "Phase 2 Vectorizer - Intelligent Geometry Reconstruction" | `dxf_compat` |
| `vectorizer_enhancements.py` | 1,155 | 2026-03-09 | "Phase 3.7 Vectorizer Enhancements — Standalone Module" | *(none)* |
| `analyzer.py` | 386 | 2026-03-06 | "Blueprint Analyzer - Claude Sonnet 4 Integration" | *(none)* |

**Subtotal:** 7,373 lines

### Classification (Contour Categorization, Grid Zones, Instrument-Specific)

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `classifiers/__init__.py` | 36 | 2026-03-09 | "Blueprint Instrument Classifiers" | `classifiers.latin_american`, `classifiers.grid_zone` |
| `classifiers/grid_zone/__init__.py` | 30 | 2026-03-09 | "Grid Zone Classifier" | `.zones`, `.classifier` |
| `classifiers/grid_zone/classifier.py` | 504 | 2026-03-09 | "Grid Zone Classifier" | `.zones` |
| `classifiers/grid_zone/zones.py` | 453 | 2026-03-09 | "Grid Zone Definitions" | *(none)* |
| `classifiers/latin_american/__init__.py` | 41 | 2026-03-09 | "Latin American String Instruments Classifier" | `.classifier`, `.instruments` |
| `classifiers/latin_american/classifier.py` | 514 | 2026-03-09 | "Latin American Strings Classifier" | `.instruments` |
| `classifiers/latin_american/instruments.py` | 419 | 2026-03-09 | "Latin American Instrument Profiles" | *(none)* |

**Subtotal:** 1,997 lines

### Calibration (Scale Detection, Pixel Calibration, Dimension Extraction)

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `calibration/__init__.py` | 39 | 2026-03-09 | "Blueprint Calibration Module" | `.pixel_calibrator`, `.scale_detector`, `.dimension_extractor` |
| `calibration/pixel_calibrator.py` | 502 | 2026-03-09 | "Pixel Calibrator" | *(none)* |
| `calibration/scale_detector.py` | 509 | 2026-03-09 | "Scale Reference Detector" | *(none)* |
| `calibration/dimension_extractor.py` | 439 | 2026-03-09 | "Calibrated Dimension Extractor" | `.pixel_calibrator` |
| `calibration_integration.py` | 337 | 2026-03-09 | "Calibration Integration Module" | `calibration` |

**Subtotal:** 1,826 lines

### OCR and Dimensions (Text Recognition, Dimension Linking)

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `dimension_extractor.py` | 489 | 2026-03-04 | "Blueprint Dimension Extractor" | *(none)* |
| `extract_dimensions.py` | 557 | 2026-03-09 | "Blueprint Dimension Extractor" | *(none)* |
| `debug_ocr.py` | 220 | 2026-03-04 | "Debug OCR output to see what texts are being detected." | *(none)* |

**Subtotal:** 1,266 lines

**Note:** Two files named similarly (`dimension_extractor.py` at root, `calibration/dimension_extractor.py`) — potential duplication or evolution.

### Phase 4 Annotation (Leader Lines, Arrows, Dimension Association)

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `phase4/__init__.py` | 49 | 2026-03-05 | "Phase 4.0: Leader Line Association" | `.arrow_detector`, `.leader_associator`, `.dimension_linker`, `.pipeline` |
| `phase4/pipeline.py` | 271 | 2026-03-09 | "Phase 4.0 End-to-End Pipeline" | *(none)* |
| `phase4/arrow_detector.py` | 827 | 2026-03-09 | "Arrow Detection for Blueprint Dimension Association" | *(none)* |
| `phase4/dimension_linker.py` | 348 | 2026-03-09 | "Dimension Linker - High-Level Orchestrator" | `.arrow_detector`, `.leader_associator` |
| `phase4/leader_associator.py` | 1,018 | 2026-03-09 | "Leader Line Association for Blueprint Dimensions" | `.arrow_detector` |
| `phase4/annotations/__init__.py` | 32 | 2026-03-09 | "Annotation Layer Management for DXF Export" | `.base`, `.dimensions`, `.exporter`, `.json_exporter` |
| `phase4/annotations/base.py` | 136 | 2026-03-09 | "Annotation Base Classes" | *(none)* |
| `phase4/annotations/dimensions.py` | 329 | 2026-03-09 | "Dimension Annotation Classes" | `.base` |
| `phase4/annotations/exporter.py` | 391 | 2026-04-03 | "Annotation-Aware DXF Exporter" | `.base` |
| `phase4/annotations/json_exporter.py` | 365 | 2026-03-09 | "Annotation JSON Exporter" | `.base`, `.dimensions` |
| `run_phase4.py` | 125 | 2026-03-09 | "Phase 4.0 CLI - Run dimension linking pipeline" | `phase4.pipeline` |

**Subtotal:** 3,891 lines

### DXF Output (Writers, Post-Processing, Layer Management)

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `dxf_compat.py` | 200 | 2026-04-02 | "DXF Compatibility Layer - R12 Standard for Maximum Compatibility" | *(none)* |
| `dxf_parser.py` | 287 | 2026-03-06 | "DXF Parser - Extract geometry from DXF files" | *(none)* |
| `dxf_postprocessor.py` | 531 | 2026-04-03 | "DXF Post-Processor for CAM-Ready Output" | `dxf_compat` |
| `export_svg.py` | 192 | 2026-03-09 | "SVG Export for Phase 3.7 Vectorizer" | *(none)* |

**Subtotal:** 1,210 lines

### Configuration and Infrastructure

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `__init__.py` | 5 | 2025-12-15 | "Blueprint Import Service" | *(none)* |
| `config/__init__.py` | 32 | 2026-03-09 | "Blueprint Import Configuration" | `.processing_tiers` |
| `config/processing_tiers.py` | 330 | 2026-03-09 | "Processing Tiers Configuration" | *(none)* |
| `train_classifier.py` | 159 | 2026-03-04 | "Bootstrap ML classifier from rule-based pseudo-labels." | `vectorizer_phase3` |

**Subtotal:** 526 lines

### Tests

| File | Lines | Last Modified | Docstring Purpose | Internal Imports |
|------|-------|---------------|-------------------|------------------|
| `tests/__init__.py` | 1 | 2026-03-15 | "Blueprint-import test suite." | *(none)* |
| `tests/test_annotation_layer.py` | 356 | 2026-03-09 | "Tests for Annotation Layer Architecture" | `phase4.annotations` |
| `tests/test_arrow_detector.py` | 516 | 2026-03-09 | "Tests for Arrow Detector" | `phase4.arrow_detector` |
| `tests/test_batch_blueprints.py` | 332 | 2026-03-09 | "Batch Blueprint Classification Test" | `classifiers.grid_zone` |
| `tests/test_dimension_linker.py` | 266 | 2026-03-09 | "Tests for Dimension Linker" | `phase4.dimension_linker`, `phase4.leader_associator` |
| `tests/test_grid_zone_classifier.py` | 450 | 2026-03-09 | "Grid Zone Classifier Tests" | `classifiers.grid_zone`, `classifiers.grid_zone.zones` |
| `tests/test_leader_associator.py` | 656 | 2026-03-09 | "Tests for Leader Line Associator" | `phase4.leader_associator`, `phase4.arrow_detector` |
| `tests/test_ocr_integration.py` | 54 | 2026-03-04 | "Test OCR integration with Phase 3.5 vectorizer." | `vectorizer_phase3` |
| `tests/test_photo_pipeline_trial.py` | 454 | 2026-03-09 | "Photo Pipeline Trial — Black Background Guitar Silhouette" | `vectorizer_enhancements` |
| `tests/test_pipeline.py` | 298 | 2026-03-09 | "Tests for Phase 4.0 Pipeline" | `phase4.pipeline` |
| `tests/test_pixel_calibration.py` | 400 | 2026-03-09 | "Test Pixel Calibration on Blueprint Collection" | `calibration` |
| `tests/test_sheet_type_detection.py` | 303 | 2026-03-09 | "Tests for Sheet Type Detection & Body Candidate Filtering" | `vectorizer_phase3` |
| `tests/test_strat_grid.py` | 206 | 2026-03-06 | "Test GridZoneClassifier on Stratocaster Grid Image" | `classifiers.grid_zone` |

**Subtotal:** 4,292 lines

---

## Task 1.2 — Component Classification Summary

| Category | Files | Lines | % of Total |
|----------|-------|-------|------------|
| Core extraction | 4 | 7,373 | 33.1% |
| Tests | 13 | 4,292 | 19.3% |
| Phase 4 annotation | 11 | 3,891 | 17.5% |
| Classification | 7 | 1,997 | 9.0% |
| Calibration | 5 | 1,826 | 8.2% |
| OCR and dimensions | 3 | 1,266 | 5.7% |
| DXF output | 4 | 1,210 | 5.4% |
| Configuration | 4 | 526 | 2.4% |
| **Total** | **48** | **22,282** | 100% |

---

## Task 1.3 — Version Progression

### Current State

| Version | File(s) | Declared Version | Status |
|---------|---------|------------------|--------|
| Phase 2 | `vectorizer_phase2.py` | *(none declared)* | **SUPERSEDED** — Not imported anywhere. Code comment in `export_svg.py` notes "Ported from vectorizer_phase2". |
| Phase 3.6 | `vectorizer_phase3.py` | 3.6.0 | **CURRENT** — Primary vectorizer. Imports enhancements optionally. |
| Phase 3.7 | `vectorizer_enhancements.py` | 3.7.0 | **ACTIVE** — Seven enhancement classes. Imported by Phase 3.6 with try/except fallback. |
| Phase 4.0 | `phase4/` (11 files) | 4.0.0 | **STANDALONE** — Complete per VECTORIZER_UPGRADE_PLAN.md. Has own CLI (`run_phase4.py`). |

### Version Declaration Discrepancy

**FLAGGED:** `VECTORIZER_UPGRADE_PLAN.md` declares "Current Vectorizer Version: 4.0.0" but:
- `vectorizer_phase3.py` declares `Version: 3.6.0`
- Phase 4.0 components live in `phase4/` directory, not integrated into main vectorizer
- No evidence of a unified v4.0.0 vectorizer file

The "v4.0.0" claim appears to be aspirational documentation rather than actual implementation state.

### Import Hierarchy

```
vectorizer_phase3.py (v3.6.0)
├── dxf_compat.py (required)
├── vectorizer_enhancements.py (v3.7.0, optional)
├── export_svg.py (optional)
├── dxf_postprocessor.py (optional)
│   └── dxf_compat.py
└── classifiers.grid_zone (optional)
    ├── classifier.py
    └── zones.py

vectorizer_phase2.py (superseded)
└── dxf_compat.py

phase4/ (standalone, not integrated with vectorizer)
├── pipeline.py (entry point)
├── dimension_linker.py
│   ├── arrow_detector.py
│   └── leader_associator.py
│       └── arrow_detector.py
└── annotations/
    ├── base.py
    ├── dimensions.py
    ├── exporter.py
    └── json_exporter.py
```

### Where v4.0.0 Functionality Lives

Per VECTORIZER_UPGRADE_PLAN.md, v4.0.0 = "Complete Phase 4.0 — ArrowDetector, LeaderLineAssociator, DimensionLinker, BlueprintPipeline"

These components are **fully implemented** in:
- `phase4/arrow_detector.py` (827 lines)
- `phase4/leader_associator.py` (1,018 lines)
- `phase4/dimension_linker.py` (348 lines)
- `phase4/pipeline.py` (271 lines)

But they are **not integrated** with `vectorizer_phase3.py`. They have their own CLI (`run_phase4.py`) and operate as a separate pipeline.

### Functional Differences Between Versions

| Feature | Phase 2 | Phase 3.6 | Phase 3.7 (enhancements) | Phase 4.0 |
|---------|---------|-----------|--------------------------|-----------|
| Dual-pass extraction | No | Yes | — | — |
| ML classification | No | Yes (optional sklearn) | — | — |
| Color filtering | Yes | Yes | — | — |
| OCR dimension extraction | No | Yes | — | — |
| Photo processing | No | — | Yes (GuitarPhotoProcessor) | — |
| Adaptive line extraction | No | — | Yes (AdaptiveLineExtractor) | — |
| Scale calibration | Basic | Basic | Yes (ScaleCalibrator) | — |
| Contour completion | No | — | Yes (ContourCompleter) | — |
| Debug visualization | No | — | Yes (DebugVisualizer) | — |
| Manual override | No | — | Yes (ManualOverride) | — |
| Validation report | No | — | Yes (ValidationReport) | — |
| Arrow detection | No | No | No | Yes |
| Leader line association | No | No | No | Yes |
| Dimension-to-geometry linking | No | No | No | Yes |
| Annotation layer separation | No | No | No | Yes |

---

## Reports and Documentation (in sandbox)

| File | Lines | Purpose |
|------|-------|---------|
| `docs/VECTORIZER_UPGRADE_PLAN.md` | ~250 | Version history, roadmap, capability assessment |
| `BATCH_CLASSIFICATION_REPORT.md` | ~200 | Test results from grid zone classifier |
| `CALIBRATION_REPORT.md` | ~150 | Pixel calibration test results |
| `DIMENSIONS_REPORT.md` | ~130 | OCR dimension extraction results |

---

## Sample Outputs Overview (detailed characterization in Phase 2)

### Root Level Test Files
- `test_dreadnought_phase5b.dxf` (398 KB)
- `test_dreadnought_phase5b_primitives.dxf` (4.3 MB)
- `test_lespaul_phase5c.dxf` (1.2 MB)
- `test_lespaul_phase5c_primitives.dxf` (1.2 MB)

### test_output/ Directory
- 8 DXF files (various guitars, cuatro)
- 1 subdirectory (`dreadnought_classified.dxf/` — appears to be directory not file)
- Size range: 398 KB to 6.6 MB

### output/ukulele/ Directory
- 4 source PDFs
- 8 DXF files (4 standard, 4 primitives variants)
- Size range: 159 KB to 3.2 MB

---

## Phase 1 Summary

**Immediate observations:**

1. **Superseded code:** `vectorizer_phase2.py` (1,684 lines) is fully superseded — candidate for removal or archival

2. **Modular architecture:** Phase 4.0 is implemented as a standalone system, not integrated with the main vectorizer. This is intentional (separate concern) but creates two entry points

3. **Version claim mismatch:** Documentation claims v4.0.0, code declares v3.6.0. The gap is the Phase 4 integration work

4. **Duplicate files:** Two `dimension_extractor.py` files exist (root and calibration/) — needs Phase 2 analysis to determine relationship

5. **Test coverage concentrated:** 4,292 lines of tests (19% of codebase) — healthy ratio

---

**Phase 1 Complete. Awaiting review before Phase 2.**
