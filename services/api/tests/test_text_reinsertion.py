"""Tests for text reinsertion module.

Sprint 3: Faithful rendering architecture.
Author: Production Shop
Date: 2026-04-26
"""

import math
import pytest


class TestRotationComputation:
    """Test rotation angle extraction from 4-point polygon."""

    def test_horizontal_text_zero_rotation(self):
        """Horizontal text should have ~0 rotation."""
        from app.services.text_reinsertion import compute_rotation_from_polygon

        # Horizontal rectangle: tl, tr, br, bl
        polygon = [(0, 0), (100, 0), (100, 20), (0, 20)]
        rotation = compute_rotation_from_polygon(polygon)
        assert abs(rotation) < 0.5

    def test_rotated_text_positive_angle(self):
        """Text rotated 45 degrees counter-clockwise."""
        from app.services.text_reinsertion import compute_rotation_from_polygon

        # 45 degree rotation
        cos45 = math.cos(math.radians(45))
        sin45 = math.sin(math.radians(45))
        w, h = 100, 20

        tl = (0, 0)
        tr = (w * cos45, -w * sin45)
        br = (w * cos45 + h * sin45, -w * sin45 + h * cos45)
        bl = (h * sin45, h * cos45)

        polygon = [tl, tr, br, bl]
        rotation = compute_rotation_from_polygon(polygon)
        assert abs(rotation - (-45)) < 1.0  # Within 1 degree

    def test_small_rotation_treated_as_zero(self):
        """Rotations < 0.5 degrees are noise and returned as 0."""
        from app.services.text_reinsertion import compute_rotation_from_polygon

        # 0.3 degree rotation
        cos = math.cos(math.radians(0.3))
        sin = math.sin(math.radians(0.3))

        polygon = [(0, 0), (100 * cos, -100 * sin), (100 * cos, 20 - 100 * sin), (0, 20)]
        rotation = compute_rotation_from_polygon(polygon)
        assert rotation == 0.0

    def test_empty_polygon_returns_zero(self):
        """Empty or short polygon returns 0 rotation."""
        from app.services.text_reinsertion import compute_rotation_from_polygon

        assert compute_rotation_from_polygon([]) == 0.0
        assert compute_rotation_from_polygon([(0, 0)]) == 0.0
        assert compute_rotation_from_polygon([(0, 0), (1, 1)]) == 0.0


class TestHeightEstimation:
    """Test text height estimation from polygon."""

    def test_horizontal_text_height(self):
        """Horizontal text height is simple vertical distance."""
        from app.services.text_reinsertion import estimate_height_from_polygon

        polygon = [(0, 0), (100, 0), (100, 20), (0, 20)]
        height = estimate_height_from_polygon(polygon)
        assert abs(height - 20.0) < 0.1

    def test_rotated_text_height(self):
        """Rotated text height uses edge length, not vertical distance."""
        from app.services.text_reinsertion import estimate_height_from_polygon

        # 45 degree rotated 20px tall text
        cos45 = math.cos(math.radians(45))
        sin45 = math.sin(math.radians(45))
        h = 20

        tl = (0, 0)
        tr = (100, 0)
        br = (100 + h * sin45, h * cos45)
        bl = (h * sin45, h * cos45)

        polygon = [tl, tr, br, bl]
        height = estimate_height_from_polygon(polygon)
        assert abs(height - 20.0) < 1.0

    def test_empty_polygon_returns_fallback(self):
        """Empty polygon returns 20.0 fallback."""
        from app.services.text_reinsertion import estimate_height_from_polygon

        assert estimate_height_from_polygon([]) == 20.0
        assert estimate_height_from_polygon([(0, 0)]) == 20.0


class TestInsertionPoint:
    """Test insertion point extraction."""

    def test_insertion_point_is_bottom_left(self):
        """Insertion point is bottom-left corner (index 3)."""
        from app.services.text_reinsertion import get_insertion_point

        polygon = [(0, 0), (100, 0), (100, 20), (5, 25)]
        insert = get_insertion_point(polygon)
        assert insert == (5.0, 25.0)

    def test_empty_polygon_returns_origin(self):
        """Empty polygon returns (0, 0)."""
        from app.services.text_reinsertion import get_insertion_point

        assert get_insertion_point([]) == (0.0, 0.0)


class TestCoordinateConversion:
    """Test pixel to DXF coordinate conversion."""

    def test_y_flip_conversion(self):
        """Y coordinate is flipped for DXF (origin at bottom)."""
        from app.services.text_reinsertion import convert_text_to_dxf_coords, ExtractedText

        texts = [ExtractedText(
            content="test",
            confidence=0.9,
            insert_px=(100, 200),  # 200 pixels from top
            height_px=20,
            rotation_deg=0,
            bbox_polygon=[(0, 0), (50, 0), (50, 20), (0, 20)],
        )]

        image_height = 1000
        mm_per_px = 0.5

        result = convert_text_to_dxf_coords(texts, image_height, mm_per_px)

        assert len(result) == 1
        # Y should be flipped: (1000 - 200) * 0.5 = 400
        assert result[0]["insert_mm"] == (50.0, 400.0)
        assert result[0]["height_mm"] == 10.0  # 20 * 0.5

    def test_scale_applied_to_all_coords(self):
        """mm_per_px scale applied to x, y, and height."""
        from app.services.text_reinsertion import convert_text_to_dxf_coords, ExtractedText

        texts = [ExtractedText(
            content="test",
            confidence=0.9,
            insert_px=(100, 100),
            height_px=40,
            rotation_deg=15,
            bbox_polygon=[],
        )]

        result = convert_text_to_dxf_coords(texts, 500, 0.25)

        assert result[0]["insert_mm"] == (25.0, 100.0)
        assert result[0]["height_mm"] == 10.0
        assert result[0]["rotation_deg"] == 15


class TestDxfWriterRotation:
    """Test that DxfWriter.add_text() accepts rotation."""

    def test_add_text_with_rotation(self):
        """add_text() accepts rotation parameter."""
        from app.cam.dxf_writer import DxfWriter, LayerDef

        writer = DxfWriter(layers=[LayerDef("TEXT", 2)])
        writer.add_text("TEXT", "rotated", (10, 20), height=5.0, rotation=45.0)

        # Check entity was added
        entities = list(writer.modelspace)
        assert len(entities) == 1
        assert entities[0].dxftype() == "TEXT"
        assert entities[0].dxf.rotation == 45.0

    def test_add_text_default_rotation_zero(self):
        """add_text() defaults to 0 rotation."""
        from app.cam.dxf_writer import DxfWriter, LayerDef

        writer = DxfWriter(layers=[LayerDef("TEXT", 2)])
        writer.add_text("TEXT", "no rotation", (0, 0))

        entities = list(writer.modelspace)
        assert entities[0].dxf.rotation == 0.0


class TestAppendTextIntegration:
    """Integration tests for append_text_to_existing_dxf."""

    def test_orchestrator_reinsert_text_parameter_exists(self):
        """Verify reinsert_text parameter is wired to orchestrator."""
        from app.services.blueprint_orchestrator import BlueprintOrchestrator
        import inspect

        sig = inspect.signature(BlueprintOrchestrator.process_file)
        params = list(sig.parameters.keys())

        assert 'reinsert_text' in params
        assert sig.parameters['reinsert_text'].default is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
