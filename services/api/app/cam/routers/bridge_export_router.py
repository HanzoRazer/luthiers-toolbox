"""
Bridge Export Router

Bridge DXF export endpoint for generating bridge saddle geometry.
Extracted from stub_routes.py during decomposition.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel


router = APIRouter(tags=["cam", "bridge"])


class BridgeGeometryIn(BaseModel):
    """Bridge geometry payload from frontend BridgeModel."""
    units: str = "mm"
    scaleLength: float
    stringSpread: float
    compTreble: float
    compBass: float
    slotWidth: float
    slotLength: float
    angleDeg: float
    endpoints: Dict[str, Dict[str, float]]
    slotPolygon: List[Dict[str, float]]


class BridgeDxfRequest(BaseModel):
    """Request payload for bridge DXF export."""
    geometry: BridgeGeometryIn
    filename: Optional[str] = None


def _build_bridge_dxf(geom: BridgeGeometryIn, meta: str = "") -> str:
    """
    Build DXF R12 content from bridge geometry.

    Layers:
    - SADDLE: Centerline from treble to bass endpoint
    - SLOT: 4 LINE entities forming closed slot rectangle
    - REFERENCE: Scale length reference line
    """
    out: List[str] = ["0", "SECTION", "2", "ENTITIES"]

    # Saddle centerline (LAYER: SADDLE)
    ep = geom.endpoints
    treble = ep.get("treble", {})
    bass = ep.get("bass", {})
    tx, ty = treble.get("x", 0), treble.get("y", 0)
    bx, by = bass.get("x", 0), bass.get("y", 0)
    out += [
        "0", "LINE", "8", "SADDLE",
        "10", str(tx), "20", str(ty), "30", "0",
        "11", str(bx), "21", str(by), "31", "0",
    ]

    # Slot polygon (LAYER: SLOT)
    poly = geom.slotPolygon
    if len(poly) >= 4:
        for i in range(len(poly)):
            p1, p2 = poly[i], poly[(i + 1) % len(poly)]
            x1, y1 = p1.get("x", 0), p1.get("y", 0)
            x2, y2 = p2.get("x", 0), p2.get("y", 0)
            out += [
                "0", "LINE", "8", "SLOT",
                "10", str(x1), "20", str(y1), "30", "0",
                "11", str(x2), "21", str(y2), "31", "0",
            ]

    # Reference line at scale length position (LAYER: REFERENCE)
    ref_y_min = -geom.stringSpread / 2 - 5
    ref_y_max = geom.stringSpread / 2 + 5
    out += [
        "0", "LINE", "8", "REFERENCE",
        "10", str(geom.scaleLength), "20", str(ref_y_min), "30", "0",
        "11", str(geom.scaleLength), "21", str(ref_y_max), "31", "0",
    ]

    out += ["0", "ENDSEC", "0", "EOF"]
    txt = chr(10).join(out)

    if meta:
        return "999" + chr(10) + meta + chr(10) + txt
    return txt


@router.post("/bridge/export_dxf", response_class=Response)
def export_bridge_dxf(body: BridgeDxfRequest) -> Response:
    """
    Export bridge saddle geometry to DXF R12 format.

    Returns a downloadable DXF file with layers:
    - SADDLE: Bridge saddle centerline
    - SLOT: Bridge slot outline (4-sided polygon)
    - REFERENCE: Scale length reference line
    """
    geom = body.geometry

    meta = f"(BRIDGE;SCALE={geom.scaleLength};SPREAD={geom.stringSpread};CT={geom.compTreble};CB={geom.compBass};UNITS={geom.units})"
    dxf_content = _build_bridge_dxf(geom, meta)

    filename = body.filename or f"bridge_{geom.scaleLength}_{geom.units}"
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")[:64] or "bridge_export"

    return Response(
        content=dxf_content,
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}.dxf"'},
    )
