"""
Tests for CAM Assist strategy package validator.

These tests verify that the validator correctly accepts valid packages
and rejects invalid packages according to the A2 schema contract.

A2 adds semantic contract enforcement:
- operation_intent with non_execution_declaration
- material_context
- safety_boundary with execution authority rejection
"""

import json
import pytest
from pathlib import Path

# Add scripts to path for import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_strategy_package import (
    validate_strategy_package,
    validate_file,
    load_json,
    ValidationResult,
    REQUIRED_TOP_LEVEL_FIELDS,
)


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
VALID_DIR = EXAMPLES_DIR / "valid"
INVALID_DIR = EXAMPLES_DIR / "invalid"


# --- Fixture: minimal valid package (A2) ---

@pytest.fixture
def minimal_valid_package() -> dict:
    """Return a minimal valid A2 strategy package."""
    return {
        "strategy_version": "1.2",
        "strategy_id": "test-package",
        "units": "inches",
        "coordinate_frame": {
            "origin": "nut_centerline",
            "x_axis": "along_neck",
            "y_axis": "across_fretboard",
        },
        "provenance": {
            "cam_assist_version": "0.3.0",
            "created_at": "2026-05-21T12:00:00Z",
        },
        "operation_intent": {
            "operation_type": "fret_slots",
            "target_feature": "fretboard",
            "cut_intent": "slot",
            "non_execution_declaration": True,
        },
        "material_context": {
            "material_class": "hardwood",
        },
        "safety_boundary": {
            "non_execution_declaration": True,
            "human_review_required": True,
        },
        "geometry": {
            "dxf_file": "geometry.dxf",
            "primary_layer": "FRET_SLOTS",
        },
        "operation": {
            "type": "slot_cut",
            "tool": {"tool_type": "slot_cutter"},
            "parameters": {"depth": 0.060},
        },
        "approval_state": "pending",
    }


# --- Tests: Valid packages ---

class TestValidPackages:
    """Tests for valid strategy packages."""

    def test_minimal_valid_package(self, minimal_valid_package):
        """Minimal valid package should pass validation."""
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_valid_example_file(self):
        """The valid example file should pass validation."""
        valid_file = VALID_DIR / "fret_slot_strategy.json"
        if valid_file.exists():
            result = validate_file(valid_file)
            assert result.valid is True, f"Errors: {result.errors}"

    def test_valid_with_optional_fields(self, minimal_valid_package):
        """Package with optional fields should pass."""
        minimal_valid_package["positions"] = [
            {"fret": 1, "distance_from_nut": 1.4312},
        ]
        minimal_valid_package["warnings"] = []
        minimal_valid_package["calculation_basis"] = {
            "formula": "test",
            "scale_length": 25.5,
        }
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is True

    def test_units_inches(self, minimal_valid_package):
        """Package with inches units should pass."""
        minimal_valid_package["units"] = "inches"
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is True

    def test_units_mm(self, minimal_valid_package):
        """Package with mm units should pass."""
        minimal_valid_package["units"] = "mm"
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is True

    def test_all_approval_states(self, minimal_valid_package):
        """All valid approval states should pass."""
        for state in ["pending", "in_review", "approved", "rejected"]:
            minimal_valid_package["approval_state"] = state
            result = validate_strategy_package(minimal_valid_package)
            assert result.valid is True, f"State '{state}' should be valid"

    def test_all_cut_intents(self, minimal_valid_package):
        """All valid cut intents should pass."""
        for intent in ["slot", "pocket", "profile", "drill", "contour", "channel"]:
            minimal_valid_package["operation_intent"]["cut_intent"] = intent
            result = validate_strategy_package(minimal_valid_package)
            assert result.valid is True, f"Cut intent '{intent}' should be valid"

    def test_all_material_classes(self, minimal_valid_package):
        """All valid material classes should pass."""
        for mat_class in ["softwood", "hardwood", "exotic", "figured",
                          "laminate", "composite", "unknown"]:
            minimal_valid_package["material_context"]["material_class"] = mat_class
            result = validate_strategy_package(minimal_valid_package)
            assert result.valid is True, f"Material class '{mat_class}' should be valid"


# --- Tests: Missing required fields ---

