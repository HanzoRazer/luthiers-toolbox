"""
Post-Freeze Expansion Router

CAM Dev Order 8A: Post-freeze expansion proposal and readiness endpoints.

Provides:
  - Proposal CRUD
  - Readiness evaluation endpoint
  - CI summary endpoint
  - Status endpoint

8A invariants:
  - All endpoints maintain implementation_authorized=False
  - No execution authorization
  - No machine output

Core principle:
  Router exposes proposals for human review.
  It does not authorize implementation, execution, or machine output.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.post_freeze_expansion_gate import (
    PostFreezeExpansionProposal,
    TargetLayer,
    ProposalState,
    create_post_freeze_proposal,
    get_proposal_summary,
    VALID_TARGET_LAYERS,
)
from app.cam.post_freeze_readiness import (
    PostFreezeExpansionReadiness,
    get_readiness_summary,
    get_readiness_status_message,
)
from app.cam.post_freeze_registry import (
    register_post_freeze_proposal,
    get_post_freeze_proposal,
    get_latest_post_freeze_proposal,
    list_post_freeze_proposals,
    list_proposals_by_target_layer,
    register_post_freeze_readiness,
    get_post_freeze_readiness,
    get_latest_post_freeze_readiness,
    list_post_freeze_readiness,
    list_readiness_for_proposal,
    evaluate_post_freeze_readiness,
    build_post_freeze_ci_summary,
    get_post_freeze_status_summary,
)


router = APIRouter(
    prefix="/api/cam/post-freeze",
    tags=["CAM", "Post-Freeze", "Governance"]
)


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────────────────────────────────────────

class CreateProposalRequest(BaseModel):
    """Request to create a post-freeze expansion proposal."""
    title: str
    target_layer: TargetLayer
    proposed_capability: str
    depends_on_freeze_id: Optional[str] = None
    expected_artifacts: List[str] = Field(default_factory=list)
    governance_risks: List[str] = Field(default_factory=list)
    required_reviews: List[str] = Field(default_factory=list)
    ontology_mutation_requested: bool = False
    baseline_rewrite_requested: bool = False
    proposal_state: ProposalState = "draft"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProposalResponse(BaseModel):
    """Response containing a proposal."""
    proposal_id: str
    title: str
    target_layer: str
    depends_on_freeze_id: Optional[str]
    proposed_capability: str
    expected_artifacts: List[str]
    governance_risks: List[str]
    required_reviews: List[str]
    ontology_mutation_requested: bool
    baseline_rewrite_requested: bool
    implementation_authorized: bool
    execution_authorized: bool
    machine_output_allowed: bool
    proposal_state: str
    deterministic_proposal_hash: str


class ReadinessResponse(BaseModel):
    """Response containing a readiness evaluation."""
    readiness_id: str
    proposal_id: str
    freeze_compatible: bool
    freeze_exists: bool
    freeze_status: Optional[str]
    required_reviews_declared: bool
    no_execution_authority: bool
    no_machine_output_authority: bool
    ontology_mutation_requested: bool
    baseline_rewrite_requested: bool
    gate: str
    blocking_issues: List[str]
    warnings: List[str]
    status_message: str
    implementation_authorized: bool
    execution_authorized: bool
    machine_output_allowed: bool
    deterministic_readiness_hash: str


class CISummaryResponse(BaseModel):
    """CI summary response."""
    total_proposals: int
    total_readiness_evaluations: int
    green_count: int
    yellow_count: int
    red_count: int
    missing_freeze_ref_count: int
    baseline_rewrite_request_count: int
    ontology_mutation_request_count: int
    execution_request_count: int
    machine_output_request_count: int
    status: str
    blocking_issues: List[str]
    warnings: List[str]


class StatusResponse(BaseModel):
    """Status summary response."""
    total_proposals: int
    draft_proposals: int
    submitted_proposals: int
    total_readiness_evaluations: int
    green_count: int
    yellow_count: int
    red_count: int
    latest_proposal_id: Optional[str]
    latest_proposal_title: Optional[str]
    latest_readiness_id: Optional[str]
    latest_readiness_gate: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# Proposal endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/proposals", response_model=ProposalResponse)
def create_proposal(request: CreateProposalRequest) -> ProposalResponse:
    """
    Create a post-freeze expansion proposal.

    Proposals declare intent for human review.
    implementation_authorized is always False.
    """
    proposal = create_post_freeze_proposal(
        title=request.title,
        target_layer=request.target_layer,
        proposed_capability=request.proposed_capability,
        depends_on_freeze_id=request.depends_on_freeze_id,
        expected_artifacts=request.expected_artifacts,
        governance_risks=request.governance_risks,
        required_reviews=request.required_reviews,
        ontology_mutation_requested=request.ontology_mutation_requested,
        baseline_rewrite_requested=request.baseline_rewrite_requested,
        proposal_state=request.proposal_state,
        metadata=request.metadata,
    )

    success, error = register_post_freeze_proposal(proposal)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return ProposalResponse(
        proposal_id=proposal.proposal_id,
        title=proposal.title,
        target_layer=proposal.target_layer,
        depends_on_freeze_id=proposal.depends_on_freeze_id,
        proposed_capability=proposal.proposed_capability,
        expected_artifacts=proposal.expected_artifacts,
        governance_risks=proposal.governance_risks,
        required_reviews=proposal.required_reviews,
        ontology_mutation_requested=proposal.ontology_mutation_requested,
        baseline_rewrite_requested=proposal.baseline_rewrite_requested,
        implementation_authorized=proposal.implementation_authorized,
        execution_authorized=proposal.execution_authorized,
        machine_output_allowed=proposal.machine_output_allowed,
        proposal_state=proposal.proposal_state,
        deterministic_proposal_hash=proposal.deterministic_proposal_hash,
    )


@router.get("/proposals", response_model=List[Dict[str, Any]])
def list_proposals(target_layer: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all proposals, optionally filtered by target layer."""
    if target_layer:
        if target_layer not in VALID_TARGET_LAYERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target_layer: {target_layer}"
            )
        proposals = list_proposals_by_target_layer(target_layer)
    else:
        proposals = list_post_freeze_proposals()
    return [get_proposal_summary(p) for p in proposals]


