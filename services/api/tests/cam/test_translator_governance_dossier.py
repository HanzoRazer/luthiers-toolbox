"""
Tests for Translator Governance Escalation Dossier (CAM Dev Order 7I)

Verifies:
  - 7I invariants (execution_authorized=false, immutable=true, etc.)
  - Deterministic dossier hashing
  - Governance evidence aggregation
  - Required inputs validation
  - Introspection endpoints
  - No execution authorization

Guardrail:
  7I packages complete governance evidence for review.
  It does NOT create approval authority, execution authority,
  or mutation authority.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.cam.translator_governance_dossier import (
    TranslatorGovernanceDossier,
    GovernanceDossierSummary,
    CANONICAL_GOVERNANCE_CONSTRAINTS,
    compute_deterministic_dossier_hash,
    build_governance_escalation_dossier,
    get_governance_dossier,
    list_governance_dossiers,
    list_governance_dossiers_for_translator,
    get_latest_dossier_for_translator,
    clear_governance_dossier_index,
    DossierBuildError,
)
from app.cam.translator_capability_registry import get_translator_capability
from app.cam.translation_artifact import TranslationArtifact
from app.cam.translation_artifact_authorization import (
    evaluate_translation_artifact_authorization,
)
from app.cam.translation_artifact_provenance import (
    build_translation_artifact_provenance,
    clear_provenance_index,
)
from app.cam.translator_readiness_matrix import (
    evaluate_translator_readiness,
    clear_readiness_index,
)
from app.cam.translator_execution_quarantine import (
    evaluate_execution_quarantine,
    get_freeze_manifest,
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
    clear_governance_dossier_index()
    clear_quarantine_index()
    clear_freeze_manifest_index()
    clear_readiness_index()
    clear_provenance_index()
    yield
    clear_governance_dossier_index()
    clear_quarantine_index()
    clear_freeze_manifest_index()
    clear_readiness_index()
    clear_provenance_index()


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


def _create_full_governance_evidence(translator_id: str):
    """Create complete governance evidence for dossier building."""
    # Create artifact
    artifact = _create_test_artifact(translator_id)

    # Build provenance (7F)
    provenance = build_translation_artifact_provenance(artifact)

    # Evaluate readiness (7G)
    readiness = evaluate_translator_readiness(translator_id, artifact=artifact)

    # Evaluate authorization (7E)
    authorization = evaluate_translation_artifact_authorization(artifact)

    # Evaluate quarantine and get freeze manifest (7H)
    quarantine = evaluate_execution_quarantine(
        translator_id,
        readiness_evaluation=readiness,
        provenance=provenance,
    )
    freeze_manifest = get_freeze_manifest(quarantine.freeze_manifest_id)

    return readiness, provenance, authorization, freeze_manifest


class TestDossierInvariants:
    """Test 7I invariants at model level."""

    def test_7i_invariant_execution_authorized_always_false(self):
        """execution_authorized must be False."""
        readiness, provenance, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=authorization,
            freeze_manifest=freeze_manifest,
        )
        assert dossier.execution_authorized is False

    def test_7i_invariant_machine_output_always_false(self):
        """machine_output_allowed must be False."""
        readiness, provenance, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=authorization,
            freeze_manifest=freeze_manifest,
        )
        assert dossier.machine_output_allowed is False

    def test_7i_invariant_immutable_always_true(self):
        """immutable must be True."""
        readiness, provenance, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=authorization,
            freeze_manifest=freeze_manifest,
        )
        assert dossier.immutable is True

    def test_cannot_create_execution_authorized_dossier(self):
        """Should reject execution_authorized=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorGovernanceDossier(
                translator_id="test",
                readiness_gate="green",
                quarantine_state="future_escalation_required",
                authorization_gate="green",
                provenance_hash="abc",
                readiness_hash="def",
                authorization_hash="ghi",
                freeze_manifest_hash="jkl",
                deterministic_dossier_hash="xyz",
                execution_authorized=True,  # Violates 7I
            )
        assert "execution_authorized must be False" in str(exc_info.value)

    def test_cannot_create_machine_output_allowed_dossier(self):
        """Should reject machine_output_allowed=True."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorGovernanceDossier(
                translator_id="test",
                readiness_gate="green",
                quarantine_state="future_escalation_required",
                authorization_gate="green",
                provenance_hash="abc",
                readiness_hash="def",
                authorization_hash="ghi",
                freeze_manifest_hash="jkl",
                deterministic_dossier_hash="xyz",
                machine_output_allowed=True,  # Violates 7I
            )
        assert "machine_output_allowed must be False" in str(exc_info.value)

    def test_cannot_create_mutable_dossier(self):
        """Should reject immutable=False."""
        with pytest.raises(ValidationError) as exc_info:
            TranslatorGovernanceDossier(
                translator_id="test",
                readiness_gate="green",
                quarantine_state="future_escalation_required",
                authorization_gate="green",
                provenance_hash="abc",
                readiness_hash="def",
                authorization_hash="ghi",
                freeze_manifest_hash="jkl",
                deterministic_dossier_hash="xyz",
                immutable=False,  # Violates 7I
            )
        assert "immutable must be True" in str(exc_info.value)


class TestDeterministicHashing:
    """Test deterministic dossier hashing."""

    def test_same_evidence_produces_same_hash(self):
        """Same governance evidence should produce same dossier hash."""
        hash1 = compute_deterministic_dossier_hash(
            provenance_hash="prov123",
            readiness_hash="ready456",
            authorization_hash="auth789",
            freeze_manifest_hash="freeze000",
            lifecycle_hashes=["life1", "life2"],
            audit_hashes=["audit1"],
            promotion_evidence_hashes=["promo1"],
            governance_constraints=["constraint1", "constraint2"],
        )

        hash2 = compute_deterministic_dossier_hash(
            provenance_hash="prov123",
            readiness_hash="ready456",
            authorization_hash="auth789",
            freeze_manifest_hash="freeze000",
            lifecycle_hashes=["life1", "life2"],
            audit_hashes=["audit1"],
            promotion_evidence_hashes=["promo1"],
            governance_constraints=["constraint1", "constraint2"],
        )

        assert hash1 == hash2

    def test_changing_provenance_changes_hash(self):
        """Changing provenance hash should change dossier hash."""
        hash1 = compute_deterministic_dossier_hash(
            provenance_hash="prov123",
            readiness_hash="ready456",
            authorization_hash="auth789",
            freeze_manifest_hash="freeze000",
            lifecycle_hashes=[],
            audit_hashes=[],
            promotion_evidence_hashes=[],
            governance_constraints=[],
        )

        hash2 = compute_deterministic_dossier_hash(
            provenance_hash="prov_DIFFERENT",  # Changed
            readiness_hash="ready456",
            authorization_hash="auth789",
            freeze_manifest_hash="freeze000",
            lifecycle_hashes=[],
            audit_hashes=[],
            promotion_evidence_hashes=[],
            governance_constraints=[],
        )

        assert hash1 != hash2

    def test_changing_readiness_changes_hash(self):
        """Changing readiness hash should change dossier hash."""
        hash1 = compute_deterministic_dossier_hash(
            provenance_hash="prov123",
            readiness_hash="ready456",
            authorization_hash="auth789",
            freeze_manifest_hash="freeze000",
            lifecycle_hashes=[],
            audit_hashes=[],
            promotion_evidence_hashes=[],
            governance_constraints=[],
        )

        hash2 = compute_deterministic_dossier_hash(
            provenance_hash="prov123",
            readiness_hash="ready_DIFFERENT",  # Changed
            authorization_hash="auth789",
            freeze_manifest_hash="freeze000",
            lifecycle_hashes=[],
            audit_hashes=[],
            promotion_evidence_hashes=[],
            governance_constraints=[],
        )

        assert hash1 != hash2

    def test_changing_freeze_manifest_changes_hash(self):
        """Changing freeze manifest hash should change dossier hash."""
        hash1 = compute_deterministic_dossier_hash(
            provenance_hash="prov123",
            readiness_hash="ready456",
            authorization_hash="auth789",
            freeze_manifest_hash="freeze000",
            lifecycle_hashes=[],
            audit_hashes=[],
            promotion_evidence_hashes=[],
            governance_constraints=[],
        )

        hash2 = compute_deterministic_dossier_hash(
            provenance_hash="prov123",
            readiness_hash="ready456",
            authorization_hash="auth789",
            freeze_manifest_hash="freeze_DIFFERENT",  # Changed
            lifecycle_hashes=[],
            audit_hashes=[],
            promotion_evidence_hashes=[],
            governance_constraints=[],
        )

        assert hash1 != hash2

    def test_hash_is_sha256(self):
        """Dossier hash should be SHA256 (64 hex chars)."""
        hash_val = compute_deterministic_dossier_hash(
            provenance_hash="prov",
            readiness_hash="ready",
            authorization_hash="auth",
            freeze_manifest_hash="freeze",
            lifecycle_hashes=[],
            audit_hashes=[],
            promotion_evidence_hashes=[],
            governance_constraints=[],
        )
        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)


class TestDossierBuilder:
    """Test dossier builder function."""

    def test_builder_creates_dossier(self):
        """Builder should create dossier from complete evidence."""
        readiness, provenance, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=authorization,
            freeze_manifest=freeze_manifest,
        )

        assert dossier.translator_id == "body_outline_dxf_r12"
        assert dossier.dossier_id.startswith("dossier-")
        assert dossier.deterministic_dossier_hash != ""

    def test_builder_requires_readiness(self):
        """Builder should fail without readiness evaluation."""
        _, provenance, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        with pytest.raises(DossierBuildError) as exc_info:
            build_governance_escalation_dossier(
                readiness_evaluation=None,
                provenance=provenance,
                authorization_evaluation=authorization,
                freeze_manifest=freeze_manifest,
            )
        assert "Missing required readiness_evaluation" in str(exc_info.value)

    def test_builder_requires_provenance(self):
        """Builder should fail without provenance."""
        readiness, _, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        with pytest.raises(DossierBuildError) as exc_info:
            build_governance_escalation_dossier(
                readiness_evaluation=readiness,
                provenance=None,
                authorization_evaluation=authorization,
                freeze_manifest=freeze_manifest,
            )
        assert "Missing required provenance" in str(exc_info.value)

    def test_builder_requires_authorization(self):
        """Builder should fail without authorization evaluation."""
        readiness, provenance, _, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        with pytest.raises(DossierBuildError) as exc_info:
            build_governance_escalation_dossier(
                readiness_evaluation=readiness,
                provenance=provenance,
                authorization_evaluation=None,
                freeze_manifest=freeze_manifest,
            )
        assert "Missing required authorization_evaluation" in str(exc_info.value)

    def test_builder_requires_freeze_manifest(self):
        """Builder should fail without freeze manifest."""
        readiness, provenance, authorization, _ = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        with pytest.raises(DossierBuildError) as exc_info:
            build_governance_escalation_dossier(
                readiness_evaluation=readiness,
                provenance=provenance,
                authorization_evaluation=authorization,
                freeze_manifest=None,
            )
        assert "Missing required freeze_manifest" in str(exc_info.value)

    def test_builder_registers_in_index(self):
        """Builder should register dossier in index."""
        readiness, provenance, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=authorization,
            freeze_manifest=freeze_manifest,
        )

        indexed = get_governance_dossier(dossier.dossier_id)
        assert indexed is not None
        assert indexed.dossier_id == dossier.dossier_id

    def test_builder_populates_governance_constraints(self):
        """Builder should populate canonical governance constraints."""
        readiness, provenance, authorization, freeze_manifest = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=authorization,
            freeze_manifest=freeze_manifest,
        )

        for constraint in CANONICAL_GOVERNANCE_CONSTRAINTS:
            assert constraint in dossier.governance_constraints


class TestDossierIndex:
    """Test in-memory dossier index."""

    def test_list_dossiers(self):
        """Should list all dossiers."""
        readiness1, provenance1, auth1, freeze1 = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        build_governance_escalation_dossier(
            readiness_evaluation=readiness1,
            provenance=provenance1,
            authorization_evaluation=auth1,
            freeze_manifest=freeze1,
        )

        readiness2, provenance2, auth2, freeze2 = _create_full_governance_evidence(
            "dxf_r12"
        )
        build_governance_escalation_dossier(
            readiness_evaluation=readiness2,
            provenance=provenance2,
            authorization_evaluation=auth2,
            freeze_manifest=freeze2,
        )

        dossiers = list_governance_dossiers()
        assert len(dossiers) >= 2

    def test_list_dossiers_for_translator(self):
        """Should list dossiers filtered by translator."""
        readiness, provenance, auth, freeze = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=auth,
            freeze_manifest=freeze,
        )

        dossiers = list_governance_dossiers_for_translator("body_outline_dxf_r12")
        assert len(dossiers) >= 1
        assert all(d.translator_id == "body_outline_dxf_r12" for d in dossiers)

    def test_get_latest_dossier_for_translator(self):
        """Should get most recent dossier for translator."""
        readiness, provenance, auth, freeze = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        d1 = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=auth,
            freeze_manifest=freeze,
        )

        # Create another
        readiness2, provenance2, auth2, freeze2 = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        d2 = build_governance_escalation_dossier(
            readiness_evaluation=readiness2,
            provenance=provenance2,
            authorization_evaluation=auth2,
            freeze_manifest=freeze2,
        )

        latest = get_latest_dossier_for_translator("body_outline_dxf_r12")
        assert latest is not None
        assert latest.dossier_id == d2.dossier_id


class TestDossierSummary:
    """Test dossier summary for 7H integration."""

    def test_to_summary_preserves_key_fields(self):
        """Summary should preserve key fields."""
        readiness, provenance, auth, freeze = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=auth,
            freeze_manifest=freeze,
        )

        summary = dossier.to_summary()
        assert summary.dossier_id == dossier.dossier_id
        assert summary.translator_id == dossier.translator_id
        assert summary.readiness_gate == dossier.readiness_gate
        assert summary.quarantine_state == dossier.quarantine_state
        assert summary.deterministic_dossier_hash == dossier.deterministic_dossier_hash

    def test_summary_enforces_invariants(self):
        """Summary should enforce 7I invariants."""
        readiness, provenance, auth, freeze = _create_full_governance_evidence(
            "body_outline_dxf_r12"
        )
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness,
            provenance=provenance,
            authorization_evaluation=auth,
            freeze_manifest=freeze,
        )

        summary = dossier.to_summary()
        assert summary.immutable is True
        assert summary.execution_authorized is False


class TestDossierEndpoints:
    """Test REST API endpoints."""

    def test_list_dossiers_endpoint(self, client):
        """GET /api/cam/translators/governance-dossiers should return list."""
        response = client.get("/api/cam/translators/governance-dossiers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_dossier_policy_endpoint(self, client):
        """GET /api/cam/translators/governance-dossiers/policy should return policy."""
        response = client.get("/api/cam/translators/governance-dossiers/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["immutable"] is True
        assert len(data["governance_constraints"]) == 6

    def test_build_dossier_endpoint(self, client):
        """POST /api/cam/translators/governance-dossier/build should build dossier."""
        response = client.post(
            "/api/cam/translators/governance-dossier/build",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["immutable"] is True

    def test_get_dossier_endpoint(self, client):
        """GET /api/cam/translators/governance-dossiers/{id} should return dossier."""
        # Build a dossier first
        response = client.post(
            "/api/cam/translators/governance-dossier/build",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        dossier_id = response.json()["dossier_id"]

        # Get it
        response = client.get(f"/api/cam/translators/governance-dossiers/{dossier_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["dossier_id"] == dossier_id

    def test_dossier_not_found(self, client):
        """Should return 404 for unknown dossier."""
        response = client.get("/api/cam/translators/governance-dossiers/unknown-dossier")
        assert response.status_code == 404

    def test_get_dossiers_by_translator_endpoint(self, client):
        """GET /api/cam/translators/governance-dossiers/by-translator/{id} should return list."""
        # Build a dossier first
        client.post(
            "/api/cam/translators/governance-dossier/build",
            json={"translator_id": "body_outline_dxf_r12"},
        )

        response = client.get(
            "/api/cam/translators/governance-dossiers/by-translator/body_outline_dxf_r12"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestSafetyAssertions:
    """Safety assertions for 7I — no execution artifacts."""

    def test_no_dxf_tokens_in_response(self, client):
        """Response should not contain DXF content tokens."""
        response = client.post(
            "/api/cam/translators/governance-dossier/build",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        text = response.text.lower()
        dxf_tokens = ["ac1009", "ac1015", "ac1024", "endsec", "entities"]
        for token in dxf_tokens:
            assert token not in text

    def test_no_gcode_tokens_in_response(self, client):
        """Response should not contain G-code tokens."""
        response = client.post(
            "/api/cam/translators/governance-dossier/build",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        text = response.text
        gcode_tokens = ["G00", "G01", "M03", "M05", "M30"]
        for token in gcode_tokens:
            assert token not in text

    def test_all_endpoints_enforce_invariants(self, client):
        """All endpoints should enforce 7I invariants."""
        # Test policy endpoint
        response = client.get("/api/cam/translators/governance-dossiers/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["immutable"] is True

        # Test build endpoint
        response = client.post(
            "/api/cam/translators/governance-dossier/build",
            json={"translator_id": "body_outline_dxf_r12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["immutable"] is True


class TestCanonicalConstraints:
    """Test canonical governance constraints."""

    def test_canonical_constraints_count(self):
        """Should have 6 canonical governance constraints."""
        assert len(CANONICAL_GOVERNANCE_CONSTRAINTS) == 6

    def test_canonical_constraints_content(self):
        """Should have correct governance constraints."""
        expected = [
            "execution_runtime_absent",
            "serializer_invocation_prohibited",
            "machine_output_prohibited",
            "plugin_loading_prohibited",
            "human_approval_required",
            "governance_escalation_required",
        ]
        assert set(CANONICAL_GOVERNANCE_CONSTRAINTS) == set(expected)
