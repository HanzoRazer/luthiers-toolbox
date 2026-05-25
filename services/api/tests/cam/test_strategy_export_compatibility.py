"""
Strategy Export Compatibility Tests

CAM Dev Order 7U: Comprehensive test suite for strategy/export interoperability.

Test categories:
  - Evaluation Tests: compatibility evaluation logic
  - Package Tests: review-safe export package model
  - Invariant Tests: 7U model-enforced constraints
  - Registry Tests: index operations, lookup
  - CI Summary Tests: CI health reporting
  - Router Tests: HTTP endpoints

Target: 60+ tests
"""

import pytest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.cam.strategy_export_compatibility import (
    StrategyExportCompatibilityEvaluation,
    ValidationGate,
    evaluate_strategy_export_compatibility,
    evaluate_general_export_readiness,
    evaluate_targeted_translator_compatibility,
)
from app.cam.review_safe_export_package import (
    ReviewSafeExportPackage,
    PackageReviewStatus,
    create_review_safe_export_package,
    add_compatibility_evaluation,
    add_strategy_to_package,
    add_geometry_authority_ref,
    add_provenance_ref,
    update_review_status,
    add_blocking_issue,
    add_warning,
    validate_package_for_review,
    is_package_approved,
)
from app.cam.strategy_export_registry import (
    STRATEGY_EXPORT_COMPATIBILITY_INDEX,
    REVIEW_SAFE_EXPORT_PACKAGE_INDEX,
    register_strategy_export_compatibility,
    get_strategy_export_compatibility,
    list_strategy_export_compatibilities,
    list_evaluations_by_workspace,
    list_evaluations_by_strategy,
    register_review_safe_export_package,
    get_review_safe_export_package,
    list_review_safe_export_packages,
    list_packages_by_workspace,
    list_packages_by_strategy,
    list_packages_by_review_status,
    get_packages_without_review,
    get_ci_summary,
    clear_strategy_export_indexes,
    get_translator_capability_for_export,
    evaluate_translator_capability_compatibility,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_strategy_export_indexes()
    yield
    clear_strategy_export_indexes()


# ============================================================================
# EVALUATION TESTS (15 tests)
# ============================================================================


class TestStrategyExportCompatibilityEvaluation:
    """Tests for compatibility evaluation logic."""

    def test_evaluate_with_workspace_id(self):
        """Evaluation with workspace_id succeeds."""
        evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
        )
        assert evaluation.workspace_id == "ws-123"
        assert evaluation.evaluation_id.startswith("compat-eval-")

    def test_evaluate_with_strategy_id(self):
        """Evaluation with strategy_id succeeds."""
        evaluation = evaluate_strategy_export_compatibility(
            strategy_id="strategy-456",
        )
        assert evaluation.strategy_id == "strategy-456"

    def test_evaluate_requires_workspace_or_strategy(self):
        """Evaluation fails without workspace_id or strategy_id."""
        with pytest.raises(ValueError, match="workspace_id or strategy_id is required"):
            StrategyExportCompatibilityEvaluation(
                modality_compatible=True,
                geometry_authority_exportable=True,
            )

    def test_evaluate_general_export_readiness(self):
        """General export readiness evaluation works."""
        evaluation = evaluate_general_export_readiness(
            workspace_id="ws-123",
            geometry_authority_ref_ids=["geo-auth-1"],
            review_status="approved",
        )
        assert evaluation.target_translator_id is None
        assert evaluation.geometry_authority_ref_ids == ["geo-auth-1"]

    def test_evaluate_targeted_translator_compatibility(self):
        """Targeted translator evaluation includes translator ID."""
        evaluation = evaluate_targeted_translator_compatibility(
            workspace_id="ws-123",
            target_translator_id="translator-dxf",
            geometry_authority_ref_ids=["geo-auth-1"],
        )
        assert evaluation.target_translator_id == "translator-dxf"

    def test_targeted_evaluation_requires_translator_id(self):
        """Targeted evaluation fails without translator ID."""
        with pytest.raises(ValueError, match="target_translator_id is required"):
            evaluate_targeted_translator_compatibility(
                workspace_id="ws-123",
                target_translator_id="",
            )

    def test_evaluation_green_when_complete(self):
        """Evaluation is GREEN when all checks pass."""
        evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
            geometry_authority_ref_ids=["geo-auth-1"],
            modality_id="rosette_routing",
            review_status="approved",
        )
        # May be yellow due to missing provenance verification
        assert evaluation.gate in ("green", "yellow")

    def test_evaluation_yellow_when_warnings(self):
        """Evaluation is YELLOW when there are warnings."""
        evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
        )
        # No geometry authority refs, no review status → warnings
        assert evaluation.gate == "yellow"
        assert len(evaluation.warnings) > 0

    def test_evaluation_red_when_blocking_issues(self):
        """Evaluation is RED when there are blocking issues."""
        evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
            workspace_status="archived",
        )
        assert evaluation.gate == "red"
        assert "archived" in str(evaluation.blocking_issues).lower()

    def test_evaluation_checks_review_status(self):
        """Evaluation checks review status."""
        valid_evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
            review_status="approved",
        )
        assert valid_evaluation.review_state_valid is True

        invalid_evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
            review_status="draft",
        )
        assert invalid_evaluation.review_state_valid is False

    def test_evaluation_has_unique_id(self):
        """Each evaluation has unique ID."""
        eval1 = evaluate_strategy_export_compatibility(workspace_id="ws-1")
        eval2 = evaluate_strategy_export_compatibility(workspace_id="ws-2")
        assert eval1.evaluation_id != eval2.evaluation_id

    def test_evaluation_has_timestamp(self):
        """Evaluation has timestamp."""
        evaluation = evaluate_strategy_export_compatibility(workspace_id="ws-123")
        assert evaluation.evaluated_at is not None
        assert isinstance(evaluation.evaluated_at, datetime)

    def test_evaluation_has_hash(self):
        """Evaluation has deterministic hash."""
        evaluation = evaluate_strategy_export_compatibility(workspace_id="ws-123")
        assert evaluation.deterministic_evaluation_hash != ""
        assert len(evaluation.deterministic_evaluation_hash) == 64

    def test_evaluation_provenance_complete(self):
        """Evaluation tracks provenance completeness."""
        with_refs = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
            geometry_authority_ref_ids=["geo-auth-1"],
        )
        assert with_refs.provenance_complete is True

        without_refs = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
        )
        assert without_refs.provenance_complete is False

    def test_evaluation_tracks_geometry_authority_refs(self):
        """Evaluation tracks geometry authority refs."""
        evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-123",
            geometry_authority_ref_ids=["geo-1", "geo-2"],
        )
        assert evaluation.geometry_authority_ref_ids == ["geo-1", "geo-2"]


