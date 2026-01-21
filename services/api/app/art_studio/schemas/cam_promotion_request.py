# services/api/app/art_studio/schemas/cam_promotion_request.py
"""
Phase 33.0 — CAM Promotion Request Schema

Represents a downstream-safe CAM request derived from PromotionIntentV1.
Does NOT grant manufacturing authority — this is a handoff artifact only.

Art Studio can REQUEST promotion; CAM/RMOS must ACCEPT and execute.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CamPromotionRequestV1(BaseModel):
    """
    Canonical CAM promotion request artifact.
    
    This is the handoff object from Art Studio to downstream CAM consumers.
    It does NOT:
      - execute toolpaths
      - generate G-code
      - create manufacturing runs
    
    It only expresses: "Art Studio requests CAM processing for this approved intent."
    """
    
    promotion_request_version: Literal["v1"] = "v1"
    
    # Identity
    promotion_request_id: str = Field(..., description="UUID for this request")
    created_at: datetime
    
    # Source tracking
    source: Literal["art_studio"] = "art_studio"
    session_id: str
    
    # Fingerprints for cache/dedup (matches PromotionIntentV1)
    design_fingerprint: str
    feasibility_fingerprint: str
    
    # Optional CAM hints (passed through from intent)
    requested_cam_profile_id: Optional[str] = None
    
    # Status: QUEUED means ready for downstream pickup
    status: Literal["QUEUED", "BLOCKED"] = "QUEUED"
    
    # If blocked, why
    blocked_reason: Optional[str] = None


class CamPromotionResponse(BaseModel):
    """
    Response wrapper for POST /promote_to_cam endpoint.
    
    Ergonomic shape for UI consumption:
      - ok=True + request: Promotion succeeded
      - ok=False + blocked_reason: Promotion blocked (not approved, etc.)
    """
    ok: bool
    request: Optional[CamPromotionRequestV1] = None
    blocked_reason: Optional[str] = None
