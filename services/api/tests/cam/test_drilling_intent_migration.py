"""
Drilling Intent Migration Tests (8I)

Tests for:
- Adapter mapping (hole_diameter_mm -> DrillConfig.drill_diameter_mm)
- Feasibility validation (depth/diameter ratio warning)
- Integration tests
"""
import pytest
from unittest.mock import patch, MagicMock

from app.cam.drilling import (
    DrillConfig,
    DrillingDesignV1,
    drilling_params_from_intent,
    compute_drilling_feasibility,
    hash_feasibility_result,
)
from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1


class TestDrillingParamsFromIntent:
    """Tests for drilling_params_from_intent adapter."""

    @pytest.fixture
    def minimal_intent(self):
        """Minimal valid CamIntentV1 for drilling."""
        return CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "holes": [
                    {"x": 0.0, "y": 0.0},
                    {"x": 10.5, "y": 0.0},
                    {"x": 21.0, "y": 0.0},
                ],
                "hole_depth_mm": 45.0,
                "hole_diameter_mm": 3.175,  # 1/8" bit
                "peck_drilling": True,
                "peck_depth_mm": 5.0,
            },
            context={
                "feed_rate_mm_min": 100.0,
                "spindle_rpm": 2000,
                "safe_z_mm": 10.0,
                "retract_z_mm": 2.0,
            },
        )

    def test_hole_diameter_maps_to_drill_diameter(self, minimal_intent):
        """
        Adapter test: hole_diameter_mm maps to DrillConfig.drill_diameter_mm.

        This is the key mapping required by 8I - hole_diameter_mm in the design
        enables feasibility validation for depth/diameter ratio.
        """
        holes, config = drilling_params_from_intent(minimal_intent)

        # KEY ASSERTION: hole_diameter_mm -> drill_diameter_mm
        assert config.drill_diameter_mm == 3.175

    def test_hole_positions_mapped(self, minimal_intent):
        """Hole positions are correctly mapped."""
        holes, config = drilling_params_from_intent(minimal_intent)

        assert len(holes) == 3
        assert holes[0].x == 0.0
        assert holes[1].x == 10.5
        assert holes[2].x == 21.0

    def test_depth_and_peck_mapped(self, minimal_intent):
        """Depth and peck depth are correctly mapped."""
        holes, config = drilling_params_from_intent(minimal_intent)

        assert config.hole_depth_mm == 45.0
        assert config.peck_depth_mm == 5.0
        assert config.use_canned_cycle is True  # peck_drilling=True means G83

    def test_context_feed_rate_mapped(self, minimal_intent):
        """Context feed rate is mapped to config."""
        holes, config = drilling_params_from_intent(minimal_intent)

        assert config.feed_rate == 100.0
        assert config.spindle_rpm == 2000

    def test_context_z_heights_mapped(self, minimal_intent):
        """Context Z heights are mapped to config."""
        holes, config = drilling_params_from_intent(minimal_intent)

        assert config.safe_z_mm == 10.0
        assert config.retract_z_mm == 2.0

    def test_defaults_applied(self):
        """Defaults are applied when context omits values."""
        intent = CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "holes": [{"x": 0.0, "y": 0.0}],
                "hole_depth_mm": 25.0,
                "hole_diameter_mm": 3.0,
                "peck_drilling": True,
                "peck_depth_mm": 5.0,
            },
            context={},  # Empty context
        )
        holes, config = drilling_params_from_intent(intent)

        # Defaults from adapter
        assert config.feed_rate == 100.0
        assert config.rapid_rate == 3000.0
        assert config.spindle_rpm == 2000
        assert config.safe_z_mm == 10.0
        assert config.retract_z_mm == 2.0

    def test_non_peck_drilling(self):
        """peck_drilling=False sets use_canned_cycle=False (G81 vs G83)."""
        intent = CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "holes": [{"x": 0.0, "y": 0.0}],
                "hole_depth_mm": 10.0,
                "hole_diameter_mm": 6.0,
                "peck_drilling": False,  # No peck
            },
            context={},
        )
        holes, config = drilling_params_from_intent(intent)

        assert config.use_canned_cycle is False


