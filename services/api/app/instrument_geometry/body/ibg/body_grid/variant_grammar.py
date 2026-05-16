"""
Variant Grammar — Morphology Grammar for Instrument Body Variants
==================================================================

Describes how instrument bodies vary through a behavior-based grammar.

Classifies by body BEHAVIOR, not by brand or exact model.

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from .primitives import MorphologyPrimitive, PrimitiveType, CurvatureClass, GeometryType
from .zones import ZoneId


class BodyMorphologyClass(Enum):
    """High-level body morphology classifications."""
    ROUNDED_ACOUSTIC = "rounded_acoustic"       # Dreadnought, jumbo, classical
    ROUNDED_SINGLE_CUT = "rounded_single_cut"   # LP-style single cutaway
    DOUBLE_CUT = "double_cut"                   # SG-style, Stratocaster
    OFFSET_WAIST = "offset_waist"               # Jazzmaster, Jaguar, Mustang
    ANGULAR_WEDGE = "angular_wedge"             # Explorer, Flying V
    SLAB_BODY = "slab_body"                     # Telecaster, basic solid body
    CARVED_TOP = "carved_top"                   # Archtop acoustic/electric
    SEMI_SYMMETRIC = "semi_symmetric"           # Mostly symmetric with minor asymmetry
    ASYMMETRIC = "asymmetric"                   # Intentionally asymmetric
    UNKNOWN = "unknown"


class HornBehavior(Enum):
    """Horn/cutaway behavior classifications."""
    SYMMETRIC_HORNS = "symmetric_horns"         # Equal horns both sides
    SINGLE_CUT_TREBLE = "single_cut_treble"     # Cutaway on treble side only
    SINGLE_CUT_BASS = "single_cut_bass"         # Cutaway on bass side (rare)
    NO_HORNS = "no_horns"                       # Rounded upper bout, no horns
    POINTED_HORNS = "pointed_horns"             # Sharp pointed horns
    ROUNDED_HORNS = "rounded_horns"             # Soft rounded horns
    ANGULAR_HORNS = "angular_horns"             # Angular/wedge horns


class WaistBehavior(Enum):
    """Waist behavior classifications."""
    DEEP_WAIST = "deep_waist"                   # Classical-style deep waist
    MODERATE_WAIST = "moderate_waist"           # Standard acoustic waist
    SHALLOW_WAIST = "shallow_waist"             # Dreadnought-style
    SUPPRESSED_WAIST = "suppressed_waist"       # Explorer, V-style (minimal waist)
    OFFSET_WAIST = "offset_waist"               # Asymmetric waist position
    ANGULAR_WAIST = "angular_waist"             # Sharp angles at waist


class BoutBehavior(Enum):
    """Bout (lower/upper) behavior classifications."""
    ROUNDED_BOUTS = "rounded_bouts"             # Smooth curved bouts
    ANGULAR_BOUTS = "angular_bouts"             # Sharp angled bouts
    ASYMMETRIC_BOUTS = "asymmetric_bouts"       # Different left/right
    EXTENDED_LOWER = "extended_lower"           # Extra-wide lower bout (jumbo)
    SUPPRESSED_UPPER = "suppressed_upper"       # Small upper bout (SG-style)


@dataclass
class VariantRule:
    """
    A rule describing expected body behavior for a variant type.

    Attributes:
        rule_id: Unique rule identifier
        name: Human-readable rule name
        required_primitives: Primitive types that MUST be present
        forbidden_primitives: Primitive types that MUST NOT be present
        zone_expectations: Expected behavior per zone
        symmetry_requirement: Required symmetry level (0-1)
        description: Human-readable description
    """
    rule_id: str
    name: str
    required_primitives: Set[PrimitiveType] = field(default_factory=set)
    forbidden_primitives: Set[PrimitiveType] = field(default_factory=set)
    zone_expectations: Dict[str, str] = field(default_factory=dict)
    symmetry_requirement: float = 0.5
    description: str = ""


@dataclass
class VariantMatch:
    """
    Result of matching a body against variant grammar.

    Attributes:
        morphology_class: Best matching morphology class
        horn_behavior: Detected horn behavior
        waist_behavior: Detected waist behavior
        bout_behavior: Detected bout behavior
        confidence: Match confidence (0-1)
        matched_rules: Rules that matched
        violated_rules: Rules that were violated
        notes: Additional observations
    """
    morphology_class: BodyMorphologyClass
    horn_behavior: HornBehavior
    waist_behavior: WaistBehavior
    bout_behavior: BoutBehavior
    confidence: float
    matched_rules: List[str] = field(default_factory=list)
    violated_rules: List[str] = field(default_factory=list)
    notes: str = ""


# Variant rules library
VARIANT_RULES: Dict[str, VariantRule] = {
    "rounded_single_cut": VariantRule(
        rule_id="rounded_single_cut",
        name="Rounded Single Cutaway",
        required_primitives={
            PrimitiveType.CONVEX_BOUT,
            PrimitiveType.CONCAVE_WAIST,
            PrimitiveType.CUTAWAY_INTRUSION,
        },
        forbidden_primitives={
            PrimitiveType.FLAT_SLAB_EDGE,  # Should be curved, not flat
        },
        zone_expectations={
            "lower_bout": "convex_outward",
            "upper_bout": "convex_outward",
            "waist": "concave_inward",
            "cutaway_right": "concave_intrusion",
        },
        symmetry_requirement=0.3,  # Asymmetric due to single cut
        description="LP-style single cutaway with rounded lower mass dominance"
    ),

    "angular_wedge": VariantRule(
        rule_id="angular_wedge",
        name="Angular Wedge Body",
        required_primitives={
            PrimitiveType.LINE_SEGMENT,
            PrimitiveType.DIAGONAL_SEGMENT,
        },
        forbidden_primitives={
            PrimitiveType.CONVEX_BOUT,      # Should be angular, not rounded
            PrimitiveType.CONCAVE_WAIST,    # Waist suppressed
        },
        zone_expectations={
            "lower_bout": "angular_diagonal",
            "upper_bout": "angular_diagonal",
            "waist": "suppressed",
        },
        symmetry_requirement=0.7,  # Often symmetric
        description="Explorer-style angular primitive dominance with suppressed waist"
    ),

    "offset_double_cut": VariantRule(
        rule_id="offset_double_cut",
        name="Offset Double Cutaway",
        required_primitives={
            PrimitiveType.CONVEX_BOUT,
            PrimitiveType.HORN_PROJECTION,
        },
        zone_expectations={
            "lower_bout": "convex_asymmetric",
            "upper_bout": "convex_asymmetric",
            "waist": "offset_position",
            "horn_left": "projection",
            "horn_right": "projection",
        },
        symmetry_requirement=0.2,  # Intentionally asymmetric
        description="Jazzmaster/Mustang-style offset body with mixed arc-line construction"
    ),

    "slab_body": VariantRule(
        rule_id="slab_body",
        name="Slab Body",
        required_primitives={
            PrimitiveType.ARC_SEGMENT,
        },
        zone_expectations={
            "lower_bout": "continuous_curve",
            "upper_bout": "continuous_curve",
            "waist": "shallow_or_absent",
        },
        symmetry_requirement=0.8,  # Usually symmetric
        description="Telecaster-style controlled slab-body continuity"
    ),

    "rounded_acoustic": VariantRule(
        rule_id="rounded_acoustic",
        name="Rounded Acoustic",
        required_primitives={
            PrimitiveType.CONVEX_BOUT,
            PrimitiveType.CONCAVE_WAIST,
            PrimitiveType.BUTT_TERMINATION,
        },
        forbidden_primitives={
            PrimitiveType.HORN_PROJECTION,
            PrimitiveType.CUTAWAY_INTRUSION,
            PrimitiveType.FLAT_SLAB_EDGE,
        },
        zone_expectations={
            "lower_bout": "convex_outward_smooth",
            "upper_bout": "convex_outward_smooth",
            "waist": "concave_inward_gradual",
            "butt_end": "rounded_termination",
        },
        symmetry_requirement=0.9,  # Highly symmetric
        description="Dreadnought/jumbo-style rounded acoustic body"
    ),

    "double_cut_horns": VariantRule(
        rule_id="double_cut_horns",
        name="Double Cutaway with Horns",
        required_primitives={
            PrimitiveType.HORN_PROJECTION,
        },
        zone_expectations={
            "horn_left": "projection_neckward",
            "horn_right": "projection_neckward",
            "waist": "present",
        },
        symmetry_requirement=0.6,  # Moderately symmetric
        description="SG/Stratocaster-style double cutaway with horn projections"
    ),
}


class VariantGrammar:
    """
    Matches body primitives against variant grammar rules.

    Classifies bodies by behavior, not by brand.
    """

    def __init__(self, rules: Dict[str, VariantRule] = None):
        self.rules = rules or VARIANT_RULES

    def classify(
        self,
        primitives: List[MorphologyPrimitive],
        asymmetry_score: float = 0.0
    ) -> VariantMatch:
        """
        Classify a body based on its primitives.

        Args:
            primitives: List of detected primitives
            asymmetry_score: Body asymmetry score (0=symmetric, 1=asymmetric)

        Returns:
            VariantMatch with classification results
        """
        # Collect primitive types present
        prim_types = {p.primitive_type for p in primitives}

        # Detect behaviors
        horn_behavior = self._detect_horn_behavior(primitives)
        waist_behavior = self._detect_waist_behavior(primitives)
        bout_behavior = self._detect_bout_behavior(primitives)

        # Score each rule
        rule_scores: Dict[str, float] = {}
        matched_rules = []
        violated_rules = []

        for rule_id, rule in self.rules.items():
            score, matched, violated = self._score_rule(
                rule, prim_types, asymmetry_score
            )
            rule_scores[rule_id] = score
            if matched:
                matched_rules.append(rule_id)
            if violated:
                violated_rules.append(rule_id)

        # Determine best morphology class
        best_rule = max(rule_scores, key=rule_scores.get) if rule_scores else None
        best_score = rule_scores.get(best_rule, 0.0) if best_rule else 0.0

        morphology_class = self._rule_to_morphology_class(best_rule)

        return VariantMatch(
            morphology_class=morphology_class,
            horn_behavior=horn_behavior,
            waist_behavior=waist_behavior,
            bout_behavior=bout_behavior,
            confidence=best_score,
            matched_rules=matched_rules,
            violated_rules=violated_rules,
        )

    def _score_rule(
        self,
        rule: VariantRule,
        prim_types: Set[PrimitiveType],
        asymmetry_score: float
    ) -> tuple:
        """
        Score how well primitives match a rule.

        Returns: (score, is_matched, is_violated)
        """
        score = 0.0
        matched = False
        violated = False

        # Check required primitives
        required_present = rule.required_primitives & prim_types
        required_missing = rule.required_primitives - prim_types

        if rule.required_primitives:
            score += len(required_present) / len(rule.required_primitives) * 0.5

        # Check forbidden primitives
        forbidden_present = rule.forbidden_primitives & prim_types
        if forbidden_present:
            score -= len(forbidden_present) * 0.2
            violated = True

        # Check symmetry requirement
        symmetry_match = 1.0 - abs(rule.symmetry_requirement - (1.0 - asymmetry_score))
        score += symmetry_match * 0.3

        # Determine if matched
        if not required_missing and not forbidden_present:
            matched = True
            score += 0.2

        return (max(0.0, min(1.0, score)), matched, violated)

    def _detect_horn_behavior(self, primitives: List[MorphologyPrimitive]) -> HornBehavior:
        """Detect horn behavior from primitives."""
        left_horn = any(
            p.primitive_type == PrimitiveType.HORN_PROJECTION and p.side == "left"
            for p in primitives
        )
        right_horn = any(
            p.primitive_type == PrimitiveType.HORN_PROJECTION and p.side == "right"
            for p in primitives
        )
        left_cutaway = any(
            p.primitive_type == PrimitiveType.CUTAWAY_INTRUSION and p.side == "left"
            for p in primitives
        )
        right_cutaway = any(
            p.primitive_type == PrimitiveType.CUTAWAY_INTRUSION and p.side == "right"
            for p in primitives
        )

        if left_horn and right_horn:
            # Check if pointed or rounded based on geometry
            horn_prims = [p for p in primitives if p.primitive_type == PrimitiveType.HORN_PROJECTION]
            if all(p.geometry_type == GeometryType.LINE for p in horn_prims):
                return HornBehavior.ANGULAR_HORNS
            return HornBehavior.SYMMETRIC_HORNS

        if right_cutaway and not left_cutaway:
            return HornBehavior.SINGLE_CUT_TREBLE
        if left_cutaway and not right_cutaway:
            return HornBehavior.SINGLE_CUT_BASS

        if not left_horn and not right_horn:
            return HornBehavior.NO_HORNS

        return HornBehavior.SYMMETRIC_HORNS

    def _detect_waist_behavior(self, primitives: List[MorphologyPrimitive]) -> WaistBehavior:
        """Detect waist behavior from primitives."""
        waist_prims = [
            p for p in primitives
            if p.zone_assignment.primary_zone == "waist"
        ]

        if not waist_prims:
            return WaistBehavior.SUPPRESSED_WAIST

        # Check curvature
        concave_count = sum(
            1 for p in waist_prims
            if p.curvature_class == CurvatureClass.CONCAVE_INWARD
        )
        angular_count = sum(
            1 for p in waist_prims
            if p.geometry_type == GeometryType.LINE
        )

        if angular_count > concave_count:
            return WaistBehavior.ANGULAR_WAIST

        # Check depth based on x_range
        max_indent = max(
            abs(p.x_range[0]) if p.side == "left" else abs(p.x_range[1])
            for p in waist_prims
        ) if waist_prims else 0

        if max_indent < 0.1:
            return WaistBehavior.SHALLOW_WAIST
        elif max_indent > 0.25:
            return WaistBehavior.DEEP_WAIST

        return WaistBehavior.MODERATE_WAIST

    def _detect_bout_behavior(self, primitives: List[MorphologyPrimitive]) -> BoutBehavior:
        """Detect bout behavior from primitives."""
        bout_prims = [
            p for p in primitives
            if p.zone_assignment.primary_zone in ("lower_bout", "upper_bout")
        ]

        if not bout_prims:
            return BoutBehavior.ROUNDED_BOUTS

        # Check for angular vs rounded
        angular_count = sum(1 for p in bout_prims if p.geometry_type == GeometryType.LINE)
        rounded_count = sum(1 for p in bout_prims if p.geometry_type == GeometryType.ARC)

        if angular_count > rounded_count:
            return BoutBehavior.ANGULAR_BOUTS

        # Check for asymmetry
        left_bouts = [p for p in bout_prims if p.side == "left"]
        right_bouts = [p for p in bout_prims if p.side == "right"]

        if left_bouts and right_bouts:
            left_extent = max(abs(p.x_range[0]) for p in left_bouts)
            right_extent = max(abs(p.x_range[1]) for p in right_bouts)
            if abs(left_extent - right_extent) > 0.1:
                return BoutBehavior.ASYMMETRIC_BOUTS

        return BoutBehavior.ROUNDED_BOUTS

    def _rule_to_morphology_class(self, rule_id: Optional[str]) -> BodyMorphologyClass:
        """Map rule ID to morphology class."""
        mapping = {
            "rounded_single_cut": BodyMorphologyClass.ROUNDED_SINGLE_CUT,
            "angular_wedge": BodyMorphologyClass.ANGULAR_WEDGE,
            "offset_double_cut": BodyMorphologyClass.OFFSET_WAIST,
            "slab_body": BodyMorphologyClass.SLAB_BODY,
            "rounded_acoustic": BodyMorphologyClass.ROUNDED_ACOUSTIC,
            "double_cut_horns": BodyMorphologyClass.DOUBLE_CUT,
        }
        return mapping.get(rule_id, BodyMorphologyClass.UNKNOWN)
