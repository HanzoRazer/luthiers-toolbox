"""
CAM V-Carve Router

V-carve infill preview generation (raster and contour modes) and G-code generation.

Migrated from: routers/cam_vcarve_router.py
G-code endpoint moved from: art_studio/vcarve_router.py (Art Studio Scope Gate compliance)

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /preview_infill    - Generate infill preview SVG (UTILITY)
    POST /gcode             - Generate VCarve G-code (OPERATION)
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    import pyclipper

    HAVE_PYCLIPPER = True
except ImportError:
    HAVE_PYCLIPPER = False

try:
    from shapely.affinity import rotate as shp_rotate
    from shapely.affinity import translate as shp_translate
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union

    HAVE_SHAPELY = True
except ImportError:
    HAVE_SHAPELY = False

# Imports for /gcode OPERATION endpoint
from ....toolpath.vcarve_toolpath import (
    VCarveToolpathParams,
    svg_to_naive_gcode,
)
from ....rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)
from ....rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ....rmos.policies import SafetyPolicy

router = APIRouter()

Point = Tuple[float, float]


class PreviewReq(BaseModel):
    mode: str  # 'raster' or 'contour'
    polygons: Optional[List[List[Point]]] = None
    centerlines_svg: Optional[str] = None
    approx_stroke_width_mm: Optional[float] = None
    raster_angle_deg: float = 0.0
    flat_stepover_mm: float = 1.2


def _parse_svg_polylines(svg: str) -> List[List[Tuple[float, float]]]:
    pl = []
    for m in re.finditer(r'<poly(?:line|gon)[^>]*points="([^"]+)"', svg, re.IGNORECASE):
        pts_str = m.group(1).strip()
        pts = []
        for token in re.split(r"\s+", pts_str):
            if not token:
                continue
            if "," in token:
                x, y = token.split(",", 1)
            else:
                parts = token.split()
                if len(parts) != 2:
                    continue
                x, y = parts
            try:
                pts.append((float(x), float(y)))
            except ValueError:  # WP-1: narrowed from except Exception
                pass
        if pts:
            pl.append(pts)
    return pl


def _polylines_to_svg(
    polylines: List[List[Tuple[float, float]]],
    stroke: str = "royalblue",
    stroke_width: float = 0.6,
) -> str:
    xs, ys = [], []
    for poly in polylines:
        for x, y in poly:
            xs.append(x)
            ys.append(y)
    if not xs:
        xs = [0, 1]
        ys = [0, 1]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    w = max(1.0, maxx - minx)
    h = max(1.0, maxy - miny)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx} {miny} {w} {h}">'
    ]
    for poly in polylines:
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in poly)
        parts.append(
            f'<polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _estimate_len(polylines: List[List[Tuple[float, float]]]) -> float:
    tot = 0.0
    for pl in polylines:
        for (x1, y1), (x2, y2) in zip(pl, pl[1:]):
            dx, dy = x2 - x1, y2 - y1
            tot += math.hypot(dx, dy)
    return tot


@router.post("/preview_infill")
def preview_infill(req: PreviewReq) -> Dict[str, Any]:
    regions = req.polygons or []
    if (
        not regions
        and req.centerlines_svg
        and req.approx_stroke_width_mm
        and HAVE_PYCLIPPER
    ):
        delta = req.approx_stroke_width_mm / 2.0
        co = pyclipper.PyclipperOffset(miterLimit=2.0, arcTolerance=0.25)
        for pl in _parse_svg_polylines(req.centerlines_svg):
            co.AddPath(
                [(x, y) for x, y in pl], pyclipper.JT_ROUND, pyclipper.ET_OPENROUND
            )
        out = co.Execute(delta)
        regions = [[(float(x), float(y)) for x, y in path] for path in out]

    if not regions:
        return {
            "ok": True,
            "svg": "<svg xmlns='http://www.w3.org/2000/svg'/>",
            "stats": {"total_spans": 0, "total_len": 0.0},
        }

    if not HAVE_SHAPELY:
        raise HTTPException(
            status_code=500, detail="Shapely required for preview. pip install shapely"
        )

    union = unary_union([Polygon(p) for p in regions if len(p) >= 3])

    polylines: List[List[Tuple[float, float]]] = []
    if req.mode == "raster":
        angle = float(req.raster_angle_deg or 0.0)
        rot = shp_rotate(union, -angle, origin=(0, 0), use_radians=False)
        minx, miny, maxx, maxy = rot.bounds
        tx, ty = -minx + 1.0, -miny + 1.0
        rot = shp_translate(rot, xoff=tx, yoff=ty)
        y = rot.bounds[1]
        while y <= rot.bounds[3]:
            seg = rot.intersection(
                LineString([(rot.bounds[0] - 1, y), (rot.bounds[2] + 1, y)])
            )
            geoms = getattr(seg, "geoms", [seg])
            for g in geoms:
                coords = list(g.coords)
                if len(coords) >= 2:
                    from shapely.affinity import rotate, translate

                    ls = LineString(coords)
                    ls = translate(ls, xoff=-tx, yoff=-ty)
                    ls = rotate(ls, angle, origin=(0, 0), use_radians=False)
                    polylines.append(list(ls.coords))
            y += max(0.1, req.flat_stepover_mm)
    else:
        if not HAVE_PYCLIPPER:
            raise HTTPException(
                status_code=500,
                detail="pyclipper required for contour infill. pip install pyclipper",
            )
        cur = [
            list(poly.exterior.coords)[:-1]
            for poly in ([union] if union.geom_type == "Polygon" else union.geoms)
        ]
        while cur:
            for ring in cur:
                polylines.append([(float(x), float(y)) for x, y in ring])
            co = pyclipper.PyclipperOffset(miterLimit=2.0, arcTolerance=0.25)
            for ring in cur:
                co.AddPath(
                    [(x, y) for x, y in ring],
                    pyclipper.JT_ROUND,
                    pyclipper.ET_CLOSEDPOLYGON,
                )
            nxt = co.Execute(-max(0.1, req.flat_stepover_mm))
            cur = [[(float(x), float(y)) for x, y in path] for path in nxt]

    svg = _polylines_to_svg(polylines)
    stats = {"total_spans": len(polylines), "total_len": _estimate_len(polylines)}
    return {"ok": True, "svg": svg, "stats": stats}


# --------------------------------------------------------------------- #
# /gcode OPERATION Endpoint (moved from Art Studio)
# --------------------------------------------------------------------- #


class VCarveGCodeRequest(BaseModel):
    """Request model for VCarve G-code generation."""

    svg: str = Field(..., description="SVG document as text")
    bit_angle_deg: float = Field(
        default=60.0, ge=10.0, le=180.0, description="V-bit angle in degrees"
    )
    depth_mm: float = Field(
        default=1.5, ge=0.1, le=10.0, description="Cutting depth in mm"
    )
    safe_z_mm: float = Field(
        default=5.0, ge=1.0, le=50.0, description="Safe Z height for rapids"
    )
    feed_rate_mm_min: float = Field(
        default=800.0, ge=100.0, le=5000.0, description="Cutting feed rate in mm/min"
    )
    plunge_rate_mm_min: float = Field(
        default=300.0, ge=50.0, le=2000.0, description="Plunge feed rate in mm/min"
    )
    tool_id: Optional[str] = Field(
        default="vcarve:default", description="Tool identifier for feasibility lookup"
    )
    material_id: Optional[str] = Field(
        default=None, description="Material identifier for feasibility assessment"
    )


class VCarveGCodeResponse(BaseModel):
    """Response model for VCarve G-code generation."""

    gcode: str = Field(..., description="Generated G-code")
    run_id: Optional[str] = Field(None, description="Run artifact ID for audit trail")
    hashes: Optional[Dict[str, str]] = Field(
        None, description="SHA256 hashes for provenance"
    )


@router.post("/gcode", response_model=VCarveGCodeResponse)
async def generate_vcarve_gcode(req: VCarveGCodeRequest) -> Dict[str, Any]:
    """
    Generate G-code from SVG for VCarve operations.

    LANE: OPERATION - Creates vcarve_gcode_execution or vcarve_gcode_blocked artifact.

    Flow:
    1. Validate SVG input
    2. Recompute feasibility server-side (NEVER trust client)
    3. Block if RED/UNKNOWN (HTTP 409)
    4. Generate G-code if safe
    5. Persist run artifact for audit trail
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump())
    tool_id = req.tool_id or "vcarve:default"

    if not req.svg.strip():
        # Create ERROR artifact for empty SVG
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_execution",
            status="ERROR",
            request_hash=request_hash,
            errors=["SVG text is empty"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "EMPTY_SVG",
                "run_id": run_id,
                "message": "SVG text is empty.",
            },
        )

    # Phase 2: Server-side feasibility enforcement
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req={
            "tool_id": tool_id,
            "material_id": req.material_id,
            "depth_mm": req.depth_mm,
            "bit_angle_deg": req.bit_angle_deg,
            "feed_rate_mm_min": req.feed_rate_mm_min,
        },
        context="vcarve_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    # Block if policy requires (BLOCKED artifact)
    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_blocked",
            status="BLOCKED",
            feasibility=feasibility,
            request_hash=feas_hash,
            notes=f"Blocked by safety policy: {risk_level}",
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "V-Carve G-code generation blocked by server-side safety policy.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    try:
        params = VCarveToolpathParams(
            bit_angle_deg=req.bit_angle_deg,
            depth_mm=req.depth_mm,
            safe_z_mm=req.safe_z_mm,
            feed_rate_mm_min=req.feed_rate_mm_min,
            plunge_rate_mm_min=req.plunge_rate_mm_min,
        )

        gcode = svg_to_naive_gcode(req.svg, params)

        # Hash outputs for provenance
        gcode_hash = sha256_of_text(gcode)

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_execution",
            status="OK",
            feasibility=feasibility,
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        return {
            "gcode": gcode,
            "run_id": run_id,
            "hashes": {
                "request_sha256": request_hash,
                "feasibility_sha256": feas_hash,
                "gcode_sha256": gcode_hash,
            },
        }

    except HTTPException:
        raise  # WP-1: pass through
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        # Create ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_execution",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "GCODE_GENERATION_ERROR",
                "run_id": run_id,
                "message": f"G-code generation failed: {str(e)}",
            },
        )
