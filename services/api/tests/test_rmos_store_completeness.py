"""
Tests for RMOS Run Artifact Store Completeness Guard.

Tests for completeness validation before persisting artifacts.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.rmos.runs_v2.store_completeness import (
    CompletenessViolation,
    check_completeness,
    create_blocked_artifact_for_violations,
    validate_and_persist,
    REQUIRED_INVARIANTS,
)


class TestCompletenessViolation:
    """Tests for CompletenessViolation class."""

    def test_violation_str(self):
        """Should format violation as string."""
        violation = CompletenessViolation("field_name", "reason text")
        assert str(violation) == "field_name: reason text"

    def test_violation_fields(self):
        """Should store field and reason."""
        violation = CompletenessViolation("hashes.sha256", "required")
        assert violation.field == "hashes.sha256"
        assert violation.reason == "required"


class TestCheckCompleteness:
    """Tests for check_completeness function."""

    def test_all_valid_returns_empty(self):
        """Should return empty list when all required fields present."""
        violations = check_completeness(
            feasibility_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            risk_level="GREEN",
        )
        assert violations == []

    def test_missing_feasibility_sha256(self):
        """Should report missing feasibility_sha256."""
        violations = check_completeness(
            feasibility_sha256=None,
            risk_level="GREEN",
        )
        assert len(violations) == 1
        assert violations[0].field == "hashes.feasibility_sha256"

    def test_missing_risk_level(self):
        """Should report missing risk_level."""
        violations = check_completeness(
            feasibility_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            risk_level=None,
        )
        assert len(violations) == 1
        assert violations[0].field == "decision.risk_level"

    def test_empty_risk_level(self):
        """Should report empty risk_level."""
        violations = check_completeness(
            feasibility_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            risk_level="",
        )
        assert len(violations) == 1
        assert violations[0].field == "decision.risk_level"

    def test_whitespace_risk_level(self):
        """Should report whitespace-only risk_level."""
        violations = check_completeness(
            feasibility_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            risk_level="   ",
        )
        assert len(violations) == 1
        assert violations[0].field == "decision.risk_level"

    def test_missing_both(self):
        """Should report both missing fields."""
        violations = check_completeness(
            feasibility_sha256=None,
            risk_level=None,
        )
        assert len(violations) == 2

    def test_feasibility_dict_fallback_sha256(self):
        """Should extract feasibility_sha256 from feasibility dict."""
        violations = check_completeness(
            feasibility_sha256=None,
            risk_level="GREEN",
            feasibility={"sha256": "fallback_sha"},
        )
        assert violations == []

    def test_feasibility_dict_fallback_hash(self):
        """Should extract feasibility_sha256 from 'hash' key."""
        violations = check_completeness(
            feasibility_sha256=None,
            risk_level="GREEN",
            feasibility={"hash": "fallback_hash"},
        )
        assert violations == []

    def test_feasibility_dict_empty_no_fallback(self):
        """Should report violation when feasibility dict has no sha256."""
        violations = check_completeness(
            feasibility_sha256=None,
            risk_level="GREEN",
            feasibility={},
        )
        assert len(violations) == 1
        assert violations[0].field == "hashes.feasibility_sha256"


class TestCreateBlockedArtifactForViolations:
    """Tests for create_blocked_artifact_for_violations function."""

    def test_creates_blocked_artifact(self):
        """Should create artifact with BLOCKED status."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="execute",
            tool_id="tool_456",
            violations=violations,
        )
        assert artifact.status == "BLOCKED"
        assert artifact.run_id == "run_123"
        assert artifact.mode == "execute"
        assert artifact.tool_id == "tool_456"

    def test_sets_error_risk_level(self):
        """Should set risk_level to ERROR."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
        )
        assert artifact.decision.risk_level == "ERROR"

    def test_includes_block_reason(self):
        """Should include violations in block_reason."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
        )
        assert "Completeness guard" in artifact.decision.block_reason
        assert "field1" in artifact.decision.block_reason

    def test_includes_warnings(self):
        """Should include violations as warnings."""
        violations = [
            CompletenessViolation("field1", "reason1"),
            CompletenessViolation("field2", "reason2"),
        ]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
        )
        assert len(artifact.decision.warnings) == 2

    def test_includes_violation_details(self):
        """Should include violation details in decision.details."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
        )
        assert "violations" in artifact.decision.details
        assert artifact.decision.details["violations"][0]["field"] == "field1"

    def test_uses_placeholder_hash(self):
        """Should use placeholder hash for incomplete data."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
        )
        assert artifact.hashes.feasibility_sha256 == "0" * 64

    def test_sets_completeness_guard_meta(self):
        """Should set completeness_guard meta flag."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
        )
        assert artifact.meta.get("completeness_guard") is True
        assert artifact.meta.get("violation_count") == 1

    def test_preserves_request_summary(self):
        """Should preserve request_summary when provided."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
            request_summary={"key": "value"},
        )
        assert artifact.request_summary == {"key": "value"}

    def test_preserves_feasibility(self):
        """Should preserve feasibility when provided."""
        violations = [CompletenessViolation("field1", "reason1")]
        artifact = create_blocked_artifact_for_violations(
            run_id="run_123",
            mode="plan",
            tool_id="tool_456",
            violations=violations,
            feasibility={"risk_level": "YELLOW"},
        )
        assert artifact.feasibility == {"risk_level": "YELLOW"}


