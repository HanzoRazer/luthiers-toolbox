"""
RosetteEngine — Unified rosette design, geometry, manufacturing, and rendering.

Consolidates:
- rosette_designer.py (geometry, BOM, MFG checks, recipes, SVG preview)
- rosette_feasibility_scorer.py (RMOS feasibility wrapper)

All geometry in SVG units (1 unit = 0.01 inch). Inch conversions at boundaries.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from app.art_studio.schemas.rosette_designer import (
    RING_DEFS,
    TILE_CATS,
    TILE_MAP,
    BomMaterialEntry,
    BomPerRingDetail,
    BomRequest,
    BomResponse,
    BomRingEntry,
    MfgCheckRequest,
    MfgCheckResponse,
    MfgFlag,
    MfgFlagCellRef,
    MfgSeverity,
    RecipePreset,
    RingDef,
    SymmetryMode,
)
from app.art_studio.schemas.rosette_params import RosetteParamSpec
from app.art_studio.schemas.rosette_feasibility import RosetteFeasibilitySummary
from app.rmos.api_contracts import RmosContext, RiskBucket
from app.rmos.feasibility_scorer import score_design_feasibility


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MFG_THRESHOLDS = {
    "FRAGILE_ARC": 0.060,
    "FRAGILE_DEPTH": 0.060,
    "NARROW_ARC": 0.100,
    "NARROW_DEPTH": 0.080,
    "MAX_SEGS_OUTER": 24,
    "THIN_TAB_ARC": 0.050,
}

_TILE_FILL_MAP = {
    "solid": lambda t: t.get("color", "#888"),
    "abalone": lambda _: "url(#pat-abalone)",
    "mop": lambda _: "url(#pat-mop)",
    "burl": lambda _: "url(#pat-burl)",
    "herringbone": lambda _: "url(#pat-herringbone)",
    "checker": lambda _: "url(#pat-checker)",
    "celtic": lambda _: "url(#pat-celtic)",
    "diagonal": lambda _: "url(#pat-diagonal)",
    "dots": lambda _: "url(#pat-dots)",
    "stripes": lambda _: "url(#pat-bwb)",
    "stripes2": lambda _: "url(#pat-rbr)",
    "stripes3": lambda _: "url(#pat-wbw)",
    "clear": lambda _: "none",
}

_TILE_COLOR_HEX = {
    "abalone": "#50c8c0", "mop": "#e8e0f0", "burl": "#C8A048",
    "herringbone": "#C09850", "checker": "#8a8a6a", "celtic": "#2a6a4a",
    "diagonal": "#c8922a", "dots": "#e8d8b8",
    "stripes": "#444", "stripes2": "#882233", "stripes3": "#aaa",
    "clear": "none",
}

_SVG_DEFS = """
<linearGradient id="g-abalone" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#6ae0d0"/><stop offset="28%" stop-color="#50c8e8"/>
  <stop offset="55%" stop-color="#8860d0"/><stop offset="78%" stop-color="#50e890"/>
  <stop offset="100%" stop-color="#60b8e8"/>
</linearGradient>
<pattern id="pat-abalone" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">
  <rect width="28" height="28" fill="url(#g-abalone)" opacity="0.88"/>
  <ellipse cx="9" cy="9" rx="7" ry="4" fill="rgba(255,255,255,0.18)" transform="rotate(-30,9,9)"/>
  <ellipse cx="20" cy="20" rx="5" ry="3" fill="rgba(255,255,255,0.12)" transform="rotate(20,20,20)"/>
</pattern>
<linearGradient id="g-mop" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#f0f0ee"/><stop offset="45%" stop-color="#e8ddf8"/>
  <stop offset="100%" stop-color="#d8f0ee"/>
</linearGradient>
<pattern id="pat-mop" x="0" y="0" width="18" height="18" patternUnits="userSpaceOnUse">
  <rect width="18" height="18" fill="url(#g-mop)"/>
  <line x1="0" y1="9" x2="18" y2="9" stroke="rgba(200,190,220,0.28)" stroke-width="0.5"/>
  <line x1="9" y1="0" x2="9" y2="18" stroke="rgba(200,190,220,0.2)" stroke-width="0.5"/>
</pattern>
<pattern id="pat-burl" x="0" y="0" width="22" height="15" patternUnits="userSpaceOnUse">
  <rect width="22" height="15" fill="#C8A048"/>
  <ellipse cx="6" cy="7" rx="4.5" ry="2.5" fill="none" stroke="#a07828" stroke-width="1" opacity="0.55"/>
  <ellipse cx="15" cy="5" rx="3.5" ry="2" fill="none" stroke="#b09030" stroke-width="0.8" opacity="0.5"/>
</pattern>
<pattern id="pat-herringbone" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
  <rect width="20" height="20" fill="#C09850"/>
  <line x1="-2" y1="12" x2="8" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
  <line x1="2" y1="16" x2="14" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
  <line x1="7" y1="20" x2="20" y2="4" stroke="#7a5c28" stroke-width="2.8"/>
  <line x1="10" y1="-2" x2="22" y2="14" stroke="#5a3c10" stroke-width="2.8"/>
  <line x1="5" y1="-2" x2="20" y2="16" stroke="#5a3c10" stroke-width="2.8"/>
  <line x1="-2" y1="4" x2="12" y2="20" stroke="#5a3c10" stroke-width="2.8"/>
</pattern>
<pattern id="pat-checker" x="0" y="0" width="14" height="14" patternUnits="userSpaceOnUse">
  <rect width="14" height="14" fill="#f0e8d8"/>
  <rect x="0" y="0" width="7" height="7" fill="#1a1a1a"/>
  <rect x="7" y="7" width="7" height="7" fill="#1a1a1a"/>
