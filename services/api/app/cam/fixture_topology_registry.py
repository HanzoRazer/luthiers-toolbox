"""
Fixture Topology Registry

CAM Dev Order 7V: In-memory registry for fixture/topology cognition.

Provides:
  - Constraint registration and lookup
  - Topology evaluation registration and lookup
  - Compatibility evaluation registration
  - Package registration
  - CI summary generation

7V invariants:
  - No registered artifact may authorize execution
  - No registered artifact may allow machine output
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from app.cam.fixture_topology_constraints import (
    FixtureTopologyConstraint,
    FixtureConstraintCategory,
)
from app.cam.topology_continuity_evaluation import (
    TopologyContinuityEvaluation,
    TopologyRiskCategory,
)
from app.cam.fixture_strategy_compatibility import (
    FixtureStrategyCompatibilityEvaluation,
)
from app.cam.review_safe_fixture_package import (
    ReviewSafeFixturePackage,
)


FIXTURE_TOPOLOGY_CONSTRAINT_INDEX: Dict[str, FixtureTopologyConstraint] = {}

TOPOLOGY_CONTINUITY_EVALUATION_INDEX: Dict[str, TopologyContinuityEvaluation] = {}

FIXTURE_STRATEGY_COMPATIBILITY_INDEX: Dict[str, FixtureStrategyCompatibilityEvaluation] = {}

REVIEW_SAFE_FIXTURE_PACKAGE_INDEX: Dict[str, ReviewSafeFixturePackage] = {}

CONSTRAINTS_BY_CATEGORY_INDEX: Dict[FixtureConstraintCategory, List[str]] = {
    "clamp_zone": [],
    "keepout_zone": [],
    "vacuum_hold": [],
    "bridge_support": [],
    "registration_constraint": [],
    "edge_clearance": [],
    "tool_access_constraint": [],
    "fragility_constraint": [],
}

EVALUATIONS_BY_GEOMETRY_REF_INDEX: Dict[str, List[str]] = {}
COMPATIBILITY_BY_STRATEGY_INDEX: Dict[str, List[str]] = {}
PACKAGES_BY_WORKSPACE_INDEX: Dict[str, List[str]] = {}


def register_fixture_constraint(
    constraint: FixtureTopologyConstraint,
) -> FixtureTopologyConstraint:
    """Register a fixture topology constraint."""
    constraint.deterministic_constraint_hash = constraint.compute_hash()

    FIXTURE_TOPOLOGY_CONSTRAINT_INDEX[constraint.constraint_id] = constraint

    category = constraint.constraint_category
    if constraint.constraint_id not in CONSTRAINTS_BY_CATEGORY_INDEX[category]:
        CONSTRAINTS_BY_CATEGORY_INDEX[category].append(constraint.constraint_id)

    return constraint


def get_fixture_constraint(
    constraint_id: str,
) -> Optional[FixtureTopologyConstraint]:
    """Get a fixture constraint by ID."""
    return FIXTURE_TOPOLOGY_CONSTRAINT_INDEX.get(constraint_id)


def list_fixture_constraints() -> List[FixtureTopologyConstraint]:
    """List all registered fixture constraints."""
    return list(FIXTURE_TOPOLOGY_CONSTRAINT_INDEX.values())


def list_constraints_by_category(
    category: FixtureConstraintCategory,
) -> List[FixtureTopologyConstraint]:
    """List constraints by category."""
    constraint_ids = CONSTRAINTS_BY_CATEGORY_INDEX.get(category, [])
    return [
        FIXTURE_TOPOLOGY_CONSTRAINT_INDEX[cid]
        for cid in constraint_ids
        if cid in FIXTURE_TOPOLOGY_CONSTRAINT_INDEX
    ]


def register_topology_evaluation(
    evaluation: TopologyContinuityEvaluation,
) -> TopologyContinuityEvaluation:
    """Register a topology continuity evaluation."""
    evaluation.deterministic_topology_hash = evaluation.compute_hash()

    TOPOLOGY_CONTINUITY_EVALUATION_INDEX[evaluation.evaluation_id] = evaluation

    geo_ref = evaluation.geometry_authority_ref_id
    if geo_ref:
        if geo_ref not in EVALUATIONS_BY_GEOMETRY_REF_INDEX:
            EVALUATIONS_BY_GEOMETRY_REF_INDEX[geo_ref] = []
        if evaluation.evaluation_id not in EVALUATIONS_BY_GEOMETRY_REF_INDEX[geo_ref]:
            EVALUATIONS_BY_GEOMETRY_REF_INDEX[geo_ref].append(evaluation.evaluation_id)

    return evaluation


def get_topology_evaluation(
    evaluation_id: str,
) -> Optional[TopologyContinuityEvaluation]:
    """Get a topology evaluation by ID."""
    return TOPOLOGY_CONTINUITY_EVALUATION_INDEX.get(evaluation_id)


def list_topology_evaluations() -> List[TopologyContinuityEvaluation]:
    """List all registered topology evaluations."""
    return list(TOPOLOGY_CONTINUITY_EVALUATION_INDEX.values())


def list_topology_evaluations_by_geometry_ref(
    geometry_authority_ref_id: str,
) -> List[TopologyContinuityEvaluation]:
    """List topology evaluations for a geometry reference."""
    eval_ids = EVALUATIONS_BY_GEOMETRY_REF_INDEX.get(geometry_authority_ref_id, [])
    return [
        TOPOLOGY_CONTINUITY_EVALUATION_INDEX[eid]
        for eid in eval_ids
        if eid in TOPOLOGY_CONTINUITY_EVALUATION_INDEX
    ]


def register_fixture_strategy_compatibility(
    evaluation: FixtureStrategyCompatibilityEvaluation,
) -> FixtureStrategyCompatibilityEvaluation:
    """Register a fixture/strategy compatibility evaluation."""
    evaluation.deterministic_compatibility_hash = evaluation.compute_hash()

    FIXTURE_STRATEGY_COMPATIBILITY_INDEX[evaluation.evaluation_id] = evaluation

    strategy_id = evaluation.strategy_id
    if strategy_id:
        if strategy_id not in COMPATIBILITY_BY_STRATEGY_INDEX:
            COMPATIBILITY_BY_STRATEGY_INDEX[strategy_id] = []
        if evaluation.evaluation_id not in COMPATIBILITY_BY_STRATEGY_INDEX[strategy_id]:
            COMPATIBILITY_BY_STRATEGY_INDEX[strategy_id].append(evaluation.evaluation_id)

    return evaluation


def get_fixture_strategy_compatibility(
    evaluation_id: str,
) -> Optional[FixtureStrategyCompatibilityEvaluation]:
    """Get a fixture/strategy compatibility evaluation by ID."""
    return FIXTURE_STRATEGY_COMPATIBILITY_INDEX.get(evaluation_id)


def list_fixture_strategy_compatibilities() -> List[FixtureStrategyCompatibilityEvaluation]:
    """List all registered compatibility evaluations."""
    return list(FIXTURE_STRATEGY_COMPATIBILITY_INDEX.values())


def list_compatibilities_by_strategy(
    strategy_id: str,
) -> List[FixtureStrategyCompatibilityEvaluation]:
    """List compatibility evaluations for a strategy."""
    eval_ids = COMPATIBILITY_BY_STRATEGY_INDEX.get(strategy_id, [])
    return [
        FIXTURE_STRATEGY_COMPATIBILITY_INDEX[eid]
        for eid in eval_ids
        if eid in FIXTURE_STRATEGY_COMPATIBILITY_INDEX
    ]


def register_review_safe_fixture_package(
    package: ReviewSafeFixturePackage,
) -> ReviewSafeFixturePackage:
    """Register a review-safe fixture package."""
    package.deterministic_package_hash = package.compute_hash()

    REVIEW_SAFE_FIXTURE_PACKAGE_INDEX[package.package_id] = package

    if package.workspace_id:
        if package.workspace_id not in PACKAGES_BY_WORKSPACE_INDEX:
            PACKAGES_BY_WORKSPACE_INDEX[package.workspace_id] = []
        if package.package_id not in PACKAGES_BY_WORKSPACE_INDEX[package.workspace_id]:
            PACKAGES_BY_WORKSPACE_INDEX[package.workspace_id].append(package.package_id)

    return package


def get_review_safe_fixture_package(
    package_id: str,
) -> Optional[ReviewSafeFixturePackage]:
    """Get a review-safe fixture package by ID."""
    return REVIEW_SAFE_FIXTURE_PACKAGE_INDEX.get(package_id)


def list_review_safe_fixture_packages() -> List[ReviewSafeFixturePackage]:
    """List all registered fixture packages."""
    return list(REVIEW_SAFE_FIXTURE_PACKAGE_INDEX.values())


def list_fixture_packages_by_workspace(
    workspace_id: str,
) -> List[ReviewSafeFixturePackage]:
    """List fixture packages for a workspace."""
    pkg_ids = PACKAGES_BY_WORKSPACE_INDEX.get(workspace_id, [])
    return [
        REVIEW_SAFE_FIXTURE_PACKAGE_INDEX[pid]
        for pid in pkg_ids
        if pid in REVIEW_SAFE_FIXTURE_PACKAGE_INDEX
    ]


def list_fixture_packages_by_review_status(
    review_status: str,
) -> List[ReviewSafeFixturePackage]:
    """List fixture packages by review status."""
    return [
        pkg for pkg in REVIEW_SAFE_FIXTURE_PACKAGE_INDEX.values()
        if pkg.review_status == review_status
    ]


CIStatus = Literal["pass", "warn", "fail"]


class FixtureTopologyCISummary(Dict[str, Any]):
    """CI summary for fixture/topology governance health."""

    pass


def get_ci_summary() -> FixtureTopologyCISummary:
    """
    Generate CI summary for fixture/topology governance health.

    Returns summary with:
      - total_constraints
      - total_topology_evaluations
      - total_compatibility_evaluations
      - total_packages
      - topology_red_count
      - topology_yellow_count
      - topology_green_count
      - compatibility_red_count
      - compatibility_yellow_count
      - compatibility_green_count
      - packages_with_risks
      - packages_with_conflicts
      - packages_without_review
      - status: pass|warn|fail
    """
    total_constraints = len(FIXTURE_TOPOLOGY_CONSTRAINT_INDEX)
    total_topology_evaluations = len(TOPOLOGY_CONTINUITY_EVALUATION_INDEX)
    total_compatibility_evaluations = len(FIXTURE_STRATEGY_COMPATIBILITY_INDEX)
    total_packages = len(REVIEW_SAFE_FIXTURE_PACKAGE_INDEX)

    topology_green = 0
    topology_yellow = 0
    topology_red = 0

    for evaluation in TOPOLOGY_CONTINUITY_EVALUATION_INDEX.values():
        if evaluation.gate == "green":
            topology_green += 1
        elif evaluation.gate == "yellow":
            topology_yellow += 1
        elif evaluation.gate == "red":
            topology_red += 1

    compatibility_green = 0
    compatibility_yellow = 0
    compatibility_red = 0

    for evaluation in FIXTURE_STRATEGY_COMPATIBILITY_INDEX.values():
        if evaluation.gate == "green":
            compatibility_green += 1
        elif evaluation.gate == "yellow":
            compatibility_yellow += 1
        elif evaluation.gate == "red":
            compatibility_red += 1

    packages_with_risks = len([
        pkg for pkg in REVIEW_SAFE_FIXTURE_PACKAGE_INDEX.values()
        if pkg.topology_risks_present
    ])

    packages_with_conflicts = len([
        pkg for pkg in REVIEW_SAFE_FIXTURE_PACKAGE_INDEX.values()
        if pkg.fixture_conflicts_present
    ])

    packages_without_review = len([
        pkg for pkg in REVIEW_SAFE_FIXTURE_PACKAGE_INDEX.values()
        if pkg.review_status in ("draft", "pending_review")
    ])

    constraints_by_category = {
        category: len(ids)
        for category, ids in CONSTRAINTS_BY_CATEGORY_INDEX.items()
    }

    status: CIStatus
    if topology_red > 0 or compatibility_red > 0:
        status = "fail"
    elif topology_yellow > 0 or compatibility_yellow > 0 or packages_without_review > 0:
        status = "warn"
    else:
        status = "pass"

    return FixtureTopologyCISummary(
        total_constraints=total_constraints,
        total_topology_evaluations=total_topology_evaluations,
        total_compatibility_evaluations=total_compatibility_evaluations,
        total_packages=total_packages,
        topology_green_count=topology_green,
        topology_yellow_count=topology_yellow,
        topology_red_count=topology_red,
        compatibility_green_count=compatibility_green,
        compatibility_yellow_count=compatibility_yellow,
        compatibility_red_count=compatibility_red,
        packages_with_risks=packages_with_risks,
        packages_with_conflicts=packages_with_conflicts,
        packages_without_review=packages_without_review,
        constraints_by_category=constraints_by_category,
        status=status,
    )


def clear_fixture_topology_indexes() -> None:
    """Clear all indexes (for testing)."""
    FIXTURE_TOPOLOGY_CONSTRAINT_INDEX.clear()
    TOPOLOGY_CONTINUITY_EVALUATION_INDEX.clear()
    FIXTURE_STRATEGY_COMPATIBILITY_INDEX.clear()
    REVIEW_SAFE_FIXTURE_PACKAGE_INDEX.clear()
    EVALUATIONS_BY_GEOMETRY_REF_INDEX.clear()
    COMPATIBILITY_BY_STRATEGY_INDEX.clear()
    PACKAGES_BY_WORKSPACE_INDEX.clear()
    for category in CONSTRAINTS_BY_CATEGORY_INDEX:
        CONSTRAINTS_BY_CATEGORY_INDEX[category] = []
