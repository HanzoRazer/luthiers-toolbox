"""
Manufacturing Review Observation

CAM Dev Order 7W: Structured review observations for manufacturing cognition.

Provides:
  - ManufacturingReviewObservation model
  - Cognition annotations
  - Review continuity notes
  - Observation hash computation

7W invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - modifies_geometry_authority: always False

Core principle:
  Review observations capture reasoning continuity.
  They do not authorize execution or modify geometry.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


ReviewObservationCategory = Literal[
    "topology_warning",
    "fixture_warning",
    "export_review_note",
    "geometry_authority_note",
    "manufacturing_strategy_note",
    "review_rationale",
    "provenance_warning",
    "continuity_observation",
]

ObservationSeverity = Literal[
    "info",
    "warning",
    "critical",
]


class ManufacturingReviewObservation(BaseModel):
    """
    Structured review observation for manufacturing cognition.

    Captures topology warnings, fixture warnings, export notes,
    strategy observations, and review rationale.

    7W invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
      - modifies_geometry_authority: always False
    """

    observation_id: str = Field(
        default_factory=lambda: f"mro-{uuid4().hex[:12]}",
        description="Unique observation identifier"
    )

    observation_category: ReviewObservationCategory = Field(
        ...,
        description="Category of observation"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="Source workspace ID"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="Source strategy ID"
    )
    fixture_package_id: Optional[str] = Field(
        default=None,
        description="Related fixture package ID"
    )
    export_package_id: Optional[str] = Field(
        default=None,
        description="Related export package ID"
    )

    geometry_authority_ref_ids: List[str] = Field(
        default_factory=list,
        description="Geometry authority reference IDs"
    )

    observation_text: str = Field(
        ...,
        description="Human-readable observation text"
    )

    severity: ObservationSeverity = Field(
        default="info",
        description="Observation severity level"
    )

    provenance_refs: List[str] = Field(
        default_factory=list,
        description="Provenance reference chain"
    )

    review_required: bool = Field(
        default=True,
        description="Whether this observation requires human review"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7W does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7W does not allow machine output"
    )
    modifies_geometry_authority: bool = Field(
        default=False,
        description="Always False — 7W does not modify geometry authority"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_observation_hash: str = Field(
        default="",
        description="Deterministic hash of observation state"
    )

    @model_validator(mode="after")
    def enforce_7w_invariants(self) -> "ManufacturingReviewObservation":
        """Enforce 7W invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7W invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7W invariant violation: machine_output_allowed must be False"
            )
        if self.modifies_geometry_authority:
            raise ValueError(
                "7W invariant violation: modifies_geometry_authority must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of observation state."""
        hash_input = {
            "observation_id": self.observation_id,
            "observation_category": self.observation_category,
            "workspace_id": self.workspace_id,
            "strategy_id": self.strategy_id,
            "fixture_package_id": self.fixture_package_id,
            "export_package_id": self.export_package_id,
            "geometry_authority_ref_ids": sorted(self.geometry_authority_ref_ids),
            "observation_text": self.observation_text,
            "severity": self.severity,
            "provenance_refs": sorted(self.provenance_refs),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_review_observation(
    observation_category: ReviewObservationCategory,
    observation_text: str,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    fixture_package_id: Optional[str] = None,
    export_package_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    severity: ObservationSeverity = "info",
    provenance_refs: Optional[List[str]] = None,
    review_required: bool = True,
) -> ManufacturingReviewObservation:
    """
    Create a manufacturing review observation.

    Captures review context without authorizing execution.
    """
    observation = ManufacturingReviewObservation(
        observation_category=observation_category,
        observation_text=observation_text,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        fixture_package_id=fixture_package_id,
        export_package_id=export_package_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids or [],
        severity=severity,
        provenance_refs=provenance_refs or [],
        review_required=review_required,
    )
    observation.deterministic_observation_hash = observation.compute_hash()
    return observation


def create_topology_warning(
    observation_text: str,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    fixture_package_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    severity: ObservationSeverity = "warning",
) -> ManufacturingReviewObservation:
    """Create a topology warning observation."""
    return create_review_observation(
        observation_category="topology_warning",
        observation_text=observation_text,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        fixture_package_id=fixture_package_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids,
        severity=severity,
    )


def create_fixture_warning(
    observation_text: str,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    fixture_package_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    severity: ObservationSeverity = "warning",
) -> ManufacturingReviewObservation:
    """Create a fixture warning observation."""
    return create_review_observation(
        observation_category="fixture_warning",
        observation_text=observation_text,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        fixture_package_id=fixture_package_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids,
        severity=severity,
    )


def create_export_review_note(
    observation_text: str,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    export_package_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    severity: ObservationSeverity = "info",
) -> ManufacturingReviewObservation:
    """Create an export review note observation."""
    return create_review_observation(
        observation_category="export_review_note",
        observation_text=observation_text,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        export_package_id=export_package_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids,
        severity=severity,
    )


def create_review_rationale(
    observation_text: str,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    fixture_package_id: Optional[str] = None,
    export_package_id: Optional[str] = None,
    provenance_refs: Optional[List[str]] = None,
) -> ManufacturingReviewObservation:
    """Create a review rationale observation."""
    return create_review_observation(
        observation_category="review_rationale",
        observation_text=observation_text,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        fixture_package_id=fixture_package_id,
        export_package_id=export_package_id,
        provenance_refs=provenance_refs,
        severity="info",
    )


def create_provenance_warning(
    observation_text: str,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    provenance_refs: Optional[List[str]] = None,
    severity: ObservationSeverity = "warning",
) -> ManufacturingReviewObservation:
    """Create a provenance warning observation."""
    return create_review_observation(
        observation_category="provenance_warning",
        observation_text=observation_text,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        provenance_refs=provenance_refs,
        severity=severity,
    )


def add_provenance_ref_to_observation(
    observation: ManufacturingReviewObservation,
    provenance_ref: str,
) -> ManufacturingReviewObservation:
    """Add a provenance reference to an observation."""
    if provenance_ref not in observation.provenance_refs:
        observation.provenance_refs.append(provenance_ref)
        observation.deterministic_observation_hash = observation.compute_hash()
    return observation


def add_geometry_authority_ref_to_observation(
    observation: ManufacturingReviewObservation,
    geometry_authority_ref_id: str,
) -> ManufacturingReviewObservation:
    """Add a geometry authority reference to an observation."""
    if geometry_authority_ref_id not in observation.geometry_authority_ref_ids:
        observation.geometry_authority_ref_ids.append(geometry_authority_ref_id)
        observation.deterministic_observation_hash = observation.compute_hash()
    return observation


def validate_observation(
    observation: ManufacturingReviewObservation,
) -> tuple[bool, List[str]]:
    """
    Validate that an observation is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if observation.execution_authorized:
        issues.append("execution_authorized must be False")

    if observation.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if observation.modifies_geometry_authority:
        issues.append("modifies_geometry_authority must be False")

    if not observation.observation_text.strip():
        issues.append("observation_text cannot be empty")

    if not observation.workspace_id and not observation.strategy_id:
        issues.append("Observation should reference a workspace or strategy")

    return len(issues) == 0, issues


def build_observation_hash(observation: ManufacturingReviewObservation) -> str:
    """Build deterministic hash for an observation."""
    return observation.compute_hash()


def is_critical_observation(observation: ManufacturingReviewObservation) -> bool:
    """Check if observation is critical severity."""
    return observation.severity == "critical"


def is_warning_observation(observation: ManufacturingReviewObservation) -> bool:
    """Check if observation is warning severity."""
    return observation.severity == "warning"


def requires_immediate_review(observation: ManufacturingReviewObservation) -> bool:
    """Check if observation requires immediate review."""
    return observation.severity == "critical" and observation.review_required
