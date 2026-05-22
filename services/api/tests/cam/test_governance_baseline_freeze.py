"""
Tests for Governance Baseline Freeze & Release Readiness (CAM Dev Order 7Z).

Coverage:
  - GovernanceBaselineFreeze model and validation
  - ReleaseReadinessEvaluation model and classification
  - GovernanceReleasePackage model
  - Registry operations (freeze, evaluation, package)
  - Router endpoints

7Z invariants tested:
  - human_review_required: always True
  - auto_release_authorized: always False
  - release_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.cam.governance_baseline_freeze import (
    GovernanceBaselineFreeze,
    create_governance_baseline_freeze,
    validate_governance_baseline_freeze,
    is_freeze_valid,
    build_freeze_hash,
    get_freeze_summary,
)
from app.cam.release_readiness_evaluation import (
    ReleaseReadinessEvaluation,
    classify_readiness_status,
    evaluate_freeze_readiness,
    build_readiness_evaluation_from_ci,
    get_readiness_status_message,
    get_evaluation_summary_dict,
)
from app.cam.governance_release_package import (
    GovernanceReleasePackage,
    create_governance_release_package,
    build_package_from_freeze,
    get_package_summary,
    get_package_review_context,
)
from app.cam.governance_freeze_registry import (
    register_governance_freeze,
    get_governance_freeze,
    get_latest_governance_freeze,
    list_governance_freezes,
    list_governance_freezes_by_status,
    get_freeze_by_name,
    update_freeze_status,
    register_release_evaluation,
    get_release_evaluation,
    get_latest_release_evaluation,
    list_release_evaluations,
    list_evaluations_for_freeze,
    list_evaluations_by_status,
    register_governance_package,
    get_governance_package,
    get_latest_governance_package,
    list_governance_packages,
    list_packages_for_freeze,
    list_packages_by_readiness,
    get_governance_freeze_count,
    get_release_evaluation_count,
    get_governance_package_count,
    get_ready_evaluation_count,
    get_blocked_evaluation_count,
    get_pending_freeze_count,
    get_reviewed_freeze_count,
    get_governance_status_summary,
    clear_governance_freeze_indexes_for_tests,
    get_governance_freeze_index_counts,
)
from app.cam.federation_ci_registry import (
    clear_federation_ci_indexes_for_tests,
)
from app.cam.federated_semantic_registry import (
    clear_federated_semantic_indexes_for_tests,
)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_governance_freeze_indexes_for_tests()
    clear_federation_ci_indexes_for_tests()
    clear_federated_semantic_indexes_for_tests()
    yield
    clear_governance_freeze_indexes_for_tests()
    clear_federation_ci_indexes_for_tests()
    clear_federated_semantic_indexes_for_tests()


# ─────────────────────────────────────────────────────────────────────────────
# GovernanceBaselineFreeze Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGovernanceBaselineFreezeModel:
    """Tests for GovernanceBaselineFreeze model."""

    def test_create_freeze_defaults(self):
        """Test freeze creation with defaults."""
        freeze = GovernanceBaselineFreeze(freeze_name="test-freeze")

        assert freeze.freeze_name == "test-freeze"
        assert freeze.freeze_id.startswith("gbf-")
        assert freeze.baseline_id is None
        assert freeze.ci_summary_id is None
        assert freeze.ci_status_at_freeze is None
        assert freeze.status == "pending"
        assert freeze.human_review_required is True
        assert freeze.auto_release_authorized is False
        assert freeze.release_authorized is False
        assert freeze.execution_authorized is False
        assert freeze.machine_output_allowed is False

    def test_create_freeze_with_ci_state(self):
        """Test freeze creation with CI state."""
        freeze = GovernanceBaselineFreeze(
            freeze_name="ci-freeze",
            baseline_id="fdb-123",
            ci_summary_id="fces-456",
            ci_status_at_freeze="pass",
            federation_ref_count_at_freeze=10,
            continuity_record_count_at_freeze=5,
            package_count_at_freeze=3,
        )

        assert freeze.baseline_id == "fdb-123"
        assert freeze.ci_summary_id == "fces-456"
        assert freeze.ci_status_at_freeze == "pass"
        assert freeze.federation_ref_count_at_freeze == 10

    def test_freeze_7z_invariant_human_review_required(self):
        """Test that human_review_required=False raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GovernanceBaselineFreeze(
                freeze_name="bad-freeze",
                human_review_required=False,
            )
        assert "human_review_required must be True" in str(exc_info.value)

    def test_freeze_7z_invariant_auto_release_authorized(self):
        """Test that auto_release_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GovernanceBaselineFreeze(
                freeze_name="bad-freeze",
                auto_release_authorized=True,
            )
        assert "auto_release_authorized must be False" in str(exc_info.value)

    def test_freeze_7z_invariant_release_authorized(self):
        """Test that release_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GovernanceBaselineFreeze(
                freeze_name="bad-freeze",
                release_authorized=True,
            )
        assert "release_authorized must be False" in str(exc_info.value)

    def test_freeze_7z_invariant_execution_authorized(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GovernanceBaselineFreeze(
                freeze_name="bad-freeze",
                execution_authorized=True,
            )
        assert "execution_authorized must be False" in str(exc_info.value)

    def test_freeze_7z_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GovernanceBaselineFreeze(
                freeze_name="bad-freeze",
                machine_output_allowed=True,
            )
        assert "machine_output_allowed must be False" in str(exc_info.value)

    def test_freeze_compute_hash(self):
        """Test deterministic hash computation."""
        freeze1 = GovernanceBaselineFreeze(
            freeze_name="test-freeze",
            ci_status_at_freeze="pass",
        )
        freeze2 = GovernanceBaselineFreeze(
            freeze_name="test-freeze",
            ci_status_at_freeze="pass",
        )

        hash1 = freeze1.compute_hash()
        hash2 = freeze2.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_freeze_hash_changes_with_values(self):
        """Test that hash changes when values change."""
        freeze1 = GovernanceBaselineFreeze(
            freeze_name="test-freeze",
            ci_status_at_freeze="pass",
        )
        freeze2 = GovernanceBaselineFreeze(
            freeze_name="test-freeze",
            ci_status_at_freeze="fail",
        )

        assert freeze1.compute_hash() != freeze2.compute_hash()


class TestGovernanceBaselineFreezeHelpers:
    """Tests for freeze helper functions."""

    def test_create_governance_baseline_freeze(self):
        """Test create_governance_baseline_freeze factory."""
        freeze = create_governance_baseline_freeze(
            freeze_name="factory-test",
            baseline_id="fdb-123",
            ci_status_at_freeze="pass",
        )

        assert freeze.freeze_name == "factory-test"
        assert freeze.baseline_id == "fdb-123"
        assert freeze.deterministic_freeze_hash != ""

    def test_validate_freeze_valid(self):
        """Test validate_governance_baseline_freeze with valid freeze."""
        freeze = create_governance_baseline_freeze(freeze_name="valid")
        is_valid, issues = validate_governance_baseline_freeze(freeze)

        assert is_valid is True
        assert issues == []

    def test_validate_freeze_empty_name(self):
        """Test validation fails for empty name."""
        freeze = GovernanceBaselineFreeze(freeze_name="")
        is_valid, issues = validate_governance_baseline_freeze(freeze)

        assert is_valid is False
        assert "freeze_name is required" in issues

    def test_validate_freeze_negative_blocking(self):
        """Test validation fails for negative blocking_issue_count."""
        freeze = GovernanceBaselineFreeze(
            freeze_name="test",
            blocking_issue_count=-1,
        )
        is_valid, issues = validate_governance_baseline_freeze(freeze)

        assert is_valid is False
        assert "blocking_issue_count cannot be negative" in issues

    def test_is_freeze_valid(self):
        """Test is_freeze_valid helper."""
        valid = create_governance_baseline_freeze(freeze_name="valid")
        invalid = GovernanceBaselineFreeze(freeze_name="", blocking_issue_count=-1)

        assert is_freeze_valid(valid) is True
        assert is_freeze_valid(invalid) is False

    def test_build_freeze_hash(self):
        """Test build_freeze_hash wrapper."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        hash1 = build_freeze_hash(freeze)
        hash2 = freeze.compute_hash()

        assert hash1 == hash2

    def test_get_freeze_summary(self):
        """Test get_freeze_summary."""
        freeze = create_governance_baseline_freeze(
            freeze_name="summary-test",
            ci_status_at_freeze="pass",
        )
        summary = get_freeze_summary(freeze)

        assert summary["freeze_name"] == "summary-test"
        assert summary["ci_status_at_freeze"] == "pass"
        assert "human_review_required" in summary


# ─────────────────────────────────────────────────────────────────────────────
# ReleaseReadinessEvaluation Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReleaseReadinessEvaluationModel:
    """Tests for ReleaseReadinessEvaluation model."""

    def test_create_evaluation_defaults(self):
        """Test evaluation creation with defaults."""
        evaluation = ReleaseReadinessEvaluation(freeze_id="gbf-123")

        assert evaluation.evaluation_id.startswith("rre-")
        assert evaluation.freeze_id == "gbf-123"
        assert evaluation.readiness_status == "not_ready"
        assert evaluation.ci_passed is False
        assert evaluation.human_review_required is True
        assert evaluation.release_authorized is False

    def test_evaluation_7z_invariant_human_review_required(self):
        """Test that human_review_required=False raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReleaseReadinessEvaluation(
                freeze_id="gbf-123",
                human_review_required=False,
            )
        assert "human_review_required must be True" in str(exc_info.value)

    def test_evaluation_7z_invariant_release_authorized(self):
        """Test that release_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReleaseReadinessEvaluation(
                freeze_id="gbf-123",
                release_authorized=True,
            )
        assert "release_authorized must be False" in str(exc_info.value)

    def test_evaluation_7z_invariant_execution_authorized(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReleaseReadinessEvaluation(
                freeze_id="gbf-123",
                execution_authorized=True,
            )
        assert "execution_authorized must be False" in str(exc_info.value)

    def test_evaluation_compute_hash(self):
        """Test deterministic hash computation."""
        eval1 = ReleaseReadinessEvaluation(
            freeze_id="gbf-123",
            readiness_status="ready",
        )
        eval2 = ReleaseReadinessEvaluation(
            freeze_id="gbf-123",
            readiness_status="ready",
        )

        hash1 = eval1.compute_hash()
        hash2 = eval2.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64


class TestReadinessClassification:
    """Tests for classify_readiness_status."""

    def test_classify_ready_all_pass(self):
        """Test READY when all criteria pass."""
        status = classify_readiness_status(
            ci_passed=True,
            no_blocking_issues=True,
            warnings_within_threshold=True,
            baseline_aligned=True,
            human_review_completed=True,
        )

        assert status == "ready"

    def test_classify_blocked_ci_failed(self):
        """Test BLOCKED when CI failed."""
        status = classify_readiness_status(
            ci_passed=False,
            no_blocking_issues=True,
            warnings_within_threshold=True,
            baseline_aligned=True,
            human_review_completed=True,
        )

        assert status == "blocked"

    def test_classify_blocked_blocking_issues(self):
        """Test BLOCKED when blocking issues exist."""
        status = classify_readiness_status(
            ci_passed=True,
            no_blocking_issues=False,
            warnings_within_threshold=True,
            baseline_aligned=True,
            human_review_completed=True,
        )

        assert status == "blocked"

    def test_classify_not_ready_warnings(self):
        """Test NOT_READY when warnings exceed threshold."""
        status = classify_readiness_status(
            ci_passed=True,
            no_blocking_issues=True,
            warnings_within_threshold=False,
            baseline_aligned=True,
            human_review_completed=True,
        )

        assert status == "not_ready"

    def test_classify_not_ready_baseline(self):
        """Test NOT_READY when baseline not aligned."""
        status = classify_readiness_status(
            ci_passed=True,
            no_blocking_issues=True,
            warnings_within_threshold=True,
            baseline_aligned=False,
            human_review_completed=True,
        )

        assert status == "not_ready"

    def test_classify_not_ready_review(self):
        """Test NOT_READY when human review incomplete."""
        status = classify_readiness_status(
            ci_passed=True,
            no_blocking_issues=True,
            warnings_within_threshold=True,
            baseline_aligned=True,
            human_review_completed=False,
        )

        assert status == "not_ready"


class TestEvaluateFreezeReadiness:
    """Tests for evaluate_freeze_readiness."""

    def test_evaluate_passing_freeze(self):
        """Test evaluation of a passing freeze."""
        freeze = create_governance_baseline_freeze(
            freeze_name="passing",
            baseline_id="fdb-123",
            ci_status_at_freeze="pass",
            blocking_issue_count=0,
            warning_count=0,
        )
        freeze.status = "reviewed"

        evaluation = evaluate_freeze_readiness(freeze)

        assert evaluation.ci_passed is True
        assert evaluation.no_blocking_issues is True
        assert evaluation.baseline_aligned is True

    def test_evaluate_failing_freeze(self):
        """Test evaluation of a failing freeze."""
        freeze = create_governance_baseline_freeze(
            freeze_name="failing",
            ci_status_at_freeze="fail",
            blocking_issue_count=3,
        )

        evaluation = evaluate_freeze_readiness(freeze)

        assert evaluation.ci_passed is False
        assert evaluation.no_blocking_issues is False
        assert evaluation.readiness_status == "blocked"
        assert len(evaluation.blocking_reasons) > 0

    def test_evaluate_with_warnings(self):
        """Test evaluation with warnings exceeding threshold."""
        freeze = create_governance_baseline_freeze(
            freeze_name="warnings",
            ci_status_at_freeze="pass",
            warning_count=5,
        )

        evaluation = evaluate_freeze_readiness(freeze, warning_threshold=2)

        assert evaluation.warnings_within_threshold is False
        assert len(evaluation.recommendations) > 0


class TestEvaluationHelpers:
    """Tests for evaluation helper functions."""

    def test_get_readiness_status_message_ready(self):
        """Test status message for ready evaluation."""
        evaluation = ReleaseReadinessEvaluation(
            freeze_id="gbf-123",
            readiness_status="ready",
        )
        message = get_readiness_status_message(evaluation)

        assert "READY" in message

    def test_get_readiness_status_message_blocked(self):
        """Test status message for blocked evaluation."""
        evaluation = ReleaseReadinessEvaluation(
            freeze_id="gbf-123",
            readiness_status="blocked",
            blocking_reasons=["CI failed"],
        )
        message = get_readiness_status_message(evaluation)

        assert "BLOCKED" in message

    def test_get_readiness_status_message_not_ready(self):
        """Test status message for not_ready evaluation."""
        evaluation = ReleaseReadinessEvaluation(
            freeze_id="gbf-123",
            readiness_status="not_ready",
            recommendations=["Complete human review"],
        )
        message = get_readiness_status_message(evaluation)

        assert "NOT READY" in message

    def test_get_evaluation_summary_dict(self):
        """Test get_evaluation_summary_dict."""
        evaluation = ReleaseReadinessEvaluation(
            freeze_id="gbf-123",
            readiness_status="ready",
        )
        result = get_evaluation_summary_dict(evaluation)

        assert result["freeze_id"] == "gbf-123"
        assert result["readiness_status"] == "ready"
        assert "status_message" in result


# ─────────────────────────────────────────────────────────────────────────────
# GovernanceReleasePackage Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGovernanceReleasePackageModel:
    """Tests for GovernanceReleasePackage model."""

    def test_create_package_defaults(self):
        """Test package creation with defaults."""
        package = GovernanceReleasePackage(
            package_name="test-package",
            freeze_id="gbf-123",
        )

        assert package.package_id.startswith("grp-")
        assert package.package_name == "test-package"
        assert package.freeze_id == "gbf-123"
        assert package.human_review_required is True
        assert package.release_authorized is False

    def test_package_7z_invariant_human_review_required(self):
        """Test that human_review_required=False raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GovernanceReleasePackage(
                package_name="bad-package",
                freeze_id="gbf-123",
                human_review_required=False,
            )
        assert "human_review_required must be True" in str(exc_info.value)

    def test_package_7z_invariant_release_authorized(self):
        """Test that release_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GovernanceReleasePackage(
                package_name="bad-package",
                freeze_id="gbf-123",
                release_authorized=True,
            )
        assert "release_authorized must be False" in str(exc_info.value)

    def test_package_compute_hash(self):
        """Test deterministic hash computation."""
        pkg1 = GovernanceReleasePackage(
            package_name="test-package",
            freeze_id="gbf-123",
        )
        pkg2 = GovernanceReleasePackage(
            package_name="test-package",
            freeze_id="gbf-123",
        )

        hash1 = pkg1.compute_hash()
        hash2 = pkg2.compute_hash()

        assert hash1 == hash2


class TestGovernanceReleasePackageHelpers:
    """Tests for package helper functions."""

    def test_create_governance_release_package(self):
        """Test create_governance_release_package factory."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        evaluation = ReleaseReadinessEvaluation(
            freeze_id=freeze.freeze_id,
            readiness_status="ready",
        )

        package = create_governance_release_package(
            package_name="factory-test",
            freeze=freeze,
            evaluation=evaluation,
        )

        assert package.package_name == "factory-test"
        assert package.freeze_id == freeze.freeze_id
        assert package.evaluation_id == evaluation.evaluation_id
        assert package.deterministic_package_hash != ""

    def test_build_package_from_freeze(self):
        """Test build_package_from_freeze."""
        freeze = create_governance_baseline_freeze(freeze_name="test")

        package = build_package_from_freeze(
            package_name="freeze-only",
            freeze=freeze,
        )

        assert package.freeze_id == freeze.freeze_id
        assert package.evaluation_id is None

    def test_get_package_summary(self):
        """Test get_package_summary."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        package = build_package_from_freeze("summary-test", freeze)
        summary = get_package_summary(package)

        assert summary["package_name"] == "summary-test"
        assert "human_review_required" in summary

    def test_get_package_review_context(self):
        """Test get_package_review_context."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        package = build_package_from_freeze("context-test", freeze)
        context = get_package_review_context(package)

        assert context["package_name"] == "context-test"
        assert "execution_authorized" in context
        assert context["execution_authorized"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests - Freezes
# ─────────────────────────────────────────────────────────────────────────────

class TestFreezeRegistry:
    """Tests for freeze registry operations."""

    def test_register_freeze_success(self):
        """Test successful freeze registration."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        success, error = register_governance_freeze(freeze)

        assert success is True
        assert error is None

    def test_register_freeze_duplicate_fails(self):
        """Test that duplicate registration fails."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        register_governance_freeze(freeze)

        success, error = register_governance_freeze(freeze)

        assert success is False
        assert "already exists" in error

    def test_register_freeze_invalid_fails(self):
        """Test that invalid freeze registration fails."""
        freeze = GovernanceBaselineFreeze(freeze_name="", blocking_issue_count=-1)
        success, error = register_governance_freeze(freeze)

        assert success is False
        assert "Validation failed" in error

    def test_get_freeze_found(self):
        """Test getting a registered freeze."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        register_governance_freeze(freeze)

        result = get_governance_freeze(freeze.freeze_id)

        assert result is not None
        assert result.freeze_id == freeze.freeze_id

    def test_get_freeze_not_found(self):
        """Test getting a non-existent freeze."""
        result = get_governance_freeze("non-existent")

        assert result is None

    def test_get_latest_freeze(self):
        """Test getting latest freeze."""
        freeze1 = create_governance_baseline_freeze(freeze_name="first")
        freeze2 = create_governance_baseline_freeze(freeze_name="second")
        register_governance_freeze(freeze1)
        register_governance_freeze(freeze2)

        latest = get_latest_governance_freeze()

        assert latest is not None
        assert latest.freeze_id == freeze2.freeze_id

    def test_list_freezes(self):
        """Test listing all freezes."""
        freeze1 = create_governance_baseline_freeze(freeze_name="first")
        freeze2 = create_governance_baseline_freeze(freeze_name="second")
        register_governance_freeze(freeze1)
        register_governance_freeze(freeze2)

        freezes = list_governance_freezes()

        assert len(freezes) == 2

    def test_list_freezes_by_status(self):
        """Test listing freezes by status."""
        freeze1 = create_governance_baseline_freeze(freeze_name="pending")
        register_governance_freeze(freeze1)

        pending = list_governance_freezes_by_status("pending")

        assert len(pending) == 1

    def test_get_freeze_by_name(self):
        """Test getting freeze by name."""
        freeze = create_governance_baseline_freeze(freeze_name="named")
        register_governance_freeze(freeze)

        result = get_freeze_by_name("named")

        assert result is not None
        assert result.freeze_name == "named"

    def test_update_freeze_status(self):
        """Test updating freeze status."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        register_governance_freeze(freeze)

        success, error = update_freeze_status(
            freeze.freeze_id,
            "reviewed",
            "Looks good",
        )

        assert success is True
        updated = get_governance_freeze(freeze.freeze_id)
        assert updated.status == "reviewed"
        assert "Looks good" in updated.reviewer_notes

    def test_update_freeze_status_invalid_transition(self):
        """Test invalid status transition."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        register_governance_freeze(freeze)

        success, error = update_freeze_status(
            freeze.freeze_id,
            "approved",  # Can't go from pending to approved
        )

        assert success is False
        assert "Invalid status transition" in error


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests - Evaluations
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluationRegistry:
    """Tests for evaluation registry operations."""

    def test_register_evaluation_success(self):
        """Test successful evaluation registration."""
        evaluation = ReleaseReadinessEvaluation(freeze_id="gbf-123")
        success, error = register_release_evaluation(evaluation)

        assert success is True
        assert error is None

    def test_register_evaluation_release_authorized_fails(self):
        """Test that evaluation with release_authorized cannot be registered."""
        evaluation = ReleaseReadinessEvaluation(freeze_id="gbf-123")
        evaluation.release_authorized = True
        success, error = register_release_evaluation(evaluation)

        assert success is False
        assert "release_authorized" in error

    def test_get_evaluation_found(self):
        """Test getting a registered evaluation."""
        evaluation = ReleaseReadinessEvaluation(freeze_id="gbf-123")
        register_release_evaluation(evaluation)

        result = get_release_evaluation(evaluation.evaluation_id)

        assert result is not None

    def test_list_evaluations(self):
        """Test listing all evaluations."""
        eval1 = ReleaseReadinessEvaluation(freeze_id="gbf-123")
        eval2 = ReleaseReadinessEvaluation(freeze_id="gbf-456")
        register_release_evaluation(eval1)
        register_release_evaluation(eval2)

        evaluations = list_release_evaluations()

        assert len(evaluations) == 2

    def test_list_evaluations_for_freeze(self):
        """Test listing evaluations for a freeze."""
        eval1 = ReleaseReadinessEvaluation(freeze_id="gbf-123")
        eval2 = ReleaseReadinessEvaluation(freeze_id="gbf-123")
        eval3 = ReleaseReadinessEvaluation(freeze_id="gbf-456")
        register_release_evaluation(eval1)
        register_release_evaluation(eval2)
        register_release_evaluation(eval3)

        evaluations = list_evaluations_for_freeze("gbf-123")

        assert len(evaluations) == 2

    def test_list_evaluations_by_status(self):
        """Test listing evaluations by status."""
        eval_ready = ReleaseReadinessEvaluation(
            freeze_id="gbf-123",
            readiness_status="ready",
        )
        eval_blocked = ReleaseReadinessEvaluation(
            freeze_id="gbf-456",
            readiness_status="blocked",
        )
        register_release_evaluation(eval_ready)
        register_release_evaluation(eval_blocked)

        ready = list_evaluations_by_status("ready")
        blocked = list_evaluations_by_status("blocked")

        assert len(ready) == 1
        assert len(blocked) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests - Packages
# ─────────────────────────────────────────────────────────────────────────────

class TestPackageRegistry:
    """Tests for package registry operations."""

    def test_register_package_success(self):
        """Test successful package registration."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        package = build_package_from_freeze("test-pkg", freeze)
        success, error = register_governance_package(package)

        assert success is True
        assert error is None

    def test_register_package_release_authorized_fails(self):
        """Test that package with release_authorized cannot be registered."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        package = build_package_from_freeze("test-pkg", freeze)
        package.release_authorized = True
        success, error = register_governance_package(package)

        assert success is False
        assert "release_authorized" in error

    def test_get_package_found(self):
        """Test getting a registered package."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        package = build_package_from_freeze("test-pkg", freeze)
        register_governance_package(package)

        result = get_governance_package(package.package_id)

        assert result is not None

    def test_list_packages(self):
        """Test listing all packages."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        pkg1 = build_package_from_freeze("pkg-1", freeze)
        pkg2 = build_package_from_freeze("pkg-2", freeze)
        register_governance_package(pkg1)
        register_governance_package(pkg2)

        packages = list_governance_packages()

        assert len(packages) == 2


class TestGovernanceStatusSummary:
    """Tests for governance status summary."""

    def test_get_governance_status_summary(self):
        """Test aggregated status summary."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        register_governance_freeze(freeze)

        evaluation = ReleaseReadinessEvaluation(
            freeze_id=freeze.freeze_id,
            readiness_status="ready",
        )
        register_release_evaluation(evaluation)

        package = build_package_from_freeze("test-pkg", freeze)
        register_governance_package(package)

        status = get_governance_status_summary()

        assert status["total_freezes"] == 1
        assert status["total_evaluations"] == 1
        assert status["total_packages"] == 1
        assert status["ready_evaluations"] == 1


class TestRegistryTestHelpers:
    """Tests for registry test helpers."""

    def test_clear_indexes(self):
        """Test clearing indexes."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        register_governance_freeze(freeze)

        clear_governance_freeze_indexes_for_tests()

        assert get_governance_freeze_count() == 0

    def test_get_index_counts(self):
        """Test getting index counts."""
        freeze = create_governance_baseline_freeze(freeze_name="test")
        register_governance_freeze(freeze)

        counts = get_governance_freeze_index_counts()

        assert counts["freezes"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Router Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGovernanceFreezeRouter:
    """Tests for governance freeze router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def test_create_freeze_endpoint(self, client):
        """Test POST /api/cam/governance-freeze/freezes."""
        response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "test-freeze"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["freeze_name"] == "test-freeze"
        assert data["human_review_required"] is True
        assert data["release_authorized"] is False

    def test_list_freezes_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/freezes."""
        client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "freeze-1"},
        )
        client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "freeze-2"},
        )

        response = client.get("/api/cam/governance-freeze/freezes")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_freeze_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/freezes/{freeze_id}."""
        create_response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "test-freeze"},
        )
        freeze_id = create_response.json()["freeze_id"]

        response = client.get(f"/api/cam/governance-freeze/freezes/{freeze_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["freeze_id"] == freeze_id

    def test_get_freeze_not_found(self, client):
        """Test GET /api/cam/governance-freeze/freezes/{freeze_id} not found."""
        response = client.get("/api/cam/governance-freeze/freezes/non-existent")

        assert response.status_code == 404

    def test_get_latest_freeze_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/freezes/latest."""
        client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "latest-test"},
        )

        response = client.get("/api/cam/governance-freeze/freezes/latest")

        assert response.status_code == 200

    def test_update_status_endpoint(self, client):
        """Test PATCH /api/cam/governance-freeze/freezes/{freeze_id}/status."""
        create_response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "status-test"},
        )
        freeze_id = create_response.json()["freeze_id"]

        response = client.patch(
            f"/api/cam/governance-freeze/freezes/{freeze_id}/status",
            json={"new_status": "reviewed", "reviewer_note": "LGTM"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"

    def test_evaluate_endpoint(self, client):
        """Test POST /api/cam/governance-freeze/evaluate."""
        create_response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "eval-test"},
        )
        freeze_id = create_response.json()["freeze_id"]

        response = client.post(
            "/api/cam/governance-freeze/evaluate",
            json={"freeze_id": freeze_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["freeze_id"] == freeze_id
        assert "readiness_status" in data

    def test_evaluate_with_invalid_freeze(self, client):
        """Test POST /api/cam/governance-freeze/evaluate with invalid freeze."""
        response = client.post(
            "/api/cam/governance-freeze/evaluate",
            json={"freeze_id": "non-existent"},
        )

        assert response.status_code == 404

    def test_get_latest_evaluation_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/evaluations/latest."""
        create_response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "eval-latest"},
        )
        freeze_id = create_response.json()["freeze_id"]
        client.post(
            "/api/cam/governance-freeze/evaluate",
            json={"freeze_id": freeze_id},
        )

        response = client.get("/api/cam/governance-freeze/evaluations/latest")

        assert response.status_code == 200

    def test_list_evaluations_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/evaluations."""
        response = client.get("/api/cam/governance-freeze/evaluations")

        assert response.status_code == 200

    def test_create_package_endpoint(self, client):
        """Test POST /api/cam/governance-freeze/packages."""
        create_response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "pkg-test"},
        )
        freeze_id = create_response.json()["freeze_id"]

        response = client.post(
            "/api/cam/governance-freeze/packages",
            json={
                "package_name": "test-package",
                "freeze_id": freeze_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["package_name"] == "test-package"
        assert data["human_review_required"] is True
        assert data["release_authorized"] is False

    def test_create_package_with_evaluation(self, client):
        """Test POST /api/cam/governance-freeze/packages with evaluation."""
        create_response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "pkg-eval-test"},
        )
        freeze_id = create_response.json()["freeze_id"]

        eval_response = client.post(
            "/api/cam/governance-freeze/evaluate",
            json={"freeze_id": freeze_id},
        )
        evaluation_id = eval_response.json()["evaluation_id"]

        response = client.post(
            "/api/cam/governance-freeze/packages",
            json={
                "package_name": "full-package",
                "freeze_id": freeze_id,
                "evaluation_id": evaluation_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["evaluation_id"] == evaluation_id

    def test_get_package_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/packages/{package_id}."""
        create_response = client.post(
            "/api/cam/governance-freeze/freezes",
            json={"freeze_name": "pkg-get"},
        )
        freeze_id = create_response.json()["freeze_id"]

        pkg_response = client.post(
            "/api/cam/governance-freeze/packages",
            json={
                "package_name": "get-test",
                "freeze_id": freeze_id,
            },
        )
        package_id = pkg_response.json()["package_id"]

        response = client.get(f"/api/cam/governance-freeze/packages/{package_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["package_id"] == package_id

    def test_list_packages_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/packages."""
        response = client.get("/api/cam/governance-freeze/packages")

        assert response.status_code == 200

    def test_get_status_endpoint(self, client):
        """Test GET /api/cam/governance-freeze/status."""
        response = client.get("/api/cam/governance-freeze/status")

        assert response.status_code == 200
        data = response.json()
        assert "total_freezes" in data
        assert "total_evaluations" in data
        assert "total_packages" in data
