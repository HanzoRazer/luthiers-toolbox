"""
Rosette Wheel Viewer — interactive cell-based symmetry painter.

Ported from rosette-wheel.jsx.  Fixed 7-ring Torres layout with
click/drag painting, symmetry modes, and 14 wood materials.

    python -m app.cam.rosette.prototypes.rosette_wheel_viewer
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.collections import PatchCollection
from matplotlib.widgets import Slider, RadioButtons, Button

from app.cam.rosette.prototypes.wood_materials import WOODS, wood_by_id, hex_to_rgb_float


# ── Ring layout (fixed Torres 7-ring) ────────────────────────

RING_NAMES = [
    "Inner Binding", "Inner Frieze", "Inner Border",
    "Main Band", "Outer Border", "Outer Frieze", "Outer Binding",
]
RING_WIDTHS = [0.6, 3.0, 0.5, 8.0, 0.5, 2.5, 0.6]  # mm
SOUNDHOLE_R = 40.8
DEFAULT_SEGMENTS = 12

DEFAULT_SCHEME = ["ebony", "maple", "ebony", "rosewood", "ebony", "maple", "ebony"]

PRESETS = {
    "torres": ["ebony", "maple", "ebony", "rosewood", "ebony", "maple", "ebony"],
    "celtic": ["walnut", "bone", "walnut", "koa", "walnut", "bone", "walnut"],
    "pearl":  ["ebony", "mop", "ebony", "abalone", "ebony", "mop", "ebony"],
    "cedar":  ["ebony", "spruce", "ebony", "cedar", "ebony", "spruce", "ebony"],
    "blank":  ["none", "none", "none", "none", "none", "none", "none"],
}


# ── Ring bounds helper ────────────────────────────────────────

def _ring_bounds():
    """Return list of (inner_r, outer_r, width) for each ring."""
    r = SOUNDHOLE_R
    bounds = []
    for w in RING_WIDTHS:
        bounds.append((r, r + w, w))
        r += w
    return bounds


# ── Rendering ─────────────────────────────────────────────────

def render_wheel(ax, cells, segments, selected_wood, ring_bounds):
    """Draw the painted rosette wheel onto ax."""
    ax.clear()
    ax.set_aspect("equal")
    ax.set_facecolor("#080604")
    ax.axis("off")

    outer_r = ring_bounds[-1][1]
    lim = outer_r + 4
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    ang_step = 360.0 / segments

    patches = []
    colors = []

    for ri, (ir, orr, ww) in enumerate(ring_bounds):
        for si in range(segments):
            a0 = si * ang_step
            a1 = (si + 1) * ang_step
            wid = cells.get(f"{ri}-{si}", "ebony")
            wood = wood_by_id(wid)
            c = hex_to_rgb_float(wood["base"])

            wedge = Wedge((0, 0), orr, a0, a1, width=ww)
            patches.append(wedge)
            colors.append(c)

    if patches:
        pc = PatchCollection(patches, facecolors=colors,
                             edgecolors=[(0.05, 0.03, 0.01, 0.5)] * len(patches),
                             linewidths=0.4)
        ax.add_collection(pc)

    # Ring separation circles
    for ir, orr, _ in ring_bounds:
        for r in [ir, orr]:
            ax.add_patch(plt.Circle((0, 0), r, fill=False,
                                     edgecolor="#c9a96e30", linewidth=0.5,
                                     linestyle="--"))

    # Soundhole
    ax.add_patch(plt.Circle((0, 0), SOUNDHOLE_R, facecolor="#0a0806",
                             edgecolor="#c9a96e55", linewidth=1.2))

    # Outer glow
    ax.add_patch(plt.Circle((0, 0), outer_r, fill=False,
                             edgecolor="#c9a96e20", linewidth=1.5))

    ax.figure.canvas.draw_idle()


# ── Interactive viewer ────────────────────────────────────────

class RosetteWheelViewer:
    def __init__(self):
        self.segments = DEFAULT_SEGMENTS
        self.sel_wood = "rosewood"
        self.symmetry = "full"
        self.cells = {}
        self.ring_bounds = _ring_bounds()
        self.painting = False

        # Apply default preset
        self._apply_preset_data(DEFAULT_SCHEME)

        # Figure
        self.fig = plt.figure(figsize=(12, 9), facecolor="#080604")
        self.fig.canvas.manager.set_window_title("Rosette Wheel — The Production Shop")

        # Main wheel
        self.ax = self.fig.add_axes([0.02, 0.05, 0.60, 0.90])

        # ── Material palette (right, top) ───
        wood_ids = [w["id"] for w in WOODS if w["id"] != "none"]
        wood_labels = [w["name"] for w in WOODS if w["id"] != "none"]
        self._wood_ids = wood_ids

        ax_mat = self.fig.add_axes([0.65, 0.40, 0.15, 0.55], facecolor="#0a0806")
        ax_mat.set_title("MATERIAL", fontsize=8, color="#c9a96e",
                         fontfamily="monospace", loc="left")
        active_idx = wood_ids.index(self.sel_wood) if self.sel_wood in wood_ids else 0
        self.radio_mat = RadioButtons(ax_mat, wood_labels, active=active_idx)
        for lbl in self.radio_mat.labels:
            lbl.set_fontsize(7)
            lbl.set_color("#c9a96e")
        self.radio_mat.on_clicked(self._on_mat_change)

        # ── Symmetry selector ───
        ax_sym = self.fig.add_axes([0.83, 0.70, 0.14, 0.22], facecolor="#0a0806")
        ax_sym.set_title("SYMMETRY", fontsize=7, color="#c9a96e",
                         fontfamily="monospace", loc="left")
        sym_labels = ["None", "Quarter (x4)", "Half (x2)", "Full ring"]
        self._sym_values = ["none", "quarter", "half", "full"]
        self.radio_sym = RadioButtons(ax_sym, sym_labels,
                                       active=self._sym_values.index(self.symmetry))
        for lbl in self.radio_sym.labels:
            lbl.set_fontsize(7)
            lbl.set_color("#c9a96e")
        self.radio_sym.on_clicked(self._on_sym_change)

        # ── Segments slider ───
        self.sl_seg = Slider(
            self.fig.add_axes([0.65, 0.35, 0.32, 0.02]),
            "Segments", 4, 36, valinit=self.segments, valstep=2,
            color="#c9a96e")
        self.sl_seg.on_changed(self._on_seg_change)

        # ── Quick segment buttons ───
        self.seg_btns = []
        for i, n in enumerate([6, 8, 12, 16, 24]):
            ax_btn = self.fig.add_axes([0.65 + i * 0.065, 0.30, 0.06, 0.035])
            btn = Button(ax_btn, str(n), color="#0a0806", hovercolor="#1a1208")
            btn.label.set_fontsize(8)
            btn.label.set_color("#c9a96e")
            btn.on_clicked(lambda _, v=n: self._set_segments(v))
            self.seg_btns.append(btn)

        # ── Preset buttons ───
        preset_names = list(PRESETS.keys())
        self.preset_btns = []
        for i, name in enumerate(preset_names):
            ax_btn = self.fig.add_axes([0.65 + i * 0.065, 0.24, 0.06, 0.035])
            btn = Button(ax_btn, name.title(), color="#0a0806", hovercolor="#1a1208")
            btn.label.set_fontsize(7)
            btn.label.set_color("#c9a96e")
            btn.on_clicked(lambda _, k=name: self._load_preset(k))
            self.preset_btns.append(btn)

        # ── Info text ───
        self._info_ax = self.fig.add_axes([0.65, 0.08, 0.32, 0.12], facecolor="#080604")
        self._info_ax.axis("off")

        # ── Mouse events for painting ───
        self.fig.canvas.mpl_connect("button_press_event", self._on_press)
        self.fig.canvas.mpl_connect("button_release_event", self._on_release)
        self.fig.canvas.mpl_connect("motion_notify_event", self._on_motion)

        self._render()

    def _apply_preset_data(self, scheme):
        self.cells = {}
        for ri in range(len(RING_WIDTHS)):
            mat = scheme[ri] if ri < len(scheme) else "ebony"
            for si in range(self.segments):
                self.cells[f"{ri}-{si}"] = mat

    def _hit_test(self, mx, my):
        """Convert data coords to ring/segment index."""
        dist = math.sqrt(mx * mx + my * my)
        ang_deg = (math.degrees(math.atan2(my, mx)) + 360) % 360
        for ri, (ir, orr, _) in enumerate(self.ring_bounds):
            if ir <= dist < orr:
                si = int(ang_deg / (360 / self.segments)) % self.segments
                return ri, si
        return None, None

    def _get_sym_peers(self, si):
        peers = {si}
        if self.symmetry == "full":
            peers = set(range(self.segments))
        elif self.symmetry == "half":
            peers.add((si + self.segments // 2) % self.segments)
        elif self.symmetry == "quarter":
            q = self.segments // 4
            for offset in [0, q, q * 2, q * 3]:
                peers.add((si + offset) % self.segments)
        return peers

    def _paint_cell(self, ri, si):
        for s in self._get_sym_peers(si):
            self.cells[f"{ri}-{s}"] = self.sel_wood
        self._render()

    def _on_press(self, event):
        if event.inaxes != self.ax:
            return
        self.painting = True
        ri, si = self._hit_test(event.xdata, event.ydata)
        if ri is not None:
            self._paint_cell(ri, si)

    def _on_release(self, _):
        self.painting = False

    def _on_motion(self, event):
        if not self.painting or event.inaxes != self.ax:
            return
        ri, si = self._hit_test(event.xdata, event.ydata)
        if ri is not None:
            self._paint_cell(ri, si)

    def _on_mat_change(self, label):
        idx = [w["name"] for w in WOODS if w["id"] != "none"].index(label)
        self.sel_wood = self._wood_ids[idx]

    def _on_sym_change(self, label):
        idx = ["None", "Quarter (x4)", "Half (x2)", "Full ring"].index(label)
        self.symmetry = self._sym_values[idx]

    def _on_seg_change(self, val):
        self._set_segments(int(val))

    def _set_segments(self, n):
        self.segments = n
        self.sl_seg.set_val(n)
        self._apply_preset_data(DEFAULT_SCHEME)
        self._render()

    def _load_preset(self, key):
        if key in PRESETS:
            self._apply_preset_data(PRESETS[key])
            self._render()

    def _update_info(self):
        ax = self._info_ax
        ax.clear()
        ax.axis("off")
        total = sum(RING_WIDTHS)
        outer = SOUNDHOLE_R + total
        wood = wood_by_id(self.sel_wood)
        ax.text(0, 0.9, f"Active: {wood['name']}", fontsize=9,
                color="#e8c87a", fontfamily="monospace", va="top")
        ax.text(0, 0.55, f"Segments: {self.segments}  |  Symmetry: {self.symmetry}",
                fontsize=8, color="#7a5c2e", fontfamily="monospace", va="top")
        ax.text(0, 0.20,
                f"SH r={SOUNDHOLE_R:.1f}mm  |  Band={total:.1f}mm  |  Outer r={outer:.1f}mm",
                fontsize=7, color="#4a3010", fontfamily="monospace", va="top")

    def _render(self):
        render_wheel(self.ax, self.cells, self.segments,
                     self.sel_wood, self.ring_bounds)
        self._update_info()
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def main():
    viewer = RosetteWheelViewer()
    viewer.show()


if __name__ == "__main__":
    main()
