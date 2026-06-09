"""
Tests for DrillingDesignV1 schema (Dev Order 8I).

Validates the design bucket for peck-drilling CamIntentV1 migration.
"""
import pytest
from pydantic import ValidationError

from app.cam.drilling.intent_schema import (
    DrillingDesignV1,
    DrillPointV1,
    validate_drilling_design,
)


def _valid_design() -> dict:
    return {
        "holes": [{"x": 0, "y": 0}, {"x": 10.5, "y": 0, "label": "string_2"}],
        "hole_depth_mm": 20.0,
        "hole_diameter_mm": 3.0,
        "peck_drilling": True,
        "peck_depth_mm": 5.0,
    }


class TestDrillingDesignV1:
    def test_valid_design_accepted(self):
        d = DrillingDesignV1(**_valid_design())
        assert len(d.holes) == 2
        assert d.hole_depth_mm == 20.0
        assert d.hole_diameter_mm == 3.0
        assert d.peck_drilling is True
        assert d.peck_depth_mm == 5.0

    def test_point_optional_fields(self):
        p = DrillPointV1(x=1.0, y=2.0)
        assert p.depth_mm is None
        assert p.label == ""
        p2 = DrillPointV1(x=1.0, y=2.0, depth_mm=12.0, label="bolt")
        assert p2.depth_mm == 12.0
        assert p2.label == "bolt"

    def test_empty_holes_rejected(self):
        d = _valid_design()
        d["holes"] = []
        with pytest.raises(ValidationError):
            DrillingDesignV1(**d)

    def test_nonpositive_hole_depth_rejected(self):
        d = _valid_design()
        d["hole_depth_mm"] = 0
        with pytest.raises(ValidationError):
            DrillingDesignV1(**d)

    def test_nonpositive_diameter_rejected(self):
        d = _valid_design()
        d["hole_diameter_mm"] = 0
        with pytest.raises(ValidationError):
            DrillingDesignV1(**d)

    def test_oversize_diameter_rejected(self):
        d = _valid_design()
        d["hole_diameter_mm"] = 60.0  # le=50
        with pytest.raises(ValidationError):
            DrillingDesignV1(**d)

    def test_nonpositive_peck_depth_rejected(self):
        d = _valid_design()
        d["peck_depth_mm"] = 0
        with pytest.raises(ValidationError):
            DrillingDesignV1(**d)

    def test_per_hole_depth_override(self):
        d = _valid_design()
        d["holes"] = [{"x": 0, "y": 0, "depth_mm": 8.0}]
        parsed = DrillingDesignV1(**d)
        assert parsed.holes[0].depth_mm == 8.0


class TestValidateDrillingDesign:
    def test_wrapper_accepts_valid(self):
        d = validate_drilling_design(_valid_design())
        assert isinstance(d, DrillingDesignV1)

    def test_wrapper_raises_valueerror_on_invalid(self):
        d = _valid_design()
        d["hole_diameter_mm"] = -1
        with pytest.raises(ValueError) as exc:
            validate_drilling_design(d)
        assert "Invalid Drilling design" in str(exc.value)
