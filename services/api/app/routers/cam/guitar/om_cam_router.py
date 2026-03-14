"""OM CAM Router — CAM operations for OM (Orchestra Model) guitars.

Provides:
- GET /templates - List DXF templates
- GET /graduation - Get graduation thickness maps
- GET /kits - List organized CNC kits
- GET /download/{path} - Download template file

LANE: UTILITY (template/asset operations)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(tags=["OM", "CAM"])

# Base path to OM project assets
OM_BASE = Path(__file__).parent.parent.parent.parent / "OM Project"


# =============================================================================
# SCHEMAS
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
# HELPERS
# =============================================================================


def _scan_om_templates() -> List[OMTemplate]:
    """Scan OM Project folder for DXF templates"""
    templates = []
    if not OM_BASE.exists():
        return templates

    for dxf in OM_BASE.rglob("*.dxf"):
        name = dxf.stem
        if "outline" in name.lower():
            ttype, desc = "outline", "OM body outline for CNC routing"
        elif "mould" in name.lower() or "mold" in name.lower():
            ttype, desc = "mold", "OM body mold template for form building"
        elif "mdf" in name.lower():
            ttype, desc = "mdf", "MDF modification template"
        else:
            ttype, desc = "general", "OM acoustic guitar template"

        templates.append(OMTemplate(
            name=name, type=ttype, format="dxf",
            path=str(dxf.relative_to(OM_BASE)), description=desc
        ))
    return templates


def _scan_graduation_maps() -> List[OMGraduationMap]:
    """Scan for graduation thickness maps (SVG and PDF)"""
    maps = []
    if not OM_BASE.exists():
        return maps

    for svg in OM_BASE.rglob("*Graduation*.svg"):
        name = svg.stem
        surface = "top" if "Top" in name else "back" if "Back" in name else "unknown"
        maps.append(OMGraduationMap(
            name=name, surface=surface, format="svg",
            grid="Grid" in name or "grid" in name,
            path=str(svg.relative_to(OM_BASE))
        ))

    for pdf in OM_BASE.rglob("*Graduation*.pdf"):
        maps.append(OMGraduationMap(
            name=pdf.stem, surface="combined", format="pdf",
            grid=False, path=str(pdf.relative_to(OM_BASE))
        ))
    return maps


def _scan_om_kits() -> List[OMKit]:
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
            files=files, zip_available=zip_path.exists(), path="OM_CAM_Import_Kit"
        ))

    mould_kit_path = OM_BASE / "OM_Mould_CNC_Kit"
    if mould_kit_path.exists():
        files = [f.name for f in mould_kit_path.iterdir() if f.is_file()]
        zip_path = OM_BASE / "OM_Mould_CNC_Kit.zip"
        kits.append(OMKit(
            name="OM Mould CNC Kit",
            description="DXF geometry for CNC-routing an OM body mold.",
            files=files, zip_available=zip_path.exists(), path="OM_Mould_CNC_Kit"
        ))
    return kits


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/templates")
def list_om_templates() -> Dict[str, Any]:
    """List all available OM DXF templates."""
    templates = _scan_om_templates()
    return {
        "ok": True, "model": "om",
        "templates": [t.model_dump() for t in templates],
        "count": len(templates), "base_path": str(OM_BASE)
    }


@router.get("/graduation")
def list_graduation_maps() -> Dict[str, Any]:
    """List OM graduation thickness maps."""
    maps = _scan_graduation_maps()
    return {
        "ok": True, "model": "om",
        "graduation_maps": [m.model_dump() for m in maps],
        "count": len(maps),
        "note": "Graduation maps show target thicknesses in mm for hand/CNC carving"
    }


@router.get("/kits")
def list_cnc_kits() -> Dict[str, Any]:
    """List organized OM CNC kits."""
    kits = _scan_om_kits()
    return {"ok": True, "model": "om", "kits": [k.model_dump() for k in kits], "count": len(kits)}


@router.get("/download/{file_path:path}")
def download_om_file(file_path: str) -> FileResponse:
    """Download an OM template file."""
    full_path = OM_BASE / file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        full_path.resolve().relative_to(OM_BASE.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path traversal attempt")

    return FileResponse(path=full_path, filename=full_path.name, media_type="application/octet-stream")


__all__ = [
    "router",
    "OM_BASE",
    "OMTemplate",
    "OMGraduationMap",
    "OMKit",
]
