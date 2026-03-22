"""
BACKEND-001: Generic curve → DXF export for CurveLab and similar tools.

POST /api/export/curve-dxf
"""

from __future__ import annotations

import io
import re
from typing import List

import ezdxf
from ezdxf import units
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["export", "curve"])


class CurvePoint(BaseModel):
    x: float
    y: float


class CurveItem(BaseModel):
    points: List[CurvePoint] = Field(..., min_length=2)
    label: str = "curve"


class CurveExportRequest(BaseModel):
    curves: List[CurveItem] = Field(..., min_length=1)
    scale_mm_per_unit: float = Field(1.0, gt=0, description="Multiply canvas units by this to get mm.")
    filename: str = Field("curve_export", max_length=200, description="Base name for download (no path).")


def _sanitize_layer(name: str, fallback: str) -> str:
    s = (name or "").strip() or fallback
    s = re.sub(r'[<>/\\":;?*|=`]', "_", s)
    if not s:
        s = fallback
    return s[:255]


def _safe_filename(name: str) -> str:
    base = re.sub(r'[^\w.\-]+', "_", (name or "").strip() or "curve_export")
    if base.lower().endswith(".dxf"):
        return base
    return f"{base}.dxf"


def build_curve_dxf(req: CurveExportRequest) -> ezdxf.document.Drawing:
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = units.MM
    msp = doc.modelspace()
    scale = req.scale_mm_per_unit

    existing_layers = {ly.dxf.name for ly in doc.layers}
    for idx, curve in enumerate(req.curves):
        pts = [(p.x * scale, p.y * scale) for p in curve.points]
        layer = _sanitize_layer(curve.label, f"CURVE_{idx}")
        if layer not in existing_layers:
            doc.layers.add(layer, color=(idx % 6) + 1)
            existing_layers.add(layer)

        if len(pts) >= 4:
            msp.add_spline([(x, y, 0.0) for x, y in pts], dxfattribs={"layer": layer})
        else:
            msp.add_lwpolyline(pts, close=False, dxfattribs={"layer": layer})

    return doc


@router.post("/curve-dxf")
def export_curve_dxf(req: CurveExportRequest) -> StreamingResponse:
    """Build a DXF with one layer per curve; 4+ points use SPLINE, fewer use open LWPOLYLINE."""
    try:
        doc = build_curve_dxf(req)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"DXF build error: {e}") from e

    text_buf = io.StringIO()
    doc.write(text_buf)
    binary_content = doc.encode(text_buf.getvalue())
    buf = io.BytesIO(binary_content)
    buf.seek(0)

    fname = _safe_filename(req.filename)
    return StreamingResponse(
        buf,
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
