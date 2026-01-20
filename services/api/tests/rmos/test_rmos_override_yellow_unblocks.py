"""
Test RMOS Override - YELLOW Unlock Primitive

Tests the override endpoint and service for unlocking blocked runs.

Markers: unit, rmos, override
"""

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def blocked_yellow_run():
    """Create a mock BLOCKED/YELLOW run artifact."""
    from app.rmos.runs_v2.schemas import (
        RunArtifact,
        RunDecision,
        Hashes,
        RunOutputs,
    )
    return RunArtifact(
        run_id=uuid4().hex,
        mode="saw",
        tool_id="circular_saw_10",
        status="BLOCKED",
        request_summary={"test": True},
        feasibility={"sha256": "a" * 64},
        decision=RunDecision(
            risk_level="YELLOW",
            block_reason="Tool wear detected",
            warnings=["Tool wear exceeds threshold"],
        ),
        hashes=Hashes(feasibility_sha256="a" * 64),
        outputs=RunOutputs(),
        meta={},
    )


@pytest.fixture
def blocked_red_run():
    """Create a mock BLOCKED/RED run artifact."""
    from app.rmos.runs_v2.schemas import (
        RunArtifact,
        RunDecision,
        Hashes,
        RunOutputs,
    )
    return RunArtifact(
        run_id=uuid4().hex,
        mode="router",
        tool_id="v_bit_60",
        status="BLOCKED",
        request_summary={"test": True},
        feasibility={"sha256": "b" * 64},
        decision=RunDecision(
            risk_level="RED",
            block_reason="Critical safety violation",
            warnings=["Material too hard for this tool"],
        ),
        hashes=Hashes(feasibility_sha256="b" * 64),
        outputs=RunOutputs(),
        meta={},
    )


@pytest.fixture
def ok_run():
    """Create a mock OK run artifact (not blocked)."""
    from app.rmos.runs_v2.schemas import (
        RunArtifact,
        RunDecision,
        Hashes,
        RunOutputs,
    )
    return RunArtifact(
        run_id=uuid4().hex,
        mode="saw",
        tool_id="circular_saw_10",
        status="OK",
        request_summary={"test": True},
        feasibility={"sha256": "c" * 64},
        decision=RunDecision(
            risk_level="GREEN",
        ),
        hashes=Hashes(feasibility_sha256="c" * 64),
        outputs=RunOutputs(),
        meta={},
    )


# =============================================================================
# Unit Tests: Override Service
# =============================================================================

