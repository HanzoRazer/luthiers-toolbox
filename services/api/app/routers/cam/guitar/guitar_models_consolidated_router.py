"""
Guitar Models CAM Routers (Consolidated)
=========================================

CAM operations for specific guitar models: archtop, OM, Stratocaster.

Consolidated from:
    - archtop_cam_router.py (6 routes)
    - om_cam_router.py (4 routes)
    - stratocaster_cam_router.py (4 routes)

Total: 14 routes under /api/cam/guitar/{model}

LANE: UTILITY (template/asset operations)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints:
    Archtop (/archtop):
        POST /contours/csv      - Generate contours from CSV
        POST /contours/outline  - Generate contours from DXF
        POST /fit               - Calculate bridge fit parameters
        POST /bridge            - Generate floating bridge DXF
        POST /saddle            - Generate compensated saddle profile

    OM (/om):
        GET /templates          - List DXF templates
        GET /graduation         - Get graduation maps
        GET /kits               - List CNC kits
        GET /download/{path}    - Download template file

    Stratocaster (/stratocaster):
        GET /templates          - List DXF templates
        GET /bom                - Bill of materials
        GET /preview            - SVG preview
        GET /download/{path}    - Download template file

Wave 15/20: Option C API Restructuring
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel


# ===========================================================================
# Sub-routers with prefixes
# ===========================================================================

archtop_router = APIRouter(tags=["Archtop", "CAM"])
om_router = APIRouter(tags=["OM", "CAM"])
stratocaster_router = APIRouter(tags=["Stratocaster", "CAM"])


# ===========================================================================
# ARCHTOP MODELS
# ===========================================================================

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


# ===========================================================================
# ARCHTOP ENDPOINTS
# ===========================================================================

@archtop_router.post("/contours/csv")
def generate_contours_from_csv(req: ArchtopContourCSVRequest) -> Dict[str, Any]:
    """Generate archtop contour rings from CSV point cloud."""
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
        return {"ok": True, "out_dir": str(out_dir), "files": files, "stdout": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Contour generation failed: {e.stderr}")


@archtop_router.post("/contours/outline")
def generate_contours_from_outline(req: ArchtopContourOutlineRequest) -> Dict[str, Any]:
    """Generate scaled contour rings from DXF outline (Mottola method)."""
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = [p.name for p in out_dir.glob(f"{req.out_prefix}*")]
        return {"ok": True, "out_dir": str(out_dir), "files": files, "stdout": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Contour generation failed: {e.stderr}")


@archtop_router.post("/fit")
def calculate_bridge_fit(req: ArchtopFitRequest) -> Dict[str, Any]:
    """Calculate neck angle, bridge height range, and string compensation."""
    neck_angle_rad = math.radians(req.neck_angle_deg)
    fingerboard_height_at_end = math.tan(neck_angle_rad) * req.fingerboard_extension_mm
    bridge_height_mm = fingerboard_height_at_end + req.top_arch_height_mm + 10.0

    compensations = [3.0, 2.5, 2.2, 2.0, 1.8, 1.5]
    avg_comp = sum(compensations) / len(compensations)
    saddle_line_mm_from_nut = req.scale_length_mm + avg_comp

    return {
        "ok": True,
        "input": req.model_dump(),
        "fit_parameters": {
            "bridge_height_mm": round(bridge_height_mm, 2),
            "bridge_height_range_mm": [round(bridge_height_mm - 2, 2), round(bridge_height_mm + 2, 2)],
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


@archtop_router.post("/bridge")
def generate_bridge_dxf(req: ArchtopBridgeRequest) -> Dict[str, Any]:
    """Generate floating bridge DXF from fit parameters."""
    script = Path("services/api/app/cam/archtop_bridge_generator.py")
    if not script.exists():
        return {
            "ok": False,
            "error": "Bridge generator script not implemented",
            "note": "Manual bridge design required - use fit parameters from /fit endpoint"
        }
    return {"ok": False, "error": "Bridge generator not yet implemented", "requested": req.model_dump()}


@archtop_router.post("/saddle")
def generate_saddle_profile(req: ArchtopSaddleRequest) -> Dict[str, Any]:
    """Generate compensated saddle profile from fit parameters."""
    script = Path("services/api/app/cam/archtop_saddle_generator.py")
    if not script.exists():
        return {
            "ok": False,
            "error": "Saddle generator script not implemented",
            "note": "Manual saddle design required - use compensations from /fit endpoint"
        }
    return {"ok": False, "error": "Saddle generator not yet implemented", "requested": req.model_dump()}


# ===========================================================================
# OM MODELS
# ===========================================================================

# Base path to OM project assets
OM_BASE = Path(__file__).parent.parent.parent.parent / "OM Project"


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


# ===========================================================================
# OM ENDPOINTS
# ===========================================================================

@om_router.get("/templates")
def list_om_templates() -> Dict[str, Any]:
    """List all available OM DXF templates."""
    templates = _scan_om_templates()
    return {
        "ok": True, "model": "om",
        "templates": [t.model_dump() for t in templates],
        "count": len(templates), "base_path": str(OM_BASE)
    }


@om_router.get("/graduation")
def list_graduation_maps() -> Dict[str, Any]:
    """List OM graduation thickness maps."""
    maps = _scan_graduation_maps()
    return {
        "ok": True, "model": "om",
        "graduation_maps": [m.model_dump() for m in maps],
        "count": len(maps),
        "note": "Graduation maps show target thicknesses in mm for hand/CNC carving"
    }


@om_router.get("/kits")
def list_cnc_kits() -> Dict[str, Any]:
    """List organized OM CNC kits."""
    kits = _scan_om_kits()
    return {"ok": True, "model": "om", "kits": [k.model_dump() for k in kits], "count": len(kits)}


@om_router.get("/download/{file_path:path}")
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


# ===========================================================================
# STRATOCASTER MODELS
# ===========================================================================

STRAT_BASE = Path("Stratocaster")


class StratocasterBOMItem(BaseModel):
    """Bill of Materials item"""
    item: str
    category: str
    series: str
    est_low_usd: float
    est_high_usd: float
    notes: str


class StratocasterBOMResponse(BaseModel):
    """BOM with cost estimates"""
    ok: bool
    items: List[StratocasterBOMItem]
    total_low: float
    total_high: float
    series: str


# ===========================================================================
# STRATOCASTER ENDPOINTS
# ===========================================================================

@stratocaster_router.get("/templates")
def list_stratocaster_templates() -> Dict[str, Any]:
    """List all available Stratocaster DXF templates."""
    if not STRAT_BASE.exists():
        raise HTTPException(status_code=404, detail="Stratocaster templates directory not found")

    templates = {"body": [], "neck": [], "fretboard": [], "pickguard": [], "hardware": []}

    body_top = STRAT_BASE / "Stratocaster BODY(Top).dxf"
    body_bottom = STRAT_BASE / "Stratocaster BODY(Bottom).dxf"
    if body_top.exists():
        templates["body"].append({
            "name": "Stratocaster Body Top",
            "file": "Stratocaster BODY(Top).dxf",
            "path": str(body_top),
            "size_kb": round(body_top.stat().st_size / 1024, 2)
        })
    if body_bottom.exists():
        templates["body"].append({
            "name": "Stratocaster Body Bottom",
            "file": "Stratocaster BODY(Bottom).dxf",
            "path": str(body_bottom),
            "size_kb": round(body_bottom.stat().st_size / 1024, 2)
        })

    neck_dxf = STRAT_BASE / "Stratocaster NECK.dxf"
    if neck_dxf.exists():
        templates["neck"].append({
            "name": "Stratocaster Neck", "file": "Stratocaster NECK.dxf",
            "path": str(neck_dxf), "size_kb": round(neck_dxf.stat().st_size / 1024, 2)
        })

    fretboard_dxf = STRAT_BASE / "Stratocaster FRETBOARD.dxf"
    if fretboard_dxf.exists():
        templates["fretboard"].append({
            "name": "Stratocaster Fretboard", "file": "Stratocaster FRETBOARD.dxf",
            "path": str(fretboard_dxf), "size_kb": round(fretboard_dxf.stat().st_size / 1024, 2)
        })

    for pg_file in STRAT_BASE.glob("*Pickguard*.dxf"):
        templates["pickguard"].append({
            "name": pg_file.stem, "file": pg_file.name,
            "path": str(pg_file), "size_kb": round(pg_file.stat().st_size / 1024, 2)
        })

    return {
        "ok": True, "model": "stratocaster", "templates": templates,
        "total_count": sum(len(v) for v in templates.values())
    }


@stratocaster_router.get("/bom")
def get_stratocaster_bom(series: str = "standard") -> StratocasterBOMResponse:
    """Get Stratocaster bill of materials with cost estimates."""
    standard_items = [
        StratocasterBOMItem(item="Alder Body Blank", category="Wood", series="standard",
                            est_low_usd=60.0, est_high_usd=120.0, notes="2-piece book-matched alder"),
        StratocasterBOMItem(item="Maple Neck Blank", category="Wood", series="standard",
                            est_low_usd=40.0, est_high_usd=80.0, notes="Quartersawn maple, 1\" thick"),
        StratocasterBOMItem(item="Rosewood Fingerboard", category="Wood", series="standard",
                            est_low_usd=25.0, est_high_usd=50.0, notes="Indian rosewood, slotted"),
        StratocasterBOMItem(item="Pickups (3x single coil)", category="Electronics", series="standard",
                            est_low_usd=50.0, est_high_usd=200.0, notes="SSS configuration"),
        StratocasterBOMItem(item="Tremolo Bridge Assembly", category="Hardware", series="standard",
                            est_low_usd=30.0, est_high_usd=150.0, notes="6-screw synchronized tremolo"),
        StratocasterBOMItem(item="Tuning Machines (6x)", category="Hardware", series="standard",
                            est_low_usd=25.0, est_high_usd=100.0, notes="Vintage-style or locking"),
        StratocasterBOMItem(item="Pickguard", category="Hardware", series="standard",
                            est_low_usd=10.0, est_high_usd=40.0, notes="11-hole, 3-ply"),
        StratocasterBOMItem(item="Electronics Kit", category="Electronics", series="standard",
                            est_low_usd=20.0, est_high_usd=60.0, notes="Pots, caps, switch, jack"),
        StratocasterBOMItem(item="Frets (22x)", category="Hardware", series="standard",
                            est_low_usd=10.0, est_high_usd=25.0, notes="Medium jumbo nickel-silver"),
        StratocasterBOMItem(item="Nut", category="Hardware", series="standard",
                            est_low_usd=5.0, est_high_usd=20.0, notes="Bone or synthetic"),
    ]

    items = standard_items
    total_low = sum(item.est_low_usd for item in items)
    total_high = sum(item.est_high_usd for item in items)

    return StratocasterBOMResponse(ok=True, items=items, total_low=total_low, total_high=total_high, series=series)


@stratocaster_router.get("/preview")
def get_stratocaster_preview() -> Dict[str, Any]:
    """Get SVG preview of Stratocaster body outline."""
    preview_svg = STRAT_BASE / "preview.svg"
    return {
        "ok": True, "model": "stratocaster",
        "preview_available": preview_svg.exists(),
        "preview_path": str(preview_svg) if preview_svg.exists() else None,
        "dimensions": {"body_length_mm": 406.4, "body_width_mm": 317.5, "scale_length_mm": 648.0}
    }


@stratocaster_router.get("/download/{file_path:path}")
def download_stratocaster_file(file_path: str) -> FileResponse:
    """Download a Stratocaster template file."""
    full_path = STRAT_BASE / file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        full_path.resolve().relative_to(STRAT_BASE.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path traversal attempt")

    return FileResponse(path=full_path, filename=full_path.name, media_type="application/octet-stream")


# ===========================================================================
# Aggregate Router
# ===========================================================================

router = APIRouter(tags=["Guitar", "CAM"])
router.include_router(archtop_router, prefix="/archtop", tags=["Archtop", "CAM"])
router.include_router(om_router, prefix="/om", tags=["OM", "CAM"])
router.include_router(stratocaster_router, prefix="/stratocaster", tags=["Stratocaster", "CAM"])

__all__ = ["router", "archtop_router", "om_router", "stratocaster_router"]