class TestDrillingFeasibility:
    """Tests for drilling feasibility check."""

    def test_low_risk_valid_config(self):
        """Valid configuration with no warnings returns low risk."""
        result = compute_drilling_feasibility(
            hole_depth_mm=25.0,
            hole_diameter_mm=6.0,  # ratio = 4.2
            peck_depth_mm=5.0,
            peck_drilling=True,
            feed_rate_mm_min=100.0,
            spindle_rpm=2000,
            safe_z_mm=10.0,
            retract_z_mm=2.0,
            hole_count=6,
            dwell_ms=0,
        )

        assert result.feasible is True
        assert result.risk_level == "low"
        assert len(result.issues) == 0
        assert len(result.warnings) == 0

    def test_depth_diameter_ratio_warning(self):
        """
        Feasibility test: depth/diameter ratio > 10 triggers warning.

        This matches the behavior in peck_cycle.py _validate().
        """
        result = compute_drilling_feasibility(
            hole_depth_mm=50.0,
            hole_diameter_mm=3.0,  # ratio = 16.7 > 10
            peck_depth_mm=5.0,
            peck_drilling=True,
            feed_rate_mm_min=100.0,
            spindle_rpm=2000,
            safe_z_mm=10.0,
            retract_z_mm=2.0,
            hole_count=6,
            dwell_ms=0,
        )

        assert result.feasible is True  # Warning, not blocking
        assert result.risk_level in ("medium", "high")
        assert any("depth/diameter ratio" in w for w in result.warnings)
        assert any("16.7" in w for w in result.warnings)  # Actual ratio

    def test_extreme_ratio_warning(self):
        """Very high depth/diameter ratio triggers warning."""
        result = compute_drilling_feasibility(
            hole_depth_mm=100.0,
            hole_diameter_mm=2.0,  # ratio = 50 >> 10
            peck_depth_mm=2.0,
            peck_drilling=True,
            feed_rate_mm_min=50.0,
            spindle_rpm=2000,
            safe_z_mm=10.0,
            retract_z_mm=2.0,
            hole_count=1,
            dwell_ms=0,
        )

        assert result.feasible is True
        assert any("depth/diameter ratio" in w for w in result.warnings)
        assert result.summary["depth_diameter_ratio"] == 50.0

    def test_zero_hole_depth_blocks(self):
        """Zero hole depth is a blocking issue."""
        result = compute_drilling_feasibility(
            hole_depth_mm=0.0,  # Invalid
            hole_diameter_mm=3.0,
            peck_depth_mm=5.0,
            peck_drilling=True,
            feed_rate_mm_min=100.0,
            spindle_rpm=2000,
            safe_z_mm=10.0,
            retract_z_mm=2.0,
            hole_count=1,
            dwell_ms=0,
        )

        assert result.feasible is False
        assert result.risk_level == "blocked"
        assert any("hole_depth_mm" in i for i in result.issues)

    def test_zero_peck_depth_blocks_when_peck_drilling(self):
        """Zero peck depth when peck_drilling=True is blocking."""
        result = compute_drilling_feasibility(
            hole_depth_mm=25.0,
            hole_diameter_mm=3.0,
            peck_depth_mm=0.0,  # Invalid when peck_drilling
            peck_drilling=True,
            feed_rate_mm_min=100.0,
            spindle_rpm=2000,
            safe_z_mm=10.0,
            retract_z_mm=2.0,
            hole_count=1,
            dwell_ms=0,
        )

        assert result.feasible is False
        assert result.risk_level == "blocked"

    def test_summary_contains_ratio(self):
        """Summary includes depth_diameter_ratio for traceability."""
        result = compute_drilling_feasibility(
            hole_depth_mm=30.0,
            hole_diameter_mm=6.0,  # ratio = 5.0
            peck_depth_mm=5.0,
            peck_drilling=True,
            feed_rate_mm_min=100.0,
            spindle_rpm=2000,
            safe_z_mm=10.0,
            retract_z_mm=2.0,
            hole_count=4,
            dwell_ms=0,
        )

        assert result.summary["depth_diameter_ratio"] == 5.0
        assert result.summary["hole_count"] == 4
        assert result.summary["peck_drilling"] is True


