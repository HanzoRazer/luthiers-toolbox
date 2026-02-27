# services/api/app/art_studio/bracing_router.py

"""
Art Studio Bracing Router

Provides endpoints for bracing calculations used by the Art Studio UI.
These endpoints are designed for interactive design workflows where
luthiers need real-time feedback on bracing properties.

Endpoints:
    POST /preview    - Calculate section properties and mass for a single brace
    POST /batch      - Calculate properties for multiple braces
    GET  /presets    - Get common bracing presets (X-brace, ladder, etc.)
    POST /export-dxf - Export bracing layout to DXF (R12-R18)
"""

from __future__ import annotations

import io
import math
from typing import List, Optional, Literal
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..calculators import bracing_calc
from ..calculators.bracing_calc import BracingCalcInput, BraceSectionResult
from ..util.dxf_compat import (
    create_document, add_polyline, add_rectangle,
    validate_version, DxfVersion, DXF_VERSIONS
)

router = APIRouter(
    prefix="/art-studio/bracing",
    tags=["Art Studio - Bracing"],
)


# --- Request/Response Models ---

class BracingPreviewRequest(BaseModel):
    """Request for bracing preview calculation."""
    
    profile_type: str = Field(
        default="parabolic",
        description="Brace profile: rectangular, triangular, parabolic, scalloped"
    )
    width_mm: float = Field(default=12.0, ge=1.0, le=50.0)
    height_mm: float = Field(default=8.0, ge=1.0, le=30.0)
    length_mm: float = Field(default=300.0, ge=10.0, le=600.0)
    density_kg_m3: float = Field(
        default=420.0, ge=200.0, le=1200.0,
        description="Wood density (Sitka ~420, Maple ~650, Ebony ~1100)"
    )
    
    def to_calc_input(self) -> BracingCalcInput:
        return BracingCalcInput(
            profile_type=self.profile_type,
            width_mm=self.width_mm,
            height_mm=self.height_mm,
            length_mm=self.length_mm,
            density_kg_m3=self.density_kg_m3,
        )


class BracingPreviewResponse(BaseModel):
    """Response from bracing preview calculation."""
    
    section: BraceSectionResult
    mass_grams: float
    stiffness_estimate: Optional[float] = Field(
        None, description="Relative stiffness estimate (area × length)"
    )


class BracingBatchRequest(BaseModel):
    """Request for batch bracing calculation."""
    
    braces: List[BracingPreviewRequest]
    name: str = Field(default="Bracing Set", description="Name for this brace set")


class BracingBatchResponse(BaseModel):
    """Response from batch bracing calculation."""
    
    name: str
    braces: List[dict]
    totals: dict


class BracingPreset(BaseModel):
    """A bracing preset configuration."""
    
    id: str
    name: str
    description: str
    braces: List[BracingPreviewRequest]


# --- Endpoints ---

@router.post("/preview", response_model=BracingPreviewResponse)
def preview_bracing(req: BracingPreviewRequest) -> BracingPreviewResponse:
    """
    Calculate bracing section properties and mass.
    
    Given a bracing configuration, returns:
    - Section properties (profile type, dimensions, area)
    - Estimated mass in grams
    - Relative stiffness estimate
    
    This endpoint is optimized for interactive UI use where
    luthiers adjust parameters and see real-time results.
    """
    calc_input = req.to_calc_input()
    section = bracing_calc.calculate_brace_section(calc_input)
    mass = bracing_calc.estimate_mass_grams(calc_input)
    
    # Simple stiffness estimate: area × length (relative, not absolute)
    stiffness = section.area_mm2 * req.length_mm
    
    return BracingPreviewResponse(
        section=section,
        mass_grams=round(mass, 2),
        stiffness_estimate=round(stiffness, 1)
    )


@router.post("/batch", response_model=BracingBatchResponse)
def batch_bracing(req: BracingBatchRequest) -> BracingBatchResponse:
    """
    Calculate properties for multiple braces.
    
    Useful for evaluating complete bracing patterns like:
    - X-bracing sets
    - Ladder bracing
    - Fan bracing
    
    Returns individual brace properties plus totals.
    """
    calc_inputs = [b.to_calc_input() for b in req.braces]
    result = bracing_calc.calculate_brace_set(calc_inputs)
    
    return BracingBatchResponse(
        name=req.name,
        braces=result["braces"],
        totals=result["totals"]
    )


