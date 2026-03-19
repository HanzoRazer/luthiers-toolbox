"""
Neck Block and Tail Block Calculator (GEOMETRY-005)
====================================================

Calculates neck and tail block dimensions based on:
- Side depth at block location
- Body style
- Neck heel width (for neck block)

Standard dimensions:
    Neck block height = side depth at neck
    Neck block width = neck heel width + 6mm each side (12mm total)
    Neck block depth (front to back) = 50-65mm typical

    Tail block height = side depth at tail
    Tail block width = 65-90mm typical
    Tail block depth = 30-40mm typical
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Literal


# ─── Standard Side Depths by Body Style ───────────────────────────────────────

STANDARD_SIDE_DEPTHS_MM: Dict[str, Dict[str, float]] = {
    "dreadnought": {"neck": 100.0, "tail": 105.0},
    "om_000": {"neck": 95.0, "tail": 100.0},
    "parlor": {"neck": 85.0, "tail": 90.0},
    "classical": {"neck": 95.0, "tail": 100.0},
    "archtop": {"neck": 75.0, "tail": 75.0},
    "jumbo": {"neck": 105.0, "tail": 110.0},
    "concert": {"neck": 90.0, "tail": 95.0},
}

# Default neck heel widths by body style (mm)
DEFAULT_NECK_HEEL_WIDTHS_MM: Dict[str, float] = {
    "dreadnought": 56.0,
    "om_000": 54.0,
    "parlor": 52.0,
    "classical": 60.0,  # Classical guitars have wider heels
    "archtop": 58.0,
    "jumbo": 58.0,
    "concert": 54.0,
}

# Standard block depths by body style
NECK_BLOCK_DEPTHS_MM: Dict[str, float] = {
    "dreadnought": 60.0,
    "om_000": 55.0,
    "parlor": 50.0,
    "classical": 55.0,
    "archtop": 65.0,  # Archtops need deeper blocks for carved top support
    "jumbo": 62.0,
    "concert": 55.0,
}

TAIL_BLOCK_DEPTHS_MM: Dict[str, float] = {
    "dreadnought": 35.0,
    "om_000": 32.0,
    "parlor": 30.0,
    "classical": 32.0,
    "archtop": 40.0,
    "jumbo": 38.0,
    "concert": 32.0,
}

TAIL_BLOCK_WIDTHS_MM: Dict[str, float] = {
    "dreadnought": 85.0,
    "om_000": 75.0,
    "parlor": 65.0,
    "classical": 80.0,
    "archtop": 90.0,
    "jumbo": 88.0,
    "concert": 72.0,
}


# ─── Output Dataclass ─────────────────────────────────────────────────────────

@dataclass
class BlockSpec:
    """Specification for a neck or tail block."""
    block_type: str              # "neck" or "tail"
    height_mm: float             # = side depth at location
    width_mm: float
    depth_mm: float              # front to back dimension
    material: str                # recommended material
    grain_orientation: str       # "vertical" or "horizontal"
    gate: str                    # GREEN, YELLOW, RED
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Gate Logic ───────────────────────────────────────────────────────────────

def _compute_neck_block_gate(
    height_mm: float,
    width_mm: float,
    depth_mm: float,
    neck_heel_width_mm: float,
) -> tuple[str, List[str]]:
    """
    Determine gate for neck block dimensions.

    GREEN: All dimensions within typical ranges
    YELLOW: Borderline dimensions
    RED: Structural concern
    """
    notes: List[str] = []
    gate = "GREEN"

    # Check height (should be >= side depth, never less)
    if height_mm < 70:
        gate = "RED"
        notes.append("Block height below 70mm - insufficient for most guitars")
    elif height_mm < 80:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block height borderline - verify side depth")

    # Check width (should provide adequate glue surface)
    min_width = neck_heel_width_mm + 8  # At least 4mm each side
    if width_mm < min_width:
        gate = "RED"
        notes.append(f"Block width {width_mm:.1f}mm too narrow for heel width {neck_heel_width_mm:.1f}mm")
    elif width_mm < neck_heel_width_mm + 10:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block width provides minimal side margin")

    # Check depth (front to back)
    if depth_mm < 45:
        gate = "RED"
        notes.append("Block depth below 45mm - insufficient glue area for neck joint")
    elif depth_mm < 50:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block depth borderline - consider increasing for stronger joint")
    elif depth_mm > 70:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block depth exceeds 70mm - adds unnecessary weight")

    if gate == "GREEN":
        notes.append("Dimensions within recommended range")

    return gate, notes


def _compute_tail_block_gate(
    height_mm: float,
    width_mm: float,
    depth_mm: float,
) -> tuple[str, List[str]]:
    """
    Determine gate for tail block dimensions.

    GREEN: All dimensions within typical ranges
    YELLOW: Borderline dimensions
    RED: Structural concern
    """
    notes: List[str] = []
    gate = "GREEN"

    # Check height
    if height_mm < 70:
        gate = "RED"
        notes.append("Block height below 70mm - may not span full side depth")
    elif height_mm < 80:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block height borderline")

    # Check width
    if width_mm < 60:
        gate = "RED"
        notes.append("Block width below 60mm - insufficient for end pin reinforcement")
    elif width_mm < 65:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block width at minimum - adequate for light use")

    # Check depth
    if depth_mm < 25:
        gate = "RED"
        notes.append("Block depth below 25mm - end pin may not have adequate support")
    elif depth_mm < 30:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block depth borderline - consider 30mm minimum")
    elif depth_mm > 45:
        gate = "YELLOW" if gate == "GREEN" else gate
        notes.append("Block depth exceeds 45mm - adds unnecessary weight")

    if gate == "GREEN":
        notes.append("Dimensions within recommended range")

    return gate, notes


# ─── Core Functions ───────────────────────────────────────────────────────────

def compute_neck_block(
    side_depth_at_neck_mm: float,
    neck_heel_width_mm: float,
    body_style: str = "dreadnought",
    material: str = "mahogany",
) -> BlockSpec:
    """
    Compute neck block dimensions.

    Args:
        side_depth_at_neck_mm: Side depth at neck end in mm
        neck_heel_width_mm: Width of neck heel in mm
        body_style: Body style (dreadnought, om_000, parlor, classical, archtop)
        material: Block material (mahogany, maple, spanish_cedar)

    Returns:
        BlockSpec with calculated dimensions
    """
    # Normalize body style
    body_style_lower = body_style.lower().strip().replace("-", "_").replace(" ", "_")

    # Height = side depth at neck
    height_mm = side_depth_at_neck_mm

    # Width = neck heel width + 6mm each side
    width_mm = neck_heel_width_mm + 12.0

    # Depth from lookup or default
    depth_mm = NECK_BLOCK_DEPTHS_MM.get(body_style_lower, 60.0)

    # Compute gate
    gate, notes = _compute_neck_block_gate(
        height_mm, width_mm, depth_mm, neck_heel_width_mm
    )

    return BlockSpec(
        block_type="neck",
        height_mm=round(height_mm, 1),
        width_mm=round(width_mm, 1),
        depth_mm=round(depth_mm, 1),
        material=material,
        grain_orientation="vertical",  # Vertical grain for strength
        gate=gate,
        notes=notes,
    )


def compute_tail_block(
    side_depth_at_tail_mm: float,
    body_style: str = "dreadnought",
    material: str = "mahogany",
) -> BlockSpec:
    """
    Compute tail block dimensions.

    Args:
        side_depth_at_tail_mm: Side depth at tail end in mm
        body_style: Body style (dreadnought, om_000, parlor, classical, archtop)
        material: Block material (mahogany, maple, spanish_cedar)

    Returns:
        BlockSpec with calculated dimensions
    """
    # Normalize body style
    body_style_lower = body_style.lower().strip().replace("-", "_").replace(" ", "_")

    # Height = side depth at tail
    height_mm = side_depth_at_tail_mm

    # Width from lookup or default
    width_mm = TAIL_BLOCK_WIDTHS_MM.get(body_style_lower, 80.0)

    # Depth from lookup or default
    depth_mm = TAIL_BLOCK_DEPTHS_MM.get(body_style_lower, 35.0)

    # Compute gate
    gate, notes = _compute_tail_block_gate(height_mm, width_mm, depth_mm)

    return BlockSpec(
        block_type="tail",
        height_mm=round(height_mm, 1),
        width_mm=round(width_mm, 1),
        depth_mm=round(depth_mm, 1),
        material=material,
        grain_orientation="horizontal",  # Horizontal for end pin support
        gate=gate,
        notes=notes,
    )


def compute_both_blocks(
    body_style: str = "dreadnought",
    neck_heel_width_mm: float | None = None,
    side_depth_at_neck_mm: float | None = None,
    side_depth_at_tail_mm: float | None = None,
    material: str = "mahogany",
) -> Dict[str, BlockSpec]:
    """
    Compute both neck and tail block dimensions.

    Args:
        body_style: Body style (uses defaults if depths not provided)
        neck_heel_width_mm: Width of neck heel (uses default for body style if None)
        side_depth_at_neck_mm: Side depth at neck (uses default for body style if None)
        side_depth_at_tail_mm: Side depth at tail (uses default for body style if None)
        material: Block material

    Returns:
        Dict with "neck" and "tail" BlockSpec
    """
    body_style_lower = body_style.lower().strip().replace("-", "_").replace(" ", "_")

    # Get defaults if not provided
    if side_depth_at_neck_mm is None:
        depths = STANDARD_SIDE_DEPTHS_MM.get(body_style_lower, {"neck": 100.0, "tail": 105.0})
        side_depth_at_neck_mm = depths["neck"]

    if side_depth_at_tail_mm is None:
        depths = STANDARD_SIDE_DEPTHS_MM.get(body_style_lower, {"neck": 100.0, "tail": 105.0})
        side_depth_at_tail_mm = depths["tail"]

    if neck_heel_width_mm is None:
        neck_heel_width_mm = DEFAULT_NECK_HEEL_WIDTHS_MM.get(body_style_lower, 56.0)

    neck_block = compute_neck_block(
        side_depth_at_neck_mm=side_depth_at_neck_mm,
        neck_heel_width_mm=neck_heel_width_mm,
        body_style=body_style,
        material=material,
    )

    tail_block = compute_tail_block(
        side_depth_at_tail_mm=side_depth_at_tail_mm,
        body_style=body_style,
        material=material,
    )

    return {"neck": neck_block, "tail": tail_block}


def list_body_styles() -> List[str]:
    """Return list of supported body styles."""
    return list(STANDARD_SIDE_DEPTHS_MM.keys())


def get_default_side_depths(body_style: str) -> Dict[str, float]:
    """Get default side depths for a body style."""
    body_style_lower = body_style.lower().strip().replace("-", "_").replace(" ", "_")
    return STANDARD_SIDE_DEPTHS_MM.get(body_style_lower, {"neck": 100.0, "tail": 105.0})
