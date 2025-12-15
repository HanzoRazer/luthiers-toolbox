# services/api/app/art_studio/svg_ingest_service.py
"""
SVG ingest service for Art Studio.

Responsibilities:
  - Parse a subset of SVG tags (path, line, rect, circle, ellipse, polygon, polyline)
  - Convert to polylines (list of (x, y) tuples)
  - Normalize coordinates (shift so bbox starts at 0,0)

This is *not* a full SVG renderer; it's targeted at CAD-style line work.
"""

from __future__ import annotations

import re
from math import cos, hypot, pi, sin
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

Point2D = Tuple[float, float]
Polyline = List[Point2D]


def parse_svg_to_polylines(svg_text: str) -> List[Polyline]:
    """
    Parse SVG text and extract polylines from supported elements.

    Supported tags:
      - <path d="...">       (M/L/H/V/Z commands only; no curves yet)
      - <line x1 y1 x2 y2>
      - <rect x y width height>
      - <circle cx cy r>
      - <ellipse cx cy rx ry>
      - <polygon points="...">
      - <polyline points="...">

    Returns a list of polylines, each a list of (x, y) points.
    """
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return []

    ns = _extract_namespace(root)
    polylines: List[Polyline] = []

    for elem in root.iter():
        tag = _strip_ns(elem.tag, ns)

        if tag == "path":
            d = elem.attrib.get("d", "")
            poly = _parse_path_d(d)
            if poly:
                polylines.append(poly)

        elif tag == "line":
            x1 = float(elem.attrib.get("x1", 0))
            y1 = float(elem.attrib.get("y1", 0))
            x2 = float(elem.attrib.get("x2", 0))
            y2 = float(elem.attrib.get("y2", 0))
            polylines.append([(x1, y1), (x2, y2)])

        elif tag == "rect":
            x = float(elem.attrib.get("x", 0))
            y = float(elem.attrib.get("y", 0))
            w = float(elem.attrib.get("width", 0))
            h = float(elem.attrib.get("height", 0))
            if w > 0 and h > 0:
                polylines.append([
                    (x, y),
                    (x + w, y),
                    (x + w, y + h),
                    (x, y + h),
                    (x, y),  # close
                ])

        elif tag == "circle":
            cx = float(elem.attrib.get("cx", 0))
            cy = float(elem.attrib.get("cy", 0))
            r = float(elem.attrib.get("r", 0))
            if r > 0:
                polylines.append(_circle_to_polyline(cx, cy, r))

        elif tag == "ellipse":
            cx = float(elem.attrib.get("cx", 0))
            cy = float(elem.attrib.get("cy", 0))
            rx = float(elem.attrib.get("rx", 0))
            ry = float(elem.attrib.get("ry", 0))
            if rx > 0 and ry > 0:
                polylines.append(_ellipse_to_polyline(cx, cy, rx, ry))

        elif tag == "polygon":
            pts = elem.attrib.get("points", "")
            poly = _parse_points_attr(pts)
            if poly:
                # close polygon
                poly.append(poly[0])
                polylines.append(poly)

        elif tag == "polyline":
            pts = elem.attrib.get("points", "")
            poly = _parse_points_attr(pts)
            if poly:
                polylines.append(poly)

    return polylines


def normalize_polylines(polylines: List[Polyline]) -> List[Polyline]:
    """
    Shift all polylines so the bounding box starts at (0, 0).
    """
    if not polylines:
        return []

    xs = [x for poly in polylines for (x, _) in poly]
    ys = [y for poly in polylines for (_, y) in poly]

    if not xs or not ys:
        return polylines

    min_x, min_y = min(xs), min(ys)
    shifted = [[(x - min_x, y - min_y) for (x, y) in poly] for poly in polylines]
    return shifted


