"""
RMOS CAM Intent Router (H7.1.2)

Provides the canonical normalization endpoint for CamIntentV1 payloads.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.rmos.cam import (
    CamIntentIssue,
    CamIntentValidationError,
    CamIntentV1,
    CamUnitsV1,
    normalize_cam_intent_v1,
)


router = APIRouter(
    prefix="/rmos/cam",
    tags=["RMOS", "CAM"],
)


class NormalizeCamIntentRequest(BaseModel):
    intent: CamIntentV1
    normalize_to_units: CamUnitsV1 = CamUnitsV1.MM
    strict: bool = False


class CamIntentIssueResponse(BaseModel):
    """Wire-safe representation of CamIntentIssue."""

    code: str
    message: str
    path: str = ""


class NormalizeCamIntentResponse(BaseModel):
    intent: CamIntentV1
    issues: List[CamIntentIssueResponse] = Field(default_factory=list)
    normalized_at_utc: str


@router.post("/intent/normalize", response_model=NormalizeCamIntentResponse)
async def normalize_intent_endpoint(
    request: NormalizeCamIntentRequest,
    x_request_id: Optional[str] = Header(default=None),
) -> NormalizeCamIntentResponse:
    """
    H7.1.2 - Canonical RMOS CAM normalization endpoint.

    Non-breaking: new endpoint only.

    Accepts: CamIntentV1 + normalize options
    Returns: { intent: normalized CamIntentV1, issues: [...], normalized_at_utc }

    Notes:
      - `issues` are non-fatal unless `strict=True` (then 422).
      - This endpoint is designed for frontend SDK normalization before execution.
    """
    try:
        normalized, issues = normalize_cam_intent_v1(
            request.intent,
            normalize_to_units=request.normalize_to_units,
            strict=request.strict,
        )
    except CamIntentValidationError as e:
        detail = {
            "message": str(e),
            "issues": [{"code": i.code, "message": i.message, "path": i.path} for i in getattr(e, "issues", [])],
        }
        raise HTTPException(status_code=422, detail=detail)
    except Exception as e:
        # Defensive: treat unexpected exceptions as 500 with minimal disclosure
        raise HTTPException(status_code=500, detail={"message": "normalize_failed", "error": str(e)})

    # Ensure timestamp exists (router owns the wire contract stability)
    if not normalized.created_at_utc:
        normalized = normalized.with_created_now()

    # Convert issues to wire-safe format
    wire_issues = [CamIntentIssueResponse(code=i.code, message=i.message, path=i.path) for i in issues]

    return NormalizeCamIntentResponse(
        intent=normalized,
        issues=wire_issues,
        normalized_at_utc=datetime.utcnow().isoformat() + "Z",
    )
