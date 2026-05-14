"""
Tests for RMOS Artifact Persistence (CAM Dev Order 6F)

Tests the optional RMOS artifact persistence for Export Objects
and lifecycle reports.

Core rule: Artifact persistence only, not run orchestration.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.cam.dxf_translator_boundary import DXFTranslatorProfile
from app.cam.export_lifecycle_orchestrator import (
    GovernedExportLifecycleRequest,
    PreviewRequestWrapper,
    run_governed_export_lifecycle,
)
from app.cam.export_rmos_artifacts import (
    RMOSPersistenceResult,
    RMOSArtifactRef,
    EXPORT_OBJECT_KIND,
    LIFECYCLE_REPORT_KIND,
    generate_export_run_id,
    persist_export_lifecycle_artifacts,
    create_empty_persistence_result,
)
from app.cam.postprocessor_boundary import MachineProfileValidationOnly


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_valid_preview_request() -> PreviewRequestWrapper:
    """Create a valid nut slot preview request wrapper."""
    return PreviewRequestWrapper(
        operation="nut_slot",
        payload={
            "nut_width_mm": 50.0,
            "num_strings": 6,
            "edge_offset_bass_mm": 4.0,
            "edge_offset_treble_mm": 4.0,
            "slot_length_mm": 4.5,
            "slot_depth_mm": 1.5,
            "slot_width_mm": 0.70,
            "stock_thickness_mm": 9.5,
            "tool_diameter_mm": 0.56,
            "safe_z_mm": 5.0,
        },
    )


def create_compatible_machine_profile() -> MachineProfileValidationOnly:
    """Create a compatible machine profile."""
    return MachineProfileValidationOnly(
        machine_profile_id="test_3axis_cnc",
        controller="none",
        units="mm",
        supported_operations=["nut_slot", "pocket", "drill"],
        axis_count=3,
        work_envelope_mm={"x": 300, "y": 300, "z": 50},
    )


def create_compatible_translator_profile() -> DXFTranslatorProfile:
    """Create a compatible translator profile."""
    return DXFTranslatorProfile(
        translator_id="dxf_r12",  # 7C: Use registered translator ID
        supported_geometry_types=["line", "polyline", "arc", "circle"],
        supports_layers=True,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


def create_lifecycle_request(persist: bool = False) -> GovernedExportLifecycleRequest:
    """Create a full lifecycle request."""
    return GovernedExportLifecycleRequest(
        preview_request=create_valid_preview_request(),
        machine_profile=create_compatible_machine_profile(),
        translator_profile=create_compatible_translator_profile(),
        persist_to_rmos=persist,
    )


# -----------------------------------------------------------------------------
# Run ID Generation Tests
# -----------------------------------------------------------------------------

class TestRunIdGeneration:
    """Tests for export run ID generation."""

    def test_run_id_has_correct_prefix(self):
        """Run ID starts with RUN-EXPORT-."""
        run_id = generate_export_run_id()
        assert run_id.startswith("RUN-EXPORT-")

    def test_run_id_is_unique(self):
        """Each run ID is unique."""
        ids = [generate_export_run_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_run_id_has_uuid_suffix(self):
        """Run ID has a UUID hex suffix."""
        run_id = generate_export_run_id()
        suffix = run_id.replace("RUN-EXPORT-", "")
        assert len(suffix) == 32  # UUID hex is 32 chars


# -----------------------------------------------------------------------------
# Default Behavior Tests (No Persistence)
# -----------------------------------------------------------------------------

class TestDefaultNoPersistence:
    """Tests verifying default behavior is no persistence."""

    def test_default_request_does_not_persist(self):
        """Default request (no flag) does not persist."""
        request = create_lifecycle_request(persist=False)
        report = run_governed_export_lifecycle(request)

        assert report.rmos is not None
        assert report.rmos.persisted is False
        assert report.rmos.run_id is None
        assert len(report.rmos.artifacts) == 0

    def test_persist_false_does_not_persist(self):
        """Explicit persist_to_rmos=false does not persist."""
        request = create_lifecycle_request(persist=False)
        report = run_governed_export_lifecycle(request)

        assert report.rmos.persisted is False

    def test_empty_persistence_result(self):
        """create_empty_persistence_result returns correct structure."""
        result = create_empty_persistence_result()

        assert result.persisted is False
        assert result.run_id is None
        assert result.artifacts == []


# -----------------------------------------------------------------------------
# Persistence Tests (with mocking)
# -----------------------------------------------------------------------------

class TestRMOSPersistence:
    """Tests for RMOS artifact persistence."""

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_persist_true_returns_persisted_true(self, mock_put):
        """persist_to_rmos=true returns rmos.persisted=true."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,  # 64-char sha256
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        assert report.rmos is not None
        assert report.rmos.persisted is True

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_run_id_present_when_persisted(self, mock_put):
        """run_id is present when persisted."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        assert report.rmos.run_id is not None
        assert report.rmos.run_id.startswith("RUN-EXPORT-")

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_export_object_artifact_present(self, mock_put):
        """Export object artifact is present when persisted."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        artifact_kinds = [a.kind for a in report.rmos.artifacts]
        assert EXPORT_OBJECT_KIND in artifact_kinds

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_lifecycle_report_artifact_present(self, mock_put):
        """Lifecycle report artifact is present when persisted."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        artifact_kinds = [a.kind for a in report.rmos.artifacts]
        assert LIFECYCLE_REPORT_KIND in artifact_kinds

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_artifact_has_sha256(self, mock_put):
        """Artifacts have sha256 hash."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        for artifact in report.rmos.artifacts:
            assert artifact.sha256 is not None
            assert len(artifact.sha256) == 64

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_artifact_has_bytes(self, mock_put):
        """Artifacts have byte size."""
        mock_put.return_value = (
            MagicMock(size_bytes=1234),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        for artifact in report.rmos.artifacts:
            assert artifact.bytes > 0


# -----------------------------------------------------------------------------
# RED Lifecycle Tests
# -----------------------------------------------------------------------------

class TestRedLifecyclePersistence:
    """Tests for RED lifecycle persistence behavior."""

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_red_lifecycle_persists_report_only(self, mock_put):
        """RED lifecycle persists lifecycle report only, not export object."""
        mock_put.return_value = (
            MagicMock(size_bytes=500),
            "/fake/path",
            "def456" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        request.preview_request.operation = "unsupported_op"

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert report.rmos.persisted is True

        artifact_kinds = [a.kind for a in report.rmos.artifacts]
        assert LIFECYCLE_REPORT_KIND in artifact_kinds
        assert EXPORT_OBJECT_KIND not in artifact_kinds

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_red_lifecycle_no_export_object_artifact(self, mock_put):
        """RED lifecycle does not create export object artifact."""
        mock_put.return_value = (
            MagicMock(size_bytes=500),
            "/fake/path",
            "def456" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        request.preview_request.operation = "unsupported_op"

        report = run_governed_export_lifecycle(request)

        # Two artifacts: lifecycle report + audit ledger (6K), but no export object
        assert len(report.rmos.artifacts) == 2
        artifact_kinds = [a.kind for a in report.rmos.artifacts]
        assert LIFECYCLE_REPORT_KIND in artifact_kinds
        assert EXPORT_OBJECT_KIND not in artifact_kinds


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestNoMachineOutput:
    """Tests verifying no machine output is generated or persisted."""

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_machine_output_generated_always_false(self, mock_put):
        """machine_output_generated remains false even with persistence."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        assert report.machine_output_generated is False

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_translator_output_generated_always_false(self, mock_put):
        """translator_output_generated remains false even with persistence."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        assert report.translator_output_generated is False

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_machine_ready_always_false(self, mock_put):
        """machine_ready remains false even with persistence."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        assert report.machine_ready is False


# -----------------------------------------------------------------------------
# Artifact Content Safety Tests
# -----------------------------------------------------------------------------

class TestArtifactContentSafety:
    """Tests verifying no G-code/DXF tokens in persisted artifacts."""

    def test_persist_function_receives_valid_json(self):
        """persist_export_lifecycle_artifacts receives valid JSON dicts."""
        export_obj = {"export_id": "test", "geometry": {}, "toolpaths": {}}
        lifecycle_report = {"lifecycle_gate": "green", "export_ready": True}

        with patch("app.cam.export_rmos_artifacts.put_json_attachment") as mock_put:
            mock_put.return_value = (
                MagicMock(size_bytes=100),
                "/fake/path",
                "0" * 64,
            )

            result = persist_export_lifecycle_artifacts(export_obj, lifecycle_report)

            # Check that put_json_attachment was called with dicts
            calls = mock_put.call_args_list
            assert len(calls) == 2

            for call in calls:
                obj = call[1]["obj"]
                # Should be JSON-serializable
                json.dumps(obj)

    def test_lifecycle_report_dict_has_no_gcode_tokens(self):
        """Lifecycle report dict doesn't contain G-code tokens."""
        request = create_lifecycle_request(persist=False)
        report = run_governed_export_lifecycle(request)

        # Serialize to check content
        report_json = report.model_dump_json()

        forbidden_tokens = ["G0 ", "G1 ", "G2 ", "G3 ", "M3 ", "M5 "]
        for token in forbidden_tokens:
            assert token not in report_json, f"Found forbidden token: {token}"

    def test_lifecycle_report_dict_has_no_dxf_tokens(self):
        """Lifecycle report dict doesn't contain DXF tokens."""
        request = create_lifecycle_request(persist=False)
        report = run_governed_export_lifecycle(request)

        report_json = report.model_dump_json()

        # DXF section markers
        forbidden_tokens = ['"SECTION"', '"ENTITIES"', '"EOF"']
        for token in forbidden_tokens:
            assert token not in report_json, f"Found forbidden DXF token: {token}"


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestEndpointPersistence:
    """Tests for endpoint RMOS persistence."""

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_endpoint_with_persist_true(self, mock_put):
        """Endpoint returns RMOS data when persist_to_rmos=true."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rmos"]["persisted"] is True
        assert data["rmos"]["run_id"] is not None

    def test_endpoint_without_persist_flag(self):
        """Endpoint returns rmos.persisted=false without flag."""
        request = create_lifecycle_request(persist=False)

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rmos"]["persisted"] is False
        assert data["rmos"]["run_id"] is None

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_endpoint_rmos_block_structure(self, mock_put):
        """Endpoint RMOS block has correct structure."""
        mock_put.return_value = (
            MagicMock(size_bytes=1234),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_lifecycle_request(persist=True)

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        data = response.json()
        rmos = data["rmos"]

        assert "persisted" in rmos
        assert "run_id" in rmos
        assert "artifacts" in rmos
        assert isinstance(rmos["artifacts"], list)

        for artifact in rmos["artifacts"]:
            assert "kind" in artifact
            assert "sha256" in artifact
            assert "bytes" in artifact
