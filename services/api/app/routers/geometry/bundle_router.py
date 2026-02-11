"""
Geometry Bundle Export Router
=============================

Handles multi-file bundle exports (ZIP archives with DXF + SVG + G-code).

Endpoints:
- POST /export_bundle - Single post bundle (DXF + SVG + NC)
- POST /export_bundle_multi - Multi-post bundle (N x NC files)

CRITICAL SAFETY RULES:
1. Filename sanitization MUST strip all unsafe characters
2. Post-processor IDs MUST match existing configurations
3. Units MUST be explicitly converted (never assume)
"""

import datetime
import io
import json
import zipfile

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from ..geometry_schemas import (
    GcodeExportIn,
    ExportBundleIn,
    ExportBundleMultiIn,
)

from .helpers import (
    _load_posts,
    _metadata_comment,
)

from .export_router import export_gcode

from ...util.exporters import export_dxf, export_svg
from ...util.units import scale_geom_units

router = APIRouter(tags=["geometry"])


@router.post("/export_bundle")
def export_bundle(body: ExportBundleIn) -> Response:
    """
    Export complete CAM bundle: DXF + SVG + G-code + manifest as ZIP archive.

    Provides all-in-one export for single post-processor workflow with full
    traceability via manifest.json and embedded metadata comments.

    Args:
        body: ExportBundleIn containing:
            - geometry: Design geometry with units and paths
            - gcode: Raw G-code toolpath body
            - post_id: Post-processor ID (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
            - job_name: Optional filename stem (sanitized, used for all files)

    Returns:
        StreamingResponse with application/zip Content-Type
        ZIP archive contains:
        - <job_name>.dxf: Design geometry in DXF R12 format
        - <job_name>.svg: Design geometry in SVG format
        - <job_name>.nc: Post-processed G-code with headers/footers
        - <job_name>_manifest.json: Metadata with units, post_id, timestamp, file list
        - README.txt: Human-readable bundle description

    Raises:
        None (uses generic post if post_id invalid)
    """
    units = body.geometry.units or "mm"
    target_units = (body.target_units or units).lower()

    # Scale geometry if a different target unit is requested
    geom_src = body.geometry.dict()
    geom = scale_geom_units(geom_src, target_units)
    units = geom["units"]

    meta = _metadata_comment(units, body.post_id or "")

    # Use job_name for filenames if provided, default to "program" for consistency
    stem = body.job_name.strip() if body.job_name else "program"

    # Build files in-memory
    dxf_txt = export_dxf(geom, meta=meta)
    svg_txt = export_svg(geom, meta=meta)

    # G-code via post-processor
    gc_request = GcodeExportIn(gcode=body.gcode, units=units, post_id=body.post_id, job_name=body.job_name)
    gc_response = export_gcode(gc_request)
    program = gc_response.body.decode("utf-8") if isinstance(gc_response.body, (bytes, bytearray)) else gc_response.body

    manifest = {
        "units": units,
        "post_id": body.post_id,
        "job_name": stem,
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "files": [f"{stem}.dxf", f"{stem}.svg", f"{stem}_{body.post_id}.nc"]
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{stem}.dxf", dxf_txt)
        z.writestr(f"{stem}.svg", svg_txt)
        z.writestr(f"{stem}_{body.post_id}.nc", program)
        z.writestr(f"{stem}_manifest.json", json.dumps(manifest, indent=2))
        z.writestr("README.txt",
                   "ToolBox bundle export\nContains DXF/SVG/G-code with metadata comments for provenance.\n")

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{stem}_bundle.zip"'}
    )


@router.post("/export_bundle_multi")
def export_bundle_multi(body: ExportBundleMultiIn) -> Response:
    """
    Export multi-post CAM bundle: DXF + SVG + N x G-code + manifest as ZIP archive.

    Provides simultaneous export for multiple CNC post-processors with optional
    unit conversion and full traceability. Ideal for shops with mixed machine fleets.

    Args:
        body: ExportBundleMultiIn containing:
            - geometry: Design geometry with units and paths
            - gcode: Raw G-code toolpath body (unit-agnostic)
            - post_ids: List of post-processor IDs (e.g., ["GRBL", "Mach4", "LinuxCNC"])
            - target_units: Optional target units for export ("mm" or "inch")
                            If provided, geometry is scaled server-side before export
            - job_name: Optional filename stem (sanitized, used for all files)

    Returns:
        StreamingResponse with application/zip Content-Type
        ZIP archive contains:
        - <job_name>.dxf: Design geometry in target units (DXF R12 format)
        - <job_name>.svg: Design geometry in target units (SVG format)
        - <job_name>_<POST1>.nc: Post-processed G-code for first post
        - <job_name>_<POST2>.nc: Post-processed G-code for second post
        - ... (one .nc file per post_id)
        - <job_name>_manifest.json: Metadata with units, post list, timestamp
        - README.txt: Human-readable bundle description

    Raises:
        HTTPException 400: No valid post_ids provided after filtering
    """
    units = body.geometry.units or "mm"
    target_units = (body.target_units or units).lower()

    # Scale geometry if a different target unit is requested
    geom_src = body.geometry.dict()
    geom = scale_geom_units(geom_src, target_units)
    units = geom["units"]

    # Use job_name for filenames if provided, default to "program" for consistency
    stem = body.job_name.strip() if body.job_name else "program"

    posts = _load_posts()
    # Map lowercase post names to actual file names for case-insensitive lookup
    posts_lower = {k.lower(): k for k in posts.keys()}
    # Preserve original case from user input in filenames
    requested = [p for p in body.post_ids if p.lower() in posts_lower]
    if not requested:
        raise HTTPException(400, "No valid post_ids supplied")

    meta = _metadata_comment(units, ",".join(requested))

    # Create common DXF/SVG in target units
    dxf_txt = export_dxf(geom, meta=meta)
    svg_txt = export_svg(geom, meta=meta)

    # Per-post G-code (with units + post headers/footers)
    nc_map = {}
    for pid in requested:
        gc_resp = export_gcode(GcodeExportIn(gcode=body.gcode, units=units, post_id=pid, job_name=body.job_name))
        program = gc_resp.body.decode("utf-8") if isinstance(gc_resp.body, (bytes, bytearray)) else gc_resp.body
        nc_map[pid] = program

    # Manifest
    manifest = {
        "units": units,
        "posts": requested,
        "job_name": stem,
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "files": [f"{stem}.dxf", f"{stem}.svg"] + [f"{stem}_{p}.nc" for p in requested]
    }

    # Build ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{stem}.dxf", dxf_txt)
        z.writestr(f"{stem}.svg", svg_txt)
        for p, txt in nc_map.items():
            z.writestr(f"{stem}_{p}.nc", txt)
        z.writestr(f"{stem}_manifest.json", json.dumps(manifest, indent=2))
        z.writestr("README.txt",
                   "ToolBox multi-post bundle export\nIncludes DXF/SVG (target units) and one NC per post.\n")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{stem}_multipost_bundle.zip"'})
