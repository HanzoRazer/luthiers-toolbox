
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Literal, Optional
import math
from ..utils.post_presets import get_post_preset, get_dwell_command

router = APIRouter(prefix="/api/cam/toolpath", tags=["helical_v161"])

class HelicalReq(BaseModel):
    # Geometry
    cx: float = Field(..., description="Arc center X (mm)")
    cy: float = Field(..., description="Arc center Y (mm)")
    radius_mm: float = Field(..., gt=0, description="Helix radius (mm)")
    direction: Literal["CW","CCW"] = Field("CCW", description="Arc direction")
    # Z & feed
    plane_z_mm: float = Field(5.0, description="Clearance plane Z (mm)")
    start_z_mm: float = Field(0.0, description="Z where helix begins descending (mm)")
    z_target_mm: float = Field(..., description="Target Z (mm, negative for plunge)")
    pitch_mm_per_rev: float = Field(1.5, gt=0, description="Z change per full 360° (absolute magnitude)")
    feed_xy_mm_min: float = Field(600.0, gt=0, description="XY feed (mm/min) during arc")
    feed_z_mm_min: Optional[float] = Field(None, description="Optional Z feed limit (mm/min). If set, we will cap effective helix speed.")
    # Output style
    ij_mode: bool = Field(True, description="Emit I,J relative center. If false, uses R where possible.")
    absolute: bool = Field(True, description="Use G90 absolute coords for X,Y,Z")
    units_mm: bool = Field(True, description="True=metric (G21), False=inches (G20)")
    # Safety & extras
    safe_rapid: bool = Field(True, description="Emit G0 to clearance plane before starting")
    dwell_ms: int = Field(0, ge=0, description="Optional dwell (ms) after helix completes")
    # Limits
    max_arc_degrees: float = Field(360.0, gt=0, le=360.0, description="Split arcs to this maximum sweep each segment")
    # Post-processor preset
    post_preset: Optional[str] = Field(None, description="Optional controller preset: GRBL | Mach3 | Haas | Marlin")

    @field_validator("z_target_mm")
    @classmethod
    def check_depth(cls, v):
        if not isinstance(v, (int,float)):
            raise ValueError("z_target_mm must be a number")
        return v

def _fmt(n: float) -> str:
    # 3 decimals is typical for mm mode; adapt as needed
    return f"{n:.4f}".rstrip('0').rstrip('.') if '.' in f"{n:.4f}" else f"{n:.4f}"

