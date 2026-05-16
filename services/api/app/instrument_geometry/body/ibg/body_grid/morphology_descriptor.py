"""
Morphology Descriptor — Body Grid Output Container
===================================================

The MorphologyDescriptor is the primary output of the Body Grid system.

It provides semantic morphology information that IBG can consume as
optional advisory evidence without changing solver behavior.

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .body_grid_schema import (
    AsymmetryDescriptor,
    BodyEvidence,
    CenterlineDescriptor,
    HardwareRegion,
    NormalizedPoint,
    ZoneAssignment,
)
from .primitives import MorphologyPrimitive, PrimitiveDetector
from .variant_grammar import VariantMatch, VariantGrammar, BodyMorphologyClass
from .zones import ZoneClassifier, ZoneId, ZONE_DEFINITIONS
from .grid_normalizer import GridNormalizer


@dataclass
class FlankProfile:
    """
    Complete profile of one side of the body.

    Attributes:
        side: 'left' or 'right'
        primitives: Primitives on this flank
        zone_assignments: Zone assignments for this flank
        extent_at_y: X extent at various Y positions
    """
    side: str
    primitives: List[MorphologyPrimitive] = field(default_factory=list)
    zone_assignments: List[ZoneAssignment] = field(default_factory=list)
    extent_at_y: Dict[str, float] = field(default_factory=dict)


@dataclass
class MorphologyDescriptor:
    """
    Complete morphology description of an instrument body.

    This is the primary output consumed by IBG as advisory evidence.

    Attributes:
        centerline: Centerline description
        asymmetry: Asymmetry characteristics
        left_flank: Left side profile
        right_flank: Right side profile
        primitives: All detected primitives
        zone_coverage: Which zones have evidence
        variant_match: Grammar-based variant classification
        confidence: Overall descriptor confidence
        missing_regions: Zones without evidence
        hardware_regions: Non-authoritative hardware observations
        extensions: Reserved for future adaptive system consumption
    """
    centerline: CenterlineDescriptor
    asymmetry: AsymmetryDescriptor
    left_flank: FlankProfile
    right_flank: FlankProfile
    primitives: List[MorphologyPrimitive]
    zone_coverage: Dict[str, float]
    variant_match: VariantMatch
    confidence: float
    missing_regions: List[str] = field(default_factory=list)
    hardware_regions: List[HardwareRegion] = field(default_factory=list)
    extensions: Dict[str, Any] = field(default_factory=lambda: {
        "adaptive_context": {
            "available": False,
            "sandbox_required": True,
            "notes": "Body Grid semantics may be consumed by future adaptive systems, but no adaptive behavior executes here."
        }
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "centerline": {
                "x_mm": self.centerline.x_mm,
                "source": self.centerline.source,
                "confidence": self.centerline.confidence,
                "symmetry_score": self.centerline.symmetry_score,
            },
            "asymmetry": {
                "is_symmetric": self.asymmetry.is_symmetric,
                "asymmetry_type": self.asymmetry.asymmetry_type,
                "dominant_side": self.asymmetry.dominant_side,
                "asymmetry_score": self.asymmetry.asymmetry_score,
            },
            "variant": {
                "morphology_class": self.variant_match.morphology_class.value,
                "horn_behavior": self.variant_match.horn_behavior.value,
                "waist_behavior": self.variant_match.waist_behavior.value,
                "bout_behavior": self.variant_match.bout_behavior.value,
                "confidence": self.variant_match.confidence,
            },
            "zone_coverage": self.zone_coverage,
            "missing_regions": self.missing_regions,
            "primitive_count": len(self.primitives),
            "confidence": self.confidence,
            "extensions": self.extensions,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class MorphologyAnalyzer:
    """
    Analyzes body evidence and produces MorphologyDescriptor.

    Main entry point for the Body Grid system.
    """

    def __init__(self):
        self.normalizer = GridNormalizer()
        self.zone_classifier = ZoneClassifier()
        self.primitive_detector = PrimitiveDetector()
        self.variant_grammar = VariantGrammar()

    def analyze(
        self,
        evidence: BodyEvidence,
        centerline_x: Optional[float] = None
    ) -> MorphologyDescriptor:
        """
        Analyze body evidence and produce MorphologyDescriptor.

        Args:
            evidence: Raw or partially normalized body evidence
            centerline_x: Optional declared centerline X position

        Returns:
            MorphologyDescriptor with complete morphology analysis
        """
        # Step 1: Normalize coordinates
        normalized, centerline = self.normalizer.normalize_evidence(
            evidence, centerline_x
        )

        # Step 2: Extract normalized points for primitive detection
        all_points = self._extract_all_points(normalized)

        # Step 3: Detect primitives
        primitives = self.primitive_detector.detect_primitives(
            all_points, self.zone_classifier
        )

        # Step 4: Build flank profiles
        left_flank = self._build_flank_profile("left", primitives)
        right_flank = self._build_flank_profile("right", primitives)

        # Step 5: Compute asymmetry
        asymmetry = self._compute_asymmetry(left_flank, right_flank, centerline)

        # Step 6: Match variant grammar
        variant_match = self.variant_grammar.classify(
            primitives, asymmetry.asymmetry_score
        )

        # Step 7: Compute zone coverage
        zone_coverage = self._compute_zone_coverage(primitives)

        # Step 8: Identify missing regions
        missing_regions = self._identify_missing_regions(zone_coverage)

        # Step 9: Compute overall confidence
        confidence = self._compute_confidence(
            primitives, zone_coverage, variant_match
        )

        return MorphologyDescriptor(
            centerline=centerline,
            asymmetry=asymmetry,
            left_flank=left_flank,
            right_flank=right_flank,
            primitives=primitives,
            zone_coverage=zone_coverage,
            variant_match=variant_match,
            confidence=confidence,
            missing_regions=missing_regions,
        )

    def _extract_all_points(self, evidence: BodyEvidence) -> List[NormalizedPoint]:
        """Extract all normalized points from evidence."""
        points = []

        # From outline_points (already normalized tuples)
        for x, y in evidence.outline_points:
            points.append(NormalizedPoint(x_norm=x, y_norm=y))

        # From contour segments
        for seg in evidence.contour_segments:
            points.extend(seg.points)

        # From landmarks
        for lm in evidence.landmarks:
            points.append(lm.point)

        # Sort by Y for consistent processing
        points.sort(key=lambda p: p.y_norm)

        return points

    def _build_flank_profile(
        self,
        side: str,
        primitives: List[MorphologyPrimitive]
    ) -> FlankProfile:
        """Build profile for one side of the body."""
        side_prims = [p for p in primitives if p.side == side]
        zone_assignments = [p.zone_assignment for p in side_prims]

        # Compute extent at standard Y positions
        extent_at_y = {}
        y_samples = {"butt": 0.05, "lower_bout": 0.25, "waist": 0.45, "upper_bout": 0.65, "shoulder": 0.85}

        for label, y in y_samples.items():
            # Find primitives near this Y
            nearby = [
                p for p in side_prims
                if p.y_range[0] <= y <= p.y_range[1]
            ]
            if nearby:
                if side == "left":
                    extent = min(p.x_range[0] for p in nearby)
                else:
                    extent = max(p.x_range[1] for p in nearby)
                extent_at_y[label] = abs(extent)

        return FlankProfile(
            side=side,
            primitives=side_prims,
            zone_assignments=zone_assignments,
            extent_at_y=extent_at_y
        )

    def _compute_asymmetry(
        self,
        left: FlankProfile,
        right: FlankProfile,
        centerline: CenterlineDescriptor
    ) -> AsymmetryDescriptor:
        """Compute asymmetry characteristics."""
        # Compare extents at each Y level
        ratios = {}
        for label in left.extent_at_y:
            if label in right.extent_at_y:
                l_ext = left.extent_at_y[label]
                r_ext = right.extent_at_y[label]
                if l_ext + r_ext > 0:
                    ratios[label] = l_ext / r_ext if r_ext > 0 else 2.0

        if not ratios:
            return AsymmetryDescriptor()

        # Compute asymmetry score
        deviations = [abs(1.0 - r) for r in ratios.values()]
        avg_deviation = sum(deviations) / len(deviations)
        asymmetry_score = min(1.0, avg_deviation)

        # Determine dominant side
        avg_ratio = sum(ratios.values()) / len(ratios)
        if avg_ratio > 1.1:
            dominant_side = "left"
        elif avg_ratio < 0.9:
            dominant_side = "right"
        else:
            dominant_side = "balanced"

        # Classify asymmetry type
        asymmetry_type = None
        if asymmetry_score > 0.3:
            # Check for specific patterns
            waist_ratio = ratios.get("waist", 1.0)
            upper_ratio = ratios.get("upper_bout", 1.0)

            if abs(waist_ratio - 1.0) > 0.2:
                asymmetry_type = "offset_waist"
            elif abs(upper_ratio - 1.0) > 0.3:
                asymmetry_type = "single_cut"
            else:
                asymmetry_type = "general_asymmetric"

        return AsymmetryDescriptor(
            is_symmetric=asymmetry_score < 0.15,
            asymmetry_type=asymmetry_type,
            left_right_ratio=ratios,
            dominant_side=dominant_side,
            asymmetry_score=asymmetry_score
        )

    def _compute_zone_coverage(
        self,
        primitives: List[MorphologyPrimitive]
    ) -> Dict[str, float]:
        """Compute coverage (evidence presence) per zone."""
        coverage = {zone.value: 0.0 for zone in ZoneId}

        for prim in primitives:
            for zone_id, weight in prim.zone_assignment.zone_weights.items():
                if zone_id in coverage:
                    coverage[zone_id] = max(coverage[zone_id], weight * prim.confidence)

        return coverage

    def _identify_missing_regions(
        self,
        zone_coverage: Dict[str, float]
    ) -> List[str]:
        """Identify zones with no evidence."""
        # Core zones that should have evidence
        core_zones = [
            ZoneId.LOWER_BOUT.value,
            ZoneId.WAIST.value,
            ZoneId.UPPER_BOUT.value,
            ZoneId.BUTT_END.value,
        ]

        missing = [z for z in core_zones if zone_coverage.get(z, 0.0) < 0.2]
        return missing

    def _compute_confidence(
        self,
        primitives: List[MorphologyPrimitive],
        zone_coverage: Dict[str, float],
        variant_match: VariantMatch
    ) -> float:
        """Compute overall descriptor confidence."""
        if not primitives:
            return 0.0

        # Factor 1: Primitive count (more is better, up to a point)
        prim_factor = min(1.0, len(primitives) / 20)

        # Factor 2: Zone coverage
        core_zones = [ZoneId.LOWER_BOUT.value, ZoneId.WAIST.value, ZoneId.UPPER_BOUT.value]
        coverage_factor = sum(zone_coverage.get(z, 0) for z in core_zones) / len(core_zones)

        # Factor 3: Variant match confidence
        variant_factor = variant_match.confidence

        # Factor 4: Average primitive confidence
        prim_conf = sum(p.confidence for p in primitives) / len(primitives)

        # Weighted combination
        confidence = (
            prim_factor * 0.2 +
            coverage_factor * 0.3 +
            variant_factor * 0.3 +
            prim_conf * 0.2
        )

        return round(confidence, 3)


def analyze_from_dxf_landmarks(
    landmarks: List[tuple],
    outline_points: Optional[List[tuple]] = None
) -> MorphologyDescriptor:
    """
    Convenience function to analyze from constraint_extractor output.

    Args:
        landmarks: List of (label, x_mm, y_mm) from constraint_extractor
        outline_points: Optional list of (x_mm, y_mm) outline points

    Returns:
        MorphologyDescriptor
    """
    from .body_grid_schema import Landmark, RawCoordinate, CoordinateSpace, EvidenceSource

    evidence = BodyEvidence(source_type=EvidenceSource.CONSTRAINT_EXTRACTOR)

    for label, x, y in landmarks:
        evidence.landmarks.append(Landmark(
            label=label,
            point=NormalizedPoint(
                x_norm=0.0,
                y_norm=0.0,
                raw=RawCoordinate(x, y, CoordinateSpace.RAW_MM)
            ),
            source=EvidenceSource.CONSTRAINT_EXTRACTOR
        ))

    if outline_points:
        evidence.outline_points = outline_points

    analyzer = MorphologyAnalyzer()
    return analyzer.analyze(evidence)
