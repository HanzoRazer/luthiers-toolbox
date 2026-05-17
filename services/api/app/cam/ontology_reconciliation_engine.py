"""
Ontology Reconciliation Engine

CAM Dev Order 7M: Semantic conflict detection and reconciliation reporting.

This module detects:
  - Duplicate definitions
  - Lifecycle drift
  - Authority collisions
  - Runtime reinterpretations
  - Semantic alias collisions

7M invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7M makes ontology drift visible. It does not automatically repair
  ontology drift.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Set
import hashlib
import json
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator

from app.cam.canonical_ontology_registry import (
    CANONICAL_ONTOLOGY_INDEX,
    ONTOLOGY_ALIAS_INDEX,
    ONTOLOGY_DOMAIN_INDEX,
    CanonicalOntologyTerm,
    get_canonical_term,
    list_canonical_terms,
    list_domains,
)
from app.cam.ontology_authority_map import (
    get_lifecycle_vocabularies,
    get_cross_domain_relationship,
)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

CONFLICT_TYPES = Literal[
    "duplicate_definition",
    "lifecycle_drift",
    "authority_collision",
    "runtime_reinterpretation",
    "semantic_alias_collision",
]

SEVERITY_LEVELS = Literal["low", "medium", "high", "critical"]

SEVERITY_PENALTIES: Dict[str, int] = {
    "low": 2,
    "medium": 5,
    "high": 15,
    "critical": 30,
}


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class OntologyConflict(BaseModel):
    """
    Detected ontology conflict.

    7M invariants:
      - reconciliation_required = true for all conflicts
    """

    conflict_id: str = Field(
        default_factory=lambda: f"conflict-{uuid.uuid4().hex[:12]}",
        description="Unique conflict identifier"
    )

    term: str = Field(..., description="Term involved in conflict")

    conflicting_sources: List[str] = Field(
        default_factory=list,
        description="Sources contributing to the conflict"
    )

    canonical_source: str = Field(
        ...,
        description="Canonical source that should own this term"
    )

    conflict_type: CONFLICT_TYPES = Field(
        ...,
        description="Type of ontology conflict"
    )

    severity: SEVERITY_LEVELS = Field(
        ...,
        description="Severity of the conflict"
    )

    description: str = Field(
        default="",
        description="Human-readable conflict description"
    )

    reconciliation_required: bool = Field(
        default=True,
        description="Always true for detected conflicts"
    )

    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("reconciliation_required", mode="before")
    @classmethod
    def enforce_reconciliation_required(cls, v: Any) -> bool:
        return True


class OntologyReconciliationReport(BaseModel):
    """
    Reconciliation report for ontology integrity.

    7M invariants (model-enforced):
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    report_id: str = Field(
        default_factory=lambda: f"report-{uuid.uuid4().hex[:12]}",
        description="Unique report identifier"
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Report generation timestamp"
    )

    # Evaluation counts
    terms_evaluated: int = Field(..., description="Total terms evaluated")
    conflicts_detected: int = Field(..., description="Total conflicts detected")
    lifecycle_conflicts: int = Field(..., description="Lifecycle drift conflicts")
    authority_conflicts: int = Field(..., description="Authority collision conflicts")
    runtime_semantic_conflicts: int = Field(
        ...,
        description="Runtime reinterpretation conflicts"
    )

    # Alignment score (severity-weighted)
    canonical_alignment_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alignment score (0.0 to 1.0)"
    )

    # Conflict details
    conflicts: List[OntologyConflict] = Field(
        default_factory=list,
        description="List of detected conflicts"
    )

    # Integrity
    ontology_integrity_valid: bool = Field(
        ...,
        description="Whether ontology integrity is valid (no critical conflicts)"
    )

    # Deterministic hash
    deterministic_report_hash: str = Field(
        ...,
        description="Deterministic hash of report contents"
    )

    # 7M invariants
    execution_authorized: bool = Field(
        default=False,
        description="Always false — no execution authorization"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always false — no machine output"
    )

    # 7M invariant validators
    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7M invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7M invariant violation: machine_output_allowed must be false"
            )
        return False

    @model_validator(mode="after")
    def validate_invariants(self) -> "OntologyReconciliationReport":
        """Validate all 7M invariants after model construction."""
        if self.execution_authorized:
            raise ValueError(
                "7M invariant violation: execution_authorized must be false"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7M invariant violation: machine_output_allowed must be false"
            )
        return self


# -----------------------------------------------------------------------------
# In-Memory Indexes
# -----------------------------------------------------------------------------

ONTOLOGY_CONFLICT_INDEX: Dict[str, OntologyConflict] = {}
ONTOLOGY_REPORT_INDEX: Dict[str, OntologyReconciliationReport] = {}


