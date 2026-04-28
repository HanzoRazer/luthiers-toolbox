# Blueprint-Import Sandbox Audit — Phase 2

**Date:** 2026-04-27  
**Scope:** Cross-reference analysis, photo-vectorizer relationship, entry points, tests, documentation, sample outputs

---

## Task 2.1 — Main Repo Overlap

### Production Import Path

The sandbox **IS production-active**. The API routers import directly from the sandbox:

**File:** `services/api/app/routers/blueprint/constants.py`
```python
# Lines 46-48:
BLUEPRINT_SERVICE_PATH = Path(__file__).parent.parent.parent.parent.parent / "blueprint-import"
sys.path.insert(0, str(BLUEPRINT_SERVICE_PATH))

# Lines 82, 97:
from vectorizer_phase2 import create_phase2_vectorizer
from vectorizer_phase3 import extract_guitar_blueprint, Phase3Vectorizer
```

### File Relationship Summary

| Sandbox File | Main Repo Relationship | Status |
|--------------|------------------------|--------|
| `vectorizer_phase3.py` | **IMPORTED** by `services/api/app/routers/blueprint/constants.py` | Production-active |
| `vectorizer_phase2.py` | **IMPORTED** by `services/api/app/routers/blueprint/constants.py` | Production-active (but superseded by phase3) |
| `analyzer.py` | **IMPORTED** by `services/api/app/routers/blueprint/constants.py` | Production-active |
| `phase4/pipeline.py` | **IMPORTED** by `services/api/app/routers/blueprint/constants.py` | Production-active |
| `dxf_compat.py` | **SANDBOX-ONLY** — no equivalent in main repo | Used by sandbox vectorizers |
| `dxf_postprocessor.py` | **SANDBOX-ONLY** | Used by sandbox vectorizers |
| `export_svg.py` | **SANDBOX-ONLY** | Used by sandbox vectorizers |
| `calibration/` | **SANDBOX-ONLY** — no equivalent in main repo | Unclear if production-active |
| `classifiers/` | **SANDBOX-ONLY** — no equivalent in main repo | Imported by vectorizer_phase3 |
| `config/` | **SANDBOX-ONLY** | Unclear if production-active |

### API Endpoint Mapping

| API Endpoint | Sandbox Module Used |
|--------------|---------------------|
| `/api/blueprint/analyze` | `analyzer.py` |
| `/api/blueprint/phase2/extract` | `vectorizer_phase2.py` |
| `/api/blueprint/phase3/extract` | `vectorizer_phase3.py` |
| `/api/blueprint/phase4/process` | `phase4/pipeline.py` |

---

## Task 2.2 — Photo-Vectorizer Relationship

### Shared Lineage Analysis

The sandbox (`services/blueprint-import/`) and photo-vectorizer (`services/photo-vectorizer/`) are **separate systems** with **no direct imports** between them.

| Component | Sandbox Location | Photo-Vectorizer Location | Relationship |
|-----------|------------------|---------------------------|--------------|
| Edge detection | `vectorizer_phase3.py` (Canny) | `edge_to_dxf.py` (Canny) | **PARALLEL IMPLEMENTATIONS** |
| Morphological gap closing | `vectorizer_phase3.py` | `light_line_body_extractor.py` | **PARALLEL IMPLEMENTATIONS** |
| DXF R12 export | `dxf_compat.py` | `edge_to_dxf.py` (inline) | **PARALLEL IMPLEMENTATIONS** |
| Scale calibration | `calibration/pixel_calibrator.py` | `calibrate_carlos_jumbo.py` | **DIVERGENT** — different approaches |
| Contour classification | `classifiers/grid_zone/` | None | **SANDBOX-ONLY** |
| ML classification | `vectorizer_phase3.py` (RandomForest) | None | **SANDBOX-ONLY** |
| Blueprint PDF handling | `vectorizer_phase3.py` | `light_line_body_extractor.py` | **DIVERGENT** — different techniques |

### Borrowing Direction

**Direction unclear from current evidence.** Git history shows:
- `light_line_body_extractor.py` created April 1, 2026 (commit 14f68241)
- `edge_to_dxf.py` evolved separately with focus on pixel-level LINE entity export
- Sandbox vectorizer_phase3.py was last significantly modified March 9, then again April 5

The morphological gap closing technique appears in both, but no evidence of direct copy. More likely: same engineer implemented similar approach in both locations for different use cases.

### Functional Differences

| Feature | Sandbox (vectorizer_phase3) | Photo-Vectorizer (light_line_body_extractor) |
|---------|----------------------------|---------------------------------------------|
| Output type | Classified contours with categories | Raw body contours only |
| Entity count | 4,000-40,000 per file | 120-289 per file (semantic) |
| Target use | Full blueprint with sections | Body outline extraction only |
| Scale method | ML + OCR + reference features | Inversion + dimension filter |

