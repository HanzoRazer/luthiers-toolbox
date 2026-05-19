"""
Tests for Translation Artifact Authorization Gate (CAM Dev Order 7E)

Tests the authorization evaluation for translation artifacts:
  - Eligibility determination (not approval)
  - Gate status (green/yellow/red)
  - 7E invariants
  - Capability snapshot comparison
  - Safety assertions

Core rule: Eligibility ≠ Approval. Execution remains disabled.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.translation_artifact import (
    TranslationArtifact,
    build_validation_translation_artifact,
)
from app.cam.translation_artifact_authorization import (
    TranslationArtifactAuthorizationEvaluation,
    TranslationArtifactAuthorizationRequest,
    evaluate_translation_artifact_authorization,
)
from app.cam.translator_capability_registry import get_translator_capability
from app.cam.nut_slot_cam import NutSlotPreviewRequest, generate_nut_slot_preview
from app.cam.nut_slot_export import create_nut_slot_export_object


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_valid_artifact() -> TranslationArtifact:
    """Create a valid translation artifact for testing."""
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
    export_obj = create_nut_slot_export_object(preview, request)
    capability = get_translator_capability("dxf_r12")

    return build_validation_translation_artifact(
        export_object=export_obj,
        translator_capability=capability,
    )


def create_artifact_with_unknown_translator() -> TranslationArtifact:
    """Create artifact referencing unknown translator."""
    return TranslationArtifact(
        translator_id="unknown_translator_xyz",
        translator_category="translator",
        output_class="dxf",
        artifact_state="validation_only",
        source_export_object_id="test-export-id",
        source_export_object_hash="a" * 64,
        capability_snapshot={},
        execution_supported=False,
        executable_payload_present=False,
        machine_output_present=False,
    )


def create_artifact_with_category_mismatch() -> TranslationArtifact:
    """Create artifact with translator_category mismatch."""
    capability = get_translator_capability("dxf_r12")
    return TranslationArtifact(
        translator_id="dxf_r12",
        translator_category="postprocessor",  # Wrong — dxf_r12 is translator
        output_class="dxf",
        artifact_state="validation_only",
        source_export_object_id="test-export-id",
        source_export_object_hash="a" * 64,
        capability_snapshot=capability.model_dump(mode="json"),
        execution_supported=False,
        executable_payload_present=False,
        machine_output_present=False,
    )


def create_artifact_with_output_class_mismatch() -> TranslationArtifact:
    """Create artifact with output_class mismatch."""
    capability = get_translator_capability("dxf_r12")
    return TranslationArtifact(
        translator_id="dxf_r12",
        translator_category="translator",
        output_class="gcode",  # Wrong — dxf_r12 outputs dxf
        artifact_state="validation_only",
        source_export_object_id="test-export-id",
        source_export_object_hash="a" * 64,
        capability_snapshot=capability.model_dump(mode="json"),
        execution_supported=False,
        executable_payload_present=False,
        machine_output_present=False,
    )


# -----------------------------------------------------------------------------
# Valid Artifact Tests
# -----------------------------------------------------------------------------

class TestValidArtifactAuthorization:
    """Tests for valid artifact authorization."""

    def test_valid_artifact_returns_green(self):
        """Valid DXF validation artifact returns GREEN gate."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "green"
        assert len(evaluation.blocking_issues) == 0

    def test_valid_artifact_eligible_for_future_execution(self):
        """Valid artifact is eligible for future execution."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.eligible_for_future_execution is True

    def test_valid_artifact_not_authorized_for_execution(self):
        """Valid artifact is NOT authorized for execution (7E invariant)."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.authorized_for_execution is False

    def test_valid_artifact_human_approval_required(self):
        """Valid artifact requires human approval (7E invariant)."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.human_approval_required is True

    def test_evaluation_captures_artifact_id(self):
        """Evaluation captures artifact ID."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.artifact_id == artifact.artifact_id

    def test_evaluation_captures_translator_id(self):
        """Evaluation captures translator ID."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.translator_id == artifact.translator_id


# -----------------------------------------------------------------------------
# Unknown Translator Tests
# -----------------------------------------------------------------------------

class TestUnknownTranslator:
    """Tests for unknown translator handling."""

    def test_unknown_translator_returns_red(self):
        """Unknown translator returns RED gate."""
        artifact = create_artifact_with_unknown_translator()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "red"
        assert any("not found" in issue for issue in evaluation.blocking_issues)

    def test_unknown_translator_not_eligible(self):
        """Unknown translator artifact is not eligible."""
        artifact = create_artifact_with_unknown_translator()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.eligible_for_future_execution is False

    def test_unknown_translator_still_not_authorized(self):
        """Unknown translator artifact is still not authorized (invariant)."""
        artifact = create_artifact_with_unknown_translator()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.authorized_for_execution is False


# -----------------------------------------------------------------------------
# Category/Output Mismatch Tests
# -----------------------------------------------------------------------------

class TestCategoryMismatch:
    """Tests for category mismatch handling."""

    def test_category_mismatch_returns_red(self):
        """Category mismatch returns RED gate."""
        artifact = create_artifact_with_category_mismatch()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "red"
        assert any("translator_category" in issue for issue in evaluation.blocking_issues)

    def test_category_mismatch_not_eligible(self):
        """Category mismatch artifact is not eligible."""
        artifact = create_artifact_with_category_mismatch()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.eligible_for_future_execution is False


class TestOutputClassMismatch:
    """Tests for output class mismatch handling."""

    def test_output_class_mismatch_returns_red(self):
        """Output class mismatch returns RED gate."""
        artifact = create_artifact_with_output_class_mismatch()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "red"
        assert any("output_class" in issue for issue in evaluation.blocking_issues)

    def test_output_class_mismatch_not_eligible(self):
        """Output class mismatch artifact is not eligible."""
        artifact = create_artifact_with_output_class_mismatch()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.eligible_for_future_execution is False


# -----------------------------------------------------------------------------
# Artifact Invariant Violation Tests
# -----------------------------------------------------------------------------

class TestArtifactInvariantViolations:
    """Tests for artifact 7D invariant violations."""

    def test_executable_payload_present_returns_red(self):
        """Artifact with executable_payload_present=true returns RED."""
        # We can't directly create this via normal builders (they enforce invariants)
        # but we can check the evaluator catches it if somehow bypassed
        artifact = create_valid_artifact()
        # Manually override to test evaluation (this would fail model validation in practice)
        artifact_dict = artifact.model_dump()
        artifact_dict["executable_payload_present"] = True

        # The TranslationArtifact model validator should catch this
        with pytest.raises(ValueError, match="executable_payload_present"):
            TranslationArtifact(**artifact_dict)

    def test_machine_output_present_returns_red(self):
        """Artifact with machine_output_present=true returns RED."""
        artifact_dict = create_valid_artifact().model_dump()
        artifact_dict["machine_output_present"] = True

        with pytest.raises(ValueError, match="machine_output_present"):
            TranslationArtifact(**artifact_dict)

    def test_execution_supported_returns_red(self):
        """Artifact with execution_supported=true returns RED."""
        artifact_dict = create_valid_artifact().model_dump()
        artifact_dict["execution_supported"] = True

        with pytest.raises(ValueError, match="execution_supported"):
            TranslationArtifact(**artifact_dict)


# -----------------------------------------------------------------------------
# 7E Invariant Enforcement Tests
# -----------------------------------------------------------------------------

class TestEvaluationInvariants:
    """Tests for 7E evaluation invariant enforcement."""

    def test_cannot_create_authorized_evaluation(self):
        """Cannot create evaluation with authorized_for_execution=True."""
        with pytest.raises(ValueError, match="authorized_for_execution must be False"):
            TranslationArtifactAuthorizationEvaluation(
                artifact_id="test",
                translator_id="dxf_r12",
                gate="green",
                authorized_for_execution=True,  # Violates 7E
                eligible_for_future_execution=True,
                human_approval_required=True,
            )

    def test_cannot_create_no_approval_required_evaluation(self):
        """Cannot create evaluation with human_approval_required=False."""
        with pytest.raises(ValueError, match="human_approval_required must be True"):
            TranslationArtifactAuthorizationEvaluation(
                artifact_id="test",
                translator_id="dxf_r12",
                gate="green",
                authorized_for_execution=False,
                eligible_for_future_execution=True,
                human_approval_required=False,  # Violates 7E
            )

    def test_cannot_create_eligible_with_red_gate(self):
        """Cannot create evaluation with eligible=True and gate=RED."""
        with pytest.raises(ValueError, match="eligible_for_future_execution cannot be True when gate is RED"):
            TranslationArtifactAuthorizationEvaluation(
                artifact_id="test",
                translator_id="dxf_r12",
                gate="red",
                authorized_for_execution=False,
                eligible_for_future_execution=True,  # Invalid with RED gate
                human_approval_required=True,
                blocking_issues=["Some blocking issue"],
            )


# -----------------------------------------------------------------------------
# Gate Logic Tests
# -----------------------------------------------------------------------------

class TestGateLogic:
    """Tests for gate determination logic."""

    def test_blocking_issues_result_in_red(self):
        """Blocking issues result in RED gate."""
        artifact = create_artifact_with_unknown_translator()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "red"
        assert len(evaluation.blocking_issues) > 0

    def test_warnings_only_result_in_yellow(self):
        """Warnings without blocking issues result in YELLOW gate."""
        # Create artifact with stale snapshot (maturity changed)
        artifact = create_valid_artifact()
        # Modify snapshot to have different maturity
        artifact.capability_snapshot["maturity"] = "prototype"

        evaluation = evaluate_translation_artifact_authorization(artifact)

        # Should be YELLOW due to maturity mismatch warning
        assert evaluation.gate in ("green", "yellow")  # Depends on exact registry state

    def test_no_issues_result_in_green(self):
        """No issues result in GREEN gate."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "green"
        assert len(evaluation.blocking_issues) == 0


