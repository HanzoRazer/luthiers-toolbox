"""
test_soundhole_climate.py — Tests for Climate/Humidity Corrections
==================================================================
DECOMP-002 Phase 4: Tests for soundhole_climate.py

Tests:
- Climate zone definitions and lookups
- Humidity-adjusted ring width calculations
- Seasonal movement estimates
- Edge cases and error handling
"""

import pytest
from app.calculators.soundhole_climate import (
    CLIMATE_ZONES,
    RING_WIDTH_HUMIDITY_ADDITION_PER_10PCT_SWING,
    RING_WIDTH_RADIUS_FRACTION,
    RING_WIDTH_ABSOLUTE_MIN_MM,
    get_ring_width_humidity_note,
    list_climate_zones,
    get_climate_zone,
    estimate_seasonal_movement,
)


# ── Climate Zone Tests ────────────────────────────────────────────────────────

class TestClimateZones:
    """Test climate zone definitions and access."""

    def test_climate_zones_exist(self):
        """All expected climate zones are defined."""
        assert "arid" in CLIMATE_ZONES
        assert "temperate" in CLIMATE_ZONES
        assert "continental" in CLIMATE_ZONES
        assert "humid" in CLIMATE_ZONES
        assert "tropical" in CLIMATE_ZONES

    def test_climate_zone_structure(self):
        """Each climate zone has required fields."""
        for key, zone in CLIMATE_ZONES.items():
            assert "label" in zone
            assert "rh_swing" in zone
            assert "example" in zone
            assert isinstance(zone["rh_swing"], (int, float))
            assert zone["rh_swing"] > 0

    def test_climate_zones_ordered_by_severity(self):
        """Climate zones are ordered from least to most humid swing."""
        swings = [CLIMATE_ZONES[k]["rh_swing"] for k in CLIMATE_ZONES.keys()]
        assert swings == sorted(swings)

    def test_list_climate_zones(self):
        """list_climate_zones returns all zones with key."""
        zones = list_climate_zones()
        assert len(zones) == 5
        assert all("key" in z for z in zones)
        assert all("label" in z for z in zones)
        assert all("rh_swing" in z for z in zones)

    def test_get_climate_zone(self):
        """get_climate_zone returns correct zone info."""
        zone = get_climate_zone("humid")
        assert zone["label"] == "Humid Subtropical"
        assert zone["rh_swing"] == 55

    def test_get_climate_zone_default(self):
        """get_climate_zone returns temperate for unknown key."""
        zone = get_climate_zone("unknown_zone")
        assert zone == CLIMATE_ZONES["temperate"]


# ── Ring Width Humidity Adjustment Tests ──────────────────────────────────────

