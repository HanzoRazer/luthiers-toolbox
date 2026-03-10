"""
CAM Binding/Purfling Module

Binding channel and purfling ledge toolpath generation.
Resolves: OM-GAP-03, OM-GAP-04, OM-PURF-01, OM-PURF-02, BEN-GAP-01

Binding is the decorative strip around the body edge.
Purfling is the thin decorative line inset from the binding.

Workflow:
1. Generate binding channel (rabbeted edge around body)
2. Generate purfling ledge (shallow ledge inside binding)
3. Glue in binding strip
4. Glue in purfling strip

Usage:
    from app.cam.binding import BindingChannel, PurflingLedge, BindingConfig

    # Binding channel
    channel = BindingChannel(
        outline=body_polygon,
        config=BindingConfig(
            channel_width_mm=1.5,
            channel_depth_mm=2.0,
            tool_diameter_mm=3.175,
        )
    )
    gcode = channel.generate_gcode()

    # Purfling ledge (second pass)
    ledge = PurflingLedge(
        outline=body_polygon,
        config=PurflingConfig(
            ledge_width_mm=1.0,
            ledge_depth_mm=0.8,
            offset_from_edge_mm=1.5,  # Inside binding
        )
    )
    gcode = ledge.generate_gcode()
"""

from .channel_toolpath import BindingChannel, BindingConfig, BindingResult
from .purfling_ledge import PurflingLedge, PurflingConfig, PurflingResult
from .offset_geometry import generate_binding_offset, generate_purfling_offset

__all__ = [
    "BindingChannel",
    "BindingConfig",
    "BindingResult",
    "PurflingLedge",
    "PurflingConfig",
    "PurflingResult",
    "generate_binding_offset",
    "generate_purfling_offset",
]
