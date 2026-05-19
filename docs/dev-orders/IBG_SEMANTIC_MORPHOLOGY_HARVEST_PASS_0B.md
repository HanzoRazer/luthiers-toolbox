# IBG Semantic Morphology Harvest Pass 0B

**Date:** 2026-05-16  
**Sprint:** IBG Morphology Harvest  
**Status:** READY FOR IMPLEMENTATION  
**Governance:** Post-audit revision — implements as thin coordination layer

---

## Executive Summary

This dev order implements the Morphology Harvest Pass as a **thin coordination layer** that reuses existing extraction infrastructure. It does NOT rebuild dimension extraction, calibration, or OCR logic.

**Prerequisite:** `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` — read before implementation.

---

## Architectural Constraints

### MUST REUSE (no recreation):

| System | Authority | Harvest Role |
|--------|-----------|--------------|
| Phase 4 pipeline | Dimension-to-geometry association | CALLER |
| GuitarDimensions | Dimension schema | CONSUMER |
| PixelCalibrator | Scale calibration | CALLER |
| body_grid/* | Morphology analysis | CONSUMER |
| BodyEvidence | Evidence container | PRODUCER (via conversion) |

### MUST EXTEND (not duplicate):

| Pattern | Source | Extension |
|---------|--------|-----------|
| PDFInventory | DXFInventory pattern | New class following pattern |
| Review manifest | regression_corpus/manifest.json | Harvest-specific fields |
| EvidenceSource | body_grid_schema.py | Add `HARVEST_INGESTION` |

### MUST CREATE (no existing owner):

| Component | Purpose |
|-----------|---------|
| HarvestRecord | Coordinates evidence from multiple extractors |
| HarvestCoordinator | Thin orchestration layer |
| Review manifest generator | Human review tracking |

---

## Vocabulary Preservation Rules

All implementations MUST follow `MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` vocabulary alignment:

### Mandatory Term Mappings

```python
# When ingesting from INSTRUMENT_SPECS expected_dimensions:
TERM_NORMALIZATIONS = {
    "lower_bout_mm": "lower_bout_width_mm",
    "upper_bout_mm": "upper_bout_width_mm",
    "waist_mm": "waist_width_mm",
    "body_width_mm": "lower_bout_width_mm",  # semantic alias
}
```

### Forbidden Actions

1. ❌ Creating new zone names (use `ZoneId` enum)
2. ❌ Creating new morphology classes (use `BodyMorphologyClass` enum)
3. ❌ Creating new coordinate conventions (use `y_norm` 0-1, 0=butt)
4. ❌ Using inches in harvest output (mm only, calibration handles conversion)
5. ❌ Creating new dimension extraction logic (call Phase 4)

---

## Implementation Specification

### File Structure

```
services/api/app/instrument_geometry/body/ibg/morphology_harvest/
├── __init__.py
├── schema.py              # HarvestRecord, FeatureCategories
├── pdf_inventory.py       # PDFInventory (follows DXFInventory pattern)
├── harvest_coordinator.py # Thin orchestration layer
├── body_evidence_adapter.py # HarvestRecord.to_body_evidence()
├── review_manifest.py     # Review tracking
└── README.md
```

### 1. HarvestRecord Schema (`schema.py`)

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from ..body_grid.body_grid_schema import EvidenceSource
from ..body_grid.variant_grammar import BodyMorphologyClass


class ReviewStatus(Enum):
    """Review states for harvested records."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    APPROVED_WITH_EDITS = "approved_with_edits"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass
class HarvestRecord:
    """
    Coordinates morphology evidence from multiple extraction systems.
    
    This is a COORDINATION record, not an extraction result.
    All extraction is delegated to Phase 4, calibration, and body_grid.
    """
    # Identity
    harvest_id: str
    source_pdf: str
    page_number: int = 1
    
    # Normalized body dimensions (use canonical terms from governance audit)
    body_length_mm: Optional[float] = None
    upper_bout_width_mm: Optional[float] = None
    waist_width_mm: Optional[float] = None
    lower_bout_width_mm: Optional[float] = None
    waist_y_norm: Optional[float] = None  # 0-1, 0=butt
    
    # Scale
    scale_length_mm: Optional[float] = None
    
    # Classification (use canonical classes)
    morphology_class: Optional[BodyMorphologyClass] = None
    instrument_family_normalized: Optional[str] = None
    
    # Provenance (trace to upstream systems)
    upstream_source: EvidenceSource = EvidenceSource.VECTORIZER_DXF
    calibration_method: Optional[str] = None
    phase4_result_id: Optional[str] = None  # Link to LinkedDimensions
    
    # Confidence (0.0-1.0)
    extraction_confidence: float = 0.0
    calibration_confidence: float = 0.0
    classification_confidence: float = 0.0
    
    # Review state
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    reviewer_notes: List[str] = field(default_factory=list)
    
    # Raw data references (for traceability, not processing)
    raw_guitar_dimensions: Optional[Dict[str, Any]] = None
    raw_linked_dimensions: Optional[Dict[str, Any]] = None
    
    def to_body_evidence(self):
        """
        Convert to BodyEvidence for Body Grid consumption.
        
        This is the ONLY approved path from harvest to body_grid.
        """
        from ..body_grid.body_grid_schema import BodyEvidence, Landmark, NormalizedPoint
        
        landmarks = []
        
        # Convert harvested dimensions to landmarks
        if self.lower_bout_width_mm and self.body_length_mm:
            # Lower bout max point (estimate at y_norm=0.15)
            landmarks.append(Landmark(
                label="lower_bout_max",
                point=NormalizedPoint(
                    x_norm=self.lower_bout_width_mm / (2 * self.body_length_mm),
                    y_norm=0.15,
                ),
                source=self.upstream_source,
                confidence=self.extraction_confidence,
            ))
        
        if self.waist_width_mm and self.body_length_mm and self.waist_y_norm:
            landmarks.append(Landmark(
                label="waist_min",
                point=NormalizedPoint(
                    x_norm=self.waist_width_mm / (2 * self.body_length_mm),
                    y_norm=self.waist_y_norm,
                ),
                source=self.upstream_source,
                confidence=self.extraction_confidence,
            ))
        
        if self.upper_bout_width_mm and self.body_length_mm:
            landmarks.append(Landmark(
                label="upper_bout_max",
                point=NormalizedPoint(
                    x_norm=self.upper_bout_width_mm / (2 * self.body_length_mm),
                    y_norm=0.75,
                ),
                source=self.upstream_source,
                confidence=self.extraction_confidence,
            ))
        
        return BodyEvidence(
            landmarks=landmarks,
            source=self.upstream_source,
        )
```

### 2. PDFInventory (`pdf_inventory.py`)

```python
"""
PDF Inventory — following DXFInventory pattern from sandbox.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
import fitz  # PyMuPDF — existing dependency


@dataclass
class PDFInventory:
    """
    PDF file inventory for morphology harvest.
    
    Follows DXFInventory pattern from:
    services/blueprint-import/sandbox/text_geometry_eval/metrics/dxf_inventory.py
    """
    file_path: str
    file_size_bytes: int
    page_count: int
    has_text: bool
    has_images: bool
    dimensions_detected: bool = False
    blueprint_confidence: float = 0.0
    
    # Page-level details
    page_dimensions: List[Dict[str, float]] = field(default_factory=list)
    
    @classmethod
    def from_pdf(cls, pdf_path: str) -> "PDFInventory":
        """Create inventory from PDF file."""
        path = Path(pdf_path)
        
        doc = fitz.open(pdf_path)
        
        has_text = False
        has_images = False
        page_dims = []
        
        for page in doc:
            text = page.get_text()
            if text.strip():
                has_text = True
            
            images = page.get_images()
            if images:
                has_images = True
            
            rect = page.rect
            page_dims.append({
                "width_pt": rect.width,
                "height_pt": rect.height,
                "width_mm": rect.width * 0.352778,  # pt to mm
                "height_mm": rect.height * 0.352778,
            })
        
        doc.close()
        
        return cls(
            file_path=str(path),
            file_size_bytes=path.stat().st_size,
            page_count=len(page_dims),
            has_text=has_text,
            has_images=has_images,
            page_dimensions=page_dims,
        )


def scan_corpus(corpus_root: str, pattern: str = "**/*.pdf") -> List[PDFInventory]:
    """Scan corpus directory for PDF files."""
    root = Path(corpus_root)
    inventories = []
    
    for pdf_path in root.glob(pattern):
        try:
            inv = PDFInventory.from_pdf(str(pdf_path))
            inventories.append(inv)
        except Exception as e:
            print(f"  SKIP {pdf_path.name}: {e}")
    
    return inventories
