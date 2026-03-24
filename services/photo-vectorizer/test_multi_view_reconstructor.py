"""
Tests for Multi-View Shape Reconstructor.

Tests:
1. Top-only reconstruction returns valid contour
2. Front + top clips points outside front projection
3. Output DXF has single BODY_OUTLINE layer
4. Internal feature classification by bounding box
5. Pass 2 extracts features inside body contour
6. DXF export includes multiple layers
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
    FeatureLayer,
    InternalFeature,
    MultiViewReconstructor,
    ReconstructionResult,
    ViewResult,
    classify_feature_by_bbox,
    parse_calibration,
    FEATURE_SPECS,
    MIN_INTERNAL_AREA_PX,
    HARDWARE_HOLE_MAX_AREA_PX,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_body_contour():
    """Create a mock FeatureContour with body outline."""
    # Simple rectangle contour: 400x200mm centered at origin
    contour_mm = np.array([
        [-200, -100],
        [200, -100],
        [200, 100],
        [-200, 100],
    ], dtype=np.float64)

    contour_px = np.array([
        [100, 50],
        [500, 50],
        [500, 250],
        [100, 250],
    ], dtype=np.float64)

    mock = MagicMock()
    mock.points_mm = contour_mm
    mock.points_px = contour_px
    mock.confidence = 0.85
    return mock


@pytest.fixture
def mock_extraction_result(mock_body_contour):
    """Create a mock PhotoExtractionResult."""
    mock = MagicMock()
    mock.body_contour = mock_body_contour
    mock.scale_factor = 1.0
    mock.calibration = MagicMock()
    mock.calibration.mm_per_pixel = 1.0
    return mock


@pytest.fixture
def reconstructor():
    """Create a MultiViewReconstructor instance."""
    return MultiViewReconstructor(
        simplify_tolerance_mm=0.5,
        extract_internal_features=True,
    )


@pytest.fixture
def reconstructor_no_internal():
    """Create a MultiViewReconstructor without internal feature extraction."""
    return MultiViewReconstructor(
        simplify_tolerance_mm=0.5,
        extract_internal_features=False,
    )


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
        ) as mock_get_vec, patch.object(
            reconstructor,
            "_extract_internal_features",
            return_value=[],
        ):
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = mock_extraction_result
            mock_get_vec.return_value = mock_vectorizer

            result = reconstructor.reconstruct(
                views={"top": str(top_image)},
                calibration_mm=300.0,
            )

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
        ) as mock_get_vec, patch.object(
            reconstructor,
            "_extract_internal_features",
            return_value=[],
        ):
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = mock_extraction_result
            mock_get_vec.return_value = mock_vectorizer

            result = reconstructor.reconstruct(views={"top": str(top_image)})

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
        top_contour = np.array([
            [-200, -150],
            [200, -150],
            [200, 150],
            [-200, 150],
        ], dtype=np.float64)

        front_contour = np.array([
            [-200, -100],
            [200, -100],
            [200, 100],
            [-200, 100],
        ], dtype=np.float64)

        clipped = reconstructor._clip_by_front_view(top_contour, front_contour)

        y_min, y_max = clipped[:, 1].min(), clipped[:, 1].max()
        assert y_min >= -100.0 - 0.01
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
            [-100, -100],
            [100, -100],
            [100, 100],
            [-100, 100],
        ], dtype=np.float64)

        clipped = reconstructor._clip_by_front_view(top_contour, front_contour)

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
        assert np.array_equal(result, top_contour)


# =============================================================================
# Test 3: Output DXF has single BODY_OUTLINE layer (backward compat)
# =============================================================================

class TestDxfExport:
    """Test that DXF output has correct layers."""

    def test_dxf_has_body_outline_layer(self, reconstructor, tmp_path):
        """Exported DXF should have BODY_OUTLINE layer."""
        pytest.importorskip("ezdxf")
        import ezdxf

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

        doc = ezdxf.readfile(str(output_path))
        assert "BODY_OUTLINE" in doc.layers

    def test_dxf_has_single_layer_only(self, reconstructor, tmp_path):
        """DXF with body-only should have just BODY_OUTLINE."""
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

        body_entities = [
            e for e in msp
            if e.dxf.layer == "BODY_OUTLINE"
        ]

        assert len(body_entities) >= 1
        assert body_entities[0].dxftype() == "LWPOLYLINE"


# =============================================================================
# Test 4: Internal feature classification by bounding box
# =============================================================================

class TestFeatureClassification:
    """Test bounding box based feature classification."""

    def test_pickup_classification_92x40mm(self):
        """92×40mm feature should classify as PICKUP."""
        layer = classify_feature_by_bbox(
            width_mm=92.0,
            height_mm=40.0,
            area_px=1000,
        )
        assert layer == FeatureLayer.PICKUP

    def test_pickup_classification_with_tolerance(self):
        """92×40mm ±15% should still classify as PICKUP."""
        # +15%
        layer = classify_feature_by_bbox(
            width_mm=92.0 * 1.14,
            height_mm=40.0 * 1.14,
            area_px=1000,
        )
        assert layer == FeatureLayer.PICKUP

        # -15%
        layer = classify_feature_by_bbox(
            width_mm=92.0 * 0.86,
            height_mm=40.0 * 0.86,
            area_px=1000,
        )
        assert layer == FeatureLayer.PICKUP

    def test_pickup_rotated_40x92mm(self):
        """40×92mm (rotated) should classify as PICKUP."""
        layer = classify_feature_by_bbox(
            width_mm=40.0,
            height_mm=92.0,
            area_px=1000,
        )
        assert layer == FeatureLayer.PICKUP

    def test_neck_pocket_classification_76x56mm(self):
        """76×56mm feature should classify as NECK_POCKET."""
        layer = classify_feature_by_bbox(
            width_mm=76.0,
            height_mm=56.0,
            area_px=1000,
        )
        assert layer == FeatureLayer.NECK_POCKET

    def test_neck_pocket_rotated_56x76mm(self):
        """56×76mm (rotated) should classify as NECK_POCKET."""
        layer = classify_feature_by_bbox(
            width_mm=56.0,
            height_mm=76.0,
            area_px=1000,
        )
        assert layer == FeatureLayer.NECK_POCKET

    def test_hardware_hole_small_area(self):
        """Features <500px² should classify as HARDWARE_HOLE."""
        layer = classify_feature_by_bbox(
            width_mm=10.0,
            height_mm=10.0,
            area_px=400,
        )
        assert layer == FeatureLayer.HARDWARE_HOLE

    def test_cavity_classification_default(self):
        """Other features should classify as CAVITY."""
        layer = classify_feature_by_bbox(
            width_mm=120.0,
            height_mm=80.0,
            area_px=5000,
        )
        assert layer == FeatureLayer.CAVITY

    def test_feature_specs_values(self):
        """Verify feature spec constants."""
        pickup = FEATURE_SPECS[FeatureLayer.PICKUP]
        assert pickup["width"] == 92.0
        assert pickup["height"] == 40.0
        assert pickup["tolerance"] == 0.15

        neck = FEATURE_SPECS[FeatureLayer.NECK_POCKET]
        assert neck["width"] == 76.0
        assert neck["height"] == 56.0
        assert neck["tolerance"] == 0.15


# =============================================================================
# Test 5: Pass 2 extracts features inside body contour
# =============================================================================

class TestInternalFeatureExtraction:
    """Test Pass 2 internal feature extraction."""

    def test_internal_features_collected_from_top_view(
        self,
        reconstructor,
        mock_extraction_result,
        tmp_path,
    ):
        """Internal features should be collected from top view."""
        top_image = tmp_path / "top.jpg"
        top_image.write_bytes(b"fake")

        # Mock internal feature
        mock_feature = InternalFeature(
            contour_px=np.array([[10, 10], [50, 10], [50, 30], [10, 30]]),
            contour_mm=np.array([[10, 10], [50, 10], [50, 30], [10, 30]], dtype=np.float64),
            layer=FeatureLayer.PICKUP,
            area_px=800,
            bbox_mm=(40.0, 20.0),
        )

        with patch.object(
            reconstructor,
            "_get_vectorizer",
        ) as mock_get_vec, patch.object(
            reconstructor,
            "_extract_internal_features",
            return_value=[mock_feature],
        ):
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = mock_extraction_result
            mock_get_vec.return_value = mock_vectorizer

            result = reconstructor.reconstruct(views={"top": str(top_image)})

            assert result.success is True
            assert len(result.internal_features) == 1
            assert result.internal_features[0].layer == FeatureLayer.PICKUP

    def test_internal_features_not_extracted_for_side_view(
        self,
        reconstructor,
        mock_extraction_result,
        tmp_path,
    ):
        """Internal features should only be extracted from top view."""
        side_image = tmp_path / "side.jpg"
        side_image.write_bytes(b"fake")

        # The side view should not trigger _extract_internal_features
        # because it's not "top"

        with patch.object(
            reconstructor,
            "_get_vectorizer",
        ) as mock_get_vec, patch.object(
            reconstructor,
            "_extract_internal_features",
        ) as mock_extract_internal:
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = mock_extraction_result
            mock_get_vec.return_value = mock_vectorizer

            # Process side view only (will fail because top is missing)
            vr = reconstructor._process_view("side", side_image, 300.0)

            # Internal feature extraction should NOT be called for side view
            mock_extract_internal.assert_not_called()

    def test_no_internal_extraction_when_disabled(
        self,
        reconstructor_no_internal,
        mock_extraction_result,
        tmp_path,
    ):
        """Internal features should not be extracted when disabled."""
        top_image = tmp_path / "top.jpg"
        top_image.write_bytes(b"fake")

        with patch.object(
            reconstructor_no_internal,
            "_get_vectorizer",
        ) as mock_get_vec, patch.object(
            reconstructor_no_internal,
            "_extract_internal_features",
        ) as mock_extract:
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = mock_extraction_result
            mock_get_vec.return_value = mock_vectorizer

            result = reconstructor_no_internal.reconstruct(
                views={"top": str(top_image)}
            )

            # Should not call internal extraction
            mock_extract.assert_not_called()
            assert result.internal_features == []


# =============================================================================
# Test 6: DXF export includes multiple layers
# =============================================================================

class TestMultiLayerDxfExport:
    """Test DXF export with multiple feature layers."""

    def test_dxf_with_multiple_layers(self, reconstructor, tmp_path):
        """DXF should include all feature layers."""
        pytest.importorskip("ezdxf")
        import ezdxf

        body = np.array([
            [0, 0], [400, 0], [400, 200], [0, 200]
        ], dtype=np.float64)

        pickup = np.array([
            [50, 50], [142, 50], [142, 90], [50, 90]
        ], dtype=np.float64)

        cavity = np.array([
            [200, 100], [300, 100], [300, 180], [200, 180]
        ], dtype=np.float64)

        features_by_layer = {
            "BODY_OUTLINE": [body],
            "PICKUP": [pickup],
            "CAVITY": [cavity],
        }

        output_path = tmp_path / "multi_layer.dxf"
        reconstructor._export_dxf_with_layers(features_by_layer, output_path)

        doc = ezdxf.readfile(str(output_path))

        assert "BODY_OUTLINE" in doc.layers
        assert "PICKUP" in doc.layers
        assert "CAVITY" in doc.layers

    def test_dxf_layers_have_distinct_colors(self, reconstructor, tmp_path):
        """Different layers should have different colors."""
        pytest.importorskip("ezdxf")
        import ezdxf

        features_by_layer = {
            "BODY_OUTLINE": [np.array([[0, 0], [100, 0], [100, 100], [0, 100]])],
            "PICKUP": [np.array([[10, 10], [50, 10], [50, 30], [10, 30]])],
            "NECK_POCKET": [np.array([[60, 60], [90, 60], [90, 90], [60, 90]])],
        }

        output_path = tmp_path / "colored.dxf"
        reconstructor._export_dxf_with_layers(features_by_layer, output_path)

        doc = ezdxf.readfile(str(output_path))

        colors = {}
        for layer in doc.layers:
            if layer.dxf.name in features_by_layer:
                colors[layer.dxf.name] = layer.dxf.color

        # Each layer should have a color
        assert len(colors) == 3
        # BODY_OUTLINE is 7 (white), PICKUP is 1 (red), NECK_POCKET is 5 (blue)
        assert colors["BODY_OUTLINE"] == 7
        assert colors["PICKUP"] == 1
        assert colors["NECK_POCKET"] == 5

    def test_dxf_multiple_contours_per_layer(self, reconstructor, tmp_path):
        """Multiple contours can exist on same layer."""
        pytest.importorskip("ezdxf")
        import ezdxf

        pickup1 = np.array([[10, 10], [50, 10], [50, 30], [10, 30]])
        pickup2 = np.array([[60, 10], [100, 10], [100, 30], [60, 30]])

        features_by_layer = {
            "BODY_OUTLINE": [np.array([[0, 0], [200, 0], [200, 100], [0, 100]])],
            "PICKUP": [pickup1, pickup2],
        }

        output_path = tmp_path / "multi_pickup.dxf"
        reconstructor._export_dxf_with_layers(features_by_layer, output_path)

        doc = ezdxf.readfile(str(output_path))
        msp = doc.modelspace()

        pickup_entities = [e for e in msp if e.dxf.layer == "PICKUP"]
        assert len(pickup_entities) == 2


# =============================================================================
# Additional utility tests
# =============================================================================

class TestCalibrationParsing:
    """Test calibration string parsing."""

    def test_parse_ruler_mm_format(self):
        assert parse_calibration("ruler_mm=300") == 300.0

    def test_parse_plain_number(self):
        assert parse_calibration("250.5") == 250.5

    def test_parse_custom_key(self):
        assert parse_calibration("custom_ref=450") == 450.0


class TestViewResult:
    """Test ViewResult dataclass."""

    def test_default_values(self):
        vr = ViewResult(view_name="test")
        assert vr.view_name == "test"
        assert vr.contour_mm is None
        assert vr.internal_features == []
        assert vr.confidence == 0.0
        assert vr.success is False


class TestReconstructionResult:
    """Test ReconstructionResult dataclass."""

    def test_to_dict_includes_internal_features(self):
        result = ReconstructionResult(
            contour_points=[(0, 0), (100, 0), (100, 50)],
            internal_features=[
                InternalFeature(
                    contour_px=np.array([[0, 0]]),
                    layer=FeatureLayer.PICKUP,
                )
            ],
            features_by_layer={"BODY_OUTLINE": [], "PICKUP": []},
            overall_confidence=0.85,
            success=True,
        )
        d = result.to_dict()

        assert d["internal_feature_count"] == 1
        assert "BODY_OUTLINE" in d["layers"]
        assert "PICKUP" in d["layers"]
        assert d["success"] is True


class TestInternalFeatureDataclass:
    """Test InternalFeature dataclass."""

    def test_default_layer_is_cavity(self):
        feat = InternalFeature(
            contour_px=np.array([[0, 0], [10, 0], [10, 10], [0, 10]]),
        )
        assert feat.layer == FeatureLayer.CAVITY

    def test_feature_with_all_fields(self):
        feat = InternalFeature(
            contour_px=np.array([[0, 0], [92, 0], [92, 40], [0, 40]]),
            contour_mm=np.array([[0, 0], [92, 0], [92, 40], [0, 40]]),
            layer=FeatureLayer.PICKUP,
            area_px=3680,
            area_mm2=3680.0,
            bbox_mm=(92.0, 40.0),
            confidence=0.9,
        )
        assert feat.layer == FeatureLayer.PICKUP
        assert feat.bbox_mm == (92.0, 40.0)


# =============================================================================
# Integration tests
# =============================================================================

class TestFullReconstruction:
    """Integration tests with mocked vectorizer."""

    def test_full_reconstruction_with_internal_features(
        self,
        reconstructor,
        tmp_path,
    ):
        """Full reconstruction including internal features."""
        top_img = tmp_path / "top.jpg"
        top_img.write_bytes(b"fake")

        def make_mock_extraction():
            contour_mm = np.array([
                [-200, -100], [200, -100], [200, 100], [-200, 100]
            ], dtype=np.float64)
            contour_px = np.array([
                [100, 50], [500, 50], [500, 250], [100, 250]
            ], dtype=np.float64)

            mock_contour = MagicMock()
            mock_contour.points_mm = contour_mm
            mock_contour.points_px = contour_px
            mock_contour.confidence = 0.8

            mock_result = MagicMock()
            mock_result.body_contour = mock_contour
            mock_result.scale_factor = 1.0
            mock_result.calibration = MagicMock()
            mock_result.calibration.mm_per_pixel = 1.0
            return mock_result

        mock_features = [
            InternalFeature(
                contour_px=np.array([[150, 100], [242, 100], [242, 140], [150, 140]]),
                contour_mm=np.array([[-50, -25], [42, -25], [42, 15], [-50, 15]]),
                layer=FeatureLayer.PICKUP,
                area_px=3680,
            ),
            InternalFeature(
                contour_px=np.array([[300, 100], [376, 100], [376, 156], [300, 156]]),
                contour_mm=np.array([[100, -25], [176, -25], [176, 31], [100, 31]]),
                layer=FeatureLayer.NECK_POCKET,
                area_px=4256,
            ),
        ]

        with patch.object(
            reconstructor,
            "_get_vectorizer",
        ) as mock_get_vec, patch.object(
            reconstructor,
            "_extract_internal_features",
            return_value=mock_features,
        ):
            mock_vectorizer = MagicMock()
            mock_vectorizer.extract.return_value = make_mock_extraction()
            mock_get_vec.return_value = mock_vectorizer

            output_dxf = tmp_path / "result.dxf"
            result = reconstructor.reconstruct(
                views={"top": str(top_img)},
                output_path=str(output_dxf),
                calibration_mm=300.0,
            )

            assert result.success is True
            assert len(result.internal_features) == 2
            assert FeatureLayer.PICKUP.value in result.features_by_layer
            assert FeatureLayer.NECK_POCKET.value in result.features_by_layer

            # Check DXF was created
            if result.output_dxf:
                pytest.importorskip("ezdxf")
                import ezdxf
                doc = ezdxf.readfile(result.output_dxf)
                assert "BODY_OUTLINE" in doc.layers
                assert "PICKUP" in doc.layers
                assert "NECK_POCKET" in doc.layers
