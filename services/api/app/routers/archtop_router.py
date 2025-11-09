"""
Archtop Guitar Router
Endpoints for archtop guitar design: contour generation, floating bridge, saddle
"""

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from pathlib import Path
import subprocess
import sys
import time
from typing import Optional

router = APIRouter(prefix="/cam/archtop", tags=["archtop"])


class ArchtopContourCSVRequest(BaseModel):
    """Generate contours from CSV point cloud (x, y, height)"""
    csv_path: str
    levels: str = "0,5,10,15,20"  # Heights in mm
    resolution: float = 1.5  # Grid resolution in mm
    out_prefix: str = "archtop_contours"


class ArchtopContourOutlineRequest(BaseModel):
    """Generate scaled contours from DXF outline (Mottola-style)"""
    dxf_path: str
    scales: str = "0.90,0.78,0.66,0.54,0.37"  # Scale factors for rings
    origin: str = "0,0"  # Origin point
    out_prefix: str = "archtop_outline"


class ArchtopFitRequest(BaseModel):
    """Calculate neck angle and bridge parameters"""
    scale_length_mm: float = 628.0  # 24.75" Gibson scale
    neck_angle_deg: float = 3.0
    body_thickness_mm: float = 45.0
    top_arch_height_mm: float = 18.0
    fingerboard_extension_mm: float = 70.0


class ArchtopBridgeRequest(BaseModel):
    """Generate floating bridge DXF"""
    fit_json_path: str
    post_spacing_mm: float = 75.0
    bridge_base_length_mm: float = 120.0
    bridge_base_width_mm: float = 20.0
    string_spacing_mm: float = 52.0
    out_dir: str = "storage/exports/archtop_bridge"


class ArchtopSaddleRequest(BaseModel):
    """Generate compensated saddle profile"""
    fit_json_path: str
    crown_radius_mm: float = 304.8  # 12" radius
    string_spacing_mm: float = 52.0
    out_dir: str = "storage/exports/archtop_saddle"


