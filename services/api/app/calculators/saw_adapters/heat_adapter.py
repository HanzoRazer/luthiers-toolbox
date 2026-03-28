"""
Heat Risk Adapter (Saw Blades)

Estimates thermal risk during saw cutting operations.

MODEL NOTES:
- Heat increases with:
  - High rim speed (friction)
  - Low bite per tooth (rubbing instead of cutting)
  - Dense/resinous materials (ebony, rosewood)
  - Dull blades
- Heat decreases with:
  - Proper chip evacuation
  - Adequate bite per tooth
  - Sharp carbide tips
  - Less dense materials (spruce, cedar)

This is a simplified model. Real implementation should consider:
- Material thermal conductivity
- Blade coating (PTFE, etc.)
- Coolant/dust collection
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Material heat sensitivity factors (higher = more heat sensitive)
MATERIAL_HEAT_FACTORS = {
    "ebony": 1.4,
    "rosewood": 1.3,
    "maple": 1.0,
    "mahogany": 0.95,
    "walnut": 0.9,
    "cherry": 0.85,
    "spruce": 0.7,
    "cedar": 0.65,
    "poplar": 0.6,
    "mdf": 1.2,  # Glue content
    "plywood": 1.1,
}

HeatCategory = Literal["COOL", "WARM", "HOT", "CRITICAL"]


@dataclass
class SawHeatResult:
    """Result from saw heat risk calculation."""
    heat_index: float  # 0-1 scale
    category: HeatCategory
    material_factor: float
    message: str


def estimate_saw_heat_risk(
    bite_mm: float,
    rim_speed_m_s: float,
    material_id: str,
    *,
    ideal_bite_min: float = 0.08,
    ideal_bite_max: float = 0.30,
) -> SawHeatResult:
    """
    Estimate heat risk for a saw cutting operation.

    Args:
        bite_mm: Bite per tooth in mm
        rim_speed_m_s: Rim speed in m/s
        material_id: Material identifier
        ideal_bite_min: Minimum ideal bite for this operation
        ideal_bite_max: Maximum ideal bite for this operation

    Returns:
        SawHeatResult with heat index and category
    """
    # Get material heat sensitivity
    material_factor = MATERIAL_HEAT_FACTORS.get(
        material_id.lower(), 1.0
    )

    # Base heat from bite (rubbing if too low)
    if bite_mm < ideal_bite_min:
        bite_heat = 0.5 + 0.5 * (1 - bite_mm / ideal_bite_min)
    elif bite_mm > ideal_bite_max:
        # Too aggressive - also generates heat
        bite_heat = 0.3 * (bite_mm - ideal_bite_max) / ideal_bite_max
    else:
        bite_heat = 0.1  # Ideal range

    # Heat from rim speed (normalized to typical 30 m/s)
    speed_heat = min(1.0, (rim_speed_m_s / 30.0) ** 1.5) * 0.4

    # Combined heat index
    raw_heat = (bite_heat * 0.6 + speed_heat * 0.4) * material_factor
    heat_index = min(1.0, max(0.0, raw_heat))

    # Categorize
    if heat_index < 0.25:
        category: HeatCategory = "COOL"
        message = "Heat risk low - good cutting conditions"
    elif heat_index < 0.50:
        category = "WARM"
        message = "Heat moderate - monitor for burning"
    elif heat_index < 0.75:
        category = "HOT"
        message = "Heat elevated - risk of burn marks, adjust feed"
    else:
        category = "CRITICAL"
        message = "Heat critical - stop and check blade/settings"

    return SawHeatResult(
        heat_index=heat_index,
        category=category,
        material_factor=material_factor,
        message=message,
    )
