"""
Tests for Translator Readiness Matrix (CAM Dev Order 7G)

Verifies:
  - 7G invariants (execution_ready=false, promotion_authorized=false, etc.)
  - Readiness level derivation from maturity
  - Promotion requirements evaluation
  - Gate propagation (RED > YELLOW > GREEN)
  - Authorization integration (7E)
  - Provenance integration (7F)
  - Endpoint responses
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.cam.translator_readiness_matrix import (
    ReadinessLevel,
    TranslatorReadinessEvaluation,
    TranslatorReadinessEvaluationSummary,
    PROMOTION_REQUIREMENTS,
    MATURITY_TO_READINESS,
    evaluate_translator_readiness,
    get_readiness_evaluation,
    list_readiness_evaluations,
    get_promotion_requirements,
    get_next_promotion_level,
    can_promote,
    clear_readiness_index,
)
from app.cam.translation_artifact import (
    TranslationArtifact,
)
from app.cam.translation_artifact_provenance import (
    build_translation_artifact_provenance,
    clear_provenance_index,
)
from app.cam.translator_capability_registry import get_translator_capability


def _create_test_artifact(translator_id: str) -> TranslationArtifact:
    """Create a test artifact for integration tests."""
    capability = get_translator_capability(translator_id)
    if capability is None:
        raise ValueError(f"Unknown translator: {translator_id}")
    return TranslationArtifact(
        translator_id=translator_id,
        translator_category=capability.translator_category,
        output_class=capability.output_class,
        artifact_state="validation_only",
        source_export_object_id="test-export-001",
        source_export_object_hash="abc123def456",
        capability_snapshot=capability.model_dump(mode="json"),
        policy_snapshot={},
        execution_supported=False,
        executable_payload_present=False,
        machine_output_present=False,
        metadata={"test": True},
    )


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear in-memory indexes before each test."""
    clear_readiness_index()
    clear_provenance_index()
    yield
    clear_readiness_index()
    clear_provenance_index()


class TestReadinessInvariants:
    """Test 7G invariants at model level."""

    def test_7g_invariant_execution_ready_always_false(self):
        """execution_ready must be False."""
        evaluation = evaluate_translator_readiness("body_outline_dxf_r12")
        assert evaluation.execution_ready is False

    def test_7g_invariant_machine_operation_authorized_always_false(self):
        """machine_operation_authorized must be False."""
        evaluation = evaluate_translator_readiness("body_outline_dxf_r12")
        assert evaluation.machine_operation_authorized is False

    def test_7g_invariant_promotion_authorized_always_false(self):
        """promotion_authorized must be False."""
        evaluation = evaluate_translator_readiness("body_outline_dxf_r12")
        assert evaluation.promotion_authorized is False

    def test_cannot_create_execution_ready_evaluation(self):
        """Should reject execution_ready=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorReadinessEvaluation(
                translator_id="test",
                current_level="experimental",
                gate="green",
                execution_ready=True,  # Violates 7G
                machine_operation_authorized=False,
                promotion_authorized=False,
                promotion_eligible=True,
            )
        assert "execution_ready must be False" in str(exc_info.value)

    def test_cannot_create_machine_authorized_evaluation(self):
        """Should reject machine_operation_authorized=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorReadinessEvaluation(
                translator_id="test",
                current_level="experimental",
                gate="green",
                execution_ready=False,
                machine_operation_authorized=True,  # Violates 7G
                promotion_authorized=False,
                promotion_eligible=True,
            )
        assert "machine_operation_authorized must be False" in str(exc_info.value)

    def test_cannot_create_promotion_authorized_evaluation(self):
        """Should reject promotion_authorized=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorReadinessEvaluation(
                translator_id="test",
                current_level="experimental",
                gate="green",
                execution_ready=False,
                machine_operation_authorized=False,
                promotion_authorized=True,  # Violates 7G
                promotion_eligible=True,
            )
        assert "promotion_authorized must be False" in str(exc_info.value)

    def test_cannot_have_promotion_eligible_with_red_gate(self):
        """promotion_eligible requires gate != red."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorReadinessEvaluation(
                translator_id="test",
                current_level="experimental",
                gate="red",
                execution_ready=False,
                machine_operation_authorized=False,
                promotion_authorized=False,
                promotion_eligible=True,  # Invalid with red gate
            )
        assert "promotion_eligible cannot be True when gate is red" in str(exc_info.value)


