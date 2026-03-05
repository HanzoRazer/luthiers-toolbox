"""
Tests for Phase 4.0 Pipeline
============================

Tests for end-to-end dimension linking pipeline.

Author: Luthier's Toolbox
Version: 4.0.0
"""

import pytest
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from phase4.pipeline import (
    BlueprintPipeline,
    PipelineResult,
    process_blueprint
)


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
    output_dxf: str = "output.dxf"
    output_svg: str = None

    def __post_init__(self):
        if self.contours_by_category is None:
            self.contours_by_category = {
                'body': [MockContourInfo('body', (0, 0, 400, 300))],
                'cavity': [MockContourInfo('cavity', (100, 100, 50, 30))]
            }
        if self.ocr_dimensions is None:
            self.ocr_dimensions = []


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_result_creation(self):
        """Test basic result creation."""
        result = PipelineResult(source_file="test.pdf")

        assert result.source_file == "test.pdf"
        assert result.extraction_time_ms == 0.0
        assert result.dimensions_linked == 0

    def test_summary(self):
        """Test summary generation."""
        result = PipelineResult(
            source_file="test_blueprint.pdf",
            dimensions_mm=(500.0, 400.0),
            dimensions_linked=5,
            association_rate=0.75,
            total_time_ms=100.0
        )

        summary = result.summary()

        assert "test_blueprint.pdf" in summary
        assert "500.0 x 400.0" in summary
        assert "5" in summary
        assert "75%" in summary

    def test_to_dict(self):
        """Test dictionary export."""
        result = PipelineResult(
            source_file="test.pdf",
            extraction_time_ms=50.0,
            linking_time_ms=30.0,
            total_time_ms=80.0,
            dimensions_linked=3,
            association_rate=0.6
        )

        d = result.to_dict()

        assert d['source_file'] == "test.pdf"
        assert d['timing']['extraction_ms'] == 50.0
        assert d['timing']['linking_ms'] == 30.0
        assert d['linking']['dimensions_linked'] == 3
        assert d['linking']['association_rate'] == 0.6


class TestBlueprintPipeline:
    """Tests for BlueprintPipeline class."""

    def test_pipeline_init_default(self):
        """Test default initialization."""
        pipeline = BlueprintPipeline()

        assert pipeline.dpi == 300
        assert pipeline.enable_ocr is True
        assert pipeline.debug_mode is False

    def test_pipeline_init_custom(self):
        """Test custom initialization."""
        pipeline = BlueprintPipeline(dpi=400, enable_ocr=False, debug_mode=True)

        assert pipeline.dpi == 400
        assert pipeline.enable_ocr is False
        assert pipeline.debug_mode is True

    def test_mm_per_px_calculation(self):
        """Test mm_per_px is calculated correctly."""
        pipeline_300 = BlueprintPipeline(dpi=300)
        pipeline_400 = BlueprintPipeline(dpi=400)

        # 25.4mm per inch / DPI = mm per pixel
        assert abs(pipeline_300.mm_per_px - (25.4 / 300)) < 0.001
        assert abs(pipeline_400.mm_per_px - (25.4 / 400)) < 0.001

    def test_linker_lazy_loaded(self):
        """Test linker is lazy loaded."""
        pipeline = BlueprintPipeline()

        assert pipeline._linker is None
        linker = pipeline.linker
        assert linker is not None
        assert pipeline._linker is linker  # Same instance

    def test_process_with_extraction_result(self):
        """Test processing with pre-extracted result."""
        pipeline = BlueprintPipeline(debug_mode=True)
        extraction = MockExtractionResult()

        result = pipeline.process(
            "test.pdf",
            extraction_result=extraction
        )

        assert isinstance(result, PipelineResult)
        assert result.source_file == "test.pdf"
        assert result.dimensions_mm == (500.0, 400.0)
        assert result.total_time_ms > 0

    def test_process_with_ocr_dimensions(self):
        """Test processing with OCR dimensions."""
        pipeline = BlueprintPipeline(debug_mode=True)
        extraction = MockExtractionResult(
            ocr_dimensions=[
                {
                    'raw_text': '100mm',
                    'value_mm': 100.0,
                    'unit': 'mm',
                    'bbox': (10, 10, 50, 20),
                    'confidence': 0.9
                },
                {
                    'raw_text': '2.5"',
                    'value_mm': 63.5,
                    'unit': 'inch',
                    'bbox': (100, 100, 40, 15),
                    'confidence': 0.85
                }
            ]
        )

        result = pipeline.process(
            "test.pdf",
            extraction_result=extraction
        )

        assert result.ocr_dimensions_found == 2
        # In debug mode, should detect 3 mock arrows
        assert result.arrows_detected == 3

    def test_process_linking_only(self):
        """Test process_with_linking_only method."""
        pipeline = BlueprintPipeline(debug_mode=True)
        extraction = MockExtractionResult()

        result = pipeline.process_with_linking_only(extraction)

        assert isinstance(result, PipelineResult)
        assert result.source_file == "test_blueprint.pdf"

    def test_features_count(self):
        """Test features count in result."""
        pipeline = BlueprintPipeline(debug_mode=True)
        extraction = MockExtractionResult(
            contours_by_category={
                'body': [MockContourInfo('body', (0, 0, 100, 100))] * 2,
                'cavity': [MockContourInfo('cavity', (10, 10, 20, 20))] * 3,
                'pickup': [MockContourInfo('pickup', (50, 50, 30, 10))]
            }
        )

        result = pipeline.process(
            "test.pdf",
            extraction_result=extraction
        )

        assert result.features_count['body'] == 2
        assert result.features_count['cavity'] == 3
        assert result.features_count['pickup'] == 1


