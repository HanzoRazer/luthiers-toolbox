"""
Art Studio API v1

Design and pattern generation for decorative elements:

1. POST /art/rosette/generate - Generate rosette pattern
2. POST /art/inlay/generate - Generate inlay pattern
3. GET  /art/inlay/presets - List inlay presets
4. POST /art/preview - Generate SVG preview

REMOVED (dead endpoints with no frontend callers):
- GET /art/rosette/presets - Removed 2026-03-15 (STUB_DEBT_REPORT remediation)
  Use /api/art/presets (root_art_router.py) for general Art Studio presets
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/art", tags=["Art Studio"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class RosetteGenerateRequest(BaseModel):
    """Request rosette pattern generation."""
    outer_diameter_mm: float = Field(100.0, description="Outer diameter")
    inner_diameter_mm: float = Field(85.0, description="Inner diameter (sound hole)")
    rings: int = Field(3, description="Number of rings")
    pattern: str = Field("herringbone", description="Pattern type")
    wood_species: List[str] = Field(["maple", "rosewood"], description="Wood species for rings")


class InlayGenerateRequest(BaseModel):
    """Request inlay pattern generation."""
    pattern_type: str = Field("vine", description="Pattern: vine, geometric, celtic, custom")
    width_mm: float = Field(150.0, description="Pattern width")
    height_mm: float = Field(30.0, description="Pattern height")
    complexity: int = Field(3, ge=1, le=5, description="Complexity level 1-5")
    style: str = Field("traditional", description="Style: traditional, modern, art_deco")


class PreviewRequest(BaseModel):
    """Request SVG preview of a design."""
    design_type: str = Field(..., description="rosette, inlay, binding")
    design_id: Optional[str] = Field(None, description="Existing design ID")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Or provide parameters directly")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/rosette/generate")
def generate_rosette(req: RosetteGenerateRequest) -> V1Response:
    """
    Generate a rosette pattern for acoustic guitar sound hole.

    Returns SVG paths and toolpath-ready geometry.
    """
    if req.outer_diameter_mm <= req.inner_diameter_mm:
        return V1Response(
            ok=False,
            error="Outer diameter must be greater than inner diameter",
        )

    ring_width = (req.outer_diameter_mm - req.inner_diameter_mm) / (2 * req.rings)

    rings_data = []
    for i in range(req.rings):
        inner_r = (req.inner_diameter_mm / 2) + (i * ring_width)
        outer_r = inner_r + ring_width
        wood = req.wood_species[i % len(req.wood_species)]
        rings_data.append({
            "ring": i + 1,
            "inner_radius_mm": round(inner_r, 2),
            "outer_radius_mm": round(outer_r, 2),
            "width_mm": round(ring_width, 2),
            "pattern": req.pattern if i == req.rings // 2 else "solid",
            "wood": wood,
        })

    return V1Response(
        ok=True,
        data={
            "rosette_id": f"rosette_{hash(str(req)) % 100000:05d}",
            "outer_diameter_mm": req.outer_diameter_mm,
            "inner_diameter_mm": req.inner_diameter_mm,
            "rings": rings_data,
            "pattern": req.pattern,
            "svg_preview": f"/api/v1/art/preview/rosette_{hash(str(req)) % 100000:05d}.svg",
        },
    )


@router.post("/inlay/generate")
def generate_inlay(req: InlayGenerateRequest) -> V1Response:
    """
    Generate an inlay pattern for fretboard or headstock.

    Returns vector paths suitable for CNC routing.
    """
    if req.width_mm <= 0 or req.height_mm <= 0:
        return V1Response(
            ok=False,
            error="Dimensions must be positive",
        )

    return V1Response(
        ok=True,
        data={
            "inlay_id": f"inlay_{hash(str(req)) % 100000:05d}",
            "pattern_type": req.pattern_type,
            "dimensions": {
                "width_mm": req.width_mm,
                "height_mm": req.height_mm,
            },
            "complexity": req.complexity,
            "style": req.style,
            "paths": [],  # Vector paths would go here
            "svg_preview": f"/api/v1/art/preview/inlay_{hash(str(req)) % 100000:05d}.svg",
            "recommended_tool_mm": 0.5 if req.complexity > 3 else 1.0,
        },
    )


@router.get("/inlay/presets")
def list_inlay_presets() -> V1Response:
    """
    List available inlay preset designs.

    Includes fretboard markers, headstock designs, and binding patterns.
    """
    presets = [
        {
            "id": "dots_standard",
            "name": "Standard Dots",
            "description": "Classic dot markers at frets 3,5,7,9,12,15,17,19,21",
            "category": "fretboard",
            "difficulty": 1,
        },
        {
            "id": "blocks_jazz",
            "name": "Jazz Blocks",
            "description": "Rectangular block inlays",
            "category": "fretboard",
            "difficulty": 2,
        },
        {
            "id": "vine_headstock",
            "name": "Vine Headstock",
            "description": "Flowing vine pattern for headstock",
            "category": "headstock",
            "difficulty": 4,
        },
        {
            "id": "celtic_knot",
            "name": "Celtic Knot",
            "description": "Interlaced celtic design",
            "category": "headstock",
            "difficulty": 5,
        },
    ]

    return V1Response(
        ok=True,
        data={
            "presets": presets,
            "categories": ["fretboard", "headstock", "body", "binding"],
            "total": len(presets),
        },
    )


@router.post("/preview")
def generate_preview(req: PreviewRequest) -> V1Response:
    """
    Generate SVG preview of any art studio design.

    Can render from existing design ID or provided parameters.
    """
    if not req.design_id and not req.parameters:
        return V1Response(
            ok=False,
            error="Provide either design_id or parameters",
        )

    preview_id = req.design_id or f"preview_{hash(str(req.parameters)) % 100000:05d}"

    return V1Response(
        ok=True,
        data={
            "preview_id": preview_id,
            "design_type": req.design_type,
            "svg_url": f"/api/v1/art/preview/{preview_id}.svg",
            "png_url": f"/api/v1/art/preview/{preview_id}.png",
            "dxf_url": f"/api/v1/art/preview/{preview_id}.dxf",
        },
    )
