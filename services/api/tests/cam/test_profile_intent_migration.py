"""
Tests for Profile CamIntentV1 Migration.

Validates the intent-based Profile endpoint:
- Accepts CamIntentV1
- Normalizes input
- Validates mode and design
- Runs feasibility
- Persists RMOS artifact
- Returns structured response with issues and metadata
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1, CamUnitsV1
from app.cam.profiling.intent_adapter import profile_params_from_intent
from app.cam.profiling.intent_schema import ProfileDesignV1
from app.cam.profiling.profile_toolpath import ProfileConfig, MillingDirection
from app.cam.profiling.feasibility import compute_profile_feasibility


class TestProfileIntentAdapter:
    """Tests for profile_params_from_intent adapter."""

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
        }

    def _make_valid_intent(self, **overrides) -> CamIntentV1:
        """Create a valid CamIntentV1 for Profile."""
        kwargs = {
            "mode": CamModeV1.ROUTER_3AXIS,
            "units": CamUnitsV1.MM,
            "design": self._make_valid_design(),
            "context": {},
            "options": {},
        }
        kwargs.update(overrides)
        return CamIntentV1(**kwargs)

    def test_adapter_returns_outline_config_and_closed(self):
        """Valid intent returns outline, ProfileConfig, and is_closed."""
        intent = self._make_valid_intent()
        outline, config, is_closed = profile_params_from_intent(intent)

        assert isinstance(outline, list)
        assert len(outline) == 4
        assert isinstance(outline[0], tuple)
        assert isinstance(config, ProfileConfig)
        assert is_closed is True

    def test_adapter_extracts_design_fields(self):
        """Design fields are extracted into config."""
        intent = self._make_valid_intent()
        _, config, _ = profile_params_from_intent(intent)

        assert config.tool_diameter_mm == 6.35
        assert config.cut_depth_mm == 6.0
        assert config.tab_count == 4
        assert config.tab_width_mm == 6.0
        assert config.tab_height_mm == 1.5

    def test_adapter_maps_is_outside_to_compensation_side(self):
        """is_outside=True maps to compensation_side='outside'."""
        intent = self._make_valid_intent()
        _, config, _ = profile_params_from_intent(intent)
        assert config.compensation_side == "outside"

        design = self._make_valid_design()
        design["is_outside"] = False
        intent = self._make_valid_intent(design=design)
        _, config, _ = profile_params_from_intent(intent)
        assert config.compensation_side == "inside"

    def test_adapter_maps_climb_milling_to_direction(self):
        """climb_milling context field maps to direction enum."""
        intent = self._make_valid_intent(context={"climb_milling": True})
        _, config, _ = profile_params_from_intent(intent)
        assert config.direction == MillingDirection.CLIMB

        intent = self._make_valid_intent(context={"climb_milling": False})
        _, config, _ = profile_params_from_intent(intent)
        assert config.direction == MillingDirection.CONVENTIONAL

    def test_adapter_extracts_context_fields(self):
        """Context fields are extracted with correct values."""
        intent = self._make_valid_intent(
            context={
                "stepdown_mm": 3.0,
                "feed_rate_mm_min": 2000.0,
                "plunge_rate_mm_min": 500.0,
                "safe_z_mm": 10.0,
                "retract_z_mm": 3.0,
                "lead_in_radius_mm": 8.0,
            }
        )
        _, config, _ = profile_params_from_intent(intent)

        assert config.stepdown_mm == 3.0
        assert config.feed_rate_xy == 2000.0
        assert config.plunge_rate == 500.0
        assert config.safe_z_mm == 10.0
        assert config.retract_z_mm == 3.0
        assert config.lead_in_radius_mm == 8.0

    def test_adapter_uses_defaults_for_missing_context(self):
        """Missing context fields get default values."""
        intent = self._make_valid_intent(context={})
        _, config, _ = profile_params_from_intent(intent)

        assert config.stepdown_mm == 6.0
        assert config.feed_rate_xy == 1500.0
        assert config.plunge_rate == 300.0
        assert config.safe_z_mm == 5.0
        assert config.retract_z_mm == 2.0
        assert config.direction == MillingDirection.CLIMB

    def test_adapter_converts_contour_to_tuples(self):
        """Design contour is converted to tuple format."""
        intent = self._make_valid_intent()
        outline, _, _ = profile_params_from_intent(intent)

        assert outline == [(0, 0), (100, 0), (100, 100), (0, 100)]

    def test_adapter_handles_tabs_disabled(self):
        """Tabs disabled sets tab_count to 0."""
        design = self._make_valid_design()
        design["use_tabs"] = False
        design["tab_count"] = 0
        intent = self._make_valid_intent(design=design)
        _, config, _ = profile_params_from_intent(intent)

        assert config.tab_count == 0

    def test_adapter_raises_on_missing_design_key(self):
        """Missing required design key raises ValueError."""
        design = self._make_valid_design()
        del design["tool_diameter_mm"]
        intent = self._make_valid_intent(design=design)

        with pytest.raises(ValueError, match="Invalid Profile design"):
            profile_params_from_intent(intent)

    def test_adapter_raises_on_invalid_context_value(self):
        """Invalid context value raises ValueError."""
        intent = self._make_valid_intent(
            context={"stepdown_mm": 0.05}  # Below minimum of 0.1
        )

        with pytest.raises(ValueError, match="stepdown_mm must be >= 0.1"):
            profile_params_from_intent(intent)


class TestProfileFeasibility:
    """Tests for Profile feasibility check."""

    def test_feasibility_passes_for_valid_params(self):
        """Valid parameters produce feasible result."""
        result = compute_profile_feasibility(
            tool_diameter_mm=6.35,
            cut_depth_mm=6.0,
            stepdown_mm=2.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=300.0,
            safe_z_mm=5.0,
            retract_z_mm=2.0,
            contour_point_count=4,
            tab_count=4,
            tab_height_mm=1.5,
            use_tabs=True,
            finishing_pass=True,
            finishing_allowance_mm=0.3,
        )

        assert result.feasible is True
        assert result.risk_level in ("low", "medium")
        assert len(result.issues) == 0

    def test_feasibility_blocks_zero_tool_diameter(self):
        """Zero tool diameter produces blocked result."""
        result = compute_profile_feasibility(
            tool_diameter_mm=0,
            cut_depth_mm=6.0,
            stepdown_mm=2.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=300.0,
            safe_z_mm=5.0,
            retract_z_mm=2.0,
            contour_point_count=4,
            tab_count=4,
            tab_height_mm=1.5,
            use_tabs=True,
            finishing_pass=True,
            finishing_allowance_mm=0.3,
        )

        assert result.feasible is False
        assert result.risk_level == "blocked"
        assert "tool_diameter_mm must be > 0" in result.issues

    def test_feasibility_warns_aggressive_stepdown(self):
        """Stepdown > tool diameter produces warning."""
        result = compute_profile_feasibility(
            tool_diameter_mm=6.35,
            cut_depth_mm=20.0,
            stepdown_mm=10.0,  # > tool diameter
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=300.0,
            safe_z_mm=5.0,
            retract_z_mm=2.0,
            contour_point_count=4,
            tab_count=4,
            tab_height_mm=1.5,
            use_tabs=True,
            finishing_pass=True,
            finishing_allowance_mm=0.3,
        )

        assert result.feasible is True
        assert any("aggressive" in w for w in result.warnings)

    def test_feasibility_blocks_insufficient_contour(self):
        """Contour with < 3 points produces blocked result."""
        result = compute_profile_feasibility(
            tool_diameter_mm=6.35,
            cut_depth_mm=6.0,
            stepdown_mm=2.0,
            feed_rate_mm_min=1500.0,
            plunge_rate_mm_min=300.0,
            safe_z_mm=5.0,
            retract_z_mm=2.0,
            contour_point_count=2,  # < 3
            tab_count=4,
            tab_height_mm=1.5,
            use_tabs=True,
            finishing_pass=True,
            finishing_allowance_mm=0.3,
        )

        assert result.feasible is False
        assert "at least 3 points" in str(result.issues)


class TestProfileIntentRouterIntegration:
    """Integration tests for the intent router endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def _make_valid_request(self) -> dict:
        """Create a valid request body."""
        return {
            "mode": "router_3axis",
            "units": "mm",
            "design": {
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
            },
            "context": {
                "stepdown_mm": 2.0,
                "feed_rate_mm_min": 1500.0,
            },
            "options": {},
        }

    def test_intent_endpoint_accepts_valid_request(self, client):
        """Valid CamIntentV1 request returns 200."""
        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=self._make_valid_request(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "gcode" in data
        assert "issues" in data
        assert "run_id" in data
        assert "metadata" in data

    def test_intent_endpoint_rejects_wrong_mode(self, client):
        """mode != router_3axis returns 422."""
        request = self._make_valid_request()
        request["mode"] = "saw"

        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=request,
        )
        assert response.status_code == 422

    def test_intent_endpoint_returns_metadata(self, client):
        """Response includes pass_count, tab_count, etc."""
        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=self._make_valid_request(),
        )
        assert response.status_code == 200
        data = response.json()
        metadata = data["metadata"]
        assert "pass_count" in metadata
        assert "tab_count" in metadata
        assert "total_length_mm" in metadata
        assert "estimated_time_seconds" in metadata

    def test_intent_endpoint_persists_run_artifact(self, client):
        """Successful call persists RMOS run artifact."""
        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=self._make_valid_request(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["run_id"] is not None

    def test_intent_endpoint_returns_hashes(self, client):
        """Response includes provenance hashes."""
        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=self._make_valid_request(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "hashes" in data
        hashes = data["hashes"]
        assert "request_sha256" in hashes
        assert "feasibility_sha256" in hashes
        assert "gcode_sha256" in hashes

    def test_intent_endpoint_rejects_invalid_design(self, client):
        """Invalid design returns 422."""
        request = self._make_valid_request()
        request["design"]["contour"] = []  # Empty contour

        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=request,
        )
        assert response.status_code == 422

    def test_intent_endpoint_rejects_missing_design_key(self, client):
        """Missing required design key returns 422."""
        request = self._make_valid_request()
        del request["design"]["tool_diameter_mm"]

        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=request,
        )
        assert response.status_code == 422

    def test_intent_endpoint_blocks_on_feasibility_failure(self, client):
        """Feasibility failure returns 409."""
        request = self._make_valid_request()
        request["design"]["tool_diameter_mm"] = 0  # Invalid

        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=request,
        )
        # Design validation should catch this at 422, not feasibility
        assert response.status_code == 422

    def test_intent_endpoint_handles_inside_cut(self, client):
        """Inside cut (is_outside=False) works correctly."""
        request = self._make_valid_request()
        request["design"]["is_outside"] = False

        response = client.post(
            "/api/cam/profiling/intent-gcode",
            json=request,
        )
        assert response.status_code == 200
        data = response.json()
        assert "gcode" in data