class TestMissingRequiredFields:
    """Tests for missing required top-level fields."""

    @pytest.mark.parametrize("field", REQUIRED_TOP_LEVEL_FIELDS)
    def test_missing_required_field(self, minimal_valid_package, field):
        """Missing any required field should fail."""
        del minimal_valid_package[field]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any(field in error for error in result.errors)

    def test_missing_units_example(self):
        """The missing_units example should fail."""
        invalid_file = INVALID_DIR / "missing_units.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("units" in error for error in result.errors)

    def test_missing_coordinate_frame_example(self):
        """The missing_coordinate_frame example should fail."""
        invalid_file = INVALID_DIR / "missing_coordinate_frame.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("coordinate_frame" in error for error in result.errors)

    def test_missing_provenance_example(self):
        """The missing_provenance example should fail."""
        invalid_file = INVALID_DIR / "missing_provenance.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("provenance" in error for error in result.errors)

    def test_missing_operation_intent_example(self):
        """The missing_operation_intent example should fail."""
        invalid_file = INVALID_DIR / "missing_operation_intent.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("operation_intent" in error for error in result.errors)

    def test_missing_material_context_example(self):
        """The missing_material_context example should fail."""
        invalid_file = INVALID_DIR / "missing_material_context.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("material_context" in error for error in result.errors)

    def test_missing_safety_boundary_example(self):
        """The missing_safety_boundary example should fail."""
        invalid_file = INVALID_DIR / "missing_safety_boundary.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("safety_boundary" in error for error in result.errors)


# --- Tests: Invalid field values ---

class TestInvalidFieldValues:
    """Tests for invalid field values."""

    def test_invalid_units(self, minimal_valid_package):
        """Invalid units value should fail."""
        minimal_valid_package["units"] = "feet"
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("units" in error.lower() for error in result.errors)

    def test_invalid_approval_state(self, minimal_valid_package):
        """Invalid approval_state should fail."""
        minimal_valid_package["approval_state"] = "unknown"
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("approval_state" in error for error in result.errors)

    def test_empty_strategy_id(self, minimal_valid_package):
        """Empty strategy_id should fail."""
        minimal_valid_package["strategy_id"] = ""
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_invalid_strategy_id_chars(self, minimal_valid_package):
        """strategy_id with invalid characters should fail."""
        minimal_valid_package["strategy_id"] = "test_package!"
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_invalid_cut_intent(self, minimal_valid_package):
        """Invalid cut_intent should fail."""
        minimal_valid_package["operation_intent"]["cut_intent"] = "invalid"
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("cut_intent" in error for error in result.errors)

    def test_invalid_material_class(self, minimal_valid_package):
        """Invalid material_class should fail."""
        minimal_valid_package["material_context"]["material_class"] = "plastic"
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("material_class" in error for error in result.errors)


# --- Tests: Execution authority rejection (A2 critical) ---

class TestExecutionAuthorityRejection:
    """Tests for execution authority rejection - critical A2 feature."""

    def test_operation_intent_non_execution_false(self, minimal_valid_package):
        """non_execution_declaration=false in operation_intent should fail."""
        minimal_valid_package["operation_intent"]["non_execution_declaration"] = False
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("EXECUTION AUTHORITY" in error for error in result.errors)

    def test_safety_boundary_non_execution_false(self, minimal_valid_package):
        """non_execution_declaration=false in safety_boundary should fail."""
        minimal_valid_package["safety_boundary"]["non_execution_declaration"] = False
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("EXECUTION AUTHORITY" in error for error in result.errors)

    def test_human_review_not_required(self, minimal_valid_package):
        """human_review_required=false should fail."""
        minimal_valid_package["safety_boundary"]["human_review_required"] = False
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("SAFETY VIOLATION" in error for error in result.errors)

    def test_execution_authority_claim_true(self, minimal_valid_package):
        """execution_authority_claim=true should fail."""
        minimal_valid_package["safety_boundary"]["execution_authority_claim"] = True
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("EXECUTION AUTHORITY" in error for error in result.errors)

    def test_execution_authority_claim_false_allowed(self, minimal_valid_package):
        """execution_authority_claim=false should pass."""
        minimal_valid_package["safety_boundary"]["execution_authority_claim"] = False
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is True

    def test_execution_authority_claim_absent_allowed(self, minimal_valid_package):
        """Absent execution_authority_claim should pass."""
        # It's not in minimal_valid_package by default
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is True

    def test_execution_authority_claim_example(self):
        """The execution_authority_claim example should fail."""
        invalid_file = INVALID_DIR / "execution_authority_claim.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("EXECUTION AUTHORITY" in error or "SAFETY VIOLATION" in error
                      for error in result.errors)


