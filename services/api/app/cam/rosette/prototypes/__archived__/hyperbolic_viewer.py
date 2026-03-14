"""
Hyperbolic Rosette Viewer — bezier drift wave multi-ring rosette.

Ported from hyperbolic-rosette.jsx.  Multi-ring layout with solid, stripe,
checker, and hyperbolic wave ring types.  4 presets (classic/pearl/koa/fire).

    python -m app.cam.rosette.prototypes.hyperbolic_viewer
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Wedge
from matplotlib.collections import PatchCollection
from matplotlib.widgets import Slider, RadioButtons, Button

from app.cam.rosette.prototypes.shape_library import _bezier3
from app.cam.rosette.prototypes.wood_materials import wood_by_id, hex_to_rgb_float


# ── Hyperbolic wave shape ─────────────────────────────────────

def hyp_shape(W, H, p, idx):
    """Return Nx2 closed polygon for one hyperbolic wave tile."""
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
        [W / 2, -hh + waveY * 0.3], 20))
    segs.append([W / 2, hh - waveY * 0.3])
    segs.extend(_bezier3(
        [W / 2, hh - waveY * 0.3],
        [peakX + W / 6, hh + waveY],
        [peakX - W / 6, hh + waveY * 0.5],
        [-W / 2, hh - waveY], 20))
    segs.append([-W / 2, -hh + waveY])
    return np.array(segs)


# ── Presets ───────────────────────────────────────────────────

PRESETS = {
    "classic": {
        "name": "Classic Dark",
        "innerR": 40.8,
        "rings": [
            {"label": "Inner Binding", "type": "solid", "widthMm": 0.9, "mat": "ebony"},
            {"label": "Inner Frieze", "type": "checker", "widthMm": 3.5,
             "matA": "ebony", "matB": "maple", "bw": 3, "bh": 2},
            {"label": "Inner Border", "type": "solid", "widthMm": 0.6, "mat": "ebony"},
            {"label": "Hyp Wave", "type": "hyp", "widthMm": 10.0,
             "matA": "maple", "matB": "rosewood", "matC": "ebony",
             "N": 28, "gap": 0.96, "thick": 0.48, "wave": 0.78,
             "skew": 0.72, "drift": 1.4, "chaos": 0.38, "dist": "abc"},
            {"label": "Outer Border", "type": "solid", "widthMm": 0.6, "mat": "ebony"},
            {"label": "Outer Frieze", "type": "checker", "widthMm": 2.5,
             "matA": "ebony", "matB": "maple", "bw": 3, "bh": 2},
            {"label": "Outer Binding", "type": "solid", "widthMm": 0.9, "mat": "ebony"},
        ],
    },
    "pearl": {
        "name": "Pearl Storm",
        "innerR": 40.8,
        "rings": [
            {"label": "Ebony Bind", "type": "solid", "widthMm": 1.0, "mat": "ebony"},
            {"label": "MOP Stripe", "type": "stripe", "widthMm": 2.5,
             "matA": "mop", "matB": "ebony", "sw": 3},
            {"label": "Ebony", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Hyp Wave", "type": "hyp", "widthMm": 11.0,
             "matA": "mop", "matB": "abalone", "matC": "ebony",
             "N": 36, "gap": 1.02, "thick": 0.42, "wave": 1.05,
             "skew": 0.80, "drift": 1.8, "chaos": 0.68, "dist": "abc"},
            {"label": "Ebony", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Abalone Line", "type": "stripe", "widthMm": 2.0,
             "matA": "abalone", "matB": "ebony", "sw": 4},
            {"label": "Ebony Bind", "type": "solid", "widthMm": 1.0, "mat": "ebony"},
        ],
    },
    "koa": {
        "name": "Koa Drift",
        "innerR": 40.8,
        "rings": [
            {"label": "Walnut Bind", "type": "solid", "widthMm": 0.8, "mat": "walnut"},
            {"label": "Koa/Maple", "type": "checker", "widthMm": 3.0,
             "matA": "koa", "matB": "maple", "bw": 4, "bh": 2},
            {"label": "Ebony", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Hyp Wave", "type": "hyp", "widthMm": 9.5,
             "matA": "koa", "matB": "maple", "matC": "walnut",
             "N": 20, "gap": 0.90, "thick": 0.58, "wave": 0.48,
             "skew": 0.65, "drift": 0.5, "chaos": 0.12, "dist": "ab"},
            {"label": "Ebony", "type": "solid", "widthMm": 0.5, "mat": "ebony"},
            {"label": "Koa/Maple", "type": "checker", "widthMm": 2.5,
             "matA": "koa", "matB": "maple", "bw": 4, "bh": 2},
            {"label": "Walnut Bind", "type": "solid", "widthMm": 0.8, "mat": "walnut"},
        ],
    },
    "fire": {
        "name": "Cedar Fire",
        "innerR": 40.8,
        "rings": [
            {"label": "Ebony Bind", "type": "solid", "widthMm": 0.7, "mat": "ebony"},
            {"label": "Cedar Stripe", "type": "stripe", "widthMm": 2.5,
             "matA": "cedar", "matB": "ebony", "sw": 5},
            {"label": "Ebony", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Hyp Wave", "type": "hyp", "widthMm": 12.0,
             "matA": "cedar", "matB": "spruce", "matC": "mahogany",
             "N": 32, "gap": 1.06, "thick": 0.36, "wave": 1.18,
             "skew": 0.88, "drift": 2.0, "chaos": 0.88, "dist": "abc"},
            {"label": "Ebony", "type": "solid", "widthMm": 0.4, "mat": "ebony"},
            {"label": "Spruce Stripe", "type": "stripe", "widthMm": 2.0,
             "matA": "spruce", "matB": "ebony", "sw": 5},
            {"label": "Ebony Bind", "type": "solid", "widthMm": 0.7, "mat": "ebony"},
        ],
    },
}


# ── Rendering ─────────────────────────────────────────────────

def _transform(pts, cx, cy, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    R = np.array([[ca, -sa], [sa, ca]])
    return (pts @ R.T) + np.array([cx, cy])


def render_rosette(ax, rings, inner_r, hyp_params=None):
    """Render multi-ring hyperbolic rosette."""
    ax.clear()
    ax.set_aspect("equal")
    ax.set_facecolor("#080604")
    ax.axis("off")

    total_w = sum(r["widthMm"] for r in rings)
    outer_r = inner_r + total_w
    scale = 1.0  # Work in mm directly

    # Build ring bounds
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
            wedge = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            wood = wood_by_id(ring.get("mat", "ebony"))
            patches.append(wedge)
            colors.append(hex_to_rgb_float(wood["base"]))
            edge_colors.append((0, 0, 0, 0))

        elif rtype == "stripe":
            matA = ring.get("matA", "ebony")
            matB = ring.get("matB", "maple")
            sw = ring.get("sw", 4)
            n_stripes = max(4, int(360 / sw))
            stripe_ang = 360 / n_stripes
            for si in range(n_stripes):
                wid = matA if (si // sw) % 2 == 0 else matB
                w = Wedge((0, 0), oR, si * stripe_ang, (si + 1) * stripe_ang,
                          width=oR - iR)
                patches.append(w)
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                edge_colors.append((0, 0, 0, 0))

        elif rtype == "checker":
            matA = ring.get("matA", "ebony")
            matB = ring.get("matB", "maple")
            bw = ring.get("bw", 4)
            bh = ring.get("bh", 2)
            n_cols = max(8, 360 // bw)
            n_rows = max(2, round(ring["widthMm"] / (bh * 0.5)))
            col_ang = 360 / n_cols
            row_h = (oR - iR) / n_rows
            for ri in range(n_rows):
                for ci in range(n_cols):
                    wid = matA if (ri + ci) % 2 == 0 else matB
                    r_inner = iR + ri * row_h
                    r_outer = iR + (ri + 1) * row_h
                    w = Wedge((0, 0), r_outer, ci * col_ang, (ci + 1) * col_ang,
                              width=row_h)
                    patches.append(w)
                    colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                    edge_colors.append((0, 0, 0, 0))

        elif rtype == "hyp":
            # Background fill for the ring
            matC = ring.get("matC", "ebony")
            bg_wedge = Wedge((0, 0), oR, 0, 360, width=oR - iR)
            patches.append(bg_wedge)
            colors.append(hex_to_rgb_float(wood_by_id(matC)["base"]))
            edge_colors.append((0, 0, 0, 0))

            # Use hyp_params override if provided, else ring data
            hp = hyp_params if hyp_params else ring
            N = hp.get("N", 24)
            gap = hp.get("gap", 0.96)
            p = {
                "thick": hp.get("thick", 0.48),
                "wave": hp.get("wave", 0.78),
                "skew": hp.get("skew", 0.72),
                "drift": hp.get("drift", 1.4),
                "chaos": hp.get("chaos", 0.38),
            }
            dist = hp.get("dist", "abc")
            matA = hp.get("matA", ring.get("matA", "maple"))
            matB = hp.get("matB", ring.get("matB", "rosewood"))

            ang_step = 2 * math.pi / N
            tile_h = (oR - iR) * gap
            tile_w = midR * ang_step * gap
            mat_cycle = [matA, matB, matC, matA]

            for i in range(N):
                mid_ang = (i + 0.5) * ang_step - math.pi / 2
                if dist == "ab":
                    wid = mat_cycle[i % 2]
                elif dist == "abc":
                    wid = mat_cycle[i % 3]
                elif dist == "abcd":
                    wid = mat_cycle[i % 4]
                else:
                    wid = matA

                pts = hyp_shape(tile_w, tile_h, p, i)
                cx = math.cos(mid_ang) * midR
                cy = math.sin(mid_ang) * midR
                world = _transform(pts, cx, cy, mid_ang + math.pi / 2)

                poly = Polygon(world, closed=True)
                patches.append(poly)
                colors.append(hex_to_rgb_float(wood_by_id(wid)["base"]))
                edge_colors.append((0, 0, 0, 0.35))

    if patches:
        pc = PatchCollection(patches, facecolors=colors,
                             edgecolors=edge_colors, linewidths=0.4)
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


# ── Interactive viewer ────────────────────────────────────────

class HyperbolicViewer:
    def __init__(self):
        self.preset_key = "classic"
        self._load_preset_data("classic")

        self.fig = plt.figure(figsize=(13, 9), facecolor="#080604")
        self.fig.canvas.manager.set_window_title("Hyperbolic Rosette — The Production Shop")

        # Main wheel
        self.ax = self.fig.add_axes([0.02, 0.08, 0.55, 0.85])

        # ── Hyp wave sliders (right side) ───
        self._hyp_ring = self._find_hyp_ring()
        hp = self._hyp_ring or {}

        slider_x = 0.62
        slider_w = 0.35

        self.sl_N = Slider(
            self.fig.add_axes([slider_x, 0.88, slider_w, 0.02]),
            "Tiles N", 6, 48, valinit=hp.get("N", 24), valstep=1, color="#c9a96e")
        self.sl_thick = Slider(
            self.fig.add_axes([slider_x, 0.83, slider_w, 0.02]),
            "Thickness", 0.1, 0.95, valinit=hp.get("thick", 0.48), color="#c9a96e")
        self.sl_wave = Slider(
            self.fig.add_axes([slider_x, 0.78, slider_w, 0.02]),
            "Wave amp", 0.0, 1.5, valinit=hp.get("wave", 0.78), color="#c9a96e")
        self.sl_skew = Slider(
            self.fig.add_axes([slider_x, 0.73, slider_w, 0.02]),
            "Skew", 0.0, 1.0, valinit=hp.get("skew", 0.72), color="#c9a96e")
        self.sl_drift = Slider(
            self.fig.add_axes([slider_x, 0.68, slider_w, 0.02]),
            "Hyp drift", 0.0, 3.0, valinit=hp.get("drift", 1.4), color="#c9a96e")
        self.sl_chaos = Slider(
            self.fig.add_axes([slider_x, 0.63, slider_w, 0.02]),
            "Chaos", 0.0, 1.5, valinit=hp.get("chaos", 0.38), color="#c9a96e")
        self.sl_gap = Slider(
            self.fig.add_axes([slider_x, 0.58, slider_w, 0.02]),
            "Gap fill", 0.5, 1.2, valinit=hp.get("gap", 0.96), color="#c9a96e")

        for sl in [self.sl_N, self.sl_thick, self.sl_wave, self.sl_skew,
                   self.sl_drift, self.sl_chaos, self.sl_gap]:
            sl.on_changed(self._on_slider)
            sl.label.set_fontsize(7)
            sl.valtext.set_fontsize(7)

        # ── Preset buttons ───
        preset_keys = list(PRESETS.keys())
        self.preset_btns = []
        for i, key in enumerate(preset_keys):
            ax_btn = self.fig.add_axes([slider_x + i * 0.09, 0.50, 0.08, 0.04])
            btn = Button(ax_btn, PRESETS[key]["name"], color="#0a0806",
                         hovercolor="#1a1208")
            btn.label.set_fontsize(7)
            btn.label.set_color("#c9a96e")
            btn.on_clicked(lambda _, k=key: self._load_preset(k))
            self.preset_btns.append(btn)

        # ── Ring info ───
        self._info_ax = self.fig.add_axes([0.62, 0.08, 0.36, 0.38], facecolor="#080604")
        self._info_ax.axis("off")

        self._render()

    def _find_hyp_ring(self):
        for r in self.rings:
            if r["type"] == "hyp":
                return r
        return None

    def _load_preset_data(self, key):
        pr = PRESETS[key]
        self.inner_r = pr["innerR"]
        self.rings = [dict(r) for r in pr["rings"]]
        self.preset_key = key

    def _load_preset(self, key):
        self._load_preset_data(key)
        hp = self._find_hyp_ring() or {}
        self.sl_N.set_val(hp.get("N", 24))
        self.sl_thick.set_val(hp.get("thick", 0.48))
        self.sl_wave.set_val(hp.get("wave", 0.78))
        self.sl_skew.set_val(hp.get("skew", 0.72))
        self.sl_drift.set_val(hp.get("drift", 1.4))
        self.sl_chaos.set_val(hp.get("chaos", 0.38))
        self.sl_gap.set_val(hp.get("gap", 0.96))
        self._render()

    def _on_slider(self, _):
        hyp = self._find_hyp_ring()
        if hyp:
            hyp["N"] = int(self.sl_N.val)
            hyp["thick"] = self.sl_thick.val
            hyp["wave"] = self.sl_wave.val
            hyp["skew"] = self.sl_skew.val
            hyp["drift"] = self.sl_drift.val
            hyp["chaos"] = self.sl_chaos.val
            hyp["gap"] = self.sl_gap.val
        self._render()

    def _update_info(self):
        ax = self._info_ax
        ax.clear()
        ax.axis("off")
        total = sum(r["widthMm"] for r in self.rings)
        outer = self.inner_r + total
        ax.text(0, 0.95, f"Preset: {PRESETS[self.preset_key]['name']}",
                fontsize=10, color="#e8c87a", fontfamily="monospace",
                va="top", weight="bold")
        y = 0.80
        for r in self.rings:
            label = r.get("label", r["type"])
            ax.text(0, y, f"  {label:20s} {r['type']:8s} {r['widthMm']:.1f}mm",
                    fontsize=7, color="#7a5c2e", fontfamily="monospace", va="top")
            y -= 0.10
        ax.text(0, y - 0.05,
                f"SH r={self.inner_r:.1f}mm  |  Band={total:.1f}mm  |  Outer={outer:.1f}mm",
                fontsize=8, color="#c9a96e", fontfamily="monospace", va="top")

    def _render(self):
        render_rosette(self.ax, self.rings, self.inner_r)
        self._update_info()
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def main():
    viewer = HyperbolicViewer()
    viewer.show()


if __name__ == "__main__":
    main()
