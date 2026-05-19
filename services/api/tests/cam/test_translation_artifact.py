"""
Tests for Translation Artifact Model (CAM Dev Order 7D)

Tests the translation artifact contracts:
  - Artifact model with 7D invariants
  - Artifact class registry
  - Lifecycle integration
  - Safety assertions

Core rule: Artifacts are governed metadata contracts, not executable payloads.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.export_object import ExportObject
from app.cam.translation_artifact import (
    TranslationArtifact,
    TranslationArtifactSummary,
    ArtifactOutputClass,
    ArtifactState,
    build_validation_translation_artifact,
    build_artifact_summary_from_translator,
    compute_export_object_hash,
)
from app.cam.translation_artifact_registry import (
    ArtifactClassRegistration,
    TRANSLATION_ARTIFACT_CLASS_REGISTRY,
    get_artifact_class,
    list_artifact_classes,
    list_artifact_class_ids,
    get_artifact_classes_by_output,
    get_artifact_classes_by_category,
    artifact_class_exists,
    get_artifact_class_for_translator,
)
from app.cam.translator_capability_registry import get_translator_capability
from app.cam.nut_slot_cam import NutSlotPreviewRequest, generate_nut_slot_preview
from app.cam.nut_slot_export import create_nut_slot_export_object


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_valid_export_object() -> ExportObject:
    """Create a valid nut slot export object for testing."""
    request = NutSlotPreviewRequest(
        nut_width_mm=50.0,
        num_strings=6,
        edge_offset_bass_mm=4.0,
        edge_offset_treble_mm=4.0,
        slot_length_mm=4.5,
        slot_depth_mm=1.5,
        slot_width_mm=0.70,
        stock_thickness_mm=9.5,
        tool_diameter_mm=0.56,
        safe_z_mm=5.0,
    )
    preview = generate_nut_slot_preview(request)
    return create_nut_slot_export_object(preview, request)


# -----------------------------------------------------------------------------
# TranslationArtifact Model Tests
# -----------------------------------------------------------------------------

class TestTranslationArtifactModel:
    """Tests for TranslationArtifact model."""

    def test_artifact_created_with_valid_inputs(self):
        """Artifact can be created with valid inputs."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact is not None
        assert artifact.artifact_id.startswith("artifact-")
        assert artifact.translator_id == "dxf_r12"

    def test_artifact_state_validation_only(self):
        """Default artifact state is validation_only."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact.artifact_state == "validation_only"

    def test_7d_invariant_execution_supported_always_false(self):
        """execution_supported must be False (7D invariant)."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact.execution_supported is False

    def test_7d_invariant_executable_payload_present_always_false(self):
        """executable_payload_present must be False (7D invariant)."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact.executable_payload_present is False

    def test_7d_invariant_machine_output_present_always_false(self):
        """machine_output_present must be False (7D invariant)."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact.machine_output_present is False

    def test_artifact_violating_execution_supported_raises(self):
        """Creating artifact with execution_supported=True raises ValueError."""
        with pytest.raises(ValueError, match="execution_supported must be False"):
            TranslationArtifact(
                translator_id="test",
                translator_category="translator",
                output_class="dxf",
                source_export_object_id="test-id",
                source_export_object_hash="abc123",
                execution_supported=True,  # Violates 7D invariant
            )

    def test_artifact_violating_machine_output_raises(self):
        """Creating artifact with machine_output_present=True raises ValueError."""
        with pytest.raises(ValueError, match="machine_output_present must be False"):
            TranslationArtifact(
                translator_id="test",
                translator_category="translator",
                output_class="dxf",
                source_export_object_id="test-id",
                source_export_object_hash="abc123",
                machine_output_present=True,  # Violates 7D invariant
            )

    def test_artifact_has_source_hash(self):
        """Artifact contains source export object hash."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact.source_export_object_hash is not None
        assert len(artifact.source_export_object_hash) == 64  # SHA256 hex

    def test_artifact_has_capability_snapshot(self):
        """Artifact captures translator capability snapshot."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact.capability_snapshot is not None
        assert artifact.capability_snapshot.get("translator_id") == "dxf_r12"


# -----------------------------------------------------------------------------
# TranslationArtifactSummary Tests
# -----------------------------------------------------------------------------