</pattern>
<pattern id="pat-celtic" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
  <rect width="24" height="24" fill="#1a3a2a"/>
  <path d="M4,4 Q12,12 20,4 Q12,0 4,4Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
  <path d="M4,20 Q12,12 20,20 Q12,24 4,20Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
  <circle cx="12" cy="12" r="3" fill="none" stroke="#50c880" stroke-width="1.5"/>
</pattern>
<pattern id="pat-diagonal" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
  <rect width="12" height="12" fill="#c8922a"/>
  <line x1="-2" y1="10" x2="10" y2="-2" stroke="#8B5a10" stroke-width="3.5"/>
  <line x1="4" y1="14" x2="14" y2="4" stroke="#8B5a10" stroke-width="3.5"/>
</pattern>
<pattern id="pat-dots" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
  <rect width="12" height="12" fill="#f5e6c8"/>
  <circle cx="6" cy="6" r="2.4" fill="#1a1a1a"/>
</pattern>
<pattern id="pat-bwb" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
  <rect x="0" y="0" width="9" height="3" fill="#111"/>
  <rect x="0" y="3" width="9" height="3" fill="#eee"/>
  <rect x="0" y="6" width="9" height="3" fill="#111"/>
</pattern>
<pattern id="pat-rbr" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
  <rect x="0" y="0" width="9" height="3" fill="#cc0033"/>
  <rect x="0" y="3" width="9" height="3" fill="#111"/>
  <rect x="0" y="6" width="9" height="3" fill="#cc0033"/>
</pattern>
<pattern id="pat-wbw" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
  <rect x="0" y="0" width="9" height="3" fill="#eee"/>
  <rect x="0" y="3" width="9" height="3" fill="#111"/>
  <rect x="0" y="6" width="9" height="3" fill="#eee"/>
</pattern>
<radialGradient id="g-soundhole" cx="50%" cy="50%" r="50%">
  <stop offset="0%" stop-color="#060402"/>
  <stop offset="100%" stop-color="#0d0905"/>