def helical_gcode(req: HelicalReq) -> Dict[str, Any]:
    # Get post-processor preset (defaults to GRBL if not specified)
    preset = get_post_preset(req.post_preset)
    
    # Override ij_mode if preset requires R-mode
    effective_ij_mode = not preset.use_r_mode if req.post_preset else req.ij_mode
    
    # compute number of full revs and final remainder angle to hit target depth
    start_z = req.start_z_mm
    target_z = req.z_target_mm
    dz_total = target_z - start_z  # negative if plunging down
    if req.pitch_mm_per_rev == 0:
        raise HTTPException(status_code=400, detail="pitch_mm_per_rev must be > 0")
    # Determine number of full turns (sign handled by dz sign)
    revs_exact = abs(dz_total) / req.pitch_mm_per_rev
    full_revs = int(math.floor(revs_exact + 1e-9))
    rem_frac = revs_exact - full_revs  # 0.. <1
    # Determine sign for Z step per rev
    z_per_rev = -abs(req.pitch_mm_per_rev) if dz_total < 0 else abs(req.pitch_mm_per_rev)
    # Build program
    lines = []
    units = "G21" if req.units_mm else "G20"
    preset_name = preset.name if req.post_preset else "default"
    lines.append(f"({req.direction} Helical Z-Ramp, r={_fmt(req.radius_mm)} pitch={_fmt(req.pitch_mm_per_rev)} startZ={_fmt(start_z)} targetZ={_fmt(target_z)})")
    lines.append(f"(Post preset: {preset_name})")
    lines.append(units)
    lines.append("G90" if req.absolute else "G91")
    lines.append("G17")  # XY plane

    # Move to start XY at clearance plane
    # Start point is at angle 0 on the circle: X = cx + r, Y = cy
    sx = req.cx + req.radius_mm
    sy = req.cy
    if req.safe_rapid:
        lines.append(f"G0 Z{_fmt(req.plane_z_mm)}")
    # XY rapid to start
    lines.append(f"G0 X{_fmt(sx)} Y{_fmt(sy)}")
    # Move to start_z
    if req.plane_z_mm != start_z:
        lines.append(f"G1 Z{_fmt(start_z)} F{_fmt(req.feed_z_mm_min or req.feed_xy_mm_min)}")

    # Determine G2/G3
    g = "G2" if req.direction == "CW" else "G3"

    def emit_arc_sweep(deg: float, z_end: float):
        nonlocal lines, sx, sy
        # Compute end point after sweep deg around center from current point
        # Current angle from center:
        ang0 = math.atan2(sy - req.cy, sx - req.cx)
        ang = ang0 + math.radians(deg if req.direction=="CCW" else -deg)
        ex = req.cx + req.radius_mm * math.cos(ang)
        ey = req.cy + req.radius_mm * math.sin(ang)
        if effective_ij_mode:
            # I,J are center offset from CURRENT start point
            I = req.cx - sx
            J = req.cy - sy
            lines.append(f"{g} X{_fmt(ex)} Y{_fmt(ey)} Z{_fmt(z_end)} I{_fmt(I)} J{_fmt(J)} F{_fmt(req.feed_xy_mm_min)}")
        else:
            # Use R word when possible (minor arc by default)
            lines.append(f"{g} X{_fmt(ex)} Y{_fmt(ey)} Z{_fmt(z_end)} R{_fmt(req.radius_mm)} F{_fmt(req.feed_xy_mm_min)}")
        sx, sy = ex, ey

    # Emit full rev arcs chunked by max_arc_degrees
    seg_deg = max(1.0, min(360.0, req.max_arc_degrees))
    per_seg_rev = seg_deg / 360.0
    # Full revs
    curr_z = start_z
    for r in range(full_revs):
        z_next = curr_z + z_per_rev
        # split one full rev into segments
        steps = int(math.ceil(360.0 / seg_deg))
        # recompute segment degrees to evenly divide 360
        deg = 360.0 / steps
        for s in range(steps):
            # linear interpolate Z over steps within this rev
            z_step = curr_z + z_per_rev * ((s+1)/steps)
            emit_arc_sweep(deg, z_step)
        curr_z = z_next

    # Remainder fraction
    if rem_frac > 1e-9:
        rem_deg_total = rem_frac * 360.0
        steps = int(math.ceil(rem_deg_total / seg_deg))
        deg = rem_deg_total / steps
        for s in range(steps):
            # interpolate Z to final target
            z_step = curr_z + (target_z - curr_z) * ((s+1)/steps)
            emit_arc_sweep(deg, z_step)
        curr_z = target_z

    # Optional dwell
    if req.dwell_ms and req.dwell_ms > 0:
        # Use preset-aware dwell command (G4 P for GRBL/Mach3/Marlin, G4 S for Haas)
        dwell_cmd = get_dwell_command(req.dwell_ms, preset)
        if dwell_cmd:
            lines.append(dwell_cmd)
    # Exit to clearance plane
    lines.append(f"G0 Z{_fmt(req.plane_z_mm)}")
    program = "\n".join(lines)
    stats = {
        "revs_exact": revs_exact,
        "full_revs": full_revs,
        "rem_frac": rem_frac,
        "segments": sum(1 for ln in lines if ln.startswith(("G2","G3"))),
        "post_preset": preset_name,
        "arc_mode": "R" if not effective_ij_mode else "IJ"
    }
    return {"ok": True, "gcode": program, "stats": stats}

@router.post("/helical_entry")
def helical_entry(req: HelicalReq) -> Dict[str, Any]:
    # Basic sanity checks
    if req.radius_mm <= 0: raise HTTPException(status_code=400, detail="radius_mm must be > 0")
    if req.max_arc_degrees <= 0 or req.max_arc_degrees > 360: raise HTTPException(status_code=400, detail="max_arc_degrees must be (0,360]")
    if req.pitch_mm_per_rev <= 0: raise HTTPException(status_code=400, detail="pitch must be > 0")
    if req.start_z_mm == req.z_target_mm: raise HTTPException(status_code=400, detail="start_z_mm equals z_target_mm; nothing to do")
    return helical_gcode(req)

@router.get("/helical_health")
def helical_health() -> Dict[str, Any]:
    return {"ok": True, "service": "helical_v161", "version": "16.1"}
