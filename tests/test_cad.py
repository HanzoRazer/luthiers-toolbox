"""Tests for CAD module."""

import pytest
from luthiers_toolbox.cad import GuitarBody, GuitarNeck, Fretboard, Point, Line


def test_point_creation():
    """Test Point creation and methods."""
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    assert p1.x == 0
    assert p1.y == 0
    assert p2.distance_to(p1) == 5.0


def test_line_creation():
    """Test Line creation and methods."""
    line = Line(Point(0, 0), Point(10, 0))
    assert line.length() == 10.0
    midpoint = line.midpoint()
    assert midpoint.x == 5.0
    assert midpoint.y == 0.0


def test_guitar_body_creation():
    """Test GuitarBody creation."""
    body = GuitarBody(shape="stratocaster", scale_length=25.5)
    assert body.shape == "stratocaster"
    assert body.scale_length == 25.5
    assert len(body.outline_points) > 0


def test_guitar_body_dimensions():
    """Test GuitarBody dimensions."""
    body = GuitarBody(body_length=18.0, body_width=13.0)
    dims = body.get_dimensions()
    assert dims["length"] == 18.0
    assert dims["width"] == 13.0


def test_guitar_body_invalid_shape():
    """Test GuitarBody with invalid shape."""
    with pytest.raises(ValueError):
        GuitarBody(shape="invalid_shape")


def test_guitar_neck_creation():
    """Test GuitarNeck creation."""
    neck = GuitarNeck(scale_length=25.5, frets=22)
    assert neck.scale_length == 25.5
    assert neck.frets == 22


def test_guitar_neck_fret_positions():
    """Test fret position calculations."""
    neck = GuitarNeck(scale_length=25.5, frets=22)
    fret_12 = neck.get_fret_position(12)
    # 12th fret should be at exactly half the scale length
    assert abs(fret_12 - 12.75) < 0.01


def test_guitar_neck_width():
    """Test neck width calculations."""
    neck = GuitarNeck(nut_width=1.65, neck_width_at_12=2.25)
    assert neck.get_neck_width_at_fret(0) == 1.65
    assert neck.get_neck_width_at_fret(12) == 2.25


def test_fretboard_creation():
    """Test Fretboard creation."""
    fb = Fretboard(scale_length=25.5, frets=22)
    assert fb.scale_length == 25.5
    assert fb.frets == 22


def test_fretboard_fret_positions():
    """Test fretboard fret position calculations."""
    fb = Fretboard(scale_length=25.5, frets=22)
    positions = fb.calculate_fret_positions()
    assert len(positions) == 22
    assert positions[0] < positions[11]  # First fret before 12th


def test_fretboard_inlay_positions():
    """Test inlay position calculations."""
    fb = Fretboard()
    inlays = fb.get_inlay_positions("standard")
    assert 3 in inlays
    assert 12 in inlays
    assert 1 not in inlays
