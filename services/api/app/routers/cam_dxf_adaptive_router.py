# File: services/api/app/routers/cam_dxf_adaptive_router.py
# NEW – DXF → Adaptive Pocket → Toolpath helper

from __future__ import annotations

import io
from typing import Any, Dict

import ezdxf
import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

router = APIRouter(prefix="/cam", tags=["cam", "adaptive", "dxf"])


def _dxf_to_adaptive_request(
    dxf_bytes: bytes,
    tool_d: float,
    *,
    units: str = "mm",
    geometry_layer: str = "GEOMETRY",
    stepover: float = 0.45,
    stepdown: float = 2.0,
    margin: float = 0.5,
    strategy: str = "Spiral",
    feed_xy: float = 1200.0,
    safe_z: float = 5.0,
    z_rough: float = -1.5,
) -> Dict[str, Any]:
    """
    Convert DXF closed polylines on a given layer into an Adaptive Pocket request body.

    This matches the PlanIn model used by /api/cam/pocket/adaptive/plan.
    """
    try:
        data_stream = io.BytesIO(dxf_bytes)
        doc = ezdxf.read(data_stream)
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Failed to parse DXF: {exc}") from exc

    msp = doc.modelspace()
    loops = []

    # Extract LWPOLYLINE entities from geometry_layer
    query_str = f'LWPOLYLINE[layer=="{geometry_layer}"]'
    for entity in msp.query(query_str):
        if not entity.closed:
            # Ignore open polylines for now; could be warnings later
            continue
        pts = [(p[0], p[1]) for p in entity.get_points()]  # (x, y, [bulge, ...])
        if len(pts) >= 3:
            loops.append({"pts": pts})

    if not loops:
        raise HTTPException(
            status_code=400,
            detail=f"No closed polylines found on layer {geometry_layer!r}. "
                   f"Ensure your DXF has a GEOMETRY layer with closed loops.",
        )

    return {
        "loops": loops,
        "tool_d": float(tool_d),
        "units": units,
        "stepover": float(stepover),
        "stepdown": float(stepdown),
        "margin": float(margin),
        "strategy": strategy,
        "feed_xy": float(feed_xy),
        "safe_z": float(safe_z),
        "z_rough": float(z_rough),
    }


@router.post("/dxf_adaptive_plan_run")
async def dxf_adaptive_plan_run(
    request: Request,
    file: UploadFile = File(...),
    units: str = Form("mm"),
    tool_d: float = Form(...),
    geometry_layer: str = Form("GEOMETRY"),
    stepover: float = Form(0.45),
    stepdown: float = Form(2.0),
    margin: float = Form(0.5),
    strategy: str = Form("Spiral"),
    feed_xy: float = Form(1200.0),
    safe_z: float = Form(5.0),
    z_rough: float = Form(-1.5),
) -> Dict[str, Any]:
    """
    DXF → Adaptive Pocket → Toolpath

    1) Reads the uploaded DXF.
    2) Extracts closed polylines from geometry_layer.
    3) Builds an Adaptive Plan request.
    4) Forwards it internally to /api/cam/pocket/adaptive/plan.
    5) Returns the toolpath (moves, stats, overlays) to the caller.

    This allows the BridgeLab UI to go directly from DXF bridge geometry
    to a full adaptive pocket plan + backplot/time estimator.
    """
    try:
        dxf_bytes = await file.read()
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Failed to read DXF file: {exc}") from exc

    body = _dxf_to_adaptive_request(
        dxf_bytes=dxf_bytes,
        tool_d=tool_d,
        units=units,
        geometry_layer=geometry_layer,
        stepover=stepover,
        stepdown=stepdown,
        margin=margin,
        strategy=strategy,
        feed_xy=feed_xy,
        safe_z=safe_z,
        z_rough=z_rough,
    )

    base_url = str(request.base_url).rstrip("/")
    adaptive_url = f"{base_url}/api/cam/pocket/adaptive/plan"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(adaptive_url, json=body, timeout=30.0)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to call adaptive planner: {exc}",
            ) from exc

    if resp.status_code != 200:
        # Bubble up error details from adaptive endpoint
        try:
            detail = resp.json()
        except (ValueError, TypeError):  # WP-1: narrowed — JSON parse fallback
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)

    data = resp.json()
    # Expecting: { moves: [...], stats: {...}, overlays: [...] }
    return data
