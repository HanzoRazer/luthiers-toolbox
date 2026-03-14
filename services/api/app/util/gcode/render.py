"""
G-code SVG Rendering

Generate SVG visualizations from G-code paths for backplot display.
"""
from __future__ import annotations

from typing import List, Tuple


def svg_from_points(points: List[Tuple[float, float]], stroke: str = "black") -> str:
    """
    Generate SVG polyline from XY points.

    Args:
        points: List of (x, y) coordinates
        stroke: SVG stroke color

    Returns:
        SVG string with polyline element

    Example:
        >>> svg = svg_from_points([(0,0), (10,0), (10,10)])
        >>> 'polyline' in svg
        True
    """
    if not points:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    pad = 10.0
    w = (maxx - minx) + 2 * pad
    h = (maxy - miny) + 2 * pad

    # Flip Y axis for SVG (Y increases downward)
    pts = " ".join([f"{x - minx + pad:.2f},{h - (y - miny + pad):.2f}" for x, y in points])

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">'
        f'<polyline fill="none" stroke="{stroke}" stroke-width="1" points="{pts}" />'
        f'</svg>'
    )


def svg_from_segments(
    segments: List[dict],
    width: int = 800,
    height: int = 600,
    padding: int = 20,
    rapid_color: str = "#00FF00",
    cut_color: str = "#0066FF",
    arc_color: str = "#FF6600",
) -> str:
    """
    Generate SVG from segment data (from simulate_segments).

    Args:
        segments: List of segment dicts with from_pos, to_pos, type
        width: SVG width in pixels
        height: SVG height in pixels
        padding: Padding around the path
        rapid_color: Color for rapid moves (G0)
        cut_color: Color for linear cuts (G1)
        arc_color: Color for arc moves (G2/G3)

    Returns:
        SVG string with path visualization
    """
    if not segments:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"/>'

    # Calculate bounds
    all_x = []
    all_y = []
    for seg in segments:
        all_x.extend([seg["from_pos"][0], seg["to_pos"][0]])
        all_y.extend([seg["from_pos"][1], seg["to_pos"][1]])

    minx, maxx = min(all_x), max(all_x)
    miny, maxy = min(all_y), max(all_y)

    # Scale to fit viewport
    data_w = maxx - minx or 1
    data_h = maxy - miny or 1
    scale_x = (width - 2 * padding) / data_w
    scale_y = (height - 2 * padding) / data_h
    scale = min(scale_x, scale_y)

    def transform(x: float, y: float) -> Tuple[float, float]:
        tx = padding + (x - minx) * scale
        ty = height - padding - (y - miny) * scale  # Flip Y
        return tx, ty

    # Build path elements
    paths = []
    for seg in segments:
        x1, y1 = transform(seg["from_pos"][0], seg["from_pos"][1])
        x2, y2 = transform(seg["to_pos"][0], seg["to_pos"][1])

        seg_type = seg.get("type", "cut")
        if seg_type == "rapid":
            color = rapid_color
            dash = "5,3"
        elif seg_type in ("arc_cw", "arc_ccw"):
            color = arc_color
            dash = ""
        else:
            color = cut_color
            dash = ""

        style = f'stroke="{color}" stroke-width="1" fill="none"'
        if dash:
            style += f' stroke-dasharray="{dash}"'

        paths.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {style}/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        + "".join(paths)
        + '</svg>'
    )
