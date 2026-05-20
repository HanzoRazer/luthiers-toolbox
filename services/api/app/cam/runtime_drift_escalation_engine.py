"""
Runtime Drift Escalation Engine

CAM Dev Order 7O: Escalation scoring and threshold evaluation for runtime
semantic consumption drift.

This module provides:
  - RuntimeDriftEscalationEvaluation model
  - Escalation severity classification
  - Drift accumulation analysis
  - Threshold evaluation

Escalation thresholds:
  - 1 occurrence, low severity drift → low
  - 2 repeated occurrences of same drift type → medium
  - 3 repeated occurrences of same drift type → high
  - any repeated authority claim → critical
  - any execution or machine-output claim → critical
  - 3+ total invalid ledger entries for same consumer → high
  - 5+ total invalid ledger entries for same consumer → critical

7O invariants (always enforced):
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
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.cam.runtime_semantic_consumption_ledger import (
    RuntimeSemanticConsumptionLedgerEntry,
    list_ledger_entries_for_consumer,
)


# -----------------------------------------------------------------------------
# Escalation Severity Type
# -----------------------------------------------------------------------------

EscalationSeverity = Literal["none", "low", "medium", "high", "critical"]


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class RuntimeDriftEscalationEvaluation(BaseModel):
    """
    Evaluation of runtime drift escalation for a consumer.

    7O invariants (model-enforced):
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)

    Additional 7O invariants:
      - governance_review_required implies escalation_threshold_exceeded
      - critical escalation implies ontology_integrity_risk
    """

    evaluation_id: str = Field(..., description="Unique evaluation ID")
    consumer_id: str = Field(..., description="Consumer being evaluated")
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    # Analysis
    ledger_entries_evaluated: int = Field(
        ...,
        ge=0,
        description="Number of ledger entries evaluated"
    )
    repeated_drift_patterns: List[str] = Field(
        default_factory=list,
        description="Drift patterns that repeated"
    )
    repeated_authority_violations: List[str] = Field(
        default_factory=list,
        description="Authority violations that repeated"
    )

    # Escalation state
    escalation_threshold_exceeded: bool = Field(
        default=False,
        description="Whether escalation threshold was exceeded"
    )
    escalation_severity: EscalationSeverity = Field(
        default="none",
        description="Escalation severity level"
    )
    governance_review_required: bool = Field(
        default=False,
        description="Whether governance review is required"
    )
    ontology_integrity_risk: bool = Field(
        default=False,
        description="Whether ontology integrity is at risk"
    )

    # Deterministic hash
    deterministic_evaluation_hash: str = Field(
        ...,
        description="Deterministic hash for verification"
    )

    # 7O invariants
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

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


# -----------------------------------------------------------------------------
# Escalation Index (in-memory)
# -----------------------------------------------------------------------------

_RUNTIME_DRIFT_ESCALATION_INDEX: Dict[str, RuntimeDriftEscalationEvaluation] = {}
_ESCALATION_BY_CONSUMER: Dict[str, List[str]] = {}


def _rebuild_escalation_consumer_index() -> None:
    """Rebuild consumer index for escalations."""
    global _ESCALATION_BY_CONSUMER
    _ESCALATION_BY_CONSUMER = {}
    for eval_id, evaluation in _RUNTIME_DRIFT_ESCALATION_INDEX.items():
        consumer_id = evaluation.consumer_id
        if consumer_id not in _ESCALATION_BY_CONSUMER:
            _ESCALATION_BY_CONSUMER[consumer_id] = []
        _ESCALATION_BY_CONSUMER[consumer_id].append(eval_id)


def store_escalation_evaluation(
    evaluation: RuntimeDriftEscalationEvaluation,
) -> None:
    """Store an escalation evaluation."""
    _RUNTIME_DRIFT_ESCALATION_INDEX[evaluation.evaluation_id] = evaluation
    _rebuild_escalation_consumer_index()


def get_escalation_evaluation(
    evaluation_id: str,
) -> Optional[RuntimeDriftEscalationEvaluation]:
    """Get an escalation evaluation by ID."""
    return _RUNTIME_DRIFT_ESCALATION_INDEX.get(evaluation_id)


def list_escalation_evaluations() -> List[RuntimeDriftEscalationEvaluation]:
    """List all escalation evaluations."""
    return list(_RUNTIME_DRIFT_ESCALATION_INDEX.values())


def list_escalations_for_consumer(
    consumer_id: str,
) -> List[RuntimeDriftEscalationEvaluation]:
    """List escalation evaluations for a specific consumer."""
    eval_ids = _ESCALATION_BY_CONSUMER.get(consumer_id, [])
    evals = [_RUNTIME_DRIFT_ESCALATION_INDEX[eid] for eid in eval_ids]
    return sorted(evals, key=lambda e: e.evaluated_at)


def get_latest_escalation_for_consumer(
    consumer_id: str,
) -> Optional[RuntimeDriftEscalationEvaluation]:
    """Get the most recent escalation evaluation for a consumer."""
    evals = list_escalations_for_consumer(consumer_id)
    if not evals:
        return None
    return evals[-1]


def clear_escalations_for_tests() -> None:
    """Clear all escalation evaluations. For testing only."""
    global _RUNTIME_DRIFT_ESCALATION_INDEX, _ESCALATION_BY_CONSUMER
    _RUNTIME_DRIFT_ESCALATION_INDEX = {}
    _ESCALATION_BY_CONSUMER = {}


# -----------------------------------------------------------------------------
# Drift Analysis
# -----------------------------------------------------------------------------

def analyze_drift_patterns(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
) -> tuple[List[str], Counter]:
    """
    Analyze drift patterns across ledger entries.

    Returns:
        (repeated_patterns, drift_counts)
    """
    drift_counts: Counter = Counter()

    for entry in entries:
        for drift_type in entry.detected_drift_types:
            drift_counts[drift_type] += 1

    # Patterns that appear more than once are repeated
    repeated_patterns = [
        drift_type for drift_type, count in drift_counts.items()
        if count >= 2
    ]

    return repeated_patterns, drift_counts


def analyze_authority_violations(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
) -> List[str]:
    """
    Analyze authority violations across ledger entries.

    Returns:
        List of repeated authority violation types
    """
    authority_types = [
        "authority_claim_attempt",
        "execution_semantic_leakage",
        "machine_output_semantic_leakage",
        "ontology_mutation_attempt",
    ]

    violation_counts: Counter = Counter()

    for entry in entries:
        for drift_type in entry.detected_drift_types:
            if drift_type in authority_types:
                violation_counts[drift_type] += 1

    # Any repeated authority violation
    repeated_violations = [
        vtype for vtype, count in violation_counts.items()
        if count >= 2
    ]

    return repeated_violations


# -----------------------------------------------------------------------------
# Escalation Severity Classification
# -----------------------------------------------------------------------------

def classify_escalation_severity(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
    repeated_drift_patterns: List[str],
    repeated_authority_violations: List[str],
    drift_counts: Counter,
) -> EscalationSeverity:
    """
    Classify escalation severity based on thresholds.

    Thresholds:
      - 1 occurrence, low severity drift → low
      - 2 repeated occurrences of same drift type → medium
      - 3 repeated occurrences of same drift type → high
      - any repeated authority claim → critical
      - any execution or machine-output claim → critical
      - 3+ total invalid ledger entries for same consumer → high
      - 5+ total invalid ledger entries for same consumer → critical
    """
    # Count invalid entries
    invalid_count = sum(1 for e in entries if not e.ontology_consumption_valid)

    # Critical checks first
    if repeated_authority_violations:
        return "critical"

    # Any execution or machine-output leakage (even single occurrence)
    critical_drift_types = {
        "execution_semantic_leakage",
        "machine_output_semantic_leakage",
    }
    for entry in entries:
        for drift_type in entry.detected_drift_types:
            if drift_type in critical_drift_types:
                return "critical"

    # 5+ invalid entries → critical
    if invalid_count >= 5:
        return "critical"

    # High checks
    # 3+ repeated occurrences of same drift type
    for drift_type, count in drift_counts.items():
        if count >= 3:
            return "high"

    # 3+ invalid entries → high
    if invalid_count >= 3:
        return "high"

    # Medium checks
    # 2 repeated occurrences of same drift type
    if repeated_drift_patterns:
        return "medium"

    # Low checks
    # Any drift detected
    has_any_drift = any(
        len(entry.detected_drift_types) > 0 for entry in entries
    )
    if has_any_drift:
        return "low"

    return "none"


# -----------------------------------------------------------------------------
# Deterministic Hash
# -----------------------------------------------------------------------------

def compute_escalation_evaluation_hash(
    consumer_id: str,
    ledger_entries_evaluated: int,
    repeated_drift_patterns: List[str],
    repeated_authority_violations: List[str],
    escalation_threshold_exceeded: bool,
    escalation_severity: EscalationSeverity,
    governance_review_required: bool,
    ontology_integrity_risk: bool,
) -> str:
    """
    Compute deterministic hash for an escalation evaluation.

    Excludes:
      - timestamps
      - UUIDs
      - generated evaluation_id
    """
    hash_data = {
        "consumer_id": consumer_id,
        "ledger_entries_evaluated": ledger_entries_evaluated,
        "repeated_drift_patterns": sorted(repeated_drift_patterns),
        "repeated_authority_violations": sorted(repeated_authority_violations),
        "escalation_threshold_exceeded": escalation_threshold_exceeded,
        "escalation_severity": escalation_severity,
        "governance_review_required": governance_review_required,
        "ontology_integrity_risk": ontology_integrity_risk,
    }

    json_str = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Escalation Evaluation
# -----------------------------------------------------------------------------

def evaluate_runtime_drift_escalation(
    consumer_id: str,
) -> RuntimeDriftEscalationEvaluation:
    """
    Evaluate runtime drift escalation for a consumer.

    Analyzes:
      - repeated reinterpretation attempts
      - repeated lifecycle mismatches
      - repeated authority violations
      - repeated missing ontology terms
      - repeated execution claims

    Escalation is based on:
      - frequency
      - severity
      - continuity

    Returns:
        RuntimeDriftEscalationEvaluation (also stored in index)
    """
    # Get all ledger entries for consumer
    entries = list_ledger_entries_for_consumer(consumer_id)

    # Analyze patterns
    repeated_drift_patterns, drift_counts = analyze_drift_patterns(entries)
    repeated_authority_violations = analyze_authority_violations(entries)

    # Classify severity
    escalation_severity = classify_escalation_severity(
        entries=entries,
        repeated_drift_patterns=repeated_drift_patterns,
        repeated_authority_violations=repeated_authority_violations,
        drift_counts=drift_counts,
    )

    # Determine threshold exceeded
    # Threshold exceeded when severity is medium or above
    # OR governance_review_required is true
    escalation_threshold_exceeded = escalation_severity in (
        "medium", "high", "critical"
    )

    # Governance review required
    governance_review_required = escalation_severity in ("high", "critical")

    # Ontology integrity risk (critical escalation implies this)
    ontology_integrity_risk = escalation_severity == "critical"

    # Compute hash
    deterministic_hash = compute_escalation_evaluation_hash(
        consumer_id=consumer_id,
        ledger_entries_evaluated=len(entries),
        repeated_drift_patterns=repeated_drift_patterns,
        repeated_authority_violations=repeated_authority_violations,
        escalation_threshold_exceeded=escalation_threshold_exceeded,
        escalation_severity=escalation_severity,
        governance_review_required=governance_review_required,
        ontology_integrity_risk=ontology_integrity_risk,
    )

    # Create evaluation
    evaluation = RuntimeDriftEscalationEvaluation(
        evaluation_id=f"escalation-{uuid.uuid4().hex[:12]}",
        consumer_id=consumer_id,
        ledger_entries_evaluated=len(entries),
        repeated_drift_patterns=repeated_drift_patterns,
        repeated_authority_violations=repeated_authority_violations,
        escalation_threshold_exceeded=escalation_threshold_exceeded,
        escalation_severity=escalation_severity,
        governance_review_required=governance_review_required,
        ontology_integrity_risk=ontology_integrity_risk,
        deterministic_evaluation_hash=deterministic_hash,
        execution_authorized=False,
        machine_output_allowed=False,
    )

    # Store evaluation
    store_escalation_evaluation(evaluation)

    return evaluation
