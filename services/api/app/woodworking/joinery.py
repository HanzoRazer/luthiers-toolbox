"""
General woodworking joinery helpers: dovetail slope, box joints, mortise & tenon, biscuits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DovetailAngleResult:
    """Dovetail angle from traditional 1:X slope (X units run per 1 unit rise along face)."""

    ratio_run_to_rise: float
    angle_deg: float
    half_angle_from_vertical_deg: float


def compute_dovetail_angle_from_slope(ratio_run_to_rise: float) -> DovetailAngleResult:
    """
    Convert 1:X notation (e.g. 1:6 softwood => ratio_run_to_rise=6) to angles.

    Each sloping face deviates from vertical by atan(1/X). Included angle is twice that.
    """
    if ratio_run_to_rise <= 0:
        return DovetailAngleResult(
            ratio_run_to_rise=ratio_run_to_rise,
            angle_deg=0.0,
            half_angle_from_vertical_deg=0.0,
        )
    half_rad = math.atan(1.0 / ratio_run_to_rise)
    full_rad = 2.0 * half_rad
    return DovetailAngleResult(
        ratio_run_to_rise=ratio_run_to_rise,
        angle_deg=math.degrees(full_rad),
        half_angle_from_vertical_deg=math.degrees(half_rad),
    )


@dataclass(frozen=True)
class BoxJointResult:
    """Finger / box joint layout."""

    stock_width_mm: float
    num_fingers: int
    kerf_mm: float
    finger_width_mm: float
    usable_width_mm: float
    notes: str


def compute_box_joint(
    stock_width_mm: float,
    num_fingers: int,
    kerf_mm: float,
) -> BoxJointResult:
    """
    Equal finger widths for through box joints: (W - (N-1)*kerf) / N.

    Assumes N fingers across the width (same count on mating piece with phase offset).
    """
    if stock_width_mm <= 0 or num_fingers < 1 or kerf_mm < 0:
        return BoxJointResult(
            stock_width_mm=stock_width_mm,
            num_fingers=num_fingers,
            kerf_mm=kerf_mm,
            finger_width_mm=0.0,
            usable_width_mm=0.0,
            notes="Invalid dimensions.",
        )
    cuts = num_fingers - 1
    if cuts < 0:
        cuts = 0
    usable = stock_width_mm - cuts * kerf_mm
    finger_w = usable / float(num_fingers)
    notes = "Equal fingers; verify blade matches kerf and index from first shoulder."
    return BoxJointResult(
        stock_width_mm=stock_width_mm,
        num_fingers=num_fingers,
        kerf_mm=kerf_mm,
        finger_width_mm=finger_w,
        usable_width_mm=usable,
        notes=notes,
    )


@dataclass(frozen=True)
class MortiseTenonResult:
    """Mortise and tenon nominal dimensions."""

    stock_thickness_mm: float
    tenon_thickness_mm: float
    shoulder_mm: float
    mortise_width_mm: float
    notes: str


def compute_mortise_tenon(
    stock_thickness_mm: float,
    shoulder_mm: float = 3.0,
    tenon_fraction: float = 0.33,
) -> MortiseTenonResult:
    """
    Nominal centered tenon: thickness ≈ fraction of stock; mortise matches tenon.

    shoulder_mm is per-face cheek allowance (total width reduction = 2 * cheek gap).
    """
    if stock_thickness_mm <= 0 or shoulder_mm < 0 or not (0.1 <= tenon_fraction <= 0.6):
        return MortiseTenonResult(
            stock_thickness_mm=stock_thickness_mm,
            tenon_thickness_mm=0.0,
            shoulder_mm=shoulder_mm,
            mortise_width_mm=0.0,
            notes="Invalid stock thickness or tenon_fraction (use ~0.33).",
        )
    tenon_t = stock_thickness_mm * tenon_fraction
    mortise_w = tenon_t
    notes = "Centered tenon; adjust for drawbore, offset shoulders, or haunches as needed."
    return MortiseTenonResult(
        stock_thickness_mm=stock_thickness_mm,
        tenon_thickness_mm=tenon_t,
        shoulder_mm=shoulder_mm,
        mortise_width_mm=mortise_w,
        notes=notes,
    )


@dataclass(frozen=True)
class BiscuitLayoutResult:
    """Biscuit slot spacing along a glue joint."""

    joint_length_mm: float
    biscuit_pitch_mm: float
    count: int
    positions_mm_from_end: List[float]
    notes: str


# Nominal biscuit cutter diameters (mm) — #0 / #10 / #20 common
BISCUIT_SIZE_PITCH_MM = {
    "0": 150.0,
    "10": 180.0,
    "20": 200.0,
}


def compute_biscuit_layout(
    joint_length_mm: float,
    biscuit_size: str = "20",
    end_margin_mm: float = 50.0,
) -> BiscuitLayoutResult:
    """
    Evenly space biscuits between end margins; count from pitch.

    Pitch defaults by biscuit size; override by passing a custom joint_length-only
    heuristic is not used — use `biscuit_pitch_mm` via size map.
    """
    pitch = BISCUIT_SIZE_PITCH_MM.get(biscuit_size.strip(), BISCUIT_SIZE_PITCH_MM["20"])
    if joint_length_mm <= 2 * end_margin_mm:
        return BiscuitLayoutResult(
            joint_length_mm=joint_length_mm,
            biscuit_pitch_mm=pitch,
            count=0,
            positions_mm_from_end=[],
            notes="Joint too short for margins; reduce end_margin_mm.",
        )
    usable = joint_length_mm - 2 * end_margin_mm
    count = max(1, int(usable / pitch) + 1)
    if count == 1:
        positions = [joint_length_mm / 2.0]
    else:
        step = usable / (count - 1)
        positions = [end_margin_mm + i * step for i in range(count)]
    return BiscuitLayoutResult(
        joint_length_mm=joint_length_mm,
        biscuit_pitch_mm=pitch,
        count=count,
        positions_mm_from_end=positions,
        notes=f"Biscuit size {biscuit_size}; positions from one end (mm).",
    )
