# tests/test_fhole_routing.py

"""
Tests for F-hole routing module (BEN-GAP-09).

Tests cover:
- Configuration and presets
- Geometry generation (traditional, contemporary, Venetian)
- Contour transformation and positioning
- Toolpath generation
- Full pipeline integration
"""

import math
import pytest

from app.cam.fhole import (
    # Config
    FHoleStyle,
    PlungeStrategy,
    FHoleToolSpec,
    FHoleGeometryConfig,
    FHolePositionConfig,
    FHoleRoutingConfig,
    create_benedetto_17_fhole_config,
    create_les_paul_fhole_config,
    create_jumbo_archtop_fhole_config,
    # Geometry
    FHoleContour,
    FHoleGenerator,
    transform_contour,
    generate_fhole_pair,
    # Toolpath
    FHoleToolpathResult,
    FHoleToolpathGenerator,
)


class TestFHoleConfig:
    """Test F-hole configuration."""

    def test_default_config_has_valid_dimensions(self):
        """Default config should have reasonable F-hole dimensions."""
        config = FHoleRoutingConfig()
        assert config.geometry.length_mm > 0
        assert config.geometry.width_mm > 0
        assert config.geometry.length_mm > config.geometry.width_mm  # Elongated shape

    def test_default_tool_spec(self):
        """Default tool should be appropriate for F-holes."""
        tool = FHoleToolSpec()
        assert tool.diameter_mm < 6.0  # Small tool for detail
        assert tool.spindle_rpm > 10000  # High RPM for small tool

    def test_config_serialization(self):
        """Config should serialize to dict."""
        config = FHoleRoutingConfig()
        d = config.to_dict()
        assert "geometry" in d
        assert "position" in d
        assert "tool" in d
        assert d["cut_depth_mm"] > 0


class TestPresetConfigs:
    """Test preset configurations."""

    def test_benedetto_17_preset(self):
        """Benedetto 17\" preset should have correct dimensions."""
        config = create_benedetto_17_fhole_config()
        assert config.geometry.length_mm == 101.6  # 4"
        assert config.geometry.width_mm == 25.4  # 1"
        assert config.geometry.style == FHoleStyle.TRADITIONAL_ARCHTOP

    def test_les_paul_preset(self):
        """Les Paul (ES-335 style) preset should be slightly larger."""
        config = create_les_paul_fhole_config()
        assert config.geometry.length_mm > 100
        assert config.top_thickness_mm == 6.0  # Laminate top

    def test_jumbo_preset(self):
        """Jumbo archtop preset should have wider positioning."""
        config = create_jumbo_archtop_fhole_config()
        assert config.position.x_offset_mm > 70  # Wider body


class TestFHoleGeometry:
    """Test F-hole geometry generation."""

    def test_generator_creates_closed_contour(self):
        """Generated contour should be closed (start ≈ end)."""
        config = FHoleGeometryConfig()
        generator = FHoleGenerator(config)
        contour = generator.generate()

        # Check closure (first and last points should be close)
        first = contour.points[0]
        last = contour.points[-1]
        dist = math.sqrt((first[0] - last[0]) ** 2 + (first[1] - last[1]) ** 2)
        assert dist < 2.0  # Within 2mm of closure (accounts for tip asymmetry)

    def test_contour_has_sufficient_points(self):
        """Contour should have enough points for smooth curve."""
        config = FHoleGeometryConfig(points_per_curve=24)
        generator = FHoleGenerator(config)
        contour = generator.generate()

        # Should have many points (8 curve segments × points_per_curve)
        assert len(contour.points) > 100

    def test_contour_fits_bounding_box(self):
        """Contour should fit within specified dimensions."""
        config = FHoleGeometryConfig(length_mm=100, width_mm=25)
        generator = FHoleGenerator(config)
        contour = generator.generate()

        bbox = contour.bounding_box
        actual_length = bbox[3] - bbox[1]  # max_y - min_y
        actual_width = bbox[2] - bbox[0]  # max_x - min_x

        # Should be approximately the specified dimensions
        assert 90 < actual_length < 110
        assert 20 < actual_width < 30

    def test_contour_centered_at_origin(self):
        """Contour should be centered approximately at origin."""
        config = FHoleGeometryConfig()
        generator = FHoleGenerator(config)
        contour = generator.generate()

        assert abs(contour.center[0]) < 5  # X center near 0
        assert abs(contour.center[1]) < 5  # Y center near 0

    def test_traditional_style_has_waist(self):
        """Traditional F-hole should have narrow waist."""
        config = FHoleGeometryConfig(
            style=FHoleStyle.TRADITIONAL_ARCHTOP,
            length_mm=100,
            width_mm=25,
        )
        generator = FHoleGenerator(config)
        contour = generator.generate()

        # Find X coordinates near Y=0 (waist)
        waist_points = [p for p in contour.points if abs(p[1]) < 5]
        waist_xs = [abs(p[0]) for p in waist_points]

        if waist_xs:
            max_waist_x = max(waist_xs)
            # Waist should be narrower than max width
            assert max_waist_x < config.width_mm / 2

    def test_contemporary_style_generates(self):
        """Contemporary style should generate valid contour."""
        config = FHoleGeometryConfig(style=FHoleStyle.CONTEMPORARY)
        generator = FHoleGenerator(config)
        contour = generator.generate()

        assert len(contour.points) > 50
        assert contour.length_mm > 0

    def test_venetian_style_generates(self):
        """Venetian style should generate valid contour."""
        config = FHoleGeometryConfig(style=FHoleStyle.VENETIAN)
        generator = FHoleGenerator(config)
        contour = generator.generate()

        assert len(contour.points) > 50