</radialGradient>"""


# ─────────────────────────────────────────────────────────────────────────────
# Feasibility Specs (absorbed from rosette_feasibility_scorer.py)
# ─────────────────────────────────────────────────────────────────────────────

class MaterialSpec:
    """Minimal material specification for feasibility checks."""
    def __init__(self, material_id: str, name: str, material_class: str):
        self.material_id = material_id
        self.name = name
        self.material_class = material_class


class ToolSpec:
    """Minimal tool specification for feasibility checks."""
    def __init__(
        self,
        tool_id: str,
        diameter_mm: float,
        flutes: int,
        tool_material: str,
        stickout_mm: float,
    ):
        self.tool_id = tool_id
        self.diameter_mm = diameter_mm
        self.flutes = flutes
        self.tool_material = tool_material
        self.stickout_mm = stickout_mm


# ─────────────────────────────────────────────────────────────────────────────
# RosetteEngine
# ─────────────────────────────────────────────────────────────────────────────

class RosetteEngine:
    """
    Unified rosette design engine.

    Consolidates geometry, BOM, manufacturing checks, feasibility scoring,
    recipe presets, and SVG rendering into a single cohesive class.
    """

    # ───────────────────────────────────────────────────────────────────────
    # GEOMETRY METHODS (static helpers)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def _rad(deg: float) -> float:
        """Convert degrees to radians."""
        return deg * math.pi / 180.0

    @staticmethod
    def _pt_on_circle(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
        """Get point on circle at given angle (0° = top, clockwise)."""
        a = RosetteEngine._rad(deg - 90)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    @staticmethod
    def _fmt(n: float) -> str:
        """Format number for SVG output."""
        return f"{n:.3f}"

    @staticmethod
    def _arc_inches(r_svg: float, ang_deg: float) -> float:
        """Arc length in inches given radius in SVG units and angle in degrees."""
        return r_svg * ang_deg * math.pi / 180.0 / 100.0

    @staticmethod
    def arc_cell_path(cx: float, cy: float, r1: float, r2: float,
                      a1: float, a2: float) -> str:
        """Build SVG arc cell path between two radii and two angles."""
        x1i, y1i = RosetteEngine._pt_on_circle(cx, cy, r1, a1)
        x1o, y1o = RosetteEngine._pt_on_circle(cx, cy, r2, a1)
        x2o, y2o = RosetteEngine._pt_on_circle(cx, cy, r2, a2)
        x2i, y2i = RosetteEngine._pt_on_circle(cx, cy, r1, a2)
        lg = 1 if (a2 - a1) > 180 else 0
        fmt = RosetteEngine._fmt
        return (
            f"M {fmt(x1i)} {fmt(y1i)} L {fmt(x1o)} {fmt(y1o)} "
            f"A {r2} {r2} 0 {lg} 1 {fmt(x2o)} {fmt(y2o)} "
            f"L {fmt(x2i)} {fmt(y2i)} "
            f"A {r1} {r1} 0 {lg} 0 {fmt(x1i)} {fmt(y1i)} Z"
        )

    @staticmethod
    def tab_path(cx: float, cy: float, r_inner: float, r_outer: float,
                 mid_angle: float, half_width: float) -> str:
        """Build SVG path for an extension tab."""
        fmt = RosetteEngine._fmt
        x1, y1 = RosetteEngine._pt_on_circle(cx, cy, r_inner, mid_angle - half_width)
        x2, y2 = RosetteEngine._pt_on_circle(cx, cy, r_outer, mid_angle - half_width)
        x3, y3 = RosetteEngine._pt_on_circle(cx, cy, r_outer, mid_angle + half_width)
        x4, y4 = RosetteEngine._pt_on_circle(cx, cy, r_inner, mid_angle + half_width)
        return (
            f"M {fmt(x1)} {fmt(y1)} L {fmt(x2)} {fmt(y2)} "
            f"L {fmt(x3)} {fmt(y3)} L {fmt(x4)} {fmt(y4)} Z"
        )

    # ───────────────────────────────────────────────────────────────────────
    # DESIGN METHODS (tile placement, symmetry, cell info)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_tile_fill(tile_id: str) -> str:
        """Return SVG fill string for a tile id."""
        if not tile_id or tile_id == "clear":
            return "none"
        tile = TILE_MAP.get(tile_id)
        if not tile:
            return "#888"
        fn = _TILE_FILL_MAP.get(tile["type"], lambda _: "#888")
        return fn(tile)

    @staticmethod
    def get_tile_color_hex(tile_id: str) -> str:
        """Return simple hex color (for previews where patterns can't render)."""
        tile = TILE_MAP.get(tile_id)
        if not tile:
            return "#666"
        if tile["type"] == "solid":
            return tile.get("color", "#666")
        return _TILE_COLOR_HEX.get(tile["type"], "#666")

    @staticmethod
    def get_symmetry_cells(ring_idx: int, seg_idx: int, sym_mode: SymmetryMode,
                           num_segs: int) -> List[List[int]]:
        """Return list of [ring, seg] pairs affected by symmetry."""
        pairs: List[List[int]] = []
        if sym_mode == SymmetryMode.NONE:
            pairs = [[ring_idx, seg_idx]]
        elif sym_mode == SymmetryMode.ROTATIONAL:
            pairs = [[ring_idx, s] for s in range(num_segs)]
        elif sym_mode == SymmetryMode.BILATERAL:
            pairs = [
                [ring_idx, seg_idx],
                [ring_idx, (num_segs - seg_idx) % num_segs],
            ]
        elif sym_mode == SymmetryMode.QUADRANT:
            step = num_segs // 4
            for i in range(4):
                s = (seg_idx + i * step) % num_segs
                pairs.append([ring_idx, s])
                pairs.append([ring_idx, (num_segs - s) % num_segs])

        # Deduplicate preserving order
        seen: set = set()
        result: List[List[int]] = []
        for r, s in pairs:
            key = f"{r}-{s}"
            if key not in seen:
                seen.add(key)
                result.append([r, s])
        return result

    @staticmethod
    def place_tile(grid: Dict[str, str], ring_idx: int, seg_idx: int,
                   tile_id: str, sym_mode: SymmetryMode, num_segs: int,
                   ring_active: List[bool]) -> Tuple[Dict[str, str], List[str]]:
        """Place a tile respecting symmetry. Returns (new_grid, affected_keys)."""
        new_grid = dict(grid)
        affected: List[str] = []
        cells = RosetteEngine.get_symmetry_cells(ring_idx, seg_idx, sym_mode, num_segs)
        for r, s in cells:
            if not ring_active[r]:
                continue
            key = f"{r}-{s}"
            if tile_id == "clear":
                new_grid.pop(key, None)
            else:
                new_grid[key] = tile_id
            affected.append(key)
        return new_grid, affected

    @staticmethod
    def get_cell_info(ring_idx: int, seg_idx: int, num_segs: int,
                      grid: Dict[str, str]) -> Dict[str, Any]:
        """Return hovered-cell info dict."""
        rd = RING_DEFS[ring_idx]
        seg_ang = 360.0 / num_segs
        mid_r = (rd.r1 + rd.r2) / 2
        arc_len = RosetteEngine._arc_inches(mid_r, seg_ang)
        depth_in = (rd.r2 - rd.r1) / 100.0
        key = f"{ring_idx}-{seg_idx}"
        tile_id = grid.get(key)
        tile = TILE_MAP.get(tile_id) if tile_id else None
        return {
            "zone": rd.label,
            "seg": f"{seg_idx + 1}/{num_segs}",
            "angle": f"{seg_ang:.1f}°",
            "depth_inches": f'{depth_in:.3f}"',
            "arc_len_inches": f'~{arc_len:.3f}"',
            "r1_inches": rd.inch1,
            "r2_inches": rd.inch2,
            "tile_name": tile["name"] if tile else None,
            "tile_id": tile_id,
        }

    # ───────────────────────────────────────────────────────────────────────
    # MANUFACTURING METHODS (BOM, checks, auto-fix, feasibility)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_bom(req: BomRequest) -> BomResponse:
        """Compute full bill of materials from grid state."""
        num_segs = req.num_segs
        grid = req.grid
        seg_ang = 360.0 / num_segs
        total_cells = len(RING_DEFS) * num_segs

        filled_keys = [k for k in grid if grid[k] and grid[k] != "clear"]

        # Per-material accumulator
        mats: Dict[str, Dict] = {}
        # Per-ring accumulator
        rings_acc = []
        for ri, rd in enumerate(RING_DEFS):
            rings_acc.append({
                "label": rd.label, "dot_color": rd.dot_color,
                "r1": rd.r1, "r2": rd.r2,
                "depth": (rd.r2 - rd.r1) / 100.0,
                "filled": 0, "total_cells": num_segs,
                "tiles": set(), "arc_total": 0.0,
            })

        for k in filled_keys:
            parts = k.split("-")
            ri, si = int(parts[0]), int(parts[1])
            tile_id = grid[k]
            rd = RING_DEFS[ri]
            mid_r = (rd.r1 + rd.r2) / 2
            inner_arc = RosetteEngine._arc_inches(rd.r1, seg_ang)
            outer_arc = RosetteEngine._arc_inches(rd.r2, seg_ang)
            mid_arc = RosetteEngine._arc_inches(mid_r, seg_ang)
            depth = (rd.r2 - rd.r1) / 100.0

            if tile_id not in mats:
                mats[tile_id] = {"pieces": 0, "arc_total": 0.0, "per_ring": {}}
            m = mats[tile_id]
            m["pieces"] += 1
            m["arc_total"] += mid_arc

            if ri not in m["per_ring"]:
                m["per_ring"][ri] = {
                    "count": 0, "arc_total": 0.0,
                    "inner_arc": inner_arc, "outer_arc": outer_arc,
                    "depth": depth, "mid_arc": mid_arc,
                }
            pr = m["per_ring"][ri]
            pr["count"] += 1
            pr["arc_total"] += mid_arc

            rings_acc[ri]["filled"] += 1
            rings_acc[ri]["arc_total"] += mid_arc
            rings_acc[ri]["tiles"].add(tile_id)

        # Build response
        total_pieces = len(filled_keys)
        mat_count = len(mats)
        total_arc = sum(m["arc_total"] for m in mats.values())
        fill_pct = (total_pieces / total_cells * 100) if total_cells > 0 else 0

        materials_out: List[BomMaterialEntry] = []
        for tile_id, m in sorted(mats.items(), key=lambda x: -x[1]["pieces"]):
            tile = TILE_MAP.get(tile_id)
            if not tile:
                continue
            per_ring_details: List[BomPerRingDetail] = []
            procurement: List[str] = []
            for ri_key in sorted(m["per_ring"].keys()):
                pr = m["per_ring"][ri_key]
                rd = RING_DEFS[ri_key]
                per_ring_details.append(BomPerRingDetail(
                    ring_label=rd.label,
                    count=pr["count"],
                    arc_total_inches=round(pr["arc_total"], 4),
                    inner_arc_inches=round(pr["inner_arc"], 4),
                    outer_arc_inches=round(pr["outer_arc"], 4),
                    depth_inches=round(pr["depth"], 4),
                    mid_arc_inches=round(pr["mid_arc"], 4),
                ))
                needed = round(pr["arc_total"] * 1.15, 2)
                zone_word = rd.label.split()[-1]
                procurement.append(f'{pr["depth"]:.3f}" × {needed}" strip ({zone_word})')

            materials_out.append(BomMaterialEntry(
                tile_id=tile_id,
                tile_name=tile["name"],
                tile_color_hex=RosetteEngine.get_tile_color_hex(tile_id),
                pieces=m["pieces"],
                arc_total_inches=round(m["arc_total"], 4),
                per_ring=per_ring_details,
                procurement_strips=procurement,
            ))

        rings_out: List[BomRingEntry] = []
        for ri, ra in enumerate(rings_acc):
            rd = RING_DEFS[ri]
            mat_names = [TILE_MAP[t]["name"] for t in ra["tiles"] if t in TILE_MAP]
            rings_out.append(BomRingEntry(
                label=ra["label"],
                dot_color=ra["dot_color"],
                depth_inches=round(ra["depth"], 4),
                r1_inches=rd.inch1,
                r2_inches=rd.inch2,
                filled=ra["filled"],
                total_cells=ra["total_cells"],
                material_names=mat_names,
                arc_total_inches=round(ra["arc_total"], 4),
            ))

        return BomResponse(
            filled_cells=total_pieces,
            total_cells=total_cells,
            material_count=mat_count,
            total_pieces=total_pieces,
            total_arc_inches=round(total_arc, 4),
            fill_percent=round(fill_pct, 1),
            materials=materials_out,
            rings=rings_out,
        )

    @staticmethod
    def bom_to_csv(req: BomRequest, design_name: str = "Untitled Design") -> str:
        """Generate CSV string from BOM data."""
        bom = RosetteEngine.compute_bom(req)
        rows = [
            "Material,Ring Zone,Pieces,Depth (in),Inner Arc (in),Outer Arc (in),"
            "Mid Arc (in),Total Mid Arc (in),Procurement Strip W (in),"
            "Procurement Strip L +15% (in)"
        ]
        for mat in bom.materials:
            for pr in mat.per_ring:
                rows.append(
                    f"{mat.tile_name},{pr.ring_label},{pr.count},"
                    f"{pr.depth_inches:.4f},{pr.inner_arc_inches:.4f},"
                    f"{pr.outer_arc_inches:.4f},{pr.mid_arc_inches:.4f},"
                    f"{pr.arc_total_inches:.4f},{pr.depth_inches:.4f},"
                    f"{pr.arc_total_inches * 1.15:.4f}"
                )
        return "\n".join(rows)

    @staticmethod
    def run_manufacturing_checks(req: MfgCheckRequest) -> MfgCheckResponse:
        """Run all 6 manufacturing intelligence checks."""
        num_segs = req.num_segs
        sym_mode = req.sym_mode
        grid = req.grid
        ring_active = req.ring_active
        show_tabs = req.show_tabs
        seg_ang = 360.0 / num_segs
        flags: List[MfgFlag] = []

        # Check 1: Arc length too short (fragile inlay)
        short_arc_cells: List[MfgFlagCellRef] = []
        narrow_arc_cells: List[MfgFlagCellRef] = []

        for ri, rd in enumerate(RING_DEFS):
            if not ring_active[ri]:
                continue
            inner_arc = RosetteEngine._arc_inches(rd.r1, seg_ang)
            outer_arc = RosetteEngine._arc_inches(rd.r2, seg_ang)
            min_arc = min(inner_arc, outer_arc)

            for si in range(num_segs):
                key = f"{ri}-{si}"
                if key not in grid:
                    continue
                if min_arc < MFG_THRESHOLDS["FRAGILE_ARC"]:
                    short_arc_cells.append(MfgFlagCellRef(
                        ri=ri, si=si, key=key, label=rd.label, val=min_arc
                    ))
                elif min_arc < MFG_THRESHOLDS["NARROW_ARC"]:
                    narrow_arc_cells.append(MfgFlagCellRef(
                        ri=ri, si=si, key=key, label=rd.label, val=min_arc
                    ))

        if short_arc_cells:
            flags.append(MfgFlag(
                id="short-arc", sev=MfgSeverity.ERROR,
                title="Pieces too narrow to cut",
                desc=(f"{len(short_arc_cells)} piece(s) have inner arc < "
                      f'{MFG_THRESHOLDS["FRAGILE_ARC"]}" — below minimum cuttable width.'),
                cells=short_arc_cells,
                fix="Reduce segment count or remove fill from these zones.",
                has_auto_fix=True,
            ))
        if narrow_arc_cells:
            flags.append(MfgFlag(
                id="narrow-arc", sev=MfgSeverity.WARNING,
                title="Narrow pieces — handle with care",
                desc=(f"{len(narrow_arc_cells)} piece(s) have inner arc between "
                      f'{MFG_THRESHOLDS["FRAGILE_ARC"]}" and {MFG_THRESHOLDS["NARROW_ARC"]}".'),
                cells=narrow_arc_cells,
                fix="Consider reducing segment count for these rings.",
            ))

        # Check 2: Ring depth too shallow
        shallow_errors: List[Dict] = []
        shallow_warns: List[Dict] = []

        for ri, rd in enumerate(RING_DEFS):
            if not ring_active[ri]:
                continue
            depth = (rd.r2 - rd.r1) / 100.0
            has_fill = any(k.startswith(f"{ri}-") and grid.get(k) for k in grid)
            if not has_fill:
                continue
            if depth < MFG_THRESHOLDS["FRAGILE_DEPTH"]:
                shallow_errors.append({"ri": ri, "label": rd.label, "depth": depth})
            elif depth < MFG_THRESHOLDS["NARROW_DEPTH"]:
                shallow_warns.append({"ri": ri, "label": rd.label, "depth": depth})

        if shallow_errors:
            labels = ", ".join(f'{s["label"]} ({s["depth"]:.3f}")' for s in shallow_errors)
            flags.append(MfgFlag(
                id="shallow-ring", sev=MfgSeverity.ERROR,
                title="Ring depth critically shallow",
                desc=f'{labels} — depth below {MFG_THRESHOLDS["FRAGILE_DEPTH"]}".',
                fix="These rings are geometry-locked. Consider removing fill from them.",
                has_auto_fix=True,
            ))
        if shallow_warns:
            labels = ", ".join(f'{s["label"]} ({s["depth"]:.3f}")' for s in shallow_warns)
            flags.append(MfgFlag(
                id="shallow-ring-warn", sev=MfgSeverity.WARNING,
                title="Shallow ring — requires thin strip",
                desc=(f'{labels} — depth between {MFG_THRESHOLDS["FRAGILE_DEPTH"]}" and '
                      f'{MFG_THRESHOLDS["NARROW_DEPTH"]}".'),
            ))

        # Check 3: Extension tab arc width
        if show_tabs:
            for ri, rd in enumerate(RING_DEFS):
                if not rd.has_tabs or not ring_active[ri]:
                    continue
                mid_r = (rd.r1 + rd.r2) / 2
                tab_arc = RosetteEngine._arc_inches(mid_r, rd.tab_ang_width)
                if tab_arc < MFG_THRESHOLDS["THIN_TAB_ARC"]:
                    flags.append(MfgFlag(
                        id=f"thin-tab-{ri}", sev=MfgSeverity.WARNING,
                        title="Extension tabs may be too narrow",
                        desc=(f'Main Channel tabs span {tab_arc:.3f}" arc. '
                              f"Consider disabling tabs or reducing segment count."),
                        fix="Disable extension tabs or reduce segment count.",
                    ))

        # Check 4: Mismatched purfling
        main_filled = any(k.startswith("2-") and grid.get(k) for k in grid)
        if main_filled:
            for ri in (1, 3):
                if not ring_active[ri]:
                    continue
                has_fill = any(k.startswith(f"{ri}-") and grid.get(k) for k in grid)
                if not has_fill:
                    flags.append(MfgFlag(
                        id=f"empty-purfling-{ri}", sev=MfgSeverity.INFO,
                        title=f"{RING_DEFS[ri].label} is empty",
                        desc=(f"Main Channel is filled but {RING_DEFS[ri].label} has no material."),
                    ))

        # Check 5: Segment count / symmetry mismatch
        if sym_mode == SymmetryMode.QUADRANT and num_segs % 4 != 0:
            flags.append(MfgFlag(
                id="sym-mismatch", sev=MfgSeverity.WARNING,
                title="Segment count not divisible by 4",
                desc=(f"Quadrant ×4 symmetry with {num_segs} segments creates uneven distribution."),
            ))
        if sym_mode == SymmetryMode.BILATERAL and num_segs % 2 != 0:
            flags.append(MfgFlag(
                id="sym-bilateral-odd", sev=MfgSeverity.INFO,
                title="Odd segment count with bilateral symmetry",
                desc=f"Bilateral symmetry on {num_segs} segments leaves one center segment unmirrored.",
            ))

        # Check 6: High segment count outer ring density
        if num_segs > MFG_THRESHOLDS["MAX_SEGS_OUTER"]:
            outer_arc = RosetteEngine._arc_inches(320, seg_ang)
            if outer_arc < MFG_THRESHOLDS["NARROW_ARC"]:
                flags.append(MfgFlag(
                    id="dense-outer", sev=MfgSeverity.WARNING,
                    title="Outer ring pieces very dense",
                    desc=(f"At {num_segs} segments, outer ring pieces are only {outer_arc:.3f}\" wide."),
                ))

        # Score computation
        errors = [f for f in flags if f.sev == MfgSeverity.ERROR]
        warnings = [f for f in flags if f.sev == MfgSeverity.WARNING]
        infos = [f for f in flags if f.sev == MfgSeverity.INFO]

        filled_cells = sum(1 for k in grid if grid.get(k))
        score = 100
        score -= len(errors) * 20
        score -= len(warnings) * 8
        score -= len(infos) * 2
        if filled_cells == 0:
            score = 0
        score = max(0, min(100, score))

        if score >= 80:
            score_class = "good"
        elif score >= 50:
            score_class = "ok"
        else:
            score_class = "bad"

        total_checks = 6
        passing = total_checks - len(errors) - len(warnings) - len(infos)

        return MfgCheckResponse(
            score=score,
            score_class=score_class,
            error_count=len(errors),
            warning_count=len(warnings),
            info_count=len(infos),
            passing_count=max(0, passing),
            flags=flags,
        )

    @staticmethod
    def auto_fix_short_arcs(grid: Dict[str, str], num_segs: int,
                            ring_active: List[bool]) -> Dict[str, str]:
        """Remove tiles from cells with arc length below fragile threshold."""
        seg_ang = 360.0 / num_segs
        new_grid = dict(grid)
        for ri, rd in enumerate(RING_DEFS):
            if not ring_active[ri]:
                continue
            min_arc = min(
                RosetteEngine._arc_inches(rd.r1, seg_ang),
                RosetteEngine._arc_inches(rd.r2, seg_ang)
            )
            if min_arc < MFG_THRESHOLDS["FRAGILE_ARC"]:
                for si in range(num_segs):
                    new_grid.pop(f"{ri}-{si}", None)
        return new_grid

    @staticmethod
    def auto_fix_shallow_rings(grid: Dict[str, str], num_segs: int,
                               ring_active: List[bool]) -> Dict[str, str]:
        """Remove tiles from rings with depth below fragile threshold."""
        new_grid = dict(grid)
        for ri, rd in enumerate(RING_DEFS):
            if not ring_active[ri]:
                continue
            depth = (rd.r2 - rd.r1) / 100.0
            if depth < MFG_THRESHOLDS["FRAGILE_DEPTH"]:
                for si in range(num_segs):
                    new_grid.pop(f"{ri}-{si}", None)
        return new_grid

    @staticmethod
    def check_feasibility(
        spec: RosetteParamSpec,
        default_material: Optional[MaterialSpec] = None,
        default_tool: Optional[ToolSpec] = None,
    ) -> RosetteFeasibilitySummary:
        """
        Estimate feasibility for a rosette design.

        Returns a lightweight summary suitable for batch preview operations.
        Absorbed from rosette_feasibility_scorer.py.
        """
        ctx = RmosContext(
            material_id=default_material.material_id if default_material else "default-ebony",
            tool_id=default_tool.tool_id if default_tool else "default-vbit",
        )
        result = score_design_feasibility(spec, ctx, workflow_mode="design_first")
        return RosetteFeasibilitySummary(
            overall_score=result.score,
            risk_bucket=result.risk_bucket,
            material_efficiency=result.efficiency or 85.0,
            estimated_cut_time_min=(result.estimated_cut_time_seconds or 300.0) / 60.0,
            warnings=result.warnings or [],
        )

    # ───────────────────────────────────────────────────────────────────────
    # PRESET/RECIPE METHODS
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_grid(num_segs: int, fills: List) -> Dict[str, str]:
        """Build a grid dict from fill specs."""
        g: Dict[str, str] = {}
        for entry in fills:
            if len(entry) == 2:
                ri, tid = entry
                for s in range(num_segs):
                    g[f"{ri}-{s}"] = tid
            elif len(entry) == 3:
                ri, si, tid = entry
                g[f"{ri}-{si}"] = tid
            elif len(entry) == 4:
                ri, start, step, tid = entry
                s = start
                while s < num_segs:
                    g[f"{ri}-{s}"] = tid
                    s += step
        return g

    @staticmethod
    def _build_alternating(num_segs: int, ring: int, even_tile: str, odd_tile: str,
                           base_fills: List) -> Dict[str, str]:
        """Build grid with alternating main channel and fixed other rings."""
        g = RosetteEngine._make_grid(num_segs, base_fills)
        for s in range(num_segs):
            g[f"{ring}-{s}"] = even_tile if s % 2 == 0 else odd_tile
        return g

    @staticmethod
    def get_recipes() -> List[RecipePreset]:
        """Return all 8 named recipe presets."""
        return [
            RecipePreset(
                id="vintage-martin", name="Vintage Martin",
                desc="Alternating rosewood & maple main channel with B/W/B purfling.",
                tags=["12 seg", "traditional", "wood"],
                num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True] * 5,
                grid=RosetteEngine._build_alternating(12, 2, "rosewood", "maple", [
                    [0, "maple"], [1, "bwb"], [3, "bwb"], [4, "rosewood"],
                ]),
            ),
            RecipePreset(
                id="shell-classic", name="Shell Classic",
                desc="Full abalone main channel with MOP purfling and ebony binding.",
                tags=["12 seg", "shell", "premium"],
                num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True] * 5,
                grid=RosetteEngine._make_grid(12, [
                    [0, "cream"], [1, "bwb"], [2, "abalone"], [3, "bwb"], [4, "ebony"],
                ]),
            ),
            RecipePreset(
                id="herringbone-band", name="Herringbone Band",
                desc="Full herringbone main channel with B/W/B purfling. D-28 style.",
                tags=["12 seg", "herringbone", "traditional"],
                num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True] * 5,
                grid=RosetteEngine._make_grid(12, [
                    [0, "maple"], [1, "bwb"], [2, "herringbone"], [3, "bwb"], [4, "rosewood"],
                ]),
            ),
            RecipePreset(
                id="celtic-ring", name="Celtic Ring",
                desc="Celtic knot motif throughout the main channel with walnut binding.",
                tags=["12 seg", "celtic", "ornate"],
                num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True] * 5,
                grid=RosetteEngine._make_grid(12, [
                    [0, "walnut"], [1, "wbw"], [2, "celtic"], [3, "wbw"], [4, "walnut"],
                ]),
            ),
            RecipePreset(
                id="checkerboard-mosaic", name="Checkerboard Mosaic",
                desc="Dense checkerboard mosaic on 16 segments for geometric pattern.",
                tags=["16 seg", "geometric", "mosaic"],
                num_segs=16, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True] * 5,
                grid=RosetteEngine._make_grid(16, [
                    [0, "ebony"], [1, "bwb"], [2, "checker"], [3, "bwb"], [4, "ebony"],
                ]),
            ),
            RecipePreset(
                id="minimalist", name="Minimalist",
                desc="Sparse design with only binding rings active. Clean purfling lines.",
                tags=["12 seg", "minimal", "modern"],
                num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True, True, False, True, True],
                grid=RosetteEngine._make_grid(12, [
                    [0, "cream"], [1, "bwb"], [3, "bwb"], [4, "mahogany"],
                ]),
            ),
            RecipePreset(
                id="abalone-burst", name="Abalone Burst",
                desc="Alternating abalone and MOP segments create shimmer effect.",
                tags=["12 seg", "shell", "burst"],
                num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True] * 5,
                grid=RosetteEngine._build_alternating(12, 2, "abalone", "mop", [
                    [0, "cream"], [1, "mop"], [3, "mop"], [4, "ebony"],
                ]),
            ),
            RecipePreset(
                id="rosewood-maple", name="Rosewood & Maple",
                desc="Alternating rosewood and figured maple with W/B/W purfling.",
                tags=["12 seg", "wood", "alternating"],
                num_segs=12, sym_mode=SymmetryMode.ROTATIONAL,
                ring_active=[True] * 5,
                grid=RosetteEngine._build_alternating(12, 2, "rosewood", "maple", [
                    [0, "maple"], [1, "wbw"], [3, "wbw"], [4, "rosewood"],
                ]),
            ),
        ]

    # ───────────────────────────────────────────────────────────────────────
    # RENDERING METHODS (SVG preview)
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def render_preview_svg(
        num_segs: int,
        grid: Dict[str, str],
        ring_active: List[bool],
        show_tabs: bool = True,
        show_annotations: bool = False,
        width: int = 620,
        height: int = 620,
    ) -> str:
        """Render a full SVG preview of the rosette wheel."""
        cx = width / 2
        cy = height / 2
        seg_ang = 360.0 / num_segs
        parts: List[str] = []
        fmt = RosetteEngine._fmt

        parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                     f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
        parts.append(f"<defs>{_SVG_DEFS}</defs>")

        # Background
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="354" fill="none" '
                     f'stroke="rgba(200,146,42,0.12)" stroke-width="8"/>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="148" fill="url(#g-soundhole)" '
                     f'stroke="rgba(200,146,42,0.45)" stroke-width="1.2"/>')

        # Ring backgrounds
        for ri, rd in enumerate(RING_DEFS):
            bg_fill = (("#12282e" if ri == 2 else rd.color)
                       if ring_active[ri] else "rgba(20,18,14,0.5)")
            opacity = 1 if ring_active[ri] else 0.35
            d = RosetteEngine.arc_cell_path(cx, cy, rd.r1, rd.r2, 0, 359.999)
            parts.append(f'<path d="{d}" fill="{bg_fill}" stroke="none" opacity="{opacity}"/>')

        # Cells
        for ri, rd in enumerate(RING_DEFS):
            for si in range(num_segs):
                a1 = si * seg_ang
                a2 = (si + 1) * seg_ang
                key = f"{ri}-{si}"
                d = RosetteEngine.arc_cell_path(cx, cy, rd.r1, rd.r2, a1, a2)
                fill = RosetteEngine.get_tile_fill(grid.get(key, "")) if key in grid else "none"
                parts.append(f'<path d="{d}" fill="{fill}"/>')

        # Extension tabs
        if show_tabs:
            for ri, rd in enumerate(RING_DEFS):
                if not rd.has_tabs or not ring_active[ri]:
                    continue
                half_aw = rd.tab_ang_width / 2
                for si in range(num_segs):
                    mid = (si + 0.5) * seg_ang
                    tile_id = grid.get(f"{ri}-{si}", "")
                    if tile_id:
                        fill = RosetteEngine.get_tile_fill(tile_id)
                    else:
                        fill = rd.tab_fill_even if si % 2 == 0 else rd.tab_fill_odd
                    # Outer tab
                    d_outer = RosetteEngine.tab_path(cx, cy, rd.r2, rd.tab_outer_r, mid, half_aw)
                    parts.append(f'<path d="{d_outer}" fill="{fill}" stroke="#1a1a2e" '
                                 f'stroke-width="0.7" opacity="0.92"/>')
                    # Inner tab
                    d_inner = RosetteEngine.tab_path(cx, cy, rd.tab_inner_r, rd.r1, mid, half_aw)
                    parts.append(f'<path d="{d_inner}" fill="{fill}" stroke="#1a1a2e" '
                                 f'stroke-width="0.7" opacity="0.85"/>')

        # Guide circles and radial lines
        for r in [150, 190, 200, 210, 300, 312, 320, 350]:
            is_tab = r in (200, 312)
            stroke = "rgba(200,146,42,0.18)" if is_tab else "rgba(200,146,42,0.38)"
            sw = 0.4 if is_tab else 0.7
            dash = 'stroke-dasharray="2,3"' if is_tab else ""
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                         f'stroke="{stroke}" stroke-width="{sw}" {dash}/>')
        for si in range(num_segs):
            angle = si * seg_ang
            x1, y1 = RosetteEngine._pt_on_circle(cx, cy, 150, angle)
            x2, y2 = RosetteEngine._pt_on_circle(cx, cy, 350, angle)
            parts.append(f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" '
                         f'y2="{fmt(y2)}" stroke="rgba(200,146,42,0.28)" stroke-width="0.55"/>')

        # Center crosshair
        parts.append(f'<line x1="{cx-14}" y1="{cy}" x2="{cx+14}" y2="{cy}" '
                     f'stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>')
        parts.append(f'<line x1="{cx}" y1="{cy-14}" x2="{cx}" y2="{cy+14}" '
                     f'stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="none" '
                     f'stroke="rgba(200,146,42,0.55)" stroke-width="0.8"/>')

        # Annotation layer (drafting mode)
        if show_annotations:
            parts.append(RosetteEngine._build_annotations_svg(cx, cy, num_segs, seg_ang))

        parts.append("</svg>")
        return "\n".join(parts)

    @staticmethod
    def _build_annotations_svg(cx: float, cy: float, num_segs: int, seg_ang: float) -> str:
        """Build the drafting annotation overlay SVG group."""
        ds = "#1a1a2e"
        fmt = RosetteEngine._fmt
        lines: List[str] = []
        lines.append(f'<rect x="0" y="0" width="{int(cx*2)}" height="{int(cy*2)}" '
                     f'fill="#f5f0e8" opacity="0.85"/>')
        # Diameter dimensions
        for r, label in [(350, 'Ø 7.00"'), (300, 'Ø 6.00"'), (150, 'Ø 3.00"')]:
            y_line = cy - r - 15 if r > 200 else cy + 20
            lines.append(f'<line x1="{fmt(cx - r)}" y1="{fmt(y_line)}" '
                         f'x2="{fmt(cx + r)}" y2="{fmt(y_line)}" '
                         f'stroke="{ds}" stroke-width="0.7" fill="none"/>')
            lines.append(f'<text x="{fmt(cx)}" y="{fmt(y_line - 5)}" fill="{ds}" '
                         f'font-family="monospace" font-size="8" text-anchor="middle">{label}</text>')

        # Zone labels
        zones = [
            (335, "Outer Binding 0.30\""), (310, "Outer Purfling 0.20\""),
            (255, "Main Channel 0.90\""), (200, "Inner Purfling 0.20\""),
            (170, "Soundhole Bind 0.40\""),
        ]
        lx = cx + 160
        for i, (r, label) in enumerate(zones):
            px, py = RosetteEngine._pt_on_circle(cx, cy, r, 75)
            ly = cy - 140 + i * 40
            lines.append(f'<line x1="{fmt(px)}" y1="{fmt(py)}" '
                         f'x2="{fmt(lx)}" y2="{fmt(ly)}" '
                         f'stroke="{ds}" stroke-width="0.55" fill="none"/>')
            lines.append(f'<text x="{fmt(lx + 4)}" y="{fmt(ly + 3)}" fill="{ds}" '
                         f'font-family="monospace" font-size="7.5">{label}</text>')

        # Segment count label
        lines.append(f'<text x="{fmt(cx)}" y="{fmt(cy + 180)}" fill="{ds}" '
                     f'font-family="monospace" font-size="8" text-anchor="middle">'
                     f'{num_segs} EQUAL DIVISIONS × {seg_ang:.1f}°</text>')

        # Section line A-A
        lines.append(f'<line x1="30" y1="{fmt(cy)}" x2="{fmt(cx*2 - 30)}" y2="{fmt(cy)}" '
                     f'stroke="{ds}" stroke-width="0.8" stroke-dasharray="8,4,2,4"/>')

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Backward compatibility exports (module-level functions that delegate)
# ─────────────────────────────────────────────────────────────────────────────