class TestRingWidthHumidityNote:
    """Test climate-adjusted ring width calculations."""

    def test_temperate_baseline(self):
        """Temperate climate uses base minimum with no addition."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,  # 96mm diameter
            ring_width_mm=10.0,
            climate_key="temperate",
        )

        # Base min = max(48 * 0.15, 6.0) = 7.2mm
        # Swing = 35%, swing_above_base = 0, addition = 0
        assert result["base_min_mm"] == 7.2
        assert result["humidity_addition_mm"] == 0.0
        assert result["adjusted_min_mm"] == 7.2
        assert result["seasonal_status"] == "adequate"

    def test_arid_less_than_temperate(self):
        """Arid climate has lower swing than temperate, still uses base."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=10.0,
            climate_key="arid",
        )

        # Swing = 25%, swing_above_base = 0 (negative clamped to 0)
        assert result["humidity_addition_mm"] == 0.0
        assert result["adjusted_min_mm"] == result["base_min_mm"]

    def test_humid_climate_addition(self):
        """Humid climate adds ring width requirement."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,  # 96mm diameter
            ring_width_mm=10.0,
            climate_key="humid",
        )

        # Base = 7.2mm
        # Swing = 55%, swing_above_base = 20%
        # Addition = (20 / 10) * 0.5 = 1.0mm
        # Adjusted = 7.2 + 1.0 = 8.2mm
        assert result["base_min_mm"] == 7.2
        assert result["humidity_addition_mm"] == 1.0
        assert result["adjusted_min_mm"] == 8.2

    def test_tropical_maximum_addition(self):
        """Tropical climate has largest swing and addition."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=10.0,
            climate_key="tropical",
        )

        # Swing = 65%, swing_above_base = 30%
        # Addition = (30 / 10) * 0.5 = 1.5mm
        assert result["humidity_addition_mm"] == 1.5
        assert result["adjusted_min_mm"] == 8.7  # 7.2 + 1.5

    def test_status_adequate(self):
        """Ring width >= adjusted_min * 1.3 → adequate."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=12.0,  # Well above adjusted min
            climate_key="humid",
        )
        # Adjusted min = 8.2, threshold = 8.2 * 1.3 = 10.66
        # 12.0 > 10.66 → adequate
        assert result["seasonal_status"] == "adequate"
        assert "adequate" in result["seasonal_note"]

    def test_status_marginal(self):
        """adjusted_min <= ring_width < adjusted_min * 1.3 → marginal."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=9.0,  # Just above adjusted min
            climate_key="humid",
        )
        # Adjusted min = 8.2, threshold = 10.66
        # 8.2 <= 9.0 < 10.66 → marginal
        assert result["seasonal_status"] == "marginal"
        assert "marginal" in result["seasonal_note"].lower()

    def test_status_insufficient(self):
        """ring_width < adjusted_min → insufficient."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=7.0,  # Below adjusted min
            climate_key="humid",
        )
        # Adjusted min = 8.2, 7.0 < 8.2 → insufficient
        assert result["seasonal_status"] == "insufficient"
        assert "below" in result["seasonal_note"].lower()

    def test_absolute_minimum_enforced(self):
        """Small holes still get 6mm absolute minimum."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=20.0,  # 40mm diameter (very small)
            ring_width_mm=8.0,
            climate_key="temperate",
        )
        # 20 * 0.15 = 3.0mm, but absolute min = 6.0mm
        assert result["base_min_mm"] == 6.0

    def test_large_hole_proportional_minimum(self):
        """Large holes get proportional minimum > 6mm."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=60.0,  # 120mm diameter (very large)
            ring_width_mm=12.0,
            climate_key="temperate",
        )
        # 60 * 0.15 = 9.0mm > 6.0mm absolute
        assert result["base_min_mm"] == 9.0

    def test_estimated_movement_calculation(self):
        """Seasonal movement estimate is reasonable."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=10.0,
            climate_key="humid",
        )
        # Plate width ≈ 48 * 6 = 288mm
        # Movement = 288 * (55 * 0.18 * 0.002) ≈ 0.57mm
        assert result["estimated_seasonal_movement_mm"] > 0
        assert result["estimated_seasonal_movement_mm"] < 2.0  # Reasonable range

    def test_guidance_includes_key_info(self):
        """Guidance string includes climate and recommendations."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=10.0,
            climate_key="humid",
        )
        guidance = result["guidance"]
        assert "55%" in guidance  # RH swing
        assert "mm" in guidance    # Movement
        assert "≥" in guidance or ">=" in guidance  # Recommendation


# ── Seasonal Movement Estimates ───────────────────────────────────────────────

class TestSeasonalMovement:
    """Test seasonal wood movement estimates."""

    def test_temperate_movement(self):
        """Temperate climate movement for standard plate."""
        result = estimate_seasonal_movement(
            plate_width_mm=380.0,  # Typical OM lower bout
            climate_key="temperate",
        )

        assert result["climate"] == "Temperate"
        assert result["rh_swing_pct"] == 35
        assert result["plate_width_mm"] == 380.0
        # Movement = 380 * (35 * 0.18) * 0.002 ≈ 0.48mm
        assert 0.4 < result["estimated_movement_mm"] < 0.6

    def test_tropical_higher_movement(self):
        """Tropical climate has higher movement than temperate."""
        temp_result = estimate_seasonal_movement(380.0, "temperate")
        trop_result = estimate_seasonal_movement(380.0, "tropical")

        assert trop_result["estimated_movement_mm"] > temp_result["estimated_movement_mm"]
        assert trop_result["rh_swing_pct"] == 65

    def test_movement_scales_with_width(self):
        """Movement scales linearly with plate width."""
        result_small = estimate_seasonal_movement(200.0, "temperate")
        result_large = estimate_seasonal_movement(400.0, "temperate")

        # Should be roughly 2x
        ratio = result_large["estimated_movement_mm"] / result_small["estimated_movement_mm"]
        assert 1.9 < ratio < 2.1

    def test_mc_change_calculation(self):
        """MC change percentage is calculated correctly."""
        result = estimate_seasonal_movement(380.0, "humid")
        # Swing = 55%, MC change = 55 * 0.18 = 9.9%
        assert 9.5 < result["mc_change_pct"] < 10.5

    def test_unknown_climate_defaults_temperate(self):
        """Unknown climate key defaults to temperate."""
        result = estimate_seasonal_movement(380.0, "mars_colony")
        assert result["climate"] == "Temperate"
        assert result["rh_swing_pct"] == 35


# ── Edge Cases and Validation ─────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and input validation."""

    def test_zero_radius(self):
        """Zero radius uses absolute minimum."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=0.0,
            ring_width_mm=8.0,
            climate_key="temperate",
        )
        assert result["base_min_mm"] == 6.0  # Absolute minimum

    def test_very_small_ring_width(self):
        """Very small ring width correctly flagged insufficient."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=2.0,  # Dangerously small
            climate_key="temperate",
        )
        assert result["seasonal_status"] == "insufficient"

    def test_very_large_ring_width(self):
        """Very large ring width correctly flagged adequate."""
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=20.0,  # Very safe
            climate_key="tropical",
        )
        assert result["seasonal_status"] == "adequate"

    def test_zero_plate_width_movement(self):
        """Zero plate width returns zero movement."""
        result = estimate_seasonal_movement(0.0, "temperate")
        assert result["estimated_movement_mm"] == 0.0


