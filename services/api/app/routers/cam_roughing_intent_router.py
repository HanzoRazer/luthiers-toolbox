# services/api/app/routers/cam_roughing_intent_router.py
"""
CAM Roughing Intent Router (H7.2)

Intent-native endpoint that accepts CamIntentV1, normalizes it,
and returns structured JSON with G-code and normalization issues.

Response format:
{
    "gcode": "G90\nG0 Z5.000\n...",
    "issues": [{"code": "...", "message": "...", "path": "..."}],
    "status": "OK" | "OK_WITH_ISSUES"
}
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.observability.metrics import (
    cam_roughing_gcode_intent_total,
    cam_roughing_gcode_intent_strict_reject_total,
)

# Canonical intent envelope (H7.1): app.rmos.cam.CamIntentV1
from app.rmos.cam import CamIntentV1, CamIntentIssue, normalize_cam_intent_v1

# Existing roughing implementation (consolidated CAM router)
# We will reuse the same generation logic to avoid drift.
from app.cam.routers.toolpath.roughing_router import roughing_gcode as _legacy_roughing_handler, RoughReq


router = APIRouter(prefix="/cam", tags=["CAM", "Intent"])


class IssueOut(BaseModel):
    """Normalization issue output."""
    code: str
    message: str
    path: str = ""


class RoughingIntentResponse(BaseModel):
    """Response from roughing intent endpoint."""
    gcode: str
    issues: List[IssueOut]
    status: Literal["OK", "OK_WITH_ISSUES"]


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


@router.post("/roughing/gcode_intent", response_model=RoughingIntentResponse)
async def roughing_gcode_intent(
    request: Request,
    intent: CamIntentV1,
    strict: bool = False,
) -> RoughingIntentResponse:
    """
    Intent-native roughing endpoint.

    - Accepts CamIntentV1
    - Normalizes via normalize_cam_intent_v1
    - Reuses legacy roughing generator to keep output identical
    - Returns structured JSON with G-code and normalization issues
    - Emits metrics for adoption tracking

    Query:
      strict=true -> reject (422) if normalizer emits issues

    Response:
      {
        "gcode": "G90\\nG0 Z5.000\\n...",
        "issues": [{"code": "...", "message": "...", "path": "..."}],
        "status": "OK" | "OK_WITH_ISSUES"
      }
    """
    # Normalize
    normalized_intent, issues = normalize_cam_intent_v1(intent)

    has_issues, severity = _issues_summary(issues)
    strict_lbl = "1" if strict else "0"

    cam_roughing_gcode_intent_total.inc(
        labels={"strict": strict_lbl, "has_issues": has_issues, "severity": severity},
    )

    # Convert issues to output format
    issues_out = [
        IssueOut(code=i.code, message=i.message, path=i.path)
        for i in issues
    ]

    if strict and issues:
        cam_roughing_gcode_intent_strict_reject_total.inc(
            labels={"severity": severity},
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "CAM_INTENT_NORMALIZATION_ISSUES",
                "issues": [i.model_dump() for i in issues_out],
            },
        )

    # Convert normalized intent -> legacy payload shape
    # Convention: keep envelope stable, mode-specific fields inside `design`.
    if isinstance(normalized_intent, dict):
        design = normalized_intent.get("design")
        context = normalized_intent.get("context", {})
        units = normalized_intent.get("units", "mm")
    else:
        design = getattr(normalized_intent, "design", None)
        context = getattr(normalized_intent, "context", {}) or {}
        units = str(getattr(normalized_intent, "units", "mm"))

    if not isinstance(design, dict):
        raise HTTPException(status_code=400, detail="CamIntentV1.design must be an object for roughing")

    # Map intent field names to RoughReq field names
    # Intent uses: width_mm, height_mm, depth_mm, stepdown_mm, stepover_mm
    # RoughReq expects: width, height, stepdown, stepover, feed
    legacy_design = {
        "width": design.get("width_mm") or design.get("width"),
        "height": design.get("height_mm") or design.get("height"),
        "stepdown": design.get("stepdown_mm") or design.get("stepdown"),
        "stepover": design.get("stepover_mm") or design.get("stepover"),
        "feed": context.get("feed_rate") or design.get("feed") or 1000.0,
        "units": units,
    }
    # Pass through optional fields if present
    for opt_field in ["safe_z", "post", "post_mode", "machine_id", "rpm", "program_no"]:
        if opt_field in design:
            legacy_design[opt_field] = design[opt_field]

    # Reuse consolidated handler by calling it directly (same behavior, no duplication)
    # Consolidated signature: roughing_gcode(req: RoughReq) -> Response
    try:
        rough_req = RoughReq(**legacy_design)
        response = _legacy_roughing_handler(rough_req)

        # Extract G-code from response body
        gcode = response.body.decode("utf-8") if hasattr(response, "body") else str(response)

        return RoughingIntentResponse(
            gcode=gcode,
            issues=issues_out,
            status="OK_WITH_ISSUES" if issues else "OK",
        )
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., safety blocks)
        raise
    except Exception as e:
        # If handler fails, return a structured error but metrics still counted
        raise HTTPException(
            status_code=422,
            detail={"error": "ROUGHING_GENERATION_FAILED", "message": str(e), "issues": []},
        )
