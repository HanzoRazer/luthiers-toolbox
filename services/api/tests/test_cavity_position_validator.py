# tests/test_cavity_position_validator.py

"""
Unit tests for cavity position validator (LP-GAP-02, EX-GAP-04).

Tests factory reference validation for:
- Les Paul cavities (pickups, control, neck pocket)
- Stratocaster cavities (3 pickups)
- Explorer cavities (2 pickups)
"""

import pytest
from app.calculators.cavity_position_validator import (
    CavityPosition,
    CavityType,
    FactoryReference,
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    validate_cavity,
    validate_all_cavities,
    validate_lespaul_cavities,
    validate_strat_cavities,
    validate_explorer_cavities,
    get_factory_reference,
    list_supported_models,
    list_cavity_types_for_model,
    LESPAUL_1959_REFERENCES,
    STRAT_REFERENCES,
    EXPLORER_REFERENCES,
)


# =============================================================================
# Factory Reference Tests
# =============================================================================

class TestFactoryReferences:
    """Test that factory references are defined correctly."""

    def test_lespaul_references_exist(self):
        """Les Paul should have pickup, control, and neck pocket references."""
        assert CavityType.PICKUP_NECK in LESPAUL_1959_REFERENCES
        assert CavityType.PICKUP_BRIDGE in LESPAUL_1959_REFERENCES
        assert CavityType.CONTROL_CAVITY in LESPAUL_1959_REFERENCES
        assert CavityType.NECK_POCKET in LESPAUL_1959_REFERENCES
        assert CavityType.BRIDGE_STUDS in LESPAUL_1959_REFERENCES
        assert CavityType.TAILPIECE_STUDS in LESPAUL_1959_REFERENCES

    def test_strat_references_exist(self):
        """Stratocaster should have 3 pickup references."""
        assert CavityType.PICKUP_NECK in STRAT_REFERENCES
        assert CavityType.PICKUP_MIDDLE in STRAT_REFERENCES
        assert CavityType.PICKUP_BRIDGE in STRAT_REFERENCES

    def test_explorer_references_exist(self):
        """Explorer should have 2 pickup references."""
        assert CavityType.PICKUP_NECK in EXPLORER_REFERENCES
        assert CavityType.PICKUP_BRIDGE in EXPLORER_REFERENCES

    def test_lespaul_neck_pickup_position(self):
        """Les Paul neck pickup should be at 155mm from bridge."""
        ref = LESPAUL_1959_REFERENCES[CavityType.PICKUP_NECK]
        assert ref.nominal_center_y_mm == 155.0
        assert ref.nominal_center_x_mm == 0.0  # Centered

    def test_lespaul_bridge_pickup_position(self):
        """Les Paul bridge pickup should be at 20mm from bridge."""
        ref = LESPAUL_1959_REFERENCES[CavityType.PICKUP_BRIDGE]
        assert ref.nominal_center_y_mm == 20.0

    def test_strat_pickup_positions(self):
        """Strat pickup positions from factory specs."""
        neck_ref = STRAT_REFERENCES[CavityType.PICKUP_NECK]
        middle_ref = STRAT_REFERENCES[CavityType.PICKUP_MIDDLE]
        bridge_ref = STRAT_REFERENCES[CavityType.PICKUP_BRIDGE]

        # 6.375", 3.625", 1.625" from bridge
        assert abs(neck_ref.nominal_center_y_mm - 161.9) < 0.1
        assert abs(middle_ref.nominal_center_y_mm - 92.1) < 0.1
        assert abs(bridge_ref.nominal_center_y_mm - 41.3) < 0.1


# =============================================================================
# CavityPosition Tests
# =============================================================================

class TestCavityPosition:
    """Test CavityPosition dataclass."""

    def test_to_dict(self):
        """CavityPosition should serialize to dict."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=155.0,
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.05,
        )
        d = cavity.to_dict()
        assert d["cavity_type"] == "pickup_neck"
        assert d["center_y_mm"] == 155.0
        assert d["width_mm"] == 40.0

    def test_optional_fields(self):
        """Optional fields should be None when not provided."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=155.0,
        )
        assert cavity.width_mm is None
        assert cavity.length_mm is None
        assert cavity.depth_mm is None


# =============================================================================
# Single Cavity Validation Tests
# =============================================================================

