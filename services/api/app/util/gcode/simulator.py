"""
G-code State Machine Simulator

Executes G-code programs with modal state tracking, calculating
travel distances, cut times, and generating backplot points.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .geometry import arc_center_from_ijk, arc_center_from_r, arc_len, dist2d, interpolate_arc_points
from .lexer import parse_lines
from .types import Modal


def _parse_block_words(blk: Dict[str, Any], u: float) -> Dict[str, Any]:
    """Extract typed values from a parsed block, applying unit factor *u*.

    P6 Extension: Now extracts T (tool), S (spindle), M (misc) codes for
    multi-tool visualization and chip load analysis.
    """
    out: Dict[str, Any] = {
        'g': None, 'x': None, 'y': None, 'z': None,
        'f': None, 'i': None, 'j': None, 'r': None,
        't': None, 's': None, 'm': None
    }
    for letter, val in blk["words"]:
        if letter == 'G':
            out['g'] = int(val)
        elif letter in ('X', 'Y', 'Z', 'I', 'J', 'R'):
            out[letter.lower()] = val * u
        elif letter == 'F':
            out['f'] = val * (u / 1.0)
        elif letter == 'T':
            out['t'] = int(val)
        elif letter == 'S':
            out['s'] = float(val)
        elif letter == 'M':
            out['m'] = int(val)
    return out


def _update_modal_state(
    modal: Modal,
    g: int | None,
    f: float | None,
    t: int | None = None,
    s: float | None = None,
    m: int | None = None,
) -> None:
    """Apply G/F/T/S/M words to modal state in-place.

    P6 Extension: Added T (tool), S (spindle RPM), M (misc) code handling
    for multi-tool visualization and chip load analysis.

    Tool changes: T1, T2, etc. (actual change happens on M6)
    Spindle: M3 = CW, M4 = CCW, M5 = stop
    Spindle speed: S-code sets RPM
    """
    if f is not None:
        modal["F"] = max(0.1, float(f))
    if g is not None:
        if g in (0, 1, 2, 3):
            modal["G"] = g
        elif g == 20:
            modal["units"] = 25.4
        elif g == 21:
            modal["units"] = 1.0
        elif g in (17, 18, 19):
            modal["plane"] = g

    # P6: Tool change (T-code sets pending tool, M6 activates it)
    if t is not None:
        modal["pending_tool"] = t

    # P6: Spindle speed
    if s is not None:
        modal["S"] = max(0.0, float(s))

    # P6: M-codes for spindle control and tool change
    if m is not None:
        if m == 3:  # Spindle CW
            modal["spindle_on"] = True
            modal["spindle_dir"] = "cw"
        elif m == 4:  # Spindle CCW
            modal["spindle_on"] = True
            modal["spindle_dir"] = "ccw"
        elif m == 5:  # Spindle stop
            modal["spindle_on"] = False
        elif m == 6:  # Tool change - activate pending tool
            if "pending_tool" in modal:
                modal["T"] = modal["pending_tool"]


def _sim_linear(
    pos: Tuple[float, float, float],
    nx: float, ny: float, nz: float,
    code: int, rapid_mm_min: float,
    modal_f: float
) -> Tuple[float, float, bool]:
    """Simulate G0/G1 linear move. Returns (dxy, t, is_rapid)."""
    dxy = dist2d((pos[0], pos[1]), (nx, ny))
    if code == 0:
        return dxy, dxy / max(1e-6, rapid_mm_min), True
    return dxy, dxy / max(1e-6, modal_f), False


def _sim_arc_xy(
    pos: Tuple[float, float, float],
    nx: float, ny: float,
    code: int, i: float | None, j: float | None,
    r: float | None, modal_f: float
) -> Tuple[float, float]:
    """Simulate G2/G3 arc in XY plane. Returns (arc_length, t)."""
    if i is not None and j is not None:
        c = arc_center_from_ijk((pos[0], pos[1]), i, j)
        length = arc_len(c, (pos[0], pos[1]), (nx, ny), cw=(code == 2))
    elif r is not None:
        c_len = dist2d((pos[0], pos[1]), (nx, ny))
        if c_len < 1e-6:
            length = 2 * math.pi * abs(r)
        elif c_len > 2 * abs(r):
            length = c_len
        else:
            theta = 2 * math.asin(max(-1.0, min(1.0, c_len / (2 * abs(r)))))
            length = abs(theta) * abs(r)
    else:
        length = dist2d((pos[0], pos[1]), (nx, ny))
    return length, length / max(1e-6, modal_f)


def simulate(
    gcode: str,
    *,
    rapid_mm_min: float = 3000.0,
    default_feed_mm_min: float = 500.0,
    units: str = "mm"
) -> Dict[str, Any]:
    """
    Simulate G-code execution and calculate statistics.

    Args:
        gcode: G-code program text
        rapid_mm_min: Rapid traverse rate (G0) in mm/min
        default_feed_mm_min: Default feed rate when F not specified
        units: Input units ("mm" or "inch")

    Returns:
        Dict with:
        - travel_mm: Rapid traverse distance
        - cut_mm: Cutting (feed) distance
        - t_rapid_min: Rapid time in minutes
        - t_feed_min: Feed time in minutes
        - t_total_min: Total cycle time in minutes
        - points_xy: List of (x, y) points for backplot
    """
    u = 1.0 if units.lower().startswith('mm') else 25.4
    prog = parse_lines(gcode)

    modal: Modal = {"G": 0, "F": default_feed_mm_min, "units": u, "plane": 17}
    pos = (0.0, 0.0, 0.0)
    path_xy: List[Tuple[float, float]] = [(pos[0], pos[1])]
    travel = cut = t_rapid = t_feed = 0.0

    for blk in prog:
        w = _parse_block_words(blk, u)
        _update_modal_state(modal, w['g'], w['f'])
        u = modal["units"]

        nx = pos[0] if w['x'] is None else w['x']
        ny = pos[1] if w['y'] is None else w['y']
        nz = pos[2] if w['z'] is None else w['z']

        code = modal["G"]
        has_arc_params = (w['i'] is not None and w['j'] is not None) or (w['r'] is not None)
        position_changed = (nx != pos[0] or ny != pos[1] or nz != pos[2])

        if code in (0, 1, 2, 3) and (position_changed or (code in (2, 3) and has_arc_params)):
            if code in (0, 1):
                dxy, t, is_rapid = _sim_linear(pos, nx, ny, nz, code, rapid_mm_min, modal["F"])
                if is_rapid:
                    t_rapid += t
                    travel += dxy
                else:
                    t_feed += t
                    cut += dxy
                path_xy.append((nx, ny))
                pos = (nx, ny, nz)
            elif code in (2, 3) and modal["plane"] == 17:
                length, t = _sim_arc_xy(pos, nx, ny, code, w['i'], w['j'], w['r'], modal["F"])
                t_feed += t
                cut += length
                path_xy.append((nx, ny))
                pos = (nx, ny, nz)

    return {
        "travel_mm": travel,
        "cut_mm": cut,
        "t_rapid_min": t_rapid,
        "t_feed_min": t_feed,
        "t_total_min": t_rapid + t_feed,
        "points_xy": path_xy
    }


def simulate_segments(
    gcode: str,
    *,
    rapid_mm_min: float = 3000.0,
    default_feed_mm_min: float = 500.0,
    units: str = "mm",
    arc_resolution_deg: float = 5.0,
) -> Dict[str, Any]:
    """
    Simulate G-code and return per-segment move data for animation.

    Unlike simulate(), which returns aggregate totals, this function emits one
    segment dict per atomic G-code motion command. G2/G3 arcs are pre-interpolated
    into linear sub-segments at arc_resolution_deg granularity so the frontend
    renderer only needs lineTo() calls.

    Returns:
        Dict with:
        - segments: list of MoveSegment dicts
        - bounds: {x_min, x_max, y_min, y_max, z_min, z_max}
        - totals: {rapid_mm, cut_mm, time_min, segment_count}
    """
    u = 1.0 if units.lower().startswith("mm") else 25.4
    prog = parse_lines(gcode)

    # P6 Extension: Initialize modal with tool/spindle tracking
    modal: Modal = {
        "G": 0,
        "F": default_feed_mm_min,
        "units": u,
        "plane": 17,
        # P6: Tool state
        "T": 1,              # Current tool number (default T1)
        "pending_tool": 1,   # Pending tool (set by T-code, activated by M6)
        # P6: Spindle state
        "S": 0.0,            # Spindle RPM
        "spindle_on": False,
        "spindle_dir": "cw",
    }
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    segs: List[Dict[str, Any]] = []
    rapid_mm = cut_mm = 0.0
    tool_changes: List[Dict[str, Any]] = []  # P6: Track tool change points

    bb: Dict[str, float] = {
        "x_min": 0.0, "x_max": 0.0,
        "y_min": 0.0, "y_max": 0.0,
        "z_min": 0.0, "z_max": 0.0,
    }

    def _expand_bb(x: float, y: float, z: float) -> None:
        bb["x_min"] = min(bb["x_min"], x)
        bb["x_max"] = max(bb["x_max"], x)
        bb["y_min"] = min(bb["y_min"], y)
        bb["y_max"] = max(bb["y_max"], y)
        bb["z_min"] = min(bb["z_min"], z)
        bb["z_max"] = max(bb["z_max"], z)

    def _emit_segment(
        seg_type: str,
        from_p: Tuple[float, float, float],
        to_p: Tuple[float, float, float],
        feed: float,
        line_number: int,
        line_text: str,
    ) -> None:
        dist = math.hypot(to_p[0] - from_p[0], to_p[1] - from_p[1])
        duration_ms = (dist / max(1e-6, feed)) * 60_000.0
        segs.append({
            "type": seg_type,
            "from_pos": list(from_p),
            "to_pos": list(to_p),
            "feed": feed,
            "duration_ms": duration_ms,
            "line_number": line_number,
            "line_text": line_text,
            # P6 Extension: Tool and spindle state for multi-tool visualization
            "tool_number": modal.get("T", 1),
            "spindle_rpm": modal.get("S", 0.0),
            "spindle_on": modal.get("spindle_on", False),
        })
        _expand_bb(*to_p)

    for line_idx, blk in enumerate(prog):
        w = _parse_block_words(blk, u)
        prev_tool = modal.get("T", 1)
        _update_modal_state(modal, w["g"], w["f"], w["t"], w["s"], w["m"])
        u = modal["units"]

        # P6: Track tool changes
        curr_tool = modal.get("T", 1)
        if curr_tool != prev_tool:
            tool_changes.append({
                "line_number": line_idx + 1,
                "from_tool": prev_tool,
                "to_tool": curr_tool,
                "position": list(pos),
            })

        nx = pos[0] if w["x"] is None else w["x"]
        ny = pos[1] if w["y"] is None else w["y"]
        nz = pos[2] if w["z"] is None else w["z"]

        code = modal["G"]
        has_arc_params = (w["i"] is not None and w["j"] is not None) or (w["r"] is not None)
        position_changed = (nx != pos[0] or ny != pos[1] or nz != pos[2])

        line_number = line_idx + 1
        line_text = blk["raw"].strip()

        if code in (0, 1) and position_changed:
            seg_type = "rapid" if code == 0 else "cut"
            feed = rapid_mm_min if code == 0 else modal["F"]
            _emit_segment(seg_type, pos, (nx, ny, nz), feed, line_number, line_text)
            dist_xy = math.hypot(nx - pos[0], ny - pos[1])
            if code == 0:
                rapid_mm += dist_xy
            else:
                cut_mm += dist_xy
            pos = (nx, ny, nz)

        elif code in (2, 3) and modal["plane"] == 17 and (position_changed or has_arc_params):
            cw = code == 2
            seg_type = "arc_cw" if cw else "arc_ccw"

            center: Optional[Tuple[float, float]] = None
            if w["i"] is not None and w["j"] is not None:
                center = (pos[0] + w["i"], pos[1] + w["j"])
            elif w["r"] is not None:
                center = arc_center_from_r(pos[0], pos[1], nx, ny, w["r"], cw)

            if center is not None:
                waypoints = interpolate_arc_points(
                    pos, (nx, ny, nz), center, cw, arc_resolution_deg
                )
                cur = pos
                for wp in waypoints:
                    _emit_segment(seg_type, cur, wp, modal["F"], line_number, line_text)
                    cut_mm += math.hypot(wp[0] - cur[0], wp[1] - cur[1])
                    cur = wp
            else:
                # Fallback: treat degenerate arc as straight cut
                _emit_segment("cut", pos, (nx, ny, nz), modal["F"], line_number, line_text)
                cut_mm += math.hypot(nx - pos[0], ny - pos[1])

            pos = (nx, ny, nz)

    total_time_min = sum(s["duration_ms"] for s in segs) / 60_000.0

    # P6: Collect unique tools used
    tools_used = sorted(set(s.get("tool_number", 1) for s in segs))

    return {
        "segments": segs,
        "bounds": bb,
        "totals": {
            "rapid_mm": rapid_mm,
            "cut_mm": cut_mm,
            "time_min": total_time_min,
            "segment_count": len(segs),
        },
        # P6 Extension: Multi-tool tracking
        "tools": {
            "used": tools_used,
            "count": len(tools_used),
            "changes": tool_changes,
        },
    }
