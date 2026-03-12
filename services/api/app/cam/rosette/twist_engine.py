# Twist & herringbone engine — angle offsets and alternating direction.
#
# Maturity: SKELETON (copies metadata, sets herringbone_flip flag).
# Full implementation will apply twist_angle_deg to angle_final_deg
# and alternate herringbone_angle_deg sign on odd/even slices.

from __future__ import annotations

from typing import List

from .models import Slice, RosetteRingConfig


def apply_twist(
    ring: RosetteRingConfig,
    slices: List[Slice],
) -> List[Slice]:
    """
    Apply twist offset to slices.

    Full implementation:
      - angle_final_deg += ring.twist_angle_deg
      - possibly clamp or normalize angles into [0, 360)

    Current behavior:
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

    Full implementation:
      - alternate sign of herringbone_angle_deg on slices
      - adjust angle_final_deg accordingly

    Current behavior:
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