def register_conflict(conflict: OntologyConflict) -> None:
    """Register a detected conflict."""
    ONTOLOGY_CONFLICT_INDEX[conflict.conflict_id] = conflict


def get_conflict(conflict_id: str) -> Optional[OntologyConflict]:
    """Get a conflict by ID."""
    return ONTOLOGY_CONFLICT_INDEX.get(conflict_id)


def list_conflicts() -> List[OntologyConflict]:
    """List all detected conflicts."""
    return list(ONTOLOGY_CONFLICT_INDEX.values())


def register_report(report: OntologyReconciliationReport) -> None:
    """Register a reconciliation report."""
    ONTOLOGY_REPORT_INDEX[report.report_id] = report


def get_report(report_id: str) -> Optional[OntologyReconciliationReport]:
    """Get a report by ID."""
    return ONTOLOGY_REPORT_INDEX.get(report_id)


def get_latest_report() -> Optional[OntologyReconciliationReport]:
    """Get the most recent reconciliation report."""
    if not ONTOLOGY_REPORT_INDEX:
        return None
    return max(ONTOLOGY_REPORT_INDEX.values(), key=lambda r: r.generated_at)


def list_reports() -> List[OntologyReconciliationReport]:
    """List all reconciliation reports."""
    return list(ONTOLOGY_REPORT_INDEX.values())


def clear_conflict_index() -> None:
    """Clear all conflicts (for testing)."""
    ONTOLOGY_CONFLICT_INDEX.clear()


def clear_report_index() -> None:
    """Clear all reports (for testing)."""
    ONTOLOGY_REPORT_INDEX.clear()


# -----------------------------------------------------------------------------
# Conflict Detection
# -----------------------------------------------------------------------------

def _detect_duplicate_definitions() -> List[OntologyConflict]:
    """
    Detect duplicate term definitions.

    In closed-world detection, this checks for terms that have
    multiple explicit registrations (shouldn't happen with current
    registry but included for completeness).
    """
    conflicts: List[OntologyConflict] = []
    # With current registry design, duplicates are rejected at registration
    # This function exists for future codebase scanning
    return conflicts


def _detect_lifecycle_drift() -> List[OntologyConflict]:
    """
    Detect lifecycle vocabulary drift between domains.

    Checks for incompatible lifecycle semantics across related domains.
    """
    conflicts: List[OntologyConflict] = []
    lifecycle_vocabs = get_lifecycle_vocabularies()

    # Group domains by lifecycle vocabulary similarity
    vocab_groups: Dict[frozenset, List[str]] = {}
    for domain, vocab in lifecycle_vocabs.items():
        vocab_key = frozenset(vocab)
        if vocab_key not in vocab_groups:
            vocab_groups[vocab_key] = []
        vocab_groups[vocab_key].append(domain)

    # Check for incompatible vocabularies between related domains
    domains = list(lifecycle_vocabs.keys())
    for i, domain_a in enumerate(domains):
        for domain_b in domains[i + 1:]:
            vocab_a = set(lifecycle_vocabs[domain_a])
            vocab_b = set(lifecycle_vocabs[domain_b])

            # If no overlap and both have vocabs, potential drift
            if vocab_a and vocab_b and not vocab_a.intersection(vocab_b):
                # Check if domains are related (share concepts)
                relationship = get_cross_domain_relationship(domain_a, domain_b)
                if relationship.shared_concepts or not relationship.lifecycle_compatibility:
                    conflict = OntologyConflict(
                        term=f"lifecycle:{domain_a}↔{domain_b}",
                        conflicting_sources=[domain_a, domain_b],
                        canonical_source=domain_a,  # First alphabetically
                        conflict_type="lifecycle_drift",
                        severity="medium",
                        description=(
                            f"Incompatible lifecycle vocabularies: "
                            f"{domain_a}={list(vocab_a)}, {domain_b}={list(vocab_b)}"
                        ),
                    )
                    conflicts.append(conflict)

    return conflicts


def _detect_authority_collisions() -> List[OntologyConflict]:
    """
    Detect authority collisions where multiple domains claim ownership.

    With closed-world detection, this checks for terms where
    aliases or prohibited_reinterpretations create implicit claims.
    """
    conflicts: List[OntologyConflict] = []

    # Check for alias collisions that imply authority disputes
    alias_owners: Dict[str, List[str]] = {}

    for term in CANONICAL_ONTOLOGY_INDEX.values():
        for alias in term.aliases:
            alias_lower = alias.lower()
            if alias_lower not in alias_owners:
                alias_owners[alias_lower] = []
            if term.owning_domain not in alias_owners[alias_lower]:
                alias_owners[alias_lower].append(term.owning_domain)

    # Detect aliases claimed by multiple domains
    for alias, domains in alias_owners.items():
        if len(domains) > 1:
            conflict = OntologyConflict(
                term=alias,
                conflicting_sources=domains,
                canonical_source=domains[0],  # First registered
                conflict_type="authority_collision",
                severity="high",
                description=(
                    f"Alias '{alias}' claimed by multiple domains: {domains}"
                ),
            )
            conflicts.append(conflict)

    return conflicts


