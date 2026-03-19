"""
Soundhole placement and sizing calculator (GEOMETRY-002).

Provides standard diameters by body style and position validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional


# ─── Standard Diameters by Body Style ────────────────────────────────────────

STANDARD_DIAMETERS_MM = {
    "dreadnought": 100.0,
    "om_000": 98.0,
    "jumbo": 102.0,
    "parlor": 85.0,
    "classical": 85.0,
    "concert": 90.0,
    "auditorium": 95.0,
    "archtop": None,  # Uses f-holes, different calculation
}

# Position as fraction of body length from neck block
STANDARD_POSITION_FRACTION = {
    "dreadnought": 0.50,
    "om_000": 0.48,
    "jumbo": 0.52,
    "parlor": 0.47,
    "classical": 0.50,
    "concert": 0.48,
    "auditorium": 0.49,
    "archtop": None,
}

# Valid position range (fraction of body length)
POSITION_MIN_FRACTION = 0.45
POSITION_MAX_FRACTION = 0.55


@dataclass
class SoundholeSpec:
    """Soundhole specification with placement and sizing."""

    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str  # GREEN, YELLOW, RED
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "diameter_mm": self.diameter_mm,
            "position_from_neck_block_mm": self.position_from_neck_block_mm,
            "body_style": self.body_style,
            "gate": self.gate,
            "notes": self.notes,
        }


def compute_soundhole_spec(
    body_style: str,
    body_length_mm: float,
    custom_diameter_mm: Optional[float] = None,
) -> SoundholeSpec:
    """
    Compute soundhole specification for a given body style.

    Args:
        body_style: Guitar body style (dreadnought, om_000, parlor, etc.)
        body_length_mm: Body length from neck block to tail block
        custom_diameter_mm: Override standard diameter if provided

    Returns:
        SoundholeSpec with diameter, position, and gate status
    """
    notes: List[str] = []
    gate = "GREEN"

    # Normalize body style
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")

    # Handle archtop separately
    if style_key == "archtop":
        return SoundholeSpec(
            diameter_mm=0.0,
            position_from_neck_block_mm=0.0,
            body_style=body_style,
            gate="YELLOW",
            notes=["Archtop uses f-holes; use f-hole calculator instead"],
        )

    # Get standard diameter
    if style_key in STANDARD_DIAMETERS_MM:
        standard_diameter = STANDARD_DIAMETERS_MM[style_key]
    else:
        # Unknown style, use average
        standard_diameter = 95.0
        notes.append(f"Unknown body style '{body_style}'; using default 95mm diameter")
        gate = "YELLOW"

    # Use custom diameter if provided
    diameter_mm = custom_diameter_mm if custom_diameter_mm is not None else standard_diameter

    # Validate diameter range
    if diameter_mm < 75.0:
        notes.append(f"Diameter {diameter_mm}mm below typical minimum (75mm)")
        gate = "RED"
    elif diameter_mm < 80.0:
        notes.append(f"Diameter {diameter_mm}mm is small; may affect bass response")
        gate = "YELLOW" if gate == "GREEN" else gate
    elif diameter_mm > 110.0:
        notes.append(f"Diameter {diameter_mm}mm exceeds typical maximum (110mm)")
        gate = "RED"
    elif diameter_mm > 105.0:
        notes.append(f"Diameter {diameter_mm}mm is large; ensure adequate ring width")
        gate = "YELLOW" if gate == "GREEN" else gate

    # Calculate position
    position_fraction = STANDARD_POSITION_FRACTION.get(style_key, 0.50)
    position_mm = body_length_mm * position_fraction

    # Validate position against body length
    if position_mm < body_length_mm * POSITION_MIN_FRACTION:
        notes.append("Position is too close to neck block")
        gate = "RED"
    elif position_mm > body_length_mm * POSITION_MAX_FRACTION:
        notes.append("Position is too close to bridge area")
        gate = "RED"

    # Check that soundhole fits within body (rough check)
    if position_mm - (diameter_mm / 2) < 20:
        notes.append("Soundhole edge too close to neck block")
        gate = "RED"

    return SoundholeSpec(
        diameter_mm=diameter_mm,
        position_from_neck_block_mm=round(position_mm, 1),
        body_style=body_style,
        gate=gate,
        notes=notes,
    )


def check_soundhole_position(
    diameter_mm: float,
    position_mm: float,
    body_length_mm: float,
) -> str:
    """
    Check if soundhole position is valid for given body length.

    Args:
        diameter_mm: Soundhole diameter in mm
        position_mm: Center position from neck block in mm
        body_length_mm: Total body length in mm

    Returns:
        Gate status: GREEN, YELLOW, or RED
    """
    if body_length_mm <= 0:
        return "RED"

    position_fraction = position_mm / body_length_mm

    # Check position fraction
    if position_fraction < 0.40 or position_fraction > 0.60:
        return "RED"
    elif position_fraction < POSITION_MIN_FRACTION or position_fraction > POSITION_MAX_FRACTION:
        return "YELLOW"

    # Check soundhole edges
    front_edge = position_mm - (diameter_mm / 2)
    rear_edge = position_mm + (diameter_mm / 2)

    # Front edge should be at least 20mm from neck block
    if front_edge < 20:
        return "RED"
    elif front_edge < 30:
        return "YELLOW"

    # Rear edge should leave room for bracing (at least 40mm from end)
    if rear_edge > body_length_mm - 40:
        return "RED"
    elif rear_edge > body_length_mm - 60:
        return "YELLOW"

    return "GREEN"


def list_body_styles() -> List[str]:
    """Return list of supported body styles."""
    return [k for k in STANDARD_DIAMETERS_MM.keys() if k != "archtop"]


def get_standard_diameter(body_style: str) -> Optional[float]:
    """Get standard soundhole diameter for a body style."""
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")
    return STANDARD_DIAMETERS_MM.get(style_key)
