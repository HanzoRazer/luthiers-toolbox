"""
Fixture Topology Constraints

CAM Dev Order 7V: Fixture-aware topology cognition constraints.

Provides:
  - FixtureTopologyConstraint model
  - Constraint categories
  - Golden fixture adapter
  - Constraint validation

7V invariants:
  - may_modify_geometry: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

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


FixtureConstraintCategory = Literal[
    "clamp_zone",
    "keepout_zone",
    "vacuum_hold",
    "bridge_support",
    "registration_constraint",
    "edge_clearance",
    "tool_access_constraint",
    "fragility_constraint",
]

ConstraintSeverity = Literal["low", "medium", "high", "critical"]


class FixtureTopologyConstraint(BaseModel):
    """
    Fixture-aware topology constraint.

    Represents a constraint that affects manufacturing interpretation
    based on fixture configuration and topology considerations.

    7V invariants (model-enforced):
      - may_modify_geometry: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    constraint_id: str = Field(
        default_factory=lambda: f"fix-constraint-{uuid4().hex[:12]}",
        description="Unique constraint identifier"
    )

    constraint_category: FixtureConstraintCategory = Field(
        ..., description="Category of constraint"
    )

    geometry_authority_ref_id: Optional[str] = Field(
        default=None,
        description="Geometry authority reference this constraint applies to"
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace this constraint applies to"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="Strategy this constraint applies to"
    )

    source_fixture_id: Optional[str] = Field(
        default=None,
        description="Source golden fixture ID if derived from 7S fixture"
    )
    source_clearance_zone_id: Optional[str] = Field(
        default=None,
        description="Source clearance zone ID if derived from 7S fixture"
    )

    description: str = Field(
        default="",
        description="Human description of constraint"
    )

    affected_regions: List[str] = Field(
        default_factory=list,
        description="Region labels affected by this constraint"
    )

    min_x_mm: Optional[float] = Field(
        default=None,
        description="Minimum X boundary in mm"
    )
    max_x_mm: Optional[float] = Field(
        default=None,
        description="Maximum X boundary in mm"
    )
    min_y_mm: Optional[float] = Field(
        default=None,
        description="Minimum Y boundary in mm"
    )
    max_y_mm: Optional[float] = Field(
        default=None,
        description="Maximum Y boundary in mm"
    )
    height_mm: Optional[float] = Field(
        default=None,
        description="Height clearance in mm"
    )

    severity: ConstraintSeverity = Field(
        default="medium",
        description="Constraint severity"
    )

    review_required: bool = Field(
        default=True,
        description="Whether human review is required"
    )

    may_modify_geometry: bool = Field(
        default=False,
        description="Always False — constraints cannot modify geometry"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7V does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7V does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_constraint_hash: str = Field(
        default="",
        description="Deterministic hash of constraint state"
    )

    @model_validator(mode="after")
    def enforce_7v_invariants(self) -> "FixtureTopologyConstraint":
        """Enforce 7V invariants."""
        if self.may_modify_geometry:
            raise ValueError(
                "7V invariant violation: may_modify_geometry must be False — "
                "constraints cannot modify geometry"
            )
        if self.execution_authorized:
            raise ValueError(
                "7V invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7V invariant violation: machine_output_allowed must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of constraint state."""
        hash_input = {
            "constraint_id": self.constraint_id,
            "constraint_category": self.constraint_category,
            "geometry_authority_ref_id": self.geometry_authority_ref_id,
            "workspace_id": self.workspace_id,
            "strategy_id": self.strategy_id,
            "source_fixture_id": self.source_fixture_id,
            "affected_regions": sorted(self.affected_regions),
            "severity": self.severity,
            "min_x_mm": self.min_x_mm,
            "max_x_mm": self.max_x_mm,
            "min_y_mm": self.min_y_mm,
            "max_y_mm": self.max_y_mm,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def region_overlaps(self, region_label: str) -> bool:
        """Check if a region label overlaps with affected regions."""
        return region_label in self.affected_regions

    def bounds_overlap(
        self,
        check_min_x: float,
        check_max_x: float,
        check_min_y: float,
        check_max_y: float,
    ) -> bool:
        """Check if bounds overlap with constraint bounds."""
        if self.min_x_mm is None or self.max_x_mm is None:
            return False
        if self.min_y_mm is None or self.max_y_mm is None:
            return False

        x_overlap = not (check_max_x < self.min_x_mm or check_min_x > self.max_x_mm)
        y_overlap = not (check_max_y < self.min_y_mm or check_min_y > self.max_y_mm)

        return x_overlap and y_overlap


def create_fixture_constraint(
    constraint_category: FixtureConstraintCategory,
    description: str = "",
    geometry_authority_ref_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    affected_regions: Optional[List[str]] = None,
    severity: ConstraintSeverity = "medium",
    min_x_mm: Optional[float] = None,
    max_x_mm: Optional[float] = None,
    min_y_mm: Optional[float] = None,
    max_y_mm: Optional[float] = None,
    height_mm: Optional[float] = None,
) -> FixtureTopologyConstraint:
    """
    Create a fixture topology constraint.

    Manual creation path for constraints not derived from golden fixtures.
    """
    constraint = FixtureTopologyConstraint(
        constraint_category=constraint_category,
        description=description,
        geometry_authority_ref_id=geometry_authority_ref_id,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        affected_regions=affected_regions or [],
        severity=severity,
        min_x_mm=min_x_mm,
        max_x_mm=max_x_mm,
        min_y_mm=min_y_mm,
        max_y_mm=max_y_mm,
        height_mm=height_mm,
    )
    constraint.deterministic_constraint_hash = constraint.compute_hash()
    return constraint


def create_constraint_from_golden_fixture(
    fixture_id: str,
    clearance_zone_id: Optional[str] = None,
    geometry_authority_ref_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
) -> Optional[List[FixtureTopologyConstraint]]:
    """
    Create constraints from a 7S golden fixture.

    Adapts golden fixture clearance zones into fixture topology constraints.

    Args:
        fixture_id: ID of the golden fixture
        clearance_zone_id: Optional specific zone to convert (all if None)
        geometry_authority_ref_id: Optional geometry ref to bind to
        workspace_id: Optional workspace to bind to
        strategy_id: Optional strategy to bind to

    Returns:
        List of constraints or None if fixture not found
    """
    try:
        from app.cam.cam_golden_artifact_fixtures import get_golden_fixture
    except ImportError:
        return None

    fixture = get_golden_fixture(fixture_id)
    if not fixture:
        return None

    constraints: List[FixtureTopologyConstraint] = []

    for zone in fixture.clearance_zones:
        if clearance_zone_id and zone.zone_id != clearance_zone_id:
            continue

        zone_type_to_category: Dict[str, FixtureConstraintCategory] = {
            "clamp": "clamp_zone",
            "screw": "keepout_zone",
            "vacuum_port": "vacuum_hold",
            "registration": "registration_constraint",
            "custom": "keepout_zone",
        }

        category = zone_type_to_category.get(zone.zone_type, "keepout_zone")

        constraint = FixtureTopologyConstraint(
            constraint_category=category,
            description=f"From fixture '{fixture.display_name}' zone '{zone.zone_id}': {zone.description}",
            geometry_authority_ref_id=geometry_authority_ref_id,
            workspace_id=workspace_id,
            strategy_id=strategy_id,
            source_fixture_id=fixture_id,
            source_clearance_zone_id=zone.zone_id,
            affected_regions=[zone.zone_id],
            severity="high" if category == "clamp_zone" else "medium",
            min_x_mm=zone.min_x_mm,
            max_x_mm=zone.max_x_mm,
            min_y_mm=zone.min_y_mm,
            max_y_mm=zone.max_y_mm,
            height_mm=zone.height_mm,
        )
        constraint.deterministic_constraint_hash = constraint.compute_hash()
        constraints.append(constraint)

    return constraints if constraints else None


def validate_fixture_constraint(
    constraint: FixtureTopologyConstraint,
) -> tuple[bool, List[str]]:
    """
    Validate a fixture constraint.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if constraint.may_modify_geometry:
        issues.append("may_modify_geometry must be False")

    if constraint.execution_authorized:
        issues.append("execution_authorized must be False")

    if constraint.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not constraint.description:
        issues.append("Constraint should have a description")

    has_bounds = (
        constraint.min_x_mm is not None and
        constraint.max_x_mm is not None and
        constraint.min_y_mm is not None and
        constraint.max_y_mm is not None
    )

    if not has_bounds and not constraint.affected_regions:
        issues.append("Constraint should have bounds or affected regions")

    return len(issues) == 0, issues


def build_fixture_constraint_hash(constraint: FixtureTopologyConstraint) -> str:
    """Build deterministic hash for a fixture constraint."""
    return constraint.compute_hash()
