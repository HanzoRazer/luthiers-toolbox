#!/usr/bin/env python3
"""
Constraint Extractor — Extract Landmarks from Partial DXF Outline
==================================================================

Reads a partial body outline DXF (from vectorizer) and extracts
landmark points for the BodyContourSolver.

Landmarks detected:
  - butt_center: lowest Y extent (centerline)
  - neck_center: highest Y extent with significant width
  - lower_bout_max: maximum X extent in lower body region
  - waist_min: minimum X in middle body region
  - upper_bout_max: maximum X extent in upper body region

Author: Production Shop
Date: 2026-04-16
Sprint: 9 — InstrumentBodyGenerator
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import ezdxf

from .body_contour_solver import LandmarkPoint


@dataclass
class ExtractionResult:
    """Result of landmark extraction from DXF."""
    landmarks: List[LandmarkPoint]
    points_extracted: int
    chains_found: int
    body_chain_points: int
    notes: str = ""


class ConstraintExtractor:
    """Extracts body landmarks from partial vectorizer DXF output."""

    def __init__(self, min_chain_points: int = 20, symmetric_tolerance: float = 50.0):
        """
        Args:
            min_chain_points: Minimum points for a chain to be considered
            symmetric_tolerance: Max absolute X difference to be considered symmetric
        """
        self.min_chain_points = min_chain_points
        self.symmetric_tolerance = symmetric_tolerance

    def extract_landmarks_from_dxf(self, dxf_path: str) -> List[LandmarkPoint]:
        """
        Extract body landmark points from a partial vectorizer output DXF.

        Args:
            dxf_path: Path to the DXF file

        Returns:
            List of LandmarkPoint objects

        Raises:
            FileNotFoundError: If DXF file does not exist
        """
        result = self.extract_with_metadata(dxf_path)
        return result.landmarks

    def extract_with_metadata(self, dxf_path: str) -> ExtractionResult:
        """
        Extract landmarks with full metadata about the extraction.

        Returns ExtractionResult with landmarks and extraction statistics.
        """
        if not os.path.exists(dxf_path):
            raise FileNotFoundError(f"DXF not found: {dxf_path}")

        points = self._extract_points_from_dxf(dxf_path)
        body_points = self._filter_body_outline(points)
        landmarks = self._detect_landmarks(body_points)

        return ExtractionResult(
            landmarks=landmarks,
            points_extracted=len(points),
            chains_found=len(points) // 50 if points else 0,  # Rough estimate
            body_chain_points=len(body_points),
            notes=f"Filtered {len(points)} -> {len(body_points)} body points",
        )

    def _extract_points_from_dxf(self, dxf_path: str) -> List[Tuple[float, float]]:
        """Extract all vertex points from DXF entities."""
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        all_chains = []
        for entity in msp:
            chain_pts = []
            if entity.dxftype() == "LINE":
                chain_pts.append((entity.dxf.start.x, entity.dxf.start.y))
                chain_pts.append((entity.dxf.end.x, entity.dxf.end.y))
            elif entity.dxftype() == "LWPOLYLINE":
                for pt in entity.get_points():
                    chain_pts.append((pt[0], pt[1]))
            elif entity.dxftype() == "POLYLINE":
                for vertex in entity.vertices:
                    loc = vertex.dxf.location
                    chain_pts.append((loc.x, loc.y))
            if chain_pts:
                all_chains.append(chain_pts)

        # Flatten all chains
        points = []
        for chain in all_chains:
            points.extend(chain)

        return points

    def _filter_body_outline(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Filter points to only body outline chains.

        Body outline characteristics:
          - Spans both negative and positive X (symmetric about centerline)
          - Reasonable half-width (100-300mm)
        """
        if not points:
            return []

        # Group points by proximity to identify chains
        # For now, use simple filtering approach

        # First pass: find points that form symmetric outline
        body_points = []
        xs = [p[0] for p in points]
        min_x, max_x = min(xs), max(xs)

        # Check for symmetry
        if min_x < -self.symmetric_tolerance and max_x > self.symmetric_tolerance:
            # Appears symmetric - check width
            half_width = max(abs(min_x), abs(max_x))
            if 100 < half_width < 300:
                # Keep only points in reasonable width range
                body_points = [p for p in points if abs(p[0]) < 300]
            else:
                # Width out of range - take largest chain
                body_points = points
        else:
            # Not symmetric - return all points, let landmark detection handle it
            body_points = points

        return body_points

    def _detect_landmarks(self, points: List[Tuple[float, float]]) -> List[LandmarkPoint]:
        """
        Detect body landmarks from filtered points.

        Landmarks:
          - butt_center: lowest Y, near X=0
          - neck_center: highest Y, near X=0
          - lower_bout_max: max X in lower 35% of Y range
          - waist_min: min X in middle 35-65% of Y range (if narrower than lower bout)
          - upper_bout_max: max X in upper 65-100% of Y range
        """
        if not points:
            return []

        landmarks = []

        # Find Y extents
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        y_range = max_y - min_y

        if y_range < 10:
            return []  # Degenerate case

        # Divide into regions
        lower_y_cutoff = min_y + y_range * 0.35
        upper_y_cutoff = min_y + y_range * 0.65

        lower_region = [p for p in points if p[1] < lower_y_cutoff]
        middle_region = [p for p in points if lower_y_cutoff <= p[1] <= upper_y_cutoff]
        upper_region = [p for p in points if p[1] > upper_y_cutoff]

        # Butt center (lowest Y, centered)
        butt_pts = sorted(points, key=lambda p: p[1])[:10]
        if butt_pts:
            butt_x_avg = sum(p[0] for p in butt_pts) / len(butt_pts)
            landmarks.append(LandmarkPoint(
                label='butt_center',
                x_mm=butt_x_avg,
                y_mm=min_y,
                source='dxf',
                confidence=0.95,
            ))

        # Neck center (highest Y, centered)
        neck_pts = sorted(points, key=lambda p: p[1], reverse=True)[:10]
        if neck_pts:
            neck_x_avg = sum(p[0] for p in neck_pts) / len(neck_pts)
            landmarks.append(LandmarkPoint(
                label='neck_center',
                x_mm=neck_x_avg,
                y_mm=max_y,
                source='dxf',
                confidence=0.95,
            ))

        # Lower bout max (positive side)
        if lower_region:
            positive_lower = [p for p in lower_region if p[0] > 0]
            if positive_lower:
                lb_pt = max(positive_lower, key=lambda p: p[0])
                landmarks.append(LandmarkPoint(
                    label='lower_bout_max',
                    x_mm=lb_pt[0],
                    y_mm=lb_pt[1],
                    source='dxf',
                    confidence=0.90,
                ))

        # Waist min (only if significantly narrower than lower bout)
        if middle_region:
            estimated_lower_bout_half = max(p[0] for p in lower_region) if lower_region else 200

            # Try Option A first — waist must be at least 30% of lower bout width
            min_waist_x = estimated_lower_bout_half * 0.30
            waist_candidates = [p for p in middle_region if p[0] > min_waist_x]

            waist_pt = None
            if waist_candidates:
                waist_pt = min(waist_candidates, key=lambda p: p[0])
            else:
                # Option B fallback — no valid candidates above threshold
                positive_middle = sorted([p for p in middle_region if p[0] > 5], key=lambda p: p[0])
                if positive_middle:
                    waist_pt = positive_middle[max(1, len(positive_middle) // 10)]

            if waist_pt and waist_pt[0] < estimated_lower_bout_half * 0.80:
                landmarks.append(LandmarkPoint(
                    label='waist_min',
                    x_mm=waist_pt[0],
                    y_mm=waist_pt[1],
                    source='dxf',
                    confidence=0.85,
                ))

        # Upper bout max (if region has enough points)
        if upper_region and len(upper_region) > 10:
            positive_upper = [p for p in upper_region if p[0] > 0]
            if positive_upper:
                ub_pt = max(positive_upper, key=lambda p: p[0])
                # Only add if reasonably wide
                lower_max_x = max(p[0] for p in lower_region) if lower_region else 200
                if ub_pt[0] > lower_max_x * 0.60:
                    landmarks.append(LandmarkPoint(
                        label='upper_bout_max',
                        x_mm=ub_pt[0],
                        y_mm=ub_pt[1],
                        source='dxf',
                        confidence=0.90,
                    ))

        return landmarks


# ─── Verification ─────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("=== Step 5: ConstraintExtractor Verification ===\n")

    test_dxf = os.path.join(
        os.path.dirname(__file__),
        "results",
        "dreadnought_phase5b_tier0_final.dxf"
    )

    if not os.path.exists(test_dxf):
        print(f"  Test file not found: {test_dxf}")
        print("  Step 5: SKIP\n")
    else:
        extractor = ConstraintExtractor()
        result = extractor.extract_with_metadata(test_dxf)

        print(f"  File: {os.path.basename(test_dxf)}")
        print(f"  Points extracted: {result.points_extracted}")
        print(f"  Body points: {result.body_chain_points}")
        print(f"  Landmarks found: {len(result.landmarks)}")

        for lm in result.landmarks:
            print(f"    {lm.label}: ({lm.x_mm:.1f}, {lm.y_mm:.1f}) conf={lm.confidence}")

        # Pass conditions:
        # - At least 3 landmarks (butt, neck, lower_bout at minimum)
        # - lower_bout_max found
        passed = True
        has_lower_bout = any(lm.label == 'lower_bout_max' for lm in result.landmarks)
        if len(result.landmarks) >= 3 and has_lower_bout:
            print("\n  Step 5: PASS")
        else:
            print(f"\n  Step 5: FAIL (need 3+ landmarks with lower_bout)")
            passed = False