def polyline_stats(polys: List[Polyline]) -> Dict[str, Any]:
    """
    Compute basic stats for a list of polylines.
    """
    if not polys:
        return {
            "polyline_count": 0,
            "total_length": 0.0,
            "bbox": None,
        }

    total_len = 0.0
    xs: List[float] = []
    ys: List[float] = []

    for poly in polys:
        if len(poly) < 2:
            continue
        for (x, y) in poly:
            xs.append(x)
            ys.append(y)
        for (x1, y1), (x2, y2) in zip(poly[:-1], poly[1:]):
            total_len += hypot(x2 - x1, y2 - y1)

    if not xs or not ys:
        bbox = None
    else:
        bbox = {
            "min_x": min(xs),
            "min_y": min(ys),
            "max_x": max(xs),
            "max_y": max(ys),
        }

    return {
        "polyline_count": len(polys),
        "total_length": float(total_len),
        "bbox": bbox,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_namespace(root: ET.Element) -> str:
    """Extract the default namespace from SVG root tag, if present."""
    match = re.match(r"\{(.+?)\}", root.tag)
    return match.group(1) if match else ""


def _strip_ns(tag: str, ns: str) -> str:
    """Strip namespace prefix from tag name."""
    if ns and tag.startswith("{" + ns + "}"):
        return tag[len(ns) + 2:]
    return tag


def _parse_path_d(d: str) -> Optional[Polyline]:
    """
    Parse a simple SVG path 'd' attribute.

    Only supports M, L, H, V, Z commands (absolute only for now).
    """
    if not d:
        return None

    points: List[Point2D] = []
    tokens = re.findall(r"[MLHVZmlhvz]|[-+]?\d*\.?\d+", d)

    x, y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    i = 0

    while i < len(tokens):
        cmd = tokens[i]

        if cmd in ("M", "m"):
            if i + 2 > len(tokens):
                break
            dx = float(tokens[i + 1])
            dy = float(tokens[i + 2])
            if cmd == "M":
                x, y = dx, dy
            else:
                x += dx
                y += dy
            start_x, start_y = x, y
            points.append((x, y))
            i += 3

        elif cmd in ("L", "l"):
            if i + 2 > len(tokens):
                break
            dx = float(tokens[i + 1])
            dy = float(tokens[i + 2])
            if cmd == "L":
                x, y = dx, dy
            else:
                x += dx
                y += dy
            points.append((x, y))
            i += 3

        elif cmd in ("H", "h"):
            if i + 1 > len(tokens):
                break
            dx = float(tokens[i + 1])
            if cmd == "H":
                x = dx
            else:
                x += dx
            points.append((x, y))
            i += 2

        elif cmd in ("V", "v"):
            if i + 1 > len(tokens):
                break
            dy = float(tokens[i + 1])
            if cmd == "V":
                y = dy
            else:
                y += dy
            points.append((x, y))
            i += 2

        elif cmd in ("Z", "z"):
            x, y = start_x, start_y
            points.append((x, y))
            i += 1

        else:
            # Unknown command; try to parse as numeric (continue with next)
            try:
                # Might be implicit lineto args
                if points:
                    dx = float(tokens[i])
                    dy = float(tokens[i + 1]) if i + 1 < len(tokens) else 0.0
                    x, y = dx, dy
                    points.append((x, y))
                    i += 2
                else:
                    i += 1
            except ValueError:
                i += 1

    return points if len(points) >= 2 else None


def _parse_points_attr(points_str: str) -> Optional[Polyline]:
    """
    Parse an SVG points attribute (e.g., '0,0 10,10 20,0').
    """
    if not points_str.strip():
        return None

    # Normalize whitespace and commas
    normalized = re.sub(r"[,\s]+", " ", points_str.strip())
    parts = normalized.split()

    points: List[Point2D] = []
    for i in range(0, len(parts) - 1, 2):
        try:
            x = float(parts[i])
            y = float(parts[i + 1])
            points.append((x, y))
        except ValueError:
            continue

    return points if points else None


def _circle_to_polyline(cx: float, cy: float, r: float, segments: int = 64) -> Polyline:
    """Approximate a circle as a closed polyline."""
    pts: List[Point2D] = []
    for i in range(segments):
        angle = 2.0 * pi * i / segments
        pts.append((cx + r * cos(angle), cy + r * sin(angle)))
    pts.append(pts[0])  # close
    return pts


def _ellipse_to_polyline(
    cx: float, cy: float, rx: float, ry: float, segments: int = 64
) -> Polyline:
    """Approximate an ellipse as a closed polyline."""
    pts: List[Point2D] = []
    for i in range(segments):
        angle = 2.0 * pi * i / segments
        pts.append((cx + rx * cos(angle), cy + ry * sin(angle)))
    pts.append(pts[0])  # close
    return pts
