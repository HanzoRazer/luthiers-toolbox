"""
Tests for archtop_graduation.py — ARCH-003.

Verifies the physics connection between normalized graduation template
and plate_design thickness calculator.
"""

import pytest

from app.calculators.plate_design.archtop_graduation import (
    graduation_from_wood_and_target,
    GraduationResult,
)


class TestGraduationFromWoodAndTarget:
    """Test graduation_from_wood_and_target function."""

    def test_maple_top_archtop_120hz(self):
        """Maple top, archtop body, 120Hz target."""
        result = graduation_from_wood_and_target(
            material="maple",
            body_style="archtop",
            target_hz=120.0,
        )
        assert isinstance(result, GraduationResult)
        assert result.edge_mm > 0
        assert result.apex_mm > result.edge_mm
        assert result.arch_height_mm > 0
        assert result.body_style == "archtop"
        assert result.material == "maple"
        assert result.target_hz == 120.0

    def test_sitka_spruce_top_archtop_105hz(self):
        """Sitka spruce top, archtop body, 105Hz target."""
        result = graduation_from_wood_and_target(
            material="sitka_spruce",
            body_style="archtop",
            target_hz=105.0,
        )
        assert isinstance(result, GraduationResult)
        assert result.edge_mm > 0
        assert result.apex_mm > result.edge_mm
        assert result.arch_height_mm > 0
        assert result.body_style == "archtop"
        assert result.material == "sitka_spruce"
        assert result.target_hz == 105.0


class TestThicknessAtZone:
    """Test thickness_at_zone method of GraduationResult."""

    def test_edge_and_apex_boundaries(self):
        """thickness_at_zone(0.0) == edge_mm, thickness_at_zone(1.0) == apex_mm."""
        result = graduation_from_wood_and_target(
            material="maple",
            body_style="archtop",
            target_hz=120.0,
        )
        # Edge (normalized=0.0) should return edge_mm
        assert result.thickness_at_zone(0.0) == pytest.approx(result.edge_mm)
        # Apex (normalized=1.0) should return apex_mm
        assert result.thickness_at_zone(1.0) == pytest.approx(result.apex_mm)
        # Midpoint should be between edge and apex
        mid = result.thickness_at_zone(0.5)
        assert result.edge_mm < mid < result.apex_mm


class TestErrorHandling:
    """Test error cases."""

    def test_unknown_material_raises(self):
        """Unknown material should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown material"):
            graduation_from_wood_and_target(
                material="unobtainium",
                body_style="archtop",
                target_hz=120.0,
            )

    def test_unknown_body_style_raises(self):
        """Unknown body style should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown body style"):
            graduation_from_wood_and_target(
                material="maple",
                body_style="not_a_real_style",
                target_hz=120.0,
            )


class TestToDict:
    """Test to_dict serialization."""

    def test_to_dict_returns_dict(self):
        """to_dict should return a dictionary with all fields."""
        result = graduation_from_wood_and_target(
            material="maple",
            body_style="archtop",
            target_hz=120.0,
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["edge_mm"] == result.edge_mm
        assert d["apex_mm"] == result.apex_mm
        assert d["arch_height_mm"] == result.arch_height_mm
        assert d["body_style"] == "archtop"
        assert d["material"] == "maple"
        assert d["target_hz"] == 120.0
