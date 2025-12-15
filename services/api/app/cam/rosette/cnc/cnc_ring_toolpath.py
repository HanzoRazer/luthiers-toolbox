# N16.0 - Ring Toolpath Geometry Core
#
# Purpose:
#   Provide accurate XY toolpath geometry for rosette rings
#   based on the SliceBatch produced by the N12 geometry engine.
#
#   This replaces the "diagonal stub" segments used in the older
#   build_linear_toolpaths helper, but is additive and does not
#   remove the old function (so existing callers remain valid).
#
#   Geometry:
#     - Each slice describes an angular region on a circular ring.
#     - We approximate each slice as a straight chord between
#       theta_start_deg and theta_end_deg at the given radius.
#     - Origin and rotation are controlled by JigAlignment.
#
#   Z:
#     - For N16.0 we support a single Z depth (one pass).
#       N16.x can extend to multi-pass Z stepping.
#
# Data contracts:
#   - slices: list[dict] where each dict includes:
#       "theta_start_deg", "theta_end_deg", "radius_mm" (optional),
#       and any other slice metadata.
#
#   - If radius_mm is absent per-slice, we use a ring_radius_mm
#     argument (nominal radius for the ring).
#
#   - Returns a ToolpathPlan using the existing ToolpathSegment
#     dataclass so it drops in with the N14 skeleton.
#

from __future__ import annotations

from math import cos, sin, radians
from typing import Dict, Any, List

from .cnc_toolpath import ToolpathPlan, ToolpathSegment  # type: ignore


def _polar_to_cartesian(
    radius_mm: float,
    theta_deg: float,
    origin_x_mm: float,
    origin_y_mm: float,
    rotation_deg: float = 0.0,
) -> tuple[float, float]:
    """
    Convert polar coordinates (radius, theta) to XY in machine space,
    with an optional rotation and origin offset.

    theta_deg is the angle on the rosette ring (before jig rotation).
    rotation_deg is the jig rotation with respect to machine axes.
    """
    # Total angle = slice angle + jig rotation
    total_deg = theta_deg + rotation_deg
    theta_rad = radians(total_deg)

    x = origin_x_mm + radius_mm * cos(theta_rad)
    y = origin_y_mm + radius_mm * sin(theta_rad)
    return x, y


def build_ring_arc_toolpaths(
    ring_id: int,
    slices: List[Dict[str, Any]],
    ring_radius_mm: float,
    feed_mm_per_min: float,
    origin_x_mm: float,
    origin_y_mm: float,
    rotation_deg: float,
    z_depth_mm: float,
) -> ToolpathPlan:
    """
    Build a ToolpathPlan for a single rosette ring, using chord segments
    between theta_start_deg and theta_end_deg for each slice.

    Arguments:
      ring_id:            numeric ID of the ring
      slices:             list of slice dicts; each must include
                          theta_start_deg and theta_end_deg in degrees
                          (as produced by N12 geometry).
                          If a slice includes "radius_mm", that is used
                          instead of ring_radius_mm.
      ring_radius_mm:     fallback radius if slices omit radius_mm
      feed_mm_per_min:    feed rate for all segments
      origin_x_mm:        jig origin X (machine coordinates)
      origin_y_mm:        jig origin Y
      rotation_deg:       jig rotation in degrees
      z_depth_mm:         cutting depth (negative is "into" the material)

    Returns:
      ToolpathPlan with one ToolpathSegment per slice.
    """
    segments: list[ToolpathSegment] = []

    for idx, s in enumerate(slices):
        theta_start = float(s.get("theta_start_deg", 0.0))
        theta_end = float(s.get("theta_end_deg", 0.0))

        # Use per-slice radius if available, otherwise the ring-wide radius
        radius = float(s.get("radius_mm", ring_radius_mm))

        x_start, y_start = _polar_to_cartesian(
            radius_mm=radius,
            theta_deg=theta_start,
            origin_x_mm=origin_x_mm,
            origin_y_mm=origin_y_mm,
            rotation_deg=rotation_deg,
        )
        x_end, y_end = _polar_to_cartesian(
            radius_mm=radius,
            theta_deg=theta_end,
            origin_x_mm=origin_x_mm,
            origin_y_mm=origin_y_mm,
            rotation_deg=rotation_deg,
        )

        seg = ToolpathSegment(
            ring_id=ring_id,
            segment_index=idx,
            x_start_mm=x_start,
            y_start_mm=y_start,
            z_start_mm=z_depth_mm,
            x_end_mm=x_end,
            y_end_mm=y_end,
            z_end_mm=z_depth_mm,
            feed_mm_per_min=feed_mm_per_min,
        )
        segments.append(seg)

    return ToolpathPlan(
        ring_id=ring_id,
        segments=segments,
    )


def build_ring_arc_toolpaths_multipass(
    ring_id: int,
    slices: List[Dict[str, Any]],
    ring_radius_mm: float,
    feed_mm_per_min: float,
    origin_x_mm: float,
    origin_y_mm: float,
    rotation_deg: float,
    z_passes_mm: List[float],
) -> ToolpathPlan:
    """
    N16.2 - Multi-pass variant of build_ring_arc_toolpaths.

    Instead of a single Z depth, this function takes a list of Z depths
    (negative values, in mm) and repeats the chord toolpaths once per
    depth. This is a simple "same geometry at deeper Z" strategy that
    lets the simulation and safety layers see realistic runtime.

    segment_index is globally unique across all passes.

    Arguments:
      ring_id:            numeric ID of the ring
      slices:             list of slice dicts with theta_start_deg and theta_end_deg
      ring_radius_mm:     fallback radius if slices omit radius_mm
      feed_mm_per_min:    feed rate for all segments
      origin_x_mm:        jig origin X (machine coordinates)
      origin_y_mm:        jig origin Y
      rotation_deg:       jig rotation in degrees
      z_passes_mm:        list of Z depths (negative values), e.g. [-0.5, -1.0, -1.5]

    Returns:
      ToolpathPlan with segments repeated for each pass.
    """
    segments: list[ToolpathSegment] = []
    seg_idx = 0

    for pass_z in z_passes_mm:
        for s in slices:
            theta_start = float(s.get("theta_start_deg", 0.0))
            theta_end = float(s.get("theta_end_deg", 0.0))
            radius = float(s.get("radius_mm", ring_radius_mm))

            x_start, y_start = _polar_to_cartesian(
                radius_mm=radius,
                theta_deg=theta_start,
                origin_x_mm=origin_x_mm,
                origin_y_mm=origin_y_mm,
                rotation_deg=rotation_deg,
            )
            x_end, y_end = _polar_to_cartesian(
                radius_mm=radius,
                theta_deg=theta_end,
                origin_x_mm=origin_x_mm,
                origin_y_mm=origin_y_mm,
                rotation_deg=rotation_deg,
            )

            seg = ToolpathSegment(
                ring_id=ring_id,
                segment_index=seg_idx,
                x_start_mm=x_start,
                y_start_mm=y_start,
                z_start_mm=pass_z,
                x_end_mm=x_end,
                y_end_mm=y_end,
                z_end_mm=pass_z,
                feed_mm_per_min=feed_mm_per_min,
            )
            segments.append(seg)
            seg_idx += 1

    return ToolpathPlan(
        ring_id=ring_id,
        segments=segments,
    )
