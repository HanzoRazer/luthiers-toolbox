"""
G-Code Simulation and Validation Router

Note: Arc geometry math extracted to geometry/arc_utils.py
following the Fortran Rule (all math in subroutines).
"""

import csv
import io
import math
import re
from typing import Any, Dict, List, Optional, Tuple

# Import canonical geometry functions - NO inline math in routers (Fortran Rule)
from ..geometry.arc_utils import (
    arc_center_from_endpoints,
    arc_length as compute_arc_length,
    trapezoidal_motion_time,
)

MOVE_RE = re.compile(r'^(?:N\d+\s+)?(G\d+(?:\.\d+)?|M\d+|T\d+|S\d+|F[-+]?\d*\.?\d+|[XYZIJKR][-+]?\d*\.?\d+|G\s*\d+)', re.I)
TOK_RE = re.compile(r'([GMTFSXYZIJKR])\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', re.I)

DEFAULT_CLEAR_Z = 5.0
DEFAULT_ENVELOPE = {'X': (-10.0, 1000.0), 'Y': (-10.0, 1000.0), 'Z': (-50.0, 100.0)}
DEFAULT_ACCEL = 2000.0  # mm/s^2 (trapezoidal)
DEFAULT_RAPID = 3000.0  # mm/min used when no feed present


class ModalState:
    def __init__(self):
        self.units = 'mm'
        self.abs = True
        self.plane = 'G17'
        self.feed_mode = 'G94'
        self.F = 1000.0
        self.S = 0.0
        self.pos = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}

    def apply_modal(self, code: str):
        c = code.upper()
        if c == 'G20':
            self.units = 'inch'
        elif c == 'G21':
            self.units = 'mm'
        elif c == 'G90':
            self.abs = True
        elif c == 'G91':
            self.abs = False
        elif c in ('G17', 'G18', 'G19'):
            self.plane = c
        elif c in ('G93', 'G94'):
            self.feed_mode = c
        elif c.startswith('F'):
            try:
                self.F = float(c[1:])
            except (ValueError, IndexError):
                pass
        elif c.startswith('S'):
            try:
                self.S = float(c[1:])
            except (ValueError, IndexError):
                pass


def parse_line(line: str) -> List[Tuple[str, float]]:
    out = []
    for k, v in TOK_RE.findall(line):
        k = k.upper()
        if k in 'GMTF':
            out.append((k + v.upper().replace(' ', ''), float(v) if k == 'F' else None))
        else:
            out.append((k, float(v)))
    return out


def as_units(ms: ModalState, val: float) -> float:
    return val if ms.units == 'mm' else val * 25.4


def arc_center_from_ijk(ms: ModalState, start: Tuple[float, float], params: Dict[str, float]) -> Tuple[float, float]:
    cx = start[0] + as_units(ms, params.get('I', 0.0))
    cy = start[1] + as_units(ms, params.get('J', 0.0))
    return (cx, cy)


def arc_center_from_r(ms: ModalState, start: Tuple[float, float], end: Tuple[float, float], r_user: float, cw: bool) -> Tuple[float, float]:
    """
    Calculate arc center from R parameter.

    Delegates to canonical arc_center_from_endpoints() from geometry/arc_utils.py.
    """
    sx, sy = start
    ex, ey = end
    r = abs(as_units(ms, r_user))
    return arc_center_from_endpoints(sx, sy, ex, ey, r, clockwise=cw)


def arc_length(cx, cy, sx, sy, ex, ey, cw: bool) -> float:
    """
    Calculate arc length.

    Delegates to canonical compute_arc_length() from geometry/arc_utils.py.
    """
    return compute_arc_length(cx, cy, sx, sy, ex, ey, clockwise=cw)


def trapezoidal_time(distance_mm: float, feed_mm_min: float, accel_mm_s2: float) -> float:
    """
    Calculate motion time using trapezoidal profile.

    Delegates to canonical trapezoidal_motion_time() from geometry/arc_utils.py.
    """
    return trapezoidal_motion_time(distance_mm, feed_mm_min, accel_mm_s2)


def within_envelope(pt: Dict[str, float], env: Dict[str, Tuple[float, float]]) -> bool:
    for ax in ('X', 'Y', 'Z'):
        lo, hi = env[ax]
        if pt[ax] < lo - 1e-9 or pt[ax] > hi + 1e-9:
            return False
    return True


