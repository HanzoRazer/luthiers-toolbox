#!/usr/bin/env python3
"""
Body Region Selector — Automatic body outline detection from full blueprint sheets

Classifies all closed regions by geometry to automatically select the instrument
body outline, discarding title blocks, annotations, and auxiliary views.

Classification rules:
- Border/frame: largest bbox, nearly fills sheet → discard
- Title block: rectangular, high aspect ratio, corner position → discard
- Dimension annotations: small, scattered, linear → discard
- Body outline: largest non-rectangular closed contour, roughly centered

Author: Production Shop
Date: 2026-04-17
Sprint: 3 — Automatic Body Region Selection
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import ezdxf

logger = logging.getLogger(__name__)


class RegionType(Enum):
    """Classification of detected regions."""
    BODY_OUTLINE = "body_outline"
    PAGE_BORDER = "page_border"
    TITLE_BLOCK = "title_block"
    AUXILIARY_VIEW = "auxiliary_view"
    ANNOTATION = "annotation"
    UNKNOWN = "unknown"


@dataclass
class DetectedRegion:
    """A detected closed region with classification metadata."""
    chain_index: int
    points: List[Tuple[float, float]]
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    layer: str

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def area(self) -> float:
        """Bounding box area."""
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        """Width / height ratio."""
        if self.height == 0:
            return 0
        return self.width / self.height

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)

    @property
    def perimeter(self) -> float:
        """Approximate perimeter from point chain."""
        if len(self.points) < 2:
            return 0
        total = 0
        for i in range(len(self.points) - 1):
            dx = self.points[i+1][0] - self.points[i][0]
            dy = self.points[i+1][1] - self.points[i][1]
            total += (dx*dx + dy*dy) ** 0.5
        # Close the loop
        dx = self.points[0][0] - self.points[-1][0]
        dy = self.points[0][1] - self.points[-1][1]
        total += (dx*dx + dy*dy) ** 0.5
        return total

    @property
    def compactness(self) -> float:
        """
        Compactness ratio: 4π × area / perimeter².
        Circle = 1.0, rectangle ≈ 0.785, long thin shape → 0.
        Guitar bodies typically 0.5-0.8.
        """
        if self.perimeter == 0:
            return 0
        return (4 * 3.14159 * self.area) / (self.perimeter ** 2)


@dataclass
class ClassifiedRegion:
    """Region with classification result."""
    region: DetectedRegion
    region_type: RegionType
    confidence: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class SelectionResult:
    """Result of body region selection."""
    success: bool
    selected_region: Optional[ClassifiedRegion]
    all_regions: List[ClassifiedRegion]
    decision: str  # "automatic", "ambiguous", "no_candidates"
    message: str


class BodyRegionSelector:
    """
    Automatic body outline selection from full blueprint sheets.

    Analyzes all closed contours and selects the most likely body outline
    based on geometry, position, and shape characteristics.
    """

    def __init__(
        self,
        min_body_area_mm2: float = 10000.0,      # ~100mm × 100mm minimum
        max_body_area_mm2: float = 500000.0,     # ~700mm × 700mm maximum
        page_fill_threshold: float = 0.85,       # >85% of page = border
        title_block_aspect_min: float = 2.5,     # Width/height > 2.5 = title block
        annotation_max_area_mm2: float = 5000.0, # Small regions = annotations
        body_aspect_min: float = 0.6,            # Body aspect ratio range
        body_aspect_max: float = 1.8,
        center_tolerance: float = 0.3,           # Body within 30% of center
    ):
        self.min_body_area = min_body_area_mm2
        self.max_body_area = max_body_area_mm2
        self.page_fill_threshold = page_fill_threshold
        self.title_block_aspect_min = title_block_aspect_min
        self.annotation_max_area = annotation_max_area_mm2
        self.body_aspect_min = body_aspect_min
        self.body_aspect_max = body_aspect_max
        self.center_tolerance = center_tolerance

    def select_from_dxf(self, dxf_path: str) -> SelectionResult:
        """
        Analyze DXF and select the body outline region.

        Args:
            dxf_path: Path to DXF file with LINE entities

        Returns:
            SelectionResult with selected body region or error
        """
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Extract all LINE entities and build chains
        regions = self._extract_regions(msp)

        if not regions:
            return SelectionResult(
                success=False,
                selected_region=None,
                all_regions=[],
                decision="no_candidates",
                message="No closed contours found. Check scan quality (300 DPI minimum, PNG format)."
            )

        # Get page bounds for relative positioning
        page_bounds = self._get_page_bounds(regions)

        # Classify each region
        classified = [self._classify_region(r, page_bounds) for r in regions]

        # Find body candidates
        body_candidates = [c for c in classified if c.region_type == RegionType.BODY_OUTLINE]

        if not body_candidates:
            return SelectionResult(
                success=False,
                selected_region=None,
                all_regions=classified,
                decision="no_candidates",
                message="No body outline candidates found. All regions classified as borders, title blocks, or annotations."
            )

        if len(body_candidates) == 1:
            # Clear winner
            return SelectionResult(
                success=True,
                selected_region=body_candidates[0],
                all_regions=classified,
                decision="automatic",
                message=f"Body outline selected automatically ({body_candidates[0].region.width:.0f}×{body_candidates[0].region.height:.0f}mm)"
            )

        # Multiple candidates — pick best by confidence
        body_candidates.sort(key=lambda c: c.confidence, reverse=True)
        best = body_candidates[0]
        runner_up = body_candidates[1] if len(body_candidates) > 1 else None

        margin = best.confidence - (runner_up.confidence if runner_up else 0)

        if margin > 0.2:
            # Clear winner by confidence
            return SelectionResult(
                success=True,
                selected_region=best,
                all_regions=classified,
                decision="automatic",
                message=f"Body outline selected (confidence {best.confidence:.0%}, margin {margin:.0%})"
            )

        # Ambiguous — multiple similar candidates
        return SelectionResult(
            success=False,
            selected_region=best,  # Provide best guess
            all_regions=classified,
            decision="ambiguous",
            message=f"Multiple body candidates ({len(body_candidates)}). Manual selection recommended."
        )

    def _extract_regions(self, msp) -> List[DetectedRegion]:
        """Extract closed regions from LINE entities."""
        # Group lines by layer
        layer_lines: Dict[str, List[Tuple[Tuple[float, float], Tuple[float, float]]]] = defaultdict(list)

        for entity in msp:
            if entity.dxftype() == "LINE":
                layer = entity.dxf.layer
                start = (round(entity.dxf.start.x, 1), round(entity.dxf.start.y, 1))
                end = (round(entity.dxf.end.x, 1), round(entity.dxf.end.y, 1))
                layer_lines[layer].append((start, end))

        regions = []
        chain_index = 0

        for layer, lines in layer_lines.items():
            chains = self._build_chains(lines)

            for chain in chains:
                if len(chain) < 4:  # Need at least 4 points for a closed region
                    continue

                # Check if closed (first and last point within tolerance)
                dist = ((chain[0][0] - chain[-1][0])**2 + (chain[0][1] - chain[-1][1])**2)**0.5
                if dist > 5.0:  # More than 5mm gap = not closed
                    continue

                # Compute bounds
                xs = [p[0] for p in chain]
                ys = [p[1] for p in chain]

                regions.append(DetectedRegion(
                    chain_index=chain_index,
                    points=chain,
                    min_x=min(xs),
                    min_y=min(ys),
                    max_x=max(xs),
                    max_y=max(ys),
                    layer=layer,
                ))
                chain_index += 1

        return regions

    def _build_chains(
        self,
        lines: List[Tuple[Tuple[float, float], Tuple[float, float]]]
    ) -> List[List[Tuple[float, float]]]:
        """Build connected point chains from line segments."""
        if not lines:
            return []

        adj: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], int]]] = defaultdict(list)

        for i, (p1, p2) in enumerate(lines):
            adj[p1].append((p2, i))
            adj[p2].append((p1, i))

        visited = set()
        chains = []

        for start_pt in adj:
            unvisited = [(pt, idx) for pt, idx in adj[start_pt] if idx not in visited]
            if not unvisited:
                continue

            chain = [start_pt]
            current = start_pt

            while True:
                connections = [(pt, idx) for pt, idx in adj[current] if idx not in visited]
                if not connections:
                    break

                next_pt, line_idx = connections[0]
                visited.add(line_idx)
                chain.append(next_pt)
                current = next_pt

            if len(chain) >= 2:
                chains.append(chain)

        return chains

    def _get_page_bounds(
        self,
        regions: List[DetectedRegion]
    ) -> Tuple[float, float, float, float]:
        """Get overall page bounds from all regions."""
        if not regions:
            return (0, 0, 1000, 1000)

        min_x = min(r.min_x for r in regions)
        min_y = min(r.min_y for r in regions)
        max_x = max(r.max_x for r in regions)
        max_y = max(r.max_y for r in regions)

        return (min_x, min_y, max_x, max_y)

    def _classify_region(
        self,
        region: DetectedRegion,
        page_bounds: Tuple[float, float, float, float]
    ) -> ClassifiedRegion:
        """Classify a single region by geometry and position."""
        reasons = []

        page_min_x, page_min_y, page_max_x, page_max_y = page_bounds
        page_width = page_max_x - page_min_x
        page_height = page_max_y - page_min_y
        page_area = page_width * page_height

        # Check for page border/frame
        fill_ratio = region.area / page_area if page_area > 0 else 0
        if fill_ratio > self.page_fill_threshold:
            reasons.append(f"Fills {fill_ratio:.0%} of page (border)")
            return ClassifiedRegion(
                region=region,
                region_type=RegionType.PAGE_BORDER,
                confidence=0.95,
                reasons=reasons,
            )

        # Check for title block (wide rectangle in corner)
        if region.aspect_ratio > self.title_block_aspect_min:
            # Check if in corner
            center_x, center_y = region.center
            in_corner = (
                (center_x < page_min_x + page_width * 0.2 or center_x > page_max_x - page_width * 0.2) and
                (center_y < page_min_y + page_height * 0.2 or center_y > page_max_y - page_height * 0.2)
            )
            if in_corner:
                reasons.append(f"Wide rectangle in corner (aspect {region.aspect_ratio:.1f})")
                return ClassifiedRegion(
                    region=region,
                    region_type=RegionType.TITLE_BLOCK,
                    confidence=0.85,
                    reasons=reasons,
                )

        # Check for small annotation
        if region.area < self.annotation_max_area:
            reasons.append(f"Small region ({region.area:.0f}mm²)")
            return ClassifiedRegion(
                region=region,
                region_type=RegionType.ANNOTATION,
                confidence=0.80,
                reasons=reasons,
            )

        # Check for body outline criteria
        confidence = 0.5  # Base confidence

        # Size in expected range
        if self.min_body_area <= region.area <= self.max_body_area:
            reasons.append(f"Size in body range ({region.width:.0f}×{region.height:.0f}mm)")
            confidence += 0.15
        else:
            reasons.append(f"Size outside typical body range")
            confidence -= 0.1

        # Aspect ratio in guitar range
        if self.body_aspect_min <= region.aspect_ratio <= self.body_aspect_max:
            reasons.append(f"Aspect ratio typical for body ({region.aspect_ratio:.2f})")
            confidence += 0.1

        # Position near center
        center_x, center_y = region.center
        page_center_x = (page_min_x + page_max_x) / 2
        page_center_y = (page_min_y + page_max_y) / 2

        x_offset = abs(center_x - page_center_x) / page_width if page_width > 0 else 0
        y_offset = abs(center_y - page_center_y) / page_height if page_height > 0 else 0

        if x_offset < self.center_tolerance and y_offset < self.center_tolerance:
            reasons.append("Roughly centered on page")
            confidence += 0.1

        # Compactness (guitar bodies are moderately compact)
        if 0.3 <= region.compactness <= 0.9:
            reasons.append(f"Shape compactness typical for body ({region.compactness:.2f})")
            confidence += 0.1

        # Largest non-border region bonus
        confidence = min(1.0, max(0.0, confidence))

        if confidence >= 0.5:
            return ClassifiedRegion(
                region=region,
                region_type=RegionType.BODY_OUTLINE,
                confidence=confidence,
                reasons=reasons,
            )

        # Default to auxiliary view
        reasons.append("Does not match body criteria")
        return ClassifiedRegion(
            region=region,
            region_type=RegionType.AUXILIARY_VIEW,
            confidence=0.5,
            reasons=reasons,
        )


def select_body_region(dxf_path: str) -> SelectionResult:
    """
    Convenience function to select body region from a DXF file.

    Args:
        dxf_path: Path to DXF with LINE entities

    Returns:
        SelectionResult with selected body or error message
    """
    selector = BodyRegionSelector()
    return selector.select_from_dxf(dxf_path)
