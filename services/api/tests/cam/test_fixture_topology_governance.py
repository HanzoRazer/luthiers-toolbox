"""
Tests for CAM Dev Order 7V — Fixture & Topology Intelligence Governance.

Tests cover:
  - Fixture topology constraint creation and validation
  - Topology continuity evaluation
  - Fixture/strategy compatibility
  - Review-safe fixture packages
  - 7V invariant enforcement (no execution, no machine output, no geometry mutation)
  - Registry operations
  - CI summary generation
  - Golden fixture adapter
  - Risk detection
"""

import pytest
from datetime import datetime, timezone

from app.cam.fixture_topology_constraints import (
    FixtureTopologyConstraint,
    FixtureConstraintCategory,
    ConstraintSeverity,
    create_fixture_constraint,
    create_constraint_from_golden_fixture,
    validate_fixture_constraint,
)
from app.cam.topology_continuity_evaluation import (
    TopologyContinuityEvaluation,
    TopologyRiskCategory,
    TopologyRiskDeclaration,
    evaluate_topology_continuity,
    validate_topology_evaluation,
    detect_thin_bridges,
    detect_unsupported_spans,
    detect_fragmented_regions,
    detect_clamp_interference,
)
from app.cam.fixture_strategy_compatibility import (
    FixtureStrategyCompatibilityEvaluation,
    evaluate_fixture_strategy_compatibility,
    validate_fixture_strategy_compatibility,
)
from app.cam.review_safe_fixture_package import (
    ReviewSafeFixturePackage,
    PackageReviewStatus,
    create_review_safe_fixture_package,
    add_fixture_constraint_to_package,
    add_topology_evaluation_to_package,
    add_compatibility_evaluation_to_package,
    add_geometry_authority_ref_to_package,
    update_fixture_package_review_status,
    add_blocking_issue_to_package,
    add_warning_to_package,
    mark_topology_risks_present,
    mark_fixture_conflicts_present,
    validate_review_safe_fixture_package,
    is_fixture_package_approved,
)
from app.cam.fixture_topology_registry import (
    register_fixture_constraint,
    get_fixture_constraint,
    list_fixture_constraints,
    list_constraints_by_category,
    register_topology_evaluation,
    get_topology_evaluation,
    list_topology_evaluations,
    list_topology_evaluations_by_geometry_ref,
    register_fixture_strategy_compatibility,
    get_fixture_strategy_compatibility,
    list_fixture_strategy_compatibilities,
    list_compatibilities_by_strategy,
    register_review_safe_fixture_package,
    get_review_safe_fixture_package,
    list_review_safe_fixture_packages,
    list_fixture_packages_by_workspace,
    list_fixture_packages_by_review_status,
    get_ci_summary,
    clear_fixture_topology_indexes,
)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_fixture_topology_indexes()
    yield
    clear_fixture_topology_indexes()


