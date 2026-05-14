"""
Tests for Translator Execution Quarantine (CAM Dev Order 7H)

Verifies:
  - 7H invariants (execution_runtime_present=false, etc.)
  - Freeze manifest immutability
  - Quarantine state semantics
  - Prohibited actions populated
  - Required escalation layers
  - Introspection endpoints
  - No execution pathways

Guardrail:
  7H creates freeze/quarantine evidence boundary.
  It does NOT create any execution pathway or approval workflow.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.cam.translator_execution_quarantine import (
    QuarantineState,
    TranslatorExecutionQuarantine,
    TranslatorGovernanceFreezeManifest,
    ExecutionQuarantineSummary,
    REQUIRED_ESCALATION_LAYERS,
    PROHIBITED_ACTIONS,
    evaluate_execution_quarantine,
    get_quarantine,
    get_latest_quarantine,
    list_quarantines,
    get_freeze_manifest,
    list_freeze_manifests,
    clear_quarantine_index,
    clear_freeze_manifest_index,
)


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear in-memory indexes before each test."""
    clear_quarantine_index()
    clear_freeze_manifest_index()
    yield
    clear_quarantine_index()
    clear_freeze_manifest_index()


class TestQuarantineInvariants:
    """Test 7H invariants at model level."""

    def test_7h_invariant_execution_runtime_always_false(self):
        """execution_runtime_present must be False."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.execution_runtime_present is False

    def test_7h_invariant_serializer_invocation_always_false(self):
        """serializer_invocation_allowed must be False."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.serializer_invocation_allowed is False

    def test_7h_invariant_subprocess_execution_always_false(self):
        """subprocess_execution_allowed must be False."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.subprocess_execution_allowed is False

    def test_7h_invariant_machine_output_always_false(self):
        """machine_output_allowed must be False."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.machine_output_allowed is False

    def test_7h_invariant_plugin_loading_always_false(self):
        """plugin_loading_allowed must be False."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.plugin_loading_allowed is False

    def test_7h_invariant_governance_escalation_always_required(self):
        """governance_escalation_required must be True."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.governance_escalation_required is True

    def test_7h_invariant_human_approval_always_required(self):
        """human_approval_required must be True."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.human_approval_required is True

    def test_cannot_create_execution_runtime_present(self):
        """Should reject execution_runtime_present=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorExecutionQuarantine(
                translator_id="test",
                execution_runtime_present=True,  # Violates 7H
            )
        assert "execution_runtime_present must be False" in str(exc_info.value)

    def test_cannot_create_serializer_invocation_allowed(self):
        """Should reject serializer_invocation_allowed=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorExecutionQuarantine(
                translator_id="test",
                serializer_invocation_allowed=True,  # Violates 7H
            )
        assert "serializer_invocation_allowed must be False" in str(exc_info.value)

    def test_cannot_create_subprocess_execution_allowed(self):
        """Should reject subprocess_execution_allowed=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorExecutionQuarantine(
                translator_id="test",
                subprocess_execution_allowed=True,  # Violates 7H
            )
        assert "subprocess_execution_allowed must be False" in str(exc_info.value)

    def test_cannot_create_machine_output_allowed(self):
        """Should reject machine_output_allowed=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorExecutionQuarantine(
                translator_id="test",
                machine_output_allowed=True,  # Violates 7H
            )
        assert "machine_output_allowed must be False" in str(exc_info.value)

    def test_cannot_create_plugin_loading_allowed(self):
        """Should reject plugin_loading_allowed=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorExecutionQuarantine(
                translator_id="test",
                plugin_loading_allowed=True,  # Violates 7H
            )
        assert "plugin_loading_allowed must be False" in str(exc_info.value)

    def test_cannot_disable_governance_escalation(self):
        """Should reject governance_escalation_required=False."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorExecutionQuarantine(
                translator_id="test",
                governance_escalation_required=False,  # Violates 7H
            )
        assert "governance_escalation_required must be True" in str(exc_info.value)

    def test_cannot_disable_human_approval(self):
        """Should reject human_approval_required=False."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorExecutionQuarantine(
                translator_id="test",
                human_approval_required=False,  # Violates 7H
            )
        assert "human_approval_required must be True" in str(exc_info.value)


