"""
Material Yield Factors — Realistic material usage including waste.

Raw materials are never 100% utilized. This module provides
yield factors (usable % of purchased material) by material type.

Factors account for:
- Defect avoidance (knots, cracks, grain runout)
- Processing waste (sawdust, edge trim)
- Safety margins (extra for mistakes)
- Matching requirements (bookmatching backs, etc.)
"""
from typing import Dict, List
from dataclasses import dataclass

from .schemas import MaterialEstimate


# =============================================================================
# YIELD FACTORS BY MATERIAL CATEGORY
# =============================================================================

# Yield = usable material / purchased material
# Lower yield = more waste = higher effective cost

TONEWOOD_YIELDS = {
    # Tops (must be carefully selected, quarter-sawn preferred)
    "top_set_premium": 0.85,    # 15% waste for defect avoidance
    "top_set_standard": 0.80,   # 20% waste
    "top_billet": 0.70,         # 30% waste when splitting billet

    # Backs & Sides (bookmatching required)
    "back_set_premium": 0.82,
    "back_set_standard": 0.75,
    "side_set": 0.78,

    # Necks (grain orientation critical)
    "neck_blank_quartersawn": 0.80,
    "neck_blank_flatsawn": 0.75,
    "neck_blank_maple": 0.82,

    # Fretboards (tight tolerances)
    "fretboard_ebony": 0.85,
    "fretboard_rosewood": 0.82,
    "fretboard_maple": 0.88,

    # Bracing stock (small pieces, lower waste)
    "brace_stock_spruce": 0.90,
    "brace_stock_cedar": 0.88,

    # Binding (long strips, breakage risk)
    "binding_plastic": 0.92,
    "binding_wood": 0.80,
    "binding_abalone": 0.70,   # Fragile, high waste

    # Purfling
    "purfling_standard": 0.90,
    "purfling_abalone": 0.75,
}

HARDWARE_YIELDS = {
    # Hardware is typically 100% usable (no processing waste)
    "tuners": 1.00,
    "bridge_pins": 0.98,      # Occasional defect
    "nut_blank": 0.90,        # Shaping waste
    "saddle_blank": 0.90,
    "truss_rod": 1.00,
    "fret_wire": 0.92,        # End cuts, mistakes
    "strings": 1.00,
    "strap_buttons": 1.00,
    "pickups": 1.00,
    "electronics": 1.00,
}

CONSUMABLES_YIELDS = {
    # Consumables are used up in process
    "sandpaper": 1.00,        # Fully consumed
    "glue": 0.95,             # Some waste
    "finish_lacquer": 0.70,   # Overspray, waste
    "finish_oil": 0.90,
    "finish_shellac": 0.75,   # Evaporation, drips
    "stain": 0.80,
    "filler": 0.85,
}


# =============================================================================
# MATERIAL CATEGORIES
# =============================================================================

@dataclass
class MaterialCategory:
    """Material category with default yield."""
    name: str
    default_yield: float
    notes: str


CATEGORIES = {
    "tonewood": MaterialCategory(
        name="Tonewood",
        default_yield=0.80,
        notes="Varies by grade and grain requirements",
    ),
    "hardware": MaterialCategory(
        name="Hardware",
        default_yield=0.98,
        notes="Minimal waste, occasional defects",
    ),
    "consumables": MaterialCategory(
        name="Consumables",
        default_yield=0.80,
        notes="Process waste, overspray, etc.",
    ),
    "inlay": MaterialCategory(
        name="Inlay Materials",
        default_yield=0.70,
        notes="High waste for precision cutting",
    ),
}


# =============================================================================
# YIELD CALCULATION
# =============================================================================

