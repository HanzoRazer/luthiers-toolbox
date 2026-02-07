# File: util/poly_offset_spiral.py
# N18 Spiral PolyCut - Phase 3: Complete with arc smoothing

from __future__ import annotations

from typing import List, Sequence, Tuple, Optional
import math

try:
    import pyclipper  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "pyclipper is required for N18 poly offset / spiral. "
        "Install with `pip install pyclipper` in your API environment."
    ) from exc


# Type aliases
Point = Tuple[float, float]
Path = List[Point]
Paths = List[Path]

# Scaling factor for pyclipper integer geometry
SCALE: float = 1000.0

# Minimum polygon area (mm^2) to consider as a valid ring
MIN_AREA_MM2: float = 0.5


def _scale_point(pt: Point, scale: float = SCALE) -> Tuple[int, int]:
    """Scale a floating point (x, y) to integer coordinates for pyclipper."""
    return (int(round(pt[0] * scale)), int(round(pt[1] * scale)))


def _unscale_point(pt: Tuple[int, int], scale: float = SCALE) -> Point:
    """Unscale an integer (x, y) from pyclipper back to mm coordinates."""
    return (pt[0] / scale, pt[1] / scale)


def _scale_path(path: Sequence[Point], scale: float = SCALE) -> List[Tuple[int, int]]:
    return [_scale_point(p, scale) for p in path]


def _unscale_path(path: Sequence[Tuple[int, int]], scale: float = SCALE) -> Path:
    return [_unscale_point(p, scale) for p in path]


def _polygon_area_mm2(path: Sequence[Point]) -> float:
    """
    Compute signed polygon area (mm^2) using the shoelace formula.
    Positive = CCW, Negative = CW.
    """
    if len(path) < 3:
        return 0.0
    area = 0.0
    x0, y0 = path[-1]
    for x1, y1 in path:
        area += (x0 * y1) - (x1 * y0)
        x0, y0 = x1, y1
    return area * 0.5


def _ensure_closed(path: Sequence[Point]) -> Path:
    """Ensure the polygon is explicitly closed (first point == last point)."""
    if not path:
        return []
    if path[0] == path[-1]:
        return list(path)
    return list(path) + [path[0]]


def _normalize_outer_orientation(path: Sequence[Point]) -> Path:
    """
    Ensure outer polygon is in a consistent orientation (CCW).
    pyclipper can handle either, but consistent orientation makes debugging easier.
    """
    closed = _ensure_closed(path)
    area = _polygon_area_mm2(closed)
    if area < 0:
        # CW → reverse to CCW
        return list(reversed(closed))
    return closed


# ---------------------------------------------------------------------------
# Phase 1: onion-skin offset generator
# ---------------------------------------------------------------------------


def offset_polygon_mm(
    outer: Sequence[Point],
    offset_step: float,
    *,
    max_rings: int = 256,
    min_area_mm2: float = MIN_AREA_MM2,
    miter_limit: float = 4.0,
    arc_tolerance: float = 0.05,
) -> Paths:
    """
    Robustly offset a polygon inward in mm using pyclipper, returning a list of
    concentric offset rings (no spiral stitching here directly).

    This is the "onion-skin" generator for N18. Phase 2 uses this in
    generate_offset_rings() and then link_rings_to_spiral() to build a spiral.

    Args:
        outer:
            The outer polygon as a sequence of (x, y) points in mm.
            It should describe a simple, non-self-intersecting polygon.
        offset_step:
            Positive distance in mm between successive inward offsets.
            (Internally applied as a negative distance for inward offset.)
        max_rings:
            Safety limit on how many offset shells to generate.
        min_area_mm2:
            Minimum area for an offset ring to be kept. Very small rings are
            discarded to avoid numerical noise.
        miter_limit:
            pyclipper miter limit (for join type).
        arc_tolerance:
            pyclipper arc tolerance in scaled units, roughly controlling
            how curves are approximated.

    Returns:
        A list of rings, each a list of (x, y) in mm. The first ring is the
        first offset from the outer polygon, and so on inward.

    Raises:
        ValueError:
            If inputs are invalid (e.g., too few vertices or non-positive step).
        RuntimeError:
            If pyclipper operations fail for unexpected reasons.
    """
    # Basic validation
    if len(outer) < 3:
        raise ValueError("offset_polygon_mm: outer polygon must have at least 3 points")

    if offset_step <= 0.0:
        raise ValueError("offset_polygon_mm: offset_step must be positive (mm)")

    # Normalize orientation + closure
    outer_norm = _normalize_outer_orientation(outer)

    # Pre-scale subject path
    subj = _scale_path(outer_norm, SCALE)

    rings: Paths = []
    current_paths: List[List[Tuple[int, int]]] = [subj]
    current_step = float(offset_step)

    # pyclipper join/endpoint configuration
    join_type = pyclipper.JT_MITER
    end_type = pyclipper.ET_CLOSEDPOLYGON

    for _ in range(max_rings):
        if not current_paths:
            break

        # We only offset the largest area path from the previous iteration
        # to avoid weird behavior when multiple tiny islands remain.
        if len(current_paths) > 1:
            # Unscale temporarily to pick the largest polygon by area
            def area_scaled(path_scaled: Sequence[Tuple[int, int]]) -> float:
                path_unscaled = _unscale_path(path_scaled, SCALE)
                return abs(_polygon_area_mm2(path_unscaled))

            current_paths.sort(key=area_scaled, reverse=True)
            current_subject = current_paths[0]
        else:
            current_subject = current_paths[0]

        co = pyclipper.PyclipperOffset(miter_limit, arc_tolerance * SCALE)
        co.AddPath(current_subject, join_type, end_type)

        # Inward offset → negative distance in scaled coordinates
        try:
            solution = co.Execute(-current_step * SCALE)
        except (RuntimeError, ValueError) as exc:  # WP-1: narrowed from except Exception  # pragma: no cover
            raise RuntimeError(f"offset_polygon_mm: pyclipper offset failed: {exc}") from exc

        if not solution:
            # No more valid offsets
            break

        next_paths: List[List[Tuple[int, int]]] = []
        for sol in solution:
            unscaled = _unscale_path(sol, SCALE)
            area = abs(_polygon_area_mm2(unscaled))
            if area < min_area_mm2:
                # Too small; ignore
                continue
            # Keep ring
            rings.append(_ensure_closed(unscaled))
            # Consider this as candidate subject for next ring
            next_paths.append(sol)

        if not next_paths:
            break

        current_paths = next_paths

    return rings


