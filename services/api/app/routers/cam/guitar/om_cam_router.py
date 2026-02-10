"""
OM CAM Router
=============

CAM operations for OM acoustic guitars: graduation maps, CNC kits, template downloads.
Instrument specs moved to /api/instruments/guitar/om/*

Endpoints:
  GET /health - CAM subsystem health
  GET /templates - List DXF templates
  GET /graduation - Get graduation maps
  GET /kits - List CNC kits
  GET /download/{file_path} - Download template file

Wave 15: Option C API Restructuring
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(tags=["OM", "CAM"])

# Base path to OM project assets
OM_BASE = Path(__file__).parent.parent.parent.parent / "OM Project"

# =============================================================================
# MODELS
# =============================================================================

class OMTemplate(BaseModel):
    """OM template file metadata"""
    name: str
    type: str  # 'outline', 'mold', 'graduation', 'mdf'
    format: str  # 'dxf', 'svg', 'pdf'
    path: str
    description: Optional[str] = None

class OMGraduationMap(BaseModel):
    """OM graduation thickness map"""
    name: str
    surface: str  # 'top' or 'back'
    format: str  # 'svg' or 'pdf'
    grid: bool  # True for grid version, False for plain
    path: str

class OMKit(BaseModel):
    """OM CNC kit metadata"""
    name: str
    description: str
    files: List[str]
    zip_available: bool
    path: Optional[str] = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _scan_templates() -> List[OMTemplate]:
    """Scan OM Project folder for DXF templates"""
    templates = []
    
    if not OM_BASE.exists():
        return templates
    
    dxf_files = list(OM_BASE.rglob("*.dxf"))
    for dxf in dxf_files:
        name = dxf.stem
        
        if "outline" in name.lower():
            ttype = "outline"
            desc = "OM body outline for CNC routing"
        elif "mould" in name.lower() or "mold" in name.lower():
            ttype = "mold"
            desc = "OM body mold template for form building"
        elif "mdf" in name.lower():
            ttype = "mdf"
            desc = "MDF modification template"
        else:
            ttype = "general"
            desc = "OM acoustic guitar template"
        
        templates.append(OMTemplate(
            name=name,
            type=ttype,
            format="dxf",
            path=str(dxf.relative_to(OM_BASE)),
            description=desc
        ))
    
    return templates

def _scan_graduation_maps() -> List[OMGraduationMap]:
    """Scan for graduation thickness maps (SVG and PDF)"""
    maps = []
    
    if not OM_BASE.exists():
        return maps
    
    svg_files = list(OM_BASE.rglob("*Graduation*.svg"))
    for svg in svg_files:
        name = svg.stem
        surface = "top" if "Top" in name else "back" if "Back" in name else "unknown"
        grid = "Grid" in name or "grid" in name
        
        maps.append(OMGraduationMap(
            name=name,
            surface=surface,
            format="svg",
            grid=grid,
            path=str(svg.relative_to(OM_BASE))
        ))
    
    pdf_files = list(OM_BASE.rglob("*Graduation*.pdf"))
    for pdf in pdf_files:
        maps.append(OMGraduationMap(
            name=pdf.stem,
            surface="combined",
            format="pdf",
            grid=False,
            path=str(pdf.relative_to(OM_BASE))
        ))
    
    return maps

def _scan_kits() -> List[OMKit]:
    """Scan for organized CNC kits"""
    kits = []
    
    if not OM_BASE.exists():
        return kits
    
    cam_kit_path = OM_BASE / "OM_CAM_Import_Kit"
    if cam_kit_path.exists():
        files = [f.name for f in cam_kit_path.iterdir() if f.is_file()]
        zip_path = OM_BASE / "OM_CAM_Import_Kit.zip"
        
        kits.append(OMKit(
            name="OM CAM Import Kit",
            description="Complete kit for importing OM templates into Fusion 360 or other CAM software.",
            files=files,
            zip_available=zip_path.exists(),
            path="OM_CAM_Import_Kit"
        ))
    
    mould_kit_path = OM_BASE / "OM_Mould_CNC_Kit"
    if mould_kit_path.exists():
        files = [f.name for f in mould_kit_path.iterdir() if f.is_file()]
        zip_path = OM_BASE / "OM_Mould_CNC_Kit.zip"
        
        kits.append(OMKit(
            name="OM Mould CNC Kit",
            description="DXF geometry for CNC-routing an OM body mold.",
            files=files,
            zip_available=zip_path.exists(),
            path="OM_Mould_CNC_Kit"
        ))
    
    return kits

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/templates")
def list_om_templates() -> Dict[str, Any]:
    """
    List all available OM DXF templates.
    
    Returns body outlines, molds, and other CNC-ready templates.
    """
    templates = _scan_templates()
    
    return {
        "ok": True,
        "model": "om",
        "templates": [t.model_dump() for t in templates],
        "count": len(templates),
        "base_path": str(OM_BASE)
    }

@router.get("/graduation")
def list_graduation_maps() -> Dict[str, Any]:
    """
    List OM graduation thickness maps.
    
    Returns SVG and PDF graduation maps for top and back carving.
    """
    maps = _scan_graduation_maps()
    
    return {
        "ok": True,
        "model": "om",
        "graduation_maps": [m.model_dump() for m in maps],
        "count": len(maps),
        "note": "Graduation maps show target thicknesses in mm for hand/CNC carving"
    }

@router.get("/kits")
def list_cnc_kits() -> Dict[str, Any]:
    """
    List organized OM CNC kits.
    
    Returns pre-packaged template bundles for CAM import.
    """
    kits = _scan_kits()
    
    return {
        "ok": True,
        "model": "om",
        "kits": [k.model_dump() for k in kits],
        "count": len(kits)
    }

@router.get("/download/{file_path:path}")
def download_om_file(file_path: str) -> FileResponse:
    """
    Download an OM template file.
    
    Returns the requested DXF, SVG, or PDF file.
    """
    full_path = OM_BASE / file_path
    
    if not full_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path}"
        )
    
    # Security: ensure path is within OM_BASE
    try:
        full_path.resolve().relative_to(OM_BASE.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied: path traversal attempt"
        )
    
    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type="application/octet-stream"
    )
