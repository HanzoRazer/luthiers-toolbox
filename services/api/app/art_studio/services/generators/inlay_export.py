"""
Inlay DXF R12 Export

Exports GeometryCollection to DXF R12 (AC1009) with three named layers:
  - CENTERLINE  (gold, colour 2)
  - MALE_CUT    (cyan, colour 4)
  - POCKET_CUT  (orange, colour 40)

Uses ezdxf (already in requirements.txt).  All coordinates in mm.
"""
from __future__ import annotations

import io
from typing import List

import ezdxf
from ezdxf.document import Drawing

from .inlay_geometry import (
    GeometryCollection,
    GeometryElement,
    offset_collection,
    Pt,
)


# DXF colour indices (ACI)
_CLR_CENTERLINE = 2   # yellow
_CLR_MALE = 4          # cyan
_CLR_POCKET = 40       # orange


def _add_element_to_msp(
    msp: ezdxf.layouts.BaseLayout,
    el: GeometryElement,
    layer: str,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> None:
    """Write one GeometryElement to the DXF model space on *layer*."""
    attribs = {"layer": layer}

    if el.kind in ("polygon", "polyline") and el.points:
        pts = [(x + origin_x, y + origin_y) for x, y in el.points]
        close = el.kind == "polygon"
        poly = msp.add_polyline2d(
            pts,
            close=close,
            dxfattribs=attribs,
        )
    elif el.kind == "circle" and el.points:
        cx, cy = el.points[0]
        msp.add_circle(
            center=(cx + origin_x, cy + origin_y),
            radius=el.radius,
            dxfattribs=attribs,
        )
    elif el.kind == "rect" and len(el.points) >= 2:
        (x0, y0), (x1, y1) = el.points[0], el.points[1]
        pts = [
            (x0 + origin_x, y0 + origin_y),
            (x1 + origin_x, y0 + origin_y),
            (x1 + origin_x, y1 + origin_y),
            (x0 + origin_x, y1 + origin_y),
        ]
        msp.add_polyline2d(pts, close=True, dxfattribs=attribs)


def geometry_to_dxf(
    centerline: GeometryCollection,
    male_offset_mm: float = 0.10,
    pocket_offset_mm: float = 0.10,
) -> Drawing:
    """Build an ezdxf Drawing with three layers from a GeometryCollection.

    Returns the Drawing object (call ``.saveas(path)`` or stream with
    ``doc.write()``).
    """
    doc = ezdxf.new("R12")
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("CENTERLINE", color=_CLR_CENTERLINE)
    doc.layers.add("MALE_CUT", color=_CLR_MALE)
    doc.layers.add("POCKET_CUT", color=_CLR_POCKET)

    ox = centerline.origin_x
    oy = centerline.origin_y

    # Centerline layer
    for el in centerline.elements:
        _add_element_to_msp(msp, el, "CENTERLINE", ox, oy)

    # Male cut (positive offset)
    male = offset_collection(centerline, male_offset_mm)
    for el in male.elements:
        _add_element_to_msp(msp, el, "MALE_CUT", ox, oy)

    # Pocket cut (negative offset)
    pocket = offset_collection(centerline, -pocket_offset_mm)
    for el in pocket.elements:
        _add_element_to_msp(msp, el, "POCKET_CUT", ox, oy)

    return doc


def geometry_to_dxf_bytes(
    centerline: GeometryCollection,
    male_offset_mm: float = 0.10,
    pocket_offset_mm: float = 0.10,
) -> bytes:
    """Convenience: return the DXF as raw bytes for HTTP streaming."""
    doc = geometry_to_dxf(centerline, male_offset_mm, pocket_offset_mm)
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("ascii", errors="replace")