```

### 3. HarvestCoordinator (`harvest_coordinator.py`)

```python
"""
Harvest Coordinator — Thin orchestration layer.

This coordinator CALLS existing extractors, it does NOT duplicate them.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import sys

# Add blueprint-import to path for Phase 4 access
sys.path.insert(0, str(Path(__file__).parents[6] / "services" / "blueprint-import"))

from .schema import HarvestRecord, ReviewStatus
from .pdf_inventory import PDFInventory


@dataclass
class HarvestResult:
    """Result of harvest operation."""
    record: Optional[HarvestRecord]
    success: bool
    error: Optional[str] = None
    phase4_available: bool = False
    calibration_available: bool = False


class HarvestCoordinator:
    """
    Thin coordination layer for morphology harvest.
    
    Delegates ALL extraction to:
    - Phase 4 for dimension-to-geometry association
    - calibration/ for scale detection
    - body_grid for morphology classification
    
    This class NEVER parses dimensions, detects scales, or classifies
    morphology directly — it coordinates calls to systems that do.
    """
    
    def __init__(self):
        self._phase4_pipeline = None
        self._calibrator = None
        self._morphology_analyzer = None
    
    def _init_phase4(self):
        """Lazy init Phase 4 pipeline."""
        if self._phase4_pipeline is None:
            try:
                from phase4.pipeline import BlueprintPipeline
                self._phase4_pipeline = BlueprintPipeline()
            except ImportError:
                pass
        return self._phase4_pipeline
    
    def _init_calibrator(self):
        """Lazy init calibration."""
        if self._calibrator is None:
            try:
                from calibration.pixel_calibrator import PixelCalibrator
                self._calibrator = PixelCalibrator()
            except ImportError:
                pass
        return self._calibrator
    
    def _init_morphology(self):
        """Lazy init morphology analyzer."""
        if self._morphology_analyzer is None:
            try:
                from ..body_grid.morphology_descriptor import MorphologyAnalyzer
                self._morphology_analyzer = MorphologyAnalyzer()
            except ImportError:
                pass
        return self._morphology_analyzer
    
    def harvest_from_pdf(
        self,
        pdf_path: str,
        page: int = 1,
        instrument_hint: Optional[str] = None,
    ) -> HarvestResult:
        """
        Harvest morphology data from a PDF blueprint.
        
        This method coordinates calls to Phase 4, calibration, and body_grid.
        It does NOT perform extraction itself.
        
        Args:
            pdf_path: Path to PDF blueprint
            page: Page number (1-indexed)
            instrument_hint: Optional instrument family hint for validation
        
        Returns:
            HarvestResult with HarvestRecord or error
        """
        from uuid import uuid4
        
        harvest_id = f"harvest_{uuid4().hex[:8]}"
        
        # Create base record
        record = HarvestRecord(
            harvest_id=harvest_id,
            source_pdf=pdf_path,
            page_number=page,
        )
        
        # Step 1: Try Phase 4 for dimension extraction
        phase4 = self._init_phase4()
        if phase4:
            try:
                linked = phase4.process(pdf_path, page=page)
                record.phase4_result_id = f"phase4_{harvest_id}"
                record.raw_linked_dimensions = linked.to_dict()
                
                # Extract dimensions from linked results
                for dim in linked.dimensions:
                    self._apply_dimension(record, dim)
                
                record.extraction_confidence = linked.association_rate
            except Exception as e:
                pass  # Phase 4 unavailable, continue without
        
        # Step 2: Try calibration for scale
        calibrator = self._init_calibrator()
        if calibrator:
            try:
                cal_result = calibrator.calibrate_from_pdf(pdf_path, page=page)
                record.calibration_method = cal_result.method
                record.calibration_confidence = cal_result.confidence
            except Exception:
                pass  # Calibration unavailable
        
        # Step 3: Try morphology classification if we have dimensions
        if record.body_length_mm and record.lower_bout_width_mm:
            analyzer = self._init_morphology()
            if analyzer:
                try:
                    evidence = record.to_body_evidence()
                    descriptor = analyzer.analyze(evidence)
                    record.morphology_class = descriptor.variant_match.morphology_class
                    record.classification_confidence = descriptor.confidence
                except Exception:
                    pass
        
        # Determine success
        success = (
            record.body_length_mm is not None or
            record.lower_bout_width_mm is not None
        )
        
        return HarvestResult(
            record=record,
            success=success,
            phase4_available=phase4 is not None,
            calibration_available=calibrator is not None,
        )
    
    def _apply_dimension(self, record: HarvestRecord, dim) -> None:
        """
        Apply dimension from Phase 4 to harvest record.
        
        Uses semantic matching to map dimension labels to
        canonical field names per governance audit.
        """
        label = getattr(dim, 'label', '').lower()
        value = getattr(dim, 'value_mm', None)
        
        if value is None:
            return
        
        # Map to canonical terms (per governance audit vocabulary)
        if 'body' in label and 'length' in label:
            record.body_length_mm = value
        elif 'lower' in label and 'bout' in label:
            record.lower_bout_width_mm = value
        elif 'upper' in label and 'bout' in label:
            record.upper_bout_width_mm = value
        elif 'waist' in label:
            record.waist_width_mm = value
        elif 'scale' in label and 'length' in label:
            record.scale_length_mm = value
```

### 4. Review Manifest (`review_manifest.py`)

```python
"""
Review Manifest Generator — follows regression_corpus manifest pattern.
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .schema import HarvestRecord, ReviewStatus


