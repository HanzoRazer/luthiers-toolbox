"""
Test Fret Slots Preview Normalization (Dev Order 5C)

Verifies that the fret_slots/preview endpoint returns governed preview
standard fields alongside legacy fields for frontend compatibility.

Reference: CAM_PREVIEW_CONTRACT_STANDARD.md
Canonical pattern: nut_slot_cam.py
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestGovernedPreviewFields:
    """Verify governed preview standard fields are present."""

    def test_response_has_operation_field(self):
        """operation field identifies the preview type."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "operation" in data
        assert data["operation"] == "fret_slot_preview"

    def test_response_has_status_field(self):
        """status field is always 'preview' for governed preview."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "status" in data
        assert data["status"] == "preview"

    def test_response_has_gate_field(self):
        """gate field indicates preview safety (green/yellow/red)."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "gate" in data
        assert data["gate"] in ["green", "yellow", "red"]

    def test_response_has_units_field(self):
        """units field is always 'mm'."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "units" in data
        assert data["units"] == "mm"

    def test_response_has_coordinate_system(self):
        """coordinate_system provides spatial reference metadata."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "coordinate_system" in data
        cs = data["coordinate_system"]
        assert cs["units"] == "mm"
        assert cs["origin"] == "nut_edge"
        assert "x_axis" in cs
        assert "y_axis" in cs
        assert "z_axis" in cs
        assert "z_zero" in cs

    def test_response_has_canonical_toolpath(self):
        """canonical_toolpath wraps the preview geometry."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "canonical_toolpath" in data
        ct = data["canonical_toolpath"]
        assert "slots" in ct
        assert "slot_count" in ct
        assert ct["slot_count"] == len(ct["slots"])

    def test_response_has_warnings_list(self):
        """warnings is a list of warning message strings."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "warnings" in data
        assert isinstance(data["warnings"], list)

    def test_response_has_errors_list(self):
        """errors is a list of error message strings."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "errors" in data
        assert isinstance(data["errors"], list)

    def test_response_has_issues_list(self):
        """issues contains structured CamIssue objects."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_response_has_metadata(self):
        """metadata provides generator provenance."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "metadata" in data
        meta = data["metadata"]
        assert meta["generator_id"] == "fret_slots_cam"
        assert meta["preview_only"] is True
        assert meta["machine_ready"] is False
        assert "generated_at" in meta


class TestLegacyFieldsPreserved:
    """Verify legacy fields are preserved for frontend compatibility."""

    def test_legacy_model_id_preserved(self):
        """model_id field preserved."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "strat_25_5",
            "fret_count": 22,
        })
        data = resp.json()
        assert "model_id" in data
        assert data["model_id"] == "strat_25_5"

    def test_legacy_fret_count_preserved(self):
        """fret_count field preserved."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 24,
        })
        data = resp.json()
        assert "fret_count" in data
        assert data["fret_count"] == 24

    def test_legacy_slots_preserved(self):
        """slots array preserved with expected structure."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "slots" in data
        assert isinstance(data["slots"], list)
        if data["slots"]:
            slot = data["slots"][0]
            assert "fret" in slot
            assert "positionMm" in slot
            assert "widthMm" in slot
            assert "depthMm" in slot

    def test_legacy_messages_preserved(self):
        """messages array preserved with RmosMessageOut structure."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_legacy_statistics_preserved(self):
        """statistics dict preserved."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "statistics" in data
        assert isinstance(data["statistics"], dict)


