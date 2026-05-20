"""
Tests for Runtime Governance Enforcement (7P)

CAM Dev Order 7P: Runtime governance enforcement checkpoints and evaluation.

Test coverage:
  - Pathway parsing and classification
  - Governance linkage validation
  - Checkpoint evaluation
  - Severity classification
  - Invariant enforcement
  - CI report generation
  - Deterministic hash stability
  - RED/YELLOW/GREEN conditions
  - Router endpoints

Minimum: 40 tests
"""

import pytest
from fastapi.testclient import TestClient

from app.cam.runtime_governance_enforcement import (
    CANONICAL_PATHWAY_TYPES,
    ENFORCEMENT_EVALUATION_INDEX,
    ENFORCEMENT_REPORT_INDEX,
    EXECUTION_IMPLYING_PREFIXES,
    EnforcementCheckpoint,
    EnforcementCheckpointReport,
    GovernanceLinkage,
    ParsedPathway,
    RuntimeEnforcementRequest,
    RuntimeGovernanceEnforcementEvaluation,
    clear_enforcement_index,
    clear_enforcement_report_index,
    get_enforcement_evaluation,
    get_enforcement_evaluations_by_severity,
    list_enforcement_evaluations,
    lookup_governance_linkage,
    parse_runtime_pathway,
    register_enforcement_evaluation,
)
from app.cam.runtime_enforcement_policy import (
    PROHIBITED_RUNTIME_ACTIONS,
    RED_CONDITIONS,
    YELLOW_CONDITIONS,
    evaluate_consumption_discipline,
    evaluate_ledger_lineage,
    evaluate_pathway_classification,
    evaluate_quarantine_enforcement,
    evaluate_runtime_enforcement,
    generate_enforcement_ci_report,
    get_enforcement_policy,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear indexes before each test."""
    clear_enforcement_index()
    clear_enforcement_report_index()
    yield
    clear_enforcement_index()
    clear_enforcement_report_index()


# -----------------------------------------------------------------------------
# Pathway Parsing Tests
# -----------------------------------------------------------------------------

class TestPathwayParsing:
    """Tests for parse_runtime_pathway function."""

    def test_parse_translator_dispatch_pathway(self):
        """Test parsing translator_dispatch pathway."""
        result = parse_runtime_pathway("translator_dispatch:dxf_r12")
        assert result.parse_valid is True
        assert result.pathway_type == "translator_dispatch"
        assert result.pathway_target == "dxf_r12"
        assert result.is_canonical_type is True
        assert result.implies_execution is False

    def test_parse_export_route_pathway(self):
        """Test parsing export_route pathway."""
        result = parse_runtime_pathway("export_route:/api/cam/export/lifecycle/validate")
        assert result.parse_valid is True
        assert result.pathway_type == "export_route"
        assert result.pathway_target == "/api/cam/export/lifecycle/validate"
        assert result.is_canonical_type is True

    def test_parse_serializer_boundary_pathway(self):
        """Test parsing serializer_boundary pathway."""
        result = parse_runtime_pathway("serializer_boundary:dxf_compat")
        assert result.parse_valid is True
        assert result.pathway_type == "serializer_boundary"
        assert result.pathway_target == "dxf_compat"
        assert result.is_canonical_type is True
        assert result.implies_execution is True

    def test_parse_machine_output_boundary_pathway(self):
        """Test parsing machine_output_boundary pathway."""
        result = parse_runtime_pathway("machine_output_boundary:grbl")
        assert result.parse_valid is True
        assert result.pathway_type == "machine_output_boundary"
        assert result.pathway_target == "grbl"
        assert result.is_canonical_type is True
        assert result.implies_execution is True

    def test_parse_geometry_consumption_pathway(self):
        """Test parsing geometry_consumption pathway."""
        result = parse_runtime_pathway("geometry_consumption:body_grid_to_export")
        assert result.parse_valid is True
        assert result.pathway_type == "geometry_consumption"
        assert result.pathway_target == "body_grid_to_export"

    def test_parse_postprocessor_boundary_pathway(self):
        """Test parsing postprocessor_boundary pathway."""
        result = parse_runtime_pathway("postprocessor_boundary:gcode_grbl_placeholder")
        assert result.parse_valid is True
        assert result.pathway_type == "postprocessor_boundary"
        assert result.pathway_target == "gcode_grbl_placeholder"

    def test_parse_runtime_dispatch_pathway(self):
        """Test parsing runtime_dispatch pathway."""
        result = parse_runtime_pathway("runtime_dispatch:nut_slot")
        assert result.parse_valid is True
        assert result.pathway_type == "runtime_dispatch"
        assert result.pathway_target == "nut_slot"
        assert result.implies_execution is True

    def test_parse_unknown_pathway_type(self):
        """Test parsing unknown pathway type."""
        result = parse_runtime_pathway("unknown_type:some_target")
        assert result.parse_valid is True
        assert result.pathway_type == "unknown"
        assert result.pathway_target == "some_target"
        assert result.is_canonical_type is False

    def test_parse_unknown_pathway_with_execution_prefix(self):
        """Test unknown pathway with execution-implying prefix."""
        result = parse_runtime_pathway("execute_something:target")
        assert result.parse_valid is True
        assert result.pathway_type == "unknown"
        assert result.implies_execution is True

    def test_parse_empty_pathway(self):
        """Test parsing empty pathway string."""
        result = parse_runtime_pathway("")
        assert result.parse_valid is False
        assert result.pathway_type == "unknown"
        assert "Empty" in result.parse_error

    def test_parse_pathway_without_separator(self):
        """Test parsing pathway without colon separator."""
        result = parse_runtime_pathway("no_separator_here")
        assert result.parse_valid is False
        assert result.pathway_type == "unknown"
        assert "Missing ':'" in result.parse_error

    def test_parse_pathway_preserves_raw(self):
        """Test that raw pathway is preserved."""
        raw = "translator_dispatch:dxf_r12"
        result = parse_runtime_pathway(raw)
        assert result.raw_pathway == raw

    def test_all_canonical_pathway_types_recognized(self):
        """Test all canonical pathway types are recognized."""
        for pathway_type in CANONICAL_PATHWAY_TYPES:
            result = parse_runtime_pathway(f"{pathway_type}:target")
            assert result.pathway_type == pathway_type
            assert result.is_canonical_type is True


# -----------------------------------------------------------------------------
# Governance Linkage Tests
# -----------------------------------------------------------------------------

class TestGovernanceLinkage:
    """Tests for governance linkage creation and lookup."""

    def test_create_empty_linkage(self):
        """Test creating linkage with no references."""
        linkage = GovernanceLinkage()
        assert linkage.quarantine_id is None
        assert linkage.consumer_id is None
        assert linkage.ledger_entry_id is None
        assert linkage.quarantine_found is False
        assert linkage.consumer_found is False
        assert linkage.ledger_entry_found is False

    def test_create_linkage_with_quarantine_ref(self):
        """Test creating linkage with quarantine reference."""
        linkage = GovernanceLinkage(quarantine_id="quarantine-abc123")
        assert linkage.quarantine_id == "quarantine-abc123"

    def test_create_linkage_with_all_refs(self):
        """Test creating linkage with all references."""
        linkage = GovernanceLinkage(
            quarantine_id="quarantine-abc",
            consumer_id="consumer-def",
            ledger_entry_id="ledger-ghi",
            translator_id="dxf_r12",
            export_route="/api/export/dxf",
        )
        assert linkage.quarantine_id == "quarantine-abc"
        assert linkage.consumer_id == "consumer-def"
        assert linkage.ledger_entry_id == "ledger-ghi"
        assert linkage.translator_id == "dxf_r12"
        assert linkage.export_route == "/api/export/dxf"

    def test_lookup_linkage_preserves_ids(self):
        """Test lookup preserves original IDs."""
        linkage = GovernanceLinkage(
            quarantine_id="quarantine-test",
            consumer_id="consumer-test",
        )
        result = lookup_governance_linkage(linkage)
        assert result.quarantine_id == "quarantine-test"
        assert result.consumer_id == "consumer-test"


# -----------------------------------------------------------------------------
# Checkpoint Evaluation Tests
# -----------------------------------------------------------------------------

class TestCheckpointEvaluation:
    """Tests for individual checkpoint evaluations."""

    def test_pathway_classification_canonical_type_green(self):
        """Test canonical pathway type produces GREEN."""
        parsed = parse_runtime_pathway("translator_dispatch:dxf_r12")
        cp, blocking, warns = evaluate_pathway_classification(parsed)
        assert cp.severity == "green"
        assert cp.checkpoint_passed is True
        assert len(blocking) == 0
        assert len(warns) == 0

    def test_pathway_classification_serializer_boundary_red(self):
        """Test serializer_boundary produces RED."""
        parsed = parse_runtime_pathway("serializer_boundary:dxf_compat")
        cp, blocking, warns = evaluate_pathway_classification(parsed)
        assert cp.severity == "red"
        assert cp.checkpoint_passed is False
        assert cp.blocking is True
        assert len(blocking) > 0

    def test_pathway_classification_machine_output_red(self):
        """Test machine_output_boundary produces RED."""
        parsed = parse_runtime_pathway("machine_output_boundary:grbl")
        cp, blocking, warns = evaluate_pathway_classification(parsed)
        assert cp.severity == "red"
        assert cp.checkpoint_passed is False
        assert len(blocking) > 0

    def test_pathway_classification_unknown_no_execution_yellow(self):
        """Test unknown type without execution produces YELLOW."""
        parsed = parse_runtime_pathway("custom_type:target")
        cp, blocking, warns = evaluate_pathway_classification(parsed)
        assert cp.severity == "yellow"
        assert cp.checkpoint_passed is True
        assert len(warns) > 0

    def test_pathway_classification_unknown_with_execution_red(self):
        """Test unknown type with execution implication produces RED."""
        parsed = parse_runtime_pathway("execute_custom:target")
        cp, blocking, warns = evaluate_pathway_classification(parsed)
        assert cp.severity == "red"
        assert cp.checkpoint_passed is False
        assert len(blocking) > 0

    def test_quarantine_enforcement_missing_reference_yellow(self):
        """Test missing quarantine reference produces YELLOW."""
        linkage = GovernanceLinkage()
        cp, blocking, warns = evaluate_quarantine_enforcement(linkage)
        assert cp.severity == "yellow"
        assert cp.checkpoint_passed is True
        assert len(warns) > 0

    def test_quarantine_enforcement_not_found_red(self):
        """Test quarantine ID not found produces RED."""
        linkage = GovernanceLinkage(quarantine_id="nonexistent-id")
        linkage = lookup_governance_linkage(linkage)
        cp, blocking, warns = evaluate_quarantine_enforcement(linkage)
        assert cp.severity == "red"
        assert cp.checkpoint_passed is False
        assert len(blocking) > 0

    def test_consumption_discipline_missing_reference_yellow(self):
        """Test missing consumer reference produces YELLOW."""
        linkage = GovernanceLinkage()
        cp, blocking, warns = evaluate_consumption_discipline(linkage)
        assert cp.severity == "yellow"
        assert cp.checkpoint_passed is True

    def test_consumption_discipline_not_found_red(self):
        """Test consumer ID not found produces RED."""
        linkage = GovernanceLinkage(consumer_id="nonexistent-consumer")
        linkage = lookup_governance_linkage(linkage)
        cp, blocking, warns = evaluate_consumption_discipline(linkage)
        assert cp.severity == "red"
        assert cp.checkpoint_passed is False

    def test_ledger_lineage_missing_reference_yellow(self):
        """Test missing ledger reference produces YELLOW."""
        linkage = GovernanceLinkage()
        cp, blocking, warns = evaluate_ledger_lineage(linkage)
        assert cp.severity == "yellow"
        assert cp.checkpoint_passed is True

    def test_ledger_lineage_not_found_red(self):
        """Test ledger entry ID not found produces RED."""
        linkage = GovernanceLinkage(ledger_entry_id="nonexistent-ledger")
        linkage = lookup_governance_linkage(linkage)
        cp, blocking, warns = evaluate_ledger_lineage(linkage)
        assert cp.severity == "red"
        assert cp.checkpoint_passed is False


# -----------------------------------------------------------------------------
# Full Enforcement Evaluation Tests
# -----------------------------------------------------------------------------

class TestEnforcementEvaluation:
    """Tests for full enforcement evaluation."""

    def test_evaluate_canonical_pathway_no_linkage(self):
        """Test evaluating canonical pathway without governance linkage."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:dxf_r12",
        )
        result = evaluate_runtime_enforcement(request)

        assert result.parsed_pathway.pathway_type == "translator_dispatch"
        assert result.severity == "yellow"  # Missing linkage = YELLOW
        assert result.governance_checkpoint_passed is True
        assert result.runtime_quarantine_respected is True
        assert result.serializer_path_detected is False

    def test_evaluate_serializer_boundary_red(self):
        """Test evaluating serializer boundary produces RED."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="serializer_boundary:dxf_compat",
        )
        result = evaluate_runtime_enforcement(request)

        assert result.severity == "red"
        assert result.serializer_path_detected is True
        assert result.runtime_quarantine_respected is False
        assert len(result.blocking_issues) > 0

    def test_evaluate_machine_output_boundary_red(self):
        """Test evaluating machine output boundary produces RED."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="machine_output_boundary:grbl",
        )
        result = evaluate_runtime_enforcement(request)

        assert result.severity == "red"
        assert result.authority_leak_detected is True
        assert result.runtime_quarantine_respected is False

    def test_evaluation_registers_in_index(self):
        """Test evaluation is registered in index."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:test",
        )
        result = evaluate_runtime_enforcement(request)

        retrieved = get_enforcement_evaluation(result.evaluation_id)
        assert retrieved is not None
        assert retrieved.evaluation_id == result.evaluation_id

    def test_evaluation_produces_deterministic_hash(self):
        """Test evaluation produces deterministic hash."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:dxf_r12",
        )
        result = evaluate_runtime_enforcement(request)

        assert result.deterministic_enforcement_hash != ""
        assert len(result.deterministic_enforcement_hash) == 64  # SHA256


