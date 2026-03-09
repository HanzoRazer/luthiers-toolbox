"""
Dimension Linker - High-Level Orchestrator
===========================================

Orchestrates the complete dimension-to-geometry association pipeline.

Author: The Production Shop
Version: 4.0.0-alpha
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from .arrow_detector import ArrowDetector, Arrow
from .leader_associator import (
    LeaderLineAssociator,
    TextRegion,
    AssociatedDimension,
    WitnessLineDetector
)

logger = logging.getLogger(__name__)


@dataclass
class LinkedDimensions:
    """Complete dimension linkage result."""
    source_file: str
    dimensions: List[AssociatedDimension] = field(default_factory=list)
    unmatched_texts: List[TextRegion] = field(default_factory=list)
    arrows_detected: int = 0
    association_rate: float = 0.0
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_file': self.source_file,
            'dimensions': [d.to_dict() for d in self.dimensions],
            'unmatched_texts': [
                {'text': t.text, 'value': t.parsed_value, 'unit': t.unit}
                for t in self.unmatched_texts
            ],
            'statistics': {
                'arrows_detected': self.arrows_detected,
                'dimensions_linked': len(self.dimensions),
                'unmatched_count': len(self.unmatched_texts),
                'association_rate': self.association_rate,
                'processing_time_ms': self.processing_time_ms
            }
        }

    def to_json(self, path: str):
        """Export to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"LinkedDimensions: {len(self.dimensions)} linked, "
            f"{len(self.unmatched_texts)} unmatched "
            f"({self.association_rate:.0%} rate)"
        )


class MultiFactorRanker:
    """
    Multi-factor ranking for dimension-geometry association.

    Scoring:
    - Proximity: 0-50 points (closer = better)
    - Plausibility: 0-30 points (dimension matches measurement)
    - Type match: 0-20 points (text context matches feature)
    """

    def __init__(self):
        self.weights = {
            'proximity': 50,
            'plausibility': 30,
            'type_match': 20
        }

    def rank(
        self,
        text: TextRegion,
        candidates: List[Any],
        mm_per_px: float
    ) -> List[tuple]:
        """Rank candidates by multi-factor score."""
        scored = []

        for candidate in candidates:
            score = self._calculate_score(text, candidate, mm_per_px)
            scored.append((candidate, score))

        return sorted(scored, key=lambda x: -x[1])

    def _calculate_score(
        self,
        text: TextRegion,
        candidate: Any,
        mm_per_px: float
    ) -> float:
        """Calculate total score for a candidate."""
        score = 0.0

        # Proximity score
        if hasattr(candidate, 'distance'):
            distance_mm = candidate.distance * mm_per_px
            if distance_mm < 10:
                score += self.weights['proximity']
            elif distance_mm < 30:
                score += self.weights['proximity'] * 0.7
            elif distance_mm < 60:
                score += self.weights['proximity'] * 0.4
            elif distance_mm < 100:
                score += self.weights['proximity'] * 0.2

        # Plausibility score
        if text.parsed_value and hasattr(candidate, 'max_dim'):
            measured = candidate.max_dim
            diff_pct = abs(measured - text.parsed_value) / (text.parsed_value + 0.001)
            if diff_pct < 0.02:
                score += self.weights['plausibility']
            elif diff_pct < 0.05:
                score += self.weights['plausibility'] * 0.7
            elif diff_pct < 0.10:
                score += self.weights['plausibility'] * 0.3

        # Type match score (simplified)
        score += self.weights['type_match'] * 0.5  # Default partial match

        return score


