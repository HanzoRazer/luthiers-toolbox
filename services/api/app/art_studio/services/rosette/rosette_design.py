"""
Rosette Design — Tile placement, symmetry operations, and cell info.

Handles design-time operations: placing tiles, computing symmetry effects,
and retrieving cell metadata for UI display.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.art_studio.schemas.rosette_designer import (
    RING_DEFS,
    TILE_MAP,
    SymmetryMode,
)
from .rosette_geometry import _arc_inches


# ─────────────────────────────────────────────────────────────────────────────
# Tile Fill Maps
# ─────────────────────────────────────────────────────────────────────────────

_TILE_FILL_MAP = {
    "solid": lambda t: t.get("color", "#888"),
    "abalone": lambda _: "url(#pat-abalone)",
    "mop": lambda _: "url(#pat-mop)",
    "burl": lambda _: "url(#pat-burl)",
    "herringbone": lambda _: "url(#pat-herringbone)",
    "checker": lambda _: "url(#pat-checker)",
    "celtic": lambda _: "url(#pat-celtic)",
    "diagonal": lambda _: "url(#pat-diagonal)",
    "dots": lambda _: "url(#pat-dots)",
    "stripes": lambda _: "url(#pat-bwb)",
    "stripes2": lambda _: "url(#pat-rbr)",
    "stripes3": lambda _: "url(#pat-wbw)",
    "clear": lambda _: "none",
}

_TILE_COLOR_HEX = {
    "abalone": "#50c8c0", "mop": "#e8e0f0", "burl": "#C8A048",
    "herringbone": "#C09850", "checker": "#8a8a6a", "celtic": "#2a6a4a",
    "diagonal": "#c8922a", "dots": "#e8d8b8",
    "stripes": "#444", "stripes2": "#882233", "stripes3": "#aaa",
    "clear": "none",
}


# ─────────────────────────────────────────────────────────────────────────────
# Tile Operations
# ─────────────────────────────────────────────────────────────────────────────

def get_tile_fill(tile_id: str) -> str:
    """Return SVG fill string for a tile id."""
    if not tile_id or tile_id == "clear":
        return "none"
    tile = TILE_MAP.get(tile_id)
    if not tile:
        return "#888"
    fn = _TILE_FILL_MAP.get(tile["type"], lambda _: "#888")
    return fn(tile)


def get_tile_color_hex(tile_id: str) -> str:
    """Return simple hex color (for previews where patterns can't render)."""
    tile = TILE_MAP.get(tile_id)
    if not tile:
        return "#666"
    if tile["type"] == "solid":
        return tile.get("color", "#666")
    return _TILE_COLOR_HEX.get(tile["type"], "#666")


# ─────────────────────────────────────────────────────────────────────────────
# Symmetry Operations
# ─────────────────────────────────────────────────────────────────────────────

def get_symmetry_cells(ring_idx: int, seg_idx: int, sym_mode: SymmetryMode,
                       num_segs: int) -> List[List[int]]:
    """Return list of [ring, seg] pairs affected by symmetry."""
    pairs: List[List[int]] = []
    if sym_mode == SymmetryMode.NONE:
        pairs = [[ring_idx, seg_idx]]
    elif sym_mode == SymmetryMode.ROTATIONAL:
        pairs = [[ring_idx, s] for s in range(num_segs)]
    elif sym_mode == SymmetryMode.BILATERAL:
        pairs = [
            [ring_idx, seg_idx],
            [ring_idx, (num_segs - seg_idx) % num_segs],
        ]
    elif sym_mode == SymmetryMode.QUADRANT:
        step = num_segs // 4
        for i in range(4):
            s = (seg_idx + i * step) % num_segs
            pairs.append([ring_idx, s])
            pairs.append([ring_idx, (num_segs - s) % num_segs])

    # Deduplicate preserving order
    seen: set = set()
    result: List[List[int]] = []
    for r, s in pairs:
        key = f"{r}-{s}"
        if key not in seen:
            seen.add(key)
            result.append([r, s])
    return result


def place_tile(grid: Dict[str, str], ring_idx: int, seg_idx: int,
               tile_id: str, sym_mode: SymmetryMode, num_segs: int,
               ring_active: List[bool]) -> Tuple[Dict[str, str], List[str]]:
    """Place a tile respecting symmetry. Returns (new_grid, affected_keys)."""
    new_grid = dict(grid)
    affected: List[str] = []
    cells = get_symmetry_cells(ring_idx, seg_idx, sym_mode, num_segs)
    for r, s in cells:
        if not ring_active[r]:
            continue
        key = f"{r}-{s}"
        if tile_id == "clear":
            new_grid.pop(key, None)
        else:
            new_grid[key] = tile_id
        affected.append(key)
    return new_grid, affected


# ─────────────────────────────────────────────────────────────────────────────
# Cell Info
# ─────────────────────────────────────────────────────────────────────────────

def get_cell_info(ring_idx: int, seg_idx: int, num_segs: int,
                  grid: Dict[str, str]) -> Dict[str, Any]:
    """Return hovered-cell info dict."""
    rd = RING_DEFS[ring_idx]
    seg_ang = 360.0 / num_segs
    mid_r = (rd.r1 + rd.r2) / 2
    arc_len = _arc_inches(mid_r, seg_ang)
    depth_in = (rd.r2 - rd.r1) / 100.0
    key = f"{ring_idx}-{seg_idx}"
    tile_id = grid.get(key)
    tile = TILE_MAP.get(tile_id) if tile_id else None
    return {
        "zone": rd.label,
        "seg": f"{seg_idx + 1}/{num_segs}",
        "angle": f"{seg_ang:.1f}°",
        "depth_inches": f'{depth_in:.3f}"',
        "arc_len_inches": f'~{arc_len:.3f}"',
        "r1_inches": rd.inch1,
        "r2_inches": rd.inch2,
        "tile_name": tile["name"] if tile else None,
        "tile_id": tile_id,
    }