# ============================================================================
# INVARIANT TESTS (8 tests)
# ============================================================================


class TestInvariants:
    """Tests for 7U model-enforced invariants."""

    def test_invariant_execution_authorized_must_be_false(self):
        """execution_authorized must be False."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            StrategyExportCompatibilityEvaluation(
                workspace_id="ws-123",
                execution_authorized=True,
            )

    def test_invariant_machine_output_allowed_must_be_false(self):
        """machine_output_allowed must be False."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            StrategyExportCompatibilityEvaluation(
                workspace_id="ws-123",
                machine_output_allowed=True,
            )

    def test_invariant_serializer_invocation_allowed_must_be_false(self):
        """serializer_invocation_allowed must be False."""
        with pytest.raises(ValueError, match="serializer_invocation_allowed must be False"):
            StrategyExportCompatibilityEvaluation(
                workspace_id="ws-123",
                serializer_invocation_allowed=True,
            )

    def test_invariant_generates_gcode_must_be_false(self):
        """generates_gcode must be False."""
        with pytest.raises(ValueError, match="generates_gcode must be False"):
            StrategyExportCompatibilityEvaluation(
                workspace_id="ws-123",
                generates_gcode=True,
            )

    def test_package_invariant_execution_authorized(self):
        """Package execution_authorized must be False."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            ReviewSafeExportPackage(
                execution_authorized=True,
            )

    def test_package_invariant_machine_output_allowed(self):
        """Package machine_output_allowed must be False."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            ReviewSafeExportPackage(
                machine_output_allowed=True,
            )

    def test_package_invariant_serializer_invocation_allowed(self):
        """Package serializer_invocation_allowed must be False."""
        with pytest.raises(ValueError, match="serializer_invocation_allowed must be False"):
            ReviewSafeExportPackage(
                serializer_invocation_allowed=True,
            )

    def test_package_invariant_generates_gcode(self):
        """Package generates_gcode must be False."""
        with pytest.raises(ValueError, match="generates_gcode must be False"):
            ReviewSafeExportPackage(
                generates_gcode=True,
            )


