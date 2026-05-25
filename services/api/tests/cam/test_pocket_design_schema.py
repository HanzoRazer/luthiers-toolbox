"""
PocketDesignV1 Schema Tests

Tests for the pocketing design schema (8J).

Key validations:
- Boundary >= 3 points
- Islands valid (>= 3 points each)
- tool_diameter_mm in L.1 range (0.5-50mm)
- stepover_percent in L.1 range (30-70%)
- pocket_depth_mm > 0
- finish_allowance_mm >= 0
"""
import pytest
from pydantic import ValidationError

from app.cam.pocketing.intent_schema import (
    PocketDesignV1,
    PocketIslandV1,
    PocketPointV1,
    validate_pocket_design,
)


class TestPocketPointV1:
    """Tests for PocketPointV1 schema."""

    def test_valid_point(self):
        """Valid point with x, y."""
        pt = PocketPointV1(x=10.0, y=20.0)
        assert pt.x == 10.0
        assert pt.y == 20.0

    def test_negative_coordinates_allowed(self):
        """Negative coordinates are valid."""
        pt = PocketPointV1(x=-50.0, y=-100.0)
        assert pt.x == -50.0
        assert pt.y == -100.0


class TestPocketIslandV1:
    """Tests for PocketIslandV1 schema."""

    def test_valid_island(self):
        """Valid island with 3+ points."""
        island = PocketIslandV1(boundary=[
            PocketPointV1(x=10, y=10),
            PocketPointV1(x=20, y=10),
            PocketPointV1(x=15, y=20),
        ])
        assert len(island.boundary) == 3

    def test_island_requires_3_points(self):
        """Island boundary must have at least 3 points."""
        with pytest.raises(ValidationError) as exc_info:
            PocketIslandV1(boundary=[
                PocketPointV1(x=10, y=10),
                PocketPointV1(x=20, y=10),
            ])
        err_text = str(exc_info.value).lower()
        assert "too_short" in err_text or "3 items" in err_text or "3 points" in err_text