# ── Integration Tests ─────────────────────────────────────────────────────────

class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_martin_om_houston_climate(self):
        """Martin OM in Houston (humid subtropical) needs larger ring."""
        # OM: 96mm soundhole (48mm radius), typically 8mm ring width
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=48.0,
            ring_width_mm=8.0,
            climate_key="humid",
        )

        # Adjusted min = 8.2mm, actual = 8.0mm → marginal or insufficient
        assert result["adjusted_min_mm"] > result["base_min_mm"]
        assert result["seasonal_status"] in ["marginal", "insufficient"]
        assert "Houston" in result["climate"] or "Humid" in result["climate"]

    def test_classical_seattle_climate(self):
        """Classical guitar in Seattle (temperate) is fine."""
        # Classical: 85mm soundhole (42.5mm radius), typically 9mm ring
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=42.5,
            ring_width_mm=9.0,
            climate_key="temperate",
        )

        # Base min = max(42.5 * 0.15, 6.0) = 6.4mm
        # No addition for temperate
        # 9.0 > 6.4 * 1.3 = 8.3 → adequate
        assert result["seasonal_status"] == "adequate"

    def test_dreadnought_miami_climate(self):
        """Dreadnought in Miami (tropical) needs maximum ring width."""
        # D-28: 100mm soundhole (50mm radius), 8mm ring (marginal)
        result = get_ring_width_humidity_note(
            soundhole_radius_mm=50.0,
            ring_width_mm=8.0,
            climate_key="tropical",
        )

        # Base = 7.5mm
        # Tropical swing = 65%, addition = 1.5mm
        # Adjusted = 9.0mm
        # 8.0 < 9.0 → insufficient
        assert result["adjusted_min_mm"] == 9.0
        assert result["seasonal_status"] == "insufficient"
        assert "Miami" in result["seasonal_note"] or "Tropical" in result["climate"]


# ── Constants Validation ──────────────────────────────────────────────────────

class TestConstants:
    """Validate module constants are reasonable."""

    def test_ring_width_fraction_reasonable(self):
        """15% of radius is empirically validated."""
        assert RING_WIDTH_RADIUS_FRACTION == 0.15

    def test_absolute_minimum_reasonable(self):
        """6mm absolute minimum matches empirical data."""
        assert RING_WIDTH_ABSOLUTE_MIN_MM == 6.0

    def test_humidity_addition_factor_reasonable(self):
        """0.5mm per 10% swing is calibrated value."""
        assert RING_WIDTH_HUMIDITY_ADDITION_PER_10PCT_SWING == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
