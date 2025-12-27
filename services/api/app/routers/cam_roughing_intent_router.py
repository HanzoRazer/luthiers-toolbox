# services/api/app/routers/cam_roughing_intent_router.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.governance.metrics_registry import metrics

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

# Existing roughing implementation (legacy JSON payload route)
# We will reuse the same generation logic to avoid drift.
from app.routers.cam_roughing_router import roughing_gcode as _legacy_roughing_handler


router = APIRouter(prefix="/cam", tags=["CAM", "Intent"])


class NormalizeResponse(BaseModel):
    intent: Dict[str, Any]
    issues: List[Dict[str, Any]]


def _issues_summary(issues: List[Dict[str, Any]]) -> Tuple[str, str]:
    # labels must be low-cardinality
    has_issues = "1" if issues else "0"
    severity = "none"
    if issues:
        # if your normalizer emits severity, map it coarsely
        # else just "some"
        severity = "some"
        for it in issues:
            sev = (it.get("severity") or "").lower()
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

    metrics.inc(
        name="cam_roughing_gcode_intent_total",
        help="Total requests to roughing_gcode_intent endpoint",
        labels={"strict": strict_lbl, "has_issues": has_issues, "severity": severity},
    )

    if issues:
        metrics.inc(
            name="cam_intent_issues_total",
            help="Total intent normalization issues emitted",
            labels={"endpoint": "roughing_gcode_intent", "severity": severity},
            amount=len(issues),
        )

    if strict and issues:
        metrics.inc(
            name="cam_roughing_gcode_intent_strict_reject_total",
            help="Strict-mode rejects for roughing_gcode_intent",
            labels={"severity": severity},
        )
        raise HTTPException(
            status_code=422,
            detail={"message": "Strict mode reject: intent normalization produced issues", "issues": issues},
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

    # Reuse legacy handler by calling it directly (same behavior, no duplication)
    # Legacy signature: roughing_gcode(payload: dict) -> Response/Text
    return await _legacy_roughing_handler(design)  # type: ignore[arg-type]