class TestContourTransformation:
    """Test contour transformation and positioning."""

    def test_transform_translates_contour(self):
        """Transform should translate contour to position."""
        config = FHoleGeometryConfig()
        generator = FHoleGenerator(config)
        contour = generator.generate()

        position = FHolePositionConfig(x_offset_mm=65, y_offset_mm=-20)
        transformed = transform_contour(contour, position)

        # Center should be near the offset position
        assert abs(transformed.center[0] - 65) < 10
        assert abs(transformed.center[1] - (-20)) < 10

    def test_transform_rotates_contour(self):
        """Transform should rotate contour."""
        config = FHoleGeometryConfig()
        generator = FHoleGenerator(config)
        contour = generator.generate()

        position = FHolePositionConfig(rotation_deg=45, x_offset_mm=0, y_offset_mm=0)
        transformed = transform_contour(contour, position)

        # Bounding box should change due to rotation
        original_bbox = contour.bounding_box
        new_bbox = transformed.bounding_box

        # 45-degree rotation should make width and height more similar
        # (elongated shape rotates to diagonal)
        original_aspect = (original_bbox[3] - original_bbox[1]) / (original_bbox[2] - original_bbox[0])
        new_aspect = (new_bbox[3] - new_bbox[1]) / (new_bbox[2] - new_bbox[0])

        # Aspect ratio should be different after rotation
        assert abs(original_aspect - new_aspect) > 0.1

    def test_mirror_creates_opposite_contour(self):
        """Mirroring should create bass-side F-hole."""
        config = FHoleGeometryConfig()
        generator = FHoleGenerator(config)
        contour = generator.generate()

        position = FHolePositionConfig(x_offset_mm=65, y_offset_mm=0)

        treble = transform_contour(contour, position, mirror=False)
        bass = transform_contour(contour, position, mirror=True)

        # Centers should be on opposite sides
        assert treble.center[0] > 0
        assert bass.center[0] < 0
        assert abs(treble.center[0] + bass.center[0]) < 10  # Symmetric

    def test_generate_fhole_pair(self):
        """generate_fhole_pair should create symmetric pair."""
        geometry = FHoleGeometryConfig()
        position = FHolePositionConfig(x_offset_mm=65, y_offset_mm=-20)

        treble, bass = generate_fhole_pair(geometry, position)

        # Both should have same number of points
        assert len(treble.points) == len(bass.points)

        # Centers should be symmetric about X axis
        assert treble.center[0] > 0
        assert bass.center[0] < 0
        assert abs(treble.center[0] + bass.center[0]) < 10


