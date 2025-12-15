# services/api/app/toolpath/vcarve_toolpath.py

"""
VCarve Toolpath Generator

Converts SVG → MLPaths → G-code for vcarve operations.

This is the cleaned-up consolidation of the early vcarve SVG→segments→G-code logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Iterable, List, Tuple

from . import MLPath, Point2D
from ..art_studio.svg_ingest_service import (
    parse_svg_to_polylines,
    normalize_polylines,
)


@dataclass
class VCarveToolpathParams:
    """Parameters for vcarve toolpath generation."""

    bit_angle_deg: float = 60.0
    depth_mm: float = 1.5
    safe_z_mm: float = 5.0
    feed_rate_mm_min: float = 800.0
    plunge_rate_mm_min: float = 300.0


def polylines_to_mlpaths(polylines: Iterable[List[Point2D]]) -> List[MLPath]:
    """
    Convert polylines into simple MLPaths.

    Args:
        polylines: Iterable of polylines (each a list of (x, y) tuples)

    Returns:
        List of MLPath objects
    """
    return [
        MLPath(
            points=list(poly),
            is_closed=(len(poly) > 2 and poly[0] == poly[-1])
        )
        for poly in polylines
    ]


def build_vcarve_mlpaths_from_svg(svg_text: str) -> List[MLPath]:
    """
    High-level SVG → MLPath converter used by Art Studio vcarve workflows.

    - Parse SVG into polylines (subset of SVG tags).
    - Normalize to (0,0)-anchored coordinates.
    - Wrap in MLPath objects.

    This deliberately does **not** handle stepover, multi-pass, or any advanced
    vcarve logic yet; that will be layered on in future waves.

    Args:
        svg_text: Raw SVG document as string

    Returns:
        List of MLPath objects representing the geometry
    """
    polylines = parse_svg_to_polylines(svg_text)
    norm = normalize_polylines(polylines)
    return polylines_to_mlpaths(norm)


def mlpaths_to_naive_gcode(
    paths: Iterable[MLPath],
    params: VCarveToolpathParams,
) -> str:
    """
    Very early G-code emitter used for smoke testing and preview only.

    IMPORTANT:
    - This is **not** production CAM.
    - It ignores chipload, stepdown, cutter diameter, etc.
    - It is useful as a sanity check while we wire up the full spine.

    Args:
        paths: Iterable of MLPath objects
        params: Toolpath parameters

    Returns:
        G-code as string
    """
    lines: List[str] = []

    header = dedent(
        f"""
        (ToolBox VCarve demo)
        G21
        G90
        G0 Z{params.safe_z_mm:.3f}
        F{params.feed_rate_mm_min:.1f}
        """
    ).strip()
    lines.append(header)

    for path in paths:
        if not path.points:
            continue

        # rapid to first point
        x0, y0 = path.points[0]
        lines.append(f"G0 X{x0:.3f} Y{y0:.3f}")
        lines.append(f"G1 Z{-params.depth_mm:.3f} F{params.plunge_rate_mm_min:.1f}")

        for (x, y) in path.points[1:]:
            lines.append(f"G1 X{x:.3f} Y{y:.3f} F{params.feed_rate_mm_min:.1f}")

        # retract
        lines.append(f"G0 Z{params.safe_z_mm:.3f}")

    # footer
    lines.append("M5")
    lines.append("M30")

    return "\n".join(lines)


def svg_to_naive_gcode(svg_text: str, params: VCarveToolpathParams | None = None) -> str:
    """
    Convenience helper: SVG → MLPaths → G-code.

    Args:
        svg_text: Raw SVG document as string
        params: Optional toolpath parameters (defaults to VCarveToolpathParams())

    Returns:
        G-code as string
    """
    if params is None:
        params = VCarveToolpathParams()
    paths = build_vcarve_mlpaths_from_svg(svg_text)
    return mlpaths_to_naive_gcode(paths, params)
