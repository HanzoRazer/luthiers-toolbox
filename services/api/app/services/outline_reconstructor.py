"""
OutlineReconstructor — Gap Completion Using Instrument Geometry
===============================================================
Completes partial body outlines by bridging gaps with geometrically
correct arcs based on measured instrument curvature data.

Input:  List[Chain] from blueprint_clean.py line 715
Output: List[Chain] with gaps bridged by zone-appropriate arcs

Author: Production Shop  Date: 2026-04-14
"""

from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..cam.unified_dxf_cleaner import Chain, Point

# Import measured radii from curvature correction
try:
    from ..instrument_geometry.curvature_correction import MEASURED_RADII
    RADII_AVAILABLE = True
except ImportError:
    MEASURED_RADII = {}
    RADII_AVAILABLE = False

logger = logging.getLogger(__name__)


# ── Zone classification ───────────────────────────────────────────────────────

class GapZone(str, Enum):
    UPPER_BOUT = "upper_bout"
    WAIST = "waist"
    LOWER_BOUT = "lower_bout"
    HORN_TIP = "horn_tip"
    CUTAWAY = "cutaway"
    UNKNOWN = "unknown"


CONCAVE_ZONES = {GapZone.CUTAWAY}

# Normalized Y boundaries (0.0=top/neck, 1.0=bottom/butt)
# Electric: neck at top, lower bout at bottom
# Acoustic: same orientation
ELECTRIC_ZONE_BOUNDARIES = {
    GapZone.HORN_TIP: (0.00, 0.20),
    GapZone.CUTAWAY: (0.20, 0.40),
    GapZone.WAIST: (0.40, 0.60),
    GapZone.LOWER_BOUT: (0.60, 1.00),
}

ACOUSTIC_ZONE_BOUNDARIES = {
    GapZone.UPPER_BOUT: (0.00, 0.30),
    GapZone.WAIST: (0.30, 0.55),
    GapZone.LOWER_BOUT: (0.55, 1.00),
}

ELECTRIC_SPECS = {
    "stratocaster", "telecaster", "les_paul", "gibson_sg", "melody_maker",
    "flying_v", "es335", "gibson_explorer", "eds1275", "bass_4string",
    "smart_guitar",
}

ZONE_RADIUS_KEY: Dict[GapZone, str] = {
    GapZone.UPPER_BOUT: "bout",
    GapZone.LOWER_BOUT: "bout",
    GapZone.WAIST: "waist",
    GapZone.HORN_TIP: "horn_tip",
    GapZone.CUTAWAY: "cutaway",
    GapZone.UNKNOWN: "default",
}


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2

    @classmethod
    def from_points(cls, points: List[Point]) -> "BoundingBox":
        if not points:
            return cls(0, 0, 0, 0)
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        return cls(min(xs), min(ys), max(xs), max(ys))

    @classmethod
    def union(cls, boxes: List["BoundingBox"]) -> "BoundingBox":
        if not boxes:
            return cls(0, 0, 0, 0)
        return cls(
            min(b.x0 for b in boxes),
            min(b.y0 for b in boxes),
            max(b.x1 for b in boxes),
            max(b.y1 for b in boxes),
        )


@dataclass
class Gap:
    chain_idx: int
    start: Point          # chain.points[-1]
    end: Point            # chain.points[0]
    distance_mm: float
    zone: GapZone
    radius_mm: float
    concave: bool


@dataclass
class ReconstructionResult:
    chains: List[Chain]
    gaps_found: int
    gaps_bridged: int
    gaps_skipped: int
    unbridged: List[Gap] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


# ── Main class ────────────────────────────────────────────────────────────────

