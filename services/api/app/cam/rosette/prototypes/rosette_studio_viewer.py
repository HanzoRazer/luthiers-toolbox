"""
Rosette Studio Viewer — multi-ring rosette designer with pattern generators.

Ported from rosette-studio.jsx.  Each ring has a pattern type (solid,
checkerboard, brick, stripe, wave, rope) and independent materials.

    python -m app.cam.rosette.prototypes.rosette_studio_viewer
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.widgets import Slider, RadioButtons, Button

from app.cam.rosette.prototypes.wood_materials import wood_by_id, hex_to_rgb_float


# ── Wave helper (arch_y ported from JSX) ──────────────────────

def arch_y(lx: float, sl: float, A: float, sk: float) -> float:
    px = sk * sl
    if px <= 0 or sl <= 0:
        return 0.0
    if lx <= px:
        return A * math.sin(math.pi / 2 * lx / px)
    return A * math.cos(math.pi / 2 * (lx - px) / (sl - px))


# ── Rope twist tile patterns ─────────────────────────────────

ROPE_BASE = [
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 0],
    [1, 1, 0, 0, 0, 1, 1],
    [0, 1, 0, 0, 1, 1, 0],
    [0, 0, 1, 1, 1, 0, 0],
]
ROPE_MIRR = [
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 1, 1, 0],
    [1, 1, 0, 0, 0, 1, 1],
    [0, 1, 1, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 0, 0],
]


# ── Grid generator (ported from JSX) ─────────────────────────

def generate_grid(ring: dict, n_cols: int, n_rows: int) -> list[list[str | None]]:
    rtype = ring["type"]
    params = ring.get("params", {})
    materials = ring.get("materials", ["ebony", "maple", "rosewood", "bone"])

    def get_mat(i):
        return materials[min(i, len(materials) - 1)] if i < len(materials) else "ebony"

    grid = []
    for r in range(n_rows):
        row = []
        for c in range(n_cols):
            v = 0
            if rtype == "solid":
                v = 0
            elif rtype == "checkerboard":
                w = params.get("w", 4)
                h = params.get("h", 2)
                bR = r // max(1, h)
                bC = c // max(1, w)
                v = (bR + bC) % 2
            elif rtype == "brick":
                w = params.get("w", 6)
                h = params.get("h", 3)
                bR = r // max(1, h)
                off = 0 if bR % 2 == 0 else w // 2
                v = ((c + off) // max(1, w)) % 2
            elif rtype == "stripe":
                w = params.get("w", 4)
                count = params.get("count", 2)
                v = (c // max(1, w)) % count
            elif rtype == "wave":
                A = params.get("A", 6)
                sl = params.get("sl", 18)
                gap = params.get("gap", 2)
                d = params.get("d", 4)
                sw = params.get("sw", 1.8)
                N = int(params.get("N", 7))
                sk = params.get("sk", 0.72)
                ch = params.get("ch", 13)
                cmode = params.get("cmode", "tri")
                pitch = sl + gap
                hit = False
                hitN = 0
                for n in range(-2, N + 3):
                    off = ((n * ch) % pitch + pitch * 100) % pitch
                    xs = ((c - off) % pitch + pitch * 100) % pitch
                    if xs >= sl:
                        continue
                    if abs(r - (n * d + arch_y(xs, sl, A, sk))) < sw / 2:
                        hit = True
                        hitN = n
                        break
                if hit:
                    idx = ((hitN % 3) + 3) % 3
                    if cmode == "mono":
                        v = 0
                    elif cmode == "bw":
                        v = 0 if ((hitN % 2) + 2) % 2 == 0 else 1
                    else:
                        v = idx
                else:
                    v = -1
            elif rtype == "rope":
                tH = 5
                rep = c // 7
                tile = ROPE_BASE if rep % 2 == 0 else ROPE_MIRR
                gr = min(r * tH // max(1, n_rows), tH - 1)
                v = tile[gr][c % 7]
            elif rtype == "custom":
                cg = params.get("grid")
                if cg and len(cg) > 0:
                    gh = len(cg)
                    gw = len(cg[0])
                    v = cg[min(r * gh // max(1, n_rows), gh - 1)][c % gw]

            row.append(None if v < 0 else get_mat(v))
        grid.append(row)
    return grid


# ── Ring definitions ──────────────────────────────────────────

TYPES = ["solid", "checkerboard", "brick", "stripe", "wave", "rope"]

INITIAL_RINGS = [
    {"label": "Inner Binding", "type": "solid", "widthMm": 0.8,
     "params": {}, "materials": ["ebony", "maple", "rosewood", "bone"]},
    {"label": "Inner Frieze", "type": "checkerboard", "widthMm": 3.5,
     "params": {"w": 4, "h": 2}, "materials": ["walnut", "maple", "rosewood", "bone"]},
    {"label": "Inner Border", "type": "solid", "widthMm": 0.5,
     "params": {}, "materials": ["ebony", "maple", "rosewood", "bone"]},
    {"label": "Wave Band", "type": "wave", "widthMm": 9.0,
     "params": {"A": 6, "sl": 18, "gap": 2, "sk": 0.72, "ch": 13,
                "d": 4, "sw": 1.8, "N": 7, "cmode": "tri"},
     "materials": ["ebony", "maple", "rosewood", "bone"]},
    {"label": "Outer Border", "type": "solid", "widthMm": 0.5,
     "params": {}, "materials": ["ebony", "maple", "rosewood", "bone"]},
    {"label": "Outer Frieze", "type": "brick", "widthMm": 2.5,
     "params": {"w": 6, "h": 3}, "materials": ["walnut", "maple", "rosewood", "bone"]},
    {"label": "Outer Binding", "type": "solid", "widthMm": 0.8,
     "params": {}, "materials": ["ebony", "maple", "rosewood", "bone"]},
]

PRESETS = {
    "torres": [
        {"label": "Inner Binding", "type": "solid", "widthMm": 0.8, "params": {}, "materials": ["ebony"]},
        {"label": "Inner Frieze", "type": "brick", "widthMm": 3.5, "params": {"w": 5, "h": 2}, "materials": ["walnut", "maple"]},
        {"label": "Border", "type": "solid", "widthMm": 0.5, "params": {}, "materials": ["ebony"]},
        {"label": "Wave Band", "type": "wave", "widthMm": 9.0,
         "params": {"A": 6, "sl": 18, "gap": 2, "sk": 0.72, "ch": 13, "d": 4, "sw": 1.8, "N": 7, "cmode": "tri"},
         "materials": ["ebony", "maple", "rosewood", "bone"]},
        {"label": "Border", "type": "solid", "widthMm": 0.5, "params": {}, "materials": ["ebony"]},
        {"label": "Outer Frieze", "type": "brick", "widthMm": 2.5, "params": {"w": 5, "h": 2}, "materials": ["walnut", "maple"]},
        {"label": "Outer Binding", "type": "solid", "widthMm": 0.8, "params": {}, "materials": ["ebony"]},
    ],
    "pearl": [
        {"label": "Ebony Ring", "type": "solid", "widthMm": 1.0, "params": {}, "materials": ["ebony"]},
        {"label": "MOP Checks", "type": "checkerboard", "widthMm": 4.0, "params": {"w": 4, "h": 2}, "materials": ["ebony", "mop"]},
        {"label": "Ebony", "type": "solid", "widthMm": 0.5, "params": {}, "materials": ["ebony"]},
        {"label": "Abalone Band", "type": "stripe", "widthMm": 6.0, "params": {"w": 6, "count": 2}, "materials": ["abalone", "mop"]},
        {"label": "Ebony", "type": "solid", "widthMm": 0.5, "params": {}, "materials": ["ebony"]},
        {"label": "MOP Rope", "type": "rope", "widthMm": 3.0, "params": {}, "materials": ["ebony", "mop"]},
        {"label": "Ebony Ring", "type": "solid", "widthMm": 1.0, "params": {}, "materials": ["ebony"]},
    ],
    "celtic": [
        {"label": "Walnut Bind", "type": "solid", "widthMm": 0.8, "params": {}, "materials": ["walnut"]},
        {"label": "Koa Stripe", "type": "stripe", "widthMm": 2.5, "params": {"w": 3, "count": 2}, "materials": ["walnut", "koa"]},
        {"label": "Ebony", "type": "solid", "widthMm": 0.5, "params": {}, "materials": ["ebony"]},
        {"label": "Rope Band", "type": "rope", "widthMm": 5.0, "params": {}, "materials": ["walnut", "koa"]},
        {"label": "Ebony", "type": "solid", "widthMm": 0.5, "params": {}, "materials": ["ebony"]},
        {"label": "Koa Checks", "type": "checkerboard", "widthMm": 3.5, "params": {"w": 4, "h": 2}, "materials": ["walnut", "koa"]},
        {"label": "Walnut Bind", "type": "solid", "widthMm": 0.8, "params": {}, "materials": ["walnut"]},
    ],
}


# ── Pixel-scanline renderer ──────────────────────────────────

CIRC_COLS = 480

def render_wheel(ax, rings, sound_r, selected_idx=None):
    """Render multi-ring rosette using scanline approach into an image."""
    ax.clear()
    ax.set_aspect("equal")
    ax.set_facecolor("#080604")
    ax.axis("off")

    total_w = sum(r["widthMm"] for r in rings)
    outer_r = sound_r + total_w

    # Prepare ring data with grids
    r_cur = sound_r
    prepared = []
    for ring in rings:
        iR = r_cur
        r_cur += ring["widthMm"]
        oR = r_cur
        n_rows = max(2, round(ring["widthMm"] / 0.5))
        grid = generate_grid(ring, CIRC_COLS, n_rows)
        prepared.append({**ring, "iR": iR, "oR": oR, "nR": n_rows, "grid": grid})

    # Build pixel image via numpy
    size = 520
    mm_px = size / ((outer_r + 6) * 2)
    cx = cy = size / 2

    img = np.zeros((size, size, 3), dtype=np.uint8)
    img[:, :] = [8, 6, 4]  # background

    ys, xs = np.mgrid[0:size, 0:size]
    dx = (xs - cx) / mm_px
    dy = (ys - cy) / mm_px
    dist = np.sqrt(dx * dx + dy * dy)
    ang = (np.arctan2(dy, dx) + math.pi) / (2 * math.pi)
    col_idx = np.clip((ang * CIRC_COLS).astype(int), 0, CIRC_COLS - 1)

    for rp in prepared:
        mask = (dist >= rp["iR"]) & (dist < rp["oR"])
        if not np.any(mask):
            continue
        row_idx = np.clip(
            ((dist[mask] - rp["iR"]) / rp["widthMm"] * rp["nR"]).astype(int),
            0, rp["nR"] - 1,
        )
        cols = col_idx[mask]
        n_pixels = mask.sum()
        for pi in range(n_pixels):
            r_i = row_idx[pi]
            c_i = cols[pi]
            wid = rp["grid"][r_i][c_i]
            if wid is None:
                continue
            wood = wood_by_id(wid)
            rgb = tuple(int(wood["base"][i:i+2], 16) for i in (1, 3, 5))
            # Get flat indices
            ym, xm = np.where(mask)
            img[ym[pi], xm[pi]] = rgb

    ax.imshow(img, extent=[-outer_r - 6, outer_r + 6, -outer_r - 6, outer_r + 6],
              origin="upper", interpolation="bilinear")

    # Ring borders
    for i, rp in enumerate(prepared):
        for r in [rp["iR"], rp["oR"]]:
            c = Circle((0, 0), r, fill=False,
                       edgecolor="#c9a96e" if i == selected_idx else "#c9a96e30",
                       linewidth=1.5 if i == selected_idx else 0.5,
                       linestyle="-" if i == selected_idx else "--")
            ax.add_patch(c)

    # Soundhole
    ax.add_patch(Circle((0, 0), sound_r, facecolor="#0a0806",
                        edgecolor="#c9a96e55", linewidth=1.2))

    lim = outer_r + 6
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.figure.canvas.draw_idle()


# ── Optimized batch renderer (avoid per-pixel Python loop) ───

def render_wheel_fast(ax, rings, sound_r, selected_idx=None):
    """Fast numpy-vectorized multi-ring renderer."""
    ax.clear()
    ax.set_aspect("equal")
    ax.set_facecolor("#080604")
    ax.axis("off")

    total_w = sum(r["widthMm"] for r in rings)
    outer_r = sound_r + total_w

    r_cur = sound_r
    prepared = []
    for ring in rings:
        iR = r_cur
        r_cur += ring["widthMm"]
        oR = r_cur
        n_rows = max(2, round(ring["widthMm"] / 0.5))
        grid = generate_grid(ring, CIRC_COLS, n_rows)
        # Pre-build color LUT for this ring
        color_grid = np.zeros((n_rows, CIRC_COLS, 3), dtype=np.uint8)
        alpha_grid = np.zeros((n_rows, CIRC_COLS), dtype=bool)
        for ri in range(n_rows):
            for ci in range(CIRC_COLS):
                wid = grid[ri][ci]
                if wid is not None:
                    w = wood_by_id(wid)
                    color_grid[ri, ci] = [int(w["base"][j:j+2], 16) for j in (1, 3, 5)]
                    alpha_grid[ri, ci] = True
        prepared.append({
            **ring, "iR": iR, "oR": oR, "nR": n_rows,
            "color_grid": color_grid, "alpha_grid": alpha_grid,
        })

    size = 520
    mm_px = size / ((outer_r + 6) * 2)
    cx = cy = size / 2

    img = np.full((size, size, 3), [8, 6, 4], dtype=np.uint8)

    ys, xs = np.mgrid[0:size, 0:size]
    dx = (xs - cx) / mm_px
    dy = (ys - cy) / mm_px
    dist = np.sqrt(dx * dx + dy * dy)
    ang = (np.arctan2(dy, dx) + math.pi) / (2 * math.pi)
    col_idx = np.clip((ang * CIRC_COLS).astype(int), 0, CIRC_COLS - 1)

    for rp in prepared:
        mask = (dist >= rp["iR"]) & (dist < rp["oR"])
        if not np.any(mask):
            continue
        row_idx = np.clip(
            ((dist[mask] - rp["iR"]) / rp["widthMm"] * rp["nR"]).astype(int),
            0, rp["nR"] - 1,
        )
        cols = col_idx[mask]
        # Vectorized lookup
        alpha = rp["alpha_grid"][row_idx, cols]
        colors = rp["color_grid"][row_idx, cols]
        img[mask] = np.where(alpha[:, None], colors, img[mask])

    ax.imshow(img, extent=[-outer_r - 6, outer_r + 6, -outer_r - 6, outer_r + 6],
              origin="upper", interpolation="bilinear")

    for i, rp in enumerate(prepared):
        for r in [rp["iR"], rp["oR"]]:
            c = Circle((0, 0), r, fill=False,
                       edgecolor="#c9a96e" if i == selected_idx else "#c9a96e30",
                       linewidth=1.5 if i == selected_idx else 0.5,
                       linestyle="-" if i == selected_idx else "--")
            ax.add_patch(c)

    ax.add_patch(Circle((0, 0), sound_r, facecolor="#0a0806",
                        edgecolor="#c9a96e55", linewidth=1.2))

    lim = outer_r + 6
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.figure.canvas.draw_idle()


# ── Interactive viewer ────────────────────────────────────────

class RosetteStudioViewer:
    def __init__(self):
        self.rings = [dict(r) for r in INITIAL_RINGS]
        self.selected = 3  # Wave Band
        self.sound_r = 40.8

        self.fig = plt.figure(figsize=(14, 9), facecolor="#080604")
        self.fig.canvas.manager.set_window_title("Rosette Studio — The Production Shop")

        # Main wheel
        self.ax = self.fig.add_axes([0.02, 0.08, 0.55, 0.85])

        # Ring list (right side)
        ax_info = self.fig.add_axes([0.60, 0.55, 0.38, 0.40], facecolor="#0a0806")
        ax_info.set_title("RING STACK (inside → outside)", fontsize=8,
                          color="#c9a96e", fontfamily="monospace", loc="left")
        ax_info.axis("off")
        self._ring_info_ax = ax_info

        # Ring type selector for selected ring
        ax_type = self.fig.add_axes([0.60, 0.35, 0.15, 0.18], facecolor="#0a0806")
        ax_type.set_title("RING TYPE", fontsize=7, color="#c9a96e",
                          fontfamily="monospace", loc="left")
        self.radio_type = RadioButtons(ax_type, TYPES,
                                        active=TYPES.index(self.rings[self.selected]["type"]))
        for lbl in self.radio_type.labels:
            lbl.set_fontsize(7)
            lbl.set_color("#c9a96e")
        self.radio_type.on_clicked(self._on_type_change)

        # Width slider for selected ring
        self.sl_width = Slider(
            self.fig.add_axes([0.60, 0.30, 0.36, 0.02]),
            "Width mm", 0.3, 15, valinit=self.rings[self.selected]["widthMm"],
            color="#c9a96e")
        self.sl_width.on_changed(self._on_width)

        # Soundhole slider
        self.sl_sh = Slider(
            self.fig.add_axes([0.60, 0.26, 0.36, 0.02]),
            "Soundhole r", 30, 65, valinit=self.sound_r, color="#c9a96e")
        self.sl_sh.on_changed(self._on_sh)

        # Ring selection buttons (up/down + select)
        ax_prev = self.fig.add_axes([0.60, 0.19, 0.08, 0.04])
        ax_next = self.fig.add_axes([0.70, 0.19, 0.08, 0.04])
        self.btn_prev = Button(ax_prev, "< Prev", color="#0a0806", hovercolor="#1a1208")
        self.btn_next = Button(ax_next, "Next >", color="#0a0806", hovercolor="#1a1208")
        self.btn_prev.label.set_fontsize(7)
        self.btn_prev.label.set_color("#c9a96e")
        self.btn_next.label.set_fontsize(7)
        self.btn_next.label.set_color("#c9a96e")
        self.btn_prev.on_clicked(self._prev_ring)
        self.btn_next.on_clicked(self._next_ring)

        # Preset buttons
        preset_keys = list(PRESETS.keys())
        self.preset_btns = []
        for i, key in enumerate(preset_keys):
            ax_btn = self.fig.add_axes([0.82 + i * 0.06, 0.19, 0.05, 0.04])
            btn = Button(ax_btn, key.title(), color="#0a0806", hovercolor="#1a1208")
            btn.label.set_fontsize(7)
            btn.label.set_color("#c9a96e")
            btn.on_clicked(lambda _, k=key: self._load_preset(k))
            self.preset_btns.append(btn)

        # Stats text
        ax_stats = self.fig.add_axes([0.60, 0.12, 0.38, 0.05], facecolor="#080604")
        ax_stats.axis("off")
        self._stats_ax = ax_stats

        self._render()

    def _update_ring_info(self):
        ax = self._ring_info_ax
        ax.clear()
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        y = 0.95
        for i, ring in enumerate(self.rings):
            sel = ">>  " if i == self.selected else "    "
            wood = wood_by_id(ring["materials"][0])
            color = "#e8c87a" if i == self.selected else "#7a5c2e"
            ax.text(0.02, y, f"{sel}{ring['label']}",
                    fontsize=7, color=color, fontfamily="monospace", va="top")
            ax.text(0.60, y, f"{ring['type']:12s} {ring['widthMm']:.1f}mm",
                    fontsize=7, color="#4a3010", fontfamily="monospace", va="top")
            y -= 0.12

    def _update_stats(self):
        ax = self._stats_ax
        ax.clear()
        ax.axis("off")
        total = sum(r["widthMm"] for r in self.rings)
        outer = self.sound_r + total
        ax.text(0.0, 0.5,
                f"SH r={self.sound_r:.1f}mm  |  Band={total:.1f}mm  |  "
                f"Outer r={outer:.1f}mm  |  {len(self.rings)} rings  |  "
                f"Selected: {self.rings[self.selected]['label']}",
                fontsize=8, color="#c9a96e", fontfamily="monospace", va="center")

    def _on_type_change(self, label):
        self.rings[self.selected]["type"] = label
        self._render()

    def _on_width(self, val):
        self.rings[self.selected]["widthMm"] = val
        self._render()

    def _on_sh(self, val):
        self.sound_r = val
        self._render()

    def _prev_ring(self, _):
        self.selected = max(0, self.selected - 1)
        self._sync_controls()
        self._render()

    def _next_ring(self, _):
        self.selected = min(len(self.rings) - 1, self.selected + 1)
        self._sync_controls()
        self._render()

    def _sync_controls(self):
        ring = self.rings[self.selected]
        self.sl_width.set_val(ring["widthMm"])
        idx = TYPES.index(ring["type"]) if ring["type"] in TYPES else 0
        self.radio_type.set_active(idx)

    def _load_preset(self, key):
        if key in PRESETS:
            self.rings = [dict(r) for r in PRESETS[key]]
            self.selected = min(3, len(self.rings) - 1)
            self._sync_controls()
            self._render()

    def _render(self):
        render_wheel_fast(self.ax, self.rings, self.sound_r, self.selected)
        self._update_ring_info()
        self._update_stats()
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def main():
    viewer = RosetteStudioViewer()
    viewer.show()


if __name__ == "__main__":
    main()
