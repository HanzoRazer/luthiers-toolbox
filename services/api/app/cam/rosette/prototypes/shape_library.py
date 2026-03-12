"""
Parametric shape library — all 17 tile shapes ported from JSX prototypes.

Each shape function returns a closed numpy array of (x, y) coordinates
in tile-local space.  Origin = tile center, X = tangential, Y = radial.
W = tile width, H = tile height.

Shapes are registered in SHAPES dict.  Each entry carries:
    label, group, hint, params (list of param descriptors), draw function.

Usage:
    from shape_library import SHAPES, draw_shape
    pts = draw_shape("parallelogram", W=40, H=30, params={"w": 0.88, "h": 0.9, "lean": 0.28, "ch": 0.14})
"""

from __future__ import annotations

import math
import numpy as np


# ─── Helper: sample cubic bezier ─────────────────────────────────

def _bezier3(p0, p1, p2, p3, n=20):
    """Return n+1 points along a cubic bezier from p0 to p3."""
    t = np.linspace(0, 1, n + 1).reshape(-1, 1)
    pts = (
        (1 - t) ** 3 * np.array(p0)
        + 3 * (1 - t) ** 2 * t * np.array(p1)
        + 3 * (1 - t) * t ** 2 * np.array(p2)
        + t ** 3 * np.array(p3)
    )
    return pts  # shape (n+1, 2)


def _quad_bezier(p0, p1, p2, n=12):
    """Return n+1 points along a quadratic bezier."""
    t = np.linspace(0, 1, n + 1).reshape(-1, 1)
    pts = (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)
    return pts


# ─── Shape definitions ────────────────────────────────────────────

def _parallelogram(W, H, p, idx=0):
    hw = W / 2 * p["w"]
    hh = H / 2 * p["h"]
    lx = W * p["lean"]
    ch = min(hw, hh) * p["ch"]
    if ch > 1:
        pts = np.array([
            [-hw + lx + ch, -hh], [hw + lx - ch, -hh],
            [hw + lx, -hh + ch], [hw - lx, hh - ch],
            [hw - lx - ch, hh], [-hw - lx + ch, hh],
            [-hw - lx, hh - ch], [-hw + lx, -hh + ch],
        ])
    else:
        pts = np.array([
            [-hw + lx, -hh], [hw + lx, -hh],
            [hw - lx, hh], [-hw - lx, hh],
        ])
    return np.vstack([pts, pts[:1]])


def _ellipse(W, H, p, idx=0):
    rx = W / 2 * p["rx"]
    ry = H / 2 * p["ry"]
    t = np.linspace(0, 2 * math.pi, 64)
    return np.column_stack([np.cos(t) * rx, np.sin(t) * ry])


def _oval_lean(W, H, p, idx=0):
    N = 52
    rx = W / 2 * p["rx"]
    ry = H / 2 * p["ry"]
    lx = W / 2 * p["lean"]
    a = np.linspace(0, 2 * math.pi, N + 1)
    x = np.cos(a) * rx + lx * np.sin(a)
    y = np.sin(a) * ry
    return np.column_stack([x, y])


def _diamond(W, H, p, idx=0):
    hw = W / 2 * p["w"]
    hh = H / 2 * p["h"]
    lx = hw * p["lean"]
    r = min(hw, hh) * p["r"]
    if r > 1:
        f = 0.55
        segs = []
        segs.append([lx, -hh + r])
        segs.extend(_bezier3([lx, -hh + r], [lx + r * f, -hh], [hw + lx - r * f, -(r * 0.3)], [hw + lx, 0], 12))
        segs.extend(_bezier3([hw + lx, 0], [hw + lx + r * f, r * 0.3], [lx + r * f, hh], [lx, hh - r], 12))
        segs.extend(_bezier3([lx, hh - r], [lx - r * f, hh], [-hw + lx + r * f, r * 0.3], [-hw + lx, 0], 12))
        segs.extend(_bezier3([-hw + lx, 0], [-hw + lx - r * f, -r * 0.3], [lx - r * f, -hh], [lx, -hh + r], 12))
        return np.array(segs)
    else:
        pts = np.array([[lx, -hh], [hw + lx, 0], [lx, hh], [-hw + lx, 0]])
        return np.vstack([pts, pts[:1]])


