"""
Production Shop — DXF Spline Service
FastAPI endpoint that evaluates NURBS/spline entities from DXF files
using ezdxf's full curve math, returning clean polylines to the browser.

Slot into your existing Production Shop FastAPI app:
    from dxf_service import router as dxf_router
    app.include_router(dxf_router, prefix="/api/dxf")
"""

from __future__ import annotations

import io
import math
import tempfile
from pathlib import Path
from typing import Optional

import ezdxf
import ezdxf.math
from ezdxf.entities import Spline, LWPolyline, Polyline, Circle, Arc, Ellipse, Line, Insert
from ezdxf.math import BSpline, Vec3

from fastapi import APIRouter, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["dxf"])


# ─── Models ──────────────────────────────────────────────────────────────────

class SplinePayload(BaseModel):
    """Raw spline data forwarded from the browser's dxf-parser."""
    control_points: list[dict]          # [{x, y, z?}]
    knot_values: Optional[list[float]]  # may be absent in R12
    degree: Optional[int] = 3
    fit_points: Optional[list[dict]] = None
    closed: Optional[bool] = False
    samples: Optional[int] = 128        # resolution of output polyline


class EntitySet(BaseModel):
    """A batch of entities from one layer for server-side evaluation."""
    entities: list[dict]                # each has 'type' + entity-specific fields
    samples_per_curve: Optional[int] = 96
    flip_y: Optional[bool] = True       # DXF Y-up → SVG Y-down


class NormalizeRequest(BaseModel):
    """Full DXF file path (server-local) → normalized path strings."""
    dxf_path: str
    target_width: Optional[float] = 200.0
    target_height: Optional[float] = 320.0
    padding: Optional[float] = 8.0
    fit_mode: Optional[str] = "contain"   # contain | width | height | stretch
    layers: Optional[list[str]] = None    # None = all layers
    samples_per_curve: Optional[int] = 96


# ─── Spline evaluation ───────────────────────────────────────────────────────

def evaluate_spline(
    control_points: list[Vec3],
    knot_values: Optional[list[float]],
    degree: int,
    closed: bool,
    samples: int,
) -> list[tuple[float, float]]:
    """
    Evaluate a B-spline using ezdxf's BSpline class.
    Returns a flat list of (x, y) tuples.
    """
    if len(control_points) < 2:
        return [(p.x, p.y) for p in control_points]

    try:
        if knot_values and len(knot_values) >= len(control_points) + degree + 1:
            bsp = BSpline(control_points, order=degree + 1, knots=knot_values)
        else:
            # Auto-generate uniform knot vector
            bsp = BSpline(control_points, order=degree + 1)

        pts = list(bsp.approximate(samples))
        return [(p.x, p.y) for p in pts]

    except Exception as exc:
        # Fall back to linear interpolation through control points
        return [(p.x, p.y) for p in control_points]


def spline_to_svg_path(pts: list[tuple[float, float]], closed: bool = False) -> str:
    if not pts:
        return ""
    d = f"M{pts[0][0]:.3f},{pts[0][1]:.3f}"
    for x, y in pts[1:]:
        d += f"L{x:.3f},{y:.3f}"
    if closed:
        d += "Z"
    return d


# ─── Entity → polyline points ─────────────────────────────────────────────────

def arc_points(
    cx: float, cy: float, r: float,
    start_deg: float, end_deg: float,
    samples: int = 48,
) -> list[tuple[float, float]]:
    """Sample an arc into (x, y) points."""
    s, e = math.radians(start_deg), math.radians(end_deg)
    if e < s:
        e += 2 * math.pi
    angles = [s + (e - s) * i / samples for i in range(samples + 1)]
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]


