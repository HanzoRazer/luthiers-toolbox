# Morphology Harvest Governance Collision Audit

**Date:** 2026-05-16  
**Sprint:** IBG Semantic Morphology Harvest Pass 0A  
**Status:** AUDIT COMPLETE  
**Auditor:** Claude Code

---

## Executive Summary

This audit identifies existing systems that may collide with the proposed Morphology Harvest Pass. The repo has **significant existing infrastructure** for dimension extraction, PDF processing, calibration, and corpus management. The harvest implementation must reuse or extend these systems rather than duplicate them.

**Key finding:** Most harvest categories already have partial or full owners. The harvest module should be a **thin coordination layer** that reuses existing extractors and schemas, not a parallel extraction system.

---

## Collision Matrix

| Category | Existing System | Path | Authority | Recommendation | Risk |
|----------|-----------------|------|-----------|----------------|------|
| PDF inventory | DXFInventory | `services/blueprint-import/sandbox/text_geometry_eval/metrics/dxf_inventory.py` | Sandbox | **Extend** for PDF | LOW |
| OCR text extraction | debug_ocr.py, pytesseract usage | `services/blueprint-import/debug_ocr.py` | Production | **Reuse** | HIGH if duplicated |
| Dimension extraction | GuitarDimensions + Phase 4 | `services/blueprint-import/calibration/dimension_extractor.py`, `phase4/` | Production | **Reuse** | HIGH if duplicated |
| Dimension-to-geometry association | DimensionLinker, LeaderAssociator | `services/blueprint-import/phase4/dimension_linker.py` | Production | **Reuse** | CRITICAL |
| Body evidence objects | BodyEvidence | `services/api/app/instrument_geometry/body/ibg/body_grid/body_grid_schema.py` | Production | **Extend** | LOW |
| Body Grid descriptors | MorphologyDescriptor | `body_grid/morphology_descriptor.py` | Production | **Integrate** | LOW |
| BOE review annotations | BOE session model | `tools/body-outline-editor.html`, IBG/BOE boundary | Production | **Avoid collision** | MEDIUM |
| Human review manifests | regression_corpus/manifest.json | `tests/regression_corpus/manifest.json` | Infrastructure | **Extend pattern** | LOW |
| Calibration / scale metadata | PixelCalibrator, CalibrationResult | `services/blueprint-import/calibration/pixel_calibrator.py` | Production | **Reuse** | HIGH if duplicated |
| Corpus registry | MORPHOLOGY_CORPUS_STANDARD | `docs/governance/MORPHOLOGY_CORPUS_STANDARD.md` | Governance | **Follow** | LOW |
| Instrument spec registry | InstrumentSpec, INSTRUMENT_SPECS | `services/api/app/instrument_geometry/instrument_specs.py`, `ibg/instrument_body_generator.py` | Production | **Extend** | MEDIUM |
| Fixture conventions | data_registry pattern | `services/api/app/data_registry/` | Production | **Follow pattern** | LOW |
| Overlay generation | contour_debug_overlay, overlay_exporter | `services/photo-vectorizer/contour_debug_overlay.py`, `body_grid/overlay_exporter.py` | Mixed | **Reuse body_grid** | LOW |
| PDF parsing (fitz/PyMuPDF) | vectorizer_phase3.py, edge_to_dxf.py | `services/blueprint-import/`, `services/photo-vectorizer/` | Production | **Reuse existing deps** | LOW |

---

## Detailed Findings

### 1. PDF Inventory

**Existing:** `DXFInventory` in `services/blueprint-import/sandbox/text_geometry_eval/metrics/dxf_inventory.py`

```python
@dataclass
class DXFInventory:
    file_path: str
    file_size_bytes: int
    dxf_version: str
    total_entities: int
    entity_types: Dict[str, int]
    layers: Dict[str, int]
    line_lengths_mm: List[float]
    coord_bbox: Tuple[float, float, float, float]
```

**Status:** Sandbox, but mature pattern

**Recommendation:** Create `PDFInventory` following same pattern. Can live in harvest module but should share base class or pattern with DXFInventory.

---

### 2. Dimension Extraction

