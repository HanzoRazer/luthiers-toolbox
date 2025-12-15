# Patch N11.2 - Kerf compensation scaffolding

from typing import Any, Dict, List


def apply_kerf_compensation_stub(
    slices: List[Dict[str, Any]],
    kerf_mm: float,
) -> List[Dict[str, Any]]:
    """
    Scaffolding only.

    Returns the input slices unchanged, but attaches a 'kerf_mm' field.
    N12 will perform real angular compensation.
    """
    compensated: List[Dict[str, Any]] = []
    for s in slices:
        s2 = dict(s)
        s2["kerf_mm"] = kerf_mm
        compensated.append(s2)
    return compensated
