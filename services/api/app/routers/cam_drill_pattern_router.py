# services/api/app/routers/cam_drill_pattern_router.py
"""
CAM Drill Pattern Router (N10 CAM Essentials)
Generate drilling patterns (grid, circle, line) with modal cycles.
"""
from datetime import datetime, timezone
from math import cos, pi, sin
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

# Import RMOS run artifact persistence (OPERATION lane requirement)
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

# Import post injection utilities
try:
    from ..util.post_injection_helpers import build_post_context_v2, wrap_with_post_v2
    HAS_POST_HELPERS = True
except ImportError:
    HAS_POST_HELPERS = False

router = APIRouter(prefix="/cam/drill/pattern", tags=["CAM", "N10"])


class GridSpec(BaseModel):
    """Grid pattern specification"""
    cols: int
    rows: int
    dx: float  # Spacing between columns (mm)
    dy: float  # Spacing between rows (mm)


class CircleSpec(BaseModel):
    """Circular pattern specification"""
    count: int
    radius: float
    start_angle_deg: float = 0.0


class LineSpec(BaseModel):
    """Linear pattern specification"""
    count: int
    dx: float  # X increment per hole
    dy: float  # Y increment per hole


class Pattern(BaseModel):
    """Drill pattern definition"""
    type: Literal["grid", "circle", "line"]
    origin_x: float = 0.0
    origin_y: float = 0.0
    
    # Pattern-specific specs (only one should be provided based on type)
    grid: Optional[GridSpec] = None
    circle: Optional[CircleSpec] = None
    line: Optional[LineSpec] = None


class DrillParams(BaseModel):
    """Drilling parameters for pattern"""
    z: float  # Hole depth
    feed: float  # Feed rate (mm/min)
    cycle: Literal["G81", "G83"] = "G81"
    r_clear: Optional[float] = None
    peck_q: Optional[float] = None
    dwell_p: Optional[float] = None
    safe_z: float = 5.0
    units: str = "mm"
    
    # Post-processor parameters
    post: Optional[str] = None
    post_mode: Optional[str] = None
    machine_id: Optional[str] = None
    rpm: Optional[float] = None
    program_no: Optional[str] = None
    work_offset: Optional[str] = None
    tool: Optional[int] = None


def _f(n: float) -> str:
    """Format float to 3 decimal places"""
    return f"{n:.3f}"


def _generate_points(p: Pattern) -> List[tuple]:
    """Generate (x, y) points from pattern specification"""
    pts = []
    ox, oy = p.origin_x, p.origin_y
    
    if p.type == "grid" and p.grid:
        # Rectangular grid pattern
        for r in range(p.grid.rows):
            for c in range(p.grid.cols):
                pts.append((ox + c * p.grid.dx, oy + r * p.grid.dy))
    
    elif p.type == "circle" and p.circle:
        # Circular pattern (evenly spaced)
        n = max(1, p.circle.count)
        for i in range(n):
            ang = (p.circle.start_angle_deg / 180.0 * pi) + 2 * pi * i / n
            pts.append((
                ox + p.circle.radius * cos(ang),
                oy + p.circle.radius * sin(ang)
            ))
    
    elif p.type == "line" and p.line:
        # Linear array
        for i in range(p.line.count):
            pts.append((ox + i * p.line.dx, oy + i * p.line.dy))
    
    return pts



def generate_drill_pattern_program(pat: Pattern, prm: DrillParams) -> str:
    """
    Pure generator: returns G-code text for the requested drill pattern.
    Single source of truth for drill pattern toolpath - used by both draft and governed endpoints.
    """
    points = _generate_points(pat)
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
    return "
".join(lines) + "
"


# =============================================================================
# Draft Lane: Fast preview, no RMOS tracking
# =============================================================================

@router.post("/gcode", response_class=Response)
def drill_pattern_gcode(pat: Pattern, prm: DrillParams) -> Response:
    """
    Generate drilling G-code from pattern specification (DRAFT lane).

    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /gcode_governed.
    """
    program = generate_drill_pattern_program(pat, prm)
    resp = Response(content=program, media_type="text/plain; charset=utf-8")

    if HAS_POST_HELPERS:
        ctx = build_post_context_v2(
            post=prm.post, post_mode=prm.post_mode, units=prm.units,
            machine_id=prm.machine_id, RPM=prm.rpm, PROGRAM_NO=prm.program_no,
            WORK_OFFSET=prm.work_offset, TOOL=prm.tool, SAFE_Z=prm.safe_z,
            DWELL_P=prm.dwell_p, PECK_Q=prm.peck_q, R_CLEAR=prm.r_clear
        )
        resp = wrap_with_post_v2(resp, ctx)

    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail
# =============================================================================

@router.post("/gcode_governed", response_class=Response)
def drill_pattern_gcode_governed(pat: Pattern, prm: DrillParams) -> Response:
    """
    Generate drilling G-code from pattern specification (GOVERNED lane).

    Same toolpath as /gcode but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    program = generate_drill_pattern_program(pat, prm)
    resp = Response(content=program, media_type="text/plain; charset=utf-8")

    if HAS_POST_HELPERS:
        ctx = build_post_context_v2(
            post=prm.post, post_mode=prm.post_mode, units=prm.units,
            machine_id=prm.machine_id, RPM=prm.rpm, PROGRAM_NO=prm.program_no,
            WORK_OFFSET=prm.work_offset, TOOL=prm.tool, SAFE_Z=prm.safe_z,
            DWELL_P=prm.dwell_p, PECK_Q=prm.peck_q, R_CLEAR=prm.r_clear
        )
        resp = wrap_with_post_v2(resp, ctx)
        try:
            program = resp.body.decode("utf-8") if isinstance(resp.body, (bytes, bytearray)) else program
        except Exception:
            pass

    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj({"pattern": pat.model_dump(mode="json"), "params": prm.model_dump(mode="json")})
    gcode_hash = sha256_of_text(program)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="drill_pattern_gcode",
        workflow_mode="drill_pattern",
        event_type="drill_pattern_gcode_execution",
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)

    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp


@router.get("/info")
def pattern_info() -> Dict[str, Any]:
    """Get drill pattern information"""
    return {
        "operation": "drill_pattern",
        "description": "Generate drilling patterns (grid, circle, line) with modal cycles",
        "supports_post_processors": HAS_POST_HELPERS,
        "patterns": {
            "grid": "Rectangular array (rows × cols with dx, dy spacing)",
            "circle": "Circular array (count holes evenly spaced on radius)",
            "line": "Linear array (count holes with dx, dy increments)"
        },
        "examples": {
            "grid_4x3": {"type": "grid", "grid": {"cols": 4, "rows": 3, "dx": 10.0, "dy": 10.0}},
            "circle_6": {"type": "circle", "circle": {"count": 6, "radius": 20.0, "start_angle_deg": 0.0}},
            "line_5": {"type": "line", "line": {"count": 5, "dx": 5.0, "dy": 0.0}}
        }
    }
