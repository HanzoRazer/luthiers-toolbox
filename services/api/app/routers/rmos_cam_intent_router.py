"""
RMOS CAM Intent Router (H7.1.2)

Provides the canonical normalization endpoint for CamIntentV1 payloads.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Union

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.rmos.cam import (
    CamIntentIssue,
    CamIntentValidationError,
    CamIntentV1,
    CamUnitsV1,
    normalize_cam_intent_v1,
)

logger = logging.getLogger(__name__)

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
    request: Union[NormalizeCamIntentRequest, CamIntentV1],
    strict: Optional[bool] = Query(default=None, description="Override strict mode via query param"),
    x_request_id: Optional[str] = Header(default=None, alias="x-request-id"),
) -> NormalizeCamIntentResponse:
    """
    H7.1.2 - Canonical RMOS CAM normalization endpoint.

    Non-breaking: new endpoint only.

    Accepts: 
      - Wrapped: { intent: CamIntentV1, normalize_to_units?, strict? }
      - Flat: CamIntentV1 directly (with strict as query param)
    Returns: { intent: normalized CamIntentV1, issues: [...], normalized_at_utc }

    Notes:
      - `issues` are non-fatal unless `strict=True` (then 422).
      - This endpoint is designed for frontend SDK normalization before execution.
    """
    # Handle both wrapped and flat request formats
    if isinstance(request, CamIntentV1):
        intent = request
        normalize_to_units = CamUnitsV1.MM
        use_strict = strict if strict is not None else False
    else:
        intent = request.intent
        normalize_to_units = request.normalize_to_units
        # Query param overrides body
        use_strict = strict if strict is not None else request.strict

    try:
        normalized, issues = normalize_cam_intent_v1(
            intent,
            normalize_to_units=normalize_to_units,
            strict=use_strict,
        )
    except CamIntentValidationError as e:
        # H7.2.3.1: Log with request_id for incident correlation
        logger.warning(
            "CAM intent strict validation failed request_id=%s issues=%d message=%s",
            x_request_id or "unknown",
            len(getattr(e, "issues", [])),
            str(e),
        )
        detail = {
            "message": str(e),
            "issues": [{"code": i.code, "message": i.message, "path": i.path} for i in getattr(e, "issues", [])],
        }
        raise HTTPException(status_code=422, detail=detail)
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
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
