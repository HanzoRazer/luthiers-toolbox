"""
Landmark Pattern Inferrer — Primitive Candidates from Sparse Evidence
======================================================================

Infers primitive candidates from landmark patterns when contour evidence
is incomplete. Produces low-confidence candidates that require review.

This addresses the 1B validation finding that landmark-only evidence
collapses classification into SLAB_BODY because variant grammar
expects curvature-aware primitives.

1B-FIX: Deterministic heuristics only, no adaptive/LLM behavior.

Author: Production Shop
Date: 2026-05-17
Sprint: IBG Morphology Harvest 1B-FIX
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .body_grid_schema import (
    BodyEvidence,
    Landmark,
    NormalizedPoint,
    ZoneAssignment,
)
from .primitives import (
    MorphologyPrimitive,
    PrimitiveType,
    CurvatureClass,
    GeometryType,
    SlopeClass,
)
from .body_grid_schema import EvidenceSource
from .zones import ZoneId

logger = logging.getLogger(__name__)


@dataclass
class InferredPrimitive:
    """
    A primitive candidate inferred from landmark patterns.

    Lower confidence than contour-derived primitives.
    Marked for human review.
    """
    primitive_type: PrimitiveType
    zone_id: ZoneId
    side: str  # "left", "right", "center"
    confidence: float  # Should be < 0.5 for inferred
    source: str = "landmark_pattern"
    requires_review: bool = True
    inference_reason: str = ""


class LandmarkPatternInferrer:
    """
    Infers primitive candidates from landmark patterns.

    When contour evidence is sparse, landmark configurations can
    suggest likely primitives:

    - Lower bout wider than upper → acoustic pattern → CONVEX_BOUT
    - Waist significantly narrower → pronounced waist → CONCAVE_WAIST
    - Asymmetric upper bout → cutaway inference → CUTAWAY_INTRUSION
    - Wide equal bouts with narrow waist suppressed → angular candidate

    All inferences are low-confidence and require human review.
    """

    # Thresholds for pattern detection
    BOUT_RATIO_ACOUSTIC = 1.3  # LB/UB ratio for acoustic-like
    WAIST_RATIO_PRONOUNCED = 0.75  # waist/bout ratio for pronounced waist
    WAIST_RATIO_SUPPRESSED = 0.95  # waist/bout ratio for suppressed waist
    ASYMMETRY_THRESHOLD = 0.15  # L/R ratio deviation for asymmetry

    def __init__(self):
        self.inference_log: List[str] = []

    def infer_from_landmarks(
        self,
        evidence: BodyEvidence,
    ) -> List[InferredPrimitive]:
        """
        Infer primitive candidates from landmark patterns.

        Args:
            evidence: BodyEvidence with landmarks

        Returns:
            List of InferredPrimitive candidates (low confidence)
        """
        self.inference_log = []
        candidates = []

        # Extract key landmarks
        landmarks = self._extract_landmark_dict(evidence)

        if not landmarks:
            self.inference_log.append("No landmarks found")
            return candidates

        # Infer bout primitives
        bout_prims = self._infer_bout_primitives(landmarks)
        candidates.extend(bout_prims)

        # Infer waist primitive
        waist_prims = self._infer_waist_primitives(landmarks)
        candidates.extend(waist_prims)

        # Infer horn/cutaway primitives
        horn_prims = self._infer_horn_primitives(landmarks)
        candidates.extend(horn_prims)

        # Log inference summary
        if candidates:
            logger.info(f"Inferred {len(candidates)} primitive candidates from landmarks")
        else:
            logger.debug("No primitive candidates inferred from landmarks")

        return candidates

    def _extract_landmark_dict(
        self,
        evidence: BodyEvidence,
    ) -> Dict[str, Tuple[float, float]]:
        """Extract landmark positions as dict."""
        landmarks = {}

        for lm in evidence.landmarks:
            # Normalize label
            label = lm.label.lower().replace(" ", "_")
            landmarks[label] = (lm.point.x_norm, lm.point.y_norm)

        return landmarks

    def _infer_bout_primitives(
        self,
        landmarks: Dict[str, Tuple[float, float]],
    ) -> List[InferredPrimitive]:
        """Infer bout primitives from bout landmarks."""
        candidates = []

        # Get bout widths (x_norm values)
        lb_right = landmarks.get("lower_bout_max", (0, 0))[0]
        lb_left = landmarks.get("lower_bout_max_left", (0, 0))[0]
        ub_right = landmarks.get("upper_bout_max", (0, 0))[0]
        ub_left = landmarks.get("upper_bout_max_left", (0, 0))[0]

        # Use absolute values for width
        lb_width = abs(lb_right) + abs(lb_left) if lb_right and lb_left else abs(lb_right) * 2
        ub_width = abs(ub_right) + abs(ub_left) if ub_right and ub_left else abs(ub_right) * 2

        if lb_width <= 0 or ub_width <= 0:
            return candidates

        bout_ratio = lb_width / ub_width

        # Acoustic pattern: lower bout significantly wider
        if bout_ratio > self.BOUT_RATIO_ACOUSTIC:
            # Infer convex bouts (acoustic figure-8)
            candidates.append(InferredPrimitive(
                primitive_type=PrimitiveType.CONVEX_BOUT,
                zone_id=ZoneId.LOWER_BOUT,
                side="right",
                confidence=0.35,
                inference_reason=f"LB/UB ratio {bout_ratio:.2f} > {self.BOUT_RATIO_ACOUSTIC} suggests acoustic",
            ))
            candidates.append(InferredPrimitive(
                primitive_type=PrimitiveType.CONVEX_BOUT,
                zone_id=ZoneId.LOWER_BOUT,
                side="left",
                confidence=0.35,
                inference_reason=f"LB/UB ratio {bout_ratio:.2f} > {self.BOUT_RATIO_ACOUSTIC} suggests acoustic",
            ))
            self.inference_log.append(f"Acoustic pattern: LB/UB={bout_ratio:.2f}")

        # Electric pattern: more equal bouts
        elif 0.8 < bout_ratio < 1.1:
            # Could be slab, double-cut, or angular - less certain
            candidates.append(InferredPrimitive(
                primitive_type=PrimitiveType.ARC_SEGMENT,
                zone_id=ZoneId.LOWER_BOUT,
                side="right",
                confidence=0.25,
                inference_reason=f"Equal bout ratio {bout_ratio:.2f} suggests electric body",
            ))
            self.inference_log.append(f"Electric pattern: LB/UB={bout_ratio:.2f}")

        return candidates

    def _infer_waist_primitives(
        self,
        landmarks: Dict[str, Tuple[float, float]],
    ) -> List[InferredPrimitive]:
        """Infer waist primitives from waist landmarks."""
        candidates = []

        # Get waist width
        waist_right = landmarks.get("waist_min", (0, 0))[0]
        waist_left = landmarks.get("waist_min_left", (0, 0))[0]
        waist_width = abs(waist_right) + abs(waist_left) if waist_right and waist_left else abs(waist_right) * 2

        if waist_width <= 0:
            return candidates

        # Get reference bout width (lower bout typically)
        lb_right = landmarks.get("lower_bout_max", (0, 0))[0]
        lb_left = landmarks.get("lower_bout_max_left", (0, 0))[0]
        bout_width = abs(lb_right) + abs(lb_left) if lb_right and lb_left else abs(lb_right) * 2

        if bout_width <= 0:
            return candidates

        waist_ratio = waist_width / bout_width

        # Pronounced waist (acoustic, classical)
        if waist_ratio < self.WAIST_RATIO_PRONOUNCED:
            candidates.append(InferredPrimitive(
                primitive_type=PrimitiveType.CONCAVE_WAIST,
                zone_id=ZoneId.WAIST,
                side="right",
                confidence=0.40,
                inference_reason=f"Waist/bout ratio {waist_ratio:.2f} < {self.WAIST_RATIO_PRONOUNCED} suggests pronounced waist",
            ))
            candidates.append(InferredPrimitive(
                primitive_type=PrimitiveType.CONCAVE_WAIST,
                zone_id=ZoneId.WAIST,
                side="left",
                confidence=0.40,
                inference_reason=f"Waist/bout ratio {waist_ratio:.2f} < {self.WAIST_RATIO_PRONOUNCED} suggests pronounced waist",
            ))
            self.inference_log.append(f"Pronounced waist: ratio={waist_ratio:.2f}")

        # Suppressed waist (angular, Explorer)
        elif waist_ratio > self.WAIST_RATIO_SUPPRESSED:
            candidates.append(InferredPrimitive(
                primitive_type=PrimitiveType.LINE_SEGMENT,
                zone_id=ZoneId.WAIST,
                side="right",
                confidence=0.30,
                inference_reason=f"Waist/bout ratio {waist_ratio:.2f} > {self.WAIST_RATIO_SUPPRESSED} suggests suppressed waist",
            ))
            self.inference_log.append(f"Suppressed waist: ratio={waist_ratio:.2f}")

        return candidates

    def _infer_horn_primitives(
        self,
        landmarks: Dict[str, Tuple[float, float]],
    ) -> List[InferredPrimitive]:
        """Infer horn/cutaway primitives from upper bout asymmetry."""
        candidates = []

        # Get upper bout landmarks
        ub_right = landmarks.get("upper_bout_max", (0, 0))[0]
        ub_left = landmarks.get("upper_bout_max_left", (0, 0))[0]

        if not ub_right or not ub_left:
            return candidates

        # Check for asymmetry
        ub_right_abs = abs(ub_right)
        ub_left_abs = abs(ub_left)

        if ub_right_abs == 0 or ub_left_abs == 0:
            return candidates

        asymmetry = abs(ub_right_abs - ub_left_abs) / max(ub_right_abs, ub_left_abs)

        if asymmetry > self.ASYMMETRY_THRESHOLD:
            # Significant asymmetry - likely cutaway
            cutaway_side = "right" if ub_right_abs < ub_left_abs else "left"

            candidates.append(InferredPrimitive(
                primitive_type=PrimitiveType.CUTAWAY_INTRUSION,
                zone_id=ZoneId.UPPER_BOUT,
                side=cutaway_side,
                confidence=0.35,
                inference_reason=f"Upper bout asymmetry {asymmetry:.2f} > {self.ASYMMETRY_THRESHOLD} suggests cutaway on {cutaway_side}",
            ))
            self.inference_log.append(f"Cutaway inference: asymmetry={asymmetry:.2f} on {cutaway_side}")

        return candidates

    def convert_to_primitives(
        self,
        inferred: List[InferredPrimitive],
    ) -> List[MorphologyPrimitive]:
        """
        Convert InferredPrimitive candidates to MorphologyPrimitive.

        These will have low confidence and human_review_status='pending'.
        """
        import uuid
        primitives = []

        for inf in inferred:
            # Create zone assignment
            zone_assignment = ZoneAssignment(
                primary_zone=inf.zone_id.value,
                zone_weights={inf.zone_id.value: inf.confidence},
            )

            # Create primitive with inferred curvature
            curvature = self._infer_curvature(inf.primitive_type)
            geometry = self._infer_geometry(inf.primitive_type)
            slope = self._infer_slope(inf.zone_id)

            prim = MorphologyPrimitive(
                primitive_id=f"inferred_{uuid.uuid4().hex[:8]}",
                primitive_type=inf.primitive_type,
                zone_assignment=zone_assignment,
                geometry_type=geometry,
                slope_class=slope,
                curvature_class=curvature,
                points=[],  # No actual points - inferred from landmarks
                side=inf.side,
                confidence=inf.confidence,
                source_evidence=EvidenceSource.SPEC_DEFAULT,  # Closest match for inferred
                human_review_status="pending",
            )
            primitives.append(prim)

        return primitives

    def _infer_slope(self, zone_id: ZoneId) -> SlopeClass:
        """Infer slope class from zone."""
        mapping = {
            ZoneId.LOWER_BOUT: SlopeClass.ASCENDING,
            ZoneId.WAIST: SlopeClass.HORIZONTAL,
            ZoneId.UPPER_BOUT: SlopeClass.ASCENDING,
            ZoneId.SHOULDER: SlopeClass.DESCENDING,
            ZoneId.BUTT_END: SlopeClass.HORIZONTAL,
        }
        return mapping.get(zone_id, SlopeClass.DIAGONAL_POS)

    def _infer_curvature(self, prim_type: PrimitiveType) -> CurvatureClass:
        """Infer curvature class from primitive type."""
        mapping = {
            PrimitiveType.CONVEX_BOUT: CurvatureClass.CONVEX_OUTWARD,
            PrimitiveType.CONCAVE_WAIST: CurvatureClass.CONCAVE_INWARD,
            PrimitiveType.CUTAWAY_INTRUSION: CurvatureClass.CONCAVE_INWARD,
            PrimitiveType.HORN_PROJECTION: CurvatureClass.CONVEX_OUTWARD,
            PrimitiveType.LINE_SEGMENT: CurvatureClass.STRAIGHT,
            PrimitiveType.ARC_SEGMENT: CurvatureClass.CONVEX_OUTWARD,
        }
        return mapping.get(prim_type, CurvatureClass.UNKNOWN)

    def _infer_geometry(self, prim_type: PrimitiveType) -> GeometryType:
        """Infer geometry type from primitive type."""
        mapping = {
            PrimitiveType.LINE_SEGMENT: GeometryType.LINE,
            PrimitiveType.DIAGONAL_SEGMENT: GeometryType.LINE,
            PrimitiveType.ARC_SEGMENT: GeometryType.ARC,
            PrimitiveType.CONVEX_BOUT: GeometryType.ARC,
            PrimitiveType.CONCAVE_WAIST: GeometryType.ARC,
            PrimitiveType.CUTAWAY_INTRUSION: GeometryType.ARC,
            PrimitiveType.HORN_PROJECTION: GeometryType.ARC,
        }
        return mapping.get(prim_type, GeometryType.UNKNOWN)
