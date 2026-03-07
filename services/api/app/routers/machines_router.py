"""
Machine Profiles Router

Manages CNC machine profiles for the CAM system.
WIRED to machine_profiles.json via machines_consolidated_router.

Endpoints:
    GET  /cam/machines           - List all machine profiles (simplified)
    GET  /cam/machines/{machine_id} - Get specific machine profile
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .machines_consolidated_router import _load_profiles


router = APIRouter(prefix="/cam/machines", tags=["cam", "machines"])


class MachineProfile(BaseModel):
    """Simplified machine profile for CAM integration."""
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


def _convert_profile(profile: dict) -> MachineProfile:
    """Convert full machine profile to simplified CAM profile."""
    limits = profile.get("limits", {})
    axes = profile.get("axes", {})
    travel = axes.get("travel_mm", [0, 0, 0])
    
    # Default safe_z to 10% of Z travel or 5.0mm, whichever is smaller
    z_travel = travel[2] if len(travel) > 2 else 50.0
    safe_z = min(z_travel * 0.1, 5.0)
    
    return MachineProfile(
        id=profile.get("id", ""),
        name=profile.get("title", profile.get("id", "Unknown")),
        max_feed_xy=limits.get("feed_xy"),
        rapid=limits.get("rapid"),
        accel=limits.get("accel"),
        jerk=limits.get("jerk"),
        safe_z_default=safe_z,
    )


@router.get("", response_model=List[MachineProfile])
def list_machines() -> List[MachineProfile]:
    """
    List available machine profiles (from machine_profiles.json).
    """
    profiles = _load_profiles()
    return [_convert_profile(p) for p in profiles]


@router.get("/{machine_id}", response_model=MachineProfile)
def get_machine(machine_id: str) -> MachineProfile:
    """
    Get a single machine profile by ID.
    """
    profiles = _load_profiles()
    for p in profiles:
        if p.get("id") == machine_id:
            return _convert_profile(p)
    raise HTTPException(status_code=404, detail="Machine not found")