def _shrink_once(outer: Sequence[Point], margin: float) -> Path:
    """
    Single-step shrink of the polygon by `margin` mm.
    Used by build_spiral_poly to honour a wall margin before rings are generated.
    """
    if margin <= 0:
        return list(outer)

    outer_norm = _normalize_outer_orientation(outer)
    subj = _scale_path(outer_norm, SCALE)

    join_type = pyclipper.JT_MITER
    end_type = pyclipper.ET_CLOSEDPOLYGON

    co = pyclipper.PyclipperOffset()
    co.AddPath(subj, join_type, end_type)

    try:
        solution = co.Execute(-margin * SCALE)
    except (RuntimeError, ValueError):  # WP-1: narrowed from except Exception
        # On failure, just return the normalized outer; better to be conservative
        return outer_norm

    if not solution:
        # Margin too large; keep original
        return outer_norm

    # Pick the largest remaining polygon as the "shrunk" outer
    def area_scaled(path_scaled: Sequence[Tuple[int, int]]) -> float:
        path_unscaled = _unscale_path(path_scaled, SCALE)
        return abs(_polygon_area_mm2(path_unscaled))

    solution_sorted = sorted(solution, key=area_scaled, reverse=True)
    return _ensure_closed(_unscale_path(solution_sorted[0], SCALE))


# ---------------------------------------------------------------------------
# Phase 2: rings → spiral stitching
# ---------------------------------------------------------------------------


def generate_offset_rings(
    outer: Sequence[Point],
    tool_d: float,
    stepover: float,
    margin: float,
    *,
    max_rings: int = 256,
) -> Paths:
    """
    Generate inward offset rings from an outer boundary, respecting margin.

    This is a higher-level helper on top of offset_polygon_mm(), doing:

        1. Shrink outer by `margin` (if > 0).
        2. Generate concentric rings at `tool_d * stepover` spacing.

    Returns:
        List of rings (outermost first) as closed paths.
    """
    if tool_d <= 0.0:
        raise ValueError("generate_offset_rings: tool_d must be positive")

    if not (0.05 <= stepover <= 0.95):
        raise ValueError("generate_offset_rings: stepover should be in [0.05, 0.95]")

    step_mm = tool_d * stepover

    if margin > 0:
        shrunk_outer = _shrink_once(outer, margin)
    else:
        shrunk_outer = list(outer)

    rings = offset_polygon_mm(
        shrunk_outer,
        offset_step=step_mm,
        max_rings=max_rings,
    )
    return rings


def _nearest_point_index(path: Sequence[Point], target: Point) -> int:
    """
    Return the index of the point in `path` closest to `target`.
    """
    if not path:
        return 0
    tx, ty = target
    best_idx = 0
    best_d2 = float("inf")
    for i, (x, y) in enumerate(path):
        dx = x - tx
        dy = y - ty
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best_idx = i
    return best_idx