# Geometry
arc_cell_path = RosetteEngine.arc_cell_path
tab_path = RosetteEngine.tab_path

# Design
get_tile_fill = RosetteEngine.get_tile_fill
get_tile_color_hex = RosetteEngine.get_tile_color_hex
get_sym_cells = RosetteEngine.get_symmetry_cells
place_tile = RosetteEngine.place_tile
cell_info = RosetteEngine.get_cell_info

# Manufacturing
compute_bom = RosetteEngine.compute_bom
bom_to_csv = RosetteEngine.bom_to_csv
run_mfg_checks = RosetteEngine.run_manufacturing_checks
auto_fix_short_arcs = RosetteEngine.auto_fix_short_arcs
auto_fix_shallow_rings = RosetteEngine.auto_fix_shallow_rings
estimate_rosette_feasibility = RosetteEngine.check_feasibility

# Rendering - backward compatible wrapper (accepts PreviewRequest or kwargs)
def render_preview_svg(
    num_segs_or_req=None,
    grid: Optional[Dict[str, str]] = None,
    ring_active: Optional[List[bool]] = None,
    show_tabs: bool = True,
    show_annotations: bool = False,
    width: int = 620,
    height: int = 620,
    *,
    num_segs: Optional[int] = None,
) -> str:
    """Render preview SVG. Accepts PreviewRequest object or keyword args."""
    # Handle keyword-only num_segs (from route calls like num_segs=12)
    if num_segs is not None:
        return RosetteEngine.render_preview_svg(
            num_segs=num_segs,
            grid=grid or {},
            ring_active=ring_active or [True] * 5,
            show_tabs=show_tabs,
            show_annotations=show_annotations,
            width=width,
            height=height,
        )
    # Handle PreviewRequest-like object (from unit tests)
    if hasattr(num_segs_or_req, "num_segs"):
        req = num_segs_or_req
        return RosetteEngine.render_preview_svg(
            num_segs=req.num_segs,
            grid=req.grid,
            ring_active=req.ring_active,
            show_tabs=getattr(req, "show_tabs", True),
            show_annotations=getattr(req, "show_annotations", False),
            width=getattr(req, "width", 620),
            height=getattr(req, "height", 620),
        )
    # Handle int as first positional arg
    if isinstance(num_segs_or_req, int):
        return RosetteEngine.render_preview_svg(
            num_segs=num_segs_or_req,
            grid=grid or {},
            ring_active=ring_active or [True] * 5,
            show_tabs=show_tabs,
            show_annotations=show_annotations,
            width=width,
            height=height,
        )
    raise ValueError("render_preview_svg requires num_segs (int) or PreviewRequest")

# Recipes
RECIPES = RosetteEngine.get_recipes()
