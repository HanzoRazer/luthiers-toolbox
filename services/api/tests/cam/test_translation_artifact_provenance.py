"""
Tests for Translation Artifact Provenance (CAM Dev Order 7F)

Tests immutable governance lineage and provenance tracking:
  - Deterministic lineage hashing
  - Provenance model invariants
  - Provenance builder
  - Introspection endpoints
  - RMOS persistence

Core rule: Governance ancestry, NOT artifact revision control.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.translation_artifact import (
    TranslationArtifact,
    build_validation_translation_artifact,
)
from app.cam.translation_artifact_provenance import (
    TranslationArtifactProvenance,
    TranslationArtifactProvenanceSummary,
    build_translation_artifact_provenance,
    compute_deterministic_lineage_hash,
    compute_snapshot_hash,
    get_provenance,
    get_provenance_by_artifact,
    get_provenance_by_lineage_hash,
    list_provenances,
    clear_provenance_index,
    PROVENANCE_INDEX,
)
from app.cam.translator_capability_registry import get_translator_capability
from app.cam.nut_slot_cam import NutSlotPreviewRequest, generate_nut_slot_preview
from app.cam.nut_slot_export import create_nut_slot_export_object


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_provenance_index():
    """Clear provenance index before each test."""
    clear_provenance_index()
    yield
    clear_provenance_index()


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


def create_sample_audit_ledger() -> dict:
    """Create sample audit ledger for testing."""
    return {
        "audit_id": "audit-123",
        "deterministic_hash": "a" * 64,
        "lifecycle_gate": "green",
    }


def create_sample_promotion_evidence() -> dict:
    """Create sample promotion evidence for testing."""
    return {
        "evidence_id": "evidence-456",
        "evidence_hash": "b" * 64,
        "promoted": True,
    }


def create_sample_lifecycle_report() -> dict:
    """Create sample lifecycle report for testing."""
    return {
        "lifecycle_gate": "green",
        "export_ready": True,
        "machine_ready": False,
    }


# -----------------------------------------------------------------------------
# Deterministic Lineage Hash Tests
# -----------------------------------------------------------------------------

class TestDeterministicLineageHash:
    """Tests for deterministic lineage hashing."""

    def test_same_ancestry_same_hash(self):
        """Same governance ancestry produces same lineage hash."""
        hash1 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=["audit1", "audit2"],
            parent_promotion_evidence_hashes=["evidence1"],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy123",
            lifecycle_snapshot_hash="lifecycle123",
        )

        hash2 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=["audit1", "audit2"],
            parent_promotion_evidence_hashes=["evidence1"],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy123",
            lifecycle_snapshot_hash="lifecycle123",
        )

        assert hash1 == hash2

    def test_changing_audit_hash_changes_lineage(self):
        """Changing audit hash produces different lineage hash."""
        hash1 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=["audit1"],
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy123",
            lifecycle_snapshot_hash="lifecycle123",
        )

        hash2 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=["audit2"],  # Changed
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy123",
            lifecycle_snapshot_hash="lifecycle123",
        )

        assert hash1 != hash2

    def test_changing_policy_snapshot_changes_lineage(self):
        """Changing policy snapshot produces different lineage hash."""
        hash1 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=[],
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy1",
            lifecycle_snapshot_hash="lifecycle123",
        )

        hash2 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=[],
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy2",  # Changed
            lifecycle_snapshot_hash="lifecycle123",
        )

        assert hash1 != hash2

    def test_changing_export_object_hash_changes_lineage(self):
        """Changing export object hash produces different lineage hash."""
        hash1 = compute_deterministic_lineage_hash(
            source_export_object_hash="export1",
            parent_audit_hashes=[],
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy123",
            lifecycle_snapshot_hash="lifecycle123",
        )

        hash2 = compute_deterministic_lineage_hash(
            source_export_object_hash="export2",  # Changed
            parent_audit_hashes=[],
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy123",
            lifecycle_snapshot_hash="lifecycle123",
        )

        assert hash1 != hash2

    def test_hash_is_sha256(self):
        """Lineage hash is 64 characters (SHA256 hex)."""
        hash_value = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=[],
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="policy123",
            lifecycle_snapshot_hash="lifecycle123",
        )

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_audit_hash_order_independent(self):
        """Audit hashes are sorted, so order doesn't matter."""
        hash1 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=["audit2", "audit1"],  # Different order
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="",
            lifecycle_snapshot_hash="",
        )

        hash2 = compute_deterministic_lineage_hash(
            source_export_object_hash="abc123",
            parent_audit_hashes=["audit1", "audit2"],  # Different order
            parent_promotion_evidence_hashes=[],
            translator_capability_hash="cap123",
            policy_snapshot_hash="",
            lifecycle_snapshot_hash="",
        )

        assert hash1 == hash2


# -----------------------------------------------------------------------------
# Provenance Model Tests
# -----------------------------------------------------------------------------

