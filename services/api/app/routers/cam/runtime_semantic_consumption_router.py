"""
Runtime Semantic Consumption Router

CAM Dev Order 7N: REST API for runtime semantic consumption discipline.

Endpoints:
  GET  /api/cam/consumption/policy               - Get 7N policy
  GET  /api/cam/consumption/consumers            - List consumers
  GET  /api/cam/consumption/consumers/{id}       - Get consumer
  GET  /api/cam/consumption/consumers/domain/{d} - List by domain
  POST /api/cam/consumption/validate             - Validate consumer
  POST /api/cam/consumption/validate/all         - Validate all consumers
  GET  /api/cam/consumption/reports              - List reports
  GET  /api/cam/consumption/reports/latest       - Get latest report
  GET  /api/cam/consumption/ci                   - Get CI summary

7N invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7N verifies that runtimes consume ontology without owning ontology.
  It does not permit runtime execution, ontology mutation, lifecycle
  definition, or semantic reinterpretation.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.cam.runtime_semantic_consumption import (
    RuntimeSemanticConsumer,
    RuntimeSemanticConsumerSummary,
    ConsumptionDisciplineReport,
    get_runtime_semantic_consumer,
    list_runtime_semantic_consumers,
    list_consumers_for_domain,
    list_consumer_domains,
    to_consumer_summary,
)
from app.cam.runtime_consumption_policy import (
    ConsumptionPolicyResponse,
    ConsumptionCISummary,
    generate_consumption_discipline_report,
    generate_all_consumer_reports,
    generate_ci_summary,
    list_reports,
    get_latest_report,
    get_reports_for_consumer,
)


router = APIRouter(
    prefix="/api/cam/consumption",
    tags=["cam", "consumption", "governance"],
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class ValidateConsumerRequest(BaseModel):
    """Request to validate a specific consumer."""

    consumer_id: str = Field(..., description="Consumer ID to validate")


class ValidateAllResponse(BaseModel):
    """Response from validating all consumers."""

    reports: List[ConsumptionDisciplineReport]
    ci_summary: ConsumptionCISummary


class ConsumerDomainsResponse(BaseModel):
    """Response listing consumer domains."""

    domains: List[str]
    total_consumers: int


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/policy",
    response_model=ConsumptionPolicyResponse,
    summary="Get 7N consumption policy",
)
def get_consumption_policy() -> ConsumptionPolicyResponse:
    """
    Get the 7N runtime semantic consumption policy.

    Returns the invariants and guardrails enforced by this module.
    """
    return ConsumptionPolicyResponse()


@router.get(
    "/consumers",
    response_model=List[RuntimeSemanticConsumerSummary],
    summary="List runtime consumers",
)
def list_consumers_endpoint(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> List[RuntimeSemanticConsumerSummary]:
    """
    List all registered runtime semantic consumers.
    """
    consumers = list_runtime_semantic_consumers()

    # Apply pagination
    paginated = consumers[offset:offset + limit]

    return [to_consumer_summary(c) for c in paginated]


@router.get(
    "/consumers/domains",
    response_model=ConsumerDomainsResponse,
    summary="List consumer domains",
)
def list_consumer_domains_endpoint() -> ConsumerDomainsResponse:
    """
    List all domains with registered consumers.
    """
    domains = list_consumer_domains()
    total = len(list_runtime_semantic_consumers())
    return ConsumerDomainsResponse(
        domains=domains,
        total_consumers=total,
    )


@router.get(
    "/consumers/{consumer_id}",
    response_model=RuntimeSemanticConsumer,
    summary="Get consumer by ID",
)
def get_consumer_endpoint(consumer_id: str) -> RuntimeSemanticConsumer:
    """
    Get a specific runtime semantic consumer by ID.

    Raises:
        404: If consumer not found
    """
    consumer = get_runtime_semantic_consumer(consumer_id)
    if consumer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Consumer not found: {consumer_id}"
        )
    return consumer


@router.get(
    "/consumers/domain/{domain}",
    response_model=List[RuntimeSemanticConsumerSummary],
    summary="List consumers by domain",
)
def list_consumers_by_domain_endpoint(
    domain: str,
) -> List[RuntimeSemanticConsumerSummary]:
    """
    List consumers for a specific domain.
    """
    consumers = list_consumers_for_domain(domain)
    return [to_consumer_summary(c) for c in consumers]


@router.post(
    "/validate",
    response_model=ConsumptionDisciplineReport,
    summary="Validate consumer discipline",
)
def validate_consumer_endpoint(
    request: ValidateConsumerRequest,
) -> ConsumptionDisciplineReport:
    """
    Validate consumption discipline for a specific consumer.

    Validates:
      - Consumed terms exist in 7M canonical registry
      - No prohibited authority claims
      - No reinterpretation risks

    Does NOT:
      - Mutate consumer
      - Register missing terms
      - Auto-repair violations

    Raises:
        404: If consumer not found
    """
    consumer = get_runtime_semantic_consumer(request.consumer_id)
    if consumer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Consumer not found: {request.consumer_id}"
        )

    return generate_consumption_discipline_report(request.consumer_id)


@router.post(
    "/validate/all",
    response_model=ValidateAllResponse,
    summary="Validate all consumers",
)
def validate_all_consumers_endpoint() -> ValidateAllResponse:
    """
    Validate consumption discipline for all registered consumers.

    Returns individual reports and CI summary.
    """
    reports = generate_all_consumer_reports()
    ci_summary = generate_ci_summary(reports)

    return ValidateAllResponse(
        reports=reports,
        ci_summary=ci_summary,
    )


@router.get(
    "/reports",
    response_model=List[ConsumptionDisciplineReport],
    summary="List consumption reports",
)
def list_reports_endpoint(
    consumer_id: Optional[str] = Query(
        default=None,
        description="Filter by consumer ID"
    ),
    limit: int = Query(default=20, ge=1, le=100),
) -> List[ConsumptionDisciplineReport]:
    """
    List consumption discipline reports.

    Optionally filter by consumer ID.
    """
    if consumer_id:
        reports = get_reports_for_consumer(consumer_id)
    else:
        reports = list_reports()

    # Sort by generated_at descending
    sorted_reports = sorted(reports, key=lambda r: r.generated_at, reverse=True)
    return sorted_reports[:limit]


@router.get(
    "/reports/latest",
    response_model=Optional[ConsumptionDisciplineReport],
    summary="Get latest report",
)
def get_latest_report_endpoint() -> Optional[ConsumptionDisciplineReport]:
    """
    Get the most recent consumption discipline report.

    Returns None if no reports have been generated.
    """
    return get_latest_report()


@router.get(
    "/ci",
    response_model=ConsumptionCISummary,
    summary="Get CI summary",
)
def get_ci_summary_endpoint() -> ConsumptionCISummary:
    """
    Get CI-visible summary of consumption discipline.

    Validates all consumers and returns pass/warn/fail status.

    If no reports exist, generates them first.
    """
    existing_reports = list_reports()

    if not existing_reports:
        # Generate reports for all consumers
        reports = generate_all_consumer_reports()
    else:
        # Use existing reports
        reports = existing_reports

    return generate_ci_summary(reports)
