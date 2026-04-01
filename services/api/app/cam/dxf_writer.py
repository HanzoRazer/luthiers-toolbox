"""Central DXF writer — single point of control for all DXF output.

Every DXF generator in the repo must use this module instead of calling
ezdxf.new() directly.  Standards were validated against Fusion 360 on
2026-03-31 (smart_guitar_front/back_v5.dxf).

Standards enforced:
  - Format: AC1015 (R2000) — tested; R2010 caused Fusion 360 freeze
  - Sentinel EXTMIN/EXTMAX preserved (do NOT recompute)
  - Coordinates rounded to 3 decimal places
  - POLYLINE2D, not LWPOLYLINE
  - INSUNITS=4 (mm), MEASUREMENT=1 (metric)
  - Named layers only — no geometry on layer 0
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace


# =============================================================================
# CONSTANTS
# =============================================================================

DXF_VERSION = "R2000"  # AC1015 — Fusion 360 validated
COORDINATE_PRECISION = 3
DEFAULT_LAYER_COLOR = 7  # white


# =============================================================================
# LAYER DEFINITION
# =============================================================================

@dataclass
class LayerDef:
    """Describes a named DXF layer."""
    name: str
    color: int = DEFAULT_LAYER_COLOR


# =============================================================================
# DXF WRITER
# =============================================================================

class DxfWriter:
    """Central DXF writer that enforces project-wide output standards.

    Usage::

        w = DxfWriter(layers=[LayerDef("BODY_OUTLINE", 7)])
        w.add_polyline2d("BODY_OUTLINE", points, closed=True)
        raw = w.to_bytes()
    """

    def __init__(self, layers: Sequence[LayerDef] | None = None) -> None:
        self._doc: Drawing = ezdxf.new(dxfversion=DXF_VERSION)
        self._msp: Modelspace = self._doc.modelspace()
        self._layers: Dict[str, LayerDef] = {}

        # Units — INSUNITS=4 (mm), MEASUREMENT=1 (metric)
        self._doc.header["$INSUNITS"] = 4
        self._doc.header["$MEASUREMENT"] = 1

        if layers:
            for ldef in layers:
                self.add_layer(ldef)

    # -- layer management -----------------------------------------------------

    def add_layer(self, ldef: LayerDef) -> None:
        """Register a named layer. Raises if name is empty or '0'."""
        if not ldef.name or ldef.name == "0":
            raise ValueError("Geometry must not be placed on layer 0")
        if ldef.name not in self._layers:
            self._doc.layers.add(ldef.name, dxfattribs={"color": ldef.color})
            self._layers[ldef.name] = ldef

    # -- geometry helpers (all round to 3 dp) ---------------------------------

    @staticmethod
    def _round_pts(
        points: Sequence[Tuple[float, float]],
    ) -> List[Tuple[float, float, float]]:
        """Round to 3 dp and promote to 3D (z=0)."""
        return [
            (
                round(x, COORDINATE_PRECISION),
                round(y, COORDINATE_PRECISION),
                0.0,
            )
            for x, y in points
        ]

    def _require_layer(self, layer: str) -> None:
        if layer not in self._layers:
            raise ValueError(
                f"Layer '{layer}' not registered — call add_layer() first"
            )

    def add_polyline2d(
        self,
        layer: str,
        points: Sequence[Tuple[float, float]],
        *,
        closed: bool = False,
    ) -> None:
        """Add a 2D polyline (POLYLINE entity, NOT LWPOLYLINE)."""
        self._require_layer(layer)
        pts = self._round_pts(points)
        self._msp.add_polyline2d(
            pts,
            close=closed,
            dxfattribs={"layer": layer},
        )

    def add_line(
        self,
        layer: str,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> None:
        """Add a LINE entity."""
        self._require_layer(layer)
        s = (round(start[0], COORDINATE_PRECISION),
             round(start[1], COORDINATE_PRECISION), 0.0)
        e = (round(end[0], COORDINATE_PRECISION),
             round(end[1], COORDINATE_PRECISION), 0.0)
        self._msp.add_line(s, e, dxfattribs={"layer": layer})

    def add_spline(
        self,
        layer: str,
        points: Sequence[Tuple[float, float]],
    ) -> None:
        """Add a SPLINE entity (fit points)."""
        self._require_layer(layer)
        pts = self._round_pts(points)
        self._msp.add_spline(pts, dxfattribs={"layer": layer})

    def add_circle(
        self,
        layer: str,
        center: Tuple[float, float],
        radius: float,
    ) -> None:
        """Add a CIRCLE entity."""
        self._require_layer(layer)
        c = (round(center[0], COORDINATE_PRECISION),
             round(center[1], COORDINATE_PRECISION))
        self._msp.add_circle(c, round(radius, COORDINATE_PRECISION),
                             dxfattribs={"layer": layer})

    # -- output ---------------------------------------------------------------

    @property
    def doc(self) -> Drawing:
        """Access the underlying ezdxf Drawing (read-only escape hatch)."""
        return self._doc

    def to_bytes(self) -> bytes:
        """Serialize to DXF bytes suitable for StreamingResponse or saveas."""
        stream = io.StringIO()
        self._doc.write(stream)
        return stream.getvalue().encode("utf-8")

    def saveas(self, path: str) -> None:
        """Write DXF to disk."""
        self._doc.saveas(path)
