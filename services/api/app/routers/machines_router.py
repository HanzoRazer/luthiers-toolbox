"""Machine Profiles Router

Manages CNC machine profiles for the CAM system.
Part of Art Studio v16.1 integration.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cam/machines", tags=["cam", "machines"])


class MachineProfile(BaseModel):
    id: str
    name: str
    max_feed_xy: Optional[float] = Field(
        None, description="Max cutting feed in XY (units/min)."
    )
    rapid: Optional[float] = Field(
        None, description="Rapid traverse feed (units/min)."
    )
    accel: Optional[float] = Field(
        None, description="Acceleration (mm/s^2)."
    )
    jerk: Optional[float] = Field(
        None, description="Jerk (mm/s^3)."
    )
    safe_z_default: Optional[float] = Field(
        None, description="Default safe Z height."
    )


# Minimal in-memory demos for alpha
_DEMO_MACHINES: List[MachineProfile] = [
    MachineProfile(
        id="grbl_desktop",
        name="GRBL Desktop Router (generic)",
        max_feed_xy=1800.0,
        rapid=3000.0,
        accel=500.0,
        jerk=1500.0,
        safe_z_default=5.0,
    ),
    MachineProfile(
        id="haas_minimill_mm",
        name="Haas MiniMill (metric)",
        max_feed_xy=6000.0,
        rapid=10000.0,
        accel=1200.0,
        jerk=3000.0,
        safe_z_default=10.0,
    ),
    MachineProfile(
        id="GUITAR_CNC_01",
        name="Guitar CNC Router (custom)",
        max_feed_xy=2000.0,
        rapid=4000.0,
        accel=600.0,
        jerk=1800.0,
        safe_z_default=5.0,
    ),
]


@router.get("", response_model=List[MachineProfile])
def list_machines() -> List[MachineProfile]:
    """
    List available machine profiles.

    Stub implementation returning a static set for development/alpha.
    """
    return _DEMO_MACHINES


@router.get("/{machine_id}", response_model=MachineProfile)
def get_machine(machine_id: str) -> MachineProfile:
    """
    Get a single machine profile by ID.
    """
    for m in _DEMO_MACHINES:
        if m.id == machine_id:
            return m
    raise HTTPException(status_code=404, detail="Machine not found")