def _crescent_outer(W, H, p, idx=0):
    """Outer ellipse of crescent."""
    return _ellipse(W, H, {"rx": p["orx"], "ry": p["ory"]})


def _crescent_inner(W, H, p, idx=0):
    """Inner void of crescent — offset ellipse."""
    rx = W / 2 * p["irx"]
    ry = H / 2 * p["iry"]
    ox = W / 2 * p["iox"]
    oy = H / 2 * p["ioy"]
    t = np.linspace(0, 2 * math.pi, 64)
    return np.column_stack([np.cos(t) * rx + ox, np.sin(t) * ry + oy])


def _lens(W, H, p, idx=0):
    hw = W / 2 * p["w"]
    hh = H / 2 * p["h"]
    cx = hw * p["curve"] * 1.2
    lx = W / 4 * p["lean"]
    segs = []
    segs.append([lx, -hh])
    segs.extend(_bezier3([lx, -hh], [cx + lx, -hh * 0.4], [cx, -hh * 0.1], [0, hh], 24))
    segs.extend(_bezier3([0, hh], [-cx, -hh * 0.1], [-cx + lx, -hh * 0.4], [lx, -hh], 24))
    return np.array(segs)


def _teardrop(W, H, p, idx=0):
    hw = W / 2 * p["w"]
    hh = H / 2 * p["h"]
    d = -1 if p["flip"] > 0.5 else 1
    tipY = -hh * d
    botY = hh * d
    tc = hh * p["tip"] * d * 0.8

    segs = []
    segs.append([0, tipY])
    segs.extend(_bezier3([0, tipY], [hw, tipY + tc], [hw * 1.1 * p["bulge"], 0], [hw * 0.85, botY], 20))
    N = 16
    for i in range(1, N + 1):
        a = i / N * math.pi
        segs.append([math.cos(math.pi - a) * hw * 0.85, botY + math.sin(math.pi - a) * hw * 0.22])
    segs.extend(_bezier3([-hw * 0.85, botY], [-hw * 1.1 * p["bulge"], 0], [-hw, tipY + tc], [0, tipY], 20))
    return np.array(segs)


def _star(W, H, p, idx=0):
    n = round(p["n"])
    sc = min(W, H) / 2
    ro = sc * p["outer"]
    ri = sc * p["inner"]
    spin = p["spin"] * math.pi
    pts = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = i * math.pi / n - math.pi / 2 + spin
        pts.append([math.cos(a) * r, math.sin(a) * r])
    pts.append(pts[0])
    return np.array(pts)


def _ogee(W, H, p, idx=0):
    hw = W / 2 * p["w"]
    hh = H / 2 * p["h"]
    bx = hw * p["bulge"]
    wy = hh * p["waist"]
    tc = H / 2 * p["top"]
    segs = []
    segs.append([-hw, -hh])
    segs.extend(_bezier3([-hw, -hh], [-hw / 2, -hh - tc], [hw / 2, -hh - tc], [hw, -hh], 12))
    segs.extend(_bezier3([hw, -hh], [hw + bx, -hh / 2], [hw - bx, -wy], [hw, 0], 12))
    segs.extend(_bezier3([hw, 0], [hw + bx, wy], [hw - bx, hh / 2], [hw, hh], 12))
    segs.extend(_bezier3([hw, hh], [hw / 2, hh + tc], [-hw / 2, hh + tc], [-hw, hh], 12))
    segs.extend(_bezier3([-hw, hh], [-hw + bx, hh / 2], [-hw - bx, wy], [-hw, 0], 12))
    segs.extend(_bezier3([-hw, 0], [-hw + bx, -wy], [-hw - bx, -hh / 2], [-hw, -hh], 12))
    return np.array(segs)


def _scale(W, H, p, idx=0):
    hw = W / 2 * p["w"]
    hh = H / 2 * p["h"]
    arch = H * p["arch"] * 0.5
    tr = hh * p["tail"]
    segs = []
    segs.append([-hw, -hh + arch])
    segs.extend(_bezier3([-hw, -hh + arch], [-hw * 0.5, -hh - arch * 0.5], [hw * 0.5, -hh - arch * 0.5], [hw, -hh + arch], 20))
    if tr > 1:
        segs.append([hw, hh - tr])
        segs.extend(_quad_bezier([hw, hh - tr], [hw, hh], [hw - tr, hh], 8))
    else:
        segs.append([hw, hh])
    segs.append([-hw, hh])
    segs.append([-hw, -hh + arch])
    return np.array(segs)