**Existing owners:**

1. **GuitarDimensions** (`calibration/dimension_extractor.py:29-78`)
   - Body length, width, bout widths, waist, neck pocket
   - Calibration method tracking
   - Pixel measurements preservation

2. **Phase 4 LinkedDimensions** (`phase4/dimension_linker.py:29-66`)
   - Text-to-geometry association
   - Unmatched text tracking
   - Association rate statistics

**Status:** Production, comprehensive

**Recommendation:** **DO NOT create new dimension schema.** Harvest should produce `GuitarDimensions` or extend it. Use Phase 4 for leader line association.

---

### 3. Phase 4 Dimension-to-Geometry Association

**Existing:** Complete pipeline in `services/blueprint-import/phase4/`

```
phase4/
├── arrow_detector.py      # Arrow/arrowhead detection
├── leader_associator.py   # Links arrows to dimension text
├── dimension_linker.py    # Orchestrator
├── pipeline.py            # End-to-end processing
└── annotations/           # Export formats
```

**API:**
```python
from phase4 import BlueprintPipeline
pipeline = BlueprintPipeline()
result = pipeline.process("blueprint.pdf")
```

**Status:** Production, version 4.0.0

**Recommendation:** **CRITICAL — DO NOT DUPLICATE.** Harvest must call Phase 4 pipeline, not rebuild extraction logic.

---

### 4. Calibration System

**Existing:** `services/blueprint-import/calibration/`

- `PixelCalibrator` — Multi-method calibration (scale length, ruler, paper size, heuristic)
- `ScaleReferenceDetector` — Scale length detection
- `CalibratedDimensionExtractor` — Dimension extraction with calibration
- `calibration_integration.py` — Integration with vectorizer

**Status:** Production

**Recommendation:** Harvest must use existing calibration. Add `calibration_method` field to harvest records linking to CalibrationResult.

---

### 5. Body Evidence / Body Grid

**Existing:** Just created in Body Grid 1A

- `BodyEvidence` — Adapter layer for body evidence from multiple sources
- `MorphologyDescriptor` — Full morphology analysis output
- `MorphologyAnalyzer` — Analysis engine

**Status:** Production (commit 099397fe)

**Recommendation:** Harvest records should be convertible to `BodyEvidence`. Add adapter method `HarvestRecord.to_body_evidence()`.

---

### 6. BOE Integration Boundary

**Existing:** Defined in `docs/architecture/IBG_BOE_BOUNDARY_MODEL.md`

```
IBG: SOLVER AUTHORITY
  - Owns: Lutherie math, constraint solving, gap bridging
  - Produces: Confidence-weighted geometry

BOE: HUMAN AUTHORITY
  - Owns: Final geometry approval
  - Can: Edit any IBG output
```

**Status:** Canonical architecture

**Recommendation:** Harvest is IBG-side. Human review in harvest flows to BOE for visual approval. Do not create parallel review UI.

---

### 7. Corpus Registry Pattern

**Existing:** `docs/governance/MORPHOLOGY_CORPUS_STANDARD.md`

Defines structure:
```
morphology_corpus/
├── specs/
├── reference_outlines/
├── validation_cases/
└── corrections/
```

**Status:** Governance doc (active)

**Recommendation:** Harvest outputs should follow this structure. Add `harvested_plans/` directory to corpus structure.

---

### 8. Instrument Spec Registry

**Existing:**

1. `INSTRUMENT_SPECS` in `ibg/instrument_body_generator.py` — 4 specs with constraints
2. `InstrumentSpec` in `instrument_specs.py` — 18+ body dimension specs
3. `instrument_model_registry.json` — Extended model registry

**Status:** Production, but fragmented

**Recommendation:** Harvest should normalize to `InstrumentSpec` pattern. Use `instrument_family_normalized` to match existing specs.

---

### 9. Overlay Generation

**Existing:**

1. `body_grid/overlay_exporter.py` — Zone/primitive overlays with PIL
2. `contour_debug_overlay.py` — Contour visualization
3. `dual_pass_overlay.py` — Side-by-side comparison overlays

**Status:** Production

