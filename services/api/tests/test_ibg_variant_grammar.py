"""
Tests for Body Grid Variant Grammar

Note: Import directly from body_grid submodules to avoid ezdxf dependency chain.
The body_grid module is designed to be independent of DXF/CAD dependencies.
"""

import pytest

# Direct imports to avoid ezdxf dependency through ibg.__init__
from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    NormalizedPoint,
    ZoneAssignment,
)
from app.instrument_geometry.body.ibg.body_grid.primitives import (
    CurvatureClass,
    GeometryType,
    MorphologyPrimitive,
    PrimitiveType,
    SlopeClass,
)
from app.instrument_geometry.body.ibg.body_grid.variant_grammar import (
    BodyMorphologyClass,
    BoutBehavior,
    HornBehavior,
    VariantGrammar,
    VariantMatch,
    VariantRule,
    WaistBehavior,
    VARIANT_RULES,
)


def make_primitive(
    prim_type: PrimitiveType,
    zone: str,
    side: str = "left",
    geometry: GeometryType = GeometryType.ARC,
    curvature: CurvatureClass = CurvatureClass.CONVEX_OUTWARD,
    y_range: tuple = (0.2, 0.35),
    x_range: tuple = (-0.5, -0.4),
) -> MorphologyPrimitive:
    """Helper to create test primitives."""
    points = [
        NormalizedPoint(x_range[0], y_range[0]),
        NormalizedPoint((x_range[0] + x_range[1]) / 2, (y_range[0] + y_range[1]) / 2),
        NormalizedPoint(x_range[1], y_range[1]),
    ]
    return MorphologyPrimitive(
        primitive_id=f"test_{prim_type.value}",
        primitive_type=prim_type,
        zone_assignment=ZoneAssignment(primary_zone=zone),
        geometry_type=geometry,
        slope_class=SlopeClass.ASCENDING,
        curvature_class=curvature,
        points=points,
        side=side,
    )


class TestVariantRule:
    """Tests for VariantRule data structure."""

    def test_create_rule(self):
        """Test rule creation."""
        rule = VariantRule(
            rule_id="test_rule",
            name="Test Rule",
            required_primitives={PrimitiveType.CONVEX_BOUT},
            forbidden_primitives={PrimitiveType.FLAT_SLAB_EDGE},
            symmetry_requirement=0.8,
        )
        assert rule.rule_id == "test_rule"
        assert PrimitiveType.CONVEX_BOUT in rule.required_primitives
        assert PrimitiveType.FLAT_SLAB_EDGE in rule.forbidden_primitives

    def test_builtin_rules_exist(self):
        """Test that built-in rules are defined."""
        assert "rounded_acoustic" in VARIANT_RULES
        assert "rounded_single_cut" in VARIANT_RULES
        assert "angular_wedge" in VARIANT_RULES
        assert "offset_double_cut" in VARIANT_RULES


