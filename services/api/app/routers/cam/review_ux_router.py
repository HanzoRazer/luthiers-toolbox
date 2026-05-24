"""
Review UX Router

CAM Dev Order 8C: REST endpoints for review UX contracts.

Provides:
  - POST /api/cam/review-ux/panels — register panel
  - GET /api/cam/review-ux/panels — list panels
  - GET /api/cam/review-ux/panels/{panel_id} — get panel
  - POST /api/cam/review-ux/explanations — register explanation
  - GET /api/cam/review-ux/explanations — list explanations
  - POST /api/cam/review-ux/priorities — register priority
  - GET /api/cam/review-ux/priorities — list priorities
  - GET /api/cam/review-ux/status — get status summary

8C invariants:
  - human_review_required: always True (panels)
  - auto_approval_allowed: always False

Core principle:
  Endpoints expose review UX state for human comprehension.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...cam.manufacturing_review_panel import (
    create_manufacturing_review_panel,
    get_panel_summary,
)
from ...cam.provenance_explanation import (
    create_provenance_explanation,
    get_explanation_summary,
)
from ...cam.review_attention_priority import (
    create_review_attention_priority,
    get_priority_summary,
)
from ...cam.review_ux_registry import (
    register_review_panel,
    get_review_panel,
    list_review_panels,
    get_review_panel_count,
    register_provenance_explanation,
    list_provenance_explanations,
    get_provenance_explanation_count,
    register_review_attention_priority,
    list_review_attention_priorities,
    get_review_attention_priority_count,
    get_review_ux_index_counts,
)


router = APIRouter(prefix="/api/cam/review-ux", tags=["cam", "review-ux"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────────────────────────────────────────

class CreatePanelRequest(BaseModel):
    """Request to create a review panel."""
    panel_name: str = Field(..., max_length=200)
    context_artifact_ids: List[str] = Field(default_factory=list)
    federation_visible: bool = Field(default=True)
    replay_complete: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateExplanationRequest(BaseModel):
    """Request to create a provenance explanation."""
    artifact_id: str = Field(...)
    explanation_text: str = Field(..., min_length=1)
    provenance_chain: List[str] = Field(default_factory=list)
    source_layer: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreatePriorityRequest(BaseModel):
    """Request to create a review attention priority."""
    panel_id: str = Field(...)
    component_scores: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PanelResponse(BaseModel):
    """Response containing panel details."""
    success: bool
    panel_id: str
    message: str
    summary: Dict[str, Any]


class ExplanationResponse(BaseModel):
    """Response containing explanation details."""
    success: bool
    explanation_id: str
    message: str
    summary: Dict[str, Any]


class PriorityResponse(BaseModel):
    """Response containing priority details."""
    success: bool
    priority_id: str
    message: str
    summary: Dict[str, Any]


class ListPanelsResponse(BaseModel):
    """Response containing list of panels."""
    total: int
    panels: List[Dict[str, Any]]


class ListExplanationsResponse(BaseModel):
    """Response containing list of explanations."""
    total: int
    explanations: List[Dict[str, Any]]


class ListPrioritiesResponse(BaseModel):
    """Response containing list of priorities."""
    total: int
    priorities: List[Dict[str, Any]]


class StatusResponse(BaseModel):
    """Response containing status summary."""
    status: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Panel endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/panels", response_model=PanelResponse)
async def create_panel(request: CreatePanelRequest) -> PanelResponse:
    """Create and register a review panel."""
    panel = create_manufacturing_review_panel(
        panel_name=request.panel_name,
        context_artifact_ids=request.context_artifact_ids,
        federation_visible=request.federation_visible,
        replay_complete=request.replay_complete,
        metadata=request.metadata,
    )

    success, error = register_review_panel(panel)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return PanelResponse(
        success=True,
        panel_id=panel.panel_id,
        message="Panel registered successfully",
        summary=get_panel_summary(panel),
    )


@router.get("/panels", response_model=ListPanelsResponse)
async def list_panels() -> ListPanelsResponse:
    """List all registered panels."""
    panels = list_review_panels()
    return ListPanelsResponse(
        total=len(panels),
        panels=[get_panel_summary(p) for p in panels],
    )


@router.get("/panels/{panel_id}", response_model=PanelResponse)
async def get_panel(panel_id: str) -> PanelResponse:
    """Get a panel by ID."""
    panel = get_review_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail=f"Panel {panel_id} not found")

    return PanelResponse(
        success=True,
        panel_id=panel.panel_id,
        message="Panel retrieved",
        summary=get_panel_summary(panel),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Explanation endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/explanations", response_model=ExplanationResponse)
async def create_explanation(request: CreateExplanationRequest) -> ExplanationResponse:
    """Create and register a provenance explanation."""
    explanation = create_provenance_explanation(
        artifact_id=request.artifact_id,
        explanation_text=request.explanation_text,
        provenance_chain=request.provenance_chain,
        source_layer=request.source_layer,
        metadata=request.metadata,
    )

    success, error = register_provenance_explanation(explanation)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return ExplanationResponse(
        success=True,
        explanation_id=explanation.explanation_id,
        message="Explanation registered successfully",
        summary=get_explanation_summary(explanation),
    )


@router.get("/explanations", response_model=ListExplanationsResponse)
async def list_explanations() -> ListExplanationsResponse:
    """List all registered explanations."""
    explanations = list_provenance_explanations()
    return ListExplanationsResponse(
        total=len(explanations),
        explanations=[get_explanation_summary(e) for e in explanations],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Priority endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/priorities", response_model=PriorityResponse)
async def create_priority(request: CreatePriorityRequest) -> PriorityResponse:
    """Create and register a review attention priority."""
    priority = create_review_attention_priority(
        panel_id=request.panel_id,
        component_scores=request.component_scores,
        metadata=request.metadata,
    )

    success, error = register_review_attention_priority(priority)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return PriorityResponse(
        success=True,
        priority_id=priority.priority_id,
        message="Priority registered successfully",
        summary=get_priority_summary(priority),
    )


@router.get("/priorities", response_model=ListPrioritiesResponse)
async def list_priorities() -> ListPrioritiesResponse:
    """List all registered priorities."""
    priorities = list_review_attention_priorities()
    return ListPrioritiesResponse(
        total=len(priorities),
        priorities=[get_priority_summary(p) for p in priorities],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Status endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Get status summary."""
    counts = get_review_ux_index_counts()
    return StatusResponse(
        status={
            "total_panels": counts["panels"],
            "total_explanations": counts["explanations"],
            "total_priorities": counts["priorities"],
        }
    )
