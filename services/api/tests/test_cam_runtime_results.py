"""
CAM Runtime Result Contract Tests

Dev Order 58: Tests for normalized runtime result contracts.

Test cases:
1. all result models validate
2. observational_only always true
3. execution_ready always false
4. machine_operation_authorized always false
5. machine_output_generated always false
6. dispatcher composes normalized manifest
7. unsupported runtime still returns normalized results
8. runtime result IDs preserved
9. provenance preserved
10. diagnostics preserved
"""

import pytest
from pydantic import ValidationError

from app.cam.runtime.runtime_results import (
    RuntimeExportResult,
    RuntimeGeometryResolution,
    RuntimePlanResult,
    RuntimePreviewResult,
    RuntimeResultBase,
    RuntimeValidationResult,
    create_unsupported_export_result,
    create_unsupported_geometry_result,
    create_unsupported_plan_result,
    create_unsupported_preview_result,
    create_unsupported_validation_result,
)


class TestRuntimeResultBase:
    """Tests for RuntimeResultBase."""

    def test_result_id_auto_generated(self):
        """Result ID is auto-generated with rr_ prefix."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
        )
        assert result.result_id.startswith("rr_")
        assert len(result.result_id) == 15  # "rr_" + 12 hex chars

    def test_result_id_can_be_provided(self):
        """Result ID can be caller-provided."""
        result = RuntimeValidationResult(
            result_id="custom-id-123",
            status="available",
            validation_gate="green",
        )
        assert result.result_id == "custom-id-123"

    def test_schema_version_is_v1(self):
        """Schema version is runtime-result.v1."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
        )
        assert result.schema_version == "runtime-result.v1"

    def test_observational_only_always_true(self):
        """Test 2: observational_only is always true."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
        )
        assert result.observational_only is True

    def test_cannot_set_observational_only_false(self):
        """Cannot set observational_only to False."""
        with pytest.raises(ValidationError):
            RuntimeValidationResult(
                status="available",
                validation_gate="green",
                observational_only=False,
            )


class TestRuntimeValidationResult:
    """Tests for RuntimeValidationResult."""

    def test_validates_with_required_fields(self):
        """Test 1: validation result validates with required fields."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
        )
        assert result.validation_gate == "green"
        assert result.valid is True

    def test_valid_property_is_computed(self):
        """Valid property is computed from validation_gate."""
        green = RuntimeValidationResult(status="available", validation_gate="green")
        yellow = RuntimeValidationResult(status="available", validation_gate="yellow")
        red = RuntimeValidationResult(status="error", validation_gate="red")

        assert green.valid is True
        assert yellow.valid is True
        assert red.valid is False

    def test_execution_ready_always_false(self):
        """Test 3: execution_ready is always false."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
        )
        assert result.execution_ready is False

    def test_cannot_set_execution_ready_true(self):
        """Cannot set execution_ready to True."""
        with pytest.raises(ValidationError):
            RuntimeValidationResult(
                status="available",
                validation_gate="green",
                execution_ready=True,
            )

    def test_machine_operation_authorized_always_false(self):
        """Test 4: machine_operation_authorized is always false."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
        )
        assert result.machine_operation_authorized is False

    def test_cannot_set_machine_operation_authorized_true(self):
        """Cannot set machine_operation_authorized to True."""
        with pytest.raises(ValidationError):
            RuntimeValidationResult(
                status="available",
                validation_gate="green",
                machine_operation_authorized=True,
            )

    def test_preserves_warnings_and_errors(self):
        """Validation result preserves warnings and errors."""
        result = RuntimeValidationResult(
            status="error",
            validation_gate="red",
            warnings=["warning1", "warning2"],
            errors=["error1"],
        )
        assert result.warnings == ["warning1", "warning2"]
        assert result.errors == ["error1"]


class TestRuntimeGeometryResolution:
    """Tests for RuntimeGeometryResolution."""

    def test_validates_with_required_fields(self):
        """Test 1: geometry resolution validates with required fields."""
        result = RuntimeGeometryResolution(
            status="available",
            geometry_resolution_status="resolved",
        )
        assert result.geometry_resolution_status == "resolved"

    def test_geometry_queries_preserved(self):
        """Geometry queries are preserved."""
        result = RuntimeGeometryResolution(
            status="available",
            geometry_resolution_status="resolved",
            geometry_queries=["query1", "query2"],
        )
        assert result.geometry_queries == ["query1", "query2"]


