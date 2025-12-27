# services/api/app/routers/cam_roughing_router.py
"""
CAM Roughing Router (N10 CAM Essentials)
Simple rectangular roughing G-code generator with post-processor support.

H7.2.2: Added roughing_gcode_intent endpoint with Prometheus-style metrics.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, Response
from pydantic import BaseModel, Field

from app.observability.metrics import (
    cam_roughing_intent_requests_total,
    cam_roughing_intent_issues_total,
    cam_roughing_intent_latency_ms,
    now_ms,
    should_sample_request_id,
)

# Import post injection utilities (already in codebase from Phase 2)
try:
    from ..util.post_injection_helpers import build_post_context_v2, wrap_with_post_v2
    HAS_POST_HELPERS = True
except ImportError:
    HAS_POST_HELPERS = False

router = APIRouter(prefix="/cam/roughing", tags=["CAM", "N10"])


class RoughReq(BaseModel):
    """Request model for rectangular roughing operation"""
    width: float
    height: float
    stepdown: float
    stepover: float
    feed: float
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


@router.post("/gcode", response_class=Response)
def roughing_gcode(req: RoughReq) -> Response:
    """
    Generate simple rectangular roughing G-code.
    
    Pattern: Move to origin, plunge, mill rectangular boundary, retract.
    Suitable for basic pocket roughing or face milling.
    """
    x2, y2 = req.width, req.height
    
    # Generate G-code body (simple rectangle)
    lines = [
        "G90",  # Absolute positioning
        f"G0 Z{_f(req.safe_z)}",  # Rapid to safe height
        "G0 X0 Y0",  # Rapid to origin
        f"G1 Z{_f(-req.stepdown)} F{_f(req.feed)}",  # Plunge to depth
        f"G1 X{_f(x2)}",  # Cut to far X
        f"G1 Y{_f(y2)}",  # Cut to far Y
        f"G1 X0",  # Cut back to near X
        f"G1 Y0",  # Cut back to origin
        "G0 Z{SAFE_Z}"  # Retract (token will be replaced)
    ]
    
    body = "\n".join(lines).replace("{SAFE_Z}", _f(req.safe_z)) + "\n"
    
    # Create response
    resp = Response(content=body, media_type="text/plain; charset=utf-8")
    
    # Apply post-processor wrapping if available
    if HAS_POST_HELPERS:
        ctx = build_post_context_v2(
            post=req.post,
            post_mode=req.post_mode,
            units=req.units,
            machine_id=req.machine_id,
            RPM=req.rpm,
            PROGRAM_NO=req.program_no,
            WORK_OFFSET=req.work_offset,
            TOOL=req.tool,
            SAFE_Z=req.safe_z
        )
        resp = wrap_with_post_v2(resp, ctx)
    
    return resp


@router.get("/info")
def roughing_info() -> Dict[str, Any]:
    """Get roughing operation information"""
    return {
        "operation": "roughing",
        "description": "Simple rectangular roughing for pocket clearing or face milling",
        "supports_post_processors": HAS_POST_HELPERS,
        "parameters": {
            "width": "Pocket width (mm)",
            "height": "Pocket height (mm)",
            "stepdown": "Depth per pass (mm)",
            "stepover": "Lateral stepover (mm)",
            "feed": "Feed rate (mm/min)",
            "safe_z": "Safe retract height (mm)"
        },
        "post_params": ["post", "post_mode", "machine_id", "rpm", "program_no", "work_offset", "tool"]
    }


# =============================================================================
# H7.2.2: Roughing G-Code Intent Endpoint (with Prometheus metrics)
# =============================================================================

class RoughingIntentDesign(BaseModel):
    """Design parameters for roughing intent."""
    width_mm: float = Field(..., description="Pocket width in mm")
    height_mm: float = Field(..., description="Pocket height in mm")
    depth_mm: float = Field(..., description="Total depth in mm")
    stepdown_mm: float = Field(..., description="Depth per pass in mm")
    stepover_mm: float = Field(..., description="Lateral stepover in mm")


class RoughingIntentContext(BaseModel):
    """Tool/machine context for roughing."""
    tool_id: Optional[str] = None
    machine_id: Optional[str] = None
    feed_rate: float = Field(default=1000.0, description="Feed rate in mm/min")
    spindle_rpm: Optional[int] = None


class RoughingIntentRequest(BaseModel):
    """H7.2.2: Roughing G-code intent request."""
    design: RoughingIntentDesign
    context: RoughingIntentContext = Field(default_factory=RoughingIntentContext)
    units: str = Field(default="mm", description="Input units: mm or inch")


class RoughingIntentIssue(BaseModel):
    """Normalization issue (non-fatal warning)."""
    code: str
    message: str
    path: str = ""


class RoughingIntentResponse(BaseModel):
    """H7.2.2: Roughing G-code intent response."""
    gcode: str = Field(..., description="Generated G-code")
    issues: List[RoughingIntentIssue] = Field(default_factory=list)
    normalized_design: RoughingIntentDesign
    status: str = Field(default="OK")


def _normalize_roughing_intent(
    req: RoughingIntentRequest,
) -> tuple[RoughingIntentDesign, List[RoughingIntentIssue]]:
    """
    Normalize roughing intent to mm and validate parameters.
    Returns (normalized_design, issues).
    """
    issues: List[RoughingIntentIssue] = []
    design = req.design

    # Unit conversion if needed
    scale = 25.4 if req.units.lower() == "inch" else 1.0
    if scale != 1.0:
        design = RoughingIntentDesign(
            width_mm=design.width_mm * scale,
            height_mm=design.height_mm * scale,
            depth_mm=design.depth_mm * scale,
            stepdown_mm=design.stepdown_mm * scale,
            stepover_mm=design.stepover_mm * scale,
        )
        issues.append(RoughingIntentIssue(
            code="UNITS_CONVERTED",
            message=f"Converted from {req.units} to mm (scale={scale})",
            path="units",
        ))

    # Validation warnings
    if design.stepdown_mm > design.depth_mm:
        issues.append(RoughingIntentIssue(
            code="STEPDOWN_EXCEEDS_DEPTH",
            message="stepdown_mm exceeds depth_mm; clamped to depth_mm",
            path="design.stepdown_mm",
        ))
        design = RoughingIntentDesign(
            width_mm=design.width_mm,
            height_mm=design.height_mm,
            depth_mm=design.depth_mm,
            stepdown_mm=design.depth_mm,
            stepover_mm=design.stepover_mm,
        )

    if design.stepover_mm <= 0:
        issues.append(RoughingIntentIssue(
            code="INVALID_STEPOVER",
            message="stepover_mm must be positive; defaulted to 5.0",
            path="design.stepover_mm",
        ))
        design = RoughingIntentDesign(
            width_mm=design.width_mm,
            height_mm=design.height_mm,
            depth_mm=design.depth_mm,
            stepdown_mm=design.stepdown_mm,
            stepover_mm=5.0,
        )

    return design, issues


def _generate_roughing_gcode(
    design: RoughingIntentDesign,
    context: RoughingIntentContext,
) -> str:
    """Generate roughing G-code from normalized design."""
    lines = [
        "; Roughing G-code (H7.2.2)",
        "G90 G21",  # Absolute, mm
        f"G0 Z5.0",  # Safe height
    ]

    if context.spindle_rpm:
        lines.append(f"S{context.spindle_rpm} M3")

    # Multi-pass roughing
    current_z = 0.0
    while current_z > -design.depth_mm:
        current_z = max(current_z - design.stepdown_mm, -design.depth_mm)
        lines.append(f"G0 X0 Y0")
        lines.append(f"G1 Z{current_z:.3f} F{context.feed_rate / 2:.0f}")

        # Simple rectangular pass
        y = 0.0
        direction = 1
        while y <= design.height_mm:
            if direction > 0:
                lines.append(f"G1 X{design.width_mm:.3f} F{context.feed_rate:.0f}")
            else:
                lines.append(f"G1 X0 F{context.feed_rate:.0f}")
            y += design.stepover_mm
            if y <= design.height_mm:
                lines.append(f"G1 Y{y:.3f}")
            direction *= -1

    lines.append("G0 Z5.0")
    lines.append("M5")
    lines.append("M30")

    return "\n".join(lines) + "\n"


@router.post("/gcode_intent", response_model=RoughingIntentResponse)
def roughing_gcode_intent(
    req: RoughingIntentRequest,
    x_request_id: Optional[str] = Header(default=None),
) -> RoughingIntentResponse:
    """
    H7.2.2: Intent-native roughing G-code generation with normalization and metrics.

    Accepts high-level roughing parameters, normalizes to mm, validates,
    and produces G-code. Metrics are recorded for monitoring.

    Request IDs are sampled for structured logging (default 1%).
    """
    import logging
    logger = logging.getLogger(__name__)

    start_ms = now_ms()

    # Increment request counter
    cam_roughing_intent_requests_total.inc()

    # Normalize and validate
    normalized_design, issues = _normalize_roughing_intent(req)

    # Track issues metric
    if issues:
        cam_roughing_intent_issues_total.inc()
        if should_sample_request_id() and x_request_id:
            logger.info(
                f"roughing_gcode_intent issues request_id={x_request_id} count={len(issues)}"
            )

    # Generate G-code
    gcode = _generate_roughing_gcode(normalized_design, req.context)

    # Record latency
    latency = now_ms() - start_ms
    cam_roughing_intent_latency_ms.observe(latency)

    return RoughingIntentResponse(
        gcode=gcode,
        issues=[RoughingIntentIssue(code=i.code, message=i.message, path=i.path) for i in issues],
        normalized_design=normalized_design,
        status="OK" if not issues else "OK_WITH_ISSUES",
    )
