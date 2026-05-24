"""
Review Queue Router

CAM Dev Order 8E: REST endpoints for governed review queue routing.

Provides:
  - POST /api/cam/review-queue/items — create queue item
  - GET /api/cam/review-queue/items — list queue items
  - GET /api/cam/review-queue/items/{queue_item_id} — get queue item
  - POST /api/cam/review-queue/items/from-panel/{panel_id} — create from panel
  - POST /api/cam/review-queue/decisions — record decision
  - GET /api/cam/review-queue/items/{queue_item_id}/decisions — get decisions
  - GET /api/cam/review-queue/by-status/{status} — list by status
  - GET /api/cam/review-queue/by-priority/{priority} — list by priority
  - GET /api/cam/review-queue/ci — get CI summary

8E invariants:
  - No authorization of implementation, execution, or machine output
  - Decisions update status but do not authorize

Core principle:
  Endpoints expose review queue state for human review routing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...cam.review_queue_item import (
    ReviewQueueItem,
    ReviewPriority,
    ReviewStatus,
    ReviewSourceLayer,
    create_review_queue_item,
    get_queue_item_summary,
)
from ...cam.review_decision_record import (
    ReviewDecisionRecord,
    DecisionType,
    create_review_decision_record,
    get_decision_record_summary,
)
from ...cam.review_queue_registry import (
    register_review_queue_item,
    get_review_queue_item,
    list_review_queue_items,
    list_review_queue_by_status,
    list_review_queue_by_priority,
    get_review_queue_item_count,
    record_review_decision,
    list_decisions_for_queue_item,
    build_review_queue_from_panel,
    sort_queue_items_by_priority,
    get_review_decision_record_count,
    list_review_decision_records,
)
from ...cam.review_queue_ci import (
    evaluate_review_queue_ci,
    get_ci_summary_dict,
)


router = APIRouter(prefix="/api/cam/review-queue", tags=["cam", "review-queue"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────────────────────────────────────────

class CreateQueueItemRequest(BaseModel):
    """Request to create a queue item."""
    review_reason: str = Field(..., min_length=1)
    source_layer: ReviewSourceLayer = Field(default="review_ux")
    review_priority: ReviewPriority = Field(default="medium")
    panel_id: Optional[str] = Field(default=None)
    priority_id: Optional[str] = Field(default=None)
    provenance_explanation_id: Optional[str] = Field(default=None)
    assigned_role: Optional[str] = Field(default=None)
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateFromPanelRequest(BaseModel):
    """Request to create queue item from panel."""
    assigned_role: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecordDecisionRequest(BaseModel):
    """Request to record a decision."""
    queue_item_id: str = Field(...)
    decision_type: DecisionType = Field(...)
    decision_rationale: str = Field(default="")
    reviewer_ref: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueueItemResponse(BaseModel):
    """Response containing queue item details."""
    success: bool
    queue_item_id: str
    message: str
    summary: Dict[str, Any]


class DecisionResponse(BaseModel):
    """Response containing decision details."""
    success: bool
    decision_id: str
    message: str
    summary: Dict[str, Any]


class ListQueueItemsResponse(BaseModel):
    """Response containing list of queue items."""
    total: int
    items: List[Dict[str, Any]]


class ListDecisionsResponse(BaseModel):
    """Response containing list of decisions."""
    total: int
    decisions: List[Dict[str, Any]]


class CISummaryResponse(BaseModel):
    """Response containing CI summary."""
    summary: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Queue item endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/items", response_model=QueueItemResponse)
async def create_queue_item(request: CreateQueueItemRequest) -> QueueItemResponse:
    """Create and register a review queue item."""
    item = create_review_queue_item(
        review_reason=request.review_reason,
        source_layer=request.source_layer,
        review_priority=request.review_priority,
        panel_id=request.panel_id,
        priority_id=request.priority_id,
        provenance_explanation_id=request.provenance_explanation_id,
        assigned_role=request.assigned_role,
        blocking_issues=request.blocking_issues,
        warnings=request.warnings,
        metadata=request.metadata,
    )

    success, error = register_review_queue_item(item)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return QueueItemResponse(
        success=True,
        queue_item_id=item.queue_item_id,
        message="Queue item registered successfully",
        summary=get_queue_item_summary(item),
    )


@router.get("/items", response_model=ListQueueItemsResponse)
async def list_items() -> ListQueueItemsResponse:
    """List all queue items."""
    items = list_review_queue_items()
    sorted_items = sort_queue_items_by_priority(items)
    return ListQueueItemsResponse(
        total=len(sorted_items),
        items=[get_queue_item_summary(item) for item in sorted_items],
    )


@router.get("/items/{queue_item_id}", response_model=QueueItemResponse)
async def get_item(queue_item_id: str) -> QueueItemResponse:
    """Get a queue item by ID."""
    item = get_review_queue_item(queue_item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_item_id} not found")

    return QueueItemResponse(
        success=True,
        queue_item_id=item.queue_item_id,
        message="Queue item retrieved",
        summary=get_queue_item_summary(item),
    )


@router.post("/items/from-panel/{panel_id}", response_model=QueueItemResponse)
async def create_from_panel(
    panel_id: str,
    request: CreateFromPanelRequest,
) -> QueueItemResponse:
    """Create a queue item from a review panel."""
    item, success, error = build_review_queue_from_panel(
        panel_id=panel_id,
        assigned_role=request.assigned_role,
        metadata=request.metadata,
    )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return QueueItemResponse(
        success=True,
        queue_item_id=item.queue_item_id,
        message=f"Queue item created from panel {panel_id}",
        summary=get_queue_item_summary(item),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Decision endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/decisions", response_model=DecisionResponse)
async def create_decision(request: RecordDecisionRequest) -> DecisionResponse:
    """Record a review decision."""
    record, success, error = record_review_decision(
        queue_item_id=request.queue_item_id,
        decision_type=request.decision_type,
        decision_rationale=request.decision_rationale,
        reviewer_ref=request.reviewer_ref,
        metadata=request.metadata,
    )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return DecisionResponse(
        success=True,
        decision_id=record.decision_id,
        message=f"Decision recorded: {request.decision_type}",
        summary=get_decision_record_summary(record),
    )


@router.get("/items/{queue_item_id}/decisions", response_model=ListDecisionsResponse)
async def get_item_decisions(queue_item_id: str) -> ListDecisionsResponse:
    """Get all decisions for a queue item."""
    item = get_review_queue_item(queue_item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_item_id} not found")

    decisions = list_decisions_for_queue_item(queue_item_id)
    return ListDecisionsResponse(
        total=len(decisions),
        decisions=[get_decision_record_summary(d) for d in decisions],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Filter endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/by-status/{status}", response_model=ListQueueItemsResponse)
async def get_by_status(status: ReviewStatus) -> ListQueueItemsResponse:
    """List queue items by status."""
    items = list_review_queue_by_status(status)
    sorted_items = sort_queue_items_by_priority(items)
    return ListQueueItemsResponse(
        total=len(sorted_items),
        items=[get_queue_item_summary(item) for item in sorted_items],
    )


@router.get("/by-priority/{priority}", response_model=ListQueueItemsResponse)
async def get_by_priority(priority: ReviewPriority) -> ListQueueItemsResponse:
    """List queue items by priority."""
    items = list_review_queue_by_priority(priority)
    return ListQueueItemsResponse(
        total=len(items),
        items=[get_queue_item_summary(item) for item in items],
    )


# ─────────────────────────────────────────────────────────────────────────────
# CI endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ci", response_model=CISummaryResponse)
async def get_ci_summary() -> CISummaryResponse:
    """Get review queue CI summary."""
    items = list_review_queue_items()
    decisions = list_review_decision_records()
    summary = evaluate_review_queue_ci(items, decisions)
    return CISummaryResponse(summary=get_ci_summary_dict(summary))
