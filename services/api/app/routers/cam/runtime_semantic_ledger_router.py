"""
Runtime Semantic Ledger Router

CAM Dev Order 7O: REST API for runtime semantic consumption ledger,
drift escalation, and replay.

Endpoints:
  GET  /api/cam/runtime-ledger/entries                  - List entries
  GET  /api/cam/runtime-ledger/entries/{entry_id}       - Get entry
  GET  /api/cam/runtime-ledger/consumer/{consumer_id}   - Consumer lineage
  POST /api/cam/runtime-ledger/record                   - Record ledger entry
  POST /api/cam/runtime-ledger/escalation/{consumer_id} - Escalation evaluation
  POST /api/cam/runtime-ledger/replay/{consumer_id}     - Replay lineage
  GET  /api/cam/runtime-ledger/report/latest            - Latest escalation
  GET  /api/cam/runtime-ledger/ci                       - CI summary

No mutation endpoints.

7O invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7O records how runtimes consume ontology over time. It does not permit
  runtime execution, ontology mutation, semantic reinterpretation, or
  machine authority.
"""

from typing import Any, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.cam.runtime_semantic_consumption import (
    ConsumptionDisciplineReport,
    get_runtime_semantic_consumer,
)
from app.cam.runtime_consumption_policy import (
    get_reports_for_consumer,
    get_latest_report,
)
from app.cam.runtime_semantic_consumption_ledger import (
    RuntimeSemanticConsumptionLedgerEntry,
    LedgerEntrySummary,
    get_ledger_entry,
    list_ledger_entries,
    list_ledger_entries_for_consumer,
    list_consumers_with_ledger_entries,
    to_ledger_summary,
    create_ledger_entry_from_report,
)
from app.cam.runtime_drift_escalation_engine import (
    RuntimeDriftEscalationEvaluation,
    evaluate_runtime_drift_escalation,
    list_escalation_evaluations,
    get_latest_escalation_for_consumer,
)
from app.cam.runtime_semantic_replay import (
    RuntimeSemanticReplayResult,
    replay_runtime_semantic_lineage,
    get_latest_replay_for_consumer,
)


router = APIRouter(
    prefix="/api/cam/runtime-ledger",
    tags=["cam", "ledger", "governance"],
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class RecordLedgerEntryRequest(BaseModel):
    """Request to record a ledger entry from a 7N report."""

    consumer_id: str = Field(..., description="Consumer ID")
    report_hash: Optional[str] = Field(
        None,
        description="Specific report hash to use (latest if not provided)"
    )
    parent_ledger_hashes: Optional[List[str]] = Field(
        None,
        description="Override parent hashes (linear chain if not provided)"
    )


class LedgerPolicyResponse(BaseModel):
    """7O ledger policy information."""

    immutable: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    dev_order: str = "7O"
    governance_tier: str = "Tier 1 — Ontology Governance / Tier 2 — Runtime Governance"
    guardrail: str = (
        "7O records how runtimes consume ontology over time. It does not "
        "permit runtime execution, ontology mutation, semantic "
        "reinterpretation, or machine authority."
    )
    boundary: str = (
        "7O is historical semantic governance memory, not runtime control."
    )


class LedgerCISummary(BaseModel):
    """CI-visible summary for runtime semantic ledger."""

    status: Literal["pass", "warn", "fail"] = Field(
        ...,
        description="CI status"
    )
    total_consumers_with_entries: int = Field(
        ...,
        description="Consumers with ledger entries"
    )
    total_ledger_entries: int = Field(
        ...,
        description="Total ledger entries"
    )
    invalid_entry_count: int = Field(
        ...,
        description="Invalid entries"
    )
    escalation_count: int = Field(
        ...,
        description="Entries with escalation recommended"
    )
    highest_escalation_severity: str = Field(
        ...,
        description="Highest escalation severity"
    )
    summary_message: str = Field(
        ...,
        description="Human-readable summary"
    )

    # 7O invariants
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


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/policy",
    response_model=LedgerPolicyResponse,
    summary="Get 7O ledger policy",
)
def get_ledger_policy() -> LedgerPolicyResponse:
    """
    Get the 7O runtime semantic ledger policy.

    Returns the invariants and guardrails enforced by this module.
    """
    return LedgerPolicyResponse()


@router.get(
    "/entries",
    response_model=List[LedgerEntrySummary],
    summary="List ledger entries",
)
def list_entries_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> List[LedgerEntrySummary]:
    """
    List all runtime semantic ledger entries.
    """
    entries = list_ledger_entries()

    # Sort by created_at descending
    sorted_entries = sorted(entries, key=lambda e: e.created_at, reverse=True)

    # Apply pagination
    paginated = sorted_entries[offset:offset + limit]

    return [to_ledger_summary(e) for e in paginated]


@router.get(
    "/entries/{entry_id}",
    response_model=RuntimeSemanticConsumptionLedgerEntry,
    summary="Get ledger entry",
)
def get_entry_endpoint(entry_id: str) -> RuntimeSemanticConsumptionLedgerEntry:
    """
    Get a specific ledger entry by ID.

    Raises:
        404: If entry not found
    """
    entry = get_ledger_entry(entry_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ledger entry not found: {entry_id}"
        )
    return entry


@router.get(
    "/consumer/{consumer_id}",
    response_model=List[RuntimeSemanticConsumptionLedgerEntry],
    summary="Get consumer lineage",
)
def get_consumer_lineage_endpoint(
    consumer_id: str,
) -> List[RuntimeSemanticConsumptionLedgerEntry]:
    """
    Get all ledger entries for a consumer (ordered by creation).

    This is the consumer's semantic consumption lineage.
    """
    # Verify consumer exists
    consumer = get_runtime_semantic_consumer(consumer_id)
    if consumer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Consumer not found: {consumer_id}"
        )

    return list_ledger_entries_for_consumer(consumer_id)