---

## Task 2.3 — Entry Points and CLI Tools

### CLI Tools Inventory

| Script | Input | Output | Syntax Check | API Endpoint |
|--------|-------|--------|--------------|--------------|
| `vectorizer_phase3.py` | PDF/image path | DXF + JSON | PASS | `/api/blueprint/phase3/extract` |
| `run_phase4.py` | PDF path | Linked dimensions | PASS | `/api/blueprint/phase4/process` |
| `debug_ocr.py` | Image path | Console output | PASS | None |
| `dimension_extractor.py` | Image path | JSON | PASS | None |
| `extract_dimensions.py` | PDF path | JSON | PASS | None |
| `train_classifier.py` | Blueprint directory | Model file | PASS | None |

### CLI Usage Examples

```bash
# Phase 3 extraction
python vectorizer_phase3.py input.pdf --output output.dxf --tier STANDARD

# Phase 4 dimension linking
python run_phase4.py input.pdf --debug --json

# OCR debugging
python debug_ocr.py input.png

# Dimension extraction
python dimension_extractor.py input.png output.json

# Classifier training
python train_classifier.py path/to/blueprints/
```

---

## Task 2.4 — Test Coverage

### Test Discovery Results

```
181 tests collected in 6.28s
```

### Test File Inventory

| Test File | Target Module | Tests | Status |
|-----------|---------------|-------|--------|
| `test_annotation_layer.py` | `phase4/annotations/` | 19 | References sandbox |
| `test_arrow_detector.py` | `phase4/arrow_detector.py` | 33 | References sandbox |
| `test_batch_blueprints.py` | `classifiers/grid_zone/` | 1 | References sandbox |
| `test_dimension_linker.py` | `phase4/dimension_linker.py` | 18 | References sandbox |
| `test_grid_zone_classifier.py` | `classifiers/grid_zone/` | 38 | References sandbox |
| `test_leader_associator.py` | `phase4/leader_associator.py` | 35 | References sandbox |
| `test_ocr_integration.py` | `vectorizer_phase3.py` | 1 | References sandbox |
| `test_photo_pipeline_trial.py` | `vectorizer_enhancements.py` | 1 | References sandbox |
| `test_pipeline.py` | `phase4/pipeline.py` | 14 | References sandbox |
| `test_pixel_calibration.py` | `calibration/` | 1 | References sandbox |
| `test_sheet_type_detection.py` | `vectorizer_phase3.py` | 18 | References sandbox |
| `test_strat_grid.py` | `classifiers/grid_zone/` | 1 | References sandbox |

### Test Coverage Notes

- All tests reference sandbox-only code
- No tests reference main-repo code directly
- No tests reference removed or renamed functions (discovery passes cleanly)
- Phase 4 tests are most comprehensive (100+ tests per VECTORIZER_UPGRADE_PLAN.md)

---

## Task 2.5 — Documentation Reliability

### VECTORIZER_UPGRADE_PLAN.md (docs/)

| Claim | Code Verification | Status |
|-------|-------------------|--------|
| "Current Vectorizer Version: 4.0.0" | `vectorizer_phase3.py` declares "Version: 3.6.0" | **MISMATCH** |
| "Phase 4.0 Complete" with ArrowDetector, LeaderLineAssociator, DimensionLinker, BlueprintPipeline | All classes exist in `phase4/` | **VERIFIED** |
| "100 tests passing" | 181 tests collected | **EXCEEDS claim** |
| "Rating: 8.0/10" | No runtime verification possible | Cannot verify |

**Key discrepancy:** Documentation claims v4.0.0, code declares v3.6.0. The Phase 4.0 components exist but are not integrated into the main vectorizer file.

### BATCH_CLASSIFICATION_REPORT.md

| Claim | Code Verification | Status |
|-------|-------------------|--------|
| "GridZoneClassifier with ELECTRIC_GUITAR_GRID" | `classifiers/grid_zone/classifier.py` exists, `ELECTRIC_GUITAR_GRID` defined in `zones.py` | **VERIFIED** |
| "100% processing success rate" | Cannot verify without running | Claim not contradicted |
| "28 blueprints tested" | Test data not in repository | Cannot verify |

### CALIBRATION_REPORT.md

| Claim | Code Verification | Status |
|-------|-------------------|--------|
| "Pixel-to-inch calibration with contour analysis" | `calibration/pixel_calibrator.py` exists | **VERIFIED** |
| "0 Good detections" | Report admits failure | **HONEST** |
| "Most calibration issues are due to unknown paper size" | `CalibrationMethod.PAPER_SIZE` exists in code | **CONSISTENT** |

**Significant finding:** The calibration report honestly reports 0 good detections out of 33 blueprints, indicating the calibration module was experimental and not production-ready at time of report (March 6).

