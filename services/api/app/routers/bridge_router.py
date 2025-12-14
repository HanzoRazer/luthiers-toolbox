"""
Bridge Calculator Router
API endpoints for acoustic guitar bridge saddle compensation calculations and DXF export.

Endpoints:
- POST /cam/bridge/export_dxf: Generate DXF from bridge geometry JSON
- GET /cam/bridge/presets: List available family/gauge/action presets
- GET /cam/bridge/health: Health check
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cam/bridge", tags=["Bridge Calculator", "CAM"])

IN_TO_MM = 25.4


def inches_to_mm(value: float) -> float:
    """Convert inches to millimeters with 2 decimal precision."""
    return round(value * IN_TO_MM, 2)


# ============================================================================
# Pydantic Models
# ============================================================================

class Point(BaseModel):
    """2D point coordinates."""
    x: float
    y: float


class BridgeEndpoints(BaseModel):
    """Saddle line endpoints (treble and bass sides)."""
    treble: Point
    bass: Point


class BridgeGeometry(BaseModel):
    """Bridge saddle compensation geometry."""
    units: str = Field(..., description="Units: 'mm' or 'in'")
    scaleLength: float = Field(..., description="Scale length from nut to saddle")
    stringSpread: float = Field(..., description="String spread (E-to-E) at bridge")
    compTreble: float = Field(..., description="Compensation offset for treble side (mm or in)")
    compBass: float = Field(..., description="Compensation offset for bass side (mm or in)")
    slotWidth: float = Field(..., description="Saddle slot width (perpendicular to saddle line)")
    slotLength: float = Field(..., description="Saddle slot length (along saddle line)")
    angleDeg: Optional[float] = Field(None, description="Saddle angle in degrees (calculated)")
    endpoints: BridgeEndpoints = Field(..., description="Saddle line endpoints")
    slotPolygon: List[Point] = Field(..., description="Slot rectangle polygon (4 vertices)")


class BridgeExportRequest(BaseModel):
    """Request body for DXF export."""
    geometry: BridgeGeometry
    filename: Optional[str] = Field(None, description="Optional output filename (without extension)")


class PresetFamily(BaseModel):
    """Guitar family preset definition."""
    id: str
    label: str
    scaleLength: float  # mm
    stringSpread: float  # mm (E-to-E spacing)
    compTreble: float  # mm compensation guide
    compBass: float  # mm compensation guide
    slotWidth: float  # mm slot width
    slotLength: float  # mm slot length


class PresetGauge(BaseModel):
    """String gauge preset."""
    id: str
    label: str
    compAdjust: float  # Legacy aggregate adjustment (mm)
    trebleAdjust: float  # mm delta applied to treble compensation
    bassAdjust: float  # mm delta applied to bass compensation


class PresetAction(BaseModel):
    """Action height preset."""
    id: str
    label: str
    compAdjust: float  # Legacy aggregate adjustment (mm)
    trebleAdjust: float  # mm delta applied to treble compensation
    bassAdjust: float  # mm delta applied to bass compensation


class PresetsResponse(BaseModel):
    """Available presets for bridge calculator."""
    families: List[PresetFamily]
    gauges: List[PresetGauge]
    actions: List[PresetAction]


# ============================================================================
# Preset Data
# ============================================================================

FAMILY_PRESETS = [
    {
        "id": "les_paul",
        "label": "Les Paul (24.75\")",
        "scaleLength": inches_to_mm(24.75),
        "stringSpread": 52.0,
        "compTreble": 1.5,
        "compBass": 3.0,
        "slotWidth": 3.0,
        "slotLength": 75.0,
    },
    {
        "id": "strat_tele",
        "label": "Strat/Tele (25.5\")",
        "scaleLength": inches_to_mm(25.5),
        "stringSpread": 52.5,
        "compTreble": 2.0,
        "compBass": 3.5,
        "slotWidth": 3.0,
        "slotLength": 75.0,
    },
    {
        "id": "om",
        "label": "OM Acoustic (25.4\")",
        "scaleLength": inches_to_mm(25.4),
        "stringSpread": 54.0,
        "compTreble": 2.0,
        "compBass": 4.2,
        "slotWidth": 3.2,
        "slotLength": 80.0,
    },
    {
        "id": "dread",
        "label": "Dreadnought (25.4\")",
        "scaleLength": inches_to_mm(25.4),
        "stringSpread": 54.0,
        "compTreble": 2.0,
        "compBass": 4.5,
        "slotWidth": 3.2,
        "slotLength": 80.0,
    },
    {
        "id": "archtop",
        "label": "Archtop (25.0\")",
        "scaleLength": inches_to_mm(25.0),
        "stringSpread": 52.0,
        "compTreble": 1.8,
        "compBass": 3.2,
        "slotWidth": 3.0,
        "slotLength": 75.0,
    },
]

GAUGE_PRESETS = [
    {
        "id": "light",
        "label": "Light (.010-.046)",
        "compAdjust": -0.3,
        "trebleAdjust": -0.3,
        "bassAdjust": -0.3,
    },
    {
        "id": "medium",
        "label": "Medium (.011-.049)",
        "compAdjust": 0.0,
        "trebleAdjust": 0.0,
        "bassAdjust": 0.0,
    },
    {
        "id": "heavy",
        "label": "Heavy (.012-.053)",
        "compAdjust": 0.35,
        "trebleAdjust": 0.3,
        "bassAdjust": 0.4,
    },
]

ACTION_PRESETS = [
    {
        "id": "low",
        "label": "Low Action",
        "compAdjust": -0.2,
        "trebleAdjust": -0.2,
        "bassAdjust": -0.2,
    },
    {
        "id": "standard",
        "label": "Standard Action",
        "compAdjust": 0.0,
        "trebleAdjust": 0.0,
        "bassAdjust": 0.0,
    },
    {
        "id": "high",
        "label": "High Action",
        "compAdjust": 0.35,
        "trebleAdjust": 0.3,
        "bassAdjust": 0.4,
    },
]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/export_dxf", response_class=Response)
def export_bridge_dxf(request: BridgeExportRequest) -> Response:
    """
    Generate R12 DXF file from bridge geometry.
    
    Calls the bridge_to_dxf.py script with geometry JSON.
    Returns DXF file as application/dxf.
    
    DXF Layers:
    - SADDLE_LINE: Cyan line with endpoint circles
    - SLOT_RECTANGLE: Yellow closed LWPolyline (CNC-ready)
    - NUT_REFERENCE: Gray dashed centerline at x=0
    - SCALE_REFERENCE: Gray tick at scale length
    - DIMENSIONS: White text annotations
    """
    # Locate bridge_to_dxf.py script (resolve from project root)
    # API runs from services/api/, need to go up to project root
    api_dir = Path(__file__).parent.parent  # services/api/app/routers -> services/api/app
    project_root = api_dir.parent.parent.parent  # services/api/app -> services/api -> services -> project root
    script_path = project_root / "server" / "pipelines" / "bridge" / "bridge_to_dxf.py"
    
    if not script_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Bridge DXF export script not found: {script_path}"
        )
    
    # Create temporary files for input JSON and output DXF
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        input_json = tmp_path / "bridge_input.json"
        output_dxf = tmp_path / "bridge_output.dxf"
        
        # Write geometry to JSON file
        geom_dict = request.geometry.dict()
        with open(input_json, "w") as f:
            json.dump(geom_dict, f, indent=2)
        
        # Run bridge_to_dxf.py script
        cmd = [
            sys.executable,
            str(script_path.resolve()),
            str(input_json),
            "--output",
            str(output_dxf)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            # Read generated DXF
            if not output_dxf.exists():
                raise HTTPException(
                    status_code=500,
                    detail="DXF file was not generated"
                )
            
            dxf_content = output_dxf.read_bytes()
            
            # Generate filename
            units = request.geometry.units
            scale = request.geometry.scaleLength
            comp_t = request.geometry.compTreble
            comp_b = request.geometry.compBass
            
            if request.filename:
                filename = f"{request.filename}.dxf"
            else:
                filename = f"bridge_{scale:.1f}{units}_ct{comp_t:.1f}_cb{comp_b:.1f}.dxf"
            
            return Response(
                content=dxf_content,
                media_type="application/dxf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
            
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=500,
                detail="Bridge DXF export timed out (>10s)"
            )
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Bridge DXF export failed: {e.stderr}"
            )


@router.get("/presets", response_model=PresetsResponse)
def get_bridge_presets() -> Dict[str, Any]:
    """
    Get available presets for bridge calculator.
    
    Returns family presets (guitar types), gauge presets (string weights),
    and action presets (height adjustments).
    """
    return {
        "families": FAMILY_PRESETS,
        "gauges": GAUGE_PRESETS,
        "actions": ACTION_PRESETS
    }


@router.get("/health")
def bridge_health() -> Dict[str, Any]:
    """
    Health check for bridge calculator module.
    
    Verifies:
    - bridge_to_dxf.py script exists
    - ezdxf library is importable
    """
    script_path = Path("server/pipelines/bridge/bridge_to_dxf.py")
    script_exists = script_path.exists()
    
    # Check ezdxf availability
    try:
        import ezdxf
        ezdxf_available = True
        ezdxf_version = ezdxf.__version__
    except ImportError:
        ezdxf_available = False
        ezdxf_version = None
    
    return {
        "status": "ok",
        "ok": True,
        "module": "bridge_calculator",
        "script_exists": script_exists,
        "script_path": str(script_path),
        "ezdxf_available": ezdxf_available,
        "ezdxf_version": ezdxf_version,
        "presets_count": {
            "families": len(FAMILY_PRESETS),
            "gauges": len(GAUGE_PRESETS),
            "actions": len(ACTION_PRESETS)
        }
    }
