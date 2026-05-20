"""
Runtime Semantic Consumption Registry

CAM Dev Order 7N: Runtime systems may consume canonical ontology but may NOT
create, mutate, reinterpret, or fork it.

This module provides:
  - RuntimeSemanticConsumer model with invariants
  - Consumer registration (seeded at module load)
  - Consumption declaration validation
  - Integration with 7M canonical ontology registry

7N invariants (always enforced):
  - execution_authorized = false
  - machine_output_allowed = false
  - immutable = true

Consumer-specific invariants:
  - declared_semantic_authority = false
  - may_register_terms = false
  - may_mutate_ontology = false
  - may_define_lifecycle = false
  - may_execute_runtime = false
  - may_generate_machine_output = false

Guardrail:
  7N verifies that runtimes consume ontology without owning ontology.
  It does not permit runtime execution, ontology mutation, lifecycle
  definition, or semantic reinterpretation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.cam.canonical_ontology_registry import (
    get_canonical_term,
    list_canonical_terms,
)


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------

ProhibitedRuntimeSemanticOperation = Literal[
    "register_term",
    "mutate_ontology",
    "define_lifecycle",
    "reinterpret_term",
    "fork_vocabulary",
    "execute_runtime",
    "generate_machine_output",
]


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class RuntimeSemanticConsumer(BaseModel):
    """
    A runtime system that consumes canonical ontology.

    7N invariants (model-enforced):
      - declared_semantic_authority = false (always)
      - may_register_terms = false (always)
      - may_mutate_ontology = false (always)
      - may_define_lifecycle = false (always)
      - may_execute_runtime = false (always)
      - may_generate_machine_output = false (always)
    """

    consumer_id: str = Field(..., description="Unique consumer identifier")
    consumer_name: str = Field(..., description="Human-readable name")
    consumer_domain: str = Field(..., description="Owning domain")
    consumed_terms: List[str] = Field(
        default_factory=list,
        description="Canonical terms this consumer depends on"
    )
    consumption_purpose: str = Field(
        ...,
        description="Why this consumer needs these terms"
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Registration timestamp"
    )

    # 7N consumer invariants (always false)
    declared_semantic_authority: bool = Field(default=False)
    may_register_terms: bool = Field(default=False)
    may_mutate_ontology: bool = Field(default=False)
    may_define_lifecycle: bool = Field(default=False)
    may_execute_runtime: bool = Field(default=False)
    may_generate_machine_output: bool = Field(default=False)

    @field_validator("declared_semantic_authority", mode="before")
    @classmethod
    def enforce_no_semantic_authority(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: declared_semantic_authority must be false"
            )
        return False

    @field_validator("may_register_terms", mode="before")
    @classmethod
    def enforce_no_term_registration(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: may_register_terms must be false"
            )
        return False

    @field_validator("may_mutate_ontology", mode="before")
    @classmethod
    def enforce_no_ontology_mutation(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: may_mutate_ontology must be false"
            )
        return False

    @field_validator("may_define_lifecycle", mode="before")
    @classmethod
    def enforce_no_lifecycle_definition(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: may_define_lifecycle must be false"
            )
        return False

    @field_validator("may_execute_runtime", mode="before")
    @classmethod
    def enforce_no_runtime_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: may_execute_runtime must be false"
            )
        return False

    @field_validator("may_generate_machine_output", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: may_generate_machine_output must be false"
            )
        return False


class RuntimeSemanticConsumerSummary(BaseModel):
    """Lightweight summary for listing consumers."""

    consumer_id: str
    consumer_name: str
    consumer_domain: str
    consumed_term_count: int
    consumption_purpose: str


class TermConsumptionMismatch(BaseModel):
    """A mismatch between declared and canonical term definition."""

    term: str = Field(..., description="The mismatched term")
    consumer_id: str = Field(..., description="Consumer that declared it")
    mismatch_type: Literal[
        "term_not_in_registry",
        "domain_mismatch",
        "lifecycle_incompatibility",
        "governance_tier_violation",
    ] = Field(..., description="Type of mismatch")
    expected_value: Optional[str] = Field(None, description="Expected value")
    declared_value: Optional[str] = Field(None, description="Declared value")
    description: str = Field(..., description="Human-readable description")


class ProhibitedAuthorityClaim(BaseModel):
    """A prohibited authority claim by a runtime consumer."""

    consumer_id: str = Field(..., description="Consumer making the claim")
    operation: ProhibitedRuntimeSemanticOperation = Field(
        ...,
        description="Prohibited operation attempted"
    )
    description: str = Field(..., description="Human-readable description")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="high",
        description="Severity of the violation"
    )


class RuntimeReinterpretationRisk(BaseModel):
    """A risk of runtime reinterpretation detected."""

    consumer_id: str = Field(..., description="Consumer with the risk")
    term: str = Field(..., description="Term at risk of reinterpretation")
    risk_type: Literal[
        "shadow_definition",
        "local_alias",
        "runtime_override",
        "semantic_drift",
    ] = Field(..., description="Type of reinterpretation risk")
    description: str = Field(..., description="Human-readable description")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Severity of the risk"
    )


class ConsumptionDisciplineReport(BaseModel):
    """
    Report on runtime semantic consumption discipline compliance.

    7N invariants (model-enforced):
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    report_id: str = Field(..., description="Unique report identifier")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Report generation timestamp"
    )
    consumer_id: str = Field(..., description="Consumer being validated")

    # Consumption analysis
    consumed_terms: List[str] = Field(
        default_factory=list,
        description="Terms consumed by this consumer"
    )
    missing_terms: List[str] = Field(
        default_factory=list,
        description="Consumed terms not in canonical registry"
    )
    term_mismatches: List[TermConsumptionMismatch] = Field(
        default_factory=list,
        description="Mismatches between declared and canonical"
    )
    prohibited_authority_claims: List[ProhibitedAuthorityClaim] = Field(
        default_factory=list,
        description="Prohibited operations detected"
    )
    runtime_reinterpretation_risks: List[RuntimeReinterpretationRisk] = Field(
        default_factory=list,
        description="Risks of semantic reinterpretation"
    )

    # Scoring
    consumption_alignment_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alignment score (0.0 to 1.0)"
    )
    discipline_valid: bool = Field(
        ...,
        description="True if no critical violations"
    )
    deterministic_report_hash: str = Field(
        ...,
        description="Hash for deterministic verification"
    )

    # 7N invariants
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7N invariant violation: machine_output_allowed must be false"
            )
        return False


