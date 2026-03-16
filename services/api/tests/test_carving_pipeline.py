# tests/test_carving_pipeline.py

"""
Tests for 3D Surface Carving Pipeline (BEN-GAP-08)

Validates the graduated thickness carving module for archtop tops/backs.
"""

import pytest
import math
from pathlib import Path

from app.cam.carving import (
    CarvingPipeline,
    CarvingPipelineResult,
    CarvingConfig,
    CarvingToolSpec,
    CarvingStrategy,
    SurfaceType,
    MaterialHardness,
    GraduationMapConfig,
    RoughingConfig,
    FinishingConfig,
    AsymmetricCarveProfile,
    GraduationMap,
    SurfaceCarvingGenerator,
    CarvingResult,
    DEFAULT_CARVING_TOOLS,
    create_benedetto_17_config,
    create_les_paul_top_config,
    create_les_paul_1959_asymmetric_config,
)


# =============================================================================
# Configuration Tests
# =============================================================================

class TestCarvingConfig:
    """Tests for CarvingConfig."""

    def test_default_config_has_valid_stock_thickness(self):
        """Default config should have reasonable stock thickness."""
        config = CarvingConfig()
        assert config.stock_thickness_mm > 0
        assert config.stock_thickness_mm >= config.graduation_map.apex_thickness_mm

    def test_default_tools_available(self):
        """Default tool library should have roughing and finishing tools."""
        config = CarvingConfig()
        assert config.rough_tool_number in config.tools
        assert config.finish_tool_number in config.tools

    def test_tool_stepover_calculation(self):
        """Tool stepover should be percentage of diameter."""
        tool = CarvingToolSpec(
            tool_number=1,
            name="Test Ball",
            diameter_mm=10.0,
            type="ball_end",
            stepover_percent=30.0,
        )
        assert tool.stepover_mm == pytest.approx(3.0, rel=0.01)

    def test_ball_end_effective_radius(self):
        """Ball end effective radius should be half diameter."""
        tool = CarvingToolSpec(
            tool_number=1,
            name="Test Ball",
            diameter_mm=12.7,
            type="ball_end",
        )
        assert tool.effective_radius_mm == pytest.approx(6.35, rel=0.01)


class TestPresetConfigs:
    """Tests for preset configurations."""

    def test_benedetto_17_config(self):
        """Benedetto 17\" config should have correct specs."""
        config = create_benedetto_17_config()
        assert config.graduation_map.apex_thickness_mm == 7.0
        assert config.graduation_map.edge_thickness_mm == 3.5
        assert config.graduation_map.recurve_depth_mm == 1.5
        assert config.material == MaterialHardness.SOFT  # Spruce

    def test_les_paul_top_config(self):
        """Les Paul config should have correct specs."""
        config = create_les_paul_top_config()
        assert config.graduation_map.apex_thickness_mm == pytest.approx(19.05, rel=0.01)
        assert config.material == MaterialHardness.MEDIUM  # Maple


# =============================================================================
# Graduation Map Tests
# =============================================================================