@dataclass
class HarvestManifest:
    """
    Manifest for harvested morphology data.
    
    Follows pattern from tests/regression_corpus/manifest.json
    """
    manifest_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    corpus_root: str = ""
    governance_doc: str = "docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md"
    
    # Statistics
    total_pdfs: int = 0
    successful_harvests: int = 0
    pending_review: int = 0
    
    # Records
    records: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_record(self, record: HarvestRecord) -> None:
        """Add harvest record to manifest."""
        self.records.append({
            "harvest_id": record.harvest_id,
            "source_pdf": record.source_pdf,
            "page_number": record.page_number,
            "review_status": record.review_status.value,
            "morphology_class": record.morphology_class.value if record.morphology_class else None,
            "body_length_mm": record.body_length_mm,
            "extraction_confidence": record.extraction_confidence,
            "classification_confidence": record.classification_confidence,
        })
        
        self.total_pdfs = len(set(r["source_pdf"] for r in self.records))
        self.successful_harvests = len([r for r in self.records if r["body_length_mm"]])
        self.pending_review = len([
            r for r in self.records 
            if r["review_status"] == ReviewStatus.PENDING_REVIEW.value
        ])
    
    def save(self, path: str) -> None:
        """Save manifest to JSON file."""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "HarvestManifest":
        """Load manifest from JSON file."""
        with open(path) as f:
            data = json.load(f)
        
        manifest = cls(
            manifest_version=data.get("manifest_version", "1.0.0"),
            created_at=data.get("created_at", ""),
            corpus_root=data.get("corpus_root", ""),
            total_pdfs=data.get("total_pdfs", 0),
            successful_harvests=data.get("successful_harvests", 0),
            pending_review=data.get("pending_review", 0),
            records=data.get("records", []),
        )
        return manifest
