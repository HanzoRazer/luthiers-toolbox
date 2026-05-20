"""
Tests for Topology Shell Validation (MRP-5I).

Sprint: MRP-5I
Status: PROTOTYPE

Tests the topology_validation package:
- Shell integrity validation
- Continuity checking
- Validation orchestrator
- Deterministic signatures
"""

import pytest
from datetime import datetime, timezone

from app.cam.topology_validation import (
    # Contracts
    ContinuityReport,
    ShellIntegrityReport,
    ValidationCategory,
    ValidationFinding,
    ValidationRequest,
    ValidationResult,
    ValidationSeverity,
    ValidationSignature,
    ValidationTier,
    # Validators
    TopologyValidator,
    validate_topology,
    validate_request,
    # Shell integrity
    ShellIntegrityValidator,
    validate_shell_integrity,
    validate_all_shells,
    # Continuity
    ContinuityChecker,
    check_continuity,
    check_all_continuity,
    # Exceptions
    ValidationError,
    ShellIntegrityError,
    ValidationRequestError,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_shell_descriptor():
    """Valid closed manifold shell descriptor."""
    return {
        "shell_id": "shell_test001",
        "shell_type": "flat_extrusion",
        "component_name": "body",
        "is_closed": True,
        "is_manifold": True,
        "surface_count": 6,
        "edge_count": 12,
        "vertex_count": 8,
        "continuity": [],
    }


@pytest.fixture
def open_shell_descriptor():
    """Shell descriptor with open edges."""
    return {
        "shell_id": "shell_open001",
        "shell_type": "flat_extrusion",
        "component_name": "body",
        "is_closed": False,
        "is_manifold": True,
        "surface_count": 5,
        "edge_count": 10,
        "vertex_count": 8,
    }


@pytest.fixture
def non_manifold_shell_descriptor():
    """Non-manifold shell descriptor."""
    return {
        "shell_id": "shell_nm001",
        "shell_type": "flat_extrusion",
        "component_name": "body",
        "is_closed": True,
        "is_manifold": False,
        "surface_count": 6,
        "edge_count": 12,
        "vertex_count": 8,
    }


@pytest.fixture
def degenerate_shell_descriptor():
    """Degenerate shell with no surfaces."""
    return {
        "shell_id": "shell_deg001",
        "shell_type": "flat_extrusion",
        "component_name": "body",
        "is_closed": False,
        "is_manifold": False,
        "surface_count": 0,
        "edge_count": 0,
        "vertex_count": 0,
    }


@pytest.fixture
def shell_with_continuity():
    """Shell descriptor with continuity metadata."""
    return {
        "shell_id": "shell_cont001",
        "shell_type": "flat_extrusion",
        "component_name": "body_outer",
        "is_closed": True,
        "is_manifold": True,
        "surface_count": 6,
        "edge_count": 12,
        "vertex_count": 8,
        "continuity": [
            {
                "junction_name": "rim_to_top",
                "target": "G0",
                "achieved": "G0",
                "validated": True,
                "gap_mm": 0.05,
            },
            {
                "junction_name": "rim_to_back",
                "target": "G1",
                "achieved": "G0",
                "validated": True,
                "angle_deviation_deg": 3.5,
            },
        ],
    }


# =============================================================================
# Shell Integrity Validator Tests
# =============================================================================


class TestShellIntegrityValidator:
    """Tests for ShellIntegrityValidator."""

    def test_valid_shell_passes(self, valid_shell_descriptor):
        """Valid closed manifold shell should pass validation."""
        report = validate_shell_integrity(valid_shell_descriptor)

        assert report.passed
        assert report.is_closed
        assert report.is_manifold
        assert len(report.findings) == 0

    def test_open_shell_fails_prototype(self, open_shell_descriptor):
        """Open shell should produce BLOCKING finding in PROTOTYPE tier."""
        report = validate_shell_integrity(
            open_shell_descriptor, tier=ValidationTier.PROTOTYPE
        )

        assert not report.passed
        assert not report.is_closed
        assert len(report.findings) >= 1

        closure_findings = [
            f for f in report.findings
            if f.category == ValidationCategory.SHELL_CLOSURE
        ]
        assert len(closure_findings) == 1
        assert closure_findings[0].severity == ValidationSeverity.BLOCKING

    def test_non_manifold_major_in_prototype(self, non_manifold_shell_descriptor):
        """Non-manifold shell should produce MAJOR finding in PROTOTYPE tier."""
        report = validate_shell_integrity(
            non_manifold_shell_descriptor, tier=ValidationTier.PROTOTYPE
        )

        assert not report.passed
        manifold_findings = [
            f for f in report.findings
            if f.category == ValidationCategory.SHELL_MANIFOLD
        ]
        assert len(manifold_findings) == 1
        assert manifold_findings[0].severity == ValidationSeverity.MAJOR

    def test_non_manifold_blocking_in_production(self, non_manifold_shell_descriptor):
        """Non-manifold shell should produce BLOCKING finding in PRODUCTION tier."""
        report = validate_shell_integrity(
            non_manifold_shell_descriptor, tier=ValidationTier.PRODUCTION
        )

        assert not report.passed
        manifold_findings = [
            f for f in report.findings
            if f.category == ValidationCategory.SHELL_MANIFOLD
        ]
        assert len(manifold_findings) == 1
        assert manifold_findings[0].severity == ValidationSeverity.BLOCKING

    def test_degenerate_shell_blocking(self, degenerate_shell_descriptor):
        """Degenerate shell with no surfaces should be BLOCKING."""
        report = validate_shell_integrity(degenerate_shell_descriptor)

        assert not report.passed
        structure_findings = [
            f for f in report.findings
            if f.category == ValidationCategory.TOPOLOGY_STRUCTURE
        ]
        assert len(structure_findings) >= 1
        assert any(f.severity == ValidationSeverity.BLOCKING for f in structure_findings)

    def test_validate_multiple_shells(self, valid_shell_descriptor, open_shell_descriptor):
        """validate_all_shells should process multiple shells."""
        shells = [valid_shell_descriptor, open_shell_descriptor]
        reports = validate_all_shells(shells)

        assert len(reports) == 2
        assert reports[0].passed  # Valid shell
        assert not reports[1].passed  # Open shell

    def test_shell_report_serialization(self, valid_shell_descriptor):
        """ShellIntegrityReport should serialize to dict."""
        report = validate_shell_integrity(valid_shell_descriptor)
        report_dict = report.to_dict()

        assert "shell_id" in report_dict
        assert "is_closed" in report_dict
        assert "is_manifold" in report_dict
        assert "passed" in report_dict
        assert report_dict["passed"] == True


# =============================================================================
# Continuity Checker Tests
# =============================================================================


class TestContinuityChecker:
    """Tests for ContinuityChecker."""

    def test_g0_met(self):
        """G0 target met with G0 achieved should pass."""
        metadata = {
            "junction_name": "test_junction",
            "achieved": "G0",
            "gap_mm": 0.05,
        }
        report = check_continuity("test_junction", "G0", metadata)

        assert report.met_target
        assert report.achieved_level == "G0"
        blocking_findings = [
            f for f in report.findings
            if f.severity == ValidationSeverity.BLOCKING
        ]
        assert len(blocking_findings) == 0

    def test_g1_exceeds_g0(self):
        """G1 achieved exceeds G0 target."""
        metadata = {"achieved": "G1", "gap_mm": 0.01}
        report = check_continuity("test_junction", "G0", metadata)

        assert report.met_target
        assert report.achieved_level == "G1"

    def test_g0_fails_g1_target(self):
        """G0 achieved fails G1 target."""
        metadata = {"achieved": "G0", "gap_mm": 0.05}
        report = check_continuity(
            "test_junction", "G1", metadata, tier=ValidationTier.PROTOTYPE
        )

        assert not report.met_target
        assert len(report.findings) >= 1
        assert report.findings[0].severity == ValidationSeverity.MAJOR

    def test_g1_fails_g1_production_is_blocking(self):
        """Unmet G1 target in PRODUCTION tier should be BLOCKING."""
        metadata = {"achieved": "G0"}
        report = check_continuity(
            "test_junction", "G1", metadata, tier=ValidationTier.PRODUCTION
        )

        assert not report.met_target
        blocking = [f for f in report.findings if f.severity == ValidationSeverity.BLOCKING]
        assert len(blocking) >= 1

    def test_no_achieved_fails(self):
        """No achieved continuity should fail target."""
        report = check_continuity("test_junction", "G0", None)

        assert not report.met_target
        assert report.achieved_level is None

    def test_check_multiple_junctions(self):
        """check_all_continuity should process multiple junctions."""
        targets = {"junction_a": "G0", "junction_b": "G1"}
        metadata = [
            {"junction_name": "junction_a", "achieved": "G0"},
            {"junction_name": "junction_b", "achieved": "G1"},
        ]

        reports = check_all_continuity(targets, metadata)

        assert len(reports) == 2
        assert reports[0].met_target
        assert reports[1].met_target

    def test_continuity_report_serialization(self):
        """ContinuityReport should serialize to dict."""
        metadata = {"achieved": "G0", "gap_mm": 0.05}
        report = check_continuity("test_junction", "G0", metadata)
        report_dict = report.to_dict()

        assert "junction_name" in report_dict
        assert "target_level" in report_dict
        assert "achieved_level" in report_dict
        assert "met_target" in report_dict


# =============================================================================
# Topology Validator (Orchestrator) Tests
# =============================================================================


class TestTopologyValidator:
    """Tests for TopologyValidator orchestrator."""

    def test_validate_valid_topology(self, valid_shell_descriptor):
        """Valid topology should pass validation."""
        topology_dict = {
            "request_id": "test_001",
            "tier": "PROTOTYPE",
            "shells": [valid_shell_descriptor],
        }

        result = validate_topology(topology_dict)

        assert result.passed
        assert result.blocking_count == 0
        assert len(result.shell_reports) == 1
        assert result.signature is not None

    def test_validate_fails_on_open_shell(self, open_shell_descriptor):
        """Topology with open shell should fail."""
        topology_dict = {
            "request_id": "test_002",
            "tier": "PROTOTYPE",
            "shells": [open_shell_descriptor],
        }

        result = validate_topology(topology_dict)

        assert not result.passed
        assert result.blocking_count >= 1

    def test_validate_with_continuity_targets(self, shell_with_continuity):
        """Validation should check continuity targets."""
        topology_dict = {
            "request_id": "test_003",
            "tier": "PROTOTYPE",
            "shells": [shell_with_continuity],
        }
        continuity_targets = {"rim_to_top": "G0", "rim_to_back": "G1"}

        result = validate_topology(
            topology_dict, continuity_targets=continuity_targets
        )

        assert len(result.continuity_reports) == 2
        rim_to_top = next(
            r for r in result.continuity_reports if r.junction_name == "rim_to_top"
        )
        assert rim_to_top.met_target

    def test_production_tier_stricter(self, non_manifold_shell_descriptor):
        """PRODUCTION tier should be stricter than PROTOTYPE."""
        topology_dict = {
            "request_id": "test_004",
            "tier": "PRODUCTION",
            "shells": [non_manifold_shell_descriptor],
        }

        result = validate_topology(topology_dict, tier=ValidationTier.PRODUCTION)

        assert not result.passed
        assert result.blocking_count >= 1

    def test_validation_request_object(self, valid_shell_descriptor):
        """validate_request should accept ValidationRequest."""
        request = ValidationRequest(
            request_id="test_005",
            tier=ValidationTier.PROTOTYPE,
            shell_descriptors=[valid_shell_descriptor],
        )

        result = validate_request(request)

        assert result.passed
        assert result.request_id == "test_005"

    def test_invalid_request_raises(self):
        """Invalid request should raise ValidationRequestError."""
        request = ValidationRequest(
            request_id="",  # Invalid: empty
            tier=ValidationTier.PROTOTYPE,
            shell_descriptors=[],  # Invalid: no shells
        )

        with pytest.raises(ValidationRequestError):
            validate_request(request)

    def test_result_serialization(self, valid_shell_descriptor):
        """ValidationResult should serialize to dict."""
        topology_dict = {
            "request_id": "test_006",
            "shells": [valid_shell_descriptor],
        }

        result = validate_topology(topology_dict)
        result_dict = result.to_dict()

        assert "request_id" in result_dict
        assert "passed" in result_dict
        assert "blocking_count" in result_dict
        assert "shell_reports" in result_dict
        assert "signature" in result_dict


# =============================================================================
# Validation Signature Tests
# =============================================================================


class TestValidationSignature:
    """Tests for deterministic validation signatures."""

    def test_signature_computed(self, valid_shell_descriptor):
        """Validation should produce a signature."""
        topology_dict = {
            "request_id": "test_sig_001",
            "shells": [valid_shell_descriptor],
        }

        result = validate_topology(topology_dict)

        assert result.signature is not None
        assert result.signature.input_hash is not None
        assert result.signature.validation_hash is not None
        assert len(result.signature.input_hash) == 16
        assert len(result.signature.validation_hash) == 16

    def test_same_input_same_signature(self, valid_shell_descriptor):
        """Same input should produce same input_hash."""
        topology_dict = {
            "request_id": "test_sig_002",
            "shells": [valid_shell_descriptor],
        }

        result1 = validate_topology(topology_dict)
        result2 = validate_topology(topology_dict)

        assert result1.signature.input_hash == result2.signature.input_hash
        assert result1.signature.validation_hash == result2.signature.validation_hash

    def test_different_input_different_signature(
        self, valid_shell_descriptor, open_shell_descriptor
    ):
        """Different input should produce different input_hash."""
        topology1 = {
            "request_id": "test_sig_003a",
            "shells": [valid_shell_descriptor],
        }
        topology2 = {
            "request_id": "test_sig_003b",
            "shells": [open_shell_descriptor],
        }

        result1 = validate_topology(topology1)
        result2 = validate_topology(topology2)

        assert result1.signature.input_hash != result2.signature.input_hash

    def test_signature_serialization(self, valid_shell_descriptor):
        """ValidationSignature should serialize to dict."""
        topology_dict = {
            "request_id": "test_sig_004",
            "shells": [valid_shell_descriptor],
        }

        result = validate_topology(topology_dict)
        sig_dict = result.signature.to_dict()

        assert "input_hash" in sig_dict
        assert "validation_hash" in sig_dict
        assert "tier" in sig_dict
        assert "timestamp_iso" in sig_dict
        assert "version" in sig_dict


# =============================================================================
# Contracts Tests
# =============================================================================


class TestContracts:
    """Tests for contract dataclasses."""

    def test_validation_finding_creation(self):
        """ValidationFinding should be creatable with all fields."""
        finding = ValidationFinding(
            category=ValidationCategory.SHELL_CLOSURE,
            severity=ValidationSeverity.BLOCKING,
            message="Test finding",
            location="shell_001",
            details={"test_key": "test_value"},
        )

        assert finding.category == ValidationCategory.SHELL_CLOSURE
        assert finding.severity == ValidationSeverity.BLOCKING
        assert finding.message == "Test finding"

    def test_validation_result_counts(self):
        """ValidationResult should count findings by severity."""
        result = ValidationResult(
            request_id="test_counts",
            passed=False,
            tier=ValidationTier.PROTOTYPE,
        )

        result.add_finding(
            ValidationFinding(
                category=ValidationCategory.SHELL_CLOSURE,
                severity=ValidationSeverity.BLOCKING,
                message="Blocking issue",
            )
        )
        result.add_finding(
            ValidationFinding(
                category=ValidationCategory.CONTINUITY,
                severity=ValidationSeverity.MAJOR,
                message="Major issue",
            )
        )
        result.add_finding(
            ValidationFinding(
                category=ValidationCategory.CONTINUITY,
                severity=ValidationSeverity.MAJOR,
                message="Another major issue",
            )
        )

        assert result.blocking_count == 1
        assert result.major_count == 2
        assert result.has_blocking_issues

    def test_validation_request_validation(self):
        """ValidationRequest.validate() should catch errors."""
        request = ValidationRequest(
            request_id="",
            tier=ValidationTier.PROTOTYPE,
        )

        is_valid, errors = request.validate()

        assert not is_valid
        assert "request_id is required" in errors

    def test_shell_integrity_report_passed_property(self):
        """ShellIntegrityReport.passed should reflect closure and manifold."""
        report_good = ShellIntegrityReport(
            shell_id="test",
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        report_open = ShellIntegrityReport(
            shell_id="test",
            component_name="body",
            is_closed=False,
            is_manifold=True,
        )

        assert report_good.passed
        assert not report_open.passed


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests with topology_builder contracts."""

    def test_validate_topology_builder_output(self, valid_shell_descriptor):
        """Should validate output matching topology_builder format."""
        topology_dict = {
            "request_id": "integration_001",
            "tier": "PROTOTYPE",
            "shells": [
                {
                    "shell_id": "shell_abc123",
                    "shell_type": "flat_extrusion",
                    "component_name": "body",
                    "is_closed": True,
                    "is_manifold": True,
                    "bounding_box": [[0, 0, 0], [350, 450, 3]],
                    "surface_count": 6,
                    "edge_count": 12,
                    "vertex_count": 8,
                    "continuity": [],
                }
            ],
            "is_valid": True,
            "shell_count": 1,
            "warnings": [],
            "metadata": {"construction_method": "flat_extrusion"},
        }

        result = validate_topology(topology_dict)

        assert result.passed
        assert len(result.shell_reports) == 1
        assert result.shell_reports[0].component_name == "body"

    def test_validate_hollow_body_with_continuity(self):
        """Should validate hollow body topology with rim continuity."""
        topology_dict = {
            "request_id": "integration_002",
            "tier": "PROTOTYPE",
            "shells": [
                {
                    "shell_id": "shell_outer",
                    "shell_type": "flat_extrusion",
                    "component_name": "body_outer",
                    "is_closed": True,
                    "is_manifold": True,
                    "surface_count": 6,
                    "edge_count": 12,
                    "vertex_count": 8,
                    "continuity": [
                        {
                            "junction_name": "rim_to_top",
                            "target": "G0",
                            "achieved": "G0",
                            "validated": True,
                        },
                        {
                            "junction_name": "rim_to_back",
                            "target": "G0",
                            "achieved": "G0",
                            "validated": True,
                        },
                    ],
                }
            ],
        }
        continuity_targets = {"rim_to_top": "G0", "rim_to_back": "G0"}

        result = validate_topology(topology_dict, continuity_targets=continuity_targets)

        assert result.passed
        assert len(result.continuity_reports) == 2
        assert all(r.met_target for r in result.continuity_reports)