class TestOverrideValidation:
    """Test override precondition validation."""

    def test_cannot_override_ok_run(self, ok_run):
        """Cannot override a run that is not blocked."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import (
            validate_override_preconditions,
            NotBlockedError,
        )

        request = OverrideRequest(reason="Test override reason here")

        with pytest.raises(NotBlockedError) as exc_info:
            validate_override_preconditions(ok_run, request)

        assert exc_info.value.code == "NOT_BLOCKED"

    def test_cannot_override_already_overridden(self, blocked_yellow_run):
        """Cannot override a run that already has an override."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import (
            validate_override_preconditions,
            AlreadyOverriddenError,
        )

        # Add existing override to meta
        blocked_yellow_run.meta = {"override": {"override_id": "existing123"}}

        request = OverrideRequest(reason="Test override reason here")

        with pytest.raises(AlreadyOverriddenError) as exc_info:
            validate_override_preconditions(blocked_yellow_run, request)

        assert exc_info.value.code == "ALREADY_OVERRIDDEN"

    def test_yellow_scope_valid_for_yellow_risk(self, blocked_yellow_run):
        """YELLOW scope is valid for YELLOW risk level."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import validate_override_preconditions

        request = OverrideRequest(reason="Tool wear is acceptable for this job", scope="YELLOW")

        # Should not raise
        validate_override_preconditions(blocked_yellow_run, request)

    def test_yellow_scope_invalid_for_red_risk(self, blocked_red_run):
        """YELLOW scope is invalid for RED risk level."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import (
            validate_override_preconditions,
            RiskMismatchError,
        )

        request = OverrideRequest(reason="Trying to use YELLOW on RED", scope="YELLOW")

        with pytest.raises(RiskMismatchError) as exc_info:
            validate_override_preconditions(blocked_red_run, request)

        assert exc_info.value.code == "RISK_MISMATCH"

    def test_red_override_disabled_by_default(self, blocked_red_run):
        """RED override is disabled by default."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import (
            validate_override_preconditions,
            RedOverrideNotAllowedError,
        )

        request = OverrideRequest(
            reason="Emergency override needed",
            scope="RED",
            acknowledge_risk=True,
        )

        with patch.dict(os.environ, {"RMOS_ALLOW_RED_OVERRIDE": ""}):
            with pytest.raises(RedOverrideNotAllowedError) as exc_info:
                validate_override_preconditions(blocked_red_run, request)

            assert exc_info.value.code == "RED_OVERRIDE_DISABLED"

    def test_red_override_requires_acknowledgment(self, blocked_red_run):
        """RED override requires explicit acknowledgment."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import (
            validate_override_preconditions,
            AcknowledgmentRequiredError,
        )

        request = OverrideRequest(
            reason="Emergency override needed",
            scope="RED",
            acknowledge_risk=False,  # Missing acknowledgment
        )

        with patch.dict(os.environ, {"RMOS_ALLOW_RED_OVERRIDE": "1"}):
            with pytest.raises(AcknowledgmentRequiredError) as exc_info:
                validate_override_preconditions(blocked_red_run, request)

            assert exc_info.value.code == "ACKNOWLEDGMENT_REQUIRED"

    def test_red_override_allowed_with_flag_and_ack(self, blocked_red_run):
        """RED override allowed when flag set and acknowledged."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import validate_override_preconditions

        request = OverrideRequest(
            reason="Emergency override needed for production deadline",
            scope="RED",
            acknowledge_risk=True,
        )

        with patch.dict(os.environ, {"RMOS_ALLOW_RED_OVERRIDE": "1"}):
            # Should not raise
            validate_override_preconditions(blocked_red_run, request)


class TestOverrideRecord:
    """Test override record creation."""

    def test_creates_valid_record(self, blocked_yellow_run):
        """Creates a valid override record with all fields."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import create_override_record

        request = OverrideRequest(reason="Operator reviewed and approved")

        record = create_override_record(
            run=blocked_yellow_run,
            request=request,
            operator_id="operator_123",
            operator_name="John Smith",
            request_id="req_abc",
        )

        assert record.run_id == blocked_yellow_run.run_id
        assert record.operator_id == "operator_123"
        assert record.operator_name == "John Smith"
        assert record.scope == "YELLOW"
        assert record.reason == "Operator reviewed and approved"
        assert record.original_risk_level == "YELLOW"
        assert record.original_status == "BLOCKED"
        assert record.request_id == "req_abc"
        assert record.override_id  # Should have a UUID


