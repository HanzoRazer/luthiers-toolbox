import json
from typing import Dict, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from .sim_validate import (
    DEFAULT_ACCEL,
    DEFAULT_CLEAR_Z,
    DEFAULT_ENVELOPE,
    csv_export,
    simulate,
)

router = APIRouter(prefix="/cam", tags=["cam-sim"])


class SimInput(BaseModel):
    gcode: str = Field(..., description="Raw G-code to simulate")
    as_csv: Optional[bool] = False
    accel: Optional[float] = DEFAULT_ACCEL
    clearance_z: Optional[float] = DEFAULT_CLEAR_Z
    envelope: Optional[Dict[str, tuple]] = DEFAULT_ENVELOPE


@router.post("/simulate_gcode")
def simulate_gcode(body: SimInput) -> Response:
    sim = simulate(body.gcode, accel=body.accel or DEFAULT_ACCEL,
                   clearance_z=body.clearance_z or DEFAULT_CLEAR_Z,
                   env=body.envelope or DEFAULT_ENVELOPE)
    if body.as_csv:
        data = csv_export(sim)
        return Response(content=data, media_type="text/csv",
                        headers={"Content-Disposition": 'attachment; filename="simulation.csv"'})
    hdr = {"X-CAM-Summary": json.dumps(sim['summary']),
           "X-CAM-Modal": json.dumps(sim['modal'])}
    return Response(content=json.dumps({'issues': sim['issues'], 'moves': sim['moves']}),
                    media_type="application/json", headers=hdr)
