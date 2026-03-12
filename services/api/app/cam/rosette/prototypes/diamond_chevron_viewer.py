"""
Diamond · Chevron Rosette Viewer — two hero shapes in one viewer.

Ported from diamond-chevron-rosette.jsx.  Multi-ring layout with solid,
stripe, checker, diamond wave, and stepped chevron ring types.
5 presets (dial_in / chev3 / combined / pearl / chev_lean).

    python -m app.cam.rosette.prototypes.diamond_chevron_viewer
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Wedge
from matplotlib.collections import PatchCollection
from matplotlib.widgets import Slider, Button

from app.cam.rosette.prototypes.wood_materials import wood_by_id, hex_to_rgb_float


# ── Diamond wave shape ────────────────────────────────────

def diamond_shape(S, p, idx):
    """Return Nx2 closed polygon for a diamond wave tile.
    S is the square tile side (used as both W and H to keep diamond proportions).
    """
    hw = S / 2
    amp = hw * p["wave"] * 0.55
    lx = S * p["lean"] * 0.5
    bv = S * p["bevel"] * 0.4
    density = p.get("density", 2.8)
    dy = max(-hw * 0.35, min(hw * 0.35,
          amp * math.sin((idx * 0.28 + density * 0.15) * math.pi)))

    pts = []
    if bv < 1.2:
        pts = [
            [lx, -hw + dy],
            [hw, 0 + dy],
            [lx, hw + dy],
            [-hw, 0 + dy],
            [lx, -hw + dy],
        ]
    else:
        N = 8

        def ew(t, ti):
            return bv * 0.25 * math.sin(t * math.pi * 2 + ti * 1.3 + idx * 0.3)

        # Top tip
        pts.append([lx - bv * 0.5, -hw + bv * 0.5 + dy])
        pts.append([lx + bv * 0.5, -hw + bv * 0.5 + dy])
        # Top-right edge
        for i in range(N + 1):
            t = i / N
            pts.append([lx + t * (hw - lx), -hw + t * hw + ew(t, 0) + dy])
        # Right tip
        pts.append([hw - bv * 0.5, -bv * 0.3 + dy])
        pts.append([hw - bv * 0.5, bv * 0.3 + dy])
        # Bottom-right edge
        for i in range(N + 1):
            t = i / N
            pts.append([hw - t * (hw - lx), t * hw + ew(t, 1) + dy])
        # Bottom tip
        pts.append([lx + bv * 0.5, hw - bv * 0.5 + dy])
        pts.append([lx - bv * 0.5, hw - bv * 0.5 + dy])
        # Bottom-left edge
        for i in range(N + 1):
            t = i / N
            pts.append([lx - t * (hw + lx), hw - t * hw + ew(t, 2) + dy])
        # Left tip
        pts.append([-hw + bv * 0.5, bv * 0.3 + dy])
        pts.append([-hw + bv * 0.5, -bv * 0.3 + dy])
        # Top-left edge
        for i in range(N + 1):
            t = i / N
            pts.append([-hw + t * (hw + lx), -t * hw + ew(t, 3) + dy])
        pts.append(pts[0])

    return np.array(pts)


# ── Stepped chevron shape ─────────────────────────────────

def chevron_shape(W, H, p):
    """Return Nx2 closed polygon for a stepped chevron tile."""
    n = max(1, round(p["steps"]))
    lx = W * p["lean"]
    sz = H / n
    hw = W / 2 * p["depth"]

    r_steps = []
    for i in range(n):
        y = -H / 2 + i * sz
        x = (hw if i % 2 == 0 else -hw) + lx * (i / n - 0.5) * 2
        r_steps.append([x, y])
        r_steps.append([x, y + sz])

    l_steps = [[-x + lx * 2, y] for x, y in reversed(r_steps)]

    pts = [[lx, -H / 2]]
    pts.extend(r_steps)
    pts.append([lx, H / 2])
    pts.extend(l_steps)
    pts.append([lx, -H / 2])

    return np.array(pts)


# ── Presets ───────────────────────────────────────────────

PRESETS = {
    "dial_in": {
        "name": "Dial-In (DiamWave)",
        "innerR": 40.8,
        "rings": [
            {"label": "Inner Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Maple Frieze", "type": "checker", "widthMm": 3.2,
             "matA": "ebony", "matB": "maple", "bw": 3},
            {"label": "Border", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Diamond Wave", "type": "diamond", "widthMm": 9.0,
             "matA": "rosewood", "matB": "ebony", "matC": "maple", "altMode": "ab",
             "N": 20, "gap": 0.88, "density": 2.8, "wave": 0.28, "lean": 0.18,
             "bevel": 0.22, "showOut": True},
            {"label": "Border", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Maple Frieze", "type": "checker", "widthMm": 2.5,
             "matA": "ebony", "matB": "maple", "bw": 3},
            {"label": "Outer Binding", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
    "chev3": {
        "name": "Chevron 3-Step",
        "innerR": 40.8,
        "rings": [
            {"label": "Ebony Bind", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Koa Stripe", "type": "stripe", "widthMm": 2.0,
             "matA": "koa", "matB": "ebony", "sw": 5},
            {"label": "Border", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Stepped Chev", "type": "chevron", "widthMm": 9.0,
             "matA": "maple", "matB": "rosewood", "matC": "ebony", "altMode": "ab",
             "N": 16, "gap": 0.92, "steps": 3, "lean": 0.0, "round": 0.0,
             "depth": 1.0, "showOut": True},
            {"label": "Border", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Koa Stripe", "type": "stripe", "widthMm": 2.0,
             "matA": "koa", "matB": "ebony", "sw": 5},
            {"label": "Ebony Bind", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
    "combined": {
        "name": "Combined (Both)",
        "innerR": 40.8,
        "rings": [
            {"label": "Ebony Bind", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
            {"label": "Bone Stripe", "type": "stripe", "widthMm": 1.5,
             "matA": "bone", "matB": "ebony", "sw": 4},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Chev 3-Step", "type": "chevron", "widthMm": 5.5,
             "matA": "maple", "matB": "rosewood", "matC": "ebony", "altMode": "ab",
             "N": 18, "gap": 0.90, "steps": 3, "lean": 0.08, "round": 0.04,
             "depth": 0.95, "showOut": True},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Diamond Wave", "type": "diamond", "widthMm": 7.5,
             "matA": "koa", "matB": "ebony", "matC": "maple", "altMode": "ab",
             "N": 22, "gap": 0.88, "density": 2.8, "wave": 0.24, "lean": 0.16,
             "bevel": 0.18, "showOut": False},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Bone Stripe", "type": "stripe", "widthMm": 1.5,
             "matA": "bone", "matB": "ebony", "sw": 4},
            {"label": "Outer Bind", "type": "solid", "widthMm": 0.8, "mat": "ebony"},
        ],
    },
    "pearl": {
        "name": "Pearl Diamond",
        "innerR": 40.8,
        "rings": [
            {"label": "Ebony Bind", "type": "solid", "widthMm": 1.0, "mat": "ebony"},
            {"label": "MOP Line", "type": "stripe", "widthMm": 1.8,
             "matA": "mop", "matB": "ebony", "sw": 6},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Diam Flow", "type": "diamond", "widthMm": 9.5,
             "matA": "mop", "matB": "abalone", "matC": "ebony", "altMode": "ab",
             "N": 24, "gap": 0.92, "density": 1.8, "wave": 0.38, "lean": 0.22,
             "bevel": 0.28, "showOut": False},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Abalone Line", "type": "stripe", "widthMm": 1.8,
             "matA": "abalone", "matB": "ebony", "sw": 6},
            {"label": "Ebony Bind", "type": "solid", "widthMm": 1.0, "mat": "ebony"},
        ],
    },
    "chev_lean": {
        "name": "Chevron Lean (Koa)",
        "innerR": 40.8,
        "rings": [
            {"label": "Walnut Bind", "type": "solid", "widthMm": 0.8, "mat": "walnut"},
            {"label": "Checker", "type": "checker", "widthMm": 2.8,
             "matA": "walnut", "matB": "maple", "bw": 4},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Chev Lean", "type": "chevron", "widthMm": 9.5,
             "matA": "koa", "matB": "maple", "matC": "walnut", "altMode": "abc",
             "N": 24, "gap": 0.88, "steps": 2, "lean": 0.22, "round": 0.10,
             "depth": 1.1, "showOut": True},
            {"label": "Border", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Checker", "type": "checker", "widthMm": 2.2,
             "matA": "walnut", "matB": "maple", "bw": 4},
            {"label": "Walnut Bind", "type": "solid", "widthMm": 0.8, "mat": "walnut"},
        ],
    },
}


# ── Transform helper ──────────────────────────────────────

def _transform(pts, cx, cy, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    R = np.array([[ca, -sa], [sa, ca]])
    return (pts @ R.T) + np.array([cx, cy])


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

    for iR, oR, midR, ring in bounds:
        rtype = ring["type"]

        if rtype == "solid":
            w = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(w)
            colors.append(hex_to_rgb_float(wood_by_id(ring.get("mat", "ebony"))["base"]))
            edge_colors.append((0, 0, 0, 0))

        elif rtype == "stripe":
            matA, matB = ring.get("matA", "ebony"), ring.get("matB", "maple")
            sw = ring.get("sw", 4)
            n_stripes = max(8, 360 // sw)
            stripe_a = 360 / n_stripes
            for si in range(n_stripes):
                wid = matA if (si // sw) % 2 == 0 else matB
                w = Wedge((0, 0), oR, si * stripe_a, (si + 1) * stripe_a, width=oR - iR)
                patches.append(w)
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                edge_colors.append((0, 0, 0, 0))

        elif rtype == "checker":
            matA, matB = ring.get("matA", "ebony"), ring.get("matB", "maple")
            bw = ring.get("bw", 4)
            n_cols = max(8, 360 // bw)
            n_rows = max(2, round(ring["widthMm"] / (bw * 0.5)))
            col_a = 360 / n_cols
            row_h = (oR - iR) / n_rows
            for ri in range(n_rows):
                for ci in range(n_cols):
                    wid = matA if (ri + ci) % 2 == 0 else matB
                    w = Wedge((0, 0), iR + (ri + 1) * row_h,
                              ci * col_a, (ci + 1) * col_a, width=row_h)
                    patches.append(w)
                    colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                    edge_colors.append((0, 0, 0, 0))

        elif rtype == "diamond":
            matA = ring.get("matA", "rosewood")
            matB = ring.get("matB", "ebony")
            matC = ring.get("matC", "maple")
            alt = ring.get("altMode", "ab")
            N = ring.get("N", 20)
            gap = ring.get("gap", 0.88)
            show_out = ring.get("showOut", True)
            mats_list = [matA, matB, matC]

            p = {
                "density": ring.get("density", 2.8),
                "wave": ring.get("wave", 0.28),
                "lean": ring.get("lean", 0.18),
                "bevel": ring.get("bevel", 0.22),
            }
            ang_step = 2 * math.pi / N
            tH = (oR - iR) * gap
            tS = tH  # Square tile for diamonds

            # Background fill
            bg_wedge = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(bg_wedge)
            colors.append(hex_to_rgb_float(wood_by_id(matC)["base"]))
            edge_colors.append((0, 0, 0, 0))

            for i in range(N):
                mid_ang = (i + 0.5) * ang_step - math.pi / 2
                if alt == "ab":
                    wid = mats_list[i % 2]
                elif alt == "abc":
                    wid = mats_list[i % 3]
                else:
                    wid = matA

                pts = diamond_shape(tS, p, i)
                cx = math.cos(mid_ang) * midR
                cy = math.sin(mid_ang) * midR
                world = _transform(pts, cx, cy, mid_ang + math.pi / 2)

                poly = Polygon(world, closed=True)
                patches.append(poly)
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                ec = (0, 0, 0, 0.55) if show_out else (0, 0, 0, 0)
                edge_colors.append(ec)

        elif rtype == "chevron":
            matA = ring.get("matA", "maple")
            matB = ring.get("matB", "rosewood")
            matC = ring.get("matC", "ebony")
            alt = ring.get("altMode", "ab")
            N = ring.get("N", 16)
            gap = ring.get("gap", 0.92)
            show_out = ring.get("showOut", True)
            mats_list = [matA, matB, matC]

            p = {
                "steps": ring.get("steps", 3),
                "lean": ring.get("lean", 0.0),
                "round": ring.get("round", 0.0),
                "depth": ring.get("depth", 1.0),
            }
            ang_step = 2 * math.pi / N
            tH = (oR - iR) * gap
            tW = midR * ang_step * gap

            # Background fill
            bg_wedge = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(bg_wedge)
            colors.append(hex_to_rgb_float(wood_by_id(matC)["base"]))
            edge_colors.append((0, 0, 0, 0))

            for i in range(N):
                mid_ang = (i + 0.5) * ang_step - math.pi / 2
                if alt == "ab":
                    wid = mats_list[i % 2]
                elif alt == "abc":
                    wid = mats_list[i % 3]
                else:
                    wid = matA

                pts = chevron_shape(tW, tH, p)
                cx = math.cos(mid_ang) * midR
                cy = math.sin(mid_ang) * midR
                world = _transform(pts, cx, cy, mid_ang + math.pi / 2)

                poly = Polygon(world, closed=True)
                patches.append(poly)
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                ec = (0, 0, 0, 0.50) if show_out else (0, 0, 0, 0)
                edge_colors.append(ec)

    if patches:
        pc = PatchCollection(patches, facecolors=colors,
                             edgecolors=edge_colors, linewidths=0.5)
        ax.add_collection(pc)

    # Soundhole
    ax.add_patch(Circle((0, 0), inner_r, facecolor="#0a0806",
                        edgecolor="#c9a96e55", linewidth=1.2))
    # Outer edge
    ax.add_patch(Circle((0, 0), outer_r, fill=False,
                        edgecolor="#c9a96e20", linewidth=1.5))

    lim = outer_r + 4
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.figure.canvas.draw_idle()


# ── Interactive viewer ────────────────────────────────────

class DiamondChevronViewer:
    def __init__(self):
        self.preset_key = "dial_in"
        self._load_preset_data("dial_in")

        self.fig = plt.figure(figsize=(14, 9), facecolor="#080604")
        self.fig.canvas.manager.set_window_title(
            "Diamond · Chevron Rosette — The Production Shop")

        # Main wheel
        self.ax = self.fig.add_axes([0.02, 0.08, 0.50, 0.85])

        # ── Find the hero ring to control ───
        self._hero_idx = self._find_hero_index()
        hero = self.rings[self._hero_idx] if self._hero_idx is not None else {}

        # ── Build sliders depending on hero type ───
        sx = 0.56
        sw = 0.20
        self.sliders = {}
        self._slider_axes = {}

        # Common sliders
        specs = [
            ("N", "Tiles N", 6, 48, 1, hero.get("N", 20)),
            ("gap", "Gap fill", 0.5, 1.15, 0.01, hero.get("gap", 0.88)),
            ("widthMm", "Width mm", 3, 18, 0.5, hero.get("widthMm", 9)),
        ]

        hero_type = hero.get("type", "diamond")
        if hero_type == "diamond":
            specs += [
                ("density", "Density", 0.5, 6.0, 0.2, hero.get("density", 2.8)),
                ("wave", "Wave amp", 0.0, 0.45, 0.01, hero.get("wave", 0.28)),
                ("lean", "Lean", -0.4, 0.4, 0.01, hero.get("lean", 0.18)),
                ("bevel", "Bevel", 0.0, 0.35, 0.01, hero.get("bevel", 0.22)),
            ]
        elif hero_type == "chevron":
            specs += [
                ("steps", "Steps", 1, 6, 1, hero.get("steps", 3)),
                ("lean", "Lean", -0.4, 0.4, 0.01, hero.get("lean", 0.0)),
                ("depth", "Depth", 0.3, 1.5, 0.05, hero.get("depth", 1.0)),
            ]

        y_pos = 0.90
        for key, label, lo, hi, step, init in specs:
            ax_sl = self.fig.add_axes([sx, y_pos, sw, 0.02])
            sl = Slider(ax_sl, label, lo, hi, valinit=init,
                        valstep=step, color="#c9a96e")
            sl.on_changed(self._on_slider)
            sl.label.set_fontsize(7)
            sl.valtext.set_fontsize(7)
            self.sliders[key] = sl
            self._slider_axes[key] = ax_sl
            y_pos -= 0.05

        # ── Preset buttons ───
        self.preset_btns = []
        pk = list(PRESETS.keys())
        for i, key in enumerate(pk):
            ax_btn = self.fig.add_axes([sx + i * 0.085, y_pos - 0.04, 0.08, 0.035])
            btn = Button(ax_btn, PRESETS[key]["name"], color="#0a0806",
                         hovercolor="#1a1208")
            btn.label.set_fontsize(6)
            btn.label.set_color("#c9a96e")
            btn.on_clicked(lambda _, k=key: self._load_preset(k))
            self.preset_btns.append(btn)

        # ── Ring info panel ───
        self._info_ax = self.fig.add_axes([0.80, 0.08, 0.19, 0.82], facecolor="#080604")
        self._info_ax.axis("off")

        self._render()

    def _find_hero_index(self):
        for i, r in enumerate(self.rings):
            if r["type"] in ("diamond", "chevron"):
                return i
        return None

    def _load_preset_data(self, key):
        pr = PRESETS[key]
        self.inner_r = pr["innerR"]
        self.rings = [dict(r) for r in pr["rings"]]
        self.preset_key = key

    def _load_preset(self, key):
        self._load_preset_data(key)
        self._hero_idx = self._find_hero_index()
        hero = self.rings[self._hero_idx] if self._hero_idx is not None else {}

        # Rebuild sliders entirely for the new hero type
        # (simpler to just update values for common keys)
        for k, sl in self.sliders.items():
            if k in hero:
                sl.set_val(hero[k])
        self._render()

    def _on_slider(self, _):
        if self._hero_idx is None:
            return
        hero = self.rings[self._hero_idx]
        for k, sl in self.sliders.items():
            if k in hero:
                hero[k] = int(sl.val) if k in ("N", "steps") else sl.val
        self._render()

    def _update_info(self):
        ax = self._info_ax
        ax.clear()
        ax.axis("off")
        total = sum(r["widthMm"] for r in self.rings)
        outer = self.inner_r + total

        ax.text(0, 0.97, PRESETS[self.preset_key]["name"],
                fontsize=10, color="#e8c87a", fontfamily="monospace",
                va="top", weight="bold")
        y = 0.90
        for r in self.rings:
            label = r.get("label", r["type"])
            accent = "#c9a050" if r["type"] == "diamond" else \
                     "#88b868" if r["type"] == "chevron" else "#7a5c2e"
            marker = "◈" if r["type"] == "diamond" else \
                     "◇" if r["type"] == "chevron" else " "
            ax.text(0, y, f"{marker} {label}",
                    fontsize=7.5, color=accent, fontfamily="monospace", va="top")
            ax.text(0.85, y, f"{r['widthMm']:.1f}",
                    fontsize=7, color="#4a3010", fontfamily="monospace",
                    va="top", ha="right")
            y -= 0.065

        y -= 0.04
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
    viewer = DiamondChevronViewer()
    viewer.show()


if __name__ == "__main__":
    main()