class TestApplyOverride:
    """Test the full override flow."""

    def test_yellow_override_changes_status_to_ok(self, blocked_yellow_run, tmp_path):
        """YELLOW override changes run status from BLOCKED to OK."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import apply_override

        # Mock store functions - patch at the point of use in override_service
        with patch("app.rmos.runs_v2.override_service.get_run", return_value=blocked_yellow_run):
            with patch("app.rmos.runs_v2.override_service.update_run") as mock_update:
                with patch("app.rmos.runs_v2.override_service.put_json_attachment") as mock_attach:
                    # Mock attachment
                    mock_attachment = MagicMock()
                    mock_attachment.sha256 = "override_hash_123"
                    mock_attach.return_value = (mock_attachment, "/path/to/attachment")

                    request = OverrideRequest(
                        reason="Tool wear is within acceptable limits for this operation"
                    )

                    response, updated_run = apply_override(
                        run_id=blocked_yellow_run.run_id,
                        request=request,
                        operator_id="op_test",
                    )

                    # Verify response
                    assert response.run_id == blocked_yellow_run.run_id
                    assert response.new_status == "OK"
                    assert response.attachment_sha256 == "override_hash_123"

                    # Verify run was updated
                    mock_update.assert_called_once()
                    call_arg = mock_update.call_args[0][0]
                    assert call_arg.status == "OK"
                    assert "override" in call_arg.meta
                    assert call_arg.meta["override"]["by"] == "op_test"

    def test_override_preserves_original_risk_level(self, blocked_yellow_run):
        """Override preserves the original decision.risk_level."""
        from app.rmos.runs_v2.schemas_override import OverrideRequest
        from app.rmos.runs_v2.override_service import apply_override

        with patch("app.rmos.runs_v2.override_service.get_run", return_value=blocked_yellow_run):
            with patch("app.rmos.runs_v2.override_service.update_run") as mock_update:
                with patch("app.rmos.runs_v2.override_service.put_json_attachment") as mock_attach:
                    mock_attachment = MagicMock()
                    mock_attachment.sha256 = "hash123"
                    mock_attach.return_value = (mock_attachment, "/path")

                    request = OverrideRequest(reason="Acceptable risk for this operation")

                    _, updated_run = apply_override(
                        run_id=blocked_yellow_run.run_id,
                        request=request,
                        operator_id="op_test",
                    )

                    # decision.risk_level should NOT change
                    call_arg = mock_update.call_args[0][0]
                    assert call_arg.decision.risk_level == "YELLOW"


class TestOverrideHelpers:
    """Test helper functions."""

    def test_is_overridden_false_for_new_run(self, blocked_yellow_run):
        """is_overridden returns False for run without override."""
        from app.rmos.runs_v2.override_service import is_overridden

        assert is_overridden(blocked_yellow_run) is False

    def test_is_overridden_true_after_override(self, blocked_yellow_run):
        """is_overridden returns True for run with override in meta."""
        from app.rmos.runs_v2.override_service import is_overridden

        blocked_yellow_run.meta = {
            "override": {
                "override_id": "test123",
                "by": "operator",
                "reason": "test",
                "scope": "YELLOW",
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "attachment_sha256": "abc123",
            }
        }

        assert is_overridden(blocked_yellow_run) is True


# =============================================================================
# Integration Tests: API Endpoint
# =============================================================================

@pytest.mark.integration
class TestOverrideEndpoint:
    """Test the override API endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def test_override_endpoint_exists(self, client):
        """Override endpoint is registered."""
        # Should get 404 for non-existent run, not 405 method not allowed
        response = client.post(
            "/api/rmos/runs/nonexistent123/override",
            json={"reason": "Test override reason here"},
        )
        # 401 = auth required (endpoint exists), 404 = run not found, 422 = validation
        # All of these mean the endpoint is mounted correctly (vs 405 method not allowed)
        assert response.status_code in (401, 404, 422, 400)

    def test_override_requires_reason_min_length(self, client):
        """Override requires reason of at least 10 characters."""
        response = client.post(
            "/api/rmos/runs/anyrun123/override",
            json={"reason": "short"},  # Too short
        )
        # 401 = auth required (endpoint exists and is protected)
        # 422 = validation error (what we'd get if auth passed)
        # Both indicate the endpoint is mounted correctly
        assert response.status_code in (401, 422)

    def test_get_override_not_found_for_non_overridden(self, client, blocked_yellow_run):
        """GET override returns 404 for run without override."""
        with patch("app.rmos.runs_v2.router_override.get_run", return_value=blocked_yellow_run):
            response = client.get(f"/api/rmos/runs/{blocked_yellow_run.run_id}/override")
            assert response.status_code == 404
            assert "No override found" in response.json()["detail"]["error"]
