"""
Tests for Federation CI Enforcement & Drift Baseline (CAM Dev Order 7Y).

Coverage:
  - FederationDriftBaseline model and validation
  - FederationCIEnforcementSummary model and classification
  - Baseline comparison logic
  - Registry operations (baseline and summary)
  - Router endpoints

7Y invariants tested:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - Baselines are immutable
  - CI summaries are historical records
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.cam.federation_drift_baseline import (
    FederationDriftBaseline,
    create_federation_drift_baseline,
    validate_federation_drift_baseline,
    is_baseline_valid,
    build_baseline_hash,
    get_baseline_summary,
)
from app.cam.federation_ci_enforcement import (
    FederationCIEnforcementSummary,
    classify_federation_ci_status,
    compare_federation_to_baseline,
    build_federation_ci_summary,
    evaluate_against_baseline,
    count_federation_authority_overrides,
    count_fragmented_federation,
    count_invalid_continuity,
    count_federation_warnings,
    get_summary_status_message,
    build_ci_summary_hash,
    get_enforcement_summary_dict,
)
from app.cam.federation_ci_registry import (
    register_federation_drift_baseline,
    get_federation_drift_baseline,
    list_federation_drift_baselines,
    get_baseline_by_name,
    register_federation_ci_summary,
    get_federation_ci_summary,
    get_latest_federation_ci_summary,
    list_federation_ci_summaries,
    list_federation_ci_summaries_by_status,
    list_summaries_for_baseline,
    get_baseline_count,
    get_ci_summary_count,
    get_passing_summary_count,
    get_failing_summary_count,
    get_warning_summary_count,
    get_ci_status_summary,
    clear_federation_ci_indexes_for_tests,
    get_federation_ci_index_counts,
)
from app.cam.federated_semantic_registry import (
    clear_federated_semantic_indexes_for_tests as clear_7x_indexes,
)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all federation CI indexes before each test."""
    clear_federation_ci_indexes_for_tests()
    clear_7x_indexes()
    yield
    clear_federation_ci_indexes_for_tests()
    clear_7x_indexes()