**Recommendation:** Reuse `body_grid/overlay_exporter.py` for body overlays. Extend for dimension text overlays.

---

### 10. PDF Parsing Dependencies

**Existing usage:**

| Dependency | Used In | Purpose |
|------------|---------|---------|
| PyMuPDF/fitz | vectorizer_phase3.py, edge_to_dxf.py | PDF rasterization |
| pdf2image | debug_ocr.py, extract_dimensions.py | PDF to image |
| pytesseract | debug_ocr.py, phase4 | OCR |
| easyocr | Optional in vectorizer | Alternative OCR |

**Status:** Production dependencies

**Recommendation:** Use existing fitz/pdf2image patterns. Do not add new PDF dependencies without justification.

---

### 11. Manifest Pattern

**Existing:** `tests/regression_corpus/manifest.json`

```json
{
  "manifest_version": "1.1.0",
  "status": "INFRASTRUCTURE_READY",
  "governance_doc": "docs/governance/...",
  "artifacts": [
    {
      "id": "DREADNOUGHT_REFERENCE",
      "purpose": "...",
      "status": "REQUIRED_FUTURE",
      "expected_accuracy": {...}
    }
  ]
}
```

**Status:** Infrastructure pattern

**Recommendation:** Harvest manifest should follow this pattern. Add `harvest_status`, `feature_categories`, `review_status` fields.

---

## Implementation Directive

Based on this audit, the Morphology Harvest implementation should:

### REUSE (do not recreate):

1. **Phase 4 pipeline** for dimension-to-geometry association
2. **GuitarDimensions** schema for extracted dimensions
3. **PixelCalibrator** for scale/calibration
4. **fitz/pdf2image** for PDF parsing
5. **pytesseract** for OCR
6. **overlay_exporter.py** for body overlays

### EXTEND (add to existing):

1. **DXFInventory pattern** → create PDFInventory
2. **BodyEvidence** → add `from_harvest_record()` adapter
3. **regression_corpus manifest** → harvest manifest format
4. **MORPHOLOGY_CORPUS_STANDARD** → add harvested_plans/ directory

### CREATE NEW (no existing owner):

1. **HarvestRecord schema** — coordinates evidence from multiple extractors
2. **PDF inventory tool** — configurable corpus root scanner
3. **Feature category schema** — neck_pocket, fretboard, headstock, etc.
4. **Review manifest** — tracks human review status per plan
5. **Harvest coordinator** — thin layer calling existing extractors

### AVOID (would cause collision):

1. New dimension extraction logic (use Phase 4)
2. New calibration system (use calibration/)
3. New OCR wrapper (use debug_ocr patterns)
4. Parallel review UI (flows to BOE)
5. New instrument registry (extend existing)

---

## Recommended Module Structure

```
services/api/app/instrument_geometry/body/ibg/morphology_harvest/
├── __init__.py
├── schema.py              # HarvestRecord, FeatureCategories (NEW)
├── pdf_inventory.py       # PDFInventory following DXFInventory pattern (EXTEND)
├── harvest_coordinator.py # Thin layer calling Phase 4, calibration (NEW)
├── body_evidence_adapter.py # HarvestRecord → BodyEvidence (EXTEND)
├── review_manifest.py     # Review tracking (NEW, follows manifest pattern)
└── README.md
```

**Not needed (use existing):**
- ~~dimension_parser.py~~ → use Phase 4
- ~~semantic_classifier.py~~ → use variant_grammar.py
- ~~overlay_exporter.py~~ → use body_grid/overlay_exporter.py

---

## Decision Matrix

| Harvest Dev Order Category | Existing Owner | Action |
|---------------------------|----------------|--------|
| PDF inventory | None (DXF pattern exists) | CREATE following pattern |
| Body data | BodyEvidence, MorphologyDescriptor | EXTEND |
| Neck pocket data | GuitarDimensions.neck_pocket_* | EXTEND schema |
| Neck system data | None | CREATE (narrow) |
| Fretboard data | fret_math.py, scale_lengths.json | EXTEND |
| Headstock data | None | CREATE (narrow) |
| Hardware/cavity data | GuitarDimensions, FeatureRoutes | EXTEND |
| Alignment/scale relationships | instrument_specs.py | EXTEND |
| Human review manifest | regression_corpus manifest | EXTEND pattern |
| Overlay outputs | body_grid/overlay_exporter | REUSE |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Duplicate dimension extraction | HIGH | Use Phase 4 pipeline |
| Duplicate calibration | HIGH | Use calibration/ module |
| Parallel review system | MEDIUM | Route to BOE |
| Schema fragmentation | MEDIUM | Extend existing schemas |
| New dependencies | LOW | Use existing fitz/pytesseract |

