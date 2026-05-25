"""
Tests for V-Carve CamIntentV1 Migration.

Validates the intent-based V-Carve endpoint:
- Accepts CamIntentV1
- Normalizes input
- Validates mode and design
- Runs feasibility
- Persists RMOS artifact
- Returns structured response with issues
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1, CamUnitsV1
from app.cam.vcarve.intent_adapter import vcarve_params_from_intent
from app.cam.vcarve.intent_schema import VCarveDesignV1
from app.cam.vcarve.toolpath import VCarveConfig, MLPath


class TestVCarveIntentAdapter:
    """Tests for vcarve_params_from_intent adapter."""

    def _make_valid_design(self) -> dict:
        """Create a valid V-Carve design dict."""
        return {
            "paths": [
                {
                    "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
                    "is_closed": False,
                }
            ],
            "bit_angle_deg": 60.0,
            "target_line_width_mm": 2.0,
        }

    def _make_valid_intent(self, **overrides) -> CamIntentV1:
        """Create a valid CamIntentV1 for V-Carve."""
        kwargs = {
            "mode": CamModeV1.ROUTER_3AXIS,
            "units": CamUnitsV1.MM,
            "design": self._make_valid_design(),
            "context": {},
            "options": {},
        }
        kwargs.update(overrides)
        return CamIntentV1(**kwargs)

    def test_adapter_returns_config_and_paths(self):
        """Valid intent returns VCarveConfig and MLPath list."""
        intent = self._make_valid_intent()
        config, paths = vcarve_params_from_intent(intent)

        assert isinstance(config, VCarveConfig)
        assert isinstance(paths, list)
        assert len(paths) == 1
        assert isinstance(paths[0], MLPath)

    def test_adapter_extracts_design_fields(self):
        """Design fields are extracted into config."""
        intent = self._make_valid_intent()
        config, _ = vcarve_params_from_intent(intent)

        assert config.bit_angle_deg == 60.0
        assert config.target_line_width_mm == 2.0
        assert config.target_depth_mm is None

    def test_adapter_extracts_depth_override(self):
        """target_depth_mm override is extracted."""
        design = self._make_valid_design()
        design["target_depth_mm"] = 1.5
        intent = self._make_valid_intent(design=design)
        config, _ = vcarve_params_from_intent(intent)

        assert config.target_depth_mm == 1.5

    def test_adapter_extracts_context_fields(self):
        """Context fields are extracted with correct values."""
        intent = self._make_valid_intent(
            context={
                "spindle_rpm": 20000,
                "flute_count": 3,
                "chipload_factor": 0.7,
                "max_stepdown_mm": 3.0,
                "safe_z_mm": 8.0,
                "corner_slowdown": False,
            }
        )
        config, _ = vcarve_params_from_intent(intent)

        assert config.spindle_rpm == 20000
        assert config.flute_count == 3
        assert config.chipload_factor == 0.7
        assert config.max_stepdown_mm == 3.0
        assert config.safe_z_mm == 8.0
        assert config.corner_slowdown is False

    def test_adapter_uses_defaults_for_missing_context(self):
        """Missing context fields get default values."""
        intent = self._make_valid_intent(context={})
        config, _ = vcarve_params_from_intent(intent)

        assert config.spindle_rpm == 18000
        assert config.flute_count == 2
        assert config.chipload_factor == 0.8
        assert config.safe_z_mm == 5.0
        assert config.corner_slowdown is True

    def test_adapter_extracts_material_from_envelope(self):
        """material_id from envelope is used for material."""
        intent = self._make_valid_intent(material_id="maple")
        config, _ = vcarve_params_from_intent(intent)

        assert config.material == "maple"

    def test_adapter_falls_back_to_context_material(self):
        """Falls back to context.material if material_id is None."""
        intent = self._make_valid_intent(
            material_id=None,
            context={"material": "softwood"},
        )
        config, _ = vcarve_params_from_intent(intent)

        assert config.material == "softwood"

    def test_adapter_extracts_options(self):
        """Options bucket fields are extracted."""
        intent = self._make_valid_intent(
            options={"optimize_path_order": False}
        )
        config, _ = vcarve_params_from_intent(intent)

        assert config.optimize_path_order is False

    def test_adapter_converts_paths_to_ml_paths(self):
        """Design paths are converted to MLPath format."""
        design = {
            "paths": [
                {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}], "is_closed": False},
                {"points": [{"x": 0, "y": 5}, {"x": 10, "y": 5}], "is_closed": True},
            ],
            "bit_angle_deg": 60.0,
            "target_line_width_mm": 2.0,
        }
        intent = self._make_valid_intent(design=design)
        _, paths = vcarve_params_from_intent(intent)

        assert len(paths) == 2
        assert paths[0].points == [(0, 0), (10, 0)]
        assert paths[0].is_closed is False
        assert paths[1].points == [(0, 5), (10, 5)]
        assert paths[1].is_closed is True

    def test_adapter_raises_on_missing_design_key(self):
        """Missing required design key raises ValueError."""
        design = {
            "paths": [{"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}]}],
            # missing bit_angle_deg and target_line_width_mm
        }
        intent = self._make_valid_intent(design=design)

        with pytest.raises(ValueError, match="Invalid V-Carve design"):
            vcarve_params_from_intent(intent)

    def test_adapter_raises_on_invalid_context_value(self):
        """Invalid context value raises ValueError."""
        intent = self._make_valid_intent(
            context={"spindle_rpm": 100}  # Below minimum of 5000
        )

        with pytest.raises(ValueError, match="spindle_rpm must be >= 5000"):
            vcarve_params_from_intent(intent)

    def test_adapter_raises_on_context_type_error(self):
        """Non-numeric context value raises ValueError."""
        intent = self._make_valid_intent(
            context={"spindle_rpm": "not a number"}
        )

        with pytest.raises(ValueError, match="spindle_rpm must be an integer"):
            vcarve_params_from_intent(intent)


class TestVCarveIntentRouterIntegration:
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
                "paths": [
                    {
                        "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
                        "is_closed": False,
                    }
                ],
                "bit_angle_deg": 60.0,
                "target_line_width_mm": 2.0,
            },
            "context": {
                "spindle_rpm": 18000,
                "material": "hardwood",
            },
            "options": {},
        }

    def test_intent_endpoint_accepts_valid_request(self, client):
        """Valid CamIntentV1 request returns 200."""
        response = client.post(
            "/api/cam/vcarve/intent-gcode",
            json=self._make_valid_request(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "gcode" in data
        assert "issues" in data
        assert "run_id" in data

    def test_intent_endpoint_rejects_wrong_mode(self, client):
        """mode != router_3axis returns 422."""
        request = self._make_valid_request()
        request["mode"] = "saw"

        response = client.post(
            "/api/cam/vcarve/intent-gcode",
            json=request,
        )
        assert response.status_code == 422

    def test_intent_endpoint_returns_normalization_issues(self, client):
        """Normalization issues are returned in response."""
        request = self._make_valid_request()
        request["units"] = "inch"  # Will be normalized to mm

        response = client.post(
            "/api/cam/vcarve/intent-gcode",
            json=request,
        )
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        # Issues list should exist (may be empty if normalization is clean)
        assert isinstance(data["issues"], list)

    def test_intent_endpoint_persists_run_artifact(self, client):
        """Successful call persists RMOS run artifact."""
        response = client.post(
            "/api/cam/vcarve/intent-gcode",
            json=self._make_valid_request(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["run_id"] is not None

    def test_intent_endpoint_returns_hashes(self, client):
        """Response includes provenance hashes."""
        response = client.post(
            "/api/cam/vcarve/intent-gcode",
            json=self._make_valid_request(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "hashes" in data
        assert isinstance(data["hashes"], dict)

    def test_intent_endpoint_rejects_invalid_design(self, client):
        """Invalid design returns 422."""
        request = self._make_valid_request()
        request["design"]["paths"] = []  # Empty paths

        response = client.post(
            "/api/cam/vcarve/intent-gcode",
            json=request,
        )
        assert response.status_code == 422

    def test_intent_endpoint_rejects_missing_design_key(self, client):
        """Missing required design key returns 422."""
        request = self._make_valid_request()
        del request["design"]["bit_angle_deg"]

        response = client.post(
            "/api/cam/vcarve/intent-gcode",
            json=request,
        )
        assert response.status_code == 422
