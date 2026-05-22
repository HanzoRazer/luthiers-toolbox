"""
Post-Freeze Expansion Gate

CAM Dev Order 8A: Post-freeze expansion proposals with controlled gates.

Provides:
  - PostFreezeExpansionProposal model
  - Proposal hash computation
  - Target layer validation

8A invariants:
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Post-freeze proposals declare intent for human review.
  They do not authorize implementation, execution, or machine output.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


TargetLayer = Literal[
    "manufacturing_cognition",
    "geometry_authority",
    "strategy_export",
    "fixture_topology",
    "observational_replay",
    "runtime_governance",
    "future_execution_boundary",
]

ProposalState = Literal["draft", "submitted_for_review"]


class PostFreezeExpansionProposal(BaseModel):
    """
    Post-freeze expansion proposal.

    Declares intent to extend capability after governance freeze.
    Requires human review before any implementation.

    8A invariants (model-enforced):
      - implementation_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    proposal_id: str = Field(
        default_factory=lambda: f"pfep-{uuid4().hex[:12]}",
        description="Unique proposal identifier"
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Proposal title"
    )

    target_layer: TargetLayer = Field(
        ...,
        description="Target layer for proposed capability"
    )

    depends_on_freeze_id: Optional[str] = Field(
        default=None,
        description="Freeze ID this proposal extends (if any)"
    )

    proposed_capability: str = Field(
        ...,
        min_length=1,
        description="Description of proposed capability"
    )

    expected_artifacts: List[str] = Field(
        default_factory=list,
        description="Expected output artifacts"
    )

    governance_risks: List[str] = Field(
        default_factory=list,
        description="Identified governance risks"
    )

    required_reviews: List[str] = Field(
        default_factory=list,
        description="Required review types before implementation"
    )

    # Explicit mutation request fields (for RED gate detection)
    ontology_mutation_requested: bool = Field(
        default=False,
        description="Whether ontology mutation is requested"
    )

    baseline_rewrite_requested: bool = Field(
        default=False,
        description="Whether baseline rewrite is requested"
    )

    # 8A invariants
    implementation_authorized: bool = Field(
        default=False,
        description="Always False — 8A does not authorize implementation"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 8A does not authorize execution"
    )

    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 8A does not allow machine output"
    )

    proposal_state: ProposalState = Field(
        default="draft",
        description="Proposal state: draft or submitted_for_review"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_proposal_hash: str = Field(
        default="",
        description="Deterministic hash of proposal state"
    )

    @model_validator(mode="after")
    def enforce_8a_invariants(self) -> "PostFreezeExpansionProposal":
        """Enforce 8A invariants."""
        if self.implementation_authorized:
            raise ValueError(
                "8A invariant violation: implementation_authorized must be False — "
                "8A does not authorize implementation"
            )
        if self.execution_authorized:
            raise ValueError(
                "8A invariant violation: execution_authorized must be False — "
                "8A does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "8A invariant violation: machine_output_allowed must be False — "
                "8A does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of proposal state."""
        hash_input = {
            "title": self.title,
            "target_layer": self.target_layer,
            "depends_on_freeze_id": self.depends_on_freeze_id,
            "proposed_capability": self.proposed_capability,
            "expected_artifacts": sorted(self.expected_artifacts),
            "governance_risks": sorted(self.governance_risks),
            "required_reviews": sorted(self.required_reviews),
            "ontology_mutation_requested": self.ontology_mutation_requested,
            "baseline_rewrite_requested": self.baseline_rewrite_requested,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_post_freeze_proposal(
    title: str,
    target_layer: TargetLayer,
    proposed_capability: str,
    depends_on_freeze_id: Optional[str] = None,
    expected_artifacts: Optional[List[str]] = None,
    governance_risks: Optional[List[str]] = None,
    required_reviews: Optional[List[str]] = None,
    ontology_mutation_requested: bool = False,
    baseline_rewrite_requested: bool = False,
    proposal_state: ProposalState = "draft",
    metadata: Optional[Dict[str, Any]] = None,
) -> PostFreezeExpansionProposal:
    """
    Create a post-freeze expansion proposal.

    All proposals start with implementation_authorized=False.
    """
    proposal = PostFreezeExpansionProposal(
        title=title,
        target_layer=target_layer,
        proposed_capability=proposed_capability,
        depends_on_freeze_id=depends_on_freeze_id,
        expected_artifacts=expected_artifacts or [],
        governance_risks=governance_risks or [],
        required_reviews=required_reviews or [],
        ontology_mutation_requested=ontology_mutation_requested,
        baseline_rewrite_requested=baseline_rewrite_requested,
        proposal_state=proposal_state,
        metadata=metadata or {},
    )
    proposal.deterministic_proposal_hash = proposal.compute_hash()
    return proposal


def build_post_freeze_proposal_hash(proposal: PostFreezeExpansionProposal) -> str:
    """Build deterministic hash for a proposal."""
    return proposal.compute_hash()


def validate_post_freeze_proposal(
    proposal: PostFreezeExpansionProposal,
) -> tuple[bool, List[str]]:
    """
    Validate a post-freeze proposal.

    Returns (is_valid, issues).
    """
    issues: List[str] = []

    if not proposal.title:
        issues.append("Missing title")

    if not proposal.proposed_capability:
        issues.append("Missing proposed_capability")

    if proposal.implementation_authorized:
        issues.append("implementation_authorized must be False")

    if proposal.execution_authorized:
        issues.append("execution_authorized must be False")

    if proposal.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    return len(issues) == 0, issues


def is_proposal_valid(proposal: PostFreezeExpansionProposal) -> bool:
    """Check if proposal is valid."""
    is_valid, _ = validate_post_freeze_proposal(proposal)
    return is_valid


def get_proposal_summary(proposal: PostFreezeExpansionProposal) -> Dict[str, Any]:
    """Get proposal summary for API response."""
    return {
        "proposal_id": proposal.proposal_id,
        "title": proposal.title,
        "target_layer": proposal.target_layer,
        "depends_on_freeze_id": proposal.depends_on_freeze_id,
        "proposed_capability": proposal.proposed_capability,
        "expected_artifact_count": len(proposal.expected_artifacts),
        "governance_risk_count": len(proposal.governance_risks),
        "required_review_count": len(proposal.required_reviews),
        "ontology_mutation_requested": proposal.ontology_mutation_requested,
        "baseline_rewrite_requested": proposal.baseline_rewrite_requested,
        "implementation_authorized": proposal.implementation_authorized,
        "execution_authorized": proposal.execution_authorized,
        "machine_output_allowed": proposal.machine_output_allowed,
        "proposal_state": proposal.proposal_state,
        "created_at": proposal.created_at.isoformat(),
    }


VALID_TARGET_LAYERS: List[str] = [
    "manufacturing_cognition",
    "geometry_authority",
    "strategy_export",
    "fixture_topology",
    "observational_replay",
    "runtime_governance",
    "future_execution_boundary",
]


def is_valid_target_layer(layer: str) -> bool:
    """Check if a string is a valid target layer."""
    return layer in VALID_TARGET_LAYERS
