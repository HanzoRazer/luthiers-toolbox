"""
Runtime Semantic Consumption Ledger

CAM Dev Order 7O: Immutable runtime ontology consumption lineage.

This module provides:
  - RuntimeSemanticConsumptionLedgerEntry model with invariants
  - Ledger entry creation from 7N reports
  - Linear chain lineage per consumer
  - Deterministic ledger hashing
  - Drift type mapping from 7N validation results

7O invariants (always enforced):
  - immutable = true
  - execution_authorized = false
  - machine_output_allowed = false

Guardrail:
  7O records how runtimes consume ontology over time. It does not permit
  runtime execution, ontology mutation, semantic reinterpretation, or
  machine authority.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.cam.runtime_semantic_consumption import (
    ConsumptionDisciplineReport,
    get_runtime_semantic_consumer,
)


# -----------------------------------------------------------------------------
# Canonical Drift Types
# -----------------------------------------------------------------------------

RUNTIME_DRIFT_TYPES = [
    "missing_term_dependency",
    "domain_reinterpretation",
    "lifecycle_reinterpretation",
    "authority_claim_attempt",
    "execution_semantic_leakage",
    "machine_output_semantic_leakage",
    "ontology_mutation_attempt",
]


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class RuntimeSemanticConsumptionLedgerEntry(BaseModel):
    """
    Immutable ledger entry for runtime semantic consumption.

    7O invariants (model-enforced):
      - immutable = true (always)
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    ledger_entry_id: str = Field(..., description="Unique ledger entry ID")
    consumer_id: str = Field(..., description="Consumer this entry belongs to")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Entry creation timestamp"
    )

    # Lineage
    parent_ledger_hashes: List[str] = Field(
        default_factory=list,
        description="Parent ledger hashes (empty for first entry)"
    )

    # 7N report reference
    consumption_report_hash: str = Field(
        ...,
        description="Hash of the 7N ConsumptionDisciplineReport"
    )

    # Consumption state
    ontology_alignment_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alignment score from 7N report"
    )
    ontology_consumption_valid: bool = Field(
        ...,
        description="Whether consumption is valid"
    )

    # Drift analysis
    detected_drift_types: List[str] = Field(
        default_factory=list,
        description="Detected drift types"
    )
    reinterpretation_risk_count: int = Field(
        default=0,
        ge=0,
        description="Count of reinterpretation risks"
    )
    authority_violation_count: int = Field(
        default=0,
        ge=0,
        description="Count of authority violations"
    )

    # Escalation
    escalation_recommended: bool = Field(
        default=False,
        description="Whether escalation is recommended"
    )
    escalation_reason_codes: List[str] = Field(
        default_factory=list,
        description="Reason codes for escalation"
    )

    # Deterministic hash
    deterministic_ledger_hash: str = Field(
        ...,
        description="Deterministic hash for lineage verification"
    )

    # 7O invariants
    immutable: bool = Field(default=True)
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    @field_validator("immutable", mode="before")
    @classmethod
    def enforce_immutable(cls, v: Any) -> bool:
        if v is False:
            raise ValueError("7O invariant violation: immutable must be true")
        return True

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7O invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7O invariant violation: machine_output_allowed must be false"
            )
        return False


class LedgerEntrySummary(BaseModel):
    """Lightweight summary for listing ledger entries."""

    ledger_entry_id: str
    consumer_id: str
    ontology_alignment_score: float
    ontology_consumption_valid: bool
    drift_type_count: int
    escalation_recommended: bool
    created_at: datetime


# -----------------------------------------------------------------------------
# Ledger Index (in-memory)
# -----------------------------------------------------------------------------

_RUNTIME_SEMANTIC_LEDGER_INDEX: Dict[str, RuntimeSemanticConsumptionLedgerEntry] = {}
_LEDGER_BY_CONSUMER: Dict[str, List[str]] = {}


def _rebuild_consumer_index() -> None:
    """Rebuild consumer index from ledger."""
    global _LEDGER_BY_CONSUMER
    _LEDGER_BY_CONSUMER = {}
    for entry_id, entry in _RUNTIME_SEMANTIC_LEDGER_INDEX.items():
        consumer_id = entry.consumer_id
        if consumer_id not in _LEDGER_BY_CONSUMER:
            _LEDGER_BY_CONSUMER[consumer_id] = []
        _LEDGER_BY_CONSUMER[consumer_id].append(entry_id)


def store_ledger_entry(entry: RuntimeSemanticConsumptionLedgerEntry) -> None:
    """Store a ledger entry."""
    if entry.ledger_entry_id in _RUNTIME_SEMANTIC_LEDGER_INDEX:
        raise ValueError(
            f"Ledger entry already exists: {entry.ledger_entry_id}"
        )
    _RUNTIME_SEMANTIC_LEDGER_INDEX[entry.ledger_entry_id] = entry
    _rebuild_consumer_index()


