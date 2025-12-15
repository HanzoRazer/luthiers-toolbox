"""
Neck Generator Router - Luthier's ToolBox

FastAPI router for neck and headstock G-code generation.

Endpoints:
    POST /api/cam/neck/generate     - Generate neck G-code
    POST /api/cam/neck/export/multi - Multi-post ZIP bundle
    GET  /api/cam/neck/presets      - List available presets
    GET  /api/cam/neck/headstocks   - List headstock styles
    GET  /api/cam/neck/profiles     - List neck profiles
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from io import BytesIO
import zipfile
import json

from ..generators.neck_headstock_generator import (
    NeckGenerator,
    NeckGCodeGenerator,
    NeckDimensions,
    HeadstockStyle,
    NeckProfile,
    NECK_PRESETS,
    NECK_TOOLS,
    generate_headstock_outline,
    generate_tuner_positions,
)


router = APIRouter()


# =============================================================================
# POST-PROCESSOR CONFIGS
# =============================================================================

POST_CONFIGS = {
    "GRBL": {"header": ["G90", "G21", "G94", "(post GRBL)"], "footer": ["M5", "M30"], "units": "mm"},
    "Mach4": {"header": ["G20", "G90", "G94", "(Mach4 Post)", "G54"], "footer": ["M5", "G28 G91 Z0", "M30"], "units": "inch"},
    "LinuxCNC": {"header": ["G21", "G90", "G94", "G64 P0.01", "(LinuxCNC)"], "footer": ["M5", "M2"], "units": "mm"},
    "PathPilot": {"header": ["G20", "G90", "G94", "(PathPilot)", "G54"], "footer": ["M5", "G53 G0 Z0", "M30"], "units": "inch"},
    "MASSO": {"header": ["G21", "G90", "G94", "(MASSO)"], "footer": ["M5", "M30"], "units": "mm"},
}


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class NeckDimensionsModel(BaseModel):
    """Custom neck dimensions."""
    blank_length_in: float = Field(26.0, description="Blank length")
    blank_width_in: float = Field(3.5, description="Blank width")
    blank_thickness_in: float = Field(1.0, description="Blank thickness")
    nut_width_in: float = Field(1.6875, description="Nut width")
    heel_width_in: float = Field(2.25, description="Heel width")
    depth_at_1st_in: float = Field(0.82, description="Depth at 1st fret")
    depth_at_12th_in: float = Field(0.92, description="Depth at 12th fret")
    scale_length_in: float = Field(25.5, description="Scale length")
    headstock_angle_deg: float = Field(14.0, description="Headstock angle")
    headstock_thickness_in: float = Field(0.55, description="Headstock thickness")
    truss_rod_width_in: float = Field(0.25, description="Truss rod channel width")
    truss_rod_depth_in: float = Field(0.375, description="Truss rod channel depth")


class GenerateNeckRequest(BaseModel):
    """Request to generate neck G-code."""
    post_id: str = Field("Mach4", description="Post-processor ID")
    preset: Optional[str] = Field(None, description="Preset name (overrides custom dimensions)")
    scale_length: float = Field(25.5, description="Scale length in inches")
    headstock_style: str = Field("paddle", description="Headstock style")
    neck_profile: str = Field("c", description="Neck profile shape")
    job_name: Optional[str] = Field(None, description="Job name")
    
    # Operation selection
    include_truss_rod: bool = Field(True, description="Include truss rod channel")
    include_headstock: bool = Field(True, description="Include headstock outline")
    include_tuner_holes: bool = Field(True, description="Include tuner drilling")
    include_profile_rough: bool = Field(True, description="Include neck profile rough")
    
    # Custom dimensions (used if preset not specified)
    custom_dimensions: Optional[NeckDimensionsModel] = None


class GenerateNeckResponse(BaseModel):
    """Neck G-code generation results."""
    gcode: str
    post_id: str
    job_name: str
    summary: Dict[str, Any]


class MultiExportNeckRequest(BaseModel):
    """Request for multi-post ZIP export."""
    post_ids: List[str] = Field(
        ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"],
        description="Post-processor IDs"
    )
    preset: Optional[str] = None
    scale_length: float = 25.5
    headstock_style: str = "paddle"
    neck_profile: str = "c"
    job_name: Optional[str] = None


class HeadstockPreviewResponse(BaseModel):
    """Headstock outline points."""
    style: str
    outline_points: List[List[float]]
    tuner_positions: List[List[float]]
    bounding_box: Dict[str, float]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def inject_post_header(gcode: str, post_id: str, job_name: str) -> str:
    """Inject post-processor header."""
    config = POST_CONFIGS.get(post_id, POST_CONFIGS["Mach4"])
    
    header_lines = [
        f"; Job: {job_name}",
        f"; Generated: {datetime.now().isoformat()}",
        f"; Post: {post_id}",
        f"(POST={post_id};DATE={datetime.now().isoformat()})",
    ]
    header_lines.extend(config["header"])
    header_lines.append("")
    
    return "\n".join(header_lines) + "\n" + gcode


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/generate", response_model=GenerateNeckResponse)
async def generate_neck_gcode(request: GenerateNeckRequest):
    """
    Generate G-code for neck machining.
    
    Includes operations for:
    - Truss rod channel
    - Headstock outline
    - Tuner hole drilling
    - Neck profile roughing
    """
    if request.post_id not in POST_CONFIGS:
        raise HTTPException(400, f"Unknown post-processor: {request.post_id}")
    
    # Create generator
    gen = NeckGenerator(
        scale_length=request.scale_length,
        headstock_style=request.headstock_style,
        profile=request.neck_profile,
        preset=request.preset,
    )
    
    job_name = request.job_name or f"Neck_{request.scale_length}in_{request.headstock_style}"
    
    # Generate with selective operations
    gen.generator = NeckGCodeGenerator(
        dims=gen.dims,
        headstock_style=gen.headstock_style,
        profile=gen.profile,
    )
    
    gen.generator.gcode = []
    gen.generator._emit(gen.generator.generate_header(job_name))
    
    if request.include_truss_rod:
        gen.generator.generate_truss_rod_channel()
    
    if request.include_headstock:
        gen.generator.generate_headstock_outline()
    
    if request.include_tuner_holes:
        gen.generator.generate_tuner_holes()
    
    if request.include_profile_rough:
        gen.generator.generate_neck_profile_rough()
    
    gen.generator._emit(gen.generator.generate_footer())
    
    gcode = "\n".join(gen.generator.gcode)
    gcode = inject_post_header(gcode, request.post_id, job_name)
    
    return GenerateNeckResponse(
        gcode=gcode,
        post_id=request.post_id,
        job_name=job_name,
        summary=gen.get_summary(),
    )


@router.post("/export/multi")
async def export_multi_post_neck(request: MultiExportNeckRequest):
    """
    Generate multi-post ZIP bundle for neck program.
    
    Creates a ZIP file containing:
    - One .nc file per post-processor
    - manifest.json with generation metadata
    """
    invalid_posts = [p for p in request.post_ids if p not in POST_CONFIGS]
    if invalid_posts:
        raise HTTPException(400, f"Unknown post-processors: {invalid_posts}")
    
    job_name = request.job_name or f"Neck_{request.scale_length}in"
    
    # Create ZIP in memory
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            'job_name': job_name,
            'generated': datetime.now().isoformat(),
            'scale_length': request.scale_length,
            'headstock_style': request.headstock_style,
            'neck_profile': request.neck_profile,
            'preset': request.preset,
            'posts': {},
        }
        
        for post_id in request.post_ids:
            # Generate for this post
            gen = NeckGenerator(
                scale_length=request.scale_length,
                headstock_style=request.headstock_style,
                profile=request.neck_profile,
                preset=request.preset,
            )
            
            gen.generator = NeckGCodeGenerator(
                dims=gen.dims,
                headstock_style=gen.headstock_style,
                profile=gen.profile,
            )
            
            gcode = gen.generator.generate_full_program(job_name)
            gcode = inject_post_header(gcode, post_id, job_name)
            
            # Add to ZIP
            filename = f"{job_name}_{post_id}.nc"
            zf.writestr(filename, gcode)
            
            manifest['posts'][post_id] = {
                'filename': filename,
                'lines': len(gcode.split('\n')),
            }
        
        # Add manifest
        zf.writestr('manifest.json', json.dumps(manifest, indent=2))
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type='application/zip',
        headers={
            'Content-Disposition': f'attachment; filename="{job_name}_multi_post.zip"'
        }
    )


@router.get("/presets")
async def list_presets():
    """List available neck dimension presets."""
    return {
        name: {
            'scale_length_in': dims.scale_length_in,
            'nut_width_in': dims.nut_width_in,
            'depth_at_1st_in': dims.depth_at_1st_in,
            'depth_at_12th_in': dims.depth_at_12th_in,
            'headstock_angle_deg': dims.headstock_angle_deg,
        }
        for name, dims in NECK_PRESETS.items()
    }


@router.get("/headstocks")
async def list_headstock_styles():
    """List available headstock styles."""
    return {
        style.value: {
            'name': style.name.replace('_', ' ').title(),
            'description': {
                'gibson_open': 'Gibson open-book 3+3 style',
                'gibson_solid': 'Gibson solid headstock',
                'fender_strat': 'Fender Stratocaster 6-in-line',
                'fender_tele': 'Fender Telecaster style',
                'prs': 'PRS style headstock',
                'classical': 'Classical guitar slotted',
                'paddle': 'Blank paddle for custom carving',
            }.get(style.value, 'Custom headstock style'),
        }
        for style in HeadstockStyle
    }


@router.get("/profiles")
async def list_neck_profiles():
    """List available neck profile shapes."""
    return {
        profile.value: {
            'name': profile.name.replace('_', ' ').title(),
            'description': {
                'c': 'Classic C shape - comfortable, versatile',
                'd': 'D shape - flatter back, modern feel',
                'v': 'V shape - vintage feel, great for thumb-over',
                'u': 'U shape - baseball bat, chunky',
                'asymmetric': 'Asymmetric - different profile bass/treble',
                'compound': 'Compound - profile changes along length',
            }.get(profile.value, 'Custom profile'),
        }
        for profile in NeckProfile
    }


@router.get("/headstock/preview/{style}")
async def preview_headstock(style: str, scale_length: float = 25.5):
    """
    Get headstock outline preview.
    
    Returns points for rendering headstock shape and tuner positions.
    """
    try:
        headstock_style = HeadstockStyle(style)
    except ValueError:
        raise HTTPException(400, f"Unknown headstock style: {style}")
    
    dims = NeckDimensions(scale_length_in=scale_length)
    
    outline = generate_headstock_outline(headstock_style, dims)
    tuners = generate_tuner_positions(headstock_style, dims)
    
    # Calculate bounding box
    if outline:
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        bbox = {
            'min_x': min(xs),
            'max_x': max(xs),
            'min_y': min(ys),
            'max_y': max(ys),
        }
    else:
        bbox = {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
    
    return HeadstockPreviewResponse(
        style=style,
        outline_points=[list(p) for p in outline],
        tuner_positions=[list(p) for p in tuners],
        bounding_box=bbox,
    )


@router.get("/tools")
async def list_neck_tools():
    """List available tools for neck operations."""
    return {
        num: {
            'number': t.number,
            'name': t.name,
            'diameter_in': t.diameter_in,
            'rpm': t.rpm,
            'feed_ipm': t.feed_ipm,
            'stepdown_in': t.stepdown_in,
        }
        for num, t in NECK_TOOLS.items()
    }


@router.get("/posts")
async def list_posts():
    """List available post-processors."""
    return {
        post_id: {
            'units': config['units'],
        }
        for post_id, config in POST_CONFIGS.items()
    }