---

## Conclusion

The Morphology Harvest Pass should be implemented as a **thin coordination layer** that:

1. Inventories PDFs (new tool, following existing pattern)
2. Calls existing Phase 4 for dimension extraction
3. Calls existing calibration for scale
4. Produces HarvestRecords that can convert to BodyEvidence
5. Generates review manifests following existing pattern
6. Routes human review needs to BOE

**Do not rebuild extraction infrastructure.**

The goal is semantic coordination, not extraction duplication.

---

## Semantic Vocabulary / Convention Alignment Addendum

This addendum documents existing terminology across extraction, calibration, and morphology systems. The Harvest module MUST reuse this vocabulary to prevent terminology drift.

### Systems Compared

| System | Path | Primary Schema |
|--------|------|----------------|
| Body Grid | `body_grid/*.py` | `NormalizedPoint`, `ZoneAssignment`, `MorphologyDescriptor` |
| Instrument Specs | `instrument_specs.py` | `BodyDimensions`, `BODY_DIMENSIONS` dict |
| IBG Generator | `instrument_body_generator.py` | `INSTRUMENT_SPECS`, `SolvedBodyModel` |
| Calibration | `calibration/dimension_extractor.py` | `GuitarDimensions` |
| Phase 4 | `phase4/dimension_linker.py` | `LinkedDimensions`, `AssociatedDimension` |

---

### 1. Coordinate Normalization Conventions

**Canonical convention (body_grid/body_grid_schema.py):**
```
y_norm: 0.0 at butt/tail, 1.0 at neck end
x_norm: signed distance from centerline (negative=bass/left, positive=treble/right)
```

**Alignment status:**
| Field | System | Convention | Status |
|-------|--------|------------|--------|
| `y_norm` | body_grid | 0.0=butt, 1.0=neck | CANONICAL |
| `waist_y_norm` | instrument_specs | fraction of body length | ALIGNED |
| raw mm coords | GuitarDimensions | no normalization | COMPATIBLE (conversion available) |
| pixel coords | Phase 4 | raw pixel space | REQUIRES CALIBRATION |

**Harvest directive:** All normalized coordinates MUST use `y_norm` 0-1 with 0=butt, 1=neck. Use `GridNormalizer` for conversion.

---

### 2. Unit / Scale Conventions

**Primary unit:** millimeters (`_mm` suffix)

**Alignment status:**
| System | Primary Unit | Secondary | Status |
|--------|--------------|-----------|--------|
| body_grid | mm | - | CANONICAL |
| instrument_specs | mm | - | ALIGNED |
| GuitarDimensions | mm | inches (dual) | ALIGNED (mm preferred) |
| Phase 4 | pixels | mm via calibration | REQUIRES CALIBRATION |

**Harvest directive:** All harvested dimensions MUST be in mm. Include `calibration_method` field linking to `CalibrationResult`.

---

### 3. Body Dimension Terminology

**Aligned terms (use these):**

| Term | Used By | Meaning |
|------|---------|---------|
| `body_length_mm` | BodyDimensions, GuitarDimensions, INSTRUMENT_SPECS | Total body length heel to tail |
| `upper_bout_width_mm` | BodyDimensions, GuitarDimensions | Maximum width in upper third |
| `waist_width_mm` | BodyDimensions, GuitarDimensions | Minimum width at body waist |
| `lower_bout_width_mm` | BodyDimensions, GuitarDimensions | Maximum width in lower half |
| `scale_length_mm` | INSTRUMENT_SPECS, GuitarDimensions | Fret scale length |

