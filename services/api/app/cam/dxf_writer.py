"""Central DXF writer - single point of control for all DXF output.

Every DXF generator in the repo must use this module instead of calling
ezdxf.new() directly. Standards were validated against Fusion 360 and
trace back to the 525 dollar Les Paul file set that would not open.

Standards enforced (CLAUDE.md):
  - Format: R12 (AC1009) - maximum CAM compatibility
  - LINE entities ONLY - no LWPOLYLINE, no POLYLINE2D
  - Sentinel EXTMIN/EXTMAX (1e+20) - do NOT recompute
  - Coordinates rounded to 3 decimal places
  - Named layers only - no geometry on layer 0

Why R12?
  - LWPOLYLINE does not exist in R12 -> guarantees LINE-only output
  - Maximum compatibility: opens in Fusion 360, VCarve, AutoCAD, FreeCAD
  - The genesis of The Production Shop - R12 is the answer to broken DXF files
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace


DXF_VERSION = "R12"
COORDINATE_PRECISION = 3
DEFAULT_LAYER_COLOR = 7


@dataclass
class LayerDef:
    """Describes a named DXF layer."""
    name: str
    color: int = DEFAULT_LAYER_COLOR


class DxfWriter:
    """Central DXF writer that enforces project-wide R12 output standards."""

    def __init__(self, layers: Sequence[LayerDef] | None = None) -> None:
        self._doc: Drawing = ezdxf.new(dxfversion=DXF_VERSION)
        self._msp: Modelspace = self._doc.modelspace()
        self._layers: Dict[str, LayerDef] = {}

        try:
            self._doc.header["$INSUNITS"] = 4
            self._doc.header["$MEASUREMENT"] = 1
        except (KeyError, ezdxf.DXFValueError):
            pass

        # Note: Do NOT set EXTMIN/EXTMAX — let ezdxf compute from actual geometry.
        # Previous sentinel values (1e+20/-1e+20) broke CAD viewer zoom-to-fit.

        if layers:
            for ldef in layers:
                self.add_layer(ldef)

    def add_layer(self, ldef: LayerDef) -> None:
        if not ldef.name or ldef.name == "0":
            raise ValueError("Geometry must not be placed on layer 0")
        if ldef.name not in self._layers:
            self._doc.layers.add(ldef.name, dxfattribs={"color": ldef.color})
            self._layers[ldef.name] = ldef

    @staticmethod
    def _round_pt(x: float, y: float) -> Tuple[float, float]:
        return (round(x, COORDINATE_PRECISION), round(y, COORDINATE_PRECISION))

    def _require_layer(self, layer: str) -> None:
        if layer not in self._layers:
            raise ValueError(f"Layer not registered: {layer}")

    def add_polyline(self, layer: str, points: Sequence[Tuple[float, float]], *, closed: bool = False) -> None:
        """Add a polyline as LINE entities (R12 standard)."""
        self._require_layer(layer)
        if len(points) < 2:
            return
        n = len(points)
        end = n if closed else n - 1
        for i in range(end):
            self.add_line(layer, points[i], points[(i + 1) % n])

    def add_line(self, layer: str, start: Tuple[float, float], end: Tuple[float, float]) -> None:
        self._require_layer(layer)
        s = self._round_pt(start[0], start[1])
        e = self._round_pt(end[0], end[1])
        self._msp.add_line(s, e, dxfattribs={"layer": layer})

    def add_circle(self, layer: str, center: Tuple[float, float], radius: float) -> None:
        self._require_layer(layer)
        c = self._round_pt(center[0], center[1])
        self._msp.add_circle(c, round(radius, COORDINATE_PRECISION), dxfattribs={"layer": layer})

    def add_arc(self, layer: str, center: Tuple[float, float], radius: float, start_angle: float, end_angle: float) -> None:
        self._require_layer(layer)
        c = self._round_pt(center[0], center[1])
        self._msp.add_arc(c, round(radius, COORDINATE_PRECISION),
                         start_angle=round(start_angle, COORDINATE_PRECISION),
                         end_angle=round(end_angle, COORDINATE_PRECISION),
                         dxfattribs={"layer": layer})

    def add_point(self, layer: str, location: Tuple[float, float]) -> None:
        self._require_layer(layer)
        self._msp.add_point(self._round_pt(location[0], location[1]), dxfattribs={"layer": layer})

    def add_text(self, layer: str, text: str, insert: Tuple[float, float], height: float = 2.5) -> None:
        """Add a TEXT entity for annotations. R12 supports TEXT."""
        self._require_layer(layer)
        pos = self._round_pt(insert[0], insert[1])
        self._msp.add_text(text, dxfattribs={"layer": layer, "height": round(height, COORDINATE_PRECISION), "insert": pos})

    def add_polyline3d(self, layer: str, points: Sequence[Tuple[float, float, float]], *, closed: bool = False) -> None:
        """Add a 3D polyline. R12 supports POLYLINE with 3D vertices."""
        self._require_layer(layer)
        if len(points) < 2:
            return
        rounded = [(round(x, COORDINATE_PRECISION), round(y, COORDINATE_PRECISION), round(z, COORDINATE_PRECISION)) for x, y, z in points]
        self._msp.add_polyline3d(rounded, close=closed, dxfattribs={"layer": layer})

    @property
    def doc(self) -> Drawing:
        return self._doc

    @property
    def modelspace(self) -> Modelspace:
        return self._msp

    def to_bytes(self) -> bytes:
        stream = io.StringIO()
        self._doc.write(stream)
        return stream.getvalue().encode("utf-8")

    def saveas(self, path: str) -> None:
        self._doc.saveas(path)


def create_dxf_writer(layer_names: Sequence[str] | None = None, layer_color: int = DEFAULT_LAYER_COLOR) -> DxfWriter:
    layers = [LayerDef(name, layer_color) for name in layer_names] if layer_names else None
    return DxfWriter(layers=layers)