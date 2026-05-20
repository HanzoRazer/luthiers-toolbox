"""
Runtime Governance Enforcement Router

CAM Dev Order 7P: REST endpoints for runtime governance enforcement.

Endpoints:
  POST /api/cam/runtime-enforcement/evaluate    - Evaluate runtime pathway
  GET  /api/cam/runtime-enforcement/report/latest - Get latest CI report
  GET  /api/cam/runtime-enforcement/violations  - List RED evaluations
  GET  /api/cam/runtime-enforcement/checkpoints - List all evaluations
  GET  /api/cam/runtime-enforcement/ci          - CI summary
  GET  /api/cam/runtime-enforcement/policy      - Get enforcement policy

7P invariants (always enforced):
  - execution_authorized = False
  - machine_output_allowed = False
  - serializer_execution_allowed = False
  - runtime_self_authorized = False

Guardrail:
  7P evaluates declared runtime-adjacent pathways for governance compliance.
  It does not intercept live traffic, invoke serializers, execute runtimes,
  or authorize machine output.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.cam.runtime_governance_enforcement import (
    EnforcementCheckpointReport,
    EnforcementSeverity,
    RuntimeEnforcementRequest,
    RuntimeGovernanceEnforcementEvaluation,
    get_enforcement_evaluation,
    get_enforcement_evaluations_by_severity,
    get_latest_enforcement_report,
    list_enforcement_evaluations,
    list_enforcement_reports,
)
from app.cam.runtime_enforcement_policy import (
    evaluate_runtime_enforcement,
    generate_enforcement_ci_report,
    get_enforcement_policy,
)


router = APIRouter(
    prefix="/api/cam/runtime-enforcement",
    tags=["CAM", "Runtime", "Enforcement", "Governance"],
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class EvaluateRequest(BaseModel):
    """Request to evaluate runtime governance enforcement."""

    runtime_pathway: str = Field(
        ...,
        description="Runtime pathway declaration (format: type:target)",
        examples=[
            "translator_dispatch:dxf_r12",
            "export_route:/api/cam/export/lifecycle/validate",
            "serializer_boundary:dxf_compat",
        ],
    )
    quarantine_id: Optional[str] = Field(
        default=None,
        description="Reference to 7H quarantine evaluation",
    )
    consumer_id: Optional[str] = Field(
        default=None,
        description="Reference to 7N semantic consumer",
    )
    ledger_entry_id: Optional[str] = Field(
        default=None,
        description="Reference to 7O ledger entry",
    )
    translator_id: Optional[str] = Field(
        default=None,
        description="Translator identifier",
    )
    export_route: Optional[str] = Field(
        default=None,
        description="Export route path",
    )
    request_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for evaluation",
    )


class EvaluationSummary(BaseModel):
    """Lightweight evaluation summary for list endpoints."""

    evaluation_id: str
    runtime_pathway: str
    pathway_type: str
    severity: EnforcementSeverity
    governance_checkpoint_passed: bool
    runtime_quarantine_respected: bool
    serializer_path_detected: bool
    runtime_bypass_detected: bool
    authority_leak_detected: bool
    blocking_issues_count: int
    warnings_count: int


class CISummary(BaseModel):
    """CI-compatible summary response."""

    status: str = Field(..., description="pass, warn, or fail")
    evaluations_count: int
    evaluations_passed: int
    evaluations_failed: int
    evaluations_warned: int
    serializer_paths_detected: int
    runtime_bypasses_detected: int
    authority_leaks_detected: int
    quarantine_violations: int
    summary_message: str
    deterministic_report_hash: str


class ViolationsResponse(BaseModel):
    """Response for violations endpoint."""

    total_violations: int
    violations: List[EvaluationSummary]
    blocking_issues: List[str]


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/evaluate",
    response_model=RuntimeGovernanceEnforcementEvaluation,
    summary="Evaluate runtime pathway for governance compliance",
    description="""
Evaluate a declared runtime-adjacent pathway for governance compliance.

This endpoint validates the pathway against:
- 7H execution quarantine state
- 7N semantic consumption discipline
- 7O consumption ledger and drift state

Returns enforcement evaluation with checkpoint results and severity.

