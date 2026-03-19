"""
GEOMETRY-008: Tuning Machine Post Height and String Tree Selection

Extends headstock_break_angle.py with selection logic for:
- Tuning machine post height from target break angle
- String tree recommendation for G and B strings
- Wrap count calculation

Post height formula (angled headstock):
  break_angle = arctan(
    (nut_to_tuner_mm × sin(headstock_angle) - post_height_mm)
    / (nut_to_tuner_mm × cos(headstock_angle))
  )

Minimum recommended break angle: 7-10° for tone and tuning stability.
Too steep (>20°): string breaks at nut, excessive friction.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Optional

Gate = Literal["GREEN", "YELLOW", "RED"]
StringTreeType = Literal["butterfly", "roller", "disc", "none"]

# String tree specifications
STRING_TREE_SPECS = {
    "butterfly": {
        "depression_mm": 3.0,
        "style": "vintage",
        "friction": "medium",
    },
    "roller": {
        "depression_mm": 3.0,
        "style": "modern",
        "friction": "low",
    },
    "disc": {
        "depression_mm": 2.0,
        "style": "modern",
        "friction": "medium",
    },
    "none": {
        "depression_mm": 0.0,
        "style": "n/a",
        "friction": "n/a",
    },
}

# Strings that typically need string trees on flat headstocks
STRINGS_NEEDING_TREES = {"G", "B", "g", "b", "3", "2"}

# Break angle thresholds
MIN_BREAK_ANGLE_DEG = 7.0
OPTIMAL_BREAK_ANGLE_DEG = 9.0
MAX_BREAK_ANGLE_DEG = 20.0

# Standard tuner post heights (mm)
STANDARD_POST_HEIGHTS = {
    "vintage_kluson": 8.5,
    "modern_locking": 10.0,
    "grover_rotomatic": 9.5,
    "schaller": 10.5,
    "gotoh": 9.0,
    "hipshot": 10.0,
}


@dataclass
class TuningMachineSpec:
    """Complete tuning machine specification."""

    post_height_mm: float
    break_angle_deg: float
    string_tree_needed: bool
    string_tree_type: StringTreeType
    wrap_count: float
    gate: Gate
    notes: list[str]


def compute_break_angle(
    headstock_angle_deg: float,
    nut_to_post_mm: float,
    post_height_mm: float,
) -> float:
    """
    Compute break angle at the nut for a given tuner configuration.

    For angled headstocks (Gibson/PRS style):
    break_angle = arctan(
        (nut_to_tuner × sin(headstock_angle) - post_height)
        / (nut_to_tuner × cos(headstock_angle))
    )

    Args:
        headstock_angle_deg: Headstock pitch angle in degrees (0 for flat)
        nut_to_post_mm: Distance from nut to tuner post in mm
        post_height_mm: Height of tuner post above headstock face in mm

    Returns:
        Break angle in degrees
    """
    if nut_to_post_mm <= 0:
        return 0.0

    headstock_rad = math.radians(headstock_angle_deg)

    # Vertical drop from nut to post
    vertical_drop = nut_to_post_mm * math.sin(headstock_rad) - post_height_mm

    # Horizontal distance
    horizontal_dist = nut_to_post_mm * math.cos(headstock_rad)

    if horizontal_dist <= 0:
        return 0.0

    break_angle_rad = math.atan(vertical_drop / horizontal_dist)
    return math.degrees(break_angle_rad)


def compute_required_post_height(
    headstock_angle_deg: float,
    nut_to_post_mm: float,
    target_break_angle_deg: float = 9.0,
) -> float:
    """
    Compute required post height to achieve target break angle.

    Solves the break angle formula for post_height_mm:
    post_height = nut_to_tuner × sin(headstock_angle)
                  - nut_to_tuner × cos(headstock_angle) × tan(target_break)

    Args:
        headstock_angle_deg: Headstock pitch angle in degrees
        nut_to_post_mm: Distance from nut to tuner post in mm
        target_break_angle_deg: Desired break angle in degrees

    Returns:
        Required post height in mm
    """
    if nut_to_post_mm <= 0:
        return 0.0

    headstock_rad = math.radians(headstock_angle_deg)
    target_rad = math.radians(target_break_angle_deg)

    post_height = (
        nut_to_post_mm * math.sin(headstock_rad)
        - nut_to_post_mm * math.cos(headstock_rad) * math.tan(target_rad)
    )

    return max(0.0, round(post_height, 2))


def check_string_tree_needed(
    string_name: str,
    break_angle_deg: float,
    min_break_angle_deg: float = 7.0,
) -> StringTreeType:
    """
    Check if a string tree is needed and recommend type.

    String tree needed if:
    - break_angle < min_break_angle AND
    - string is G or B (most common case on flat headstocks)

    Args:
        string_name: String identifier (e.g., "G", "B", "1", "2", "3")
        break_angle_deg: Current break angle in degrees
        min_break_angle_deg: Minimum acceptable break angle

    Returns:
        String tree type: "butterfly", "roller", "disc", or "none"
    """
    # Normalize string name
    name = string_name.strip().upper()

    # Check if this string typically needs a tree
    needs_check = name in {"G", "B", "2", "3"}

    if not needs_check:
        return "none"

    if break_angle_deg >= min_break_angle_deg:
        return "none"

    # Recommend tree type based on break angle deficit
    deficit = min_break_angle_deg - break_angle_deg

    if deficit > 5.0:
        # Large deficit - need more depression
        return "butterfly"
    elif deficit > 3.0:
        # Medium deficit - roller for low friction
        return "roller"
    else:
        # Small deficit - disc is sufficient
        return "disc"


def compute_wrap_count(
    post_height_mm: float,
    string_gauge_inch: float,
) -> float:
    """
    Compute number of string wraps around tuner post.

    Strings should wrap 2-3 times for tuning stability.
    More wraps = more slippage risk; fewer = string can pop off.

    Formula: wraps = post_height / (string_diameter_mm + 0.5mm clearance)

    Args:
        post_height_mm: Height of tuner post in mm
        string_gauge_inch: String diameter in inches

    Returns:
        Number of wraps (typically 2-4)
    """
    if post_height_mm <= 0 or string_gauge_inch <= 0:
        return 0.0

    string_diameter_mm = string_gauge_inch * 25.4
    clearance_mm = 0.5

    wraps = post_height_mm / (string_diameter_mm + clearance_mm)
    return round(wraps, 1)


def compute_tuning_machine_spec(
    headstock_angle_deg: float,
    nut_to_post_mm: float,
    post_height_mm: float,
    string_name: str,
    string_gauge_inch: float = 0.010,
) -> TuningMachineSpec:
    """
    Compute complete tuning machine specification for a string.

    Args:
        headstock_angle_deg: Headstock pitch angle in degrees
        nut_to_post_mm: Distance from nut to tuner post in mm
        post_height_mm: Height of tuner post in mm
        string_name: String identifier (e.g., "G", "B", "e")
        string_gauge_inch: String diameter in inches

    Returns:
        TuningMachineSpec with all computed values and gate
    """
    notes: list[str] = []
    gate: Gate = "GREEN"

    # Compute break angle
    break_angle = compute_break_angle(
        headstock_angle_deg=headstock_angle_deg,
        nut_to_post_mm=nut_to_post_mm,
        post_height_mm=post_height_mm,
    )

    # Check break angle thresholds
    if break_angle < MIN_BREAK_ANGLE_DEG:
        if headstock_angle_deg < 5.0:
            # Flat headstock - may need string tree
            gate = "YELLOW"
            notes.append(
                f"Break angle {break_angle:.1f}° below minimum {MIN_BREAK_ANGLE_DEG}°"
            )
        else:
            gate = "RED"
            notes.append(
                f"Break angle {break_angle:.1f}° too shallow - tuning instability"
            )
    elif break_angle > MAX_BREAK_ANGLE_DEG:
        gate = "RED"
        notes.append(
            f"Break angle {break_angle:.1f}° too steep - string breakage risk"
        )
    elif break_angle < OPTIMAL_BREAK_ANGLE_DEG:
        notes.append(f"Break angle {break_angle:.1f}° acceptable but not optimal")

    # Check string tree
    tree_type = check_string_tree_needed(
        string_name=string_name,
        break_angle_deg=break_angle,
    )
    string_tree_needed = tree_type != "none"

    if string_tree_needed:
        notes.append(f"String tree recommended: {tree_type}")
        if gate == "RED":
            gate = "YELLOW"  # Tree can fix the issue

    # Compute wrap count
    wrap_count = compute_wrap_count(
        post_height_mm=post_height_mm,
        string_gauge_inch=string_gauge_inch,
    )

    if wrap_count < 2.0:
        notes.append(f"Wrap count {wrap_count} too low - string may slip")
        gate = "YELLOW" if gate == "GREEN" else gate
    elif wrap_count > 4.0:
        notes.append(f"Wrap count {wrap_count} high - trim excess string")

    if gate == "GREEN" and not notes:
        notes.append("Configuration within optimal range")

    return TuningMachineSpec(
        post_height_mm=post_height_mm,
        break_angle_deg=round(break_angle, 2),
        string_tree_needed=string_tree_needed,
        string_tree_type=tree_type,
        wrap_count=wrap_count,
        gate=gate,
        notes=notes,
    )


def list_standard_post_heights() -> dict[str, float]:
    """Return standard tuner post heights by brand."""
    return STANDARD_POST_HEIGHTS.copy()


def get_string_tree_spec(tree_type: str) -> dict:
    """Get specifications for a string tree type."""
    return STRING_TREE_SPECS.get(tree_type, STRING_TREE_SPECS["none"]).copy()