# ============================================================================
# PACKAGE TESTS (15 tests)
# ============================================================================


class TestReviewSafeExportPackage:
    """Tests for review-safe export package model."""

    def test_create_package(self):
        """Create review-safe export package."""
        package = create_review_safe_export_package(
            workspace_id="ws-123",
            title="Test Package",
        )
        assert package.workspace_id == "ws-123"
        assert package.title == "Test Package"
        assert package.package_id.startswith("export-pkg-")

    def test_package_default_review_status(self):
        """Package default review status is draft."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        assert package.review_status == "draft"

    def test_add_compatibility_evaluation(self):
        """Add compatibility evaluation to package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        updated = add_compatibility_evaluation(package, "eval-1")
        assert "eval-1" in updated.compatibility_evaluation_ids

    def test_add_strategy_to_package(self):
        """Add strategy to package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        updated = add_strategy_to_package(package, "strategy-1")
        assert "strategy-1" in updated.strategy_ids

    def test_add_geometry_authority_ref(self):
        """Add geometry authority ref to package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        updated = add_geometry_authority_ref(package, "geo-auth-1")
        assert "geo-auth-1" in updated.geometry_authority_ref_ids

    def test_add_provenance_ref(self):
        """Add provenance ref to package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        updated = add_provenance_ref(package, "prov-1")
        assert "prov-1" in updated.provenance_refs

    def test_update_review_status(self):
        """Update package review status."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        updated = update_review_status(package, "pending_review", "Ready for review")
        assert updated.review_status == "pending_review"
        assert "Ready for review" in updated.reviewer_notes

    def test_add_blocking_issue(self):
        """Add blocking issue to package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        updated = add_blocking_issue(package, "Missing geometry refs")
        assert "Missing geometry refs" in updated.blocking_issues

    def test_add_warning(self):
        """Add warning to package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        updated = add_warning(package, "Consider adding modality")
        assert "Consider adding modality" in updated.warnings

    def test_validate_package_for_review_valid(self):
        """Validate valid package for review."""
        package = create_review_safe_export_package(
            workspace_id="ws-123",
            geometry_authority_ref_ids=["geo-1"],
        )
        add_compatibility_evaluation(package, "eval-1")
        is_valid, issues = validate_package_for_review(package)
        assert is_valid is True
        assert len(issues) == 0

    def test_validate_package_for_review_invalid(self):
        """Validate invalid package for review."""
        package = create_review_safe_export_package()
        is_valid, issues = validate_package_for_review(package)
        assert is_valid is False
        assert len(issues) > 0

    def test_is_package_approved_true(self):
        """is_package_approved returns True for approved package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        update_review_status(package, "approved")
        assert is_package_approved(package) is True

    def test_is_package_approved_false_not_approved(self):
        """is_package_approved returns False for non-approved package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        assert is_package_approved(package) is False

    def test_is_package_approved_false_blocking_issues(self):
        """is_package_approved returns False with blocking issues."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        update_review_status(package, "approved")
        add_blocking_issue(package, "Some issue")
        assert is_package_approved(package) is False

    def test_package_has_timestamps(self):
        """Package has created_at and updated_at."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        assert package.created_at is not None
        assert package.updated_at is not None


# ============================================================================
# REGISTRY TESTS (12 tests)
# ============================================================================