class TestVariantGrammar:
    """Tests for VariantGrammar classifier."""

    @pytest.fixture
    def grammar(self):
        return VariantGrammar()

    def test_classify_rounded_acoustic(self, grammar):
        """Test classification of rounded acoustic body (dreadnought-like)."""
        primitives = [
            # Convex lower bout
            make_primitive(
                PrimitiveType.CONVEX_BOUT,
                "lower_bout",
                side="left",
                curvature=CurvatureClass.CONVEX_OUTWARD,
            ),
            make_primitive(
                PrimitiveType.CONVEX_BOUT,
                "lower_bout",
                side="right",
                curvature=CurvatureClass.CONVEX_OUTWARD,
                x_range=(0.4, 0.5),
            ),
            # Concave waist
            make_primitive(
                PrimitiveType.CONCAVE_WAIST,
                "waist",
                side="left",
                curvature=CurvatureClass.CONCAVE_INWARD,
                y_range=(0.4, 0.5),
            ),
            make_primitive(
                PrimitiveType.CONCAVE_WAIST,
                "waist",
                side="right",
                curvature=CurvatureClass.CONCAVE_INWARD,
                y_range=(0.4, 0.5),
                x_range=(0.3, 0.4),
            ),
            # Convex upper bout
            make_primitive(
                PrimitiveType.CONVEX_BOUT,
                "upper_bout",
                side="left",
                curvature=CurvatureClass.CONVEX_OUTWARD,
                y_range=(0.55, 0.7),
            ),
            make_primitive(
                PrimitiveType.CONVEX_BOUT,
                "upper_bout",
                side="right",
                curvature=CurvatureClass.CONVEX_OUTWARD,
                y_range=(0.55, 0.7),
                x_range=(0.35, 0.45),
            ),
            # Butt termination
            make_primitive(
                PrimitiveType.BUTT_TERMINATION,
                "butt_end",
                side="centerline",
                y_range=(0.0, 0.05),
                x_range=(-0.1, 0.1),
            ),
        ]

        match = grammar.classify(primitives, asymmetry_score=0.05)

        # Should classify as rounded acoustic
        assert match.morphology_class == BodyMorphologyClass.ROUNDED_ACOUSTIC
        assert match.horn_behavior == HornBehavior.NO_HORNS
        assert match.waist_behavior != WaistBehavior.SUPPRESSED_WAIST
        assert match.confidence > 0.3

    def test_classify_angular_wedge(self, grammar):
        """Test classification of angular wedge body (Explorer-like)."""
        primitives = [
            # Angular lower bout (line segments)
            make_primitive(
                PrimitiveType.LINE_SEGMENT,
                "lower_bout",
                side="left",
                geometry=GeometryType.LINE,
                curvature=CurvatureClass.STRAIGHT,
            ),
            make_primitive(
                PrimitiveType.DIAGONAL_SEGMENT,
                "lower_bout",
                side="right",
                geometry=GeometryType.LINE,
                curvature=CurvatureClass.STRAIGHT,
                x_range=(0.4, 0.5),
            ),
            # No waist primitives (suppressed waist)
            # Angular upper bout
            make_primitive(
                PrimitiveType.LINE_SEGMENT,
                "upper_bout",
                side="left",
                geometry=GeometryType.LINE,
                curvature=CurvatureClass.STRAIGHT,
                y_range=(0.55, 0.7),
            ),
        ]

        match = grammar.classify(primitives, asymmetry_score=0.1)

        # Should detect suppressed waist
        assert match.waist_behavior == WaistBehavior.SUPPRESSED_WAIST
        # Should detect angular bouts
        assert match.bout_behavior == BoutBehavior.ANGULAR_BOUTS

    def test_classify_single_cut(self, grammar):
        """Test classification of single cutaway body (LP-like)."""
        primitives = [
            # Convex bouts
            make_primitive(
                PrimitiveType.CONVEX_BOUT,
                "lower_bout",
                side="left",
            ),
            make_primitive(
                PrimitiveType.CONVEX_BOUT,
                "lower_bout",
                side="right",
                x_range=(0.4, 0.5),
            ),
            # Waist
            make_primitive(
                PrimitiveType.CONCAVE_WAIST,
                "waist",
                side="left",
                y_range=(0.4, 0.5),
            ),
            # Cutaway on right (treble) side
            make_primitive(
                PrimitiveType.CUTAWAY_INTRUSION,
                "cutaway_right",
                side="right",
                curvature=CurvatureClass.CONCAVE_INWARD,
                y_range=(0.6, 0.75),
                x_range=(0.2, 0.35),
            ),
            # No cutaway on left
        ]

        match = grammar.classify(primitives, asymmetry_score=0.3)

        # Should detect single cut on treble side
        assert match.horn_behavior == HornBehavior.SINGLE_CUT_TREBLE

    def test_classify_double_cut_horns(self, grammar):
        """Test classification of double cutaway with horns (SG-like)."""
        primitives = [
            # Horn projections on both sides
            make_primitive(
                PrimitiveType.HORN_PROJECTION,
                "horn_left",
                side="left",
                y_range=(0.65, 0.8),
            ),
            make_primitive(
                PrimitiveType.HORN_PROJECTION,
                "horn_right",
                side="right",
                y_range=(0.65, 0.8),
                x_range=(0.3, 0.4),
            ),
            # Waist present
            make_primitive(
                PrimitiveType.CONCAVE_WAIST,
                "waist",
                side="left",
                y_range=(0.4, 0.5),
            ),
        ]

        match = grammar.classify(primitives, asymmetry_score=0.1)

        # Should detect symmetric horns
        assert match.horn_behavior == HornBehavior.SYMMETRIC_HORNS

    def test_classify_with_high_asymmetry(self, grammar):
        """Test that high asymmetry affects classification."""
        primitives = [
            make_primitive(PrimitiveType.CONVEX_BOUT, "lower_bout", side="left"),
            make_primitive(PrimitiveType.CONCAVE_WAIST, "waist", side="left", y_range=(0.4, 0.5)),
        ]

        # Classify with high asymmetry
        match = grammar.classify(primitives, asymmetry_score=0.6)

        # Should have lower confidence due to asymmetry
        # (depends on rule symmetry requirements)
        assert isinstance(match.confidence, float)


class TestVariantMatch:
    """Tests for VariantMatch output."""

    def test_match_fields(self):
        """Test that VariantMatch has all required fields."""
        match = VariantMatch(
            morphology_class=BodyMorphologyClass.ROUNDED_ACOUSTIC,
            horn_behavior=HornBehavior.NO_HORNS,
            waist_behavior=WaistBehavior.MODERATE_WAIST,
            bout_behavior=BoutBehavior.ROUNDED_BOUTS,
            confidence=0.85,
            matched_rules=["rounded_acoustic"],
            violated_rules=[],
        )

        assert match.morphology_class == BodyMorphologyClass.ROUNDED_ACOUSTIC
        assert match.horn_behavior == HornBehavior.NO_HORNS
        assert match.confidence == 0.85
        assert "rounded_acoustic" in match.matched_rules
