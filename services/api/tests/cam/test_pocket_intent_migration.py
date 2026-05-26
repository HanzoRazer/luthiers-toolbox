"""
Pocketing Intent Migration Tests (8J)

Tests for:
- Adapter mapping (stepover_percent -> fraction)
- Feasibility validation (geometric validity checks)
- Integration tests
"""
import pytest
from unittest.mock import patch, MagicMock

from app.cam.pocketing import (
    PocketDesignV1,
    pocket_params_from_intent,
)
from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1

# Conditional import for shapely-dependent tests
try:
    from app.cam.pocketing.feasibility import (
        compute_pocket_feasibility,
        compute_pocket_area,
        hash_feasibility_result,
    )
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    compute_pocket_feasibility = None
    compute_pocket_area = None
    hash_feasibility_result = None

requires_shapely = pytest.mark.skipif(
    not SHAPELY_AVAILABLE,
    reason="shapely not available (numpy compatibility issue)"
)


class TestPocketParamsFromIntent:
    """Tests for pocket_params_from_intent adapter."""

    @pytest.fixture
    def minimal_intent(self):
        """Minimal valid CamIntentV1 for pocketing."""
        return CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "boundary": [
                    {"x": 0, "y": 0},
                    {"x": 100, "y": 0},
                    {"x": 100, "y": 60},
                    {"x": 0, "y": 60},
                ],
                "pocket_depth_mm": 10.0,
                "tool_diameter_mm": 6.0,
                "stepover_percent": 50.0,
            },
            context={
                "stepdown_mm": 3.0,
                "feed_rate_mm_min": 1500.0,
                "plunge_rate_mm_min": 500.0,
                "safe_z_mm": 10.0,
                "retract_z_mm": 5.0,
            },
        )

    def test_stepover_percent_converts_to_fraction(self, minimal_intent):
        """
        Adapter test: stepover_percent / 100 -> stepover fraction.

        L.1 expects stepover as fraction 0.3-0.7.
        Schema uses percent 30-70 for user clarity.
        """
        adaptation = pocket_params_from_intent(minimal_intent)

        # KEY ASSERTION: 50% -> 0.5 fraction
        assert adaptation.stepover == 0.5

    def test_boundary_mapped_to_loops(self, minimal_intent):
        """Boundary is first element of loops."""
        adaptation = pocket_params_from_intent(minimal_intent)

        assert len(adaptation.loops) >= 1
        assert len(adaptation.loops[0]) == 4  # 4-point boundary
        assert adaptation.loops[0][0] == (0.0, 0.0)

    def test_tool_diameter_mapped(self, minimal_intent):
        """Tool diameter maps to tool_d."""
        adaptation = pocket_params_from_intent(minimal_intent)
        assert adaptation.tool_d == 6.0

    def test_context_parameters_mapped(self, minimal_intent):
        """Context parameters map correctly."""
        adaptation = pocket_params_from_intent(minimal_intent)

        assert adaptation.stepdown == 3.0
        assert adaptation.feed_xy == 1500.0
        assert adaptation.plunge_rate == 500.0
        assert adaptation.safe_z == 10.0
        assert adaptation.retract_z == 5.0

    def test_defaults_applied(self):
        """Defaults applied when context omits values."""
        intent = CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "boundary": [
                    {"x": 0, "y": 0},
                    {"x": 50, "y": 0},
                    {"x": 25, "y": 40},
                ],
                "pocket_depth_mm": 5.0,
                "tool_diameter_mm": 3.0,
            },
            context={},  # Empty context
        )
        adaptation = pocket_params_from_intent(intent)

        # Defaults from adapter
        assert adaptation.stepdown == 3.0
        assert adaptation.margin == 0.0
        assert adaptation.strategy == "Spiral"
        assert adaptation.smoothing_radius == 0.5
        assert adaptation.feed_xy == 1500.0

    def test_islands_mapped_to_loops(self):
        """Islands become loops[1:]."""
        intent = CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "boundary": [
                    {"x": 0, "y": 0},
                    {"x": 100, "y": 0},
                    {"x": 100, "y": 80},
                    {"x": 0, "y": 80},
                ],
                "islands": [
                    {
                        "boundary": [
                            {"x": 20, "y": 20},
                            {"x": 40, "y": 20},
                            {"x": 30, "y": 40},
                        ]
                    },
                    {
                        "boundary": [
                            {"x": 60, "y": 20},
                            {"x": 80, "y": 20},
                            {"x": 70, "y": 40},
                        ]
                    },
                ],
                "pocket_depth_mm": 10.0,
                "tool_diameter_mm": 6.0,
            },
            context={},
        )
        adaptation = pocket_params_from_intent(intent)

        assert len(adaptation.loops) == 3  # boundary + 2 islands
        assert len(adaptation.loops[1]) == 3  # First island
        assert len(adaptation.loops[2]) == 3  # Second island


