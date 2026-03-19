"""
Tests for Electronics Physical Layout Calculator (CONSTRUCTION-008)
"""

import pytest
from fastapi.testclient import TestClient

from app.calculators.electronics_layout_calc import (
    compute_pickup_cavity,
    compute_control_layout,
    check_cavity_clearance,
    compute_shielding_area,
    list_pickup_types,
    list_switch_types,
    list_jack_types,
    list_body_styles,
    CavitySpec,
    PICKUP_CAVITY_SPECS,
)
from app.main import app

client = TestClient(app)


# ─── Unit Tests ───────────────────────────────────────────────────────────────

class TestPickupCavity:
    """Tests for compute_pickup_cavity function."""

    def test_humbucker_cavity_dimensions(self):
        """Humbucker cavity should be 50×40×45mm."""
        spec = compute_pickup_cavity(
            pickup_type="humbucker",
            position="bridge",
            body_thickness_mm=45.0,
        )
        assert spec.length_mm == 50.0
        assert spec.width_mm == 40.0
        assert spec.depth_mm == 45.0
        assert spec.component == "humbucker"

    def test_single_coil_cavity_dimensions(self):
        """Single coil cavity should be 90×15×45mm."""
        spec = compute_pickup_cavity(
            pickup_type="single_coil",
            position="neck",
            body_thickness_mm=45.0,
        )
        assert spec.length_mm == 90.0
        assert spec.width_mm == 15.0
        assert spec.depth_mm == 45.0

    def test_p90_cavity_dimensions(self):
        """P90 cavity should be 90×50×45mm."""
        spec = compute_pickup_cavity(
            pickup_type="p90",
            position="bridge",
            body_thickness_mm=45.0,
        )
        assert spec.length_mm == 90.0
        assert spec.width_mm == 50.0
        assert spec.depth_mm == 45.0

    def test_mini_humbucker_cavity_dimensions(self):
        """Mini humbucker cavity should be 67×34×40mm."""
        spec = compute_pickup_cavity(
            pickup_type="mini_humbucker",
            position="neck",
            body_thickness_mm=45.0,
        )
        assert spec.length_mm == 67.0
        assert spec.width_mm == 34.0
        assert spec.depth_mm == 40.0

    def test_pickup_position_varies_by_body_style(self):
        """Pickup position should differ between body styles."""
        strat = compute_pickup_cavity("single_coil", "bridge", body_style="stratocaster")
        tele = compute_pickup_cavity("single_coil", "bridge", body_style="telecaster")
        # Both should have different positions
        assert strat.position_y_mm != tele.position_y_mm

    def test_green_gate_for_adequate_clearance(self):
        """Adequate body thickness should produce GREEN gate."""
        spec = compute_pickup_cavity(
            pickup_type="humbucker",
            position="bridge",
            body_thickness_mm=55.0,  # 55 - 45 = 10mm clearance
        )
        assert spec.gate == "GREEN"

    def test_red_gate_for_thin_body(self):
        """Very thin body should produce RED gate (breakthrough risk)."""
        spec = compute_pickup_cavity(
            pickup_type="humbucker",
            position="bridge",
            body_thickness_mm=46.0,  # 46 - 45 = 1mm clearance
        )
        assert spec.gate == "RED"


class TestControlLayout:
    """Tests for compute_control_layout function."""

    def test_returns_three_cavities(self):
        """Control layout should return control, switch, and jack cavities."""
        cavities = compute_control_layout(
            pot_count=4,
            switch_type="3way_toggle",
            jack_type="side",
            body_style="les_paul",
        )
        assert len(cavities) == 3
        components = [c.component for c in cavities]
        assert "control" in components
        assert any("switch" in c for c in components)
        assert any("jack" in c for c in components)

    def test_control_cavity_adjusts_for_pot_count(self):
        """Control cavity length should increase with pot count."""
        small = compute_control_layout(pot_count=2, body_style="les_paul")
        large = compute_control_layout(pot_count=6, body_style="les_paul")
        # Control cavity is first in list
        small_control = [c for c in small if c.component == "control"][0]
        large_control = [c for c in large if c.component == "control"][0]
        assert large_control.length_mm >= small_control.length_mm

    def test_shielding_area_included_in_notes(self):
        """Control cavity notes should include shielding area."""
        cavities = compute_control_layout(pot_count=4, body_style="les_paul")
        control = [c for c in cavities if c.component == "control"][0]
        assert any("Shielding area" in note for note in control.notes)


class TestCavityClearance:
    """Tests for check_cavity_clearance function."""

    def test_green_for_all_adequate(self):
        """All adequate clearances should return GREEN."""
        cavities = [
            CavitySpec(
                component="test",
                length_mm=50.0,
                width_mm=40.0,
                depth_mm=35.0,  # 45 - 35 = 10mm clearance
                position_x_mm=0.0,
                position_y_mm=25.0,
                clearance_mm=3.0,
                gate="GREEN",
                notes=[],
            )
        ]
        result = check_cavity_clearance(cavities, body_thickness_mm=45.0)
        assert result == "GREEN"

    def test_red_for_breakthrough_risk(self):
        """Breakthrough risk should return RED."""
        cavities = [
            CavitySpec(
                component="test",
                length_mm=50.0,
                width_mm=40.0,
                depth_mm=44.0,  # 45 - 44 = 1mm clearance
                position_x_mm=0.0,
                position_y_mm=25.0,
                clearance_mm=3.0,
                gate="RED",
                notes=[],
            )
        ]
        result = check_cavity_clearance(cavities, body_thickness_mm=45.0)
        assert result == "RED"


