"""
DrillingDesignV1 Schema Tests

Tests for the drilling design schema (8I).

Key validations:
- Hole positions required
- hole_depth_mm > 0
- hole_diameter_mm > 0 (enables feasibility validation)
- peck_depth_mm > 0 and < hole_depth_mm when peck_drilling=True
"""
import pytest
from pydantic import ValidationError

from app.cam.drilling.intent_schema import (
    DrillingDesignV1,
    DrillPointV1,
    validate_drilling_design,
)


class TestDrillPointV1:
    """Tests for DrillPointV1 schema."""

    def test_minimal_point(self):
        """Minimal point with just x, y."""
        pt = DrillPointV1(x=10.0, y=20.0)
        assert pt.x == 10.0
        assert pt.y == 20.0
        assert pt.depth_mm is None
        assert pt.label == ""

    def test_point_with_depth_override(self):
        """Point with per-hole depth override."""
        pt = DrillPointV1(x=10.0, y=20.0, depth_mm=15.0, label="string_1")
        assert pt.depth_mm == 15.0
        assert pt.label == "string_1"

    def test_point_depth_bounds(self):
        """Depth override must be > 0 and <= 200."""
        with pytest.raises(ValidationError) as exc_info:
            DrillPointV1(x=10.0, y=20.0, depth_mm=0.0)
        assert "greater_than" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            DrillPointV1(x=10.0, y=20.0, depth_mm=250.0)
        assert "less_than_equal" in str(exc_info.value).lower()


class TestDrillingDesignV1:
    """Tests for DrillingDesignV1 schema."""

    @pytest.fixture
    def minimal_design(self):
        """Minimal valid design."""
        return {
            "holes": [{"x": 0.0, "y": 0.0}],
            "hole_depth_mm": 25.0,
            "hole_diameter_mm": 3.0,
            "peck_drilling": True,
            "peck_depth_mm": 5.0,
        }

    def test_minimal_valid_design(self, minimal_design):
        """Minimal valid design passes."""
        design = DrillingDesignV1(**minimal_design)
        assert design.hole_depth_mm == 25.0
        assert design.hole_diameter_mm == 3.0
        assert design.peck_drilling is True
        assert design.peck_depth_mm == 5.0
        assert design.dwell_ms == 0

    def test_holes_required(self):
        """Holes list is required."""
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(
                hole_depth_mm=25.0,
                hole_diameter_mm=3.0,
            )
        assert "holes" in str(exc_info.value).lower()

    def test_holes_not_empty(self):
        """Holes list must have at least one hole."""
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(
                holes=[],
                hole_depth_mm=25.0,
                hole_diameter_mm=3.0,
            )
        assert "at least" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()

    def test_hole_depth_required(self):
        """hole_depth_mm is required."""
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(
                holes=[{"x": 0.0, "y": 0.0}],
                hole_diameter_mm=3.0,
            )
        assert "hole_depth_mm" in str(exc_info.value).lower()

    def test_hole_diameter_required(self, minimal_design):
        """hole_diameter_mm is required for feasibility validation."""
        del minimal_design["hole_diameter_mm"]
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(**minimal_design)
        assert "hole_diameter_mm" in str(exc_info.value).lower()

    def test_hole_depth_bounds(self, minimal_design):
        """hole_depth_mm must be > 0 and <= 200."""
        minimal_design["hole_depth_mm"] = 0.0
        with pytest.raises(ValidationError):
            DrillingDesignV1(**minimal_design)

        minimal_design["hole_depth_mm"] = 250.0
        with pytest.raises(ValidationError):
            DrillingDesignV1(**minimal_design)

    def test_hole_diameter_bounds(self, minimal_design):
        """hole_diameter_mm must be > 0 and <= 50."""
        minimal_design["hole_diameter_mm"] = 0.0
        with pytest.raises(ValidationError):
            DrillingDesignV1(**minimal_design)

        minimal_design["hole_diameter_mm"] = 60.0
        with pytest.raises(ValidationError):
            DrillingDesignV1(**minimal_design)