class TestFixtureTopologyConstraint:
    """Tests for FixtureTopologyConstraint model."""

    def test_create_constraint_with_defaults(self):
        """Test creating a constraint with default values."""
        constraint = FixtureTopologyConstraint(
            constraint_category="clamp_zone",
        )
        assert constraint.constraint_id.startswith("fix-constraint-")
        assert constraint.constraint_category == "clamp_zone"
        assert constraint.severity == "medium"
        assert constraint.execution_authorized is False
        assert constraint.machine_output_allowed is False
        assert constraint.may_modify_geometry is False

    def test_create_constraint_with_all_fields(self):
        """Test creating a constraint with all fields populated."""
        constraint = FixtureTopologyConstraint(
            constraint_category="keepout_zone",
            description="Avoid bracing area",
            geometry_authority_ref_id="geo-auth-123",
            workspace_id="ws-456",
            strategy_id="strategy-789",
            affected_regions=["upper_bout", "lower_bout"],
            severity="critical",
            min_x_mm=0.0,
            max_x_mm=100.0,
            min_y_mm=0.0,
            max_y_mm=200.0,
            height_mm=25.0,
        )
        assert constraint.constraint_category == "keepout_zone"
        assert constraint.description == "Avoid bracing area"
        assert constraint.severity == "critical"
        assert constraint.max_x_mm == 100.0

    def test_constraint_7v_invariant_execution_authorized(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            FixtureTopologyConstraint(
                constraint_category="clamp_zone",
                execution_authorized=True,
            )

    def test_constraint_7v_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            FixtureTopologyConstraint(
                constraint_category="clamp_zone",
                machine_output_allowed=True,
            )

    def test_constraint_7v_invariant_geometry_mutation(self):
        """Test that may_modify_geometry=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            FixtureTopologyConstraint(
                constraint_category="clamp_zone",
                may_modify_geometry=True,
            )

    def test_constraint_compute_hash(self):
        """Test that constraint hash is deterministic."""
        constraint = FixtureTopologyConstraint(
            constraint_category="vacuum_hold",
            description="Test constraint",
        )
        hash1 = constraint.compute_hash()
        hash2 = constraint.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_create_fixture_constraint_function(self):
        """Test create_fixture_constraint helper function."""
        constraint = create_fixture_constraint(
            constraint_category="bridge_support",
            description="Bridge support constraint",
            severity="high",
            min_x_mm=50.0,
            max_x_mm=150.0,
        )
        assert constraint.constraint_category == "bridge_support"
        assert constraint.severity == "high"
        assert constraint.min_x_mm == 50.0
        assert constraint.max_x_mm == 150.0

    def test_validate_fixture_constraint_valid(self):
        """Test validation of valid constraint."""
        constraint = create_fixture_constraint(
            constraint_category="clamp_zone",
            description="Valid constraint",
            affected_regions=["upper_bout"],
        )
        is_valid, issues = validate_fixture_constraint(constraint)
        assert is_valid is True
        assert len(issues) == 0

    def test_validate_fixture_constraint_no_description(self):
        """Test validation warns about missing description."""
        constraint = create_fixture_constraint(
            constraint_category="clamp_zone",
        )
        is_valid, issues = validate_fixture_constraint(constraint)
        assert "description" in str(issues).lower()

    def test_all_constraint_categories(self):
        """Test that all constraint categories work."""
        categories: list[FixtureConstraintCategory] = [
            "clamp_zone",
            "keepout_zone",
            "vacuum_hold",
            "bridge_support",
            "registration_constraint",
            "edge_clearance",
            "tool_access_constraint",
            "fragility_constraint",
        ]
        for category in categories:
            constraint = create_fixture_constraint(constraint_category=category)
            assert constraint.constraint_category == category

    def test_all_constraint_severities(self):
        """Test that all severity levels work."""
        severities: list[ConstraintSeverity] = ["low", "medium", "high", "critical"]
        for severity in severities:
            constraint = create_fixture_constraint(
                constraint_category="clamp_zone",
                severity=severity,
            )
            assert constraint.severity == severity

    def test_constraint_bounds_overlap(self):
        """Test bounds overlap detection."""
        constraint = FixtureTopologyConstraint(
            constraint_category="clamp_zone",
            min_x_mm=0.0,
            max_x_mm=100.0,
            min_y_mm=0.0,
            max_y_mm=100.0,
        )
        assert constraint.bounds_overlap(50, 150, 50, 150) is True
        assert constraint.bounds_overlap(200, 300, 200, 300) is False

    def test_constraint_region_overlaps(self):
        """Test region overlap detection."""
        constraint = FixtureTopologyConstraint(
            constraint_category="clamp_zone",
            affected_regions=["upper_bout", "waist"],
        )
        assert constraint.region_overlaps("upper_bout") is True
        assert constraint.region_overlaps("lower_bout") is False


class TestGoldenFixtureAdapter:
    """Tests for golden fixture adapter."""

    def test_create_constraint_from_nonexistent_fixture(self):
        """Test that nonexistent fixture returns None."""
        result = create_constraint_from_golden_fixture(
            fixture_id="nonexistent-fixture",
        )
        assert result is None

    def test_create_constraint_from_golden_fixture_with_ids(self):
        """Test creating constraints with workspace and strategy IDs."""
        result = create_constraint_from_golden_fixture(
            fixture_id="any-fixture",
            workspace_id="ws-123",
            strategy_id="strategy-456",
        )
        assert result is None


class TestTopologyContinuityEvaluation:
    """Tests for TopologyContinuityEvaluation model."""

    def test_create_evaluation_with_defaults(self):
        """Test creating evaluation with defaults."""
        evaluation = TopologyContinuityEvaluation(
            geometry_authority_ref_id="geo-auth-123",
        )
        assert evaluation.evaluation_id.startswith("topo-eval-")
        assert evaluation.geometry_authority_ref_id == "geo-auth-123"
        assert evaluation.gate == "green"
        assert evaluation.execution_authorized is False
        assert evaluation.machine_output_allowed is False
        assert evaluation.geometry_mutation_attempted is False

    def test_evaluation_7v_invariant_execution(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                execution_authorized=True,
            )

    def test_evaluation_7v_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                machine_output_allowed=True,
            )

    def test_evaluation_7v_invariant_geometry_mutation(self):
        """Test that geometry_mutation_attempted=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                geometry_mutation_attempted=True,
            )

    def test_evaluation_7v_invariant_auto_correction(self):
        """Test that auto_correction_attempted=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                auto_correction_attempted=True,
            )

    def test_evaluation_compute_hash(self):
        """Test evaluation hash is deterministic."""
        evaluation = TopologyContinuityEvaluation(
            geometry_authority_ref_id="geo-auth-123",
        )
        hash1 = evaluation.compute_hash()
        hash2 = evaluation.compute_hash()
        assert hash1 == hash2

    def test_evaluate_topology_continuity_green(self):
        """Test evaluation with no declared risks."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
        )
        assert evaluation.gate == "green"

    def test_evaluate_topology_continuity_yellow_thin_bridges(self):
        """Test evaluation with declared thin bridges."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
            declared_thin_bridges=True,
        )
        assert evaluation.thin_bridges_detected is True
        assert evaluation.gate == "yellow"
        assert "thin_bridge" in evaluation.topology_risks

    def test_evaluate_topology_continuity_red_fragmented(self):
        """Test evaluation with declared fragmented regions."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
            declared_fragmented_regions=True,
        )
        assert evaluation.fragmented_regions_detected is True
        assert evaluation.gate == "red"
        assert "fragmented_region" in evaluation.topology_risks

    def test_evaluate_topology_continuity_with_clamp_interference(self):
        """Test evaluation with declared clamp interference."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
            declared_clamp_interference=True,
        )
        assert evaluation.clamp_interference_detected is True
        assert evaluation.gate == "red"
        assert "clamp_interference" in evaluation.topology_risks

    def test_evaluate_topology_with_risk_declarations(self):
        """Test evaluation with TopologyRiskDeclaration list."""
        risk = TopologyRiskDeclaration(
            risk_category="thin_bridge",
            severity="high",
            description="Bridge at waist is too thin",
            region_label="waist",
        )
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
            risk_declarations=[risk],
        )
        assert len(evaluation.risk_declarations) == 1
        assert evaluation.risk_declarations[0].risk_category == "thin_bridge"

    def test_evaluate_topology_critical_risk_declaration(self):
        """Test evaluation with critical risk declaration."""
        risk = TopologyRiskDeclaration(
            risk_category="continuity_break",
            severity="critical",
            description="Critical continuity break",
        )
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
            risk_declarations=[risk],
        )
        assert evaluation.gate == "red"

    def test_validate_topology_evaluation_valid(self):
        """Test validation of valid evaluation."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
        )
        is_valid, issues = validate_topology_evaluation(evaluation)
        assert is_valid is True
        assert len(issues) == 0


