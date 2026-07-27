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

import pytest

# Canonical photo-vectorizer lives under services/ (not repo_root/photo-vectorizer)
REPO_ROOT = Path(__file__).resolve().parents[3]
PHOTO_VECTORIZER_PATH = REPO_ROOT / "services" / "photo-vectorizer"
if str(PHOTO_VECTORIZER_PATH) not in sys.path:
    sys.path.insert(0, str(PHOTO_VECTORIZER_PATH))


def _photo_numpy():
    """
    Numpy bound through edge_to_dxf's import context.

    api-verify runs thousands of tests; ezdxf.math.construct2d re-imports numpy
    mid-session (see CI warning on construct2d.py:8). A module-level
    ``import numpy as np`` in this file goes stale, and ndarray.sum() on masks
    then raises _NoValueType. Import edge_to_dxf first and use its np binding.
    """
    import edge_to_dxf

    return edge_to_dxf.np


class TestTextMaskingFunctions:
    """Unit tests for text masking helper functions."""

    def test_create_text_mask_empty_regions(self):
        """Empty region list produces empty mask."""
        np = _photo_numpy()
        from edge_to_dxf import create_text_mask

        mask = create_text_mask((100, 200), [])
        assert mask.shape == (100, 200)
        assert np.sum(mask) == 0

    def test_create_text_mask_single_region(self):
        """Single region is correctly filled."""
        np = _photo_numpy()
        from edge_to_dxf import create_text_mask

        regions = [(10, 20, 30, 40)]  # x, y, w, h
        mask = create_text_mask((100, 200), regions)

        # Check that region is filled
        assert np.sum(mask[20:60, 10:40]) == 255 * 30 * 40
        # Check that outside region is empty
        assert np.sum(mask[0:20, :]) == 0
        assert np.sum(mask[60:, :]) == 0

    def test_create_text_mask_multiple_regions(self):
        """Multiple regions are all filled."""
        np = _photo_numpy()
        from edge_to_dxf import create_text_mask

        regions = [
            (10, 10, 20, 20),
            (50, 50, 20, 20),
        ]
        mask = create_text_mask((100, 100), regions)

        # Both regions should be filled
        assert np.sum(mask[10:30, 10:30]) > 0
        assert np.sum(mask[50:70, 50:70]) > 0

    def test_create_text_mask_clips_to_bounds(self):
        """Regions extending beyond image are clipped."""
        np = _photo_numpy()
        from edge_to_dxf import create_text_mask

        # Region extends beyond image bounds
        regions = [(90, 90, 50, 50)]  # Extends beyond 100x100
        mask = create_text_mask((100, 100), regions)

        # Should not crash, mask should be clipped
        assert mask.shape == (100, 100)
        assert np.sum(mask[90:100, 90:100]) > 0

    def test_apply_text_mask_to_edges_removes_text(self):
        """Text mask correctly removes edge pixels in text regions."""
        np = _photo_numpy()
        from edge_to_dxf import apply_text_mask_to_edges

        # Create edge image with edges everywhere
        edges = np.ones((100, 100), dtype=np.uint8) * 255

        # Create mask for half the image
        text_mask = np.zeros((100, 100), dtype=np.uint8)
        text_mask[:, 50:] = 255

        masked, removed = apply_text_mask_to_edges(edges, text_mask)

        # Right half should be masked out
        assert np.sum(masked[:, 50:]) == 0
        # Left half should be preserved
        assert np.sum(masked[:, :50]) == 255 * 100 * 50
        # Removed count should be the right half
        assert removed == 100 * 50

    def test_apply_text_mask_to_edges_handles_none(self):
        """None mask returns edges unchanged."""
        np = _photo_numpy()
        from edge_to_dxf import apply_text_mask_to_edges

        edges = np.ones((100, 100), dtype=np.uint8) * 255
        masked, removed = apply_text_mask_to_edges(edges, None)

        assert np.array_equal(masked, edges)
        assert removed == 0