class TestFreezeManifest:
    """Test freeze manifest model and immutability."""

    def test_freeze_manifest_created_on_evaluation(self):
        """Freeze manifest should be created during quarantine evaluation."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.freeze_manifest_id != ""
        assert quarantine.freeze_manifest_hash != ""

        manifest = get_freeze_manifest(quarantine.freeze_manifest_id)
        assert manifest is not None
        assert manifest.translator_id == "body_outline_dxf_r12"

    def test_freeze_manifest_immutable(self):
        """Freeze manifest immutable flag must be True."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        manifest = get_freeze_manifest(quarantine.freeze_manifest_id)
        assert manifest.immutable is True

    def test_cannot_create_mutable_freeze_manifest(self):
        """Should reject immutable=False."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorGovernanceFreezeManifest(
                translator_id="test",
                immutable=False,  # Violates 7H
            )
        assert "immutable must be True" in str(exc_info.value)

    def test_freeze_manifest_has_prohibited_actions(self):
        """Freeze manifest should have all prohibited actions."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        manifest = get_freeze_manifest(quarantine.freeze_manifest_id)

        assert "DXF_generation" in manifest.prohibited_actions
        assert "SVG_generation" in manifest.prohibited_actions
        assert "G-code_generation" in manifest.prohibited_actions
        assert "serializer_invocation" in manifest.prohibited_actions
        assert "runtime_translator_execution" in manifest.prohibited_actions
        assert "plugin_loading" in manifest.prohibited_actions
        assert "machine_output" in manifest.prohibited_actions
        assert "subprocess_execution" in manifest.prohibited_actions

    def test_freeze_manifest_has_escalation_layers(self):
        """Freeze manifest should have all required escalation layers."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        manifest = get_freeze_manifest(quarantine.freeze_manifest_id)

        assert "governance_review" in manifest.required_escalation_layers
        assert "translator_execution_architecture_review" in manifest.required_escalation_layers
        assert "human_approval" in manifest.required_escalation_layers
        assert "security_review" in manifest.required_escalation_layers
        assert "artifact_generation_policy_review" in manifest.required_escalation_layers

    def test_freeze_manifest_hash_deterministic(self):
        """Freeze manifest hash should be deterministic."""
        manifest = TranslatorGovernanceFreezeManifest(
            translator_id="test",
            created_from_readiness_hash="abc123",
            created_from_provenance_hash="def456",
        )
        hash1 = manifest.compute_manifest_hash()
        hash2 = manifest.compute_manifest_hash()
        assert hash1 == hash2


class TestQuarantineState:
    """Test quarantine state semantics."""

    def test_default_state_is_future_escalation_required(self):
        """Default quarantine state should be future_escalation_required."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.quarantine_state == "future_escalation_required"

    def test_all_quarantine_states_valid(self):
        """All defined quarantine states should be valid."""
        valid_states = ["execution_prohibited", "governance_freeze", "future_escalation_required"]
        for state in valid_states:
            quarantine = TranslatorExecutionQuarantine(
                translator_id="test",
                quarantine_state=state,
            )
            assert quarantine.quarantine_state == state


