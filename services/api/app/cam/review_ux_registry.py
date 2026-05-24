"""
Review UX Registry

CAM Dev Order 8C: Registry for review UX artifacts.

Provides:
  - In-memory panel registry
  - In-memory explanation registry
  - In-memory priority registry
  - Registration helpers
  - Query helpers

Core principle:
  Registry tracks review UX artifacts for human comprehension.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .manufacturing_review_panel import (
    ManufacturingReviewPanel,
    validate_manufacturing_review_panel,
    get_panel_summary,
)
from .provenance_explanation import (
    ProvenanceExplanationArtifact,
    validate_provenance_explanation,
    get_explanation_summary,
)
from .review_attention_priority import (
    ReviewAttentionPriority,
    validate_review_attention_priority,
    get_priority_summary,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory indexes
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_PANEL_INDEX: Dict[str, ManufacturingReviewPanel] = {}
PROVENANCE_EXPLANATION_INDEX: Dict[str, ProvenanceExplanationArtifact] = {}
REVIEW_PRIORITY_INDEX: Dict[str, ReviewAttentionPriority] = {}

_REVIEW_PANEL_ORDER: List[str] = []
_PROVENANCE_EXPLANATION_ORDER: List[str] = []
_REVIEW_PRIORITY_ORDER: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Panel registration
# ─────────────────────────────────────────────────────────────────────────────

def register_review_panel(
    panel: ManufacturingReviewPanel,
) -> Tuple[bool, Optional[str]]:
    """
    Register a review panel.

    Returns (success, error_message).
    """
    is_valid, issues = validate_manufacturing_review_panel(panel)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    if panel.panel_id in REVIEW_PANEL_INDEX:
        return False, f"Panel {panel.panel_id} already exists"

    panel.deterministic_panel_hash = panel.compute_hash()

    REVIEW_PANEL_INDEX[panel.panel_id] = panel
    _REVIEW_PANEL_ORDER.append(panel.panel_id)
    return True, None


def get_review_panel(panel_id: str) -> Optional[ManufacturingReviewPanel]:
    """Get a panel by ID."""
    return REVIEW_PANEL_INDEX.get(panel_id)


def list_review_panels() -> List[ManufacturingReviewPanel]:
    """List all panels in registration order."""
    return [
        REVIEW_PANEL_INDEX[pid]
        for pid in _REVIEW_PANEL_ORDER
        if pid in REVIEW_PANEL_INDEX
    ]


def get_review_panel_count() -> int:
    """Get total panel count."""
    return len(REVIEW_PANEL_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# Explanation registration
# ─────────────────────────────────────────────────────────────────────────────

def register_provenance_explanation(
    explanation: ProvenanceExplanationArtifact,
) -> Tuple[bool, Optional[str]]:
    """
    Register a provenance explanation.

    Returns (success, error_message).
    """
    is_valid, issues = validate_provenance_explanation(explanation)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    if explanation.explanation_id in PROVENANCE_EXPLANATION_INDEX:
        return False, f"Explanation {explanation.explanation_id} already exists"

    explanation.deterministic_explanation_hash = explanation.compute_hash()

    PROVENANCE_EXPLANATION_INDEX[explanation.explanation_id] = explanation
    _PROVENANCE_EXPLANATION_ORDER.append(explanation.explanation_id)
    return True, None


def get_provenance_explanation(explanation_id: str) -> Optional[ProvenanceExplanationArtifact]:
    """Get an explanation by ID."""
    return PROVENANCE_EXPLANATION_INDEX.get(explanation_id)


def list_provenance_explanations() -> List[ProvenanceExplanationArtifact]:
    """List all explanations in registration order."""
    return [
        PROVENANCE_EXPLANATION_INDEX[eid]
        for eid in _PROVENANCE_EXPLANATION_ORDER
        if eid in PROVENANCE_EXPLANATION_INDEX
    ]


def get_provenance_explanation_count() -> int:
    """Get total explanation count."""
    return len(PROVENANCE_EXPLANATION_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# Priority registration
# ─────────────────────────────────────────────────────────────────────────────

def register_review_attention_priority(
    priority: ReviewAttentionPriority,
) -> Tuple[bool, Optional[str]]:
    """
    Register a review attention priority.

    Returns (success, error_message).
    """
    is_valid, issues = validate_review_attention_priority(priority)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    if priority.priority_id in REVIEW_PRIORITY_INDEX:
        return False, f"Priority {priority.priority_id} already exists"

    priority.deterministic_priority_hash = priority.compute_hash()

    REVIEW_PRIORITY_INDEX[priority.priority_id] = priority
    _REVIEW_PRIORITY_ORDER.append(priority.priority_id)
    return True, None


def get_review_attention_priority(priority_id: str) -> Optional[ReviewAttentionPriority]:
    """Get a priority by ID."""
    return REVIEW_PRIORITY_INDEX.get(priority_id)


def list_review_attention_priorities() -> List[ReviewAttentionPriority]:
    """List all priorities in registration order."""
    return [
        REVIEW_PRIORITY_INDEX[pid]
        for pid in _REVIEW_PRIORITY_ORDER
        if pid in REVIEW_PRIORITY_INDEX
    ]


def get_review_attention_priority_count() -> int:
    """Get total priority count."""
    return len(REVIEW_PRIORITY_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# Detection helpers (for 8D counting)
# ─────────────────────────────────────────────────────────────────────────────

def detect_missing_provenance(
    panels: List[ManufacturingReviewPanel],
    explanations: List[ProvenanceExplanationArtifact],
) -> List[str]:
    """
    Detect artifact IDs missing provenance explanations.

    Returns list of artifact IDs without explanations.
    """
    explained_ids = {e.artifact_id for e in explanations}
    missing = []
    for panel in panels:
        for artifact_id in panel.context_artifact_ids:
            if artifact_id not in explained_ids:
                missing.append(artifact_id)
    return missing


def detect_federation_visibility_gaps(
    panels: List[ManufacturingReviewPanel],
) -> List[str]:
    """
    Detect panels with federation visibility gaps.

    Returns list of panel IDs with federation_visible=False.
    """
    return [p.panel_id for p in panels if not p.federation_visible]


def detect_fragmented_replay(
    panels: List[ManufacturingReviewPanel],
) -> List[str]:
    """
    Detect panels with fragmented replay.

    Returns list of panel IDs with replay_complete=False.
    """
    return [p.panel_id for p in panels if not p.replay_complete]


def detect_review_overload(
    priorities: List[ReviewAttentionPriority],
    threshold: float = 0.85,
) -> List[str]:
    """
    Detect panels with review overload.

    Returns list of panel IDs with aggregate_attention_score >= threshold.
    """
    return [
        p.panel_id for p in priorities
        if p.aggregate_attention_score >= threshold
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_review_ux_indexes_for_tests() -> None:
    """Clear all indexes for testing."""
    REVIEW_PANEL_INDEX.clear()
    PROVENANCE_EXPLANATION_INDEX.clear()
    REVIEW_PRIORITY_INDEX.clear()
    _REVIEW_PANEL_ORDER.clear()
    _PROVENANCE_EXPLANATION_ORDER.clear()
    _REVIEW_PRIORITY_ORDER.clear()


def get_review_ux_index_counts() -> Dict[str, int]:
    """Get index counts for debugging."""
    return {
        "panels": len(REVIEW_PANEL_INDEX),
        "explanations": len(PROVENANCE_EXPLANATION_INDEX),
        "priorities": len(REVIEW_PRIORITY_INDEX),
    }
