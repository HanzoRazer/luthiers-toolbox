from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import List, Literal, Optional, Union

try:  # pragma: no cover - optional dependency
    import ezdxf
except ImportError:  # pragma: no cover - executed if ezdxf missing  # WP-1: narrowed from except Exception
    ezdxf = None  # type: ignore[assignment]

GeomKind = Literal["line", "circle"]


@dataclass
class DxfLine:
    kind: GeomKind
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    layer: str = "0"


@dataclass
class DxfCircle:
    kind: GeomKind
    center_x_mm: float
    center_y_mm: float
    radius_mm: float
    layer: str = "0"


DxfGeom = Union[DxfLine, DxfCircle]


def _require_ezdxf() -> None:
    if ezdxf is None:  # pragma: no cover - optional path
        raise RuntimeError(
            "DXF support requires ezdxf. Install it via `pip install ezdxf`."
        )


def load_dxf_geometries(
    dxf_path: str,
    layer: Optional[str] = None,
    unit_scale: float = 1.0,
) -> List[DxfGeom]:
    """Load LINE and CIRCLE entities from a DXF file and normalize to mm."""
    _require_ezdxf()

    if not os.path.exists(dxf_path):
        raise FileNotFoundError(dxf_path)

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    geoms: List[DxfGeom] = []
    for entity in msp:
        entity_layer = getattr(entity.dxf, "layer", "0")
        if layer and entity_layer != layer:
            continue

        dxftype = entity.dxftype()
        if dxftype == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            geoms.append(
                DxfLine(
                    kind="line",
                    x1_mm=float(start.x) * unit_scale,
                    y1_mm=float(start.y) * unit_scale,
                    x2_mm=float(end.x) * unit_scale,
                    y2_mm=float(end.y) * unit_scale,
                    layer=entity_layer,
                )
            )
        elif dxftype == "CIRCLE":
            center = entity.dxf.center
            radius = float(entity.dxf.radius) * unit_scale
            if radius > 0:
                geoms.append(
                    DxfCircle(
                        kind="circle",
                        center_x_mm=float(center.x) * unit_scale,
                        center_y_mm=float(center.y) * unit_scale,
                        radius_mm=radius,
                        layer=entity_layer,
                    )
                )

    def _sort_key(geom: DxfGeom) -> tuple[int, float]:
        if geom.kind == "circle":
            return (0, getattr(geom, "radius_mm", 0.0))
        length = math.hypot(geom.x2_mm - geom.x1_mm, geom.y2_mm - geom.y1_mm)
        return (1, length)

    geoms.sort(key=_sort_key)
    return geoms
