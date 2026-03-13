"""
CAM Simulation Routers (Consolidated)
=====================================

G-code simulation and validation.

Consolidated from:
    - gcode_sim_router.py (1 route)
    - upload_router.py (1 route)

Total: 2 routes under /api/cam/simulation

Endpoints:
    POST /simulate_gcode    - Simulate G-code and return moves/issues
    POST /upload            - Upload and simulate G-code file
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from ....routers.sim_validate import (
    DEFAULT_ACCEL,
    DEFAULT_CLEAR_Z,
    DEFAULT_ENVELOPE,
    csv_export,
    simulate,
)

router = APIRouter()


# ===========================================================================
# G-code Simulation (from gcode_sim_router.py)
# ===========================================================================

class SimInput(BaseModel):
    gcode: str = Field(..., description="Raw G-code to simulate")
    as_csv: Optional[bool] = False
    accel: Optional[float] = DEFAULT_ACCEL
    clearance_z: Optional[float] = DEFAULT_CLEAR_Z
    envelope: Optional[Dict[str, tuple]] = DEFAULT_ENVELOPE


@router.post("/simulate_gcode")
def simulate_gcode(body: SimInput) -> Response:
    """Simulate G-code and return moves/issues."""
    sim = simulate(
        body.gcode,
        accel=body.accel or DEFAULT_ACCEL,
        clearance_z=body.clearance_z or DEFAULT_CLEAR_Z,
        env=body.envelope or DEFAULT_ENVELOPE
    )
    if body.as_csv:
        data = csv_export(sim)
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="simulation.csv"'}
        )
    hdr = {
        "X-CAM-Summary": json.dumps(sim['summary']),
        "X-CAM-Modal": json.dumps(sim['modal'])
    }
    return Response(
        content=json.dumps({'issues': sim['issues'], 'moves': sim['moves']}),
        media_type="application/json",
        headers=hdr
    )


# ===========================================================================
# Upload Simulation (from upload_router.py)
# ===========================================================================

def _parse_gcode_lines(text: str) -> List[Dict[str, Any]]:
    """Minimal G-code parser: detect motion codes and XYZ moves."""
    lines = text.splitlines()
    moves: List[Dict[str, Any]] = []
    x = y = z = f = None
    pattern = re.compile(r"([XYZF])([-+]?\d*\.?\d+)")

    for line in lines:
        code = line.strip().split(" ")[0].upper()
        if not code or code.startswith("("):
            continue

        if code in {"G0", "G00", "G1", "G01"}:
            params = {m[0]: float(m[1]) for m in pattern.findall(line)}
            x = params.get("X", x)
            y = params.get("Y", y)
            z = params.get("Z", z)
            f = params.get("F", f)
            moves.append({"code": code[:2], "x": x, "y": y, "z": z, "f": f})

    return moves


@router.post("/upload")
async def simulate_gcode_upload(
    file: UploadFile = File(...),
    units: str = Form("mm")
) -> Dict[str, Any]:
    """
    Accepts a G-code file upload, parses basic motion, returns path and simple statistics.
    """
    try:
        text = (await file.read()).decode("utf-8", errors="ignore")
    except (UnicodeDecodeError, IOError) as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {exc}") from exc

    moves = _parse_gcode_lines(text)
    if not moves:
        raise HTTPException(status_code=400, detail="No motion commands found in file")

    # Simple length/time stats
    length_mm = 0.0
    last = None
    for m in moves:
        if last and None not in (last.get("x"), last.get("y"), m.get("x"), m.get("y")):
            dx = m["x"] - last["x"]
            dy = m["y"] - last["y"]
            length_mm += (dx ** 2 + dy ** 2) ** 0.5
        last = m

    return {
        "ok": True,
        "units": units,
        "move_count": len(moves),
        "length_mm": length_mm,
        "time_s": round(length_mm / 100.0, 2),
        "moves": moves,
        "issues": [],
    }


__all__ = ["router"]