def _resolve_next_pos(ms: ModalState, params: Dict[str, float]) -> Tuple[float, float, float]:
    """Compute next X/Y/Z from modal state and parsed params."""
    x, y, z = ms.pos['X'], ms.pos['Y'], ms.pos['Z']
    nx = (x + as_units(ms, params['X'])) if ('X' in params and not ms.abs) else as_units(ms, params['X']) if 'X' in params else x
    ny = (y + as_units(ms, params['Y'])) if ('Y' in params and not ms.abs) else as_units(ms, params['Y']) if 'Y' in params else y
    nz = (z + as_units(ms, params['Z'])) if ('Z' in params and not ms.abs) else as_units(ms, params['Z']) if 'Z' in params else z
    return nx, ny, nz


def _sim_rapid(idx: int, x: float, y: float, z: float,
               nx: float, ny: float, nz: float,
               clearance_z: float, rapid: float, accel: float,
               moves: list) -> Tuple[float, float, float, float, float, float]:
    """Handle G0 rapid: retract → XY move → plunge. Returns (x, y, z, dxy, dz, dt)."""
    dxy = dz = dt = 0.0
    if z < clearance_z:
        d = abs(clearance_z - z)
        t = trapezoidal_time(d, rapid, accel)
        dz += d; dt += t
        moves.append({'line': idx, 'code': 'G0', 'x': x, 'y': y, 'z': clearance_z, 'feed': rapid, 't': t})
        z = clearance_z
    if nx != x or ny != y:
        d = math.hypot(nx - x, ny - y)
        t = trapezoidal_time(d, rapid, accel)
        dxy += d; dt += t
        moves.append({'line': idx, 'code': 'G0', 'x': nx, 'y': ny, 'z': z, 'feed': rapid, 't': t})
        x, y = nx, ny
    if nz != z:
        d = abs(nz - z)
        t = trapezoidal_time(d, rapid, accel)
        dz += d; dt += t
        moves.append({'line': idx, 'code': 'G0', 'x': x, 'y': y, 'z': nz, 'feed': rapid, 't': t})
        z = nz
    return x, y, z, dxy, dz, dt


def _sim_linear(idx: int, x: float, y: float, z: float,
                nx: float, ny: float, nz: float,
                feed: float, accel: float,
                moves: list) -> Tuple[float, float, float]:
    """Handle G1 linear cut. Returns (dxy, dz, dt)."""
    dxy = math.hypot(nx - x, ny - y)
    dz = abs(nz - z)
    t = trapezoidal_time(dxy, feed, accel) + trapezoidal_time(dz, feed, accel)
    moves.append({'line': idx, 'code': 'G1', 'x': nx, 'y': ny, 'z': nz, 'feed': feed, 't': t})
    return dxy, dz, t


def _sim_arc(idx: int, x: float, y: float, z: float,
             nx: float, ny: float, nz: float,
             gnum: int, params: Dict[str, float], ms: ModalState,
             accel: float, moves: list, issues: list) -> Tuple[float, float, float]:
    """Handle G2/G3 arc. Returns (dxy, dz, dt)."""
    cw = (gnum == 2)
    if 'I' in params or 'J' in params:
        cx, cy = arc_center_from_ijk(ms, (x, y), params)
    elif 'R' in params:
        cx, cy = arc_center_from_r(ms, (x, y), (nx, ny), params['R'], cw)
    else:
        issues.append({'line': idx, 'severity': 'error', 'type': 'arc_missing_params', 'msg': 'Arc missing IJK or R'})
        cx, cy = (x, y)
    length = arc_length(cx, cy, x, y, nx, ny, cw)
    dz = abs(nz - z)
    t = trapezoidal_time(length, ms.F, accel) + trapezoidal_time(dz, ms.F, accel)
    moves.append({'line': idx, 'code': f'G{gnum}', 'x': nx, 'y': ny, 'z': nz,
                  'i': cx - x, 'j': cy - y, 'cx': cx, 'cy': cy, 'feed': ms.F, 't': t})
    return length, dz, t


def _sim_dwell(idx: int, params: Dict[str, float], moves: list) -> float:
    """Handle G4 dwell. Returns dt."""
    p = params.get('P', 0.0)
    dt = p / 1000.0 if p > 10 else p
    moves.append({'line': idx, 'code': 'G4', 'p': p, 't': dt})
    return dt


def _parse_line_tokens(ln: str, ms: 'ModalState') -> Tuple[Optional[str], Dict[str, float]]:
    """Parse a G-code line, update *ms* in-place, return ``(g_word, params)``."""
    toks = parse_line(ln)
    word: Optional[str] = None
    params: Dict[str, float] = {}
    for t, v in toks:
        if t[0] in 'GMTFS':
            ms.apply_modal(t.split()[0] if ' ' in t else t)
            if t.startswith('G'):
                word = t
        else:
            params[t] = v
    return word, params


