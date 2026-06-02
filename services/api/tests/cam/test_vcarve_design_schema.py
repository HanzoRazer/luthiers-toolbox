"""
Tests for VCarveDesignV1 schema.

Validates that the design schema correctly enforces required fields
and rejects invalid inputs.
"""
import pytest

from app.cam.vcarve.intent_schema import (
    VCarveDesignV1,
    VCarvePathV1,
    PathPoint,
    validate_vcarve_design,
)


class TestVCarveDesignV1:
    """Tests for VCarveDesignV1 model."""

    def test_valid_design_accepted(self):
        """Well-formed design is accepted."""
        design = VCarveDesignV1(
            paths=[
                VCarvePathV1(
                    points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                    is_closed=False,
                )
            ],
            bit_angle_deg=60.0,
            target_line_width_mm=2.0,
        )
        assert design.bit_angle_deg == 60.0
        assert design.target_line_width_mm == 2.0
        assert design.target_depth_mm is None
        assert len(design.paths) == 1

    def test_optional_depth_override(self):
        """target_depth_mm can override calculated depth."""
        design = VCarveDesignV1(
            paths=[
                VCarvePathV1(
                    points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                )
            ],
            bit_angle_deg=60.0,
            target_line_width_mm=2.0,
            target_depth_mm=1.5,
        )
        assert design.target_depth_mm == 1.5

    def test_missing_paths_rejected(self):
        """Design without paths raises ValidationError."""
        with pytest.raises(Exception):
            VCarveDesignV1(
                bit_angle_deg=60.0,
                target_line_width_mm=2.0,
            )

    def test_empty_paths_rejected(self):
        """Design with empty paths list raises ValidationError."""
        with pytest.raises(Exception):
            VCarveDesignV1(
                paths=[],
                bit_angle_deg=60.0,
                target_line_width_mm=2.0,
            )

    def test_missing_bit_angle_rejected(self):
        """Design without bit_angle_deg raises ValidationError."""
        with pytest.raises(Exception):
            VCarveDesignV1(
                paths=[
                    VCarvePathV1(
                        points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                    )
                ],
                target_line_width_mm=2.0,
            )

    def test_missing_target_width_rejected(self):
        """Design without target_line_width_mm raises ValidationError."""
        with pytest.raises(Exception):
            VCarveDesignV1(
                paths=[
                    VCarvePathV1(
                        points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                    )
                ],
                bit_angle_deg=60.0,
            )

    def test_bit_angle_too_small_rejected(self):
        """bit_angle_deg < 10 raises ValidationError."""
        with pytest.raises(Exception):
            VCarveDesignV1(
                paths=[
                    VCarvePathV1(
                        points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                    )
                ],
                bit_angle_deg=5.0,
                target_line_width_mm=2.0,
            )

    def test_bit_angle_too_large_rejected(self):
        """bit_angle_deg > 120 raises ValidationError."""
        with pytest.raises(Exception):
            VCarveDesignV1(
                paths=[
                    VCarvePathV1(
                        points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                    )
                ],
                bit_angle_deg=150.0,
                target_line_width_mm=2.0,
            )

    def test_path_with_single_point_rejected(self):
        """Path with only 1 point raises ValidationError."""
        with pytest.raises(Exception):
            VCarveDesignV1(
                paths=[
                    VCarvePathV1(
                        points=[PathPoint(x=0, y=0)],
                    )
                ],
                bit_angle_deg=60.0,
                target_line_width_mm=2.0,
            )

    def test_multiple_paths_accepted(self):
        """Multiple valid paths are accepted."""
        design = VCarveDesignV1(
            paths=[
                VCarvePathV1(
                    points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                ),
                VCarvePathV1(
                    points=[PathPoint(x=0, y=5), PathPoint(x=10, y=5), PathPoint(x=10, y=10)],
                    is_closed=True,
                ),
            ],
            bit_angle_deg=90.0,
            target_line_width_mm=3.0,
        )
        assert len(design.paths) == 2
        assert design.paths[1].is_closed is True

    def test_tip_diameter_default_zero(self):
        """tip_diameter_mm defaults to 0 (sharp tip)."""
        design = VCarveDesignV1(
            paths=[
                VCarvePathV1(
                    points=[PathPoint(x=0, y=0), PathPoint(x=10, y=0)],
                )
            ],
            bit_angle_deg=60.0,
            target_line_width_mm=2.0,
        )
        assert design.tip_diameter_mm == 0.0


class TestValidateVCarveDesign:
    """Tests for validate_vcarve_design helper."""

    def test_valid_dict_returns_model(self):
        """Valid dict returns VCarveDesignV1 instance."""
        design_dict = {
            "paths": [
                {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}], "is_closed": False}
            ],
            "bit_angle_deg": 60.0,
            "target_line_width_mm": 2.0,
        }
        result = validate_vcarve_design(design_dict)
        assert isinstance(result, VCarveDesignV1)
        assert result.bit_angle_deg == 60.0

    def test_invalid_dict_raises_valueerror(self):
        """Invalid dict raises ValueError with clear message."""
        design_dict = {
            "paths": [],
            "bit_angle_deg": 60.0,
            "target_line_width_mm": 2.0,
        }
        with pytest.raises(ValueError, match="Invalid V-Carve design"):
            validate_vcarve_design(design_dict)

    def test_missing_key_raises_valueerror(self):
        """Missing required key raises ValueError."""
        design_dict = {
            "paths": [
                {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}]}
            ],
            # missing bit_angle_deg and target_line_width_mm
        }
        with pytest.raises(ValueError, match="Invalid V-Carve design"):
            validate_vcarve_design(design_dict)
