"""
Adaptive Spiralizer L.2 - Enhanced Utilities
Curvature-based adaptive respacing and resampling tools
"""
import math
from typing import List, Tuple


def polyline_length(pts: List[Tuple[float, float]]) -> float:
    """Calculate total length of polyline"""
    if not pts:
        return 0.0
    L = 0.0
    for i in range(1, len(pts)):
        x1, y1 = pts[i - 1]
        x2, y2 = pts[i]
        L += math.hypot(x2 - x1, y2 - y1)
    return L


def resample_path(pts: List[Tuple[float, float]], ds: float) -> List[Tuple[float, float]]:
    """Resample path to approximate constant chord length ds"""
    if not pts or ds <= 1e-9:
        return pts
    out = [pts[0]]
    acc = 0.0
    for i in range(1, len(pts)):
        x1, y1 = out[-1]
        x2, y2 = pts[i]
        seg = math.hypot(x2 - x1, y2 - y1)
        while acc + seg >= ds:
            t = (ds - acc) / seg if seg > 1e-9 else 1.0
            nx = x1 + (x2 - x1) * t
            ny = y1 + (y2 - y1) * t
            out.append((nx, ny))
            x1, y1 = nx, ny
            seg = math.hypot(x2 - x1, y2 - y1)
            acc = 0.0
        acc += seg
        if seg > 1e-9 and (x2, y2) != out[-1]:
            out.append((x2, y2))
    return out


def curvature(pts: List[Tuple[float, float]], i: int) -> float:
    """
    Discrete curvature k ~ 2*area / (|ab|*|bc|*|ac|)
    Returns curvature in 1/mm (higher = tighter curve)
    """
    if i <= 0 or i >= len(pts) - 1:
        return 0.0
    ax, ay = pts[i - 1]
    bx, by = pts[i]
    cx, cy = pts[i + 1]
    ab = math.hypot(bx - ax, by - ay)
    bc = math.hypot(cx - bx, cy - by)
    ac = math.hypot(cx - ax, cy - ay)
    if ab < 1e-9 or bc < 1e-9 or ac < 1e-9:
        return 0.0
    area = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) / 2.0
    k = 4.0 * area / (ab * bc * ac)
    return k


def adaptive_respace(
    pts: List[Tuple[float, float]],
    ds_min: float,
    ds_max: float,
    k_threshold: float
) -> List[Tuple[float, float]]:
    """
    Locally shrink spacing (ds) as curvature rises (k), between ds_min and ds_max.
    k_threshold: curvature (1/mm) above which we begin reducing spacing
    """
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    i = 1
    while i < len(pts):
        # Estimate curvature at current region
        k = max(
            curvature(pts, max(1, i - 1)),
            curvature(pts, i) if i < len(pts) - 1 else 0.0,
            curvature(pts, min(i + 1, len(pts) - 2))
        )
        # Map curvature to spacing: high k → small ds
        alpha = min(1.0, max(0.0, k / max(1e-6, k_threshold)))  # 0..1
        ds = ds_max - (ds_max - ds_min) * alpha

        # Walk forward until we exceed ds
        last = out[-1]
        walked = 0.0
        j = i
        while j < len(pts):
            d = math.hypot(pts[j][0] - last[0], pts[j][1] - last[1])
            if walked + d >= ds:
                break
            walked += d
            last = pts[j]
            j += 1
        if j >= len(pts):
            break

        # Interpolate on segment to hit target ds
        x1, y1 = last
        x2, y2 = pts[j]
        seg = math.hypot(x2 - x1, y2 - y1)
        t = 0.0 if seg < 1e-9 else (ds - walked) / seg
        nx = x1 + (x2 - x1) * t
        ny = y1 + (y2 - y1) * t
        out.append((nx, ny))
        i = max(j, i + 1)

    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def compute_slowdown_factors(
    pts: List[Tuple[float, float]],
    tool_d: float,
    k_threshold: float = None,
    slowdown_range: Tuple[float, float] = (0.4, 1.0)
) -> List[float]:
    """
    Compute per-point feed slowdown factor based on curvature.
    Returns list of scale factors (0.4..1.0) where 1.0 = full speed.
    
    Args:
        pts: Toolpath points
        tool_d: Tool diameter
        k_threshold: Curvature threshold (1/mm) above which to slow down
        slowdown_range: (min_scale, max_scale) for feed adjustment
    """
    if k_threshold is None:
        k_threshold = 1.0 / max(1.0, 3.0 * tool_d)  # Begin slowing when R < 3x tool_d
    
    min_scale, max_scale = slowdown_range
    factors = []
    
    for i in range(len(pts)):
        if i <= 0 or i >= len(pts) - 1:
            factors.append(max_scale)  # Full speed at endpoints
            continue
        
        # Get local curvature
        k = max(
            curvature(pts, max(1, i - 1)),
            curvature(pts, i),
            curvature(pts, min(i + 1, len(pts) - 2))
        )
        
        # Map curvature to slowdown: k > k_threshold → reduce speed
        alpha = min(1.0, max(0.0, k / k_threshold))  # 0 = low curvature, 1 = high
        scale = max_scale - (max_scale - min_scale) * alpha
        factors.append(scale)
    
    return factors