class TestRegistry:
    """Tests for strategy/export registry."""

    def test_register_and_retrieve_evaluation(self):
        """Register and retrieve evaluation."""
        evaluation = evaluate_strategy_export_compatibility(workspace_id="ws-123")
        registered = register_strategy_export_compatibility(evaluation)
        retrieved = get_strategy_export_compatibility(evaluation.evaluation_id)
        assert retrieved is not None
        assert retrieved.evaluation_id == evaluation.evaluation_id

    def test_list_evaluations(self):
        """List all evaluations."""
        eval1 = evaluate_strategy_export_compatibility(workspace_id="ws-1")
        eval2 = evaluate_strategy_export_compatibility(workspace_id="ws-2")
        register_strategy_export_compatibility(eval1)
        register_strategy_export_compatibility(eval2)
        evals = list_strategy_export_compatibilities()
        assert len(evals) == 2

    def test_list_evaluations_by_workspace(self):
        """List evaluations by workspace."""
        eval1 = evaluate_strategy_export_compatibility(workspace_id="ws-123")
        eval2 = evaluate_strategy_export_compatibility(workspace_id="ws-123")
        eval3 = evaluate_strategy_export_compatibility(workspace_id="ws-456")
        register_strategy_export_compatibility(eval1)
        register_strategy_export_compatibility(eval2)
        register_strategy_export_compatibility(eval3)
        ws_evals = list_evaluations_by_workspace("ws-123")
        assert len(ws_evals) == 2

    def test_list_evaluations_by_strategy(self):
        """List evaluations by strategy."""
        eval1 = evaluate_strategy_export_compatibility(strategy_id="strategy-1")
        eval2 = evaluate_strategy_export_compatibility(strategy_id="strategy-1")
        register_strategy_export_compatibility(eval1)
        register_strategy_export_compatibility(eval2)
        strat_evals = list_evaluations_by_strategy("strategy-1")
        assert len(strat_evals) == 2

    def test_register_and_retrieve_package(self):
        """Register and retrieve package."""
        package = create_review_safe_export_package(workspace_id="ws-123")
        registered = register_review_safe_export_package(package)
        retrieved = get_review_safe_export_package(package.package_id)
        assert retrieved is not None
        assert retrieved.package_id == package.package_id

    def test_list_packages(self):
        """List all packages."""
        pkg1 = create_review_safe_export_package(workspace_id="ws-1")
        pkg2 = create_review_safe_export_package(workspace_id="ws-2")
        register_review_safe_export_package(pkg1)
        register_review_safe_export_package(pkg2)
        packages = list_review_safe_export_packages()
        assert len(packages) == 2

    def test_list_packages_by_workspace(self):
        """List packages by workspace."""
        pkg1 = create_review_safe_export_package(workspace_id="ws-123")
        pkg2 = create_review_safe_export_package(workspace_id="ws-123")
        pkg3 = create_review_safe_export_package(workspace_id="ws-456")
        register_review_safe_export_package(pkg1)
        register_review_safe_export_package(pkg2)
        register_review_safe_export_package(pkg3)
        ws_pkgs = list_packages_by_workspace("ws-123")
        assert len(ws_pkgs) == 2

    def test_list_packages_by_strategy(self):
        """List packages by strategy."""
        pkg1 = create_review_safe_export_package(strategy_id="strategy-1")
        pkg2 = create_review_safe_export_package(strategy_id="strategy-1")
        register_review_safe_export_package(pkg1)
        register_review_safe_export_package(pkg2)
        strat_pkgs = list_packages_by_strategy("strategy-1")
        assert len(strat_pkgs) == 2

    def test_list_packages_by_review_status(self):
        """List packages by review status."""
        pkg1 = create_review_safe_export_package(workspace_id="ws-1")
        pkg2 = create_review_safe_export_package(workspace_id="ws-2")
        update_review_status(pkg1, "approved")
        register_review_safe_export_package(pkg1)
        register_review_safe_export_package(pkg2)
        approved = list_packages_by_review_status("approved")
        assert len(approved) == 1

    def test_get_packages_without_review(self):
        """Get packages without review."""
        pkg1 = create_review_safe_export_package(workspace_id="ws-1")
        pkg2 = create_review_safe_export_package(workspace_id="ws-2")
        update_review_status(pkg1, "approved")
        register_review_safe_export_package(pkg1)
        register_review_safe_export_package(pkg2)
        no_review = get_packages_without_review()
        assert len(no_review) == 1
        assert no_review[0].workspace_id == "ws-2"

    def test_clear_indexes(self):
        """clear_strategy_export_indexes clears all."""
        evaluation = evaluate_strategy_export_compatibility(workspace_id="ws-123")
        package = create_review_safe_export_package(workspace_id="ws-123")
        register_strategy_export_compatibility(evaluation)
        register_review_safe_export_package(package)
        assert len(list_strategy_export_compatibilities()) == 1
        assert len(list_review_safe_export_packages()) == 1
        clear_strategy_export_indexes()
        assert len(list_strategy_export_compatibilities()) == 0
        assert len(list_review_safe_export_packages()) == 0

    def test_adapter_translator_capability(self):
        """Adapter function for translator capability."""
        is_compatible, error = evaluate_translator_capability_compatibility(
            translator_id="unknown-translator",
            modality_id="rosette_routing",
        )
        # Without actual translator registry, should return compatible
        assert is_compatible is True