class TestValidateCavity:
    """Test single cavity validation."""

    def test_valid_lespaul_neck_pickup(self):
        """Valid Les Paul neck pickup should pass."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=155.0,  # Exact factory spec
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.05,
        )
        passed, issues = validate_cavity(cavity, "les_paul")
        assert passed is True
        assert len(issues) == 0

    def test_offset_lespaul_neck_pickup_warning(self):
        """Slightly off Les Paul neck pickup should warn."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=158.0,  # 3mm off (tolerance is 2mm)
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.05,
        )
        passed, issues = validate_cavity(cavity, "les_paul")
        # WARNING severity still passes (only ERROR/CRITICAL fail)
        assert passed is True
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING
        assert issues[0].field == "center_y_mm"

    def test_severely_offset_cavity_error(self):
        """Severely offset cavity should error."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=165.0,  # 10mm off (>2x tolerance)
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.05,
        )
        passed, issues = validate_cavity(cavity, "les_paul")
        assert passed is False
        assert any(i.severity == ValidationSeverity.ERROR for i in issues)

    def test_off_center_cavity_warning(self):
        """Off-centerline cavity should warn."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=3.0,  # 3mm off center (tolerance is 2mm)
            center_y_mm=155.0,
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=19.05,
        )
        passed, issues = validate_cavity(cavity, "les_paul")
        # WARNING severity still passes (only ERROR/CRITICAL fail)
        assert passed is True
        assert any(i.field == "center_x_mm" for i in issues)
        assert any(i.severity == ValidationSeverity.WARNING for i in issues)

    def test_depth_too_shallow_critical(self):
        """Way too shallow cavity should be critical."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=155.0,
            width_mm=40.0,
            length_mm=71.0,
            depth_mm=15.0,  # 4mm too shallow (>3x tolerance)
        )
        passed, issues = validate_cavity(cavity, "les_paul")
        assert passed is False
        assert any(i.severity == ValidationSeverity.CRITICAL for i in issues)

    def test_unknown_model_passes(self):
        """Unknown model should skip validation and pass."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=100.0,  # Way off
            center_y_mm=500.0,
        )
        passed, issues = validate_cavity(cavity, "unknown_model")
        assert passed is True
        assert len(issues) == 0

    def test_unknown_cavity_type_passes(self):
        """Cavity type without reference should skip validation."""
        cavity = CavityPosition(
            cavity_type=CavityType.WIRING_CHANNEL,  # No reference for this
            center_x_mm=0.0,
            center_y_mm=50.0,
        )
        passed, issues = validate_cavity(cavity, "les_paul")
        assert passed is True
        assert len(issues) == 0


# =============================================================================
# Multiple Cavity Validation Tests
# =============================================================================

class TestValidateAllCavities:
    """Test validation of multiple cavities."""

    def test_all_valid_lespaul_cavities(self):
        """All valid Les Paul cavities should pass."""
        cavities = [
            CavityPosition(
                cavity_type=CavityType.PICKUP_NECK,
                center_x_mm=0.0,
                center_y_mm=155.0,
                width_mm=40.0,
                length_mm=71.0,
                depth_mm=19.05,
            ),
            CavityPosition(
                cavity_type=CavityType.PICKUP_BRIDGE,
                center_x_mm=0.0,
                center_y_mm=20.0,
                width_mm=40.0,
                length_mm=71.0,
                depth_mm=19.05,
            ),
        ]
        result = validate_all_cavities(cavities, "les_paul")
        assert result.valid is True
        assert result.cavities_validated == 2
        assert result.cavities_passed == 2
        assert len(result.issues) == 0

    def test_mixed_valid_invalid_cavities(self):
        """Mix of valid and invalid cavities."""
        cavities = [
            CavityPosition(
                cavity_type=CavityType.PICKUP_NECK,
                center_x_mm=0.0,
                center_y_mm=155.0,  # Valid
            ),
            CavityPosition(
                cavity_type=CavityType.PICKUP_BRIDGE,
                center_x_mm=0.0,
                center_y_mm=30.0,  # Invalid (should be 20mm)
            ),
        ]
        result = validate_all_cavities(cavities, "les_paul")
        assert result.cavities_validated == 2
        assert result.cavities_passed == 1  # Only one passed
        assert len(result.issues) > 0


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestValidateLespaulCavities:
    """Test Les Paul convenience function (LP-GAP-02)."""

    def test_factory_spec_passes(self):
        """Factory spec values should pass."""
        result = validate_lespaul_cavities(
            pickup_neck_y_mm=155.0,
            pickup_bridge_y_mm=20.0,
            control_cavity_width_mm=64.0,
            control_cavity_length_mm=108.0,
            neck_pocket_width_mm=53.0,
            neck_pocket_length_mm=89.0,
        )
        assert result.valid is True
        assert result.instrument_model == "les_paul"
        assert result.cavities_validated == 4

    def test_slightly_off_warns(self):
        """Slightly off values should warn but may still be valid."""
        result = validate_lespaul_cavities(
            pickup_neck_y_mm=156.5,  # 1.5mm off (within 2mm tolerance)
            pickup_bridge_y_mm=21.0,  # 1mm off (within tolerance)
        )
        # Still valid because within tolerance
        assert result.valid is True

    def test_far_off_fails(self):
        """Far off values should fail."""
        result = validate_lespaul_cavities(
            pickup_neck_y_mm=170.0,  # 15mm off!
            pickup_bridge_y_mm=20.0,
        )
        assert result.valid is False
        assert len(result.issues) > 0