def _rotate_path_to_index(path: Sequence[Point], idx: int) -> Path:
    """
    Rotate a closed path so that `idx` becomes the first element.
    Assumes path is already closed (first == last).
    """
    if not path:
        return []
    n = len(path)
    if n <= 1:
        return list(path)
    idx = idx % n
    rotated = list(path[idx:]) + list(path[1:idx + 1])  # keep closure
    # Ensure closed explicitly
    if rotated[0] != rotated[-1]:
        rotated.append(rotated[0])
    return rotated


def _reverse_path_preserving_closure(path: Sequence[Point]) -> Path:
    """
    Reverse a closed path while preserving closure (first == last).
    """
    if not path:
        return []
    if len(path) <= 2:
        return list(path)
    # strip closure, reverse, re-close
    core = list(path[:-1])
    core.reverse()
    core.append(core[0])
    return core


def link_rings_to_spiral(
    rings: Paths,
    *,
    climb: bool = True,
) -> Path:
    """
    Stitch a list of inward offset rings into a single continuous spiral path.

    Strategy:
        - Start on the outermost ring.
        - For each subsequent ring:
            * pick the nearest point to the current end of the spiral
            * rotate the ring so that point is first
            * reverse orientation when necessary to maintain smooth traversal
            * connect with a short linear link segment.

    Notes:
        - This is a geometry-only function; feed/speed/Z is handled elsewhere.
        - Assumes rings are closed paths.

    Returns:
        A single path (open polyline) representing the spiral in XY.
    """
    if not rings:
        return []

    # Start with the outermost ring
    # We will treat the path as open for the spiral (do not re-close at the end)
    spiral: Path = []

    # Determine desired orientation for main cutting direction
    # Climb milling: typically CCW for outer boundaries.
    def desired_ccw() -> bool:
        return True if climb else False

    ccw = desired_ccw()

    # Normalize orientation of each ring
    norm_rings: Paths = []
    for r in rings:
        if not r:
            continue
        # Ensure closed
        r_closed = _ensure_closed(r)
        area = _polygon_area_mm2(r_closed)
        if ccw and area < 0:
            r_norm = list(reversed(r_closed))
        elif (not ccw) and area > 0:
            r_norm = list(reversed(r_closed))
        else:
            r_norm = r_closed
        norm_rings.append(r_norm)

    if not norm_rings:
        return []

    # Initialize spiral with first ring; start at index 0
    first_ring = norm_rings[0]
    # Remove closure for the spiral; we don't want to loop back to start at the end
    spiral.extend(first_ring[:-1])

    # Walk inward through remaining rings
    for ring in norm_rings[1:]:
        if not ring:
            continue
        # Current spiral end
        current_end = spiral[-1]

        # Find nearest point on this ring to current_end
        idx = _nearest_point_index(ring, current_end)

        # Rotate ring so that nearest point is ring[0]
        rotated = _rotate_path_to_index(ring, idx)

        # Decide if we should reverse to maintain orientation alignment
        # Check the vector from first->second point; we want to roughly
        # align movement direction from current_end to ring[1].
        if len(rotated) >= 3:
            # Try both directions and choose the smaller angle to the
            # vector from current_end.
            def angle(a: Point, b: Point) -> float:
                return math.atan2(b[1] - a[1], b[0] - a[0])

            cand_forward = rotated
            cand_reverse = _reverse_path_preserving_closure(rotated)

            v_current_angle = angle(spiral[-1], cand_forward[1])
            v_rev_angle = angle(spiral[-1], cand_reverse[1])
            # Rough heuristic: choose whichever has smaller absolute delta to 0 angle
            # (i.e. less sharp turn)
            if abs(v_rev_angle) < abs(v_current_angle):
                rotated = cand_reverse

        # Build link segment from current_end to the new ring start
        link_start = current_end
        link_end = rotated[0]
        if link_start != link_end:
            spiral.append(link_end)

        # Append inner ring segment, skipping its closure point
        spiral.extend(rotated[1:-1])

    return spiral


# ---------------------------------------------------------------------------
# Phase 3: ARC SMOOTHING ENGINE
# ---------------------------------------------------------------------------


def _normalize(vx: float, vy: float) -> Tuple[float, float]:
    mag = math.hypot(vx, vy)
    if mag < 1e-9:
        return 0.0, 0.0
    return vx / mag, vy / mag


def _distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _corner_angle(prev: Point, curr: Point, nxt: Point) -> float:
    """Return interior angle in radians at curr."""
    ax, ay = prev[0] - curr[0], prev[1] - curr[1]
    bx, by = nxt[0] - curr[0], nxt[1] - curr[1]

    ax, ay = _normalize(ax, ay)
    bx, by = _normalize(bx, by)

    dot = ax * bx + ay * by
    dot = max(-1.0, min(1.0, dot))
    return math.acos(dot)


