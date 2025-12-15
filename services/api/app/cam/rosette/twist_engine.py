# Patch N12.0 - Twist & herringbone engine skeleton
#
# This module will eventually implement twist offsets and herringbone
# alternation in angle_final_deg. For now, we just mark flags and keep
# angles unchanged.

from __future__ import annotations

from typing import List

from .models import Slice, RosetteRingConfig


def apply_twist(
    ring: RosetteRingConfig,
    slices: List[Slice],
) -> List[Slice]:
    """
    Apply twist offset to slices.

    N12 final behavior:
      - angle_final_deg += ring.twist_angle_deg
      - possibly clamp or normalize angles into [0, 360)

    N12.0 skeleton behavior:
      - keep angles unchanged
      - ensure twist_angle_deg is copied into the slice
    """
    out: List[Slice] = []
    for s in slices:
        s2 = Slice(**vars(s))
        s2.twist_angle_deg = ring.twist_angle_deg
        out.append(s2)
    return out


def apply_herringbone(
    ring: RosetteRingConfig,
    slices: List[Slice],
) -> List[Slice]:
    """
    Apply herringbone alternation to slices.

    N12 final behavior:
      - alternate sign of herringbone_angle_deg on slices
      - adjust angle_final_deg accordingly

    N12.0 skeleton behavior:
      - set herringbone_flip = odd/even index
      - ensure herringbone_angle_deg is copied
    """
    out: List[Slice] = []
    for idx, s in enumerate(slices):
        s2 = Slice(**vars(s))
        s2.herringbone_angle_deg = ring.herringbone_angle_deg
        s2.herringbone_flip = (idx % 2 == 1)
        out.append(s2)
    return out