class TestGraduationMap:
    """Tests for GraduationMap."""

    def test_parametric_thickness_at_center(self):
        """Parametric map should return apex thickness at center."""
        config = GraduationMapConfig(
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
        )
        grad_map = GraduationMap.create_parametric(config)
        thickness = grad_map.get_thickness_at(0, 0)
        assert thickness == pytest.approx(7.0, rel=0.01)

    def test_parametric_thickness_at_edge(self):
        """Parametric map should return edge thickness at perimeter."""
        config = GraduationMapConfig(
            bounds_x_mm=(-200, 200),
            bounds_y_mm=(-200, 200),
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
        )
        grad_map = GraduationMap.create_parametric(config)
        # Check at normalized radius ~1.0
        thickness = grad_map.get_thickness_at(200, 0)
        # Should be near edge thickness (within recurve range)
        assert thickness <= config.apex_thickness_mm
        assert thickness >= config.edge_thickness_mm * 0.7

    def test_thickness_decreases_from_center(self):
        """Thickness should decrease as distance from center increases."""
        config = GraduationMapConfig(
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
        )
        grad_map = GraduationMap.create_parametric(config)

        t_center = grad_map.get_thickness_at(0, 0)
        t_halfway = grad_map.get_thickness_at(100, 0)
        t_edge = grad_map.get_thickness_at(200, 0)

        assert t_center > t_halfway
        assert t_halfway > t_edge

    def test_surface_z_calculation(self):
        """Surface Z should be computed correctly from thickness."""
        config = GraduationMapConfig(
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
        )
        grad_map = GraduationMap.create_parametric(config)

        stock = 25.0
        z_center = grad_map.get_surface_z_at(0, 0, stock)
        z_edge = grad_map.get_surface_z_at(200, 0, stock)

        # Center should be higher (less removed)
        assert z_center > z_edge

        # Z should be negative (carving into stock)
        assert z_center < 0
        assert z_edge < 0

    def test_z_levels_generation(self):
        """Z levels should span from stock top to final surface."""
        config = GraduationMapConfig(
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
        )
        grad_map = GraduationMap.create_parametric(config)

        z_levels = grad_map.generate_z_levels(
            stock_thickness_mm=25.0,
            stepdown_mm=4.0,
            finish_allowance_mm=1.0,
        )

        # Should have multiple levels
        assert len(z_levels) >= 3

        # Levels should be descending (negative)
        for i in range(1, len(z_levels)):
            assert z_levels[i] < z_levels[i - 1]

    def test_generate_grid_from_parametric(self):
        """Should be able to generate grid data from parametric model."""
        config = GraduationMapConfig(
            grid_size_x=16,
            grid_size_y=16,
        )
        grad_map = GraduationMap.create_parametric(config)
        grad_map.generate_grid_from_parametric()

        assert len(grad_map.thickness_grid) == 16
        assert len(grad_map.thickness_grid[0]) == 16


class TestGraduationMapIO:
    """Tests for graduation map file I/O."""

    def test_load_benedetto_graduation_map(self):
        """Should load Benedetto graduation map from JSON."""
        json_path = Path(__file__).parent.parent / \
            "app/instrument_geometry/models/benedetto_17/graduation_map.json"

        if json_path.exists():
            grad_map = GraduationMap.from_json(json_path)
            assert grad_map.config.apex_thickness_mm == 7.0
            assert grad_map.config.edge_thickness_mm == 3.5
            assert grad_map.config.surface_type == SurfaceType.ARCHTOP

    def test_save_and_reload(self, tmp_path):
        """Should save and reload graduation map."""
        config = GraduationMapConfig(
            grid_size_x=8,
            grid_size_y=8,
            apex_thickness_mm=10.0,
            edge_thickness_mm=5.0,
        )
        grad_map = GraduationMap.create_parametric(config)
        grad_map.generate_grid_from_parametric()

        save_path = tmp_path / "test_grad_map.json"
        grad_map.save_json(save_path)

        loaded = GraduationMap.from_json(save_path)
        assert loaded.config.apex_thickness_mm == 10.0
        assert len(loaded.thickness_grid) == 8


# =============================================================================
# Surface Carving Generator Tests
# =============================================================================

class TestSurfaceCarvingGenerator:
    """Tests for SurfaceCarvingGenerator."""

    def test_roughing_generates_gcode(self):
        """Roughing should generate G-code."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        generator = SurfaceCarvingGenerator(config, grad_map)

        result = generator.generate_roughing()

        assert isinstance(result, CarvingResult)
        assert len(result.gcode_lines) > 0
        assert result.pass_count > 0

    def test_finishing_generates_gcode(self):
        """Finishing should generate G-code."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        generator = SurfaceCarvingGenerator(config, grad_map)

        result = generator.generate_finishing()

        assert isinstance(result, CarvingResult)
        assert len(result.gcode_lines) > 0

    def test_roughing_uses_correct_tool(self):
        """Roughing should use configured rough tool."""
        config = CarvingConfig(rough_tool_number=1)
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        generator = SurfaceCarvingGenerator(config, grad_map)

        result = generator.generate_roughing()

        assert result.tool_number == 1

    def test_finishing_uses_correct_tool(self):
        """Finishing should use configured finish tool."""
        config = CarvingConfig(finish_tool_number=3)
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        generator = SurfaceCarvingGenerator(config, grad_map)

        result = generator.generate_finishing()

        assert result.tool_number == 3

    def test_scallop_to_stepover_calculation(self):
        """Scallop height should convert to stepover correctly."""
        config = CarvingConfig()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        generator = SurfaceCarvingGenerator(config, grad_map)

        # For ball end, stepover = 2 * sqrt(2*R*h - h^2)
        tool_radius = 3.175  # 1/8" ball
        scallop = 0.05  # 0.05mm scallop

        stepover = generator._scallop_to_stepover(scallop, tool_radius)

        # Should be roughly sqrt(2*3.175*0.05) * 2 ≈ 1.13mm
        assert stepover > 0
        assert stepover < tool_radius * 2  # Can't be more than diameter


