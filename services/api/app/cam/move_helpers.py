"""
Shared move helper functions for CAM modules.

Consolidates duplicate utility functions from energy_model.py and heat_timeseries.py.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List


def length_annotate(moves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Annotate moves with _len_mm field (XY distance from previous point).

    Args:
        moves: List of move dicts with x, y coordinates

    Returns:
        Annotated moves with _len_mm field added
    """
    out = []
    last = None

    for m in moves:
        mm = dict(m)
        if "x" in mm and "y" in mm:
            p = (mm["x"], mm["y"])
            if last is None:
                mm["_len_mm"] = 0.0
            else:
                mm["_len_mm"] = math.hypot(p[0] - last[0], p[1] - last[1])
            last = p
        out.append(mm)

    return out