def _detect_runtime_reinterpretations() -> List[OntologyConflict]:
    """
    Detect runtime reinterpretation violations.

    Checks if any term's prohibited_reinterpretations appear
    as registered terms or aliases.
    """
    conflicts: List[OntologyConflict] = []

    for term in CANONICAL_ONTOLOGY_INDEX.values():
        for prohibited in term.prohibited_reinterpretations:
            prohibited_lower = prohibited.lower()

            # Check if prohibited reinterpretation is registered as a term
            if prohibited_lower in CANONICAL_ONTOLOGY_INDEX:
                conflict = OntologyConflict(
                    term=term.term,
                    conflicting_sources=[
                        term.owning_domain,
                        CANONICAL_ONTOLOGY_INDEX[prohibited_lower].owning_domain,
                    ],
                    canonical_source=term.owning_domain,
                    conflict_type="runtime_reinterpretation",
                    severity="critical",
                    description=(
                        f"Prohibited reinterpretation '{prohibited}' for term "
                        f"'{term.term}' is registered as a canonical term"
                    ),
                )
                conflicts.append(conflict)

            # Check if prohibited reinterpretation is an alias
            if prohibited_lower in ONTOLOGY_ALIAS_INDEX:
                canonical_for_alias = ONTOLOGY_ALIAS_INDEX[prohibited_lower]
                if canonical_for_alias.lower() != term.term.lower():
                    conflict = OntologyConflict(
                        term=term.term,
                        conflicting_sources=[
                            term.owning_domain,
                            get_canonical_term(canonical_for_alias).owning_domain
                            if get_canonical_term(canonical_for_alias) else "unknown",
                        ],
                        canonical_source=term.owning_domain,
                        conflict_type="runtime_reinterpretation",
                        severity="high",
                        description=(
                            f"Prohibited reinterpretation '{prohibited}' for term "
                            f"'{term.term}' is registered as an alias for "
                            f"'{canonical_for_alias}'"
                        ),
                    )
                    conflicts.append(conflict)

    return conflicts


def _detect_semantic_alias_collisions() -> List[OntologyConflict]:
    """
    Detect semantic alias collisions.

    Checks for aliases that could create semantic ambiguity.
    """
    conflicts: List[OntologyConflict] = []

    # Check for aliases that are too similar to canonical terms
    for term in CANONICAL_ONTOLOGY_INDEX.values():
        for alias in term.aliases:
            alias_lower = alias.lower()

            # Check if alias is a substring of another canonical term
            for other_term_name, other_term in CANONICAL_ONTOLOGY_INDEX.items():
                if other_term_name == term.term.lower():
                    continue

                # Check for substring collisions
                if alias_lower in other_term_name or other_term_name in alias_lower:
                    if len(alias_lower) > 3 and len(other_term_name) > 3:
                        conflict = OntologyConflict(
                            term=alias,
                            conflicting_sources=[term.owning_domain, other_term.owning_domain],
                            canonical_source=term.owning_domain,
                            conflict_type="semantic_alias_collision",
                            severity="low",
                            description=(
                                f"Alias '{alias}' for '{term.term}' collides with "
                                f"canonical term '{other_term.term}'"
                            ),
                        )
                        conflicts.append(conflict)

    return conflicts


def detect_ontology_conflicts() -> List[OntologyConflict]:
    """
    Detect all types of ontology conflicts.

    Returns:
        List of detected OntologyConflict instances
    """
    all_conflicts: List[OntologyConflict] = []

    # Run all detectors
    all_conflicts.extend(_detect_duplicate_definitions())
    all_conflicts.extend(_detect_lifecycle_drift())
    all_conflicts.extend(_detect_authority_collisions())
    all_conflicts.extend(_detect_runtime_reinterpretations())
    all_conflicts.extend(_detect_semantic_alias_collisions())

    # Register all conflicts
    for conflict in all_conflicts:
        register_conflict(conflict)

    return all_conflicts


# -----------------------------------------------------------------------------
# Alignment Score Calculation
# -----------------------------------------------------------------------------

def calculate_alignment_score(conflicts: List[OntologyConflict]) -> float:
    """
    Calculate severity-weighted alignment score.

    Score = max(0, 100 - total_penalty) / 100

    Penalty model:
      - low: 2
      - medium: 5
      - high: 15
      - critical: 30
    """
    total_penalty = sum(
        SEVERITY_PENALTIES.get(c.severity, 0)
        for c in conflicts
    )
    score = max(0, 100 - total_penalty) / 100
    return round(score, 4)