class TestQuarantineEvaluator:
    """Test quarantine evaluation function."""

    def test_evaluator_creates_quarantine(self):
        """Evaluator should create quarantine evaluation."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert quarantine.translator_id == "body_outline_dxf_r12"
        assert quarantine.quarantine_id.startswith("quarantine-")

    def test_evaluator_populates_blocking_constraints(self):
        """Evaluator should populate blocking constraints."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        assert len(quarantine.blocking_constraints) > 0

    def test_evaluator_registers_in_index(self):
        """Evaluator should register quarantine in index."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        indexed = get_quarantine(quarantine.quarantine_id)
        assert indexed is not None
        assert indexed.quarantine_id == quarantine.quarantine_id

    def test_evaluator_creates_and_registers_freeze_manifest(self):
        """Evaluator should create and register freeze manifest."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        manifest = get_freeze_manifest(quarantine.freeze_manifest_id)
        assert manifest is not None


class TestQuarantineIndex:
    """Test in-memory quarantine index."""

    def test_get_quarantine_by_translator(self):
        """Should get quarantines by translator ID."""
        evaluate_execution_quarantine("body_outline_dxf_r12")
        evaluate_execution_quarantine("body_outline_dxf_r12")

        from app.cam.translator_execution_quarantine import get_quarantine_by_translator
        quarantines = get_quarantine_by_translator("body_outline_dxf_r12")
        assert len(quarantines) == 2

    def test_get_latest_quarantine(self):
        """Should get most recent quarantine for translator."""
        q1 = evaluate_execution_quarantine("body_outline_dxf_r12")
        q2 = evaluate_execution_quarantine("body_outline_dxf_r12")

        latest = get_latest_quarantine("body_outline_dxf_r12")
        assert latest.quarantine_id == q2.quarantine_id

    def test_list_quarantines(self):
        """Should list all quarantine evaluations."""
        evaluate_execution_quarantine("body_outline_dxf_r12")
        evaluate_execution_quarantine("dxf_r12")

        quarantines = list_quarantines()
        assert len(quarantines) >= 2


class TestFreezeManifestIndex:
    """Test in-memory freeze manifest index."""

    def test_list_freeze_manifests(self):
        """Should list all freeze manifests."""
        evaluate_execution_quarantine("body_outline_dxf_r12")
        evaluate_execution_quarantine("dxf_r12")

        manifests = list_freeze_manifests()
        assert len(manifests) >= 2

    def test_get_freeze_manifests_by_translator(self):
        """Should get freeze manifests by translator ID."""
        evaluate_execution_quarantine("body_outline_dxf_r12")
        evaluate_execution_quarantine("body_outline_dxf_r12")

        from app.cam.translator_execution_quarantine import get_freeze_manifests_by_translator
        manifests = get_freeze_manifests_by_translator("body_outline_dxf_r12")
        assert len(manifests) == 2


class TestQuarantineSummary:
    """Test quarantine summary for 7G integration."""

    def test_to_summary_preserves_key_fields(self):
        """Summary should preserve key fields."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        summary = quarantine.to_summary()

        assert summary.quarantine_id == quarantine.quarantine_id
        assert summary.translator_id == quarantine.translator_id
        assert summary.quarantine_state == quarantine.quarantine_state

    def test_summary_enforces_invariants(self):
        """Summary should always enforce 7H invariants."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")
        summary = quarantine.to_summary()

        assert summary.governance_escalation_required is True
        assert summary.execution_runtime_present is False
        assert summary.machine_output_allowed is False


