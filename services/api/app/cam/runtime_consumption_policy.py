"""
Runtime Consumption Policy

CAM Dev Order 7N: Policy enforcement and report generation for runtime
semantic consumption discipline.

This module provides:
  - Consumption discipline validation
  - Alignment score calculation
  - Report generation with deterministic hashing
  - CI-visible summary

7N invariants (always enforced):
  - execution_authorized = false
  - machine_output_allowed = false
  - immutable = true

Guardrail:
  7N verifies that runtimes consume ontology without owning ontology.
  It does not permit runtime execution, ontology mutation, lifecycle
  definition, or semantic reinterpretation.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.cam.runtime_semantic_consumption import (
    RuntimeSemanticConsumer,
    ConsumptionDisciplineReport,
    TermConsumptionMismatch,
    ProhibitedAuthorityClaim,
    RuntimeReinterpretationRisk,
    ProhibitedRuntimeSemanticOperation,
    get_runtime_semantic_consumer,
    list_runtime_semantic_consumers,
    validate_consumed_terms,
    detect_prohibited_authority_claims,
    detect_reinterpretation_risks,
)


# -----------------------------------------------------------------------------
# Severity Penalties (aligned with 7M)
# -----------------------------------------------------------------------------

SEVERITY_PENALTIES: Dict[str, int] = {
    "low": 2,
    "medium": 5,
    "high": 15,
    "critical": 30,
}


# -----------------------------------------------------------------------------
# Report Storage (in-memory)
# -----------------------------------------------------------------------------

_REPORT_STORAGE: List[ConsumptionDisciplineReport] = []


def store_report(report: ConsumptionDisciplineReport) -> None:
    """Store a report in memory."""
    _REPORT_STORAGE.append(report)


def list_reports() -> List[ConsumptionDisciplineReport]:
    """List all stored reports."""
    return list(_REPORT_STORAGE)


def get_latest_report() -> Optional[ConsumptionDisciplineReport]:
    """Get the most recent report."""
    if not _REPORT_STORAGE:
        return None
    return max(_REPORT_STORAGE, key=lambda r: r.generated_at)


def get_reports_for_consumer(
    consumer_id: str,
) -> List[ConsumptionDisciplineReport]:
    """Get all reports for a specific consumer."""
    return [r for r in _REPORT_STORAGE if r.consumer_id == consumer_id]


def clear_reports_for_tests() -> None:
    """Clear all reports. For testing only."""
    global _REPORT_STORAGE
    _REPORT_STORAGE = []


# -----------------------------------------------------------------------------
# Alignment Score Calculation
# -----------------------------------------------------------------------------

def calculate_consumption_alignment_score(
    missing_terms: List[str],
    mismatches: List[TermConsumptionMismatch],
    prohibited_claims: List[ProhibitedAuthorityClaim],
    reinterpretation_risks: List[RuntimeReinterpretationRisk],
) -> float:
    """
    Calculate consumption alignment score.

    Uses severity-weighted penalties (aligned with 7M):
      - low: 2 points
      - medium: 5 points
      - high: 15 points
      - critical: 30 points

    Score = max(0, 100 - total_penalty) / 100
    """
    total_penalty = 0

    # Missing terms are high severity
    total_penalty += len(missing_terms) * SEVERITY_PENALTIES["high"]

    # Mismatches vary by type
    for mismatch in mismatches:
        if mismatch.mismatch_type == "term_not_in_registry":
            continue  # Already counted in missing_terms
        elif mismatch.mismatch_type == "governance_tier_violation":
            total_penalty += SEVERITY_PENALTIES["critical"]
        elif mismatch.mismatch_type == "domain_mismatch":
            total_penalty += SEVERITY_PENALTIES["medium"]
        elif mismatch.mismatch_type == "lifecycle_incompatibility":
            total_penalty += SEVERITY_PENALTIES["high"]

    # Prohibited claims are critical
    for claim in prohibited_claims:
        total_penalty += SEVERITY_PENALTIES.get(claim.severity, 30)

    # Reinterpretation risks vary
    for risk in reinterpretation_risks:
        total_penalty += SEVERITY_PENALTIES.get(risk.severity, 5)

    return max(0, 100 - total_penalty) / 100


def is_discipline_valid(
    missing_terms: List[str],
    prohibited_claims: List[ProhibitedAuthorityClaim],
    mismatches: List[TermConsumptionMismatch],
) -> bool:
    """
    Determine if discipline is valid.

    Invalid if:
      - Any critical severity violations
      - Any prohibited authority claims
      - Missing terms that are required
    """
    # Any prohibited claims = invalid
    if prohibited_claims:
        return False

    # Any critical mismatches = invalid
    for mismatch in mismatches:
        if mismatch.mismatch_type == "governance_tier_violation":
            return False

    # Missing terms = invalid (consumer depends on non-existent terms)
    if missing_terms:
        return False

    return True


# -----------------------------------------------------------------------------
# Deterministic Hash
# -----------------------------------------------------------------------------

def compute_consumption_report_hash(
    consumer_id: str,
    consumed_terms: List[str],
    missing_terms: List[str],
    mismatches: List[TermConsumptionMismatch],
    prohibited_claims: List[ProhibitedAuthorityClaim],
    reinterpretation_risks: List[RuntimeReinterpretationRisk],
    alignment_score: float,
    discipline_valid: bool,
) -> str:
    """
    Compute deterministic hash for a consumption report.

    Includes:
      - consumer_id
      - consumed terms (sorted)
      - missing terms (sorted)
      - mismatch details (sorted by term)
      - prohibited claims (sorted by operation)
      - reinterpretation risks (sorted by term)
      - alignment score
      - validity result

    Excludes:
      - timestamps
      - UUIDs
      - generated report_id
    """
    hash_data = {
        "consumer_id": consumer_id,
        "consumed_terms": sorted(consumed_terms),
        "missing_terms": sorted(missing_terms),
        "mismatches": sorted(
            [
                {
                    "term": m.term,
                    "mismatch_type": m.mismatch_type,
                    "expected_value": m.expected_value,
                    "declared_value": m.declared_value,
                }
                for m in mismatches
            ],
            key=lambda x: x["term"],
        ),
        "prohibited_claims": sorted(
            [
                {
                    "operation": c.operation,
                    "severity": c.severity,
                }
                for c in prohibited_claims
            ],
            key=lambda x: x["operation"],
        ),
        "reinterpretation_risks": sorted(
            [
                {
                    "term": r.term,
                    "risk_type": r.risk_type,
                    "severity": r.severity,
                }
                for r in reinterpretation_risks
            ],
            key=lambda x: x["term"],
        ),
        "alignment_score": round(alignment_score, 4),
        "discipline_valid": discipline_valid,
    }

    json_str = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Report Generation
# -----------------------------------------------------------------------------

def generate_consumption_discipline_report(
    consumer_id: str,
) -> ConsumptionDisciplineReport:
    """
    Generate a consumption discipline report for a consumer.

    Validates:
      - Consumed terms exist in 7M canonical registry
      - No prohibited authority claims
      - No reinterpretation risks

    Does NOT:
      - Mutate consumer
      - Register missing terms
      - Auto-repair violations
    """
    consumer = get_runtime_semantic_consumer(consumer_id)
    if consumer is None:
        raise ValueError(f"Consumer not found: {consumer_id}")

    # Validate consumed terms against 7M registry
    missing_terms, mismatches = validate_consumed_terms(consumer)

    # Detect prohibited authority claims
    prohibited_claims = detect_prohibited_authority_claims(consumer)

    # Detect reinterpretation risks
    reinterpretation_risks = detect_reinterpretation_risks(consumer)

    # Calculate alignment score
    alignment_score = calculate_consumption_alignment_score(
        missing_terms=missing_terms,
        mismatches=mismatches,
        prohibited_claims=prohibited_claims,
        reinterpretation_risks=reinterpretation_risks,
    )

    # Determine validity
    discipline_valid = is_discipline_valid(
        missing_terms=missing_terms,
        prohibited_claims=prohibited_claims,
        mismatches=mismatches,
    )

    # Compute deterministic hash
    report_hash = compute_consumption_report_hash(
        consumer_id=consumer_id,
        consumed_terms=consumer.consumed_terms,
        missing_terms=missing_terms,
        mismatches=mismatches,
        prohibited_claims=prohibited_claims,
        reinterpretation_risks=reinterpretation_risks,
        alignment_score=alignment_score,
        discipline_valid=discipline_valid,
    )

    # Create report
    report = ConsumptionDisciplineReport(
        report_id=f"consumption-{uuid.uuid4().hex[:12]}",
        consumer_id=consumer_id,
        consumed_terms=consumer.consumed_terms,
        missing_terms=missing_terms,
        term_mismatches=mismatches,
        prohibited_authority_claims=prohibited_claims,
        runtime_reinterpretation_risks=reinterpretation_risks,
        consumption_alignment_score=alignment_score,
        discipline_valid=discipline_valid,
        deterministic_report_hash=report_hash,
        execution_authorized=False,
        machine_output_allowed=False,
    )

    # Store report
    store_report(report)

    return report


def generate_all_consumer_reports() -> List[ConsumptionDisciplineReport]:
    """Generate reports for all registered consumers."""
    reports = []
    for consumer in list_runtime_semantic_consumers():
        report = generate_consumption_discipline_report(consumer.consumer_id)
        reports.append(report)
    return reports


# -----------------------------------------------------------------------------
# CI Summary
# -----------------------------------------------------------------------------

class ConsumptionCISummary(BaseModel):
    """
    CI-visible summary for consumption discipline.

    Designed for quick pass/fail determination in CI pipelines.
    """

    status: Literal["pass", "warn", "fail"] = Field(
        ...,
        description="CI status: pass (valid), warn (risks only), fail (violations)"
    )
    consumers_evaluated: int = Field(..., description="Total consumers evaluated")
    consumers_valid: int = Field(..., description="Consumers with valid discipline")
    consumers_invalid: int = Field(..., description="Consumers with violations")
    total_missing_terms: int = Field(..., description="Total missing terms")
    total_prohibited_claims: int = Field(..., description="Total prohibited claims")
    total_reinterpretation_risks: int = Field(..., description="Total risks")
    average_alignment_score: float = Field(..., description="Average alignment")
    summary_message: str = Field(..., description="Human-readable summary")

    # 7N invariants
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        return False


def generate_ci_summary(
    reports: List[ConsumptionDisciplineReport],
) -> ConsumptionCISummary:
    """
    Generate CI-visible summary from consumption reports.

    Status determination:
      - pass: All consumers valid
      - warn: No violations but risks present
      - fail: Any violations (invalid consumers)
    """
    if not reports:
        return ConsumptionCISummary(
            status="pass",
            consumers_evaluated=0,
            consumers_valid=0,
            consumers_invalid=0,
            total_missing_terms=0,
            total_prohibited_claims=0,
            total_reinterpretation_risks=0,
            average_alignment_score=1.0,
            summary_message="No consumers to evaluate.",
            execution_authorized=False,
            machine_output_allowed=False,
        )

    consumers_valid = sum(1 for r in reports if r.discipline_valid)
    consumers_invalid = len(reports) - consumers_valid
    total_missing = sum(len(r.missing_terms) for r in reports)
    total_prohibited = sum(len(r.prohibited_authority_claims) for r in reports)
    total_risks = sum(len(r.runtime_reinterpretation_risks) for r in reports)
    avg_score = sum(r.consumption_alignment_score for r in reports) / len(reports)

    if consumers_invalid > 0:
        status = "fail"
        message = (
            f"Consumption discipline FAILED. {consumers_invalid} of "
            f"{len(reports)} consumers have violations. "
            f"{total_missing} missing terms, {total_prohibited} prohibited claims."
        )
    elif total_risks > 0:
        status = "warn"
        message = (
            f"Consumption discipline valid with warnings. "
            f"{total_risks} reinterpretation risks detected. "
            f"Average alignment: {avg_score:.2%}"
        )
    else:
        status = "pass"
        message = (
            f"Consumption discipline verified. {len(reports)} consumers valid. "
            f"Average alignment: {avg_score:.2%}"
        )

    return ConsumptionCISummary(
        status=status,
        consumers_evaluated=len(reports),
        consumers_valid=consumers_valid,
        consumers_invalid=consumers_invalid,
        total_missing_terms=total_missing,
        total_prohibited_claims=total_prohibited,
        total_reinterpretation_risks=total_risks,
        average_alignment_score=round(avg_score, 4),
        summary_message=message,
        execution_authorized=False,
        machine_output_allowed=False,
    )


# -----------------------------------------------------------------------------
# Policy Information
# -----------------------------------------------------------------------------

class ConsumptionPolicyResponse(BaseModel):
    """7N consumption policy information."""

    immutable: bool = True
    ontology_authoritative: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    mutation_allowed: bool = False
    runtime_may_own_ontology: bool = False
    dev_order: str = "7N"
    governance_tier: str = "Tier 1 - Structural / Runtime Governance"
    guardrail: str = (
        "7N verifies that runtimes consume ontology without owning ontology. "
        "It does not permit runtime execution, ontology mutation, lifecycle "
        "definition, or semantic reinterpretation."
    )
    prohibited_operations: List[str] = [
        "register_term",
        "mutate_ontology",
        "define_lifecycle",
        "reinterpret_term",
        "fork_vocabulary",
        "execute_runtime",
        "generate_machine_output",
    ]
