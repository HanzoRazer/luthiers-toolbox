"""
Rosette BOM (Bill of Materials) — Veneer cutting bill calculations.

Provides COL_WIDTHS arrays and material breakdowns for each preset pattern.
Used by the mothership for veneer cutting bill breakdowns by column width.

The key data structures:
- COL_WIDTHS: Per-column width array for each preset
- PRESET_BOM_SUMMARY: Pre-computed BOM summary for each preset
- generate_veneer_cut_bill(): Generate detailed cutting bill for a preset

Example usage:
    from app.cam.rosette.rosette_bom import (
        get_col_widths,
        get_veneer_cut_bill,
        get_all_preset_bom_summaries,
    )

    # Get column widths for a preset
    widths = get_col_widths("classic_rope_5x9")
    # -> [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    # Get full cutting bill
    bill = get_veneer_cut_bill("hauser_rope_6x11", strip_length_mm=250.0)
    # -> {"col_widths": [...], "cut_list": [...], "total_area_mm2": ...}

    # Get all preset summaries
    summaries = get_all_preset_bom_summaries()
"""

from typing import Dict, List, Any, Optional

from .presets import PRESET_MATRICES
from .pattern_schemas import MatrixFormula


# =============================================================================
# PRE-COMPUTED COL_WIDTHS FOR ALL PRESETS
# =============================================================================

def _compute_col_widths_map() -> Dict[str, List[float]]:
    """Pre-compute COL_WIDTHS arrays for all presets."""
    return {
        preset_id: formula.col_widths
        for preset_id, formula in PRESET_MATRICES.items()
    }


# Cached COL_WIDTHS for all presets (computed once at module load)
COL_WIDTHS: Dict[str, List[float]] = _compute_col_widths_map()


# =============================================================================
# PRESET BOM SUMMARY (pre-computed for quick lookup)
# =============================================================================

def _compute_preset_bom_summaries() -> Dict[str, Dict[str, Any]]:
    """Pre-compute BOM summaries for all presets."""
    summaries = {}
    for preset_id, formula in PRESET_MATRICES.items():
        material_totals = formula.get_material_totals()
        summaries[preset_id] = {
            "name": formula.name,
            "col_widths": formula.col_widths,
            "strip_width_mm": formula.strip_width_mm,
            "strip_thickness_mm": formula.strip_thickness_mm,
            "chip_length_mm": formula.chip_length_mm,
            "column_count": formula.column_count,
            "row_count": formula.row_count,
            "total_pattern_width_mm": formula.get_pattern_width_mm(),
            "total_pattern_height_mm": formula.get_pattern_height_mm(),
            "material_totals": material_totals,
            "total_strips": sum(material_totals.values()),
        }
    return summaries


# Cached BOM summaries for all presets
PRESET_BOM_SUMMARY: Dict[str, Dict[str, Any]] = _compute_preset_bom_summaries()


# =============================================================================
# PUBLIC API
# =============================================================================

def get_col_widths(preset_id: str) -> Optional[List[float]]:
    """
    Get the COL_WIDTHS array for a preset.

    Args:
        preset_id: Preset identifier (e.g., "classic_rope_5x9")

    Returns:
        List of column widths in mm, or None if preset not found
    """
    return COL_WIDTHS.get(preset_id)


def get_veneer_cut_bill(
    preset_id: str,
    strip_length_mm: float = 200.0,
    waste_allowance_pct: float = 15.0,
) -> Optional[Dict[str, Any]]:
    """
    Generate a complete veneer cutting bill for a preset.

    Args:
        preset_id: Preset identifier
        strip_length_mm: Length of veneer strips to cut (panel dimension)
        waste_allowance_pct: Waste allowance percentage (default 15%)

    Returns:
        Dict with col_widths, cut_list, areas, and totals, or None if preset not found
    """
    formula = PRESET_MATRICES.get(preset_id)
    if not formula:
        return None

    material_totals = formula.get_material_totals()
    cut_list = []
    total_area_mm2 = 0.0

    for material, count in material_totals.items():
        area = count * formula.strip_width_mm * strip_length_mm
        total_area_mm2 += area
        cut_list.append({
            "material": material,
            "quantity": count,
            "width_mm": formula.strip_width_mm,
            "length_mm": strip_length_mm,
            "thickness_mm": formula.strip_thickness_mm,
            "area_mm2": round(area, 2),
        })

    adjusted_area = total_area_mm2 * (1 + waste_allowance_pct / 100)

    return {
        "preset_id": preset_id,
        "preset_name": formula.name,
        "col_widths": formula.col_widths,
        "strip_width_mm": formula.strip_width_mm,
        "strip_thickness_mm": formula.strip_thickness_mm,
        "chip_length_mm": formula.chip_length_mm,
        "column_count": formula.column_count,
        "row_count": formula.row_count,
        "total_pattern_width_mm": formula.get_pattern_width_mm(),
        "cut_list": cut_list,
        "total_area_mm2": round(total_area_mm2, 2),
        "waste_allowance_pct": waste_allowance_pct,
        "adjusted_area_mm2": round(adjusted_area, 2),
    }