### DIMENSIONS_REPORT.md

| Claim | Code Verification | Status |
|-------|-------------------|--------|
| "OCR Available: No (pytesseract not installed)" | `dimension_extractor.py` imports EasyOCR, not pytesseract | **OUTDATED** |
| "Scale Length Found: 9 (32%)" | Cannot verify | Claim not contradicted |
| "Body Dimensions Found: 0" | Report admits failure | **HONEST** |

---

## Task 2.6 — Sample Outputs

### Root-Level Test Files

| File | Entities | Layers | Size | Quality Category |
|------|----------|--------|------|------------------|
| `test_dreadnought_phase5b.dxf` | 2,409 | 3 | 398 KB | Clean extraction |
| `test_dreadnought_phase5b_primitives.dxf` | N/A (subdir) | — | — | — |
| `test_lespaul_phase5c.dxf` | 7,370 | 3 | 1.2 MB | Clean extraction |
| `test_lespaul_phase5c_primitives.dxf` | N/A (subdir) | — | — | — |

### test_output/ Directory

| File | Entities | Layers | Size | Quality Category |
|------|----------|--------|------|------------------|
| `A003-Dreadnought-MM_phase3.dxf` | 4,133 | 3 | 670 KB | Clean extraction |
| `A003-Dreadnought-MM_phase3_primitives.dxf` | 42,296 | 3 | 6.6 MB | Pixel dump (high entity count) |
| `Gibson-Les-Paul-59-Complete_phase3.dxf` | 7,370 | 3 | 1.2 MB | Clean extraction |
| `Gibson-Les-Paul-59-Complete_phase3_primitives.dxf` | 7,658 | 3 | 1.2 MB | Clean extraction |
| `cuatro puertoriqueño_phase3.dxf` | 14,921 | 3 | 2.4 MB | Mixed (high count) |
| `cuatro puertoriqueño_phase3_primitives.dxf` | 37,866 | 3 | 6.0 MB | Pixel dump |

### output/ukulele/ Directory

| File | Entities | Layers | Size | Quality Category |
|------|----------|--------|------|------------------|
| `01 Ukulele Crown Sander_phase3.dxf` | 1,440 | 3 | 233 KB | Clean extraction |
| `01 Ukulele Crown Sander_phase3_primitives.dxf` | 10,534 | 3 | 1.6 MB | Mixed |
| `Soprano-Ukelele-MM_phase3.dxf` | 1,172 | 3 | 193 KB | Clean extraction |
| `Soprano-Ukelele-MM_phase3_primitives.dxf` | 20,699 | 3 | 3.2 MB | Pixel dump |
| `Soprano_ukulele_en_phase3.dxf` | 1,565 | 3 | 256 KB | Clean extraction |
| `Soprano_ukulele_en_phase3_primitives.dxf` | 20,539 | 3 | 3.2 MB | Pixel dump |
| `Ukelele-Concert-MM_phase3.dxf` | 976 | 3 | 159 KB | Clean extraction |
| `Ukelele-Concert-MM_phase3_primitives.dxf` | 3,292 | 3 | 511 KB | Mixed |

### Quality Categories Explained

- **Clean extraction**: 1,000-8,000 entities, reasonable file size, semantic structure
- **Mixed**: 10,000-20,000 entities, may include noise alongside useful geometry
- **Pixel dump**: 20,000+ entities, likely capturing every edge pixel rather than clean contours

### Layer Structure (consistent across all files)

All files use 3 layers (based on grep count). Standard sandbox layer names per `vectorizer_phase3.py`:
- `BODY_OUTLINE`
- `CAVITIES`
- `DETAILS` (or similar)

---

## Task 2.7 — March 6 Technology Location

### Investigation Summary

The "March 6 working technology" refers to the vectorizer state that achieved 8.0/10 rating, documented in:
- `docs/PHASE_2_3_IMPLEMENTATION_PLAN.md` (dated 2026-03-06)
- Commit `bed5d0ec` "docs(blueprint): add March 6 session log to vectorizer plan"

### Git History Analysis

| Date | Commit | File | Change |
|------|--------|------|--------|
| 2026-03-04 | 6cb7610d | `vectorizer_phase3.py` | Bump to v3.6.0, OCR integration |
| 2026-03-06 | 234afbd7 | `vectorizer_phase3.py` | Add SIMPLE extraction mode |
| 2026-03-06 | 811aee36 | Multiple | Add pixel calibration module + grid zone classifier |
| 2026-03-08 | Multiple | `vectorizer_phase3.py` | Add specs, fix bugs |
| 2026-03-09 | a51d0418 | `vectorizer_phase3.py` | Phase 3.7 enhancements |
| 2026-04-01 | 14f68241 | `light_line_body_extractor.py` | **NEW FILE** in photo-vectorizer |
| 2026-04-03 | 04735bd4 | `vectorizer_phase3.py` | Add --raw mode "restoring March 2026 fidelity" |
| 2026-04-05 | cb0761ed | `vectorizer_phase3.py` | Phase 5G body contour height ceiling |