@router.post(
    "/record",
    response_model=RuntimeSemanticConsumptionLedgerEntry,
    summary="Record ledger entry",
)
def record_ledger_entry_endpoint(
    request: RecordLedgerEntryRequest,
) -> RuntimeSemanticConsumptionLedgerEntry:
    """
    Record a ledger entry from a 7N consumption report.

    This creates an immutable ledger entry that records the
    consumption state for governance lineage tracking.

    Raises:
        404: If consumer or report not found
    """
    # Verify consumer exists
    consumer = get_runtime_semantic_consumer(request.consumer_id)
    if consumer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Consumer not found: {request.consumer_id}"
        )

    # Get the report
    if request.report_hash:
        # Find report by hash
        reports = get_reports_for_consumer(request.consumer_id)
        matching = [
            r for r in reports
            if r.deterministic_report_hash == request.report_hash
        ]
        if not matching:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found with hash: {request.report_hash}"
            )
        report = matching[0]
    else:
        # Use latest report
        reports = get_reports_for_consumer(request.consumer_id)
        if not reports:
            raise HTTPException(
                status_code=404,
                detail=f"No reports found for consumer: {request.consumer_id}"
            )
        report = max(reports, key=lambda r: r.generated_at)

    # Create ledger entry
    entry = create_ledger_entry_from_report(
        report=report,
        parent_ledger_hashes=request.parent_ledger_hashes,
    )

    return entry


@router.post(
    "/escalation/{consumer_id}",
    response_model=RuntimeDriftEscalationEvaluation,
    summary="Evaluate escalation",
)
def evaluate_escalation_endpoint(
    consumer_id: str,
) -> RuntimeDriftEscalationEvaluation:
    """
    Evaluate runtime drift escalation for a consumer.

    Analyzes the consumer's ledger history for repeated drift patterns,
    authority violations, and determines escalation severity.
    """
    # Verify consumer exists
    consumer = get_runtime_semantic_consumer(consumer_id)
    if consumer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Consumer not found: {consumer_id}"
        )

    return evaluate_runtime_drift_escalation(consumer_id)


@router.post(
    "/replay/{consumer_id}",
    response_model=RuntimeSemanticReplayResult,
    summary="Replay lineage",
)
def replay_lineage_endpoint(
    consumer_id: str,
) -> RuntimeSemanticReplayResult:
    """
    Replay the runtime semantic consumption lineage for a consumer.

    Performs deterministic governance lineage replay:
      - Verifies parent hash continuity
      - Detects drift progression
      - Detects escalation progression
      - Confirms invariants remain valid

    Does NOT re-run 7N validation or execute runtime behavior.
    """
    # Verify consumer exists
    consumer = get_runtime_semantic_consumer(consumer_id)
    if consumer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Consumer not found: {consumer_id}"
        )

    return replay_runtime_semantic_lineage(consumer_id)


@router.get(
    "/report/latest",
    response_model=Optional[RuntimeDriftEscalationEvaluation],
    summary="Get latest escalation report",
)
def get_latest_escalation_report_endpoint(
    consumer_id: Optional[str] = Query(
        default=None,
        description="Filter by consumer ID"
    ),
) -> Optional[RuntimeDriftEscalationEvaluation]:
    """
    Get the most recent escalation evaluation.

    Optionally filter by consumer ID.
    """
    if consumer_id:
        return get_latest_escalation_for_consumer(consumer_id)

    # Get latest across all consumers
    all_evals = list_escalation_evaluations()
    if not all_evals:
        return None
    return max(all_evals, key=lambda e: e.evaluated_at)


@router.get(
    "/ci",
    response_model=LedgerCISummary,
    summary="Get CI summary",
)
def get_ci_summary_endpoint() -> LedgerCISummary:
    """
    Get CI-visible summary for runtime semantic ledger.

    Returns pass/warn/fail status suitable for CI pipelines.
    """
    entries = list_ledger_entries()
    consumers = list_consumers_with_ledger_entries()

    # Count invalid entries
    invalid_count = sum(
        1 for e in entries if not e.ontology_consumption_valid
    )

    # Count escalation recommended
    escalation_count = sum(
        1 for e in entries if e.escalation_recommended
    )

    # Determine highest severity from escalation evaluations
    all_evals = list_escalation_evaluations()
    severity_order = ["none", "low", "medium", "high", "critical"]
    highest_severity = "none"
    for eval_result in all_evals:
        if severity_order.index(eval_result.escalation_severity) > \
           severity_order.index(highest_severity):
            highest_severity = eval_result.escalation_severity

    # Determine status
    if highest_severity == "critical":
        status = "fail"
        message = (
            f"Runtime semantic ledger FAILED. Critical escalation detected. "
            f"{invalid_count} invalid entries, {escalation_count} with "
            f"escalation recommended."
        )
    elif highest_severity in ("medium", "high") or invalid_count > 0:
        status = "warn"
        message = (
            f"Runtime semantic ledger has warnings. {invalid_count} invalid "
            f"entries, highest escalation: {highest_severity}."
        )
    else:
        status = "pass"
        message = (
            f"Runtime semantic ledger healthy. {len(entries)} entries across "
            f"{len(consumers)} consumers."
        )

    return LedgerCISummary(
        status=status,
        total_consumers_with_entries=len(consumers),
        total_ledger_entries=len(entries),
        invalid_entry_count=invalid_count,
        escalation_count=escalation_count,
        highest_escalation_severity=highest_severity,
        summary_message=message,
        execution_authorized=False,
        machine_output_allowed=False,
    )
