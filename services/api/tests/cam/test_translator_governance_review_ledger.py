"""
Tests for Translator Governance Review Ledger (7K)

CAM Dev Order 7K: Immutable governance review trace chain.

7K invariants:
  - immutable = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7K records governance review trace ancestry. It must not mutate
  prior entries, approval state, or execution authority.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.cam.translator_governance_review_ledger import (
    TranslatorGovernanceReviewLedgerEntry,
    GovernanceReviewLedgerSummary,
    REVIEW_LEDGER_INDEX,
    UNRESOLVED_HASH_PLACEHOLDER,
    register_review_ledger_entry,
    get_review_ledger_entry,
    list_review_ledger_entries,
    list_review_ledger_entries_for_translator,
    get_latest_ledger_entry_for_translator,
    clear_review_ledger_index,
    build_governance_review_ledger_entry,
    build_governance_review_ledger_entry_by_matrix_id,
    get_lineage_chain,
    to_summary,
    LedgerBuildError,
    DuplicateLedgerEntryError,
    _compute_review_trace_hash,
    _extract_hash,
    _auto_detect_parent_hashes,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_index():
    """Clear ledger index before each test."""
    clear_review_ledger_index()
    yield
    clear_review_ledger_index()


def _create_mock_review_matrix(
    review_matrix_id: str = "review-test-123",
    dossier_id: str = "dossier-test-123",
    translator_id: str = "body_outline_dxf_r12",
    review_gate: str = "green",
    review_readiness_score: int = 100,
    review_state: str = "review_only",
    evidence_hash: str = "matrix_hash_123",
    blockers: list = None,
) -> MagicMock:
    """Create a mock review matrix for testing."""
    matrix = MagicMock()
    matrix.review_matrix_id = review_matrix_id
    matrix.dossier_id = dossier_id
    matrix.translator_id = translator_id
    matrix.review_gate = review_gate
    matrix.review_readiness_score = review_readiness_score
    matrix.review_state = review_state
    matrix.evidence_hash = evidence_hash
    matrix.blockers = blockers or []
    return matrix


def _create_mock_dossier(
    dossier_id: str = "dossier-test-123",
    deterministic_dossier_hash: str = "dossier_hash_123",
    governance_constraints: list = None,
) -> MagicMock:
    """Create a mock dossier for testing."""
    dossier = MagicMock()
    dossier.dossier_id = dossier_id
    dossier.deterministic_dossier_hash = deterministic_dossier_hash
    dossier.governance_constraints = governance_constraints or ["no_dxf", "no_gcode"]
    return dossier


def _create_mock_provenance(
    lineage_hash: str = "provenance_hash_123",
) -> MagicMock:
    """Create a mock provenance for testing."""
    provenance = MagicMock()
    provenance.deterministic_lineage_hash = lineage_hash
    return provenance


def _create_mock_readiness(
    readiness_hash: str = "readiness_hash_123",
) -> MagicMock:
    """Create a mock readiness for testing."""
    readiness = MagicMock()
    readiness.deterministic_readiness_hash = readiness_hash
    return readiness


def _create_mock_quarantine(
    freeze_manifest_hash: str = "quarantine_hash_123",
) -> MagicMock:
    """Create a mock quarantine for testing."""
    quarantine = MagicMock()
    quarantine.freeze_manifest_hash = freeze_manifest_hash
    return quarantine


def _create_mock_authorization(
    authorization_hash: str = "authorization_hash_123",
) -> MagicMock:
    """Create a mock authorization for testing."""
    authorization = MagicMock()
    authorization.deterministic_authorization_hash = authorization_hash
    return authorization


def _create_complete_ledger_entry() -> TranslatorGovernanceReviewLedgerEntry:
    """Create a complete ledger entry using the builder."""
    matrix = _create_mock_review_matrix()
    dossier = _create_mock_dossier()
    provenance = _create_mock_provenance()
    readiness = _create_mock_readiness()
    quarantine = _create_mock_quarantine()
    authorization = _create_mock_authorization()

    # Clear index to avoid duplicate errors
    clear_review_ledger_index()

    return build_governance_review_ledger_entry(
        review_matrix=matrix,
        dossier=dossier,
        provenance=provenance,
        readiness=readiness,
        quarantine=quarantine,
        authorization=authorization,
    )


# -----------------------------------------------------------------------------
# Test 7K Invariants
# -----------------------------------------------------------------------------

class TestLedgerInvariants:
    """Test 7K model-enforced invariants."""

    def test_7k_invariant_immutable_always_true(self):
        """immutable must always be true."""
        entry = _create_complete_ledger_entry()
        assert entry.immutable is True

    def test_7k_invariant_execution_authorized_always_false(self):
        """execution_authorized must always be false."""
        entry = _create_complete_ledger_entry()
        assert entry.execution_authorized is False

    def test_7k_invariant_machine_output_always_false(self):
        """machine_output_allowed must always be false."""
        entry = _create_complete_ledger_entry()
        assert entry.machine_output_allowed is False

    def test_cannot_create_mutable_entry(self):
        """Creating an entry with immutable=false must fail."""
        with pytest.raises(ValueError, match="7K invariant violation"):
            TranslatorGovernanceReviewLedgerEntry(
                ledger_entry_id="test-001",
                review_matrix_id="matrix-001",
                dossier_id="dossier-001",
                translator_id="test_translator",
                review_gate="green",
                review_readiness_score=100,
                provenance_hash="hash1",
                readiness_hash="hash2",
                quarantine_hash="hash3",
                authorization_hash="hash4",
                dossier_hash="hash5",
                review_matrix_hash="hash6",
                review_trace_hash="trace_hash",
                immutable=False,  # Must fail
            )

    def test_cannot_create_execution_authorized_entry(self):
        """Creating an entry with execution_authorized=true must fail."""
        with pytest.raises(ValueError, match="7K invariant violation"):
            TranslatorGovernanceReviewLedgerEntry(
                ledger_entry_id="test-001",
                review_matrix_id="matrix-001",
                dossier_id="dossier-001",
                translator_id="test_translator",
                review_gate="green",
                review_readiness_score=100,
                provenance_hash="hash1",
                readiness_hash="hash2",
                quarantine_hash="hash3",
                authorization_hash="hash4",
                dossier_hash="hash5",
                review_matrix_hash="hash6",
                review_trace_hash="trace_hash",
                execution_authorized=True,  # Must fail
            )

    def test_cannot_create_machine_output_allowed_entry(self):
        """Creating an entry with machine_output_allowed=true must fail."""
        with pytest.raises(ValueError, match="7K invariant violation"):
            TranslatorGovernanceReviewLedgerEntry(
                ledger_entry_id="test-001",
                review_matrix_id="matrix-001",
                dossier_id="dossier-001",
                translator_id="test_translator",
                review_gate="green",
                review_readiness_score=100,
                provenance_hash="hash1",
                readiness_hash="hash2",
                quarantine_hash="hash3",
                authorization_hash="hash4",
                dossier_hash="hash5",
                review_matrix_hash="hash6",
                review_trace_hash="trace_hash",
                machine_output_allowed=True,  # Must fail
            )


# -----------------------------------------------------------------------------
# Test Deterministic Review Trace Hashing
# -----------------------------------------------------------------------------

class TestDeterministicHashing:
    """Test deterministic review trace hashing."""

    def test_same_ancestry_produces_same_hash(self):
        """Same governance review ancestry produces same review trace hash."""
        hash1 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash",
            dossier_hash="dossier_hash",
            provenance_hash="prov_hash",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=["constraint1", "constraint2"],
            parent_ledger_hashes=["parent1", "parent2"],
        )
        hash2 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash",
            dossier_hash="dossier_hash",
            provenance_hash="prov_hash",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=["constraint1", "constraint2"],
            parent_ledger_hashes=["parent1", "parent2"],
        )
        assert hash1 == hash2

    def test_changing_provenance_changes_hash(self):
        """Changing provenance hash changes review trace hash."""
        hash1 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash",
            dossier_hash="dossier_hash",
            provenance_hash="prov_hash_1",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=[],
            parent_ledger_hashes=[],
        )
        hash2 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash",
            dossier_hash="dossier_hash",
            provenance_hash="prov_hash_2",  # Changed
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=[],
            parent_ledger_hashes=[],
        )
        assert hash1 != hash2

    def test_changing_review_matrix_changes_hash(self):
        """Changing review matrix hash changes review trace hash."""
        hash1 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash_1",
            dossier_hash="dossier_hash",
            provenance_hash="prov_hash",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=[],
            parent_ledger_hashes=[],
        )
        hash2 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash_2",  # Changed
            dossier_hash="dossier_hash",
            provenance_hash="prov_hash",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=[],
            parent_ledger_hashes=[],
        )
        assert hash1 != hash2

    def test_changing_dossier_changes_hash(self):
        """Changing dossier hash changes review trace hash."""
        hash1 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash",
            dossier_hash="dossier_hash_1",
            provenance_hash="prov_hash",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=[],
            parent_ledger_hashes=[],
        )
        hash2 = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash",
            dossier_hash="dossier_hash_2",  # Changed
            provenance_hash="prov_hash",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=[],
            parent_ledger_hashes=[],
        )
        assert hash1 != hash2

    def test_hash_is_sha256(self):
        """Review trace hash is valid SHA256."""
        hash_val = _compute_review_trace_hash(
            review_matrix_hash="matrix_hash",
            dossier_hash="dossier_hash",
            provenance_hash="prov_hash",
            readiness_hash="read_hash",
            quarantine_hash="quar_hash",
            authorization_hash="auth_hash",
            governance_constraints=[],
            parent_ledger_hashes=[],
        )
        assert len(hash_val) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in hash_val)


# -----------------------------------------------------------------------------
# Test Ledger Builder
# -----------------------------------------------------------------------------

class TestLedgerBuilder:
    """Test ledger entry builder."""

    def test_builder_creates_entry(self):
        """Builder creates ledger entry successfully."""
        matrix = _create_mock_review_matrix()
        entry = build_governance_review_ledger_entry(review_matrix=matrix)

        assert entry.review_matrix_id == "review-test-123"
        assert entry.translator_id == "body_outline_dxf_r12"
        assert entry.review_gate == "green"
        assert entry.immutable is True
        assert entry.execution_authorized is False
        assert entry.machine_output_allowed is False

    def test_builder_requires_review_matrix(self):
        """Builder requires review_matrix."""
        with pytest.raises(LedgerBuildError, match="review_matrix is required"):
            build_governance_review_ledger_entry(review_matrix=None)

    def test_builder_extracts_hashes_from_objects(self):
        """Builder extracts hashes from provided objects."""
        matrix = _create_mock_review_matrix()
        dossier = _create_mock_dossier(deterministic_dossier_hash="custom_dossier_hash")
        provenance = _create_mock_provenance(lineage_hash="custom_prov_hash")

        entry = build_governance_review_ledger_entry(
            review_matrix=matrix,
            dossier=dossier,
            provenance=provenance,
        )

        assert entry.dossier_hash == "custom_dossier_hash"
        assert entry.provenance_hash == "custom_prov_hash"

    def test_builder_tracks_unresolved_hashes(self):
        """Builder tracks unresolved hashes."""
        matrix = _create_mock_review_matrix()
        # Don't provide provenance, readiness, etc.

        entry = build_governance_review_ledger_entry(review_matrix=matrix)

        # Should have unresolved hashes for missing objects
        assert len(entry.unresolved_hashes) > 0
        assert "provenance_hash" in entry.unresolved_hashes

    def test_builder_registers_in_index(self):
        """Builder registers entry in index."""
        matrix = _create_mock_review_matrix()
        entry = build_governance_review_ledger_entry(review_matrix=matrix)

        retrieved = get_review_ledger_entry(entry.ledger_entry_id)
        assert retrieved is not None
        assert retrieved.ledger_entry_id == entry.ledger_entry_id


# -----------------------------------------------------------------------------
# Test Parent Detection and Lineage
# -----------------------------------------------------------------------------

class TestParentDetection:
    """Test parent ledger hash detection."""

    def test_genesis_entry_has_empty_parents(self):
        """First entry (genesis) has empty parent_ledger_hashes."""
        matrix = _create_mock_review_matrix()
        entry = build_governance_review_ledger_entry(review_matrix=matrix)

        assert entry.parent_ledger_hashes == []

    def test_subsequent_entry_has_parent(self):
        """Subsequent entries auto-detect parent."""
        # Create first entry
        matrix1 = _create_mock_review_matrix(review_matrix_id="matrix-1")
        entry1 = build_governance_review_ledger_entry(review_matrix=matrix1)

        # Create second entry for same translator
        matrix2 = _create_mock_review_matrix(review_matrix_id="matrix-2")
        entry2 = build_governance_review_ledger_entry(review_matrix=matrix2)

        assert len(entry2.parent_ledger_hashes) == 1
        assert entry1.review_trace_hash in entry2.parent_ledger_hashes

    def test_explicit_parent_override(self):
        """Explicit parent_ledger_hashes overrides auto-detect."""
        matrix = _create_mock_review_matrix()
        explicit_parents = ["explicit_parent_hash_1", "explicit_parent_hash_2"]

        entry = build_governance_review_ledger_entry(
            review_matrix=matrix,
            parent_ledger_hashes=explicit_parents,
        )

        assert entry.parent_ledger_hashes == explicit_parents

    def test_lineage_chain_traversal(self):
        """get_lineage_chain traverses ancestry."""
        # Create three entries in sequence
        matrix1 = _create_mock_review_matrix(review_matrix_id="matrix-1")
        entry1 = build_governance_review_ledger_entry(review_matrix=matrix1)

        matrix2 = _create_mock_review_matrix(review_matrix_id="matrix-2")
        entry2 = build_governance_review_ledger_entry(review_matrix=matrix2)

        matrix3 = _create_mock_review_matrix(review_matrix_id="matrix-3")
        entry3 = build_governance_review_ledger_entry(review_matrix=matrix3)

        # Get lineage chain starting from entry3
        chain = get_lineage_chain(entry3.ledger_entry_id)

        assert len(chain) == 3
        assert chain[0].ledger_entry_id == entry3.ledger_entry_id
        assert chain[1].ledger_entry_id == entry2.ledger_entry_id
        assert chain[2].ledger_entry_id == entry1.ledger_entry_id


# -----------------------------------------------------------------------------
# Test Duplicate Protection
# -----------------------------------------------------------------------------

class TestDuplicateProtection:
    """Test duplicate ledger entry ID protection."""

    def test_duplicate_id_raises_error(self):
        """Registering duplicate ID raises DuplicateLedgerEntryError."""
        entry = TranslatorGovernanceReviewLedgerEntry(
            ledger_entry_id="duplicate-test",
            review_matrix_id="matrix-001",
            dossier_id="dossier-001",
            translator_id="test_translator",
            review_gate="green",
            review_readiness_score=100,
            provenance_hash="hash1",
            readiness_hash="hash2",
            quarantine_hash="hash3",
            authorization_hash="hash4",
            dossier_hash="hash5",
            review_matrix_hash="hash6",
            review_trace_hash="trace_hash",
        )

        register_review_ledger_entry(entry)

        # Try to register again with same ID
        with pytest.raises(DuplicateLedgerEntryError):
            register_review_ledger_entry(entry)


# -----------------------------------------------------------------------------
# Test Index Operations
# -----------------------------------------------------------------------------

class TestIndexOperations:
    """Test in-memory index operations."""

    def test_register_and_get(self):
        """Register and retrieve a ledger entry."""
        matrix = _create_mock_review_matrix()
        entry = build_governance_review_ledger_entry(review_matrix=matrix)

        retrieved = get_review_ledger_entry(entry.ledger_entry_id)
        assert retrieved is not None
        assert retrieved.ledger_entry_id == entry.ledger_entry_id

    def test_list_entries(self):
        """List all ledger entries."""
        matrix1 = _create_mock_review_matrix(
            review_matrix_id="matrix-1",
            translator_id="trans-1",
        )
        matrix2 = _create_mock_review_matrix(
            review_matrix_id="matrix-2",
            translator_id="trans-2",
        )

        build_governance_review_ledger_entry(review_matrix=matrix1)
        build_governance_review_ledger_entry(review_matrix=matrix2)

        entries = list_review_ledger_entries()
        assert len(entries) == 2

    def test_list_by_translator(self):
        """List entries for a specific translator."""
        matrix1 = _create_mock_review_matrix(
            review_matrix_id="matrix-1",
            translator_id="trans-A",
        )
        matrix2 = _create_mock_review_matrix(
            review_matrix_id="matrix-2",
            translator_id="trans-A",
        )
        matrix3 = _create_mock_review_matrix(
            review_matrix_id="matrix-3",
            translator_id="trans-B",
        )

        build_governance_review_ledger_entry(review_matrix=matrix1)
        build_governance_review_ledger_entry(review_matrix=matrix2)
        build_governance_review_ledger_entry(review_matrix=matrix3)

        entries_a = list_review_ledger_entries_for_translator("trans-A")
        entries_b = list_review_ledger_entries_for_translator("trans-B")

        assert len(entries_a) == 2
        assert len(entries_b) == 1

    def test_get_latest_for_translator(self):
        """Get latest entry for a translator."""
        matrix1 = _create_mock_review_matrix(review_matrix_id="matrix-1")
        matrix2 = _create_mock_review_matrix(review_matrix_id="matrix-2")

        entry1 = build_governance_review_ledger_entry(review_matrix=matrix1)
        entry2 = build_governance_review_ledger_entry(review_matrix=matrix2)

        latest = get_latest_ledger_entry_for_translator("body_outline_dxf_r12")
        assert latest.ledger_entry_id == entry2.ledger_entry_id

    def test_clear_index(self):
        """Clear index removes all entries."""
        matrix = _create_mock_review_matrix()
        build_governance_review_ledger_entry(review_matrix=matrix)

        assert len(list_review_ledger_entries()) > 0
        clear_review_ledger_index()
        assert len(list_review_ledger_entries()) == 0


# -----------------------------------------------------------------------------
# Test Summary Model
# -----------------------------------------------------------------------------

class TestSummaryModel:
    """Test ledger entry summary model."""

    def test_to_summary_preserves_key_fields(self):
        """Summary preserves key fields."""
        entry = _create_complete_ledger_entry()
        summary = to_summary(entry)

        assert summary.ledger_entry_id == entry.ledger_entry_id
        assert summary.review_matrix_id == entry.review_matrix_id
        assert summary.dossier_id == entry.dossier_id
        assert summary.translator_id == entry.translator_id
        assert summary.review_gate == entry.review_gate
        assert summary.review_trace_hash == entry.review_trace_hash
        assert summary.parent_count == len(entry.parent_ledger_hashes)

    def test_summary_enforces_invariants(self):
        """Summary enforces 7K invariants."""
        summary = GovernanceReviewLedgerSummary(
            ledger_entry_id="test-001",
            review_matrix_id="matrix-001",
            dossier_id="dossier-001",
            translator_id="test_translator",
            review_gate="green",
            review_readiness_score=100,
            review_trace_hash="trace_hash",
            parent_count=0,
            created_at=datetime.now(timezone.utc),
            immutable=False,  # Will be forced to True
            execution_authorized=True,  # Will be forced to False
            machine_output_allowed=True,  # Will be forced to False
        )
        assert summary.immutable is True
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False


# -----------------------------------------------------------------------------
# Test Endpoints
# -----------------------------------------------------------------------------

class TestEndpoints:
    """Test REST API endpoints."""

    def test_list_ledger_entries_endpoint(self):
        """GET /api/cam/translators/governance-review-ledger returns list."""
        response = client.get("/api/cam/translators/governance-review-ledger")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_ledger_policy_endpoint(self):
        """GET /api/cam/translators/governance-review-ledger/policy returns policy."""
        response = client.get("/api/cam/translators/governance-review-ledger/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["append_only"] is True
        assert data["mutation_allowed"] is False
        assert data["immutable"] is True
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

    def test_build_ledger_entry_endpoint(self):
        """POST /api/cam/translators/governance-review-ledger/build creates entry."""
        # First create a review matrix in the index
        from app.cam.translator_governance_review_matrix import (
            REVIEW_MATRIX_INDEX,
            TranslatorGovernanceReviewMatrix,
        )

        test_matrix = TranslatorGovernanceReviewMatrix(
            review_matrix_id="test-matrix-for-ledger",
            dossier_id="dossier-001",
            translator_id="body_outline_dxf_r12",
            review_gate="green",
            review_readiness_score=100,
            dossier_integrity_valid=True,
            provenance_integrity_valid=True,
            quarantine_integrity_valid=True,
            authorization_integrity_valid=True,
            readiness_integrity_valid=True,
            governance_constraints_satisfied=True,
            escalation_layers_complete=True,
            blocker_count=0,
            warning_count=0,
            eligible_for_human_governance_review=True,
            evidence_hash="test_matrix_hash",
        )
        REVIEW_MATRIX_INDEX[test_matrix.review_matrix_id] = test_matrix

        try:
            response = client.post(
                "/api/cam/translators/governance-review-ledger/build",
                json={"review_matrix_id": "test-matrix-for-ledger"}
            )
            assert response.status_code == 201
            data = response.json()
            assert data["review_matrix_id"] == "test-matrix-for-ledger"
            assert data["translator_id"] == "body_outline_dxf_r12"
            assert data["immutable"] is True
            assert data["execution_authorized"] is False
            assert data["machine_output_allowed"] is False
        finally:
            REVIEW_MATRIX_INDEX.pop("test-matrix-for-ledger", None)

    def test_build_missing_matrix_returns_400(self):
        """POST with missing matrix returns 400."""
        response = client.post(
            "/api/cam/translators/governance-review-ledger/build",
            json={"review_matrix_id": "nonexistent-matrix"}
        )
        assert response.status_code == 400

    def test_get_ledger_entry_endpoint(self):
        """GET /api/cam/translators/governance-review-ledger/{id} returns entry."""
        matrix = _create_mock_review_matrix()
        entry = build_governance_review_ledger_entry(review_matrix=matrix)

        response = client.get(
            f"/api/cam/translators/governance-review-ledger/{entry.ledger_entry_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ledger_entry_id"] == entry.ledger_entry_id

    def test_get_ledger_entry_not_found(self):
        """GET with unknown ID returns 404."""
        response = client.get(
            "/api/cam/translators/governance-review-ledger/unknown-ledger-id"
        )
        assert response.status_code == 404

    def test_get_entries_by_translator_endpoint(self):
        """GET /api/cam/translators/governance-review-ledger/by-translator/{id} returns list."""
        matrix = _create_mock_review_matrix(translator_id="specific-translator")
        build_governance_review_ledger_entry(review_matrix=matrix)

        response = client.get(
            "/api/cam/translators/governance-review-ledger/by-translator/specific-translator"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(e["translator_id"] == "specific-translator" for e in data)

    def test_get_lineage_endpoint(self):
        """GET /api/cam/translators/governance-review-ledger/{id}/lineage returns chain."""
        # Create two entries in sequence
        matrix1 = _create_mock_review_matrix(review_matrix_id="matrix-1")
        entry1 = build_governance_review_ledger_entry(review_matrix=matrix1)

        matrix2 = _create_mock_review_matrix(review_matrix_id="matrix-2")
        entry2 = build_governance_review_ledger_entry(review_matrix=matrix2)

        response = client.get(
            f"/api/cam/translators/governance-review-ledger/{entry2.ledger_entry_id}/lineage"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2


# -----------------------------------------------------------------------------
# Test Safety Assertions
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Test that 7K never produces execution artifacts."""

    def test_no_dxf_tokens_in_response(self):
        """Response contains no DXF generation tokens."""
        entry = _create_complete_ledger_entry()
        response_text = entry.model_dump_json()

        dxf_tokens = ["SECTION", "ENTITIES", "ENDSEC", "EOF", "LINE", "LWPOLYLINE"]
        for token in dxf_tokens:
            assert token not in response_text

    def test_no_gcode_tokens_in_response(self):
        """Response contains no G-code tokens."""
        entry = _create_complete_ledger_entry()
        response_text = entry.model_dump_json()

        gcode_tokens = ["G00", "G01", "G02", "G03", "M03", "M05", "M30"]
        for token in gcode_tokens:
            assert token not in response_text

    def test_all_endpoints_enforce_invariants(self):
        """All endpoint responses enforce invariants."""
        # Policy endpoint
        response = client.get("/api/cam/translators/governance-review-ledger/policy")
        data = response.json()
        assert data["immutable"] is True
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False


