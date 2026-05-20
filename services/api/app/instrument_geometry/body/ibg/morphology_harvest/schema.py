"""
HarvestRecord Schema — Coordination Layer Data Container
=========================================================

The HarvestRecord coordinates morphology evidence from multiple
extraction systems. It is NOT an extraction result itself.

All extraction is delegated to Phase 4, calibration, and body_grid.
This record preserves and normalizes their outputs.

Terminology Normalization:
    source_term: Original term from upstream system
    normalized_term: Canonical term per governance audit
    owning_system: Which system owns this semantic authority
    confidence: Confidence in the normalization
    requires_review: Whether human review is needed

STORAGE AUTHORITY WARNING:
    HarvestRecord is a preservation/coordination artifact.
    The `morphology_harvest/outputs/` directory is NOT canonical storage.
    It is a temporary staging area for generated outputs only.

    Canonical promotion target must be resolved before harvested
    records are used as shared instrument-building data.

    Potential promotion targets:
    - data_registry/system/instruments/body_templates.json
    - instrument_specs.py BODY_DIMENSIONS dict
    - A new governed morphology corpus location

    Do not treat HarvestRecord as authoritative instrument data
    until governance assigns canonical storage authority.

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .evidence_categories import (
    BodyData,
    NeckPocketData,
    NeckSystemData,
    FretboardData,
    HeadstockData,
    HardwareCavityData,
    AlignmentData,
    ConstructionNotes,
    create_empty_categories,
)


class ReviewStatus(Enum):
    """Review states for harvested records."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    APPROVED_WITH_EDITS = "approved_with_edits"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class HarvestSource(Enum):
    """Source classification for harvested PDFs."""
    VECTOR_TEXT = "vector_text"  # Clean vector PDF with text
    VECTOR_NO_TEXT = "vector_no_text"  # Vector PDF without embedded text
    RASTER_CLEAN = "raster_clean"  # Clean raster scan
    RASTER_NOISY = "raster_noisy"  # Noisy/degraded scan
    PHOTO = "photo"  # Photograph of plans
    MIXED = "mixed"  # Multiple source types
    UNKNOWN = "unknown"


# Terminology normalization mappings (per governance audit)
TERM_NORMALIZATIONS: Dict[str, str] = {
    # INSTRUMENT_SPECS expected_dimensions drift
    "lower_bout_mm": "lower_bout_width_mm",
    "upper_bout_mm": "upper_bout_width_mm",
    "waist_mm": "waist_width_mm",
    # GuitarDimensions semantic aliases
    "body_width_mm": "lower_bout_width_mm",
    "body_width_inches": "lower_bout_width_inches",
    # Common variations
    "lower_bout": "lower_bout_width_mm",
    "upper_bout": "upper_bout_width_mm",
    "waist": "waist_width_mm",
    "body_length": "body_length_mm",
    "scale_length": "scale_length_mm",
}


@dataclass
class TermNormalization:
    """
    Record of a terminology normalization.

    Tracks the mapping from source term to canonical term
    with provenance and confidence.
    """
    source_term: str
    normalized_term: str
    owning_system: str
    confidence: float
    requires_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_term": self.source_term,
            "normalized_term": self.normalized_term,
            "owning_system": self.owning_system,
            "confidence": self.confidence,
            "requires_review": self.requires_review,
        }