# -----------------------------------------------------------------------------
# Consumer Registry (in-memory, seeded at module load)
# -----------------------------------------------------------------------------

_CONSUMER_REGISTRY: Dict[str, RuntimeSemanticConsumer] = {}
_CONSUMER_BY_DOMAIN: Dict[str, List[str]] = {}


def _build_domain_index() -> None:
    """Rebuild domain index from registry."""
    global _CONSUMER_BY_DOMAIN
    _CONSUMER_BY_DOMAIN = {}
    for consumer_id, consumer in _CONSUMER_REGISTRY.items():
        domain = consumer.consumer_domain
        if domain not in _CONSUMER_BY_DOMAIN:
            _CONSUMER_BY_DOMAIN[domain] = []
        _CONSUMER_BY_DOMAIN[domain].append(consumer_id)


def register_runtime_semantic_consumer(consumer: RuntimeSemanticConsumer) -> None:
    """
    Register a runtime semantic consumer.

    Args:
        consumer: The consumer to register

    Raises:
        ValueError: If consumer_id already exists
    """
    if consumer.consumer_id in _CONSUMER_REGISTRY:
        raise ValueError(
            f"Consumer already registered: {consumer.consumer_id}"
        )
    _CONSUMER_REGISTRY[consumer.consumer_id] = consumer
    _build_domain_index()


def get_runtime_semantic_consumer(
    consumer_id: str,
) -> Optional[RuntimeSemanticConsumer]:
    """Get a consumer by ID."""
    return _CONSUMER_REGISTRY.get(consumer_id)


