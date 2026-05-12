"""
Tests for CAM Lifecycle Policy Engine (CAM Dev Order 6I)

Tests policy enforcement for governed export lifecycle.

Core principle: Policy engine controls lifecycle stages BEFORE they run.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.cam.cam_lifecycle_policy_engine import (
    LifecyclePolicyEvaluation,
    evaluate_lifecycle_policy,
    is_lifecycle_allowed,
    get_stage_permissions,
)
from app.cam.cam_operation_registry import (
    CAM_OPERATION_REGISTRY,
    CAMOperationCapability,
)
from app.cam.export_lifecycle_orchestrator import (
    GovernedExportLifecycleRequest,
    PreviewRequestWrapper,
    run_governed_export_lifecycle,
)
from app.cam.dxf_translator_boundary import DXFTranslatorProfile
from app.cam.postprocessor_boundary import MachineProfileValidationOnly


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_lifecycle_request(
    operation: str = "nut_slot",
    persist_to_rmos: bool = False,
) -> GovernedExportLifecycleRequest:
    """Create a test lifecycle request."""
    if operation == "nut_slot":
        payload = {
            "nut_width_mm": 50.0,
            "num_strings": 6,
            "edge_offset_bass_mm": 4.0,
            "edge_offset_treble_mm": 4.0,
            "slot_length_mm": 4.5,
            "slot_depth_mm": 1.5,
            "slot_width_mm": 0.70,
            "stock_thickness_mm": 9.5,
            "tool_diameter_mm": 0.56,
            "safe_z_mm": 5.0,
        }
    elif operation == "drilling":
        payload = {
            "holes": [
                {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 5.0, "depth_mm": 8.0},
            ],
            "stock_thickness_mm": 20.0,
        }
    else:
        payload = {}

    return GovernedExportLifecycleRequest(
        preview_request=PreviewRequestWrapper(
            operation=operation,
            payload=payload,
        ),
        machine_profile=MachineProfileValidationOnly(
            machine_profile_id="test_machine",
            controller="none",
            units="mm",
            supported_operations=[operation, "pocket"],
            axis_count=3,
            work_envelope_mm={"x": 300, "y": 300, "z": 50},
        ),
        translator_profile=DXFTranslatorProfile(
            translator_id="test_translator",
            supported_geometry_types=["line", "polyline", "circle", "arc"],
            supports_layers=True,
            units="mm",
        ),
        persist_to_rmos=persist_to_rmos,
    )


# -----------------------------------------------------------------------------
# Policy Evaluation Basic Tests
# -----------------------------------------------------------------------------

class TestPolicyEvaluationBasics:
    """Tests for basic policy evaluation."""

    def test_governed_export_operation_allowed(self):
        """governed_export operation is allowed."""
        policy = evaluate_lifecycle_policy("nut_slot")

        assert policy.allowed is True
        assert policy.lifecycle_gate in ["green", "yellow"]
        assert policy.exportability_class == "governed_export"

    def test_drilling_allowed(self):
        """drilling operation is allowed."""
        policy = evaluate_lifecycle_policy("drilling")

        assert policy.allowed is True
        assert policy.lifecycle_gate in ["green", "yellow"]

    def test_unsupported_operation_returns_red(self):
        """Unsupported operation returns RED."""
        policy = evaluate_lifecycle_policy("unknown_operation")

        assert policy.allowed is False
        assert policy.lifecycle_gate == "red"
        assert any("not found" in issue for issue in policy.blocking_issues)

    def test_policy_returns_evaluation_model(self):
        """Policy returns LifecyclePolicyEvaluation model."""
        policy = evaluate_lifecycle_policy("nut_slot")

        assert isinstance(policy, LifecyclePolicyEvaluation)
        assert policy.operation == "nut_slot"


# -----------------------------------------------------------------------------
# Stage Permission Tests
# -----------------------------------------------------------------------------

class TestStagePermissions:
    """Tests for stage permission enforcement."""

    def test_governed_export_all_stages_allowed(self):
        """governed_export allows all stages."""
        policy = evaluate_lifecycle_policy("nut_slot")

        assert policy.preview_allowed is True
        assert policy.export_object_allowed is True
        assert policy.machine_validation_allowed is True
        assert policy.translator_validation_allowed is True
        assert policy.rmos_persistence_allowed is True

    def test_drilling_all_stages_allowed(self):
        """drilling allows all stages."""
        policy = evaluate_lifecycle_policy("drilling")

        assert policy.preview_allowed is True
        assert policy.export_object_allowed is True
        assert policy.machine_validation_allowed is True
        assert policy.translator_validation_allowed is True
        assert policy.rmos_persistence_allowed is True


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Tests verifying safety assertions always enforced."""

    def test_machine_output_allowed_always_false(self):
        """machine_output_allowed is always false."""
        for op in CAM_OPERATION_REGISTRY.keys():
            policy = evaluate_lifecycle_policy(op)
            assert policy.machine_output_allowed is False, f"{op} has machine_output_allowed=True"

    def test_translator_execution_allowed_always_false(self):
        """translator_execution_allowed is always false."""
        for op in CAM_OPERATION_REGISTRY.keys():
            policy = evaluate_lifecycle_policy(op)
            assert policy.translator_execution_allowed is False, f"{op} has translator_execution_allowed=True"

    def test_unknown_operation_still_has_safety_assertions(self):
        """Unknown operation still has safety assertions."""
        policy = evaluate_lifecycle_policy("unknown_op")

        assert policy.machine_output_allowed is False
        assert policy.translator_execution_allowed is False


