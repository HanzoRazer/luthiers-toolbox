"""
Tests for Runtime Governance Router Checkpoints (7Q)

CAM Dev Order 7Q: Integration tests for live router governance checkpoints.

Test coverage:
  - Checkpoint response helpers
  - Pathway construction utilities
  - Authorization router checkpoint integration
  - RED blocking behavior (HTTP 409)
  - YELLOW/GREEN pass-through behavior
  - Invariant enforcement
  - Checkpoint summary in responses

Note: export_lifecycle_router has a pre-existing broken import
(cam_lifecycle_audit_ledger missing) and cannot be tested until fixed.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.cam.runtime_checkpoint_response import (
    RuntimeCheckpointSummary,
    RuntimeCheckpointBlockedResponse,
    build_export_route_pathway,
    build_translator_dispatch_pathway,
    build_serializer_boundary_pathway,
    build_postprocessor_boundary_pathway,
    build_geometry_consumption_pathway,
    evaluate_runtime_pathway_checkpoint,
    to_checkpoint_summary,
    is_red_checkpoint,
    is_yellow_checkpoint,
    is_green_checkpoint,
    raise_on_red_checkpoint,
    maybe_add_checkpoint_to_dict,
)
from app.cam.runtime_governance_enforcement import (
    clear_enforcement_index,
    clear_enforcement_report_index,
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
# Pathway Construction Tests
# -----------------------------------------------------------------------------

class TestPathwayConstruction:
    """Tests for pathway construction helpers."""

    def test_build_export_route_pathway(self):
        """Test export_route pathway construction."""
        pathway = build_export_route_pathway("/api/cam/export/lifecycle/validate")
        assert pathway == "export_route:/api/cam/export/lifecycle/validate"

    def test_build_translator_dispatch_pathway(self):
        """Test translator_dispatch pathway construction."""
        pathway = build_translator_dispatch_pathway("dxf_r12")
        assert pathway == "translator_dispatch:dxf_r12"

    def test_build_serializer_boundary_pathway(self):
        """Test serializer_boundary pathway construction."""
        pathway = build_serializer_boundary_pathway("dxf_compat")
        assert pathway == "serializer_boundary:dxf_compat"

    def test_build_postprocessor_boundary_pathway(self):
        """Test postprocessor_boundary pathway construction."""
        pathway = build_postprocessor_boundary_pathway("grbl_placeholder")
        assert pathway == "postprocessor_boundary:grbl_placeholder"

    def test_build_geometry_consumption_pathway(self):
        """Test geometry_consumption pathway construction."""
        pathway = build_geometry_consumption_pathway("body_grid_to_export")
        assert pathway == "geometry_consumption:body_grid_to_export"


# -----------------------------------------------------------------------------
# Checkpoint Evaluation Tests
# -----------------------------------------------------------------------------

class TestCheckpointEvaluation:
    """Tests for checkpoint evaluation helper."""

    def test_evaluate_runtime_pathway_checkpoint_returns_evaluation(self):
        """Test evaluate_runtime_pathway_checkpoint returns evaluation."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:dxf_r12",
            translator_id="dxf_r12",
        )
        assert evaluation is not None
        assert evaluation.runtime_pathway == "translator_dispatch:dxf_r12"
        assert evaluation.translator_id == "dxf_r12"

    def test_evaluate_with_export_route(self):
        """Test evaluation with export route parameter."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="export_route:/api/test",
            export_route="/api/test",
        )
        assert evaluation.export_route == "/api/test"

    def test_evaluate_without_linkage_produces_yellow(self):
        """Test evaluation without governance linkage produces YELLOW."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        # Without linkage refs, should be YELLOW
        assert evaluation.severity == "yellow"
        assert len(evaluation.warnings) > 0

    def test_evaluate_serializer_boundary_produces_red(self):
        """Test serializer_boundary pathway produces RED."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="serializer_boundary:dxf_compat",
        )
        assert evaluation.severity == "red"
        assert evaluation.serializer_path_detected is True

    def test_evaluation_invariants_enforced(self):
        """Test 7P/7Q invariants are enforced."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        assert evaluation.execution_authorized is False
        assert evaluation.machine_output_allowed is False
        assert evaluation.serializer_execution_allowed is False


# -----------------------------------------------------------------------------
# Summary Conversion Tests
# -----------------------------------------------------------------------------

