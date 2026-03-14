"""
API routes for Interactive Rosette Designer.

All endpoints are UTILITY lane (stateless, no governance).
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from app.art_studio.schemas.rosette_designer import (
    BomRequest,
    BomResponse,
    CellInfoResponse,
    ExportBomCsvRequest,
    ExportSvgRequest,
    MfgCheckRequest,
    MfgCheckResponse,
    PlaceTileRequest,
    PlaceTileResponse,
    PreviewRequest,
    PreviewResponse,
    RecipeListResponse,
    RecipePreset,
    SymmetryCellsRequest,
    SymmetryCellsResponse,
    SymmetryMode,
    TileCatalogResponse,
    TILE_CATS,
    TILE_MAP,
    RING_DEFS,
    SEG_OPTIONS,
)
# Rosette Consolidation: rosette_designer.py → rosette_engine.py
from app.art_studio.services.rosette_engine import (
    auto_fix_shallow_rings,
    auto_fix_short_arcs,
    bom_to_csv,
    cell_info,
    compute_bom,
    get_sym_cells,
    get_tile_color_hex,
    place_tile,
    RECIPES,
    render_preview_svg,
    run_mfg_checks,
)

router = APIRouter()


# ── Tile catalog ──────────────────────────────────────────────────

@router.get("/catalog", response_model=TileCatalogResponse)
def get_tile_catalog() -> TileCatalogResponse:
    """Return full tile catalog, ring defs, segment options."""
    return TileCatalogResponse(
        tile_map=TILE_MAP,
        categories=TILE_CATS,
        ring_defs=[rd.model_dump() for rd in RING_DEFS],
        seg_options=list(SEG_OPTIONS),
    )


# ── Place tile ────────────────────────────────────────────────────

@router.post("/place-tile", response_model=PlaceTileResponse)
def place_tile_endpoint(req: PlaceTileRequest) -> PlaceTileResponse:
    """Place a tile respecting current symmetry mode."""
    new_grid, affected = place_tile(
        req.grid, req.ring_idx, req.seg_idx, req.tile_id,
        req.sym_mode, req.num_segs, req.ring_active,
    )
    return PlaceTileResponse(grid=new_grid, affected_cells=affected)


# ── Symmetry cells ────────────────────────────────────────────────

@router.post("/sym-cells", response_model=SymmetryCellsResponse)
def get_symmetry_cells(req: SymmetryCellsRequest) -> SymmetryCellsResponse:
    """Return list of cells affected by current symmetry mode."""
    cells = get_sym_cells(req.ring_idx, req.seg_idx, req.sym_mode, req.num_segs)
    return SymmetryCellsResponse(cells=cells)


# ── Cell info ─────────────────────────────────────────────────────

@router.get("/cell-info")
def get_cell_info(ri: int, si: int, num_segs: int, grid: str = "") -> CellInfoResponse:
    """Return info for a hovered cell. Grid is JSON-encoded string."""
    import json
    grid_dict = json.loads(grid) if grid else {}
    info = cell_info(ri, si, num_segs, grid_dict)
    return CellInfoResponse(**info)


# ── BOM ───────────────────────────────────────────────────────────

@router.post("/bom", response_model=BomResponse)
def compute_bom_endpoint(req: BomRequest) -> BomResponse:
    """Compute full bill of materials."""
    return compute_bom(req)


@router.post("/bom/csv")
def export_bom_csv(req: ExportBomCsvRequest) -> PlainTextResponse:
    """Export BOM as CSV string."""
    bom_req = BomRequest(
        num_segs=req.num_segs, grid=req.grid, ring_active=req.ring_active,
    )
    csv_str = bom_to_csv(bom_req, req.design_name)
    return PlainTextResponse(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{req.design_name or "rosette"}_bom.csv"'},
    )


# ── MFG checks ────────────────────────────────────────────────────

@router.post("/mfg-check", response_model=MfgCheckResponse)
def run_mfg_check(req: MfgCheckRequest) -> MfgCheckResponse:
    """Run manufacturing intelligence checks."""
    return run_mfg_checks(req)


@router.post("/mfg-auto-fix")
def apply_mfg_auto_fix(req: MfgCheckRequest) -> dict:
    """Apply auto-fix for MFG issues (remove problem tiles)."""
    grid = dict(req.grid)
    grid = auto_fix_short_arcs(grid, req.num_segs, req.ring_active)
    grid = auto_fix_shallow_rings(grid, req.num_segs, req.ring_active)
    return {"grid": grid}


# ── Recipes ───────────────────────────────────────────────────────

@router.get("/recipes", response_model=RecipeListResponse)
def list_recipes() -> RecipeListResponse:
    """Return all 8 recipe presets."""
    return RecipeListResponse(recipes=RECIPES)


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str) -> RecipePreset:
    """Return a single recipe by id."""
    for r in RECIPES:
        if r.id == recipe_id:
            return r
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")


# ── SVG Preview ───────────────────────────────────────────────────

@router.post("/preview", response_model=PreviewResponse)
def render_preview(req: PreviewRequest) -> PreviewResponse:
    """Render SVG preview of the current design."""
    svg = render_preview_svg(
        num_segs=req.num_segs, grid=req.grid,
        ring_active=req.ring_active, show_tabs=req.show_tabs,
        show_annotations=req.show_annotations,
        width=req.width, height=req.height,
    )
    filled_count = sum(1 for k, v in req.grid.items() if v and v != "clear")
    total_cells = len(RING_DEFS) * req.num_segs
    return PreviewResponse(svg=svg, filled_count=filled_count, total_cells=total_cells)


@router.post("/export/svg")
def export_svg(req: ExportSvgRequest) -> Response:
    """Export design as downloadable SVG file."""
    svg = render_preview_svg(
        num_segs=req.num_segs, grid=req.grid,
        ring_active=req.ring_active, show_tabs=req.show_tabs,
        show_annotations=req.with_annotations,
    )
    filename = f"{req.design_name or 'rosette'}_{'drafting' if req.with_annotations else 'design'}.svg"
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