class TestGateDerivation:
    """Verify gate is correctly derived from messages."""

    def test_gate_green_when_no_errors_or_warnings(self):
        """Gate is green when no issues present."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "strat_25_5",
            "fret_count": 22,
            "slot_width_mm": 0.58,
            "bit_diameter_mm": 0.58,
            "slot_depth_mm": 3.0,
        })
        data = resp.json()
        has_warnings = any(m["severity"] == "warning" for m in data["messages"])
        has_errors = any(m["severity"] == "error" for m in data["messages"])
        if not has_warnings and not has_errors:
            assert data["gate"] == "green"

    def test_gate_yellow_when_warning_present(self):
        """Gate is yellow when warning is present."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "nonexistent_model_xyz",
            "fret_count": 22,
        })
        data = resp.json()
        has_warnings = any(m["severity"] == "warning" for m in data["messages"])
        if has_warnings:
            assert data["gate"] in ["yellow", "red"]

    def test_gate_yellow_when_bit_too_large(self):
        """Gate is yellow when bit diameter exceeds slot width."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "slot_width_mm": 0.5,
            "bit_diameter_mm": 2.0,  # Much larger than slot
        })
        data = resp.json()
        bit_warning = any(
            m["code"] == "BIT_TOO_LARGE" and m["severity"] == "warning"
            for m in data["messages"]
        )
        if bit_warning:
            assert data["gate"] in ["yellow", "red"]

    def test_warnings_list_matches_messages(self):
        """warnings list contains messages with severity='warning'."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "nonexistent_model_for_warning",
            "fret_count": 22,
        })
        data = resp.json()
        warning_messages = [m["message"] for m in data["messages"] if m["severity"] == "warning"]
        assert data["warnings"] == warning_messages


class TestStatisticsNormalization:
    """Verify statistics include required core fields."""

    def test_statistics_has_operation_count(self):
        """operation_count is present in normalized statistics."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "operation_count" in data["statistics"]

    def test_statistics_has_move_count(self):
        """move_count is present in normalized statistics."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "move_count" in data["statistics"]

    def test_statistics_has_warning_count(self):
        """warning_count is present in normalized statistics."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "warning_count" in data["statistics"]

    def test_statistics_has_error_count(self):
        """error_count is present in normalized statistics."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "error_count" in data["statistics"]

    def test_statistics_preserves_legacy_fields(self):
        """Legacy statistics fields like slot_count are preserved."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert "slot_count" in data["statistics"]


class TestIssuesStructure:
    """Verify issues array has correct structure."""

    def test_issues_have_code_field(self):
        """Each issue has a code field."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "nonexistent_model_for_issue",
            "fret_count": 22,
        })
        data = resp.json()
        for issue in data["issues"]:
            assert "code" in issue

    def test_issues_have_severity_field(self):
        """Each issue has severity in green/yellow/red."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "nonexistent_model_for_issue",
            "fret_count": 22,
        })
        data = resp.json()
        for issue in data["issues"]:
            assert "severity" in issue
            assert issue["severity"] in ["green", "yellow", "red"]

    def test_issues_have_message_field(self):
        """Each issue has a message field."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "nonexistent_model_for_issue",
            "fret_count": 22,
        })
        data = resp.json()
        for issue in data["issues"]:
            assert "message" in issue


class TestCoordinateSystemDocumentation:
    """Verify coordinate system accurately reflects actual behavior."""

    def test_coordinate_origin_is_nut_edge(self):
        """Origin is at nut edge per fret_slots_cam.py behavior."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert data["coordinate_system"]["origin"] == "nut_edge"

    def test_z_zero_is_top_of_fretboard(self):
        """Z-zero is at top of fretboard (cutting goes negative)."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert data["coordinate_system"]["z_zero"] == "top_of_fretboard"

    def test_coordinate_units_are_mm(self):
        """Coordinate system uses millimeters."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
        })
        data = resp.json()
        assert data["coordinate_system"]["units"] == "mm"


class TestFanFretMode:
    """Verify normalization works for fan-fret mode."""

    def test_fan_fret_mode_has_governed_fields(self):
        """Fan-fret preview includes governed preview fields."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
            "bass_scale_mm": 686.0,
            "treble_scale_mm": 648.0,
            "perpendicular_fret": 7,
        })
        data = resp.json()
        assert "operation" in data
        assert "gate" in data
        assert "coordinate_system" in data

    def test_fan_fret_canonical_toolpath_has_mode(self):
        """canonical_toolpath includes mode field."""
        resp = client.post("/api/cam/fret_slots/preview", json={
            "model_id": "test_model",
            "fret_count": 22,
            "mode": "fan_fret",
        })
        data = resp.json()
        assert data["canonical_toolpath"]["mode"] == "fan_fret"