def _rope_asym(W, H, p, idx=0):
    hh = H / 2 * p["thick"]
    wave = H / 2 * p["wave"]
    peakX = -W / 2 + W * p["skew"]
    driftY = (H / 2 - hh) * math.sin(idx * p["drift"] * 0.8)
    y0 = driftY
    cr = hh * p["cap"]
    segs = []
    start = [-W / 2, y0 - hh + cr]
    segs.append(start)
    if cr > 1:
        segs.extend(_quad_bezier([-W / 2, y0 - hh + cr], [-W / 2, y0 - hh], [-W / 2 + cr, y0 - hh], 6))
    segs.extend(_bezier3(
        [-W / 2 + (cr if cr > 1 else 0), y0 - hh],
        [peakX - W / 6, y0 - hh - wave],
        [peakX + W / 6, y0 - hh - wave * 0.8],
        [W / 2, y0 - hh + wave * 0.3], 20,
    ))
    segs.append([W / 2, y0 + hh - wave * 0.3])
    segs.extend(_bezier3(
        [W / 2, y0 + hh - wave * 0.3],
        [peakX + W * 0.1 + W / 6, y0 + hh + wave * 0.8],
        [peakX + W * 0.1 - W / 6, y0 + hh + wave],
        [-W / 2, y0 + hh], 20,
    ))
    if cr > 1:
        segs.extend(_quad_bezier([-W / 2, y0 + hh], [-W / 2, y0 + hh], [-W / 2, y0 + hh - cr], 6))
    segs.append(start)
    return np.array(segs)


def _hexagon(W, H, p, idx=0):
    r = min(W, H) / 2 * p["r"]
    spin = p["rot"] * math.pi
    pts = []
    for i in range(6):
        a = i * math.pi / 3 + spin
        pts.append([math.cos(a) * r, math.sin(a) * r * p["squish"]])
    pts.append(pts[0])
    return np.array(pts)


def _petal(W, H, p, idx=0):
    hw = W / 2 * p["w"]
    hh = H / 2 * p["h"]
    lx = W * p["lean"]
    segs = []
    segs.append([lx, -hh])
    segs.extend(_bezier3(
        [lx, -hh],
        [hw + lx + W * p["c1"], -hh * 0.5],
        [hw, 0],
        [hw * 0.6, hh], 16,
    ))
    segs.extend(_bezier3(
        [hw * 0.6, hh],
        [hw * 0.2, hh * 1.1],
        [-hw * 0.2, hh * 1.1],
        [-hw * 0.6, hh], 12,
    ))
    segs.extend(_bezier3(
        [-hw * 0.6, hh],
        [-hw, 0],
        [-hw + lx + W * p["c2"], -hh * 0.5],
        [lx, -hh], 16,
    ))
    return np.array(segs)


def _hyperbolic_wave(W, H, p, idx=0):
    hh = H / 2 * p["thick"]
    t = idx * 0.3 + p["drift"] * math.log(idx + 2) + p["chaos"] * math.sin(idx * 0.17)
    peakX = -W / 2 + W * (p["skew"] + 0.1 * math.sin(t))
    waveY = H / 2 * p["wave"] * math.sin(t * 2.3)
    segs = []
    segs.append([-W / 2, -hh + waveY])
    segs.extend(_bezier3(
        [-W / 2, -hh + waveY],
        [peakX - W / 6, -hh - waveY * 0.5],
        [peakX + W / 6, -hh + waveY],
        [W / 2, -hh + waveY * 0.3], 20,
    ))
    segs.append([W / 2, hh - waveY * 0.3])
    segs.extend(_bezier3(
        [W / 2, hh - waveY * 0.3],
        [peakX + W / 6, hh + waveY],
        [peakX - W / 6, hh + waveY * 0.5],
        [-W / 2, hh - waveY], 20,
    ))
    segs.append([-W / 2, -hh + waveY])
    return np.array(segs)