class TestConvenienceFunction:
    """Tests for process_blueprint convenience function."""

    def test_process_blueprint_without_pdf(self):
        """Test that missing PDF raises error."""
        # Can't test actual processing without a PDF,
        # but we can verify the function exists and has correct signature
        import inspect
        sig = inspect.signature(process_blueprint)

        params = list(sig.parameters.keys())
        assert 'pdf_path' in params
        assert 'dpi' in params
        assert 'instrument_type' in params
        assert 'debug_mode' in params


class TestPipelineIntegration:
    """Integration tests for pipeline."""

    def test_full_pipeline_mock_mode(self):
        """Test full pipeline in mock/debug mode."""
        pipeline = BlueprintPipeline(debug_mode=True)
        extraction = MockExtractionResult(
            ocr_dimensions=[
                {
                    'raw_text': '400mm',
                    'value_mm': 400.0,
                    'unit': 'mm',
                    'bbox': (200, 150, 60, 25),
                    'confidence': 0.95
                }
            ],
            dimensions_mm=(500.0, 400.0)
        )

        result = pipeline.process(
            "guitar_body.pdf",
            extraction_result=extraction
        )

        # Verify complete result
        assert result.source_file == "guitar_body.pdf"
        assert result.extraction_time_ms >= 0
        assert result.linking_time_ms >= 0
        assert result.total_time_ms >= result.linking_time_ms

        # Debug mode produces mock arrows
        assert result.arrows_detected == 3

        # Should have linked_dimensions object
        assert result.linked_dimensions is not None

    def test_result_serialization(self):
        """Test that result can be serialized to dict/JSON."""
        import json

        pipeline = BlueprintPipeline(debug_mode=True)
        extraction = MockExtractionResult()

        result = pipeline.process(
            "test.pdf",
            extraction_result=extraction
        )

        # Convert to dict
        d = result.to_dict()
        assert isinstance(d, dict)

        # Should be JSON serializable
        json_str = json.dumps(d)
        assert len(json_str) > 0

        # Parse back
        parsed = json.loads(json_str)
        assert parsed['source_file'] == "test.pdf"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
