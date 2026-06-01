"""
G-code State Machine Simulator

Executes G-code programs with modal state tracking, calculating travel
distances, cut times, and generating per-segment backplot data for animation.

Fidelity notes (see TOOLPATH_ANIMATION_AUDIT 2026-05-30):
- Segment *timing* uses true 3D distance so vertical (Z) plunges/retracts and
  helical moves contribute to cycle time (X1). Odometry (rapid_mm / cut_mm)
  stays planar by design — it measures travel in the work plane.
- Canned drilling cycles (G81/G82/G83/G73/G85/G84) are expanded into their
  constituent rapid/plunge/peck/retract moves so drilling actually animates (X2).
- All G-words on a line are honoured; a non-motion word (e.g. a trailing G17)
  no longer clobbers the motion code (X3).
- G90/G91 absolute/incremental is tracked (Y1); arcs are simulated in the active
  plane G17/G18/G19 and always advance position so the path can't desync (Y2).
- Unrecognised G/M codes, ignored work offsets, degenerate arcs, and truncation
  are collected and returned in ``warnings`` rather than failing silently (Z1).
- ``simulate()`` is a thin wrapper over ``simulate_segments()`` so the aggregate
  and per-segment paths share one implementation and cannot disagree.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .geometry import arc_center_from_r, interpolate_arc
from .lexer import parse_lines
from .types import Modal

# Modal group 1 motion codes that emit ordinary moves.
MOTION = {0, 1, 2, 3}
# Canned cycle codes (modal group 1). CANNED_IMPL are modelled faithfully;
# the rest are approximated as a single feed plunge and flagged.
CANNED_IMPL = {73, 81, 82, 83, 84, 85}
CANNED = CANNED_IMPL | {86, 89}
# Work-offset codes — acknowledged but not applied (no offset table available).
WORK_OFFSETS = {54, 55, 56, 57, 58, 59}
# M-codes we understand; anything else is surfaced as unsupported.
KNOWN_M = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 30}


def _parse_block_words(blk: Dict[str, Any], u: float) -> Dict[str, Any]:
    """Extract typed values from a parsed block, applying unit factor *u*.

    Collects *all* G-words into ``gs`` (a list) so multi-G lines are handled
    correctly (X3). Distance-bearing words (X/Y/Z/I/J/K/R/Q) and the feed are
    scaled by *u*; the dwell time P is not.
    """
    out: Dict[str, Any] = {
        "gs": [], "x": None, "y": None, "z": None,
        "f": None, "i": None, "j": None, "k": None, "r": None,
        "q": None, "p": None, "t": None, "s": None, "m": None,
    }
    for letter, val in blk["words"]:
        if letter == "G":
            out["gs"].append(int(round(val)))
        elif letter in ("X", "Y", "Z", "I", "J", "K", "R", "Q"):
            out[letter.lower()] = val * u
        elif letter == "F":
            out["f"] = val * u
        elif letter == "P":
            out["p"] = val
        elif letter == "T":
            out["t"] = int(val)
        elif letter == "S":
            out["s"] = float(val)
        elif letter == "M":
            out["m"] = int(val)
    return out


def _apply_modal(
    modal: Modal,
    gs: List[int],
    f: float | None,
    t: int | None,
    s: float | None,
    m: int | None,
    warn: Dict[str, Any],
) -> None:
    """Apply all G/F/T/S/M words on a line to modal state, in order.

    Unknown G-codes and unhandled M-codes are recorded in *warn* rather than
    being silently dropped (Z1).
    """
    if f is not None:
        modal["F"] = max(0.1, float(f))

    for g in gs:
        if g in MOTION:
            modal["G"] = g
            modal["cycle"] = None
            modal["cycle_active"] = False
        elif g == 80:                      # cancel canned cycle
            modal["cycle"] = None
            modal["cycle_active"] = False
        elif g in CANNED:
            modal["cycle"] = g
        elif g in (17, 18, 19):
            modal["plane"] = g
        elif g == 20:
            modal["units"] = 25.4
        elif g == 21:
            modal["units"] = 1.0
        elif g == 90:
            modal["absolute"] = True
        elif g == 91:
            modal["absolute"] = False
        elif g in (98, 99):
            modal["return_mode"] = g
        elif g == 4:
            pass                            # dwell handled in the main loop
        elif g in WORK_OFFSETS:
            warn["ignored_offsets"].add(g)
        else:
            warn["unsupported_g"].add(g)

    if t is not None:
        modal["pending_tool"] = t
    if s is not None:
        modal["S"] = max(0.0, float(s))
    if m is not None:
        if m == 3:
            modal["spindle_on"] = True
            modal["spindle_dir"] = "cw"
        elif m == 4:
            modal["spindle_on"] = True
            modal["spindle_dir"] = "ccw"
        elif m == 5:
            modal["spindle_on"] = False
        elif m == 6:
            modal["T"] = modal.get("pending_tool", modal.get("T", 1))
        elif m not in KNOWN_M:
            warn["unsupported_m"].add(m)


def _arc_center(
    plane: int,
    pos: Tuple[float, float, float],
    nx: float, ny: float, nz: float,
    w: Dict[str, Any],
    cw: bool,
) -> Optional[Tuple[float, float]]:
    """Compute the arc center in the active plane's two axes, or None.

    IJK take precedence over R. Returns None when no usable arc parameters are
    present or the R-radius is geometrically invalid (degenerate arc).
    """
    if plane == 18:  # XZ — axes (x, z), offsets I, K
        if w["i"] is not None or w["k"] is not None:
            return (pos[0] + (w["i"] or 0.0), pos[2] + (w["k"] or 0.0))
        if w["r"] is not None:
            return arc_center_from_r(pos[0], pos[2], nx, nz, w["r"], cw)
        return None
    if plane == 19:  # YZ — axes (y, z), offsets J, K
        if w["j"] is not None or w["k"] is not None:
            return (pos[1] + (w["j"] or 0.0), pos[2] + (w["k"] or 0.0))
        if w["r"] is not None:
            return arc_center_from_r(pos[1], pos[2], ny, nz, w["r"], cw)
        return None
    # G17 XY — axes (x, y), offsets I, J
    if w["i"] is not None or w["j"] is not None:
        return (pos[0] + (w["i"] or 0.0), pos[1] + (w["j"] or 0.0))
    if w["r"] is not None:
        return arc_center_from_r(pos[0], pos[1], nx, ny, w["r"], cw)
    return None


def _expand_canned_cycle(
    code: int,
    x: float, y: float,
    z_start: float, z_initial: float,
    r_plane: float, z_depth: float,
    q_peck: float | None,
    feed: float, rapid_feed: float,
    return_mode: int,
) -> Tuple[List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float], float]], float, bool]:
    """Expand a canned drilling cycle into atomic moves (X2).

    Returns (moves, return_z, approximated) where each move is
    (seg_type, from_xyz, to_xyz, feed). All Z values are absolute (mm).
    """
    moves: List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float], float]] = []
    approximated = False
    z = z_start

    # Position to the R (retract) plane at rapid before cutting.
    if abs(z - r_plane) > 1e-9:
        moves.append(("rapid", (x, y, z), (x, y, r_plane), rapid_feed))
        z = r_plane

    if code in (81, 82):
        moves.append(("cut", (x, y, r_plane), (x, y, z_depth), feed))
        z = z_depth
    elif code in (84, 85):  # bore / tap — feed in, feed back out
        moves.append(("cut", (x, y, r_plane), (x, y, z_depth), feed))
        moves.append(("cut", (x, y, z_depth), (x, y, r_plane), feed))
        z = r_plane
    elif code in (83, 73):  # peck drill (G83 full retract / G73 chip-break)
        depth_total = abs(r_plane - z_depth)
        peck = abs(q_peck) if q_peck else depth_total
        if peck < 1e-9:
            peck = depth_total if depth_total > 1e-9 else 1.0
        cur = r_plane
        while cur > z_depth + 1e-9:
            nxt = max(cur - peck, z_depth)
            moves.append(("cut", (x, y, cur), (x, y, nxt), feed))
            if nxt > z_depth + 1e-9:
                if code == 83:                       # full retract to R, re-approach
                    moves.append(("rapid", (x, y, nxt), (x, y, r_plane), rapid_feed))
                    approach = nxt + 0.5
                    moves.append(("rapid", (x, y, r_plane), (x, y, approach), rapid_feed))
                    cur = approach
                else:                                # G73 small chip-break retract
                    brk = nxt + 0.5
                    moves.append(("rapid", (x, y, nxt), (x, y, brk), rapid_feed))
                    cur = brk
            else:
                cur = nxt
        z = z_depth
    else:  # G86/G89 etc. — approximate as a single plunge
        approximated = True
        moves.append(("cut", (x, y, r_plane), (x, y, z_depth), feed))
        z = z_depth

    return_z = z_initial if return_mode == 98 else r_plane
    if abs(z - return_z) > 1e-9:
        moves.append(("rapid", (x, y, z), (x, y, return_z), rapid_feed))

    return moves, return_z, approximated


def _default_modal(default_feed_mm_min: float, u: float) -> Modal:
    return {
        "G": 0,
        "F": default_feed_mm_min,
        "units": u,
        "plane": 17,
        "absolute": True,
        "return_mode": 98,
        "cycle": None,
        "cycle_active": False,
        "cycle_z": None,
        "cycle_r": None,
        "cycle_q": None,
        "cycle_f": None,
        "cycle_initial_z": 0.0,
        "T": 1,
        "pending_tool": 1,
        "S": 0.0,
        "spindle_on": False,
        "spindle_dir": "cw",
    }


def _apply_accel_profile(
    segs: List[Dict[str, Any]],
    accel_mm_s2: float,
    junction_deviation_mm: float,
) -> None:
    """Recompute each segment's ``duration_ms`` with a trapezoidal accel/decel
    model and Grbl-style junction speeds (opt-in).

    Constant-velocity timing treats every move as instantaneous-to-feed; this
    instead accelerates from rest, blends through corners up to a junction speed
    derived from ``junction_deviation_mm``, and decelerates to rest at stops.
    Dwell and zero-length segments are left untouched and act as hard stops that
    force their neighbours' junction speed to zero. (CAM-TPA-001: accel model)
    """
    a = accel_mm_s2
    if a <= 0 or not segs:
        return

    n = len(segs)
    length = [0.0] * n
    vnom = [0.0] * n
    unit: List[Optional[Tuple[float, float, float]]] = [None] * n
    is_move = [False] * n

    for i, s in enumerate(segs):
        if s["type"] == "dwell":
            continue
        fp, tp = s["from_pos"], s["to_pos"]
        d = math.dist(fp, tp)
        if d > 1e-9:
            length[i] = d
            is_move[i] = True
            unit[i] = ((tp[0] - fp[0]) / d, (tp[1] - fp[1]) / d, (tp[2] - fp[2]) / d)
            vnom[i] = max(1e-6, s["feed"] / 60.0)  # mm/min → mm/s

    def junction_speed(
        u_in: Optional[Tuple[float, float, float]],
        u_out: Optional[Tuple[float, float, float]],
    ) -> float:
        if u_in is None or u_out is None:
            return 0.0
        cos_t = u_in[0] * u_out[0] + u_in[1] * u_out[1] + u_in[2] * u_out[2]
        cos_t = max(-1.0, min(1.0, cos_t))
        if cos_t <= -0.999999:
            return 0.0
        sin_half = math.sqrt((1.0 - cos_t) / 2.0)
        if sin_half >= 0.999999:
            return 0.0
        radius = junction_deviation_mm * sin_half / (1.0 - sin_half)
        return math.sqrt(a * radius)

    moves = [i for i in range(n) if is_move[i]]
    if not moves:
        return

    def gap_has_stop(lo: int, hi: int) -> bool:
        return any(not is_move[m] for m in range(lo + 1, hi))

    # Per-move junction entry cap.
    max_entry = {}
    for k, i in enumerate(moves):
        if k == 0:
            max_entry[i] = 0.0
            continue
        prev = moves[k - 1]
        if gap_has_stop(prev, i):
            max_entry[i] = 0.0
        else:
            jv = junction_speed(unit[prev], unit[i])
            max_entry[i] = min(jv, vnom[prev], vnom[i])

    def exit_of(k: int, entry: Dict[int, float]) -> float:
        i = moves[k]
        if k == len(moves) - 1:
            return 0.0
        nxt = moves[k + 1]
        return 0.0 if gap_has_stop(i, nxt) else entry[nxt]

    entry: Dict[int, float] = {i: min(vnom[i], max_entry[i]) for i in moves}

    # Reverse pass — decel limit.
    for k in range(len(moves) - 1, -1, -1):
        i = moves[k]
        ev = exit_of(k, entry)
        cap = min(vnom[i], max_entry[i], math.sqrt(ev * ev + 2.0 * a * length[i]))
        entry[i] = cap

    # Forward pass — accel limit (start of each motion run begins at rest).
    for k, i in enumerate(moves):
        if k == 0 or gap_has_stop(moves[k - 1], i):
            entry[i] = 0.0
        else:
            prev = moves[k - 1]
            entry[i] = min(entry[i], math.sqrt(entry[prev] * entry[prev] + 2.0 * a * length[prev]))

    # Trapezoidal time per move.
    for k, i in enumerate(moves):
        ve = entry[i]
        vx = exit_of(k, entry)
        l_i = length[i]
        vp = min(vnom[i], math.sqrt(max(0.0, (2.0 * a * l_i + ve * ve + vx * vx) / 2.0)))
        vp = max(vp, ve, vx)
        d_acc = max(0.0, (vp * vp - ve * ve) / (2.0 * a))
        d_dec = max(0.0, (vp * vp - vx * vx) / (2.0 * a))
        d_cruise = l_i - d_acc - d_dec
        t = (vp - ve) / a + (vp - vx) / a
        if d_cruise > 1e-9 and vp > 1e-9:
            t += d_cruise / vp
        segs[i]["duration_ms"] = t * 1000.0


def simulate_segments(
    gcode: str,
    *,
    rapid_mm_min: float = 3000.0,
    default_feed_mm_min: float = 500.0,
    units: str = "mm",
    arc_resolution_deg: float = 5.0,
    max_segments: Optional[int] = None,
    accel_mm_s2: Optional[float] = None,
    junction_deviation_mm: float = 0.05,
) -> Dict[str, Any]:
    """
    Simulate G-code and return per-segment move data for animation.

    Emits one segment dict per atomic motion. G2/G3 arcs are pre-interpolated at
    ``arc_resolution_deg`` so the renderer only needs lineTo() calls; canned
    cycles are expanded into rapid/plunge/peck/retract moves.

    Args:
        max_segments: optional safety ceiling. When exceeded, further segments
            are dropped and ``warnings.truncated`` is set (with a count). This
            protects backend memory on pathological inputs; the frontend store
            does the finer-grained downsampling.

    Returns:
        Dict with ``segments``, ``bounds``, ``totals``, ``tools``, ``warnings``.
    """
    u = 1.0 if units.lower().startswith("mm") else 25.4
    prog = parse_lines(gcode)

    modal: Modal = _default_modal(default_feed_mm_min, u)
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    segs: List[Dict[str, Any]] = []
    rapid_mm = cut_mm = 0.0
    tool_changes: List[Dict[str, Any]] = []

    warn: Dict[str, Any] = {
        "unsupported_g": set(),
        "unsupported_m": set(),
        "ignored_offsets": set(),
        "approx_cycles": set(),
        "non_xy_arcs": 0,
        "degenerate_arcs": 0,
        "truncated": False,
        "dropped_segments": 0,
    }

    inf = float("inf")
    bb: Dict[str, float] = {
        "x_min": inf, "x_max": -inf,
        "y_min": inf, "y_max": -inf,
        "z_min": inf, "z_max": -inf,
    }

    def _expand_bb(x: float, y: float, z: float) -> None:
        bb["x_min"] = min(bb["x_min"], x)
        bb["x_max"] = max(bb["x_max"], x)
        bb["y_min"] = min(bb["y_min"], y)
        bb["y_max"] = max(bb["y_max"], y)
        bb["z_min"] = min(bb["z_min"], z)
        bb["z_max"] = max(bb["z_max"], z)

    def _emit(
        seg_type: str,
        from_p: Tuple[float, float, float],
        to_p: Tuple[float, float, float],
        feed: float,
        line_number: int,
        line_text: str,
        *,
        is_cycle: bool = False,
        cycle_kind: str = "",
        duration_override: Optional[float] = None,
    ) -> None:
        if max_segments is not None and len(segs) >= max_segments:
            warn["truncated"] = True
            warn["dropped_segments"] += 1
            return
        if duration_override is not None:
            duration_ms = duration_override
        else:
            dist = math.dist(from_p, to_p)        # 3D — timing includes Z (X1)
            duration_ms = (dist / max(1e-6, feed)) * 60_000.0
        segs.append({
            "type": seg_type,
            "from_pos": list(from_p),
            "to_pos": list(to_p),
            "feed": feed,
            "duration_ms": duration_ms,
            "line_number": line_number,
            "line_text": line_text,
            "tool_number": modal.get("T", 1),
            "spindle_rpm": modal.get("S", 0.0),
            "spindle_on": modal.get("spindle_on", False),
            "is_cycle": is_cycle,
            "cycle_kind": cycle_kind,
        })
        # Bound to actual destinations only. Segments chain (each from_pos is the
        # previous to_pos), so the sole point this omits is the synthetic (0,0,0)
        # start — which would otherwise frame empty space when a job lives away
        # from the origin (finding Z3).
        _expand_bb(*to_p)

    for line_idx, blk in enumerate(prog):
        w = _parse_block_words(blk, u)
        prev_tool = modal.get("T", 1)
        _apply_modal(modal, w["gs"], w["f"], w["t"], w["s"], w["m"], warn)
        u = modal["units"]

        curr_tool = modal.get("T", 1)
        if curr_tool != prev_tool:
            tool_changes.append({
                "line_number": line_idx + 1,
                "from_tool": prev_tool,
                "to_tool": curr_tool,
                "position": list(pos),
            })

        absolute = modal["absolute"]
        if absolute:
            nx = pos[0] if w["x"] is None else w["x"]
            ny = pos[1] if w["y"] is None else w["y"]
            nz = pos[2] if w["z"] is None else w["z"]
        else:
            nx = pos[0] + (w["x"] or 0.0)
            ny = pos[1] + (w["y"] or 0.0)
            nz = pos[2] + (w["z"] or 0.0)

        line_number = line_idx + 1
        line_text = blk["raw"].strip()

        # --- Dwell (G4) — no motion, but it consumes time (Z2). ------------
        if 4 in w["gs"]:
            dwell_s = w["p"] if w["p"] is not None else 0.0
            if dwell_s > 0:
                _emit("dwell", pos, pos, modal["F"], line_number, line_text,
                      duration_override=dwell_s * 1000.0)
            continue

        # --- Canned cycle expansion (X2). ---------------------------------
        cycle = modal["cycle"]
        if cycle is not None:
            line_has_cycle = any(g in CANNED for g in w["gs"])
            if w["z"] is not None:
                modal["cycle_z"] = nz
            if w["r"] is not None:
                modal["cycle_r"] = w["r"] if absolute else pos[2] + w["r"]
            if w["q"] is not None:
                modal["cycle_q"] = abs(w["q"])
            if w["f"] is not None:
                modal["cycle_f"] = modal["F"]
            if line_has_cycle and not modal["cycle_active"]:
                modal["cycle_initial_z"] = pos[2]
                modal["cycle_active"] = True

            triggered = line_has_cycle or (w["x"] is not None or w["y"] is not None)
            if triggered:
                # Reposition in XY at the current Z before drilling.
                if abs(nx - pos[0]) > 1e-9 or abs(ny - pos[1]) > 1e-9:
                    _emit("rapid", pos, (nx, ny, pos[2]), rapid_mm_min,
                          line_number, line_text)
                    rapid_mm += math.hypot(nx - pos[0], ny - pos[1])
                    pos = (nx, ny, pos[2])

                z_depth = modal["cycle_z"] if modal["cycle_z"] is not None else pos[2]
                r_plane = modal["cycle_r"] if modal["cycle_r"] is not None else pos[2]
                q_peck = modal["cycle_q"]
                cfeed = modal["cycle_f"] if modal["cycle_f"] is not None else modal["F"]
                init_z = modal["cycle_initial_z"]

                moves, ret_z, approx = _expand_canned_cycle(
                    cycle, nx, ny, pos[2], init_z, r_plane, z_depth,
                    q_peck, cfeed, rapid_mm_min, modal["return_mode"],
                )
                if approx:
                    warn["approx_cycles"].add(cycle)
                cycle_kind = f"G{cycle}"
                for mt, fp, tp, fd in moves:
                    _emit(mt, fp, tp, fd, line_number, line_text,
                          is_cycle=True, cycle_kind=cycle_kind)
                    if mt == "rapid":
                        rapid_mm += math.hypot(tp[0] - fp[0], tp[1] - fp[1])
                    else:
                        cut_mm += math.hypot(tp[0] - fp[0], tp[1] - fp[1])
                pos = (nx, ny, ret_z)
            continue

        # --- Ordinary motion. ---------------------------------------------
        code = modal["G"]
        has_arc = (
            w["i"] is not None or w["j"] is not None
            or w["k"] is not None or w["r"] is not None
        )
        position_changed = (
            abs(nx - pos[0]) > 1e-12
            or abs(ny - pos[1]) > 1e-12
            or abs(nz - pos[2]) > 1e-12
        )

        if code in (0, 1) and position_changed:
            seg_type = "rapid" if code == 0 else "cut"
            feed = rapid_mm_min if code == 0 else modal["F"]
            _emit(seg_type, pos, (nx, ny, nz), feed, line_number, line_text)
            dist_xy = math.hypot(nx - pos[0], ny - pos[1])
            if code == 0:
                rapid_mm += dist_xy
            else:
                cut_mm += dist_xy
            pos = (nx, ny, nz)

        elif code in (2, 3) and (position_changed or has_arc):
            plane = modal["plane"]
            cw = code == 2
            seg_type = "arc_cw" if cw else "arc_ccw"
            if plane != 17:
                warn["non_xy_arcs"] += 1

            center2 = _arc_center(plane, pos, nx, ny, nz, w, cw)
            if center2 is not None:
                waypoints = interpolate_arc(
                    pos, (nx, ny, nz), center2, cw, plane, arc_resolution_deg
                )
                cur = pos
                for wp in waypoints:
                    _emit(seg_type, cur, wp, modal["F"], line_number, line_text)
                    cut_mm += math.hypot(wp[0] - cur[0], wp[1] - cur[1])
                    cur = wp
            else:
                # Degenerate / unresolvable arc: draw a straight cut so the path
                # still reaches the endpoint instead of desyncing (Y2/Y3).
                warn["degenerate_arcs"] += 1
                _emit("cut", pos, (nx, ny, nz), modal["F"], line_number, line_text)
                cut_mm += math.hypot(nx - pos[0], ny - pos[1])

            pos = (nx, ny, nz)   # always advance, even on fallback

    # Optional trapezoidal accel/decel timing (constant-velocity if disabled).
    if accel_mm_s2 is not None and accel_mm_s2 > 0:
        _apply_accel_profile(segs, accel_mm_s2, junction_deviation_mm)

    # Normalise an empty bounding box to zeros.
    if not segs:
        for key in bb:
            bb[key] = 0.0

    total_time_min = sum(s["duration_ms"] for s in segs) / 60_000.0
    tools_used = sorted({s.get("tool_number", 1) for s in segs})

    warnings_out = {
        "unsupported_g": sorted(warn["unsupported_g"]),
        "unsupported_m": sorted(warn["unsupported_m"]),
        "ignored_offsets": sorted(warn["ignored_offsets"]),
        "approx_cycles": sorted(warn["approx_cycles"]),
        "non_xy_arcs": warn["non_xy_arcs"],
        "degenerate_arcs": warn["degenerate_arcs"],
        "truncated": warn["truncated"],
        "dropped_segments": warn["dropped_segments"],
    }

    return {
        "segments": segs,
        "bounds": bb,
        "totals": {
            "rapid_mm": rapid_mm,
            "cut_mm": cut_mm,
            "time_min": total_time_min,
            "segment_count": len(segs),
        },
        "tools": {
            "used": tools_used,
            "count": len(tools_used),
            "changes": tool_changes,
        },
        "warnings": warnings_out,
    }


def simulate(
    gcode: str,
    *,
    rapid_mm_min: float = 3000.0,
    default_feed_mm_min: float = 500.0,
    units: str = "mm",
    accel_mm_s2: Optional[float] = None,
    junction_deviation_mm: float = 0.05,
) -> Dict[str, Any]:
    """
    Aggregate G-code statistics (travel/cut distance and cycle time).

    Derived from :func:`simulate_segments` so the two share one engine and
    cannot disagree on timing (previously they shared only XY-planar distance
    logic, which made the parity test green while both omitted Z time).

    Returns:
        Dict with travel_mm, cut_mm, t_rapid_min, t_feed_min, t_total_min,
        points_xy.
    """
    res = simulate_segments(
        gcode,
        rapid_mm_min=rapid_mm_min,
        default_feed_mm_min=default_feed_mm_min,
        units=units,
        arc_resolution_deg=1.0,
        max_segments=None,
        accel_mm_s2=accel_mm_s2,
        junction_deviation_mm=junction_deviation_mm,
    )
    segs = res["segments"]

    travel = cut = t_rapid = t_feed = 0.0
    if segs:
        points_xy: List[Tuple[float, float]] = [
            (segs[0]["from_pos"][0], segs[0]["from_pos"][1])
        ]
    else:
        points_xy = [(0.0, 0.0)]

    for s in segs:
        fp, tp = s["from_pos"], s["to_pos"]
        dist_xy = math.hypot(tp[0] - fp[0], tp[1] - fp[1])
        dur_min = s["duration_ms"] / 60_000.0
        if s["type"] == "rapid":
            travel += dist_xy
            t_rapid += dur_min
        else:
            cut += dist_xy
            t_feed += dur_min
        points_xy.append((tp[0], tp[1]))

    return {
        "travel_mm": travel,
        "cut_mm": cut,
        "t_rapid_min": t_rapid,
        "t_feed_min": t_feed,
        "t_total_min": t_rapid + t_feed,
        "points_xy": points_xy,
    }
