"""
Stratocaster CAM Router
=======================

CAM operations for Stratocaster guitars: template downloads, BOM, toolpath previews.
Instrument specs moved to /api/instruments/guitar/stratocaster/*

Endpoints:
  GET /health - CAM subsystem health
  GET /templates - List DXF templates
  GET /bom - Bill of materials
  GET /preview - SVG preview
  GET /download/{file_path} - Download template file

Wave 15: Option C API Restructuring
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(tags=["Stratocaster", "CAM"])


# Base path to Stratocaster assets
STRAT_BASE = Path("Stratocaster")


# =============================================================================
# MODELS
# =============================================================================

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


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/health")
def stratocaster_cam_health() -> Dict[str, Any]:
    """
    Get Stratocaster CAM subsystem health status.
    """
    return {
        "ok": STRAT_BASE.exists(),
        "subsystem": "stratocaster_cam",
        "model_id": "stratocaster",
        "strat_path": str(STRAT_BASE),
        "strat_exists": STRAT_BASE.exists(),
        "capabilities": [
            "templates",
            "bom",
            "preview",
            "file_download"
        ],
        "instrument_spec": "/api/instruments/guitar/stratocaster/spec"
    }


@router.get("/templates")
def list_stratocaster_templates() -> Dict[str, Any]:
    """
    List all available Stratocaster DXF templates.
    
    Returns body, neck, fretboard, pickguard, and tremolo cover templates.
    """
    if not STRAT_BASE.exists():
        raise HTTPException(
            status_code=404,
            detail="Stratocaster templates directory not found"
        )
    
    templates = {
        "body": [],
        "neck": [],
        "fretboard": [],
        "pickguard": [],
        "hardware": []
    }
    
    # Body templates
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
    
    # Neck template
    neck_dxf = STRAT_BASE / "Stratocaster NECK.dxf"
    if neck_dxf.exists():
        templates["neck"].append({
            "name": "Stratocaster Neck",
            "file": "Stratocaster NECK.dxf",
            "path": str(neck_dxf),
            "size_kb": round(neck_dxf.stat().st_size / 1024, 2)
        })
    
    # Fretboard template
    fretboard_dxf = STRAT_BASE / "Stratocaster FRETBOARD.dxf"
    if fretboard_dxf.exists():
        templates["fretboard"].append({
            "name": "Stratocaster Fretboard",
            "file": "Stratocaster FRETBOARD.dxf",
            "path": str(fretboard_dxf),
            "size_kb": round(fretboard_dxf.stat().st_size / 1024, 2)
        })
    
    # Pickguard templates
    for pg_file in STRAT_BASE.glob("*Pickguard*.dxf"):
        templates["pickguard"].append({
            "name": pg_file.stem,
            "file": pg_file.name,
            "path": str(pg_file),
            "size_kb": round(pg_file.stat().st_size / 1024, 2)
        })
    
    return {
        "ok": True,
        "model": "stratocaster",
        "templates": templates,
        "total_count": sum(len(v) for v in templates.values())
    }


@router.get("/bom")
def get_stratocaster_bom(series: str = "standard") -> StratocasterBOMResponse:
    """
    Get Stratocaster bill of materials with cost estimates.
    
    Args:
        series: standard, deluxe, or vintage
    """
    # Standard Stratocaster BOM
    standard_items = [
        StratocasterBOMItem(
            item="Alder Body Blank",
            category="Wood",
            series="standard",
            est_low_usd=60.0,
            est_high_usd=120.0,
            notes="2-piece book-matched alder"
        ),
        StratocasterBOMItem(
            item="Maple Neck Blank",
            category="Wood",
            series="standard",
            est_low_usd=40.0,
            est_high_usd=80.0,
            notes="Quartersawn maple, 1\" thick"
        ),
        StratocasterBOMItem(
            item="Rosewood Fingerboard",
            category="Wood",
            series="standard",
            est_low_usd=25.0,
            est_high_usd=50.0,
            notes="Indian rosewood, slotted"
        ),
        StratocasterBOMItem(
            item="Pickups (3x single coil)",
            category="Electronics",
            series="standard",
            est_low_usd=50.0,
            est_high_usd=200.0,
            notes="SSS configuration"
        ),
        StratocasterBOMItem(
            item="Tremolo Bridge Assembly",
            category="Hardware",
            series="standard",
            est_low_usd=30.0,
            est_high_usd=150.0,
            notes="6-screw synchronized tremolo"
        ),
        StratocasterBOMItem(
            item="Tuning Machines (6x)",
            category="Hardware",
            series="standard",
            est_low_usd=25.0,
            est_high_usd=100.0,
            notes="Vintage-style or locking"
        ),
        StratocasterBOMItem(
            item="Pickguard",
            category="Hardware",
            series="standard",
            est_low_usd=10.0,
            est_high_usd=40.0,
            notes="11-hole, 3-ply"
        ),
        StratocasterBOMItem(
            item="Electronics Kit",
            category="Electronics",
            series="standard",
            est_low_usd=20.0,
            est_high_usd=60.0,
            notes="Pots, caps, switch, jack"
        ),
        StratocasterBOMItem(
            item="Frets (22x)",
            category="Hardware",
            series="standard",
            est_low_usd=10.0,
            est_high_usd=25.0,
            notes="Medium jumbo nickel-silver"
        ),
        StratocasterBOMItem(
            item="Nut",
            category="Hardware",
            series="standard",
            est_low_usd=5.0,
            est_high_usd=20.0,
            notes="Bone or synthetic"
        ),
    ]
    
    items = standard_items  # Could filter by series
    total_low = sum(item.est_low_usd for item in items)
    total_high = sum(item.est_high_usd for item in items)
    
    return StratocasterBOMResponse(
        ok=True,
        items=items,
        total_low=total_low,
        total_high=total_high,
        series=series
    )


@router.get("/preview")
def get_stratocaster_preview() -> Dict[str, Any]:
    """
    Get SVG preview of Stratocaster body outline.
    """
    preview_svg = STRAT_BASE / "preview.svg"
    
    return {
        "ok": True,
        "model": "stratocaster",
        "preview_available": preview_svg.exists(),
        "preview_path": str(preview_svg) if preview_svg.exists() else None,
        "dimensions": {
            "body_length_mm": 406.4,
            "body_width_mm": 317.5,
            "scale_length_mm": 648.0
        }
    }


@router.get("/download/{file_path:path}")
def download_stratocaster_file(file_path: str) -> FileResponse:
    """
    Download a Stratocaster template file.
    """
    full_path = STRAT_BASE / file_path
    
    if not full_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path}"
        )
    
    try:
        full_path.resolve().relative_to(STRAT_BASE.resolve())
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
