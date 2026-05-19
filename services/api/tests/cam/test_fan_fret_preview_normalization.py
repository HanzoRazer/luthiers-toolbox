"""
Test Fan Fret Preview Normalization (Dev Order 5D)

Verifies that fan_fret mode returns governed preview standard fields,
uses the actual fan fret generator, and preserves legacy compatibility.

Reference: CAM_PREVIEW_CONTRACT_STANDARD.md
Canonical pattern: nut_slot_cam.py, fret_slots_cam (5C)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestFanFretGovernedPreviewFields:
    """Verify fan fret mode returns governed preview standard fields."""

    def test_fan_fret_has_operation_field(self):
        """operation field is 'fan_fret_preview' for fan fret mode."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
            "perpendicular_fret": 7,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["operation"] == "fan_fret_preview"

    def test_fan_fret_has_status_field(self):
        """status field is always 'preview'."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert data["status"] == "preview"

    def test_fan_fret_has_gate_field(self):
        """gate field indicates preview safety."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert "gate" in data
        assert data["gate"] in ["green", "yellow", "red"]

    def test_fan_fret_has_coordinate_system_with_notes(self):
        """coordinate_system includes fan-fret specific notes."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        cs = data["coordinate_system"]
        assert cs["units"] == "mm"
        assert cs["origin"] == "nut_edge"
        assert cs["notes"] is not None
        assert "angled" in cs["notes"].lower()
        assert cs["coordinate_confidence"] == "documented_from_current_code"

    def test_fan_fret_has_canonical_toolpath_with_scales(self):
        """canonical_toolpath includes fan fret scale lengths."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
            "perpendicular_fret": 9,
        })
        data = resp.json()
        ct = data["canonical_toolpath"]
        assert ct["mode"] == "fan_fret"
        assert ct["bass_scale_mm"] == 686.0
        assert ct["treble_scale_mm"] == 648.0
        assert ct["perpendicular_fret"] == 9

    def test_fan_fret_has_metadata_with_mode(self):
        """metadata includes mode field."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        meta = data["metadata"]
        assert meta["mode"] == "fan_fret"
        assert meta["generator_id"] == "fret_slots_fan_cam"
        assert meta["preview_only"] is True
        assert meta["machine_ready"] is False


class TestFanFretLegacyFieldsPreserved:
    """Verify legacy fields are preserved for fan fret mode."""

    def test_fan_fret_legacy_model_id(self):
        """model_id field preserved."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "multiscale_test",
            "fret_count": 24,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert data["model_id"] == "multiscale_test"

    def test_fan_fret_legacy_fret_count(self):
        """fret_count field preserved."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 24,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert data["fret_count"] == 24

    def test_fan_fret_legacy_slots_array(self):
        """slots array preserved with angle data."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert "slots" in data
        assert isinstance(data["slots"], list)
        if data["slots"]:
            slot = data["slots"][0]
            assert "fret" in slot
            assert "positionMm" in slot
            assert "angleRad" in slot

    def test_fan_fret_legacy_messages_array(self):
        """messages array preserved."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_fan_fret_legacy_statistics(self):
        """statistics dict preserved with fan-specific fields."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert "statistics" in data
        stats = data["statistics"]
        assert "operation_count" in stats
        assert "move_count" in stats


class TestFanFretGeneratorWiring:
    """Verify fan fret mode uses actual fan fret generator."""

    def test_fan_fret_generates_angled_slots(self):
        """Fan fret slots have non-zero angles (except perpendicular)."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
            "perpendicular_fret": 7,
        })
        data = resp.json()
        slots = data["slots"]
        if slots:
            angles = [s["angleRad"] for s in slots if s["angleRad"] is not None]
            non_zero_angles = [a for a in angles if abs(a) > 0.001]
            assert len(non_zero_angles) > 0, "Fan fret should have angled slots"

    def test_fan_fret_statistics_include_scale_lengths(self):
        """Fan fret statistics include bass and treble scale lengths."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        stats = data["statistics"]
        assert stats.get("bass_scale_mm") == 686.0
        assert stats.get("treble_scale_mm") == 648.0
        assert stats.get("mode") == "fan"

    def test_fan_fret_missing_params_returns_error(self):
        """Fan fret without scale lengths returns error gate."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
        })
        data = resp.json()
        assert data["gate"] == "red"
        assert any(m["code"] == "FAN_FRET_PARAMS_MISSING" for m in data["messages"])


class TestStandardModeUnchanged:
    """Verify standard mode still works correctly after 5D."""

    def test_standard_mode_operation_unchanged(self):
        """Standard mode still returns fret_slot_preview operation."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "standard",
        })
        data = resp.json()
        assert data["operation"] == "fret_slot_preview"

    def test_standard_mode_coordinate_system_no_notes(self):
        """Standard mode coordinate system has no fan-specific notes."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "standard",
        })
        data = resp.json()
        cs = data["coordinate_system"]
        assert cs["notes"] is None or "angled" not in (cs["notes"] or "").lower()

    def test_standard_mode_metadata_mode(self):
        """Standard mode metadata includes mode='standard'."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "standard",
        })
        data = resp.json()
        assert data["metadata"]["mode"] == "standard"
        assert data["metadata"]["generator_id"] == "fret_slots_cam"

    def test_default_mode_is_standard(self):
        """When mode is omitted, defaults to standard."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert data["operation"] == "fret_slot_preview"
        assert data["metadata"]["mode"] == "standard"


class TestFanFretGateInheritance:
    """Verify gate derivation works for fan fret mode."""

    def test_fan_fret_gate_green_on_success(self):
        """Fan fret with valid params returns green gate."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "strat_25_5",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
            "slot_width_mm": 0.58,
            "bit_diameter_mm": 0.58,
        })
        data = resp.json()
        has_errors = any(m["severity"] == "error" for m in data["messages"])
        has_warnings = any(m["severity"] == "warning" for m in data["messages"])
        if not has_errors and not has_warnings:
            assert data["gate"] == "green"

    def test_fan_fret_gate_yellow_on_warning(self):
        """Fan fret with warning returns yellow gate."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "nonexistent_model_xyz",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        has_warnings = any(m["severity"] == "warning" for m in data["messages"])
        has_errors = any(m["severity"] == "error" for m in data["messages"])
        if has_warnings and not has_errors:
            assert data["gate"] == "yellow"

    def test_fan_fret_gate_red_on_error(self):
        """Fan fret with error returns red gate."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            # Missing bass_scale_mm and treble_scale_mm
        })
        data = resp.json()
        assert data["gate"] == "red"


class TestFanFretStatisticsNormalization:
    """Verify statistics include required core fields for fan fret."""

    def test_fan_fret_statistics_has_operation_count(self):
        """operation_count present in fan fret statistics."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert "operation_count" in data["statistics"]

    def test_fan_fret_statistics_has_move_count(self):
        """move_count present in fan fret statistics."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        assert "move_count" in data["statistics"]

    def test_fan_fret_statistics_has_max_angle(self):
        """max_angle_deg present in fan fret statistics."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        stats = data["statistics"]
        assert "max_angle_deg" in stats
        assert stats["max_angle_deg"] >= 0


class TestFanFretIssuesStructure:
    """Verify issues array structure for fan fret mode."""

    def test_fan_fret_issues_have_correct_structure(self):
        """Issues have code, severity, message fields."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "nonexistent_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
        })
        data = resp.json()
        for issue in data["issues"]:
            assert "code" in issue
            assert "severity" in issue
            assert issue["severity"] in ["green", "yellow", "red"]
            assert "message" in issue