class TestTopologyRiskDeclaration:
    """Tests for TopologyRiskDeclaration model."""

    def test_create_risk_declaration(self):
        """Test creating a risk declaration."""
        risk = TopologyRiskDeclaration(
            risk_category="unsupported_span",
            severity="medium",
            description="Long unsupported span in upper bout",
        )
        assert risk.risk_category == "unsupported_span"
        assert risk.severity == "medium"

    def test_all_risk_categories(self):
        """Test all risk categories work."""
        categories: list[TopologyRiskCategory] = [
            "thin_bridge",
            "unsupported_span",
            "fragmented_region",
            "clamp_interference",
            "edge_instability",
            "registration_instability",
            "fixture_conflict",
            "continuity_break",
        ]
        for category in categories:
            risk = TopologyRiskDeclaration(risk_category=category)
            assert risk.risk_category == category

    def test_risk_declaration_with_region_label(self):
        """Test risk declaration with region label."""
        risk = TopologyRiskDeclaration(
            risk_category="thin_bridge",
            region_label="waist",
        )
        assert risk.region_label == "waist"


class TestRiskDetectionFunctions:
    """Tests for risk detection functions."""

    def test_detect_thin_bridges_with_declared_regions(self):
        """Test thin bridge detection with declared regions."""
        detected, regions = detect_thin_bridges(
            declared_regions=["waist", "cutaway"],
        )
        assert detected is True
        assert "waist" in regions

    def test_detect_thin_bridges_without_declared_regions(self):
        """Test thin bridge detection without declared regions."""
        detected, regions = detect_thin_bridges()
        assert detected is False
        assert len(regions) == 0

    def test_detect_unsupported_spans_with_declared_regions(self):
        """Test unsupported spans detection with declared regions."""
        detected, regions = detect_unsupported_spans(
            declared_regions=["upper_bout"],
        )
        assert detected is True
        assert "upper_bout" in regions

    def test_detect_fragmented_regions_with_declared(self):
        """Test fragmented regions detection."""
        detected, regions = detect_fragmented_regions(
            declared_regions=["fragment_1"],
        )
        assert detected is True

    def test_detect_clamp_interference_with_overlap(self):
        """Test clamp interference detection with overlap."""
        detected, overlapping = detect_clamp_interference(
            constraint_region_labels=["clamp_area", "waist"],
            workpiece_region_labels=["waist", "lower_bout"],
        )
        assert detected is True
        assert "waist" in overlapping

    def test_detect_clamp_interference_no_overlap(self):
        """Test clamp interference detection without overlap."""
        detected, overlapping = detect_clamp_interference(
            constraint_region_labels=["clamp_area"],
            workpiece_region_labels=["lower_bout"],
        )
        assert detected is False
        assert len(overlapping) == 0