def ellipse_points(
    cx: float, cy: float,
    major_x: float, major_y: float,
    ratio: float,
    start_param: float = 0.0,
    end_param: float = 2 * math.pi,
    samples: int = 64,
) -> list[tuple[float, float]]:
    major_len = math.sqrt(major_x ** 2 + major_y ** 2)
    minor_len = major_len * ratio
    angle = math.atan2(major_y, major_x)
    params = [start_param + (end_param - start_param) * i / samples for i in range(samples + 1)]
    pts = []
    for p in params:
        lx = major_len * math.cos(p)
        ly = minor_len * math.sin(p)
        rx = lx * math.cos(angle) - ly * math.sin(angle) + cx
        ry = lx * math.sin(angle) + ly * math.cos(angle) + cy
        pts.append((rx, ry))
    return pts


def lwpoly_points(vertices: list[dict]) -> list[tuple[float, float]]:
    """
    Convert LWPOLYLINE vertices (with optional bulge) to polyline points.
    Bulge encodes arc segments between consecutive vertices.
    """
    pts = []
    for i, v in enumerate(vertices):
        pts.append((v["x"], v["y"]))
        bulge = v.get("bulge", 0.0)
        if bulge and abs(bulge) > 1e-6 and i < len(vertices) - 1:
            nv = vertices[i + 1]
            x1, y1 = v["x"], v["y"]
            x2, y2 = nv["x"], nv["y"]
            d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if d < 1e-10:
                continue
            r_val = d * (1 + bulge ** 2) / (4 * abs(bulge))
            # Centre of arc
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            sagitta = bulge * d / 2
            perp_x = -(y2 - y1) / d
            perp_y = (x2 - x1) / d
            sign = 1 if bulge > 0 else -1
            dist_to_center = math.sqrt(max(r_val ** 2 - (d / 2) ** 2, 0))
            acx = mid_x + sign * dist_to_center * perp_x
            acy = mid_y + sign * dist_to_center * perp_y
            a1 = math.atan2(y1 - acy, x1 - acx)
            a2 = math.atan2(y2 - acy, x2 - acx)
            if bulge > 0 and a2 < a1:
                a2 += 2 * math.pi
            elif bulge < 0 and a2 > a1:
                a2 -= 2 * math.pi
            steps = max(8, int(abs(a2 - a1) / (2 * math.pi) * 48))
            for j in range(1, steps + 1):
                a = a1 + (a2 - a1) * j / steps
                pts.append((acx + r_val * math.cos(a), acy + r_val * math.sin(a)))
    return pts


# ─── Full DXF file processing ─────────────────────────────────────────────────

