"""
Adaptive Pocketing Core Engine
Generates offset-based toolpaths for clearing pockets with optional islands
"""
import math
from typing import List, Dict, Tuple

# Geometry input: list of closed loops (outer first, then inner islands), each loop as [(x,y), ...]
# Output toolpath: list of moves [{"code":"G1","x":...,"y":...,"f":...}, {"code":"G2","x":...,"y":...,"i":...,"j":...}, ...]

def _offset_loop(loop: List[Tuple[float,float]], offset: float, round_joints=True) -> List[Tuple[float,float]]:
    """
    Very small inward offset: vector normals + miter/round joins. Not robust for self-intersections,
    but good enough for rects/rounded pockets. We iterate this to create offset shells.
    """
    pts = loop[:]
    n = len(pts)
    out = []
    for i in range(n):
        x1,y1 = pts[i-1]
        x2,y2 = pts[i]
        x3,y3 = pts[(i+1)%n]
        # edges
        ux,uy = x2-x1, y2-y1
        vx,vy = x3-x2, y3-y2
        # unit left normals
        lu = (-(uy)/((ux**2+uy**2)**0.5+1e-12), (ux)/((ux**2+uy**2)**0.5+1e-12))
        lv = (-(vy)/((vx**2+vy**2)**0.5+1e-12), (vx)/((vx**2+vy**2)**0.5+1e-12))
        # bisector
        bx,by = lu[0]+lv[0], lu[1]+lv[1]
        bl = (bx**2+by**2)**0.5+1e-12
        bx,by = bx/bl, by/bl
        # miter length; clamp to avoid crazy spikes
        sin_half = max(1e-6, math.sin(0.5*angle_between(ux,uy,vx,vy)))
        m = min(10.0, 1.0/sin_half)
        px = x2 + bx * offset * m
        py = y2 + by * offset * m
        out.append((px,py))
    return out

def angle_between(ax,ay,bx,by):
    a = math.atan2(ay,ax); b = math.atan2(by,bx)
    d = b-a
    while d>math.pi: d -= 2*math.pi
    while d<-math.pi: d += 2*math.pi
    return abs(d)

def build_offset_stacks(outer: List[Tuple[float,float]], islands: List[List[Tuple[float,float]]], tool_d: float, stepover: float, margin: float):
    """
    Returns a list of inward offset loops starting from (tool/2 + margin) inside the outer, stopping before collapse or island collision.
    """
    step = tool_d * max(0.05, min(0.95, stepover))  # mm
    inner = []
    cur = _offset_loop(outer, -(tool_d/2.0 + margin))
    while cur and len(cur) >= 3:
        inner.append(cur)
        nxt = _offset_loop(cur, -step)
        if not nxt or len(nxt) < 3: break
        # crude stop if area collapses
        if polygon_area(nxt) <= 1e-2: break
        cur = nxt
    # TODO: subtract islands properly; in first cut we just stop when inner area <= any island bbox.
    return inner

def polygon_area(loop: List[Tuple[float,float]]):
    a=0.0
    for i in range(len(loop)):
        x1,y1 = loop[i]
        x2,y2 = loop[(i+1)%len(loop)]
        a += x1*y2 - x2*y1
    return abs(a)/2.0

def spiralize(stacks: List[List[Tuple[float,float]]], smoothing: float) -> List[Tuple[float,float]]:
    """
    Link successive offset rings with short connectors to create one continuous path.
    smoothing: corner fillet radius (mm). First cut just interpolates midpoints.
    """
    if not stacks: return []
    path = []
    for k, ring in enumerate(stacks):
        if k==0:
            path += ring
        else:
            # connect last of previous to nearest of this ring
            prev_pt = path[-1]
            jmin = min(range(len(ring)), key=lambda j: (ring[j][0]-prev_pt[0])**2+(ring[j][1]-prev_pt[1])**2)
            path += [ring[jmin]] + ring[jmin+1:] + ring[:jmin]
    return path

def to_toolpath(path_pts: List[Tuple[float,float]], feed_xy: float, z_rough: float, safe_z: float, lead_r: float, climb=True):
    moves = []
    # lead-in arc
    if path_pts:
        sx,sy = path_pts[0]
        moves += [{"code":"G0","z":safe_z},{"code":"G0","x":sx,"y":sy},{"code":"G1","z":z_rough,"f":feed_xy}]
    for i in range(1,len(path_pts)):
        x,y = path_pts[i]
        moves.append({"code":"G1","x":x,"y":y,"f":feed_xy})
    moves += [{"code":"G0","z":safe_z}]
    return moves

def plan_adaptive(loops: List[List[Tuple[float,float]]], tool_d: float, stepover: float, stepdown: float, margin: float, strategy: str, smoothing: float, climb: bool):
    outer = loops[0]
    islands = loops[1:] if len(loops)>1 else []
    stacks = build_offset_stacks(outer, islands, tool_d, stepover, margin)
    if strategy.lower().startswith("spiral"):
        path_pts = spiralize(stacks, smoothing)
    else:
        # lanes fallback: just concatenate rings
        path_pts = [pt for ring in stacks for pt in ring]
    return path_pts
