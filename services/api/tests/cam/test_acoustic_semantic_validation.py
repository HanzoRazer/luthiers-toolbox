"""
Acoustic Semantic Validation Tests.

Sprint: MRP-5F
Tests:
    1. Valid acoustic semantics acceptance
    2. Invalid thickness rejection
    3. Taper consistency validation
    4. Enum validation
    5. Runtime support classification
    6. Authority boundary preservation
"""

import pytest

from app.export.cad_semantics import (
    AcousticSemantics,
    BodyCategory,
    CadSemantics,
    ClosureType,
    ContinuityTarget,
    FlatBodySemantics,
    PlateRelationshipSemantics,
    PlateType,
    RimSemantics,
    RuntimeSupport,
    SemanticValidationResult,
    SideProfileSemantics,
    SideProfileType,
    ThicknessSemantics,
    classify_acoustic_runtime_support,
    validate_acoustic_semantics,
)


# ─── Valid Semantics Tests ───────────────────────────────────────────────────


class TestValidAcousticSemantics:
    """Tests for valid acoustic semantic configurations."""

    def test_valid_dreadnought_semantics(self):
        """Dreadnought acoustic semantics should validate."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
            acoustic=AcousticSemantics(
                thickness=ThicknessSemantics(
                    top_thickness_mm=2.8,
                    back_thickness_mm=2.5,
                    side_depth_mm=121.0,
                ),
                side_profile=SideProfileSemantics(
                    type=SideProfileType.TAPERED,
                    max_depth_mm=121.0,
                    min_depth_mm=105.0,
                ),
                rim=RimSemantics(
                    continuity_target=ContinuityTarget.G1,
                ),
            ),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True
        assert len(result.blocking_errors) == 0
        assert result.runtime_support == RuntimeSupport.SEMANTIC_ONLY

    def test_valid_flat_body_semantics(self):
        """Flat body semantics should validate and be SUPPORTED."""
        semantics = CadSemantics(
            body_category=BodyCategory.FLAT_BODY,
            flat_body=FlatBodySemantics(
                uniform_thickness_mm=45.0,
            ),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True
        assert result.runtime_support == RuntimeSupport.SUPPORTED

    def test_valid_minimal_acoustic_semantics(self):
        """Minimal acoustic semantics should validate."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
            acoustic=AcousticSemantics(),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True
        assert result.runtime_support == RuntimeSupport.SEMANTIC_ONLY

    def test_valid_hollowbody_semantics(self):
        """Hollow electric semantics should validate."""
        semantics = CadSemantics(
            body_category=BodyCategory.HOLLOW_ELECTRIC,
            acoustic=AcousticSemantics(
                thickness=ThicknessSemantics(
                    side_depth_mm=57.0,
                ),
                rim=RimSemantics(
                    continuity_target=ContinuityTarget.G0,
                ),
            ),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True
        assert result.runtime_support == RuntimeSupport.SEMANTIC_ONLY


# ─── Invalid Thickness Tests ─────────────────────────────────────────────────


class TestInvalidThicknessRejection:
    """Tests for invalid thickness value rejection."""

    def test_negative_top_thickness_blocks(self):
        """Negative top thickness should be blocked by Pydantic."""
        with pytest.raises(ValueError):
            ThicknessSemantics(top_thickness_mm=-1.0)

    def test_zero_top_thickness_blocks(self):
        """Zero top thickness should be blocked."""
        with pytest.raises(ValueError):
            ThicknessSemantics(top_thickness_mm=0.0)

    def test_negative_back_thickness_blocks(self):
        """Negative back thickness should be blocked."""
        with pytest.raises(ValueError):
            ThicknessSemantics(back_thickness_mm=-2.5)

    def test_negative_side_depth_blocks(self):
        """Negative side depth should be blocked."""
        with pytest.raises(ValueError):
            ThicknessSemantics(side_depth_mm=-100.0)

    def test_very_small_thickness_blocks(self):
        """Thickness below minimum should be blocked."""
        with pytest.raises(ValueError):
            ThicknessSemantics(top_thickness_mm=0.05)

    def test_excessive_thickness_blocks(self):
        """Thickness above maximum should be blocked."""
        with pytest.raises(ValueError):
            ThicknessSemantics(top_thickness_mm=100.0)


# ─── Taper Consistency Tests ─────────────────────────────────────────────────


class TestTaperConsistency:
    """Tests for side profile taper validation."""

    def test_valid_taper_values(self):
        """Valid taper with min < max should pass."""
        profile = SideProfileSemantics(
            type=SideProfileType.TAPERED,
            max_depth_mm=121.0,
            min_depth_mm=105.0,
        )

        assert profile.max_depth_mm == 121.0
        assert profile.min_depth_mm == 105.0

    def test_taper_min_greater_than_max_blocks(self):
        """Taper with min > max should be blocked."""
        with pytest.raises(ValueError, match="cannot exceed"):
            SideProfileSemantics(
                type=SideProfileType.TAPERED,
                max_depth_mm=100.0,
                min_depth_mm=120.0,
            )

    def test_taper_equal_values_allowed(self):
        """Equal min/max should be allowed (no actual taper)."""
        profile = SideProfileSemantics(
            type=SideProfileType.TAPERED,
            max_depth_mm=100.0,
            min_depth_mm=100.0,
        )

        assert profile.max_depth_mm == profile.min_depth_mm

    def test_incomplete_taper_warns(self):
        """Tapered profile without min/max should warn."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
            acoustic=AcousticSemantics(
                side_profile=SideProfileSemantics(
                    type=SideProfileType.TAPERED,
                    # Missing max/min depth
                ),
            ),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True  # Warnings don't block
        assert len(result.warnings) > 0
        assert any("missing" in w.lower() for w in result.warnings)


# ─── Enum Validation Tests ───────────────────────────────────────────────────


class TestEnumValidation:
    """Tests for enum value validation."""

    def test_valid_body_category_enum(self):
        """Valid body category values should work."""
        for category in BodyCategory:
            semantics = CadSemantics(body_category=category)
            result = validate_acoustic_semantics(semantics)
            assert result.valid is True

    def test_valid_continuity_target_enum(self):
        """Valid continuity targets should work."""
        for target in ContinuityTarget:
            rim = RimSemantics(continuity_target=target)
            assert rim.continuity_target == target

    def test_valid_plate_type_enum(self):
        """Valid plate types should work."""
        for plate_type in PlateType:
            plate = PlateRelationshipSemantics(top_type=plate_type)
            assert plate.top_type == plate_type

    def test_invalid_enum_string_rejected(self):
        """Invalid enum string should be rejected by Pydantic."""
        with pytest.raises(ValueError):
            CadSemantics(body_category="invalid_category")


# ─── Runtime Support Classification Tests ────────────────────────────────────


class TestRuntimeSupportClassification:
    """Tests for runtime support classification."""

    def test_flat_body_is_supported(self):
        """Flat body should be SUPPORTED."""
        semantics = CadSemantics(
            body_category=BodyCategory.FLAT_BODY,
            flat_body=FlatBodySemantics(uniform_thickness_mm=45.0),
        )

        assert semantics.get_runtime_support() == RuntimeSupport.SUPPORTED

    def test_acoustic_flat_top_is_semantic_only(self):
        """Acoustic flat top should be SEMANTIC_ONLY."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
        )

        assert semantics.get_runtime_support() == RuntimeSupport.SEMANTIC_ONLY

    def test_archtop_is_semantic_only(self):
        """Archtop should be SEMANTIC_ONLY."""
        semantics = CadSemantics(
            body_category=BodyCategory.ARCHTOP,
        )

        assert semantics.get_runtime_support() == RuntimeSupport.SEMANTIC_ONLY

    def test_resonator_is_unsupported(self):
        """Resonator should be UNSUPPORTED."""
        semantics = CadSemantics(
            body_category=BodyCategory.RESONATOR,
        )

        assert semantics.get_runtime_support() == RuntimeSupport.UNSUPPORTED

    def test_unknown_is_unsupported(self):
        """Unknown category should be UNSUPPORTED."""
        semantics = CadSemantics(
            body_category=BodyCategory.UNKNOWN,
        )

        assert semantics.get_runtime_support() == RuntimeSupport.UNSUPPORTED

    def test_classify_runtime_support_components(self):
        """Should classify each semantic component."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
            acoustic=AcousticSemantics(
                thickness=ThicknessSemantics(top_thickness_mm=2.8),
            ),
        )

        classification = classify_acoustic_runtime_support(semantics)

        assert classification["body_category"] == RuntimeSupport.SEMANTIC_ONLY
        assert classification["acoustic"] == RuntimeSupport.SEMANTIC_ONLY
        assert classification["acoustic.thickness"] == RuntimeSupport.SEMANTIC_ONLY


# ─── Acoustic Topology Requirement Tests ─────────────────────────────────────


class TestAcousticTopologyRequirement:
    """Tests for detecting acoustic topology requirements."""

    def test_flat_body_no_acoustic_topology(self):
        """Flat body should not require acoustic topology."""
        semantics = CadSemantics(
            body_category=BodyCategory.FLAT_BODY,
        )

        assert semantics.requires_acoustic_topology() is False

    def test_acoustic_flat_top_requires_topology(self):
        """Acoustic flat top should require topology."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
        )

        assert semantics.requires_acoustic_topology() is True

    def test_tapered_profile_requires_topology(self):
        """Tapered side profile should require acoustic topology."""
        semantics = CadSemantics(
            body_category=BodyCategory.FLAT_BODY,  # Even with flat_body
            acoustic=AcousticSemantics(
                side_profile=SideProfileSemantics(
                    type=SideProfileType.TAPERED,
                ),
            ),
        )

        assert semantics.requires_acoustic_topology() is True

    def test_radiused_back_requires_topology(self):
        """Radiused back should require acoustic topology."""
        semantics = CadSemantics(
            body_category=BodyCategory.FLAT_BODY,
            acoustic=AcousticSemantics(
                plate_relationship=PlateRelationshipSemantics(
                    back_type=PlateType.RADIUSED,
                ),
            ),
        )

        assert semantics.requires_acoustic_topology() is True

    def test_flat_plates_no_topology_requirement(self):
        """Flat plates should not require acoustic topology."""
        semantics = CadSemantics(
            body_category=BodyCategory.FLAT_BODY,
            acoustic=AcousticSemantics(
                plate_relationship=PlateRelationshipSemantics(
                    top_type=PlateType.FLAT,
                    back_type=PlateType.FLAT,
                ),
            ),
        )

        assert semantics.requires_acoustic_topology() is False


