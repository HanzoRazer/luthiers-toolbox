"""Acoustic CAM Router — GEN-6

CAM operations for acoustic guitar bodies.

Endpoints:
    GET  /styles              - List available acoustic body styles
    POST /{style}/body/gcode  - Generate body perimeter G-code
    POST /{style}/soundhole/gcode - Generate soundhole routing G-code
    POST /{style}/binding/gcode   - Generate binding channel G-code
    POST /preview             - Preview outline without G-code

LANE: CAM (G-code generation operations)
"""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ....generators.acoustic_body_generator import (
    AcousticBodyGenerator,
    AcousticBodyStyle,
    list_acoustic_styles,
)

router = APIRouter(tags=["Acoustic", "CAM", "GEN-6"])


# =============================================================================
# SCHEMAS
# =============================================================================


class MachineSettings(BaseModel):
    """Machine configuration for G-code generation."""
    safe_z_mm: float = Field(10.0, description="Safe Z height for rapid moves")
    rapid_z_mm: float = Field(3.0, description="Rapid Z above workpiece")
    feed_xy_mm_min: float = Field(1500.0, description="XY feed rate mm/min")
    feed_z_mm_min: float = Field(500.0, description="Z plunge feed rate mm/min")
    spindle_rpm: int = Field(18000, description="Spindle speed RPM")


class PerimeterRequest(BaseModel):
    """Request for body perimeter G-code."""
    tool_diameter_mm: float = Field(6.35, description="End mill diameter (1/4\" = 6.35mm)")
    total_depth_mm: float = Field(12.7, description="Total cut depth (1/2\" = 12.7mm)")
    stepdown_mm: float = Field(3.0, description="Depth per pass")
    tab_count: int = Field(8, description="Number of holding tabs")
    tab_width_mm: float = Field(15.0, description="Tab width")
    tab_height_mm: float = Field(3.0, description="Tab height")
    scale: float = Field(1.0, description="Scale factor (1.0 = full size)")
    machine: MachineSettings = Field(default_factory=MachineSettings)


class SoundholeRequest(BaseModel):
    """Request for soundhole G-code."""
    tool_diameter_mm: float = Field(6.35, description="End mill diameter")
    soundhole_diameter_mm: float = Field(101.6, description="Soundhole diameter (4\" = 101.6mm)")
    depth_mm: float = Field(3.5, description="Top thickness")
    stepdown_mm: float = Field(1.0, description="Depth per pass")
    scale: float = Field(1.0, description="Scale factor")
    machine: MachineSettings = Field(default_factory=MachineSettings)


class BindingRequest(BaseModel):
    """Request for binding channel G-code."""
    channel_width_mm: float = Field(2.0, description="Binding channel width")
    channel_depth_mm: float = Field(2.0, description="Binding channel depth")
    tool_diameter_mm: float = Field(2.0, description="Slot cutter or end mill diameter")
    stepdown_mm: float = Field(0.5, description="Depth per pass")
    scale: float = Field(1.0, description="Scale factor")
    machine: MachineSettings = Field(default_factory=MachineSettings)


class OutlinePreviewRequest(BaseModel):
    """Request for outline preview (no G-code)."""
    style: str = Field("dreadnought", description="Acoustic body style")
    scale: float = Field(1.0, description="Scale factor")
    include_svg: bool = Field(True, description="Include SVG representation")


class GCodeResponse(BaseModel):
    """G-code generation response (for non-streaming)."""
    ok: bool
    style: str
    operation: str
    gcode: str
    line_count: int
    stats: Dict[str, Any] = {}


# =============================================================================
# HELPERS
# =============================================================================


def _validate_style(style: str) -> AcousticBodyStyle:
    """Validate and normalize style parameter."""
    style_lower = style.lower().replace("-", "_").replace(" ", "_")

    # Handle aliases
    if style_lower in ("om", "000", "triple_o"):
        return AcousticBodyStyle.OM
    if style_lower in ("oo", "00", "double_o", "martin_oo"):
        return AcousticBodyStyle.OO

    try:
        return AcousticBodyStyle(style_lower)
    except ValueError:
        available = [s.value for s in AcousticBodyStyle]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown style: '{style}'. Available: {available}"
        )


def _create_generator(style: AcousticBodyStyle, scale: float, machine: MachineSettings) -> AcousticBodyGenerator:
    """Create generator with machine settings."""
    return AcousticBodyGenerator(
        style=style,
        scale=scale,
        safe_z=machine.safe_z_mm,
        rapid_z=machine.rapid_z_mm,
        feed_xy=machine.feed_xy_mm_min,
        feed_z=machine.feed_z_mm_min,
        spindle_rpm=machine.spindle_rpm,
    )


