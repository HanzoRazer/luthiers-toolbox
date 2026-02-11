"""
Adaptive Pocketing Batch Export Router
======================================

Batch export endpoint for multi-mode G-code generation.

LANE: OPERATION
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints:
- POST /batch_export: Multi-post ZIP bundle with multiple feed modes
"""

import io
import json
import logging
import time
import zipfile
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..adaptive_schemas import (
    AdaptiveFeedOverride,
    BatchExportIn,
)

from .helpers import (
    _load_post_profiles,
    _merge_adaptive_override,
    _apply_adaptive_feed,
    _safe_stem,
    ALLOWED_MODES,
)
from .plan_router import plan

router = APIRouter(tags=["cam-adaptive"])


@router.post("/batch_export")
def batch_export(body: BatchExportIn) -> StreamingResponse:
    """
    Batch export adaptive pocket G-code with multiple feed modes.

    Generates ZIP archive containing NC files for each requested adaptive
    feed mode plus a JSON manifest with run metadata. Allows users to
    compare different feed control strategies (comment/inline_f/mcode)
    without re-running toolpath planning.

    Args:
        body: BatchExportIn with geometry, machining params, and mode filter

    Returns:
        StreamingResponse with ZIP file
        Content-Type: application/zip
        Content-Disposition: attachment; filename="<stem>_multi_mode.zip"

        ZIP contents:
        - <stem>_comment.nc: FEED_HINT comment mode
        - <stem>_inline_f.nc: Inline F override mode
        - <stem>_mcode.nc: M-code wrapper mode (if requested)
        - <stem>_manifest.json: Run metadata

    Raises:
        HTTPException 400: If loops missing, empty, or invalid geometry
        HTTPException 409: If safety/governance blocks export
    """
    # -------------------------------------------------------------------------
    # Bundle 17: Input validation guards (convert 500 → governed 4xx)
    # -------------------------------------------------------------------------

    # Guard: loops must be present
    if not body.loops:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_GEOMETRY",
                "reason": "loops is required and cannot be empty",
            }
        )

    # Guard: each loop must have valid pts
    for i, loop in enumerate(body.loops):
        pts = getattr(loop, "pts", None)
        if not pts or len(pts) < 3:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_GEOMETRY",
                    "reason": f"Loop {i} must have at least 3 points",
                    "loop_index": i,
                }
            )

    # Guard: tool_d must be positive
    if body.tool_d <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_TOOL",
                "reason": "tool_d must be positive",
            }
        )

    # Normalize modes - filter to allowed values
    modes = [m for m in (body.modes or []) if m in ALLOWED_MODES]
    if not modes:
        modes = list(ALLOWED_MODES)

    # Resolve program stem (use job_name if provided, else timestamp)
    post_id = body.post_id or "GRBL"
    stem = _safe_stem(body.job_name)

    def render_with_mode(mode: str) -> str:
        """
        Render G-code with specific adaptive feed mode.

        Args:
            mode: Adaptive feed mode ("comment", "inline_f", or "mcode")

        Returns:
            Complete G-code program as string with headers/footers
        """
        # Clone body and set override mode
        body_copy = body.model_copy(deep=True)

        # Create override if not present
        if body_copy.adaptive_feed_override is None:
            body_copy.adaptive_feed_override = AdaptiveFeedOverride()

        # Set mode
        body_copy.adaptive_feed_override.mode = mode  # type: ignore

        # Generate plan
        plan_out = plan(body_copy)

        # Load post profiles
        post_profiles = _load_post_profiles()
        post = post_profiles.get(body_copy.post_id or "GRBL")

        # Apply override
        post = _merge_adaptive_override(
            post,
            body_copy.adaptive_feed_override.dict() if body_copy.adaptive_feed_override else None
        )

        # Get headers/footers
        hdr = post.get("header", ["G90", "G17"]) if post else ["G90", "G17"]
        ftr = post.get("footer", ["M30"]) if post else ["M30"]

        # Add units command
        units_cmd = "G20" if body_copy.units.lower().startswith("in") else "G21"
        if units_cmd not in hdr:
            hdr = [units_cmd] + hdr

        # Apply adaptive feed translation
        body_lines = _apply_adaptive_feed(
            moves=plan_out["moves"],
            post=post,
            base_units=body_copy.units
        )

        # Add metadata
        meta = f"(POST={body_copy.post_id or 'GRBL'};UNITS={body_copy.units};MODE={mode};DATE={datetime.utcnow().isoformat()}Z)"

        # Assemble program
        program = "\n".join(hdr + [meta] + body_lines + ftr) + "\n"
        return program

    # -------------------------------------------------------------------------
    # Bundle 17: Wrap ZIP generation with exception handling
    # -------------------------------------------------------------------------
    try:
        # Build ZIP with requested modes only
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for m in modes:
                z.writestr(f"{stem}_{m}.nc", render_with_mode(m))

            # Add manifest with modes list and run metadata
            manifest = {
                "modes": modes,
                "post": post_id,
                "units": body.units,
                "tool_d": body.tool_d,
                "stepover": body.stepover,
                "stepdown": body.stepdown,
                "strategy": body.strategy,
                "trochoids": bool(getattr(body, "use_trochoids", False)),
                "jerk_aware": bool(getattr(body, "jerk_aware", False)),
                "job_name": stem,
                "timestamp": int(time.time())
            }
            z.writestr(f"{stem}_manifest.json", json.dumps(manifest, indent=2))

        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{stem}_multi_mode.zip"'}
        )

    except HTTPException:
        # Re-raise HTTP exceptions (already governed)
        raise

    except ValueError as e:
        # Known geometry/value errors → 400
        raise HTTPException(
            status_code=400,
            detail={
                "error": "GEOMETRY_ERROR",
                "reason": str(e),
            }
        )

    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        # Unexpected errors → 500 with logging
        logging.exception(f"batch_export unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "EXPORT_FAILED",
                "reason": "Unexpected error during batch export",
            }
        )
