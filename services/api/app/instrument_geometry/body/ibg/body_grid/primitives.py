"""
Body Grid Primitives — Morphology Primitive Classes
====================================================

Deterministic primitive classes for describing body contour segments.

Each primitive captures geometry type, curvature class, and zone association
without ML or adaptive behavior.

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .body_grid_schema import NormalizedPoint, ZoneAssignment, EvidenceSource
from .zones import ZoneId


class GeometryType(Enum):
    """Fundamental geometry types for contour segments."""
    ARC = "arc"
    LINE = "line"
    SPLINE = "spline"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class CurvatureClass(Enum):
    """Curvature direction classification."""
    CONVEX_OUTWARD = "convex_outward"   # Bulging away from body center
    CONCAVE_INWARD = "concave_inward"   # Curving toward body center
    STRAIGHT = "straight"
    INFLECTION = "inflection"           # Changes direction
    UNKNOWN = "unknown"


class SlopeClass(Enum):
    """Slope direction classification relative to Y axis."""
    ASCENDING = "ascending"       # Moving neckward as X increases
    DESCENDING = "descending"     # Moving buttward as X increases
    HORIZONTAL = "horizontal"     # Constant Y
    VERTICAL = "vertical"         # Constant X
    DIAGONAL_POS = "diagonal_pos" # Positive slope
    DIAGONAL_NEG = "diagonal_neg" # Negative slope


class PrimitiveType(Enum):
    """Named primitive types for body morphology."""
    ARC_SEGMENT = "arc_segment"
    LINE_SEGMENT = "line_segment"
    DIAGONAL_SEGMENT = "diagonal_segment"
    CONVEX_BOUT = "convex_bout"
    CONCAVE_WAIST = "concave_waist"
    HORN_PROJECTION = "horn_projection"
    CUTAWAY_INTRUSION = "cutaway_intrusion"
    FLAT_SLAB_EDGE = "flat_slab_edge"
    OFFSET_MASS_REGION = "offset_mass_region"
    CENTERLINE_ANCHOR = "centerline_anchor"
    BRIDGE_AXIS_ANCHOR = "bridge_axis_anchor"
    BUTT_TERMINATION = "butt_termination"
    NECK_JUNCTION = "neck_junction"
    SHOULDER_TRANSITION = "shoulder_transition"


@dataclass
class MorphologyPrimitive:
    """
    A classified contour segment with morphology metadata.

    Attributes:
        primitive_id: Unique identifier for this primitive
        primitive_type: Named primitive type
        zone_assignment: Fuzzy zone assignment
        geometry_type: Fundamental geometry class
        slope_class: Slope direction
        curvature_class: Curvature direction
        points: Normalized points forming this primitive
        side: 'left', 'right', or 'centerline'
        confidence: Detection confidence (0.0-1.0)
        source_evidence: Where this primitive came from
        human_review_status: 'pending', 'approved', 'rejected'
        notes: Human-readable description
    """
    primitive_id: str
    primitive_type: PrimitiveType
    zone_assignment: ZoneAssignment
    geometry_type: GeometryType
    slope_class: SlopeClass
    curvature_class: CurvatureClass
    points: List[NormalizedPoint]
    side: str = "unknown"
    confidence: float = 1.0
    source_evidence: EvidenceSource = EvidenceSource.VECTORIZER_DXF
    human_review_status: str = "pending"
    notes: str = ""

    @property
    def y_range(self) -> Tuple[float, float]:
        """Get Y range of this primitive."""
        if not self.points:
            return (0.0, 0.0)
        ys = [p.y_norm for p in self.points]
        return (min(ys), max(ys))

    @property
    def x_range(self) -> Tuple[float, float]:
        """Get X range of this primitive."""
        if not self.points:
            return (0.0, 0.0)
        xs = [p.x_norm for p in self.points]
        return (min(xs), max(xs))

    @property
    def centroid(self) -> NormalizedPoint:
        """Get centroid of primitive points."""
        if not self.points:
            return NormalizedPoint(0.0, 0.0)
        x_avg = sum(p.x_norm for p in self.points) / len(self.points)
        y_avg = sum(p.y_norm for p in self.points) / len(self.points)
        return NormalizedPoint(x_avg, y_avg)


class PrimitiveDetector:
    """
    Detects morphology primitives from contour segments.

    Uses deterministic geometry analysis — no ML.
    """

    def __init__(
        self,
        curvature_threshold: float = 0.02,
        angle_threshold_deg: float = 15.0
    ):
        """
        Args:
            curvature_threshold: Threshold for straight vs curved
            angle_threshold_deg: Angle threshold for slope classification
        """
        self.curvature_threshold = curvature_threshold
        self.angle_threshold = angle_threshold_deg
        self._next_id = 0

    def detect_primitives(
        self,
        points: List[NormalizedPoint],
        zone_classifier
    ) -> List[MorphologyPrimitive]:
        """
        Detect primitives from a list of normalized points.

        Args:
            points: Contour points in order
            zone_classifier: ZoneClassifier for zone assignment

        Returns:
            List of detected MorphologyPrimitive
        """
        if len(points) < 3:
            return []

        primitives = []
        segments = self._segment_by_curvature(points)

        for segment in segments:
            if len(segment) < 2:
                continue

            primitive = self._classify_segment(segment, zone_classifier)
            if primitive:
                primitives.append(primitive)

        return primitives

    def _segment_by_curvature(
        self,
        points: List[NormalizedPoint]
    ) -> List[List[NormalizedPoint]]:
        """
        Split points into segments at curvature inflection points.
        """
        if len(points) < 3:
            return [points]

        segments = []
        current_segment = [points[0], points[1]]

        for i in range(2, len(points)):
            p0, p1, p2 = points[i-2], points[i-1], points[i]

            # Compute curvature sign change
            curv_prev = self._compute_curvature(p0, p1, p2)
            if i > 2:
                p_prev = points[i-3]
                curv_before = self._compute_curvature(p_prev, p0, p1)

                # Check for inflection
                if curv_prev * curv_before < 0 and abs(curv_prev) > self.curvature_threshold:
                    # Inflection point — start new segment
                    segments.append(current_segment)
                    current_segment = [p1]

            current_segment.append(p2)

        if current_segment:
            segments.append(current_segment)

        return segments

    def _compute_curvature(
        self,
        p0: NormalizedPoint,
        p1: NormalizedPoint,
        p2: NormalizedPoint
    ) -> float:
        """
        Compute signed curvature at middle point.

        Positive = curving left (concave from right)
        Negative = curving right (concave from left)
        """
        dx1 = p1.x_norm - p0.x_norm
        dy1 = p1.y_norm - p0.y_norm
        dx2 = p2.x_norm - p1.x_norm
        dy2 = p2.y_norm - p1.y_norm

        # Cross product gives signed area
        cross = dx1 * dy2 - dy1 * dx2

        # Normalize by segment lengths
        len1 = (dx1**2 + dy1**2) ** 0.5
        len2 = (dx2**2 + dy2**2) ** 0.5

        if len1 < 1e-9 or len2 < 1e-9:
            return 0.0

        return cross / (len1 * len2)

    def _classify_segment(
        self,
        points: List[NormalizedPoint],
        zone_classifier
    ) -> Optional[MorphologyPrimitive]:
        """
        Classify a contour segment into a MorphologyPrimitive.
        """
        if len(points) < 2:
            return None

        # Compute segment properties
        curvature = self._average_curvature(points)
        slope = self._compute_slope(points[0], points[-1])
        centroid = self._compute_centroid(points)
        side = "left" if centroid.x_norm < 0 else "right" if centroid.x_norm > 0 else "centerline"

        # Classify curvature
        if abs(curvature) < self.curvature_threshold:
            curv_class = CurvatureClass.STRAIGHT
        elif curvature > 0:
            curv_class = CurvatureClass.CONVEX_OUTWARD if side == "left" else CurvatureClass.CONCAVE_INWARD
        else:
            curv_class = CurvatureClass.CONCAVE_INWARD if side == "left" else CurvatureClass.CONVEX_OUTWARD

        # Classify slope
        slope_class = self._classify_slope(slope)

        # Classify geometry type
        if abs(curvature) < self.curvature_threshold:
            geom_type = GeometryType.LINE
        else:
            geom_type = GeometryType.ARC

        # Get zone assignment from centroid
        zone_assignment = zone_classifier.classify_point(centroid)

        # Determine primitive type based on zone and geometry
        prim_type = self._infer_primitive_type(
            zone_assignment, curv_class, geom_type, side
        )

        self._next_id += 1
        return MorphologyPrimitive(
            primitive_id=f"prim_{self._next_id:04d}",
            primitive_type=prim_type,
            zone_assignment=zone_assignment,
            geometry_type=geom_type,
            slope_class=slope_class,
            curvature_class=curv_class,
            points=points,
            side=side,
            confidence=0.8,  # Default confidence
        )

    def _average_curvature(self, points: List[NormalizedPoint]) -> float:
        """Compute average signed curvature of segment."""
        if len(points) < 3:
            return 0.0

        curvatures = []
        for i in range(1, len(points) - 1):
            c = self._compute_curvature(points[i-1], points[i], points[i+1])
            curvatures.append(c)

        return sum(curvatures) / len(curvatures) if curvatures else 0.0

    def _compute_slope(self, p0: NormalizedPoint, p1: NormalizedPoint) -> float:
        """Compute slope between two points."""
        dx = p1.x_norm - p0.x_norm
        dy = p1.y_norm - p0.y_norm
        if abs(dx) < 1e-9:
            return float('inf') if dy > 0 else float('-inf')
        return dy / dx

    def _classify_slope(self, slope: float) -> SlopeClass:
        """Classify slope into named class."""
        import math

        if abs(slope) == float('inf'):
            return SlopeClass.VERTICAL

        angle = math.degrees(math.atan(slope))

        if abs(angle) < self.angle_threshold:
            return SlopeClass.HORIZONTAL
        elif abs(angle) > 90 - self.angle_threshold:
            return SlopeClass.VERTICAL
        elif angle > 0:
            return SlopeClass.DIAGONAL_POS
        else:
            return SlopeClass.DIAGONAL_NEG

    def _compute_centroid(self, points: List[NormalizedPoint]) -> NormalizedPoint:
        """Compute centroid of points."""
        if not points:
            return NormalizedPoint(0.0, 0.0)
        x_avg = sum(p.x_norm for p in points) / len(points)
        y_avg = sum(p.y_norm for p in points) / len(points)
        return NormalizedPoint(x_avg, y_avg)

    def _infer_primitive_type(
        self,
        zone: ZoneAssignment,
        curv: CurvatureClass,
        geom: GeometryType,
        side: str
    ) -> PrimitiveType:
        """
        Infer named primitive type from zone and geometry.
        """
        zone_id = zone.primary_zone

        # Bout regions with convex curvature
        if zone_id in ("lower_bout", "upper_bout"):
            if curv == CurvatureClass.CONVEX_OUTWARD:
                return PrimitiveType.CONVEX_BOUT
            elif geom == GeometryType.LINE:
                return PrimitiveType.FLAT_SLAB_EDGE

        # Waist region with concave curvature
        if zone_id == "waist":
            if curv == CurvatureClass.CONCAVE_INWARD:
                return PrimitiveType.CONCAVE_WAIST
            elif geom == GeometryType.LINE:
                return PrimitiveType.FLAT_SLAB_EDGE

        # Horn regions
        if zone_id in ("horn_left", "horn_right"):
            return PrimitiveType.HORN_PROJECTION

        # Cutaway regions
        if zone_id in ("cutaway_left", "cutaway_right"):
            return PrimitiveType.CUTAWAY_INTRUSION

        # Butt end
        if zone_id == "butt_end":
            return PrimitiveType.BUTT_TERMINATION

        # Neck region
        if zone_id == "neck_pocket":
            return PrimitiveType.NECK_JUNCTION

        # Shoulder region
        if zone_id == "shoulder":
            return PrimitiveType.SHOULDER_TRANSITION

        # Default based on geometry
        if geom == GeometryType.LINE:
            return PrimitiveType.LINE_SEGMENT
        elif geom == GeometryType.ARC:
            return PrimitiveType.ARC_SEGMENT
        else:
            return PrimitiveType.ARC_SEGMENT
