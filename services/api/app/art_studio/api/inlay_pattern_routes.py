"""
Inlay Pattern Routes — FastAPI Router

Endpoints for generating, previewing, and exporting inlay patterns.
Integrates all three prototype layers:
  - Layer 1: Pattern generators (herringbone, diamond, greek_key, spiral, sunburst, feather)
  - Layer 2: Import pipeline (DXF, SVG, CSV — server-side, no XSS)
  - Layer 3: CNC offset engine (normal-vector offsets) + DXF R12 export
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from ..schemas.inlay_patterns import (
    BlueprintToInlayRequest,
    ComposeBandRequest,
    ExportFormat,
    InlayBomEntry,
    InlayBomResponse,
    InlayExportRequest,
    InlayGenerateRequest,
    InlayGenerateResponse,
    InlayGeneratorInfo,
    InlayGeneratorListResponse,
    InlayImportResponse,
)
from ..services.generators.inlay_patterns import (
    INLAY_GENERATORS,
    generate_inlay_pattern,
)
from ..services.generators.inlay_geometry import (
    MATERIAL_KEYS,
    calculate_bom,
    collection_to_layered_svg,
    collection_to_svg,
)
from ..services.generators.inlay_export import geometry_to_dxf_bytes
from ..services.generators.inlay_import import (
    parse_csv_grid,
    parse_dxf,
    parse_svg,
)

router = APIRouter(
    prefix="/api/art/inlay-patterns",
    tags=["Art Studio", "Inlay Patterns"],
)


# ---------------------------------------------------------------------------
# List available generators
# ---------------------------------------------------------------------------

@router.get("", response_model=InlayGeneratorListResponse)
async def list_inlay_generators() -> InlayGeneratorListResponse:
    """List all available inlay pattern generators with parameter hints."""
    generators = []
    for key, entry in INLAY_GENERATORS.items():
        # Build param_hints from the function's docstring params section
        generators.append(InlayGeneratorInfo(
            shape=key,
            name=entry["name"],
            description=entry["description"],
            is_linear=entry["linear"],
        ))
    return InlayGeneratorListResponse(generators=generators)


# ---------------------------------------------------------------------------
# Generate (preview)
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=InlayGenerateResponse)
async def generate_inlay(req: InlayGenerateRequest) -> InlayGenerateResponse:
    """Generate an inlay pattern and return an SVG preview.

    When ``include_offsets`` is true, returns a layered SVG with
    centerline / male_cut / pocket_cut groups.
    """
    try:
        geo = generate_inlay_pattern(req.shape, req.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if req.include_offsets:
        svg = collection_to_layered_svg(
            geo,
            male_offset_mm=req.male_offset_mm,
            pocket_offset_mm=req.pocket_offset_mm,
            materials=req.materials,
            bg_material=req.bg_material,
        )
    else:
        svg = collection_to_svg(
            geo,
            materials=req.materials,
            bg_material=req.bg_material,
            for_export=False,
        )

    return InlayGenerateResponse(
        shape=req.shape,
        svg=svg,
        width_mm=geo.width_mm,
        height_mm=geo.height_mm,
        element_count=len(geo.elements),
        is_radial=geo.radial,
    )


# ---------------------------------------------------------------------------
# Export (SVG / DXF / Layered SVG)
# ---------------------------------------------------------------------------

@router.post("/export")
async def export_inlay(req: InlayExportRequest) -> Response:
    """Export an inlay pattern as SVG (mm dimensions), layered SVG, or DXF R12.

    Returns the file as a downloadable attachment.
    """
    try:
        geo = generate_inlay_pattern(req.shape, req.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    fmt: ExportFormat = req.format
    filename = f"{req.shape}-inlay"

    if fmt == "dxf":
        data = geometry_to_dxf_bytes(
            geo,
            male_offset_mm=req.male_offset_mm,
            pocket_offset_mm=req.pocket_offset_mm,
        )
        return Response(
            content=data,
            media_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="{filename}.dxf"'},
        )
    elif fmt == "layered_svg":
        svg = collection_to_layered_svg(
            geo,
            male_offset_mm=req.male_offset_mm,
            pocket_offset_mm=req.pocket_offset_mm,
            materials=req.materials,
            bg_material=req.bg_material,
        )
        return Response(
            content=svg.encode("utf-8"),
            media_type="image/svg+xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}-layered.svg"'},
        )
    else:
        # Plain SVG with mm dimensions
        svg = collection_to_svg(
            geo,
            materials=req.materials,
            bg_material=req.bg_material,
            for_export=True,
        )
        return Response(
            content=svg.encode("utf-8"),
            media_type="image/svg+xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}.svg"'},
        )


# ---------------------------------------------------------------------------
# Compose (multi-layer band)
# ---------------------------------------------------------------------------

@router.post("/compose", response_model=InlayGenerateResponse)
async def compose_band_endpoint(req: ComposeBandRequest) -> InlayGenerateResponse:
    """Generate a composite multi-layer band from stacked patterns."""
    compose_params: Dict[str, Any] = {}
    if req.preset:
        compose_params["preset"] = req.preset
    if req.layers:
        compose_params["layers"] = req.layers
    compose_params["band_width_mm"] = req.band_width_mm
    compose_params["band_height_mm"] = req.band_height_mm
    compose_params["gap_mm"] = req.gap_mm
    compose_params["repeats"] = req.repeats
    compose_params["mirror"] = req.mirror

    try:
        geo = generate_inlay_pattern("compose_band", compose_params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if req.include_offsets:
        svg = collection_to_layered_svg(
            geo,
            male_offset_mm=req.male_offset_mm,
            pocket_offset_mm=req.pocket_offset_mm,
            materials=req.materials,
            bg_material=req.bg_material,
        )
    else:
        svg = collection_to_svg(
            geo,
            materials=req.materials,
            bg_material=req.bg_material,
            for_export=False,
        )

    return InlayGenerateResponse(
        shape="compose_band",
        svg=svg,
        width_mm=geo.width_mm,
        height_mm=geo.height_mm,
        element_count=len(geo.elements),
        is_radial=geo.radial,
    )


# ---------------------------------------------------------------------------
# Import (DXF / SVG / CSV upload)
# ---------------------------------------------------------------------------

_MAX_IMPORT_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/import", response_model=InlayImportResponse)
async def import_inlay_file(
    file: UploadFile = File(..., description="DXF, SVG, or CSV file to import"),
) -> InlayImportResponse:
    """Import a DXF, SVG, or CSV file as clip geometry.

    The file is parsed server-side — no client-side script execution.
    Maximum upload size: 5 MB.
    """
    raw = await file.read(_MAX_IMPORT_BYTES + 1)
    if len(raw) > _MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit")

    text = raw.decode("utf-8", errors="replace")
    name = (file.filename or "").lower()

    if name.endswith(".dxf"):
        fmt = "dxf"
        geo = parse_dxf(text)
    elif name.endswith(".svg"):
        fmt = "svg"
        geo = parse_svg(text)
    elif name.endswith(".csv"):
        fmt = "csv"
        geo = parse_csv_grid(text)
    else:
        # Try auto-detection by content
        if text.strip().startswith("0") and "ENTITIES" in text[:2000]:
            fmt = "dxf"
            geo = parse_dxf(text)
        elif text.strip().startswith("<"):
            fmt = "svg"
            geo = parse_svg(text)
        else:
            fmt = "csv"
            geo = parse_csv_grid(text)

    preview = collection_to_svg(geo, for_export=False)

    return InlayImportResponse(
        format_detected=fmt,
        element_count=len(geo.elements),
        width_mm=geo.width_mm,
        height_mm=geo.height_mm,
        preview_svg=preview,
    )


# ---------------------------------------------------------------------------
# BOM (Bill of Materials)
# ---------------------------------------------------------------------------

@router.post("/bom", response_model=InlayBomResponse)
async def inlay_bom(req: InlayGenerateRequest) -> InlayBomResponse:
    """Calculate a bill of materials for a generated inlay pattern.

    Returns piece count and area per (shape_type, material) group.
    """
    try:
        geo = generate_inlay_pattern(req.shape, req.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    materials = req.materials if req.materials else MATERIAL_KEYS[:3]
    entries = calculate_bom(geo, materials)

    bom_entries = [
        InlayBomEntry(
            shape_type=e.shape_type,
            material_key=e.material_key,
            count=e.count,
            area_mm2=round(e.area_mm2, 4),
        )
        for e in entries
    ]

    return InlayBomResponse(
        shape=req.shape,
        entries=bom_entries,
        total_pieces=sum(e.count for e in bom_entries),
        total_area_mm2=round(sum(e.area_mm2 for e in bom_entries), 4),
    )


# ---------------------------------------------------------------------------
# Blueprint-to-Inlay Bridge (dual input portal #2)
# ---------------------------------------------------------------------------

_ALLOWED_BLUEPRINT_DIR = "blueprint_output"


@router.post("/import-from-blueprint", response_model=InlayImportResponse)
async def import_from_blueprint(req: BlueprintToInlayRequest) -> InlayImportResponse:
    """Import geometry from a Blueprint Reader vectorisation result.

    Reads a server-side DXF or SVG file produced by the Blueprint Reader
    pipeline and converts it into the inlay geometry IR.  This is the
    second input portal — the first is the direct ``/import`` upload.
    """
    from pathlib import Path

    chosen_path: str | None = req.dxf_path or req.svg_path
    if not chosen_path:
        raise HTTPException(
            status_code=400,
            detail="Provide either dxf_path or svg_path",
        )

    # Resolve and validate the path stays inside the allowed directory
    resolved = Path(chosen_path).resolve()
    allowed_root = Path(_ALLOWED_BLUEPRINT_DIR).resolve()
    if not str(resolved).startswith(str(allowed_root)):
        raise HTTPException(
            status_code=403,
            detail="Path must be inside the blueprint output directory",
        )
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    text = resolved.read_text(encoding="utf-8", errors="replace")

    if req.dxf_path:
        geo = parse_dxf(text)
    else:
        geo = parse_svg(text)

    preview = collection_to_svg(geo, for_export=False)

    return InlayImportResponse(
        format_detected="dxf" if req.dxf_path else "svg",
        element_count=len(geo.elements),
        width_mm=geo.width_mm,
        height_mm=geo.height_mm,
        preview_svg=preview,
    )
