# server/app/core/rosette_planner.py
from __future__ import annotations

from collections import defaultdict
from math import pi, ceil
from typing import List, Dict

from app.schemas.rosette_pattern import RosettePatternInDB, RosetteRingBand
from app.schemas.manufacturing_plan import (
    ManufacturingPlan,
    RingRequirement,
    StripFamilyPlan,
)


def _tiles_for_ring(
    ring: RosetteRingBand,
    guitars: int,
    default_tile_length_mm: float,
) -> tuple[RingRequirement, int]:
    """
    Compute tile counts for one ring and return:
    - RingRequirement
    - total tiles needed for this ring across all guitars
    """
    tile_len = ring.tile_length_override_mm or default_tile_length_mm
    circumference = 2.0 * pi * ring.radius_mm

    tiles_per_guitar = max(1, int(round(circumference / tile_len)))
    total_for_all = tiles_per_guitar * guitars

    req = RingRequirement(
        ring_index=ring.index,
        strip_family_id=ring.strip_family_id,
        radius_mm=ring.radius_mm,
        width_mm=ring.width_mm,
        circumference_mm=circumference,
        tiles_per_guitar=tiles_per_guitar,
        total_tiles=total_for_all,
        tile_length_mm=tile_len,
    )
    return req, total_for_all


def generate_manufacturing_plan(
    pattern: RosettePatternInDB,
    guitars: int = 1,
    tile_length_mm: float = 8.0,
    scrap_factor: float = 0.12,
) -> ManufacturingPlan:
    """
    Multi-strip-family planner:

    - Each ring has strip_family_id (e.g. 'bw_checker_main', 'green_diag').
    - Rings are grouped by strip_family_id.
    - Each family gets its own StripFamilyPlan with:
        - tile counts (with scrap per family)
        - strip length (m)
        - sticks needed (given suggested stick length)
    - Uses ring.tile_length_override_mm when set; otherwise tile_length_mm param.

    Parameters
    ----------
    pattern : RosettePatternInDB
        The rosette pattern definition.
    guitars : int
        Number of guitars to plan for (>= 1).
    tile_length_mm : float
        Default tile length along the ring circumference.
    scrap_factor : float
        Extra tiles fraction per family (e.g. 0.12 = 12% extra).
    """
    if guitars < 1:
        guitars = 1

    rings_sorted: List[RosetteRingBand] = sorted(
        pattern.ring_bands, key=lambda r: r.index
    )

    ring_requirements: List[RingRequirement] = []

    # Aggregation structures keyed by strip_family_id
    family_tiles: Dict[str, int] = defaultdict(int)
    family_tile_lengths: Dict[str, float] = {}
    family_angles: Dict[str, float] = {}
    family_color_hint: Dict[str, str | None] = {}
    family_rings: Dict[str, list[int]] = defaultdict(list)

    # 1) Per-ring requirements + aggregate tiles per family
    for ring in rings_sorted:
        req, tiles_for_ring = _tiles_for_ring(
            ring=ring,
            guitars=guitars,
            default_tile_length_mm=tile_length_mm,
        )
        ring_requirements.append(req)

        fam = ring.strip_family_id
        family_tiles[fam] += tiles_for_ring
        family_rings[fam].append(ring.index)

        # For display, we just pick the first seen values for these:
        if fam not in family_tile_lengths:
            family_tile_lengths[fam] = req.tile_length_mm
        if fam not in family_angles:
            family_angles[fam] = ring.slice_angle_deg
        if fam not in family_color_hint:
            family_color_hint[fam] = ring.color_hint

    # 2) Build StripFamilyPlan entries
    strip_plans: List[StripFamilyPlan] = []
    suggested_stick_len_mm = 300.0

    for fam, base_tiles in family_tiles.items():
        # Add scrap per-family
        total_tiles_with_scrap = int(ceil(base_tiles * (1.0 + scrap_factor)))

        tile_len = family_tile_lengths.get(fam, tile_length_mm)
        tiles_per_meter = int(1000.0 // tile_len) or 1
        total_strip_length_m = total_tiles_with_scrap / tiles_per_meter

        tiles_per_stick = int(suggested_stick_len_mm // tile_len) or 1
        sticks_needed = int(ceil(total_tiles_with_scrap / tiles_per_stick))

        strip_plans.append(
            StripFamilyPlan(
                strip_family_id=fam,
                color_hint=family_color_hint.get(fam),
                slice_angle_deg=family_angles.get(fam, 0.0),
                tile_length_mm=tile_len,
                total_tiles_needed=total_tiles_with_scrap,
                tiles_per_meter=tiles_per_meter,
                total_strip_length_m=total_strip_length_m,
                suggested_stick_length_mm=suggested_stick_len_mm,
                sticks_needed=sticks_needed,
                ring_indices=sorted(family_rings.get(fam, [])),
            )
        )

    notes = (
        "Planner groups rings by strip_family_id so each strip family "
        "gets its own tile and strip requirements. "
        "Refine per-family parameters (tile length, scrap, angle) as needed."
    )

    return ManufacturingPlan(
        pattern=pattern,
        guitars=guitars,
        ring_requirements=ring_requirements,
        strip_plans=strip_plans,
        notes=notes,
    )
