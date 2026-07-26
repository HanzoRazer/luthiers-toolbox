"""Canonical CAM geometry contract types.

This module owns the shared geometry primitives exchanged across CAM
boundaries. It is deliberately narrow: it holds the contract types that more
than one CAM subsystem must agree on, and nothing else. Subsystem-specific
request/response models belong in their own schema modules.

Provenance: consolidated from three functionally identical ``Loop``
definitions (adaptive schemas, blueprint→CAM bridge schemas, contour
reconstructor) under CONV-001 / LAB-013 WP-GEOM-3. The definition is
behavior-preserving; the historical modules re-export or import from here so
all access paths resolve to a single class identity.
"""

from typing import List, Tuple

from pydantic import BaseModel

__all__ = ["Loop"]


class Loop(BaseModel):
    """
    Closed polygon representing a boundary or island.

    Shared CAM geometry contract. Where a caller supplies an ordered list of
    loops, the first loop is the outer boundary (CCW orientation) and any
    subsequent loops are islands/holes (CW orientation). That ordering
    convention is imposed by the consuming operation, not by this type.

    Attributes:
        pts: List of (x, y) tuples forming a closed polygon.
             First and last point are automatically connected if different.

    Example:
        >>> outer = Loop(pts=[(0, 0), (100, 0), (100, 60), (0, 60)])
        >>> island = Loop(pts=[(30, 15), (70, 15), (70, 45), (30, 45)])
    """

    pts: List[Tuple[float, float]]