def get_all_preset_bom_summaries() -> Dict[str, Dict[str, Any]]:
    """
    Get pre-computed BOM summaries for all presets.

    Returns:
        Dict mapping preset_id to BOM summary
    """
    return PRESET_BOM_SUMMARY.copy()


def get_preset_col_widths_table() -> Dict[str, Dict[str, Any]]:
    """
    Get a summary table of COL_WIDTHS for all presets.

    Useful for UI dropdowns and quick reference.

    Returns:
        Dict mapping preset_id to {name, col_widths, total_width_mm}
    """
    return {
        preset_id: {
            "name": formula.name,
            "col_widths": formula.col_widths,
            "total_width_mm": formula.get_pattern_width_mm(),
            "column_count": formula.column_count,
        }
        for preset_id, formula in PRESET_MATRICES.items()
    }


def list_presets_by_width_range(
    min_width_mm: float = 0.0,
    max_width_mm: float = 20.0,
) -> List[Dict[str, Any]]:
    """
    List presets filtered by total pattern width range.

    Args:
        min_width_mm: Minimum pattern width
        max_width_mm: Maximum pattern width

    Returns:
        List of preset summaries within the width range
    """
    results = []
    for preset_id, formula in PRESET_MATRICES.items():
        total_width = formula.get_pattern_width_mm()
        if min_width_mm <= total_width <= max_width_mm:
            results.append({
                "preset_id": preset_id,
                "name": formula.name,
                "col_widths": formula.col_widths,
                "total_width_mm": total_width,
                "strip_width_mm": formula.strip_width_mm,
                "column_count": formula.column_count,
            })
    return sorted(results, key=lambda x: x["total_width_mm"])


def get_material_requirements_all_presets(
    strip_length_mm: float = 200.0,
) -> Dict[str, Dict[str, float]]:
    """
    Get total material area requirements for all presets.

    Useful for inventory planning - shows how much of each material
    is needed across all available patterns.

    Args:
        strip_length_mm: Length of veneer strips

    Returns:
        Dict mapping preset_id to {material: area_mm2}
    """
    results = {}
    for preset_id, formula in PRESET_MATRICES.items():
        material_totals = formula.get_material_totals()
        areas = {}
        for material, count in material_totals.items():
            areas[material] = round(
                count * formula.strip_width_mm * strip_length_mm, 2
            )
        results[preset_id] = areas
    return results


# =============================================================================
# BATCH BOM GENERATION
# =============================================================================

def generate_batch_veneer_bill(
    preset_ids: List[str],
    strip_length_mm: float = 200.0,
    quantities: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Generate a combined veneer cutting bill for multiple presets.

    Useful for batch production planning.

    Args:
        preset_ids: List of preset identifiers
        strip_length_mm: Length of veneer strips
        quantities: Optional dict mapping preset_id to quantity (default 1 each)

    Returns:
        Combined bill with per-preset and aggregate totals
    """
    if quantities is None:
        quantities = {pid: 1 for pid in preset_ids}

    per_preset = []
    aggregate_materials: Dict[str, float] = {}
    total_area = 0.0

    for preset_id in preset_ids:
        qty = quantities.get(preset_id, 1)
        bill = get_veneer_cut_bill(preset_id, strip_length_mm)
        if bill is None:
            continue

        # Scale by quantity
        scaled_bill = bill.copy()
        scaled_bill["quantity"] = qty
        scaled_bill["total_area_mm2"] *= qty
        scaled_bill["adjusted_area_mm2"] *= qty
        for item in scaled_bill["cut_list"]:
            item["quantity"] *= qty
            item["area_mm2"] *= qty

        per_preset.append(scaled_bill)
        total_area += scaled_bill["total_area_mm2"]

        # Aggregate materials
        for item in scaled_bill["cut_list"]:
            mat = item["material"]
            aggregate_materials[mat] = aggregate_materials.get(mat, 0) + item["area_mm2"]

    return {
        "preset_count": len(per_preset),
        "per_preset_bills": per_preset,
        "aggregate_materials_mm2": {k: round(v, 2) for k, v in aggregate_materials.items()},
        "total_area_mm2": round(total_area, 2),
        "total_area_with_waste_mm2": round(total_area * 1.15, 2),
    }