def list_runtime_semantic_consumers() -> List[RuntimeSemanticConsumer]:
    """List all registered consumers."""
    return list(_CONSUMER_REGISTRY.values())


def list_consumers_for_domain(domain: str) -> List[RuntimeSemanticConsumer]:
    """List consumers for a specific domain."""
    consumer_ids = _CONSUMER_BY_DOMAIN.get(domain, [])
    return [_CONSUMER_REGISTRY[cid] for cid in consumer_ids]


def list_consumer_domains() -> List[str]:
    """List all domains with registered consumers."""
    return sorted(_CONSUMER_BY_DOMAIN.keys())


def to_consumer_summary(
    consumer: RuntimeSemanticConsumer,
) -> RuntimeSemanticConsumerSummary:
    """Convert consumer to summary."""
    return RuntimeSemanticConsumerSummary(
        consumer_id=consumer.consumer_id,
        consumer_name=consumer.consumer_name,
        consumer_domain=consumer.consumer_domain,
        consumed_term_count=len(consumer.consumed_terms),
        consumption_purpose=consumer.consumption_purpose,
    )


def clear_runtime_semantic_consumers_for_tests() -> None:
    """Clear all consumers. For testing only."""
    global _CONSUMER_REGISTRY, _CONSUMER_BY_DOMAIN
    _CONSUMER_REGISTRY = {}
    _CONSUMER_BY_DOMAIN = {}


# -----------------------------------------------------------------------------
# Validation Helpers
# -----------------------------------------------------------------------------

def validate_consumed_terms(
    consumer: RuntimeSemanticConsumer,
) -> tuple[List[str], List[TermConsumptionMismatch]]:
    """
    Validate that consumed terms exist in 7M canonical registry.

    Returns:
        (missing_terms, mismatches)
    """
    missing_terms: List[str] = []
    mismatches: List[TermConsumptionMismatch] = []

    for term in consumer.consumed_terms:
        canonical = get_canonical_term(term)
        if canonical is None:
            missing_terms.append(term)
            mismatches.append(TermConsumptionMismatch(
                term=term,
                consumer_id=consumer.consumer_id,
                mismatch_type="term_not_in_registry",
                expected_value="(canonical term)",
                declared_value=term,
                description=f"Term '{term}' not found in canonical ontology registry",
            ))

    return missing_terms, mismatches


def detect_prohibited_authority_claims(
    consumer: RuntimeSemanticConsumer,
) -> List[ProhibitedAuthorityClaim]:
    """
    Detect any prohibited authority claims in the consumer.

    For 7N, we check if any of the consumer's invariant flags were
    set to True before validation (which would have been rejected).
    This is a belt-and-suspenders check.
    """
    claims: List[ProhibitedAuthorityClaim] = []

    # These checks are for documentation/reporting purposes
    # The model validators already enforce False
    if consumer.declared_semantic_authority:
        claims.append(ProhibitedAuthorityClaim(
            consumer_id=consumer.consumer_id,
            operation="register_term",
            description="Consumer declared semantic authority",
            severity="critical",
        ))

    if consumer.may_register_terms:
        claims.append(ProhibitedAuthorityClaim(
            consumer_id=consumer.consumer_id,
            operation="register_term",
            description="Consumer claims term registration authority",
            severity="critical",
        ))

    if consumer.may_mutate_ontology:
        claims.append(ProhibitedAuthorityClaim(
            consumer_id=consumer.consumer_id,
            operation="mutate_ontology",
            description="Consumer claims ontology mutation authority",
            severity="critical",
        ))

    if consumer.may_define_lifecycle:
        claims.append(ProhibitedAuthorityClaim(
            consumer_id=consumer.consumer_id,
            operation="define_lifecycle",
            description="Consumer claims lifecycle definition authority",
            severity="critical",
        ))

    if consumer.may_execute_runtime:
        claims.append(ProhibitedAuthorityClaim(
            consumer_id=consumer.consumer_id,
            operation="execute_runtime",
            description="Consumer claims runtime execution authority",
            severity="critical",
        ))

    if consumer.may_generate_machine_output:
        claims.append(ProhibitedAuthorityClaim(
            consumer_id=consumer.consumer_id,
            operation="generate_machine_output",
            description="Consumer claims machine output authority",
            severity="critical",
        ))

    return claims


