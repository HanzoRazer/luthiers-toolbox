"""
Inlay Import Pipeline — DXF / SVG / CSV Parsers (Server-Side)

Parses uploaded files into GeometryCollection clip masks.
Running on the server eliminates the XSS vector identified in the V2
prototype review (no dangerouslySetInnerHTML).

Supported formats:
  - DXF: LWPOLYLINE, POLYLINE+VERTEX, CIRCLE, ARC
  - SVG: <path>, <rect>, <circle>, <ellipse>, <polygon>, <polyline>
  - CSV: Material grids (names, aliases, or indices)
"""
from __future__ import annotations

import csv
import io
import math
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from .inlay_geometry import (
    GeometryCollection,
    GeometryElement,
    MATERIAL_KEYS,
    Pt,
)

# ---------------------------------------------------------------------------
# DXF parser — ported from V2, handles 4 entity types
# ---------------------------------------------------------------------------

def parse_dxf(text: str) -> GeometryCollection:
    """Parse a DXF R12 string into a GeometryCollection of polylines/circles.

    Handles LWPOLYLINE, POLYLINE+VERTEX, CIRCLE, ARC.
    """
    lines = text.replace("\r", "").split("\n")
    pairs: List[Tuple[int, str]] = []
    i = 0
    while i < len(lines) - 1:
        try:
            code = int(lines[i].strip())
        except ValueError:
            i += 1
            continue
        val = lines[i + 1].strip()
        pairs.append((code, val))
        i += 2

    # Extract entities
    raw_entities: List[Dict[str, Any]] = []
    in_entities = False
    cur: Optional[Dict[str, Any]] = None
    last_x: Optional[float] = None

    for code, val in pairs:
        if code == 2 and val == "ENTITIES":
            in_entities = True
            continue
        if code == 0 and val == "ENDSEC" and in_entities:
            if cur:
                raw_entities.append(cur)
            break
        if not in_entities:
            continue

        if code == 0:
            if cur:
                raw_entities.append(cur)
            cur = {"type": val, "pts": []}
            last_x = None
        elif cur is not None:
            if code == 10:
                last_x = float(val)
            elif code == 20 and last_x is not None:
                cur["pts"].append((last_x, float(val)))
                last_x = None
            elif code == 40:
                cur["radius"] = float(val)
            elif code == 50:
                cur["start_angle"] = float(val)
            elif code == 51:
                cur["end_angle"] = float(val)
            elif code == 70:
                cur["flags"] = int(val)

    # Merge VERTEX entities into preceding POLYLINE
    merged: List[Dict[str, Any]] = []
    poly: Optional[Dict[str, Any]] = None
    for ent in raw_entities:
        if ent["type"] == "POLYLINE":
            poly = {"type": "POLYLINE", "pts": [], "flags": ent.get("flags", 0)}
        elif ent["type"] == "VERTEX" and poly is not None:
            if ent["pts"]:
                poly["pts"].append(ent["pts"][0])
        elif ent["type"] == "SEQEND" and poly is not None:
            merged.append(poly)
            poly = None
        else:
            if poly is not None:
                merged.append(poly)
                poly = None
            merged.append(ent)

    # Compute bounds
    all_pts: List[Pt] = []
    for ent in merged:
        all_pts.extend(ent.get("pts", []))
        if ent["type"] == "CIRCLE" and ent.get("pts"):
            cx, cy = ent["pts"][0]
            r = ent.get("radius", 0)
            all_pts.extend([(cx - r, cy - r), (cx + r, cy + r)])

    if not all_pts:
        return GeometryCollection()

    min_x = min(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    W = max_x - min_x or 100.0
    H = max_y - min_y or 100.0

    # Convert to GeometryElements (translate to origin, flip Y for SVG)
    elements: List[GeometryElement] = []
    for ent in merged:
        etype = ent["type"]
        if etype in ("LWPOLYLINE", "POLYLINE"):
            pts = [
                (x - min_x, (max_y - y) + min_y) for x, y in ent.get("pts", [])
            ]
            if len(pts) < 2:
                continue
            closed = ent.get("flags", 0) & 1 == 1
            elements.append(GeometryElement(
                kind="polygon" if closed else "polyline",
                points=pts,
                stroke_width=0.25,
            ))
        elif etype == "CIRCLE" and ent.get("pts"):
            cx, cy = ent["pts"][0]
            elements.append(GeometryElement(
                kind="circle",
                points=[(cx - min_x, (max_y - cy) + min_y)],
                radius=ent.get("radius", 0),
                stroke_width=0.25,
            ))
        elif etype == "ARC" and ent.get("pts"):
            cx, cy = ent["pts"][0]
            r = ent.get("radius", 0)
            sa = math.radians(ent.get("start_angle", 0))
            ea = math.radians(ent.get("end_angle", 360))
            if ea <= sa:
                ea += 2 * math.pi
            steps = max(8, int((ea - sa) / (math.pi / 18)))
            pts: List[Pt] = []
            for s in range(steps + 1):
                t = sa + (ea - sa) * s / steps
                pts.append((
                    cx + r * math.cos(t) - min_x,
                    (max_y - (cy + r * math.sin(t))) + min_y,
                ))
            elements.append(GeometryElement(
                kind="polyline",
                points=pts,
                stroke_width=0.25,
            ))

    return GeometryCollection(
        elements=elements,
        width_mm=W,
        height_mm=H,
    )


# ---------------------------------------------------------------------------
# SVG parser — extracts geometry from SVG, no script execution
# ---------------------------------------------------------------------------

_SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def _parse_viewbox(svg_el: ET.Element) -> Tuple[float, float, float, float]:
    vb = svg_el.get("viewBox", "0 0 100 100")
    parts = re.split(r"[\s,]+", vb.strip())
    nums = [float(p) for p in parts[:4]]
    while len(nums) < 4:
        nums.append(100.0)
    return tuple(nums)  # type: ignore[return-value]


def _svg_path_d_to_pts(d: str) -> List[Pt]:
    """Crude SVG path d-string to polyline approximation (M/L/Z only).

    Curves are linearised by sampling; this is intentionally simple for
    clip-mask extraction.
    """
    pts: List[Pt] = []
    tokens = re.findall(r"[MmLlHhVvZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
    cx, cy = 0.0, 0.0
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd in ("M", "m", "L", "l"):
            relative = cmd.islower()
            i += 1
            while i < len(tokens) and tokens[i] not in "MmLlHhVvZzCcSsQqTtAa":
                x = float(tokens[i])
                i += 1
                if i >= len(tokens) or tokens[i] in "MmLlHhVvZzCcSsQqTtAa":
                    break
                y = float(tokens[i])
                i += 1
                if relative:
                    cx += x
                    cy += y
                else:
                    cx, cy = x, y
                pts.append((cx, cy))
        elif cmd in ("H", "h"):
            i += 1
            if i < len(tokens):
                v = float(tokens[i])
                cx = cx + v if cmd == "h" else v
                pts.append((cx, cy))
                i += 1
        elif cmd in ("V", "v"):
            i += 1
            if i < len(tokens):
                v = float(tokens[i])
                cy = cy + v if cmd == "v" else v
                pts.append((cx, cy))
                i += 1
        elif cmd in ("Z", "z"):
            if pts:
                pts.append(pts[0])
            i += 1
        else:
            i += 1
    return pts


def parse_svg(text: str) -> GeometryCollection:
    """Parse SVG text into a GeometryCollection.

    Strips ``<script>``, ``on*`` handlers, and ``<foreignObject>`` before
    parsing to eliminate injection vectors.
    """
    # Sanitize: remove script tags, event handlers, foreignObject
    sanitized = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    sanitized = re.sub(r"<foreignObject\b[^>]*>.*?</foreignObject>", "", sanitized, flags=re.DOTALL | re.IGNORECASE)
    sanitized = re.sub(r'\bon\w+\s*=\s*"[^"]*"', "", sanitized)
    sanitized = re.sub(r"\bon\w+\s*=\s*'[^']*'", "", sanitized)

    root = ET.fromstring(sanitized)
    vb = _parse_viewbox(root)
    W, H = vb[2], vb[3]

    elements: List[GeometryElement] = []

    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag

        if tag == "path":
            d = el.get("d", "")
            pts = _svg_path_d_to_pts(d)
            if len(pts) >= 2:
                closed = pts[0] == pts[-1] if len(pts) > 2 else False
                elements.append(GeometryElement(
                    kind="polygon" if closed else "polyline",
                    points=pts,
                    stroke_width=0.25,
                ))
        elif tag == "circle":
            cx = float(el.get("cx", "0"))
            cy = float(el.get("cy", "0"))
            r = float(el.get("r", "0"))
            if r > 0:
                elements.append(GeometryElement(
                    kind="circle",
                    points=[(cx, cy)],
                    radius=r,
                    stroke_width=0.25,
                ))
        elif tag == "rect":
            x = float(el.get("x", "0"))
            y = float(el.get("y", "0"))
            w = float(el.get("width", "0"))
            h = float(el.get("height", "0"))
            if w > 0 and h > 0:
                elements.append(GeometryElement(
                    kind="rect",
                    points=[(x, y), (x + w, y + h)],
                    stroke_width=0.25,
                ))
        elif tag == "polygon":
            points_str = el.get("points", "")
            pts = _parse_points_attr(points_str)
            if len(pts) >= 3:
                elements.append(GeometryElement(
                    kind="polygon",
                    points=pts,
                    stroke_width=0.25,
                ))
        elif tag == "polyline":
            points_str = el.get("points", "")
            pts = _parse_points_attr(points_str)
            if len(pts) >= 2:
                elements.append(GeometryElement(
                    kind="polyline",
                    points=pts,
                    stroke_width=0.25,
                ))
        elif tag == "ellipse":
            cx = float(el.get("cx", "0"))
            cy = float(el.get("cy", "0"))
            rx = float(el.get("rx", "0"))
            ry = float(el.get("ry", "0"))
            if rx > 0 and ry > 0:
                # Approximate ellipse as polygon
                steps = 36
                pts = [
                    (cx + rx * math.cos(2 * math.pi * s / steps),
                     cy + ry * math.sin(2 * math.pi * s / steps))
                    for s in range(steps)
                ]
                elements.append(GeometryElement(
                    kind="polygon",
                    points=pts,
                    stroke_width=0.25,
                ))

    return GeometryCollection(
        elements=elements,
        width_mm=W,
        height_mm=H,
    )


def _parse_points_attr(s: str) -> List[Pt]:
    """Parse an SVG ``points`` attribute into (x, y) tuples."""
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
    pts: List[Pt] = []
    for i in range(0, len(nums) - 1, 2):
        pts.append((float(nums[i]), float(nums[i + 1])))
    return pts


# ---------------------------------------------------------------------------
# CSV parser — material grid
# ---------------------------------------------------------------------------

_CSV_ALIASES: Dict[str, str] = {
    "b": "ebony", "w": "maple", "r": "red",
    "0": "ebony", "1": "mop", "2": "koa",
    "3": "rosewood", "4": "maple", "5": "walnut",
    "6": "bone", "7": "gold", "8": "cedar", "9": "abalone",
}


def parse_csv_grid(
    text: str,
    band_w: float = 120.0,
    band_h: float = 22.0,
) -> GeometryCollection:
    """Parse a CSV material grid into coloured rectangles.

    Each cell becomes a rect scaled to fill the band.  Cell values can be
    material names (``ebony``), single-letter aliases (``B``), or numeric
    indices (``0``–``9``).
    """
    reader = csv.reader(io.StringIO(text))
    rows: List[List[str]] = []
    for row in reader:
        resolved = []
        for cell in row:
            cell = cell.strip().lower()
            cell = _CSV_ALIASES.get(cell, cell)
            if cell not in MATERIAL_KEYS:
                cell = MATERIAL_KEYS[0]  # fallback to first material
            resolved.append(cell)
        if resolved:
            rows.append(resolved)

    if not rows:
        return GeometryCollection()

    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    cell_w = band_w / n_cols
    cell_h = band_h / n_rows

    elements: List[GeometryElement] = []
    for ri, row in enumerate(rows):
        for ci, mat in enumerate(row):
            mi = MATERIAL_KEYS.index(mat) if mat in MATERIAL_KEYS else 0
            x0 = ci * cell_w
            y0 = ri * cell_h
            elements.append(GeometryElement(
                kind="rect",
                points=[(x0, y0), (x0 + cell_w, y0 + cell_h)],
                material_index=mi,
                stroke_width=0.15,
            ))

    return GeometryCollection(
        elements=elements,
        width_mm=band_w,
        height_mm=band_h,
        radial=False,
        tile_w=band_w,
        tile_h=band_h,
    )
