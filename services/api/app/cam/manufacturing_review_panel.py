"""
Manufacturing Review Panel

CAM Dev Order 8C: Model for manufacturing review panels.

Provides:
  - ManufacturingReviewPanel model
  - Panel validation
  - Summary helpers

8C invariants:
  - human_review_required: always True
  - auto_approval_allowed: always False

Core principle:
  Review panels are for human comprehension, not machine execution.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class ManufacturingReviewPanel(BaseModel):
    """
    Manufacturing review panel for human comprehension.

    Defines a review context with associated artifacts.

    8C invariants (model-enforced):
      - human_review_required: always True
      - auto_approval_allowed: always False
    """

    panel_id: str = Field(
        default_factory=lambda: f"mrp-{uuid4().hex[:12]}",
        description="Unique panel identifier"
    )

    panel_name: str = Field(
        default="",
        max_length=200,
        description="Panel name"
    )

    context_artifact_ids: List[str] = Field(
        default_factory=list,
        description="Artifact IDs in this panel's context"
    )

    federation_visible: bool = Field(
        default=True,
        description="Whether panel is visible to federation"
    )

    replay_complete: bool = Field(
        default=True,
        description="Whether replay data is complete"
    )

    human_review_required: bool = Field(
        default=True,
        description="Always True — 8C requires human review"
    )

    auto_approval_allowed: bool = Field(
        default=False,
        description="Always False — 8C does not allow auto-approval"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_panel_hash: str = Field(
        default="",
        description="Deterministic hash of panel state"
    )

    @model_validator(mode="after")
    def enforce_8c_invariants(self) -> "ManufacturingReviewPanel":
        """Enforce 8C invariants."""
        if not self.human_review_required:
            raise ValueError(
                "8C invariant violation: human_review_required must be True — "
                "8C requires human review"
            )
        if self.auto_approval_allowed:
            raise ValueError(
                "8C invariant violation: auto_approval_allowed must be False — "
                "8C does not allow auto-approval"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of panel state."""
        hash_input = {
            "panel_name": self.panel_name,
            "context_artifact_ids": sorted(self.context_artifact_ids),
            "federation_visible": self.federation_visible,
            "replay_complete": self.replay_complete,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_manufacturing_review_panel(
    panel_name: str,
    context_artifact_ids: Optional[List[str]] = None,
    federation_visible: bool = True,
    replay_complete: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> ManufacturingReviewPanel:
    """Create a manufacturing review panel."""
    panel = ManufacturingReviewPanel(
        panel_name=panel_name,
        context_artifact_ids=context_artifact_ids or [],
        federation_visible=federation_visible,
        replay_complete=replay_complete,
        metadata=metadata or {},
    )
    panel.deterministic_panel_hash = panel.compute_hash()
    return panel


def validate_manufacturing_review_panel(
    panel: ManufacturingReviewPanel,
) -> tuple[bool, List[str]]:
    """Validate a manufacturing review panel."""
    issues: List[str] = []

    if not panel.human_review_required:
        issues.append("human_review_required must be True")

    if panel.auto_approval_allowed:
        issues.append("auto_approval_allowed must be False")

    return len(issues) == 0, issues


def get_panel_summary(panel: ManufacturingReviewPanel) -> Dict[str, Any]:
    """Get panel summary for API response."""
    return {
        "panel_id": panel.panel_id,
        "panel_name": panel.panel_name,
        "context_artifact_count": len(panel.context_artifact_ids),
        "federation_visible": panel.federation_visible,
        "replay_complete": panel.replay_complete,
        "human_review_required": panel.human_review_required,
        "auto_approval_allowed": panel.auto_approval_allowed,
        "created_at": panel.created_at.isoformat(),
    }