class TestTranslationArtifactSummary:
    """Tests for TranslationArtifactSummary model."""

    def test_summary_from_artifact(self):
        """Summary can be created from full artifact."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )
        summary = artifact.to_summary()

        assert summary.artifact_id == artifact.artifact_id
        assert summary.translator_id == artifact.translator_id
        assert summary.output_class == artifact.output_class

    def test_summary_7d_invariants(self):
        """Summary maintains 7D invariants."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )
        summary = artifact.to_summary()

        assert summary.execution_supported is False
        assert summary.executable_payload_present is False
        assert summary.machine_output_present is False

    def test_summary_has_deterministic_hash(self):
        """Summary includes deterministic hash."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )
        summary = artifact.to_summary()

        assert summary.deterministic_hash is not None
        assert len(summary.deterministic_hash) == 64

    def test_build_summary_from_translator(self):
        """Summary can be built directly from translator ID."""
        export_obj = create_valid_export_object()

        summary = build_artifact_summary_from_translator(
            export_object=export_obj,
            translator_id="dxf_r12",
        )

        assert summary is not None
        assert summary.translator_id == "dxf_r12"

    def test_build_summary_unknown_translator_returns_none(self):
        """Unknown translator ID returns None."""
        export_obj = create_valid_export_object()

        summary = build_artifact_summary_from_translator(
            export_object=export_obj,
            translator_id="unknown_translator",
        )

        assert summary is None


# -----------------------------------------------------------------------------
# Artifact Class Registry Tests
# -----------------------------------------------------------------------------

class TestArtifactClassRegistry:
    """Tests for translation artifact class registry."""

    def test_registry_has_dxf_artifact_class(self):
        """Registry contains DXF validation artifact class."""
        assert "dxf_validation_artifact" in TRANSLATION_ARTIFACT_CLASS_REGISTRY

    def test_registry_has_svg_artifact_class(self):
        """Registry contains SVG validation artifact class."""
        assert "svg_validation_artifact" in TRANSLATION_ARTIFACT_CLASS_REGISTRY

    def test_registry_has_neutral_toolpath_artifact_class(self):
        """Registry contains neutral toolpath validation artifact class."""
        assert "neutral_toolpath_validation_artifact" in TRANSLATION_ARTIFACT_CLASS_REGISTRY

    def test_registry_has_gcode_artifact_class(self):
        """Registry contains G-code validation artifact class."""
        assert "gcode_validation_artifact" in TRANSLATION_ARTIFACT_CLASS_REGISTRY

    def test_all_artifact_classes_non_executable(self):
        """All registered artifact classes are non-executable."""
        for artifact_class in TRANSLATION_ARTIFACT_CLASS_REGISTRY.values():
            assert artifact_class.executable_output_supported is False

    def test_all_artifact_classes_no_machine_output(self):
        """All registered artifact classes have no machine output."""
        for artifact_class in TRANSLATION_ARTIFACT_CLASS_REGISTRY.values():
            assert artifact_class.machine_output_supported is False

    def test_get_artifact_class_by_id(self):
        """Can retrieve artifact class by ID."""
        artifact_class = get_artifact_class("dxf_validation_artifact")
        assert artifact_class is not None
        assert artifact_class.artifact_class_id == "dxf_validation_artifact"

    def test_get_artifact_class_unknown_returns_none(self):
        """Unknown artifact class ID returns None."""
        assert get_artifact_class("unknown_artifact") is None

    def test_list_artifact_classes(self):
        """Can list all artifact classes."""
        classes = list_artifact_classes()
        assert len(classes) == 4

    def test_list_artifact_class_ids(self):
        """Can list all artifact class IDs."""
        ids = list_artifact_class_ids()
        assert "dxf_validation_artifact" in ids
        assert "gcode_validation_artifact" in ids

    def test_get_artifact_classes_by_output_dxf(self):
        """Can filter artifact classes by DXF output."""
        dxf_classes = get_artifact_classes_by_output("dxf")
        assert len(dxf_classes) == 1
        assert dxf_classes[0].output_class == "dxf"

    def test_get_artifact_classes_by_category_translator(self):
        """Can filter artifact classes by translator category."""
        translator_classes = get_artifact_classes_by_category("translator")
        assert len(translator_classes) == 3  # dxf, svg, neutral_toolpath

    def test_get_artifact_classes_by_category_postprocessor(self):
        """Can filter artifact classes by postprocessor category."""
        postprocessor_classes = get_artifact_classes_by_category("postprocessor")
        assert len(postprocessor_classes) == 1  # gcode
        assert postprocessor_classes[0].artifact_class_id == "gcode_validation_artifact"

    def test_artifact_class_exists(self):
        """Can check if artifact class exists."""
        assert artifact_class_exists("dxf_validation_artifact") is True
        assert artifact_class_exists("unknown_artifact") is False

    def test_get_artifact_class_for_translator(self):
        """Can map translator ID to artifact class."""
        assert get_artifact_class_for_translator("dxf_r12") == "dxf_validation_artifact"
        assert get_artifact_class_for_translator("dxf_r2000") == "dxf_validation_artifact"
        assert get_artifact_class_for_translator("gcode_grbl_placeholder") == "gcode_validation_artifact"
        assert get_artifact_class_for_translator("unknown") is None


# -----------------------------------------------------------------------------
# Artifact Class Invariant Tests
# -----------------------------------------------------------------------------

class TestArtifactClassInvariants:
    """Tests for artifact class invariant enforcement."""

    def test_cannot_create_executable_artifact_class(self):
        """Cannot create artifact class with executable output."""
        with pytest.raises(ValueError, match="executable_output_supported must be False"):
            ArtifactClassRegistration(
                artifact_class_id="bad_artifact",
                output_class="dxf",
                description="Bad artifact",
                executable_output_supported=True,  # Violates 7D
            )

    def test_cannot_create_machine_output_artifact_class(self):
        """Cannot create artifact class with machine output."""
        with pytest.raises(ValueError, match="machine_output_supported must be False"):
            ArtifactClassRegistration(
                artifact_class_id="bad_artifact",
                output_class="gcode",
                description="Bad artifact",
                machine_output_supported=True,  # Violates 7D
            )


# -----------------------------------------------------------------------------
# Export Object Hash Tests
# -----------------------------------------------------------------------------

class TestExportObjectHash:
    """Tests for export object hashing."""

    def test_hash_is_deterministic(self):
        """Same export object produces same hash."""
        export_obj = create_valid_export_object()

        hash1 = compute_export_object_hash(export_obj)
        hash2 = compute_export_object_hash(export_obj)

        assert hash1 == hash2

    def test_hash_is_sha256(self):
        """Hash is 64 characters (SHA256 hex)."""
        export_obj = create_valid_export_object()
        hash_value = compute_export_object_hash(export_obj)

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)


# -----------------------------------------------------------------------------
# Lifecycle Integration Tests
# -----------------------------------------------------------------------------

class TestLifecycleIntegration:
    """Tests for translation artifact integration with lifecycle."""

    def test_lifecycle_report_has_artifact_summary(self):
        """Lifecycle report includes translation artifact summary."""
        from app.cam.dxf_translator_boundary import DXFTranslatorProfile
        from app.cam.export_lifecycle_orchestrator import (
            GovernedExportLifecycleRequest,
            PreviewRequestWrapper,
            run_governed_export_lifecycle,
        )
        from app.cam.postprocessor_boundary import MachineProfileValidationOnly

        request = GovernedExportLifecycleRequest(
            preview_request=PreviewRequestWrapper(
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
            ),
            machine_profile=MachineProfileValidationOnly(
                machine_profile_id="test_cnc",
                controller="none",
                units="mm",
                supported_operations=["nut_slot"],
                axis_count=3,
                work_envelope_mm={"x": 300, "y": 300, "z": 50},
            ),
            translator_profile=DXFTranslatorProfile(
                translator_id="dxf_r12",
                supported_geometry_types=["line", "polyline", "arc", "circle"],
                supports_layers=True,
                units="mm",
            ),
        )

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "green"
        assert report.translation_artifact_summary is not None
        assert report.translation_artifact_summary.translator_id == "dxf_r12"

    def test_lifecycle_red_has_no_artifact_summary(self):
        """RED lifecycle gate has no artifact summary."""
        from app.cam.dxf_translator_boundary import DXFTranslatorProfile
        from app.cam.export_lifecycle_orchestrator import (
            GovernedExportLifecycleRequest,
            PreviewRequestWrapper,
            run_governed_export_lifecycle,
        )
        from app.cam.postprocessor_boundary import MachineProfileValidationOnly

        request = GovernedExportLifecycleRequest(
            preview_request=PreviewRequestWrapper(
                operation="unsupported_op",
                payload={},
            ),
            machine_profile=MachineProfileValidationOnly(
                machine_profile_id="test_cnc",
                controller="none",
                units="mm",
                supported_operations=["nut_slot"],
                axis_count=3,
                work_envelope_mm={"x": 300, "y": 300, "z": 50},
            ),
            translator_profile=DXFTranslatorProfile(
                translator_id="dxf_r12",
                supported_geometry_types=["line", "polyline"],
                supports_layers=True,
                units="mm",
            ),
        )

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert report.translation_artifact_summary is None


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestArtifactClassEndpoints:
    """Tests for translation artifact class introspection endpoints."""

    def test_list_artifact_classes_endpoint(self):
        """GET /api/cam/translation-artifacts returns all classes."""
        response = client.get("/api/cam/translation-artifacts")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 4
        assert len(data["artifact_classes"]) == 4
        assert data["executable_artifacts_present"] is False
        assert data["machine_output_artifacts_present"] is False

    def test_list_artifact_class_ids_endpoint(self):
        """GET /api/cam/translation-artifacts/ids returns IDs."""
        response = client.get("/api/cam/translation-artifacts/ids")

        assert response.status_code == 200
        data = response.json()
        assert "dxf_validation_artifact" in data["artifact_class_ids"]

    def test_get_artifact_class_endpoint(self):
        """GET /api/cam/translation-artifacts/{id} returns single class."""
        response = client.get("/api/cam/translation-artifacts/dxf_validation_artifact")

        assert response.status_code == 200
        data = response.json()
        assert data["artifact_class"]["artifact_class_id"] == "dxf_validation_artifact"
        assert data["executable_output_supported"] is False
        assert data["machine_output_supported"] is False

    def test_get_artifact_class_not_found(self):
        """GET /api/cam/translation-artifacts/{id} returns 404 for unknown."""
        response = client.get("/api/cam/translation-artifacts/unknown_artifact")

        assert response.status_code == 404

    def test_filter_by_output_class_endpoint(self):
        """GET /api/cam/translation-artifacts/by-output/{output_class} filters."""
        response = client.get("/api/cam/translation-artifacts/by-output/dxf")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["artifact_classes"][0]["output_class"] == "dxf"

    def test_filter_by_category_endpoint(self):
        """GET /api/cam/translation-artifacts/by-category/{category} filters."""
        response = client.get("/api/cam/translation-artifacts/by-category/postprocessor")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["artifact_classes"][0]["translator_category"] == "postprocessor"


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Tests verifying no executable output."""

    def test_artifact_model_no_payload_field(self):
        """TranslationArtifact has no payload field."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert not hasattr(artifact, "payload")
        assert not hasattr(artifact, "dxf_content")
        assert not hasattr(artifact, "gcode_content")

    def test_artifact_json_has_no_dxf_tokens(self):
        """Artifact JSON contains no DXF serialization tokens."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )
        json_output = artifact.model_dump_json()

        forbidden = ['"SECTION"', '"ENTITIES"', '"POLYLINE"', '"EOF"']
        for token in forbidden:
            assert token not in json_output, f"Found forbidden DXF token: {token}"

    def test_artifact_json_has_no_gcode_tokens(self):
        """Artifact JSON contains no G-code tokens."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )
        json_output = artifact.model_dump_json()

        forbidden = ["G0 ", "G1 ", "G2 ", "M3 ", "M5 "]
        for token in forbidden:
            assert token not in json_output, f"Found forbidden G-code token: {token}"

    def test_artifact_metadata_validation_only_true(self):
        """Artifact metadata.validation_only is True."""
        export_obj = create_valid_export_object()
        capability = get_translator_capability("dxf_r12")

        artifact = build_validation_translation_artifact(
            export_object=export_obj,
            translator_capability=capability,
        )

        assert artifact.metadata.get("validation_only") is True

    def test_all_endpoint_responses_non_executable(self):
        """All artifact endpoint responses declare non-executable."""
        response = client.get("/api/cam/translation-artifacts")
        data = response.json()

        assert data["executable_artifacts_present"] is False
        assert data["machine_output_artifacts_present"] is False

        for artifact_class in data["artifact_classes"]:
            assert artifact_class["executable_output_supported"] is False
            assert artifact_class["machine_output_supported"] is False
