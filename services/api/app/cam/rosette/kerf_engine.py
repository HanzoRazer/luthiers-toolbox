# Kerf physics engine — angular compensation for saw blade kerf.
#
# Maturity: SKELETON (attaches kerf_mm metadata, no angle adjustment).
# Full implementation: kerf_angle_deg = (kerf_mm / radius_mm) × (180/π),
# applied cumulatively to angle_final_deg with drift tracking.

from __future__ import annotations

from typing import List

from .models import Slice, RosetteRingConfig


def apply_kerf_physics(
    ring: RosetteRingConfig,
    slices: List[Slice],
) -> List[Slice]:
    """
    Apply kerf correction to slice angles.

    Full implementation:
      - compute kerf_angle_deg = (kerf_mm / radius_mm) × (180 / π)
      - adjust angle_final_deg for each slice
      - track drift accumulation and enforce constraints

    Current behavior:
      - leaves angle_final_deg unchanged
      - ensures Slice.kerf_mm reflects the ring kerf
    """
    out: List[Slice] = []
    for s in slices:
        s2 = Slice(**vars(s))
        s2.kerf_mm = ring.kerf_mm
        out.append(s2)
    return out