class TestSummaryConversion:
    """Tests for checkpoint summary conversion."""

    def test_to_checkpoint_summary_creates_summary(self):
        """Test to_checkpoint_summary creates RuntimeCheckpointSummary."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        summary = to_checkpoint_summary(evaluation)

        assert isinstance(summary, RuntimeCheckpointSummary)
        assert summary.checkpoint_gate == evaluation.severity
        assert summary.pathway == evaluation.runtime_pathway

    def test_summary_preserves_blocking_issues(self):
        """Test summary preserves blocking issues."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="serializer_boundary:test",
        )
        summary = to_checkpoint_summary(evaluation)

        assert summary.checkpoint_gate == "red"
        assert len(summary.blocking_issues) > 0

    def test_summary_preserves_warnings(self):
        """Test summary preserves warnings."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        summary = to_checkpoint_summary(evaluation)

        assert len(summary.warnings) > 0  # Missing linkage warning

    def test_summary_has_enforcement_hash(self):
        """Test summary includes enforcement hash."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        summary = to_checkpoint_summary(evaluation)

        assert summary.enforcement_hash != ""

    def test_summary_invariants(self):
        """Test summary enforces invariants."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        summary = to_checkpoint_summary(evaluation)

        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False


# -----------------------------------------------------------------------------
# Severity Check Tests
# -----------------------------------------------------------------------------

class TestSeverityChecks:
    """Tests for severity check helpers."""

    def test_is_red_checkpoint_detects_red(self):
        """Test is_red_checkpoint detects RED."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="serializer_boundary:test",
        )
        assert is_red_checkpoint(evaluation) is True
        assert is_yellow_checkpoint(evaluation) is False
        assert is_green_checkpoint(evaluation) is False

    def test_is_yellow_checkpoint_detects_yellow(self):
        """Test is_yellow_checkpoint detects YELLOW."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        assert is_yellow_checkpoint(evaluation) is True
        assert is_red_checkpoint(evaluation) is False
        assert is_green_checkpoint(evaluation) is False


# -----------------------------------------------------------------------------
# RED Blocking Tests
# -----------------------------------------------------------------------------

class TestRedBlocking:
    """Tests for RED checkpoint blocking."""

    def test_raise_on_red_checkpoint_raises_409(self):
        """Test raise_on_red_checkpoint raises HTTPException 409."""
        from fastapi import HTTPException

        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="serializer_boundary:test",
        )

        with pytest.raises(HTTPException) as exc_info:
            raise_on_red_checkpoint(evaluation, "/api/test")

        assert exc_info.value.status_code == 409
        assert "runtime_governance_checkpoint_blocked" in str(exc_info.value.detail)

    def test_raise_on_red_checkpoint_no_raise_for_yellow(self):
        """Test raise_on_red_checkpoint does not raise for YELLOW."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        # Should not raise
        raise_on_red_checkpoint(evaluation, "/api/test")

    def test_blocked_response_includes_summary(self):
        """Test blocked response includes checkpoint summary."""
        from fastapi import HTTPException

        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="machine_output_boundary:grbl",
        )

        with pytest.raises(HTTPException) as exc_info:
            raise_on_red_checkpoint(evaluation, "/api/test")

        detail = exc_info.value.detail
        assert "checkpoint_summary" in detail
        assert detail["checkpoint_summary"]["checkpoint_gate"] == "red"

    def test_blocked_response_includes_route(self):
        """Test blocked response includes route path."""
        from fastapi import HTTPException

        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="serializer_boundary:test",
        )

        with pytest.raises(HTTPException) as exc_info:
            raise_on_red_checkpoint(evaluation, "/api/cam/test/route")

        detail = exc_info.value.detail
        assert detail["route"] == "/api/cam/test/route"


# -----------------------------------------------------------------------------
# Response Enrichment Tests
# -----------------------------------------------------------------------------

class TestResponseEnrichment:
    """Tests for response enrichment helpers."""

    def test_maybe_add_checkpoint_to_dict(self):
        """Test maybe_add_checkpoint_to_dict adds summary."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        response_dict = {"key": "value"}

        result = maybe_add_checkpoint_to_dict(response_dict, evaluation)

        assert "runtime_checkpoint_summary" in result
        assert result["runtime_checkpoint_summary"]["pathway"] == "translator_dispatch:test"

    def test_maybe_add_checkpoint_custom_field_name(self):
        """Test maybe_add_checkpoint_to_dict with custom field name."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        response_dict = {}

        result = maybe_add_checkpoint_to_dict(
            response_dict, evaluation, field_name="governance_checkpoint"
        )

        assert "governance_checkpoint" in result


