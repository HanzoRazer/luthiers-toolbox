"""
DXF Export Router for Luthier's Tool Box
Provides endpoints to export polylines and bi-arc curves to DXF format
Supports both ezdxf (preferred) and ASCII R12 fallback
Includes export history tracking and DXF comment stamping

Migrated from legacy ./server/dxf_exports_router.py
"""

from fastapi import APIRouter, Response, HTTPException, Query
from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone
import json

from ..exports.dxf_helpers import (
    write_polyline_ascii,
    write_arc_ascii,
    build_ascii_r12,
    try_build_with_ezdxf
)
from ..exports.curvemath_biarc import biarc_entities
from ..exports.history_store import (
    start_entry,
    write_file,
    write_text,
    finalize,
    list_entries,
    read_meta,
    file_bytes,
    get_units,
    get_version,
    get_git_sha
)

router = APIRouter(prefix="/exports", tags=["DXF Exports"])


# ============================================================================
# Helper Functions
# ============================================================================

def _utc_now_iso() -> str:
    """Generate UTC timestamp in ISO 8601 format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _comment_stamp(extra: str = "") -> str:
    """Generate DXF comment header with ToolBox version, Git SHA, timestamp, and units"""
    parts = [
        f"# {get_version()}",
        f"# Git: {get_git_sha()}",
        f"# UTC: {_utc_now_iso()}",
        f"# Units: {get_units()}",
    ]
    if extra:
        parts.append(extra)
    return " | ".join(parts)


# ============================================================================
# Request Models
# ============================================================================

class PolyLine(BaseModel):
    """Polyline defined by a sequence of 2D points"""
    points: List[Tuple[float, float]]


class PolyDXFReq(BaseModel):
    """Request to export a polyline to DXF format"""
    polyline: PolyLine
    layer: str = "CURVE"
    layers: Optional[Dict[str, str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "polyline": {
                    "points": [[0, 0], [100, 0], [100, 50], [0, 50]]
                },
                "layer": "PICKUP_CAVITY",
                "layers": {"CURVE": "PICKUP_CAVITY"}
            }
        }


class BiarcDXFReq(BaseModel):
    """Request to export a bi-arc blend to DXF format"""
    p0: Tuple[float, float]
    t0: Tuple[float, float]
    p1: Tuple[float, float]
    t1: Tuple[float, float]
    layer: str = "CURVE"
    layers: Optional[Dict[str, str]] = None
    arcs: Optional[List[dict]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "p0": [0, 0],
                "t0": [1, 0],
                "p1": [100, 50],
                "t1": [0, 1],
                "layer": "NECK_TRANSITION",
                "layers": {"ARC": "NECK_ARC", "CURVE": "NECK_LINE"}
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/polyline_dxf",
    summary="Export polyline to DXF",
    description="Export a polyline to DXF R12 format for CAM software.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/dxf": {}},
            "description": "DXF file ready for download"
        }
    }
)
def export_polyline_dxf(req: PolyDXFReq):
    """Export a polyline to DXF format with history tracking"""
    pts = req.polyline.points
    comment_extra = f"# POLYLINE VERTS={len(pts)}"
    comment = _comment_stamp(comment_extra)

    ez = try_build_with_ezdxf([
        ('polyline', {
            'points': pts,
            'layer': req.layer,
            'comment': comment
        })
    ])

    if ez is not None:
        data = ez
    else:
        entities = [write_polyline_ascii(pts, layer=req.layer)]
        data = build_ascii_r12(entities, comment=comment)

    entry = start_entry("polyline", {
        "verts": len(pts),
        "layer": req.layer or "CURVE"
    })
    write_file(entry, "polyline.dxf", data)

    summary = {
        "mode": "polyline",
        "created_utc": _utc_now_iso(),
        "verts": len(pts),
        "layer": req.layer,
        "points": pts
    }
    write_text(entry, "summary.json", json.dumps(summary, indent=2))
    finalize(entry)

    return Response(
        content=data,
        media_type="application/dxf",
        headers={
            "Content-Disposition": "attachment; filename=polycurve.dxf",
            "X-Export-Id": entry["id"]
        }
    )


@router.post(
    "/biarc_dxf",
    summary="Export bi-arc blend to DXF",
    description="Export a bi-arc G1-continuous curve blend to DXF R12 format.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/dxf": {}},
            "description": "DXF file with arc entities"
        }
    }
)
def export_biarc_dxf(req: BiarcDXFReq):
    """Export a bi-arc blend to DXF format with history tracking"""
    ents = biarc_entities(req.p0, req.t0, req.p1, req.t1)

    arc_radii = [e.get("radius", 0.0) for e in ents if e.get("type") == "arc"]
    min_r = min(arc_radii) if arc_radii else 0.0
    max_r = max(arc_radii) if arc_radii else 0.0
    line_count = len([e for e in ents if e.get("type") == "line"])

    counts = f"# BIARC: arcs={len(arc_radii)}, lines={line_count}, minR={min_r:.6f}, maxR={max_r:.6f}"
    comment = _comment_stamp(counts)

    ez_payload = []
    ascii_entities = []

    for e in ents:
        if e['type'] == 'arc':
            ez_payload.append(('arc', {
                'center': e['center'],
                'radius': e['radius'],
                'start_angle': e['start_angle'],
                'end_angle': e['end_angle'],
                'layer': req.layer,
                'comment': comment
            }))
            ascii_entities.append(write_arc_ascii(
                e['center'],
                e['radius'],
                e['start_angle'],
                e['end_angle'],
                layer=req.layer
            ))
        elif e['type'] == 'line':
            pts = [e['A'], e['B']]
            ez_payload.append(('polyline', {
                'points': pts,
                'layer': req.layer,
                'comment': comment
            }))
            ascii_entities.append(write_polyline_ascii(pts, layer=req.layer))

    ez = try_build_with_ezdxf(ez_payload)
    if ez is not None:
        data = ez
    else:
        data = build_ascii_r12(ascii_entities, comment=comment)

    entry = start_entry("biarc", {
        "layer": req.layer or "ARC",
        "arcs": len(arc_radii),
        "lines": line_count,
        "min_radius": min_r,
        "max_radius": max_r
    })
    write_file(entry, "biarc.dxf", data)

    summary = {
        "mode": "biarc",
        "created_utc": _utc_now_iso(),
        "counts": {
            "arcs": len(arc_radii),
            "lines": line_count
        },
        "min_radius": min_r,
        "max_radius": max_r,
        "radii": arc_radii,
        "entities": ents
    }
    write_text(entry, "summary.json", json.dumps(summary, indent=2))
    finalize(entry)

    return Response(
        content=data,
        media_type="application/dxf",
        headers={
            "Content-Disposition": "attachment; filename=biarc.dxf",
            "X-Export-Id": entry["id"]
        }
    )


# ============================================================================
# Export History Endpoints
# ============================================================================

@router.get(
    "/history",
    summary="List recent export history",
    description="Retrieve a list of recent DXF/SVG exports with metadata."
)
def history(limit: int = Query(50, ge=1, le=250, description="Max entries to return")):
    """List recent export entries"""
    return {"items": list_entries(limit=limit)}


@router.get(
    "/history/{entry_id}",
    summary="Get export metadata by ID",
    description="Retrieve metadata for a specific export entry."
)
def history_entry(entry_id: str):
    """Read metadata for specific export"""
    try:
        return read_meta(entry_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Export entry {entry_id} not found")


@router.get(
    "/history/{entry_id}/file/{filename}",
    summary="Download file from export history",
    description="Download a specific file from an export entry."
)
def history_file(entry_id: str, filename: str):
    """Read file from export entry"""
    try:
        data = file_bytes(entry_id, filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File {filename} not found in entry {entry_id}")

    mt = "application/octet-stream"
    if filename.endswith(".json"):
        mt = "application/json"
    elif filename.endswith(".dxf"):
        mt = "application/dxf"
    elif filename.endswith(".md"):
        mt = "text/markdown"
    elif filename.endswith(".svg"):
        mt = "image/svg+xml"

    return Response(
        content=data,
        media_type=mt,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/dxf/health",
    summary="Check DXF export capabilities",
    tags=["health"]
)
def dxf_health():
    """Check if ezdxf is available for native DXF export"""
    try:
        import ezdxf
        return {
            "status": "healthy",
            "ezdxf_version": ezdxf.__version__,
            "formats": ["ezdxf (native)", "ASCII R12 (fallback)"],
            "history_enabled": True
        }
    except ImportError:
        return {
            "status": "healthy",
            "ezdxf_version": None,
            "formats": ["ASCII R12 (fallback only)"],
            "history_enabled": True,
            "note": "Install ezdxf for better DXF compatibility: pip install ezdxf>=1.1"
        }