def get_ledger_entry(
    ledger_entry_id: str,
) -> Optional[RuntimeSemanticConsumptionLedgerEntry]:
    """Get a ledger entry by ID."""
    return _RUNTIME_SEMANTIC_LEDGER_INDEX.get(ledger_entry_id)


def list_ledger_entries() -> List[RuntimeSemanticConsumptionLedgerEntry]:
    """List all ledger entries."""
    return list(_RUNTIME_SEMANTIC_LEDGER_INDEX.values())


def list_ledger_entries_for_consumer(
    consumer_id: str,
) -> List[RuntimeSemanticConsumptionLedgerEntry]:
    """List ledger entries for a specific consumer (ordered by creation)."""
    entry_ids = _LEDGER_BY_CONSUMER.get(consumer_id, [])
    entries = [_RUNTIME_SEMANTIC_LEDGER_INDEX[eid] for eid in entry_ids]
    return sorted(entries, key=lambda e: e.created_at)


def get_latest_ledger_entry_for_consumer(
    consumer_id: str,
) -> Optional[RuntimeSemanticConsumptionLedgerEntry]:
    """Get the most recent ledger entry for a consumer."""
    entries = list_ledger_entries_for_consumer(consumer_id)
    if not entries:
        return None
    return entries[-1]


def list_consumers_with_ledger_entries() -> List[str]:
    """List all consumers with ledger entries."""
    return sorted(_LEDGER_BY_CONSUMER.keys())


def clear_ledger_for_tests() -> None:
    """Clear all ledger entries. For testing only."""
    global _RUNTIME_SEMANTIC_LEDGER_INDEX, _LEDGER_BY_CONSUMER
    _RUNTIME_SEMANTIC_LEDGER_INDEX = {}
    _LEDGER_BY_CONSUMER = {}


def to_ledger_summary(
    entry: RuntimeSemanticConsumptionLedgerEntry,
) -> LedgerEntrySummary:
    """Convert ledger entry to summary."""
    return LedgerEntrySummary(
        ledger_entry_id=entry.ledger_entry_id,
        consumer_id=entry.consumer_id,
        ontology_alignment_score=entry.ontology_alignment_score,
        ontology_consumption_valid=entry.ontology_consumption_valid,
        drift_type_count=len(entry.detected_drift_types),
        escalation_recommended=entry.escalation_recommended,
        created_at=entry.created_at,
    )


# -----------------------------------------------------------------------------
# Drift Type Mapping
# -----------------------------------------------------------------------------

def map_drift_types_from_report(
    report: ConsumptionDisciplineReport,
) -> List[str]:
    """
    Map 7N validation results to canonical drift types.

    Mapping:
      - missing_terms → missing_term_dependency
      - term_mismatches (domain) → domain_reinterpretation
      - term_mismatches (lifecycle) → lifecycle_reinterpretation
      - prohibited_authority_claims → authority_claim_attempt
      - runtime_reinterpretation_risks → domain/lifecycle/mutation based on text
      - execution claims → execution_semantic_leakage
      - machine_output claims → machine_output_semantic_leakage
    """
    drift_types: set = set()

    # Missing terms
    if report.missing_terms:
        drift_types.add("missing_term_dependency")

    # Term mismatches
    for mismatch in report.term_mismatches:
        if mismatch.mismatch_type == "domain_mismatch":
            drift_types.add("domain_reinterpretation")
        elif mismatch.mismatch_type == "lifecycle_incompatibility":
            drift_types.add("lifecycle_reinterpretation")
        elif mismatch.mismatch_type == "governance_tier_violation":
            drift_types.add("authority_claim_attempt")

    # Prohibited authority claims
    for claim in report.prohibited_authority_claims:
        if claim.operation in ("execute_runtime",):
            drift_types.add("execution_semantic_leakage")
        elif claim.operation in ("generate_machine_output",):
            drift_types.add("machine_output_semantic_leakage")
        elif claim.operation in ("register_term", "mutate_ontology"):
            drift_types.add("ontology_mutation_attempt")
        else:
            drift_types.add("authority_claim_attempt")

    # Reinterpretation risks
    for risk in report.runtime_reinterpretation_risks:
        desc_lower = risk.description.lower()
        if "lifecycle" in desc_lower:
            drift_types.add("lifecycle_reinterpretation")
        elif "mutation" in desc_lower or "fork" in desc_lower or "register" in desc_lower:
            drift_types.add("ontology_mutation_attempt")
        else:
            drift_types.add("domain_reinterpretation")

    return sorted(drift_types)


# -----------------------------------------------------------------------------
# Deterministic Hashing
# -----------------------------------------------------------------------------

