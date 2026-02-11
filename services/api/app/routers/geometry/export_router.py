"""
Geometry Export Router
======================

Handles single-file geometry exports (DXF, SVG, G-code).

Endpoints:
- POST /export - Export geometry to DXF or SVG
- POST /export_gcode - Export G-code with post-processor headers/footers
- POST /export_gcode_governed - Export G-code with RMOS artifact persistence

CRITICAL SAFETY RULES:
1. Filename sanitization MUST strip all unsafe characters
2. Post-processor IDs MUST match existing configurations
3. Units MUST be explicitly converted (never assume)
"""

import datetime

from fastapi import APIRouter, Body, HTTPException, Response
from datetime import timezone

from ..geometry_schemas import (
    ExportRequest,
    GcodeExportIn,
)

from .helpers import (
    _load_posts,
    _units_gcode,
    _safe_stem,
    _metadata_comment,
)

from ...util.exporters import export_dxf, export_svg

# Import RMOS run artifact persistence (OPERATION lane requirement)
from ...rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

router = APIRouter(tags=["geometry"])


@router.post("/export")
def export_geometry(fmt: str = "dxf", body: ExportRequest = Body(...)):
    """
    Export geometry to DXF or SVG format with post-processor metadata.

    Generates CAM-ready file with embedded metadata comments for provenance tracking.
    Supports multi-post workflow by injecting post_id into metadata.

    Args:
        fmt: Export format ("dxf" or "svg") via query parameter
        body: ExportRequest containing:
            - geometry: Canonical geometry with units and paths
            - post_id: Optional post-processor ID (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
            - job_name: Optional filename stem (sanitized for filesystem safety)

    Returns:
        Response with appropriate Content-Type and Content-Disposition headers

    Raises:
        HTTPException 400: Invalid format parameter (not dxf or svg)
    """
    fmt = (fmt or "dxf").lower()
    if fmt not in ("dxf", "svg"):
        raise HTTPException(400, "fmt must be dxf or svg")

    posts = _load_posts()
    post_id = (body.post_id or "").strip()
    post = posts.get(post_id) if post_id else None
    geom = body.geometry.dict()
    units = geom.get("units", "mm")

    # Use job_name for filename if provided
    stem = _safe_stem(body.job_name, default_prefix="export")

    if fmt == "dxf":
        txt = export_dxf(geom, meta=_metadata_comment(units, post_id))
        return Response(
            content=txt,
            media_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="{stem}.dxf"'},
        )
    else:  # svg
        txt = export_svg(geom, meta=_metadata_comment(units, post_id))
        return Response(
            content=txt,
            media_type="image/svg+xml",
            headers={"Content-Disposition": f'attachment; filename="{stem}.svg"'},
        )


@router.post("/export_gcode")
def export_gcode(body: GcodeExportIn) -> Response:
    """
    Export G-code with post-processor headers/footers and metadata.

    Wraps raw G-code with machine-specific initialization/shutdown sequences
    from post-processor configuration files. Ensures proper units mode and
    metadata provenance tracking.

    Args:
        body: GcodeExportIn containing:
            - gcode: Raw G-code body (toolpath commands)
            - units: "mm" or "inch" (determines G21/G20 injection)
            - post_id: Post-processor ID (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
            - job_name: Optional filename stem (sanitized for filesystem safety)

    Returns:
        Response with text/plain Content-Type and .nc extension

    Raises:
        None (uses generic header/footer if post_id invalid)
    """
    posts = _load_posts()
    hdr = []
    ftr = []
    units_code = _units_gcode(body.units or "mm")
    meta = _metadata_comment(body.units or "mm", body.post_id or "")

    # Case-insensitive post lookup
    posts_lower = {k.lower(): v for k, v in posts.items()}
    if body.post_id and body.post_id.lower() in posts_lower:
        post = posts_lower[body.post_id.lower()]
        hdr = (post.get("header") or [])[:]
        ftr = (post.get("footer") or [])[:]

    # Ensure units + meta are present in header
    if units_code not in hdr:
        hdr = [units_code] + hdr
    hdr = hdr + [meta]

    program = "\n".join(hdr + [body.gcode.strip()] + ftr) + ("\n" if not body.gcode.endswith("\n") else "")

    # Use job_name for filename if provided
    stem = _safe_stem(body.job_name, default_prefix="program")

    resp = Response(
        content=program,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{stem}.nc"'},
    )
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


@router.post("/export_gcode_governed")
def export_gcode_governed(body: GcodeExportIn) -> Response:
    """
    Export G-code with post-processor headers/footers and metadata (GOVERNED lane).

    Same functionality as /export_gcode but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    posts = _load_posts()
    hdr = []
    ftr = []
    units_code = _units_gcode(body.units or "mm")
    meta = _metadata_comment(body.units or "mm", body.post_id or "")

    # Case-insensitive post lookup
    posts_lower = {k.lower(): v for k, v in posts.items()}
    if body.post_id and body.post_id.lower() in posts_lower:
        post = posts_lower[body.post_id.lower()]
        hdr = (post.get("header") or [])[:]
        ftr = (post.get("footer") or [])[:]

    # Ensure units + meta are present in header
    if units_code not in hdr:
        hdr = [units_code] + hdr
    hdr = hdr + [meta]

    program = "\n".join(hdr + [body.gcode.strip()] + ftr) + ("\n" if not body.gcode.endswith("\n") else "")

    # Create RMOS artifact
    now = datetime.datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(body.model_dump(mode="json"))
    gcode_hash = sha256_of_text(program)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="geometry_export_gcode",
        workflow_mode="geometry_export",
        event_type="geometry_export_gcode_execution",
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)

    # Use job_name for filename if provided
    stem = _safe_stem(body.job_name, default_prefix="program")

    resp = Response(
        content=program,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{stem}.nc"'},
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp
