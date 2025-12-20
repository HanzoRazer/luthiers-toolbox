# services/api/app/routers/rmos_saw_ops_router.py
"""
RMOS Saw Operations Router

Note: Circle/arc geometry extracted to geometry/arc_utils.py
following the Fortran Rule (all math in subroutines).
"""

from __future__ import annotations

import math
import uuid
from typing import Dict, Any, List

from fastapi import APIRouter

# Import canonical geometry functions - NO inline math in routers (Fortran Rule)
from ..geometry.arc_utils import circle_circumference, arc_length_from_angle

from ..rmos.models.pattern import (
    SlicePreviewRequest,
    SlicePreviewResponse,
    PipelineHandoffRequest,
    PipelineHandoffResponse,
)

router = APIRouter(
    prefix="/saw-ops",
    tags=["RMOS", "Saw Operations"],
)


def _estimate_path_length_mm(geometry: Dict[str, Any]) -> float:
    """
    Very simple path-length estimate based on geometry descriptor.

    Delegates to canonical geometry functions from geometry/arc_utils.py.

    This is intentionally conservative and stubby for Wave E1.
    Saw Lab can override this later with real slice planning.
    """
    gtype = (geometry.get("type") or "").lower()

    if gtype == "circle":
        r = float(geometry.get("radius_mm", 0.0))
        return circle_circumference(r)

    if gtype == "arc":
        r = float(geometry.get("radius_mm", 0.0))
        angle_deg = float(geometry.get("angle_deg", 0.0))
        return arc_length_from_angle(r, angle_deg)

    if gtype == "polyline":
        pts = geometry.get("points") or []
        total = 0.0
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            dx = float(x2) - float(x1)
            dy = float(y2) - float(y1)
            total += math.hypot(dx, dy)  # hypot is stdlib, not algorithm
        return total

    # Fallback: unknown type, assume short path
    return float(geometry.get("approx_length_mm", 10.0))


@router.post("/slice/preview", response_model=SlicePreviewResponse)
async def preview_slice(request: SlicePreviewRequest) -> SlicePreviewResponse:
    """
    Generate a lightweight preview for a single saw slice operation.

    For Wave E1 this is a stub that:
    - Estimates path length from the geometry
    - Computes a rough time estimate from feed rate
    - Returns a minimal toolpath & inline SVG stub
    """
    feed = float(request.feed_rate_mm_min or 800.0)
    path_length = _estimate_path_length_mm(request.geometry)
    # Convert feed mm/min → mm/sec
    feed_mm_sec = feed / 60.0 if feed > 0 else 1.0
    time_sec = path_length / feed_mm_sec if feed_mm_sec > 0 else 0.0

    toolpath: List[Dict[str, Any]] = [
        {
            "x": 0.0,
            "y": 0.0,
            "z": -float(request.cut_depth_mm),
            "feed_mm_min": feed,
            "comment": "Stub preview move – replace with real Saw Lab path planning.",
        }
    ]

    warnings: List[str] = []
    if request.feed_rate_mm_min is None:
        warnings.append("feed_rate_mm_min not provided; used default 800 mm/min.")
    if path_length <= 0:
        warnings.append("Could not estimate path length from geometry; statistics may be inaccurate.")

    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        "<rect x='10' y='10' width='80' height='20' "
        "fill='none' stroke='black' stroke-width='1'/>"
        "<text x='50' y='50' dominant-baseline='middle' text-anchor='middle' font-size='8'>"
        "Saw preview (stub)"
        "</text>"
        "</svg>"
    )

    stats: Dict[str, Any] = {
        "estimated_time_sec": time_sec,
        "path_length_mm": path_length,
        "feed_rate_mm_min": feed,
        "cut_depth_mm": request.cut_depth_mm,
    }

    return SlicePreviewResponse(
        toolpath=toolpath,
        statistics=stats,
        warnings=warnings,
        visualization_svg=svg,
    )


@router.post("/pipeline/handoff", response_model=PipelineHandoffResponse)
async def pipeline_handoff(request: PipelineHandoffRequest) -> PipelineHandoffResponse:
    """
    Handoff a rosette pattern to the RMOS → Saw Lab CAM pipeline.

    For Wave E1 this creates a synthetic job_id and returns 'queued'.
    Later Saw Lab / PipelineLab can pick this up and attach real job records.
    """
    job_id = f"saw_job_{uuid.uuid4().hex[:12]}"

    message = (
        f"Pattern {request.pattern_id} queued for {request.operation_type} "
        f"with tool {request.tool_id} and material {request.material_id}."
    )

    return PipelineHandoffResponse(
        job_id=job_id,
        pattern_id=request.pattern_id,
        status="queued",
        message=message,
    )