class TestProvenanceModel:
    """Tests for TranslationArtifactProvenance model."""

    def test_provenance_created_with_valid_inputs(self):
        """Provenance can be created with valid inputs."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance is not None
        assert provenance.provenance_id.startswith("prov-")
        assert provenance.artifact_id == artifact.artifact_id

    def test_7f_invariant_immutable_always_true(self):
        """immutable must be True (7F invariant)."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.immutable is True

    def test_7f_invariant_execution_authorized_always_false(self):
        """execution_authorized must be False (7F invariant)."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.execution_authorized is False

    def test_7f_invariant_machine_output_present_always_false(self):
        """machine_output_present must be False (7F invariant)."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.machine_output_present is False

    def test_cannot_create_mutable_provenance(self):
        """Cannot create provenance with immutable=False."""
        with pytest.raises(ValueError, match="immutable must be True"):
            TranslationArtifactProvenance(
                artifact_id="test",
                source_export_object_hash="abc123",
                translator_capability_hash="cap123",
                deterministic_lineage_hash="def456",
                immutable=False,  # Violates 7F
            )

    def test_cannot_create_authorized_provenance(self):
        """Cannot create provenance with execution_authorized=True."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            TranslationArtifactProvenance(
                artifact_id="test",
                source_export_object_hash="abc123",
                translator_capability_hash="cap123",
                deterministic_lineage_hash="def456",
                execution_authorized=True,  # Violates 7F
            )

    def test_cannot_create_machine_output_provenance(self):
        """Cannot create provenance with machine_output_present=True."""
        with pytest.raises(ValueError, match="machine_output_present must be False"):
            TranslationArtifactProvenance(
                artifact_id="test",
                source_export_object_hash="abc123",
                translator_capability_hash="cap123",
                deterministic_lineage_hash="def456",
                machine_output_present=True,  # Violates 7F
            )


# -----------------------------------------------------------------------------
# Provenance Builder Tests
# -----------------------------------------------------------------------------

class TestProvenanceBuilder:
    """Tests for provenance builder function."""

    def test_builder_creates_provenance(self):
        """Builder creates valid provenance."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance is not None
        assert provenance.artifact_id == artifact.artifact_id

    def test_builder_captures_export_object_hash(self):
        """Builder captures source export object hash."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.source_export_object_hash == artifact.source_export_object_hash

    def test_builder_with_audit_ledger(self):
        """Builder captures audit ledger hash."""
        artifact = create_valid_artifact()
        audit = create_sample_audit_ledger()

        provenance = build_translation_artifact_provenance(
            artifact=artifact,
            audit_ledger=audit,
        )

        assert audit["deterministic_hash"] in provenance.parent_audit_hashes

    def test_builder_with_promotion_evidence(self):
        """Builder captures promotion evidence hash."""
        artifact = create_valid_artifact()
        evidence = create_sample_promotion_evidence()

        provenance = build_translation_artifact_provenance(
            artifact=artifact,
            promotion_evidence=evidence,
        )

        assert evidence["evidence_hash"] in provenance.parent_promotion_evidence_hashes

    def test_builder_registers_in_index(self):
        """Builder registers provenance in index."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        retrieved = get_provenance(provenance.provenance_id)
        assert retrieved is not None
        assert retrieved.provenance_id == provenance.provenance_id

    def test_builder_metadata_includes_dev_order(self):
        """Builder metadata includes dev_order=7F."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.metadata.get("dev_order") == "7F"


# -----------------------------------------------------------------------------
# Provenance Index Tests
# -----------------------------------------------------------------------------

class TestProvenanceIndex:
    """Tests for provenance index operations."""

    def test_get_provenance_by_id(self):
        """Can retrieve provenance by ID."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        retrieved = get_provenance(provenance.provenance_id)

        assert retrieved is not None
        assert retrieved.provenance_id == provenance.provenance_id

    def test_get_provenance_unknown_returns_none(self):
        """Unknown provenance ID returns None."""
        assert get_provenance("unknown-provenance") is None

    def test_get_provenance_by_artifact(self):
        """Can retrieve provenances by artifact ID."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        provenances = get_provenance_by_artifact(artifact.artifact_id)

        assert len(provenances) == 1
        assert provenances[0].provenance_id == provenance.provenance_id

    def test_multiple_provenances_per_artifact(self):
        """Same artifact can have multiple provenances."""
        artifact = create_valid_artifact()

        # Create first provenance
        prov1 = build_translation_artifact_provenance(artifact)

        # Create second provenance with different governance context
        prov2 = build_translation_artifact_provenance(
            artifact=artifact,
            audit_ledger=create_sample_audit_ledger(),
        )

        provenances = get_provenance_by_artifact(artifact.artifact_id)

        assert len(provenances) == 2
        assert prov1.provenance_id in [p.provenance_id for p in provenances]
        assert prov2.provenance_id in [p.provenance_id for p in provenances]

    def test_get_provenance_by_lineage_hash(self):
        """Can retrieve provenance by lineage hash."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        retrieved = get_provenance_by_lineage_hash(
            provenance.deterministic_lineage_hash
        )

        assert retrieved is not None
        assert retrieved.provenance_id == provenance.provenance_id

    def test_list_provenances(self):
        """Can list all provenances."""
        artifact1 = create_valid_artifact()
        artifact2 = create_valid_artifact()

        prov1 = build_translation_artifact_provenance(artifact1)
        prov2 = build_translation_artifact_provenance(artifact2)

        all_provenances = list_provenances()

        assert len(all_provenances) == 2