def process_dxf_file(
    dxf_bytes: bytes,
    layers: Optional[list[str]] = None,
    samples: int = 96,
    flip_y: bool = True,
) -> dict:
    """
    Parse a full DXF file with ezdxf and return:
      - path strings per entity (SVG 200×320 coordinate space)
      - bounding box of raw geometry
      - layer names found
      - entity type counts
    """
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
        f.write(dxf_bytes)
        tmp = Path(f.name)

    try:
        doc = ezdxf.readfile(str(tmp))
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise ValueError(f"ezdxf parse error: {exc}")
    finally:
        tmp.unlink(missing_ok=True)

    msp = doc.modelspace()
    all_pts: list[tuple[float, float]] = []
    entity_paths: list[dict] = []
    type_counts: dict[str, int] = {}
    layer_names: set[str] = set()

    for ent in msp:
        layer = getattr(ent.dxf, "layer", "0")
        layer_names.add(layer)
        if layers and layer not in layers:
            continue

        etype = ent.dxftype()
        type_counts[etype] = type_counts.get(etype, 0) + 1
        pts: list[tuple[float, float]] = []

        try:
            if etype == "LINE":
                s, e = ent.dxf.start, ent.dxf.end
                pts = [(s.x, s.y), (e.x, e.y)]

            elif etype in ("LWPOLYLINE",):
                verts = [{"x": v[0], "y": v[1], "bulge": v[4] if len(v) > 4 else 0.0}
                         for v in ent.get_points("xyb")]
                pts = lwpoly_points(verts)
                if ent.is_closed and pts:
                    pts.append(pts[0])

            elif etype == "POLYLINE":
                verts = [{"x": v.dxf.location.x, "y": v.dxf.location.y,
                          "bulge": getattr(v.dxf, "bulge", 0.0)}
                         for v in ent.vertices]
                pts = lwpoly_points(verts)

            elif etype == "CIRCLE":
                c = ent.dxf.center
                pts = arc_points(c.x, c.y, ent.dxf.radius, 0, 359.99, samples)

            elif etype == "ARC":
                c = ent.dxf.center
                pts = arc_points(c.x, c.y, ent.dxf.radius,
                                 ent.dxf.start_angle, ent.dxf.end_angle, samples)

            elif etype == "ELLIPSE":
                c = ent.dxf.center
                me = ent.dxf.major_axis
                pts = ellipse_points(
                    c.x, c.y, me.x, me.y,
                    ent.dxf.ratio,
                    ent.dxf.start_param, ent.dxf.end_param, samples
                )

            elif etype == "SPLINE":
                cp = [Vec3(p) for p in ent.control_points]
                kv = list(ent.knots) if ent.knots else None
                deg = ent.dxf.degree if hasattr(ent.dxf, "degree") else 3
                evaluated = evaluate_spline(cp, kv, deg, ent.closed, samples)
                pts = evaluated

            # Skip INSERT, TEXT, DIMENSION, HATCH, etc.

        except Exception:
            continue

        if not pts:
            continue

        all_pts.extend(pts)
        d = spline_to_svg_path(pts, closed=(etype in ("LWPOLYLINE", "POLYLINE") and
                               hasattr(ent, "is_closed") and ent.is_closed))
        entity_paths.append({
            "id": f"{etype}_{len(entity_paths)}",
            "type": etype,
            "layer": layer,
            "d_raw": d,
            "point_count": len(pts),
        })

    if not all_pts:
        return {
            "entity_paths": [],
            "bbox": None,
            "layers": sorted(layer_names),
            "type_counts": type_counts,
            "error": "No renderable geometry found",
        }

    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    bbox = {"minX": min(xs), "minY": min(ys), "maxX": max(xs), "maxY": max(ys),
            "w": max(xs) - min(xs), "h": max(ys) - min(ys)}

    return {
        "entity_paths": entity_paths,
        "bbox": bbox,
        "layers": sorted(layer_names),
        "type_counts": type_counts,
    }


def normalize_paths(
    entity_paths: list[dict],
    bbox: dict,
    target_w: float = 200.0,
    target_h: float = 320.0,
    padding: float = 8.0,
    fit_mode: str = "contain",
    flip_y: bool = True,
) -> list[dict]:
    """
    Transform raw path point sets into the 200×320 target space.
    Returns entity_paths with a new 'd_norm' field.
    """
    tw, th = target_w - padding * 2, target_h - padding * 2
    bw, bh = bbox["w"], bbox["h"]
    if bw < 1e-9 or bh < 1e-9:
        return entity_paths

    if fit_mode == "contain":
        sc = min(tw / bw, th / bh)
        sx = sy = sc
    elif fit_mode == "width":
        sx = sy = tw / bw
    elif fit_mode == "height":
        sx = sy = th / bh
    else:  # stretch
        sx, sy = tw / bw, th / bh

    scaled_w = bw * sx
    scaled_h = bh * sy
    off_x = padding + (tw - scaled_w) / 2
    off_y = padding + (th - scaled_h) / 2

    result = []
    for ep in entity_paths:
        # Re-parse raw path points from 'd_raw'
        raw = ep.get("d_raw", "")
        if not raw:
            result.append({**ep, "d_norm": ""})
            continue

        # Extract points from M/L commands
        pts: list[tuple[float, float]] = []
        for cmd in raw.replace("M", " M ").replace("L", " L ").replace("Z", "").split():
            pass  # handled below

        import re
        coords = re.findall(r"[ML]\s*([-\d.]+),([-\d.]+)", raw)
        if not coords:
            result.append({**ep, "d_norm": raw})
            continue

        norm_pts = []
        for sx_str, sy_str in coords:
            rx, ry = float(sx_str), float(sy_str)
            # Shift to origin
            nx = (rx - bbox["minX"]) * sx + off_x
            if flip_y:
                ny = target_h - ((ry - bbox["minY"]) * sy + off_y)
            else:
                ny = (ry - bbox["minY"]) * sy + off_y
            norm_pts.append((nx, ny))

        closed = raw.strip().endswith("Z")
        d_norm = spline_to_svg_path(norm_pts, closed)
        result.append({**ep, "d_norm": d_norm})

    return result


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/spline/evaluate")
async def evaluate_spline_endpoint(payload: SplinePayload):
    """
    Evaluate a single B-spline from browser-parsed control points.
    Called when dxf-parser in the browser encounters a SPLINE entity
    and forwards the raw data for server-side NURBS evaluation.
    """
    cp = [Vec3(p["x"], p.get("y", 0), p.get("z", 0)) for p in payload.control_points]
    kv = payload.knot_values
    deg = payload.degree or 3
    pts = evaluate_spline(cp, kv, deg, payload.closed or False, payload.samples or 128)
    return {
        "points": [{"x": x, "y": y} for x, y in pts],
        "d": spline_to_svg_path(pts, payload.closed or False),
        "point_count": len(pts),
        "method": "ezdxf_bspline",
    }


