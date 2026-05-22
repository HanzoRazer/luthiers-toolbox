"""
Federated Semantic Reference

CAM Dev Order 7X: Cross-domain semantic federation.

Provides:
  - FederatedDomainType taxonomy
  - SemanticRelationshipType taxonomy
  - FederatedSemanticReference model
  - Reference validation and hash computation

7X invariants:
  - preserves_authority_boundary: default True
  - authority_override_attempted: always False in valid refs
  - ontology_mutation_attempted: always False in valid refs
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Domains may reference one another.
  Domains may not absorb one another's authority.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


FederatedDomainType = Literal[
    "cam",
    "geometry",
    "morphology",
    "topology",
    "acoustics",
    "runtime_governance",
    "translator_governance",
    "review_governance",
]

SemanticRelationshipType = Literal[
    "references",
    "derives_from",
    "observes",
    "validates",
    "annotates",
    "packages",
    "replays",
    "shares_provenance_with",
    "shares_continuity_with",
]


class FederatedSemanticReference(BaseModel):
    """
    Cross-domain semantic reference.

    Links concepts across domain boundaries without collapsing authority.

    7X invariants (model-enforced):
      - authority_override_attempted: must be False
      - ontology_mutation_attempted: must be False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    federation_ref_id: str = Field(
        default_factory=lambda: f"fsr-{uuid4().hex[:12]}",
        description="Unique federation reference identifier"
    )

    source_domain: FederatedDomainType = Field(
        ...,
        description="Domain that owns the source reference"
    )
    target_domain: FederatedDomainType = Field(
        ...,
        description="Domain that owns the target reference"
    )

    relationship_type: SemanticRelationshipType = Field(
        ...,
        description="Type of semantic relationship"
    )

    source_ref_id: str = Field(
        ...,
        description="Reference ID within source domain"
    )
    target_ref_id: str = Field(
        ...,
        description="Reference ID within target domain"
    )

    preserves_authority_boundary: bool = Field(
        default=True,
        description="Whether this reference preserves domain authority boundaries"
    )

    authority_override_attempted: bool = Field(
        default=False,
        description="Flag for authority override attempt detection"
    )
    ontology_mutation_attempted: bool = Field(
        default=False,
        description="Flag for ontology mutation attempt detection"
    )

    provenance_refs: List[str] = Field(
        default_factory=list,
        description="Provenance reference chain"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7X does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7X does not allow machine output"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Issues blocking federation validity"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_federation_hash: str = Field(
        default="",
        description="Deterministic hash of federation state"
    )

    @model_validator(mode="after")
    def enforce_7x_invariants(self) -> "FederatedSemanticReference":
        """Enforce 7X invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7X invariant violation: execution_authorized must be False — "
                "7X does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7X invariant violation: machine_output_allowed must be False — "
                "7X does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of federation state."""
        hash_input = {
            "source_domain": self.source_domain,
            "target_domain": self.target_domain,
            "relationship_type": self.relationship_type,
            "source_ref_id": self.source_ref_id,
            "target_ref_id": self.target_ref_id,
            "preserves_authority_boundary": self.preserves_authority_boundary,
            "authority_override_attempted": self.authority_override_attempted,
            "ontology_mutation_attempted": self.ontology_mutation_attempted,
            "provenance_refs": sorted(self.provenance_refs),
            "blocking_issues": sorted(self.blocking_issues),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_federated_semantic_reference(
    source_domain: FederatedDomainType,
    target_domain: FederatedDomainType,
    relationship_type: SemanticRelationshipType,
    source_ref_id: str,
    target_ref_id: str,
    provenance_refs: List[str] | None = None,
) -> FederatedSemanticReference:
    """
    Create a federated semantic reference.

    Validates authority boundaries and computes deterministic hash.
    """
    ref = FederatedSemanticReference(
        source_domain=source_domain,
        target_domain=target_domain,
        relationship_type=relationship_type,
        source_ref_id=source_ref_id,
        target_ref_id=target_ref_id,
        provenance_refs=provenance_refs or [],
    )

    # Detect same-domain false federation
    if source_domain == target_domain:
        if relationship_type in ("shares_provenance_with", "shares_continuity_with"):
            ref.warnings.append(
                f"Same-domain ({source_domain}) reference with cross-domain relationship type"
            )

    ref.deterministic_federation_hash = ref.compute_hash()
    return ref


def validate_federated_semantic_reference(
    ref: FederatedSemanticReference,
) -> Tuple[bool, List[str]]:
    """
    Validate that a federation reference is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if ref.execution_authorized:
        issues.append("execution_authorized must be False")

    if ref.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if ref.authority_override_attempted:
        issues.append("authority_override_attempted indicates invalid federation")

    if ref.ontology_mutation_attempted:
        issues.append("ontology_mutation_attempted indicates invalid federation")

    if not ref.preserves_authority_boundary:
        issues.append("preserves_authority_boundary is False — boundary violation")

    if not ref.source_ref_id:
        issues.append("source_ref_id is required")

    if not ref.target_ref_id:
        issues.append("target_ref_id is required")

    return len(issues) == 0, issues


def detect_authority_override(ref: FederatedSemanticReference) -> bool:
    """
    Detect if a reference attempts authority override.

    Authority override conditions:
      - preserves_authority_boundary == False
      - authority_override_attempted == True
      - ontology_mutation_attempted == True
      - execution_authorized or machine_output_allowed True
      - Same domain claiming cross-domain semantics inappropriately
    """
    if not ref.preserves_authority_boundary:
        return True
    if ref.authority_override_attempted:
        return True
    if ref.ontology_mutation_attempted:
        return True
    if ref.execution_authorized:
        return True
    if ref.machine_output_allowed:
        return True
    return False


def detect_semantic_overlap(
    ref1: FederatedSemanticReference,
    ref2: FederatedSemanticReference,
) -> bool:
    """
    Detect if two references have semantic overlap.

    Overlap occurs when both references target the same entity
    from different sources with potentially conflicting relationships.
    """
    if ref1.target_ref_id != ref2.target_ref_id:
        return False
    if ref1.target_domain != ref2.target_domain:
        return False
    if ref1.source_domain == ref2.source_domain:
        return False
    return True


def is_cross_domain_reference(ref: FederatedSemanticReference) -> bool:
    """Check if reference spans different domains."""
    return ref.source_domain != ref.target_domain


def is_valid_federation_reference(ref: FederatedSemanticReference) -> bool:
    """Check if reference is valid for federation."""
    is_valid, _ = validate_federated_semantic_reference(ref)
    return is_valid


def build_federation_hash(ref: FederatedSemanticReference) -> str:
    """Build deterministic hash for a federation reference."""
    return ref.compute_hash()


def add_provenance_ref(
    ref: FederatedSemanticReference,
    provenance_ref: str,
) -> FederatedSemanticReference:
    """Add a provenance reference."""
    if provenance_ref not in ref.provenance_refs:
        ref.provenance_refs.append(provenance_ref)
        ref.deterministic_federation_hash = ref.compute_hash()
    return ref


def add_warning(
    ref: FederatedSemanticReference,
    warning: str,
) -> FederatedSemanticReference:
    """Add a warning to the reference."""
    if warning not in ref.warnings:
        ref.warnings.append(warning)
    return ref


def add_blocking_issue(
    ref: FederatedSemanticReference,
    issue: str,
) -> FederatedSemanticReference:
    """Add a blocking issue to the reference."""
    if issue not in ref.blocking_issues:
        ref.blocking_issues.append(issue)
        ref.deterministic_federation_hash = ref.compute_hash()
    return ref


def mark_authority_override_attempted(
    ref: FederatedSemanticReference,
) -> FederatedSemanticReference:
    """Mark that an authority override was attempted."""
    ref.authority_override_attempted = True
    ref.blocking_issues.append("Authority override attempted")
    ref.deterministic_federation_hash = ref.compute_hash()
    return ref


def mark_ontology_mutation_attempted(
    ref: FederatedSemanticReference,
) -> FederatedSemanticReference:
    """Mark that an ontology mutation was attempted."""
    ref.ontology_mutation_attempted = True
    ref.blocking_issues.append("Ontology mutation attempted")
    ref.deterministic_federation_hash = ref.compute_hash()
    return ref


def get_reference_summary(ref: FederatedSemanticReference) -> Dict[str, Any]:
    """Get a summary of the federation reference."""
    return {
        "federation_ref_id": ref.federation_ref_id,
        "source_domain": ref.source_domain,
        "target_domain": ref.target_domain,
        "relationship_type": ref.relationship_type,
        "source_ref_id": ref.source_ref_id,
        "target_ref_id": ref.target_ref_id,
        "is_cross_domain": is_cross_domain_reference(ref),
        "preserves_authority_boundary": ref.preserves_authority_boundary,
        "authority_override_detected": detect_authority_override(ref),
        "warning_count": len(ref.warnings),
        "blocking_issue_count": len(ref.blocking_issues),
    }
