#!/usr/bin/env python3
"""
Luthier's Tool Box - Main FastAPI Application

Provides REST API for:
- Project management (CRUD operations)
- Pipeline integrations (rosette, bracing, hardware, gcode, dxf)
- Export queue management
- File serving for DXF/G-code downloads

All geometry is stored in millimeters (mm).
DXF exports are R12 format with closed LWPolylines.
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import pathlib
import tempfile
import subprocess
import uuid
from datetime import datetime

# Import pipeline modules
from pipelines.rosette import rosette_calc
from pipelines.bracing import bracing_calc
from pipelines.hardware import hardware_layout
from pipelines.financial import cnc_roi_calculator
from utils import export_queue

# Import curve math router
from curvemath_router import router as curves_router

# Import DXF export router
from dxf_exports_router import router as dxf_router

# Import CAM routers (Patches F2, G, H, H0, I, J, J1, J2)
from cam_router import router as cam_router
from cam_pocket_router import router as cam_pocket_router
from neutral_router import router as neutral_router
from cam_sim_router import router as cam_sim_router    # Patch I: Simulation
from tool_router import router as tool_router          # Patch J: Tool Library
from cam_rough_router import router as cam_rough_router  # Patch J2: Roughing
from cam_curve_router import router as cam_curve_router  # Patch J2: Curve/Bi-Arc

# Import RMOS router (pattern library, job log, manufacturing plans)
from rmos_router import router as rmos_router

app = FastAPI(
    title="Luthier's Tool Box API",
    description="CNC guitar lutherie CAD/CAM REST API",
    version="1.0.0"
)

# Include curve math endpoints
app.include_router(curves_router)

# Include DXF export endpoints
app.include_router(dxf_router)

# Include CAM endpoints (Patches F2, G, H, H0, I, J, J1, J2)
app.include_router(cam_router)          # POST /cam/roughing_gcode (with units/lead-in/tabs)
app.include_router(cam_pocket_router)   # POST /cam/pocket_gcode (raster pocketing + post injection)
app.include_router(neutral_router)      # POST /neutral/bundle.zip (CAM-neutral export)
app.include_router(cam_sim_router)      # POST /cam/simulate_gcode (Patch I: G-code simulation)
app.include_router(tool_router)         # GET /cam/tools, GET /cam/posts (Patch J: Tool library)
app.include_router(cam_rough_router)    # POST /cam/rough_gcode (Patch J2: Roughing with post injection)
app.include_router(cam_curve_router)    # POST /cam/biarc_gcode (Patch J2: Curve/bi-arc with post injection)

# Include RMOS endpoints (patterns, job log, manufacturing plans)
app.include_router(rmos_router)         # /api/rosette-patterns, /api/joblog, /api/rmos/*

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths
STORAGE_DIR = pathlib.Path(__file__).parent / "storage"
PROJECTS_DIR = STORAGE_DIR / "projects"
EXPORTS_DIR = STORAGE_DIR / "exports"
TEMP_DIR = STORAGE_DIR / "temp"

# Ensure directories exist
for d in [STORAGE_DIR, PROJECTS_DIR, EXPORTS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ==================== Models ====================

class RosetteParams(BaseModel):
    """Parametric rosette design parameters."""
    soundhole_diameter_mm: float = Field(..., gt=0, description="Soundhole diameter in mm")
    exposure_mm: float = Field(0.15, ge=0, description="Exposure above top surface in mm")
    glue_clearance_mm: float = Field(0.08, ge=0, description="Glue clearance in mm")
    central_band: Dict[str, float] = Field(
        default={"width_mm": 18.0, "thickness_mm": 1.0},
        description="Central band dimensions"
    )
    inner_purfling: List[Dict[str, Any]] = Field(default=[], description="Inner purfling strips")
    outer_purfling: List[Dict[str, Any]] = Field(default=[], description="Outer purfling strips")

class RosetteResult(BaseModel):
    """Rosette calculation results."""
    soundhole_diameter_mm: float
    channel_width_mm: float
    channel_depth_mm: float
    stack: Dict[str, Any]

class BracingParams(BaseModel):
    """Bracing layout parameters."""
    model_name: str = "Bracing"
    units: str = "mm"
    top_radius_mm: Optional[float] = None
    back_radius_mm: Optional[float] = None
    braces: List[Dict[str, Any]]

class HardwareParams(BaseModel):
    """Hardware layout parameters."""
    model_name: str = "HardwareLayout"
    units: str = "mm"
    components: List[Dict[str, Any]]

class ExportRequest(BaseModel):
    """Generic export request."""
    type: str = Field(..., description="Export type: rosette_dxf, rosette_gcode, bracing_report, etc.")
    params: Dict[str, Any] = Field(..., description="Type-specific parameters")

class ExportStatus(BaseModel):
    """Export queue item status."""
    id: str
    type: str
    model: str
    file: str
    status: str = "queued"  # queued, processing, ready, downloaded
    queued_at: str

# ==================== Health & Info ====================

@app.get("/")
async def root():
    """API information."""
    return {
        "name": "Luthier's Tool Box API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "pipelines": {
                "rosette": "/api/pipelines/rosette",
                "bracing": "/api/pipelines/bracing",
                "hardware": "/api/pipelines/hardware",
                "bridge": "/api/pipelines/bridge",
                "gcode_explainer": "/api/pipelines/gcode",
                "dxf_cleaner": "/api/pipelines/dxf",
                "cnc_roi_calculator": "/api/pipelines/financial/cnc-roi"
            },
            "exports": "/api/exports",
            "rmos": {
                "patterns": "/api/rosette-patterns",
                "joblog": "/api/joblog",
                "manufacturing_plan": "/api/rosette/manufacturing-plan",
                "live_monitor": "/api/rmos/live-monitor/{job_id}/drilldown"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ==================== Rosette Pipeline ====================

@app.post("/api/pipelines/rosette/calculate", response_model=RosetteResult)
async def calculate_rosette(params: RosetteParams):
    """
    Calculate rosette channel dimensions from purfling stack.
    
    Returns channel width and depth in millimeters.
    """
    try:
        result = rosette_calc.compute(params.dict())
        return RosetteResult(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/pipelines/rosette/export-dxf")
async def export_rosette_dxf(params: RosetteParams):
    """
    Export rosette design as R12 DXF file.
    
    Returns DXF file with soundhole and channel circles.
    """
    try:
        # Create temp file for params
        temp_json = TEMP_DIR / f"rosette_{uuid.uuid4()}.json"
        temp_json.write_text(json.dumps(params.dict(), indent=2))
        
        # Run calculation first
        calc_result = rosette_calc.compute(params.dict())
        calc_json = temp_json.with_name(temp_json.stem + "_calc.json")
        calc_json.write_text(json.dumps(calc_result, indent=2))
        
        # Generate DXF
        output_dir = EXPORTS_DIR / "rosette"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dxf = output_dir / f"rosette_{uuid.uuid4()}.dxf"
        
        subprocess.run([
            "python",
            str(pathlib.Path(__file__).parent / "pipelines" / "rosette" / "rosette_to_dxf.py"),
            str(temp_json),
            "--out", str(output_dxf)
        ], check=True, cwd=pathlib.Path(__file__).parent)
        
        # Add to export queue
        export_queue.enqueue({
            "id": output_dxf.stem,
            "type": "rosette_dxf",
            "model": "Rosette",
            "file": output_dxf.name,
            "status": "ready",
            "queued_at": datetime.utcnow().isoformat()
        })
        
        return FileResponse(
            path=output_dxf,
            media_type="application/dxf",
            filename=output_dxf.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pipelines/rosette/export-gcode")
async def export_rosette_gcode(
    params: RosetteParams,
    tool_mm: float = 1.0,
    feed: float = 300.0,
    rpm: int = 20000,
    stepdown: float = 0.20,
    radstep: float = 0.05
):
    """
    Generate G-code for rosette channel machining.
    
    Returns NGC file with parametric spiral cut pattern.
    """
    try:
        # Create temp file for params
        temp_json = TEMP_DIR / f"rosette_{uuid.uuid4()}.json"
        temp_json.write_text(json.dumps(params.dict(), indent=2))
        
        # Generate G-code
        output_dir = EXPORTS_DIR / "rosette"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_gcode = output_dir / f"rosette_{uuid.uuid4()}.ngc"
        
        subprocess.run([
            "python",
            str(pathlib.Path(__file__).parent / "pipelines" / "rosette" / "rosette_make_gcode.py"),
            str(temp_json),
            "--out", str(output_gcode),
            "--tool-mm", str(tool_mm),
            "--feed", str(feed),
            "--rpm", str(rpm),
            "--stepdown", str(stepdown),
            "--radstep", str(radstep)
        ], check=True, cwd=pathlib.Path(__file__).parent)
        
        # Add to export queue
        export_queue.enqueue({
            "id": output_gcode.stem,
            "type": "rosette_gcode",
            "model": "Rosette",
            "file": output_gcode.name,
            "status": "ready",
            "queued_at": datetime.utcnow().isoformat()
        })
        
        return FileResponse(
            path=output_gcode,
            media_type="text/plain",
            filename=output_gcode.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Bracing Pipeline ====================

@app.post("/api/pipelines/bracing/calculate")
async def calculate_bracing(params: BracingParams):
    """
    Calculate bracing structural properties.
    
    Returns mass estimation and glue area for each brace.
    """
    try:
        # Create temp config file
        temp_json = TEMP_DIR / f"bracing_{uuid.uuid4()}.json"
        temp_json.write_text(json.dumps(params.dict(), indent=2))
        
        # Run calculation
        output_dir = EXPORTS_DIR / "bracing"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        bracing_calc.run(str(temp_json), str(output_dir))
        
        # Read result
        model_name = params.model_name
        result_file = output_dir / f"{model_name}_bracing_report.json"
        result = json.loads(result_file.read_text())
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Hardware Pipeline ====================

@app.post("/api/pipelines/hardware/generate")
async def generate_hardware_layout(params: HardwareParams):
    """
    Generate hardware cavity layout DXF.
    
    Returns DXF with pickup/control positions.
    """
    try:
        # Create temp config file
        temp_json = TEMP_DIR / f"hardware_{uuid.uuid4()}.json"
        temp_json.write_text(json.dumps(params.dict(), indent=2))
        
        # Run generation
        output_dir = EXPORTS_DIR / "hardware"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        hardware_layout.run(str(temp_json), str(output_dir))
        
        # Read result summary
        model_name = params.model_name
        summary_file = output_dir / f"{model_name}_hardware_summary.json"
        summary = json.loads(summary_file.read_text())
        
        return JSONResponse(content=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== G-code Explainer Pipeline ====================

@app.post("/api/pipelines/gcode/explain")
async def explain_gcode(file: UploadFile = File(...)):
    """
    Analyze G-code file and provide line-by-line explanation.
    
    Uploads NC/NGC file and returns markdown explanation.
    """
    try:
        # Save uploaded file
        temp_gcode = TEMP_DIR / f"gcode_{uuid.uuid4()}.ngc"
        with temp_gcode.open("wb") as f:
            f.write(await file.read())
        
        # Run explainer
        output_dir = EXPORTS_DIR / "gcode"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_md = output_dir / f"{temp_gcode.stem}_explained.md"
        
        subprocess.run([
            "python",
            str(pathlib.Path(__file__).parent / "pipelines" / "gcode_explainer" / "explain_gcode_ai.py"),
            "--in", str(temp_gcode),
            "--out", str(output_md),
            "--md"
        ], check=True, cwd=pathlib.Path(__file__).parent)
        
        # Read and return markdown
        explanation = output_md.read_text(encoding="utf-8")
        
        return JSONResponse(content={
            "filename": file.filename,
            "explanation": explanation,
            "download_url": f"/api/files/gcode/{output_md.name}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DXF Cleaner Pipeline ====================

@app.post("/api/pipelines/dxf/clean")
async def clean_dxf(file: UploadFile = File(...), tolerance: float = 0.12):
    """
    Clean DXF file for CAM compatibility.
    
    Converts LINE/ARC/CIRCLE/SPLINE → closed LWPolylines (R12 format).
    """
    try:
        # Save uploaded file
        temp_dxf = TEMP_DIR / f"input_{uuid.uuid4()}.dxf"
        with temp_dxf.open("wb") as f:
            f.write(await file.read())
        
        # Run cleaner
        output_dir = EXPORTS_DIR / "dxf"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dxf = output_dir / f"cleaned_{uuid.uuid4()}.dxf"
        
        subprocess.run([
            "python",
            str(pathlib.Path(__file__).parent / "pipelines" / "dxf_cleaner" / "clean_dxf.py"),
            str(temp_dxf),
            "-o", str(output_dxf),
            "-t", str(tolerance)
        ], check=True, cwd=pathlib.Path(__file__).parent)
        
        # Add to export queue
        export_queue.enqueue({
            "id": output_dxf.stem,
            "type": "dxf_clean",
            "model": file.filename,
            "file": output_dxf.name,
            "status": "ready",
            "queued_at": datetime.utcnow().isoformat()
        })
        
        return FileResponse(
            path=output_dxf,
            media_type="application/dxf",
            filename=f"cleaned_{file.filename}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Financial Calculator ====================

@app.post("/api/pipelines/financial/cnc-roi")
async def calculate_cnc_roi(params: dict):
    """
    Calculate CNC investment Return on Investment (ROI).
    
    Analyzes equipment costs, operating expenses, labor savings,
    material efficiency, and revenue impact to determine:
    - Payback period
    - Net Present Value (NPV)
    - ROI percentage
    - Year-by-year cash flow projections
    
    Args:
        params: Dictionary containing:
            - equipment: Equipment cost breakdown
            - operating: Annual operating costs
            - labor: Production volume, hourly rates, manual vs. CNC hours
            - materials: Material costs and waste rates
            - revenue: Pricing, production increase, reject rates
            - include_bracing: Boolean for acoustic guitar bracing
            - discount_rate: Discount rate for NPV (default 0.08)
            - analysis_years: Years to analyze (default 5)
    
    Returns:
        Complete ROI analysis with:
        - summary: Total investment, annual benefit, payback, NPV, ROI%
        - cost_breakdown: Labor/material savings, operating costs
        - labor_analysis: Per-guitar cost comparison
        - year_by_year: Detailed cash flow projections
    
    Example:
        POST /api/pipelines/financial/cnc-roi
        {
            "equipment": {"cnc_router_price": 25000.0},
            "labor": {"annual_production_guitars": 50},
            "include_bracing": false,
            "analysis_years": 5
        }
    """
    try:
        result = cnc_roi_calculator.calculate_roi(params)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ROI calculation failed: {str(e)}")

# ==================== Export Queue ====================

@app.get("/api/exports/list")
async def list_exports():
    """List all exports in queue."""
    try:
        items = export_queue.list_items()
        return JSONResponse(content=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/exports/{export_id}/downloaded")
async def mark_downloaded(export_id: str):
    """Mark export as downloaded."""
    # Simple implementation - in production, update status in database
    return {"status": "success", "export_id": export_id}

# ==================== Bridge Calculator ====================

@app.post("/api/pipelines/bridge/export-dxf")
async def export_bridge_dxf(payload: dict):
    """
    Export bridge calculator geometry to R12 DXF.
    
    Args:
        payload: Bridge calculator model JSON with:
            - units: "mm" or "in"
            - scaleLength, stringSpread, compTreble, compBass
            - slotWidth, slotLength
            - endpoints: {treble: {x, y}, bass: {x, y}}
            - slotPolygon: [{x, y}, ...]
    
    Returns:
        DXF file with layers:
        - SADDLE_LINE: Compensated saddle endpoints
        - SLOT_RECTANGLE: Closed LWPolyline for CAM toolpath
        - NUT_REFERENCE: Centerline at x=0
        - SCALE_REFERENCE: Tick mark at scale length
        - DIMENSIONS: Text annotations
    """
    try:
        # Validate units
        if payload.get('units', 'mm') not in ['mm', 'in']:
            raise HTTPException(400, "units must be 'mm' or 'in'")
        
        # Create temp JSON input
        input_json = EXPORTS_DIR / "bridge" / f"bridge_input_{uuid.uuid4().hex[:8]}.json"
        input_json.parent.mkdir(parents=True, exist_ok=True)
        
        with open(input_json, 'w') as f:
            json.dump(payload, f, indent=2)
        
        # Generate DXF filename
        export_id = uuid.uuid4().hex[:12]
        output_dxf = EXPORTS_DIR / "bridge" / f"bridge_saddle_{export_id}.dxf"
        
        # Call pipeline script
        script_path = pathlib.Path(__file__).parent / "pipelines" / "bridge" / "bridge_to_dxf.py"
        result = subprocess.run(
            ["python", str(script_path), str(input_json), "--output", str(output_dxf)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(500, f"DXF generation failed: {result.stderr}")
        
        # Add to export queue
        export_queue.add_item({
            "id": export_id,
            "type": "bridge_dxf",
            "filename": output_dxf.name,
            "path": str(output_dxf),
            "timestamp": datetime.utcnow().isoformat(),
            "params": payload
        })
        
        return {
            "success": True,
            "export_id": export_id,
            "filename": output_dxf.name,
            "download_url": f"/api/files/{export_id}"
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "DXF generation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== File Serving ====================

@app.get("/api/files/{export_id}")
async def download_file(export_id: str):
    """Download export file by ID."""
    # Search in all export directories
    for subdir in ["rosette", "bracing", "hardware", "bridge", "gcode", "dxf"]:
        search_dir = EXPORTS_DIR / subdir
        if search_dir.exists():
            for file_path in search_dir.glob(f"{export_id}.*"):
                return FileResponse(
                    path=file_path,
                    filename=file_path.name
                )
    
    raise HTTPException(status_code=404, detail="File not found")

# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
