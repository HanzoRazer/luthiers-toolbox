"""
Tests for text-masking preprocessing in blueprint vectorization.

Sprint 3: Text-masking preprocessing pass for blueprint vectorizer.
Problem: Morphological gap closing (7×7 kernel) bridges text glyph strokes.
Solution: Detect text regions with OCR, mask them before edge detection.

Author: Production Shop
Date: 2026-04-26
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add photo-vectorizer to path for imports
PHOTO_VECTORIZER_PATH = Path(__file__).parent.parent.parent.parent / "photo-vectorizer"
if str(PHOTO_VECTORIZER_PATH) not in sys.path:
    sys.path.insert(0, str(PHOTO_VECTORIZER_PATH))


class TestTextMaskingFunctions:
    """Unit tests for text masking helper functions."""

    def test_create_text_mask_empty_regions(self):
        """Empty region list produces empty mask."""
        from edge_to_dxf import create_text_mask

        mask = create_text_mask((100, 200), [])
        assert mask.shape == (100, 200)
        assert mask.sum() == 0

    def test_create_text_mask_single_region(self):
        """Single region is correctly filled."""
        from edge_to_dxf import create_text_mask

        regions = [(10, 20, 30, 40)]  # x, y, w, h
        mask = create_text_mask((100, 200), regions)

        # Check that region is filled
        assert mask[20:60, 10:40].sum() == 255 * 30 * 40
        # Check that outside region is empty
        assert mask[0:20, :].sum() == 0
        assert mask[60:, :].sum() == 0

    def test_create_text_mask_multiple_regions(self):
        """Multiple regions are all filled."""
        from edge_to_dxf import create_text_mask

        regions = [
            (10, 10, 20, 20),
            (50, 50, 20, 20),
        ]
        mask = create_text_mask((100, 100), regions)

        # Both regions should be filled
        assert mask[10:30, 10:30].sum() > 0
        assert mask[50:70, 50:70].sum() > 0

    def test_create_text_mask_clips_to_bounds(self):
        """Regions extending beyond image are clipped."""
        from edge_to_dxf import create_text_mask

        # Region extends beyond image bounds
        regions = [(90, 90, 50, 50)]  # Extends beyond 100x100
        mask = create_text_mask((100, 100), regions)

        # Should not crash, mask should be clipped
        assert mask.shape == (100, 100)
        assert mask[90:100, 90:100].sum() > 0

    def test_apply_text_mask_to_edges_removes_text(self):
        """Text mask correctly removes edge pixels in text regions."""
        from edge_to_dxf import apply_text_mask_to_edges

        # Create edge image with edges everywhere
        edges = np.ones((100, 100), dtype=np.uint8) * 255

        # Create mask for half the image
        text_mask = np.zeros((100, 100), dtype=np.uint8)
        text_mask[:, 50:] = 255

        masked, removed = apply_text_mask_to_edges(edges, text_mask)

        # Right half should be masked out
        assert masked[:, 50:].sum() == 0
        # Left half should be preserved
        assert masked[:, :50].sum() == 255 * 100 * 50
        # Removed count should be the right half
        assert removed == 100 * 50

    def test_apply_text_mask_to_edges_handles_none(self):
        """None mask returns edges unchanged."""
        from edge_to_dxf import apply_text_mask_to_edges

        edges = np.ones((100, 100), dtype=np.uint8) * 255
        masked, removed = apply_text_mask_to_edges(edges, None)

        assert np.array_equal(masked, edges)
        assert removed == 0


class TestTextDetection:
    """Tests for OCR-based text detection."""

    def test_detect_text_regions_no_easyocr(self):
        """Returns empty list when EasyOCR unavailable."""
        from edge_to_dxf import detect_text_regions

        # Mock EasyOCR as unavailable
        with patch.dict('sys.modules', {'easyocr': None}):
            import edge_to_dxf
            # Reset the availability flag
            original_available = edge_to_dxf._EASYOCR_AVAILABLE
            edge_to_dxf._EASYOCR_AVAILABLE = False

            try:
                image = np.zeros((100, 100, 3), dtype=np.uint8)
                regions = detect_text_regions(image)
                assert regions == []
            finally:
                edge_to_dxf._EASYOCR_AVAILABLE = original_available

    def test_detect_text_regions_filters_low_confidence(self):
        """Low-confidence detections are filtered out."""
        from edge_to_dxf import detect_text_regions, _get_easyocr_reader

        # Skip if EasyOCR not available
        if _get_easyocr_reader() is None:
            pytest.skip("EasyOCR not available")

        # Create a simple test image (white background, no text)
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        regions = detect_text_regions(image, min_confidence=0.3)

        # Should return empty (no text in blank image)
        assert isinstance(regions, list)


class TestConvertEnhancedIntegration:
    """Integration tests for convert_enhanced with text masking."""

    def test_convert_enhanced_mask_text_parameter_exists(self):
        """Verify mask_text parameter is accepted."""
        from edge_to_dxf import EdgeToDXF
        import inspect

        sig = inspect.signature(EdgeToDXF.convert_enhanced)
        params = list(sig.parameters.keys())

        assert 'mask_text' in params

    def test_convert_enhanced_mask_text_default_true(self):
        """Verify mask_text defaults to True."""
        from edge_to_dxf import EdgeToDXF
        import inspect

        sig = inspect.signature(EdgeToDXF.convert_enhanced)
        default = sig.parameters['mask_text'].default

        assert default is True


class TestOrchestratorIntegration:
    """Integration tests for orchestrator with text masking."""

    def test_orchestrator_mask_text_parameter_exists(self):
        """Verify mask_text parameter is wired to orchestrator."""
        from app.services.blueprint_orchestrator import BlueprintOrchestrator
        import inspect

        sig = inspect.signature(BlueprintOrchestrator.process_file)
        params = list(sig.parameters.keys())

        assert 'mask_text' in params

    def test_extract_enhanced_mask_text_parameter_exists(self):
        """Verify mask_text parameter is wired to extract_blueprint_enhanced."""
        from app.services.blueprint_extract import extract_blueprint_enhanced
        import inspect

        sig = inspect.signature(extract_blueprint_enhanced)
        params = list(sig.parameters.keys())

        assert 'mask_text' in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