# -----------------------------------------------------------------------------
# Invariant Enforcement Tests
# -----------------------------------------------------------------------------

class TestInvariantEnforcement:
    """Tests for 7P invariant enforcement."""

    def test_invariant_execution_authorized_false(self):
        """Test execution_authorized cannot be True."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:test",
        )
        result = evaluate_runtime_enforcement(request)
        assert result.execution_authorized is False

    def test_invariant_machine_output_allowed_false(self):
        """Test machine_output_allowed cannot be True."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:test",
        )
        result = evaluate_runtime_enforcement(request)
        assert result.machine_output_allowed is False

    def test_invariant_serializer_execution_allowed_false(self):
        """Test serializer_execution_allowed cannot be True."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:test",
        )
        result = evaluate_runtime_enforcement(request)
        assert result.serializer_execution_allowed is False

    def test_invariant_runtime_self_authorized_false(self):
        """Test runtime_self_authorized cannot be True."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:test",
        )
        result = evaluate_runtime_enforcement(request)
        assert result.runtime_self_authorized is False

    def test_invariant_violation_raises_error(self):
        """Test invariant violation raises ValueError."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            RuntimeGovernanceEnforcementEvaluation(
                runtime_pathway="test",
                parsed_pathway=parse_runtime_pathway("test:target"),
                execution_authorized=True,
            )

    def test_machine_output_invariant_violation_raises_error(self):
        """Test machine_output invariant violation raises ValueError."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            RuntimeGovernanceEnforcementEvaluation(
                runtime_pathway="test",
                parsed_pathway=parse_runtime_pathway("test:target"),
                machine_output_allowed=True,
            )