class TestQuarantineEndpoints:
    """Test REST API endpoints."""

    def test_list_quarantines_endpoint(self, client):
        """GET /api/cam/translators/quarantine should return list."""
        evaluate_execution_quarantine("body_outline_dxf_r12")

        response = client.get("/api/cam/translators/quarantine")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_quarantine_policy_endpoint(self, client):
        """GET /api/cam/translators/quarantine/policy should return policy."""
        response = client.get("/api/cam/translators/quarantine/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_runtime_present"] is False
        assert data["governance_escalation_required"] is True
        assert len(data["required_escalation_layers"]) == 5
        assert len(data["prohibited_actions"]) == 8

    def test_get_translator_quarantine_endpoint(self, client):
        """GET /api/cam/translators/quarantine/{translator_id} should return quarantine."""
        response = client.get("/api/cam/translators/quarantine/body_outline_dxf_r12")
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["execution_runtime_present"] is False
        assert data["governance_escalation_required"] is True

    def test_evaluate_quarantine_endpoint(self, client):
        """POST /api/cam/translators/quarantine/evaluate should evaluate."""
        response = client.post(
            "/api/cam/translators/quarantine/evaluate",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["quarantine_state"] == "future_escalation_required"

    def test_list_freeze_manifests_endpoint(self, client):
        """GET /api/cam/translators/freeze-manifests should return list."""
        evaluate_execution_quarantine("body_outline_dxf_r12")

        response = client.get("/api/cam/translators/freeze-manifests")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_freeze_manifest_endpoint(self, client):
        """GET /api/cam/translators/freeze-manifests/{manifest_id} should return manifest."""
        quarantine = evaluate_execution_quarantine("body_outline_dxf_r12")

        response = client.get(f"/api/cam/translators/freeze-manifests/{quarantine.freeze_manifest_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["immutable"] is True

    def test_freeze_manifest_not_found(self, client):
        """Should return 404 for unknown freeze manifest."""
        response = client.get("/api/cam/translators/freeze-manifests/unknown-manifest")
        assert response.status_code == 404


class TestSafetyAssertions:
    """Safety assertions for 7H — no execution artifacts."""

    def test_no_dxf_tokens_in_response(self, client):
        """Response should not contain DXF content tokens."""
        response = client.get("/api/cam/translators/quarantine/body_outline_dxf_r12")
        text = response.text.lower()
        dxf_tokens = ["ac1009", "ac1015", "ac1024", "endsec", "entities"]
        for token in dxf_tokens:
            assert token not in text

    def test_no_gcode_tokens_in_response(self, client):
        """Response should not contain G-code tokens."""
        response = client.get("/api/cam/translators/quarantine/body_outline_dxf_r12")
        text = response.text
        gcode_tokens = ["G00", "G01", "M03", "M05", "M30"]
        for token in gcode_tokens:
            assert token not in text

    def test_all_endpoints_enforce_invariants(self, client):
        """All endpoints should enforce 7H invariants."""
        # Test list endpoint
        response = client.get("/api/cam/translators/quarantine/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_runtime_present"] is False
        assert data["governance_escalation_required"] is True

        # Test evaluate endpoint
        response = client.post(
            "/api/cam/translators/quarantine/evaluate",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["execution_runtime_present"] is False
        assert data["serializer_invocation_allowed"] is False
        assert data["subprocess_execution_allowed"] is False
        assert data["machine_output_allowed"] is False
        assert data["plugin_loading_allowed"] is False
        assert data["governance_escalation_required"] is True
        assert data["human_approval_required"] is True


class TestCanonicalConstants:
    """Test canonical constants are properly defined."""

    def test_required_escalation_layers_count(self):
        """Should have 5 required escalation layers."""
        assert len(REQUIRED_ESCALATION_LAYERS) == 5

    def test_prohibited_actions_count(self):
        """Should have 8 prohibited actions."""
        assert len(PROHIBITED_ACTIONS) == 8

    def test_required_escalation_layers_content(self):
        """Should have correct escalation layers."""
        expected = [
            "governance_review",
            "translator_execution_architecture_review",
            "human_approval",
            "security_review",
            "artifact_generation_policy_review",
        ]
        assert set(REQUIRED_ESCALATION_LAYERS) == set(expected)

    def test_prohibited_actions_content(self):
        """Should have correct prohibited actions."""
        expected = [
            "DXF_generation",
            "SVG_generation",
            "G-code_generation",
            "serializer_invocation",
            "runtime_translator_execution",
            "plugin_loading",
            "machine_output",
            "subprocess_execution",
        ]
        assert set(PROHIBITED_ACTIONS) == set(expected)