@router.post("/parse")
async def parse_dxf_upload(
    file: UploadFile = File(...),
    layers: Optional[str] = None,          # comma-separated layer filter
    samples: int = 96,
    flip_y: bool = True,
):
    """
    Upload a full DXF file. Returns all geometry as SVG path strings
    with bbox and layer info. SPLINE entities are evaluated with full
    ezdxf NURBS math rather than the browser's control-point approximation.
    """
    if not file.filename.lower().endswith((".dxf",)):
        raise HTTPException(400, "Only .dxf files accepted on this endpoint")

    data = await file.read()
    layer_filter = [l.strip() for l in layers.split(",")] if layers else None

    try:
        result = process_dxf_file(data, layer_filter, samples, flip_y)
    except ValueError as e:
        raise HTTPException(422, str(e))

    return JSONResponse(result)


@router.post("/parse-and-normalize")
async def parse_and_normalize(
    file: UploadFile = File(...),
    target_width: float = 200.0,
    target_height: float = 320.0,
    padding: float = 8.0,
    fit_mode: str = "contain",
    layers: Optional[str] = None,
    samples: int = 96,
    flip_y: bool = True,
):
    """
    Full pipeline: upload DXF → evaluate all entities → normalize to
    target coordinate space → return SVG path strings ready for the
    headstock workspace canvas.
    """
    if not file.filename.lower().endswith(".dxf"):
        raise HTTPException(400, "Only .dxf files accepted")

    data = await file.read()
    layer_filter = [l.strip() for l in layers.split(",")] if layers else None

    try:
        result = process_dxf_file(data, layer_filter, samples, flip_y)
    except ValueError as e:
        raise HTTPException(422, str(e))

    if not result.get("entity_paths") or not result.get("bbox"):
        raise HTTPException(422, result.get("error", "No geometry found"))

    normalized = normalize_paths(
        result["entity_paths"], result["bbox"],
        target_width, target_height, padding, fit_mode, flip_y
    )

    return JSONResponse({
        "paths": [
            {
                "id": ep["id"],
                "type": ep["type"],
                "layer": ep["layer"],
                "d": ep.get("d_norm", ep.get("d_raw", "")),
                "point_count": ep["point_count"],
            }
            for ep in normalized
        ],
        "bbox_raw": result["bbox"],
        "layers": result["layers"],
        "type_counts": result["type_counts"],
        "target": {"width": target_width, "height": target_height},
    })


@router.get("/layers")
async def get_layers(file: UploadFile = File(...)):
    """
    Quick scan — returns only the layer names in a DXF file
    without full geometry processing.
    """
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
        f.write(data); tmp = Path(f.name)
    try:
        doc = ezdxf.readfile(str(tmp))
        layers = [l.dxf.name for l in doc.layers]
        return {"layers": layers}
    except Exception as e:
        raise HTTPException(422, str(e))
    finally:
        tmp.unlink(missing_ok=True)