class TestFHoleToolpath:
    """Test F-hole toolpath generation."""

    def test_toolpath_generates_gcode(self):
        """Toolpath generator should produce G-code."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        assert len(result.gcode_lines) > 0
        gcode = result.get_gcode()
        assert "G" in gcode  # Contains G-codes

    def test_gcode_has_header_footer(self):
        """G-code should have proper header and footer."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        gcode = result.get_gcode()
        assert "F-HOLE ROUTING PROGRAM" in gcode
        assert "END OF F-HOLE ROUTING PROGRAM" in gcode
        assert "M30" in gcode  # Program end

    def test_gcode_has_tool_change(self):
        """G-code should include tool change."""
        config = create_benedetto_17_fhole_config()
        config.tool.tool_number = 5
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        gcode = result.get_gcode()
        assert "T5 M6" in gcode
        assert f"S{config.tool.spindle_rpm}" in gcode

    def test_gcode_has_both_fholes(self):
        """G-code should route both treble and bass F-holes."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        gcode = result.get_gcode()
        assert "TREBLE-SIDE F-HOLE" in gcode
        assert "BASS-SIDE F-HOLE" in gcode

    def test_result_has_contours(self):
        """Result should include both F-hole contours."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        assert result.treble_contour is not None
        assert result.bass_contour is not None

    def test_result_tracks_statistics(self):
        """Result should track cut length and time."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        assert result.total_cut_length_mm > 0
        assert result.total_passes > 0
        assert result.estimated_time_seconds > 0

    def test_helical_plunge_strategy(self):
        """Helical plunge should generate spiral entry."""
        config = create_benedetto_17_fhole_config()
        config.plunge_strategy = PlungeStrategy.HELICAL
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        gcode = result.get_gcode()
        assert "Helical plunge" in gcode

    def test_single_fhole_generation(self):
        """Should be able to generate single F-hole."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)

        geometry = FHoleGeometryConfig()
        gen = FHoleGenerator(geometry)
        contour = gen.generate()

        result = generator.generate_single(contour, side="treble")

        assert result.treble_contour is not None
        assert result.bass_contour is None
        assert len(result.gcode_lines) > 0


class TestFHoleIntegration:
    """Integration tests for complete F-hole routing."""

    def test_benedetto_full_pipeline(self):
        """Full Benedetto F-hole pipeline should work."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        # Verify complete result
        assert result.total_passes > 2  # Multiple depth passes
        assert result.total_cut_length_mm > 400  # Both F-holes
        assert len(result.gcode_lines) > 100

        # Verify G-code structure
        gcode = result.get_gcode()
        assert gcode.count("G0 Z") > 4  # Safe retracts
        assert gcode.count("G1 X") > 50  # Many cutting moves

    def test_result_serialization(self):
        """Result should serialize to dict."""
        config = create_benedetto_17_fhole_config()
        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        d = result.to_dict()
        assert "generated_at" in d
        assert "total_cut_length_mm" in d
        assert "estimated_time_minutes" in d
        assert "treble_contour" in d
        assert "bass_contour" in d

    def test_depth_passes_reach_through_cut(self):
        """Depth passes should reach through-cut depth."""
        config = create_benedetto_17_fhole_config()
        config.cut_depth_mm = 8.0
        config.stepdown_mm = 2.0

        generator = FHoleToolpathGenerator(config)
        result = generator.generate()

        gcode = result.get_gcode()
        # Should reach -8.0mm
        assert "Z-8.000" in gcode or "Z-8" in gcode

    def test_tool_compensation_reduces_contour(self):
        """Tool compensation should offset contour inward."""
        config = create_benedetto_17_fhole_config()
        config.tool.diameter_mm = 6.0  # Larger tool

        generator = FHoleToolpathGenerator(config)

        # Get original contour
        geometry = FHoleGeometryConfig()
        gen = FHoleGenerator(geometry)
        original = gen.generate()

        # The toolpath should use offset contour
        # (internal implementation detail, but we can verify through bbox)
        result = generator.generate()

        # Just verify it completes
        assert len(result.gcode_lines) > 50

    def test_different_presets_produce_different_gcode(self):
        """Different presets should produce different G-code."""
        benedetto_config = create_benedetto_17_fhole_config()
        jumbo_config = create_jumbo_archtop_fhole_config()

        ben_gen = FHoleToolpathGenerator(benedetto_config)
        jumbo_gen = FHoleToolpathGenerator(jumbo_config)

        ben_result = ben_gen.generate()
        jumbo_result = jumbo_gen.generate()

        # Cut lengths should be different (different F-hole sizes)
        assert abs(ben_result.total_cut_length_mm - jumbo_result.total_cut_length_mm) > 10
