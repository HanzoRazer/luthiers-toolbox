"""
Generative Rosette Explorer — fractal, voronoi, l-system plus diamond/chevron.

Ported from the Generative Rosette Explorer JSX.  Three exotic ring types
(fractal lace, voronoi web, l-system vine) alongside classic solid/stripe/
checker/diamond/chevron.  5 presets (lace/voronoi/vine/all/diamond).

    python -m app.cam.rosette.prototypes.generative_explorer_viewer
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, Wedge, Polygon
from matplotlib.collections import PatchCollection
from matplotlib.widgets import Slider, Button

from app.cam.rosette.prototypes.wood_materials import wood_by_id, hex_to_rgb_float, prng


# ── Shape helpers (diamond / chevron) ─────────────────────

def _diamond_shape(S, p, idx):
    hw = S / 2
    lx = S * p.get("lean", 0) * 0.5
    bv = S * p.get("bevel", 0) * 0.4
    density = p.get("density", 2.8)
    wave = p.get("wave", 0.28)
    amp = hw * wave * 0.55
    dy = max(-hw * 0.35, min(hw * 0.35,
          amp * math.sin((idx * 0.28 + density * 0.15) * math.pi)))
    if bv < 1.2:
        return np.array([
            [lx, -hw + dy], [hw, dy], [lx, hw + dy], [-hw, dy], [lx, -hw + dy]])
    pts = []
    N = 8
    def ew(t, ti):
        return bv * 0.25 * math.sin(t * math.pi * 2 + ti * 1.3 + idx * 0.3)
    pts.append([lx - bv * .5, -hw + bv * .5 + dy])
    pts.append([lx + bv * .5, -hw + bv * .5 + dy])
    for i in range(N + 1):
        t = i / N; pts.append([lx + t * (hw - lx), -hw + t * hw + ew(t, 0) + dy])
    pts.append([hw - bv * .5, -bv * .3 + dy]); pts.append([hw - bv * .5, bv * .3 + dy])
    for i in range(N + 1):
        t = i / N; pts.append([hw - t * (hw - lx), t * hw + ew(t, 1) + dy])
    pts.append([lx + bv * .5, hw - bv * .5 + dy]); pts.append([lx - bv * .5, hw - bv * .5 + dy])
    for i in range(N + 1):
        t = i / N; pts.append([lx - t * (hw + lx), hw - t * hw + ew(t, 2) + dy])
    pts.append([-hw + bv * .5, bv * .3 + dy]); pts.append([-hw + bv * .5, -bv * .3 + dy])
    for i in range(N + 1):
        t = i / N; pts.append([-hw + t * (hw + lx), -t * hw + ew(t, 3) + dy])
    pts.append(pts[0])
    return np.array(pts)


def _chevron_shape(W, H, p):
    n = max(1, round(p.get("steps", 3)))
    lx = W * p.get("lean", 0)
    sz = H / n
    hw = W / 2 * p.get("depth", 1)
    r_steps = []
    for i in range(n):
        y = -H / 2 + i * sz
        x = (hw if i % 2 == 0 else -hw) + lx * (i / n - 0.5) * 2
        r_steps.append([x, y]); r_steps.append([x, y + sz])
    l_steps = [[-x + lx * 2, y] for x, y in reversed(r_steps)]
    pts = [[lx, -H / 2]] + r_steps + [[lx, H / 2]] + l_steps + [[lx, -H / 2]]
    return np.array(pts)


def _transform(pts, cx, cy, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    R = np.array([[ca, -sa], [sa, ca]])
    return (pts @ R.T) + np.array([cx, cy])


# ── L-system expansion ───────────────────────────────────

_L_RULES = ["F+F+F", "F-F+F+F-F", "F+F-F-F+F", "F-F-F+F-F"]


def _expand_lsystem(axiom_idx, iterations):
    rule = _L_RULES[axiom_idx % 4]
    sys = "F"
    for _ in range(iterations):
        nx = []
        length = 0
        for c in sys:
            if c == "F":
                nx.append(rule)
                length += len(rule)
            else:
                nx.append(c)
                length += 1
            if length > 3600:
                break
        sys = "".join(nx)[:3600]
    return sys


def _turtle_points(sys, seg_len, start_angle):
    """Run turtle interpreter, return list of (x, y) line segments."""
    x, y, a = 0.0, 0.0, start_angle
    pts = [(x, y)]
    for c in sys:
        if c == "F":
            x += seg_len * math.cos(a)
            y += seg_len * math.sin(a)
            pts.append((x, y))
        elif c == "+":
            a += 0.45
        elif c == "-":
            a -= 0.45
    return pts


# ── Presets ───────────────────────────────────────────────

PRESETS = {
    "lace": {
        "name": "Fractal Lace", "col": "#9b6dff", "innerR": 40.8,
        "rings": [
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Ivory Line", "type": "stripe", "widthMm": 1.4,
             "matA": "bone", "matB": "ebony", "sw": 6},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Fractal Lace", "type": "fractal", "widthMm": 11,
             "matA": "mop", "matB": "abalone", "matC": "ebony",
             "N": 24, "gap": 0.88, "depth": 3, "spin": 0.15},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Ivory Line", "type": "stripe", "widthMm": 1.4,
             "matA": "bone", "matB": "ebony", "sw": 6},
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
    "voronoi": {
        "name": "Voronoi Web", "col": "#2dd4bf", "innerR": 40.8,
        "rings": [
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Checker", "type": "checker", "widthMm": 2.2,
             "matA": "ebony", "matB": "maple", "bw": 3},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Voronoi Web", "type": "voronoi", "widthMm": 11,
             "matA": "rosewood", "matB": "koa", "matC": "ebony",
             "seeds": 10, "jitter": 0.45},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Checker", "type": "checker", "widthMm": 1.8,
             "matA": "ebony", "matB": "maple", "bw": 3},
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
    "vine": {
        "name": "L-System Vine", "col": "#4ade80", "innerR": 40.8,
        "rings": [
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Dark Band", "type": "solid", "widthMm": 1.5, "mat": "walnut"},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "L-System Vine", "type": "lsystem", "widthMm": 11,
             "matA": "koa", "matB": "cedar", "matC": "ebony",
             "N": 24, "gap": 0.92, "axiom": 1, "iter": 4},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Dark Band", "type": "solid", "widthMm": 1.5, "mat": "walnut"},
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
    "all": {
        "name": "All Three", "col": "#f97316", "innerR": 40.8,
        "rings": [
            {"label": "Outer Bind", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Vine Band", "type": "lsystem", "widthMm": 5.5,
             "matA": "cedar", "matB": "spruce", "matC": "mahogany",
             "N": 18, "gap": 0.9, "axiom": 2, "iter": 3},
            {"label": "Divider", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Lace Band", "type": "fractal", "widthMm": 7,
             "matA": "bone", "matB": "mop", "matC": "rosewood",
             "N": 20, "gap": 0.85, "depth": 3, "spin": 0.2},
            {"label": "Divider", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Voronoi Band", "type": "voronoi", "widthMm": 6,
             "matA": "koa", "matB": "ovangkol", "matC": "ebony",
             "seeds": 9, "jitter": 0.4},
            {"label": "Inner Bind", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
    "diamond": {
        "name": "Diamond Wave", "col": "#c9a050", "innerR": 40.8,
        "rings": [
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Checker", "type": "checker", "widthMm": 3,
             "matA": "ebony", "matB": "maple", "bw": 3},
            {"label": "Border", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Diamond Wave", "type": "diamond", "widthMm": 9,
             "matA": "rosewood", "matB": "ebony", "matC": "maple",
             "altMode": "ab", "N": 20, "gap": 0.88, "density": 2.8,
             "wave": 0.28, "lean": 0.18, "bevel": 0.22, "showOut": True},
            {"label": "Border", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Checker", "type": "checker", "widthMm": 2.5,
             "matA": "ebony", "matB": "maple", "bw": 3},
            {"label": "Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
}

# Types that are "hero" rings (selectable for param editing)
_HERO_TYPES = {"fractal", "voronoi", "lsystem", "diamond", "chevron"}


# ── Rendering ─────────────────────────────────────────────

def render_rosette(ax, rings, inner_r):
    ax.clear()
    ax.set_aspect("equal")
    ax.set_facecolor("#080604")
    ax.axis("off")

    total_w = sum(r["widthMm"] for r in rings)
    outer_r = inner_r + total_w

    r_cur = inner_r
    bounds = []
    for ring in rings:
        iR = r_cur
        r_cur += ring["widthMm"]
        oR = r_cur
        bounds.append((iR, oR, (iR + oR) / 2, ring))

    patches = []
    colors = []
    edge_colors = []

    # Collect line-art for lsystem (drawn after PatchCollection)
    line_art = []

    for iR, oR, midR, ring in bounds:
        rtype = ring["type"]

        # ── SOLID ─────────────────────────────────────────
        if rtype == "solid":
            w = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(w)
            colors.append(hex_to_rgb_float(wood_by_id(ring.get("mat", "ebony"))["base"]))
            edge_colors.append((0, 0, 0, 0))

        # ── STRIPE ────────────────────────────────────────
        elif rtype == "stripe":
            matA, matB = ring.get("matA", "ebony"), ring.get("matB", "maple")
            sw = ring.get("sw", 4)
            n_stripes = max(8, 360 // sw)
            sa = 360 / n_stripes
            for si in range(n_stripes):
                wid = matA if (si // sw) % 2 == 0 else matB
                w = Wedge((0, 0), oR, si * sa, (si + 1) * sa, width=oR - iR)
                patches.append(w)
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                edge_colors.append((0, 0, 0, 0))

        # ── CHECKER ───────────────────────────────────────
        elif rtype == "checker":
            matA, matB = ring.get("matA", "ebony"), ring.get("matB", "maple")
            bw = ring.get("bw", 4)
            n_cols = max(8, 360 // bw)
            n_rows = max(2, round(ring["widthMm"] / (bw * 0.5)))
            ca = 360 / n_cols
            row_h = (oR - iR) / n_rows
            for ri in range(n_rows):
                for ci in range(n_cols):
                    wid = matA if (ri + ci) % 2 == 0 else matB
                    w = Wedge((0, 0), iR + (ri + 1) * row_h,
                              ci * ca, (ci + 1) * ca, width=row_h)
                    patches.append(w)
                    colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                    edge_colors.append((0, 0, 0, 0))

        # ── DIAMOND WAVE ──────────────────────────────────
        elif rtype == "diamond":
            matA = ring.get("matA", "rosewood")
            matB = ring.get("matB", "ebony")
            matC = ring.get("matC", "maple")
            alt = ring.get("altMode", "ab")
            N = ring.get("N", 20)
            gap = ring.get("gap", 0.88)
            show_out = ring.get("showOut", True)
            mats_list = [matA, matB, matC]
            p = {k: ring.get(k, d) for k, d in
                 [("density", 2.8), ("wave", 0.28), ("lean", 0.18), ("bevel", 0.22)]}
            ang_step = 2 * math.pi / N
            tH = (oR - iR) * gap
            tS = tH

            bg = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(bg); colors.append(hex_to_rgb_float(wood_by_id(matC)["base"]))
            edge_colors.append((0, 0, 0, 0))

            for i in range(N):
                mid_ang = (i + 0.5) * ang_step - math.pi / 2
                wid = mats_list[i % 2] if alt == "ab" else \
                      mats_list[i % 3] if alt == "abc" else matA
                pts = _diamond_shape(tS, p, i)
                cx = math.cos(mid_ang) * midR
                cy = math.sin(mid_ang) * midR
                world = _transform(pts, cx, cy, mid_ang + math.pi / 2)
                patches.append(Polygon(world, closed=True))
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                edge_colors.append((0, 0, 0, 0.55) if show_out else (0, 0, 0, 0))

        # ── CHEVRON ───────────────────────────────────────
        elif rtype == "chevron":
            matA = ring.get("matA", "maple")
            matB = ring.get("matB", "rosewood")
            matC = ring.get("matC", "ebony")
            alt = ring.get("altMode", "ab")
            N = ring.get("N", 16)
            gap = ring.get("gap", 0.92)
            show_out = ring.get("showOut", True)
            mats_list = [matA, matB, matC]
            p = {k: ring.get(k, d) for k, d in
                 [("steps", 3), ("lean", 0.0), ("round", 0.0), ("depth", 1.0)]}
            ang_step = 2 * math.pi / N
            tH = (oR - iR) * gap
            tW = midR * ang_step * gap

            bg = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(bg); colors.append(hex_to_rgb_float(wood_by_id(matC)["base"]))
            edge_colors.append((0, 0, 0, 0))

            for i in range(N):
                mid_ang = (i + 0.5) * ang_step - math.pi / 2
                wid = mats_list[i % 2] if alt == "ab" else \
                      mats_list[i % 3] if alt == "abc" else matA
                pts = _chevron_shape(tW, tH, p)
                cx = math.cos(mid_ang) * midR
                cy = math.sin(mid_ang) * midR
                world = _transform(pts, cx, cy, mid_ang + math.pi / 2)
                patches.append(Polygon(world, closed=True))
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                edge_colors.append((0, 0, 0, 0.50) if show_out else (0, 0, 0, 0))

        # ── FRACTAL LACE ─────────────────────────────────
        elif rtype == "fractal":
            N = ring.get("N", 24)
            gap = ring.get("gap", 0.88)
            dep = ring.get("depth", 3)
            spin = ring.get("spin", 0.15)
            matA = ring.get("matA", "mop")
            matB = ring.get("matB", "abalone")
            matC = ring.get("matC", "ebony")
            bg_wood = wood_by_id(matC)
            mats = [wood_by_id(matA), wood_by_id(matB)]
            ang_step = 2 * math.pi / N
            tH = (oR - iR) * gap

            # Background
            bg = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(bg); colors.append(hex_to_rgb_float(bg_wood["base"]))
            edge_colors.append((0, 0, 0, 0))

            # Recursive ellipse tree per tile
            def _fractal_ellipses(cx, cy, r, d, tile_idx):
                if r < 0.7:
                    return
                wd = mats[tile_idx % 2] if d % 2 == 0 else bg_wood
                ell = Ellipse((cx, cy), r * 1.76, r * 1.24, angle=0)
                patches.append(ell)
                colors.append(hex_to_rgb_float(wd["base"]))
                edge_colors.append(hex_to_rgb_float(wd.get("hi", wd["base"])) + (0.6,))
                if d < dep:
                    a2 = (tile_idx * 0.11 + spin) * math.pi * 2
                    s = r * 0.54
                    _fractal_ellipses(cx + s * math.cos(a2), cy + s * math.sin(a2), s, d + 1, tile_idx)
                    _fractal_ellipses(cx - s * math.cos(a2), cy - s * math.sin(a2), s, d + 1, tile_idx)

            for i in range(N):
                mid_ang = (i + 0.5) * ang_step - math.pi / 2
                tcx = math.cos(mid_ang) * midR
                tcy = math.sin(mid_ang) * midR
                _fractal_ellipses(tcx, tcy, tH / 2, 0, i)

        # ── VORONOI WEB ──────────────────────────────────
        elif rtype == "voronoi":
            n_seeds = ring.get("seeds", 10)
            jitter = ring.get("jitter", 0.45)
            matA = ring.get("matA", "rosewood")
            matB = ring.get("matB", "koa")
            matC = ring.get("matC", "ebony")
            bg_wood = wood_by_id(matC)
            cell_mats = [wood_by_id(matA), wood_by_id(matB)]

            # Generate seed points in annular band
            rng_state = (hash(str(ring.get("label", ""))) * 7919 + 1) & 0xFFFFFFFF
            def _vrng():
                nonlocal rng_state
                rng_state = (rng_state * 1664525 + 1013904223) & 0xFFFFFFFF
                return rng_state / 0x100000000

            seed_pts = []
            for si in range(n_seeds):
                a = si / n_seeds * math.pi * 2 + si * 0.41
                r = iR + (oR - iR) * (0.12 + _vrng() * 0.76)
                sx = math.cos(a) * r + (_vrng() - 0.5) * jitter * (oR - iR) * 0.55
                sy = math.sin(a) * r + (_vrng() - 0.5) * jitter * (oR - iR) * 0.55
                seed_pts.append((sx, sy))

            # Vectorized Voronoi via pixel sampling, rendered as
            # angular wedge approximation for speed
            n_ang = 360
            n_rad = max(4, round((oR - iR) / 0.5))
            ang_arr = np.linspace(0, 2 * math.pi, n_ang, endpoint=False)
            rad_arr = np.linspace(iR, oR, n_rad)
            for ri in range(n_rad - 1):
                for ai in range(n_ang):
                    r_mid = (rad_arr[ri] + rad_arr[ri + 1]) / 2
                    a_mid = ang_arr[ai]
                    px = math.cos(a_mid) * r_mid
                    py = math.sin(a_mid) * r_mid
                    d1, d2, cl = 1e18, 1e18, 0
                    for si, (sx, sy) in enumerate(seed_pts):
                        sd = (px - sx) ** 2 + (py - sy) ** 2
                        if sd < d1:
                            d2 = d1; cl = si; d1 = sd
                        elif sd < d2:
                            d2 = sd
                    edge = math.sqrt(d2) - math.sqrt(d1)
                    wd = bg_wood if edge < 0.8 else cell_mats[cl % 2]
                    a_deg_start = math.degrees(ang_arr[ai])
                    a_deg_end = a_deg_start + 360 / n_ang
                    w = Wedge((0, 0), rad_arr[ri + 1],
                              a_deg_start, a_deg_end,
                              width=rad_arr[ri + 1] - rad_arr[ri])
                    patches.append(w)
                    colors.append(hex_to_rgb_float(wd["base"]))
                    edge_colors.append((0, 0, 0, 0))

        # ── L-SYSTEM VINE ─────────────────────────────────
        elif rtype == "lsystem":
            N = ring.get("N", 24)
            gap = ring.get("gap", 0.92)
            axiom = ring.get("axiom", 1)
            itr = ring.get("iter", 4)
            matA = ring.get("matA", "koa")
            matB = ring.get("matB", "cedar")
            matC = ring.get("matC", "ebony")
            bg_wood = wood_by_id(matC)
            ang_step = 2 * math.pi / N
            tH = (oR - iR) * gap

            # Background
            bg = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(bg); colors.append(hex_to_rgb_float(bg_wood["base"]))
            edge_colors.append((0, 0, 0, 0))

            # Expand L-system string once
            sys = _expand_lsystem(axiom, itr)
            seg_len = min(midR * ang_step * gap, tH) / max(math.sqrt(len(sys)) * 0.72, 3)

            for i in range(N):
                mid_ang = (i + 0.5) * ang_step - math.pi / 2
                tcx = math.cos(mid_ang) * midR
                tcy = math.sin(mid_ang) * midR

                wd = wood_by_id(matA if i % 2 == 0 else matB)
                pts = _turtle_points(sys, seg_len, i * 0.37)
                if len(pts) > 1:
                    # Transform turtle path into world space
                    arr = np.array(pts)
                    world = _transform(arr, tcx, tcy, mid_ang + math.pi / 2)
                    line_art.append({
                        "pts": world,
                        "bg_color": hex_to_rgb_float(bg_wood["grain"]),
                        "fg_color": hex_to_rgb_float(wd.get("hi", wd["base"])),
                    })

    # ── Draw patches ──────────────────────────────────────
    if patches:
        pc = PatchCollection(patches, facecolors=colors,
                             edgecolors=edge_colors, linewidths=0.4)
        ax.add_collection(pc)

    # ── Draw L-system vine lines ──────────────────────────
    for la in line_art:
        xs, ys = la["pts"][:, 0], la["pts"][:, 1]
        ax.plot(xs, ys, color=la["bg_color"] + (0.55,), linewidth=2.0,
                solid_capstyle="round", solid_joinstyle="round")
        ax.plot(xs, ys, color=la["fg_color"] + (0.9,), linewidth=0.9,
                solid_capstyle="round", solid_joinstyle="round")

    # Soundhole + outer edge
    ax.add_patch(Circle((0, 0), inner_r, facecolor="#0a0806",
                        edgecolor="#c9a96e99", linewidth=1.2))
    ax.add_patch(Circle((0, 0), outer_r, fill=False,
                        edgecolor="#c9a96e20", linewidth=1.5))

    lim = outer_r + 4
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.figure.canvas.draw_idle()


# ── Interactive viewer ────────────────────────────────────

# Type-specific slider definitions: (key, label, lo, hi, step, default)
_SLIDER_DEFS = {
    "fractal": [
        ("N",     "Tiles N",   8,  40, 2,   24),
        ("depth", "Recursion", 1,  4,  1,   3),
        ("spin",  "Spin",      0,  1,  0.05, 0.15),
        ("gap",   "Gap",       0.5, 1.1, 0.02, 0.88),
    ],
    "voronoi": [
        ("seeds", "Seeds",  3,  18, 1,   10),
        ("jitter", "Jitter", 0, 1.2, 0.05, 0.45),
    ],
    "lsystem": [
        ("N",    "Tiles N",    8, 36, 2,   24),
        ("iter", "Iterations", 1, 6,  1,   4),
        ("gap",  "Gap",        0.5, 1.1, 0.02, 0.92),
    ],
    "diamond": [
        ("N",       "Tiles N", 8,  36, 2,   20),
        ("wave",    "Wave",    0,  0.45, 0.01, 0.28),
        ("lean",    "Lean",    -0.4, 0.4, 0.01, 0.18),
        ("bevel",   "Bevel",   0, 0.35, 0.01, 0.22),
    ],
    "chevron": [
        ("N",     "Tiles N", 8,  36, 2,   16),
        ("steps", "Steps",   1,  6,  1,   3),
        ("lean",  "Lean",    -0.4, 0.4, 0.01, 0.0),
        ("depth", "Depth",   0.3, 1.5, 0.05, 1.0),
    ],
}
_SLIDER_DEFS["fractal"].insert(0, ("widthMm", "Width mm", 3, 16, 0.5, 11))
_SLIDER_DEFS["voronoi"].insert(0, ("widthMm", "Width mm", 3, 16, 0.5, 11))
_SLIDER_DEFS["lsystem"].insert(0, ("widthMm", "Width mm", 3, 16, 0.5, 11))
_SLIDER_DEFS["diamond"].insert(0, ("widthMm", "Width mm", 3, 18, 0.5, 9))
_SLIDER_DEFS["chevron"].insert(0, ("widthMm", "Width mm", 3, 18, 0.5, 9))


class GenerativeExplorerViewer:
    def __init__(self):
        self.preset_key = "lace"
        self._load_preset_data("lace")

        self.fig = plt.figure(figsize=(14, 9), facecolor="#080604")
        self.fig.canvas.manager.set_window_title(
            "Generative Rosette Explorer — The Production Shop")

        # Main wheel
        self.ax = self.fig.add_axes([0.01, 0.06, 0.52, 0.88])

        # ── Preset buttons ───
        pk = list(PRESETS.keys())
        self.preset_btns = []
        bx = 0.56
        for i, key in enumerate(pk):
            ax_btn = self.fig.add_axes([bx + i * 0.088, 0.93, 0.085, 0.04])
            btn = Button(ax_btn, PRESETS[key]["name"], color="#0a0806",
                         hovercolor="#1a1208")
            btn.label.set_fontsize(6.5)
            btn.label.set_color(PRESETS[key]["col"])
            btn.on_clicked(lambda _, k=key: self._load_preset(k))
            self.preset_btns.append(btn)

        # ── Sliders (built for initial hero ring) ───
        self._hero_idx = self._find_hero_index()
        self.sliders = {}
        self._slider_axes = {}
        self._build_sliders()

        # ── Info panel ───
        self._info_ax = self.fig.add_axes([0.80, 0.06, 0.19, 0.82], facecolor="#080604")
        self._info_ax.axis("off")

        self._render()

    def _find_hero_index(self):
        for i, r in enumerate(self.rings):
            if r["type"] in _HERO_TYPES:
                return i
        return None

    def _build_sliders(self):
        # Remove old slider axes
        for ax_sl in self._slider_axes.values():
            ax_sl.remove()
        self.sliders.clear()
        self._slider_axes.clear()

        hero = self.rings[self._hero_idx] if self._hero_idx is not None else {}
        htype = hero.get("type", "fractal")
        defs = _SLIDER_DEFS.get(htype, [])

        sx, sw = 0.56, 0.22
        y_pos = 0.86
        for key, label, lo, hi, step, default in defs:
            ax_sl = self.fig.add_axes([sx, y_pos, sw, 0.022])
            init = hero.get(key, default)
            sl = Slider(ax_sl, label, lo, hi, valinit=init,
                        valstep=step, color="#c9a96e")
            sl.on_changed(self._on_slider)
            sl.label.set_fontsize(7)
            sl.valtext.set_fontsize(7)
            self.sliders[key] = sl
            self._slider_axes[key] = ax_sl
            y_pos -= 0.05

    def _load_preset_data(self, key):
        pr = PRESETS[key]
        self.inner_r = pr["innerR"]
        self.rings = [dict(r) for r in pr["rings"]]
        self.preset_key = key

    def _load_preset(self, key):
        self._load_preset_data(key)
        self._hero_idx = self._find_hero_index()
        self._build_sliders()
        self._render()

    def _on_slider(self, _):
        if self._hero_idx is None:
            return
        hero = self.rings[self._hero_idx]
        for k, sl in self.sliders.items():
            if k in hero:
                hero[k] = int(sl.val) if k in ("N", "depth", "seeds", "iter", "steps", "axiom") else sl.val
        self._render()

    def _update_info(self):
        ax = self._info_ax
        ax.clear(); ax.axis("off")
        total = sum(r["widthMm"] for r in self.rings)
        outer = self.inner_r + total
        pr = PRESETS[self.preset_key]

        ax.text(0, 0.97, pr["name"], fontsize=10, color=pr["col"],
                fontfamily="monospace", va="top", weight="bold")
        tc = {"fractal": "#9b6dff", "voronoi": "#2dd4bf", "lsystem": "#4ade80",
              "diamond": "#c9a050", "chevron": "#88b868"}
        y = 0.88
        for r in self.rings:
            col = tc.get(r["type"], "#5a4020")
            marker = {"fractal": "✦", "voronoi": "◎", "lsystem": "⌥",
                      "diamond": "◈", "chevron": "◇"}.get(r["type"], " ")
            ax.text(0, y, f"{marker} {r.get('label', r['type'])}",
                    fontsize=7, color=col, fontfamily="monospace", va="top")
            ax.text(0.9, y, f"{r['widthMm']:.1f}",
                    fontsize=6.5, color="#4a3010", fontfamily="monospace",
                    va="top", ha="right")
            y -= 0.058
        y -= 0.03
        ax.text(0, y, f"SH  r = {self.inner_r:.1f} mm",
                fontsize=8, color="#c9a96e", fontfamily="monospace", va="top")
        ax.text(0, y - 0.05, f"Band  = {total:.1f} mm",
                fontsize=8, color="#e8c87a", fontfamily="monospace", va="top")
        ax.text(0, y - 0.10, f"Outer = {outer:.1f} mm",
                fontsize=8, color="#c9a96e", fontfamily="monospace", va="top")

    def _render(self):
        render_rosette(self.ax, self.rings, self.inner_r)
        self._update_info()
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def main():
    viewer = GenerativeExplorerViewer()
    viewer.show()


if __name__ == "__main__":
    main()
