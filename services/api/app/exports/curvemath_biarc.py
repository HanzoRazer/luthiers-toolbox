"""
Bi-arc Construction Algorithm for G1-Continuous Curve Blending

A bi-arc blend uses two circular arcs (or lines if degenerate) to create a smooth
transition between two points with specified tangent directions.

Migrated from legacy ./server/curvemath_router_biarc.py
"""

import math
from typing import List, Tuple, Dict, Optional


def _unit(v: Tuple[float, float]) -> Tuple[float, float]:
    """Normalize vector to unit length"""
    mag = math.sqrt(v[0]**2 + v[1]**2)
    if mag < 1e-12:
        return (1.0, 0.0)
    return (v[0] / mag, v[1] / mag)


def _normal(v: Tuple[float, float]) -> Tuple[float, float]:
    """Compute perpendicular vector (rotate 90 CCW)"""
    return (-v[1], v[0])


def _add(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    """Vector addition"""
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    """Vector subtraction"""
    return (a[0] - b[0], a[1] - b[1])


def _scale(v: Tuple[float, float], s: float) -> Tuple[float, float]:
    """Scalar multiplication"""
    return (v[0] * s, v[1] * s)


def _arc_from_A_T_to_B(
    A: Tuple[float, float],
    TA: Tuple[float, float],
    B: Tuple[float, float]
) -> Optional[Dict]:
    """
    Construct circular arc from point A with tangent TA to point B

    Returns:
        Dict with keys: 'type', 'center', 'radius', 'start_angle', 'end_angle'
        Returns None if degenerate
    """
    TA_unit = _unit(TA)

    AB = _sub(B, A)
    dist_AB = math.sqrt(AB[0]**2 + AB[1]**2)
    if dist_AB < 1e-9:
        return None

    NA = _normal(TA_unit)
    M = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)

    AB_unit = (AB[0] / dist_AB, AB[1] / dist_AB)
    perp_bisector = _normal(AB_unit)

    det = NA[0] * (-perp_bisector[1]) - NA[1] * (-perp_bisector[0])
    if abs(det) < 1e-9:
        return None

    rhs = _sub(M, A)
    s = (rhs[0] * (-perp_bisector[1]) - rhs[1] * (-perp_bisector[0])) / det

    C = _add(A, _scale(NA, s))
    radius = math.sqrt((A[0] - C[0])**2 + (A[1] - C[1])**2)

    start_angle = math.degrees(math.atan2(A[1] - C[1], A[0] - C[0]))
    end_angle = math.degrees(math.atan2(B[1] - C[1], B[0] - C[0]))

    angle_diff = end_angle - start_angle
    if angle_diff > 180:
        end_angle -= 360
    elif angle_diff < -180:
        end_angle += 360

    return {
        'type': 'arc',
        'center': C,
        'radius': radius,
        'start_angle': start_angle,
        'end_angle': end_angle
    }


def biarc_entities(
    p0: Tuple[float, float],
    t0: Tuple[float, float],
    p1: Tuple[float, float],
    t1: Tuple[float, float]
) -> List[Dict]:
    """
    Construct bi-arc G1-continuous blend between two points with tangents

    Args:
        p0: Start point (x, y) in mm
        t0: Tangent direction at start
        p1: End point (x, y) in mm
        t1: Tangent direction at end

    Returns:
        List of entity dictionaries (arc or line)
    """
    T0 = _unit(t0)
    T1 = _unit(t1)

    cross = T0[0] * T1[1] - T0[1] * T1[0]
    if abs(cross) < 1e-9:
        return [{'type': 'line', 'A': p0, 'B': p1}]

    det = T0[0] * (-T1[1]) - T0[1] * (-T1[0])
    if abs(det) < 1e-9:
        return [{'type': 'line', 'A': p0, 'B': p1}]

    rhs = _sub(p1, p0)
    s = (rhs[0] * (-T1[1]) - rhs[1] * (-T1[0])) / det

    mid = _add(p0, _scale(T0, s))

    arc1 = _arc_from_A_T_to_B(p0, T0, mid)
    if arc1 is None:
        return [{'type': 'line', 'A': p0, 'B': p1}]

    T1_reversed = (-T1[0], -T1[1])
    arc2 = _arc_from_A_T_to_B(mid, T1_reversed, p1)
    if arc2 is None:
        return [{'type': 'line', 'A': p0, 'B': p1}]

    return [arc1, arc2]


def biarc_point_at_t(entities: List[Dict], t: float) -> Tuple[float, float]:
    """Evaluate bi-arc at parameter t in [0, 1]"""
    if not entities:
        raise ValueError("Empty entity list")

    if len(entities) == 1:
        e = entities[0]
        if e['type'] == 'line':
            A, B = e['A'], e['B']
            return (
                A[0] + t * (B[0] - A[0]),
                A[1] + t * (B[1] - A[1])
            )
        elif e['type'] == 'arc':
            a0 = math.radians(e['start_angle'])
            a1 = math.radians(e['end_angle'])
            angle = a0 + t * (a1 - a0)
            C = e['center']
            r = e['radius']
            return (
                C[0] + r * math.cos(angle),
                C[1] + r * math.sin(angle)
            )
    else:
        if t < 0.5:
            return biarc_point_at_t([entities[0]], t * 2)
        else:
            return biarc_point_at_t([entities[1]], (t - 0.5) * 2)

    raise ValueError("Unknown entity type")


def biarc_length(entities: List[Dict]) -> float:
    """Approximate total arc length of bi-arc curve"""
    total = 0.0
    for e in entities:
        if e['type'] == 'line':
            A, B = e['A'], e['B']
            dx = B[0] - A[0]
            dy = B[1] - A[1]
            total += math.sqrt(dx*dx + dy*dy)
        elif e['type'] == 'arc':
            r = e['radius']
            a0 = math.radians(e['start_angle'])
            a1 = math.radians(e['end_angle'])
            angle_span = abs(a1 - a0)
            total += r * angle_span
    return total
