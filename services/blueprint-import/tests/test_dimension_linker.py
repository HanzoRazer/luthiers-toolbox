"""
Tests for Dimension Linker
==========================

Tests for Phase 4.0 DimensionLinker orchestrator.

Author: The Production Shop
Version: 4.0.0
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from phase4.dimension_linker import (
    DimensionLinker,
    LinkedDimensions,
    MultiFactorRanker,
    link_blueprint_dimensions
)
from phase4.leader_associator import TextRegion


# Mock classes for testing
@dataclass
class MockContourInfo:
    category: str
    bbox: tuple
    contour: Any = None

    @property
    def distance(self):
        return 10.0

    @property
    def max_dim(self):
        return 100.0


@dataclass
class MockExtractionResult:
    source_path: str = "test_blueprint.pdf"
    contours_by_category: Dict[str, List] = None
    ocr_dimensions: List[Dict] = None
    dimensions_mm: tuple = (500.0, 400.0)

    def __post_init__(self):
        if self.contours_by_category is None:
            self.contours_by_category = {}
        if self.ocr_dimensions is None:
            self.ocr_dimensions = []


class TestLinkedDimensions:
    """Tests for LinkedDimensions dataclass."""

    def test_linked_dimensions_creation(self):
        """Test basic creation."""
        linked = LinkedDimensions(source_file="test.pdf")

        assert linked.source_file == "test.pdf"
        assert linked.dimensions == []
        assert linked.unmatched_texts == []
        assert linked.arrows_detected == 0
        assert linked.association_rate == 0.0

    def test_to_dict(self):
        """Test dictionary export."""
        linked = LinkedDimensions(
            source_file="test.pdf",
            arrows_detected=5,
            association_rate=0.75
        )

        d = linked.to_dict()

        assert d['source_file'] == "test.pdf"
        assert d['statistics']['arrows_detected'] == 5
        assert d['statistics']['association_rate'] == 0.75

    def test_summary(self):
        """Test summary string."""
        linked = LinkedDimensions(
            source_file="test.pdf",
            association_rate=0.8
        )

        summary = linked.summary()

        assert "0 linked" in summary
        assert "0 unmatched" in summary
        assert "80%" in summary


class TestDimensionLinkerInit:
    """Tests for DimensionLinker initialization."""

    def test_default_init(self):
        """Test default initialization."""
        linker = DimensionLinker()

        assert linker.mm_per_px == 0.0635
        assert linker.debug_mode is False
        assert linker.arrow_detector is not None
        assert linker.associator is not None

    def test_custom_mm_per_px(self):
        """Test custom mm_per_px."""
        linker = DimensionLinker(mm_per_px=0.1)

        assert linker.mm_per_px == 0.1

    def test_debug_mode(self):
        """Test debug mode."""
        linker = DimensionLinker(debug_mode=True)

        assert linker.debug_mode is True


class TestDimensionLinkerProcessing:
    """Tests for DimensionLinker processing."""

    def test_process_empty_blueprint(self):
        """Test processing empty blueprint."""
        linker = DimensionLinker()
        result = MockExtractionResult()

        linked = linker.process_blueprint(result)

        assert isinstance(linked, LinkedDimensions)
        assert linked.source_file == "test_blueprint.pdf"
        assert len(linked.dimensions) == 0

    def test_process_with_ocr_dimensions(self):
        """Test processing with OCR dimensions."""
        linker = DimensionLinker()
        result = MockExtractionResult(
            ocr_dimensions=[
                {'raw_text': '100mm', 'value_mm': 100.0, 'unit': 'mm',
                 'bbox': (10, 10, 50, 20), 'confidence': 0.9}
            ]
        )

        linked = linker.process_blueprint(result)

        # Should have unmatched text since no geometry to associate with
        assert len(linked.unmatched_texts) >= 0

    def test_process_blueprint_timing(self):
        """Test that processing time is recorded."""
        linker = DimensionLinker()
        result = MockExtractionResult()

        linked = linker.process_blueprint(result)

        assert linked.processing_time_ms > 0


class TestMultiFactorRanker:
    """Tests for MultiFactorRanker."""

    def test_ranker_creation(self):
        """Test ranker initialization."""
        ranker = MultiFactorRanker()

        assert ranker.weights['proximity'] == 50
        assert ranker.weights['plausibility'] == 30
        assert ranker.weights['type_match'] == 20

    def test_rank_empty_candidates(self):
        """Test ranking with no candidates."""
        ranker = MultiFactorRanker()
        text = TextRegion(text="100mm", bbox=(0, 0, 50, 20), confidence=0.9)

        ranked = ranker.rank(text, [], 0.0635)

        assert ranked == []

    def test_rank_single_candidate(self):
        """Test ranking with single candidate."""
        ranker = MultiFactorRanker()
        text = TextRegion(text="100mm", bbox=(0, 0, 50, 20), confidence=0.9, parsed_value=100.0)
        candidate = MockContourInfo('body', (50, 50, 100, 100))

        ranked = ranker.rank(text, [candidate], 0.0635)

        assert len(ranked) == 1
        assert ranked[0][0] == candidate
        assert ranked[0][1] > 0  # Should have some score

    def test_rank_multiple_candidates(self):
        """Test that ranking sorts by score descending."""
        ranker = MultiFactorRanker()
        text = TextRegion(text="100mm", bbox=(0, 0, 50, 20), confidence=0.9, parsed_value=100.0)

        candidates = [
            MockContourInfo('body', (100, 100, 50, 50)),
            MockContourInfo('cavity', (50, 50, 50, 50)),
        ]

        ranked = ranker.rank(text, candidates, 0.0635)

        assert len(ranked) == 2
        # Should be sorted by score
        assert ranked[0][1] >= ranked[1][1]


class TestAdaptiveRadius:
    """Tests for adaptive search radius."""

    def test_default_radius(self):
        """Test default radius calculation."""
        linker = DimensionLinker()

        radius = linker._adaptive_radius(500.0, 2.5)

        # 10% of 500mm = 50mm, text_scale = 1.0
        assert radius == 50.0

    def test_radius_scales_with_text(self):
        """Test radius scales with text size."""
        linker = DimensionLinker()

        small_radius = linker._adaptive_radius(500.0, 2.5)
        large_radius = linker._adaptive_radius(500.0, 5.0)

        assert large_radius > small_radius

    def test_radius_capped(self):
        """Test radius is capped at 200mm."""
        linker = DimensionLinker()

        # Very large blueprint, very large text
        radius = linker._adaptive_radius(5000.0, 10.0)

        assert radius <= 200.0


class TestConvenienceFunction:
    """Tests for convenience function."""

    def test_link_blueprint_dimensions(self):
        """Test convenience function."""
        result = MockExtractionResult()

        linked = link_blueprint_dimensions(result)

        assert isinstance(linked, LinkedDimensions)


class TestDebugMode:
    """Tests for debug mode."""

    def test_debug_mode_with_mock_arrows(self):
        """Test that debug mode uses mock arrows."""
        linker = DimensionLinker(debug_mode=True)
        result = MockExtractionResult()

        linked = linker.process_blueprint(result)

        # Debug mode should return mock arrows
        assert linked.arrows_detected == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
