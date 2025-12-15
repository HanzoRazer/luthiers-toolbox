"""
Body Generator Router - Luthier's ToolBox

FastAPI router for electric guitar body G-code generation.
Integrates with existing multi-post architecture.

Endpoints:
    POST /api/cam/body/analyze     - Analyze DXF, return layer info
    POST /api/cam/body/generate    - Generate G-code for single post
    POST /api/cam/body/export/multi - Multi-post ZIP bundle
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from io import BytesIO
import zipfile
import json
import tempfile
import os

from ..generators.lespaul_body_generator import (
    LesPaulBodyGenerator,
    LesPaulDXFReader,
    LesPaulGCodeGenerator,
    TOOLS,
    MACHINES,
    ToolConfig,
    MachineConfig,
)


router = APIRouter()


# =============================================================================
# POST-PROCESSOR CONFIGURATIONS
# =============================================================================

POST_CONFIGS = {
    "GRBL": {
        "header": ["G90", "G21", "G94", "F1000", "(post GRBL)"],
        "footer": ["M5", "M30"],
        "units": "mm",
        "arc_mode": "IJK",
    },
    "Mach4": {
        "header": ["G20", "G90", "G94", "(Mach4 Post-Processor)", "G54"],
        "footer": ["M5", "G28 G91 Z0", "M30"],
        "units": "inch",
        "arc_mode": "IJK",
    },
    "LinuxCNC": {
        "header": ["G21", "G90", "G94", "G64 P0.01", "(LinuxCNC Post)"],
        "footer": ["M5", "M2"],
        "units": "mm",
        "arc_mode": "R",
    },
    "PathPilot": {
        "header": ["G20", "G90", "G94", "(PathPilot / Tormach)", "G54"],
        "footer": ["M5", "G53 G0 Z0", "M30"],
        "units": "inch",
        "arc_mode": "IJK",
    },
    "MASSO": {
        "header": ["G21", "G90", "G94", "(MASSO Controller)"],
        "footer": ["M5", "M30"],
        "units": "mm",
        "arc_mode": "IJK",
    },
}


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ToolConfigModel(BaseModel):
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float
    stepover_pct: float


class MachineConfigModel(BaseModel):
    name: str
    max_x_in: float
    max_y_in: float
    max_z_in: float
    safe_z_in: float = 0.75
    retract_z_in: float = 0.25
    rapid_rate: float = 200.0


class AnalyzeResponse(BaseModel):
    """DXF analysis results."""
    filepath: str
    body_outline: Optional[Dict[str, Any]]
    layers: Dict[str, Dict[str, int]]
    origin_offset: Tuple[float, float]
    recommended_operations: List[str]


class GenerateRequest(BaseModel):
    """Request to generate body G-code."""
    post_id: str = Field("Mach4", description="Post-processor ID")
    machine: str = Field("txrx_router", description="Machine configuration")
    stock_thickness_in: float = Field(1.75, description="Stock thickness in inches")
    tab_count: int = Field(6, description="Number of holding tabs")
    tab_width_in: float = Field(0.5, description="Tab width in inches")
    tab_height_in: float = Field(0.125, description="Tab height in inches")
    job_name: Optional[str] = None


class GenerateResponse(BaseModel):
    """Body G-code generation results."""
    gcode: str
    post_id: str
    job_name: str
    stats: Dict[str, Any]
    body_size: Dict[str, float]


class MultiExportRequest(BaseModel):
    """Request for multi-post ZIP export."""
    post_ids: List[str] = Field(
        ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"],
        description="Post-processor IDs"
    )
    machine: str = "txrx_router"
    stock_thickness_in: float = 1.75
    tab_count: int = 6
    job_name: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def inject_post_header(gcode: str, post_id: str, job_name: str) -> str:
    """Inject post-processor specific header."""
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


def inject_post_footer(gcode: str, post_id: str) -> str:
    """Inject post-processor specific footer."""
    config = POST_CONFIGS.get(post_id, POST_CONFIGS["Mach4"])
    
    footer_lines = ["", "(PROGRAM END)"]
    footer_lines.extend(config["footer"])
    
    return gcode + "\n" + "\n".join(footer_lines)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_dxf(file: UploadFile = File(...)):
    """
    Analyze a DXF file and return layer information.
    
    Upload a DXF file to extract:
    - Body outline dimensions
    - Layer names and path counts
    - Recommended operations based on layers found
    """
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(400, "File must be a DXF file")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        reader = LesPaulDXFReader(tmp_path)
        reader.load()
        
        summary = reader.get_summary()
        
        # Determine recommended operations based on layers
        recommended = []
        layer_ops = {
            "Cutout": "OP50: Body perimeter contour",
            "Neck Mortise": "OP20: Neck pocket",
            "Pickup Cavity": "OP21: Pickup routes",
            "Electronic Cavities": "OP22: Electronics cavity",
            "Cover Recess": "OP25: Back cover recess",
            "Wiring Channel": "OP40: Wiring channels",
            "Pot Holes": "OP60: Control pot drilling",
            "Studs": "OP61: Bridge/tailpiece studs",
        }
        
        for layer, op in layer_ops.items():
            if layer in summary['layers']:
                recommended.append(op)
        
        return AnalyzeResponse(
            filepath=file.filename,
            body_outline=summary.get('body_outline'),
            layers=summary['layers'],
            origin_offset=summary['origin_offset'],
            recommended_operations=recommended,
        )
        
    finally:
        os.unlink(tmp_path)


@router.post("/generate", response_model=GenerateResponse)
async def generate_body_gcode(
    file: UploadFile = File(...),
    post_id: str = "Mach4",
    machine: str = "txrx_router",
    stock_thickness_in: float = 1.75,
    tab_count: int = 6,
    job_name: Optional[str] = None
):
    """
    Generate G-code for guitar body from DXF.
    
    Upload a layered DXF file to generate production G-code.
    Includes all operations: pockets, channels, perimeter, drilling.
    """
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(400, "File must be a DXF file")
    
    if post_id not in POST_CONFIGS:
        raise HTTPException(400, f"Unknown post-processor: {post_id}")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Use job name from filename if not provided
        if not job_name:
            job_name = file.filename.rsplit('.', 1)[0]
        
        gen = LesPaulBodyGenerator(tmp_path, machine=machine)
        
        # Create generator with custom settings
        gen.generator = LesPaulGCodeGenerator(
            reader=gen.reader,
            machine=gen.machine,
            stock_thickness_in=stock_thickness_in,
        )
        
        gcode = gen.generator.generate_full_program(job_name)
        
        # Wrap with post-specific header/footer
        gcode = inject_post_header(gcode, post_id, job_name)
        
        stats = gen.generator.get_stats()
        
        return GenerateResponse(
            gcode=gcode,
            post_id=post_id,
            job_name=job_name,
            stats=stats,
            body_size={
                'width': gen.reader.body_outline.width if gen.reader.body_outline else 0,
                'height': gen.reader.body_outline.height if gen.reader.body_outline else 0,
            },
        )
        
    finally:
        os.unlink(tmp_path)


@router.post("/export/multi")
async def export_multi_post(
    file: UploadFile = File(...),
    post_ids: str = "GRBL,Mach4,LinuxCNC,PathPilot,MASSO",
    machine: str = "txrx_router",
    stock_thickness_in: float = 1.75,
    job_name: Optional[str] = None
):
    """
    Generate multi-post ZIP bundle.
    
    Creates a ZIP file containing:
    - One .nc file per post-processor
    - manifest.json with generation metadata
    - DXF analysis summary
    """
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(400, "File must be a DXF file")
    
    # Parse post IDs
    posts = [p.strip() for p in post_ids.split(',') if p.strip()]
    invalid_posts = [p for p in posts if p not in POST_CONFIGS]
    if invalid_posts:
        raise HTTPException(400, f"Unknown post-processors: {invalid_posts}")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        if not job_name:
            job_name = file.filename.rsplit('.', 1)[0]
        
        gen = LesPaulBodyGenerator(tmp_path, machine=machine)
        
        # Create ZIP in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            manifest = {
                'job_name': job_name,
                'generated': datetime.now().isoformat(),
                'source_file': file.filename,
                'machine': machine,
                'stock_thickness_in': stock_thickness_in,
                'posts': {},
            }
            
            for post_id in posts:
                # Generate G-code for this post
                gen.generator = LesPaulGCodeGenerator(
                    reader=gen.reader,
                    machine=gen.machine,
                    stock_thickness_in=stock_thickness_in,
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
            
            # Add DXF summary
            summary = gen.reader.get_summary()
            summary['stats'] = gen.generator.get_stats() if gen.generator else {}
            zf.writestr('dxf_analysis.json', json.dumps(summary, indent=2))
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{job_name}_multi_post.zip"'
            }
        )
        
    finally:
        os.unlink(tmp_path)


@router.get("/machines")
async def list_machines():
    """List available machine configurations."""
    return {
        name: {
            'name': m.name,
            'max_x_in': m.max_x_in,
            'max_y_in': m.max_y_in,
            'max_z_in': m.max_z_in,
            'safe_z_in': m.safe_z_in,
        }
        for name, m in MACHINES.items()
    }


@router.get("/tools")
async def list_tools():
    """List available tool configurations."""
    return {
        num: {
            'number': t.number,
            'name': t.name,
            'diameter_in': t.diameter_in,
            'rpm': t.rpm,
            'feed_ipm': t.feed_ipm,
            'stepdown_in': t.stepdown_in,
            'stepover_pct': t.stepover_pct,
        }
        for num, t in TOOLS.items()
    }


@router.get("/posts")
async def list_posts():
    """List available post-processors."""
    return {
        post_id: {
            'units': config['units'],
            'arc_mode': config.get('arc_mode', 'IJK'),
        }
        for post_id, config in POST_CONFIGS.items()
    }
