"""
Tests for PocketDesignV1 schema (Dev Order 8J, reconstructed from bytecode).
"""
import pytest
from pydantic import ValidationError

from app.cam.pocketing.intent_schema import (
    PocketDesignV1,
    PocketPointV1,
    PocketIslandV1,
    validate_pocket_design,
)


def _square(s=100.0):
    return [{"x": 0, "y": 0}, {"x": s, "y": 0}, {"x": s, "y": s}, {"x": 0, "y": s}]


def _valid_design() -> dict:
    return {
        "boundary": _square(),
        "islands": [],
        "pocket_depth_mm": 6.0,
        "tool_diameter_mm": 6.0,
        "stepover_percent": 50.0,
    }


class TestPocketDesignV1:
    def test_valid_design_accepted(self):
        d = PocketDesignV1(**_valid_design())
        assert len(d.boundary) == 4
        assert d.pocket_depth_mm == 6.0
        assert d.tool_diameter_mm == 6.0
        assert d.stepover_percent == 50.0
        assert d.islands == []

    def test_point_model(self):
        p = PocketPointV1(x=1.0, y=2.0)
        assert (p.x, p.y) == (1.0, 2.0)

    def test_island_model(self):
        isl = PocketIslandV1(boundary=[{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 1, "y": 1}])
        assert len(isl.boundary) == 3

    def test_island_too_few_points_rejected(self):
        with pytest.raises(ValidationError):
            PocketIslandV1(boundary=[{"x": 0, "y": 0}, {"x": 1, "y": 0}])

    def test_boundary_too_few_points_rejected(self):
        d = _valid_design()
        d["boundary"] = [{"x": 0, "y": 0}, {"x": 1, "y": 0}]
        with pytest.raises(ValidationError):
            PocketDesignV1(**d)

    def test_nonpositive_depth_rejected(self):
        d = _valid_design()
        d["pocket_depth_mm"] = 0
        with pytest.raises(ValidationError):
            PocketDesignV1(**d)

    def test_tool_below_l1_min_rejected(self):
        d = _valid_design()
        d["tool_diameter_mm"] = 0.3  # < 0.5
        with pytest.raises(ValidationError):
            PocketDesignV1(**d)

    def test_tool_above_l1_max_rejected(self):
        d = _valid_design()
        d["tool_diameter_mm"] = 60.0  # > 50
        with pytest.raises(ValidationError):
            PocketDesignV1(**d)

    def test_stepover_below_min_rejected(self):
        d = _valid_design()
        d["stepover_percent"] = 20.0  # < 30
        with pytest.raises(ValidationError):
            PocketDesignV1(**d)

    def test_stepover_above_max_rejected(self):
        d = _valid_design()
        d["stepover_percent"] = 80.0  # > 70
        with pytest.raises(ValidationError):
            PocketDesignV1(**d)

    def test_roughing_only_forces_finish_off(self):
        d = _valid_design()
        d["roughing_only"] = True
        d["finish_pass"] = True
        parsed = PocketDesignV1(**d)
        assert parsed.finish_pass is False  # coherence validator

    def test_islands_parsed(self):
        d = _valid_design()
        d["islands"] = [{"boundary": [{"x": 40, "y": 40}, {"x": 60, "y": 40}, {"x": 60, "y": 60}]}]
        parsed = PocketDesignV1(**d)
        assert len(parsed.islands) == 1
        assert len(parsed.islands[0].boundary) == 3


class TestValidatePocketDesign:
    def test_wrapper_accepts_valid(self):
        assert isinstance(validate_pocket_design(_valid_design()), PocketDesignV1)

    def test_wrapper_raises_valueerror(self):
        d = _valid_design()
        d["tool_diameter_mm"] = 0.1
        with pytest.raises(ValueError) as exc:
            validate_pocket_design(d)
        assert "Invalid Pocketing design" in str(exc.value)