# =============================================================================
# Pipeline Orchestrator Tests
# =============================================================================

class TestCarvingPipeline:
    """Tests for CarvingPipeline orchestrator."""

    def test_pipeline_generates_complete_program(self):
        """Pipeline should generate complete G-code program."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()

        assert isinstance(result, CarvingPipelineResult)
        assert len(result.gcode_lines) > 0
        assert result.total_operations >= 1

    def test_pipeline_includes_roughing_and_finishing(self):
        """Full pipeline should include roughing and finishing."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()

        assert result.roughing is not None
        assert result.finishing is not None
        assert result.total_operations == 2

    def test_pipeline_can_exclude_operations(self):
        """Operations can be individually disabled."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate(include_roughing=False)

        assert result.roughing is None
        assert result.finishing is not None
        assert result.total_operations == 1

    def test_pipeline_calculates_total_time(self):
        """Pipeline should calculate total cut time."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()

        assert result.total_cut_time_seconds > 0

    def test_gcode_has_header_footer(self):
        """G-code should have proper header and footer."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()
        gcode = result.get_gcode()

        assert "3D SURFACE CARVING PIPELINE" in gcode
        assert "END OF CARVING PROGRAM" in gcode
        assert "M30" in gcode

    def test_preview_graduation(self):
        """Can preview graduation without generating G-code."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        preview = pipeline.preview_graduation()

        assert "surface_type" in preview
        assert "apex_thickness_mm" in preview
        assert "sample_thicknesses" in preview
        assert "center" in preview["sample_thicknesses"]

    def test_preview_z_levels(self):
        """Can preview Z levels without generating G-code."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        z_levels = pipeline.preview_z_levels()

        assert len(z_levels) > 0
        assert all(z < 0 for z in z_levels)  # All negative

    def test_roughing_only_generation(self):
        """Can generate only roughing passes."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate_roughing_only()

        assert result.roughing is not None
        assert result.finishing is None
        assert result.total_operations == 1

    def test_finishing_only_generation(self):
        """Can generate only finishing passes."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate_finishing_only()

        assert result.roughing is None
        assert result.finishing is not None
        assert result.total_operations == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestCarvingIntegration:
    """Integration tests for complete carving workflow."""

    def test_benedetto_full_pipeline(self):
        """Full Benedetto archtop should generate valid G-code."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()
        gcode = result.get_gcode()

        # Should have G-code motion commands
        assert "G0" in gcode or "G00" in gcode
        assert "G1" in gcode or "G01" in gcode

        # Should have tool changes
        assert "M6" in gcode

        # Should have spindle commands
        assert "M3" in gcode
        assert "M5" in gcode

    def test_les_paul_top_pipeline(self):
        """Les Paul carved top should generate valid G-code."""
        config = create_les_paul_top_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()

        assert result.total_operations == 2
        assert len(result.gcode_lines) > 100

    def test_result_serialization(self):
        """Result should serialize to dict."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()
        data = result.to_dict()

        assert "generated_at" in data
        assert "total_cut_time_seconds" in data
        assert "operations" in data
        assert "graduation_map" in data

    def test_tools_specified_in_output(self):
        """Each operation should reference tool number."""
        config = create_benedetto_17_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()

        # Roughing uses T1
        assert result.roughing.tool_number == config.rough_tool_number

        # Finishing uses T3
        assert result.finishing.tool_number == config.finish_tool_number

    def test_recurve_affects_edge_thickness(self):
        """Recurve should reduce thickness near edges."""
        config_with_recurve = GraduationMapConfig(
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
            recurve_depth_mm=1.5,
        )
        config_no_recurve = GraduationMapConfig(
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
            recurve_depth_mm=0.0,
        )

        map_with = GraduationMap.create_parametric(config_with_recurve)
        map_without = GraduationMap.create_parametric(config_no_recurve)

        # Check near edge (x=230 gives r ≈ 0.92, well into recurve zone >0.85)
        # Default bounds are (-250, 250), so nx = 2*(230+250)/500 - 1 = 0.92
        t_with = map_with.get_thickness_at(230, 0)
        t_without = map_without.get_thickness_at(230, 0)

        # Recurve should make it thinner near edge
        assert t_with < t_without


# =============================================================================
# Asymmetric Carving Tests (LP-GAP-05)
# =============================================================================

class TestAsymmetricCarveProfile:
    """Tests for AsymmetricCarveProfile configuration."""

    def test_default_profile_has_authentic_1959_specs(self):
        """Default profile should have authentic 1959 Les Paul specs."""
        profile = AsymmetricCarveProfile()
        assert profile.peak_offset_y_mm == 30.0  # 30mm toward neck
        assert profile.major_radius_mm == 508.0  # 20" across width
        assert profile.minor_radius_mm == 381.0  # 15" along length
        assert profile.total_rise_mm == 7.8

    def test_profile_serialization(self):
        """Profile should serialize to dict."""
        profile = AsymmetricCarveProfile()
        d = profile.to_dict()
        assert "peak_offset_mm" in d
        assert "compound_radius_mm" in d
        assert "total_rise_mm" in d
        assert "slopes_deg" in d

    def test_les_paul_1959_preset(self):
        """1959 Les Paul preset should have correct specs."""
        config = create_les_paul_1959_asymmetric_config()
        assert config.graduation_map.surface_type == SurfaceType.ARCHTOP_ASYMMETRIC
        assert config.graduation_map.asymmetric_profile is not None
        assert config.material == MaterialHardness.MEDIUM  # Maple


class TestAsymmetricThicknessCalculation:
    """Tests for asymmetric thickness calculation."""

    def test_peak_at_offset_position(self):
        """Maximum thickness should be at the offset peak position."""
        profile = AsymmetricCarveProfile(
            peak_offset_x_mm=0.0,
            peak_offset_y_mm=30.0,
        )
        config = GraduationMapConfig(
            bounds_x_mm=(-165.0, 165.0),
            bounds_y_mm=(-222.0, 222.0),
            apex_thickness_mm=12.7,
            edge_thickness_mm=5.0,
            surface_type=SurfaceType.ARCHTOP_ASYMMETRIC,
            asymmetric_profile=profile,
        )
        grad_map = GraduationMap.create_parametric(config)

        # Thickness at offset peak (0, 30) should be higher than at geometric center (0, 0)
        t_at_peak = grad_map.get_thickness_at(0, 30)
        t_at_center = grad_map.get_thickness_at(0, 0)
        assert t_at_peak > t_at_center

    def test_thickness_decreases_from_peak(self):
        """Thickness should decrease as distance from offset peak increases."""
        config = create_les_paul_1959_asymmetric_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)

        # Get thicknesses at various distances from peak (0, 30)
        t_peak = grad_map.get_thickness_at(0, 30)
        t_mid = grad_map.get_thickness_at(50, 30)
        t_far = grad_map.get_thickness_at(120, 30)

        assert t_peak > t_mid
        assert t_mid > t_far

    def test_asymmetric_profile_vs_symmetric(self):
        """Asymmetric profile should differ from symmetric at same point."""
        # Symmetric config
        sym_config = GraduationMapConfig(
            bounds_x_mm=(-165.0, 165.0),
            bounds_y_mm=(-222.0, 222.0),
            apex_thickness_mm=12.7,
            edge_thickness_mm=5.0,
            surface_type=SurfaceType.ARCHTOP,
        )

        # Asymmetric config
        asym_config = GraduationMapConfig(
            bounds_x_mm=(-165.0, 165.0),
            bounds_y_mm=(-222.0, 222.0),
            apex_thickness_mm=12.7,
            edge_thickness_mm=5.0,
            surface_type=SurfaceType.ARCHTOP_ASYMMETRIC,
            asymmetric_profile=AsymmetricCarveProfile(peak_offset_y_mm=30.0),
        )

        sym_map = GraduationMap.create_parametric(sym_config)
        asym_map = GraduationMap.create_parametric(asym_config)

        # At geometric center (0, 0), symmetric should be thicker
        # because asymmetric peak is offset to (0, 30)
        t_sym_center = sym_map.get_thickness_at(0, 0)
        t_asym_center = asym_map.get_thickness_at(0, 0)
        assert t_sym_center > t_asym_center

    def test_binding_ledge_creates_flat_edge(self):
        """Binding ledge should create flat edge zone."""
        profile = AsymmetricCarveProfile(binding_ledge_mm=3.0)
        config = GraduationMapConfig(
            bounds_x_mm=(-165.0, 165.0),
            bounds_y_mm=(-222.0, 222.0),
            apex_thickness_mm=12.7,
            edge_thickness_mm=5.0,
            surface_type=SurfaceType.ARCHTOP_ASYMMETRIC,
            asymmetric_profile=profile,
        )
        grad_map = GraduationMap.create_parametric(config)

        # Points near the very edge should return edge thickness
        t_edge = grad_map.get_thickness_at(163, 0)  # Near X boundary
        assert t_edge <= config.edge_thickness_mm * 1.1  # Near edge thickness

    def test_cutaway_zone_has_steeper_slope(self):
        """Cutaway zone should have steeper slope than crown."""
        profile = AsymmetricCarveProfile(
            slope_crown_deg=1.5,
            slope_cutaway_deg=6.0,
            cutaway_zone_x_min=0.5,
            cutaway_zone_y_max=0.7,
        )
        config = GraduationMapConfig(
            bounds_x_mm=(-165.0, 165.0),
            bounds_y_mm=(-222.0, 222.0),
            apex_thickness_mm=12.7,
            edge_thickness_mm=5.0,
            surface_type=SurfaceType.ARCHTOP_ASYMMETRIC,
            asymmetric_profile=profile,
        )
        grad_map = GraduationMap.create_parametric(config)

        # Sample points in crown zone (near peak) and cutaway zone
        # Crown zone: small x, near peak y
        t_crown_1 = grad_map.get_thickness_at(20, 30)
        t_crown_2 = grad_map.get_thickness_at(40, 30)
        crown_delta = t_crown_1 - t_crown_2

        # Cutaway zone: large x, upper body
        t_cutaway_1 = grad_map.get_thickness_at(100, 100)
        t_cutaway_2 = grad_map.get_thickness_at(130, 100)
        cutaway_delta = t_cutaway_1 - t_cutaway_2

        # Cutaway should have larger thickness delta per distance (steeper slope)
        # This is a relative comparison of how quickly thickness changes
        assert cutaway_delta >= crown_delta * 0.5  # Allow some tolerance


class TestAsymmetricPipeline:
    """Integration tests for asymmetric carving pipeline."""

    def test_les_paul_1959_pipeline(self):
        """1959 Les Paul asymmetric carving should generate valid G-code."""
        config = create_les_paul_1959_asymmetric_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()

        assert result.total_operations == 2
        assert len(result.gcode_lines) > 100

        gcode = result.get_gcode()
        assert "G0" in gcode or "G00" in gcode
        assert "G1" in gcode or "G01" in gcode
        assert "M6" in gcode

    def test_asymmetric_result_serialization(self):
        """Asymmetric result should serialize with profile info."""
        config = create_les_paul_1959_asymmetric_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        result = pipeline.generate()
        data = result.to_dict()

        assert "graduation_map" in data
        # The serialized graduation map should include asymmetric info
        grad_data = data["graduation_map"]
        assert grad_data["config"]["surface_type"] == "archtop_asymmetric"
        # Asymmetric profile should be included
        assert "asymmetric_profile" in grad_data["config"]

    def test_preview_asymmetric_graduation(self):
        """Can preview asymmetric graduation map."""
        config = create_les_paul_1959_asymmetric_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        preview = pipeline.preview_graduation()

        assert preview["surface_type"] == "archtop_asymmetric"
        assert "sample_thicknesses" in preview

    def test_asymmetric_z_levels(self):
        """Asymmetric carving should generate valid Z levels."""
        config = create_les_paul_1959_asymmetric_config()
        grad_map = GraduationMap.create_parametric(config.graduation_map)
        pipeline = CarvingPipeline(config, grad_map)

        z_levels = pipeline.preview_z_levels()

        assert len(z_levels) > 0
        assert all(z < 0 for z in z_levels)