def compute_ledger_entry_hash(
    consumer_id: str,
    parent_ledger_hashes: List[str],
    consumption_report_hash: str,
    detected_drift_types: List[str],
    ontology_consumption_valid: bool,
    ontology_alignment_score: float,
    escalation_recommended: bool,
    escalation_reason_codes: List[str],
    reinterpretation_risk_count: int,
    authority_violation_count: int,
) -> str:
    """
    Compute deterministic hash for a ledger entry.

    Includes:
      - consumer_id
      - parent_ledger_hashes (sorted)
      - consumption_report_hash
      - drift types (sorted)
      - validity flags
      - alignment score
      - escalation flags
      - counts

    Excludes:
      - timestamps
      - UUIDs
      - generated ledger_entry_id
    """
    hash_data = {
        "consumer_id": consumer_id,
        "parent_ledger_hashes": sorted(parent_ledger_hashes),
        "consumption_report_hash": consumption_report_hash,
        "detected_drift_types": sorted(detected_drift_types),
        "ontology_consumption_valid": ontology_consumption_valid,
        "ontology_alignment_score": round(ontology_alignment_score, 4),
        "escalation_recommended": escalation_recommended,
        "escalation_reason_codes": sorted(escalation_reason_codes),
        "reinterpretation_risk_count": reinterpretation_risk_count,
        "authority_violation_count": authority_violation_count,
    }

    json_str = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Ledger Entry Creation
# -----------------------------------------------------------------------------

def create_ledger_entry_from_report(
    report: ConsumptionDisciplineReport,
    parent_ledger_hashes: Optional[List[str]] = None,
) -> RuntimeSemanticConsumptionLedgerEntry:
    """
    Create an immutable ledger entry from a 7N consumption report.

    If parent_ledger_hashes is not provided, uses the most recent
    ledger entry for the consumer (linear chain).

    Args:
        report: The 7N ConsumptionDisciplineReport
        parent_ledger_hashes: Optional override for parent hashes

    Returns:
        RuntimeSemanticConsumptionLedgerEntry (also stored in index)
    """
    consumer_id = report.consumer_id

    # Determine parent hashes (linear chain by default)
    if parent_ledger_hashes is None:
        latest = get_latest_ledger_entry_for_consumer(consumer_id)
        if latest is not None:
            parent_ledger_hashes = [latest.deterministic_ledger_hash]
        else:
            parent_ledger_hashes = []

    # Map drift types
    detected_drift_types = map_drift_types_from_report(report)

    # Count violations
    reinterpretation_risk_count = len(report.runtime_reinterpretation_risks)
    authority_violation_count = len(report.prohibited_authority_claims)

    # Determine escalation (basic for ledger entry, full analysis in engine)
    escalation_recommended = False
    escalation_reason_codes: List[str] = []

    if authority_violation_count > 0:
        escalation_recommended = True
        escalation_reason_codes.append("authority_violation_detected")

    if "execution_semantic_leakage" in detected_drift_types:
        escalation_recommended = True
        escalation_reason_codes.append("execution_semantic_leakage")

    if "machine_output_semantic_leakage" in detected_drift_types:
        escalation_recommended = True
        escalation_reason_codes.append("machine_output_semantic_leakage")

    if not report.discipline_valid:
        escalation_reason_codes.append("consumption_invalid")

    # Compute deterministic hash
    deterministic_hash = compute_ledger_entry_hash(
        consumer_id=consumer_id,
        parent_ledger_hashes=parent_ledger_hashes,
        consumption_report_hash=report.deterministic_report_hash,
        detected_drift_types=detected_drift_types,
        ontology_consumption_valid=report.discipline_valid,
        ontology_alignment_score=report.consumption_alignment_score,
        escalation_recommended=escalation_recommended,
        escalation_reason_codes=escalation_reason_codes,
        reinterpretation_risk_count=reinterpretation_risk_count,
        authority_violation_count=authority_violation_count,
    )

    # Create entry
    entry = RuntimeSemanticConsumptionLedgerEntry(
        ledger_entry_id=f"ledger-{uuid.uuid4().hex[:12]}",
        consumer_id=consumer_id,
        parent_ledger_hashes=parent_ledger_hashes,
        consumption_report_hash=report.deterministic_report_hash,
        ontology_alignment_score=report.consumption_alignment_score,
        ontology_consumption_valid=report.discipline_valid,
        detected_drift_types=detected_drift_types,
        reinterpretation_risk_count=reinterpretation_risk_count,
        authority_violation_count=authority_violation_count,
        escalation_recommended=escalation_recommended,
        escalation_reason_codes=escalation_reason_codes,
        deterministic_ledger_hash=deterministic_hash,
        immutable=True,
        execution_authorized=False,
        machine_output_allowed=False,
    )

    # Store entry
    store_ledger_entry(entry)

    return entry
