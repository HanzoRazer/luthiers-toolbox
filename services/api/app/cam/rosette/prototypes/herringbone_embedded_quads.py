"""
Embedded herringbone DXF tile quads accessor.

This module provides the accessor function for embedded herringbone quad data.
The raw coordinate data is stored in herringbone_quads_data.py.

596 dark + 602 light tiles, each quad as 4 corner points in mm.
"""

from .herringbone_quads_data import DARK_QUADS_RAW, LIGHT_QUADS_RAW


def get_embedded_quads() -> list[tuple[int, list[tuple[float, float]]]]:
    """
    Return embedded quads as (parity, [(x,y) x 4]) pairs.

    parity 0 = dark, 1 = light.
    Each quad is 4 corner points in mm coordinates.
    """
    quads: list[tuple[int, list[tuple[float, float]]]] = []
    for raw in DARK_QUADS_RAW:
        pts = [(raw[i], raw[i + 1]) for i in range(0, 8, 2)]
        quads.append((0, pts))
    for raw in LIGHT_QUADS_RAW:
        pts = [(raw[i], raw[i + 1]) for i in range(0, 8, 2)]
        quads.append((1, pts))
    return quads
