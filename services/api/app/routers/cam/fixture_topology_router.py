"""
Fixture Topology Router

CAM Dev Order 7V: HTTP endpoints for fixture/topology intelligence governance.

Provides endpoints for:
  - Fixture constraint management
  - Topology continuity evaluation
  - Fixture/strategy compatibility
  - Review-safe fixture packages
  - CI summary

7V invariants:
  - No endpoint authorizes execution
  - No endpoint allows machine output
  - No endpoint mutates geometry
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
    update_fixture_package_review_status,
    validate_review_safe_fixture_package,
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
)


router = APIRouter(
    prefix="/api/cam/fixture-topology",
    tags=["CAM", "Fixture", "Topology", "Governance"],
)


class FixtureTopologyMeta(BaseModel):
    """Metadata for Fixture Topology API."""

    version: str = "7V"
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    geometry_mutation_allowed: bool = False
    description: str = "Fixture/topology intelligence governance — no execution"


@router.get("/", response_model=FixtureTopologyMeta)
async def get_meta() -> FixtureTopologyMeta:
    """Get Fixture Topology API metadata."""
    return FixtureTopologyMeta()


class CreateConstraintRequest(BaseModel):
    """Request to create a fixture constraint."""

    constraint_category: FixtureConstraintCategory
    description: str = ""
    geometry_authority_ref_id: Optional[str] = None
    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    affected_regions: Optional[List[str]] = None
    severity: ConstraintSeverity = "medium"
    min_x_mm: Optional[float] = None
    max_x_mm: Optional[float] = None
    min_y_mm: Optional[float] = None
    max_y_mm: Optional[float] = None
    height_mm: Optional[float] = None


@router.post("/constraints", response_model=FixtureTopologyConstraint)
async def create_constraint(
    request: CreateConstraintRequest,
) -> FixtureTopologyConstraint:
    """Create and register a fixture topology constraint."""
    constraint = create_fixture_constraint(
        constraint_category=request.constraint_category,
        description=request.description,
        geometry_authority_ref_id=request.geometry_authority_ref_id,
        workspace_id=request.workspace_id,
        strategy_id=request.strategy_id,
        affected_regions=request.affected_regions,
        severity=request.severity,
        min_x_mm=request.min_x_mm,
        max_x_mm=request.max_x_mm,
        min_y_mm=request.min_y_mm,
        max_y_mm=request.max_y_mm,
        height_mm=request.height_mm,
    )
    return register_fixture_constraint(constraint)


class CreateConstraintFromFixtureRequest(BaseModel):
    """Request to create constraints from a golden fixture."""

    fixture_id: str
    clearance_zone_id: Optional[str] = None
    geometry_authority_ref_id: Optional[str] = None
    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None


@router.post("/constraints/from-fixture", response_model=List[FixtureTopologyConstraint])
async def create_constraints_from_fixture(
    request: CreateConstraintFromFixtureRequest,
) -> List[FixtureTopologyConstraint]:
    """Create constraints from a 7S golden fixture."""
    constraints = create_constraint_from_golden_fixture(
        fixture_id=request.fixture_id,
        clearance_zone_id=request.clearance_zone_id,
        geometry_authority_ref_id=request.geometry_authority_ref_id,
        workspace_id=request.workspace_id,
        strategy_id=request.strategy_id,
    )
    if not constraints:
        raise HTTPException(404, f"Fixture '{request.fixture_id}' not found or has no clearance zones")

    return [register_fixture_constraint(c) for c in constraints]


@router.get("/constraints", response_model=List[FixtureTopologyConstraint])
async def list_all_constraints(
    category: Optional[FixtureConstraintCategory] = None,
) -> List[FixtureTopologyConstraint]:
    """List all fixture constraints, optionally filtered by category."""
    if category:
        return list_constraints_by_category(category)
    return list_fixture_constraints()


@router.get("/constraints/{constraint_id}", response_model=FixtureTopologyConstraint)
async def get_constraint(constraint_id: str) -> FixtureTopologyConstraint:
    """Get a specific fixture constraint by ID."""
    constraint = get_fixture_constraint(constraint_id)
    if not constraint:
        raise HTTPException(404, f"Constraint '{constraint_id}' not found")
    return constraint


class EvaluateTopologyRequest(BaseModel):
    """Request to evaluate topology continuity."""

    geometry_authority_ref_id: str
    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    declared_thin_bridges: bool = False
    declared_fragmented_regions: bool = False
    declared_unsupported_spans: bool = False
    declared_clamp_interference: bool = False
    risk_declarations: Optional[List[TopologyRiskDeclaration]] = None
    fixture_constraint_ids: Optional[List[str]] = None


@router.post("/evaluate", response_model=TopologyContinuityEvaluation)
async def evaluate_topology(
    request: EvaluateTopologyRequest,
) -> TopologyContinuityEvaluation:
    """Evaluate topology continuity for a geometry reference."""
    evaluation = evaluate_topology_continuity(
        geometry_authority_ref_id=request.geometry_authority_ref_id,
        workspace_id=request.workspace_id,
        strategy_id=request.strategy_id,
        declared_thin_bridges=request.declared_thin_bridges,
        declared_fragmented_regions=request.declared_fragmented_regions,
        declared_unsupported_spans=request.declared_unsupported_spans,
        declared_clamp_interference=request.declared_clamp_interference,
        risk_declarations=request.risk_declarations,
        fixture_constraint_ids=request.fixture_constraint_ids,
    )
    return register_topology_evaluation(evaluation)


@router.get("/evaluations", response_model=List[TopologyContinuityEvaluation])
async def list_all_topology_evaluations() -> List[TopologyContinuityEvaluation]:
    """List all topology evaluations."""
    return list_topology_evaluations()


@router.get("/evaluations/{evaluation_id}", response_model=TopologyContinuityEvaluation)
async def get_topology_eval(evaluation_id: str) -> TopologyContinuityEvaluation:
    """Get a specific topology evaluation by ID."""
    evaluation = get_topology_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(404, f"Evaluation '{evaluation_id}' not found")
    return evaluation


@router.get(
    "/evaluations/by-geometry/{geometry_ref_id}",
    response_model=List[TopologyContinuityEvaluation],
)
async def get_evaluations_by_geometry(
    geometry_ref_id: str,
) -> List[TopologyContinuityEvaluation]:
    """List topology evaluations for a geometry reference."""
    return list_topology_evaluations_by_geometry_ref(geometry_ref_id)


class EvaluateCompatibilityRequest(BaseModel):
    """Request to evaluate fixture/strategy compatibility."""

    strategy_id: str
    workspace_id: Optional[str] = None
    geometry_authority_ref_ids: Optional[List[str]] = None
    fixture_constraint_ids: Optional[List[str]] = None
    topology_evaluation_ids: Optional[List[str]] = None
    strategy_operation_family: Optional[str] = None
    declared_clamp_conflicts: bool = False
    declared_keepout_violations: bool = False


@router.post("/strategy-compatibility", response_model=FixtureStrategyCompatibilityEvaluation)
async def evaluate_strategy_compatibility(
    request: EvaluateCompatibilityRequest,
) -> FixtureStrategyCompatibilityEvaluation:
    """Evaluate fixture/strategy compatibility."""
    constraints = None
    if request.fixture_constraint_ids:
        constraints = [
            get_fixture_constraint(cid)
            for cid in request.fixture_constraint_ids
            if get_fixture_constraint(cid)
        ]

    evaluation = evaluate_fixture_strategy_compatibility(
        strategy_id=request.strategy_id,
        workspace_id=request.workspace_id,
        geometry_authority_ref_ids=request.geometry_authority_ref_ids,
        fixture_constraints=constraints,
        topology_evaluation_ids=request.topology_evaluation_ids,
        strategy_operation_family=request.strategy_operation_family,
        declared_clamp_conflicts=request.declared_clamp_conflicts,
        declared_keepout_violations=request.declared_keepout_violations,
    )
    return register_fixture_strategy_compatibility(evaluation)


@router.get("/strategy-compatibility", response_model=List[FixtureStrategyCompatibilityEvaluation])
async def list_all_compatibilities() -> List[FixtureStrategyCompatibilityEvaluation]:
    """List all fixture/strategy compatibility evaluations."""
    return list_fixture_strategy_compatibilities()


@router.get(
    "/strategy-compatibility/{evaluation_id}",
    response_model=FixtureStrategyCompatibilityEvaluation,
)
async def get_compatibility(evaluation_id: str) -> FixtureStrategyCompatibilityEvaluation:
    """Get a specific compatibility evaluation by ID."""
    evaluation = get_fixture_strategy_compatibility(evaluation_id)
    if not evaluation:
        raise HTTPException(404, f"Compatibility evaluation '{evaluation_id}' not found")
    return evaluation


@router.get(
    "/strategy-compatibility/by-strategy/{strategy_id}",
    response_model=List[FixtureStrategyCompatibilityEvaluation],
)
async def get_compatibilities_by_strategy(
    strategy_id: str,
) -> List[FixtureStrategyCompatibilityEvaluation]:
    """List compatibility evaluations for a strategy."""
    return list_compatibilities_by_strategy(strategy_id)


class CreatePackageRequest(BaseModel):
    """Request to create a review-safe fixture package."""

    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    geometry_authority_ref_ids: Optional[List[str]] = None
    fixture_constraint_ids: Optional[List[str]] = None
    topology_evaluation_ids: Optional[List[str]] = None
    compatibility_evaluation_ids: Optional[List[str]] = None
    title: str = ""
    description: str = ""


@router.post("/review-package", response_model=ReviewSafeFixturePackage)
async def create_review_package(
    request: CreatePackageRequest,
) -> ReviewSafeFixturePackage:
    """Create and register a review-safe fixture package."""
    package = create_review_safe_fixture_package(
        workspace_id=request.workspace_id,
        strategy_id=request.strategy_id,
        geometry_authority_ref_ids=request.geometry_authority_ref_ids,
        fixture_constraint_ids=request.fixture_constraint_ids,
        topology_evaluation_ids=request.topology_evaluation_ids,
        compatibility_evaluation_ids=request.compatibility_evaluation_ids,
        title=request.title,
        description=request.description,
    )
    return register_review_safe_fixture_package(package)


@router.get("/review-package", response_model=List[ReviewSafeFixturePackage])
async def list_all_packages(
    review_status: Optional[PackageReviewStatus] = None,
) -> List[ReviewSafeFixturePackage]:
    """List all fixture packages, optionally filtered by review status."""
    if review_status:
        return list_fixture_packages_by_review_status(review_status)
    return list_review_safe_fixture_packages()


@router.get("/review-package/{package_id}", response_model=ReviewSafeFixturePackage)
async def get_package(package_id: str) -> ReviewSafeFixturePackage:
    """Get a specific fixture package by ID."""
    package = get_review_safe_fixture_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")
    return package


@router.get(
    "/review-package/by-workspace/{workspace_id}",
    response_model=List[ReviewSafeFixturePackage],
)
async def get_packages_by_workspace(
    workspace_id: str,
) -> List[ReviewSafeFixturePackage]:
    """List fixture packages for a workspace."""
    return list_fixture_packages_by_workspace(workspace_id)


class UpdateReviewStatusRequest(BaseModel):
    """Request to update package review status."""

    review_status: PackageReviewStatus
    reviewer_note: Optional[str] = None


@router.post(
    "/review-package/{package_id}/review-status",
    response_model=ReviewSafeFixturePackage,
)
async def update_package_review_status(
    package_id: str,
    request: UpdateReviewStatusRequest,
) -> ReviewSafeFixturePackage:
    """Update the review status of a package."""
    package = get_review_safe_fixture_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")

    updated = update_fixture_package_review_status(
        package,
        request.review_status,
        request.reviewer_note,
    )
    return updated


@router.post("/review-package/{package_id}/validate")
async def validate_package(package_id: str) -> Dict[str, Any]:
    """Validate that a fixture package is ready for review."""
    package = get_review_safe_fixture_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")

    is_valid, issues = validate_review_safe_fixture_package(package)

    return {
        "package_id": package_id,
        "is_valid": is_valid,
        "issues": issues,
        "review_status": package.review_status,
        "topology_risks_present": package.topology_risks_present,
        "fixture_conflicts_present": package.fixture_conflicts_present,
        "blocking_issues": package.blocking_issues,
        "warnings": package.warnings,
    }


@router.get("/ci")
async def get_ci_status() -> Dict[str, Any]:
    """
    Get CI summary for fixture/topology governance health.

    Returns:
      - total_constraints
      - total_topology_evaluations
      - total_compatibility_evaluations
      - total_packages
      - topology_green/yellow/red_count
      - compatibility_green/yellow/red_count
      - packages_with_risks
      - packages_with_conflicts
      - packages_without_review
      - status: pass|warn|fail
    """
    return get_ci_summary()