class OutlineReconstructor:
    """
    Completes partial outlines using instrument-specific curvature.

    Usage:
        r = OutlineReconstructor(spec_name="dreadnought")
        result = r.complete(final_chains)
        completed_chains = result.chains
    """

    def __init__(
        self,
        spec_name: str,
        max_gap_mm: float = 8.0,
        min_gap_mm: float = 1.0,
        arc_point_spacing_mm: float = 0.5,
    ):
        self.spec_name = spec_name
        self.max_gap_mm = max_gap_mm
        self.min_gap_mm = min_gap_mm
        self.spacing = arc_point_spacing_mm
        self.is_electric = spec_name in ELECTRIC_SPECS
        self.radii = MEASURED_RADII.get(spec_name, {})

    def complete(self, chains: List[Chain]) -> ReconstructionResult:
        if not chains:
            return ReconstructionResult(
                chains=[],
                gaps_found=0,
                gaps_bridged=0,
                gaps_skipped=0,
            )

        # Body bounding box from ALL chains combined — not individual chain bbox
        all_points = [p for c in chains for p in c.points]
        body_bbox = BoundingBox.from_points(all_points)

        gaps = self._detect_gaps(chains, body_bbox)
        result = self._bridge_gaps(chains, gaps)

        logger.info(
            f"OUTLINE_RECONSTRUCT | spec={self.spec_name} "
            f"gaps_found={result.gaps_found} bridged={result.gaps_bridged} "
            f"skipped={result.gaps_skipped}"
        )

        return result

    # ── Gap detection ─────────────────────────────────────────────────────────

    def _detect_gaps(
        self,
        chains: List[Chain],
        body_bbox: BoundingBox,
    ) -> List[Optional[Gap]]:
        """
        Returns a list parallel to chains.
        Entry is None if chain is closed or gap is out of range.
        """
        result = []
        for idx, chain in enumerate(chains):
            if len(chain.points) < 2:
                result.append(None)
                continue

            if chain.is_closed(tolerance=self.min_gap_mm):
                result.append(None)
                continue

            start = chain.points[-1]
            end = chain.points[0]
            dist = start.distance_to(end)

            if dist < self.min_gap_mm or dist > self.max_gap_mm:
                result.append(None)
                continue

            zone = self._classify_zone(start, end, body_bbox)
            radius = self._get_zone_radius(zone)
            concave = zone in CONCAVE_ZONES

            result.append(Gap(
                chain_idx=idx,
                start=start,
                end=end,
                distance_mm=dist,
                zone=zone,
                radius_mm=radius,
                concave=concave,
            ))

        return result

    # ── Zone classification ───────────────────────────────────────────────────

    def _classify_zone(
        self,
        p1: Point,
        p2: Point,
        body_bbox: BoundingBox,
    ) -> GapZone:
        if body_bbox.height < 1.0:
            return GapZone.UNKNOWN

        # Normalize gap midpoint Y relative to full body bbox
        mid_y = (p1.y + p2.y) / 2
        rel_y = (mid_y - body_bbox.y0) / body_bbox.height

        boundaries = (
            ELECTRIC_ZONE_BOUNDARIES if self.is_electric
            else ACOUSTIC_ZONE_BOUNDARIES
        )

        for zone, (y_min, y_max) in boundaries.items():
            if y_min <= rel_y < y_max:
                return zone

        return GapZone.UNKNOWN

    # ── Radius lookup ─────────────────────────────────────────────────────────

    def _get_zone_radius(self, zone: GapZone) -> float:
        key = ZONE_RADIUS_KEY.get(zone, "default")
        # Try specific key, then "bout" as fallback, then 200mm (near-flat)
        return (
            self.radii.get(key)
            or self.radii.get("bout")
            or 200.0
        )

    # ── Gap bridging ──────────────────────────────────────────────────────────

    def _bridge_gaps(
        self,
        chains: List[Chain],
        gaps: List[Optional[Gap]],
    ) -> ReconstructionResult:
        completed = []
        bridged = 0
        skipped = 0
        unbridged = []

        for chain, gap in zip(chains, gaps):
            if gap is None:
                completed.append(chain)
                continue

            arc = self._generate_arc(gap)

            if arc is None:
                unbridged.append(gap)
                skipped += 1
                completed.append(chain)
                continue

            completed.append(Chain(points=list(chain.points) + arc))
            bridged += 1

        return ReconstructionResult(
            chains=completed,
            gaps_found=sum(1 for g in gaps if g is not None),
            gaps_bridged=bridged,
            gaps_skipped=skipped,
            unbridged=unbridged,
        )

    # ── Arc generation ────────────────────────────────────────────────────────

    def _generate_arc(self, gap: Gap) -> Optional[List[Point]]:
        """
        Generate arc points from gap.start to gap.end with gap.radius_mm.
        Returns None if arc is geometrically invalid.
        """
        p1, p2 = gap.start, gap.end
        R = gap.radius_mm
        chord = p1.distance_to(p2)

        if chord < 1e-6:
            return None
        if R < chord / 2:
            # Radius too small for chord — use minimum valid radius
            R = chord / 2 * 1.001

        # Sagitta
        half_chord = chord / 2
        sagitta = R - math.sqrt(R * R - half_chord * half_chord)

        # Perpendicular to chord
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        perp_x = -dy / chord
        perp_y = dx / chord

        # Arc midpoint
        mid_x = (p1.x + p2.x) / 2
        mid_y = (p1.y + p2.y) / 2
        sign = -1.0 if gap.concave else 1.0
        arc_mid = Point(
            x=mid_x + sign * sagitta * perp_x,
            y=mid_y + sign * sagitta * perp_y,
        )

        # Circle center from p1, arc_mid, p2
        center = self._circle_center(p1, arc_mid, p2)
        if center is None:
            return None
        cx, cy = center

        # Arc angles
        a1 = math.atan2(p1.y - cy, p1.x - cx)
        a2 = math.atan2(p2.y - cy, p2.x - cx)
        sweep = a2 - a1

        # Normalize sweep to match arc direction
        if gap.concave:
            if sweep > 0:
                sweep -= 2 * math.pi
        else:
            if sweep < 0:
                sweep += 2 * math.pi

        arc_length = abs(sweep) * R
        n_points = max(3, int(arc_length / self.spacing))

        points = []
        for i in range(1, n_points + 1):  # skip i=0 (already in chain)
            t = i / n_points
            angle = a1 + t * sweep
            points.append(Point(
                x=cx + R * math.cos(angle),
                y=cy + R * math.sin(angle),
            ))

        return points

    @staticmethod
    def _circle_center(
        p1: Point, p2: Point, p3: Point
    ) -> Optional[Tuple[float, float]]:
        """Circumcenter of three points. Returns None if collinear."""
        ax, ay = p1.x, p1.y
        bx, by = p2.x, p2.y
        cx, cy = p3.x, p3.y

        D = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(D) < 1e-10:
            return None

        ux = (
            (ax ** 2 + ay ** 2) * (by - cy) +
            (bx ** 2 + by ** 2) * (cy - ay) +
            (cx ** 2 + cy ** 2) * (ay - by)
        ) / D
        uy = (
            (ax ** 2 + ay ** 2) * (cx - bx) +
            (bx ** 2 + by ** 2) * (ax - cx) +
            (cx ** 2 + cy ** 2) * (bx - ax)
        ) / D

        return ux, uy


# ── Integration wrapper ───────────────────────────────────────────────────────

def complete_outline_if_needed(
    chains: List[Chain],
    spec_name: Optional[str] = None,
    max_gap_mm: float = 8.0,
) -> Tuple[List[Chain], Optional[ReconstructionResult]]:
    """
    Drop-in wrapper for blueprint_clean.py line 715.

    Usage:
        final_chains = [c for c, _ in selected_chains]
        final_chains, recon = complete_outline_if_needed(
            final_chains, spec_name=spec_name
        )
    """
    enabled = os.environ.get("ENABLE_OUTLINE_RECONSTRUCTION", "0") == "1"

    if not enabled or not spec_name:
        return chains, None

    if not RADII_AVAILABLE:
        logger.warning("OutlineReconstructor: MEASURED_RADII not available")
        return chains, None

    if spec_name not in MEASURED_RADII:
        logger.debug(f"OutlineReconstructor: No curvature data for '{spec_name}'")
        return chains, None

    reconstructor = OutlineReconstructor(
        spec_name=spec_name,
        max_gap_mm=max_gap_mm,
    )
    result = reconstructor.complete(chains)
    return result.chains, result
