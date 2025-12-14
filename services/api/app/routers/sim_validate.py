import csv
import io
import math
import re
from typing import Any, Dict, List, Tuple

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
            except:
                pass
        elif c.startswith('S'):
            try:
                self.S = float(c[1:])
            except:
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
    sx, sy = start
    ex, ey = end
    r = abs(as_units(ms, r_user))
    dx = ex - sx
    dy = ey - sy
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return (sx, sy + r)
    h2 = r * r - (d * d) / 4.0
    h = math.sqrt(max(0.0, h2))
    mx = (sx + ex) / 2.0
    my = (sy + ey) / 2.0
    ux, uy = (-dy / d, dx / d)
    cands = [(mx + ux * h, my + uy * h), (mx - ux * h, my - uy * h)]

    def signed_sweep(cx, cy):
        a0 = math.atan2(sy - cy, sx - cx)
        a1 = math.atan2(ey - cy, ex - cx)
        return ((a1 - a0 + math.pi) % (2 * math.pi) - math.pi)

    c = cands[0]
    s = signed_sweep(*c)
    if (cw and s > 0) or ((not cw) and s < 0):
        c = cands[1]
    return c


def arc_length(cx, cy, sx, sy, ex, ey, cw: bool) -> float:
    a0 = math.atan2(sy - cy, sx - cx)
    a1 = math.atan2(ey - cy, ex - cx)
    r = math.hypot(sx - cx, sy - cy)
    da = (a1 - a0)
    if cw:
        while da > 0:
            da -= 2 * math.pi
    else:
        while da < 0:
            da += 2 * math.pi
    return abs(da) * abs(r)


def trapezoidal_time(distance_mm: float, feed_mm_min: float, accel_mm_s2: float) -> float:
    v = max(feed_mm_min, 1e-6) / 60.0  # mm/s
    a = max(accel_mm_s2, 1e-6)
    t_acc = v / a
    d_acc = 0.5 * a * t_acc * t_acc
    if 2 * d_acc >= distance_mm:
        return 2.0 * (distance_mm / a) ** 0.5  # triangular
    cruise = distance_mm - 2 * d_acc
    return 2 * t_acc + cruise / v


def within_envelope(pt: Dict[str, float], env: Dict[str, Tuple[float, float]]) -> bool:
    for ax in ('X', 'Y', 'Z'):
        lo, hi = env[ax]
        if pt[ax] < lo - 1e-9 or pt[ax] > hi + 1e-9:
            return False
    return True