# ─── Effective Thickness Tests ───────────────────────────────────────────────


class TestEffectiveThickness:
    """Tests for effective thickness retrieval."""

    def test_flat_body_thickness_preferred(self):
        """flat_body.uniform_thickness_mm should be preferred."""
        semantics = CadSemantics(
            flat_body=FlatBodySemantics(uniform_thickness_mm=45.0),
            uniform_thickness_mm=38.0,  # Legacy field
        )

        assert semantics.get_effective_thickness() == 45.0

    def test_legacy_thickness_fallback(self):
        """Legacy uniform_thickness_mm should be used as fallback."""
        semantics = CadSemantics(
            uniform_thickness_mm=38.0,
        )

        assert semantics.get_effective_thickness() == 38.0

    def test_no_thickness_returns_none(self):
        """Missing thickness should return None."""
        semantics = CadSemantics()

        assert semantics.get_effective_thickness() is None


# ─── Plate Relationship Tests ────────────────────────────────────────────────


class TestPlateRelationship:
    """Tests for plate relationship validation."""

    def test_radiused_back_without_radius_warns(self):
        """Radiused back without radius value should warn."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
            acoustic=AcousticSemantics(
                plate_relationship=PlateRelationshipSemantics(
                    back_type=PlateType.RADIUSED,
                    # Missing back_radius_mm
                ),
            ),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True  # Warning, not blocking
        assert any("radius" in w.lower() for w in result.warnings)

    def test_radiused_back_with_radius_passes(self):
        """Radiused back with radius value should pass without warning."""
        semantics = CadSemantics(
            body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
            acoustic=AcousticSemantics(
                plate_relationship=PlateRelationshipSemantics(
                    back_type=PlateType.RADIUSED,
                    back_radius_mm=7620.0,
                ),
            ),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True
        # No warnings about missing radius
        assert not any("radius" in w.lower() for w in result.warnings)


# ─── Category/Semantic Mismatch Tests ────────────────────────────────────────


class TestCategorySemanticMismatch:
    """Tests for category/semantic mismatch warnings."""

    def test_flat_body_with_acoustic_topology_warns(self):
        """Flat body with acoustic topology requirements should warn."""
        semantics = CadSemantics(
            body_category=BodyCategory.FLAT_BODY,
            acoustic=AcousticSemantics(
                side_profile=SideProfileSemantics(
                    type=SideProfileType.TAPERED,
                    max_depth_mm=121.0,
                    min_depth_mm=105.0,
                ),
            ),
        )

        result = validate_acoustic_semantics(semantics)

        assert result.valid is True  # Warning, not blocking
        assert any("flat_body" in w for w in result.warnings)
