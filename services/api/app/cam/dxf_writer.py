# GOVERNANCE:
# SYSTEM: DXF_COMPAT_LAYER
# STATUS: PROTECTED_PRODUCTION_BASELINE
# DOC: docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md
# RULE: Do not alter production behavior without GOVERNANCE_APPROVED_CHANGE.

"""Central DXF writer - single point of control for all DXF output.

Every DXF generator in the repo must use this module instead of calling
ezdxf.new() directly. Standards were validated against DWG TrueView 2026
and trace back to the 525 dollar Les Paul file set that would not open.

Dual-format support (CLAUDE.md):
  - Free tier: R12 (AC1009) - LINE entities for maximum CAM compatibility
  - Paid tier: R2000 (AC1015) - LWPOLYLINE entities for CAM workflows

Common standards (both formats):
  - Coordinates rounded to 3 decimal places
  - Named layers only - no geometry on layer 0
  - All entity creation routes through dxf_compat for version-aware output

R2000 callers must verify their use case against the dxf_compat output format
(LWPOLYLINE vs LINE). R2000 was verified safe for DWG TrueView 2026 on 2026-04-28.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

import ezdxf
from ezdxf import bbox
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace

from app.util.dxf_compat import create_document, add_polyline as compat_add_polyline


DXF_VERSION_DEFAULT = "R12"
COORDINATE_PRECISION = 3
DEFAULT_LAYER_COLOR = 7


@dataclass
class LayerDef:
    """Describes a named DXF layer."""
    name: str
    color: int = DEFAULT_LAYER_COLOR


class DxfWriter:
    """Central DXF writer with dual-format support (R12 free tier, R2000 paid tier)."""

    def __init__(self, layers: Sequence[LayerDef] | None = None, version: str = DXF_VERSION_DEFAULT) -> None:
        self._version = version
        self._doc: Drawing = create_document(version=version)
        self._msp: Modelspace = self._doc.modelspace()
        self._layers: Dict[str, LayerDef] = {}

        try:
            self._doc.header["$INSUNITS"] = 4
            self._doc.header["$MEASUREMENT"] = 1
        except (KeyError, ezdxf.DXFValueError):
            pass

        # EXTMIN/EXTMAX are derived from geometry at serialization time
        # (see _finalize_extents). They are never left at ezdxf's uninitialized
        # ±1e20 sentinel defaults, which break CAD viewer zoom-to-fit. A plain
        # doc.write() does NOT recompute extents, so this must be done explicitly.

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
        """Add a polyline using version-appropriate entity (LINE for R12, LWPOLYLINE for R2000+)."""
        self._require_layer(layer)
        if len(points) < 2:
            return
        rounded_points = [self._round_pt(p[0], p[1]) for p in points]
        compat_add_polyline(self._msp, rounded_points, layer=layer, closed=closed, version=self._version)

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

    def add_text(self, layer: str, text: str, insert: Tuple[float, float], height: float = 2.5, rotation: float = 0.0) -> None:
        """Add a TEXT entity for annotations. R12 supports TEXT with rotation.

        Args:
            layer: Target layer name
            text: Text content
            insert: (x, y) insertion point in mm
            height: Text height in mm (default 2.5)
            rotation: Counter-clockwise rotation in degrees (default 0.0)
        """
        self._require_layer(layer)
        pos = self._round_pt(insert[0], insert[1])
        self._msp.add_text(text, dxfattribs={
            "layer": layer,
            "height": round(height, COORDINATE_PRECISION),
            "insert": pos,
            "rotation": round(rotation, COORDINATE_PRECISION)
        })

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

    def _finalize_extents(self) -> None:
        """Derive finite extents from geometry before serialization.

        A fresh ezdxf document leaves the extents at the uninitialized ±1e20
        sentinels, and ezdxf's export (Drawing.update_extents) actively rewrites
        the header $EXTMIN/$EXTMAX from the *block record* extents (msp.dxf.extmin
        and the active paperspace layout's extmin) — so merely setting the header
        is clobbered on write. We therefore set the source-of-truth block extents
        (which the exporter reads), and the header directly for the case where
        update_extents skips a falsy origin extent. Paperspace carries no geometry
        and would otherwise export its ±1e20 sentinel, so it is pinned finite too.
        Without this the writer ships the sentinel extents the policy forbids
        (they break CAD viewer zoom-to-fit). A document with no geometry gets a
        finite degenerate box at the origin rather than the sentinels.
        """
        bounds = bbox.extents(self._msp)
        if bounds.has_data:
            emin = (
                round(bounds.extmin.x, COORDINATE_PRECISION),
                round(bounds.extmin.y, COORDINATE_PRECISION),
                round(bounds.extmin.z, COORDINATE_PRECISION),
            )
            emax = (
                round(bounds.extmax.x, COORDINATE_PRECISION),
                round(bounds.extmax.y, COORDINATE_PRECISION),
                round(bounds.extmax.z, COORDINATE_PRECISION),
            )
        else:
            emin = (0.0, 0.0, 0.0)
            emax = (0.0, 0.0, 0.0)

        # Block-record extents are what ezdxf's exporter copies into the header.
        self._msp.dxf.extmin = emin
        self._msp.dxf.extmax = emax
        # Header directly, for the origin case where update_extents skips a
        # falsy (0,0,0) modelspace extent and would otherwise leave it unchanged.
        self._doc.header["$EXTMIN"] = emin
        self._doc.header["$EXTMAX"] = emax
        # Paperspace ($PEXTMIN/$PEXTMAX) has no geometry; pin it finite so the
        # serialized output carries no ±1e20 sentinels anywhere.
        active_layout = self._doc.active_layout()
        active_layout.dxf.extmin = emin
        active_layout.dxf.extmax = emax

    def to_bytes(self) -> bytes:
        self._finalize_extents()
        stream = io.StringIO()
        self._doc.write(stream)
        return stream.getvalue().encode("utf-8")

    def saveas(self, path: str) -> None:
        self._finalize_extents()
        self._doc.saveas(path)


def create_dxf_writer(
    layer_names: Sequence[str] | None = None,
    layer_color: int = DEFAULT_LAYER_COLOR,
    version: str = DXF_VERSION_DEFAULT
) -> DxfWriter:
    """Create a DxfWriter with optional layers and version.

    Args:
        layer_names: Optional list of layer names to pre-register
        layer_color: Default color for layers (default: 7/white)
        version: DXF version - 'R12' for free tier, 'R2000' for paid tier
    """
    layers = [LayerDef(name, layer_color) for name in layer_names] if layer_names else None
    return DxfWriter(layers=layers, version=version)