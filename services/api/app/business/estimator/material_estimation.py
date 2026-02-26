"""
Material Estimation Module — Material cost calculation with waste factors.

Extracted from estimator_service.py for single-responsibility.
"""
from typing import List, Optional

from .schemas import (
    ComplexitySelections,
    MaterialEstimate,
    InstrumentType,
)
from .material_yield import estimate_material_costs


def estimate_materials(
    instrument_type: InstrumentType,
    complexity: ComplexitySelections,
    include_waste: bool,
    bom_service: Optional[object] = None,
) -> List[MaterialEstimate]:
    """
    Estimate material costs with waste factors.

    Args:
        instrument_type: Type of instrument being built
        complexity: Complexity selections from request
        include_waste: Whether to include waste factors
        bom_service: Optional BOM service for template lookup

    Returns:
        List of material estimates
    """
    # Try to get BOM template if service provided
    if bom_service is not None:
        try:
            from ..schemas import InstrumentType as BOMInstrumentType
            # Map to BOM instrument type
            bom_type_map = {
                InstrumentType.ACOUSTIC_DREADNOUGHT: "acoustic_dreadnought",
                InstrumentType.CLASSICAL: "classical",
            }
            bom_type = bom_type_map.get(instrument_type)

            if bom_type:
                bom = bom_service.create_bom_from_template(
                    instrument_type=bom_type,
                    instrument_name="Estimate",
                )
                items = [
                    {
                        "material_id": item.material_id,
                        "unit_cost": item.unit_cost,
                        "quantity": item.quantity,
                    }
                    for item in bom.items
                ]
                return estimate_material_costs(items, include_waste)
        except (ImportError, KeyError, ValueError, AttributeError):  # WP-1: BOM estimate
            pass

    # Fallback: generic estimates by instrument type
    if instrument_type.value.startswith("acoustic"):
        return _acoustic_material_estimate(include_waste)
    elif "electric" in instrument_type.value or "bass" in instrument_type.value:
        return _electric_material_estimate(complexity, include_waste)
    else:
        return _acoustic_material_estimate(include_waste)


def _acoustic_material_estimate(include_waste: bool) -> List[MaterialEstimate]:
    """
    Generic acoustic guitar material estimate.

    Args:
        include_waste: Whether to include waste factors

    Returns:
        List of material estimates for acoustic guitar
    """
    items = [
        {"material_id": "top_set_premium", "unit_cost": 120, "quantity": 1},
        {"material_id": "back_set_premium", "unit_cost": 180, "quantity": 1},
        {"material_id": "neck_blank_quartersawn", "unit_cost": 80, "quantity": 1},
        {"material_id": "fretboard_ebony", "unit_cost": 45, "quantity": 1},
        {"material_id": "binding_wood", "unit_cost": 25, "quantity": 1},
        {"material_id": "brace_stock_spruce", "unit_cost": 20, "quantity": 1},
        {"material_id": "tuners", "unit_cost": 80, "quantity": 1},
        {"material_id": "fret_wire", "unit_cost": 15, "quantity": 1},
        {"material_id": "finish_lacquer", "unit_cost": 60, "quantity": 1},
        {"material_id": "glue", "unit_cost": 20, "quantity": 1},
    ]
    return estimate_material_costs(items, include_waste)


def _electric_material_estimate(
    complexity: ComplexitySelections,
    include_waste: bool,
) -> List[MaterialEstimate]:
    """
    Generic electric guitar material estimate.

    Args:
        complexity: Complexity selections (for pickup count)
        include_waste: Whether to include waste factors

    Returns:
        List of material estimates for electric guitar
    """
    items = [
        {"material_id": "body_blank", "unit_cost": 100, "quantity": 1},
        {"material_id": "neck_blank_maple", "unit_cost": 70, "quantity": 1},
        {"material_id": "fretboard_rosewood", "unit_cost": 35, "quantity": 1},
        {"material_id": "tuners", "unit_cost": 60, "quantity": 1},
        {"material_id": "bridge", "unit_cost": 50, "quantity": 1},
        {"material_id": "fret_wire", "unit_cost": 15, "quantity": 1},
        {"material_id": "finish_lacquer", "unit_cost": 50, "quantity": 1},
    ]

    # Add pickups based on complexity
    if complexity.pickup_count > 0:
        pickup_cost = 80 * complexity.pickup_count
        items.append({"material_id": "pickups", "unit_cost": pickup_cost, "quantity": 1})
        items.append({"material_id": "electronics", "unit_cost": 40, "quantity": 1})

    return estimate_material_costs(items, include_waste)