# -----------------------------------------------------------------------------
# Provenance Summary Tests
# -----------------------------------------------------------------------------

class TestProvenanceSummary:
    """Tests for provenance summary."""

    def test_summary_from_provenance(self):
        """Can create summary from full provenance."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        summary = provenance.to_summary()

        assert summary.provenance_id == provenance.provenance_id
        assert summary.deterministic_lineage_hash == provenance.deterministic_lineage_hash

    def test_summary_7f_invariants(self):
        """Summary maintains 7F invariants."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        summary = provenance.to_summary()

        assert summary.immutable is True
        assert summary.execution_authorized is False


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestProvenanceEndpoints:
    """Tests for provenance introspection endpoints."""

    def test_list_provenances_endpoint(self):
        """GET /api/cam/translation-provenance returns all provenances."""
        artifact = create_valid_artifact()
        build_translation_artifact_provenance(artifact)

        response = client.get("/api/cam/translation-provenance")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert data["all_immutable"] is True
        assert data["execution_authorized_count"] == 0

    def test_get_provenance_endpoint(self):
        """GET /api/cam/translation-provenance/{id} returns provenance."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        response = client.get(
            f"/api/cam/translation-provenance/{provenance.provenance_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provenance"]["provenance_id"] == provenance.provenance_id
        assert data["immutable"] is True
        assert data["execution_authorized"] is False

    def test_get_provenance_not_found(self):
        """GET /api/cam/translation-provenance/{id} returns 404 for unknown."""
        response = client.get("/api/cam/translation-provenance/unknown-prov")

        assert response.status_code == 404

    def test_get_provenances_by_artifact_endpoint(self):
        """GET /api/cam/translation-provenance/by-artifact/{id} returns provenances."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        response = client.get(
            f"/api/cam/translation-provenance/by-artifact/{artifact.artifact_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_get_provenance_by_lineage_hash_endpoint(self):
        """GET /api/cam/translation-provenance/by-lineage-hash/{hash} works."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        response = client.get(
            f"/api/cam/translation-provenance/by-lineage-hash/{provenance.deterministic_lineage_hash}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provenance"]["provenance_id"] == provenance.provenance_id

    def test_list_summaries_endpoint(self):
        """GET /api/cam/translation-provenance/summaries returns summaries."""
        artifact = create_valid_artifact()
        build_translation_artifact_provenance(artifact)

        response = client.get("/api/cam/translation-provenance/summaries")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert len(data["summaries"]) >= 1


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Tests verifying no execution or machine output."""

    def test_provenance_no_dxf_tokens(self):
        """Provenance JSON contains no DXF tokens."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)
        json_output = provenance.model_dump_json()

        forbidden = ['"SECTION"', '"ENTITIES"', '"POLYLINE"', '"EOF"']
        for token in forbidden:
            assert token not in json_output, f"Found forbidden DXF token: {token}"

    def test_provenance_no_gcode_tokens(self):
        """Provenance JSON contains no G-code tokens."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)
        json_output = provenance.model_dump_json()

        forbidden = ["G0 ", "G1 ", "G2 ", "M3 ", "M5 "]
        for token in forbidden:
            assert token not in json_output, f"Found forbidden G-code token: {token}"

    def test_immutable_always_true(self):
        """immutable is always True."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.immutable is True

    def test_execution_authorized_always_false(self):
        """execution_authorized is always False."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.execution_authorized is False

    def test_machine_output_present_always_false(self):
        """machine_output_present is always False."""
        artifact = create_valid_artifact()
        provenance = build_translation_artifact_provenance(artifact)

        assert provenance.machine_output_present is False

    def test_all_endpoints_enforce_invariants(self):
        """All endpoint responses enforce 7F invariants."""
        artifact = create_valid_artifact()
        build_translation_artifact_provenance(artifact)

        response = client.get("/api/cam/translation-provenance")
        data = response.json()

        assert data["all_immutable"] is True
        assert data["execution_authorized_count"] == 0

        for prov in data["provenances"]:
            assert prov["immutable"] is True
            assert prov["execution_authorized"] is False
            assert prov["machine_output_present"] is False
