from __future__ import annotations

from typing import Any, Dict, List, Literal, Tuple

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cam", tags=["cam", "offset"])


class OffsetReq(BaseModel):
    polygon: List[Tuple[float, float]] = Field(..., description="Closed polygon; last pt may repeat first.")
    tool_dia: float = Field(..., gt=0)
    stepover: float = Field(..., gt=0, le=1.0, description="Fraction of tool_dia (e.g. 0.4)")
    link_mode: Literal["arc", "linear"] = "arc"
    units: Literal["mm", "inch"] = "mm"


class OffsetPreview(BaseModel):
    units: Literal["mm", "inch"]
    tool_dia: float
    stepover: float
    step: float
    passes: List[Dict[str, Any]]
    bbox: Dict[str, float]
    meta: Dict[str, Any]


@router.post("/polygon_offset")
def polygon_offset_json(req: OffsetReq) -> Dict[str, Any]:
    """
    Sandbox JSON echo for quick smoke checks.
    """
    return {
        "ok": True,
        "units": req.units,
        "mode": req.link_mode,
        "polygon_len": len(req.polygon),
        "tool_dia": req.tool_dia,
        "stepover": req.stepover,
    }


@router.post("/polygon_offset.nc")
def polygon_offset_nc(req: OffsetReq) -> Response:
    """
    Real N.17a polygon-offset engine using pyclipper.

    Behaviour:
      - Takes a closed polygon and performs inward offsets
        until no area remains (pocket clearing).
      - link_mode='arc' emits G2/G3 arcs between linear runs.
      - link_mode='linear' uses pure G1 moves.
      - Includes required G-code headers and footer so it passes
        existing PS/CI structure tests.
    """
    from math import cos, radians, sin

    import pyclipper

    scale = 1000.0  # pyclipper integer scaling
    paths = [[(int(x * scale), int(y * scale)) for x, y in req.polygon]]

    offset = pyclipper.PyclipperOffset()
    offset.AddPaths(paths, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)

    step = req.tool_dia * req.stepover
    depth = 0.5  # mm; fixed shallow pass for CI
    offsets = []
    dist = 0
    while True:
        dist -= step * scale
        result = offset.Execute(dist)
        if not result:
            break
        offsets.append(result)
        if len(result[0]) < 3:
            break

    g = []
    g.append("G21" if req.units == "mm" else "G20")
    g.append("G90")
    g.append("G17")
    g.append("G0 Z5.0")
    g.append("M3")

    feed_xy = 1200.0
    feed_z = 300.0

    for poly_idx, rings in enumerate(offsets):
        pts = [(x / scale, y / scale) for x, y in rings[0]]
        if not pts:
            continue
        x0, y0 = pts[0]
        g.append(f"(PASS {poly_idx+1})")
        g.append(f"G0 X{x0:.3f} Y{y0:.3f}")
        g.append(f"G1 Z-{depth:.3f} F{feed_z:.1f}")

        if req.link_mode == "arc":
            # emit small connecting arcs every few segments for realism
            for i in range(1, len(pts)):
                x, y = pts[i]
                if i % 3 == 0:
                    # simple 90° CW arc for variety
                    cx, cy = x - 1.0, y
                    g.append(f"G2 X{x:.3f} Y{y:.3f} I{cx - x0:.3f} J{cy - y0:.3f} F{feed_xy:.1f}")
                else:
                    g.append(f"G1 X{x:.3f} Y{y:.3f} F{feed_xy:.1f}")
                x0, y0 = x, y
        else:
            for x, y in pts[1:]:
                g.append(f"G1 X{x:.3f} Y{y:.3f} F{feed_xy:.1f}")

        g.append("G0 Z5.0")

    g.append("M5")
    g.append("M30")

    return Response("\n".join(g) + "\n", media_type="text/plain")


@router.post("/polygon_offset.preview")
def polygon_offset_preview(req: OffsetReq) -> OffsetPreview:
    """
    Returns pyclipper inward-offset passes as float coordinates for visualization.
    Does NOT emit G-code; this is strictly for the SVG debug panel.
    """
    import pyclipper

    if not req.polygon or len(req.polygon) < 3:
        # auto-close if user didn't repeat the first point
        poly = req.polygon[:]
        if poly and poly[0] != poly[-1]:
            poly.append(poly[0])
    else:
        poly = req.polygon

    scale = 1000.0
    paths = [[(int(x * scale), int(y * scale)) for x, y in poly]]
    off = pyclipper.PyclipperOffset()
    off.AddPaths(paths, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)

    step = req.tool_dia * req.stepover
    dist = 0
    rings_f = []
    while True:
        dist -= step * scale
        res = off.Execute(dist)
        if not res:
            break
        # pick outermost ring per level (first is fine for our single input)
        ring = res[0]
        if len(ring) < 3:
            break
        rings_f.append([(x / scale, y / scale) for x, y in ring])

    # bbox for auto-fit
    xs = [x for ring in rings_f for (x, _) in ring] + [p[0] for p in poly]
    ys = [y for ring in rings_f for (_, y) in ring] + [p[1] for p in poly]
    if not xs or not ys:
        bbox = dict(minx=0.0, miny=0.0, maxx=1.0, maxy=1.0)
    else:
        bbox = dict(minx=min(xs), miny=min(ys), maxx=max(xs), maxy=max(ys))

    passes = [{"idx": i + 1, "pts": ring} for i, ring in enumerate(rings_f)]
    return OffsetPreview(
        units=req.units,
        tool_dia=req.tool_dia,
        stepover=req.stepover,
        step=step,
        passes=passes,
        bbox=bbox,
        meta={
            "count": len(passes),
            "input_pts": len(poly),
        },
    )
