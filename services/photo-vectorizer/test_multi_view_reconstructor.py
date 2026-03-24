"""
Tests for Multi-View Shape Reconstructor.

Tests:
1. Top-only reconstruction returns valid contour
2. Front + top clips points outside front projection
3. Output DXF has single BODY_OUTLINE layer
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Import module under test
from multi_view_reconstructor import (
    MultiViewReconstructor,
    ReconstructionResult,
    ViewResult,
    parse_calibration,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_body_contour():
    """Create a mock FeatureContour with body outline."""
    # Simple rectangle contour: 400x200mm centered at origin
    contour = np.array([
        [-200, -100],
        [200, -100],
        [200, 100],
        [-200, 100],
    ], dtype=np.float64)

    mock = MagicMock()
    mock.points_mm = contour
    mock.confidence = 0.85
    return mock


@pytest.fixture
def mock_extraction_result(mock_body_contour):
    """Create a mock PhotoExtractionResult."""
    mock = MagicMock()
    mock.body_contour = mock_body_contour
    mock.scale_factor = 1.0
    return mock


@pytest.fixture
def reconstructor():
    """Create a MultiViewReconstructor instance."""
    return MultiViewReconstructor(simplify_tolerance_mm=0.5)


# =============================================================================
# Test 1: Top-only reconstruction returns valid contour
# =============================================================================

class TestTopOnlyReconstruction:
    """Test that top-only reconstruction returns valid contour."""

    def test_top_only_returns_valid_contour(
        self,
        reconstructor,
        mock_extraction_result,
        tmp_path,
    ):
        """Top view only should return a valid contour."""
        # Create a dummy image file
        top_image = tmp_path / "top.jpg"
        top_image.write_bytes(b"fake image data")

        with patch.object(
            reconstructor,
            "_get_vectorizer",
        ) as mock_get_vec:
            # Setup mock vectorizer
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = mock_extraction_result
            mock_get_vec.return_value = mock_vectorizer

            # Run reconstruction
            result = reconstructor.reconstruct(
                views={"top": str(top_image)},
                calibration_mm=300.0,
            )

            # Verify result
            assert result.success is True
            assert result.contour_mm is not None
            assert len(result.contour_mm) >= 3
            assert result.contour_points is not None
            assert len(result.contour_points) >= 3
            assert result.overall_confidence > 0

    def test_top_only_without_front_side_succeeds(
        self,
        reconstructor,
        mock_extraction_result,
        tmp_path,
    ):
        """Reconstruction should succeed with just top view."""
        top_image = tmp_path / "top.jpg"
        top_image.write_bytes(b"fake")

        with patch.object(
            reconstructor,
            "_get_vectorizer",
        ) as mock_get_vec:
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = mock_extraction_result
            mock_get_vec.return_value = mock_vectorizer

            result = reconstructor.reconstruct(views={"top": str(top_image)})

            # Only top view should be in results
            assert "top" in result.view_results
            assert result.view_results["top"].success is True
            assert "front" not in result.view_results
            assert "side" not in result.view_results

    def test_missing_top_view_fails(self, reconstructor):
        """Missing top view should fail reconstruction."""
        result = reconstructor.reconstruct(views={"front": "front.jpg"})

        assert result.success is False
        assert any("top" in w.lower() for w in result.warnings)


# =============================================================================
# Test 2: Front + top clips points outside front projection
# =============================================================================

class TestFrontViewClipping:
    """Test that front view clips points outside its projection."""

    def test_front_clips_top_contour_y_range(self, reconstructor):
        """Front view should clip top contour to its Y range."""
        # Top view contour: large rectangle
        top_contour = np.array([
            [-200, -150],  # Y=-150 outside front range
            [200, -150],
            [200, 150],   # Y=150 outside front range
            [-200, 150],
        ], dtype=np.float64)

        # Front view contour: smaller Y range (-100 to 100)
        front_contour = np.array([
            [-200, -100],
            [200, -100],
            [200, 100],
            [-200, 100],
        ], dtype=np.float64)

        # Apply clipping
        clipped = reconstructor._clip_by_front_view(top_contour, front_contour)

        # Y values should be clipped to front's range
        y_min, y_max = clipped[:, 1].min(), clipped[:, 1].max()
        assert y_min >= -100.0 - 0.01  # Allow small tolerance
        assert y_max <= 100.0 + 0.01

    def test_front_view_preserves_x_range(self, reconstructor):
        """Front view clipping should not affect X range."""
        top_contour = np.array([
            [-300, -50],
            [300, -50],
            [300, 50],
            [-300, 50],
        ], dtype=np.float64)

        front_contour = np.array([
            [-100, -100],  # Smaller X range
            [100, -100],
            [100, 100],
            [-100, 100],
        ], dtype=np.float64)

        clipped = reconstructor._clip_by_front_view(top_contour, front_contour)

        # X range should be unchanged
        x_min, x_max = clipped[:, 0].min(), clipped[:, 0].max()
        assert x_min == pytest.approx(-300.0, abs=0.01)
        assert x_max == pytest.approx(300.0, abs=0.01)

    def test_no_clipping_when_front_is_none(self, reconstructor):
        """No clipping should occur when front contour is None."""
        top_contour = np.array([
            [-200, -150],
            [200, -150],
            [200, 150],
            [-200, 150],
        ], dtype=np.float64)

        result = reconstructor._clip_by_front_view(top_contour, None)

        # Should return unchanged contour
        assert np.array_equal(result, top_contour)


# =============================================================================
# Test 3: Output DXF has single BODY_OUTLINE layer
# =============================================================================

class TestDxfExport:
    """Test that DXF output has single BODY_OUTLINE layer."""

    def test_dxf_has_body_outline_layer(self, reconstructor, tmp_path):
        """Exported DXF should have BODY_OUTLINE layer."""
        pytest.importorskip("ezdxf")
        import ezdxf

        # Simple contour
        contour = np.array([
            [0, 0],
            [100, 0],
            [100, 50],
            [0, 50],
        ], dtype=np.float64)

        output_path = tmp_path / "test_output.dxf"
        result = reconstructor._export_dxf(contour, output_path)

        assert result is not None
        assert output_path.exists()

        # Load and verify DXF
        doc = ezdxf.readfile(str(output_path))
        assert "BODY_OUTLINE" in doc.layers

    def test_dxf_has_single_layer_only(self, reconstructor, tmp_path):
        """DXF should only have BODY_OUTLINE and default layer."""
        pytest.importorskip("ezdxf")
        import ezdxf

        contour = np.array([
            [0, 0],
            [100, 0],
            [100, 50],
            [0, 50],
        ], dtype=np.float64)

        output_path = tmp_path / "test_single_layer.dxf"
        reconstructor._export_dxf(contour, output_path)

        doc = ezdxf.readfile(str(output_path))

        # Get non-default layer names
        layer_names = [
            layer.dxf.name for layer in doc.layers
            if layer.dxf.name not in ("0", "Defpoints")
        ]

        assert layer_names == ["BODY_OUTLINE"]

    def test_dxf_contains_polyline_on_body_outline_layer(
        self,
        reconstructor,
        tmp_path,
    ):
        """DXF should contain a polyline on BODY_OUTLINE layer."""
        pytest.importorskip("ezdxf")
        import ezdxf

        contour = np.array([
            [0, 0],
            [100, 0],
            [100, 50],
            [0, 50],
        ], dtype=np.float64)

        output_path = tmp_path / "test_polyline.dxf"
        reconstructor._export_dxf(contour, output_path)

        doc = ezdxf.readfile(str(output_path))
        msp = doc.modelspace()

        # Find entities on BODY_OUTLINE layer
        body_entities = [
            e for e in msp
            if e.dxf.layer == "BODY_OUTLINE"
        ]

        assert len(body_entities) >= 1
        assert body_entities[0].dxftype() == "LWPOLYLINE"


# =============================================================================
# Additional utility tests
# =============================================================================

class TestCalibrationParsing:
    """Test calibration string parsing."""

    def test_parse_ruler_mm_format(self):
        """Should parse 'ruler_mm=300' format."""
        assert parse_calibration("ruler_mm=300") == 300.0

    def test_parse_plain_number(self):
        """Should parse plain number."""
        assert parse_calibration("250.5") == 250.5

    def test_parse_custom_key(self):
        """Should parse any key=value format."""
        assert parse_calibration("custom_ref=450") == 450.0


class TestViewResult:
    """Test ViewResult dataclass."""

    def test_default_values(self):
        """ViewResult should have correct defaults."""
        vr = ViewResult(view_name="test")
        assert vr.view_name == "test"
        assert vr.contour_mm is None
        assert vr.confidence == 0.0
        assert vr.success is False


class TestReconstructionResult:
    """Test ReconstructionResult dataclass."""

    def test_to_dict(self):
        """to_dict should return serializable dict."""
        result = ReconstructionResult(
            contour_points=[(0, 0), (100, 0), (100, 50)],
            overall_confidence=0.85,
            success=True,
        )
        d = result.to_dict()

        assert d["contour_points"] == [(0, 0), (100, 0), (100, 50)]
        assert d["overall_confidence"] == 0.85
        assert d["success"] is True


# =============================================================================
# Integration test with mock vectorizer
# =============================================================================

class TestFullReconstruction:
    """Integration tests with mocked vectorizer."""

    def test_full_reconstruction_with_all_views(
        self,
        reconstructor,
        tmp_path,
    ):
        """Full reconstruction with top, front, side views."""
        # Create mock images
        top_img = tmp_path / "top.jpg"
        front_img = tmp_path / "front.jpg"
        side_img = tmp_path / "side.jpg"
        for img in [top_img, front_img, side_img]:
            img.write_bytes(b"fake")

        # Create different contours for each view
        def make_mock_extraction(width, height):
            contour = np.array([
                [-width/2, -height/2],
                [width/2, -height/2],
                [width/2, height/2],
                [-width/2, height/2],
            ], dtype=np.float64)
            mock_contour = MagicMock()
            mock_contour.points_mm = contour
            mock_contour.confidence = 0.8
            mock_result = MagicMock()
            mock_result.body_contour = mock_contour
            mock_result.scale_factor = 1.0
            return mock_result

        # Top: 400x200, Front: smaller Y, Side: smaller X
        extractions = {
            "top": make_mock_extraction(400, 200),
            "front": make_mock_extraction(400, 150),  # clips Y
            "side": make_mock_extraction(350, 200),   # clips X
        }

        def mock_extract(path, **kwargs):
            name = Path(path).stem
            return extractions.get(name, extractions["top"])

        with patch.object(
            reconstructor,
            "_get_vectorizer",
        ) as mock_get_vec:
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.side_effect = mock_extract
            mock_get_vec.return_value = mock_vectorizer

            output_dxf = tmp_path / "result.dxf"
            result = reconstructor.reconstruct(
                views={
                    "top": str(top_img),
                    "front": str(front_img),
                    "side": str(side_img),
                },
                output_path=str(output_dxf),
                calibration_mm=300.0,
            )

            assert result.success is True
            assert len(result.view_results) == 3
            assert all(vr.success for vr in result.view_results.values())
