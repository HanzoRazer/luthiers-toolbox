"""
Ontology Authority Map

CAM Dev Order 7M: Semantic ownership mapping for canonical vocabulary.

This module provides authority queries:
  - Domain ownership lookups
  - Tier resolution
  - Authority conflict detection
  - Cross-domain ownership analysis

7M invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7M makes ontology drift visible. It does not automatically repair
  ontology drift.
"""

from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.cam.canonical_ontology_registry import (
    CANONICAL_ONTOLOGY_INDEX,
    ONTOLOGY_DOMAIN_INDEX,
    ONTOLOGY_TERM_DOMAIN_INDEX,
    CanonicalOntologyTerm,
    get_canonical_term,
    list_domains,
)


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class DomainOwnershipSummary(BaseModel):
    """Summary of a domain's ontology ownership."""

    domain: str = Field(..., description="Domain name")
    term_count: int = Field(..., description="Number of owned terms")
    terms: List[str] = Field(default_factory=list, description="Owned terms")
    governance_tiers: List[int] = Field(
        default_factory=list,
        description="Governance tiers present in this domain"
    )
    has_lifecycle_terms: bool = Field(
        default=False,
        description="Whether domain has terms with lifecycle semantics"
    )


class AuthorityClaimAnalysis(BaseModel):
    """Analysis of authority claims for a semantic concept."""

    concept: str = Field(..., description="Semantic concept being analyzed")
    claiming_domains: List[str] = Field(
        default_factory=list,
        description="Domains claiming authority over this concept"
    )
    canonical_owner: Optional[str] = Field(
        None,
        description="Canonical owner if registered"
    )
    has_collision: bool = Field(
        default=False,
        description="Whether multiple domains claim authority"
    )
    collision_details: Optional[str] = Field(
        None,
        description="Details of authority collision if present"
    )


class CrossDomainRelationship(BaseModel):
    """Relationship between two domains in the ontology."""

    domain_a: str
    domain_b: str
    shared_concepts: List[str] = Field(
        default_factory=list,
        description="Concepts that both domains reference"
    )
    potential_conflicts: List[str] = Field(
        default_factory=list,
        description="Concepts with potential authority conflicts"
    )
    lifecycle_compatibility: bool = Field(
        default=True,
        description="Whether lifecycle semantics are compatible"
    )


# -----------------------------------------------------------------------------
# Authority Map Queries
# -----------------------------------------------------------------------------

def get_domain_ownership_summary(domain: str) -> Optional[DomainOwnershipSummary]:
    """Get ownership summary for a domain."""
    if domain not in ONTOLOGY_DOMAIN_INDEX:
        return None

    terms = ONTOLOGY_DOMAIN_INDEX[domain]
    governance_tiers: Set[int] = set()
    has_lifecycle = False

    for term_name in terms:
        term = get_canonical_term(term_name)
        if term:
            governance_tiers.add(term.owning_governance_tier)
            if term.lifecycle_semantics:
                has_lifecycle = True

    return DomainOwnershipSummary(
        domain=domain,
        term_count=len(terms),
        terms=terms,
        governance_tiers=sorted(governance_tiers),
        has_lifecycle_terms=has_lifecycle,
    )


def get_all_domain_summaries() -> List[DomainOwnershipSummary]:
    """Get ownership summaries for all domains."""
    summaries = []
    for domain in list_domains():
        summary = get_domain_ownership_summary(domain)
        if summary:
            summaries.append(summary)
    return summaries


def get_terms_at_tier(tier: int) -> List[CanonicalOntologyTerm]:
    """Get all terms at a specific governance tier."""
    return [
        term for term in CANONICAL_ONTOLOGY_INDEX.values()
        if term.owning_governance_tier == tier
    ]


def analyze_authority_claim(concept: str) -> AuthorityClaimAnalysis:
    """
    Analyze authority claims for a semantic concept.

    Checks if the concept is registered and identifies potential
    authority collisions.
    """
    concept_lower = concept.lower()
    claiming_domains: List[str] = []
    canonical_owner: Optional[str] = None

    # Check if directly registered
    term = get_canonical_term(concept)
    if term:
        canonical_owner = term.owning_domain
        claiming_domains.append(term.owning_domain)

    # Check for similar terms (potential collisions)
    for term_name, registered_term in CANONICAL_ONTOLOGY_INDEX.items():
        # Check if concept appears in aliases
        if concept_lower in [a.lower() for a in registered_term.aliases]:
            if registered_term.owning_domain not in claiming_domains:
                claiming_domains.append(registered_term.owning_domain)

        # Check if concept is in prohibited reinterpretations
        if concept_lower in [p.lower() for p in registered_term.prohibited_reinterpretations]:
            if registered_term.owning_domain not in claiming_domains:
                claiming_domains.append(registered_term.owning_domain)

    has_collision = len(claiming_domains) > 1
    collision_details = None
    if has_collision:
        collision_details = (
            f"Multiple domains reference '{concept}': {claiming_domains}"
        )

    return AuthorityClaimAnalysis(
        concept=concept,
        claiming_domains=claiming_domains,
        canonical_owner=canonical_owner,
        has_collision=has_collision,
        collision_details=collision_details,
    )


