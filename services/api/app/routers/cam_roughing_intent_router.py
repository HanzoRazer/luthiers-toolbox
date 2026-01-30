# services/api/app/routers/cam_roughing_intent_router.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.observability.metrics import (
    cam_roughing_gcode_intent_total,
    cam_roughing_gcode_intent_strict_reject_total,
)

# TODO: Update these imports once CamIntentV1 and normalize_cam_intent_v1 are available
# Canonical intent envelope (H7.1): app.rmos.cam.CamIntentV1
# Possible locations:
#   from app.rmos.cam import CamIntentV1, normalize_cam_intent_v1
#   from app.rmos.cam.intent import CamIntentV1, normalize_cam_intent_v1
try:
    from app.rmos.cam import CamIntentV1, normalize_cam_intent_v1
except ImportError:
    try:
        from app.rmos.cam.intent import CamIntentV1, normalize_cam_intent_v1  # type: ignore
    except ImportError:
        # Stub until intent schema is available
        CamIntentV1 = Dict[str, Any]  # type: ignore
        def normalize_cam_intent_v1(intent):  # type: ignore
            return intent, []

# Existing roughing implementation (consolidated CAM router)
# We will reuse the same generation logic to avoid drift.
from app.cam.routers.toolpath.roughing_router import roughing_gcode as _legacy_roughing_handler, RoughReq


router = APIRouter(prefix="/cam", tags=["CAM", "Intent"])


class NormalizeResponse(BaseModel):
    intent: Dict[str, Any]
    issues: List[Dict[str, Any]]


def _issues_summary(issues: List[Any]) -> Tuple[str, str]:
    # labels must be low-cardinality
    has_issues = "1" if issues else "0"
    severity = "none"
    if issues:
        # if your normalizer emits severity, map it coarsely
        # else just "some"
        severity = "some"
        for it in issues:
            # Handle both dict-style and object-style issues
            if isinstance(it, dict):
                sev = (it.get("severity") or "").lower()
            else:
                sev = (getattr(it, "severity", None) or "").lower()
            if sev in ("error", "fatal"):
                severity = "error"
                break
            if sev in ("warn", "warning") and severity != "error":
                severity = "warn"
    return has_issues, severity


@router.post("/roughing_gcode_intent")
async def roughing_gcode_intent(
    request: Request,
    intent: CamIntentV1,
    strict: bool = False,
):
    """
    Intent-native roughing endpoint.

    - Accepts CamIntentV1
    - Normalizes via normalize_cam_intent_v1
    - Reuses legacy roughing generator to keep output identical
    - Emits metrics for adoption tracking

    Query:
      strict=true -> reject if normalizer emits issues
    """
    # Normalize
    normalized_intent, issues = normalize_cam_intent_v1(intent)

    has_issues, severity = _issues_summary(issues)
    strict_lbl = "1" if strict else "0"

    cam_roughing_gcode_intent_total.inc(
        labels={"strict": strict_lbl, "has_issues": has_issues, "severity": severity},
    )

    if strict and issues:
        cam_roughing_gcode_intent_strict_reject_total.inc(
            labels={"severity": severity},
        )
        # Convert issues to dicts for JSON serialization
        issues_dicts = []
        for i in issues:
            if isinstance(i, dict):
                issues_dicts.append(i)
            elif hasattr(i, "model_dump"):
                issues_dicts.append(i.model_dump())
            elif hasattr(i, "dict"):
                issues_dicts.append(i.dict())
            else:
                issues_dicts.append({"message": str(i)})
        raise HTTPException(
            status_code=422,
            detail={"message": "Strict mode reject: intent normalization produced issues", "issues": issues_dicts},
        )

    # Convert normalized intent -> legacy payload shape
    # Convention: keep envelope stable, mode-specific fields inside `design`.
    # Legacy roughing endpoint expects a JSON dict payload.
    design = getattr(normalized_intent, "design", None)
    if design is None:
        # could be dict style intent, depends on your model; handle both safely:
        design = normalized_intent.get("design") if isinstance(normalized_intent, dict) else None

    if not isinstance(design, dict):
        raise HTTPException(status_code=400, detail="CamIntentV1.design must be an object for roughing")

    # Reuse consolidated handler by calling it directly (same behavior, no duplication)
    # Consolidated signature: roughing_gcode(req: RoughReq) -> Response
    try:
        rough_req = RoughReq(**design)
        return _legacy_roughing_handler(rough_req)
    except Exception as e:
        # If handler fails, return a structured error but metrics still counted
        raise HTTPException(
            status_code=422,
            detail={"message": f"Roughing generation failed: {e}", "issues": []},
        )
