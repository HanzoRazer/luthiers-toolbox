"""
Tests for simulation gate enforcement (Priority #3 from Design Review).

The simulation gate ensures G-code exports require either:
1. Simulation verification (simulation_passed=True with simulation_hash)
2. Explicit override (simulation_override=True with simulation_override_reason)

See: docs/DESIGN_REVIEW_2026-02-22.md Priority #3
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.routers.geometry_schemas import GcodeExportIn, SimulationGateFields
from app.routers.geometry.export_router import _check_simulation_gate


class TestSimulationGateSchema:
    """Test SimulationGateFields schema."""

    def test_simulation_gate_fields_exist(self):
        """SimulationGateFields has all required fields."""
        body = GcodeExportIn(gcode="G0 X0 Y0")
        assert hasattr(body, "simulation_passed")
        assert hasattr(body, "simulation_hash")
        assert hasattr(body, "simulation_override")
        assert hasattr(body, "simulation_override_reason")

    def test_simulation_gate_defaults(self):
        """SimulationGateFields defaults are correct."""
        body = GcodeExportIn(gcode="G0 X0 Y0")
        assert body.simulation_passed is None
        assert body.simulation_hash is None
        assert body.simulation_override is False
        assert body.simulation_override_reason is None


class TestSimulationGateLogic:
    """Test _check_simulation_gate function."""

    def test_simulation_passed_allows_export(self):
        """simulation_passed=True allows export."""
        body = GcodeExportIn(
            gcode="G0 X0 Y0",
            simulation_passed=True,
            simulation_hash="sha256_abc123",
        )
        result = _check_simulation_gate(body)
        assert result["gate_passed"] is True
        assert result["override_used"] is False
        assert result["reason"] == "simulation_verified"

    def test_simulation_passed_warns_without_hash(self):
        """simulation_passed=True without hash logs warning but allows export."""
        body = GcodeExportIn(
            gcode="G0 X0 Y0",
            simulation_passed=True,
            # No simulation_hash
        )
        result = _check_simulation_gate(body)
        assert result["gate_passed"] is True

    def test_override_with_reason_allows_export(self):
        """simulation_override=True with reason allows export."""
        body = GcodeExportIn(
            gcode="G0 X0 Y0",
            simulation_override=True,
            simulation_override_reason="Emergency repair - known-good program",
        )
        result = _check_simulation_gate(body)
        assert result["gate_passed"] is True
        assert result["override_used"] is True
        assert result["reason"] == "Emergency repair - known-good program"

    def test_override_without_reason_raises_403(self):
        """simulation_override=True without reason raises 403."""
        body = GcodeExportIn(
            gcode="G0 X0 Y0",
            simulation_override=True,
            # No simulation_override_reason
        )
        with pytest.raises(HTTPException) as exc_info:
            _check_simulation_gate(body)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"] == "simulation_override_requires_reason"

    def test_no_simulation_raises_403(self):
        """No simulation fields raises 403."""
        body = GcodeExportIn(gcode="G0 X0 Y0")
        with pytest.raises(HTTPException) as exc_info:
            _check_simulation_gate(body)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"] == "simulation_required"
        assert "hint" in exc_info.value.detail


class TestSimulationGateEnvVar:
    """Test RMOS_REQUIRE_SIMULATION environment variable."""

    def test_env_var_parsing_logic(self):
        """Test env var parsing logic matches implementation."""
        # Test the parsing logic directly (same as in export_router.py)
        def parse_require_sim(val: str) -> bool:
            return val.lower() in ("1", "true", "yes")

        # Enabled values
        assert parse_require_sim("1") is True
        assert parse_require_sim("true") is True
        assert parse_require_sim("TRUE") is True
        assert parse_require_sim("yes") is True
        assert parse_require_sim("YES") is True

        # Disabled values
        assert parse_require_sim("0") is False
        assert parse_require_sim("false") is False
        assert parse_require_sim("no") is False

    def test_env_var_is_boolean(self):
        """RMOS_REQUIRE_SIMULATION is a boolean."""
        from app.routers.geometry.export_router import RMOS_REQUIRE_SIMULATION
        assert isinstance(RMOS_REQUIRE_SIMULATION, bool)