def _draw_diamond_wave(W, H, p, idx=0):
    """Diamond wave shape from diamond-chevron-rosette.jsx (square tile)."""
    S = W  # square aspect
    hw = S / 2
    amp = hw * p.get("wave", 0.22) * 0.55
    lx = S * p.get("lean", 0.18) * 0.5
    bv = S * p.get("bevel", 0.15) * 0.4
    density = p.get("density", 2.8)
    dy_val = amp * math.sin((idx * 0.28 + density * 0.15) * math.pi)
    dy = max(-hw * 0.35, min(hw * 0.35, dy_val))

    if bv < 1.2:
        pts = np.array([
            [lx, -hw + dy], [hw, 0 + dy], [lx, hw + dy], [-hw, 0 + dy],
        ])
        return np.vstack([pts, pts[:1]])
    else:
        segs = []
        N_steps = 8
        # Simplified beveled version — chamfer tips
        segs.append([lx - bv * 0.5, -hw + bv * 0.5 + dy])
        segs.append([lx + bv * 0.5, -hw + bv * 0.5 + dy])
        for i in range(N_steps + 1):
            t = i / N_steps
            ew = bv * 0.25 * math.sin(t * math.pi * 2 + idx * 0.3)
            segs.append([lx + t * (hw - lx), -hw + t * hw + ew + dy])
        segs.append([hw - bv * 0.5, -bv * 0.3 + dy])
        segs.append([hw - bv * 0.5, bv * 0.3 + dy])
        for i in range(N_steps + 1):
            t = i / N_steps
            ew = bv * 0.25 * math.sin(t * math.pi * 2 + 1.3 + idx * 0.3)
            segs.append([hw - t * (hw - lx), t * hw + ew + dy])
        segs.append([lx + bv * 0.5, hw - bv * 0.5 + dy])
        segs.append([lx - bv * 0.5, hw - bv * 0.5 + dy])
        for i in range(N_steps + 1):
            t = i / N_steps
            ew = bv * 0.25 * math.sin(t * math.pi * 2 + 2.6 + idx * 0.3)
            segs.append([lx - t * (hw + lx), hw - t * hw + ew + dy])
        segs.append([-hw + bv * 0.5, bv * 0.3 + dy])
        segs.append([-hw + bv * 0.5, -bv * 0.3 + dy])
        for i in range(N_steps + 1):
            t = i / N_steps
            ew = bv * 0.25 * math.sin(t * math.pi * 2 + 3.9 + idx * 0.3)
            segs.append([-hw + t * (hw + lx), -t * hw + ew + dy])
        segs.append(segs[0])
        return np.array(segs)


def _draw_chevron(W, H, p, idx=0):
    """Stepped chevron from diamond-chevron-rosette.jsx."""
    n = max(1, round(p.get("steps", 3)))
    lx = W * p.get("lean", 0.0)
    sz = H / n
    hw = W / 2 * p.get("depth", 1.0)
    r = min(sz, hw) * p.get("round", 0.0)

    right_steps = []
    for i in range(n):
        y = -H / 2 + i * sz
        x = (hw if i % 2 == 0 else -hw) + lx * (i / n - 0.5) * 2
        right_steps.append([x, y])
        right_steps.append([x, y + sz])

    left_steps = [[-(x) + lx * 2, y] for x, y in reversed(right_steps)]

    if r < 1:
        pts = [[lx, -H / 2]] + right_steps + [[lx, H / 2]] + left_steps
        pts.append(pts[0])
        return np.array(pts)
    else:
        P = [[lx, -H / 2]] + right_steps + [[lx, H / 2]] + left_steps
        # Approximate arcTo with straight segments for simplicity
        pts = []
        for i in range(len(P)):
            pts.append(P[i])
        pts.append(pts[0])
        return np.array(pts)


# ─── Shape registry ───────────────────────────────────────────────

