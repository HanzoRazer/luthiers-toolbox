"""
Fixture Strategy Compatibility

CAM Dev Order 7V: Fixture-aware strategy compatibility evaluation.

Provides:
  - FixtureStrategyCompatibilityEvaluation model
  - Strategy ↔ fixture compatibility checking
  - Topology risk integration

7V invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - fixture_execution_present: always False

Core principle:
  Fixtures constrain manufacturing interpretation.
  Fixtures do not redefine canonical geometry.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.cam.fixture_topology_constraints import (
    FixtureConstraintCategory,
    FixtureTopologyConstraint,
)


ValidationGate = Literal["green", "yellow", "red"]


class FixtureStrategyCompatibilityEvaluation(BaseModel):
    """
    Evaluation of strategy ↔ fixture compatibility.

    Determines whether a manufacturing strategy is compatible with
    fixture constraints and topology considerations.

    7V invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
      - fixture_execution_present: always False
    """

    evaluation_id: str = Field(
        default_factory=lambda: f"fix-compat-{uuid4().hex[:12]}",
        description="Unique evaluation identifier"
    )

    strategy_id: str = Field(
        ..., description="Strategy being evaluated"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace context"
    )

    geometry_authority_ref_ids: List[str] = Field(
        default_factory=list,
        description="Geometry authority references involved"
    )

    fixture_constraint_ids: List[str] = Field(
        default_factory=list,
        description="Fixture constraints evaluated against"
    )

    compatible_fixture_categories: List[FixtureConstraintCategory] = Field(
        default_factory=list,
        description="Fixture categories compatible with strategy"
    )

    incompatible_fixture_categories: List[FixtureConstraintCategory] = Field(
        default_factory=list,
        description="Fixture categories incompatible with strategy"
    )

    topology_risk_refs: List[str] = Field(
        default_factory=list,
        description="Topology evaluation IDs with risks"
    )

    topology_evaluation_ids: List[str] = Field(
        default_factory=list,
        description="All topology evaluation IDs considered"
    )

    clamp_conflicts_detected: bool = Field(
        default=False,
        description="Whether clamp conflicts were detected"
    )
    keepout_violations_detected: bool = Field(
        default=False,
        description="Whether keepout violations were detected"
    )

    gate: ValidationGate = Field(
        default="green",
        description="Validation gate result"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW warnings"
    )

    review_required: bool = Field(
        default=True,
        description="Whether human review is required"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7V does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7V does not allow machine output"
    )
    fixture_execution_present: bool = Field(
        default=False,
        description="Always False — no fixture execution in 7V"
    )

    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_compatibility_hash: str = Field(
        default="",
        description="Deterministic hash of evaluation state"
    )

    @model_validator(mode="after")
    def enforce_7v_invariants(self) -> "FixtureStrategyCompatibilityEvaluation":
        """Enforce 7V invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7V invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7V invariant violation: machine_output_allowed must be False"
            )
        if self.fixture_execution_present:
            raise ValueError(
                "7V invariant violation: fixture_execution_present must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of evaluation state."""
        hash_input = {
            "evaluation_id": self.evaluation_id,
            "strategy_id": self.strategy_id,
            "workspace_id": self.workspace_id,
            "geometry_authority_ref_ids": sorted(self.geometry_authority_ref_ids),
            "fixture_constraint_ids": sorted(self.fixture_constraint_ids),
            "compatible_fixture_categories": sorted(self.compatible_fixture_categories),
            "incompatible_fixture_categories": sorted(self.incompatible_fixture_categories),
            "topology_risk_refs": sorted(self.topology_risk_refs),
            "gate": self.gate,
            "blocking_issues": sorted(self.blocking_issues),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def evaluate_fixture_strategy_compatibility(
    strategy_id: str,
    workspace_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    fixture_constraints: Optional[List[FixtureTopologyConstraint]] = None,
    topology_evaluation_ids: Optional[List[str]] = None,
    strategy_operation_family: Optional[str] = None,
    declared_clamp_conflicts: bool = False,
    declared_keepout_violations: bool = False,
) -> FixtureStrategyCompatibilityEvaluation:
    """
    Evaluate strategy ↔ fixture compatibility.

    Args:
        strategy_id: Strategy to evaluate
        workspace_id: Optional workspace context
        geometry_authority_ref_ids: Geometry authority refs
        fixture_constraints: Constraints to evaluate against
        topology_evaluation_ids: Topology evaluations to consider
        strategy_operation_family: Operation family for compatibility hints
        declared_clamp_conflicts: Whether clamp conflicts are declared
        declared_keepout_violations: Whether keepout violations are declared

    Returns:
        FixtureStrategyCompatibilityEvaluation with gate and issues
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    compatible_categories: List[FixtureConstraintCategory] = []
    incompatible_categories: List[FixtureConstraintCategory] = []
    fixture_constraint_ids: List[str] = []
    topology_risk_refs: List[str] = []

    if fixture_constraints:
        for constraint in fixture_constraints:
            fixture_constraint_ids.append(constraint.constraint_id)

            if constraint.severity == "critical":
                incompatible_categories.append(constraint.constraint_category)
                blocking_issues.append(
                    f"Critical fixture constraint '{constraint.constraint_category}': "
                    f"{constraint.description}"
                )
            elif constraint.severity == "high":
                if constraint.constraint_category not in compatible_categories:
                    compatible_categories.append(constraint.constraint_category)
                warnings.append(
                    f"High severity fixture constraint '{constraint.constraint_category}'"
                )
            else:
                if constraint.constraint_category not in compatible_categories:
                    compatible_categories.append(constraint.constraint_category)

    if declared_clamp_conflicts:
        blocking_issues.append("Clamp conflicts detected — strategy incompatible with fixture")
        if "clamp_zone" not in incompatible_categories:
            incompatible_categories.append("clamp_zone")

    if declared_keepout_violations:
        blocking_issues.append("Keepout zone violations detected")
        if "keepout_zone" not in incompatible_categories:
            incompatible_categories.append("keepout_zone")

    if strategy_operation_family:
        family_hints = _get_fixture_compatibility_hints(strategy_operation_family)
        for hint_warning in family_hints.get("warnings", []):
            if hint_warning not in warnings:
                warnings.append(hint_warning)

    if not fixture_constraints and not topology_evaluation_ids:
        warnings.append("No fixture constraints or topology evaluations provided")

    if blocking_issues:
        gate: ValidationGate = "red"
    elif warnings:
        gate = "yellow"
    else:
        gate = "green"

    evaluation = FixtureStrategyCompatibilityEvaluation(
        strategy_id=strategy_id,
        workspace_id=workspace_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids or [],
        fixture_constraint_ids=fixture_constraint_ids,
        compatible_fixture_categories=compatible_categories,
        incompatible_fixture_categories=incompatible_categories,
        topology_risk_refs=topology_risk_refs,
        topology_evaluation_ids=topology_evaluation_ids or [],
        clamp_conflicts_detected=declared_clamp_conflicts,
        keepout_violations_detected=declared_keepout_violations,
        gate=gate,
        blocking_issues=blocking_issues,
        warnings=warnings,
    )

    evaluation.deterministic_compatibility_hash = evaluation.compute_hash()

    return evaluation


def _get_fixture_compatibility_hints(
    operation_family: str,
) -> Dict[str, Any]:
    """
    Get fixture compatibility hints for an operation family.

    Returns hints based on operation family characteristics.
    """
    hints: Dict[str, Dict[str, Any]] = {
        "rosette": {
            "recommended_fixtures": ["vacuum_hold", "registration_constraint"],
            "avoid_fixtures": ["clamp_zone"],
            "warnings": ["Rosette operations require stable center registration"],
        },
        "binding_channel": {
            "recommended_fixtures": ["clamp_zone", "edge_clearance"],
            "avoid_fixtures": [],
            "warnings": ["Binding channel requires bearing-guided edge access"],
        },
        "neck_profile": {
            "recommended_fixtures": ["clamp_zone", "registration_constraint"],
            "avoid_fixtures": [],
            "warnings": ["Neck profile requires secure longitudinal clamping"],
        },
        "fret_slotting": {
            "recommended_fixtures": ["vacuum_hold", "registration_constraint"],
            "avoid_fixtures": ["clamp_zone"],
            "warnings": ["Fret slotting requires flat, stable workholding"],
        },
        "body_outline": {
            "recommended_fixtures": ["vacuum_hold", "bridge_support"],
            "avoid_fixtures": [],
            "warnings": ["Body outline may require bridge tabs for part retention"],
        },
    }

    return hints.get(operation_family, {"warnings": []})


def detect_fixture_conflicts(
    strategy_regions: Optional[List[str]] = None,
    constraint_regions: Optional[List[str]] = None,
) -> tuple[bool, List[str]]:
    """
    Detect fixture conflicts based on declared region overlap.

    Args:
        strategy_regions: Regions affected by strategy operations
        constraint_regions: Regions affected by fixture constraints

    Returns:
        (detected, conflicting_regions)
    """
    if not strategy_regions or not constraint_regions:
        return False, []

    conflicts = [r for r in strategy_regions if r in constraint_regions]
    return len(conflicts) > 0, conflicts


def validate_fixture_strategy_compatibility(
    evaluation: FixtureStrategyCompatibilityEvaluation,
) -> tuple[bool, List[str]]:
    """
    Validate a fixture strategy compatibility evaluation.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if evaluation.execution_authorized:
        issues.append("execution_authorized must be False")

    if evaluation.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if evaluation.fixture_execution_present:
        issues.append("fixture_execution_present must be False")

    if not evaluation.strategy_id:
        issues.append("strategy_id is required")

    return len(issues) == 0, issues
