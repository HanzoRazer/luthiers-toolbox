"""
Frame-and-panel and solid panel sizing: expansion gaps and rough blanks.

Delegates wood movement to the existing instrument wood movement calculator where possible.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.calculators.wood_movement_calc import compute_wood_movement


@dataclass(frozen=True)
class FloatingPanelGapResult:
    """Recommended gaps for a panel captured on multiple edges."""

    panel_width_across_grain_mm: float
    species: str
    rh_from: float
    rh_to: float
    total_movement_mm: float
    gap_per_edge_mm: float
    num_edges: int
    notes: str


def compute_floating_panel_gaps(
    panel_width_across_grain_mm: float,
    species: str,
    rh_from: float,
    rh_to: float,
    num_capture_edges: int = 4,
) -> FloatingPanelGapResult:
    """
    Total tangential movement across panel width; split gap across captured edges.

    For a rectangular frame, movement is taken across the panel width (tangential).
    Gap per edge = total / (2 * edges) for symmetric allowance — here we split
    total movement evenly across `num_capture_edges` (shop rule-of-thumb variant).
    """
    if panel_width_across_grain_mm <= 0 or num_capture_edges < 1:
        return FloatingPanelGapResult(
            panel_width_across_grain_mm=panel_width_across_grain_mm,
            species=species,
            rh_from=rh_from,
            rh_to=rh_to,
            total_movement_mm=0.0,
            gap_per_edge_mm=0.0,
            num_edges=num_capture_edges,
            notes="Invalid width or edge count.",
        )

    spec = compute_wood_movement(
        species=species,
        dimension_mm=panel_width_across_grain_mm,
        rh_from=rh_from,
        rh_to=rh_to,
        grain_direction="tangential",
    )
    total = abs(spec.movement_mm)
    # Allow half the total movement per pair of opposite rails — split across edges.
    gap = total / float(num_capture_edges)
    notes = (
        f"{spec.direction}; {spec.risk_note} "
        "Verify with local EMC; add finish swell separately."
    )
    return FloatingPanelGapResult(
        panel_width_across_grain_mm=panel_width_across_grain_mm,
        species=species,
        rh_from=rh_from,
        rh_to=rh_to,
        total_movement_mm=total,
        gap_per_edge_mm=gap,
        num_edges=num_capture_edges,
        notes=notes,
    )


@dataclass(frozen=True)
class PanelBlankResult:
    """Rough blank size from opening + movement allowance."""

    opening_width_mm: float
    opening_height_mm: float
    oversize_mm_each_side: float
    blank_width_mm: float
    blank_height_mm: float
    grain_note: str


def compute_panel_blank_oversize(
    opening_width_mm: float,
    opening_height_mm: float,
    oversize_mm_each_side: float = 3.0,
    width_is_across_grain: bool = True,
) -> PanelBlankResult:
    """
    Add uniform trim allowance around a measured opening.

    Does not include seasonal movement — use `compute_floating_panel_gaps` for that.
    """
    ow = max(0.0, opening_width_mm)
    oh = max(0.0, opening_height_mm)
    o = max(0.0, oversize_mm_each_side)
    bw = ow + 2 * o
    bh = oh + 2 * o
    grain_note = (
        "Width runs across grain; prioritize movement on width if solid wood."
        if width_is_across_grain
        else "Confirm grain direction against opening for movement."
    )
    return PanelBlankResult(
        opening_width_mm=ow,
        opening_height_mm=oh,
        oversize_mm_each_side=o,
        blank_width_mm=bw,
        blank_height_mm=bh,
        grain_note=grain_note,
    )
