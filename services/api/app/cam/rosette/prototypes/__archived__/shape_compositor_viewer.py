"""
Shape Compositor Viewer — interactive matplotlib rosette tile explorer.

Ported from shape-compositor (2).jsx.  Renders an annular ring of parametric
tiles with per-shape sliders, material pickers, and 18 presets.

    python -m app.cam.rosette.prototypes.shape_compositor_viewer
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Wedge, Circle
from matplotlib.collections import PatchCollection
from matplotlib.widgets import Slider, RadioButtons, Button

from app.cam.rosette.prototypes.shape_library import SHAPES, draw_shape, default_params
from app.cam.rosette.prototypes.wood_materials import wood_by_id, WOODS, hex_to_rgb_float

# ── Presets (ported from JSX) ─────────────────────────────────

PRESETS = [
    {"name": "Fusion 360", "shape": "parallelogram", "params": {"w": 0.88, "h": 0.90, "lean": 0.28, "ch": 0.14}, "N": 12, "gap": 0.82, "matFg": "rosewood", "matBg": "ebony", "matAlt": "maple", "altMode": "ab", "ringW": 9},
    {"name": "Pearl Ovals", "shape": "ellipse", "params": {"rx": 0.78, "ry": 0.88}, "N": 20, "gap": 0.78, "matFg": "mop", "matBg": "ebony", "matAlt": "abalone", "altMode": "ab", "ringW": 7},
    {"name": "Koa Scales", "shape": "scale", "params": {"w": 0.98, "h": 0.92, "arch": 0.55, "tail": 0.0}, "N": 18, "gap": 0.95, "matFg": "koa", "matBg": "ebony", "matAlt": "walnut", "altMode": "ab", "ringW": 8},
    {"name": "Star Burst", "shape": "star", "params": {"n": 6, "outer": 0.88, "inner": 0.42, "spin": 0}, "N": 12, "gap": 0.85, "matFg": "maple", "matBg": "ebony", "matAlt": "rosewood", "altMode": "ab", "ringW": 10},
    {"name": "Moon Ring", "shape": "crescent", "params": {"orx": 0.88, "ory": 0.90, "irx": 0.70, "iry": 0.72, "iox": 0.18, "ioy": 0.0}, "N": 16, "gap": 0.85, "matFg": "mop", "matBg": "ebony", "matAlt": "maple", "altMode": "solid", "ringW": 8},
    {"name": "Ogee Flow", "shape": "ogee", "params": {"w": 0.92, "h": 0.92, "bulge": 0.38, "waist": 0.0, "top": 0.0}, "N": 14, "gap": 0.96, "matFg": "walnut", "matBg": "ebony", "matAlt": "maple", "altMode": "ab", "ringW": 9},
    {"name": "Teardrops", "shape": "teardrop", "params": {"w": 0.68, "h": 0.90, "bulge": 0.65, "tip": 0.55, "flip": 0}, "N": 16, "gap": 0.82, "matFg": "cedar", "matBg": "ebony", "matAlt": "spruce", "altMode": "ab", "ringW": 8},
    {"name": "Paisley", "shape": "petal", "params": {"w": 0.72, "h": 0.92, "c1": 0.6, "c2": -0.3, "lean": 0.2}, "N": 14, "gap": 0.85, "matFg": "koa", "matBg": "ebony", "matAlt": "maple", "altMode": "ab", "ringW": 9},
    {"name": "Rope Wave", "shape": "rope_asym", "params": {"thick": 0.58, "wave": 0.42, "skew": 0.62, "drift": 0.22, "cap": 0.6}, "N": 24, "gap": 0.92, "matFg": "maple", "matBg": "ebony", "matAlt": "rosewood", "altMode": "abc", "ringW": 7},
    {"name": "Hyp Calm", "shape": "hyperbolic_wave", "params": {"thick": 0.45, "wave": 0.68, "skew": 0.75, "drift": 1.2, "chaos": 0.33}, "N": 24, "gap": 0.98, "matFg": "maple", "matBg": "ebony", "matAlt": "rosewood", "altMode": "abc", "ringW": 8},
    {"name": "Hyp Storm", "shape": "hyperbolic_wave", "params": {"thick": 0.38, "wave": 1.18, "skew": 0.88, "drift": 2.0, "chaos": 0.95}, "N": 36, "gap": 1.05, "matFg": "mop", "matBg": "ebony", "matAlt": "abalone", "altMode": "abcd", "ringW": 10},
]

# ── Rendering ─────────────────────────────────────────────────

def _transform_tile(pts: np.ndarray, cx: float, cy: float, angle: float) -> np.ndarray:
    """Rotate by angle, then translate to (cx, cy)."""
    ca, sa = math.cos(angle), math.sin(angle)
    R = np.array([[ca, -sa], [sa, ca]])
    return (pts @ R.T) + np.array([cx, cy])


def render_wheel(ax, shape_key, params, N, ring_w, inner_r, gap,
                 mat_fg, mat_bg, mat_alt, alt_mode):
    """Render rosette wheel onto a matplotlib Axes."""
    ax.clear()
    ax.set_aspect("equal")
    ax.set_facecolor("#080604")
    ax.axis("off")

    outer_r = inner_r + ring_w
    margin = 4.0
    lim = outer_r + margin
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    # Background ring (full annulus)
    bg_wood = wood_by_id(mat_bg)
    bg_color = hex_to_rgb_float(bg_wood["base"])
    wedge = Wedge((0, 0), outer_r, 0, 360, width=ring_w,
                  facecolor=bg_color, edgecolor="none")
    ax.add_patch(wedge)

    # Tiles
    mid_r = (inner_r + outer_r) / 2
    ang_step = 2 * math.pi / N
    tile_h = (outer_r - inner_r) * gap
    tile_w = mid_r * ang_step * gap

    mat_cycle = [mat_fg, mat_alt, mat_bg]  # for abc mode

    patches = []
    colors = []

    for i in range(N):
        mid_ang = (i + 0.5) * ang_step - math.pi / 2

        # Material selection
        if alt_mode == "ab":
            wid = mat_fg if i % 2 == 0 else mat_alt
        elif alt_mode == "abc":
            wid = [mat_fg, mat_alt, mat_bg][i % 3]
        elif alt_mode == "abcd":
            wid = [mat_fg, mat_alt, mat_bg, mat_fg][i % 4]
        else:
            wid = mat_fg

        wood = wood_by_id(wid)
        color = hex_to_rgb_float(wood["base"])

        pts = draw_shape(shape_key, tile_w, tile_h, params, idx=i)
        cx = math.cos(mid_ang) * mid_r
        cy = math.sin(mid_ang) * mid_r
        world_pts = _transform_tile(pts, cx, cy, mid_ang + math.pi / 2)

        poly = Polygon(world_pts, closed=True)
        patches.append(poly)
        colors.append(color)

    if patches:
        pc = PatchCollection(patches, facecolors=colors,
                             edgecolors=[(0, 0, 0, 0.4)] * len(patches),
                             linewidths=0.6)
        ax.add_collection(pc)

    # Soundhole
    hole = Circle((0, 0), inner_r, facecolor="#0a0806", edgecolor="#c9a96e55",
                  linewidth=1.2)
    ax.add_patch(hole)

    # Outer ring edge
    outer_circle = Circle((0, 0), outer_r, fill=False,
                          edgecolor="#c9a96e30", linewidth=1.5)
    ax.add_patch(outer_circle)

    ax.figure.canvas.draw_idle()


# ── Interactive viewer ────────────────────────────────────────

class ShapeCompositorViewer:
    def __init__(self):
        self.shape_key = "parallelogram"
        self.params = default_params(self.shape_key)
        self.N = 12
        self.ring_w = 9.0
        self.inner_r = 40.8
        self.gap = 0.82
        self.mat_fg = "rosewood"
        self.mat_bg = "ebony"
        self.mat_alt = "maple"
        self.alt_mode = "ab"

        # Create figure
        self.fig = plt.figure(figsize=(14, 9), facecolor="#080604")
        self.fig.canvas.manager.set_window_title("Shape Compositor — The Production Shop")

        # Main wheel axes (center-left area)
        self.ax = self.fig.add_axes([0.05, 0.08, 0.55, 0.85])

        # ── Shape picker (right side, top) ───
        shape_keys = list(SHAPES.keys())
        shape_labels = [SHAPES[k]["label"] for k in shape_keys]
        self._shape_keys = shape_keys

        ax_shape = self.fig.add_axes([0.64, 0.48, 0.14, 0.48],
                                     facecolor="#0a0806")
        ax_shape.set_title("SHAPE", fontsize=8, color="#c9a96e",
                           fontfamily="monospace", loc="left")
        self.radio_shape = RadioButtons(ax_shape, shape_labels,
                                        active=shape_keys.index(self.shape_key))
        for lbl in self.radio_shape.labels:
            lbl.set_fontsize(7)
            lbl.set_color("#c9a96e")
        self.radio_shape.on_clicked(self._on_shape_change)

        # ── Ring sliders (bottom strip) ───
        slider_left = 0.12
        slider_width = 0.46

        self.sl_N = Slider(
            self.fig.add_axes([slider_left, 0.04, slider_width, 0.02]),
            "Tiles", 3, 48, valinit=self.N, valstep=1, color="#c9a96e")
        self.sl_ringW = Slider(
            self.fig.add_axes([slider_left, 0.01, slider_width, 0.02]),
            "Band mm", 2, 20, valinit=self.ring_w, color="#c9a96e")

        self.sl_N.on_changed(self._on_slider)
        self.sl_ringW.on_changed(self._on_slider)

        # ── Param sliders (right side, middle) ───
        self.param_sliders = {}
        self._build_param_sliders()

        # ── Preset buttons (right side, bottom) ───
        self.preset_buttons = []
        n_presets = min(len(PRESETS), 11)
        for i in range(n_presets):
            ax_btn = self.fig.add_axes([0.82, 0.48 - i * 0.04, 0.16, 0.035])
            btn = Button(ax_btn, PRESETS[i]["name"], color="#0a0806",
                         hovercolor="#1a1208")
            btn.label.set_fontsize(7)
            btn.label.set_color("#c9a96e")
            btn.on_clicked(lambda _, idx=i: self._load_preset(idx))
            self.preset_buttons.append(btn)

        # ── Material display ───
        ax_info = self.fig.add_axes([0.64, 0.08, 0.34, 0.04], facecolor="#080604")
        ax_info.axis("off")
        fg_c = hex_to_rgb_float(wood_by_id(self.mat_fg)["base"])
        bg_c = hex_to_rgb_float(wood_by_id(self.mat_bg)["base"])
        alt_c = hex_to_rgb_float(wood_by_id(self.mat_alt)["base"])
        ax_info.text(0, 0.5, f"FG: {self.mat_fg}  BG: {self.mat_bg}  ALT: {self.mat_alt}",
                     color="#c9a96e", fontsize=8, fontfamily="monospace",
                     va="center")

        self._render()

    def _build_param_sliders(self):
        """Create sliders for current shape's parameters."""
        # Remove old sliders
        for key, sl in self.param_sliders.items():
            sl.ax.remove()
        self.param_sliders.clear()

        spec = SHAPES[self.shape_key]
        param_defs = spec["params"]
        n = len(param_defs)

        for i, pd in enumerate(param_defs):
            y = 0.42 - i * 0.04
            if y < 0.14:
                break
            ax_sl = self.fig.add_axes([0.64, y, 0.34, 0.025])
            sl = Slider(ax_sl, pd["l"], pd["min"], pd["max"],
                        valinit=self.params.get(pd["k"], pd["d"]),
                        valstep=pd["s"], color="#c9a96e")
            sl.label.set_fontsize(7)
            sl.valtext.set_fontsize(7)
            sl.on_changed(lambda val, k=pd["k"]: self._on_param(k, val))
            self.param_sliders[pd["k"]] = sl

    def _on_shape_change(self, label):
        idx = [SHAPES[k]["label"] for k in self._shape_keys].index(label)
        self.shape_key = self._shape_keys[idx]
        self.params = default_params(self.shape_key)
        self._build_param_sliders()
        self._render()

    def _on_param(self, key, val):
        self.params[key] = val
        self._render()

    def _on_slider(self, _):
        self.N = int(self.sl_N.val)
        self.ring_w = self.sl_ringW.val
        self._render()

    def _load_preset(self, idx):
        pr = PRESETS[idx]
        self.shape_key = pr["shape"]
        self.params = dict(pr["params"])
        self.N = pr["N"]
        self.ring_w = pr["ringW"]
        self.gap = pr["gap"]
        self.mat_fg = pr["matFg"]
        self.mat_bg = pr["matBg"]
        self.mat_alt = pr["matAlt"]
        self.alt_mode = pr["altMode"]

        # Update slider values
        self.sl_N.set_val(self.N)
        self.sl_ringW.set_val(self.ring_w)

        # Update shape radio
        idx_s = self._shape_keys.index(self.shape_key)
        self.radio_shape.set_active(idx_s)

        self._build_param_sliders()
        self._render()

    def _render(self):
        render_wheel(self.ax, self.shape_key, self.params,
                     self.N, self.ring_w, self.inner_r, self.gap,
                     self.mat_fg, self.mat_bg, self.mat_alt, self.alt_mode)
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def main():
    viewer = ShapeCompositorViewer()
    viewer.show()


if __name__ == "__main__":
    main()