class TestFixtureStrategyCompatibility:
    """Tests for FixtureStrategyCompatibilityEvaluation model."""

    def test_create_compatibility_with_defaults(self):
        """Test creating compatibility evaluation with defaults."""
        evaluation = FixtureStrategyCompatibilityEvaluation(
            strategy_id="strategy-123",
        )
        assert evaluation.evaluation_id.startswith("fix-compat-")
        assert evaluation.strategy_id == "strategy-123"
        assert evaluation.gate == "green"
        assert evaluation.execution_authorized is False
        assert evaluation.machine_output_allowed is False

    def test_compatibility_7v_invariant_execution(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            FixtureStrategyCompatibilityEvaluation(
                strategy_id="strategy-123",
                execution_authorized=True,
            )

    def test_compatibility_7v_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            FixtureStrategyCompatibilityEvaluation(
                strategy_id="strategy-123",
                machine_output_allowed=True,
            )

    def test_compatibility_7v_invariant_fixture_execution(self):
        """Test that fixture_execution_present=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            FixtureStrategyCompatibilityEvaluation(
                strategy_id="strategy-123",
                fixture_execution_present=True,
            )

    def test_compatibility_compute_hash(self):
        """Test compatibility hash is deterministic."""
        evaluation = FixtureStrategyCompatibilityEvaluation(
            strategy_id="strategy-123",
        )
        hash1 = evaluation.compute_hash()
        hash2 = evaluation.compute_hash()
        assert hash1 == hash2

    def test_evaluate_fixture_strategy_compatibility_basic(self):
        """Test basic compatibility evaluation."""
        evaluation = evaluate_fixture_strategy_compatibility(
            strategy_id="strategy-123",
        )
        assert evaluation.strategy_id == "strategy-123"
        assert evaluation.gate in ("green", "yellow", "red")

    def test_evaluate_compatibility_with_constraints(self):
        """Test compatibility evaluation with fixture constraints."""
        constraint = create_fixture_constraint(
            constraint_category="clamp_zone",
        )
        evaluation = evaluate_fixture_strategy_compatibility(
            strategy_id="strategy-123",
            fixture_constraints=[constraint],
        )
        assert len(evaluation.fixture_constraint_ids) == 1

    def test_evaluate_compatibility_with_declared_conflicts(self):
        """Test compatibility evaluation with declared conflicts."""
        evaluation = evaluate_fixture_strategy_compatibility(
            strategy_id="strategy-123",
            declared_clamp_conflicts=True,
            declared_keepout_violations=True,
        )
        assert evaluation.clamp_conflicts_detected is True
        assert evaluation.keepout_violations_detected is True
        assert evaluation.gate == "red"

    def test_evaluate_compatibility_critical_constraint(self):
        """Test compatibility evaluation with critical constraint."""
        constraint = create_fixture_constraint(
            constraint_category="clamp_zone",
            severity="critical",
            description="Critical clamp zone",
        )
        evaluation = evaluate_fixture_strategy_compatibility(
            strategy_id="strategy-123",
            fixture_constraints=[constraint],
        )
        assert evaluation.gate == "red"
        assert "clamp_zone" in evaluation.incompatible_fixture_categories

    def test_evaluate_compatibility_with_operation_family(self):
        """Test compatibility evaluation with operation family hints."""
        evaluation = evaluate_fixture_strategy_compatibility(
            strategy_id="strategy-123",
            strategy_operation_family="rosette",
        )
        assert len(evaluation.warnings) > 0

    def test_validate_fixture_strategy_compatibility_valid(self):
        """Test validation of valid compatibility evaluation."""
        evaluation = evaluate_fixture_strategy_compatibility(
            strategy_id="strategy-123",
        )
        is_valid, issues = validate_fixture_strategy_compatibility(evaluation)
        assert is_valid is True


class TestReviewSafeFixturePackage:
    """Tests for ReviewSafeFixturePackage model."""

    def test_create_package_with_defaults(self):
        """Test creating package with defaults."""
        package = ReviewSafeFixturePackage(
            workspace_id="ws-123",
        )
        assert package.package_id.startswith("fix-pkg-")
        assert package.workspace_id == "ws-123"
        assert package.review_status == "draft"
        assert package.executable_payload_present is False
        assert package.execution_authorized is False
        assert package.machine_output_allowed is False

    def test_package_7v_invariant_executable_payload(self):
        """Test that executable_payload_present=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            ReviewSafeFixturePackage(
                workspace_id="ws-123",
                executable_payload_present=True,
            )

    def test_package_7v_invariant_execution(self):
        """Test that execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            ReviewSafeFixturePackage(
                workspace_id="ws-123",
                execution_authorized=True,
            )

    def test_package_7v_invariant_machine_output(self):
        """Test that machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError, match="7V invariant violation"):
            ReviewSafeFixturePackage(
                workspace_id="ws-123",
                machine_output_allowed=True,
            )

    def test_create_review_safe_fixture_package_function(self):
        """Test create_review_safe_fixture_package helper function."""
        package = create_review_safe_fixture_package(
            workspace_id="ws-123",
            strategy_id="strategy-456",
            title="Test Package",
            description="Test description",
        )
        assert package.workspace_id == "ws-123"
        assert package.strategy_id == "strategy-456"
        assert package.title == "Test Package"

    def test_add_fixture_constraint_to_package(self):
        """Test adding fixture constraint to package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = add_fixture_constraint_to_package(package, "fix-constraint-123")
        assert "fix-constraint-123" in updated.fixture_constraint_ids

    def test_add_topology_evaluation_to_package(self):
        """Test adding topology evaluation to package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = add_topology_evaluation_to_package(package, "topo-eval-123")
        assert "topo-eval-123" in updated.topology_evaluation_ids

    def test_add_compatibility_evaluation_to_package(self):
        """Test adding compatibility evaluation to package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = add_compatibility_evaluation_to_package(package, "fix-compat-123")
        assert "fix-compat-123" in updated.compatibility_evaluation_ids

    def test_add_geometry_authority_ref_to_package(self):
        """Test adding geometry authority ref to package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = add_geometry_authority_ref_to_package(package, "geo-auth-123")
        assert "geo-auth-123" in updated.geometry_authority_ref_ids

    def test_update_fixture_package_review_status(self):
        """Test updating package review status."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = update_fixture_package_review_status(
            package, "pending_review", "Ready for review"
        )
        assert updated.review_status == "pending_review"
        assert "Ready for review" in updated.reviewer_notes

    def test_add_blocking_issue_to_package(self):
        """Test adding blocking issue to package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = add_blocking_issue_to_package(package, "Critical issue")
        assert "Critical issue" in updated.blocking_issues

    def test_add_warning_to_package(self):
        """Test adding warning to package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = add_warning_to_package(package, "Minor warning")
        assert "Minor warning" in updated.warnings

    def test_mark_topology_risks_present(self):
        """Test marking topology risks present."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = mark_topology_risks_present(package)
        assert updated.topology_risks_present is True

    def test_mark_fixture_conflicts_present(self):
        """Test marking fixture conflicts present."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        updated = mark_fixture_conflicts_present(package)
        assert updated.fixture_conflicts_present is True

    def test_validate_review_safe_fixture_package_valid(self):
        """Test validation of valid package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        add_fixture_constraint_to_package(package, "fix-constraint-123")
        is_valid, issues = validate_review_safe_fixture_package(package)
        assert is_valid is True

    def test_validate_review_safe_fixture_package_no_refs(self):
        """Test validation fails without constraints or evaluations."""
        package = create_review_safe_fixture_package(strategy_id="strategy-123")
        is_valid, issues = validate_review_safe_fixture_package(package)
        assert "no fixture constraints or topology evaluations" in str(issues).lower()

    def test_is_fixture_package_approved_true(self):
        """Test is_fixture_package_approved returns True when approved."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        package.review_status = "approved"
        assert is_fixture_package_approved(package) is True

    def test_is_fixture_package_approved_false_with_issues(self):
        """Test is_fixture_package_approved returns False with blocking issues."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        package.review_status = "approved"
        add_blocking_issue_to_package(package, "Issue")
        assert is_fixture_package_approved(package) is False

    def test_all_review_statuses(self):
        """Test all review statuses work."""
        statuses: list[PackageReviewStatus] = [
            "draft",
            "pending_review",
            "under_review",
            "approved_for_export_review",
            "approved",
            "rejected",
            "deferred",
        ]
        for status in statuses:
            package = create_review_safe_fixture_package(workspace_id="ws-123")
            updated = update_fixture_package_review_status(package, status)
            assert updated.review_status == status

    def test_package_hash_changes_on_update(self):
        """Test that package hash changes when state changes."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        hash1 = package.deterministic_package_hash
        add_fixture_constraint_to_package(package, "fix-constraint-123")
        hash2 = package.deterministic_package_hash
        assert hash1 != hash2


class TestFixtureTopologyRegistry:
    """Tests for fixture topology registry operations."""

    def test_register_fixture_constraint(self):
        """Test registering a fixture constraint."""
        constraint = create_fixture_constraint(constraint_category="clamp_zone")
        registered = register_fixture_constraint(constraint)
        assert registered.deterministic_constraint_hash != ""
        assert get_fixture_constraint(registered.constraint_id) is not None

    def test_get_nonexistent_constraint(self):
        """Test getting nonexistent constraint returns None."""
        result = get_fixture_constraint("nonexistent-id")
        assert result is None

    def test_list_fixture_constraints(self):
        """Test listing all fixture constraints."""
        c1 = create_fixture_constraint(constraint_category="clamp_zone")
        c2 = create_fixture_constraint(constraint_category="keepout_zone")
        register_fixture_constraint(c1)
        register_fixture_constraint(c2)
        all_constraints = list_fixture_constraints()
        assert len(all_constraints) == 2

    def test_list_constraints_by_category(self):
        """Test listing constraints by category."""
        c1 = create_fixture_constraint(constraint_category="clamp_zone")
        c2 = create_fixture_constraint(constraint_category="clamp_zone")
        c3 = create_fixture_constraint(constraint_category="keepout_zone")
        register_fixture_constraint(c1)
        register_fixture_constraint(c2)
        register_fixture_constraint(c3)
        clamp_constraints = list_constraints_by_category("clamp_zone")
        assert len(clamp_constraints) == 2

    def test_register_topology_evaluation(self):
        """Test registering a topology evaluation."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
        )
        registered = register_topology_evaluation(evaluation)
        assert registered.deterministic_topology_hash != ""
        assert get_topology_evaluation(registered.evaluation_id) is not None

    def test_get_nonexistent_evaluation(self):
        """Test getting nonexistent evaluation returns None."""
        result = get_topology_evaluation("nonexistent-id")
        assert result is None

    def test_list_topology_evaluations(self):
        """Test listing all topology evaluations."""
        e1 = evaluate_topology_continuity(geometry_authority_ref_id="geo-auth-1")
        e2 = evaluate_topology_continuity(geometry_authority_ref_id="geo-auth-2")
        register_topology_evaluation(e1)
        register_topology_evaluation(e2)
        all_evaluations = list_topology_evaluations()
        assert len(all_evaluations) == 2

    def test_list_topology_evaluations_by_geometry_ref(self):
        """Test listing topology evaluations by geometry ref."""
        e1 = evaluate_topology_continuity(geometry_authority_ref_id="geo-auth-123")
        e2 = evaluate_topology_continuity(geometry_authority_ref_id="geo-auth-123")
        e3 = evaluate_topology_continuity(geometry_authority_ref_id="geo-auth-456")
        register_topology_evaluation(e1)
        register_topology_evaluation(e2)
        register_topology_evaluation(e3)
        ref_evaluations = list_topology_evaluations_by_geometry_ref("geo-auth-123")
        assert len(ref_evaluations) == 2

    def test_register_fixture_strategy_compatibility(self):
        """Test registering a compatibility evaluation."""
        evaluation = evaluate_fixture_strategy_compatibility(
            strategy_id="strategy-123",
        )
        registered = register_fixture_strategy_compatibility(evaluation)
        assert registered.deterministic_compatibility_hash != ""
        assert get_fixture_strategy_compatibility(registered.evaluation_id) is not None

    def test_get_nonexistent_compatibility(self):
        """Test getting nonexistent compatibility returns None."""
        result = get_fixture_strategy_compatibility("nonexistent-id")
        assert result is None

    def test_list_fixture_strategy_compatibilities(self):
        """Test listing all compatibility evaluations."""
        e1 = evaluate_fixture_strategy_compatibility(strategy_id="strategy-1")
        e2 = evaluate_fixture_strategy_compatibility(strategy_id="strategy-2")
        register_fixture_strategy_compatibility(e1)
        register_fixture_strategy_compatibility(e2)
        all_compat = list_fixture_strategy_compatibilities()
        assert len(all_compat) == 2

    def test_list_compatibilities_by_strategy(self):
        """Test listing compatibilities by strategy."""
        e1 = evaluate_fixture_strategy_compatibility(strategy_id="strategy-123")
        e2 = evaluate_fixture_strategy_compatibility(strategy_id="strategy-123")
        e3 = evaluate_fixture_strategy_compatibility(strategy_id="strategy-456")
        register_fixture_strategy_compatibility(e1)
        register_fixture_strategy_compatibility(e2)
        register_fixture_strategy_compatibility(e3)
        strategy_compat = list_compatibilities_by_strategy("strategy-123")
        assert len(strategy_compat) == 2

    def test_register_review_safe_fixture_package(self):
        """Test registering a fixture package."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        registered = register_review_safe_fixture_package(package)
        assert registered.deterministic_package_hash != ""
        assert get_review_safe_fixture_package(registered.package_id) is not None

    def test_get_nonexistent_package(self):
        """Test getting nonexistent package returns None."""
        result = get_review_safe_fixture_package("nonexistent-id")
        assert result is None

    def test_list_review_safe_fixture_packages(self):
        """Test listing all fixture packages."""
        p1 = create_review_safe_fixture_package(workspace_id="ws-1")
        p2 = create_review_safe_fixture_package(workspace_id="ws-2")
        register_review_safe_fixture_package(p1)
        register_review_safe_fixture_package(p2)
        all_packages = list_review_safe_fixture_packages()
        assert len(all_packages) == 2

    def test_list_fixture_packages_by_workspace(self):
        """Test listing packages by workspace."""
        p1 = create_review_safe_fixture_package(workspace_id="ws-123")
        p2 = create_review_safe_fixture_package(workspace_id="ws-123")
        p3 = create_review_safe_fixture_package(workspace_id="ws-456")
        register_review_safe_fixture_package(p1)
        register_review_safe_fixture_package(p2)
        register_review_safe_fixture_package(p3)
        ws_packages = list_fixture_packages_by_workspace("ws-123")
        assert len(ws_packages) == 2

    def test_list_fixture_packages_by_review_status(self):
        """Test listing packages by review status."""
        p1 = create_review_safe_fixture_package(workspace_id="ws-1")
        p2 = create_review_safe_fixture_package(workspace_id="ws-2")
        p2.review_status = "approved"
        register_review_safe_fixture_package(p1)
        register_review_safe_fixture_package(p2)
        draft_packages = list_fixture_packages_by_review_status("draft")
        assert len(draft_packages) == 1
        approved_packages = list_fixture_packages_by_review_status("approved")
        assert len(approved_packages) == 1


class TestCISummary:
    """Tests for CI summary generation."""

    def test_get_ci_summary_empty(self):
        """Test CI summary with empty indexes."""
        summary = get_ci_summary()
        assert summary["total_constraints"] == 0
        assert summary["total_topology_evaluations"] == 0
        assert summary["total_compatibility_evaluations"] == 0
        assert summary["total_packages"] == 0
        assert summary["status"] == "pass"

    def test_get_ci_summary_with_data(self):
        """Test CI summary with data."""
        constraint = create_fixture_constraint(constraint_category="clamp_zone")
        register_fixture_constraint(constraint)

        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
        )
        register_topology_evaluation(evaluation)

        package = create_review_safe_fixture_package(workspace_id="ws-123")
        register_review_safe_fixture_package(package)

        summary = get_ci_summary()
        assert summary["total_constraints"] == 1
        assert summary["total_topology_evaluations"] == 1
        assert summary["total_packages"] == 1

    def test_get_ci_summary_with_green_evaluations(self):
        """Test CI summary with green evaluations passes."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
        )
        assert evaluation.gate == "green"
        register_topology_evaluation(evaluation)

        summary = get_ci_summary()
        assert summary["topology_green_count"] == 1
        assert summary["status"] == "pass"

    def test_get_ci_summary_with_yellow_gate(self):
        """Test CI summary warns on yellow gate."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
            declared_thin_bridges=True,
        )
        assert evaluation.gate == "yellow"
        register_topology_evaluation(evaluation)

        summary = get_ci_summary()
        assert summary["topology_yellow_count"] == 1
        assert summary["status"] == "warn"

    def test_get_ci_summary_with_red_gate(self):
        """Test CI summary fails on red gate."""
        evaluation = evaluate_topology_continuity(
            geometry_authority_ref_id="geo-auth-123",
            declared_fragmented_regions=True,
        )
        assert evaluation.gate == "red"
        register_topology_evaluation(evaluation)

        summary = get_ci_summary()
        assert summary["topology_red_count"] == 1
        assert summary["status"] == "fail"

    def test_get_ci_summary_packages_with_risks(self):
        """Test CI summary counts packages with risks."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        mark_topology_risks_present(package)
        register_review_safe_fixture_package(package)

        summary = get_ci_summary()
        assert summary["packages_with_risks"] == 1

    def test_get_ci_summary_packages_with_conflicts(self):
        """Test CI summary counts packages with conflicts."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        mark_fixture_conflicts_present(package)
        register_review_safe_fixture_package(package)

        summary = get_ci_summary()
        assert summary["packages_with_conflicts"] == 1

    def test_get_ci_summary_packages_without_review(self):
        """Test CI summary counts packages without review."""
        package = create_review_safe_fixture_package(workspace_id="ws-123")
        register_review_safe_fixture_package(package)

        summary = get_ci_summary()
        assert summary["packages_without_review"] == 1
        assert summary["status"] == "warn"

    def test_get_ci_summary_constraints_by_category(self):
        """Test CI summary includes constraints by category."""
        c1 = create_fixture_constraint(constraint_category="clamp_zone")
        c2 = create_fixture_constraint(constraint_category="clamp_zone")
        c3 = create_fixture_constraint(constraint_category="keepout_zone")
        register_fixture_constraint(c1)
        register_fixture_constraint(c2)
        register_fixture_constraint(c3)

        summary = get_ci_summary()
        assert summary["constraints_by_category"]["clamp_zone"] == 2
        assert summary["constraints_by_category"]["keepout_zone"] == 1


class TestLuthierWorkspaceIntegration:
    """Tests for LuthierOperationWorkspace 7V integration."""

    def test_workspace_has_fixture_package_refs(self):
        """Test workspace has fixture_package_refs field."""
        from app.cam.luthier_operation_workspace import LuthierOperationWorkspaceV1

        workspace = LuthierOperationWorkspaceV1(
            title="Test Workspace",
            operation_family="rosette",
            fixture_package_refs=["fix-pkg-123"],
        )
        assert workspace.fixture_package_refs == ["fix-pkg-123"]

    def test_workspace_fixture_refs_default_empty(self):
        """Test workspace fixture_package_refs defaults to empty."""
        from app.cam.luthier_operation_workspace import LuthierOperationWorkspaceV1

        workspace = LuthierOperationWorkspaceV1(
            title="Test Workspace",
            operation_family="rosette",
        )
        assert workspace.fixture_package_refs == []


class TestLuthierStrategyIntegration:
    """Tests for LuthierManufacturingStrategy 7V integration."""

    def test_strategy_has_fixture_constraint_refs(self):
        """Test strategy has fixture_constraint_refs field."""
        from app.cam.luthier_manufacturing_strategy import LuthierManufacturingStrategy

        strategy = LuthierManufacturingStrategy(
            operation_family="rosette",
            fixture_constraint_refs=["fix-constraint-123"],
        )
        assert strategy.fixture_constraint_refs == ["fix-constraint-123"]

    def test_strategy_has_topology_evaluation_refs(self):
        """Test strategy has topology_evaluation_refs field."""
        from app.cam.luthier_manufacturing_strategy import LuthierManufacturingStrategy

        strategy = LuthierManufacturingStrategy(
            operation_family="rosette",
            topology_evaluation_refs=["topo-eval-123"],
        )
        assert strategy.topology_evaluation_refs == ["topo-eval-123"]

    def test_strategy_refs_default_empty(self):
        """Test strategy refs default to empty."""
        from app.cam.luthier_manufacturing_strategy import LuthierManufacturingStrategy

        strategy = LuthierManufacturingStrategy(
            operation_family="rosette",
        )
        assert strategy.fixture_constraint_refs == []
        assert strategy.topology_evaluation_refs == []


class TestStrategyExportCompatibilityIntegration:
    """Tests for 7U/7V integration."""

    def test_strategy_export_has_fixture_compatibility_refs(self):
        """Test StrategyExportCompatibilityEvaluation has fixture_compatibility_refs."""
        from app.cam.strategy_export_compatibility import (
            StrategyExportCompatibilityEvaluation,
        )

        evaluation = StrategyExportCompatibilityEvaluation(
            workspace_id="ws-123",
            fixture_compatibility_refs=["fix-compat-123"],
        )
        assert evaluation.fixture_compatibility_refs == ["fix-compat-123"]

    def test_strategy_export_fixture_refs_default_empty(self):
        """Test fixture_compatibility_refs defaults to empty."""
        from app.cam.strategy_export_compatibility import (
            StrategyExportCompatibilityEvaluation,
        )

        evaluation = StrategyExportCompatibilityEvaluation(
            workspace_id="ws-123",
        )
        assert evaluation.fixture_compatibility_refs == []


class TestInvariantEnforcement:
    """Tests for strict 7V invariant enforcement."""

    def test_constraint_mutation_blocked(self):
        """Test that may_modify_geometry cannot be True."""
        with pytest.raises(ValueError, match="may_modify_geometry"):
            FixtureTopologyConstraint(
                constraint_category="clamp_zone",
                may_modify_geometry=True,
            )

    def test_evaluation_mutation_blocked(self):
        """Test that topology evaluation cannot mutate geometry."""
        with pytest.raises(ValueError, match="geometry_mutation"):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                geometry_mutation_attempted=True,
            )

    def test_evaluation_auto_correction_blocked(self):
        """Test that topology evaluation cannot auto-correct."""
        with pytest.raises(ValueError, match="auto_correction"):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                auto_correction_attempted=True,
            )

    def test_package_no_executable_payload(self):
        """Test that packages cannot contain executable payloads."""
        with pytest.raises(ValueError, match="executable_payload"):
            ReviewSafeFixturePackage(
                workspace_id="ws-123",
                executable_payload_present=True,
            )

    def test_all_7v_artifacts_block_execution(self):
        """Test all 7V artifacts block execution authorization."""
        with pytest.raises(ValueError):
            FixtureTopologyConstraint(
                constraint_category="clamp_zone",
                execution_authorized=True,
            )

        with pytest.raises(ValueError):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                execution_authorized=True,
            )

        with pytest.raises(ValueError):
            FixtureStrategyCompatibilityEvaluation(
                strategy_id="strategy-123",
                execution_authorized=True,
            )

        with pytest.raises(ValueError):
            ReviewSafeFixturePackage(
                workspace_id="ws-123",
                execution_authorized=True,
            )

    def test_all_7v_artifacts_block_machine_output(self):
        """Test all 7V artifacts block machine output."""
        with pytest.raises(ValueError):
            FixtureTopologyConstraint(
                constraint_category="clamp_zone",
                machine_output_allowed=True,
            )

        with pytest.raises(ValueError):
            TopologyContinuityEvaluation(
                geometry_authority_ref_id="geo-auth-123",
                machine_output_allowed=True,
            )

        with pytest.raises(ValueError):
            FixtureStrategyCompatibilityEvaluation(
                strategy_id="strategy-123",
                machine_output_allowed=True,
            )

        with pytest.raises(ValueError):
            ReviewSafeFixturePackage(
                workspace_id="ws-123",
                machine_output_allowed=True,
            )

    def test_compatibility_fixture_execution_blocked(self):
        """Test that compatibility evaluation cannot have fixture execution."""
        with pytest.raises(ValueError, match="fixture_execution"):
            FixtureStrategyCompatibilityEvaluation(
                strategy_id="strategy-123",
                fixture_execution_present=True,
            )