@dataclass
class HarvestRecord:
    """
    Coordinates morphology evidence from multiple extraction systems.

    This is a COORDINATION record, not an extraction result.
    All extraction is delegated to Phase 4, calibration, and body_grid.

    Attributes:
        harvest_id: Unique identifier for this harvest
        source_pdf: Path to source PDF
        page_number: Page number (1-indexed)
        harvest_timestamp: When this record was created
        harvest_source: Classification of source type

        # Evidence categories (nested dataclasses)
        body_data: Body dimension and morphology evidence
        neck_pocket_data: Neck pocket evidence
        neck_system_data: Neck system evidence
        fretboard_data: Fretboard evidence
        headstock_data: Headstock evidence
        hardware_cavity_data: Hardware/cavity evidence
        alignment_data: Alignment evidence
        construction_notes: Free-form notes

        # Terminology tracking
        term_normalizations: List of term mappings applied

        # Provenance
        upstream_sources: Dict of upstream system references
        calibration_method: How scale was determined
        phase4_result_id: Reference to Phase 4 result if used

        # Review state
        review_status: Current review status
        reviewer_notes: Notes from human review

        # Adaptive boundary (inert only)
        extensions: Reserved for future systems
    """
    # Identity
    harvest_id: str
    source_pdf: str
    page_number: int = 1
    harvest_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    harvest_source: HarvestSource = HarvestSource.UNKNOWN

    # Evidence categories
    body_data: BodyData = field(default_factory=BodyData)
    neck_pocket_data: NeckPocketData = field(default_factory=NeckPocketData)
    neck_system_data: NeckSystemData = field(default_factory=NeckSystemData)
    fretboard_data: FretboardData = field(default_factory=FretboardData)
    headstock_data: HeadstockData = field(default_factory=HeadstockData)
    hardware_cavity_data: HardwareCavityData = field(default_factory=HardwareCavityData)
    alignment_data: AlignmentData = field(default_factory=AlignmentData)
    construction_notes: ConstructionNotes = field(default_factory=ConstructionNotes)

    # Terminology tracking
    term_normalizations: List[TermNormalization] = field(default_factory=list)

    # Provenance
    upstream_sources: Dict[str, Any] = field(default_factory=dict)
    calibration_method: Optional[str] = None
    phase4_result_id: Optional[str] = None

    # Review state
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    reviewer_notes: List[str] = field(default_factory=list)

    # Adaptive boundary (inert metadata only)
    extensions: Dict[str, Any] = field(default_factory=lambda: {
        "adaptive_context": {
            "available": False,
            "sandbox_required": True,
            "notes": "Harvest semantics may be consumed by future adaptive systems, "
                     "but no adaptive behavior executes here."
        }
    })

    def normalize_term(self, source_term: str, owning_system: str = "harvest") -> str:
        """
        Normalize a terminology term per governance audit.

        Args:
            source_term: Original term from upstream
            owning_system: System that produced this term

        Returns:
            Normalized canonical term
        """
        normalized = TERM_NORMALIZATIONS.get(source_term, source_term)

        if normalized != source_term:
            self.term_normalizations.append(TermNormalization(
                source_term=source_term,
                normalized_term=normalized,
                owning_system=owning_system,
                confidence=1.0,  # Dictionary mapping is certain
                requires_review=False,
            ))

        return normalized

    def to_body_evidence(self):
        """
        Convert to BodyEvidence for Body Grid consumption.

        This is the ONLY approved path from harvest to body_grid.
        Uses governance-aligned coordinate conventions.
        """
        try:
            from ..body_grid.body_grid_schema import (
                BodyEvidence, Landmark, NormalizedPoint, EvidenceSource
            )
        except ImportError:
            return None

        landmarks = []
        body = self.body_data

        # Only create landmarks if we have body_length for normalization
        if not body.body_length_mm or body.body_length_mm <= 0:
            return BodyEvidence(landmarks=[], source=EvidenceSource.VECTORIZER_DXF)

        # Lower bout landmark
        if body.lower_bout_width_mm:
            landmarks.append(Landmark(
                label="lower_bout_max",
                point=NormalizedPoint(
                    x_norm=body.lower_bout_width_mm / (2 * body.body_length_mm),
                    y_norm=0.15,  # Typical lower bout position
                ),
                source=EvidenceSource.VECTORIZER_DXF,
                confidence=body.confidence,
            ))

        # Waist landmark
        if body.waist_width_mm and body.waist_y_norm:
            landmarks.append(Landmark(
                label="waist_min",
                point=NormalizedPoint(
                    x_norm=body.waist_width_mm / (2 * body.body_length_mm),
                    y_norm=body.waist_y_norm,
                ),
                source=EvidenceSource.VECTORIZER_DXF,
                confidence=body.confidence,
            ))

        # Upper bout landmark
        if body.upper_bout_width_mm:
            landmarks.append(Landmark(
                label="upper_bout_max",
                point=NormalizedPoint(
                    x_norm=body.upper_bout_width_mm / (2 * body.body_length_mm),
                    y_norm=0.75,  # Typical upper bout position
                ),
                source=EvidenceSource.VECTORIZER_DXF,
                confidence=body.confidence,
            ))

        return BodyEvidence(
            landmarks=landmarks,
            source_type=EvidenceSource.VECTORIZER_DXF,
        )

    def overall_confidence(self) -> float:
        """
        Calculate overall harvest confidence.

        Weighted average of observed category confidences.
        """
        categories = [
            self.body_data,
            self.neck_pocket_data,
            self.neck_system_data,
            self.fretboard_data,
            self.headstock_data,
            self.hardware_cavity_data,
            self.alignment_data,
            self.construction_notes,
        ]

        observed = [c for c in categories if c.observed]
        if not observed:
            return 0.0

        return sum(c.confidence for c in observed) / len(observed)

    def requires_human_review(self) -> bool:
        """Check if any category requires human review."""
        categories = [
            self.body_data,
            self.neck_pocket_data,
            self.neck_system_data,
            self.fretboard_data,
            self.headstock_data,
            self.hardware_cavity_data,
            self.alignment_data,
            self.construction_notes,
        ]

        return any(c.requires_review for c in categories if c.observed)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "harvest_id": self.harvest_id,
            "source_pdf": self.source_pdf,
            "page_number": self.page_number,
            "harvest_timestamp": self.harvest_timestamp,
            "harvest_source": self.harvest_source.value,
            "evidence_categories": {
                "body_data": _sanitize_for_json(asdict(self.body_data)),
                "neck_pocket_data": _sanitize_for_json(asdict(self.neck_pocket_data)),
                "neck_system_data": _sanitize_for_json(asdict(self.neck_system_data)),
                "fretboard_data": _sanitize_for_json(asdict(self.fretboard_data)),
                "headstock_data": _sanitize_for_json(asdict(self.headstock_data)),
                "hardware_cavity_data": _sanitize_for_json(asdict(self.hardware_cavity_data)),
                "alignment_data": _sanitize_for_json(asdict(self.alignment_data)),
                "construction_notes": _sanitize_for_json(asdict(self.construction_notes)),
            },
            "term_normalizations": [t.to_dict() for t in self.term_normalizations],
            "provenance": {
                "upstream_sources": _sanitize_for_json(self.upstream_sources),
                "calibration_method": self.calibration_method,
                "phase4_result_id": self.phase4_result_id,
            },
            "review": {
                "status": self.review_status.value,
                "notes": self.reviewer_notes,
                "requires_review": self.requires_human_review(),
            },
            "confidence": {
                "overall": self.overall_confidence(),
            },
            "extensions": _sanitize_for_json(self.extensions),
        }

    def save(self, path: str) -> None:
        """Save record to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, cls=_EnumSafeEncoder)

    @classmethod
    def load(cls, path: str) -> "HarvestRecord":
        """Load record from JSON file."""
        with open(path) as f:
            data = json.load(f)

        record = cls(
            harvest_id=data["harvest_id"],
            source_pdf=data["source_pdf"],
            page_number=data.get("page_number", 1),
            harvest_timestamp=data.get("harvest_timestamp", ""),
            harvest_source=HarvestSource(data.get("harvest_source", "unknown")),
        )

        # Load evidence categories
        cats = data.get("evidence_categories", {})
        if "body_data" in cats:
            record.body_data = BodyData(**{
                k: v for k, v in cats["body_data"].items()
                if k in BodyData.__dataclass_fields__
            })

        # Load review state
        review = data.get("review", {})
        if "status" in review:
            record.review_status = ReviewStatus(review["status"])
        record.reviewer_notes = review.get("notes", [])

        return record


def _sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert enum values to strings for JSON serialization.

    Handles ContourCategory and other enum types that may leak through
    from vectorizer responses when running against local server.
    """
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    return obj


class _EnumSafeEncoder(json.JSONEncoder):
    """
    JSON encoder that converts enum values to strings.

    Handles ContourCategory and other enum types that may leak through
    from vectorizer responses when running against local server.

    Minimal fix for 1B validation serialization failures.
    """

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)
