# Patch N11.2 - Herringbone scaffolding

from typing import Any, Dict, List


def apply_herringbone_stub(
    slices: List[Dict[str, Any]],
    herringbone_angle_deg: float,
) -> List[Dict[str, Any]]:
    """
    Scaffolding only.

    Alternates a boolean 'herringbone_flip' flag on each slice to simulate
    alternating direction. N12 will apply real angle changes.
    """
    result: List[Dict[str, Any]] = []
    for idx, s in enumerate(slices):
        s2 = dict(s)
        s2["herringbone_flip"] = (idx % 2 == 1)
        s2["herringbone_angle_deg"] = herringbone_angle_deg
        result.append(s2)
    return result
