"""
Treble Bleed Calculator

Calculates optimal treble bleed network values for volume pot roll-off.

MODEL NOTES:
- Standard treble bleed: capacitor only (bright, can be harsh)
- Kinman-style: capacitor + series resistor (warmer, more natural)
- Duncan-style: capacitor + parallel resistor (balanced)
- Values depend on:
  - Volume pot value (250K, 500K, 1M)
  - Pickup impedance
  - Desired brightness level

References:
- https://www.seymourduncan.com/blog/latest-updates/treble-bleed-which-values-to-use
- https://www.premierguitar.com/diy/treble-bleed-circuits
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

TrebleBleedType = Literal["capacitor_only", "series_resistor", "parallel_resistor"]


@dataclass
class TrebleBleedResult:
    """Result from treble bleed calculation."""
    circuit_type: TrebleBleedType
    capacitance_nf: float
    resistance_kohm: Optional[float]
    description: str
    notes: str


# Common treble bleed values by pot value
STANDARD_VALUES = {
    250: {  # 250K pot (single coils)
        "capacitor_only": (680, None),      # 680pF = 0.68nF
        "series_resistor": (1000, 150),     # 1nF + 150K
        "parallel_resistor": (1200, 130),   # 1.2nF || 130K
    },
    500: {  # 500K pot (humbuckers)
        "capacitor_only": (1000, None),     # 1nF
        "series_resistor": (1500, 150),     # 1.5nF + 150K
        "parallel_resistor": (2200, 100),   # 2.2nF || 100K
    },
    1000: {  # 1M pot (high impedance/piezo blend)
        "capacitor_only": (470, None),      # 470pF
        "series_resistor": (680, 220),      # 680pF + 220K
        "parallel_resistor": (1000, 150),   # 1nF || 150K
    },
}


def suggest_treble_bleed(
    pot_value_kohm: int,
    circuit_type: TrebleBleedType = "series_resistor",
    *,
    brightness: float = 0.5,  # 0 = darker, 1 = brighter
) -> TrebleBleedResult:
    """
    Suggest treble bleed component values.

    Args:
        pot_value_kohm: Volume pot value in kohms (250, 500, 1000)
        circuit_type: Type of treble bleed circuit
        brightness: Brightness preference 0-1 (affects capacitor value)

    Returns:
        TrebleBleedResult with suggested values
    """
    # Normalize pot value to standard
    if pot_value_kohm <= 300:
        standard_pot = 250
    elif pot_value_kohm <= 750:
        standard_pot = 500
    else:
        standard_pot = 1000

    if standard_pot not in STANDARD_VALUES:
        standard_pot = 500  # Default

    base_cap, base_res = STANDARD_VALUES[standard_pot][circuit_type]

    # Adjust capacitance for brightness preference
    # Higher cap = more highs pass through = brighter
    brightness_factor = 0.7 + (brightness * 0.6)  # 0.7x to 1.3x
    adjusted_cap = base_cap * brightness_factor

    # Round to nearest standard value
    adjusted_cap = _nearest_standard_cap(adjusted_cap)

    # Build description
    if circuit_type == "capacitor_only":
        description = f"{adjusted_cap:.0f}pF capacitor across volume pot lugs 1 & 3"
        notes = "Simple but can sound harsh at low volumes. Good for clean tones."
    elif circuit_type == "series_resistor":
        description = f"{adjusted_cap:.0f}pF cap in series with {base_res}K resistor"
        notes = "Kinman-style. Natural roll-off, retains some bass. Most versatile."
    else:  # parallel_resistor
        description = f"{adjusted_cap:.0f}pF cap in parallel with {base_res}K resistor"
        notes = "Duncan-style. Balanced highs/lows. Good for high-gain."

    return TrebleBleedResult(
        circuit_type=circuit_type,
        capacitance_nf=adjusted_cap / 1000.0,  # Convert pF to nF
        resistance_kohm=base_res,
        description=description,
        notes=notes,
    )


def _nearest_standard_cap(value_pf: float) -> float:
    """Round to nearest standard capacitor value (E12 series)."""
    standard_pf = [
        100, 120, 150, 180, 220, 270, 330, 390, 470, 560, 680, 820,
        1000, 1200, 1500, 1800, 2200, 2700, 3300, 3900, 4700,
    ]
    return min(standard_pf, key=lambda x: abs(x - value_pf))