class TestPocketDesignV1:
    """Tests for PocketDesignV1 schema."""

    @pytest.fixture
    def minimal_design(self):
        """Minimal valid design dict."""
        return {
            "boundary": [
                {"x": 0, "y": 0},
                {"x": 100, "y": 0},
                {"x": 100, "y": 60},
                {"x": 0, "y": 60},
            ],
            "pocket_depth_mm": 10.0,
            "tool_diameter_mm": 6.0,
        }

    def test_minimal_valid_design(self, minimal_design):
        """Minimal valid design passes."""
        design = PocketDesignV1(**minimal_design)
        assert design.pocket_depth_mm == 10.0
        assert design.tool_diameter_mm == 6.0
        assert design.stepover_percent == 40.0  # default
        assert design.islands == []
        assert design.finish_pass is True

    def test_boundary_required(self):
        """Boundary is required."""
        with pytest.raises(ValidationError) as exc_info:
            PocketDesignV1(
                pocket_depth_mm=10.0,
                tool_diameter_mm=6.0,
            )
        assert "boundary" in str(exc_info.value).lower()

    def test_boundary_min_3_points(self):
        """Boundary must have at least 3 points."""
        with pytest.raises(ValidationError) as exc_info:
            PocketDesignV1(
                boundary=[{"x": 0, "y": 0}, {"x": 100, "y": 0}],
                pocket_depth_mm=10.0,
                tool_diameter_mm=6.0,
            )
        err_text = str(exc_info.value).lower()
        assert "too_short" in err_text or "3 items" in err_text or "3 points" in err_text

    def test_pocket_depth_required(self, minimal_design):
        """pocket_depth_mm is required."""
        del minimal_design["pocket_depth_mm"]
        with pytest.raises(ValidationError) as exc_info:
            PocketDesignV1(**minimal_design)
        assert "pocket_depth_mm" in str(exc_info.value).lower()

    def test_pocket_depth_must_be_positive(self, minimal_design):
        """pocket_depth_mm must be > 0."""
        minimal_design["pocket_depth_mm"] = 0.0
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

        minimal_design["pocket_depth_mm"] = -5.0
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

    def test_pocket_depth_max(self, minimal_design):
        """pocket_depth_mm must be <= 100."""
        minimal_design["pocket_depth_mm"] = 150.0
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

    def test_tool_diameter_required(self, minimal_design):
        """tool_diameter_mm is required."""
        del minimal_design["tool_diameter_mm"]
        with pytest.raises(ValidationError) as exc_info:
            PocketDesignV1(**minimal_design)
        assert "tool_diameter_mm" in str(exc_info.value).lower()

    def test_tool_diameter_l1_range(self, minimal_design):
        """tool_diameter_mm must be in L.1 range (0.5-50mm)."""
        # Below minimum
        minimal_design["tool_diameter_mm"] = 0.3
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

        # Above maximum
        minimal_design["tool_diameter_mm"] = 60.0
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

    def test_stepover_percent_default(self, minimal_design):
        """stepover_percent defaults to 40%."""
        design = PocketDesignV1(**minimal_design)
        assert design.stepover_percent == 40.0

    def test_stepover_percent_l1_range(self, minimal_design):
        """stepover_percent must be in L.1 range (30-70%)."""
        # Below minimum (30%)
        minimal_design["stepover_percent"] = 20.0
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

        # Above maximum (70%)
        minimal_design["stepover_percent"] = 80.0
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

    def test_stepover_percent_valid_range(self, minimal_design):
        """Valid stepover values within L.1 range."""
        for pct in [30.0, 40.0, 50.0, 60.0, 70.0]:
            minimal_design["stepover_percent"] = pct
            design = PocketDesignV1(**minimal_design)
            assert design.stepover_percent == pct

    def test_finish_allowance_bounds(self, minimal_design):
        """finish_allowance_mm must be >= 0 and <= 5."""
        minimal_design["finish_allowance_mm"] = -0.1
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

        minimal_design["finish_allowance_mm"] = 6.0
        with pytest.raises(ValidationError):
            PocketDesignV1(**minimal_design)

    def test_design_with_islands(self, minimal_design):
        """Design with valid islands."""
        minimal_design["islands"] = [
            {
                "boundary": [
                    {"x": 30, "y": 20},
                    {"x": 40, "y": 20},
                    {"x": 35, "y": 30},
                ]
            },
            {
                "boundary": [
                    {"x": 60, "y": 20},
                    {"x": 70, "y": 20},
                    {"x": 65, "y": 30},
                ]
            },
        ]
        design = PocketDesignV1(**minimal_design)
        assert len(design.islands) == 2

    def test_roughing_only_overrides_finish_pass(self, minimal_design):
        """roughing_only=True forces finish_pass=False."""
        minimal_design["roughing_only"] = True
        minimal_design["finish_pass"] = True
        design = PocketDesignV1(**minimal_design)
        assert design.roughing_only is True
        assert design.finish_pass is False


class TestValidatePocketDesign:
    """Tests for validate_pocket_design function."""

    def test_valid_dict(self):
        """Valid dict passes through."""
        design = validate_pocket_design({
            "boundary": [
                {"x": 0, "y": 0},
                {"x": 100, "y": 0},
                {"x": 100, "y": 60},
                {"x": 0, "y": 60},
            ],
            "pocket_depth_mm": 15.0,
            "tool_diameter_mm": 8.0,
            "stepover_percent": 50.0,
        })
        assert isinstance(design, PocketDesignV1)
        assert design.pocket_depth_mm == 15.0

    def test_invalid_dict_raises_valueerror(self):
        """Invalid dict raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_pocket_design({
                "boundary": [],  # Invalid: empty
                "pocket_depth_mm": 10.0,
                "tool_diameter_mm": 6.0,
            })
        assert "Invalid Pocketing design" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Missing required fields raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_pocket_design({
                "boundary": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 5, "y": 10}],
                # Missing pocket_depth_mm and tool_diameter_mm
            })
        assert "Invalid Pocketing design" in str(exc_info.value)