class DimensionLinker:
    """
    High-level orchestrator for dimension association.

    This is the main entry point for Phase 4.0 functionality.

    Usage:
        linker = DimensionLinker()
        linked = linker.process_blueprint(extraction_result)

        for dim in linked.dimensions:
            print(f"{dim.text_region.text} -> {dim.target_feature.category}")
    """

    def __init__(
        self,
        mm_per_px: float = 0.0635,
        debug_mode: bool = False
    ):
        """
        Initialize dimension linker.

        Args:
            mm_per_px: Millimeters per pixel (default 400 DPI)
            debug_mode: Enable mock data for testing
        """
        self.mm_per_px = mm_per_px
        self.debug_mode = debug_mode

        # Initialize components
        self.arrow_detector = ArrowDetector(debug_mode=debug_mode)
        self.associator = LeaderLineAssociator(
            search_radius_calculator=self._adaptive_radius,
            mm_per_px=mm_per_px
        )
        self.witness_detector = WitnessLineDetector(mm_per_px=mm_per_px)
        self.ranker = MultiFactorRanker()

    def process_blueprint(
        self,
        extraction_result: Any,
        ocr_dimensions: Optional[List[Dict]] = None
    ) -> LinkedDimensions:
        """
        Process a blueprint extraction result to link dimensions.

        Args:
            extraction_result: ExtractionResult from Phase 3.6 vectorizer
            ocr_dimensions: Optional pre-extracted OCR dimensions

        Returns:
            LinkedDimensions with associated dimension-feature pairs
        """
        import time
        start_time = time.time()

        source_file = getattr(extraction_result, 'source_path', 'unknown')
        logger.info(f"Processing dimension linking for: {source_file}")

        # Step 1: Convert OCR dimensions to TextRegions
        text_regions = self._build_text_regions(extraction_result, ocr_dimensions)
        logger.info(f"Found {len(text_regions)} dimension text regions")

        # Step 2: Extract raw contours for arrow detection
        all_contours = self._extract_all_contours(extraction_result)
        logger.info(f"Analyzing {len(all_contours)} contours for arrows")

        # Step 3: Detect arrows
        arrows = self.arrow_detector.detect_arrows(all_contours)
        logger.info(f"Detected {len(arrows)} arrows")

        # Step 4: Get geometry by category
        geometry = self._get_geometry_dict(extraction_result)

        # Step 5: Calculate blueprint dimensions
        blueprint_width_mm = self._estimate_blueprint_width(extraction_result)

        # Step 6: Associate dimensions with geometry
        associations = self.associator.associate(
            arrows=arrows,
            text_regions=text_regions,
            geometry=geometry,
            blueprint_width_mm=blueprint_width_mm
        )

        # Step 7: Identify unmatched texts
        matched_texts = {a.text_region.text for a in associations}
        unmatched = [t for t in text_regions if t.text not in matched_texts]

        # Calculate statistics
        total_texts = len(text_regions)
        association_rate = len(associations) / total_texts if total_texts > 0 else 0.0
        processing_time = (time.time() - start_time) * 1000

        result = LinkedDimensions(
            source_file=source_file,
            dimensions=associations,
            unmatched_texts=unmatched,
            arrows_detected=len(arrows),
            association_rate=association_rate,
            processing_time_ms=processing_time
        )

        logger.info(result.summary())

        return result

    def _build_text_regions(
        self,
        extraction_result: Any,
        ocr_dimensions: Optional[List[Dict]]
    ) -> List[TextRegion]:
        """Build TextRegion objects from extraction result."""
        regions = []

        # Use provided OCR dimensions
        if ocr_dimensions:
            for dim in ocr_dimensions:
                region = TextRegion(
                    text=dim.get('raw_text', ''),
                    bbox=dim.get('bbox', (0, 0, 0, 0)),
                    confidence=dim.get('confidence', 0.5),
                    parsed_value=dim.get('value_mm'),
                    unit=dim.get('unit', 'unknown')
                )
                regions.append(region)

        # Also check extraction result for OCR data
        if hasattr(extraction_result, 'ocr_dimensions'):
            for dim in extraction_result.ocr_dimensions:
                if isinstance(dim, dict):
                    region = TextRegion(
                        text=dim.get('raw_text', ''),
                        bbox=tuple(dim.get('bbox', (0, 0, 0, 0))),
                        confidence=dim.get('confidence', 0.5),
                        parsed_value=dim.get('value_mm'),
                        unit=dim.get('unit', 'unknown')
                    )
                    regions.append(region)

        return regions

    def _extract_all_contours(self, extraction_result: Any) -> List:
        """Extract raw contours from extraction result."""
        contours = []

        if hasattr(extraction_result, 'contours_by_category'):
            categories = extraction_result.contours_by_category
            for category, items in categories.items():
                for item in items:
                    if hasattr(item, 'contour'):
                        contours.append(item.contour)

        return contours

    def _get_geometry_dict(self, extraction_result: Any) -> Dict[str, List]:
        """Get geometry organized by category."""
        if hasattr(extraction_result, 'contours_by_category'):
            return extraction_result.contours_by_category
        return {}

    def _estimate_blueprint_width(self, extraction_result: Any) -> float:
        """Estimate blueprint width in mm."""
        if hasattr(extraction_result, 'dimensions_mm'):
            w, h = extraction_result.dimensions_mm
            return max(w, h, 400)  # Minimum 400mm

        return 500.0  # Default

    def _adaptive_radius(
        self,
        blueprint_width_mm: float,
        text_size_mm: float
    ) -> float:
        """
        Calculate adaptive search radius for leader lines.

        Args:
            blueprint_width_mm: Total blueprint width in mm
            text_size_mm: Height of dimension text in mm

        Returns:
            Search radius in mm
        """
        # Base radius: 10% of blueprint width
        base_radius = blueprint_width_mm * 0.1

        # Scale by text size (larger text = longer leaders typically)
        text_scale = max(1.0, text_size_mm / 2.5)  # 2.5mm is typical

        # Cap at reasonable maximum (200mm as specified)
        return min(base_radius * text_scale, 200.0)


def link_blueprint_dimensions(
    extraction_result: Any,
    mm_per_px: float = 0.0635
) -> LinkedDimensions:
    """
    Convenience function to link dimensions in a blueprint.

    Args:
        extraction_result: ExtractionResult from Phase 3.6
        mm_per_px: Millimeters per pixel

    Returns:
        LinkedDimensions with associations
    """
    linker = DimensionLinker(mm_per_px=mm_per_px)
    return linker.process_blueprint(extraction_result)