# --- Tests: Nested object validation ---

class TestNestedObjectValidation:
    """Tests for nested object field validation."""

    def test_missing_coordinate_frame_origin(self, minimal_valid_package):
        """Missing origin in coordinate_frame should fail."""
        del minimal_valid_package["coordinate_frame"]["origin"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False
        assert any("origin" in error for error in result.errors)

    def test_missing_coordinate_frame_x_axis(self, minimal_valid_package):
        """Missing x_axis in coordinate_frame should fail."""
        del minimal_valid_package["coordinate_frame"]["x_axis"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_coordinate_frame_y_axis(self, minimal_valid_package):
        """Missing y_axis in coordinate_frame should fail."""
        del minimal_valid_package["coordinate_frame"]["y_axis"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_provenance_cam_assist_version(self, minimal_valid_package):
        """Missing cam_assist_version in provenance should fail."""
        del minimal_valid_package["provenance"]["cam_assist_version"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_provenance_created_at(self, minimal_valid_package):
        """Missing created_at in provenance should fail."""
        del minimal_valid_package["provenance"]["created_at"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_operation_intent_operation_type(self, minimal_valid_package):
        """Missing operation_type in operation_intent should fail."""
        del minimal_valid_package["operation_intent"]["operation_type"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_operation_intent_target_feature(self, minimal_valid_package):
        """Missing target_feature in operation_intent should fail."""
        del minimal_valid_package["operation_intent"]["target_feature"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_operation_intent_cut_intent(self, minimal_valid_package):
        """Missing cut_intent in operation_intent should fail."""
        del minimal_valid_package["operation_intent"]["cut_intent"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_material_context_material_class(self, minimal_valid_package):
        """Missing material_class in material_context should fail."""
        del minimal_valid_package["material_context"]["material_class"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_geometry_dxf_file(self, minimal_valid_package):
        """Missing dxf_file in geometry should fail."""
        del minimal_valid_package["geometry"]["dxf_file"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_geometry_primary_layer(self, minimal_valid_package):
        """Missing primary_layer in geometry should fail."""
        del minimal_valid_package["geometry"]["primary_layer"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_operation_type(self, minimal_valid_package):
        """Missing type in operation should fail."""
        del minimal_valid_package["operation"]["type"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_operation_tool(self, minimal_valid_package):
        """Missing tool in operation should fail."""
        del minimal_valid_package["operation"]["tool"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False

    def test_missing_operation_parameters(self, minimal_valid_package):
        """Missing parameters in operation should fail."""
        del minimal_valid_package["operation"]["parameters"]
        result = validate_strategy_package(minimal_valid_package)
        assert result.valid is False


# --- Tests: JSON parsing ---

class TestJsonParsing:
    """Tests for JSON parsing errors."""

    def test_malformed_json(self):
        """Malformed JSON should fail with parse error."""
        invalid_file = INVALID_DIR / "malformed_json.json"
        if invalid_file.exists():
            result = validate_file(invalid_file)
            assert result.valid is False
            assert any("parse" in error.lower() or "json" in error.lower()
                      for error in result.errors)

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file should fail."""
        result = validate_file(tmp_path / "does_not_exist.json")
        assert result.valid is False
        assert any("not found" in error.lower() for error in result.errors)


# --- Tests: Warnings ---

class TestWarnings:
    """Tests for validation warnings."""

    def test_old_version_warning(self, minimal_valid_package):
        """Old strategy_version should produce warning."""
        minimal_valid_package["strategy_version"] = "1.1"
        result = validate_strategy_package(minimal_valid_package)
        # Still valid but with warning
        assert len(result.warnings) > 0
        assert any("version" in warning.lower() for warning in result.warnings)


# --- Tests: Non-execution guarantee ---

class TestNonExecution:
    """Tests verifying the validator does not execute anything."""

    def test_validator_returns_result_only(self, minimal_valid_package):
        """Validator should only return ValidationResult, not execute."""
        result = validate_strategy_package(minimal_valid_package)
        assert isinstance(result, ValidationResult)
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    def test_no_side_effects(self, minimal_valid_package, tmp_path):
        """Validation should not create any files or side effects."""
        marker_file = tmp_path / "marker.txt"

        # Validate
        validate_strategy_package(minimal_valid_package)

        # No files should be created
        assert not marker_file.exists()
        assert len(list(tmp_path.iterdir())) == 0