```

---

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | HarvestRecord uses canonical vocabulary | Field names match governance audit |
| 2 | No dimension parsing in harvest module | Grep for OCR/regex returns empty |
| 3 | Phase 4 called for dimension extraction | Import path present |
| 4 | Calibration called for scale | Import path present |
| 5 | HarvestRecord.to_body_evidence() works | Unit test passes |
| 6 | PDFInventory follows DXFInventory pattern | Structural comparison |
| 7 | Review manifest follows corpus pattern | JSON schema match |
| 8 | No new zone names created | Grep for ZoneId usage |
| 9 | Morphology classes from enum only | Grep for BodyMorphologyClass |
| 10 | README references governance audit | Link present |

---

## Test Plan

### Unit Tests

```python
# tests/test_harvest_schema.py

def test_harvest_record_uses_canonical_terms():
    """Verify field names match governance audit."""
    from app.instrument_geometry.body.ibg.morphology_harvest.schema import HarvestRecord
    
    # These are the canonical terms from the audit
    canonical = {
        "body_length_mm",
        "upper_bout_width_mm", 
        "waist_width_mm",
        "lower_bout_width_mm",
        "waist_y_norm",
        "scale_length_mm",
    }
    
    record_fields = {f.name for f in dataclasses.fields(HarvestRecord)}
    
    # All canonical terms must be present
    assert canonical.issubset(record_fields)