def _fillet(
    prev: Point,
    curr: Point,
    nxt: Point,
    radius: float,
    segments: int = 5,
) -> Path:
    """
    Insert a circular fillet between prev → curr → nxt.
    Returns small polyline approximating the arc.
    """
    # Direction vectors
    vx1, vy1 = prev[0] - curr[0], prev[1] - curr[1]
    vx2, vy2 = nxt[0] - curr[0], nxt[1] - curr[1]
    nx1, ny1 = _normalize(vx1, vy1)
    nx2, ny2 = _normalize(vx2, vy2)

    # Points offset from curr along each direction
    p1 = (curr[0] + nx1 * radius, curr[1] + ny1 * radius)
    p2 = (curr[0] + nx2 * radius, curr[1] + ny2 * radius)

    # Mid-angle interpolation for arc (simple circular transition)
    angle1 = math.atan2(nx1 * -1, ny1 * -1)  # rotate into perpendicular space
    angle2 = math.atan2(nx2 * -1, ny2 * -1)

    # Normalize sweep
    # We want smallest positive sweep
    while angle2 < angle1:
        angle2 += 2 * math.pi

    arc = []
    for i in range(segments + 1):
        t = i / segments
        ang = angle1 + (angle2 - angle1) * t
        x = curr[0] + radius * math.cos(ang)
        y = curr[1] + radius * math.sin(ang)
        arc.append((x, y))
    return arc


def smooth_with_arcs(
    path: Sequence[Point],
    corner_radius_min: float,
    corner_tol_mm: float,
) -> Path:
    """
    Phase 3 arc smoothing: scan corners of `path` and insert small circular
    fillets where:
        - corner angle is sufficiently sharp
        - path segments are long enough to accept a fillet

    This does NOT emit G2/G3 directly — g2_emitter will convert these
    small arc-approximated poly segments into G2/G3 as needed.
    """
    if corner_radius_min is None:
        return list(path)
    if corner_tol_mm is None:
        corner_tol_mm = corner_radius_min * 0.5

    pts = list(path)
    n = len(pts)
    if n < 3:
        return pts

    out: Path = [pts[0]]

    for i in range(1, n - 1):
        prev = pts[i - 1]
        curr = pts[i]
        nxt = pts[i + 1]

        # Corner angle
        angle = _corner_angle(prev, curr, nxt)

        # If nearly straight → skip smoothing
        if abs(angle - math.pi) < 0.1:
            out.append(curr)
            continue

        # Determine allowable radius based on adjacent segments
        d1 = _distance(prev, curr)
        d2 = _distance(curr, nxt)
        max_r = min(d1, d2) * 0.3  # keep reasonable
        r = min(max_r, corner_radius_min)

        if r < corner_radius_min * 0.5:
            # Too small to matter
            out.append(curr)
            continue

        # Insert fillet
        arc = _fillet(prev, curr, nxt, r, segments=5)
        # Replace the corner by the arc (but avoid duplicating curr)
        out.extend(arc)

    out.append(pts[-1])
    return out


# ---------------------------------------------------------------------------
# Phase 3: Build spiral poly (complete implementation)
# ---------------------------------------------------------------------------


def build_spiral_poly(
    outer: Sequence[Point],
    tool_d: float,
    stepover: float,
    margin: float,
    *,
    climb: bool = True,
    corner_radius_min: Optional[float] = None,
    corner_tol_mm: Optional[float] = None,
) -> Path:
    """
    Build a spiral toolpath from a pocket boundary using inward offsets.

    High-level steps:
        1. Shrink outer by `margin` (if > 0).
        2. Generate inward offset rings at spacing tool_d * stepover.
        3. Stitch rings into a single continuous spiral path.
        4. (Phase 3) Optionally smooth with arcs (corner fillets).

    For N18, the spiral path is then consumed by the G-code emitter:
        - XY is taken from this polyline
        - Feed/Z is managed by the router.

    Returns:
        A single path (open polyline) in XY (mm).
    """
    rings = generate_offset_rings(
        outer=outer,
        tool_d=tool_d,
        stepover=stepover,
        margin=margin,
    )
    if not rings:
        return []

    raw_spiral = link_rings_to_spiral(rings, climb=climb)

    # Arc smoothing (optional)
    if corner_radius_min:
        smoothed = smooth_with_arcs(
            raw_spiral,
            corner_radius_min=corner_radius_min,
            corner_tol_mm=corner_tol_mm or corner_radius_min * 0.5,
        )
        return smoothed

    return raw_spiral


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    'build_spiral_poly',
    'offset_polygon_mm',
    'generate_offset_rings',
    'link_rings_to_spiral',
    'smooth_with_arcs',
]

