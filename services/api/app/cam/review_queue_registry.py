"""
Review Queue Registry

CAM Dev Order 8E: Registry for review queue items and decision records.

Provides:
  - In-memory queue item registry
  - In-memory decision record registry
  - Registration helpers
  - Query helpers (by status, by priority)
  - Panel-to-queue item builder
  - Decision recording with status update

8E invariants:
  - No authorization of implementation, execution, or machine output
  - Decisions update status but do not authorize

Core principle:
  Registry tracks review queue state for human review routing.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .review_queue_item import (
    ReviewQueueItem,
    ReviewPriority,
    ReviewStatus,
    validate_review_queue_item,
    get_queue_item_summary,
    create_review_queue_item,
)
from .review_decision_record import (
    ReviewDecisionRecord,
    DecisionType,
    validate_review_decision_record,
    get_decision_record_summary,
    create_review_decision_record,
    get_resulting_status,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory indexes
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_QUEUE_ITEM_INDEX: Dict[str, ReviewQueueItem] = {}
REVIEW_DECISION_RECORD_INDEX: Dict[str, ReviewDecisionRecord] = {}

_REVIEW_QUEUE_ITEM_ORDER: List[str] = []
_REVIEW_DECISION_RECORD_ORDER: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Queue item registration
# ─────────────────────────────────────────────────────────────────────────────

def register_review_queue_item(
    item: ReviewQueueItem,
) -> Tuple[bool, Optional[str]]:
    """
    Register a review queue item.

    Returns (success, error_message).
    """
    is_valid, issues = validate_review_queue_item(item)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    if item.queue_item_id in REVIEW_QUEUE_ITEM_INDEX:
        return False, f"Queue item {item.queue_item_id} already exists"

    item.deterministic_queue_hash = item.compute_hash()

    REVIEW_QUEUE_ITEM_INDEX[item.queue_item_id] = item
    _REVIEW_QUEUE_ITEM_ORDER.append(item.queue_item_id)
    return True, None


def get_review_queue_item(
    queue_item_id: str,
) -> Optional[ReviewQueueItem]:
    """Get a queue item by ID."""
    return REVIEW_QUEUE_ITEM_INDEX.get(queue_item_id)


def get_latest_review_queue_item() -> Optional[ReviewQueueItem]:
    """Get the most recently registered queue item."""
    if not _REVIEW_QUEUE_ITEM_ORDER:
        return None
    latest_id = _REVIEW_QUEUE_ITEM_ORDER[-1]
    return REVIEW_QUEUE_ITEM_INDEX.get(latest_id)


def list_review_queue_items() -> List[ReviewQueueItem]:
    """List all queue items in registration order."""
    return [
        REVIEW_QUEUE_ITEM_INDEX[qid]
        for qid in _REVIEW_QUEUE_ITEM_ORDER
        if qid in REVIEW_QUEUE_ITEM_INDEX
    ]


def list_review_queue_by_status(
    status: ReviewStatus,
) -> List[ReviewQueueItem]:
    """List queue items by status (computed on-demand)."""
    return [
        item for item in list_review_queue_items()
        if item.review_status == status
    ]


def list_review_queue_by_priority(
    priority: ReviewPriority,
) -> List[ReviewQueueItem]:
    """List queue items by priority (computed on-demand)."""
    return [
        item for item in list_review_queue_items()
        if item.review_priority == priority
    ]


def get_review_queue_item_count() -> int:
    """Get total queue item count."""
    return len(REVIEW_QUEUE_ITEM_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# Decision record registration
# ─────────────────────────────────────────────────────────────────────────────

def register_review_decision_record(
    record: ReviewDecisionRecord,
) -> Tuple[bool, Optional[str]]:
    """
    Register a decision record.

    Returns (success, error_message).
    """
    is_valid, issues = validate_review_decision_record(record)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    if record.decision_id in REVIEW_DECISION_RECORD_INDEX:
        return False, f"Decision {record.decision_id} already exists"

    record.deterministic_decision_hash = record.compute_hash()

    REVIEW_DECISION_RECORD_INDEX[record.decision_id] = record
    _REVIEW_DECISION_RECORD_ORDER.append(record.decision_id)
    return True, None


def get_review_decision_record(
    decision_id: str,
) -> Optional[ReviewDecisionRecord]:
    """Get a decision record by ID."""
    return REVIEW_DECISION_RECORD_INDEX.get(decision_id)


def list_review_decision_records() -> List[ReviewDecisionRecord]:
    """List all decision records in registration order."""
    return [
        REVIEW_DECISION_RECORD_INDEX[did]
        for did in _REVIEW_DECISION_RECORD_ORDER
        if did in REVIEW_DECISION_RECORD_INDEX
    ]


def list_decisions_for_queue_item(
    queue_item_id: str,
) -> List[ReviewDecisionRecord]:
    """List all decisions for a specific queue item."""
    return [
        record for record in list_review_decision_records()
        if record.queue_item_id == queue_item_id
    ]


def get_review_decision_record_count() -> int:
    """Get total decision record count."""
    return len(REVIEW_DECISION_RECORD_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# Decision recording with status update
# ─────────────────────────────────────────────────────────────────────────────

def record_review_decision(
    queue_item_id: str,
    decision_type: DecisionType,
    decision_rationale: str = "",
    reviewer_ref: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[ReviewDecisionRecord], bool, Optional[str]]:
    """
    Record a review decision and update queue item status.

    Returns (decision_record, success, error_message).
    """
    item = get_review_queue_item(queue_item_id)
    if not item:
        return None, False, f"Queue item {queue_item_id} not found"

    record = create_review_decision_record(
        queue_item_id=queue_item_id,
        decision_type=decision_type,
        decision_rationale=decision_rationale,
        reviewer_ref=reviewer_ref,
        metadata=metadata,
    )

    success, error = register_review_decision_record(record)
    if not success:
        return None, False, error

    # Update queue item status
    new_status = get_resulting_status(decision_type)
    item.review_status = new_status
    item.deterministic_queue_hash = item.compute_hash()

    return record, True, None


# ─────────────────────────────────────────────────────────────────────────────
# Panel-to-queue item builder
# ─────────────────────────────────────────────────────────────────────────────

def build_review_queue_from_panel(
    panel_id: str,
    assigned_role: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[ReviewQueueItem], bool, Optional[str]]:
    """
    Build and register a queue item from a review panel.

    Uses shallow registry lookup:
      - Looks up panel in 8C registry
      - Uses priority from ReviewAttentionPriority if available
      - Copies blocking_issues and warnings from panel

    Returns (queue_item, success, error_message).
    """
    try:
        from .review_ux_registry import (
            get_review_panel,
            list_review_attention_priorities,
        )
    except ImportError:
        return None, False, "8C registry not available"

    panel = get_review_panel(panel_id)
    if not panel:
        return None, False, f"Panel {panel_id} not found"

    # Find associated priority
    review_priority: ReviewPriority = "medium"
    priority_id: Optional[str] = None

    priorities = list_review_attention_priorities()
    for p in priorities:
        if p.panel_id == panel_id:
            priority_id = p.priority_id
            review_priority = p.priority_level
            break

    # Build queue item
    item = create_review_queue_item(
        review_reason=f"Review required for manufacturing review panel {panel_id}",
        source_layer="review_ux",
        review_priority=review_priority,
        panel_id=panel_id,
        priority_id=priority_id,
        assigned_role=assigned_role,
        blocking_issues=[],  # Panel model doesn't have blocking_issues
        warnings=[],  # Panel model doesn't have warnings
        metadata=metadata,
    )

    success, error = register_review_queue_item(item)
    if not success:
        return None, False, error

    return item, True, None


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def sort_queue_items_by_priority(
    items: List[ReviewQueueItem],
) -> List[ReviewQueueItem]:
    """Sort queue items by priority (critical first, low last)."""
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(items, key=lambda x: priority_order.get(x.review_priority, 4))


def detect_unassigned_critical_reviews() -> List[ReviewQueueItem]:
    """Detect critical/high priority items without assignment."""
    return [
        item for item in list_review_queue_items()
        if item.review_priority in ("critical", "high")
        and item.assigned_role is None
        and item.review_status in ("queued", "in_review", "needs_more_evidence")
    ]


def detect_stale_review_items(
    max_age_days: int = 7,
) -> List[ReviewQueueItem]:
    """
    Detect stale review items.

    Items are stale if:
      - created_at exists and is older than max_age_days
      - status is queued, in_review, or needs_more_evidence

    If timestamps not available, returns empty list.
    """
    stale_items: List[ReviewQueueItem] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

    for item in list_review_queue_items():
        if item.review_status not in ("queued", "in_review", "needs_more_evidence"):
            continue

        if hasattr(item, "created_at") and item.created_at:
            if item.created_at < cutoff:
                stale_items.append(item)

    return stale_items


def get_open_review_items() -> List[ReviewQueueItem]:
    """Get items that are still open (not reviewed/deferred/rejected)."""
    return [
        item for item in list_review_queue_items()
        if item.review_status in ("queued", "in_review", "needs_more_evidence")
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_review_queue_indexes_for_tests() -> None:
    """Clear all indexes for testing."""
    REVIEW_QUEUE_ITEM_INDEX.clear()
    REVIEW_DECISION_RECORD_INDEX.clear()
    _REVIEW_QUEUE_ITEM_ORDER.clear()
    _REVIEW_DECISION_RECORD_ORDER.clear()


def get_review_queue_index_counts() -> Dict[str, int]:
    """Get index counts for debugging."""
    return {
        "queue_items": len(REVIEW_QUEUE_ITEM_INDEX),
        "decision_records": len(REVIEW_DECISION_RECORD_INDEX),
        "queue_item_order": len(_REVIEW_QUEUE_ITEM_ORDER),
        "decision_record_order": len(_REVIEW_DECISION_RECORD_ORDER),
    }