# -----------------------------------------------------------------------------
# CI Report Tests
# -----------------------------------------------------------------------------

class TestCIReport:
    """Tests for CI report generation."""

    def test_generate_empty_report(self):
        """Test generating report with no evaluations."""
        report = generate_enforcement_ci_report()
        assert report.evaluations_count == 0
        assert report.ci_status == "pass"

    def test_generate_report_with_green_evaluations(self):
        """Test report with GREEN evaluations."""
        # Create a green evaluation (canonical path, no linkage = yellow actually)
        request = RuntimeEnforcementRequest(
            runtime_pathway="export_route:/api/test",
        )
        evaluate_runtime_enforcement(request)

        report = generate_enforcement_ci_report()
        assert report.evaluations_count == 1
        # Without linkage, it's YELLOW
        assert report.ci_status == "warn"

    def test_generate_report_with_red_evaluation(self):
        """Test report with RED evaluation produces fail."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="serializer_boundary:test",
        )
        evaluate_runtime_enforcement(request)

        report = generate_enforcement_ci_report()
        assert report.ci_status == "fail"
        assert report.red_count > 0
        assert report.serializer_paths_detected > 0

    def test_report_aggregates_blocking_issues(self):
        """Test report aggregates blocking issues."""
        # Create multiple red evaluations
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="serializer_boundary:a")
        )
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="machine_output_boundary:b")
        )

        report = generate_enforcement_ci_report()
        assert len(report.all_blocking_issues) > 0

    def test_report_has_deterministic_hash(self):
        """Test report produces deterministic hash."""
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="translator_dispatch:test")
        )
        report = generate_enforcement_ci_report()
        assert report.deterministic_report_hash != ""
        assert len(report.deterministic_report_hash) == 64


# -----------------------------------------------------------------------------
# Severity Classification Tests
# -----------------------------------------------------------------------------

class TestSeverityClassification:
    """Tests for severity classification."""

    def test_get_evaluations_by_severity_red(self):
        """Test filtering by RED severity."""
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="serializer_boundary:test")
        )
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="translator_dispatch:test")
        )

        red_evals = get_enforcement_evaluations_by_severity("red")
        assert len(red_evals) == 1
        assert red_evals[0].severity == "red"

    def test_get_evaluations_by_severity_yellow(self):
        """Test filtering by YELLOW severity."""
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="translator_dispatch:test")
        )

        yellow_evals = get_enforcement_evaluations_by_severity("yellow")
        assert len(yellow_evals) == 1
        assert yellow_evals[0].severity == "yellow"

    def test_list_all_evaluations(self):
        """Test listing all evaluations."""
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="serializer_boundary:test")
        )
        evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="translator_dispatch:test")
        )

        all_evals = list_enforcement_evaluations()
        assert len(all_evals) == 2


# -----------------------------------------------------------------------------
# Policy Tests
# -----------------------------------------------------------------------------

class TestPolicy:
    """Tests for enforcement policy."""

    def test_get_policy_returns_structure(self):
        """Test get_enforcement_policy returns expected structure."""
        policy = get_enforcement_policy()
        assert "dev_order" in policy
        assert policy["dev_order"] == "7P"
        assert "configurable" in policy
        assert policy["configurable"] is False

    def test_policy_contains_prohibited_actions(self):
        """Test policy contains prohibited actions."""
        policy = get_enforcement_policy()
        assert "prohibited_runtime_actions" in policy
        assert len(policy["prohibited_runtime_actions"]) > 0

    def test_policy_contains_red_conditions(self):
        """Test policy contains RED conditions."""
        policy = get_enforcement_policy()
        assert "red_conditions" in policy
        assert len(policy["red_conditions"]) > 0

    def test_policy_contains_yellow_conditions(self):
        """Test policy contains YELLOW conditions."""
        policy = get_enforcement_policy()
        assert "yellow_conditions" in policy
        assert len(policy["yellow_conditions"]) > 0

    def test_policy_contains_invariants(self):
        """Test policy contains invariants."""
        policy = get_enforcement_policy()
        assert "invariants" in policy
        assert policy["invariants"]["execution_authorized"] is False
        assert policy["invariants"]["machine_output_allowed"] is False

    def test_policy_contains_guardrail(self):
        """Test policy contains guardrail statement."""
        policy = get_enforcement_policy()
        assert "guardrail" in policy
        assert "does not intercept live traffic" in policy["guardrail"]


# -----------------------------------------------------------------------------
# Hash Stability Tests
# -----------------------------------------------------------------------------

class TestHashStability:
    """Tests for deterministic hash stability."""

    def test_same_input_same_hash(self):
        """Test same input produces same hash."""
        request1 = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:dxf_r12",
            translator_id="test-translator",
        )
        request2 = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:dxf_r12",
            translator_id="test-translator",
        )

        result1 = evaluate_runtime_enforcement(request1)
        clear_enforcement_index()
        result2 = evaluate_runtime_enforcement(request2)

        assert result1.deterministic_enforcement_hash == result2.deterministic_enforcement_hash

    def test_different_pathway_different_hash(self):
        """Test different pathway produces different hash."""
        result1 = evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="translator_dispatch:a")
        )
        result2 = evaluate_runtime_enforcement(
            RuntimeEnforcementRequest(runtime_pathway="translator_dispatch:b")
        )

        assert result1.deterministic_enforcement_hash != result2.deterministic_enforcement_hash


# -----------------------------------------------------------------------------
# Router Endpoint Tests
# -----------------------------------------------------------------------------

@pytest.mark.allow_missing_request_id
class TestRouterEndpoints:
    """Tests for router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with minimal app containing 7P router."""
        from fastapi import FastAPI
        from app.routers.cam.runtime_governance_enforcement_router import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_evaluate_endpoint(self, client):
        """Test POST /evaluate endpoint."""
        response = client.post(
            "/api/cam/runtime-enforcement/evaluate",
            json={"runtime_pathway": "translator_dispatch:dxf_r12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "evaluation_id" in data
        assert data["runtime_pathway"] == "translator_dispatch:dxf_r12"

    def test_policy_endpoint(self, client):
        """Test GET /policy endpoint."""
        response = client.get("/api/cam/runtime-enforcement/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["dev_order"] == "7P"

    def test_ci_endpoint(self, client):
        """Test GET /ci endpoint."""
        response = client.get("/api/cam/runtime-enforcement/ci")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("pass", "warn", "fail")

    def test_checkpoints_endpoint(self, client):
        """Test GET /checkpoints endpoint."""
        # First create an evaluation
        client.post(
            "/api/cam/runtime-enforcement/evaluate",
            json={"runtime_pathway": "translator_dispatch:test"},
        )

        response = client.get("/api/cam/runtime-enforcement/checkpoints")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_violations_endpoint(self, client):
        """Test GET /violations endpoint."""
        response = client.get("/api/cam/runtime-enforcement/violations")
        assert response.status_code == 200
        data = response.json()
        assert "total_violations" in data

    def test_checkpoint_by_id_not_found(self, client):
        """Test GET /checkpoints/{id} returns 404 for unknown ID."""
        response = client.get("/api/cam/runtime-enforcement/checkpoints/nonexistent")
        assert response.status_code == 404


# -----------------------------------------------------------------------------
# Edge Case Tests
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_pathway_with_multiple_colons(self):
        """Test pathway with multiple colons in target."""
        result = parse_runtime_pathway("export_route:/api/v2:3000/test")
        assert result.parse_valid is True
        assert result.pathway_type == "export_route"
        assert result.pathway_target == "/api/v2:3000/test"

    def test_pathway_with_whitespace(self):
        """Test pathway with whitespace is handled."""
        result = parse_runtime_pathway("  translator_dispatch : dxf_r12  ")
        assert result.parse_valid is True
        assert result.pathway_type == "translator_dispatch"
        assert result.pathway_target == "dxf_r12"

    def test_evaluation_with_all_linkage_missing_produces_yellow(self):
        """Test evaluation with no linkage refs produces YELLOW (not GREEN)."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="geometry_consumption:body_grid",
        )
        result = evaluate_runtime_enforcement(request)
        # Should be YELLOW due to incomplete governance linkage
        assert result.severity == "yellow"
        assert len(result.warnings) > 0

    def test_multiple_checkpoints_evaluated(self):
        """Test all 5 checkpoints are evaluated."""
        request = RuntimeEnforcementRequest(
            runtime_pathway="translator_dispatch:test",
        )
        result = evaluate_runtime_enforcement(request)
        assert len(result.checkpoints) == 5
        checkpoint_types = {cp.checkpoint_type for cp in result.checkpoints}
        assert "pathway_classification" in checkpoint_types
        assert "quarantine_enforcement" in checkpoint_types
        assert "consumption_discipline" in checkpoint_types
        assert "ledger_lineage" in checkpoint_types
        assert "invariant_verification" in checkpoint_types
