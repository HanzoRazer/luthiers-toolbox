"""Body Generator Router - Luthier's ToolBox"""
from datetime import datetime, timezone
from io import BytesIO
from typing import List, Dict, Optional, Tuple, Any
import os, tempfile, zipfile

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from .body_generator_schemas import (
    ToolConfigModel, MachineConfigModel, AnalyzeResponse, GenerateRequest,
    GenerateResponse, GenerateGovernedResponse, MultiExportRequest,
)
from ..generators.lespaul_body_generator import (
    LesPaulDXFReader, LesPaulGCodeGenerator, TOOLS, MACHINES, ToolConfig, MachineConfig,
)
from ..rmos.runs import RunArtifact, persist_run, create_run_id, sha256_of_obj, sha256_of_text

router = APIRouter()

# --- Post-Processor Configurations ---
POST_CONFIGS = {
    "GRBL": {"header": ["G90", "G21", "G94", "F1000", "(post GRBL)"], "footer": ["M5", "M30"], "units": "mm", "arc_mode": "IJK"},
    "Mach4": {"header": ["G20", "G90", "G94", "(Mach4 Post-Processor)", "G54"], "footer": ["M5", "G28 G91 Z0", "M30"], "units": "inch", "arc_mode": "IJK"},
    "LinuxCNC": {"header": ["G21", "G90", "G94", "G64 P0.01", "(LinuxCNC Post)"], "footer": ["M5", "M2"], "units": "mm", "arc_mode": "R"},
    "PathPilot": {"header": ["G20", "G90", "G94", "(PathPilot / Tormach)", "G54"], "footer": ["M5", "G53 G0 Z0", "M30"], "units": "inch", "arc_mode": "IJK"},
    "MASSO": {"header": ["G21", "G90", "G94", "(MASSO Controller)"], "footer": ["M5", "M30"], "units": "mm", "arc_mode": "IJK"},
}

# --- Helper Functions ---

def inject_post_header(gcode: str, post_id: str) -> str:
    """Inject post-processor header into G-code."""
    cfg = POST_CONFIGS.get(post_id, POST_CONFIGS["GRBL"])
    header_lines = cfg["header"]
    return "\n".join(header_lines) + "\n" + gcode

def inject_post_footer(gcode: str, post_id: str) -> str:
    """Inject post-processor footer into G-code."""
    cfg = POST_CONFIGS.get(post_id, POST_CONFIGS["GRBL"])
    footer_lines = cfg["footer"]
    return gcode.rstrip() + "\n" + "\n".join(footer_lines) + "\n"

def generate_body_gcode_from_dxf(
    tmp_path: str,
    machine: str,
    stock_thickness_in: float,
    post_id: str,
    job_name: str,
) -> Tuple[str, Dict[str, Any], Dict[str, float]]:
    """Pure generator function: DXF file -> G-code string."""
    # Load machine config
    machine_cfg = MACHINES.get(machine)
    if not machine_cfg:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown machine: {machine}. Available: {list(MACHINES.keys())}"
        )

    # Parse DXF
    reader = LesPaulDXFReader(filepath=tmp_path)
    reader.load()

    # Create G-code generator
    gcode_gen = LesPaulGCodeGenerator(
        reader=reader,
        machine=machine_cfg,
        stock_thickness_in=stock_thickness_in,
    )

    # Generate G-code
    raw_gcode = gcode_gen.generate_full_program(program_name=job_name)

    # Apply post-processor
    gcode = inject_post_header(raw_gcode, post_id)
    gcode = inject_post_footer(gcode, post_id)

    # Collect stats from generator
    gen_stats = gcode_gen.get_stats()
    stats = {
        "cut_distance_in": gen_stats.get("cut_distance_in", 0),
        "rapid_distance_in": gen_stats.get("rapid_distance_in", 0),
        "estimated_time_min": gen_stats.get("cut_time_min", 0),
        "line_count": len(gcode.splitlines()),
    }

    # Body dimensions
    body_size = {
        "width_in": reader.body_outline.width if reader.body_outline else 0,
        "height_in": reader.body_outline.height if reader.body_outline else 0,
        "thickness_in": stock_thickness_in,
    }

    return gcode, stats, body_size