def _dispatch_gcode(
    idx: int, gnum: int,
    x: float, y: float, z: float,
    nx: float, ny: float, nz: float,
    params: Dict[str, float], ms: 'ModalState',
    clearance_z: float, rapid_mm_min: float, accel: float,
    moves: list, issues: list,
) -> Tuple[float, float, float, float, float, float]:
    """Dispatch a single G-code command. Returns ``(x, y, z, dxy, dz, dt)``."""
    if gnum == 0:
        return _sim_rapid(idx, x, y, z, nx, ny, nz, clearance_z, rapid_mm_min, accel, moves)
    if gnum == 1:
        dxy, dz, dt = _sim_linear(idx, x, y, z, nx, ny, nz, ms.F, accel, moves)
        return x, y, z, dxy, dz, dt
    if gnum in (2, 3):
        dxy, dz, dt = _sim_arc(idx, x, y, z, nx, ny, nz, gnum, params, ms, accel, moves, issues)
        return x, y, z, dxy, dz, dt
    if gnum == 4:
        dt = _sim_dwell(idx, params, moves)
        return x, y, z, 0.0, 0.0, dt
    return x, y, z, 0.0, 0.0, 0.0


def _check_move_issues(
    idx: int, z: float, word: Optional[str],
    x: float, y: float,
    nx: float, ny: float, nz: float,
    env: dict, issues: list,
) -> None:
    """Append envelope-violation or unsafe-rapid issues."""
    next_pos = {'X': nx, 'Y': ny, 'Z': nz}
    if not within_envelope(next_pos, env):
        issues.append({'line': idx, 'severity': 'fatal', 'type': 'envelope_violation',
                       'msg': f'Position out of travel: {next_pos}'})
    if (z < 0 and word and word.upper().startswith('G')
            and int(float(word[1:])) == 0 and (nx != x or ny != y)):
        issues.append({'line': idx, 'severity': 'warn', 'type': 'unsafe_rapid',
                       'msg': 'XY rapid below Z=0; split applied'})


def simulate(gcode: str, accel: float = DEFAULT_ACCEL, clearance_z: float = DEFAULT_CLEAR_Z,
             env: dict = DEFAULT_ENVELOPE, rapid_mm_min: float = DEFAULT_RAPID) -> Dict[str, Any]:
    ms = ModalState()
    moves: list = []
    issues: list = []
    total_xy = 0.0
    total_z = 0.0
    total_time = 0.0

    for idx, raw in enumerate(gcode.splitlines(), start=1):
        ln = raw.strip()
        if not ln or ln.startswith('(') or ln.startswith(';'):
            continue
        if not MOVE_RE.search(ln):
            continue

        word, params = _parse_line_tokens(ln, ms)
        x, y, z = ms.pos['X'], ms.pos['Y'], ms.pos['Z']
        nx, ny, nz = _resolve_next_pos(ms, params)

        if word and word.upper().startswith('G'):
            gnum = int(float(word[1:]))
            x, y, z, dxy, dz, dt = _dispatch_gcode(
                idx, gnum, x, y, z, nx, ny, nz, params, ms,
                clearance_z, rapid_mm_min, accel, moves, issues)
            total_xy += dxy; total_z += dz; total_time += dt

        _check_move_issues(idx, z, word, x, y, nx, ny, nz, env, issues)
        ms.pos.update({'X': nx, 'Y': ny, 'Z': nz})

    summary = {'units': ms.units, 'total_xy': total_xy, 'total_z': total_z, 'est_seconds': total_time}
    return {'moves': moves, 'modal': {'units': ms.units, 'abs': ms.abs, 'plane': ms.plane, 'feed_mode': ms.feed_mode, 'F': ms.F, 'S': ms.S}, 'summary': summary, 'issues': issues}


def csv_export(sim: Dict[str, Any]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['i', 'line', 'code', 'x', 'y', 'z', 'i', 'j', 'feed', 't'])
    for i, m in enumerate(sim['moves']):
        w.writerow([i, m.get('line', ''), m.get('code', ''), m.get('x', ''), m.get('y', ''), m.get('z', ''), m.get('i', ''), m.get('j', ''), m.get('feed', ''), m.get('t', '')])
    return buf.getvalue().encode('utf-8')
