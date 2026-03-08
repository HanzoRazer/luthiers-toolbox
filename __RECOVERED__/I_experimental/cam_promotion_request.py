from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .promotion_intent import PromotionIntentV1


class CamPromotionRequestV1(BaseModel):
    """
    Orchestration-only handoff object. NOT toolpaths, NOT G-code, NOT execution authority.
    """

    promotion_request_version: Literal["v1"] = "v1"
    promotion_request_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    source: Literal["art_studio"] = "art_studio"
    session_id: str

    # Embed canonical intent for traceability (downstream can also rely on fingerprints)
    intent: PromotionIntentV1

    design_fingerprint: str
    feasibility_fingerprint: str

    requested_cam_profile_id: Optional[str] = None

    status: Literal["QUEUED", "BLOCKED"] = "QUEUED"


class CamPromotionResponse(BaseModel):
    ok: bool
    request: Optional[CamPromotionRequestV1] = None
    blocked_reason: Optional[str] = None
