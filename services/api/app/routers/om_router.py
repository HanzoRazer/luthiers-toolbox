"""
OM Acoustic Guitar Router
Provides API endpoints for OM-style acoustic guitar templates, graduation maps, and CNC kits.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

router = APIRouter(prefix="/cam/om", tags=["om"])

# Base path to OM project assets
OM_BASE = Path(__file__).parent.parent.parent.parent / "OM Project"


# ============================================================================
# Pydantic Models
# ============================================================================

class OMTemplate(BaseModel):
    """OM template file metadata"""
    name: str
    type: str  # 'outline', 'mold', 'graduation', 'mdf'
    format: str  # 'dxf', 'svg', 'pdf'
    path: str
    description: Optional[str] = None


class OMSpecs(BaseModel):
    """OM acoustic guitar specifications"""
    model: str
    scale_length_mm: float
    scale_length_inches: float
    nut_width_mm: float
    end_width_mm: float
    body_length_mm: float
    body_width_upper_mm: float
    body_width_lower_mm: float
    body_depth_mm: float
    fret_count: int
    string_spacing_mm: float
    features: List[str]


class OMKit(BaseModel):
    """OM CNC kit metadata"""
    name: str
    description: str
    files: List[str]
    zip_available: bool
    path: Optional[str] = None


class OMGraduationMap(BaseModel):
    """OM graduation thickness map"""
    name: str
    surface: str  # 'top' or 'back'
    format: str  # 'svg' or 'pdf'
    grid: bool  # True for grid version, False for plain
    path: str


class OMResource(BaseModel):
    """OM project resource file"""
    name: str
    type: str  # 'pdf', 'docx', 'dxf', 'svg'
    category: str  # 'documentation', 'template', 'checklist', 'reference'
    path: str


# ============================================================================
# Helper Functions
# ============================================================================

def _scan_templates() -> List[OMTemplate]:
    """Scan OM Project folder for DXF templates"""
    templates = []
    
    if not OM_BASE.exists():
        return templates
    
    # Scan for DXF files
    dxf_files = list(OM_BASE.rglob("*.dxf"))
    for dxf in dxf_files:
        name = dxf.stem
        
        # Determine type from filename
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
    
    # Scan for SVG graduation maps
    svg_files = list(OM_BASE.rglob("*Graduation*.svg"))
    for svg in svg_files:
        name = svg.stem
        
        # Determine surface (top or back)
        if "Top" in name:
            surface = "top"
        elif "Back" in name:
            surface = "back"
        else:
            surface = "unknown"
        
        # Determine if grid or plain
        grid = "Grid" in name or "grid" in name
        
        maps.append(OMGraduationMap(
            name=name,
            surface=surface,
            format="svg",
            grid=grid,
            path=str(svg.relative_to(OM_BASE))
        ))
    
    # Scan for PDF graduation maps
    pdf_files = list(OM_BASE.rglob("*Graduation*.pdf"))
    for pdf in pdf_files:
        name = pdf.stem
        maps.append(OMGraduationMap(
            name=name,
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
    
    # CAM Import Kit
    cam_kit_path = OM_BASE / "OM_CAM_Import_Kit"
    if cam_kit_path.exists():
        files = [f.name for f in cam_kit_path.iterdir() if f.is_file()]
        zip_path = OM_BASE / "OM_CAM_Import_Kit.zip"
        
        kits.append(OMKit(
            name="OM CAM Import Kit",
            description="Complete kit for importing OM templates into Fusion 360 or other CAM software. Includes outline DXF, graduation maps, and reference documentation.",
            files=files,
            zip_available=zip_path.exists(),
            path="OM_CAM_Import_Kit" if cam_kit_path.exists() else None
        ))
    
    # Mould CNC Kit
    mould_kit_path = OM_BASE / "OM_Mould_CNC_Kit"
    if mould_kit_path.exists():
        files = [f.name for f in mould_kit_path.iterdir() if f.is_file()]
        zip_path = OM_BASE / "OM_Mould_CNC_Kit.zip"
        
        kits.append(OMKit(
            name="OM Mould CNC Kit",
            description="DXF geometry for CNC-routing an OM body mold. Suitable for 3/4\" MDF or Baltic birch plywood.",
            files=files,
            zip_available=zip_path.exists(),
            path="OM_Mould_CNC_Kit" if mould_kit_path.exists() else None
        ))
    
    return kits


def _scan_resources() -> List[OMResource]:
    """Scan for documentation and resource files"""
    resources = []
    
    if not OM_BASE.exists():
        return resources
    
    # PDF documentation
    pdf_files = list(OM_BASE.rglob("*.pdf"))
    for pdf in pdf_files:
        name = pdf.stem
        
        # Categorize
        if "checklist" in name.lower():
            category = "checklist"
        elif "reference" in name.lower() or "notes" in name.lower():
            category = "reference"
        elif "graduation" in name.lower():
            category = "graduation"
        else:
            category = "documentation"
        
        resources.append(OMResource(
            name=name,
            type="pdf",
            category=category,
            path=str(pdf.relative_to(OM_BASE))
        ))
    
    # DOCX files
    docx_files = list(OM_BASE.rglob("*.docx"))
    for docx in docx_files:
        resources.append(OMResource(
            name=docx.stem,
            type="docx",
            category="checklist",
            path=str(docx.relative_to(OM_BASE))
        ))
    
    return resources


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/health")
async def health():
    """Health check for OM module"""
    om_exists = OM_BASE.exists()
    
    # Count assets
    template_count = len(_scan_templates()) if om_exists else 0
    graduation_count = len(_scan_graduation_maps()) if om_exists else 0
    kit_count = len(_scan_kits()) if om_exists else 0
    
    return {
        "ok": True,
        "module": "om",
        "om_project_path": str(OM_BASE),
        "om_project_exists": om_exists,
        "templates_available": template_count,
        "graduation_maps_available": graduation_count,
        "kits_available": kit_count
    }


@router.get("/templates", response_model=List[OMTemplate])
async def get_templates():
    """List all OM DXF templates"""
    templates = _scan_templates()
    
    if not templates:
        raise HTTPException(
            status_code=404,
            detail="No OM templates found. Check OM Project folder exists."
        )
    
    return templates


@router.get("/templates/{template_type}/download")
async def download_template(template_type: str):
    """
    Download a specific OM template by type.
    
    Types: outline, mold, mdf
    """
    templates = _scan_templates()
    
    # Find template by type
    matching = [t for t in templates if t.type == template_type]
    
    if not matching:
        raise HTTPException(
            status_code=404,
            detail=f"No template found for type: {template_type}"
        )
    
    # Use first match
    template = matching[0]
    file_path = OM_BASE / template.path
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Template file not found: {template.path}"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=f"OM_{template_type}.dxf",
        media_type="application/dxf"
    )


@router.get("/specs", response_model=OMSpecs)
async def get_specs():
    """Get OM acoustic guitar specifications"""
    
    # Load defaults from OM/defaults.json if available
    defaults_path = OM_BASE / "OM" / "defaults.json"
    
    if defaults_path.exists():
        with open(defaults_path, 'r') as f:
            defaults = json.load(f)
            scale_mm = defaults.get("scale_mm", 647.7)
            nut_width = defaults.get("nut_width_mm", 43.0)
            end_width = defaults.get("end_width_mm", 56.0)
    else:
        # Fallback defaults
        scale_mm = 647.7
        nut_width = 43.0
        end_width = 56.0
    
    return OMSpecs(
        model="OM (Orchestra Model)",
        scale_length_mm=scale_mm,
        scale_length_inches=round(scale_mm / 25.4, 2),
        nut_width_mm=nut_width,
        end_width_mm=end_width,
        body_length_mm=505.0,
        body_width_upper_mm=286.0,
        body_width_lower_mm=394.0,
        body_depth_mm=105.0,
        fret_count=20,
        string_spacing_mm=9.0,
        features=[
            "14-fret neck joint",
            "Smaller body than Dreadnought",
            "Balanced tone (midrange focus)",
            "Comfortable for fingerstyle",
            "X-bracing pattern",
            "Carved top and back graduation"
        ]
    )


@router.get("/graduation-maps", response_model=List[OMGraduationMap])
async def get_graduation_maps():
    """List all OM graduation thickness maps"""
    maps = _scan_graduation_maps()
    
    if not maps:
        raise HTTPException(
            status_code=404,
            detail="No graduation maps found in OM Project folder"
        )
    
    return maps


@router.get("/graduation-maps/{surface}/{format}/download")
async def download_graduation_map(surface: str, format: str, grid: bool = False):
    """
    Download a specific graduation map.
    
    - surface: 'top' or 'back'
    - format: 'svg' or 'pdf'
    - grid: True for grid version, False for plain (SVG only)
    """
    maps = _scan_graduation_maps()
    
    # Filter by criteria
    matching = [
        m for m in maps
        if m.surface == surface and m.format == format
    ]
    
    if format == "svg":
        matching = [m for m in matching if m.grid == grid]
    
    if not matching:
        raise HTTPException(
            status_code=404,
            detail=f"No graduation map found: surface={surface}, format={format}, grid={grid}"
        )
    
    # Use first match
    grad_map = matching[0]
    file_path = OM_BASE / grad_map.path
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Graduation map file not found: {grad_map.path}"
        )
    
    media_type = "image/svg+xml" if format == "svg" else "application/pdf"
    
    return FileResponse(
        path=str(file_path),
        filename=f"OM_{surface}_graduation{'_grid' if grid else ''}.{format}",
        media_type=media_type
    )


@router.get("/kits", response_model=List[OMKit])
async def get_kits():
    """List available OM CNC kits"""
    kits = _scan_kits()
    
    if not kits:
        raise HTTPException(
            status_code=404,
            detail="No OM kits found in OM Project folder"
        )
    
    return kits


@router.get("/kits/{kit_name}/download")
async def download_kit(kit_name: str):
    """
    Download a complete OM kit as ZIP.
    
    Available kits:
    - cam-import: OM CAM Import Kit
    - mould: OM Mould CNC Kit
    """
    kit_map = {
        "cam-import": "OM_CAM_Import_Kit.zip",
        "mould": "OM_Mould_CNC_Kit.zip"
    }
    
    if kit_name not in kit_map:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown kit: {kit_name}. Available: cam-import, mould"
        )
    
    zip_path = OM_BASE / kit_map[kit_name]
    
    if not zip_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Kit ZIP not found: {kit_map[kit_name]}"
        )
    
    return FileResponse(
        path=str(zip_path),
        filename=kit_map[kit_name],
        media_type="application/zip"
    )


@router.get("/resources", response_model=List[OMResource])
async def get_resources():
    """List all OM project resources (PDFs, docs, etc.)"""
    resources = _scan_resources()
    
    if not resources:
        raise HTTPException(
            status_code=404,
            detail="No resources found in OM Project folder"
        )
    
    return resources


@router.get("/resources/{resource_name}/download")
async def download_resource(resource_name: str):
    """Download a specific OM resource file"""
    resources = _scan_resources()
    
    # Find resource by name
    matching = [r for r in resources if r.name == resource_name]
    
    if not matching:
        raise HTTPException(
            status_code=404,
            detail=f"Resource not found: {resource_name}"
        )
    
    resource = matching[0]
    file_path = OM_BASE / resource.path
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Resource file not found: {resource.path}"
        )
    
    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "dxf": "application/dxf",
        "svg": "image/svg+xml"
    }
    
    media_type = media_types.get(resource.type, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{resource_name}.{resource.type}",
        media_type=media_type
    )
