"""
RMOS MVP Router

MVP wrapper endpoints for DXF-to-GRBL conversion.
Extracted from stub_routes.py during decomposition.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, UploadFile

from .runs_v2.attachments import put_bytes_attachment, put_json_attachment
from .runs_v2.schemas import RunAttachment


router = APIRouter(tags=["rmos", "mvp"])


@router.post("/wrap/mvp/dxf-to-grbl")
async def dxf_to_grbl(
    file: UploadFile = File(...),
    tool_d: float = Form(6.0),
    stepover: float = Form(0.4),
    stepdown: float = Form(2.0),
    z_rough: float = Form(-3.0),
    feed_xy: float = Form(1000.0),
    feed_z: float = Form(300.0),
    rapid: float = Form(3000.0),
    safe_z: float = Form(10.0),
    strategy: str = Form("Spiral"),
    layer_name: str = Form("0"),
    climb: bool = Form(True),
    smoothing: bool = Form(False),
    margin: float = Form(0.0),
) -> Dict[str, Any]:
    """
    Convert DXF to GRBL G-code (MVP workflow).

    Wired to real DXF parsing + adaptive toolpath + G-code generation.
    Creates RMOS run artifact with full attachment persistence.
    """
    import ezdxf
    from ..routers.adaptive.plan_router import plan as compute_plan
    from ..routers.adaptive_schemas import Loop, PlanIn

    run_id = f"RUN-DXF-{uuid.uuid4().hex[:12].upper()}"
    attachments: List[RunAttachment] = []

    try:
        dxf_bytes = await file.read()
        dxf_sha = hashlib.sha256(dxf_bytes).hexdigest()

        dxf_att, _ = put_bytes_attachment(
            dxf_bytes,
            kind="dxf_input",
            mime="application/dxf",
            filename=file.filename or "input.dxf",
            ext=".dxf",
        )
        attachments.append(dxf_att)

        import tempfile
        import os as os_module
        fd, tmp_path = tempfile.mkstemp(suffix=".dxf")
        try:
            os_module.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(dxf_bytes)
            doc = ezdxf.readfile(tmp_path)
        finally:
            if os_module.path.exists(tmp_path):
                os_module.unlink(tmp_path)

        msp = doc.modelspace()
        loops: List[List[tuple]] = []

        for entity in msp:
            if entity.dxftype() == "LWPOLYLINE":
                if layer_name == "0" or entity.dxf.layer == layer_name:
                    pts = [(p[0], p[1]) for p in entity.get_points()]
                    if len(pts) >= 3:
                        if pts[0] != pts[-1]:
                            pts.append(pts[0])
                        loops.append(pts)
            elif entity.dxftype() == "POLYLINE":
                if layer_name == "0" or entity.dxf.layer == layer_name:
                    pts = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                    if len(pts) >= 3:
                        if pts[0] != pts[-1]:
                            pts.append(pts[0])
                        loops.append(pts)

        if not loops:
            return {
                "ok": False,
                "run_id": run_id,
                "gcode": None,
                "message": f"No closed polylines found on layer '{layer_name}'",
            }

        plan_in = PlanIn(
            loops=[Loop(pts=loop) for loop in loops],
            tool_d=tool_d,
            stepover=stepover,
            stepdown=stepdown,
            z_final=z_rough,
            feed=feed_xy,
            plunge=feed_z,
            rapid=rapid,
            safe_z=safe_z,
            strategy=strategy,
            climb=climb,
            smoothing=smoothing,
        )

        plan_result = compute_plan(plan_in)

        plan_att, _, plan_sha = put_json_attachment(
            plan_result,
            kind="cam_plan",
            filename="cam_plan.json",
        )
        attachments.append(plan_att)

        moves = plan_result.get("moves", [])
        gcode_lines = [
            "; DXF-to-GRBL MVP Export",
            f"; Run ID: {run_id}",
            f"; Tool: {tool_d}mm, Stepover: {stepover*100}%, Stepdown: {stepdown}mm",
            "G21 ; mm mode",
            "G90 ; absolute",
            f"G0 Z{safe_z}",
        ]

        for move in moves:
            cmd = move.get("cmd", "G1")
            x = move.get("x")
            y = move.get("y")
            z = move.get("z")
            f = move.get("f")

            parts = [cmd]
            if x is not None:
                parts.append(f"X{x:.3f}")
            if y is not None:
                parts.append(f"Y{y:.3f}")
            if z is not None:
                parts.append(f"Z{z:.3f}")
            if f is not None:
                parts.append(f"F{f:.0f}")
            gcode_lines.append(" ".join(parts))

        gcode_lines.extend([
            f"G0 Z{safe_z}",
            "M5 ; spindle off",
            "G0 X0 Y0",
            "M30 ; end",
        ])

        gcode_text = "\n".join(gcode_lines)

        gcode_att, _ = put_bytes_attachment(
            gcode_text.encode(),
            kind="gcode",
            mime="text/plain",
            filename=f"{run_id}.nc",
            ext=".nc",
        )
        gcode_sha = gcode_att.sha256
        attachments.append(gcode_att)

        return {
            "ok": True,
            "run_id": run_id,
            "gcode": {
                "inline": True,
                "text": gcode_text,
            },
            "decision": {
                "risk_level": "GREEN",
                "export_allowed": True,
            },
            "feasibility": {
                "rules_triggered": [],
            },
            "attachments": [a.model_dump() for a in attachments],
            "hashes": {
                "dxf_input": dxf_sha,
                "gcode": gcode_sha,
            },
            "mode": "mvp",
            "stats": plan_result.get("stats", {}),
        }

    except (ValueError, TypeError, KeyError, AttributeError, OSError, IndexError) as e:
        return {
            "ok": False,
            "run_id": run_id,
            "gcode": None,
            "message": f"DXF-to-GRBL conversion failed: {str(e)}",
        }