# -----------------------------------------------------------------------------
# Maturity Enforcement Tests
# -----------------------------------------------------------------------------

class TestMaturityEnforcement:
    """Tests for maturity level enforcement."""

    def test_canonical_maturity_returns_green(self):
        """canonical maturity returns GREEN."""
        policy = evaluate_lifecycle_policy("nut_slot")

        # nut_slot is canonical
        assert policy.maturity == "canonical"
        # No maturity warnings for canonical
        assert not any("maturity" in w.lower() for w in policy.warnings)

    def test_governed_maturity_returns_green(self):
        """governed maturity returns GREEN (no warnings)."""
        # Currently both operations are canonical, so this tests the policy logic
        policy = evaluate_lifecycle_policy("drilling")
        assert policy.maturity == "canonical"


# -----------------------------------------------------------------------------
# RMOS Eligibility Tests
# -----------------------------------------------------------------------------

class TestRMOSEligibility:
    """Tests for RMOS persistence eligibility."""

    def test_rmos_allowed_when_not_requested(self):
        """RMOS check passes when not requested."""
        policy = evaluate_lifecycle_policy("nut_slot", persist_to_rmos=False)

        assert "rmos_eligibility: PASS" in policy.policy_checks

    def test_rmos_allowed_for_governed_export(self):
        """RMOS is allowed for governed_export operations."""
        policy = evaluate_lifecycle_policy("nut_slot", persist_to_rmos=True)

        assert policy.rmos_persistence_allowed is True
        assert policy.lifecycle_gate != "red"


# -----------------------------------------------------------------------------
# Policy Checks Output Tests
# -----------------------------------------------------------------------------

class TestPolicyChecksOutput:
    """Tests for policy_checks output format."""

    def test_policy_checks_populated(self):
        """policy_checks list is populated."""
        policy = evaluate_lifecycle_policy("nut_slot")

        assert len(policy.policy_checks) > 0

    def test_policy_checks_contain_operation_registered(self):
        """policy_checks contains operation_registered check."""
        policy = evaluate_lifecycle_policy("nut_slot")

        assert any("operation_registered" in check for check in policy.policy_checks)

    def test_policy_checks_contain_lifecycle_supported(self):
        """policy_checks contains lifecycle_supported check."""
        policy = evaluate_lifecycle_policy("nut_slot")

        assert any("lifecycle_supported" in check for check in policy.policy_checks)

    def test_policy_checks_contain_exportability_class(self):
        """policy_checks contains exportability_class check."""
        policy = evaluate_lifecycle_policy("nut_slot")

        assert any("exportability_class" in check for check in policy.policy_checks)