SHAPES = {
    "parallelogram": {
        "label": "Parallelogram", "group": "polygon",
        "hint": "The Fusion 360 tile — chamfered corners, lean controls direction",
        "params": [
            {"k": "w", "l": "Width", "min": 0.2, "max": 1.1, "s": 0.01, "d": 0.88},
            {"k": "h", "l": "Height", "min": 0.2, "max": 1.1, "s": 0.01, "d": 0.90},
            {"k": "lean", "l": "Lean", "min": -0.6, "max": 0.6, "s": 0.01, "d": 0.28},
            {"k": "ch", "l": "Chamfer", "min": 0, "max": 0.45, "s": 0.01, "d": 0.14},
        ],
        "draw": _parallelogram,
    },
    "ellipse": {
        "label": "Ellipse", "group": "curve",
        "hint": "Floating ovals — gap shows through between tiles",
        "params": [
            {"k": "rx", "l": "X radius", "min": 0.1, "max": 1.1, "s": 0.01, "d": 0.82},
            {"k": "ry", "l": "Y radius", "min": 0.1, "max": 1.1, "s": 0.01, "d": 0.85},
        ],
        "draw": _ellipse,
    },
    "oval_lean": {
        "label": "Leaning Oval", "group": "curve",
        "hint": "Sheared ellipse — the lean creates implied rotation and movement",
        "params": [
            {"k": "rx", "l": "X radius", "min": 0.1, "max": 1.1, "s": 0.01, "d": 0.78},
            {"k": "ry", "l": "Y radius", "min": 0.1, "max": 1.1, "s": 0.01, "d": 0.88},
            {"k": "lean", "l": "Lean", "min": -1, "max": 1, "s": 0.02, "d": 0.45},
        ],
        "draw": _oval_lean,
    },
    "diamond": {
        "label": "Diamond", "group": "polygon",
        "hint": "Rhombus with optional corner rounding and lean",
        "params": [
            {"k": "w", "l": "Width", "min": 0.1, "max": 1.2, "s": 0.01, "d": 0.82},
            {"k": "h", "l": "Height", "min": 0.1, "max": 1.2, "s": 0.01, "d": 0.90},
            {"k": "lean", "l": "Lean", "min": -0.8, "max": 0.8, "s": 0.01, "d": 0.0},
            {"k": "r", "l": "Corner round", "min": 0, "max": 0.5, "s": 0.01, "d": 0.0},
        ],
        "draw": _diamond,
    },
    "crescent": {
        "label": "Crescent", "group": "curve",
        "hint": "Moon shape — outer ellipse minus inner.  Background shows through the void",
        "params": [
            {"k": "orx", "l": "Outer X", "min": 0.2, "max": 1.1, "s": 0.01, "d": 0.88},
            {"k": "ory", "l": "Outer Y", "min": 0.2, "max": 1.1, "s": 0.01, "d": 0.90},
            {"k": "irx", "l": "Inner X", "min": 0.1, "max": 1.0, "s": 0.01, "d": 0.70},
            {"k": "iry", "l": "Inner Y", "min": 0.1, "max": 1.0, "s": 0.01, "d": 0.72},
            {"k": "iox", "l": "Inner offset X", "min": -0.5, "max": 0.5, "s": 0.01, "d": 0.18},
            {"k": "ioy", "l": "Inner offset Y", "min": -0.5, "max": 0.5, "s": 0.01, "d": 0.0},
        ],
        "draw": _crescent_outer,
        "draw_inner": _crescent_inner,
    },
    "lens": {
        "label": "Lens / Vesica", "group": "curve",
        "hint": "Two arcs meeting at points — Gothic window, eye, almond",
        "params": [
            {"k": "w", "l": "Width", "min": 0.1, "max": 1.1, "s": 0.01, "d": 0.65},
            {"k": "h", "l": "Height", "min": 0.2, "max": 1.2, "s": 0.01, "d": 0.92},
            {"k": "curve", "l": "Curvature", "min": 0.05, "max": 2.5, "s": 0.05, "d": 0.75},
            {"k": "lean", "l": "Lean", "min": -0.5, "max": 0.5, "s": 0.01, "d": 0.0},
        ],
        "draw": _lens,
    },
    "teardrop": {
        "label": "Teardrop", "group": "curve",
        "hint": "Botanical — petal, leaf, seed.  Flip inverts orientation in ring",
        "params": [
            {"k": "w", "l": "Width", "min": 0.1, "max": 1.1, "s": 0.01, "d": 0.68},
            {"k": "h", "l": "Height", "min": 0.2, "max": 1.2, "s": 0.01, "d": 0.90},
            {"k": "bulge", "l": "Bulge", "min": 0.1, "max": 1.2, "s": 0.01, "d": 0.65},
            {"k": "tip", "l": "Tip tight", "min": 0.0, "max": 1.0, "s": 0.01, "d": 0.55},
            {"k": "flip", "l": "Flip (0/1)", "min": 0, "max": 1, "s": 1, "d": 0},
        ],
        "draw": _teardrop,
    },
    "star": {
        "label": "Star", "group": "polygon",
        "hint": "N-pointed star — 3-12 points, inner radius controls fatness",
        "params": [
            {"k": "n", "l": "Points", "min": 3, "max": 12, "s": 1, "d": 5},
            {"k": "outer", "l": "Outer radius", "min": 0.2, "max": 1.1, "s": 0.01, "d": 0.88},
            {"k": "inner", "l": "Inner radius", "min": 0.05, "max": 0.9, "s": 0.01, "d": 0.42},
            {"k": "spin", "l": "Spin offset", "min": 0, "max": 1, "s": 0.01, "d": 0.0},
        ],
        "draw": _star,
    },
    "ogee": {
        "label": "Ogee Tile", "group": "curve",
        "hint": "S-curve sides — tiles interlock like a Gothic tracery repeat",
        "params": [
            {"k": "w", "l": "Width", "min": 0.2, "max": 1.1, "s": 0.01, "d": 0.92},
            {"k": "h", "l": "Height", "min": 0.2, "max": 1.1, "s": 0.01, "d": 0.92},
            {"k": "bulge", "l": "S-depth", "min": 0.0, "max": 0.9, "s": 0.01, "d": 0.38},
            {"k": "waist", "l": "Waist", "min": 0.0, "max": 0.8, "s": 0.01, "d": 0.0},
            {"k": "top", "l": "Top curve", "min": -0.5, "max": 0.5, "s": 0.01, "d": 0.0},
        ],
        "draw": _ogee,
    },
    "scale": {
        "label": "Fish Scale", "group": "curve",
        "hint": "Arch top bleeds into neighbor, creating layered scale effect",
        "params": [
            {"k": "w", "l": "Width", "min": 0.2, "max": 1.2, "s": 0.01, "d": 0.98},
            {"k": "h", "l": "Height", "min": 0.2, "max": 1.2, "s": 0.01, "d": 0.92},
            {"k": "arch", "l": "Arch depth", "min": 0.0, "max": 1.2, "s": 0.01, "d": 0.55},
            {"k": "tail", "l": "Tail round", "min": 0.0, "max": 0.6, "s": 0.01, "d": 0.0},
        ],
        "draw": _scale,
    },
    "rope_asym": {
        "label": "Asymm. Rope", "group": "organic",
        "hint": "Non-symmetric strand — skew + drift make it non-periodic",
        "params": [
            {"k": "thick", "l": "Thickness", "min": 0.1, "max": 0.95, "s": 0.01, "d": 0.58},
            {"k": "wave", "l": "Wave depth", "min": 0.0, "max": 0.9, "s": 0.01, "d": 0.42},
            {"k": "skew", "l": "Skew", "min": 0.0, "max": 0.95, "s": 0.01, "d": 0.62},
            {"k": "drift", "l": "Drift", "min": 0.0, "max": 0.8, "s": 0.01, "d": 0.12},
            {"k": "cap", "l": "Cap round", "min": 0.0, "max": 1.0, "s": 0.01, "d": 0.6},
        ],
        "draw": _rope_asym,
    },
    "hexagon": {
        "label": "Hexagon", "group": "polygon",
        "hint": "Flat-top or pointy-top hex — tiles can pack edge-to-edge",
        "params": [
            {"k": "r", "l": "Radius", "min": 0.2, "max": 1.0, "s": 0.01, "d": 0.82},
            {"k": "rot", "l": "Rotation", "min": 0, "max": 1, "s": 0.01, "d": 0.0},
            {"k": "squish", "l": "Squish", "min": 0.3, "max": 1.5, "s": 0.01, "d": 1.0},
        ],
        "draw": _hexagon,
    },
    "hyperbolic_wave": {
        "label": "Hyperbolic Wave", "group": "organic",
        "hint": "Non-repeating wave — hyperbolic drift makes each tile slightly different",
        "params": [
            {"k": "thick", "l": "Thickness", "min": 0.1, "max": 0.95, "s": 0.01, "d": 0.45},
            {"k": "wave", "l": "Wave amp", "min": 0.0, "max": 1.2, "s": 0.01, "d": 0.68},
            {"k": "skew", "l": "Skew", "min": 0.0, "max": 1.0, "s": 0.01, "d": 0.75},
            {"k": "drift", "l": "Hyperbolic drift", "min": 0.0, "max": 2.0, "s": 0.02, "d": 1.2},
            {"k": "chaos", "l": "Chaos", "min": 0.0, "max": 1.0, "s": 0.01, "d": 0.33},
        ],
        "draw": _hyperbolic_wave,
    },
    "braid_trenza": {
        "label": "Braid / Trenza", "group": "mosaic",
        "hint": "N-strand helical braid with over/under per tile",
        "params": [
            {"k": "n", "l": "Strands", "min": 2, "max": 5, "s": 1, "d": 3},
            {"k": "freq", "l": "Cycles/ring", "min": 0.5, "max": 8, "s": 0.25, "d": 2.5},
            {"k": "sw", "l": "Strand fill", "min": 0.3, "max": 0.98, "s": 0.01, "d": 0.82},
            {"k": "gap", "l": "Inter-gap", "min": 0, "max": 0.18, "s": 0.005, "d": 0.06},
            {"k": "lean", "l": "Lean", "min": -0.5, "max": 0.5, "s": 0.01, "d": 0.22},
            {"k": "round", "l": "End rounding", "min": 0, "max": 0.5, "s": 0.01, "d": 0.0},
        ],
        "draw": _hyperbolic_wave,  # placeholder bounding rect; real rendering is strand-based
    },
    "diamond_wave": {
        "label": "Diamond Wave", "group": "polygon",
        "hint": "CNC diamond with wave distortion and optional bevel — the dial-in shape",
        "params": [
            {"k": "density", "l": "Density", "min": 1, "max": 6, "s": 0.2, "d": 2.8},
            {"k": "wave", "l": "Wave amp", "min": 0, "max": 0.45, "s": 0.01, "d": 0.22},
            {"k": "lean", "l": "Lean", "min": -0.4, "max": 0.4, "s": 0.01, "d": 0.18},
            {"k": "bevel", "l": "Bevel", "min": 0, "max": 0.35, "s": 0.01, "d": 0.15},
        ],
        "draw": _draw_diamond_wave,
    },
    "chevron": {
        "label": "Stepped Chevron", "group": "polygon",
        "hint": "N-step interlocking zigzag — the chevron shape",
        "params": [
            {"k": "steps", "l": "Steps", "min": 1, "max": 6, "s": 1, "d": 3},
            {"k": "lean", "l": "Lean", "min": -0.3, "max": 0.3, "s": 0.01, "d": 0.0},
            {"k": "round", "l": "Round", "min": 0, "max": 0.2, "s": 0.01, "d": 0.0},
            {"k": "depth", "l": "Depth", "min": 0.3, "max": 1.5, "s": 0.05, "d": 1.0},
        ],
        "draw": _draw_chevron,
    },
    "petal": {
        "label": "Petal / Paisley", "group": "organic",
        "hint": "Curved quadrilateral — rotate around ring for mandala-like effects",
        "params": [
            {"k": "w", "l": "Width", "min": 0.1, "max": 1.1, "s": 0.01, "d": 0.72},
            {"k": "h", "l": "Height", "min": 0.2, "max": 1.2, "s": 0.01, "d": 0.92},
            {"k": "c1", "l": "Curve A", "min": -1, "max": 1, "s": 0.01, "d": 0.6},
            {"k": "c2", "l": "Curve B", "min": -1, "max": 1, "s": 0.01, "d": -0.3},
            {"k": "lean", "l": "Lean", "min": -0.6, "max": 0.6, "s": 0.01, "d": 0.2},
        ],
        "draw": _petal,
    },
}


# ─── Public API ────────────────────────────────────────────────────

def draw_shape(shape_key: str, W: float, H: float,
               params: dict | None = None, idx: int = 0) -> np.ndarray:
    """Return closed polygon as Nx2 numpy array for the named shape."""
    spec = SHAPES[shape_key]
    if params is None:
        params = {pd["k"]: pd["d"] for pd in spec["params"]}
    return spec["draw"](W, H, params, idx)


def default_params(shape_key: str) -> dict:
    """Return the default parameter dict for a shape."""
    return {pd["k"]: pd["d"] for pd in SHAPES[shape_key]["params"]}


def shape_keys() -> list[str]:
    """Return all registered shape keys."""
    return list(SHAPES.keys())