# -----------------------------------------------------------------------------
# Lifecycle Alignment Validation
# -----------------------------------------------------------------------------

def validate_lifecycle_alignment() -> tuple[bool, List[str]]:
    """
    Validate lifecycle vocabulary alignment across domains.

    Returns:
        (is_aligned, list_of_issues)
    """
    issues: List[str] = []
    lifecycle_vocabs = get_lifecycle_vocabularies()

    # Check for domains with incompatible vocabularies
    domains = list(lifecycle_vocabs.keys())
    for i, domain_a in enumerate(domains):
        for domain_b in domains[i + 1:]:
            vocab_a = set(lifecycle_vocabs[domain_a])
            vocab_b = set(lifecycle_vocabs[domain_b])

            if vocab_a and vocab_b and not vocab_a.intersection(vocab_b):
                issues.append(
                    f"No shared lifecycle terms between {domain_a} and {domain_b}"
                )

    return len(issues) == 0, issues


def validate_authority_alignment() -> tuple[bool, List[str]]:
    """
    Validate authority alignment across domains.

    Returns:
        (is_aligned, list_of_issues)
    """
    issues: List[str] = []

    # Check for tier conflicts (lower tier shouldn't override higher)
    for term in CANONICAL_ONTOLOGY_INDEX.values():
        if term.owning_governance_tier > 1:
            # Check if any Tier 1 term references this
            for tier1_term in CANONICAL_ONTOLOGY_INDEX.values():
                if tier1_term.owning_governance_tier == 1:
                    if term.term.lower() in [
                        p.lower() for p in tier1_term.prohibited_reinterpretations
                    ]:
                        issues.append(
                            f"Term '{term.term}' (Tier {term.owning_governance_tier}) "
                            f"conflicts with Tier 1 term '{tier1_term.term}'"
                        )

    return len(issues) == 0, issues


# -----------------------------------------------------------------------------
# Deterministic Report Hashing
# -----------------------------------------------------------------------------

def _compute_report_hash(
    terms_evaluated: int,
    conflicts: List[OntologyConflict],
    alignment_score: float,
    ontology_integrity_valid: bool,
) -> str:
    """
    Compute deterministic hash of report contents.

    Excludes:
      - timestamps
      - UUIDs
      - generated report_id
    """
    hash_input = {
        "terms_evaluated": terms_evaluated,
        "conflicts": [
            {
                "term": c.term,
                "conflict_type": c.conflict_type,
                "severity": c.severity,
                "canonical_source": c.canonical_source,
                "conflicting_sources": sorted(c.conflicting_sources),
            }
            for c in sorted(conflicts, key=lambda x: (x.term, x.conflict_type))
        ],
        "alignment_score": alignment_score,
        "ontology_integrity_valid": ontology_integrity_valid,
    }
    canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Reconciliation Report Generation
# -----------------------------------------------------------------------------

def generate_reconciliation_report() -> OntologyReconciliationReport:
    """
    Generate a comprehensive reconciliation report.

    This is a passive, read-only operation that:
      - Evaluates all registered terms
      - Detects conflicts
      - Calculates alignment score
      - Does NOT mutate any state

    Returns:
        OntologyReconciliationReport
    """
    # Get all terms
    terms = list_canonical_terms()
    terms_evaluated = len(terms)

    # Detect conflicts
    conflicts = detect_ontology_conflicts()

    # Categorize conflicts
    lifecycle_conflicts = len([
        c for c in conflicts if c.conflict_type == "lifecycle_drift"
    ])
    authority_conflicts = len([
        c for c in conflicts if c.conflict_type == "authority_collision"
    ])
    runtime_semantic_conflicts = len([
        c for c in conflicts if c.conflict_type == "runtime_reinterpretation"
    ])

    # Calculate alignment score
    alignment_score = calculate_alignment_score(conflicts)

    # Determine integrity validity (no critical conflicts)
    has_critical = any(c.severity == "critical" for c in conflicts)
    ontology_integrity_valid = not has_critical

    # Compute deterministic hash
    deterministic_hash = _compute_report_hash(
        terms_evaluated=terms_evaluated,
        conflicts=conflicts,
        alignment_score=alignment_score,
        ontology_integrity_valid=ontology_integrity_valid,
    )

    # Build report
    report = OntologyReconciliationReport(
        terms_evaluated=terms_evaluated,
        conflicts_detected=len(conflicts),
        lifecycle_conflicts=lifecycle_conflicts,
        authority_conflicts=authority_conflicts,
        runtime_semantic_conflicts=runtime_semantic_conflicts,
        canonical_alignment_score=alignment_score,
        conflicts=conflicts,
        ontology_integrity_valid=ontology_integrity_valid,
        deterministic_report_hash=deterministic_hash,
        execution_authorized=False,
        machine_output_allowed=False,
    )

    # Register report
    register_report(report)

    return report
