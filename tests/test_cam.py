"""Tests for CAM module."""

import pytest
from luthiers_toolbox.cam import (
    Toolpath,
    ToolpathGenerator,
    GCodeGenerator,
    ToolpathType,
)


def test_toolpath_creation():
    """Test Toolpath creation."""
    tp = Toolpath(
        name="Test",
        toolpath_type=ToolpathType.PROFILE,
        tool_diameter=0.25,
        feedrate=40.0,
        plunge_rate=20.0,
        depth=0.5,
    )
    assert tp.name == "Test"
    assert tp.tool_diameter == 0.25
    assert len(tp.points) == 0


def test_toolpath_add_point():
    """Test adding points to toolpath."""
    tp = Toolpath(
        "Test", ToolpathType.PROFILE, 0.25, 40.0, 20.0, 0.5
    )
    tp.add_point(0, 0, 0)
    tp.add_point(1, 1, -0.5)
    assert len(tp.points) == 2


def test_toolpath_generator_creation():
    """Test ToolpathGenerator creation."""
    gen = ToolpathGenerator(stock_thickness=2.0)
    assert gen.stock_thickness == 2.0
    assert len(gen.toolpaths) == 0


def test_profile_toolpath_generation():
    """Test profile toolpath generation."""
    gen = ToolpathGenerator()
    points = [(0, 0), (5, 0), (5, 3), (0, 3)]
    tp = gen.generate_profile_toolpath(points, depth=0.5)
    assert tp.toolpath_type == ToolpathType.PROFILE
    assert len(tp.points) > 0


def test_pocket_toolpath_generation():
    """Test pocket toolpath generation."""
    gen = ToolpathGenerator()
    tp = gen.generate_pocket_toolpath(
        bounds=(0, 0, 5, 3),
        depth=0.5,
    )
    assert tp.toolpath_type == ToolpathType.POCKET
    assert len(tp.points) > 0


def test_gcode_generator_creation():
    """Test GCodeGenerator creation."""
    gen = GCodeGenerator(units="inches", spindle_speed=18000)
    assert gen.units == "inches"
    assert gen.spindle_speed == 18000


def test_gcode_header_generation():
    """Test G-code header generation."""
    gen = GCodeGenerator()
    header = gen.generate_header()
    assert len(header) > 0
    assert any("G20" in line or "G21" in line for line in header)


def test_gcode_footer_generation():
    """Test G-code footer generation."""
    gen = GCodeGenerator()
    footer = gen.generate_footer()
    assert len(footer) > 0
    assert any("M5" in line for line in footer)


def test_gcode_generation():
    """Test complete G-code generation."""
    tp_gen = ToolpathGenerator()
    points = [(0, 0), (5, 0), (5, 3)]
    tp = tp_gen.generate_profile_toolpath(points, depth=0.5)

    gcode_gen = GCodeGenerator()
    gcode = gcode_gen.generate([tp])
    assert len(gcode) > 0
    assert "G20" in gcode or "G21" in gcode
    assert "M3" in gcode
    assert "M5" in gcode
