"""
Rosette Recipes — Preset rosette patterns.

Named recipe presets for quick starting points: Vintage Martin, Shell Classic,
Herringbone Band, Celtic Ring, Checkerboard Mosaic, Minimalist, etc.
"""
from __future__ import annotations

from typing import Dict, List

from app.art_studio.schemas.rosette_designer import RecipePreset, SymmetryMode


# ─────────────────────────────────────────────────────────────────────────────
# Recipe Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_grid(num_segs: int, fills: List) -> Dict[str, str]:
    """Build a grid dict from fill specs."""
    g: Dict[str, str] = {}
    for entry in fills:
        if len(entry) == 2:
            ri, tid = entry
            for s in range(num_segs):
                g[f"{ri}-{s}"] = tid
        elif len(entry) == 3:
            ri, si, tid = entry
            g[f"{ri}-{si}"] = tid
        elif len(entry) == 4:
            ri, start, step, tid = entry
            s = start
            while s < num_segs:
                g[f"{ri}-{s}"] = tid
                s += step
    return g


def _build_alternating(num_segs: int, ring: int, even_tile: str, odd_tile: str,
                       base_fills: List) -> Dict[str, str]:
    """Build grid with alternating main channel and fixed other rings."""
    g = _make_grid(num_segs, base_fills)
    for s in range(num_segs):
        g[f"{ring}-{s}"] = even_tile if s % 2 == 0 else odd_tile
    return g


# ─────────────────────────────────────────────────────────────────────────────
# Recipe Presets
# ─────────────────────────────────────────────────────────────────────────────

def get_recipes() -> List[RecipePreset]:
    """Return all 8 named recipe presets."""
    return [
        RecipePreset(
            id="vintage-martin", name="Vintage Martin",
            desc="Alternating rosewood & maple main channel with B/W/B purfling.",
            tags=["12 seg", "traditional", "wood"],
            num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True] * 5,
            grid=_build_alternating(12, 2, "rosewood", "maple", [
                [0, "maple"], [1, "bwb"], [3, "bwb"], [4, "rosewood"],
            ]),
        ),
        RecipePreset(
            id="shell-classic", name="Shell Classic",
            desc="Full abalone main channel with MOP purfling and ebony binding.",
            tags=["12 seg", "shell", "premium"],
            num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True] * 5,
            grid=_make_grid(12, [
                [0, "cream"], [1, "bwb"], [2, "abalone"], [3, "bwb"], [4, "ebony"],
            ]),
        ),
        RecipePreset(
            id="herringbone-band", name="Herringbone Band",
            desc="Full herringbone main channel with B/W/B purfling. D-28 style.",
            tags=["12 seg", "herringbone", "traditional"],
            num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True] * 5,
            grid=_make_grid(12, [
                [0, "maple"], [1, "bwb"], [2, "herringbone"], [3, "bwb"], [4, "rosewood"],
            ]),
        ),
        RecipePreset(
            id="celtic-ring", name="Celtic Ring",
            desc="Celtic knot motif throughout the main channel with walnut binding.",
            tags=["12 seg", "celtic", "ornate"],
            num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True] * 5,
            grid=_make_grid(12, [
                [0, "walnut"], [1, "wbw"], [2, "celtic"], [3, "wbw"], [4, "walnut"],
            ]),
        ),
        RecipePreset(
            id="checkerboard-mosaic", name="Checkerboard Mosaic",
            desc="Dense checkerboard mosaic on 16 segments for geometric pattern.",
            tags=["16 seg", "geometric", "mosaic"],
            num_segs=16, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True] * 5,
            grid=_make_grid(16, [
                [0, "ebony"], [1, "bwb"], [2, "checker"], [3, "bwb"], [4, "ebony"],
            ]),
        ),
        RecipePreset(
            id="minimalist", name="Minimalist",
            desc="Sparse design with only binding rings active. Clean purfling lines.",
            tags=["12 seg", "minimal", "modern"],
            num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True, True, False, True, True],
            grid=_make_grid(12, [
                [0, "cream"], [1, "bwb"], [3, "bwb"], [4, "mahogany"],
            ]),
        ),
        RecipePreset(
            id="abalone-burst", name="Abalone Burst",
            desc="Alternating abalone and MOP segments create shimmer effect.",
            tags=["12 seg", "shell", "burst"],
            num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True] * 5,
            grid=_build_alternating(12, 2, "abalone", "mop", [
                [0, "cream"], [1, "mop"], [3, "mop"], [4, "ebony"],
            ]),
        ),
        RecipePreset(
            id="rosewood-maple", name="Rosewood & Maple",
            desc="Alternating rosewood and figured maple with W/B/W purfling.",
            tags=["12 seg", "wood", "alternating"],
            num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
            ring_active=[True] * 5,
            grid=_build_alternating(12, 2, "rosewood", "maple", [
                [0, "maple"], [1, "wbw"], [3, "wbw"], [4, "rosewood"],
            ]),
        ),
    ]


# Pre-computed recipes for backward compatibility
RECIPES = get_recipes()
