# services/api/app/art_studio/schemas/workflow_design_first.py
"""
Design-First Workflow Schemas (Bundle 32.7.0)

This is a lightweight workflow binding for Art Studio that:
- Enables Design → Review → Approve → "CAM handoff intent" bridge
- Does NOT execute CAM, toolpaths, or create run authority
- Produces a PromotionIntent payload that CAM/RMOS lanes may consume

Separate from the full workflow_integration.py which handles RMOS state machine.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Conditional import for RosetteParamSpec
try:
    from app.art_studio.schemas.rosette_params import RosetteParamSpec
except ImportError:
    from art_studio.schemas.rosette_params import RosetteParamSpec


class DesignFirstMode(str, Enum):
    DESIGN_FIRST = "design_first"


class DesignFirstState(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class DesignFirstEvent(BaseModel):
    ts: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "user"
    action: str
    from_state: DesignFirstState
    to_state: DesignFirstState
    note: Optional[str] = None


class DesignFirstSession(BaseModel):
    """Lightweight workflow session for design-first mode."""
    session_id: str
    mode: DesignFirstMode = DesignFirstMode.DESIGN_FIRST

    state: DesignFirstState = DesignFirstState.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # "current design" tracked by workflow lane (ornament intent only)
    design: RosetteParamSpec

    # last known feasibility summary (opaque payload from RMOS/art feasibility)
    feasibility: Optional[Dict[str, Any]] = None

    history: List[DesignFirstEvent] = Field(default_factory=list)


# Request/Response models

class StartDesignFirstRequest(BaseModel):
    mode: DesignFirstMode = DesignFirstMode.DESIGN_FIRST
    design: RosetteParamSpec
    feasibility: Optional[Dict[str, Any]] = None


class StartDesignFirstResponse(BaseModel):
    session: DesignFirstSession


class GetDesignFirstResponse(BaseModel):
    session: DesignFirstSession


class TransitionDesignFirstRequest(BaseModel):
    to_state: DesignFirstState
    note: Optional[str] = None
    actor: str = "user"

    # Optionally update the design/feasibility at transition time
    design: Optional[RosetteParamSpec] = None
    feasibility: Optional[Dict[str, Any]] = None


class TransitionDesignFirstResponse(BaseModel):
    session: DesignFirstSession


class PromotionIntent(BaseModel):
    """
    IMPORTANT: This is NOT execution.
    This is an intent payload that CAM/RMOS lanes may consume.
    """
    session_id: str
    mode: DesignFirstMode
    approved_at: datetime
    design: RosetteParamSpec
    feasibility: Optional[Dict[str, Any]] = None

    # This field is intentionally descriptive only (no authority creation).
    recommended_next_step: str = "hand_off_to_cam_lane"


class PromotionIntentResponse(BaseModel):
    ok: bool
    intent: Optional[PromotionIntent] = None
    blocked_reason: Optional[str] = None
