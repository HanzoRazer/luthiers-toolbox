"""
Stratocaster Guitar Router
Endpoints for Fender Stratocaster templates, BOM, and design resources
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
import json

router = APIRouter(prefix="/cam/stratocaster", tags=["stratocaster"])


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


@router.get("/templates")
def list_stratocaster_templates():
    """
    List all available Stratocaster DXF templates.
    
    Returns body, neck, fretboard, pickguard, and tremolo cover templates.
    """
    strat_dir = Path("Stratocaster")
    if not strat_dir.exists():
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
    body_top = strat_dir / "Stratocaster BODY(Top).dxf"
    body_bottom = strat_dir / "Stratocaster BODY(Bottom).dxf"
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
    neck_dxf = strat_dir / "Stratocaster NECK.dxf"
    if neck_dxf.exists():
        templates["neck"].append({
            "name": "Stratocaster Neck",
            "file": "Stratocaster NECK.dxf",
            "path": str(neck_dxf),
            "size_kb": round(neck_dxf.stat().st_size / 1024, 2)
        })
    
    # Fretboard template
    fretboard_dxf = strat_dir / "Stratocaster FRETBOARD.dxf"
    if fretboard_dxf.exists():
        templates["fretboard"].append({
            "name": "Stratocaster Fretboard",
            "file": "Stratocaster FRETBOARD.dxf",
            "path": str(fretboard_dxf),
            "size_kb": round(fretboard_dxf.stat().st_size / 1024, 2)
        })
    
    # Pickguard template
    pickguard_dxf = strat_dir / "Stratocaster PICKGUARD.dxf"
    if pickguard_dxf.exists():
        templates["hardware"].append({
            "name": "Stratocaster Pickguard (11-hole)",
            "file": "Stratocaster PICKGUARD.dxf",
            "path": str(pickguard_dxf),
            "size_kb": round(pickguard_dxf.stat().st_size / 1024, 2)
        })
    
    # Tremolo cover template
    tremolo_dxf = strat_dir / "Stratocaster TREMOLO COVER.dxf"
    if tremolo_dxf.exists():
        templates["hardware"].append({
            "name": "Stratocaster Tremolo Cover",
            "file": "Stratocaster TREMOLO COVER.dxf",
            "path": str(tremolo_dxf),
            "size_kb": round(tremolo_dxf.stat().st_size / 1024, 2)
        })
    
    return {
        "ok": True,
        "templates": templates,
        "total_count": sum(len(v) for v in templates.values())
    }


@router.get("/templates/{component}/download")
def download_stratocaster_template(component: str):
    """
    Download specific Stratocaster template.
    
    Component options: body-top, body-bottom, neck, fretboard, pickguard, tremolo
    """
    strat_dir = Path("Stratocaster")
    
    file_map = {
        "body-top": "Stratocaster BODY(Top).dxf",
        "body-bottom": "Stratocaster BODY(Bottom).dxf",
        "neck": "Stratocaster NECK.dxf",
        "fretboard": "Stratocaster FRETBOARD.dxf",
        "pickguard": "Stratocaster PICKGUARD.dxf",
        "tremolo": "Stratocaster TREMOLO COVER.dxf"
    }
    
    if component not in file_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown component. Valid options: {', '.join(file_map.keys())}"
        )
    
    file_path = strat_dir / file_map[component]
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Template file not found: {file_map[component]}"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=file_map[component],
        media_type="application/dxf"
    )


@router.get("/bom")
def get_stratocaster_bom(series: str = "Player II") -> StratocasterBOMResponse:
    """
    Get Stratocaster Bill of Materials with cost estimates.
    
    Series options: "Player II", "American Pro II", "All"
    """
    bom_file = Path("Stratocaster/stratocaster_bom_price_sheet.csv")
    if not bom_file.exists():
        raise HTTPException(
            status_code=404,
            detail="BOM file not found"
        )
    
    import csv
    items = []
    total_low = 0.0
    total_high = 0.0
    
    with open(bom_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter by series if specified
            if series != "All" and row['Series'] != series and row['Series'] != "All":
                continue
            
            try:
                low = float(row['Est. Low (USD)'])
                high = float(row['Est. High (USD)'])
            except ValueError:
                low = high = 0.0
            
            items.append(StratocasterBOMItem(
                item=row['Item'],
                category=row['Category'],
                series=row['Series'],
                est_low_usd=low,
                est_high_usd=high,
                notes=row['Notes']
            ))
            
            total_low += low
            total_high += high
    
    return StratocasterBOMResponse(
        ok=True,
        items=items,
        total_low=round(total_low, 2),
        total_high=round(total_high, 2),
        series=series
    )


@router.get("/specs")
def get_stratocaster_specs():
    """
    Get standard Stratocaster specifications.
    
    Returns dimensions, scale length, hardware specs.
    """
    specs = {
        "scale_length": {
            "inches": 25.5,
            "mm": 648.0
        },
        "body": {
            "shape": "Double cutaway contoured",
            "wood": "Alder or Ash",
            "thickness_mm": 44.5,
            "length_mm": 460.0,
            "width_mm": 320.0
        },
        "neck": {
            "profile": "Modern C",
            "width_at_nut_mm": 42.0,
            "frets": 22,
            "fretboard_radius_mm": 241.0,  # 9.5"
            "joint": "Bolt-on (4-screw)"
        },
        "electronics": {
            "pickups": "3 Single-coil",
            "controls": "1 Volume, 2 Tone, 5-way selector",
            "output": "1/4\" jack"
        },
        "hardware": {
            "bridge": "2-point synchronized tremolo",
            "tuners": "6-in-line sealed",
            "pickguard": "11-hole 3-ply"
        },
        "strings": {
            "count": 6,
            "gauge": ".009-.042 (standard)",
            "spacing_at_bridge_mm": 52.0,
            "spacing_at_nut_mm": 35.0
        }
    }
    
    return {"ok": True, "specs": specs, "model": "Fender Stratocaster"}


@router.get("/resources")
def get_stratocaster_resources():
    """
    List available Stratocaster resources (PDFs, plans, STL files).
    """
    strat_dir = Path("Stratocaster")
    
    resources = {
        "plans": [],
        "stl_files": [],
        "documentation": []
    }
    
    # Find PDF plans
    for pdf in strat_dir.glob("*.pdf"):
        resources["plans"].append({
            "name": pdf.stem,
            "file": pdf.name,
            "size_kb": round(pdf.stat().st_size / 1024, 2)
        })
    
    # Find STL files (3D models)
    for stl in strat_dir.glob("*.stl"):
        resources["stl_files"].append({
            "name": stl.stem,
            "file": stl.name,
            "size_kb": round(stl.stat().st_size / 1024, 2)
        })
    
    # Check for project folder
    project_dir = strat_dir / "Fender Stratocaster_Project"
    if project_dir.exists():
        resources["documentation"].append({
            "name": "Fender Stratocaster Project Files",
            "path": str(project_dir),
            "type": "directory"
        })
    
    return {"ok": True, "resources": resources}


@router.get("/presets")
def get_stratocaster_presets():
    """
    Get recommended CAM presets for Stratocaster components.
    
    Returns tool recommendations, feeds/speeds, and operation sequences.
    """
    presets = {
        "body_routing": {
            "tool": "1/4\" (6mm) upcut end mill",
            "operations": [
                {
                    "name": "Body outline rough",
                    "tool_d_mm": 6.0,
                    "stepdown_mm": 3.0,
                    "feed_xy_mm_min": 1200,
                    "rpm": 18000
                },
                {
                    "name": "Body contour finish",
                    "tool_d_mm": 6.0,
                    "stepdown_mm": 1.5,
                    "feed_xy_mm_min": 1000,
                    "rpm": 18000
                },
                {
                    "name": "Neck pocket",
                    "tool_d_mm": 6.0,
                    "stepdown_mm": 2.0,
                    "feed_xy_mm_min": 800,
                    "rpm": 18000,
                    "notes": "Tight fit required - 0.05mm tolerance"
                },
                {
                    "name": "Pickup cavities",
                    "tool_d_mm": 6.0,
                    "stepdown_mm": 3.0,
                    "feed_xy_mm_min": 1200,
                    "rpm": 18000,
                    "depth_mm": 18.0
                },
                {
                    "name": "Control cavity",
                    "tool_d_mm": 6.0,
                    "stepdown_mm": 3.0,
                    "feed_xy_mm_min": 1200,
                    "rpm": 18000,
                    "depth_mm": 35.0
                }
            ]
        },
        "neck_routing": {
            "tool": "1/4\" (6mm) end mill",
            "operations": [
                {
                    "name": "Truss rod channel",
                    "tool_d_mm": 6.0,
                    "depth_mm": 9.0,
                    "width_mm": 6.5,
                    "feed_xy_mm_min": 600
                },
                {
                    "name": "Neck outline",
                    "tool_d_mm": 6.0,
                    "stepdown_mm": 2.0,
                    "feed_xy_mm_min": 1000
                }
            ]
        },
        "pickguard": {
            "tool": "1/8\" (3mm) end mill",
            "operations": [
                {
                    "name": "Pickguard outline",
                    "tool_d_mm": 3.0,
                    "material": "3-ply plastic",
                    "thickness_mm": 3.0,
                    "feed_xy_mm_min": 800,
                    "rpm": 15000,
                    "tabs": True,
                    "notes": "Use 4-6 tabs to prevent warping"
                },
                {
                    "name": "Screw holes (11)",
                    "tool": "2mm drill",
                    "peck_depth_mm": 1.0
                }
            ]
        },
        "material_recommendations": {
            "body": "Alder or Swamp Ash",
            "neck": "Hard Maple",
            "fretboard": "Rosewood or Maple"
        }
    }
    
    return {"ok": True, "presets": presets, "model": "Fender Stratocaster"}


@router.get("/health")
def stratocaster_health():
    """Health check for Stratocaster module"""
    strat_dir = Path("Stratocaster")
    templates_exist = strat_dir.exists()
    
    template_files = [
        "Stratocaster BODY(Top).dxf",
        "Stratocaster BODY(Bottom).dxf",
        "Stratocaster NECK.dxf",
        "Stratocaster FRETBOARD.dxf",
        "Stratocaster PICKGUARD.dxf",
        "Stratocaster TREMOLO COVER.dxf"
    ]
    
    available_templates = []
    if templates_exist:
        available_templates = [
            f for f in template_files
            if (strat_dir / f).exists()
        ]
    
    return {
        "ok": True,
        "module": "stratocaster",
        "templates_dir_exists": templates_exist,
        "available_templates": len(available_templates),
        "total_templates": len(template_files),
        "bom_available": (strat_dir / "stratocaster_bom_price_sheet.csv").exists() if templates_exist else False
    }