class TestValidateAndPersist:
    """Tests for validate_and_persist function."""

    @patch("app.rmos.runs_v2.store._get_default_store")
    def test_valid_artifact_persisted(self, mock_get_store):
        """Should persist valid artifact."""
        mock_store = MagicMock()
        mock_get_store.return_value = mock_store

        artifact = validate_and_persist(
            run_id="run_123",
            mode="execute",
            tool_id="tool_456",
            status="OK",
            request_summary={"key": "value"},
            feasibility={"risk_level": "GREEN"},
            feasibility_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            risk_level="GREEN",
        )

        mock_store.put.assert_called_once()
        assert artifact.status == "OK"
        assert artifact.decision.risk_level == "GREEN"

    @patch("app.rmos.runs_v2.store._get_default_store")
    def test_invalid_creates_blocked_artifact(self, mock_get_store):
        """Should create BLOCKED artifact when validation fails."""
        mock_store = MagicMock()
        mock_get_store.return_value = mock_store

        artifact = validate_and_persist(
            run_id="run_123",
            mode="execute",
            tool_id="tool_456",
            status="OK",
            request_summary={},
            feasibility={},
            feasibility_sha256=None,  # Missing
            risk_level=None,  # Missing
        )

        mock_store.put.assert_called_once()
        assert artifact.status == "BLOCKED"
        assert artifact.decision.risk_level == "ERROR"

    @patch("app.rmos.runs_v2.store._get_default_store")
    def test_optional_fields_preserved(self, mock_get_store):
        """Should preserve optional fields."""
        mock_store = MagicMock()
        mock_get_store.return_value = mock_store

        artifact = validate_and_persist(
            run_id="run_123",
            mode="execute",
            tool_id="tool_456",
            status="OK",
            request_summary={},
            feasibility={},
            feasibility_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            risk_level="GREEN",
            decision_score=0.95,
            decision_warnings=["warn1"],
            decision_details={"detail": "value"},
            toolpaths_sha256="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            gcode_sha256="cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            meta={"custom": "meta"},
        )

        assert artifact.decision.score == 0.95
        assert artifact.decision.warnings == ["warn1"]
        assert artifact.decision.details == {"detail": "value"}
        assert artifact.hashes.toolpaths_sha256 == "b" * 64
        assert artifact.hashes.gcode_sha256 == "c" * 64
        assert artifact.meta.get("custom") == "meta"


class TestRequiredInvariants:
    """Tests for REQUIRED_INVARIANTS constant."""

    def test_required_invariants_defined(self):
        """Should have required invariants defined."""
        assert len(REQUIRED_INVARIANTS) >= 2

    def test_invariants_have_field_and_reason(self):
        """Each invariant should have field and reason."""
        for field, reason in REQUIRED_INVARIANTS:
            assert field
            assert reason
