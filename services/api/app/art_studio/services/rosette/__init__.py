"""
Rosette — Unified rosette design, geometry, manufacturing, and rendering.

Split into focused modules:
- rosette_geometry.py: Core primitives, thresholds, MaterialSpec, ToolSpec
- rosette_design.py: Tile placement, symmetry, cell info
- rosette_manufacturing.py: BOM, checks, auto-fix, feasibility
- rosette_recipes.py: Preset recipes
- rosette_svg.py: SVG preview rendering

All public API is re-exported here for backward compatibility.
"""
from __future__ import annotations

# Geometry
from .rosette_geometry import (
    MFG_THRESHOLDS,
    MaterialSpec,
    ToolSpec,
    _arc_inches,
    _fmt,
    _pt_on_circle,
    _rad,
    arc_cell_path,
    tab_path,
)

# Design
from .rosette_design import (
    _TILE_COLOR_HEX,
    _TILE_FILL_MAP,
    get_cell_info,
    get_symmetry_cells,
    get_tile_color_hex,
    get_tile_fill,
    place_tile,
)

# Manufacturing
from .rosette_manufacturing import (
    auto_fix_shallow_rings,
    auto_fix_short_arcs,
    bom_to_csv,
    check_feasibility,
    compute_bom,
    run_manufacturing_checks,
)

# Recipes
from .rosette_recipes import (
    RECIPES,
    _build_alternating,
    _make_grid,
    get_recipes,
)

# SVG
from .rosette_svg import (
    _SVG_DEFS,
    _build_annotations_svg,
    render_preview_svg,
    render_preview_svg_compat,
)

__all__ = [
    # Geometry
    "MFG_THRESHOLDS",
    "MaterialSpec",
    "ToolSpec",
    "_rad",
    "_pt_on_circle",
    "_fmt",
    "_arc_inches",
    "arc_cell_path",
    "tab_path",
    # Design
    "_TILE_FILL_MAP",
    "_TILE_COLOR_HEX",
    "get_tile_fill",
    "get_tile_color_hex",
    "get_symmetry_cells",
    "place_tile",
    "get_cell_info",
    # Manufacturing
    "compute_bom",
    "bom_to_csv",
    "run_manufacturing_checks",
    "auto_fix_short_arcs",
    "auto_fix_shallow_rings",
    "check_feasibility",
    # Recipes
    "_make_grid",
    "_build_alternating",
    "get_recipes",
    "RECIPES",
    # SVG
    "_SVG_DEFS",
    "render_preview_svg",
    "render_preview_svg_compat",
    "_build_annotations_svg",
]