def simulate(gcode: str, accel: float = DEFAULT_ACCEL, clearance_z: float = DEFAULT_CLEAR_Z,
             env: dict = DEFAULT_ENVELOPE, rapid_mm_min: float = DEFAULT_RAPID) -> Dict[str, Any]:
    ms = ModalState()
    moves, issues = [], []
    total_xy = 0.0
    total_z = 0.0
    total_time = 0.0

    def schedule_linear(code, x0, y0, z0, x1, y1, z1, feed):
        dxy = math.hypot(x1 - x0, y1 - y0)
        dz = abs(z1 - z0)
        t = trapezoidal_time(dxy, feed if feed > 0 else rapid_mm_min, accel) \
            + trapezoidal_time(dz, feed if feed > 0 else rapid_mm_min, accel)
        return dxy, dz, t

    lines = gcode.splitlines()
    for idx, raw in enumerate(lines, start=1):
        ln = raw.strip()
        if not ln or ln.startswith('(') or ln.startswith(';'):
            continue
        if not MOVE_RE.search(ln):
            continue

        toks = parse_line(ln)
        word = None
        params = {}
        for t, v in toks:
            if t[0] in 'GMTFS':
                ms.apply_modal(t.split()[0] if ' ' in t else t)
                if t.startswith('G'):
                    word = t
            else:
                params[t] = v

        x = ms.pos['X']
        y = ms.pos['Y']
        z = ms.pos['Z']
        nx = x
        ny = y
        nz = z
        if 'X' in params:
            nx = (x + as_units(ms, params['X'])) if not ms.abs else as_units(ms, params['X'])
        if 'Y' in params:
            ny = (y + as_units(ms, params['Y'])) if not ms.abs else as_units(ms, params['Y'])
        if 'Z' in params:
            nz = (z + as_units(ms, params['Z'])) if not ms.abs else as_units(ms, params['Z'])

        if word and word.upper().startswith('G'):
            gnum = int(float(word[1:]))
            if gnum == 0:
                if z < clearance_z:
                    dxy, dz, t = schedule_linear('G0', x, y, z, x, y, clearance_z, rapid_mm_min)
                    total_xy += dxy
                    total_z += dz
                    total_time += t
                    moves.append({'line': idx, 'code': 'G0', 'x': x, 'y': y, 'z': clearance_z, 'feed': rapid_mm_min, 't': t})
                    z = clearance_z
                if (nx != x) or (ny != y):
                    dxy, dz, t = schedule_linear('G0', x, y, z, nx, ny, z, rapid_mm_min)
                    total_xy += dxy
                    total_z += dz
                    total_time += t
                    moves.append({'line': idx, 'code': 'G0', 'x': nx, 'y': ny, 'z': z, 'feed': rapid_mm_min, 't': t})
                    x, y = nx, ny
                if nz != z:
                    dxy, dz, t = schedule_linear('G0', x, y, z, x, y, nz, rapid_mm_min)
                    total_xy += dxy
                    total_z += dz
                    total_time += t
                    moves.append({'line': idx, 'code': 'G0', 'x': x, 'y': y, 'z': nz, 'feed': rapid_mm_min, 't': t})
                    z = nz

            elif gnum == 1:
                dxy, dz, t = schedule_linear('G1', x, y, z, nx, ny, nz, ms.F)
                total_xy += dxy
                total_z += dz
                total_time += t
                moves.append({'line': idx, 'code': 'G1', 'x': nx, 'y': ny, 'z': nz, 'feed': ms.F, 't': t})

            elif gnum in (2, 3):
                cw = (gnum == 2)
                sx, sy = x, y
                ex, ey = nx, ny
                if 'I' in params or 'J' in params:
                    cx, cy = arc_center_from_ijk(ms, (sx, sy), params)
                elif 'R' in params:
                    cx, cy = arc_center_from_r(ms, (sx, sy), (ex, ey), params['R'], cw)
                else:
                    issues.append({'line': idx, 'severity': 'error', 'type': 'arc_missing_params', 'msg': 'Arc missing IJK or R'})
                    cx, cy = (sx, sy)
                length = arc_length(cx, cy, sx, sy, ex, ey, cw)
                t = trapezoidal_time(length, ms.F, DEFAULT_ACCEL) + trapezoidal_time(abs(nz - z), ms.F, DEFAULT_ACCEL)
                total_xy += length
                total_time += t
                total_z += abs(nz - z)
                moves.append({'line': idx, 'code': f'G{gnum}', 'x': nx, 'y': ny, 'z': nz, 'i': cx - sx, 'j': cy - sy, 'cx': cx, 'cy': cy, 'feed': ms.F, 't': t})

            elif gnum in (20, 21, 90, 91, 93, 94, 17, 18, 19, 4):
                if gnum == 4:
                    p = params.get('P', 0.0)  # dwell
                    dt = p / 1000.0 if p > 10 else p
                    total_time += dt
                    moves.append({'line': idx, 'code': 'G4', 'p': p, 't': dt})

        next_pos = {'X': nx, 'Y': ny, 'Z': nz}
        if not within_envelope(next_pos, DEFAULT_ENVELOPE):
            issues.append({'line': idx, 'severity': 'fatal', 'type': 'envelope_violation', 'msg': f'Position out of travel: {next_pos}'})
        if z < 0 and word and word.upper().startswith('G') and int(float(word[1:])) == 0 and ((nx != x) or (ny != y)):
            issues.append({'line': idx, 'severity': 'warn', 'type': 'unsafe_rapid', 'msg': 'XY rapid below Z=0; split applied'})

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
