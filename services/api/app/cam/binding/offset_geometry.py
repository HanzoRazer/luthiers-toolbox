"""
Offset Geometry for Binding/Purfling

Generates offset curves for binding channel and purfling ledge routing.
Uses the existing polygon_offset_n17 module for robust offsetting.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from app.cam.polygon_offset_n17 import offset_polygon_mm

Pt = Tuple[float, float]


def generate_binding_offset(
    outline: List[Pt],
    channel_width_mm: float,
    tool_diameter_mm: float,
) -> Optional[List[Pt]]:
    """
    Generate the toolpath for binding channel routing.

    The binding channel is cut at the edge of the body. The toolpath
    follows the body outline offset inward by half the tool diameter
    plus half the channel width (so the tool cuts a channel of the
    correct width centered on the edge).

    Args:
        outline: Body outline polygon (closed)
        channel_width_mm: Width of the binding channel
        tool_diameter_mm: Diameter of the router bit

    Returns:
        Offset polygon for toolpath, or None if offset fails
    """
    if not outline or len(outline) < 3:
        return None

    # Calculate offset: inward by (tool_radius + half_channel_width)
    # This positions the tool so it cuts a channel of the right width
    tool_radius = tool_diameter_mm / 2.0

    # For binding, we want the channel centered on the body edge
    # So offset inward by: channel_width/2 - tool_radius
    # This puts the outer edge of the cut at the body edge
    offset = -(channel_width_mm / 2.0)

    result = offset_polygon_mm(
        outline,
        offset,
        join_type="round",
        arc_tolerance=0.1,
    )

    if not result:
        return None

    return result[0]  # Return largest polygon


def generate_purfling_offset(
    outline: List[Pt],
    offset_from_edge_mm: float,
    ledge_width_mm: float,
    tool_diameter_mm: float,
) -> Optional[List[Pt]]:
    """
    Generate the toolpath for purfling ledge routing.

    The purfling ledge is a shallow channel inside the binding.
    It's offset inward from the body edge by the binding width.

    Args:
        outline: Body outline polygon (closed)
        offset_from_edge_mm: Distance from body edge (typically binding width)
        ledge_width_mm: Width of the purfling ledge
        tool_diameter_mm: Diameter of the router bit

    Returns:
        Offset polygon for toolpath, or None if offset fails
    """
    if not outline or len(outline) < 3:
        return None

    # Offset inward by the binding width plus half ledge width
    # This positions the purfling inside the binding
    total_offset = -(offset_from_edge_mm + ledge_width_mm / 2.0)

    result = offset_polygon_mm(
        outline,
        total_offset,
        join_type="round",
        arc_tolerance=0.1,
    )

    if not result:
        return None

    return result[0]


def generate_dual_offset_paths(
    outline: List[Pt],
    channel_width_mm: float,
    tool_diameter_mm: float,
) -> Tuple[Optional[List[Pt]], Optional[List[Pt]]]:
    """
    Generate both inner and outer toolpaths for a channel.

    For wider binding channels, you may need two passes:
    one at the outer edge and one at the inner edge.

    Args:
        outline: Body outline polygon
        channel_width_mm: Total channel width
        tool_diameter_mm: Tool diameter

    Returns:
        Tuple of (outer_path, inner_path), either may be None
    """
    tool_radius = tool_diameter_mm / 2.0

    # Outer pass: tool at outer edge of channel
    outer_offset = -tool_radius
    outer_result = offset_polygon_mm(outline, outer_offset, join_type="round")
    outer_path = outer_result[0] if outer_result else None

    # Inner pass: tool at inner edge of channel
    inner_offset = -(channel_width_mm - tool_radius)
    inner_result = offset_polygon_mm(outline, inner_offset, join_type="round")
    inner_path = inner_result[0] if inner_result else None

    return (outer_path, inner_path)
