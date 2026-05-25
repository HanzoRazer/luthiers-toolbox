"""
Tests for ProfileDesignV1 schema validation.

Validates the Profile design schema:
- Required fields
- Field bounds
- Contour validation
- Tab configuration coherence
"""
import pytest

from app.cam.profiling.intent_schema import (
    ProfileDesignV1,
    ProfilePointV1,
    validate_profile_design,
)


class TestProfileDesignV1:
    """Tests for ProfileDesignV1 schema."""

    def _make_valid_design(self) -> dict:
        """Create a valid Profile design dict."""
        return {
            "contour": [
                {"x": 0, "y": 0},
                {"x": 100, "y": 0},
                {"x": 100, "y": 100},
                {"x": 0, "y": 100},
            ],
            "is_closed": True,
            "is_outside": True,
            "tool_diameter_mm": 6.35,
            "cut_depth_mm": 6.0,
            "use_tabs": True,
            "tab_count": 4,
            "tab_width_mm": 6.0,
            "tab_height_mm": 1.5,
            "finishing_pass": True,
            "finishing_allowance_mm": 0.3,
        }

    def test_valid_design_accepted(self):
        """Valid design with all fields passes validation."""
        design = ProfileDesignV1(**self._make_valid_design())
        assert design.tool_diameter_mm == 6.35
        assert design.cut_depth_mm == 6.0
        assert len(design.contour) == 4

    def test_minimal_design_accepted(self):
        """Minimal design with only required fields passes."""
        design = ProfileDesignV1(
            contour=[
                ProfilePointV1(x=0, y=0),
                ProfilePointV1(x=10, y=0),
                ProfilePointV1(x=10, y=10),
            ],
            tool_diameter_mm=6.35,
            cut_depth_mm=6.0,
        )
        assert design.is_closed is True  # default
        assert design.is_outside is True  # default
        assert design.tab_count == 4  # default

    def test_contour_requires_3_points(self):
        """Contour with fewer than 3 points rejected."""
        design = self._make_valid_design()
        design["contour"] = [{"x": 0, "y": 0}, {"x": 10, "y": 0}]

        with pytest.raises(ValueError, match="at least 3"):
            ProfileDesignV1(**design)

    def test_empty_contour_rejected(self):
        """Empty contour rejected."""
        design = self._make_valid_design()
        design["contour"] = []

        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_tool_diameter_must_be_positive(self):
        """tool_diameter_mm <= 0 rejected."""
        design = self._make_valid_design()
        design["tool_diameter_mm"] = 0

        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_tool_diameter_upper_bound(self):
        """tool_diameter_mm > 50 rejected."""
        design = self._make_valid_design()
        design["tool_diameter_mm"] = 51.0

        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_cut_depth_must_be_positive(self):
        """cut_depth_mm <= 0 rejected."""
        design = self._make_valid_design()
        design["cut_depth_mm"] = 0

        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_cut_depth_upper_bound(self):
        """cut_depth_mm > 100 rejected."""
        design = self._make_valid_design()
        design["cut_depth_mm"] = 101.0

        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_tab_count_must_be_positive_when_tabs_enabled(self):
        """tab_count < 1 rejected when use_tabs=True."""
        design = self._make_valid_design()
        design["use_tabs"] = True
        design["tab_count"] = 0

        with pytest.raises(ValueError, match="tab_count must be >= 1"):
            ProfileDesignV1(**design)

    def test_tab_count_zero_allowed_when_tabs_disabled(self):
        """tab_count=0 allowed when use_tabs=False."""
        design = self._make_valid_design()
        design["use_tabs"] = False
        design["tab_count"] = 0

        model = ProfileDesignV1(**design)
        assert model.tab_count == 0
        assert model.use_tabs is False

    def test_tab_width_bounds(self):
        """tab_width_mm must be in [1.0, 30.0]."""
        design = self._make_valid_design()

        design["tab_width_mm"] = 0.5
        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

        design["tab_width_mm"] = 31.0
        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_tab_height_bounds(self):
        """tab_height_mm must be in [0.5, 10.0]."""
        design = self._make_valid_design()

        design["tab_height_mm"] = 0.4
        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

        design["tab_height_mm"] = 10.5
        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_finishing_allowance_bounds(self):
        """finishing_allowance_mm must be in [0.0, 5.0]."""
        design = self._make_valid_design()

        design["finishing_allowance_mm"] = -0.1
        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

        design["finishing_allowance_mm"] = 5.1
        with pytest.raises(ValueError):
            ProfileDesignV1(**design)

    def test_is_outside_false_accepted(self):
        """is_outside=False (inside cut) accepted."""
        design = self._make_valid_design()
        design["is_outside"] = False

        model = ProfileDesignV1(**design)
        assert model.is_outside is False

    def test_is_closed_false_accepted(self):
        """is_closed=False (open contour) accepted."""
        design = self._make_valid_design()
        design["is_closed"] = False

        model = ProfileDesignV1(**design)
        assert model.is_closed is False

    def test_finishing_pass_false_accepted(self):
        """finishing_pass=False accepted."""
        design = self._make_valid_design()
        design["finishing_pass"] = False

        model = ProfileDesignV1(**design)
        assert model.finishing_pass is False


class TestValidateProfileDesign:
    """Tests for validate_profile_design helper."""

    def _make_valid_design(self) -> dict:
        return {
            "contour": [
                {"x": 0, "y": 0},
                {"x": 100, "y": 0},
                {"x": 100, "y": 100},
            ],
            "tool_diameter_mm": 6.35,
            "cut_depth_mm": 6.0,
        }

    def test_valid_dict_returns_model(self):
        """Valid dict returns ProfileDesignV1 instance."""
        design = self._make_valid_design()
        result = validate_profile_design(design)

        assert isinstance(result, ProfileDesignV1)
        assert result.tool_diameter_mm == 6.35

    def test_invalid_dict_raises_valueerror(self):
        """Invalid dict raises ValueError."""
        design = self._make_valid_design()
        design["tool_diameter_mm"] = -1

        with pytest.raises(ValueError, match="Invalid Profile design"):
            validate_profile_design(design)

    def test_missing_required_key_raises_valueerror(self):
        """Missing required key raises ValueError."""
        design = self._make_valid_design()
        del design["tool_diameter_mm"]

        with pytest.raises(ValueError, match="Invalid Profile design"):
            validate_profile_design(design)