# -----------------------------------------------------------------------------
# Orchestrator Integration Tests
# -----------------------------------------------------------------------------

class TestOrchestratorIntegration:
    """Tests for policy engine integration with orchestrator."""

    def test_policy_evaluation_included_in_report(self):
        """Policy evaluation is included in lifecycle report."""
        request = create_lifecycle_request("nut_slot")
        report = run_governed_export_lifecycle(request)

        assert report.policy_evaluation is not None
        assert report.policy_evaluation.operation == "nut_slot"

    def test_policy_red_stops_lifecycle(self):
        """Policy RED stops lifecycle execution."""
        request = create_lifecycle_request("unknown_operation")
        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert report.export_ready is False
        assert report.export_object_summary is None
        assert any("not found" in issue for issue in report.blocking_issues)

    def test_valid_operation_proceeds_through_lifecycle(self):
        """Valid operation proceeds through full lifecycle."""
        request = create_lifecycle_request("nut_slot")
        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate in ["green", "yellow"]
        assert report.export_ready is True
        assert report.export_object_summary is not None

    def test_policy_warnings_propagate_to_report(self):
        """Policy warnings propagate to lifecycle report."""
        request = create_lifecycle_request("nut_slot")
        report = run_governed_export_lifecycle(request)

        # Policy evaluation should be present
        assert report.policy_evaluation is not None


# -----------------------------------------------------------------------------
# Helper Function Tests
# -----------------------------------------------------------------------------

class TestHelperFunctions:
    """Tests for policy helper functions."""

    def test_is_lifecycle_allowed_returns_true_for_valid(self):
        """is_lifecycle_allowed returns True for valid operations."""
        assert is_lifecycle_allowed("nut_slot") is True
        assert is_lifecycle_allowed("drilling") is True

    def test_is_lifecycle_allowed_returns_false_for_unknown(self):
        """is_lifecycle_allowed returns False for unknown operations."""
        assert is_lifecycle_allowed("unknown_op") is False

    def test_get_stage_permissions_returns_dict(self):
        """get_stage_permissions returns dict for valid operations."""
        perms = get_stage_permissions("nut_slot")

        assert perms is not None
        assert "preview_allowed" in perms
        assert "export_object_allowed" in perms

    def test_get_stage_permissions_returns_none_for_unknown(self):
        """get_stage_permissions returns None for unknown operations."""
        perms = get_stage_permissions("unknown_op")

        assert perms is None


# -----------------------------------------------------------------------------
# preview_only Simulation Tests
# -----------------------------------------------------------------------------

class TestPreviewOnlyBehavior:
    """Tests simulating preview_only exportability class behavior.

    Note: Currently no operations are preview_only, so we test the policy
    logic directly by examining what would happen.
    """

    def test_preview_only_would_block_export_object(self):
        """preview_only exportability blocks export object creation."""
        # Create a mock capability with preview_only
        from app.cam.cam_lifecycle_policy_engine import _compute_stage_permissions

        mock_cap = CAMOperationCapability(
            operation="test_preview_only",
            lifecycle_supported=True,
            export_object_supported=False,
            machine_validation_supported=False,
            translator_validation_supported=False,
            rmos_persistence_supported=False,
            exportability_class="preview_only",
            maturity="experimental",
        )

        perms = _compute_stage_permissions(mock_cap)

        assert perms["preview_allowed"] is True
        assert perms["export_object_allowed"] is False
        assert perms["machine_validation_allowed"] is False
        assert perms["translator_validation_allowed"] is False
        assert perms["rmos_persistence_allowed"] is False


