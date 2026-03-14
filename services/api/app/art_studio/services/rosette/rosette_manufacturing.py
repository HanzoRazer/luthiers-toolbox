"""
Rosette Manufacturing — BOM computation, manufacturing checks, and feasibility.

Handles bill of materials generation, manufacturing intelligence checks,
auto-fix operations, and RMOS feasibility scoring integration.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.art_studio.schemas.rosette_designer import (
    RING_DEFS,
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
    SymmetryMode,
)
from app.art_studio.schemas.rosette_params import RosetteParamSpec
from app.art_studio.schemas.rosette_feasibility import RosetteFeasibilitySummary
from app.rmos.api_contracts import RmosContext
from app.rmos.feasibility_scorer import score_design_feasibility

from .rosette_geometry import MFG_THRESHOLDS, MaterialSpec, ToolSpec, _arc_inches
from .rosette_design import get_tile_color_hex


# ─────────────────────────────────────────────────────────────────────────────
# Bill of Materials
# ─────────────────────────────────────────────────────────────────────────────

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
        inner_arc = _arc_inches(rd.r1, seg_ang)
        outer_arc = _arc_inches(rd.r2, seg_ang)
        mid_arc = _arc_inches(mid_r, seg_ang)
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
            tile_color_hex=get_tile_color_hex(tile_id),
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


def bom_to_csv(req: BomRequest, design_name: str = "Untitled Design") -> str:
    """Generate CSV string from BOM data."""
    bom = compute_bom(req)
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


# ─────────────────────────────────────────────────────────────────────────────
# Manufacturing Checks
# ─────────────────────────────────────────────────────────────────────────────

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
        inner_arc = _arc_inches(rd.r1, seg_ang)
        outer_arc = _arc_inches(rd.r2, seg_ang)
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
            tab_arc = _arc_inches(mid_r, rd.tab_ang_width)
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
        outer_arc = _arc_inches(320, seg_ang)
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


# ─────────────────────────────────────────────────────────────────────────────
# Auto-Fix Operations
# ─────────────────────────────────────────────────────────────────────────────

def auto_fix_short_arcs(grid: Dict[str, str], num_segs: int,
                        ring_active: List[bool]) -> Dict[str, str]:
    """Remove tiles from cells with arc length below fragile threshold."""
    seg_ang = 360.0 / num_segs
    new_grid = dict(grid)
    for ri, rd in enumerate(RING_DEFS):
        if not ring_active[ri]:
            continue
        min_arc = min(
            _arc_inches(rd.r1, seg_ang),
            _arc_inches(rd.r2, seg_ang)
        )
        if min_arc < MFG_THRESHOLDS["FRAGILE_ARC"]:
            for si in range(num_segs):
                new_grid.pop(f"{ri}-{si}", None)
    return new_grid


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


# ─────────────────────────────────────────────────────────────────────────────
# Feasibility Scoring
# ─────────────────────────────────────────────────────────────────────────────

def check_feasibility(
    spec: RosetteParamSpec,
    default_material: Optional[MaterialSpec] = None,
    default_tool: Optional[ToolSpec] = None,
) -> RosetteFeasibilitySummary:
    """
    Estimate feasibility for a rosette design.

    Returns a lightweight summary suitable for batch preview operations.
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