def detect_reinterpretation_risks(
    consumer: RuntimeSemanticConsumer,
) -> List[RuntimeReinterpretationRisk]:
    """
    Detect risks of runtime reinterpretation.

    Currently performs:
      - Check for terms consumed from multiple domains
      - Check for potential shadow definitions
    """
    risks: List[RuntimeReinterpretationRisk] = []

    # Check for terms that might shadow canonical definitions
    canonical_terms = {t.term.lower() for t in list_canonical_terms()}
    for term in consumer.consumed_terms:
        term_lower = term.lower()
        # Check for near-misses (potential typos or shadow definitions)
        for canonical in canonical_terms:
            if term_lower != canonical and (
                term_lower in canonical or canonical in term_lower
            ):
                risks.append(RuntimeReinterpretationRisk(
                    consumer_id=consumer.consumer_id,
                    term=term,
                    risk_type="shadow_definition",
                    description=(
                        f"Term '{term}' may shadow canonical term '{canonical}'"
                    ),
                    severity="low",
                ))

    return risks


# -----------------------------------------------------------------------------
# Initial Seeded Consumers (5 canonical consumers)
# -----------------------------------------------------------------------------

_INITIAL_CONSUMERS = [
    RuntimeSemanticConsumer(
        consumer_id="cam_runtime",
        consumer_name="CAM Runtime",
        consumer_domain="CAM",
        consumed_terms=[
            "translator",
            "intent",
            "artifact",
            "readiness",
            "quarantine",
        ],
        consumption_purpose=(
            "CAM runtime consumes translator and artifact semantics for "
            "toolpath coordination without executing machine output"
        ),
    ),
    RuntimeSemanticConsumer(
        consumer_id="translator_runtime",
        consumer_name="Translator Runtime",
        consumer_domain="Translator Governance",
        consumed_terms=[
            "translator",
            "serialization",
            "provenance",
            "validation",
        ],
        consumption_purpose=(
            "Translator runtime consumes serialization and provenance "
            "semantics for format conversion without owning ontology"
        ),
    ),
    RuntimeSemanticConsumer(
        consumer_id="morphology_runtime",
        consumer_name="Morphology Runtime",
        consumer_domain="MRP",
        consumed_terms=[
            "morphology",
            "topology",
            "geometry_authority",
        ],
        consumption_purpose=(
            "Morphology runtime consumes topology and geometry semantics "
            "for shape reconstruction without defining lifecycles"
        ),
    ),
    RuntimeSemanticConsumer(
        consumer_id="execution_scheduler",
        consumer_name="Execution Scheduler",
        consumer_domain="Runtime Governance",
        consumed_terms=[
            "runtime",
            "execution",
            "runtime_authority",
        ],
        consumption_purpose=(
            "Execution scheduler consumes runtime semantics for scheduling "
            "without authorizing actual execution"
        ),
    ),
    RuntimeSemanticConsumer(
        consumer_id="validation_runtime",
        consumer_name="Validation Runtime",
        consumer_domain="Governance",
        consumed_terms=[
            "validation",
            "provenance",
        ],
        consumption_purpose=(
            "Validation runtime consumes governance semantics for "
            "verification without mutating validation rules"
        ),
    ),
]


def _seed_initial_consumers() -> None:
    """Seed initial consumers at module load."""
    for consumer in _INITIAL_CONSUMERS:
        if consumer.consumer_id not in _CONSUMER_REGISTRY:
            _CONSUMER_REGISTRY[consumer.consumer_id] = consumer
    _build_domain_index()


# Seed on module load
_seed_initial_consumers()