# -----------------------------------------------------------------------------
# Authorization Router Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.allow_missing_request_id
class TestAuthorizationRouterCheckpoints:
    """Integration tests for authorization router with 7Q checkpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with authorization router."""
        from fastapi import FastAPI
        from app.routers.cam.translation_artifact_authorization_router import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def valid_artifact_payload(self):
        """Create a valid artifact payload for testing."""
        return {
            "artifact": {
                "translator_id": "dxf_r12",
                "translator_category": "translator",
                "output_class": "dxf",
                "artifact_state": "validation_only",
                "source_export_object_id": "export-test-123",
                "source_export_object_hash": "abc123def456",
                "execution_supported": False,
                "executable_payload_present": False,
                "machine_output_present": False,
            }
        }

    def test_authorization_endpoint_includes_checkpoint_summary(
        self, client, valid_artifact_payload
    ):
        """Test authorization endpoint includes runtime_checkpoint_summary."""
        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=valid_artifact_payload,
        )

        # Should succeed (YELLOW due to missing linkage, not RED)
        assert response.status_code == 200
        data = response.json()
        assert "runtime_checkpoint_summary" in data
        assert data["runtime_checkpoint_summary"]["pathway"].startswith("translator_dispatch:")

    def test_authorization_checkpoint_is_yellow_without_linkage(
        self, client, valid_artifact_payload
    ):
        """Test authorization checkpoint is YELLOW without governance linkage."""
        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=valid_artifact_payload,
        )

        assert response.status_code == 200
        data = response.json()
        # Without linkage, should be YELLOW
        assert data["runtime_checkpoint_summary"]["checkpoint_gate"] == "yellow"

    def test_authorization_response_preserves_base_evaluation(
        self, client, valid_artifact_payload
    ):
        """Test authorization response preserves base evaluation fields."""
        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=valid_artifact_payload,
        )

        assert response.status_code == 200
        data = response.json()
        # Base evaluation fields should be present
        assert "gate" in data
        assert "authorized_for_execution" in data
        assert data["authorized_for_execution"] is False

    def test_authorization_invariants_enforced(self, client, valid_artifact_payload):
        """Test 7Q invariants are enforced in response."""
        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=valid_artifact_payload,
        )

        assert response.status_code == 200
        data = response.json()
        # Check invariants in checkpoint summary
        assert data["runtime_checkpoint_summary"]["execution_authorized"] is False
        assert data["runtime_checkpoint_summary"]["machine_output_allowed"] is False


# -----------------------------------------------------------------------------
# Blocked Response Model Tests
# -----------------------------------------------------------------------------

class TestBlockedResponseModel:
    """Tests for RuntimeCheckpointBlockedResponse model."""

    def test_blocked_response_model_creation(self):
        """Test RuntimeCheckpointBlockedResponse can be created."""
        summary = RuntimeCheckpointSummary(
            checkpoint_gate="red",
            checkpoint_passed=False,
            blocking_issues=["test issue"],
            warnings=[],
            enforcement_hash="abc123",
            pathway="serializer_boundary:test",
        )

        blocked = RuntimeCheckpointBlockedResponse(
            message="Test blocked",
            checkpoint_summary=summary,
            route="/api/test",
        )

        assert blocked.error == "runtime_governance_checkpoint_blocked"
        assert blocked.checkpoint_summary.checkpoint_gate == "red"

    def test_blocked_response_model_serialization(self):
        """Test RuntimeCheckpointBlockedResponse serializes correctly."""
        summary = RuntimeCheckpointSummary(
            checkpoint_gate="red",
            checkpoint_passed=False,
            blocking_issues=["blocking issue"],
            warnings=[],
            enforcement_hash="def456",
            pathway="machine_output_boundary:grbl",
        )

        blocked = RuntimeCheckpointBlockedResponse(
            message="Blocked due to governance",
            checkpoint_summary=summary,
            route="/api/cam/blocked",
        )

        data = blocked.model_dump()
        assert data["error"] == "runtime_governance_checkpoint_blocked"
        assert data["checkpoint_summary"]["checkpoint_gate"] == "red"
        assert data["route"] == "/api/cam/blocked"


# -----------------------------------------------------------------------------
# Edge Case Tests
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case tests for 7Q checkpoint integration."""

    def test_empty_translator_id_pathway(self):
        """Test pathway construction with empty translator ID."""
        pathway = build_translator_dispatch_pathway("")
        assert pathway == "translator_dispatch:"

    def test_checkpoint_with_request_context(self):
        """Test checkpoint evaluation with request context."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
            request_context={"source": "test", "version": "7Q"},
        )
        assert evaluation.metadata.get("request_context", {}).get("source") == "test"

    def test_multiple_checkpoints_independent(self):
        """Test multiple checkpoint evaluations are independent."""
        eval1 = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:first",
        )
        eval2 = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="serializer_boundary:second",
        )

        assert eval1.evaluation_id != eval2.evaluation_id
        assert eval1.severity == "yellow"  # Missing linkage
        assert eval2.severity == "red"  # Serializer boundary


# -----------------------------------------------------------------------------
# No Execution Tests
# -----------------------------------------------------------------------------

class TestNoExecution:
    """Tests confirming no execution occurs."""

    def test_checkpoint_does_not_invoke_serializers(self):
        """Test checkpoint evaluation does not invoke serializers."""
        # Even for serializer_boundary pathway, no actual serializer runs
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="serializer_boundary:dxf_compat",
        )
        # It should be RED (blocked), but no serializer was invoked
        assert evaluation.serializer_path_detected is True
        assert evaluation.serializer_execution_allowed is False

    def test_checkpoint_does_not_produce_machine_output(self):
        """Test checkpoint evaluation does not produce machine output."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="machine_output_boundary:grbl",
        )
        assert evaluation.authority_leak_detected is True
        assert evaluation.machine_output_allowed is False

    def test_checkpoint_does_not_authorize_execution(self):
        """Test checkpoint evaluation does not authorize execution."""
        evaluation = evaluate_runtime_pathway_checkpoint(
            runtime_pathway="translator_dispatch:test",
        )
        assert evaluation.execution_authorized is False
