"""
Drilling operations router (G81-G89 modal cycles).

Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Phase 5 Part 3: N.06 Modal Cycles
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..cam.modal_cycles import generate_drilling_gcode

router = APIRouter()


class Hole(BaseModel):
    """Single hole location."""
    x: float
    y: float


class DrillingIn(BaseModel):
    """Drilling operation parameters."""
    cycle: str = Field(..., description="Cycle type: G81, G83, G73, G84, G85")
    holes: List[Hole] = Field(..., description="Hole locations")
    depth: float = Field(..., description="Final Z depth (negative, e.g., -20.0)")
    retract: float = Field(default=2.0, description="R-plane for retract (positive)")
    feed: float = Field(default=300.0, description="Feed rate in mm/min")
    safe_z: float = Field(default=10.0, description="Safe Z height")
    
    # Optional parameters
    post_id: Optional[str] = Field(default=None, description="Post-processor ID")
    peck_depth: Optional[float] = Field(default=None, description="Peck depth for G83/G73 (mm)")
    thread_pitch: Optional[float] = Field(default=None, description="Thread pitch for G84 (mm)")
    spindle_rpm: Optional[float] = Field(default=None, description="Spindle RPM for G84")
    expand_cycles: bool = Field(default=False, description="Force expansion to G0/G1")
    
    # Units
    units: str = Field(default="mm", description="Units (mm or inch)")


class DrillingOut(BaseModel):
    """Drilling operation output."""
    gcode: str
    stats: Dict[str, Any]
    warnings: List[str] = []


@router.post("/drill/gcode", response_model=DrillingOut)
async def generate_drill_gcode(body: DrillingIn) -> DrillingOut:
    """
    Generate G-code for drilling operations.
    
    Supports cycles:
    - G81: Simple drill (rapid retract)
    - G83: Peck drill (full retract)
    - G73: Chip break (partial retract)
    - G84: Rigid tap
    - G85: Bore (feed retract)
    
    Auto-expands cycles to G0/G1 for hobby controllers (GRBL, TinyG).
    
    Example request:
    ```json
    {
      "cycle": "G83",
      "holes": [{"x": 10, "y": 10}, {"x": 20, "y": 10}],
      "depth": -20.0,
      "retract": 2.0,
      "feed": 300,
      "peck_depth": 5.0,
      "post_id": "GRBL"
    }
    ```
    """
    # Validate holes
    if not body.holes or len(body.holes) == 0:
        raise HTTPException(400, "At least one hole required")
    
    # Validate cycle-specific parameters
    warnings = []
    
    if body.cycle in ["G83", "G73"] and not body.peck_depth:
        warnings.append(f"{body.cycle} requires peck_depth, using default 5mm")
        body.peck_depth = 5.0
    
    if body.cycle == "G84":
        if not body.thread_pitch:
            raise HTTPException(400, "G84 requires thread_pitch")
        if not body.spindle_rpm:
            raise HTTPException(400, "G84 requires spindle_rpm")
    
    # Validate depth is negative
    if body.depth >= 0:
        raise HTTPException(400, "depth must be negative (below surface)")
    
    # Validate retract is positive
    if body.retract < 0:
        raise HTTPException(400, "retract must be positive (above surface)")
    
    try:
        # Convert holes to dict format
        holes_list = [{"x": h.x, "y": h.y} for h in body.holes]
        
        # Generate G-code
        gcode, stats = generate_drilling_gcode(
            cycle=body.cycle,
            holes=holes_list,
            depth=body.depth,
            retract=body.retract,
            feed=body.feed,
            safe_z=body.safe_z,
            post_id=body.post_id,
            peck_depth=body.peck_depth,
            thread_pitch=body.thread_pitch,
            spindle_rpm=body.spindle_rpm,
            expand_cycles=body.expand_cycles
        )
        
        return DrillingOut(
            gcode=gcode,
            stats=stats,
            warnings=warnings
        )
    
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Drilling generation failed: {str(e)}")


@router.post("/drill/gcode/download")
async def download_drill_gcode(body: DrillingIn) -> Response:
    """
    Generate and download G-code as .nc file.
    
    Returns G-code with appropriate Content-Disposition header.
    """
    # Validate and generate (reuse logic from main endpoint)
    result = await generate_drill_gcode(body)
    
    # Determine filename
    cycle_name = body.cycle.lower()
    filename = f"drilling_{cycle_name}_{len(body.holes)}holes.nc"
    
    return Response(
        content=result.gcode,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/drill/cycles")
async def list_drill_cycles() -> Dict[str, Any]:
    """
    List available drilling cycles with descriptions.
    
    Returns cycle information for UI builders.
    """
    return {
        "cycles": [
            {
                "id": "G81",
                "name": "Simple Drill",
                "description": "Drill to depth, rapid retract",
                "parameters": ["depth", "retract", "feed"],
                "use_case": "Through holes, spot drilling"
            },
            {
                "id": "G83",
                "name": "Peck Drill",
                "description": "Drill with full retract pecking",
                "parameters": ["depth", "retract", "feed", "peck_depth"],
                "use_case": "Deep holes, chip evacuation"
            },
            {
                "id": "G73",
                "name": "Chip Break",
                "description": "Drill with partial retract",
                "parameters": ["depth", "retract", "feed", "peck_depth"],
                "use_case": "Faster than G83, less chip evacuation"
            },
            {
                "id": "G84",
                "name": "Rigid Tap",
                "description": "Threading cycle with reversing",
                "parameters": ["depth", "retract", "thread_pitch", "spindle_rpm"],
                "use_case": "M3-M12 threads"
            },
            {
                "id": "G85",
                "name": "Boring",
                "description": "Bore with feed retract",
                "parameters": ["depth", "retract", "feed"],
                "use_case": "Accurate holes, better finish"
            }
        ]
    }


@router.get("/drill/posts")
async def get_post_support() -> Dict[str, Any]:
    """
    Get post-processor cycle support information.
    
    Returns which posts support canned cycles vs. expansion.
    """
    return {
        "modal_cycles_supported": [
            "Fanuc", "Haas", "Mazak", "Okuma",
            "LinuxCNC", "PathPilot", "Mach4"
        ],
        "requires_expansion": [
            "GRBL", "TinyG", "Smoothie", "Marlin"
        ],
        "note": "Hobby controllers automatically expand cycles to G0/G1"
    }