# -----------------------------------------------------------------------------
# Test RMOS Persistence
# -----------------------------------------------------------------------------

class TestRMOSPersistence:
    """Test optional RMOS persistence."""

    def test_persist_to_rmos_default_false(self):
        """RMOS persistence is off by default."""
        matrix = _create_mock_review_matrix()

        with patch(
            "app.cam.translator_governance_review_ledger._persist_to_rmos"
        ) as mock_persist:
            build_governance_review_ledger_entry(
                review_matrix=matrix,
                persist_to_rmos=False,
            )
            mock_persist.assert_not_called()

    def test_persist_to_rmos_when_enabled(self):
        """RMOS persistence is called when enabled."""
        matrix = _create_mock_review_matrix()

        with patch(
            "app.cam.translator_governance_review_ledger._persist_to_rmos"
        ) as mock_persist:
            build_governance_review_ledger_entry(
                review_matrix=matrix,
                persist_to_rmos=True,
            )
            mock_persist.assert_called_once()


# -----------------------------------------------------------------------------
# Test Hash Extraction
# -----------------------------------------------------------------------------

class TestHashExtraction:
    """Test hash extraction helpers."""

    def test_extract_hash_returns_value(self):
        """Extract hash returns value from object."""
        obj = MagicMock()
        obj.evidence_hash = "test_hash_value"

        result = _extract_hash(obj, ["evidence_hash"])
        assert result == "test_hash_value"

    def test_extract_hash_returns_placeholder_for_none(self):
        """Extract hash returns placeholder for None object."""
        result = _extract_hash(None, ["evidence_hash"])
        assert result == UNRESOLVED_HASH_PLACEHOLDER

    def test_extract_hash_tries_fallback_fields(self):
        """Extract hash tries fallback fields."""
        obj = MagicMock()
        obj.primary_hash = None
        obj.fallback_hash = "fallback_value"

        result = _extract_hash(obj, ["primary_hash"], ["fallback_hash"])
        assert result == "fallback_value"
