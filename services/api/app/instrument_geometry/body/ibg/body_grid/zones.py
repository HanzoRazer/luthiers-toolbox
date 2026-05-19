"""
Body Grid Zones — Semantic Region Definitions
==============================================

Defines the body zones used for morphology reasoning.

Zones are fuzzy regions with soft boundaries that can overlap.
Each zone has a semantic role describing body behavior in that region.

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .body_grid_schema import NormalizedPoint, ZoneAssignment


class ZoneId(Enum):
    """Canonical zone identifiers."""
    CENTERLINE = "centerline"
    UPPER_BOUT = "upper_bout"
    WAIST = "waist"
    LOWER_BOUT = "lower_bout"
    HORN_LEFT = "horn_left"
    HORN_RIGHT = "horn_right"
    CUTAWAY_LEFT = "cutaway_left"
    CUTAWAY_RIGHT = "cutaway_right"
    NECK_POCKET = "neck_pocket"
    BRIDGE_REGION = "bridge_region"
    LEFT_FLANK = "left_flank"
    RIGHT_FLANK = "right_flank"
    OUTER_BOUNDARY = "outer_boundary"
    BUTT_END = "butt_end"
    SHOULDER = "shoulder"


@dataclass
class ZoneDefinition:
    """
    Definition of a body zone.

    Attributes:
        zone_id: Canonical zone identifier
        name: Human-readable name
        y_range: (min, max) normalized Y range (0=butt, 1=neck)
        x_behavior: Expected X behavior in this zone
        semantic_role: What this zone represents morphologically
        expected_behaviors: What body contours typically do here
        variant_behaviors: How variants may differ
        forbidden_behaviors: What should never happen here
    """
    zone_id: ZoneId
    name: str
    y_range: Tuple[float, float]
    x_behavior: str
    semantic_role: str
    expected_behaviors: List[str] = field(default_factory=list)
    variant_behaviors: List[str] = field(default_factory=list)
    forbidden_behaviors: List[str] = field(default_factory=list)


# Zone definitions with normalized Y ranges and behaviors
ZONE_DEFINITIONS: Dict[ZoneId, ZoneDefinition] = {
    ZoneId.BUTT_END: ZoneDefinition(
        zone_id=ZoneId.BUTT_END,
        y_range=(0.0, 0.08),
        name="Butt End",
        x_behavior="convergent_to_centerline",
        semantic_role="Tail/end block region where sides meet",
        expected_behaviors=[
            "rounded_termination",
            "centerline_convergence",
            "end_block_flat"
        ],
        variant_behaviors=[
            "pointed_termination",  # Some classical guitars
            "squared_termination"   # Some electric bodies
        ],
        forbidden_behaviors=[
            "divergent_from_centerline",
            "horn_projection"
        ]
    ),

    ZoneId.LOWER_BOUT: ZoneDefinition(
        zone_id=ZoneId.LOWER_BOUT,
        y_range=(0.08, 0.40),
        name="Lower Bout",
        x_behavior="maximum_width_region",
        semantic_role="Widest body region, primary resonant mass",
        expected_behaviors=[
            "convex_arc_outward",
            "maximum_x_extent",
            "smooth_curvature"
        ],
        variant_behaviors=[
            "asymmetric_bout",      # Offset bodies
            "angular_lower_bout",   # Explorer-style
            "extended_lower_bout"   # Jumbo bodies
        ],
        forbidden_behaviors=[
            "concave_inward",
            "horn_projection"
        ]
    ),

    ZoneId.WAIST: ZoneDefinition(
        zone_id=ZoneId.WAIST,
        y_range=(0.35, 0.55),
        name="Waist",
        x_behavior="minimum_width_region",
        semantic_role="Narrowest body region, ergonomic cutaway",
        expected_behaviors=[
            "concave_arc_inward",
            "minimum_x_extent",
            "smooth_transition"
        ],
        variant_behaviors=[
            "suppressed_waist",     # Explorer, V-style
            "deep_waist",           # Classical style
            "asymmetric_waist",     # Offset bodies
            "angular_waist"         # Wedge bodies
        ],
        forbidden_behaviors=[
            "convex_outward",
            "wider_than_bouts"
        ]
    ),

    ZoneId.UPPER_BOUT: ZoneDefinition(
        zone_id=ZoneId.UPPER_BOUT,
        y_range=(0.50, 0.75),
        name="Upper Bout",
        x_behavior="secondary_width_region",
        semantic_role="Secondary resonant mass, horn attachment region",
        expected_behaviors=[
            "convex_arc_outward",
            "narrower_than_lower_bout",
            "smooth_curvature"
        ],
        variant_behaviors=[
            "horn_projection",      # LP-style
            "angular_upper_bout",   # Explorer-style
            "suppressed_upper_bout" # SG-style
        ],
        forbidden_behaviors=[
            "wider_than_lower_bout"  # Violates standard guitar morphology
        ]
    ),

    ZoneId.HORN_LEFT: ZoneDefinition(
        zone_id=ZoneId.HORN_LEFT,
        y_range=(0.60, 0.85),
        name="Left Horn",
        x_behavior="projection_from_upper_bout",
        semantic_role="Upper body projection (bass side)",
        expected_behaviors=[
            "projection_neckward",
            "smooth_junction_to_bout"
        ],
        variant_behaviors=[
            "pointed_horn",         # LP-style
            "rounded_horn",         # SG-style
            "angular_horn",         # Explorer-style
            "absent_horn"           # Offset bodies
        ],
        forbidden_behaviors=[]
    ),

    ZoneId.HORN_RIGHT: ZoneDefinition(
        zone_id=ZoneId.HORN_RIGHT,
        y_range=(0.60, 0.85),
        name="Right Horn",
        x_behavior="projection_from_upper_bout",
        semantic_role="Upper body projection (treble side)",
        expected_behaviors=[
            "projection_neckward",
            "smooth_junction_to_bout"
        ],
        variant_behaviors=[
            "pointed_horn",
            "rounded_horn",
            "angular_horn",
            "cutaway_intrusion"     # Single-cut replaces horn with cutaway
        ],
        forbidden_behaviors=[]
    ),

    ZoneId.CUTAWAY_LEFT: ZoneDefinition(
        zone_id=ZoneId.CUTAWAY_LEFT,
        y_range=(0.55, 0.80),
        name="Left Cutaway",
        x_behavior="intrusion_into_upper_bout",
        semantic_role="Access cutaway on bass side (rare)",
        expected_behaviors=[
            "concave_intrusion",
            "smooth_neck_access"
        ],
        variant_behaviors=[
            "florentine_cutaway",
            "venetian_cutaway",
            "sharp_cutaway"
        ],
        forbidden_behaviors=[]
    ),

    ZoneId.CUTAWAY_RIGHT: ZoneDefinition(
        zone_id=ZoneId.CUTAWAY_RIGHT,
        y_range=(0.55, 0.80),
        name="Right Cutaway",
        x_behavior="intrusion_into_upper_bout",
        semantic_role="Access cutaway on treble side (common)",
        expected_behaviors=[
            "concave_intrusion",
            "smooth_neck_access"
        ],
        variant_behaviors=[
            "florentine_cutaway",
            "venetian_cutaway",
            "sharp_cutaway"
        ],
        forbidden_behaviors=[]
    ),

    ZoneId.NECK_POCKET: ZoneDefinition(
        zone_id=ZoneId.NECK_POCKET,
        y_range=(0.80, 1.0),
        name="Neck Pocket",
        x_behavior="convergent_to_neck_axis",
        semantic_role="Neck attachment region",
        expected_behaviors=[
            "convergence_to_neck_width",
            "smooth_shoulder_transition"
        ],
        variant_behaviors=[
            "set_neck_junction",
            "bolt_on_heel",
            "neck_through"
        ],
        forbidden_behaviors=[
            "divergent_from_neck"
        ]
    ),

    ZoneId.SHOULDER: ZoneDefinition(
        zone_id=ZoneId.SHOULDER,
        y_range=(0.75, 0.90),
        name="Shoulder",
        x_behavior="transition_bout_to_neck",
        semantic_role="Transition from upper bout to neck pocket",
        expected_behaviors=[
            "smooth_curvature_reduction",
            "gradual_width_reduction"
        ],
        variant_behaviors=[
            "sharp_shoulder",       # LP-style
            "sloped_shoulder",      # Classical
            "angular_shoulder"      # Explorer
        ],
        forbidden_behaviors=[]
    ),

    ZoneId.BRIDGE_REGION: ZoneDefinition(
        zone_id=ZoneId.BRIDGE_REGION,
        y_range=(0.15, 0.35),
        name="Bridge Region",
        x_behavior="centered_on_centerline",
        semantic_role="Bridge placement region (affects soundhole on acoustics)",
        expected_behaviors=[
            "flat_top_area",
            "centered_placement"
        ],
        variant_behaviors=[
            "offset_bridge",        # Some archtops
            "dual_bridge"           # Doubleneck
        ],
        forbidden_behaviors=[]
    ),

    ZoneId.LEFT_FLANK: ZoneDefinition(
        zone_id=ZoneId.LEFT_FLANK,
        y_range=(0.0, 1.0),
        name="Left Flank",
        x_behavior="full_left_profile",
        semantic_role="Complete left side contour (bass side)",
        expected_behaviors=[
            "continuous_contour",
            "smooth_zone_transitions"
        ],
        variant_behaviors=[
            "asymmetric_profile"
        ],
        forbidden_behaviors=[
            "discontinuous_contour"
        ]
    ),

    ZoneId.RIGHT_FLANK: ZoneDefinition(
        zone_id=ZoneId.RIGHT_FLANK,
        y_range=(0.0, 1.0),
        name="Right Flank",
        x_behavior="full_right_profile",
        semantic_role="Complete right side contour (treble side)",
        expected_behaviors=[
            "continuous_contour",
            "smooth_zone_transitions"
        ],
        variant_behaviors=[
            "asymmetric_profile",
            "cutaway_intrusion"
        ],
        forbidden_behaviors=[
            "discontinuous_contour"
        ]
    ),

    ZoneId.CENTERLINE: ZoneDefinition(
        zone_id=ZoneId.CENTERLINE,
        y_range=(0.0, 1.0),
        name="Centerline",
        x_behavior="x_norm_equals_zero",
        semantic_role="Body axis of reference (not symmetry enforcer)",
        expected_behaviors=[
            "neck_axis_alignment",
            "bridge_alignment"
        ],
        variant_behaviors=[
            "offset_centerline"     # Some offset bodies
        ],
        forbidden_behaviors=[]
    ),
}


class ZoneClassifier:
    """
    Classifies points and segments into fuzzy zone assignments.
    """

    def __init__(self, zone_definitions: Dict[ZoneId, ZoneDefinition] = None):
        self.zones = zone_definitions or ZONE_DEFINITIONS

    def classify_point(self, point: NormalizedPoint) -> ZoneAssignment:
        """
        Assign a normalized point to zones with fuzzy weights.

        Args:
            point: Point in centerline-relative normalized coordinates

        Returns:
            ZoneAssignment with primary zone and weighted secondary zones
        """
        weights: Dict[str, float] = {}

        for zone_id, zone_def in self.zones.items():
            weight = self._compute_zone_weight(point, zone_def)
            if weight > 0.01:  # Threshold for relevance
                weights[zone_id.value] = weight

        if not weights:
            # Fallback: assign to outer_boundary
            return ZoneAssignment(
                primary_zone=ZoneId.OUTER_BOUNDARY.value,
                zone_weights={ZoneId.OUTER_BOUNDARY.value: 1.0}
            )

        # Find primary (highest weight)
        primary = max(weights, key=weights.get)
        secondaries = [z for z in weights if z != primary and weights[z] > 0.1]

        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return ZoneAssignment(
            primary_zone=primary,
            secondary_zones=secondaries,
            zone_weights=weights
        )

    def _compute_zone_weight(
        self,
        point: NormalizedPoint,
        zone_def: ZoneDefinition
    ) -> float:
        """
        Compute weight of point belonging to a zone.

        Uses smooth falloff at zone boundaries.
        """
        y_min, y_max = zone_def.y_range
        y = point.y_norm

        # Check if point is in Y range (with soft boundaries)
        if y < y_min - 0.1 or y > y_max + 0.1:
            return 0.0

        # Compute Y membership with soft boundaries
        if y_min <= y <= y_max:
            y_membership = 1.0
        elif y < y_min:
            y_membership = 1.0 - (y_min - y) / 0.1
        else:
            y_membership = 1.0 - (y - y_max) / 0.1

        y_membership = max(0.0, min(1.0, y_membership))

        # Apply X behavior filtering for side-specific zones
        x = point.x_norm

        if zone_def.zone_id == ZoneId.LEFT_FLANK and x > 0:
            return 0.0
        if zone_def.zone_id == ZoneId.RIGHT_FLANK and x < 0:
            return 0.0
        if zone_def.zone_id == ZoneId.HORN_LEFT and x > 0:
            return y_membership * 0.5  # Reduced weight
        if zone_def.zone_id == ZoneId.HORN_RIGHT and x < 0:
            return y_membership * 0.5
        if zone_def.zone_id == ZoneId.CUTAWAY_LEFT and x > 0:
            return 0.0
        if zone_def.zone_id == ZoneId.CUTAWAY_RIGHT and x < 0:
            return 0.0

        return y_membership

    def get_zone_at_y(self, y_norm: float) -> List[ZoneId]:
        """Get all zones that include the given Y position."""
        result = []
        for zone_id, zone_def in self.zones.items():
            y_min, y_max = zone_def.y_range
            if y_min <= y_norm <= y_max:
                result.append(zone_id)
        return result