# --- UTILITY ENDPOINTS (No RMOS tracking) ---

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_dxf(file: UploadFile = File(...)) -> AnalyzeResponse:
    """
    Analyze uploaded DXF file for body generation.

    LANE: UTILITY - Analysis only, no artifacts.
    """
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="File must be a .dxf file")

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        reader = LesPaulDXFReader()
        body_data = reader.read_dxf(tmp_path)

        return AnalyzeResponse(
            filepath=file.filename,
            body_outline=body_data.get("outline"),
            layers=body_data.get("layers", {}),
            origin_offset=body_data.get("origin_offset", (0, 0)),
            recommended_operations=[
                "rough_perimeter",
                "finish_perimeter",
                "pocket_cavities",
                "drill_holes",
            ],
        )
    finally:
        os.unlink(tmp_path)

# --- DRAFT LANE: Fast preview, no RMOS tracking ---

@router.post("/generate", response_model=GenerateResponse)
async def generate_body_gcode(
    file: UploadFile = File(...),
    post_id: str = "Mach4",
    machine: str = "txrx_router",
    stock_thickness_in: float = 1.75,
    job_name: Optional[str] = None,
) -> GenerateResponse:
    """Generate body G-code from DXF file (DRAFT lane)."""
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="File must be a .dxf file")

    # Validate post_id
    if post_id not in POST_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown post_id: {post_id}. Available: {list(POST_CONFIGS.keys())}"
        )

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        final_job_name = job_name or file.filename.replace(".dxf", "")

        gcode, stats, body_size = generate_body_gcode_from_dxf(
            tmp_path=tmp_path,
            machine=machine,
            stock_thickness_in=stock_thickness_in,
            post_id=post_id,
            job_name=final_job_name,
        )

        return GenerateResponse(
            gcode=gcode,
            post_id=post_id,
            job_name=final_job_name,
            stats=stats,
            body_size=body_size,
        )
    finally:
        os.unlink(tmp_path)

@router.post("/export/multi")
async def export_multi_post(
    file: UploadFile = File(...),
    post_ids: str = "GRBL,Mach4,LinuxCNC,PathPilot,MASSO",
    machine: str = "txrx_router",
    stock_thickness_in: float = 1.75,
    job_name: Optional[str] = None,
) -> StreamingResponse:
    """Generate multi-post ZIP export (DRAFT lane)."""
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="File must be a .dxf file")

    post_list = [p.strip() for p in post_ids.split(",") if p.strip()]

    # Validate all post_ids
    for pid in post_list:
        if pid not in POST_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown post_id: {pid}. Available: {list(POST_CONFIGS.keys())}"
            )

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        final_job_name = job_name or file.filename.replace(".dxf", "")

        # Create ZIP in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for pid in post_list:
                gcode, stats, body_size = generate_body_gcode_from_dxf(
                    tmp_path=tmp_path,
                    machine=machine,
                    stock_thickness_in=stock_thickness_in,
                    post_id=pid,
                    job_name=final_job_name,
                )

                filename = f"{final_job_name}_{pid}.nc"
                zf.writestr(filename, gcode)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{final_job_name}_multi.zip"',
                "X-ToolBox-Lane": "draft",
            },
        )
    finally:
        os.unlink(tmp_path)

# --- GOVERNED LANE: Full RMOS artifact persistence and audit trail ---

@router.post("/generate_governed", response_model=GenerateGovernedResponse)
async def generate_body_gcode_governed(
    file: UploadFile = File(...),
    post_id: str = "Mach4",
    machine: str = "txrx_router",
    stock_thickness_in: float = 1.75,
    job_name: Optional[str] = None,
) -> GenerateGovernedResponse:
    """Generate body G-code from DXF file (GOVERNED lane)."""
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="File must be a .dxf file")

    # Validate post_id
    if post_id not in POST_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown post_id: {post_id}. Available: {list(POST_CONFIGS.keys())}"
        )

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        final_job_name = job_name or file.filename.replace(".dxf", "")

        # Build request hash (for audit)
        request_data = {
            "filename": file.filename,
            "post_id": post_id,
            "machine": machine,
            "stock_thickness_in": stock_thickness_in,
            "job_name": final_job_name,
        }
        request_hash = sha256_of_obj(request_data)

        gcode, stats, body_size = generate_body_gcode_from_dxf(
            tmp_path=tmp_path,
            machine=machine,
            stock_thickness_in=stock_thickness_in,
            post_id=post_id,
            job_name=final_job_name,
        )

        # Hash G-code for provenance
        gcode_hash = sha256_of_text(gcode)

        # Create RMOS artifact
        now = datetime.now(timezone.utc).isoformat()
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="body_gcode",
            workflow_mode="body_generation",
            event_type="body_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        return GenerateGovernedResponse(
            gcode=gcode,
            post_id=post_id,
            job_name=final_job_name,
            stats=stats,
            body_size=body_size,
            run_id=run_id,
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
    finally:
        os.unlink(tmp_path)