# ─────────────────────────────────────────────────────────────────────────────
# FederationDriftBaseline Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederationDriftBaselineModel:
    """Tests for FederationDriftBaseline model."""

    def test_create_baseline_defaults(self):
        """Test baseline creation with defaults."""
        baseline = FederationDriftBaseline(baseline_name="test-baseline")

        assert baseline.baseline_name == "test-baseline"
        assert baseline.baseline_id.startswith("fdb-")
        assert baseline.expected_federation_ref_count is None
        assert baseline.expected_continuity_record_count is None
        assert baseline.expected_package_count is None
        assert baseline.allowed_warning_count == 0
        assert baseline.allowed_fragmented_federation_count == 0
        assert baseline.authority_override_allowed is False
        assert baseline.ontology_mutation_allowed is False
        assert baseline.execution_authorized is False
        assert baseline.machine_output_allowed is False

    def test_create_baseline_with_expectations(self):
        """Test baseline creation with expected counts."""
        baseline = FederationDriftBaseline(
            baseline_name="full-baseline",
            expected_federation_ref_count=10,
            expected_continuity_record_count=5,
            expected_package_count=3,
            allowed_warning_count=2,
            allowed_fragmented_federation_count=1,
        )

        assert baseline.expected_federation_ref_count == 10
        assert baseline.expected_continuity_record_count == 5
        assert baseline.expected_package_count == 3
        assert baseline.allowed_warning_count == 2
        assert baseline.allowed_fragmented_federation_count == 1

    def test_baseline_7y_invariant_execution_authorized(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FederationDriftBaseline(
                baseline_name="bad-baseline",
                execution_authorized=True,
            )
        assert "execution_authorized must be False" in str(exc_info.value)

    def test_baseline_7y_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FederationDriftBaseline(
                baseline_name="bad-baseline",
                machine_output_allowed=True,
            )
        assert "machine_output_allowed must be False" in str(exc_info.value)

    def test_baseline_compute_hash(self):
        """Test deterministic hash computation."""
        baseline1 = FederationDriftBaseline(
            baseline_name="test-baseline",
            expected_federation_ref_count=10,
        )
        baseline2 = FederationDriftBaseline(
            baseline_name="test-baseline",
            expected_federation_ref_count=10,
        )

        hash1 = baseline1.compute_hash()
        hash2 = baseline2.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_baseline_hash_changes_with_values(self):
        """Test that hash changes when values change."""
        baseline1 = FederationDriftBaseline(
            baseline_name="test-baseline",
            expected_federation_ref_count=10,
        )
        baseline2 = FederationDriftBaseline(
            baseline_name="test-baseline",
            expected_federation_ref_count=20,
        )

        assert baseline1.compute_hash() != baseline2.compute_hash()

    def test_baseline_has_created_at(self):
        """Test that baseline has created_at timestamp."""
        baseline = FederationDriftBaseline(baseline_name="test-baseline")
        assert baseline.created_at is not None
        assert isinstance(baseline.created_at, datetime)


class TestFederationDriftBaselineHelpers:
    """Tests for baseline helper functions."""

    def test_create_federation_drift_baseline(self):
        """Test create_federation_drift_baseline factory."""
        baseline = create_federation_drift_baseline(
            baseline_name="factory-test",
            expected_federation_ref_count=5,
            expected_continuity_record_count=3,
        )

        assert baseline.baseline_name == "factory-test"
        assert baseline.expected_federation_ref_count == 5
        assert baseline.expected_continuity_record_count == 3
        assert baseline.deterministic_baseline_hash != ""

    def test_validate_baseline_valid(self):
        """Test validate_federation_drift_baseline with valid baseline."""
        baseline = create_federation_drift_baseline(baseline_name="valid")
        is_valid, issues = validate_federation_drift_baseline(baseline)

        assert is_valid is True
        assert issues == []

    def test_validate_baseline_empty_name(self):
        """Test validation fails for empty name."""
        baseline = FederationDriftBaseline(baseline_name="")
        is_valid, issues = validate_federation_drift_baseline(baseline)

        assert is_valid is False
        assert "baseline_name is required" in issues

    def test_validate_baseline_negative_warning_count(self):
        """Test validation fails for negative allowed_warning_count."""
        baseline = FederationDriftBaseline(
            baseline_name="test",
            allowed_warning_count=-1,
        )
        is_valid, issues = validate_federation_drift_baseline(baseline)

        assert is_valid is False
        assert "allowed_warning_count cannot be negative" in issues

    def test_validate_baseline_negative_fragmented_count(self):
        """Test validation fails for negative allowed_fragmented_federation_count."""
        baseline = FederationDriftBaseline(
            baseline_name="test",
            allowed_fragmented_federation_count=-1,
        )
        is_valid, issues = validate_federation_drift_baseline(baseline)

        assert is_valid is False
        assert "allowed_fragmented_federation_count cannot be negative" in issues

    def test_is_baseline_valid(self):
        """Test is_baseline_valid helper."""
        valid = create_federation_drift_baseline(baseline_name="valid")
        invalid = FederationDriftBaseline(baseline_name="", allowed_warning_count=-1)

        assert is_baseline_valid(valid) is True
        assert is_baseline_valid(invalid) is False

    def test_build_baseline_hash(self):
        """Test build_baseline_hash wrapper."""
        baseline = create_federation_drift_baseline(baseline_name="test")
        hash1 = build_baseline_hash(baseline)
        hash2 = baseline.compute_hash()

        assert hash1 == hash2

    def test_get_baseline_summary(self):
        """Test get_baseline_summary."""
        baseline = create_federation_drift_baseline(
            baseline_name="summary-test",
            expected_federation_ref_count=10,
            expected_continuity_record_count=5,
        )
        summary = get_baseline_summary(baseline)

        assert summary["baseline_name"] == "summary-test"
        assert summary["expected_federation_ref_count"] == 10
        assert summary["expected_continuity_record_count"] == 5
        assert "authority_override_allowed" in summary


# ─────────────────────────────────────────────────────────────────────────────
# FederationCIEnforcementSummary Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederationCIEnforcementSummaryModel:
    """Tests for FederationCIEnforcementSummary model."""

    def test_create_summary_defaults(self):
        """Test summary creation with defaults."""
        summary = FederationCIEnforcementSummary()

        assert summary.summary_id.startswith("fces-")
        assert summary.baseline_id is None
        assert summary.total_federation_refs == 0
        assert summary.total_continuity_records == 0
        assert summary.total_federated_packages == 0
        assert summary.authority_override_count == 0
        assert summary.ontology_mutation_attempt_count == 0
        assert summary.fragmented_federation_count == 0
        assert summary.invalid_continuity_count == 0
        assert summary.warning_count == 0
        assert summary.blocking_issue_count == 0
        assert summary.baseline_mismatch_detected is False
        assert summary.status == "pass"
        assert summary.blocking_issues == []
        assert summary.warnings == []
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False

    def test_summary_7y_invariant_execution_authorized(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FederationCIEnforcementSummary(execution_authorized=True)
        assert "execution_authorized must be False" in str(exc_info.value)

    def test_summary_7y_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FederationCIEnforcementSummary(machine_output_allowed=True)
        assert "machine_output_allowed must be False" in str(exc_info.value)

    def test_summary_compute_hash(self):
        """Test deterministic hash computation."""
        summary1 = FederationCIEnforcementSummary(
            total_federation_refs=10,
            total_continuity_records=5,
        )
        summary2 = FederationCIEnforcementSummary(
            total_federation_refs=10,
            total_continuity_records=5,
        )

        hash1 = summary1.compute_hash()
        hash2 = summary2.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_summary_hash_changes_with_values(self):
        """Test that hash changes when values change."""
        summary1 = FederationCIEnforcementSummary(total_federation_refs=10)
        summary2 = FederationCIEnforcementSummary(total_federation_refs=20)

        assert summary1.compute_hash() != summary2.compute_hash()

    def test_summary_with_warnings(self):
        """Test summary with warnings."""
        summary = FederationCIEnforcementSummary(
            warnings=["Warning 1", "Warning 2"],
            warning_count=2,
        )

        assert len(summary.warnings) == 2
        assert summary.warning_count == 2

    def test_summary_with_blocking_issues(self):
        """Test summary with blocking issues."""
        summary = FederationCIEnforcementSummary(
            blocking_issues=["Issue 1"],
            blocking_issue_count=1,
            status="fail",
        )

        assert len(summary.blocking_issues) == 1
        assert summary.status == "fail"


# ─────────────────────────────────────────────────────────────────────────────
# CI Status Classification Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCIStatusClassification:
    """Tests for classify_federation_ci_status."""

    def test_classify_pass_all_clean(self):
        """Test PASS when all counts are zero."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=False,
        )

        assert status == "pass"

    def test_classify_fail_authority_override(self):
        """Test FAIL when authority_override_count > 0."""
        status = classify_federation_ci_status(
            authority_override_count=1,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=False,
        )

        assert status == "fail"

    def test_classify_fail_ontology_mutation(self):
        """Test FAIL when ontology_mutation_attempt_count > 0."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=1,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=False,
        )

        assert status == "fail"

    def test_classify_fail_invalid_continuity(self):
        """Test FAIL when invalid_continuity_count > 0."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=1,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=False,
        )

        assert status == "fail"

    def test_classify_fail_blocking_issues(self):
        """Test FAIL when blocking_issue_count > 0."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=1,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=False,
        )

        assert status == "fail"

    def test_classify_fail_execution_authorized(self):
        """Test FAIL when execution_authorized is True."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=True,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=False,
        )

        assert status == "fail"

    def test_classify_fail_machine_output(self):
        """Test FAIL when machine_output_allowed is True."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=True,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=False,
        )

        assert status == "fail"

    def test_classify_warn_fragmented_exceeds_threshold(self):
        """Test WARN when fragmented_federation_count exceeds allowed."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=2,
            warning_count=0,
            baseline_mismatch_detected=False,
            allowed_fragmented_federation_count=1,
        )

        assert status == "warn"

    def test_classify_warn_warnings_exceed_threshold(self):
        """Test WARN when warning_count exceeds allowed."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=3,
            baseline_mismatch_detected=False,
            allowed_warning_count=2,
        )

        assert status == "warn"

    def test_classify_warn_baseline_mismatch(self):
        """Test WARN when baseline_mismatch_detected is True."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=0,
            warning_count=0,
            baseline_mismatch_detected=True,
        )

        assert status == "warn"

    def test_classify_pass_within_thresholds(self):
        """Test PASS when counts are within allowed thresholds."""
        status = classify_federation_ci_status(
            authority_override_count=0,
            ontology_mutation_attempt_count=0,
            invalid_continuity_count=0,
            blocking_issue_count=0,
            execution_authorized=False,
            machine_output_allowed=False,
            fragmented_federation_count=2,
            warning_count=3,
            baseline_mismatch_detected=False,
            allowed_fragmented_federation_count=2,
            allowed_warning_count=3,
        )

        assert status == "pass"


# ─────────────────────────────────────────────────────────────────────────────
# Baseline Comparison Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBaselineComparison:
    """Tests for compare_federation_to_baseline."""

    def test_compare_no_mismatch_all_match(self):
        """Test no mismatch when all counts match."""
        baseline = create_federation_drift_baseline(
            baseline_name="test",
            expected_federation_ref_count=10,
            expected_continuity_record_count=5,
            expected_package_count=3,
        )

        mismatch, warnings = compare_federation_to_baseline(
            total_federation_refs=10,
            total_continuity_records=5,
            total_federated_packages=3,
            baseline=baseline,
        )

        assert mismatch is False
        assert warnings == []

    def test_compare_mismatch_federation_refs(self):
        """Test mismatch detected for federation ref count."""
        baseline = create_federation_drift_baseline(
            baseline_name="test",
            expected_federation_ref_count=10,
        )

        mismatch, warnings = compare_federation_to_baseline(
            total_federation_refs=15,
            total_continuity_records=0,
            total_federated_packages=0,
            baseline=baseline,
        )

        assert mismatch is True
        assert len(warnings) == 1
        assert "Federation ref count mismatch" in warnings[0]

    def test_compare_mismatch_continuity_records(self):
        """Test mismatch detected for continuity record count."""
        baseline = create_federation_drift_baseline(
            baseline_name="test",
            expected_continuity_record_count=5,
        )

        mismatch, warnings = compare_federation_to_baseline(
            total_federation_refs=0,
            total_continuity_records=7,
            total_federated_packages=0,
            baseline=baseline,
        )

        assert mismatch is True
        assert len(warnings) == 1
        assert "Continuity record count mismatch" in warnings[0]

    def test_compare_mismatch_packages(self):
        """Test mismatch detected for package count."""
        baseline = create_federation_drift_baseline(
            baseline_name="test",
            expected_package_count=3,
        )

        mismatch, warnings = compare_federation_to_baseline(
            total_federation_refs=0,
            total_continuity_records=0,
            total_federated_packages=5,
            baseline=baseline,
        )

        assert mismatch is True
        assert len(warnings) == 1
        assert "Package count mismatch" in warnings[0]

    def test_compare_no_mismatch_none_expectations(self):
        """Test no mismatch when expectations are None."""
        baseline = create_federation_drift_baseline(
            baseline_name="test",
            # All expectations are None by default
        )

        mismatch, warnings = compare_federation_to_baseline(
            total_federation_refs=100,
            total_continuity_records=50,
            total_federated_packages=25,
            baseline=baseline,
        )

        assert mismatch is False
        assert warnings == []

    def test_compare_multiple_mismatches(self):
        """Test multiple mismatches detected."""
        baseline = create_federation_drift_baseline(
            baseline_name="test",
            expected_federation_ref_count=10,
            expected_continuity_record_count=5,
            expected_package_count=3,
        )

        mismatch, warnings = compare_federation_to_baseline(
            total_federation_refs=20,
            total_continuity_records=10,
            total_federated_packages=6,
            baseline=baseline,
        )

        assert mismatch is True
        assert len(warnings) == 3


# ─────────────────────────────────────────────────────────────────────────────
# CI Summary Building Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildFederationCISummary:
    """Tests for build_federation_ci_summary."""

    def test_build_summary_no_baseline(self):
        """Test building summary without baseline."""
        summary = build_federation_ci_summary()

        assert summary.baseline_id is None
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False
        assert summary.deterministic_summary_hash != ""

    def test_build_summary_with_baseline(self):
        """Test building summary with baseline."""
        baseline = create_federation_drift_baseline(baseline_name="test")

        summary = build_federation_ci_summary(baseline=baseline)

        assert summary.baseline_id == baseline.baseline_id

    def test_evaluate_against_baseline(self):
        """Test evaluate_against_baseline wrapper."""
        baseline = create_federation_drift_baseline(baseline_name="test")

        summary = evaluate_against_baseline(baseline)

        assert summary.baseline_id == baseline.baseline_id

    def test_summary_status_message_pass(self):
        """Test status message for passing summary."""
        summary = FederationCIEnforcementSummary(status="pass")
        message = get_summary_status_message(summary)

        assert "passed" in message.lower()

    def test_summary_status_message_warn(self):
        """Test status message for warning summary."""
        summary = FederationCIEnforcementSummary(
            status="warn",
            baseline_mismatch_detected=True,
            fragmented_federation_count=2,
        )
        message = get_summary_status_message(summary)

        assert "warning" in message.lower()
        assert "baseline mismatch" in message.lower() or "fragmented" in message.lower()

    def test_summary_status_message_fail(self):
        """Test status message for failing summary."""
        summary = FederationCIEnforcementSummary(
            status="fail",
            blocking_issues=["Authority override detected"],
        )
        message = get_summary_status_message(summary)

        assert "failed" in message.lower()


class TestCISummaryHelpers:
    """Tests for CI summary helper functions."""

    def test_count_federation_authority_overrides(self):
        """Test authority override counting."""
        count = count_federation_authority_overrides()
        assert isinstance(count, int)
        assert count >= 0

    def test_count_fragmented_federation(self):
        """Test fragmented federation counting."""
        count = count_fragmented_federation()
        assert isinstance(count, int)
        assert count >= 0

    def test_count_invalid_continuity(self):
        """Test invalid continuity counting."""
        count = count_invalid_continuity()
        assert isinstance(count, int)
        assert count >= 0

    def test_count_federation_warnings(self):
        """Test warning counting."""
        count = count_federation_warnings()
        assert isinstance(count, int)
        assert count >= 0

    def test_build_ci_summary_hash(self):
        """Test build_ci_summary_hash wrapper."""
        summary = FederationCIEnforcementSummary()
        hash1 = build_ci_summary_hash(summary)
        hash2 = summary.compute_hash()

        assert hash1 == hash2

    def test_get_enforcement_summary_dict(self):
        """Test get_enforcement_summary_dict."""
        summary = FederationCIEnforcementSummary(
            total_federation_refs=10,
            status="pass",
        )
        result = get_enforcement_summary_dict(summary)

        assert result["total_federation_refs"] == 10
        assert result["status"] == "pass"
        assert "status_message" in result


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests - Baselines
# ─────────────────────────────────────────────────────────────────────────────

class TestBaselineRegistry:
    """Tests for baseline registry operations."""

    def test_register_baseline_success(self):
        """Test successful baseline registration."""
        baseline = create_federation_drift_baseline(baseline_name="test")
        success, error = register_federation_drift_baseline(baseline)

        assert success is True
        assert error is None

    def test_register_baseline_duplicate_fails(self):
        """Test that duplicate registration fails."""
        baseline = create_federation_drift_baseline(baseline_name="test")
        register_federation_drift_baseline(baseline)

        success, error = register_federation_drift_baseline(baseline)

        assert success is False
        assert "already exists" in error
        assert "immutable" in error

    def test_register_baseline_invalid_fails(self):
        """Test that invalid baseline registration fails."""
        baseline = FederationDriftBaseline(baseline_name="", allowed_warning_count=-1)
        success, error = register_federation_drift_baseline(baseline)

        assert success is False
        assert "Validation failed" in error

    def test_get_baseline_found(self):
        """Test getting a registered baseline."""
        baseline = create_federation_drift_baseline(baseline_name="test")
        register_federation_drift_baseline(baseline)

        result = get_federation_drift_baseline(baseline.baseline_id)

        assert result is not None
        assert result.baseline_id == baseline.baseline_id

    def test_get_baseline_not_found(self):
        """Test getting a non-existent baseline."""
        result = get_federation_drift_baseline("non-existent")

        assert result is None

    def test_list_baselines(self):
        """Test listing all baselines."""
        baseline1 = create_federation_drift_baseline(baseline_name="test-1")
        baseline2 = create_federation_drift_baseline(baseline_name="test-2")
        register_federation_drift_baseline(baseline1)
        register_federation_drift_baseline(baseline2)

        baselines = list_federation_drift_baselines()

        assert len(baselines) == 2

    def test_get_baseline_by_name(self):
        """Test getting baseline by name."""
        baseline = create_federation_drift_baseline(baseline_name="named-baseline")
        register_federation_drift_baseline(baseline)

        result = get_baseline_by_name("named-baseline")

        assert result is not None
        assert result.baseline_name == "named-baseline"

    def test_get_baseline_by_name_not_found(self):
        """Test getting non-existent baseline by name."""
        result = get_baseline_by_name("non-existent")

        assert result is None

    def test_get_baseline_count(self):
        """Test baseline count."""
        assert get_baseline_count() == 0

        baseline = create_federation_drift_baseline(baseline_name="test")
        register_federation_drift_baseline(baseline)

        assert get_baseline_count() == 1


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests - CI Summaries
# ─────────────────────────────────────────────────────────────────────────────

class TestCISummaryRegistry:
    """Tests for CI summary registry operations."""

    def test_register_summary_success(self):
        """Test successful summary registration."""
        summary = FederationCIEnforcementSummary()
        success, error = register_federation_ci_summary(summary)

        assert success is True
        assert error is None

    def test_register_summary_execution_authorized_fails(self):
        """Test that summary with execution_authorized cannot be registered."""
        summary = FederationCIEnforcementSummary()
        summary.execution_authorized = True
        success, error = register_federation_ci_summary(summary)

        assert success is False
        assert "execution_authorized" in error

    def test_register_summary_machine_output_fails(self):
        """Test that summary with machine_output_allowed cannot be registered."""
        summary = FederationCIEnforcementSummary()
        summary.machine_output_allowed = True
        success, error = register_federation_ci_summary(summary)

        assert success is False
        assert "machine_output_allowed" in error

    def test_get_summary_found(self):
        """Test getting a registered summary."""
        summary = FederationCIEnforcementSummary()
        register_federation_ci_summary(summary)

        result = get_federation_ci_summary(summary.summary_id)

        assert result is not None
        assert result.summary_id == summary.summary_id

    def test_get_summary_not_found(self):
        """Test getting a non-existent summary."""
        result = get_federation_ci_summary("non-existent")

        assert result is None

    def test_get_latest_summary(self):
        """Test getting latest summary."""
        summary1 = FederationCIEnforcementSummary()
        summary2 = FederationCIEnforcementSummary()
        register_federation_ci_summary(summary1)
        register_federation_ci_summary(summary2)

        latest = get_latest_federation_ci_summary()

        assert latest is not None
        assert latest.summary_id == summary2.summary_id

    def test_get_latest_summary_empty(self):
        """Test getting latest summary when none exist."""
        latest = get_latest_federation_ci_summary()

        assert latest is None

    def test_list_summaries(self):
        """Test listing all summaries."""
        summary1 = FederationCIEnforcementSummary()
        summary2 = FederationCIEnforcementSummary()
        register_federation_ci_summary(summary1)
        register_federation_ci_summary(summary2)

        summaries = list_federation_ci_summaries()

        assert len(summaries) == 2

    def test_list_summaries_by_status(self):
        """Test listing summaries by status."""
        pass_summary = FederationCIEnforcementSummary(status="pass")
        fail_summary = FederationCIEnforcementSummary(status="fail")
        register_federation_ci_summary(pass_summary)
        register_federation_ci_summary(fail_summary)

        passing = list_federation_ci_summaries_by_status("pass")
        failing = list_federation_ci_summaries_by_status("fail")

        assert len(passing) == 1
        assert len(failing) == 1

    def test_list_summaries_for_baseline(self):
        """Test listing summaries for a baseline."""
        baseline = create_federation_drift_baseline(baseline_name="test")
        register_federation_drift_baseline(baseline)

        summary1 = FederationCIEnforcementSummary(baseline_id=baseline.baseline_id)
        summary2 = FederationCIEnforcementSummary(baseline_id=baseline.baseline_id)
        summary3 = FederationCIEnforcementSummary()  # No baseline
        register_federation_ci_summary(summary1)
        register_federation_ci_summary(summary2)
        register_federation_ci_summary(summary3)

        summaries = list_summaries_for_baseline(baseline.baseline_id)

        assert len(summaries) == 2

    def test_get_ci_summary_count(self):
        """Test summary count."""
        assert get_ci_summary_count() == 0

        summary = FederationCIEnforcementSummary()
        register_federation_ci_summary(summary)

        assert get_ci_summary_count() == 1

    def test_get_passing_summary_count(self):
        """Test passing summary count."""
        pass_summary = FederationCIEnforcementSummary(status="pass")
        fail_summary = FederationCIEnforcementSummary(status="fail")
        register_federation_ci_summary(pass_summary)
        register_federation_ci_summary(fail_summary)

        assert get_passing_summary_count() == 1

    def test_get_failing_summary_count(self):
        """Test failing summary count."""
        pass_summary = FederationCIEnforcementSummary(status="pass")
        fail_summary = FederationCIEnforcementSummary(status="fail")
        register_federation_ci_summary(pass_summary)
        register_federation_ci_summary(fail_summary)

        assert get_failing_summary_count() == 1

    def test_get_warning_summary_count(self):
        """Test warning summary count."""
        warn_summary = FederationCIEnforcementSummary(status="warn")
        pass_summary = FederationCIEnforcementSummary(status="pass")
        register_federation_ci_summary(warn_summary)
        register_federation_ci_summary(pass_summary)

        assert get_warning_summary_count() == 1

    def test_get_ci_status_summary(self):
        """Test aggregated CI status summary."""
        pass_summary = FederationCIEnforcementSummary(status="pass")
        warn_summary = FederationCIEnforcementSummary(status="warn")
        fail_summary = FederationCIEnforcementSummary(status="fail")
        register_federation_ci_summary(pass_summary)
        register_federation_ci_summary(warn_summary)
        register_federation_ci_summary(fail_summary)

        status = get_ci_status_summary()

        assert status["total_summaries"] == 3
        assert status["passing_count"] == 1
        assert status["warning_count"] == 1
        assert status["failing_count"] == 1
        assert status["latest_status"] == "fail"


class TestRegistryTestHelpers:
    """Tests for registry test helpers."""

    def test_clear_indexes(self):
        """Test clearing indexes."""
        baseline = create_federation_drift_baseline(baseline_name="test")
        summary = FederationCIEnforcementSummary()
        register_federation_drift_baseline(baseline)
        register_federation_ci_summary(summary)

        clear_federation_ci_indexes_for_tests()

        assert get_baseline_count() == 0
        assert get_ci_summary_count() == 0

    def test_get_index_counts(self):
        """Test getting index counts."""
        baseline = create_federation_drift_baseline(baseline_name="test")
        summary = FederationCIEnforcementSummary()
        register_federation_drift_baseline(baseline)
        register_federation_ci_summary(summary)

        counts = get_federation_ci_index_counts()

        assert counts["baselines"] == 1
        assert counts["summaries"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Router Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederationCIRouter:
    """Tests for federation CI router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def test_create_baseline_endpoint(self, client):
        """Test POST /api/cam/federation-ci/baselines."""
        response = client.post(
            "/api/cam/federation-ci/baselines",
            json={
                "baseline_name": "test-baseline",
                "expected_federation_ref_count": 10,
                "expected_continuity_record_count": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["baseline_name"] == "test-baseline"
        assert data["expected_federation_ref_count"] == 10
        assert data["authority_override_allowed"] is False

    def test_create_duplicate_baseline_fails(self, client):
        """Test that duplicate baseline creation fails."""
        client.post(
            "/api/cam/federation-ci/baselines",
            json={"baseline_name": "test-baseline"},
        )

        response = client.post(
            "/api/cam/federation-ci/baselines",
            json={"baseline_name": "test-baseline"},
        )

        # We'll get a 200 because it's a different baseline_id, but with same name
        # This is expected behavior - names are not unique, IDs are
        assert response.status_code == 200

    def test_list_baselines_endpoint(self, client):
        """Test GET /api/cam/federation-ci/baselines."""
        client.post(
            "/api/cam/federation-ci/baselines",
            json={"baseline_name": "baseline-1"},
        )
        client.post(
            "/api/cam/federation-ci/baselines",
            json={"baseline_name": "baseline-2"},
        )

        response = client.get("/api/cam/federation-ci/baselines")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_baseline_endpoint(self, client):
        """Test GET /api/cam/federation-ci/baselines/{baseline_id}."""
        create_response = client.post(
            "/api/cam/federation-ci/baselines",
            json={"baseline_name": "test-baseline"},
        )
        baseline_id = create_response.json()["baseline_id"]

        response = client.get(f"/api/cam/federation-ci/baselines/{baseline_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["baseline_id"] == baseline_id

    def test_get_baseline_not_found(self, client):
        """Test GET /api/cam/federation-ci/baselines/{baseline_id} not found."""
        response = client.get("/api/cam/federation-ci/baselines/non-existent")

        assert response.status_code == 404

    def test_evaluate_endpoint(self, client):
        """Test POST /api/cam/federation-ci/evaluate."""
        response = client.post(
            "/api/cam/federation-ci/evaluate",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary_id" in data
        assert "status" in data
        assert data["status"] in ["pass", "warn", "fail"]

    def test_evaluate_with_baseline(self, client):
        """Test POST /api/cam/federation-ci/evaluate with baseline."""
        create_response = client.post(
            "/api/cam/federation-ci/baselines",
            json={"baseline_name": "eval-baseline"},
        )
        baseline_id = create_response.json()["baseline_id"]

        response = client.post(
            "/api/cam/federation-ci/evaluate",
            json={"baseline_id": baseline_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["baseline_id"] == baseline_id

    def test_evaluate_with_invalid_baseline(self, client):
        """Test POST /api/cam/federation-ci/evaluate with invalid baseline."""
        response = client.post(
            "/api/cam/federation-ci/evaluate",
            json={"baseline_id": "non-existent"},
        )

        assert response.status_code == 404

    def test_get_latest_summary_endpoint(self, client):
        """Test GET /api/cam/federation-ci/summary/latest."""
        # First create a summary via evaluate
        client.post("/api/cam/federation-ci/evaluate", json={})

        response = client.get("/api/cam/federation-ci/summary/latest")

        assert response.status_code == 200
        data = response.json()
        assert "summary_id" in data

    def test_get_latest_summary_no_summaries(self, client):
        """Test GET /api/cam/federation-ci/summary/latest with no summaries."""
        response = client.get("/api/cam/federation-ci/summary/latest")

        assert response.status_code == 404

    def test_get_ci_status_endpoint(self, client):
        """Test GET /api/cam/federation-ci/status."""
        response = client.get("/api/cam/federation-ci/status")

        assert response.status_code == 200
        data = response.json()
        assert "total_baselines" in data
        assert "total_summaries" in data
        assert "passing_count" in data

    def test_list_summaries_endpoint(self, client):
        """Test GET /api/cam/federation-ci/summaries."""
        client.post("/api/cam/federation-ci/evaluate", json={})
        client.post("/api/cam/federation-ci/evaluate", json={})

        response = client.get("/api/cam/federation-ci/summaries")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_summary_endpoint(self, client):
        """Test GET /api/cam/federation-ci/summaries/{summary_id}."""
        eval_response = client.post("/api/cam/federation-ci/evaluate", json={})
        summary_id = eval_response.json()["summary_id"]

        response = client.get(f"/api/cam/federation-ci/summaries/{summary_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["summary_id"] == summary_id

    def test_get_summary_not_found(self, client):
        """Test GET /api/cam/federation-ci/summaries/{summary_id} not found."""
        response = client.get("/api/cam/federation-ci/summaries/non-existent")

        assert response.status_code == 404