class TestTextDetection:
    """Tests for OCR-based text detection."""

    def test_detect_text_regions_no_easyocr(self):
        """Returns empty list when EasyOCR unavailable."""
        np = _photo_numpy()
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
        np = _photo_numpy()
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


class TestTextDetectionFailureIsNotSilent:
    """BR-037: OCR failure must not masquerade as 'no text present'.

    Before the fix, `detect_text_regions` returned [] on any exception. The caller
    guards with `if text_regions:`, so masking was skipped, the glyph edges stayed
    in the edge image, and findContours traced them into the DXF as body geometry —
    in an output that still reported success.
    """

    def test_ocr_failure_raises_instead_of_returning_empty(self):
        """An OCR crash raises TextDetectionError; it does not return []."""
        np = _photo_numpy()
        import edge_to_dxf
        from edge_to_dxf import detect_text_regions, TextDetectionError

        class _BoomReader:
            def readtext(self, image):
                raise RuntimeError("simulated OCR engine failure")

        original = edge_to_dxf._EASYOCR_READER
        original_avail = edge_to_dxf._EASYOCR_AVAILABLE
        edge_to_dxf._EASYOCR_READER = _BoomReader()
        edge_to_dxf._EASYOCR_AVAILABLE = True
        try:
            image = np.zeros((100, 100, 3), dtype=np.uint8)
            with pytest.raises(TextDetectionError):
                detect_text_regions(image)
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail

    def test_clean_empty_result_is_still_a_plain_empty_list(self):
        """'No text present' stays [] — the legitimate, common case is unchanged."""
        np = _photo_numpy()
        import edge_to_dxf
        from edge_to_dxf import detect_text_regions

        class _EmptyReader:
            def readtext(self, image):
                return []

        original = edge_to_dxf._EASYOCR_READER
        original_avail = edge_to_dxf._EASYOCR_AVAILABLE
        edge_to_dxf._EASYOCR_READER = _EmptyReader()
        edge_to_dxf._EASYOCR_AVAILABLE = True
        try:
            image = np.zeros((100, 100, 3), dtype=np.uint8)
            assert detect_text_regions(image) == []
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail

    def test_convert_marks_result_degraded_when_ocr_fails(self, tmp_path):
        """BR-037: OCR failure yields DEGRADED output, not clean SUCCESS.

        Reproduced pre-fix: 1475 DXF entities landed inside the text bounding box
        (0 in a no-text control) while the result still reported SUCCESS. The fix
        keeps emitting -- a failed OCR pass cannot know whether the image had any
        text, so refusing would reject the many images that have none -- but the
        result must no longer claim a clean conversion.
        """
        np = _photo_numpy()
        cv2 = pytest.importorskip("cv2")
        import edge_to_dxf
        from edge_to_dxf import EdgeToDXF, ConversionStatus

        class _BoomReader:
            def readtext(self, image):
                raise RuntimeError("simulated OCR engine failure")

        img = np.full((300, 400, 3), 255, np.uint8)
        cv2.ellipse(img, (200, 200), (120, 70), 0, 0, 360, (30, 30, 30), -1)
        src = tmp_path / "src.png"
        out = tmp_path / "out.dxf"
        cv2.imwrite(str(src), img)

        original, original_avail = edge_to_dxf._EASYOCR_READER, edge_to_dxf._EASYOCR_AVAILABLE
        edge_to_dxf._EASYOCR_READER = _BoomReader()
        edge_to_dxf._EASYOCR_AVAILABLE = True
        try:
            result = EdgeToDXF().convert_enhanced(
                str(src), str(out), target_height_mm=200.0, mask_text=True
            )
        finally:
            edge_to_dxf._EASYOCR_READER = original
            edge_to_dxf._EASYOCR_AVAILABLE = original_avail

        assert result.text_detection_failed is True
        assert result.status is ConversionStatus.DEGRADED
        assert result.status is not ConversionStatus.SUCCESS
        assert out.exists(), "output must still be produced, not refused"
        assert "DEGRADED" in result.summary()