def _gcode_streaming_response(gcode: str, filename: str) -> StreamingResponse:
    """Create streaming response for G-code download."""
    return StreamingResponse(
        io.BytesIO(gcode.encode("utf-8")),
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        }
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/styles")
def list_styles() -> Dict[str, Any]:
    """
    List all available acoustic body styles.

    Returns list of styles with dimensions and outline availability.
    """
    styles = list_acoustic_styles()
    return {
        "ok": True,
        "category": "acoustic",
        "styles": styles,
        "count": len(styles),
        "note": "Use style 'id' in POST /{style}/body/gcode endpoint"
    }


@router.post("/preview")
def preview_outline(request: OutlinePreviewRequest) -> Dict[str, Any]:
    """
    Preview acoustic body outline without G-code generation.

    Returns outline geometry, SVG, and acoustic properties.
    """
    style_enum = _validate_style(request.style)
    generator = AcousticBodyGenerator(style=style_enum, scale=request.scale)
    outline = generator.generate_outline()

    result = outline.to_dict()
    result["ok"] = True

    if request.include_svg:
        result["svg"] = outline.to_svg(
            include_soundhole=True,
            include_centerline=True
        )

    return result


@router.post("/{style}/body/gcode")
def generate_body_perimeter(
    style: str,
    request: PerimeterRequest,
    download: bool = Query(True, description="Return as .nc file download")
) -> Any:
    """
    Generate body perimeter G-code for the specified acoustic style.

    Includes holding tabs for workholding.
    """
    style_enum = _validate_style(style)
    generator = _create_generator(style_enum, request.scale, request.machine)

    gcode = generator.generate_perimeter_gcode(
        tool_diameter_mm=request.tool_diameter_mm,
        total_depth_mm=request.total_depth_mm,
        stepdown_mm=request.stepdown_mm,
        tab_count=request.tab_count,
        tab_width_mm=request.tab_width_mm,
        tab_height_mm=request.tab_height_mm,
    )

    if download:
        filename = f"{style_enum.value}_body_perimeter.nc"
        return _gcode_streaming_response(gcode, filename)

    return GCodeResponse(
        ok=True,
        style=style_enum.value,
        operation="body_perimeter",
        gcode=gcode,
        line_count=len(gcode.splitlines()),
        stats={
            "tool_diameter_mm": request.tool_diameter_mm,
            "total_depth_mm": request.total_depth_mm,
            "tab_count": request.tab_count,
        }
    )


@router.post("/{style}/soundhole/gcode")
def generate_soundhole(
    style: str,
    request: SoundholeRequest,
    download: bool = Query(True, description="Return as .nc file download")
) -> Any:
    """
    Generate soundhole routing G-code.

    Creates circular soundhole cut through guitar top.
    """
    style_enum = _validate_style(style)
    generator = _create_generator(style_enum, request.scale, request.machine)
    generator.soundhole_diameter_mm = request.soundhole_diameter_mm

    gcode = generator.generate_soundhole_gcode(
        tool_diameter_mm=request.tool_diameter_mm,
        depth_mm=request.depth_mm,
        stepdown_mm=request.stepdown_mm,
    )

    if download:
        filename = f"{style_enum.value}_soundhole.nc"
        return _gcode_streaming_response(gcode, filename)

    return GCodeResponse(
        ok=True,
        style=style_enum.value,
        operation="soundhole",
        gcode=gcode,
        line_count=len(gcode.splitlines()),
        stats={
            "soundhole_diameter_mm": request.soundhole_diameter_mm,
            "tool_diameter_mm": request.tool_diameter_mm,
        }
    )


@router.post("/{style}/binding/gcode")
def generate_binding_channel(
    style: str,
    request: BindingRequest,
    download: bool = Query(True, description="Return as .nc file download")
) -> Any:
    """
    Generate binding channel routing G-code.

    Creates ledge around body perimeter for binding strip.
    """
    style_enum = _validate_style(style)
    generator = _create_generator(style_enum, request.scale, request.machine)

    gcode = generator.generate_binding_channel_gcode(
        channel_width_mm=request.channel_width_mm,
        channel_depth_mm=request.channel_depth_mm,
        tool_diameter_mm=request.tool_diameter_mm,
        stepdown_mm=request.stepdown_mm,
    )

    if download:
        filename = f"{style_enum.value}_binding_channel.nc"
        return _gcode_streaming_response(gcode, filename)

    return GCodeResponse(
        ok=True,
        style=style_enum.value,
        operation="binding_channel",
        gcode=gcode,
        line_count=len(gcode.splitlines()),
        stats={
            "channel_width_mm": request.channel_width_mm,
            "channel_depth_mm": request.channel_depth_mm,
        }
    )


__all__ = [
    "router",
    "MachineSettings",
    "PerimeterRequest",
    "SoundholeRequest",
    "BindingRequest",
    "OutlinePreviewRequest",
    "GCodeResponse",
]