class TestValidateStratCavities:
    """Test Stratocaster convenience function."""

    def test_factory_spec_passes(self):
        """Factory spec values should pass."""
        result = validate_strat_cavities(
            pickup_neck_y_mm=161.9,    # 6.375"
            pickup_middle_y_mm=92.1,   # 3.625"
            pickup_bridge_y_mm=41.3,   # 1.625"
        )
        assert result.valid is True
        assert result.cavities_validated == 3

    def test_24_fret_note_added(self):
        """24-fret config should add note about neck pickup."""
        result = validate_strat_cavities(
            pickup_neck_y_mm=161.9,
            pickup_middle_y_mm=92.1,
            pickup_bridge_y_mm=41.3,
            fret_count=24,
        )
        assert any("24-fret" in note for note in result.notes)


class TestValidateExplorerCavities:
    """Test Explorer convenience function (EX-GAP-04)."""

    def test_factory_spec_passes(self):
        """Factory spec values should pass."""
        result = validate_explorer_cavities(
            pickup_neck_y_mm=140.0,
            pickup_bridge_y_mm=38.1,
        )
        assert result.valid is True
        assert result.cavities_validated == 2

    def test_off_spec_fails(self):
        """Off-spec values should fail."""
        result = validate_explorer_cavities(
            pickup_neck_y_mm=160.0,  # Way off
            pickup_bridge_y_mm=38.1,
        )
        assert result.valid is False


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestHelperFunctions:
    """Test helper/utility functions."""

    def test_get_factory_reference(self):
        """Should retrieve factory reference for model/cavity."""
        ref = get_factory_reference("les_paul", CavityType.PICKUP_NECK)
        assert ref is not None
        assert ref.nominal_center_y_mm == 155.0

    def test_get_factory_reference_unknown_model(self):
        """Unknown model should return None."""
        ref = get_factory_reference("unknown", CavityType.PICKUP_NECK)
        assert ref is None

    def test_get_factory_reference_unknown_cavity(self):
        """Unknown cavity type should return None."""
        ref = get_factory_reference("les_paul", CavityType.WIRING_CHANNEL)
        assert ref is None

    def test_list_supported_models(self):
        """Should list all supported models."""
        models = list_supported_models()
        assert "les_paul" in models
        assert "stratocaster" in models
        assert "explorer" in models

    def test_list_cavity_types_for_model(self):
        """Should list cavity types for a model."""
        types = list_cavity_types_for_model("les_paul")
        assert "pickup_neck" in types
        assert "pickup_bridge" in types
        assert "control_cavity" in types

    def test_list_cavity_types_unknown_model(self):
        """Unknown model should return empty list."""
        types = list_cavity_types_for_model("unknown")
        assert types == []


# =============================================================================
# Serialization Tests
# =============================================================================

class TestSerialization:
    """Test JSON serialization of results."""

    def test_validation_result_to_dict(self):
        """ValidationResult should serialize to dict."""
        result = validate_lespaul_cavities(155.0, 20.0)
        d = result.to_dict()

        assert "instrument_model" in d
        assert "valid" in d
        assert "summary" in d
        assert "issues" in d
        assert "warnings" in d
        assert "notes" in d

        assert d["instrument_model"] == "les_paul"
        assert isinstance(d["summary"]["cavities_validated"], int)

    def test_validation_issue_to_dict(self):
        """ValidationIssue should serialize to dict."""
        issue = ValidationIssue(
            cavity_type=CavityType.PICKUP_NECK,
            severity=ValidationSeverity.WARNING,
            field="center_y_mm",
            message="Test message",
            actual_value=158.0,
            expected_value=155.0,
            deviation_mm=3.0,
            tolerance_mm=2.0,
        )
        d = issue.to_dict()

        assert d["cavity_type"] == "pickup_neck"
        assert d["severity"] == "warning"
        assert d["deviation_mm"] == 3.0


# =============================================================================
# Model Name Normalization Tests
# =============================================================================

class TestModelNormalization:
    """Test model name normalization."""

    def test_les_paul_variants(self):
        """Various Les Paul spellings should work."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=155.0,
        )

        for model in ["les_paul", "Les Paul", "les-paul", "gibson_les_paul"]:
            passed, _ = validate_cavity(cavity, model)
            assert passed is True, f"Failed for model: {model}"

    def test_strat_variants(self):
        """Various Strat spellings should work."""
        cavity = CavityPosition(
            cavity_type=CavityType.PICKUP_NECK,
            center_x_mm=0.0,
            center_y_mm=161.9,
        )

        for model in ["stratocaster", "strat", "Strat", "fender_strat"]:
            passed, _ = validate_cavity(cavity, model)
            assert passed is True, f"Failed for model: {model}"
