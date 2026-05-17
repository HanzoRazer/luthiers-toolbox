"""
Canonical Ontology Registry

CAM Dev Order 7M: Canonical vocabulary authority for the repository.

This module establishes canonical semantic ownership across:
  - CAM
  - MRP
  - Governance
  - Morphology
  - Runtime contracts
  - Future domains

7M invariants:
  - immutable = true (always)
  - ontology_authoritative = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7M makes ontology drift visible. It does not automatically repair
  ontology drift.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

GOVERNANCE_TIERS = {
    1: "Structural / Ontology Governance",
    2: "Domain Governance",
    3: "Operational Policies",
}


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class OntologyRegistrationError(Exception):
    """Raised when ontology term registration fails."""
    pass


class DuplicateTermError(OntologyRegistrationError):
    """Raised when attempting to register a duplicate term."""
    pass


class ImmutableTermError(OntologyRegistrationError):
    """Raised when attempting to modify an immutable term."""
    pass


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class CanonicalOntologyTerm(BaseModel):
    """
    Canonical ontology term with ownership and semantic authority.

    7M invariants (model-enforced):
      - immutable = true (always)
      - ontology_authoritative = true (always)
    """

    term: str = Field(..., description="Canonical term identifier")

    canonical_definition: str = Field(
        ...,
        description="Authoritative definition of the term"
    )

    owning_domain: str = Field(
        ...,
        description="Domain that owns this term's definition"
    )

    owning_governance_tier: int = Field(
        ...,
        ge=1,
        le=3,
        description="Governance tier (1=Structural, 2=Domain, 3=Operational)"
    )

    canonical_contracts: List[str] = Field(
        default_factory=list,
        description="Contracts that depend on this term's semantics"
    )

    prohibited_reinterpretations: List[str] = Field(
        default_factory=list,
        description="Explicitly prohibited reinterpretations"
    )

    lifecycle_semantics: Optional[List[str]] = Field(
        default=None,
        description="Lifecycle vocabulary for this term (e.g., ['green', 'yellow', 'red'])"
    )

    aliases: List[str] = Field(
        default_factory=list,
        description="Accepted aliases for this term"
    )

    # 7M invariants
    immutable: bool = Field(
        default=True,
        description="Always true — canonical terms are immutable"
    )
    ontology_authoritative: bool = Field(
        default=True,
        description="Always true — canonical terms are authoritative"
    )

    # Metadata
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 7M invariant validators
    @field_validator("immutable", mode="before")
    @classmethod
    def enforce_immutable(cls, v: Any) -> bool:
        if v is False:
            raise ValueError(
                "7M invariant violation: immutable must be true"
            )
        return True

    @field_validator("ontology_authoritative", mode="before")
    @classmethod
    def enforce_authoritative(cls, v: Any) -> bool:
        if v is False:
            raise ValueError(
                "7M invariant violation: ontology_authoritative must be true"
            )
        return True

    @model_validator(mode="after")
    def validate_invariants(self) -> "CanonicalOntologyTerm":
        """Validate all 7M invariants after model construction."""
        if not self.immutable:
            raise ValueError(
                "7M invariant violation: immutable must be true"
            )
        if not self.ontology_authoritative:
            raise ValueError(
                "7M invariant violation: ontology_authoritative must be true"
            )
        return self


class CanonicalOntologyTermSummary(BaseModel):
    """Summary of a canonical ontology term for listing."""

    term: str
    owning_domain: str
    owning_governance_tier: int
    alias_count: int
    has_lifecycle_semantics: bool
    immutable: bool = True
    ontology_authoritative: bool = True

    @field_validator("immutable", mode="before")
    @classmethod
    def enforce_immutable(cls, v: Any) -> bool:
        return True

    @field_validator("ontology_authoritative", mode="before")
    @classmethod
    def enforce_authoritative(cls, v: Any) -> bool:
        return True


# -----------------------------------------------------------------------------
# In-Memory Indexes
# -----------------------------------------------------------------------------

# term -> CanonicalOntologyTerm
CANONICAL_ONTOLOGY_INDEX: Dict[str, CanonicalOntologyTerm] = {}

# domain -> list of terms
ONTOLOGY_DOMAIN_INDEX: Dict[str, List[str]] = {}

# term -> domain (reverse lookup)
ONTOLOGY_TERM_DOMAIN_INDEX: Dict[str, str] = {}

# alias -> canonical term
ONTOLOGY_ALIAS_INDEX: Dict[str, str] = {}


# -----------------------------------------------------------------------------
# Registry Operations
# -----------------------------------------------------------------------------

def register_canonical_term(term: CanonicalOntologyTerm) -> None:
    """
    Register a canonical ontology term.

    Raises:
        DuplicateTermError: If term already exists
    """
    term_key = term.term.lower()

    if term_key in CANONICAL_ONTOLOGY_INDEX:
        raise DuplicateTermError(
            f"Canonical term already registered: {term.term}"
        )

    # Check alias collisions
    for alias in term.aliases:
        alias_key = alias.lower()
        if alias_key in ONTOLOGY_ALIAS_INDEX:
            existing_term = ONTOLOGY_ALIAS_INDEX[alias_key]
            raise DuplicateTermError(
                f"Alias '{alias}' already registered for term '{existing_term}'"
            )
        if alias_key in CANONICAL_ONTOLOGY_INDEX:
            raise DuplicateTermError(
                f"Alias '{alias}' conflicts with existing canonical term"
            )

    # Register term
    CANONICAL_ONTOLOGY_INDEX[term_key] = term

    # Update domain index
    domain = term.owning_domain
    if domain not in ONTOLOGY_DOMAIN_INDEX:
        ONTOLOGY_DOMAIN_INDEX[domain] = []
    ONTOLOGY_DOMAIN_INDEX[domain].append(term.term)

    # Update reverse lookup
    ONTOLOGY_TERM_DOMAIN_INDEX[term_key] = domain

    # Register aliases
    for alias in term.aliases:
        ONTOLOGY_ALIAS_INDEX[alias.lower()] = term.term


def get_canonical_term(term: str) -> Optional[CanonicalOntologyTerm]:
    """Get a canonical term by name or alias."""
    term_key = term.lower()

    # Direct lookup
    if term_key in CANONICAL_ONTOLOGY_INDEX:
        return CANONICAL_ONTOLOGY_INDEX[term_key]

    # Alias lookup
    if term_key in ONTOLOGY_ALIAS_INDEX:
        canonical_term = ONTOLOGY_ALIAS_INDEX[term_key]
        return CANONICAL_ONTOLOGY_INDEX.get(canonical_term.lower())

    return None


def list_canonical_terms() -> List[CanonicalOntologyTerm]:
    """List all canonical terms."""
    return list(CANONICAL_ONTOLOGY_INDEX.values())


def list_terms_for_domain(domain: str) -> List[CanonicalOntologyTerm]:
    """List all canonical terms for a domain."""
    terms = ONTOLOGY_DOMAIN_INDEX.get(domain, [])
    return [
        CANONICAL_ONTOLOGY_INDEX[t.lower()]
        for t in terms
        if t.lower() in CANONICAL_ONTOLOGY_INDEX
    ]


def get_domain_for_term(term: str) -> Optional[str]:
    """Get the owning domain for a term."""
    return ONTOLOGY_TERM_DOMAIN_INDEX.get(term.lower())


def list_domains() -> List[str]:
    """List all registered domains."""
    return list(ONTOLOGY_DOMAIN_INDEX.keys())


def resolve_alias(alias: str) -> Optional[str]:
    """Resolve an alias to its canonical term."""
    return ONTOLOGY_ALIAS_INDEX.get(alias.lower())


def clear_ontology_registry() -> None:
    """Clear all ontology indexes (for testing)."""
    CANONICAL_ONTOLOGY_INDEX.clear()
    ONTOLOGY_DOMAIN_INDEX.clear()
    ONTOLOGY_TERM_DOMAIN_INDEX.clear()
    ONTOLOGY_ALIAS_INDEX.clear()


# -----------------------------------------------------------------------------
# Summary Helper
# -----------------------------------------------------------------------------

def to_summary(term: CanonicalOntologyTerm) -> CanonicalOntologyTermSummary:
    """Convert a term to its summary representation."""
    return CanonicalOntologyTermSummary(
        term=term.term,
        owning_domain=term.owning_domain,
        owning_governance_tier=term.owning_governance_tier,
        alias_count=len(term.aliases),
        has_lifecycle_semantics=term.lifecycle_semantics is not None,
        immutable=True,
        ontology_authoritative=True,
    )


# -----------------------------------------------------------------------------
# Initial Canonical Vocabulary (Hard-coded at module load)
# -----------------------------------------------------------------------------

INITIAL_CANONICAL_VOCABULARY: List[Dict[str, Any]] = [
    {
        "term": "translator",
        "canonical_definition": (
            "A governed component that transforms geometry or intent into "
            "a target format (e.g., DXF, G-code) under explicit authorization."
        ),
        "owning_domain": "CAM",
        "owning_governance_tier": 2,
        "canonical_contracts": [
            "TranslatorCapabilityContract",
            "TranslationArtifactContract",
        ],
        "prohibited_reinterpretations": [
            "runtime_dispatch_engine",
            "automatic_converter",
            "plugin_executor",
        ],
        "lifecycle_semantics": ["registered", "validated", "authorized", "quarantined"],
        "aliases": ["translation_engine", "format_translator"],
    },
    {
        "term": "runtime",
        "canonical_definition": (
            "Execution environment context that is explicitly separated from "
            "governance authority and requires explicit authorization."
        ),
        "owning_domain": "Runtime Governance",
        "owning_governance_tier": 1,
        "canonical_contracts": ["RuntimeGovernanceContract"],
        "prohibited_reinterpretations": [
            "automatic_execution_layer",
            "ungoverned_dispatch",
        ],
        "lifecycle_semantics": ["absent", "quarantined", "authorized"],
        "aliases": ["execution_runtime", "runtime_environment"],
    },
    {
        "term": "intent",
        "canonical_definition": (
            "Declared manufacturing purpose that flows from geometry through "
            "governance to translator without runtime reinterpretation."
        ),
        "owning_domain": "CAM",
        "owning_governance_tier": 2,
        "canonical_contracts": ["IntentContract", "GeometryIntentContract"],
        "prohibited_reinterpretations": [
            "runtime_inferred_intent",
            "automatic_intent_detection",
        ],
        "lifecycle_semantics": None,
        "aliases": ["manufacturing_intent", "declared_intent"],
    },
    {
        "term": "provenance",
        "canonical_definition": (
            "Immutable lineage chain recording the complete history of "
            "governance decisions, transformations, and evidence."
        ),
        "owning_domain": "Governance",
        "owning_governance_tier": 1,
        "canonical_contracts": ["ProvenanceLineageContract"],
        "prohibited_reinterpretations": [
            "mutable_history",
            "runtime_generated_provenance",
        ],
        "lifecycle_semantics": None,
        "aliases": ["lineage", "governance_provenance"],
    },
    {
        "term": "morphology",
        "canonical_definition": (
            "Semantic structure describing instrument body shape, regions, "
            "and topology under MRP governance."
        ),
        "owning_domain": "MRP",
        "owning_governance_tier": 2,
        "canonical_contracts": ["MorphologyContract", "TopologyContract"],
        "prohibited_reinterpretations": [
            "runtime_computed_morphology",
            "automatic_shape_inference",
        ],
        "lifecycle_semantics": ["draft", "validated", "canonical"],
        "aliases": ["body_morphology", "instrument_morphology"],
    },
    {
        "term": "validation",
        "canonical_definition": (
            "Governance-owned verification of contracts, constraints, and "
            "invariants without execution authority."
        ),
        "owning_domain": "Governance",
        "owning_governance_tier": 1,
        "canonical_contracts": ["ValidationContract"],
        "prohibited_reinterpretations": [
            "runtime_validation",
            "automatic_approval",
        ],
        "lifecycle_semantics": ["pending", "passed", "failed", "blocked"],
        "aliases": ["governance_validation", "contract_validation"],
    },
    {
        "term": "execution",
        "canonical_definition": (
            "Runtime invocation of translator or serializer that requires "
            "explicit governance authorization and is prohibited by default."
        ),
        "owning_domain": "Runtime Governance",
        "owning_governance_tier": 1,
        "canonical_contracts": ["ExecutionAuthorizationContract"],
        "prohibited_reinterpretations": [
            "automatic_execution",
            "ungoverned_invocation",
        ],
        "lifecycle_semantics": ["prohibited", "quarantined", "authorized"],
        "aliases": ["translator_execution", "runtime_execution"],
    },
    {
        "term": "readiness",
        "canonical_definition": (
            "Governance evaluation of whether a translator or artifact meets "
            "all prerequisites for the next governance stage."
        ),
        "owning_domain": "CAM Governance",
        "owning_governance_tier": 2,
        "canonical_contracts": ["ReadinessEvaluationContract"],
        "prohibited_reinterpretations": [
            "automatic_readiness_inference",
            "runtime_readiness_check",
        ],
        "lifecycle_semantics": ["green", "yellow", "red"],
        "aliases": ["governance_readiness", "translator_readiness"],
    },
    {
        "term": "quarantine",
        "canonical_definition": (
            "Governance state that isolates a translator or artifact from "
            "execution while preserving evidence for review."
        ),
        "owning_domain": "CAM Governance",
        "owning_governance_tier": 2,
        "canonical_contracts": ["QuarantineContract", "FreezeManifestContract"],
        "prohibited_reinterpretations": [
            "temporary_disable",
            "runtime_isolation",
        ],
        "lifecycle_semantics": ["active", "frozen", "released"],
        "aliases": ["execution_quarantine", "governance_quarantine"],
    },
    {
        "term": "topology",
        "canonical_definition": (
            "Semantic structure describing spatial relationships, regions, "
            "and connectivity under MRP governance."
        ),
        "owning_domain": "MRP",
        "owning_governance_tier": 2,
        "canonical_contracts": ["TopologyContract", "RegionContract"],
        "prohibited_reinterpretations": [
            "runtime_topology_inference",
            "automatic_region_detection",
        ],
        "lifecycle_semantics": ["draft", "validated", "canonical"],
        "aliases": ["body_topology", "spatial_topology"],
    },
    {
        "term": "serialization",
        "canonical_definition": (
            "Governed transformation of internal representation to external "
            "format that requires explicit translator authorization."
        ),
        "owning_domain": "Translator Governance",
        "owning_governance_tier": 2,
        "canonical_contracts": ["SerializationContract"],
        "prohibited_reinterpretations": [
            "automatic_serialization",
            "runtime_format_conversion",
        ],
        "lifecycle_semantics": ["prohibited", "authorized"],
        "aliases": ["format_serialization", "export_serialization"],
    },
    {
        "term": "artifact",
        "canonical_definition": (
            "Governed output of a translator that carries provenance, "
            "authorization evidence, and immutable governance state."
        ),
        "owning_domain": "CAM Governance",
        "owning_governance_tier": 2,
        "canonical_contracts": [
            "TranslationArtifactContract",
            "ArtifactProvenanceContract",
        ],
        "prohibited_reinterpretations": [
            "runtime_generated_output",
            "ungoverned_file",
        ],
        "lifecycle_semantics": ["draft", "authorized", "exported"],
        "aliases": ["translation_artifact", "governance_artifact"],
    },
    {
        "term": "geometry_authority",
        "canonical_definition": (
            "Canonical source of geometric truth for instrument shapes, "
            "owned by Geometry domain and consumed by downstream systems."
        ),
        "owning_domain": "Geometry",
        "owning_governance_tier": 2,
        "canonical_contracts": ["GeometryAuthorityContract"],
        "prohibited_reinterpretations": [
            "runtime_geometry_source",
            "computed_authority",
        ],
        "lifecycle_semantics": None,
        "aliases": ["canonical_geometry", "geometry_source"],
    },
    {
        "term": "runtime_authority",
        "canonical_definition": (
            "Governance layer that controls what runtime operations are "
            "permitted and under what conditions."
        ),
        "owning_domain": "Runtime Governance",
        "owning_governance_tier": 1,
        "canonical_contracts": ["RuntimeAuthorityContract"],
        "prohibited_reinterpretations": [
            "automatic_runtime_control",
            "self_authorizing_runtime",
        ],
        "lifecycle_semantics": ["absent", "governed", "authorized"],
        "aliases": ["execution_authority", "runtime_governance_authority"],
    },
]


def _seed_initial_vocabulary() -> None:
    """Seed the initial canonical vocabulary at module load."""
    for term_data in INITIAL_CANONICAL_VOCABULARY:
        term = CanonicalOntologyTerm(**term_data)
        try:
            register_canonical_term(term)
        except DuplicateTermError:
            pass


# Seed on module load
_seed_initial_vocabulary()