def get_cross_domain_relationship(
    domain_a: str,
    domain_b: str,
) -> CrossDomainRelationship:
    """
    Analyze the relationship between two domains.

    Identifies shared concepts and potential conflicts.
    """
    terms_a = set(ONTOLOGY_DOMAIN_INDEX.get(domain_a, []))
    terms_b = set(ONTOLOGY_DOMAIN_INDEX.get(domain_b, []))

    # Find shared concepts (terms that reference each other)
    shared_concepts: List[str] = []
    potential_conflicts: List[str] = []

    for term_name in terms_a:
        term = get_canonical_term(term_name)
        if not term:
            continue

        # Check if term's contracts or aliases reference domain_b's terms
        for contract in term.canonical_contracts:
            for term_b_name in terms_b:
                if term_b_name.lower() in contract.lower():
                    shared_concepts.append(f"{term_name}->{term_b_name}")

    for term_name in terms_b:
        term = get_canonical_term(term_name)
        if not term:
            continue

        for contract in term.canonical_contracts:
            for term_a_name in terms_a:
                if term_a_name.lower() in contract.lower():
                    if f"{term_a_name}->{term_name}" not in shared_concepts:
                        shared_concepts.append(f"{term_name}->{term_a_name}")

    # Check lifecycle compatibility
    lifecycle_a: Set[str] = set()
    lifecycle_b: Set[str] = set()

    for term_name in terms_a:
        term = get_canonical_term(term_name)
        if term and term.lifecycle_semantics:
            lifecycle_a.update(term.lifecycle_semantics)

    for term_name in terms_b:
        term = get_canonical_term(term_name)
        if term and term.lifecycle_semantics:
            lifecycle_b.update(term.lifecycle_semantics)

    # Lifecycle compatibility: check for conflicting semantics
    lifecycle_compatible = True
    if lifecycle_a and lifecycle_b:
        # If both domains have lifecycle semantics, check for conflicts
        # (e.g., one uses "green/yellow/red", other uses "ready/pending/blocked")
        common = lifecycle_a.intersection(lifecycle_b)
        if not common and lifecycle_a and lifecycle_b:
            # No common lifecycle terms - potential drift
            potential_conflicts.append(
                f"Lifecycle drift: {domain_a}={list(lifecycle_a)}, "
                f"{domain_b}={list(lifecycle_b)}"
            )
            lifecycle_compatible = False

    return CrossDomainRelationship(
        domain_a=domain_a,
        domain_b=domain_b,
        shared_concepts=shared_concepts,
        potential_conflicts=potential_conflicts,
        lifecycle_compatibility=lifecycle_compatible,
    )


def get_tier_1_authority_terms() -> List[CanonicalOntologyTerm]:
    """Get all Tier 1 (Structural/Ontology) authority terms."""
    return get_terms_at_tier(1)


def get_tier_2_authority_terms() -> List[CanonicalOntologyTerm]:
    """Get all Tier 2 (Domain) authority terms."""
    return get_terms_at_tier(2)


def get_tier_3_authority_terms() -> List[CanonicalOntologyTerm]:
    """Get all Tier 3 (Operational) authority terms."""
    return get_terms_at_tier(3)


def get_lifecycle_terms() -> List[CanonicalOntologyTerm]:
    """Get all terms that have lifecycle semantics."""
    return [
        term for term in CANONICAL_ONTOLOGY_INDEX.values()
        if term.lifecycle_semantics
    ]


def get_lifecycle_vocabularies() -> Dict[str, List[str]]:
    """
    Get all lifecycle vocabularies grouped by domain.

    Returns:
        Dict mapping domain -> list of lifecycle terms used
    """
    result: Dict[str, Set[str]] = {}

    for term in CANONICAL_ONTOLOGY_INDEX.values():
        if term.lifecycle_semantics:
            domain = term.owning_domain
            if domain not in result:
                result[domain] = set()
            result[domain].update(term.lifecycle_semantics)

    return {k: sorted(v) for k, v in result.items()}