class TestRuntimePlanResult:
    """Tests for RuntimePlanResult."""

    def test_validates_with_required_fields(self):
        """Test 1: plan result validates with required fields."""
        result = RuntimePlanResult(
            status="placeholder",
            planning_stage="placeholder",
        )
        assert result.planning_stage == "placeholder"

    def test_operation_count_default_zero(self):
        """Operation count defaults to zero."""
        result = RuntimePlanResult(
            status="placeholder",
            planning_stage="placeholder",
        )
        assert result.operation_count == 0


class TestRuntimePreviewResult:
    """Tests for RuntimePreviewResult."""

    def test_validates_with_required_fields(self):
        """Test 1: preview result validates with required fields."""
        result = RuntimePreviewResult(
            status="placeholder",
            preview_stage="placeholder",
        )
        assert result.preview_stage == "placeholder"

    def test_preview_artifacts_preserved(self):
        """Preview artifacts are preserved."""
        result = RuntimePreviewResult(
            status="available",
            preview_stage="preview_stub",
            preview_artifacts=["artifact1", "artifact2"],
        )
        assert result.preview_artifacts == ["artifact1", "artifact2"]


class TestRuntimeExportResult:
    """Tests for RuntimeExportResult."""

    def test_validates_with_required_fields(self):
        """Test 1: export result validates with required fields."""
        result = RuntimeExportResult(
            status="placeholder",
            export_stage="placeholder",
        )
        assert result.export_stage == "placeholder"

    def test_machine_output_generated_always_false(self):
        """Test 5: machine_output_generated is always false."""
        result = RuntimeExportResult(
            status="placeholder",
            export_stage="placeholder",
        )
        assert result.machine_output_generated is False

    def test_cannot_set_machine_output_generated_true(self):
        """Cannot set machine_output_generated to True."""
        with pytest.raises(ValidationError):
            RuntimeExportResult(
                status="placeholder",
                export_stage="placeholder",
                machine_output_generated=True,
            )

    def test_export_formats_preserved(self):
        """Export formats are preserved."""
        result = RuntimeExportResult(
            status="placeholder",
            export_stage="export_stub",
            export_formats=["dxf", "svg"],
        )
        assert result.export_formats == ["dxf", "svg"]


class TestUnsupportedResultFactories:
    """Tests for unsupported result factory functions."""

    def test_unsupported_validation_result(self):
        """Test 7: unsupported validation result is normalized."""
        result = create_unsupported_validation_result(
            reason="Operation not supported",
            provenance=["test:unsupported"],
        )
        assert result.status == "unsupported"
        assert result.validation_gate == "red"
        assert result.valid is False
        assert "Operation not supported" in result.diagnostics
        assert "test:unsupported" in result.provenance

    def test_unsupported_geometry_result(self):
        """Test 7: unsupported geometry result is normalized."""
        result = create_unsupported_geometry_result(
            reason="Geometry not available",
        )
        assert result.status == "unsupported"
        assert result.geometry_resolution_status == "unsupported"
        assert "Geometry not available" in result.diagnostics

    def test_unsupported_plan_result(self):
        """Test 7: unsupported plan result is normalized."""
        result = create_unsupported_plan_result(
            reason="Planning not available",
        )
        assert result.status == "unsupported"
        assert result.planning_stage == "unsupported"
        assert "Planning not available" in result.diagnostics

    def test_unsupported_preview_result(self):
        """Test 7: unsupported preview result is normalized."""
        result = create_unsupported_preview_result(
            reason="Preview not available",
        )
        assert result.status == "unsupported"
        assert result.preview_stage == "unsupported"
        assert "Preview not available" in result.diagnostics

    def test_unsupported_export_result(self):
        """Test 7: unsupported export result is normalized."""
        result = create_unsupported_export_result(
            reason="Export not available",
        )
        assert result.status == "unsupported"
        assert result.export_stage == "unsupported"
        assert result.machine_output_generated is False
        assert "Export not available" in result.diagnostics


class TestProvenanceAndDiagnostics:
    """Tests for provenance and diagnostics preservation."""

    def test_provenance_preserved(self):
        """Test 9: provenance is preserved."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
            provenance=["stage1:action", "stage2:action"],
        )
        assert result.provenance == ["stage1:action", "stage2:action"]

    def test_diagnostics_preserved(self):
        """Test 10: diagnostics are preserved."""
        result = RuntimeValidationResult(
            status="available",
            validation_gate="green",
            diagnostics=["diag1", "diag2"],
        )
        assert result.diagnostics == ["diag1", "diag2"]

    def test_result_id_preserved(self):
        """Test 8: result ID is preserved."""
        result = RuntimeValidationResult(
            result_id="preserved-id-456",
            status="available",
            validation_gate="green",
        )
        assert result.result_id == "preserved-id-456"