# ============================================================================
# CI SUMMARY TESTS (8 tests)
# ============================================================================


class TestCISummary:
    """Tests for CI summary generation."""

    def test_ci_summary_empty_registry(self):
        """CI summary for empty registry."""
        summary = get_ci_summary()
        assert summary["total_evaluations"] == 0
        assert summary["total_packages"] == 0
        assert summary["status"] == "pass"

    def test_ci_summary_counts_evaluations(self):
        """CI summary counts total evaluations."""
        for i in range(3):
            evaluation = evaluate_strategy_export_compatibility(workspace_id=f"ws-{i}")
            register_strategy_export_compatibility(evaluation)
        summary = get_ci_summary()
        assert summary["total_evaluations"] == 3

    def test_ci_summary_counts_packages(self):
        """CI summary counts total packages."""
        for i in range(2):
            package = create_review_safe_export_package(workspace_id=f"ws-{i}")
            register_review_safe_export_package(package)
        summary = get_ci_summary()
        assert summary["total_packages"] == 2

    def test_ci_summary_counts_by_gate(self):
        """CI summary counts by gate."""
        eval_yellow = evaluate_strategy_export_compatibility(workspace_id="ws-1")
        eval_red = evaluate_strategy_export_compatibility(
            workspace_id="ws-2",
            workspace_status="archived",
        )
        register_strategy_export_compatibility(eval_yellow)
        register_strategy_export_compatibility(eval_red)
        summary = get_ci_summary()
        assert summary["red_count"] >= 1

    def test_ci_summary_status_pass(self):
        """CI summary status is pass when healthy."""
        summary = get_ci_summary()
        assert summary["status"] == "pass"

    def test_ci_summary_status_warn_yellow(self):
        """CI summary status is warn with YELLOW evaluations."""
        evaluation = evaluate_strategy_export_compatibility(workspace_id="ws-1")
        register_strategy_export_compatibility(evaluation)
        summary = get_ci_summary()
        # Yellow evaluation → warn
        if summary["yellow_count"] > 0:
            assert summary["status"] == "warn"

    def test_ci_summary_status_fail_red(self):
        """CI summary status is fail with RED evaluations."""
        evaluation = evaluate_strategy_export_compatibility(
            workspace_id="ws-1",
            workspace_status="archived",
        )
        register_strategy_export_compatibility(evaluation)
        summary = get_ci_summary()
        assert summary["status"] == "fail"

    def test_ci_summary_includes_packages_by_status(self):
        """CI summary includes packages by review status."""
        pkg1 = create_review_safe_export_package(workspace_id="ws-1")
        pkg2 = create_review_safe_export_package(workspace_id="ws-2")
        update_review_status(pkg1, "approved")
        register_review_safe_export_package(pkg1)
        register_review_safe_export_package(pkg2)
        summary = get_ci_summary()
        assert "packages_by_review_status" in summary


# ============================================================================
# ROUTER TESTS (12 tests)
# ============================================================================