def get_yield_factor(material_id: str) -> float:
    """
    Get yield factor for a material.

    Args:
        material_id: Material identifier

    Returns:
        Yield factor (0.0-1.0)
    """
    # Check specific yields first
    if material_id in TONEWOOD_YIELDS:
        return TONEWOOD_YIELDS[material_id]
    if material_id in HARDWARE_YIELDS:
        return HARDWARE_YIELDS[material_id]
    if material_id in CONSUMABLES_YIELDS:
        return CONSUMABLES_YIELDS[material_id]

    # Infer from material name
    material_lower = material_id.lower()

    if any(w in material_lower for w in ["top", "back", "side", "neck", "fretboard"]):
        return 0.80  # Default tonewood
    if any(w in material_lower for w in ["tuner", "pickup", "bridge", "nut", "saddle"]):
        return 0.98  # Default hardware
    if any(w in material_lower for w in ["glue", "finish", "lacquer", "oil", "sand"]):
        return 0.80  # Default consumable
    if any(w in material_lower for w in ["inlay", "abalone", "pearl", "mop"]):
        return 0.70  # Default inlay

    return 0.85  # Generic default


def calculate_material_cost_with_waste(
    base_cost: float,
    material_id: str,
    quantity: int = 1,
) -> MaterialEstimate:
    """
    Calculate material cost including waste factor.

    Args:
        base_cost: Cost per unit at 100% yield
        material_id: Material identifier
        quantity: Number of units

    Returns:
        MaterialEstimate with adjusted cost
    """
    yield_factor = get_yield_factor(material_id)

    # Adjusted cost = base_cost / yield
    # (If you only use 80%, you need to buy 125%)
    adjusted_unit_cost = base_cost / yield_factor
    total_adjusted = adjusted_unit_cost * quantity

    # Infer category
    material_lower = material_id.lower()
    if any(w in material_lower for w in ["top", "back", "side", "neck", "fretboard", "brace"]):
        category = "tonewood"
    elif any(w in material_lower for w in ["tuner", "pickup", "bridge", "electronic"]):
        category = "hardware"
    elif any(w in material_lower for w in ["glue", "finish", "sand"]):
        category = "consumables"
    else:
        category = "other"

    return MaterialEstimate(
        category=category,
        base_cost=round(base_cost * quantity, 2),
        waste_factor=round(1 / yield_factor, 3),  # Multiplier form
        adjusted_cost=round(total_adjusted, 2),
    )


def estimate_material_costs(
    bom_items: List[Dict],
    include_waste: bool = True,
) -> List[MaterialEstimate]:
    """
    Estimate material costs from BOM with waste factors.

    Args:
        bom_items: List of {"material_id": str, "unit_cost": float, "quantity": int}
        include_waste: Whether to apply waste factors

    Returns:
        List of MaterialEstimate
    """
    estimates = []

    for item in bom_items:
        material_id = item.get("material_id", "unknown")
        unit_cost = item.get("unit_cost", 0)
        quantity = item.get("quantity", 1)

        if include_waste:
            estimate = calculate_material_cost_with_waste(
                base_cost=unit_cost,
                material_id=material_id,
                quantity=quantity,
            )
        else:
            estimate = MaterialEstimate(
                category="direct",
                base_cost=round(unit_cost * quantity, 2),
                waste_factor=1.0,
                adjusted_cost=round(unit_cost * quantity, 2),
            )

        estimates.append(estimate)

    return estimates


# =============================================================================
# BATCH EFFICIENCY
# =============================================================================

def batch_material_efficiency(
    base_yield: float,
    batch_size: int,
) -> float:
    """
    Calculate improved yield for batch production.

    Larger batches can:
    - Better utilize offcuts
    - Share setup waste
    - Optimize cutting patterns

    Args:
        base_yield: Single-unit yield factor
        batch_size: Number of units

    Returns:
        Improved yield factor for batch
    """
    if batch_size <= 1:
        return base_yield

    # Diminishing improvement: ~2% better per doubling, max 10% improvement
    import math
    doublings = math.log2(batch_size)
    improvement = min(0.10, 0.02 * doublings)

    # Can't exceed 100% yield
    return min(1.0, base_yield + improvement)