### Location of March 6 Technology

**Finding:** The March 6 technology exists in **git history**, specifically commits around 6cb7610d through a51d0418. The current sandbox state (April 5) includes post-March modifications that changed behavior.

The commit message `04735bd4 "feat: add --raw extraction mode restoring March 2026 fidelity"` explicitly acknowledges that:
1. March 2026 fidelity was **lost** by April 3
2. A `--raw` extraction mode was added to **restore** it
3. The raw mode produces 1,150,754 LINE segments (per commit message)

### Comparison: Sandbox vs Photo-Vectorizer Output

| System | Entity Count (cuatro) | Approach |
|--------|----------------------|----------|
| Sandbox `vectorizer_phase3.py` | ~129,000+ | ML classification, dual-pass |
| Photo-vectorizer `light_line_body_extractor.py` | 120-289 | Body-only, dimension filter |
| Sandbox `--raw` mode | 1,150,754 | No classification, all edges |

**Conclusion:** The "March 6 working technology" that produced semantic structure (hundreds of entities) is **NOT the same** as what's in the current sandbox. The sandbox produces much higher entity counts.

The semantic extraction (289 for Gibson L0, 120 for Dreadnought) comes from `light_line_body_extractor.py` in photo-vectorizer, which was created **April 1** — after the March 6 work but designed with a different philosophy (body-only extraction vs full classification).

### Uncertainty Flag

**UNCLEAR:** Whether the March 6 8.0/10 rating refers to:
1. The sandbox vectorizer at that time (which has been modified since), OR
2. A conceptual achievement that was never fully recorded in code, OR
3. A specific combination of parameters that was later overwritten

The `--raw` mode restoration suggests awareness that something was lost, but the resulting 1.1M entities doesn't match the "semantic structure" described for March 6 work.

---

## Phase 2 Summary: Component Classification

Based on the Phase 1 context (production-active vs abandoned) and Phase 2 cross-reference:

### Production-Active (currently imported by main repo)

| File | Last Modified | Evidence |
|------|---------------|----------|
| `vectorizer_phase3.py` | 2026-04-05 | Imported by `constants.py` |
| `vectorizer_phase2.py` | 2026-03-04 | Imported by `constants.py` |
| `analyzer.py` | 2026-03-06 | Imported by `constants.py` |
| `phase4/pipeline.py` | 2026-03-09 | Imported by `constants.py` |
| `dxf_compat.py` | 2026-04-02 | Used by vectorizers |
| `classifiers/` | 2026-03-09 | Imported by vectorizer_phase3 |

### Pre-April 5 Work (stable, possibly superseded)

| File | Last Modified | Notes |
|------|---------------|-------|
| `vectorizer_enhancements.py` | 2026-03-09 | Optional imports, stable |
| `calibration/` | 2026-03-09 | 0/33 good detections per report |
| `dimension_extractor.py` | 2026-03-04 | Superseded by calibration/? |
| `extract_dimensions.py` | 2026-03-09 | Duplicate functionality |

### April 5-21 Work — Needs Ross's Classification

| File | Last Modified | Notes |
|------|---------------|-------|
| `vectorizer_phase3.py` | 2026-04-05 | Phase 5G modifications |
| `dxf_compat.py` | 2026-04-02 | R12 standard enforcement |
| `dxf_postprocessor.py` | 2026-04-03 | Arc fitting, scale application |
| `phase4/annotations/exporter.py` | 2026-04-03 | Annotation layer export |

### Unclear Classification — Needs Ross's Input

- `calibration/` — Report shows 0/33 success, but files still exist and are importable
- `dimension_extractor.py` vs `extract_dimensions.py` — Duplicate functionality, unclear which is canonical
- `train_classifier.py` — Training script, unclear if model file exists or is used

---

## Recommendations (Report Only — No Action Taken)

1. **Version reconciliation needed:** Documentation claims v4.0.0, code declares v3.6.0. One should be updated.

2. **Calibration module status:** The CALIBRATION_REPORT.md shows 0/33 good detections. Either fix or archive.

3. **Duplicate dimension extractors:** `dimension_extractor.py` and `extract_dimensions.py` serve similar purposes. Consider consolidation.

4. **March 6 technology preservation:** If the March 6 semantic extraction is valuable, it may need to be recovered from git history and explicitly preserved, as current sandbox produces different output characteristics.

5. **Photo-vectorizer integration:** The sandbox and photo-vectorizer implement similar techniques independently. Consider whether consolidation is desirable.

---

**Phase 2 Complete.**
