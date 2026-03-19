"""
Nut Slot Depth Calculator (CONSTRUCTION-001)
=============================================

Calculates nut slot depths for guitar strings based on:
- String gauge (diameter)
- Fret crown height
- Desired clearance above first fret

Formula:
    slot_depth = string_diameter / 2 + fret_crown_height / 2 + clearance

The string should sit with its center at the fret crown height level,
with a small clearance (0.1-0.15mm) for clean action without buzzing.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any


# ─── String Diameter Table (gauge in inches → mm) ────────────────────────────

STRING_DIAMETERS_MM: Dict[str, float] = {
    # Plain steel strings
    "008": 0.203,
    "009": 0.229,
    "010": 0.254,
    "011": 0.279,
    "012": 0.305,
    "013": 0.330,
    "014": 0.356,
    "015": 0.381,
    "016": 0.406,
    "017": 0.432,
    "018": 0.457,
    # Wound strings
    "020": 0.508,
    "022": 0.559,
    "024": 0.610,
    "026": 0.660,
    "028": 0.711,
    "030": 0.762,
    "032": 0.813,
    "034": 0.864,
    "036": 0.914,
    "038": 0.965,
    "040": 1.016,
    "042": 1.067,
    "044": 1.118,
    "046": 1.168,
    "048": 1.219,
    "050": 1.270,
    "052": 1.321,
    "053": 1.346,
    "054": 1.372,
    "056": 1.422,
}

# Common string sets for convenience
STANDARD_STRING_SETS: Dict[str, List[Dict[str, Any]]] = {
    "light_electric_009": [
        {"name": "e", "gauge_inch": 0.009},
        {"name": "B", "gauge_inch": 0.011},
        {"name": "G", "gauge_inch": 0.016},
        {"name": "D", "gauge_inch": 0.024},
        {"name": "A", "gauge_inch": 0.032},
        {"name": "E", "gauge_inch": 0.042},
    ],
    "regular_electric_010": [
        {"name": "e", "gauge_inch": 0.010},
        {"name": "B", "gauge_inch": 0.013},
        {"name": "G", "gauge_inch": 0.017},
        {"name": "D", "gauge_inch": 0.026},
        {"name": "A", "gauge_inch": 0.036},
        {"name": "E", "gauge_inch": 0.046},
    ],
    "light_acoustic_012": [
        {"name": "e", "gauge_inch": 0.012},
        {"name": "B", "gauge_inch": 0.016},
        {"name": "G", "gauge_inch": 0.024},
        {"name": "D", "gauge_inch": 0.032},
        {"name": "A", "gauge_inch": 0.042},
        {"name": "E", "gauge_inch": 0.053},
    ],
    "medium_acoustic_013": [
        {"name": "e", "gauge_inch": 0.013},
        {"name": "B", "gauge_inch": 0.017},
        {"name": "G", "gauge_inch": 0.026},
        {"name": "D", "gauge_inch": 0.035},
        {"name": "A", "gauge_inch": 0.045},
        {"name": "E", "gauge_inch": 0.056},
    ],
}


# ─── Fret Crown Heights by Type ───────────────────────────────────────────────

FRET_CROWN_HEIGHTS_MM: Dict[str, float] = {
    "vintage_narrow": 0.89,   # 0.035"
    "medium": 1.19,           # 0.047"
    "medium_jumbo": 1.40,     # 0.055"
    "jumbo": 1.52,            # 0.060"
    "extra_jumbo": 1.65,      # 0.065"
    "evo_gold": 1.14,         # 0.045"
}


# ─── Output Dataclass ─────────────────────────────────────────────────────────

@dataclass
class NutSlotSpec:
    """Specification for a single nut slot."""
    string_name: str
    gauge_inch: float
    gauge_mm: float
    fret_type: str
    slot_depth_mm: float
    slot_width_mm: float              # gauge + 0.05mm clearance
    string_height_above_first_fret_mm: float
    gate: str                         # GREEN, YELLOW, RED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Core Functions ───────────────────────────────────────────────────────────

def _gauge_to_mm(gauge_inch: float) -> float:
    """Convert gauge in inches to mm."""
    return gauge_inch * 25.4


def _compute_gate(string_height_mm: float) -> str:
    """
    Determine gate based on string height above first fret.

    GREEN:  0.3-0.5mm — optimal range
    YELLOW: 0.2-0.3mm (low — buzzing risk) or 0.5-0.8mm (high — intonation)
    RED:    < 0.2mm or > 0.8mm
    """
    if 0.3 <= string_height_mm <= 0.5:
        return "GREEN"
    elif 0.2 <= string_height_mm < 0.3:
        return "YELLOW"  # Low — buzzing risk
    elif 0.5 < string_height_mm <= 0.8:
        return "YELLOW"  # High — intonation affected
    else:
        return "RED"


def compute_nut_slot_depth(
    gauge_inch: float,
    fret_type: str,
    clearance_mm: float = 0.13,
) -> NutSlotSpec:
    """
    Compute nut slot depth for a single string.

    Formula:
        slot_depth = string_diameter / 2 + fret_crown_height / 2 + clearance

    The string should sit with its center approximately at the
    fret crown height level, with clearance for clean action.

    Args:
        gauge_inch: String gauge in inches (e.g., 0.012)
        fret_type: Fret type (vintage_narrow, medium, jumbo, etc.)
        clearance_mm: Desired clearance above first fret (0.1-0.15mm typical)

    Returns:
        NutSlotSpec with all calculated values
    """
    # Get fret crown height
    fret_crown_height = FRET_CROWN_HEIGHTS_MM.get(fret_type.lower().strip())
    if fret_crown_height is None:
        # Default to medium if unknown
        fret_crown_height = FRET_CROWN_HEIGHTS_MM["medium"]

    # Convert gauge to mm
    gauge_mm = _gauge_to_mm(gauge_inch)
    string_radius = gauge_mm / 2

    # Calculate slot depth
    # String sits with center at fret crown + clearance
    slot_depth_mm = string_radius + (fret_crown_height / 2) + clearance_mm

    # Slot width: gauge + 0.05mm clearance for smooth movement
    slot_width_mm = gauge_mm + 0.05

    # String height above first fret when properly seated
    # This is the clearance we designed for
    string_height_above_first_fret_mm = clearance_mm + (fret_crown_height / 2)

    # Determine gate
    gate = _compute_gate(string_height_above_first_fret_mm)

    return NutSlotSpec(
        string_name="",  # Set by caller
        gauge_inch=gauge_inch,
        gauge_mm=round(gauge_mm, 3),
        fret_type=fret_type,
        slot_depth_mm=round(slot_depth_mm, 3),
        slot_width_mm=round(slot_width_mm, 3),
        string_height_above_first_fret_mm=round(string_height_above_first_fret_mm, 3),
        gate=gate,
    )


def compute_nut_slot_schedule(
    string_set: List[Dict[str, Any]],
    fret_type: str,
    nut_width_mm: float = 43.0,
    clearance_mm: float = 0.13,
) -> List[NutSlotSpec]:
    """
    Compute nut slot schedule for an entire string set.

    Args:
        string_set: List of dicts with 'name' and 'gauge_inch' keys
        fret_type: Fret type for all strings
        nut_width_mm: Total nut width (for future spacing calculations)
        clearance_mm: Desired clearance above first fret

    Returns:
        List of NutSlotSpec for each string
    """
    schedule: List[NutSlotSpec] = []

    for string_info in string_set:
        name = string_info.get("name", "")
        gauge_inch = string_info.get("gauge_inch", 0.010)

        spec = compute_nut_slot_depth(
            gauge_inch=gauge_inch,
            fret_type=fret_type,
            clearance_mm=clearance_mm,
        )
        # Set the string name
        spec.string_name = name

        schedule.append(spec)

    return schedule


def list_fret_types() -> List[str]:
    """Return list of supported fret types."""
    return list(FRET_CROWN_HEIGHTS_MM.keys())


def list_string_sets() -> List[str]:
    """Return list of predefined string sets."""
    return list(STANDARD_STRING_SETS.keys())


def get_string_set(name: str) -> List[Dict[str, Any]]:
    """Get a predefined string set by name."""
    return STANDARD_STRING_SETS.get(name, STANDARD_STRING_SETS["light_acoustic_012"])
