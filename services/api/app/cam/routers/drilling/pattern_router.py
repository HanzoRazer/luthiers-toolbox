"""
CAM Drill Pattern Router

Generate drilling patterns (grid, circle, line) with modal cycles.

Migrated from: routers/cam_drill_pattern_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /gcode    - Generate pattern drilling G-code
    GET  /info     - Get pattern info
"""

from __future__ import annotations

from math import cos, pi, sin
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

try:
    from ....util.post_injection_helpers import build_post_context_v2, wrap_with_post_v2
    HAS_POST_HELPERS = True
except ImportError:
    HAS_POST_HELPERS = False

router = APIRouter()


class GridSpec(BaseModel):
    cols: int
    rows: int
    dx: float
    dy: float


class CircleSpec(BaseModel):
    count: int
    radius: float
    start_angle_deg: float = 0.0


class LineSpec(BaseModel):
    count: int
    dx: float
    dy: float


class Pattern(BaseModel):
    type: Literal["grid", "circle", "line"]
    origin_x: float = 0.0
    origin_y: float = 0.0
    grid: Optional[GridSpec] = None
    circle: Optional[CircleSpec] = None
    line: Optional[LineSpec] = None


class DrillParams(BaseModel):
    z: float
    feed: float
    cycle: Literal["G81", "G83"] = "G81"
    r_clear: Optional[float] = None
    peck_q: Optional[float] = None
    dwell_p: Optional[float] = None
    safe_z: float = 5.0
    units: str = "mm"
    post: Optional[str] = None
    post_mode: Optional[str] = None
    machine_id: Optional[str] = None
    rpm: Optional[float] = None
    program_no: Optional[str] = None
    work_offset: Optional[str] = None
    tool: Optional[int] = None


def _f(n: float) -> str:
    return f"{n:.3f}"


def _generate_points(p: Pattern) -> List[tuple]:
    pts = []
    ox, oy = p.origin_x, p.origin_y

    if p.type == "grid" and p.grid:
        for r in range(p.grid.rows):
            for c in range(p.grid.cols):
                pts.append((ox + c * p.grid.dx, oy + r * p.grid.dy))
    elif p.type == "circle" and p.circle:
        n = max(1, p.circle.count)
        for i in range(n):
            ang = (p.circle.start_angle_deg / 180.0 * pi) + 2 * pi * i / n
            pts.append((ox + p.circle.radius * cos(ang), oy + p.circle.radius * sin(ang)))
    elif p.type == "line" and p.line:
        for i in range(p.line.count):
            pts.append((ox + i * p.line.dx, oy + i * p.line.dy))

    return pts


@router.post("/gcode", response_class=Response)
def drill_pattern_gcode(pat: Pattern, prm: DrillParams) -> Response:
    """Generate drilling G-code from pattern specification."""
    points = _generate_points(pat)

    if HAS_POST_HELPERS:
        ctx = build_post_context_v2(
            post=prm.post,
            post_mode=prm.post_mode,
            units=prm.units,
            machine_id=prm.machine_id,
            RPM=prm.rpm,
            PROGRAM_NO=prm.program_no,
            WORK_OFFSET=prm.work_offset,
            TOOL=prm.tool,
            SAFE_Z=prm.safe_z,
        )

    r_clear = _f(prm.r_clear if prm.r_clear is not None else 5.0)

    lines = [
        "G90",
        f"G0 Z{_f(prm.safe_z)}",
    ]

    cyc = prm.cycle.upper()

    for (x, y) in points:
        if cyc == "G81":
            dwell = f" P{_f(prm.dwell_p)}" if prm.dwell_p is not None else ""
            lines.append(f"G81 X{_f(x)} Y{_f(y)} Z{_f(prm.z)} R{r_clear} F{_f(prm.feed)}{dwell}")
        else:
            peck = _f(prm.peck_q if prm.peck_q is not None else 1.0)
            dwell = f" P{_f(prm.dwell_p)}" if prm.dwell_p is not None else ""
            lines.append(f"G83 X{_f(x)} Y{_f(y)} Z{_f(prm.z)} R{r_clear} Q{peck} F{_f(prm.feed)}{dwell}")

    lines.append("G80")
    body = "\n".join(lines) + "\n"
    resp = Response(content=body, media_type="text/plain; charset=utf-8")

    if HAS_POST_HELPERS:
        resp = wrap_with_post_v2(resp, ctx)

    return resp


@router.get("/info")
def pattern_info() -> Dict[str, Any]:
    """Get drill pattern information"""
    return {
        "operation": "drill_pattern",
        "description": "Generate drilling patterns (grid, circle, line) with modal cycles",
        "supports_post_processors": HAS_POST_HELPERS,
    }