@router.get("/presets", response_model=List[BracingPreset])
def get_bracing_presets() -> List[BracingPreset]:
    """
    Get common bracing presets.
    
    Returns pre-configured brace sets for common patterns.
    These can be used as starting points for custom designs.
    """
    return [
        BracingPreset(
            id="x-brace-standard",
            name="Standard X-Brace",
            description="Classic Martin-style X-bracing for steel string acoustic",
            braces=[
                BracingPreviewRequest(
                    profile_type="parabolic",
                    width_mm=12.0,
                    height_mm=8.0,
                    length_mm=280.0,
                    density_kg_m3=420.0,
                ),
                BracingPreviewRequest(
                    profile_type="parabolic",
                    width_mm=12.0,
                    height_mm=8.0,
                    length_mm=280.0,
                    density_kg_m3=420.0,
                ),
            ]
        ),
        BracingPreset(
            id="ladder-classical",
            name="Classical Ladder Bracing",
            description="Traditional fan-style bracing for classical guitar",
            braces=[
                BracingPreviewRequest(
                    profile_type="rectangular",
                    width_mm=8.0,
                    height_mm=5.0,
                    length_mm=200.0,
                    density_kg_m3=380.0,
                ),
                BracingPreviewRequest(
                    profile_type="rectangular",
                    width_mm=8.0,
                    height_mm=5.0,
                    length_mm=220.0,
                    density_kg_m3=380.0,
                ),
                BracingPreviewRequest(
                    profile_type="rectangular",
                    width_mm=8.0,
                    height_mm=5.0,
                    length_mm=240.0,
                    density_kg_m3=380.0,
                ),
            ]
        ),
        BracingPreset(
            id="scalloped-x",
            name="Scalloped X-Brace",
            description="Lighter scalloped X-bracing for improved resonance",
            braces=[
                BracingPreviewRequest(
                    profile_type="scalloped",
                    width_mm=14.0,
                    height_mm=10.0,
                    length_mm=300.0,
                    density_kg_m3=420.0,
                ),
                BracingPreviewRequest(
                    profile_type="scalloped",
                    width_mm=14.0,
                    height_mm=10.0,
                    length_mm=300.0,
                    density_kg_m3=420.0,
                ),
            ]
        ),
    ]


# --- DXF Export Models ---

class BraceLayoutItem(BaseModel):
    """A single brace in a layout with position."""
    
    profile_type: str = Field(default="parabolic")
    width_mm: float = Field(default=12.0, ge=1.0, le=50.0)
    height_mm: float = Field(default=8.0, ge=1.0, le=30.0)
    length_mm: float = Field(default=300.0, ge=10.0, le=600.0)
    
    # Position and rotation
    x_mm: float = Field(default=0.0, description="X position of brace center")
    y_mm: float = Field(default=0.0, description="Y position of brace center")
    angle_deg: float = Field(default=0.0, description="Rotation angle in degrees")
    
    # Optional metadata
    name: str = Field(default="", description="Brace name/label")


class BracingDxfExportRequest(BaseModel):
    """Request for DXF export of bracing layout."""
    
    braces: List[BraceLayoutItem] = Field(
        ..., min_length=1,
        description="List of braces with positions"
    )
    
    # DXF version selection (R12-R18)
    dxf_version: str = Field(
        default="R12",
        description="DXF version: R12, R13, R14, R2000/R15, R2004/R16, R2007/R17, R2010/R18"
    )
    
    # Layout options
    soundhole_diameter_mm: Optional[float] = Field(
        None, ge=50.0, le=120.0,
        description="Soundhole diameter for reference circle"
    )
    soundhole_x_mm: float = Field(default=0.0, description="Soundhole center X")
    soundhole_y_mm: float = Field(default=0.0, description="Soundhole center Y")
    
    # Export options
    include_centerlines: bool = Field(
        default=True,
        description="Include brace centerlines"
    )
    include_outlines: bool = Field(
        default=True, 
        description="Include brace outline rectangles"
    )
    include_labels: bool = Field(
        default=True,
        description="Include brace name labels"
    )
    
    filename: str = Field(
        default="bracing_layout",
        description="Base filename (without .dxf extension)"
    )


class BracingDxfExportResponse(BaseModel):
    """Response metadata for DXF export."""
    
    filename: str
    dxf_version: str
    brace_count: int
    file_size_bytes: int


# --- DXF Export Endpoint ---