class TestReadinessLevelDerivation:
    """Test readiness level derivation from capability maturity."""

    def test_maturity_to_readiness_mapping(self):
        """Verify maturity → readiness level mapping."""
        assert MATURITY_TO_READINESS["placeholder"] == "experimental"
        assert MATURITY_TO_READINESS["candidate"] == "governed_experimental"
        assert MATURITY_TO_READINESS["governed"] == "stable_candidate"
        assert MATURITY_TO_READINESS["canonical"] == "production"

    def test_placeholder_translator_is_experimental(self):
        """Placeholder translators should be experimental."""
        evaluation = evaluate_translator_readiness("gcode_grbl_placeholder")
        assert evaluation.current_level == "experimental"

    def test_governed_translator_is_stable_candidate(self):
        """Governed translators should be stable_candidate."""
        evaluation = evaluate_translator_readiness("body_outline_dxf_r12")
        assert evaluation.current_level == "stable_candidate"

    def test_candidate_translator_is_governed_experimental(self):
        """Candidate translators should be governed_experimental."""
        evaluation = evaluate_translator_readiness("dxf_r12")
        assert evaluation.current_level == "governed_experimental"


class TestPromotionRequirements:
    """Test promotion requirement checks."""

    def test_experimental_has_no_requirements(self):
        """Experimental level has minimal requirements."""
        requirements = get_promotion_requirements("experimental")
        assert requirements["min_test_fixtures"] == 0
        assert requirements["requires_governance_approval"] is False

    def test_production_has_strict_requirements(self):
        """Production level has strict requirements."""
        requirements = get_promotion_requirements("production")
        assert requirements["min_test_fixtures"] == 20
        assert requirements["min_test_pass_rate"] == 1.00
        assert requirements["requires_governance_approval"] is True
        assert requirements["stability_days_required"] == 90

    def test_get_next_promotion_level(self):
        """Test promotion level progression."""
        assert get_next_promotion_level("experimental") == "governed_experimental"
        assert get_next_promotion_level("governed_experimental") == "stable_candidate"
        assert get_next_promotion_level("stable_candidate") == "production"
        assert get_next_promotion_level("production") is None


class TestGatePropagation:
    """Test gate propagation logic."""

    def test_unknown_translator_is_red(self):
        """Unknown translator should give red gate."""
        evaluation = evaluate_translator_readiness("unknown_translator_xyz")
        assert evaluation.gate == "red"
        assert evaluation.promotion_eligible is False

    def test_known_translator_can_be_green(self):
        """Known translator with no issues should be green."""
        evaluation = evaluate_translator_readiness("body_outline_dxf_r12")
        # May be green or yellow depending on warnings
        assert evaluation.gate in ("green", "yellow")

    def test_target_level_mismatch_adds_warnings(self):
        """Targeting wrong level should add warnings."""
        evaluation = evaluate_translator_readiness(
            translator_id="gcode_grbl_placeholder",
            target_level="production",
        )
        # Should have warnings/blockers about maturity mismatch
        assert len(evaluation.warnings) > 0 or len(evaluation.promotion_blockers) > 0


class TestAuthorizationIntegration:
    """Test 7E authorization integration."""

    def test_artifact_triggers_authorization_check(self):
        """Providing artifact should trigger authorization evaluation."""
        artifact = _create_test_artifact("body_outline_dxf_r12")

        evaluation = evaluate_translator_readiness(
            translator_id="body_outline_dxf_r12",
            artifact=artifact,
        )

        # Should have captured authorization gate
        assert evaluation.authorization_gate is not None

    def test_red_authorization_propagates_to_readiness(self):
        """Red authorization gate should propagate to readiness."""
        artifact = _create_test_artifact("body_outline_dxf_r12")

        # Tamper with artifact to make authorization red
        artifact_dict = artifact.model_dump()
        artifact_dict["translator_category"] = "postprocessor"  # Mismatch
        tampered = TranslationArtifact(**artifact_dict)

        evaluation = evaluate_translator_readiness(
            translator_id="body_outline_dxf_r12",
            artifact=tampered,
        )

        # Red authorization should propagate
        assert evaluation.authorization_gate == "red"
        assert evaluation.gate == "red"
        assert evaluation.promotion_eligible is False


class TestProvenanceIntegration:
    """Test 7F provenance integration."""

    def test_provenance_count_tracked(self):
        """Provenance count should be tracked."""
        artifact = _create_test_artifact("body_outline_dxf_r12")

        # Create provenance
        provenance = build_translation_artifact_provenance(artifact)

        evaluation = evaluate_translator_readiness(
            translator_id="body_outline_dxf_r12",
            artifact=artifact,
        )

        assert evaluation.has_provenance_lineage is True
        assert evaluation.provenance_count == 1


class TestReadinessIndex:
    """Test in-memory readiness index."""

    def test_evaluation_registered_in_index(self):
        """Evaluation should be registered in index."""
        evaluation = evaluate_translator_readiness("body_outline_dxf_r12")

        indexed = get_readiness_evaluation("body_outline_dxf_r12")
        assert indexed is not None
        assert indexed.translator_id == "body_outline_dxf_r12"

    def test_list_evaluations(self):
        """Should list all evaluations."""
        evaluate_translator_readiness("body_outline_dxf_r12")
        evaluate_translator_readiness("dxf_r12")

        evaluations = list_readiness_evaluations()
        assert len(evaluations) >= 2

    def test_list_evaluations_filtered(self):
        """Should filter by translator_id."""
        evaluate_translator_readiness("body_outline_dxf_r12")
        evaluate_translator_readiness("dxf_r12")

        evaluations = list_readiness_evaluations(translator_id="body_outline_dxf_r12")
        assert all(e.translator_id == "body_outline_dxf_r12" for e in evaluations)