@router.post("/contours/csv")
def generate_contours_from_csv(req: ArchtopContourCSVRequest):
    """
    Generate archtop contour rings from CSV point cloud.
    
    CSV format: x,y,height (in mm)
    Returns DXF + SVG + PNG preview
    """
    script = Path("services/api/app/cam/archtop_contour_generator.py")
    if not script.exists():
        # Try legacy location
        script = Path("Archtop/archtop_contour_generator.py")
        if not script.exists():
            raise HTTPException(
                status_code=500,
                detail="archtop_contour_generator.py not found"
            )
    
    # Create timestamped output directory
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = Path("storage/exports") / f"{ts}_archtop_contours"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = out_dir / req.out_prefix
    
    cmd = [
        sys.executable, str(script),
        "csv",
        "--in", req.csv_path,
        "--levels", req.levels,
        "--res", str(req.resolution),
        "--out-prefix", str(out_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Find generated files
        files = [p.name for p in out_dir.glob(f"{req.out_prefix}*")]
        
        return {
            "ok": True,
            "out_dir": str(out_dir),
            "files": files,
            "stdout": result.stdout
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contour generation failed: {e.stderr}"
        )


@router.post("/contours/outline")
def generate_contours_from_outline(req: ArchtopContourOutlineRequest):
    """
    Generate scaled contour rings from DXF outline (Mottola method).
    
    Scales the outline by given factors to create graduated thickness zones.
    Returns DXF + SVG + PNG preview
    """
    script = Path("services/api/app/cam/archtop_contour_generator.py")
    if not script.exists():
        script = Path("Archtop/archtop_contour_generator.py")
        if not script.exists():
            raise HTTPException(
                status_code=500,
                detail="archtop_contour_generator.py not found"
            )
    
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = Path("storage/exports") / f"{ts}_archtop_contours"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = out_dir / req.out_prefix
    
    cmd = [
        sys.executable, str(script),
        "outline",
        "--in", req.dxf_path,
        "--scales", req.scales,
        "--origin", req.origin,
        "--out-prefix", str(out_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        files = [p.name for p in out_dir.glob(f"{req.out_prefix}*")]
        
        return {
            "ok": True,
            "out_dir": str(out_dir),
            "files": files,
            "stdout": result.stdout
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contour generation failed: {e.stderr}"
        )


@router.post("/fit")
def calculate_bridge_fit(req: ArchtopFitRequest):
    """
    Calculate neck angle, bridge height range, and string compensation.
    
    Returns JSON with fit parameters for bridge generation.
    """
    # Basic fit calculations (simplified - full implementation would be more complex)
    import math
    
    # Calculate bridge height at saddle
    # Geometry: neck angle creates string break angle over bridge
    scale_length_m = req.scale_length_mm / 1000.0
    neck_angle_rad = math.radians(req.neck_angle_deg)
    
    # Approximate bridge height (this is simplified - real calc involves more geometry)
    fingerboard_height_at_end = math.tan(neck_angle_rad) * (req.fingerboard_extension_mm / 1000.0) * 1000.0
    bridge_height_mm = fingerboard_height_at_end + req.top_arch_height_mm + 10.0  # +10mm typical string clearance
    
    # String compensation (heavier strings need more length)
    # Typical compensation: Low E = +3mm, High E = +1.5mm
    compensations = [3.0, 2.5, 2.2, 2.0, 1.8, 1.5]  # 6 strings
    
    # Saddle line position (scale length + average compensation)
    avg_comp = sum(compensations) / len(compensations)
    saddle_line_mm_from_nut = req.scale_length_mm + avg_comp
    
    fit_data = {
        "scale_length_mm": req.scale_length_mm,
        "neck_angle_deg": req.neck_angle_deg,
        "bridge_height_mm": bridge_height_mm,
        "bridge_height_range_mm": {
            "min": bridge_height_mm - 2.0,
            "max": bridge_height_mm + 2.0
        },
        "saddle_line_mm_from_nut": saddle_line_mm_from_nut,
        "string_compensations_mm": compensations,
        "post_spacing_mm": 75.0,  # Default
        "string_spacing_at_saddle_mm": 52.0,  # Default
        "bridge_base_mm": {
            "length": 120.0,
            "width": 20.0
        }
    }
    
    # Save to exports directory
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = Path("storage/exports/archtop_fit")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    fit_path = out_dir / f"archtop_fit_{ts}.json"
    with open(fit_path, "w") as f:
        json.dump(fit_data, f, indent=2)
    
    return {
        "ok": True,
        "fit_data": fit_data,
        "fit_json_path": str(fit_path)
    }


@router.post("/bridge")
def generate_floating_bridge(req: ArchtopBridgeRequest):
    """
    Generate floating bridge DXF with layers:
    - BRIDGE_BASE: Rectangle outline
    - POSTS: Two drill holes
    - SADDLE_TICKS: String position markers
    - SADDLE_LINE: Compensated saddle line
    - UNDERSIDE_PROFILE: Arch profile for base shaping
    
    Requires fit JSON from /archtop/fit endpoint.
    """
    # This would call bridge_generator.py script
    # For now, return a placeholder
    raise HTTPException(
        status_code=501,
        detail="Bridge generation requires bridge_generator.py script (to be ported from v0.9.11)"
    )


@router.post("/saddle")
def generate_saddle_profile(req: ArchtopSaddleRequest):
    """
    Generate crowned saddle profile with compensation.
    
    Requires fit JSON from /archtop/fit endpoint.
    """
    raise HTTPException(
        status_code=501,
        detail="Saddle generation requires saddle_generator.py script (to be ported from v0.9.12)"
    )


@router.get("/kits")
def list_contour_kits():
    """List available archtop contour kits (templates and examples)"""
    kits_dir = Path("services/api/data/archtop_kits")
    if not kits_dir.exists():
        # Try legacy location
        kits_dir = Path("Archtop")
        if not kits_dir.exists():
            return {"ok": True, "kits": []}
    
    kits = []
    for kit_path in kits_dir.iterdir():
        if kit_path.is_dir() and "Contour" in kit_path.name:
            kits.append({
                "id": kit_path.name,
                "path": str(kit_path),
                "files": [p.name for p in kit_path.glob("*.dxf")][:5]  # Sample
            })
    
    return {"ok": True, "kits": kits}


@router.get("/health")
def archtop_health():
    """Health check for archtop module"""
    script = Path("services/api/app/cam/archtop_contour_generator.py")
    script_exists = script.exists()
    
    if not script_exists:
        script = Path("Archtop/archtop_contour_generator.py")
        script_exists = script.exists()
    
    return {
        "ok": True,
        "module": "archtop",
        "contour_generator": script_exists,
        "bridge_generator": False,  # To be ported
        "saddle_generator": False   # To be ported
    }