@router.post("/export-dxf")
def export_bracing_dxf(req: BracingDxfExportRequest):
    """
    Export bracing layout to DXF file.
    
    Supports DXF versions R12 through R18 (R2010).
    R12 is recommended for maximum CAM software compatibility
    (the genesis of Luthier's ToolBox).
    
    The export includes:
    - BRACES layer: Brace outline rectangles
    - CENTERLINES layer: Brace centerlines
    - REFERENCE layer: Soundhole reference circle
    - LABELS layer: Brace name annotations
    
    Returns: DXF file as streaming download
    """
    # Validate and normalize DXF version
    try:
        version = validate_version(req.dxf_version)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create DXF document with selected version
    doc = create_document(version)
    msp = doc.modelspace()
    
    # Define layers with colors
    layers = [
        ('BRACES', 3),       # Green - brace outlines
        ('CENTERLINES', 1),  # Red - centerlines
        ('REFERENCE', 5),    # Blue - soundhole reference
        ('LABELS', 7),       # White - text labels
    ]
    for layer_name, color in layers:
        doc.layers.add(name=layer_name, color=color)
    
    # Draw soundhole reference circle if specified
    if req.soundhole_diameter_mm:
        msp.add_circle(
            center=(req.soundhole_x_mm, req.soundhole_y_mm),
            radius=req.soundhole_diameter_mm / 2,
            dxfattribs={'layer': 'REFERENCE'}
        )
    
    # Draw each brace
    for idx, brace in enumerate(req.braces):
        angle_rad = math.radians(brace.angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Half dimensions
        half_length = brace.length_mm / 2
        half_width = brace.width_mm / 2
        
        # Calculate rotated corners for brace outline
        if req.include_outlines:
            corners = []
            for dx, dy in [
                (-half_length, -half_width),
                (half_length, -half_width),
                (half_length, half_width),
                (-half_length, half_width),
            ]:
                # Rotate and translate
                rx = dx * cos_a - dy * sin_a + brace.x_mm
                ry = dx * sin_a + dy * cos_a + brace.y_mm
                corners.append((rx, ry))
            
            # Draw outline (version-aware: LINE for R12, LWPOLYLINE for R13+)
            add_polyline(msp, corners, layer='BRACES', closed=True, version=version)
        
        # Draw centerline
        if req.include_centerlines:
            # Centerline endpoints
            x1 = -half_length * cos_a + brace.x_mm
            y1 = -half_length * sin_a + brace.y_mm
            x2 = half_length * cos_a + brace.x_mm
            y2 = half_length * sin_a + brace.y_mm
            
            msp.add_line(
                (x1, y1), (x2, y2),
                dxfattribs={'layer': 'CENTERLINES'}
            )
        
        # Add label
        if req.include_labels:
            label = brace.name or f"Brace {idx + 1}"
            # Position label slightly above brace center
            label_offset = half_width + 3  # 3mm above
            lx = -label_offset * sin_a + brace.x_mm
            ly = label_offset * cos_a + brace.y_mm
            
            msp.add_text(
                label,
                dxfattribs={
                    'layer': 'LABELS',
                    'height': 3.0,
                    'rotation': brace.angle_deg,
                    'insert': (lx, ly),
                }
            )
    
    # Write to text buffer first, then encode to bytes
    text_buffer = io.StringIO()
    doc.write(text_buffer)
    text_buffer.seek(0)
    dxf_bytes = text_buffer.getvalue().encode('utf-8')
    
    # Generate filename
    filename = f"{req.filename}.dxf"
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(dxf_bytes),
        media_type="application/dxf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-DXF-Version": version,
            "X-Brace-Count": str(len(req.braces)),
        }
    )


@router.get("/dxf-versions")
def get_dxf_versions() -> dict:
    """
    Get available DXF versions for export.
    
    Returns version info including:
    - Version name
    - AutoCAD code
    - LWPOLYLINE support
    - Recommended use case
    """
    versions = []
    for name, ac_code in DXF_VERSIONS.items():
        versions.append({
            "version": name,
            "ac_code": ac_code,
            "supports_lwpolyline": name != "R12",
            "recommended": name == "R12",
            "notes": "Genesis - Maximum CAM compatibility" if name == "R12" else ""
        })
    
    return {
        "default": "R12",
        "versions": sorted(versions, key=lambda v: v["ac_code"]),
        "genesis_note": "R12 doesn't support LWPOLYLINE - uses LINE segments for maximum CAM compatibility"
    }