def test_to_body_evidence_conversion():
    """Verify HarvestRecord converts to BodyEvidence."""
    record = HarvestRecord(
        harvest_id="test_001",
        source_pdf="test.pdf",
        body_length_mm=520.0,
        lower_bout_width_mm=381.0,
        waist_width_mm=241.0,
        upper_bout_width_mm=292.0,
        waist_y_norm=0.43,
    )
    
    evidence = record.to_body_evidence()
    
    assert evidence is not None
    assert len(evidence.landmarks) >= 2


def test_no_dimension_parsing_in_harvest():
    """Verify harvest module delegates extraction."""
    import ast
    from pathlib import Path
    
    harvest_dir = Path("services/api/app/instrument_geometry/body/ibg/morphology_harvest")
    
    forbidden_patterns = ["pytesseract", "easyocr", "re.findall", "re.search"]
    
    for py_file in harvest_dir.glob("*.py"):
        content = py_file.read_text()
        for pattern in forbidden_patterns:
            assert pattern not in content, f"Found {pattern} in {py_file.name}"
```

---

## Implementation Checklist

- [ ] Read `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md`
- [ ] Create `morphology_harvest/` directory structure
- [ ] Implement `schema.py` with HarvestRecord
- [ ] Implement `pdf_inventory.py` following DXFInventory pattern
- [ ] Implement `harvest_coordinator.py` as thin layer
- [ ] Implement `review_manifest.py` following corpus pattern
- [ ] Add `HARVEST_INGESTION` to EvidenceSource enum
- [ ] Write unit tests
- [ ] Create README.md referencing governance audit
- [ ] Verify no dimension parsing in harvest module

---

## Risk Mitigations

| Risk | Mitigation | Status |
|------|------------|--------|
| Duplicate extraction logic | Audit checklist, grep verification | PLANNED |
| Vocabulary drift | Canonical term tests | PLANNED |
| Schema fragmentation | to_body_evidence() adapter | PLANNED |
| Phase 4 unavailable | Graceful degradation | PLANNED |

---

## Related Documents

- `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` — collision audit (REQUIRED READING)
- `docs/architecture/IBG_BOE_BOUNDARY_MODEL.md` — IBG/BOE boundary
- `docs/governance/MORPHOLOGY_CORPUS_STANDARD.md` — corpus structure
- `services/blueprint-import/phase4/` — Phase 4 pipeline
- `services/blueprint-import/calibration/` — calibration system
