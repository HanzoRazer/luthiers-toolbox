"""
Ontology Reconciliation Router

CAM Dev Order 7M: REST API for ontology reconciliation infrastructure.

Endpoints:
  GET  /api/cam/ontology/terms          - List canonical terms
  GET  /api/cam/ontology/terms/{term}   - Get canonical term
  GET  /api/cam/ontology/conflicts      - List conflicts
  POST /api/cam/ontology/reconcile      - Generate reconciliation report
  GET  /api/cam/ontology/report/latest  - Latest report
  GET  /api/cam/ontology/domains        - Domain ownership map
  GET  /api/cam/ontology/policy         - Get 7M policy

7M invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7M makes ontology drift visible. It does not automatically repair
  ontology drift.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.cam.canonical_ontology_registry import (
    CanonicalOntologyTerm,
    CanonicalOntologyTermSummary,
    get_canonical_term,
    list_canonical_terms,
    list_terms_for_domain,
    list_domains,
    to_summary,
)
from app.cam.ontology_authority_map import (
    DomainOwnershipSummary,
    get_domain_ownership_summary,
    get_all_domain_summaries,
    get_lifecycle_vocabularies,
)
from app.cam.ontology_reconciliation_engine import (
    OntologyConflict,
    OntologyReconciliationReport,
    list_conflicts,
    get_latest_report,
    list_reports,
    generate_reconciliation_report,
)
from app.cam.ontology_drift_report import (
    OntologyDriftReport,
    CISummary,
    generate_drift_report,
    generate_latest_drift_report,
    generate_ci_summary,
)


router = APIRouter(
    prefix="/api/cam/ontology",
    tags=["cam", "ontology", "governance"],
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class OntologyPolicyResponse(BaseModel):
    """7M ontology policy information."""

    immutable: bool = True
    ontology_authoritative: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    mutation_allowed: bool = False
    automatic_repair: bool = False
    closed_world_detection: bool = True
    dev_order: str = "7M"
    governance_tier: str = "Tier 1 - Structural / Ontology Governance"
    guardrail: str = (
        "7M makes ontology drift visible. It does not automatically repair "
        "ontology drift."
    )


class ReconcileRequest(BaseModel):
    """Request to generate a reconciliation report."""

    include_drift_report: bool = Field(
        default=True,
        description="Include drift analysis in response"
    )


class ReconcileResponse(BaseModel):
    """Response from reconciliation endpoint."""

    reconciliation_report: OntologyReconciliationReport
    drift_report: Optional[OntologyDriftReport] = None
    ci_summary: CISummary


class LifecycleVocabulariesResponse(BaseModel):
    """Lifecycle vocabularies by domain."""

    vocabularies: dict = Field(
        ...,
        description="Domain -> lifecycle terms mapping"
    )
    total_domains: int
    domains_with_lifecycle: int


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/policy",
    response_model=OntologyPolicyResponse,
    summary="Get 7M ontology policy",
)
def get_ontology_policy() -> OntologyPolicyResponse:
    """
    Get the 7M ontology reconciliation policy.

    Returns the invariants and guardrails enforced by this module.
    """
    return OntologyPolicyResponse()


@router.get(
    "/terms",
    response_model=List[CanonicalOntologyTermSummary],
    summary="List canonical terms",
)
def list_terms_endpoint(
    domain: Optional[str] = Query(
        default=None,
        description="Filter by owning domain"
    ),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> List[CanonicalOntologyTermSummary]:
    """
    List all canonical ontology terms.

    Optionally filter by owning domain.
    """
    if domain:
        terms = list_terms_for_domain(domain)
    else:
        terms = list_canonical_terms()

    # Apply pagination
    paginated = terms[offset:offset + limit]

    return [to_summary(t) for t in paginated]


@router.get(
    "/terms/{term}",
    response_model=CanonicalOntologyTerm,
    summary="Get canonical term",
)
def get_term_endpoint(term: str) -> CanonicalOntologyTerm:
    """
    Get a canonical term by name or alias.

    Raises:
        404: If term not found
    """
    result = get_canonical_term(term)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Canonical term not found: {term}"
        )
    return result


@router.get(
    "/domains",
    response_model=List[DomainOwnershipSummary],
    summary="List domain ownership",
)
def list_domains_endpoint() -> List[DomainOwnershipSummary]:
    """
    List all domains with their ownership summaries.
    """
    return get_all_domain_summaries()


@router.get(
    "/domains/{domain}",
    response_model=DomainOwnershipSummary,
    summary="Get domain ownership",
)
def get_domain_endpoint(domain: str) -> DomainOwnershipSummary:
    """
    Get ownership summary for a specific domain.

    Raises:
        404: If domain not found
    """
    result = get_domain_ownership_summary(domain)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Domain not found: {domain}"
        )
    return result


@router.get(
    "/lifecycles",
    response_model=LifecycleVocabulariesResponse,
    summary="Get lifecycle vocabularies",
)
def get_lifecycle_vocabularies_endpoint() -> LifecycleVocabulariesResponse:
    """
    Get all lifecycle vocabularies grouped by domain.
    """
    vocabs = get_lifecycle_vocabularies()
    return LifecycleVocabulariesResponse(
        vocabularies=vocabs,
        total_domains=len(list_domains()),
        domains_with_lifecycle=len(vocabs),
    )


@router.get(
    "/conflicts",
    response_model=List[OntologyConflict],
    summary="List detected conflicts",
)
def list_conflicts_endpoint(
    severity: Optional[str] = Query(
        default=None,
        description="Filter by severity (low, medium, high, critical)"
    ),
    conflict_type: Optional[str] = Query(
        default=None,
        description="Filter by conflict type"
    ),
) -> List[OntologyConflict]:
    """
    List all detected ontology conflicts.

    Optionally filter by severity or conflict type.
    """
    conflicts = list_conflicts()

    if severity:
        conflicts = [c for c in conflicts if c.severity == severity]
    if conflict_type:
        conflicts = [c for c in conflicts if c.conflict_type == conflict_type]

    return conflicts


@router.post(
    "/reconcile",
    response_model=ReconcileResponse,
    summary="Generate reconciliation report",
)
def reconcile_endpoint(
    request: ReconcileRequest = ReconcileRequest(),
) -> ReconcileResponse:
    """
    Generate a reconciliation report.

    This is a passive, read-only operation that:
      - Evaluates all registered terms
      - Detects conflicts
      - Calculates alignment score

    It does NOT:
      - Mutate terms
      - Resolve conflicts automatically
      - Change ownership
    """
    # Generate reconciliation report
    reconciliation_report = generate_reconciliation_report()

    # Generate CI summary
    ci_summary = generate_ci_summary(reconciliation_report)

    # Generate drift report if requested
    drift_report = None
    if request.include_drift_report:
        drift_report = generate_drift_report(reconciliation_report)

    return ReconcileResponse(
        reconciliation_report=reconciliation_report,
        drift_report=drift_report,
        ci_summary=ci_summary,
    )


@router.get(
    "/report/latest",
    response_model=Optional[OntologyReconciliationReport],
    summary="Get latest report",
)
def get_latest_report_endpoint() -> Optional[OntologyReconciliationReport]:
    """
    Get the most recent reconciliation report.

    Returns None if no reports have been generated.
    """
    return get_latest_report()


@router.get(
    "/reports",
    response_model=List[OntologyReconciliationReport],
    summary="List all reports",
)
def list_reports_endpoint(
    limit: int = Query(default=10, ge=1, le=100),
) -> List[OntologyReconciliationReport]:
    """
    List reconciliation reports (most recent first).
    """
    reports = list_reports()
    # Sort by generated_at descending
    sorted_reports = sorted(reports, key=lambda r: r.generated_at, reverse=True)
    return sorted_reports[:limit]


@router.get(
    "/drift/latest",
    response_model=Optional[OntologyDriftReport],
    summary="Get latest drift report",
)
def get_latest_drift_report_endpoint() -> Optional[OntologyDriftReport]:
    """
    Get the most recent drift report.

    Returns None if no reports have been generated.
    """
    return generate_latest_drift_report()


@router.get(
    "/ci",
    response_model=CISummary,
    summary="Get CI summary",
)
def get_ci_summary_endpoint() -> CISummary:
    """
    Get CI-visible summary from latest report.

    Returns a pass/warn/fail status suitable for CI pipelines.

    If no report exists, generates one first.
    """
    latest = get_latest_report()
    if latest is None:
        latest = generate_reconciliation_report()

    return generate_ci_summary(latest)
