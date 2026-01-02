"""
Archtop CAM Router
==================

CAM operations for archtop guitars: contour generation, bridge fitting, saddle profiles.
Instrument specs moved to /api/instruments/guitar/archtop/*

Endpoints:
  GET /health - CAM subsystem health
  POST /contours/csv - Generate contours from CSV point cloud
  POST /contours/outline - Generate scaled contours from DXF outline
  POST /fit - Calculate bridge fit parameters
  POST /bridge - Generate floating bridge DXF
  POST /saddle - Generate compensated saddle profile

Wave 15: Option C API Restructuring
"""

import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Archtop", "CAM"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

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


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/health")
def archtop_cam_health() -> Dict[str, Any]:
    """
    Get archtop CAM subsystem health status.
    
    Checks availability of contour generator scripts and dependencies.
    """
    script = Path("services/api/app/cam/archtop_contour_generator.py")
    legacy_script = Path("Archtop/archtop_contour_generator.py")
    
    return {
        "ok": True,
        "subsystem": "archtop_cam",
        "model_id": "archtop",
        "capabilities": [
            "contour_csv",
            "contour_outline",
            "bridge_fit",
            "bridge_dxf",
            "saddle_profile"
        ],
        "scripts": {
            "contour_generator": script.exists() or legacy_script.exists(),
            "contour_generator_path": str(script) if script.exists() else str(legacy_script) if legacy_script.exists() else None
        },
        "instrument_spec": "/api/instruments/guitar/archtop/spec"
    }


@router.post("/contours/csv")
def generate_contours_from_csv(req: ArchtopContourCSVRequest) -> Dict[str, Any]:
    """
    Generate archtop contour rings from CSV point cloud.
    
    CSV format: x,y,height (in mm)
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
def generate_contours_from_outline(req: ArchtopContourOutlineRequest) -> Dict[str, Any]:
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
def calculate_bridge_fit(req: ArchtopFitRequest) -> Dict[str, Any]:
    """
    Calculate neck angle, bridge height range, and string compensation.
    
    Returns JSON with fit parameters for bridge generation.
    """
    # Calculate bridge height at saddle
    neck_angle_rad = math.radians(req.neck_angle_deg)
    
    # Approximate bridge height
    fingerboard_height_at_end = math.tan(neck_angle_rad) * req.fingerboard_extension_mm
    bridge_height_mm = fingerboard_height_at_end + req.top_arch_height_mm + 10.0  # +10mm string clearance
    
    # String compensation (heavier strings need more length)
    compensations = [3.0, 2.5, 2.2, 2.0, 1.8, 1.5]  # 6 strings
    
    # Saddle line position
    avg_comp = sum(compensations) / len(compensations)
    saddle_line_mm_from_nut = req.scale_length_mm + avg_comp
    
    fit_data = {
        "ok": True,
        "input": req.model_dump(),
        "fit_parameters": {
            "bridge_height_mm": round(bridge_height_mm, 2),
            "bridge_height_range_mm": [
                round(bridge_height_mm - 2, 2),
                round(bridge_height_mm + 2, 2)
            ],
            "saddle_line_from_nut_mm": round(saddle_line_mm_from_nut, 2),
            "string_compensations_mm": compensations,
            "fingerboard_clearance_mm": 10.0,
            "neck_angle_deg": req.neck_angle_deg
        },
        "notes": [
            "Bridge height assumes 10mm string clearance at 12th fret",
            "Compensations are typical values - may need adjustment for specific string gauges",
            "Use fit_parameters with /bridge endpoint to generate DXF"
        ]
    }
    
    return fit_data


@router.post("/bridge")
def generate_bridge_dxf(req: ArchtopBridgeRequest) -> Dict[str, Any]:
    """
    Generate floating bridge DXF from fit parameters.
    
    Creates a DXF with bridge base outline, post holes, and saddle slot.
    """
    script = Path("services/api/app/cam/archtop_bridge_generator.py")
    if not script.exists():
        # Return placeholder response
        return {
            "ok": False,
            "error": "Bridge generator script not implemented",
            "note": "Manual bridge design required - use fit parameters from /fit endpoint"
        }
    
    # TODO: Implement bridge generator subprocess call
    return {
        "ok": False,
        "error": "Bridge generator not yet implemented",
        "requested": req.model_dump()
    }


@router.post("/saddle")
def generate_saddle_profile(req: ArchtopSaddleRequest) -> Dict[str, Any]:
    """
    Generate compensated saddle profile from fit parameters.
    
    Creates a profile with individual string compensation.
    """
    script = Path("services/api/app/cam/archtop_saddle_generator.py")
    if not script.exists():
        return {
            "ok": False,
            "error": "Saddle generator script not implemented",
            "note": "Manual saddle design required - use compensations from /fit endpoint"
        }
    
    return {
        "ok": False,
        "error": "Saddle generator not yet implemented",
        "requested": req.model_dump()
    }