class TestShieldingArea:
    """Tests for compute_shielding_area function."""

    def test_shielding_area_calculation(self):
        """Shielding area should include floor and walls."""
        cavities = [
            CavitySpec(
                component="test",
                length_mm=100.0,
                width_mm=50.0,
                depth_mm=20.0,
                position_x_mm=0.0,
                position_y_mm=0.0,
                clearance_mm=3.0,
                gate="GREEN",
                notes=[],
            )
        ]
        area = compute_shielding_area(cavities)
        # Floor: 100 × 50 = 5000
        # Walls: 2 × (100 + 50) × 20 = 6000
        # Total: 11000
        assert area == 11000.0


class TestListFunctions:
    """Tests for list functions."""

    def test_list_pickup_types_has_expected_types(self):
        """Pickup types list should include standard pickups."""
        types = list_pickup_types()
        assert "humbucker" in types
        assert "single_coil" in types
        assert "p90" in types
        assert len(types) >= 7

    def test_list_switch_types_has_expected_types(self):
        """Switch types list should include standard switches."""
        types = list_switch_types()
        assert "3way_toggle" in types
        assert "5way_blade" in types
        assert "rotary" in types

    def test_list_jack_types_has_expected_types(self):
        """Jack types list should include standard jacks."""
        types = list_jack_types()
        assert "side" in types
        assert "top" in types
        assert "endpin" in types


# ─── API Endpoint Tests ───────────────────────────────────────────────────────

class TestElectronicsLayoutEndpoint:
    """Tests for POST /api/instrument/electronics-layout endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.post(
            "/api/instrument/electronics-layout",
            json={
                "pickups": [
                    {"pickup_type": "humbucker", "position": "bridge"},
                    {"pickup_type": "humbucker", "position": "neck"},
                ],
                "pot_count": 4,
                "switch_type": "3way_toggle",
                "jack_type": "side",
                "body_style": "les_paul",
            },
        )
        assert response.status_code == 200

    def test_endpoint_returns_complete_layout(self):
        """Response should include pickup and control cavities."""
        response = client.post(
            "/api/instrument/electronics-layout",
            json={
                "pickups": [
                    {"pickup_type": "single_coil", "position": "bridge"},
                    {"pickup_type": "single_coil", "position": "middle"},
                    {"pickup_type": "single_coil", "position": "neck"},
                ],
                "pot_count": 3,
                "switch_type": "5way_blade",
                "body_style": "stratocaster",
            },
        )
        data = response.json()
        assert "pickup_cavities" in data
        assert "control_cavities" in data
        assert "overall_gate" in data
        assert "total_shielding_area_mm2" in data
        assert len(data["pickup_cavities"]) == 3
        assert len(data["control_cavities"]) == 3  # control + switch + jack


class TestPickupCavityEndpoint:
    """Tests for POST /api/instrument/electronics-layout/pickup-cavity endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.post(
            "/api/instrument/electronics-layout/pickup-cavity",
            json={"pickup_type": "humbucker", "position": "bridge"},
        )
        assert response.status_code == 200

    def test_endpoint_returns_cavity_spec(self):
        """Response should include cavity specification."""
        response = client.post(
            "/api/instrument/electronics-layout/pickup-cavity",
            json={
                "pickup_type": "p90",
                "position": "neck",
                "body_thickness_mm": 50.0,
            },
        )
        data = response.json()
        assert "cavity" in data
        assert data["cavity"]["component"] == "p90"
        assert data["cavity"]["length_mm"] == 90.0
        assert data["cavity"]["width_mm"] == 50.0


class TestControlLayoutEndpoint:
    """Tests for POST /api/instrument/electronics-layout/control-layout endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.post(
            "/api/instrument/electronics-layout/control-layout",
            json={"pot_count": 4, "body_style": "les_paul"},
        )
        assert response.status_code == 200

    def test_endpoint_returns_multiple_cavities(self):
        """Response should include control, switch, and jack cavities."""
        response = client.post(
            "/api/instrument/electronics-layout/control-layout",
            json={
                "pot_count": 2,
                "switch_type": "3way_toggle",
                "jack_type": "side",
                "body_style": "telecaster",
            },
        )
        data = response.json()
        assert "cavities" in data
        assert len(data["cavities"]) == 3
        assert "shielding_area_mm2" in data


class TestElectronicsOptionsEndpoint:
    """Tests for GET /api/instrument/electronics-layout/options endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.get("/api/instrument/electronics-layout/options")
        assert response.status_code == 200

    def test_endpoint_returns_all_option_lists(self):
        """Response should include all option lists."""
        response = client.get("/api/instrument/electronics-layout/options")
        data = response.json()
        assert "pickup_types" in data
        assert "switch_types" in data
        assert "jack_types" in data
        assert "body_styles" in data
        assert len(data["pickup_types"]) >= 7
        assert len(data["switch_types"]) >= 3
        assert len(data["jack_types"]) >= 3
