"""
RosetteEngine — Unified rosette design, geometry, manufacturing, and rendering.

This module is now a thin wrapper that re-exports from focused sub-modules:
- rosette/rosette_geometry.py: Core primitives, thresholds, MaterialSpec, ToolSpec
- rosette/rosette_design.py: Tile placement, symmetry, cell info
- rosette/rosette_manufacturing.py: BOM, checks, auto-fix, feasibility
- rosette/rosette_recipes.py: Preset recipes
- rosette/rosette_svg.py: SVG preview rendering

All geometry in SVG units (1 unit = 0.01 inch). Inch conversions at boundaries.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.art_studio.schemas.rosette_designer import (
    BomRequest,
    BomResponse,
    MfgCheckRequest,
    MfgCheckResponse,
    RecipePreset,
    SymmetryMode,
)
from app.art_studio.schemas.rosette_params import RosetteParamSpec
from app.art_studio.schemas.rosette_feasibility import RosetteFeasibilitySummary

# Import from submodules
from .rosette import (
    # Geometry
    MFG_THRESHOLDS,
    MaterialSpec,
    ToolSpec,
    _arc_inches,
    _fmt,
    _pt_on_circle,
    _rad,
    arc_cell_path as _arc_cell_path,
    tab_path as _tab_path,
    # Design
    _TILE_COLOR_HEX,
    _TILE_FILL_MAP,
    get_cell_info as _get_cell_info,
    get_symmetry_cells as _get_symmetry_cells,
    get_tile_color_hex as _get_tile_color_hex,
    get_tile_fill as _get_tile_fill,
    place_tile as _place_tile,
    # Manufacturing
    auto_fix_shallow_rings as _auto_fix_shallow_rings,
    auto_fix_short_arcs as _auto_fix_short_arcs,
    bom_to_csv as _bom_to_csv,
    check_feasibility as _check_feasibility,
    compute_bom as _compute_bom,
    run_manufacturing_checks as _run_manufacturing_checks,
    # Recipes
    RECIPES,
    get_recipes as _get_recipes,
    # SVG
    _SVG_DEFS,
    render_preview_svg as _render_preview_svg_core,
    render_preview_svg_compat,
)


# ─────────────────────────────────────────────────────────────────────────────
# RosetteEngine Facade
# ─────────────────────────────────────────────────────────────────────────────

class RosetteEngine:
    """
    Unified rosette design engine.

    Consolidates geometry, BOM, manufacturing checks, feasibility scoring,
    recipe presets, and SVG rendering into a single cohesive class.

    All methods delegate to focused sub-modules.
    """

    # ───────────────────────────────────────────────────────────────────────
    # GEOMETRY METHODS (static helpers)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def _rad(deg: float) -> float:
        """Convert degrees to radians."""
        return _rad(deg)

    @staticmethod
    def _pt_on_circle(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
        """Get point on circle at given angle (0° = top, clockwise)."""
        return _pt_on_circle(cx, cy, r, deg)

    @staticmethod
    def _fmt(n: float) -> str:
        """Format number for SVG output."""
        return _fmt(n)

    @staticmethod
    def _arc_inches(r_svg: float, ang_deg: float) -> float:
        """Arc length in inches given radius in SVG units and angle in degrees."""
        return _arc_inches(r_svg, ang_deg)

    @staticmethod
    def arc_cell_path(cx: float, cy: float, r1: float, r2: float,
                      a1: float, a2: float) -> str:
        """Build SVG arc cell path between two radii and two angles."""
        return _arc_cell_path(cx, cy, r1, r2, a1, a2)

    @staticmethod
    def tab_path(cx: float, cy: float, r_inner: float, r_outer: float,
                 mid_angle: float, half_width: float) -> str:
        """Build SVG path for an extension tab."""
        return _tab_path(cx, cy, r_inner, r_outer, mid_angle, half_width)

    # ───────────────────────────────────────────────────────────────────────
    # DESIGN METHODS (tile placement, symmetry, cell info)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_tile_fill(tile_id: str) -> str:
        """Return SVG fill string for a tile id."""
        return _get_tile_fill(tile_id)

    @staticmethod
    def get_tile_color_hex(tile_id: str) -> str:
        """Return simple hex color (for previews where patterns can't render)."""
        return _get_tile_color_hex(tile_id)

    @staticmethod
    def get_symmetry_cells(ring_idx: int, seg_idx: int, sym_mode: SymmetryMode,
                           num_segs: int) -> List[List[int]]:
        """Return list of [ring, seg] pairs affected by symmetry."""
        return _get_symmetry_cells(ring_idx, seg_idx, sym_mode, num_segs)

    @staticmethod
    def place_tile(grid: Dict[str, str], ring_idx: int, seg_idx: int,
                   tile_id: str, sym_mode: SymmetryMode, num_segs: int,
                   ring_active: List[bool]) -> Tuple[Dict[str, str], List[str]]:
        """Place a tile respecting symmetry. Returns (new_grid, affected_keys)."""
        return _place_tile(grid, ring_idx, seg_idx, tile_id, sym_mode, num_segs, ring_active)

    @staticmethod
    def get_cell_info(ring_idx: int, seg_idx: int, num_segs: int,
                      grid: Dict[str, str]) -> Dict[str, Any]:
        """Return hovered-cell info dict."""
        return _get_cell_info(ring_idx, seg_idx, num_segs, grid)

    # ───────────────────────────────────────────────────────────────────────
    # MANUFACTURING METHODS (BOM, checks, auto-fix, feasibility)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_bom(req: BomRequest) -> BomResponse:
        """Compute full bill of materials from grid state."""
        return _compute_bom(req)

    @staticmethod
    def bom_to_csv(req: BomRequest, design_name: str = "Untitled Design") -> str:
        """Generate CSV string from BOM data."""
        return _bom_to_csv(req, design_name)

    @staticmethod
    def run_manufacturing_checks(req: MfgCheckRequest) -> MfgCheckResponse:
        """Run all 6 manufacturing intelligence checks."""
        return _run_manufacturing_checks(req)

    @staticmethod
    def auto_fix_short_arcs(grid: Dict[str, str], num_segs: int,
                            ring_active: List[bool]) -> Dict[str, str]:
        """Remove tiles from cells with arc length below fragile threshold."""
        return _auto_fix_short_arcs(grid, num_segs, ring_active)

    @staticmethod
    def auto_fix_shallow_rings(grid: Dict[str, str], num_segs: int,
                               ring_active: List[bool]) -> Dict[str, str]:
        """Remove tiles from rings with depth below fragile threshold."""
        return _auto_fix_shallow_rings(grid, num_segs, ring_active)

    @staticmethod
    def check_feasibility(
        spec: RosetteParamSpec,
        default_material: Optional[MaterialSpec] = None,
        default_tool: Optional[ToolSpec] = None,
    ) -> RosetteFeasibilitySummary:
        """Estimate feasibility for a rosette design."""
        return _check_feasibility(spec, default_material, default_tool)

    # ───────────────────────────────────────────────────────────────────────
    # PRESET/RECIPE METHODS
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_recipes() -> List[RecipePreset]:
        """Return all 8 named recipe presets."""
        return _get_recipes()

    # ───────────────────────────────────────────────────────────────────────
    # RENDERING METHODS (SVG preview)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def render_preview_svg(
        num_segs: int,
        grid: Dict[str, str],
        ring_active: List[bool],
        show_tabs: bool = True,
        show_annotations: bool = False,
        width: int = 620,
        height: int = 620,
    ) -> str:
        """Render a full SVG preview of the rosette wheel."""
        return _render_preview_svg_core(
            num_segs=num_segs,
            grid=grid,
            ring_active=ring_active,
            show_tabs=show_tabs,
            show_annotations=show_annotations,
            width=width,
            height=height,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Backward compatibility exports (module-level functions that delegate)
# ─────────────────────────────────────────────────────────────────────────────

# Geometry
arc_cell_path = RosetteEngine.arc_cell_path
tab_path = RosetteEngine.tab_path

# Design
get_tile_fill = RosetteEngine.get_tile_fill
get_tile_color_hex = RosetteEngine.get_tile_color_hex
get_sym_cells = RosetteEngine.get_symmetry_cells
place_tile = RosetteEngine.place_tile
cell_info = RosetteEngine.get_cell_info

# Manufacturing
compute_bom = RosetteEngine.compute_bom
bom_to_csv = RosetteEngine.bom_to_csv
run_mfg_checks = RosetteEngine.run_manufacturing_checks
auto_fix_short_arcs = RosetteEngine.auto_fix_short_arcs
auto_fix_shallow_rings = RosetteEngine.auto_fix_shallow_rings
estimate_rosette_feasibility = RosetteEngine.check_feasibility

# Rendering - backward compatible wrapper (accepts PreviewRequest or kwargs)
render_preview_svg = render_preview_svg_compat
