"""
Federation Drift Baseline

CAM Dev Order 7Y: Federation CI drift baselines.

Provides:
  - FederationDriftBaseline model
  - Baseline hash computation
  - Immutable baseline registration

7Y invariants:
  - authority_override_allowed: default False
  - ontology_mutation_allowed: default False
  - execution_authorized: always False
  - machine_output_allowed: always False
  - baselines are immutable once registered

Core principle:
  Baselines record expected semantic health.
  Baselines do not repair drift.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class FederationDriftBaseline(BaseModel):
    """
    Federation drift baseline for CI enforcement.

    Records expected federation state for comparison.
    Immutable once registered.

    7Y invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    baseline_id: str = Field(
        default_factory=lambda: f"fdb-{uuid4().hex[:12]}",
        description="Unique baseline identifier"
    )

    baseline_name: str = Field(
        ...,
        description="Human-readable baseline name"
    )

    expected_federation_ref_count: Optional[int] = Field(
        default=None,
        description="Expected number of federation references"
    )
    expected_continuity_record_count: Optional[int] = Field(
        default=None,
        description="Expected number of continuity records"
    )
    expected_package_count: Optional[int] = Field(
        default=None,
        description="Expected number of federated packages"
    )

    allowed_warning_count: int = Field(
        default=0,
        description="Maximum allowed warnings before WARN status"
    )
    allowed_fragmented_federation_count: int = Field(
        default=0,
        description="Maximum allowed fragmented federations before WARN"
    )

    authority_override_allowed: bool = Field(
        default=False,
        description="Whether authority overrides are allowed (should be False)"
    )
    ontology_mutation_allowed: bool = Field(
        default=False,
        description="Whether ontology mutations are allowed (should be False)"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7Y does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7Y does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_baseline_hash: str = Field(
        default="",
        description="Deterministic hash of baseline state"
    )

    @model_validator(mode="after")
    def enforce_7y_invariants(self) -> "FederationDriftBaseline":
        """Enforce 7Y invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7Y invariant violation: execution_authorized must be False — "
                "7Y does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7Y invariant violation: machine_output_allowed must be False — "
                "7Y does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of baseline state."""
        hash_input = {
            "baseline_name": self.baseline_name,
            "expected_federation_ref_count": self.expected_federation_ref_count,
            "expected_continuity_record_count": self.expected_continuity_record_count,
            "expected_package_count": self.expected_package_count,
            "allowed_warning_count": self.allowed_warning_count,
            "allowed_fragmented_federation_count": self.allowed_fragmented_federation_count,
            "authority_override_allowed": self.authority_override_allowed,
            "ontology_mutation_allowed": self.ontology_mutation_allowed,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_federation_drift_baseline(
    baseline_name: str,
    expected_federation_ref_count: Optional[int] = None,
    expected_continuity_record_count: Optional[int] = None,
    expected_package_count: Optional[int] = None,
    allowed_warning_count: int = 0,
    allowed_fragmented_federation_count: int = 0,
) -> FederationDriftBaseline:
    """
    Create a federation drift baseline.

    Baselines are immutable once registered.
    """
    baseline = FederationDriftBaseline(
        baseline_name=baseline_name,
        expected_federation_ref_count=expected_federation_ref_count,
        expected_continuity_record_count=expected_continuity_record_count,
        expected_package_count=expected_package_count,
        allowed_warning_count=allowed_warning_count,
        allowed_fragmented_federation_count=allowed_fragmented_federation_count,
    )
    baseline.deterministic_baseline_hash = baseline.compute_hash()
    return baseline


def validate_federation_drift_baseline(
    baseline: FederationDriftBaseline,
) -> Tuple[bool, List[str]]:
    """
    Validate that a baseline is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if baseline.execution_authorized:
        issues.append("execution_authorized must be False")

    if baseline.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not baseline.baseline_name:
        issues.append("baseline_name is required")

    if baseline.allowed_warning_count < 0:
        issues.append("allowed_warning_count cannot be negative")

    if baseline.allowed_fragmented_federation_count < 0:
        issues.append("allowed_fragmented_federation_count cannot be negative")

    return len(issues) == 0, issues


def is_baseline_valid(baseline: FederationDriftBaseline) -> bool:
    """Check if baseline is valid."""
    is_valid, _ = validate_federation_drift_baseline(baseline)
    return is_valid


def build_baseline_hash(baseline: FederationDriftBaseline) -> str:
    """Build deterministic hash for a baseline."""
    return baseline.compute_hash()


def get_baseline_summary(baseline: FederationDriftBaseline) -> Dict[str, Any]:
    """Get a summary of the baseline."""
    return {
        "baseline_id": baseline.baseline_id,
        "baseline_name": baseline.baseline_name,
        "expected_federation_ref_count": baseline.expected_federation_ref_count,
        "expected_continuity_record_count": baseline.expected_continuity_record_count,
        "expected_package_count": baseline.expected_package_count,
        "allowed_warning_count": baseline.allowed_warning_count,
        "allowed_fragmented_federation_count": baseline.allowed_fragmented_federation_count,
        "authority_override_allowed": baseline.authority_override_allowed,
        "ontology_mutation_allowed": baseline.ontology_mutation_allowed,
    }