**7P Guardrail**: This endpoint evaluates declarations, not live traffic.
It does not invoke serializers, execute runtimes, or authorize machine output.
""",
)
def evaluate_enforcement(request: EvaluateRequest) -> RuntimeGovernanceEnforcementEvaluation:
    """Evaluate runtime pathway for governance compliance."""
    enforcement_request = RuntimeEnforcementRequest(
        runtime_pathway=request.runtime_pathway,
        quarantine_id=request.quarantine_id,
        consumer_id=request.consumer_id,
        ledger_entry_id=request.ledger_entry_id,
        translator_id=request.translator_id,
        export_route=request.export_route,
        request_context=request.request_context,
    )

    return evaluate_runtime_enforcement(enforcement_request)


@router.get(
    "/report/latest",
    response_model=EnforcementCheckpointReport,
    summary="Get latest enforcement CI report",
    description="Returns the most recent enforcement checkpoint report.",
)
def get_latest_report() -> EnforcementCheckpointReport:
    """Get latest enforcement CI report."""
    report = get_latest_enforcement_report()
    if not report:
        # Generate a fresh report if none exists
        return generate_enforcement_ci_report()
    return report


@router.get(
    "/violations",
    response_model=ViolationsResponse,
    summary="List RED enforcement violations",
    description="Returns all enforcement evaluations with RED severity.",
)
def list_violations() -> ViolationsResponse:
    """List RED enforcement violations."""
    red_evaluations = get_enforcement_evaluations_by_severity("red")

    summaries = [
        EvaluationSummary(
            evaluation_id=e.evaluation_id,
            runtime_pathway=e.runtime_pathway,
            pathway_type=e.parsed_pathway.pathway_type,
            severity=e.severity,
            governance_checkpoint_passed=e.governance_checkpoint_passed,
            runtime_quarantine_respected=e.runtime_quarantine_respected,
            serializer_path_detected=e.serializer_path_detected,
            runtime_bypass_detected=e.runtime_bypass_detected,
            authority_leak_detected=e.authority_leak_detected,
            blocking_issues_count=len(e.blocking_issues),
            warnings_count=len(e.warnings),
        )
        for e in red_evaluations
    ]

    all_blocking: List[str] = []
    for e in red_evaluations:
        all_blocking.extend(e.blocking_issues)

    return ViolationsResponse(
        total_violations=len(red_evaluations),
        violations=summaries,
        blocking_issues=list(set(all_blocking)),
    )


@router.get(
    "/checkpoints",
    response_model=List[EvaluationSummary],
    summary="List all enforcement evaluations",
    description="Returns summaries of all enforcement evaluations.",
)
def list_checkpoints(
    severity: Optional[EnforcementSeverity] = Query(
        default=None,
        description="Filter by severity (green, yellow, red)",
    ),
) -> List[EvaluationSummary]:
    """List all enforcement evaluations."""
    if severity:
        evaluations = get_enforcement_evaluations_by_severity(severity)
    else:
        evaluations = list_enforcement_evaluations()

    return [
        EvaluationSummary(
            evaluation_id=e.evaluation_id,
            runtime_pathway=e.runtime_pathway,
            pathway_type=e.parsed_pathway.pathway_type,
            severity=e.severity,
            governance_checkpoint_passed=e.governance_checkpoint_passed,
            runtime_quarantine_respected=e.runtime_quarantine_respected,
            serializer_path_detected=e.serializer_path_detected,
            runtime_bypass_detected=e.runtime_bypass_detected,
            authority_leak_detected=e.authority_leak_detected,
            blocking_issues_count=len(e.blocking_issues),
            warnings_count=len(e.warnings),
        )
        for e in evaluations
    ]


@router.get(
    "/checkpoints/{evaluation_id}",
    response_model=RuntimeGovernanceEnforcementEvaluation,
    summary="Get enforcement evaluation by ID",
    description="Returns full enforcement evaluation details.",
)
def get_checkpoint(evaluation_id: str) -> RuntimeGovernanceEnforcementEvaluation:
    """Get enforcement evaluation by ID."""
    evaluation = get_enforcement_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail=f"Enforcement evaluation not found: {evaluation_id}",
        )
    return evaluation


@router.get(
    "/ci",
    response_model=CISummary,
    summary="Get CI enforcement summary",
    description="""
Returns CI-compatible enforcement summary.

Status determination:
- **pass**: All evaluations GREEN
- **warn**: YELLOW evaluations present (no RED)
- **fail**: Any RED evaluations

Use this endpoint in CI pipelines to gate deployments.
""",
)
def get_ci_summary() -> CISummary:
    """Get CI enforcement summary."""
    report = generate_enforcement_ci_report()

    return CISummary(
        status=report.ci_status,
        evaluations_count=report.evaluations_count,
        evaluations_passed=report.evaluations_passed,
        evaluations_failed=report.evaluations_failed,
        evaluations_warned=report.evaluations_warned,
        serializer_paths_detected=report.serializer_paths_detected,
        runtime_bypasses_detected=report.runtime_bypasses_detected,
        authority_leaks_detected=report.authority_leaks_detected,
        quarantine_violations=report.quarantine_violations,
        summary_message=report.summary_message,
        deterministic_report_hash=report.deterministic_report_hash,
    )


@router.get(
    "/policy",
    response_model=Dict[str, Any],
    summary="Get enforcement policy",
    description="""
Returns 7P enforcement policy constants.

Policy is hard-coded (not configurable) because this is
boundary enforcement, not tenant policy.

Includes:
- Prohibited runtime actions
- RED conditions (blocking)
- YELLOW conditions (warnings)
- Checkpoint types
- 7P invariants
""",
)
def get_policy() -> Dict[str, Any]:
    """Get enforcement policy."""
    return get_enforcement_policy()


@router.get(
    "/reports",
    response_model=List[EnforcementCheckpointReport],
    summary="List all enforcement reports",
    description="Returns all generated enforcement checkpoint reports.",
)
def list_reports() -> List[EnforcementCheckpointReport]:
    """List all enforcement reports."""
    return list_enforcement_reports()
