"""
Tests for Saw Lab Calculator Adapters

Tests the adapter layer that bridges Saw Lab calculators to the Calculator Spine.
"""
import pytest

from app.calculators.saw.bite_per_tooth_adapter import (
    compute_bite_per_tooth,
    BitePerToothResult,
)
from app.calculators.saw.rim_speed_adapter import (
    compute_saw_rim_speed,
    SawRimSpeedResult,
)
from app.calculators.saw.heat_adapter import (
    estimate_saw_heat_risk,
    SawHeatResult,
)
from app.calculators.saw.deflection_adapter import (
    estimate_blade_deflection,
    estimate_feed_force_n,
    BladeDeflectionResult,
)
from app.calculators.saw.kickback_adapter import (
    assess_kickback_risk,
    KickbackRiskResult,
)


class TestBitePerTooth:
    """Tests for bite-per-tooth calculator."""

    def test_basic_calculation(self):
        """Test basic bite per tooth formula."""
        # feed / (rpm * teeth)
        # 3000 / (3450 * 24) = 0.0362mm
        result = compute_bite_per_tooth(
            feed_mm_min=3000,
            rpm=3450,
            tooth_count=24,
        )
        
        assert isinstance(result, BitePerToothResult)
        assert result.bite_mm is not None
        assert abs(result.bite_mm - 0.0362) < 0.001
        assert result.in_range is False  # Below typical 0.05mm minimum

    def test_in_range_bite(self):
        """Test bite in recommended range."""
        result = compute_bite_per_tooth(
            feed_mm_min=6000,
            rpm=3450,
            tooth_count=24,
            min_bite_mm=0.05,
            max_bite_mm=0.50,
        )
        
        # 6000 / (3450 * 24) = 0.0725mm - in range
        assert result.in_range is True
        assert "in range" in result.message.lower()

    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        result = compute_bite_per_tooth(
            feed_mm_min=3000,
            rpm=0,
            tooth_count=24,
        )
        
        assert result.bite_mm == 0.0
        assert result.in_range is False


class TestRimSpeed:
    """Tests for rim speed calculator."""

    def test_basic_calculation(self):
        """Test rim speed formula: v = π * d * rpm / 60."""
        # 10" blade (254mm) at 3450 RPM
        result = compute_saw_rim_speed(
            blade_diameter_mm=254,
            rpm=3450,
        )
        
        assert isinstance(result, SawRimSpeedResult)
        # v = π * 0.254 * 3450 / 60 ≈ 45.9 m/s
        assert abs(result.speed_m_per_s - 45.9) < 1.0
        assert result.speed_sfpm > 0

    def test_within_limits(self):
        """Test speed limit checking."""
        result = compute_saw_rim_speed(
            blade_diameter_mm=254,
            rpm=3450,
            max_speed_m_per_s=60.0,
        )
        
        assert result.within_limits is True

    def test_exceeds_limits(self):
        """Test detection of excessive rim speed."""
        result = compute_saw_rim_speed(
            blade_diameter_mm=400,  # 16" blade
            rpm=5000,
            max_speed_m_per_s=60.0,
        )
        
        # v = π * 0.4 * 5000 / 60 ≈ 104.7 m/s
        assert result.within_limits is False
        assert "REDUCE" in result.message.upper()


class TestHeatRisk:
    """Tests for heat risk calculator."""

    def test_ideal_conditions(self):
        """Test heat with good bite and speed."""
        result = estimate_saw_heat_risk(
            bite_mm=0.15,  # Good bite
            rim_speed_m_s=30.0,  # Moderate speed
            material_id="maple",
        )
        
        assert isinstance(result, SawHeatResult)
        assert result.heat_index < 0.5
        assert result.category in ("COOL", "WARM")

    def test_rubbing_conditions(self):
        """Test heat with too-low bite (rubbing)."""
        result = estimate_saw_heat_risk(
            bite_mm=0.02,  # Too low
            rim_speed_m_s=40.0,  # High speed
            material_id="ebony",  # Heat sensitive
        )
        
        assert result.heat_index > 0.5
        assert result.category in ("HOT", "CRITICAL")

    def test_material_sensitivity(self):
        """Test that dense woods show higher heat risk."""
        ebony_result = estimate_saw_heat_risk(
            bite_mm=0.10,
            rim_speed_m_s=35.0,
            material_id="ebony",
        )
        
        spruce_result = estimate_saw_heat_risk(
            bite_mm=0.10,
            rim_speed_m_s=35.0,
            material_id="spruce",
        )
        
        assert ebony_result.heat_index > spruce_result.heat_index


class TestDeflection:
    """Tests for blade deflection calculator."""

    def test_basic_deflection(self):
        """Test basic deflection estimate."""
        force = estimate_feed_force_n(
            bite_mm=0.15,
            depth_mm=25,
            material_hardness=1.0,
        )
        
        result = estimate_blade_deflection(
            blade_diameter_mm=254,
            kerf_mm=3.0,
            feed_force_n=force,
        )
        
        assert isinstance(result, BladeDeflectionResult)
        assert result.deflection_mm >= 0

    def test_thin_kerf_more_deflection(self):
        """Test that thin kerf blades deflect more."""
        force = 50.0
        
        standard = estimate_blade_deflection(
            blade_diameter_mm=254,
            kerf_mm=3.0,
            feed_force_n=force,
        )
        
        thin = estimate_blade_deflection(
            blade_diameter_mm=254,
            kerf_mm=2.0,
            feed_force_n=force,
        )
        
        assert thin.deflection_mm > standard.deflection_mm


class TestKickback:
    """Tests for kickback risk calculator."""

    def test_safe_setup(self):
        """Test low-risk setup."""
        result = assess_kickback_risk(
            blade_diameter_mm=254,
            blade_height_above_work_mm=6,  # Ideal
            depth_of_cut_mm=19,
            bite_mm=0.15,
            has_riving_knife=True,
            has_anti_kickback=True,
            is_ripping=True,
        )
        
        assert isinstance(result, KickbackRiskResult)
        assert result.category == "LOW"
        assert result.risk_score < 0.3

    def test_no_riving_knife(self):
        """Test high risk without riving knife."""
        result = assess_kickback_risk(
            blade_diameter_mm=254,
            blade_height_above_work_mm=6,
            depth_of_cut_mm=19,
            bite_mm=0.15,
            has_riving_knife=False,  # DANGER
            has_anti_kickback=False,
            is_ripping=True,
        )
        
        assert result.risk_score > 0.3
        assert "RIVING KNIFE" in str(result.risk_factors)

    def test_aggressive_bite_warning(self):
        """Test warning for aggressive bite."""
        result = assess_kickback_risk(
            blade_diameter_mm=254,
            blade_height_above_work_mm=6,
            depth_of_cut_mm=19,
            bite_mm=0.5,  # Very aggressive
            has_riving_knife=True,
        )
        
        assert any("bite" in f.lower() for f in result.risk_factors)