class TestCanPromote:
    """Test can_promote helper function."""

    def test_can_promote_returns_tuple(self):
        """can_promote should return (bool, list)."""
        eligible, blockers = can_promote("body_outline_dxf_r12")
        assert isinstance(eligible, bool)
        assert isinstance(blockers, list)

    def test_unknown_translator_cannot_promote(self):
        """Unknown translator should not be promotable."""
        eligible, blockers = can_promote("unknown_translator_xyz")
        assert eligible is False
        assert len(blockers) > 0


class TestSummaryModel:
    """Test summary model creation."""

    def test_to_summary_preserves_key_fields(self):
        """Summary should preserve key identification fields."""
        evaluation = evaluate_translator_readiness("body_outline_dxf_r12")
        summary = evaluation.to_summary()

        assert summary.translator_id == evaluation.translator_id
        assert summary.current_level == evaluation.current_level
        assert summary.gate == evaluation.gate
        assert summary.execution_ready is False


class TestReadinessEndpoints:
    """Test REST API endpoints."""

    def test_list_evaluations_endpoint(self, client):
        """GET /api/cam/translators/readiness should return list."""
        evaluate_translator_readiness("body_outline_dxf_r12")

        response = client.get("/api/cam/translators/readiness")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_levels_endpoint(self, client):
        """GET /api/cam/translators/readiness/levels should return levels."""
        response = client.get("/api/cam/translators/readiness/levels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # experimental, governed_experimental, stable_candidate, production

    def test_get_requirements_endpoint(self, client):
        """GET /api/cam/translators/readiness/requirements/{level} should return requirements."""
        response = client.get("/api/cam/translators/readiness/requirements/production")
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "production"
        assert "requirements" in data

    def test_get_translator_readiness_endpoint(self, client):
        """GET /api/cam/translators/readiness/{translator_id} should return evaluation."""
        response = client.get("/api/cam/translators/readiness/body_outline_dxf_r12")
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["execution_ready"] is False
        assert data["promotion_authorized"] is False

    def test_evaluate_readiness_endpoint(self, client):
        """POST /api/cam/translators/readiness/evaluate should evaluate."""
        response = client.post(
            "/api/cam/translators/readiness/evaluate",
            json={
                "translator_id": "body_outline_dxf_r12",
                "target_level": "production",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["target_level"] == "production"

    def test_can_promote_endpoint(self, client):
        """POST /api/cam/translators/readiness/can-promote should check eligibility."""
        response = client.post(
            "/api/cam/translators/readiness/can-promote",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["promotion_authorized"] is False

    def test_maturity_mapping_endpoint(self, client):
        """GET /api/cam/translators/readiness/maturity-mapping should return mapping."""
        response = client.get("/api/cam/translators/readiness/maturity-mapping")
        assert response.status_code == 200
        data = response.json()
        # Verify the response has the expected maturity levels
        assert len(data) == 4  # 4 maturity levels
        # Check that values are readiness levels
        expected_values = {"experimental", "governed_experimental", "stable_candidate", "production"}
        assert set(data.values()) == expected_values


class TestSafetyAssertions:
    """Safety assertions for 7G — no execution artifacts."""

    def test_no_dxf_tokens_in_response(self, client):
        """Response should not contain DXF content tokens."""
        response = client.get("/api/cam/translators/readiness/body_outline_dxf_r12")
        text = response.text.lower()
        # These would indicate actual DXF content
        dxf_tokens = ["ac1009", "ac1015", "ac1024", "endsec", "entities"]
        for token in dxf_tokens:
            assert token not in text

    def test_no_gcode_tokens_in_response(self, client):
        """Response should not contain G-code tokens."""
        response = client.get("/api/cam/translators/readiness/body_outline_dxf_r12")
        text = response.text
        gcode_tokens = ["G00", "G01", "M03", "M05", "M30"]
        for token in gcode_tokens:
            assert token not in text

    def test_all_endpoints_enforce_invariants(self, client):
        """All endpoints should enforce 7G invariants."""
        # Test list endpoint
        response = client.get("/api/cam/translators/readiness")
        assert response.status_code == 200
        for item in response.json():
            assert item.get("execution_ready") is False

        # Test evaluate endpoint
        response = client.post(
            "/api/cam/translators/readiness/evaluate",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["execution_ready"] is False
        assert data["machine_operation_authorized"] is False
        assert data["promotion_authorized"] is False