class TestPeckDepthValidation:
    """Tests for peck_depth_mm validation (8I requirement)."""

    def test_peck_depth_required_when_peck_drilling_true(self):
        """peck_depth_mm must be > 0 when peck_drilling=True."""
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(
                holes=[{"x": 0.0, "y": 0.0}],
                hole_depth_mm=25.0,
                hole_diameter_mm=3.0,
                peck_drilling=True,
                peck_depth_mm=None,  # Missing
            )
        assert "peck_depth_mm must be > 0" in str(exc_info.value)

    def test_peck_depth_zero_invalid_when_peck_drilling(self):
        """peck_depth_mm=0 invalid when peck_drilling=True."""
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(
                holes=[{"x": 0.0, "y": 0.0}],
                hole_depth_mm=25.0,
                hole_diameter_mm=3.0,
                peck_drilling=True,
                peck_depth_mm=0.0,  # Field constraint catches this
            )
        # Either the field validator or model validator catches this
        err_text = str(exc_info.value).lower()
        assert "peck_depth_mm" in err_text

    def test_peck_depth_must_be_less_than_hole_depth(self):
        """peck_depth_mm must be < hole_depth_mm when peck_drilling=True."""
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(
                holes=[{"x": 0.0, "y": 0.0}],
                hole_depth_mm=25.0,
                hole_diameter_mm=3.0,
                peck_drilling=True,
                peck_depth_mm=25.0,  # Equal to hole_depth
            )
        assert "peck_depth_mm" in str(exc_info.value)
        assert "hole_depth_mm" in str(exc_info.value)

    def test_peck_depth_exceeds_hole_depth_invalid(self):
        """peck_depth_mm > hole_depth_mm is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            DrillingDesignV1(
                holes=[{"x": 0.0, "y": 0.0}],
                hole_depth_mm=25.0,
                hole_diameter_mm=3.0,
                peck_drilling=True,
                peck_depth_mm=30.0,  # Greater than hole_depth
            )
        assert "peck_depth_mm" in str(exc_info.value)

    def test_peck_depth_optional_when_peck_drilling_false(self):
        """peck_depth_mm is optional when peck_drilling=False."""
        design = DrillingDesignV1(
            holes=[{"x": 0.0, "y": 0.0}],
            hole_depth_mm=25.0,
            hole_diameter_mm=3.0,
            peck_drilling=False,
            peck_depth_mm=None,
        )
        assert design.peck_drilling is False
        assert design.peck_depth_mm is None

    def test_valid_peck_configuration(self):
        """Valid peck configuration passes."""
        design = DrillingDesignV1(
            holes=[{"x": 0.0, "y": 0.0}],
            hole_depth_mm=25.0,
            hole_diameter_mm=3.0,
            peck_drilling=True,
            peck_depth_mm=5.0,  # Valid: > 0 and < hole_depth
        )
        assert design.peck_depth_mm == 5.0


class TestValidateDrillingDesign:
    """Tests for validate_drilling_design function."""

    def test_valid_dict(self):
        """Valid dict passes through."""
        design = validate_drilling_design({
            "holes": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}],
            "hole_depth_mm": 30.0,
            "hole_diameter_mm": 4.0,
            "peck_drilling": True,
            "peck_depth_mm": 6.0,
        })
        assert isinstance(design, DrillingDesignV1)
        assert len(design.holes) == 2

    def test_invalid_dict_raises_valueerror(self):
        """Invalid dict raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_drilling_design({
                "holes": [],  # Invalid: empty
                "hole_depth_mm": 25.0,
                "hole_diameter_mm": 3.0,
            })
        assert "Invalid Drilling design" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Missing required fields raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_drilling_design({
                "holes": [{"x": 0.0, "y": 0.0}],
                # Missing hole_depth_mm and hole_diameter_mm
            })
        assert "Invalid Drilling design" in str(exc_info.value)