@requires_shapely
class TestPocketFeasibility:
    """Tests for pocketing feasibility check."""

    @pytest.fixture
    def valid_boundary(self):
        """Valid rectangular boundary."""
        return [(0, 0), (100, 0), (100, 60), (0, 60)]

    @pytest.fixture
    def valid_island(self):
        """Valid island within boundary."""
        return [(30, 20), (50, 20), (40, 40)]

    def test_valid_pocket_low_risk(self, valid_boundary):
        """Valid configuration with no warnings returns low risk."""
        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is True
        assert result.risk_level == "low"
        assert len(result.issues) == 0

    def test_self_intersecting_boundary_blocks(self):
        """Self-intersecting boundary is a blocking issue."""
        # Figure-8 shape (self-intersecting)
        boundary = [(0, 0), (100, 100), (100, 0), (0, 100)]

        result = compute_pocket_feasibility(
            boundary=boundary,
            islands=[],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is False
        assert result.risk_level == "blocked"
        assert any("boundary" in i.lower() and "valid" in i.lower() for i in result.issues)

    def test_self_intersecting_island_blocks(self, valid_boundary):
        """Self-intersecting island is a blocking issue."""
        # Figure-8 island
        bad_island = [(30, 20), (50, 40), (50, 20), (30, 40)]

        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[bad_island],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is False
        assert result.risk_level == "blocked"
        assert any("island 0" in i.lower() for i in result.issues)

    def test_island_outside_boundary_blocks(self, valid_boundary):
        """Island outside boundary is a blocking issue."""
        # Island completely outside boundary
        outside_island = [(200, 200), (220, 200), (210, 220)]

        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[outside_island],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is False
        assert result.risk_level == "blocked"
        assert any("island" in i.lower() and ("outside" in i.lower() or "within" in i.lower()) for i in result.issues)

    def test_overlapping_islands_blocks(self, valid_boundary):
        """Overlapping islands is a blocking issue."""
        island1 = [(30, 20), (50, 20), (40, 40)]
        island2 = [(35, 25), (55, 25), (45, 45)]  # Overlaps with island1

        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[island1, island2],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is False
        assert result.risk_level == "blocked"
        assert any("overlap" in i.lower() for i in result.issues)

    def test_valid_island_within_boundary(self, valid_boundary, valid_island):
        """Valid island within boundary passes."""
        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[valid_island],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is True
        assert len(result.issues) == 0

    def test_stepover_out_of_l1_range_blocks(self, valid_boundary):
        """Stepover outside L.1 range is blocking."""
        # Below 30%
        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=20.0,  # Below L.1 minimum
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is False
        assert any("stepover" in i.lower() and "30%" in i for i in result.issues)

    def test_aggressive_stepover_warns(self, valid_boundary):
        """Stepover > 60% triggers warning."""
        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=65.0,  # Above 60% threshold
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is True
        assert any("aggressive" in w.lower() or "scallop" in w.lower() for w in result.warnings)

    def test_deep_pocket_ratio_warns(self, valid_boundary):
        """Deep pocket (depth/diameter > 3) triggers warning."""
        result = compute_pocket_feasibility(
            boundary=valid_boundary,
            islands=[],
            pocket_depth_mm=30.0,  # 30mm depth
            tool_diameter_mm=6.0,  # 6mm tool = ratio 5
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )

        assert result.feasible is True
        assert any("deep" in w.lower() for w in result.warnings)


@requires_shapely
class TestComputePocketArea:
    """Tests for pocket area computation."""

    def test_simple_rectangle(self):
        """Simple rectangle area."""
        boundary = [(0, 0), (100, 0), (100, 60), (0, 60)]
        area = compute_pocket_area(boundary, [])

        assert abs(area - 6000.0) < 1.0  # 100 x 60 = 6000

    def test_rectangle_with_triangular_island(self):
        """Rectangle minus triangular island."""
        boundary = [(0, 0), (100, 0), (100, 60), (0, 60)]
        # Triangle with base 20, height 20 -> area 200
        island = [(30, 20), (50, 20), (40, 40)]

        area = compute_pocket_area(boundary, [island])

        # 6000 - 200 = 5800
        assert abs(area - 5800.0) < 1.0


@requires_shapely
class TestHashFeasibilityResult:
    """Tests for feasibility result hashing."""

    def test_hash_is_64_chars(self):
        """Hash must be full 64-char SHA256."""
        result = compute_pocket_feasibility(
            boundary=[(0, 0), (100, 0), (100, 60), (0, 60)],
            islands=[],
            pocket_depth_mm=10.0,
            tool_diameter_mm=6.0,
            stepover_percent=40.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=500.0,
            safe_z_mm=10.0,
            retract_z_mm=5.0,
            stepdown_mm=3.0,
            finish_allowance_mm=0.25,
        )
        hash_val = hash_feasibility_result(result)

        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_hash_deterministic(self):
        """Same input produces same hash."""
        def make_result():
            return compute_pocket_feasibility(
                boundary=[(0, 0), (100, 0), (100, 60), (0, 60)],
                islands=[],
                pocket_depth_mm=10.0,
                tool_diameter_mm=6.0,
                stepover_percent=40.0,
                feed_rate_mm_min=1500.0,
                plunge_rate_mm_min=500.0,
                safe_z_mm=10.0,
                retract_z_mm=5.0,
                stepdown_mm=3.0,
                finish_allowance_mm=0.25,
            )

        hash1 = hash_feasibility_result(make_result())
        hash2 = hash_feasibility_result(make_result())

        assert hash1 == hash2


@requires_shapely
class TestPocketingIntentIntegration:
    """Integration tests for full intent -> feasibility flow."""

    @pytest.fixture
    def control_cavity_intent(self):
        """Control cavity pocketing intent (guitar body)."""
        return CamIntentV1(
            mode=CamModeV1.ROUTER_3AXIS,
            design={
                "boundary": [
                    {"x": 0, "y": 0},
                    {"x": 60, "y": 0},
                    {"x": 60, "y": 95},
                    {"x": 0, "y": 95},
                ],
                "islands": [],
                "pocket_depth_mm": 35.0,
                "tool_diameter_mm": 6.35,  # 1/4"
                "stepover_percent": 50.0,
            },
            context={
                "stepdown_mm": 5.0,
                "feed_rate_mm_min": 2500.0,
                "plunge_rate_mm_min": 600.0,
                "safe_z_mm": 10.0,
                "retract_z_mm": 2.0,
                "strategy": "Spiral",
            },
        )

    def test_adapter_and_feasibility_flow(self, control_cavity_intent):
        """Full flow from intent to feasibility check."""
        adaptation = pocket_params_from_intent(control_cavity_intent)

        # Verify stepover conversion
        assert adaptation.stepover == 0.5  # 50% -> 0.5

        # Run feasibility
        feasibility = compute_pocket_feasibility(
            boundary=adaptation.loops[0],
            islands=adaptation.loops[1:] if len(adaptation.loops) > 1 else [],
            pocket_depth_mm=adaptation.pocket_depth_mm,
            tool_diameter_mm=adaptation.tool_d,
            stepover_percent=adaptation.stepover * 100,
            feed_rate_mm_min=adaptation.feed_xy,
            plunge_rate_mm_min=adaptation.plunge_rate,
            safe_z_mm=adaptation.safe_z,
            retract_z_mm=adaptation.retract_z,
            stepdown_mm=adaptation.stepdown,
            finish_allowance_mm=adaptation.finish_allowance_mm,
        )

        assert feasibility.feasible is True
        # 35mm depth / 6.35mm tool = 5.5 ratio > 3 -> deep pocket warning
        assert any("deep" in w.lower() for w in feasibility.warnings)

    def test_pocket_area_computed_after_validation(self, control_cavity_intent):
        """Pocket area in summary after geometric validation."""
        adaptation = pocket_params_from_intent(control_cavity_intent)

        feasibility = compute_pocket_feasibility(
            boundary=adaptation.loops[0],
            islands=[],
            pocket_depth_mm=adaptation.pocket_depth_mm,
            tool_diameter_mm=adaptation.tool_d,
            stepover_percent=adaptation.stepover * 100,
            feed_rate_mm_min=adaptation.feed_xy,
            plunge_rate_mm_min=adaptation.plunge_rate,
            safe_z_mm=adaptation.safe_z,
            retract_z_mm=adaptation.retract_z,
            stepdown_mm=adaptation.stepdown,
            finish_allowance_mm=adaptation.finish_allowance_mm,
        )

        # 60 x 95 = 5700 mm²
        assert abs(feasibility.summary["pocket_area_mm2"] - 5700.0) < 1.0