**Minor naming drift (normalize on harvest):**

| Source Term | Normalized Term | Owning System | Notes |
|-------------|-----------------|---------------|-------|
| `lower_bout_mm` | `lower_bout_width_mm` | INSTRUMENT_SPECS.expected_dimensions | Missing `_width` suffix |
| `upper_bout_mm` | `upper_bout_width_mm` | INSTRUMENT_SPECS.expected_dimensions | Missing `_width` suffix |
| `waist_mm` | `waist_width_mm` | INSTRUMENT_SPECS.expected_dimensions | Missing `_width` suffix |
| `body_width_mm` | `lower_bout_width_mm` | GuitarDimensions | Semantic alias (body width = lower bout for most guitars) |

**Harvest directive:** Use normalized terms with full `_width_mm` suffix. When ingesting from INSTRUMENT_SPECS expected_dimensions, map `lower_bout_mm` → `lower_bout_width_mm`.

---

### 4. Zone Vocabulary

**Canonical zone names (zones.py ZoneId enum):**

```
UPPER_BOUT, UPPER_BOUT_CORNER, UPPER_SHOULDER
WAIST, WAIST_TRANSITION_UPPER, WAIST_TRANSITION_LOWER
LOWER_BOUT, LOWER_BOUT_CORNER, LOWER_BOUT_BELLY
BUTT_END, BUTT_CORNER
NECK_JOINT, NECK_POCKET
HORN_LEFT, HORN_RIGHT, CUTAWAY_LEFT, CUTAWAY_RIGHT
```

**Implicit zones in other systems:**

| System | Zone Reference | Alignment |
|--------|---------------|-----------|
| BodyDimensions | `upper_bout_width_mm`, `waist_width_mm`, `lower_bout_width_mm` | ALIGNED (field names match zone names) |
| GuitarDimensions | same field names | ALIGNED |
| Phase 4 | no zone concept | N/A (dimension-only) |

**Harvest directive:** Zone references MUST use `ZoneId` enum values from `body_grid/zones.py`. Do not invent new zone names.

---

### 5. Centerline Representation

**Canonical (body_grid_schema.py):**
```python
@dataclass
class CenterlineDescriptor:
    x_mm: float              # X position in mm
    source: str              # How centerline was determined
    confidence: float        # 0.0-1.0
    symmetry_score: float    # How symmetric the body is around this line
```

**Harvest directive:** All centerline data MUST include `source` and `confidence`. Valid sources: `"computed_from_bbox"`, `"computed_from_landmarks"`, `"spec_default"`, `"user_override"`.

---

### 6. Body Family / Morphology Class Descriptors

**Canonical classes (variant_grammar.py BodyMorphologyClass):**

```
ROUNDED_ACOUSTIC     # Dreadnought, OM, Parlor
ROUNDED_SINGLE_CUT   # Les Paul, ES-335
ROUNDED_DOUBLE_CUT   # SG, PRS
SLAB_BODY            # Telecaster, Stratocaster
ANGULAR_WEDGE        # Explorer, Flying V
OFFSET_DOUBLE_CUT    # Jazzmaster, Jaguar
HYBRID_FORM          # Mixed characteristics
CLASSICAL_FIGURE_8   # Classical guitar proportions
UNCLASSIFIED         # Could not match rules
```

**Mapping from INSTRUMENT_SPECS families:**

| INSTRUMENT_SPECS family | BodyMorphologyClass | Notes |
|------------------------|---------------------|-------|
| `dreadnought` | `ROUNDED_ACOUSTIC` | Direct map |
| `stratocaster` | `SLAB_BODY` | Direct map |
| `cuatro_venezolano` | `ROUNDED_ACOUSTIC` | Small acoustic |

**Harvest directive:** Use `BodyMorphologyClass` for classification. Store `INSTRUMENT_SPECS` family as `instrument_family_normalized` field for reference.

---

### 7. Evidence Source Tracking

**Canonical sources (body_grid_schema.py EvidenceSource):**