@router.post("/export/multi_governed")
async def export_multi_post_governed(
    file: UploadFile = File(...),
    post_ids: str = "GRBL,Mach4,LinuxCNC,PathPilot,MASSO",
    machine: str = "txrx_router",
    stock_thickness_in: float = 1.75,
    job_name: Optional[str] = None,
) -> StreamingResponse:
    """Generate multi-post ZIP export (GOVERNED lane)."""
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="File must be a .dxf file")

    post_list = [p.strip() for p in post_ids.split(",") if p.strip()]

    # Validate all post_ids
    for pid in post_list:
        if pid not in POST_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown post_id: {pid}. Available: {list(POST_CONFIGS.keys())}"
            )

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        final_job_name = job_name or file.filename.replace(".dxf", "")
        now = datetime.now(timezone.utc).isoformat()

        # Track all run_ids and hashes
        run_ids = []
        gcode_hashes = []

        # Create ZIP in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for pid in post_list:
                # Build request hash for this post
                request_data = {
                    "filename": file.filename,
                    "post_id": pid,
                    "machine": machine,
                    "stock_thickness_in": stock_thickness_in,
                    "job_name": final_job_name,
                }
                request_hash = sha256_of_obj(request_data)

                gcode, stats, body_size = generate_body_gcode_from_dxf(
                    tmp_path=tmp_path,
                    machine=machine,
                    stock_thickness_in=stock_thickness_in,
                    post_id=pid,
                    job_name=final_job_name,
                )

                # Hash G-code
                gcode_hash = sha256_of_text(gcode)
                gcode_hashes.append(gcode_hash)

                # Create RMOS artifact for this post
                run_id = create_run_id()
                run_ids.append(run_id)

                artifact = RunArtifact(
                    run_id=run_id,
                    created_at_utc=now,
                    tool_id="body_gcode",
                    workflow_mode="body_generation",
                    event_type="body_gcode_execution",
                    status="OK",
                    request_hash=request_hash,
                    gcode_hash=gcode_hash,
                    notes=f"Multi-export post: {pid}",
                )
                persist_run(artifact)

                filename = f"{final_job_name}_{pid}.nc"
                zf.writestr(filename, gcode)

        zip_buffer.seek(0)

        # Hash the entire ZIP for aggregate provenance
        zip_content = zip_buffer.getvalue()
        zip_hash = sha256_of_text(zip_content.decode("latin-1"))
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{final_job_name}_multi.zip"',
                "X-ToolBox-Lane": "governed",
                "X-Run-IDs": ",".join(run_ids),
                "X-GCode-SHA256s": ",".join(gcode_hashes),
                "X-ZIP-SHA256": zip_hash,
            },
        )
    finally:
        os.unlink(tmp_path)

# --- INFO ENDPOINTS (UTILITY lane) ---

@router.get("/machines")
def list_machines() -> Dict[str, Any]:
    """List available machine configurations."""
    return {
        name: {
            "name": cfg.name,
            "max_x_in": cfg.max_x_in,
            "max_y_in": cfg.max_y_in,
            "max_z_in": cfg.max_z_in,
        }
        for name, cfg in MACHINES.items()
    }

@router.get("/tools")
def list_tools() -> Dict[str, Any]:
    """List available tool configurations."""
    return {
        name: {
            "number": cfg.number,
            "name": cfg.name,
            "diameter_in": cfg.diameter_in,
            "rpm": cfg.rpm,
        }
        for name, cfg in TOOLS.items()
    }

@router.get("/posts")
def list_posts() -> Dict[str, Any]:
    """List available post-processor configurations."""
    return {
        name: {
            "units": cfg["units"],
            "arc_mode": cfg["arc_mode"],
        }
        for name, cfg in POST_CONFIGS.items()
    }