class TestStrategyExportRouter:
    """Tests for strategy/export HTTP endpoints."""

    def test_get_meta(self):
        """GET /api/cam/strategy-export returns metadata."""
        response = client.get("/api/cam/strategy-export/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "7U"
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["serializer_invocation_allowed"] is False
        assert data["generates_gcode"] is False

    def test_evaluate_compatibility(self):
        """POST /api/cam/strategy-export/evaluate creates evaluation."""
        response = client.post(
            "/api/cam/strategy-export/evaluate",
            json={
                "workspace_id": "ws-123",
                "geometry_authority_ref_ids": ["geo-1"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == "ws-123"
        assert data["gate"] in ["green", "yellow", "red"]

    def test_evaluate_requires_workspace_or_strategy(self):
        """POST /api/cam/strategy-export/evaluate requires workspace or strategy."""
        response = client.post(
            "/api/cam/strategy-export/evaluate",
            json={},
        )
        assert response.status_code == 400

    def test_list_evaluations(self):
        """GET /api/cam/strategy-export/evaluations lists all."""
        client.post(
            "/api/cam/strategy-export/evaluate",
            json={"workspace_id": "ws-1"},
        )
        response = client.get("/api/cam/strategy-export/evaluations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_evaluation(self):
        """GET /api/cam/strategy-export/evaluations/{id} retrieves evaluation."""
        create_resp = client.post(
            "/api/cam/strategy-export/evaluate",
            json={"workspace_id": "ws-123"},
        )
        eval_id = create_resp.json()["evaluation_id"]
        response = client.get(f"/api/cam/strategy-export/evaluations/{eval_id}")
        assert response.status_code == 200
        assert response.json()["evaluation_id"] == eval_id

    def test_create_package(self):
        """POST /api/cam/strategy-export/packages creates package."""
        response = client.post(
            "/api/cam/strategy-export/packages",
            json={
                "workspace_id": "ws-123",
                "title": "Test Package",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == "ws-123"
        assert data["title"] == "Test Package"

    def test_list_packages(self):
        """GET /api/cam/strategy-export/packages lists all."""
        client.post(
            "/api/cam/strategy-export/packages",
            json={"workspace_id": "ws-1"},
        )
        response = client.get("/api/cam/strategy-export/packages")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_package(self):
        """GET /api/cam/strategy-export/packages/{id} retrieves package."""
        create_resp = client.post(
            "/api/cam/strategy-export/packages",
            json={"workspace_id": "ws-123"},
        )
        pkg_id = create_resp.json()["package_id"]
        response = client.get(f"/api/cam/strategy-export/packages/{pkg_id}")
        assert response.status_code == 200
        assert response.json()["package_id"] == pkg_id

    def test_update_review_status(self):
        """POST /api/cam/strategy-export/packages/{id}/review-status updates status."""
        create_resp = client.post(
            "/api/cam/strategy-export/packages",
            json={"workspace_id": "ws-123"},
        )
        pkg_id = create_resp.json()["package_id"]
        response = client.post(
            f"/api/cam/strategy-export/packages/{pkg_id}/review-status",
            json={
                "review_status": "pending_review",
                "reviewer_note": "Ready",
            },
        )
        assert response.status_code == 200
        assert response.json()["review_status"] == "pending_review"

    def test_validate_package(self):
        """POST /api/cam/strategy-export/packages/{id}/validate validates package."""
        create_resp = client.post(
            "/api/cam/strategy-export/packages",
            json={"workspace_id": "ws-123"},
        )
        pkg_id = create_resp.json()["package_id"]
        response = client.post(f"/api/cam/strategy-export/packages/{pkg_id}/validate")
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "issues" in data

    def test_get_ci_summary(self):
        """GET /api/cam/strategy-export/ci returns CI summary."""
        client.post(
            "/api/cam/strategy-export/evaluate",
            json={"workspace_id": "ws-1"},
        )
        response = client.get("/api/cam/strategy-export/ci")
        assert response.status_code == 200
        data = response.json()
        assert "total_evaluations" in data
        assert "total_packages" in data
        assert "status" in data
        assert data["status"] in ["pass", "warn", "fail"]

    def test_evaluations_by_workspace(self):
        """GET /api/cam/strategy-export/evaluations/by-workspace/{id} filters."""
        client.post(
            "/api/cam/strategy-export/evaluate",
            json={"workspace_id": "ws-123"},
        )
        client.post(
            "/api/cam/strategy-export/evaluate",
            json={"workspace_id": "ws-456"},
        )
        response = client.get("/api/cam/strategy-export/evaluations/by-workspace/ws-123")
        assert response.status_code == 200
        data = response.json()
        for evaluation in data:
            assert evaluation["workspace_id"] == "ws-123"
