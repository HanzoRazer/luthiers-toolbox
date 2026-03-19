"""
Bridge Geometry Calculator — GEOMETRY-004.

Computes bridge dimensions, pin positions, and saddle slot specs
based on body style and scale length.

Key relationships:
- String spacing at bridge (E to e): 52-56mm typical
- Pin spacing matches string spacing
- Saddle slot: width 3.2mm, depth 4-5mm typical
- Bridge plate sized to distribute string tension
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any


# ─── Bridge Dimension Standards ──────────────────────────────────────────────

BRIDGE_SPECS: Dict[str, Dict[str, Any]] = {
    "dreadnought": {
        "string_spacing_mm": 54.0,
        "bridge_length_mm": 170.0,
        "bridge_width_mm": 32.0,
        "saddle_slot_width_mm": 3.2,
        "saddle_slot_depth_mm": 4.5,
        "bridge_plate_length_mm": 180.0,
        "bridge_plate_width_mm": 100.0,
        "material": "ebony",
    },
    "om_000": {
        "string_spacing_mm": 52.0,
        "bridge_length_mm": 165.0,
        "bridge_width_mm": 30.0,
        "saddle_slot_width_mm": 3.2,
        "saddle_slot_depth_mm": 4.5,
        "bridge_plate_length_mm": 170.0,
        "bridge_plate_width_mm": 95.0,
        "material": "ebony",
    },
    "parlor": {
        "string_spacing_mm": 50.0,
        "bridge_length_mm": 155.0,
        "bridge_width_mm": 28.0,
        "saddle_slot_width_mm": 3.2,
        "saddle_slot_depth_mm": 4.0,
        "bridge_plate_length_mm": 155.0,
        "bridge_plate_width_mm": 85.0,
        "material": "ebony",
    },
    "classical": {
        "string_spacing_mm": 58.0,
        "bridge_length_mm": 180.0,
        "bridge_width_mm": 28.0,
        "saddle_slot_width_mm": 3.2,
        "saddle_slot_depth_mm": 5.0,
        "bridge_plate_length_mm": 0.0,  # No bridge plate on classical
        "bridge_plate_width_mm": 0.0,
        "material": "rosewood",
    },
    "archtop": {
        "string_spacing_mm": 52.0,
        "bridge_length_mm": 95.0,
        "bridge_width_mm": 18.0,
        "saddle_slot_width_mm": 0.0,  # Tune-o-matic, no slot
        "saddle_slot_depth_mm": 0.0,
        "bridge_plate_length_mm": 0.0,  # No bridge plate
        "bridge_plate_width_mm": 0.0,
        "material": "ebony",
    },
    "jumbo": {
        "string_spacing_mm": 55.0,
        "bridge_length_mm": 175.0,
        "bridge_width_mm": 33.0,
        "saddle_slot_width_mm": 3.2,
        "saddle_slot_depth_mm": 4.5,
        "bridge_plate_length_mm": 185.0,
        "bridge_plate_width_mm": 105.0,
        "material": "ebony",
    },
}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class BridgeSpec:
    """Complete bridge geometry specification."""
    body_style: str
    string_spacing_mm: float      # E to e at saddle
    bridge_length_mm: float       # total bridge length
    bridge_width_mm: float        # front to back
    saddle_slot_width_mm: float
    saddle_slot_depth_mm: float
    pin_spacing_mm: float         # center to center (same as string spacing)
    bridge_plate_length_mm: float
    bridge_plate_width_mm: float
    material: str
    gate: str
    string_count: int = 6
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return asdict(self)


@dataclass
class PinPositions:
    """Bridge pin positions from centerline."""
    positions_mm: List[float]
    string_spacing_mm: float
    string_count: int
    total_span_mm: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return asdict(self)


# ─── Core Functions ──────────────────────────────────────────────────────────

def compute_bridge_spec(
    body_style: str,
    scale_length_mm: float,
    string_count: int = 6,
    custom_spacing_mm: Optional[float] = None,
) -> BridgeSpec:
    """
    Compute bridge geometry specification for a body style.

    Args:
        body_style: Body style name (dreadnought, om_000, parlor, etc.)
        scale_length_mm: Scale length in mm (used for validation)
        string_count: Number of strings (default 6)
        custom_spacing_mm: Optional custom string spacing override

    Returns:
        BridgeSpec with all bridge dimensions

    Raises:
        ValueError: If body_style is not recognized
    """
    body_style_lower = body_style.lower().replace("-", "_").replace(" ", "_")

    if body_style_lower not in BRIDGE_SPECS:
        raise ValueError(
            f"Unknown body style: '{body_style}'. "
            f"Supported: {list(BRIDGE_SPECS.keys())}"
        )

    spec_data = BRIDGE_SPECS[body_style_lower]
    notes: List[str] = []
    gate = "GREEN"

    # Use custom spacing if provided
    string_spacing = custom_spacing_mm if custom_spacing_mm else spec_data["string_spacing_mm"]

    # Adjust spacing for non-6-string instruments
    if string_count != 6:
        if string_count == 12:
            # 12-string: pairs closer, total span similar
            string_spacing = string_spacing * 0.9
            notes.append("12-string: reduced pair spacing")
        elif string_count == 7:
            # 7-string: slightly wider total span
            string_spacing = string_spacing * 1.05
            notes.append("7-string: wider total span")
        elif string_count < 6:
            notes.append(f"{string_count}-string: verify custom spacing")

    # Pin spacing equals string spacing for acoustic bridges
    pin_spacing = string_spacing

    # Validate scale length is reasonable
    if scale_length_mm < 400 or scale_length_mm > 900:
        gate = "YELLOW"
        notes.append(f"Unusual scale length: {scale_length_mm}mm")

    # Validate string spacing range
    if string_spacing < 48 or string_spacing > 62:
        gate = "YELLOW"
        notes.append(f"String spacing {string_spacing}mm outside typical range (48-62mm)")

    # Classical guitars have tie blocks, not pins
    if body_style_lower == "classical":
        pin_spacing = 0.0
        notes.append("Classical: tie block, no bridge pins")

    # Archtop uses tune-o-matic style
    if body_style_lower == "archtop":
        notes.append("Archtop: tune-o-matic style bridge")

    return BridgeSpec(
        body_style=body_style_lower,
        string_spacing_mm=string_spacing,
        bridge_length_mm=spec_data["bridge_length_mm"],
        bridge_width_mm=spec_data["bridge_width_mm"],
        saddle_slot_width_mm=spec_data["saddle_slot_width_mm"],
        saddle_slot_depth_mm=spec_data["saddle_slot_depth_mm"],
        pin_spacing_mm=pin_spacing,
        bridge_plate_length_mm=spec_data["bridge_plate_length_mm"],
        bridge_plate_width_mm=spec_data["bridge_plate_width_mm"],
        material=spec_data["material"],
        gate=gate,
        string_count=string_count,
        notes=notes,
    )


def compute_pin_positions(
    string_spacing_mm: float,
    string_count: int = 6,
    bridge_center_x: float = 0.0,
) -> PinPositions:
    """
    Compute bridge pin positions from centerline.

    Args:
        string_spacing_mm: Total E-to-e string spacing in mm
        string_count: Number of strings (default 6)
        bridge_center_x: X position of bridge center (default 0)

    Returns:
        PinPositions with list of x positions from centerline

    Note:
        For 6 strings, pins are evenly distributed across the spacing.
        Position[0] = low E (bass side), Position[5] = high e (treble side)
    """
    if string_count < 1:
        return PinPositions(
            positions_mm=[],
            string_spacing_mm=string_spacing_mm,
            string_count=0,
            total_span_mm=0.0,
        )

    if string_count == 1:
        return PinPositions(
            positions_mm=[bridge_center_x],
            string_spacing_mm=0.0,
            string_count=1,
            total_span_mm=0.0,
        )

    # Compute inter-string spacing
    inter_string_spacing = string_spacing_mm / (string_count - 1)

    # Calculate positions from centerline
    # Strings are centered around bridge_center_x
    half_span = string_spacing_mm / 2
    positions = []

    for i in range(string_count):
        # Start from bass side (-half_span) to treble side (+half_span)
        x = bridge_center_x - half_span + (i * inter_string_spacing)
        positions.append(round(x, 3))

    return PinPositions(
        positions_mm=positions,
        string_spacing_mm=string_spacing_mm,
        string_count=string_count,
        total_span_mm=string_spacing_mm,
    )


def list_body_styles() -> List[str]:
    """Return list of supported body styles."""
    return list(BRIDGE_SPECS.keys())


def get_bridge_defaults(body_style: str) -> Dict[str, Any]:
    """Get default bridge dimensions for a body style."""
    body_style_lower = body_style.lower().replace("-", "_").replace(" ", "_")
    if body_style_lower not in BRIDGE_SPECS:
        raise ValueError(f"Unknown body style: '{body_style}'")
    return BRIDGE_SPECS[body_style_lower].copy()