@router.get("/proposals/latest", response_model=ProposalResponse)
def get_latest_proposal() -> ProposalResponse:
    """Get the most recent proposal."""
    proposal = get_latest_post_freeze_proposal()
    if not proposal:
        raise HTTPException(status_code=404, detail="No proposals registered")

    return ProposalResponse(
        proposal_id=proposal.proposal_id,
        title=proposal.title,
        target_layer=proposal.target_layer,
        depends_on_freeze_id=proposal.depends_on_freeze_id,
        proposed_capability=proposal.proposed_capability,
        expected_artifacts=proposal.expected_artifacts,
        governance_risks=proposal.governance_risks,
        required_reviews=proposal.required_reviews,
        ontology_mutation_requested=proposal.ontology_mutation_requested,
        baseline_rewrite_requested=proposal.baseline_rewrite_requested,
        implementation_authorized=proposal.implementation_authorized,
        execution_authorized=proposal.execution_authorized,
        machine_output_allowed=proposal.machine_output_allowed,
        proposal_state=proposal.proposal_state,
        deterministic_proposal_hash=proposal.deterministic_proposal_hash,
    )


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
def get_proposal(proposal_id: str) -> ProposalResponse:
    """Get a proposal by ID."""
    proposal = get_post_freeze_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    return ProposalResponse(
        proposal_id=proposal.proposal_id,
        title=proposal.title,
        target_layer=proposal.target_layer,
        depends_on_freeze_id=proposal.depends_on_freeze_id,
        proposed_capability=proposal.proposed_capability,
        expected_artifacts=proposal.expected_artifacts,
        governance_risks=proposal.governance_risks,
        required_reviews=proposal.required_reviews,
        ontology_mutation_requested=proposal.ontology_mutation_requested,
        baseline_rewrite_requested=proposal.baseline_rewrite_requested,
        implementation_authorized=proposal.implementation_authorized,
        execution_authorized=proposal.execution_authorized,
        machine_output_allowed=proposal.machine_output_allowed,
        proposal_state=proposal.proposal_state,
        deterministic_proposal_hash=proposal.deterministic_proposal_hash,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Readiness endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/readiness/{proposal_id}", response_model=ReadinessResponse)
def evaluate_readiness(proposal_id: str) -> ReadinessResponse:
    """
    Evaluate readiness for a proposal.

    Classifies proposal as green/yellow/red based on gate rules.
    """
    proposal = get_post_freeze_proposal(proposal_id)
    if not proposal:
        raise HTTPException(
            status_code=404,
            detail=f"Proposal {proposal_id} not found"
        )

    readiness = evaluate_post_freeze_readiness(proposal)

    success, error = register_post_freeze_readiness(readiness)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return ReadinessResponse(
        readiness_id=readiness.readiness_id,
        proposal_id=readiness.proposal_id,
        freeze_compatible=readiness.freeze_compatible,
        freeze_exists=readiness.freeze_exists,
        freeze_status=readiness.freeze_status,
        required_reviews_declared=readiness.required_reviews_declared,
        no_execution_authority=readiness.no_execution_authority,
        no_machine_output_authority=readiness.no_machine_output_authority,
        ontology_mutation_requested=readiness.ontology_mutation_requested,
        baseline_rewrite_requested=readiness.baseline_rewrite_requested,
        gate=readiness.gate,
        blocking_issues=readiness.blocking_issues,
        warnings=readiness.warnings,
        status_message=get_readiness_status_message(readiness),
        implementation_authorized=readiness.implementation_authorized,
        execution_authorized=readiness.execution_authorized,
        machine_output_allowed=readiness.machine_output_allowed,
        deterministic_readiness_hash=readiness.deterministic_readiness_hash,
    )


@router.get("/readiness/latest", response_model=ReadinessResponse)
def get_latest_readiness() -> ReadinessResponse:
    """Get the most recent readiness evaluation."""
    readiness = get_latest_post_freeze_readiness()
    if not readiness:
        raise HTTPException(status_code=404, detail="No readiness evaluations registered")

    return ReadinessResponse(
        readiness_id=readiness.readiness_id,
        proposal_id=readiness.proposal_id,
        freeze_compatible=readiness.freeze_compatible,
        freeze_exists=readiness.freeze_exists,
        freeze_status=readiness.freeze_status,
        required_reviews_declared=readiness.required_reviews_declared,
        no_execution_authority=readiness.no_execution_authority,
        no_machine_output_authority=readiness.no_machine_output_authority,
        ontology_mutation_requested=readiness.ontology_mutation_requested,
        baseline_rewrite_requested=readiness.baseline_rewrite_requested,
        gate=readiness.gate,
        blocking_issues=readiness.blocking_issues,
        warnings=readiness.warnings,
        status_message=get_readiness_status_message(readiness),
        implementation_authorized=readiness.implementation_authorized,
        execution_authorized=readiness.execution_authorized,
        machine_output_allowed=readiness.machine_output_allowed,
        deterministic_readiness_hash=readiness.deterministic_readiness_hash,
    )


@router.get("/readiness", response_model=List[Dict[str, Any]])
def list_readiness() -> List[Dict[str, Any]]:
    """List all readiness evaluations."""
    evals = list_post_freeze_readiness()
    return [get_readiness_summary(r) for r in evals]


@router.get("/readiness/proposal/{proposal_id}", response_model=List[Dict[str, Any]])
def list_readiness_for_proposal_endpoint(proposal_id: str) -> List[Dict[str, Any]]:
    """List readiness evaluations for a specific proposal."""
    evals = list_readiness_for_proposal(proposal_id)
    return [get_readiness_summary(r) for r in evals]


# ─────────────────────────────────────────────────────────────────────────────
# CI and status endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ci", response_model=CISummaryResponse)
def get_ci_summary() -> CISummaryResponse:
    """
    Get CI summary for post-freeze expansion state.

    Returns gate distribution and status (pass/warn/fail).
    """
    summary = build_post_freeze_ci_summary()
    return CISummaryResponse(**summary)


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Get aggregated status summary."""
    status = get_post_freeze_status_summary()
    return StatusResponse(**status)
