"""
Tests for CAM Dev Order 8D: Review UX CI Enforcement.

Covers:
  - ReviewUXBaseline model and validation
  - ReviewUXCIEnforcementSummary model and invariants
  - Pure counting helpers
  - Baseline comparison
  - CI classification
  - Registry operations
  - Router endpoints

8D invariants tested:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - auto_approval_allowed: always False
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.cam.review_ux_baseline import (
    ReviewUXBaseline,
    create_review_ux_baseline,
    validate_review_ux_baseline,
    build_review_ux_baseline_hash,
    get_baseline_summary,
)
from app.cam.review_ux_ci_enforcement import (
    ReviewUXCIEnforcementSummary,
    count_missing_provenance,
    count_federation_visibility_gaps,
    count_fragmented_replay,
    count_review_overload,
    compare_review_ux_to_baseline,
    classify_review_ux_ci_status,
    evaluate_review_ux_against_baseline,
    get_ci_enforcement_summary,
)
from app.cam.review_ux_ci_registry import (
    register_review_ux_baseline,
    get_review_ux_baseline,
    get_latest_review_ux_baseline,
    list_review_ux_baselines,
    get_review_ux_baseline_count,
    register_review_ux_ci_summary,
    get_review_ux_ci_summary,
    get_latest_review_ux_ci_summary,
    list_review_ux_ci_summaries,
    list_ci_summaries_by_status,
    get_review_ux_ci_summary_count,
    evaluate_current_review_ux_state,
    run_review_ux_ci_check,
    build_review_ux_ci_report,
    get_review_ux_ci_status_summary,
    clear_review_ux_ci_indexes_for_tests,
    get_review_ux_ci_index_counts,
)
from app.cam.manufacturing_review_panel import ManufacturingReviewPanel
from app.cam.provenance_explanation import ProvenanceExplanationArtifact
from app.cam.review_attention_priority import ReviewAttentionPriority
from app.cam.review_ux_registry import clear_review_ux_indexes_for_tests


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_review_ux_ci_indexes_for_tests()
    clear_review_ux_indexes_for_tests()
    yield
    clear_review_ux_ci_indexes_for_tests()
    clear_review_ux_indexes_for_tests()


# ─────────────────────────────────────────────────────────────────────────────
# ReviewUXBaseline model tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewUXBaselineModel:
    """Tests for ReviewUXBaseline model."""

    def test_create_baseline_defaults(self):
        """Baseline has sensible defaults."""
        baseline = ReviewUXBaseline(baseline_name="test-baseline")
        assert baseline.baseline_name == "test-baseline"
        assert baseline.required_panel_count is None
        assert baseline.allowed_missing_provenance_count == 0
        assert baseline.allowed_federation_visibility_gap_count == 0
        assert baseline.allowed_fragmented_replay_count == 0
        assert baseline.allowed_review_overload_count == 0
        assert baseline.execution_authorized is False
        assert baseline.machine_output_allowed is False
        assert baseline.auto_approval_allowed is False

    def test_create_baseline_with_thresholds(self):
        """Baseline accepts threshold values."""
        baseline = ReviewUXBaseline(
            baseline_name="threshold-test",
            required_panel_count=5,
            allowed_missing_provenance_count=2,
            allowed_federation_visibility_gap_count=1,
            allowed_fragmented_replay_count=3,
            allowed_review_overload_count=1,
        )
        assert baseline.required_panel_count == 5
        assert baseline.allowed_missing_provenance_count == 2
        assert baseline.allowed_federation_visibility_gap_count == 1
        assert baseline.allowed_fragmented_replay_count == 3
        assert baseline.allowed_review_overload_count == 1

    def test_baseline_invariant_execution_authorized(self):
        """Baseline rejects execution_authorized=True."""
        with pytest.raises(ValueError, match="8D invariant violation"):
            ReviewUXBaseline(
                baseline_name="test",
                execution_authorized=True,
            )

    def test_baseline_invariant_machine_output_allowed(self):
        """Baseline rejects machine_output_allowed=True."""
        with pytest.raises(ValueError, match="8D invariant violation"):
            ReviewUXBaseline(
                baseline_name="test",
                machine_output_allowed=True,
            )

    def test_baseline_invariant_auto_approval_allowed(self):
        """Baseline rejects auto_approval_allowed=True."""
        with pytest.raises(ValueError, match="8D invariant violation"):
            ReviewUXBaseline(
                baseline_name="test",
                auto_approval_allowed=True,
            )

    def test_baseline_compute_hash(self):
        """Baseline computes deterministic hash."""
        baseline1 = ReviewUXBaseline(
            baseline_name="test",
            allowed_missing_provenance_count=1,
        )
        baseline2 = ReviewUXBaseline(
            baseline_name="test",
            allowed_missing_provenance_count=1,
        )
        assert baseline1.compute_hash() == baseline2.compute_hash()

    def test_baseline_hash_changes_with_thresholds(self):
        """Different thresholds produce different hashes."""
        baseline1 = ReviewUXBaseline(
            baseline_name="test",
            allowed_missing_provenance_count=1,
        )
        baseline2 = ReviewUXBaseline(
            baseline_name="test",
            allowed_missing_provenance_count=2,
        )
        assert baseline1.compute_hash() != baseline2.compute_hash()

    def test_create_review_ux_baseline_helper(self):
        """create_review_ux_baseline helper populates hash."""
        baseline = create_review_ux_baseline(
            baseline_name="helper-test",
            allowed_missing_provenance_count=3,
        )
        assert baseline.deterministic_baseline_hash != ""
        assert len(baseline.deterministic_baseline_hash) == 64

    def test_validate_review_ux_baseline_valid(self):
        """Valid baseline passes validation."""
        baseline = create_review_ux_baseline(baseline_name="valid")
        is_valid, issues = validate_review_ux_baseline(baseline)
        assert is_valid is True
        assert issues == []

    def test_validate_review_ux_baseline_empty_name(self):
        """Empty baseline_name fails validation."""
        baseline = ReviewUXBaseline(baseline_name="x")
        baseline.baseline_name = ""
        is_valid, issues = validate_review_ux_baseline(baseline)
        assert is_valid is False
        assert "Missing baseline_name" in issues

    def test_get_baseline_summary(self):
        """get_baseline_summary returns expected fields."""
        baseline = create_review_ux_baseline(
            baseline_name="summary-test",
            required_panel_count=10,
        )
        summary = get_baseline_summary(baseline)
        assert summary["baseline_name"] == "summary-test"
        assert summary["required_panel_count"] == 10
        assert summary["execution_authorized"] is False
        assert summary["machine_output_allowed"] is False
        assert summary["auto_approval_allowed"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Pure counting helper tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCountingHelpers:
    """Tests for pure counting helpers."""

    def test_count_missing_provenance_empty(self):
        """Empty collections return 0."""
        count = count_missing_provenance([], [])
        assert count == 0

    def test_count_missing_provenance_all_have_provenance(self):
        """Panels with matching explanations return 0."""
        panels = [
            ManufacturingReviewPanel(
                panel_id="p1",
                panel_name="Panel 1",
                context_artifact_ids=["a1"],
            ),
        ]
        explanations = [
            ProvenanceExplanationArtifact(
                explanation_id="e1",
                artifact_id="a1",
                explanation_text="Test explanation",
            ),
        ]
        count = count_missing_provenance(panels, explanations)
        assert count == 0

    def test_count_missing_provenance_some_missing(self):
        """Panels without matching explanations are counted."""
        panels = [
            ManufacturingReviewPanel(
                panel_id="p1",
                panel_name="Panel 1",
                context_artifact_ids=["a1", "a2"],
            ),
        ]
        explanations = [
            ProvenanceExplanationArtifact(
                explanation_id="e1",
                artifact_id="a1",
                explanation_text="Test explanation",
            ),
        ]
        count = count_missing_provenance(panels, explanations)
        assert count == 1

    def test_count_federation_visibility_gaps_empty(self):
        """Empty list returns 0."""
        count = count_federation_visibility_gaps([])
        assert count == 0

    def test_count_federation_visibility_gaps_none_missing(self):
        """Panels with federation_visible=True return 0."""
        panels = [
            ManufacturingReviewPanel(
                panel_id="p1",
                panel_name="Panel 1",
                federation_visible=True,
            ),
        ]
        count = count_federation_visibility_gaps(panels)
        assert count == 0

    def test_count_federation_visibility_gaps_some_missing(self):
        """Panels with federation_visible=False are counted."""
        panels = [
            ManufacturingReviewPanel(
                panel_id="p1",
                panel_name="Panel 1",
                federation_visible=False,
            ),
            ManufacturingReviewPanel(
                panel_id="p2",
                panel_name="Panel 2",
                federation_visible=True,
            ),
        ]
        count = count_federation_visibility_gaps(panels)
        assert count == 1

    def test_count_fragmented_replay_empty(self):
        """Empty list returns 0."""
        count = count_fragmented_replay([])
        assert count == 0

    def test_count_fragmented_replay_none_fragmented(self):
        """Panels with replay_complete=True return 0."""
        panels = [
            ManufacturingReviewPanel(
                panel_id="p1",
                panel_name="Panel 1",
                replay_complete=True,
            ),
        ]
        count = count_fragmented_replay(panels)
        assert count == 0

    def test_count_fragmented_replay_some_fragmented(self):
        """Panels with replay_complete=False are counted."""
        panels = [
            ManufacturingReviewPanel(
                panel_id="p1",
                panel_name="Panel 1",
                replay_complete=False,
            ),
        ]
        count = count_fragmented_replay(panels)
        assert count == 1

    def test_count_review_overload_empty(self):
        """Empty list returns 0."""
        count = count_review_overload([])
        assert count == 0

    def test_count_review_overload_none_overloaded(self):
        """Priorities with low scores return 0."""
        priorities = [
            ReviewAttentionPriority(
                priority_id="rp1",
                panel_id="p1",
                aggregate_attention_score=0.3,
            ),
        ]
        count = count_review_overload(priorities)
        assert count == 0

    def test_count_review_overload_some_overloaded(self):
        """Priorities with aggregate_attention_score >= 0.85 are counted."""
        priorities = [
            ReviewAttentionPriority(
                priority_id="rp1",
                panel_id="p1",
                aggregate_attention_score=0.9,
            ),
            ReviewAttentionPriority(
                priority_id="rp2",
                panel_id="p2",
                aggregate_attention_score=0.5,
            ),
        ]
        count = count_review_overload(priorities)
        assert count == 1

    def test_count_review_overload_threshold_boundary(self):
        """Score exactly 0.85 is counted as overloaded."""
        priorities = [
            ReviewAttentionPriority(
                priority_id="rp1",
                panel_id="p1",
                aggregate_attention_score=0.85,
            ),
        ]
        count = count_review_overload(priorities)
        assert count == 1


# ─────────────────────────────────────────────────────────────────────────────
# Baseline comparison tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBaselineComparison:
    """Tests for baseline comparison."""

    def test_compare_no_baseline_all_pass(self):
        """No baseline means comparison passes."""
        result = compare_review_ux_to_baseline(
            missing_provenance_count=5,
            federation_visibility_gap_count=3,
            fragmented_replay_count=2,
            review_overload_count=1,
            panel_count=10,
            baseline=None,
        )
        assert result["baseline_exceeded"] is False
        assert result["exceeded_fields"] == []

    def test_compare_within_thresholds(self):
        """Counts within thresholds pass."""
        baseline = create_review_ux_baseline(
            baseline_name="test",
            allowed_missing_provenance_count=5,
            allowed_federation_visibility_gap_count=3,
            allowed_fragmented_replay_count=2,
            allowed_review_overload_count=1,
        )
        result = compare_review_ux_to_baseline(
            missing_provenance_count=3,
            federation_visibility_gap_count=2,
            fragmented_replay_count=1,
            review_overload_count=0,
            panel_count=10,
            baseline=baseline,
        )
        assert result["baseline_exceeded"] is False
        assert result["exceeded_fields"] == []

    def test_compare_exceeds_missing_provenance(self):
        """Exceeding missing_provenance threshold is detected."""
        baseline = create_review_ux_baseline(
            baseline_name="test",
            allowed_missing_provenance_count=2,
        )
        result = compare_review_ux_to_baseline(
            missing_provenance_count=3,
            federation_visibility_gap_count=0,
            fragmented_replay_count=0,
            review_overload_count=0,
            panel_count=10,
            baseline=baseline,
        )
        assert result["baseline_exceeded"] is True
        assert "missing_provenance" in result["exceeded_fields"]

    def test_compare_exceeds_multiple_thresholds(self):
        """Multiple exceeded thresholds are all reported."""
        baseline = create_review_ux_baseline(
            baseline_name="test",
            allowed_missing_provenance_count=1,
            allowed_federation_visibility_gap_count=1,
        )
        result = compare_review_ux_to_baseline(
            missing_provenance_count=3,
            federation_visibility_gap_count=3,
            fragmented_replay_count=0,
            review_overload_count=0,
            panel_count=10,
            baseline=baseline,
        )
        assert result["baseline_exceeded"] is True
        assert "missing_provenance" in result["exceeded_fields"]
        assert "federation_visibility_gap" in result["exceeded_fields"]

    def test_compare_required_panel_count_met(self):
        """Meeting required_panel_count passes."""
        baseline = create_review_ux_baseline(
            baseline_name="test",
            required_panel_count=5,
        )
        result = compare_review_ux_to_baseline(
            missing_provenance_count=0,
            federation_visibility_gap_count=0,
            fragmented_replay_count=0,
            review_overload_count=0,
            panel_count=5,
            baseline=baseline,
        )
        assert result["baseline_exceeded"] is False

    def test_compare_required_panel_count_not_met(self):
        """Not meeting required_panel_count fails."""
        baseline = create_review_ux_baseline(
            baseline_name="test",
            required_panel_count=10,
        )
        result = compare_review_ux_to_baseline(
            missing_provenance_count=0,
            federation_visibility_gap_count=0,
            fragmented_replay_count=0,
            review_overload_count=0,
            panel_count=5,
            baseline=baseline,
        )
        assert result["baseline_exceeded"] is True
        assert "panel_count" in result["exceeded_fields"]


# ─────────────────────────────────────────────────────────────────────────────
# CI classification tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCIClassification:
    """Tests for CI status classification."""

    def test_classify_pass_no_issues(self):
        """No issues and no exceeded baseline is PASS."""
        status, blocking, warnings = classify_review_ux_ci_status(
            missing_provenance_count=0,
            federation_visibility_gap_count=0,
            fragmented_replay_count=0,
            review_overload_count=0,
            baseline_exceeded=False,
            exceeded_fields=[],
        )
        assert status == "pass"
        assert blocking == []
        assert warnings == []

    def test_classify_warn_has_missing_provenance(self):
        """Missing provenance without exceeding baseline is WARN."""
        status, blocking, warnings = classify_review_ux_ci_status(
            missing_provenance_count=2,
            federation_visibility_gap_count=0,
            fragmented_replay_count=0,
            review_overload_count=0,
            baseline_exceeded=False,
            exceeded_fields=[],
        )
        assert status == "warn"
        assert len(warnings) >= 1

    def test_classify_fail_baseline_exceeded(self):
        """Exceeding baseline is FAIL."""
        status, blocking, warnings = classify_review_ux_ci_status(
            missing_provenance_count=5,
            federation_visibility_gap_count=0,
            fragmented_replay_count=0,
            review_overload_count=0,
            baseline_exceeded=True,
            exceeded_fields=["missing_provenance"],
        )
        assert status == "fail"
        assert len(blocking) >= 1

    def test_classify_fail_review_overload(self):
        """Review overload is FAIL."""
        status, blocking, warnings = classify_review_ux_ci_status(
            missing_provenance_count=0,
            federation_visibility_gap_count=0,
            fragmented_replay_count=0,
            review_overload_count=3,
            baseline_exceeded=False,
            exceeded_fields=[],
        )
        assert status == "fail"
        assert any("overload" in b.lower() for b in blocking)


# ─────────────────────────────────────────────────────────────────────────────
# ReviewUXCIEnforcementSummary model tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewUXCIEnforcementSummary:
    """Tests for ReviewUXCIEnforcementSummary model."""

    def test_summary_defaults(self):
        """Summary has expected defaults."""
        summary = ReviewUXCIEnforcementSummary()
        assert summary.status == "pass"
        assert summary.panel_count == 0
        assert summary.missing_provenance_count == 0
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False
        assert summary.auto_approval_allowed is False

    def test_summary_invariant_execution_authorized(self):
        """Summary rejects execution_authorized=True."""
        with pytest.raises(ValueError, match="8D invariant violation"):
            ReviewUXCIEnforcementSummary(execution_authorized=True)

    def test_summary_invariant_machine_output_allowed(self):
        """Summary rejects machine_output_allowed=True."""
        with pytest.raises(ValueError, match="8D invariant violation"):
            ReviewUXCIEnforcementSummary(machine_output_allowed=True)

    def test_summary_invariant_auto_approval_allowed(self):
        """Summary rejects auto_approval_allowed=True."""
        with pytest.raises(ValueError, match="8D invariant violation"):
            ReviewUXCIEnforcementSummary(auto_approval_allowed=True)

    def test_summary_compute_hash(self):
        """Summary computes deterministic hash."""
        summary1 = ReviewUXCIEnforcementSummary(
            panel_count=5,
            missing_provenance_count=2,
        )
        summary2 = ReviewUXCIEnforcementSummary(
            panel_count=5,
            missing_provenance_count=2,
        )
        assert summary1.compute_hash() == summary2.compute_hash()

    def test_evaluate_review_ux_against_baseline_no_baseline(self):
        """evaluate_review_ux_against_baseline works without baseline."""
        summary = evaluate_review_ux_against_baseline(
            panels=[],
            explanations=[],
            priorities=[],
            baseline=None,
        )
        assert summary.panel_count == 0
        assert summary.baseline_exceeded is False

    def test_evaluate_review_ux_against_baseline_with_data(self):
        """evaluate_review_ux_against_baseline processes collections."""
        panels = [
            ManufacturingReviewPanel(
                panel_id="p1",
                panel_name="Panel 1",
                context_artifact_ids=["a1"],
                federation_visible=False,
            ),
        ]
        explanations = []
        priorities = []

        summary = evaluate_review_ux_against_baseline(
            panels=panels,
            explanations=explanations,
            priorities=priorities,
            baseline=None,
        )
        assert summary.panel_count == 1
        assert summary.missing_provenance_count == 1
        assert summary.federation_visibility_gap_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# Registry tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistry:
    """Tests for registry operations."""

    def test_register_baseline(self):
        """Baseline registration succeeds."""
        baseline = create_review_ux_baseline(baseline_name="test")
        success, error = register_review_ux_baseline(baseline)
        assert success is True
        assert error is None
        assert get_review_ux_baseline_count() == 1

    def test_register_baseline_duplicate_fails(self):
        """Duplicate baseline registration fails."""
        baseline = create_review_ux_baseline(baseline_name="test")
        register_review_ux_baseline(baseline)
        success, error = register_review_ux_baseline(baseline)
        assert success is False
        assert "already exists" in error

    def test_get_review_ux_baseline(self):
        """Baseline retrieval by ID works."""
        baseline = create_review_ux_baseline(baseline_name="test")
        register_review_ux_baseline(baseline)
        retrieved = get_review_ux_baseline(baseline.baseline_id)
        assert retrieved is not None
        assert retrieved.baseline_name == "test"

    def test_get_latest_review_ux_baseline(self):
        """Latest baseline retrieval works."""
        baseline1 = create_review_ux_baseline(baseline_name="first")
        baseline2 = create_review_ux_baseline(baseline_name="second")
        register_review_ux_baseline(baseline1)
        register_review_ux_baseline(baseline2)
        latest = get_latest_review_ux_baseline()
        assert latest is not None
        assert latest.baseline_name == "second"

    def test_list_review_ux_baselines(self):
        """Baseline listing preserves order."""
        baseline1 = create_review_ux_baseline(baseline_name="first")
        baseline2 = create_review_ux_baseline(baseline_name="second")
        register_review_ux_baseline(baseline1)
        register_review_ux_baseline(baseline2)
        baselines = list_review_ux_baselines()
        assert len(baselines) == 2
        assert baselines[0].baseline_name == "first"
        assert baselines[1].baseline_name == "second"

    def test_register_ci_summary(self):
        """CI summary registration succeeds."""
        summary = ReviewUXCIEnforcementSummary()
        success, error = register_review_ux_ci_summary(summary)
        assert success is True
        assert error is None
        assert get_review_ux_ci_summary_count() == 1

    def test_register_ci_summary_invariant_check(self):
        """CI summary registration checks invariants."""
        summary = ReviewUXCIEnforcementSummary()
        object.__setattr__(summary, "execution_authorized", True)
        success, error = register_review_ux_ci_summary(summary)
        assert success is False
        assert "execution_authorized" in error

    def test_get_review_ux_ci_summary(self):
        """CI summary retrieval by ID works."""
        summary = ReviewUXCIEnforcementSummary()
        register_review_ux_ci_summary(summary)
        retrieved = get_review_ux_ci_summary(summary.summary_id)
        assert retrieved is not None

    def test_list_ci_summaries_by_status(self):
        """CI summary filtering by status works."""
        summary_pass = ReviewUXCIEnforcementSummary(status="pass")
        summary_warn = ReviewUXCIEnforcementSummary(status="warn")
        register_review_ux_ci_summary(summary_pass)
        register_review_ux_ci_summary(summary_warn)

        pass_list = list_ci_summaries_by_status("pass")
        warn_list = list_ci_summaries_by_status("warn")
        assert len(pass_list) == 1
        assert len(warn_list) == 1

    def test_run_review_ux_ci_check(self):
        """run_review_ux_ci_check executes and registers."""
        summary, success, error = run_review_ux_ci_check()
        assert success is True
        assert error is None
        assert summary is not None
        assert get_review_ux_ci_summary_count() == 1

    def test_run_review_ux_ci_check_with_baseline(self):
        """run_review_ux_ci_check uses specified baseline."""
        baseline = create_review_ux_baseline(baseline_name="strict")
        register_review_ux_baseline(baseline)
        summary, success, error = run_review_ux_ci_check(baseline.baseline_id)
        assert success is True
        assert summary.baseline_id == baseline.baseline_id

    def test_run_review_ux_ci_check_missing_baseline(self):
        """run_review_ux_ci_check fails for missing baseline."""
        summary, success, error = run_review_ux_ci_check("nonexistent")
        assert success is False
        assert "not found" in error

    def test_build_review_ux_ci_report(self):
        """CI report contains expected fields."""
        baseline = create_review_ux_baseline(baseline_name="test")
        register_review_ux_baseline(baseline)
        run_review_ux_ci_check()

        report = build_review_ux_ci_report()
        assert "total_baselines" in report
        assert "total_ci_summaries" in report
        assert "pass_count" in report
        assert "status" in report

    def test_get_review_ux_ci_status_summary(self):
        """Status summary contains expected fields."""
        summary = get_review_ux_ci_status_summary()
        assert "total_baselines" in summary
        assert "total_ci_summaries" in summary
        assert "latest_baseline_id" in summary

    def test_clear_indexes_for_tests(self):
        """clear_review_ux_ci_indexes_for_tests clears all indexes."""
        baseline = create_review_ux_baseline(baseline_name="test")
        register_review_ux_baseline(baseline)
        run_review_ux_ci_check()

        clear_review_ux_ci_indexes_for_tests()
        counts = get_review_ux_ci_index_counts()
        assert counts["baselines"] == 0
        assert counts["ci_summaries"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Router endpoint tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRouterEndpoints:
    """Tests for router endpoints."""

    def test_create_baseline_endpoint(self):
        """POST /baselines creates baseline."""
        response = client.post(
            "/api/cam/review-ux-ci/baselines",
            json={
                "baseline_name": "api-test",
                "allowed_missing_provenance_count": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["baseline_name"] == "api-test"

    def test_list_baselines_endpoint(self):
        """GET /baselines returns list."""
        client.post(
            "/api/cam/review-ux-ci/baselines",
            json={"baseline_name": "test1"},
        )
        client.post(
            "/api/cam/review-ux-ci/baselines",
            json={"baseline_name": "test2"},
        )

        response = client.get("/api/cam/review-ux-ci/baselines")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_latest_baseline_endpoint(self):
        """GET /baselines/latest returns latest."""
        client.post(
            "/api/cam/review-ux-ci/baselines",
            json={"baseline_name": "first"},
        )
        client.post(
            "/api/cam/review-ux-ci/baselines",
            json={"baseline_name": "second"},
        )

        response = client.get("/api/cam/review-ux-ci/baselines/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["baseline_name"] == "second"

    def test_get_baseline_by_id_endpoint(self):
        """GET /baselines/{id} returns baseline."""
        create_response = client.post(
            "/api/cam/review-ux-ci/baselines",
            json={"baseline_name": "findme"},
        )
        baseline_id = create_response.json()["baseline_id"]

        response = client.get(f"/api/cam/review-ux-ci/baselines/{baseline_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["baseline_name"] == "findme"

    def test_get_baseline_not_found(self):
        """GET /baselines/{id} returns 404 for missing."""
        response = client.get("/api/cam/review-ux-ci/baselines/nonexistent")
        assert response.status_code == 404

    def test_run_ci_check_endpoint(self):
        """POST /check runs CI check."""
        response = client.post(
            "/api/cam/review-ux-ci/check",
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] in ["pass", "warn", "fail"]

    def test_run_ci_check_with_baseline(self):
        """POST /check uses specified baseline."""
        create_response = client.post(
            "/api/cam/review-ux-ci/baselines",
            json={"baseline_name": "strict-check"},
        )
        baseline_id = create_response.json()["baseline_id"]

        response = client.post(
            "/api/cam/review-ux-ci/check",
            json={"baseline_id": baseline_id},
        )
        assert response.status_code == 200

    def test_list_summaries_endpoint(self):
        """GET /summaries returns list."""
        client.post("/api/cam/review-ux-ci/check", json={})
        client.post("/api/cam/review-ux-ci/check", json={})

        response = client.get("/api/cam/review-ux-ci/summaries")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_latest_summary_endpoint(self):
        """GET /summaries/latest returns latest."""
        client.post("/api/cam/review-ux-ci/check", json={})

        response = client.get("/api/cam/review-ux-ci/summaries/latest")
        assert response.status_code == 200
        data = response.json()
        assert "summary_id" in data

    def test_get_summary_not_found(self):
        """GET /summaries/{id} returns 404 for missing."""
        response = client.get("/api/cam/review-ux-ci/summaries/nonexistent")
        assert response.status_code == 404

    def test_get_ci_report_endpoint(self):
        """GET /report returns report."""
        response = client.get("/api/cam/review-ux-ci/report")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "status" in data["report"]

    def test_get_status_endpoint(self):
        """GET /status returns status summary."""
        response = client.get("/api/cam/review-ux-ci/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "total_baselines" in data["status"]
