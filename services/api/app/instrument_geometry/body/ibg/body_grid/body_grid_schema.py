"""
Body Grid Schema — Core Data Structures for Semantic Morphology
================================================================

Defines the coordinate system, evidence containers, and zone assignment
structures for the Body Grid semantic layer.

Coordinate System:
    y_norm: 0.0 at butt/tail, 1.0 at neck end
    x_norm: signed distance from centerline (negative=bass/left, positive=treble/right)

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class CoordinateSpace(Enum):
    """Coordinate space identifiers for traceability."""
    RAW_PIXEL = "raw_pixel"
    RAW_MM = "raw_mm"
    BOUNDING_BOX = "bounding_box"
    CENTERLINE_RELATIVE = "centerline_relative"


class EvidenceSource(Enum):
    """Source of body evidence."""
    VECTORIZER_DXF = "vectorizer_dxf"
    CONSTRAINT_EXTRACTOR = "constraint_extractor"
    PHOTO_EXTRACTION = "photo_extraction"
    USER_INPUT = "user_input"
    SPEC_DEFAULT = "spec_default"


@dataclass
class RawCoordinate:
    """Raw coordinate with source space tracking."""
    x: float
    y: float
    space: CoordinateSpace
    confidence: float = 1.0


@dataclass
class NormalizedPoint:
    """
    Point in centerline-relative normalized coordinates.

    Attributes:
        x_norm: Signed distance from centerline (negative=bass/left, positive=treble/right)
        y_norm: Normalized body length (0.0=butt, 1.0=neck)
        raw: Original coordinates for traceability
        confidence: Confidence in this point's accuracy (0.0-1.0)
    """
    x_norm: float
    y_norm: float
    raw: Optional[RawCoordinate] = None
    confidence: float = 1.0


@dataclass
class ContourSegment:
    """
    A segment of body contour with normalized coordinates.

    Attributes:
        points: List of normalized points forming the segment
        is_closed: Whether segment forms a closed loop
        side: 'left', 'right', or 'centerline'
        source: Evidence source type
    """
    points: List[NormalizedPoint]
    is_closed: bool = False
    side: str = "unknown"
    source: EvidenceSource = EvidenceSource.VECTORIZER_DXF


@dataclass
class Landmark:
    """
    Named landmark point on the body.

    Compatible with existing constraint_extractor.LandmarkPoint.
    """
    label: str
    point: NormalizedPoint
    source: EvidenceSource
    confidence: float = 1.0


@dataclass
class ZoneAssignment:
    """
    Fuzzy zone assignment for a point or segment.

    Allows overlapping zone membership with weights.

    Attributes:
        primary_zone: Most likely zone
        secondary_zones: Other possible zones
        zone_weights: Weight per zone (should sum to ~1.0)
    """
    primary_zone: str
    secondary_zones: List[str] = field(default_factory=list)
    zone_weights: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.zone_weights:
            self.zone_weights = {self.primary_zone: 1.0}
        if self.primary_zone not in self.zone_weights:
            self.zone_weights[self.primary_zone] = 1.0


@dataclass
class BodyEvidence:
    """
    Container for all body evidence from various sources.

    This is the input adapter layer — accepts evidence from multiple
    extractors without tying Body Grid to one specific format.

    Attributes:
        outline_points: Raw outline points (optional)
        contour_segments: Vectorizer contour segments (optional)
        landmarks: Named landmark points (optional)
        source_type: Primary evidence source
        source_transform: Transform applied to reach normalized coords
        bounding_box_mm: Original bounding box in mm (for denormalization)
        centerline_x_mm: Detected or declared centerline X position
    """
    outline_points: List[Tuple[float, float]] = field(default_factory=list)
    contour_segments: List[ContourSegment] = field(default_factory=list)
    landmarks: List[Landmark] = field(default_factory=list)
    source_type: EvidenceSource = EvidenceSource.VECTORIZER_DXF
    source_transform: Optional[Dict[str, float]] = None
    bounding_box_mm: Optional[Tuple[float, float, float, float]] = None
    centerline_x_mm: Optional[float] = None

    def has_landmarks(self) -> bool:
        """Check if landmarks are available."""
        return len(self.landmarks) > 0

    def has_contours(self) -> bool:
        """Check if contour segments are available."""
        return len(self.contour_segments) > 0

    def get_landmark(self, label: str) -> Optional[Landmark]:
        """Get landmark by label."""
        for lm in self.landmarks:
            if lm.label == label:
                return lm
        return None


@dataclass
class CenterlineDescriptor:
    """
    Describes the body centerline.

    Attributes:
        x_mm: Centerline X position in mm coordinates
        source: How centerline was determined
        confidence: Confidence in centerline detection
        symmetry_score: How symmetric the body is about this line (0-1)
    """
    x_mm: float
    source: str  # "detected", "declared", "spec_default"
    confidence: float = 1.0
    symmetry_score: float = 1.0


@dataclass
class AsymmetryDescriptor:
    """
    Describes body asymmetry characteristics.

    Attributes:
        is_symmetric: True if body is reasonably symmetric
        asymmetry_type: Type of asymmetry (e.g., "single_cut", "offset", "angular")
        left_right_ratio: Width ratio left/right at various Y positions
        dominant_side: 'left', 'right', or 'balanced'
        asymmetry_score: 0.0 = perfectly symmetric, 1.0 = highly asymmetric
    """
    is_symmetric: bool = True
    asymmetry_type: Optional[str] = None
    left_right_ratio: Dict[str, float] = field(default_factory=dict)
    dominant_side: str = "balanced"
    asymmetry_score: float = 0.0


@dataclass
class HardwareRegion:
    """
    Non-authoritative observation of hardware placement.

    These do NOT affect outer contour reconstruction.
    """
    region_type: str  # "pickup", "control", "bridge", "tailpiece"
    bounds_norm: Tuple[float, float, float, float]  # x_min, y_min, x_max, y_max
    confidence: float = 0.5
    notes: str = ""