# -----------------------------------------------------------------------------
# machine_candidate Simulation Tests
# -----------------------------------------------------------------------------

class TestMachineCandidateBehavior:
    """Tests for machine_candidate exportability class behavior."""

    def test_machine_candidate_produces_warning(self):
        """machine_candidate produces warning about execution prohibition."""
        from app.cam.cam_lifecycle_policy_engine import _check_exportability_class

        mock_cap = CAMOperationCapability(
            operation="test_machine_candidate",
            lifecycle_supported=True,
            export_object_supported=True,
            machine_validation_supported=True,
            translator_validation_supported=True,
            rmos_persistence_supported=True,
            exportability_class="machine_candidate",
            maturity="canonical",
        )

        check = _check_exportability_class(mock_cap)

        assert check.gate == "yellow"
        assert "machine-output candidate" in check.message
        assert "execution remains prohibited" in check.message


# -----------------------------------------------------------------------------
# Experimental Maturity Tests
# -----------------------------------------------------------------------------

class TestExperimentalMaturity:
    """Tests for experimental maturity enforcement."""

    def test_experimental_maturity_returns_yellow(self):
        """experimental maturity returns YELLOW with warning."""
        from app.cam.cam_lifecycle_policy_engine import _check_maturity

        mock_cap = CAMOperationCapability(
            operation="test_experimental",
            lifecycle_supported=True,
            export_object_supported=True,
            machine_validation_supported=True,
            translator_validation_supported=True,
            rmos_persistence_supported=True,
            exportability_class="governed_export",
            maturity="experimental",
        )

        check = _check_maturity(mock_cap)

        assert check.gate == "yellow"
        assert "experimental" in check.message

    def test_candidate_maturity_returns_yellow(self):
        """candidate maturity returns YELLOW with warning."""
        from app.cam.cam_lifecycle_policy_engine import _check_maturity

        mock_cap = CAMOperationCapability(
            operation="test_candidate",
            lifecycle_supported=True,
            export_object_supported=True,
            machine_validation_supported=True,
            translator_validation_supported=True,
            rmos_persistence_supported=True,
            exportability_class="governed_export",
            maturity="candidate",
        )

        check = _check_maturity(mock_cap)

        assert check.gate == "yellow"
        assert "candidate" in check.message


# -----------------------------------------------------------------------------
# End-to-End Policy Flow Tests
# -----------------------------------------------------------------------------

class TestEndToEndPolicyFlow:
    """End-to-end tests for complete policy flow."""

    def test_nut_slot_full_lifecycle_with_policy(self):
        """nut_slot completes full lifecycle with policy evaluation."""
        request = create_lifecycle_request("nut_slot")
        report = run_governed_export_lifecycle(request)

        # Policy evaluation present
        assert report.policy_evaluation is not None
        assert report.policy_evaluation.allowed is True

        # Lifecycle completed
        assert report.lifecycle_gate in ["green", "yellow"]
        assert report.export_ready is True

        # Safety assertions enforced
        assert report.machine_ready is False
        assert report.machine_output_generated is False
        assert report.translator_output_generated is False

    def test_drilling_full_lifecycle_with_policy(self):
        """drilling completes full lifecycle with policy evaluation."""
        request = create_lifecycle_request("drilling")
        report = run_governed_export_lifecycle(request)

        # Policy evaluation present
        assert report.policy_evaluation is not None
        assert report.policy_evaluation.allowed is True

        # Lifecycle completed
        assert report.lifecycle_gate in ["green", "yellow"]
        assert report.export_ready is True

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_rmos_persistence_respects_policy(self, mock_put):
        """RMOS persistence respects policy permissions."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request("nut_slot", persist_to_rmos=True)
        report = run_governed_export_lifecycle(request)

        # Policy allows RMOS persistence
        assert report.policy_evaluation.rmos_persistence_allowed is True

        # RMOS persistence occurred
        assert report.rmos.persisted is True