```
VECTORIZER_DXF        # Extracted from vectorized blueprint DXF
CONSTRAINT_EXTRACTOR  # IBG constraint extractor output
PHOTO_EXTRACTION      # Extracted from photograph
USER_INPUT            # Manual user entry
SPEC_DEFAULT          # Default from instrument spec
```

**Phase 4 annotation sources (phase4/annotations/base.py AnnotationSource):**

```
DETECTED_OCR          # OCR text detection
DETECTED_GEOMETRY     # Geometry analysis
INFERRED              # Derived from other data
USER_CORRECTED        # Human correction
```

**Harvest directive:** New harvest evidence type: `HARVEST_INGESTION`. HarvestRecord MUST track original source via `upstream_source` field containing the Phase 4/calibration source.

---

### 8. Review State Conventions

**Regression corpus manifest pattern:**

```json
{
  "status": "REQUIRED_FUTURE" | "READY" | "VALIDATED" | "FAILED",
  "expected_accuracy": {...}
}
```

**Harvest review states (proposed):**

| State | Meaning |
|-------|---------|
| `PENDING_REVIEW` | Awaiting human review |
| `APPROVED` | Human approved, no edits |
| `APPROVED_WITH_EDITS` | Human approved after correction |
| `REJECTED` | Human rejected, needs re-extraction |
| `DEFERRED` | Skipped for now, revisit later |

**Harvest directive:** Use review states above. Route all `APPROVED_WITH_EDITS` corrections to BOE for visual confirmation.

---

### 9. Confidence Scoring Convention

**Existing conventions:**

| System | Confidence Field | Range | Meaning |
|--------|-----------------|-------|---------|
| body_grid | `confidence` | 0.0-1.0 | Point/assignment confidence |
| GuitarDimensions | `calibration_confidence` | 0.0-1.0 | Scale confidence |
| Phase 4 | `confidence` | 0.0-1.0 | Association confidence |
| IBG solver | `SolvedBodyModel.confidence` | 0.0-1.0 | Overall solve confidence |

**Harvest directive:** All confidence values MUST be 0.0-1.0. Include separate fields for:
- `extraction_confidence` — how confident is the raw extraction
- `calibration_confidence` — how confident is the scale
- `classification_confidence` — how confident is the morphology class

---

### Vocabulary Alignment Summary

| Category | Status | Action for Harvest |
|----------|--------|-------------------|
| Coordinate normalization | ALIGNED | Use body_grid convention |
| Unit convention | ALIGNED | Use mm exclusively |
| Body dimension terms | MINOR DRIFT | Normalize on ingest |
| Zone vocabulary | ALIGNED | Use ZoneId enum |
| Centerline representation | ALIGNED | Use CenterlineDescriptor |
| Morphology classes | ALIGNED | Use BodyMorphologyClass |
| Evidence sources | REQUIRES EXTENSION | Add HARVEST_INGESTION |
| Review states | NEW | Define per addendum |
| Confidence scoring | ALIGNED | Use 0.0-1.0 range |

---

### Recommended HarvestRecord Schema Pattern

Based on vocabulary alignment, the HarvestRecord should include:

```python
@dataclass
class HarvestRecord:
    # Identity
    harvest_id: str
    source_pdf: str
    page_number: int
    
    # Normalized body dimensions (use canonical terms)
    body_length_mm: Optional[float]
    upper_bout_width_mm: Optional[float]
    waist_width_mm: Optional[float]
    lower_bout_width_mm: Optional[float]
    
    # Classification (use canonical classes)
    morphology_class: BodyMorphologyClass
    instrument_family_normalized: str  # From INSTRUMENT_SPECS
    
    # Provenance
    upstream_source: EvidenceSource     # Phase 4 / calibration
    calibration_method: str             # Link to CalibrationResult
    
    # Confidence (0.0-1.0)
    extraction_confidence: float
    calibration_confidence: float
    classification_confidence: float
    
    # Review state
    review_status: str  # PENDING_REVIEW, APPROVED, etc.
    
    # Conversion method
    def to_body_evidence(self) -> BodyEvidence:
        """Convert to BodyEvidence for Body Grid consumption."""
        ...
```

This schema reuses existing vocabulary, extends where necessary (evidence source, review states), and provides clean conversion to existing consumers.
