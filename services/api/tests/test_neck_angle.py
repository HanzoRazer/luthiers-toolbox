"""
Tests for neck angle calculator (GEOMETRY-001).

Canonical module: app.instrument_geometry.neck.neck_angle
"""
import pytest

from app.instrument_geometry.neck.fret_math import compute_fret_to_bridge_mm
from app.instrument_geometry.neck.neck_angle import (
    NeckAngleInput,
    NeckAngleResult,
    compute_neck_angle,
)


# Gibson 24.75" scale, 14th fret joint
SCALE_GIBSON_MM = 24.75 * 25.4  # 628.65
BODY_LENGTH_14 = compute_fret_to_bridge_mm(SCALE_GIBSON_MM, 14)  # ~374 mm


class TestNeckAngleStandardGeometry:
    """Standard Gibson-style geometry → 1.5–2.5° GREEN."""

    def test_gibson_geometry_green(self):
        """Typical Gibson geometry yields angle in GREEN range (1.0°–3.5°)."""
        inp = NeckAngleInput(
            bridge_height_mm=15.0,
            saddle_projection_mm=3.0,
            fretboard_height_at_joint_mm=4.95,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
            action_12th_mm=2.0,
        )
        result = compute_neck_angle(inp)
        assert result.gate == "GREEN"
        assert 1.0 <= result.angle_deg <= 3.5
        assert "normal range" in result.message.lower()

    def test_gibson_1_5_deg_green(self):
        """~1.5° still GREEN."""
        # tan(1.5°) * L ≈ 9.8 mm
        inp = NeckAngleInput(
            bridge_height_mm=14.0,
            saddle_projection_mm=2.5,
            fretboard_height_at_joint_mm=6.7,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        result = compute_neck_angle(inp)
        assert result.gate == "GREEN"
        assert 1.0 <= result.angle_deg <= 3.5


class TestNeckAngleFlatRed:
    """Flat neck (e.g. 0.3°) → RED."""

    def test_flat_neck_red(self):
        """Angle < 0.5° → RED, too flat."""
        # ~0.3°: tan(0.3°) * L ≈ 1.96 mm
        inp = NeckAngleInput(
            bridge_height_mm=8.0,
            saddle_projection_mm=2.0,
            fretboard_height_at_joint_mm=8.04,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        result = compute_neck_angle(inp)
        assert result.gate == "RED"
        assert result.angle_deg < 0.5
        assert "flat" in result.message.lower() or "reset" in result.message.lower()


class TestNeckAngleSteepRed:
    """Steep neck (e.g. 6°) → RED."""

    def test_steep_neck_red(self):
        """Angle > 5° → RED, too steep."""
        # ~6°: tan(6°) * L ≈ 39.2 mm
        inp = NeckAngleInput(
            bridge_height_mm=25.0,
            saddle_projection_mm=18.0,
            fretboard_height_at_joint_mm=3.8,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        result = compute_neck_angle(inp)
        assert result.gate == "RED"
        assert result.angle_deg > 5.0
        assert "steep" in result.message.lower()


class TestNeckAngleErrorSensitivity:
    """0.5° error sensitivity (BACKLOG: ~2.6 mm over 300 mm)."""

    def test_half_degree_height_sensitivity(self):
        """Rough check: small height change produces ~0.5° angle change."""
        # Baseline ~2°
        inp0 = NeckAngleInput(
            bridge_height_mm=15.0,
            saddle_projection_mm=3.0,
            fretboard_height_at_joint_mm=4.95,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        r0 = compute_neck_angle(inp0)
        # Lower saddle by ~2 mm → angle drops
        inp1 = NeckAngleInput(
            bridge_height_mm=15.0,
            saddle_projection_mm=1.0,
            fretboard_height_at_joint_mm=4.95,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        r1 = compute_neck_angle(inp1)
        delta_deg = r0.angle_deg - r1.angle_deg
        assert delta_deg > 0.3  # At least ~0.3° per 2 mm on this scale
        assert delta_deg < 0.6  # Roughly in 0.5° ballpark for ~2 mm


class TestNeckAngleYellow:
    """YELLOW gate: marginal flat or steep."""

    def test_yellow_flat(self):
        """0.5° <= θ < 1.0° → YELLOW (too flat)."""
        # ~0.7°
        inp = NeckAngleInput(
            bridge_height_mm=10.0,
            saddle_projection_mm=2.5,
            fretboard_height_at_joint_mm=7.95,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        result = compute_neck_angle(inp)
        assert result.gate == "YELLOW"
        assert 0.5 <= result.angle_deg < 1.0

    def test_yellow_steep(self):
        """3.5° < θ <= 5° → YELLOW (steep)."""
        # ~4°
        inp = NeckAngleInput(
            bridge_height_mm=18.0,
            saddle_projection_mm=6.0,
            fretboard_height_at_joint_mm=2.0,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        result = compute_neck_angle(inp)
        assert result.gate == "YELLOW"
        assert 3.5 < result.angle_deg <= 5.0


class TestNeckAngleEdgeCases:
    """Joint fret and result fields."""

    def test_12th_fret_join_different_angle(self):
        """12th fret join yields different body length and angle than 14th."""
        base = NeckAngleInput(
            bridge_height_mm=15.0,
            saddle_projection_mm=3.0,
            fretboard_height_at_joint_mm=5.0,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        r14 = compute_neck_angle(base)
        inp12 = NeckAngleInput(
            bridge_height_mm=base.bridge_height_mm,
            saddle_projection_mm=base.saddle_projection_mm,
            fretboard_height_at_joint_mm=base.fretboard_height_at_joint_mm,
            nut_to_bridge_mm=base.nut_to_bridge_mm,
            neck_joint_fret=12,
        )
        r12 = compute_neck_angle(inp12)
        assert r12.angle_deg != r14.angle_deg

    def test_saddle_height_required_in_result(self):
        """Result includes saddle_height_required_mm (from input saddle projection)."""
        inp = NeckAngleInput(
            bridge_height_mm=15.0,
            saddle_projection_mm=3.5,
            fretboard_height_at_joint_mm=5.0,
            nut_to_bridge_mm=SCALE_GIBSON_MM,
            neck_joint_fret=14,
        )
        result = compute_neck_angle(inp)
        assert result.saddle_height_required_mm == 3.5


# =============================================================================
# API ENDPOINT
# =============================================================================

class TestNeckAngleEndpoint:
    """POST /api/neck/angle integration."""

    def test_angle_endpoint_returns_angle_and_gate(self, client):
        """POST /api/neck/angle returns angle_deg, gate, message, saddle_height_required_mm."""
        response = client.post(
            "/api/neck/angle",
            json={
                "bridge_height_mm": 15.0,
                "saddle_projection_mm": 3.0,
                "fretboard_height_at_joint_mm": 5.0,
                "nut_to_bridge_mm": SCALE_GIBSON_MM,
                "neck_joint_fret": 14,
                "action_12th_mm": 2.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "angle_deg" in data
        assert "gate" in data
        assert data["gate"] in ("GREEN", "YELLOW", "RED")
        assert "message" in data
        assert "saddle_height_required_mm" in data
        assert data["saddle_height_required_mm"] == 3.0

    def test_angle_endpoint_defaults(self, client):
        """POST /api/neck/angle accepts optional neck_joint_fret and action_12th_mm."""
        response = client.post(
            "/api/neck/angle",
            json={
                "bridge_height_mm": 14.0,
                "saddle_projection_mm": 2.5,
                "fretboard_height_at_joint_mm": 6.0,
                "nut_to_bridge_mm": SCALE_GIBSON_MM,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "angle_deg" in data
        assert "gate" in data