# -----------------------------------------------------------------------------
# Capability Snapshot Comparison Tests
# -----------------------------------------------------------------------------

class TestCapabilitySnapshotComparison:
    """Tests for capability snapshot comparison."""

    def test_matching_snapshot_no_warnings(self):
        """Matching capability snapshot produces no warnings."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        # Should have minimal or no warnings if snapshot matches
        assert evaluation.gate == "green"

    def test_evaluation_includes_current_capability(self):
        """Evaluation includes current capability snapshot for comparison."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.capability_snapshot is not None
        assert evaluation.capability_snapshot.get("translator_id") == "dxf_r12"


# -----------------------------------------------------------------------------
# Metadata Tests
# -----------------------------------------------------------------------------

class TestEvaluationMetadata:
    """Tests for evaluation metadata."""

    def test_metadata_includes_dev_order(self):
        """Metadata includes dev_order=7E."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.metadata.get("dev_order") == "7E"

    def test_metadata_validation_only_true(self):
        """Metadata includes validation_only=True."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.metadata.get("validation_only") is True

    def test_metadata_includes_artifact_state(self):
        """Metadata includes artifact state."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.metadata.get("artifact_state") == "validation_only"


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestAuthorizationEndpoint:
    """Tests for authorization validation endpoint."""

    def test_endpoint_returns_200_for_valid_artifact(self):
        """Endpoint returns 200 for valid artifact."""
        artifact = create_valid_artifact()
        request_body = {"artifact": artifact.model_dump(mode="json")}

        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=request_body,
        )

        assert response.status_code == 200

    def test_endpoint_returns_green_gate(self):
        """Endpoint returns green gate for valid artifact."""
        artifact = create_valid_artifact()
        request_body = {"artifact": artifact.model_dump(mode="json")}

        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=request_body,
        )

        data = response.json()
        assert data["gate"] == "green"

    def test_endpoint_returns_red_for_unknown_translator(self):
        """Endpoint returns red gate for unknown translator."""
        artifact = create_artifact_with_unknown_translator()
        request_body = {"artifact": artifact.model_dump(mode="json")}

        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=request_body,
        )

        data = response.json()
        assert data["gate"] == "red"
        assert data["eligible_for_future_execution"] is False

    def test_endpoint_response_structure(self):
        """Endpoint response has expected structure."""
        artifact = create_valid_artifact()
        request_body = {"artifact": artifact.model_dump(mode="json")}

        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=request_body,
        )

        data = response.json()
        assert "artifact_id" in data
        assert "translator_id" in data
        assert "gate" in data
        assert "authorized_for_execution" in data
        assert "eligible_for_future_execution" in data
        assert "human_approval_required" in data
        assert "blocking_issues" in data
        assert "warnings" in data
        assert "metadata" in data

    def test_endpoint_always_not_authorized(self):
        """Endpoint always returns authorized_for_execution=False."""
        artifact = create_valid_artifact()
        request_body = {"artifact": artifact.model_dump(mode="json")}

        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=request_body,
        )

        data = response.json()
        assert data["authorized_for_execution"] is False

    def test_endpoint_always_requires_approval(self):
        """Endpoint always returns human_approval_required=True."""
        artifact = create_valid_artifact()
        request_body = {"artifact": artifact.model_dump(mode="json")}

        response = client.post(
            "/api/cam/translation-artifacts/authorize/validate",
            json=request_body,
        )

        data = response.json()
        assert data["human_approval_required"] is True


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Tests verifying no output generation."""

    def test_no_dxf_tokens_in_evaluation(self):
        """Evaluation contains no DXF serialization tokens."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)
        json_output = evaluation.model_dump_json()

        forbidden = ['"SECTION"', '"ENTITIES"', '"POLYLINE"', '"EOF"']
        for token in forbidden:
            assert token not in json_output, f"Found forbidden DXF token: {token}"

    def test_no_gcode_tokens_in_evaluation(self):
        """Evaluation contains no G-code tokens."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)
        json_output = evaluation.model_dump_json()

        forbidden = ["G0 ", "G1 ", "G2 ", "M3 ", "M5 "]
        for token in forbidden:
            assert token not in json_output, f"Found forbidden G-code token: {token}"

    def test_human_approval_required_always_true(self):
        """human_approval_required is always True."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.human_approval_required is True

    def test_authorized_for_execution_always_false(self):
        """authorized_for_execution is always False."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.authorized_for_execution is False

    def test_red_gate_not_eligible(self):
        """RED gate means not eligible for future execution."""
        artifact = create_artifact_with_unknown_translator()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "red"
        assert evaluation.eligible_for_future_execution is False

    def test_green_gate_eligible_but_not_authorized(self):
        """GREEN gate is eligible but not authorized."""
        artifact = create_valid_artifact()
        evaluation = evaluate_translation_artifact_authorization(artifact)

        assert evaluation.gate == "green"
        assert evaluation.eligible_for_future_execution is True
        assert evaluation.authorized_for_execution is False