class TestHashFeasibilityResult:
    """Tests for feasibility result hashing."""

    def test_hash_is_64_chars(self):
        """Hash must be full 64-char SHA256."""
        result = compute_drilling_feasibility(
            hole_depth_mm=25.0,
            hole_diameter_mm=3.0,
            peck_depth_mm=5.0,
            peck_drilling=True,
            feed_rate_mm_min=100.0,
            spindle_rpm=2000,
            safe_z_mm=10.0,
            retract_z_mm=2.0,
            hole_count=1,
            dwell_ms=0,
        )
        hash_val = hash_feasibility_result(result)

        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_hash_deterministic(self):
        """Same input produces same hash."""
        def make_result():
            return compute_drilling_feasibility(
                hole_depth_mm=25.0,
                hole_diameter_mm=3.0,
                peck_depth_mm=5.0,
                peck_drilling=True,
                feed_rate_mm_min=100.0,
                spindle_rpm=2000,
                safe_z_mm=10.0,
                retract_z_mm=2.0,
                hole_count=1,
                dwell_ms=0,
            )

        hash1 = hash_feasibility_result(make_result())
        hash2 = hash_feasibility_result(make_result())

        assert hash1 == hash2


class TestDrillingIntentIntegration:
    """Integration tests for full intent -> G-code flow."""

    @pytest.fixture
    def string_through_intent(self):
        """String-through ferrule drilling intent."""
        return CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "holes": [
                    {"x": 0.0, "y": 0.0, "label": "string_1"},
                    {"x": 10.5, "y": 0.0, "label": "string_2"},
                    {"x": 21.0, "y": 0.0, "label": "string_3"},
                    {"x": 31.5, "y": 0.0, "label": "string_4"},
                    {"x": 42.0, "y": 0.0, "label": "string_5"},
                    {"x": 52.5, "y": 0.0, "label": "string_6"},
                ],
                "hole_depth_mm": 45.0,
                "hole_diameter_mm": 3.175,  # 1/8" for ferrules
                "peck_drilling": True,
                "peck_depth_mm": 5.0,
                "dwell_ms": 100,
            },
            context={
                "feed_rate_mm_min": 100.0,
                "spindle_rpm": 2000,
                "safe_z_mm": 10.0,
                "retract_z_mm": 2.0,
            },
        )

    def test_adapter_and_feasibility_flow(self, string_through_intent):
        """Full flow from intent to feasibility check."""
        holes, config = drilling_params_from_intent(string_through_intent)

        feasibility = compute_drilling_feasibility(
            hole_depth_mm=config.hole_depth_mm,
            hole_diameter_mm=config.drill_diameter_mm,  # KEY: drill_diameter_mm
            peck_depth_mm=config.peck_depth_mm,
            peck_drilling=config.use_canned_cycle,
            feed_rate_mm_min=config.feed_rate,
            spindle_rpm=config.spindle_rpm,
            safe_z_mm=config.safe_z_mm,
            retract_z_mm=config.retract_z_mm,
            hole_count=len(holes),
            dwell_ms=config.dwell_ms,
        )

        # 45mm depth / 3.175mm diameter = 14.2 ratio > 10
        assert feasibility.feasible is True
        assert any("depth/diameter ratio" in w for w in feasibility.warnings)
        assert feasibility.summary["hole_count"] == 6

    def test_gcode_generation_from_intent(self, string_through_intent):
        """Generate G-code from intent."""
        from app.cam.drilling import PeckDrill

        holes, config = drilling_params_from_intent(string_through_intent)
        drill = PeckDrill(holes=holes, config=config)
        result = drill.generate()

        assert result.hole_count == 6
        assert result.estimated_time_seconds > 0
        assert "G83" in result.gcode  # Peck drilling cycle
        assert "string_1" in result.gcode  # Labels preserved
