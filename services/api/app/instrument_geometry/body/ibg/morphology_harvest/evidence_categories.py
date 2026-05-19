"""
Evidence Categories — Semantic Morphology Data Containers
==========================================================

Lightweight dataclasses for each evidence category.
Categories evolve independently, hence separate classes.

Each category shares common fields:
- observed: bool (was this data observed?)
- confidence: float (0.0-1.0)
- source_type: str (where did this come from?)
- source_authority: str (which system owns this data?)
- requires_review: bool (does a human need to verify?)
- notes: list of strings

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EvidenceCategoryBase:
    """
    Base fields shared by all evidence categories.

    Not instantiated directly — subclasses add category-specific fields.
    """
    observed: bool = False
    confidence: float = 0.0
    source_type: Optional[str] = None  # "pdf_text", "pdf_vector", "ocr", "inferred"
    source_authority: Optional[str] = None  # "phase4", "calibration", "body_grid", "harvest"
    requires_review: bool = True
    notes: List[str] = field(default_factory=list)

    def mark_observed(self, confidence: float, source_type: str, source_authority: str):
        """Mark this category as observed with provenance."""
        self.observed = True
        self.confidence = confidence
        self.source_type = source_type
        self.source_authority = source_authority
        self.requires_review = confidence < 0.8


@dataclass
class BodyData(EvidenceCategoryBase):
    """
    Body dimension and morphology evidence.

    Uses canonical vocabulary from governance audit:
    - body_length_mm (not body_length)
    - lower_bout_width_mm (not lower_bout_mm or body_width_mm)
    - upper_bout_width_mm
    - waist_width_mm
    - waist_y_norm (0-1, 0=butt)
    """
    # Canonical dimension fields (governance-aligned)
    body_length_mm: Optional[float] = None
    lower_bout_width_mm: Optional[float] = None
    upper_bout_width_mm: Optional[float] = None
    waist_width_mm: Optional[float] = None
    waist_y_norm: Optional[float] = None

    # Body thickness (if side view available)
    body_depth_mm: Optional[float] = None

    # Morphology classification (use BodyMorphologyClass enum values)
    morphology_class: Optional[str] = None
    instrument_family_normalized: Optional[str] = None

    # Raw source terms (for terminology tracking)
    source_terms: Dict[str, str] = field(default_factory=dict)


@dataclass
class NeckPocketData(EvidenceCategoryBase):
    """
    Neck pocket dimension evidence.

    Canonical fields from GuitarDimensions schema.
    """
    neck_pocket_length_mm: Optional[float] = None
    neck_pocket_width_mm: Optional[float] = None
    neck_pocket_depth_mm: Optional[float] = None
    neck_angle_deg: Optional[float] = None
    pocket_type: Optional[str] = None  # "bolt_on", "set_neck", "neck_through"


@dataclass
class NeckSystemData(EvidenceCategoryBase):
    """
    Neck system evidence (scale, profile, etc.).

    No existing owner for full neck system — this is narrow new schema.
    """
    scale_length_mm: Optional[float] = None
    nut_width_mm: Optional[float] = None
    neck_width_at_12th_mm: Optional[float] = None
    neck_profile: Optional[str] = None  # "C", "D", "V", "U", etc.
    truss_rod_type: Optional[str] = None


@dataclass
class FretboardData(EvidenceCategoryBase):
    """
    Fretboard evidence.

    Extends existing fret_math.py vocabulary where applicable.
    """
    fretboard_radius_mm: Optional[float] = None
    fretboard_radius_inches: Optional[float] = None  # Common in specs
    fret_count: Optional[int] = None
    fretboard_material: Optional[str] = None
    inlay_pattern: Optional[str] = None
    fret_width_mm: Optional[float] = None


@dataclass
class HeadstockData(EvidenceCategoryBase):
    """
    Headstock evidence.

    No existing owner — this is narrow new schema.
    """
    headstock_style: Optional[str] = None  # "3x3", "6_inline", "4x2", "slotted"
    headstock_angle_deg: Optional[float] = None
    headstock_length_mm: Optional[float] = None
    headstock_width_mm: Optional[float] = None
    tuner_layout: Optional[str] = None


@dataclass
class HardwareCavityData(EvidenceCategoryBase):
    """
    Hardware and cavity evidence.

    Extends GuitarDimensions and FeatureRoutes concepts.
    """
    pickup_routes: List[str] = field(default_factory=list)  # "humbucker", "single_coil", etc.
    control_cavity_present: bool = False
    tremolo_route_present: bool = False
    battery_cavity_present: bool = False
    bridge_type: Optional[str] = None

    # Cavity dimensions if detected
    cavity_dimensions: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class AlignmentData(EvidenceCategoryBase):
    """
    Alignment and scale relationship evidence.

    Extends instrument_specs.py concepts.
    """
    centerline_confidence: float = 0.0
    centerline_source: Optional[str] = None
    symmetry_score: Optional[float] = None
    bridge_to_nut_alignment: Optional[str] = None  # "aligned", "offset", "unknown"
    neck_to_body_alignment: Optional[str] = None


@dataclass
class ConstructionNotes(EvidenceCategoryBase):
    """
    Free-form construction notes and annotations.

    For text evidence that doesn't fit structured categories.
    """
    detected_text_blocks: List[str] = field(default_factory=list)
    material_mentions: List[str] = field(default_factory=list)
    dimension_strings: List[str] = field(default_factory=list)
    construction_method_hints: List[str] = field(default_factory=list)

    # Keyword flags
    has_bracing_info: bool = False
    has_binding_info: bool = False
    has_finish_info: bool = False


def create_empty_categories() -> Dict[str, EvidenceCategoryBase]:
    """
    Create a dictionary of all empty evidence categories.

    Returns:
        Dict mapping category name to empty category instance
    """
    return {
        "body_data": BodyData(),
        "neck_pocket_data": NeckPocketData(),
        "neck_system_data": NeckSystemData(),
        "fretboard_data": FretboardData(),
        "headstock_data": HeadstockData(),
        "hardware_cavity_data": HardwareCavityData(),
        "alignment_data": AlignmentData(),
        "construction_notes": ConstructionNotes(),
    }
