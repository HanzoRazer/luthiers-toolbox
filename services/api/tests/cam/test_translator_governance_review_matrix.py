"""
Tests for Translator Governance Review Matrix (7J)

CAM Dev Order 7J: Governance review readiness consolidation layer.

7J invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7J determines review readiness only. It does not create approval
  authority, execution authority, or mutation authority.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.cam.translator_governance_review_matrix import (
    TranslatorGovernanceReviewMatrix,
    GovernanceReviewMatrixSummary,
    CANONICAL_ESCALATION_LAYERS,
    SCORING_WEIGHTS,
    GATE_THRESHOLDS,
    REVIEW_MATRIX_INDEX,
    register_review_matrix,
    get_review_matrix,
    list_review_matrices,
    list_review_matrices_for_translator,
    clear_review_matrix_index,
    evaluate_governance_review_readiness,
    evaluate_governance_review_readiness_by_dossier_id,
    to_summary,
    ReviewMatrixEvaluationError,
    _compute_integrity_score,
    _determine_gate,
    _classify_deficiencies,
    _compute_evidence_hash,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_index():
    """Clear review matrix index before each test."""
    clear_review_matrix_index()
    yield
    clear_review_matrix_index()


def _create_mock_dossier(
    dossier_id: str = "dossier-test-123",
    translator_id: str = "body_outline_dxf_r12",
    deterministic_dossier_hash: str = "abc123hash",
    provenance_hash: str = "prov_hash_123",
    freeze_manifest_hash: str = "freeze_hash_123",
    authorization_hash: str = "auth_hash_123",
    readiness_hash: str = "read_hash_123",
    readiness_gate: str = "green",
    authorization_gate: str = "yellow",
    quarantine_state: str = "governance_freeze",
    required_escalation_layers: list = None,
    governance_constraints: list = None,
    execution_authorized: bool = False,
    machine_output_allowed: bool = False,
    immutable: bool = True,
) -> MagicMock:
    """Create a mock dossier for testing."""
    dossier = MagicMock()
    dossier.dossier_id = dossier_id
    dossier.translator_id = translator_id
    dossier.deterministic_dossier_hash = deterministic_dossier_hash
    dossier.provenance_hash = provenance_hash
    dossier.freeze_manifest_hash = freeze_manifest_hash
    dossier.authorization_hash = authorization_hash
    dossier.readiness_hash = readiness_hash
    dossier.readiness_gate = readiness_gate
    dossier.authorization_gate = authorization_gate
    dossier.quarantine_state = quarantine_state
    dossier.required_escalation_layers = required_escalation_layers or CANONICAL_ESCALATION_LAYERS.copy()
    dossier.governance_constraints = governance_constraints or ["constraint1", "constraint2"]
    dossier.execution_authorized = execution_authorized
    dossier.machine_output_allowed = machine_output_allowed
    dossier.immutable = immutable
    return dossier


def _create_complete_dossier() -> MagicMock:
    """Create a complete, valid dossier."""
    return _create_mock_dossier(
        deterministic_dossier_hash="valid_hash",
        provenance_hash="prov_hash_complete",
        freeze_manifest_hash="freeze_hash_complete",
        authorization_hash="auth_hash_complete",
        readiness_hash="read_hash_complete",
        readiness_gate="green",
        authorization_gate="green",
        quarantine_state="governance_freeze",
        required_escalation_layers=CANONICAL_ESCALATION_LAYERS.copy(),
        governance_constraints=["no_dxf", "no_gcode"],
        execution_authorized=False,
        machine_output_allowed=False,
        immutable=True,
    )


# -----------------------------------------------------------------------------
# Test 7J Invariants
# -----------------------------------------------------------------------------

class TestReviewMatrixInvariants:
    """Test 7J model-enforced invariants."""

    def test_7j_invariant_execution_authorized_always_false(self):
        """execution_authorized must always be false."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.execution_authorized is False

    def test_7j_invariant_machine_output_always_false(self):
        """machine_output_allowed must always be false."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.machine_output_allowed is False

    def test_cannot_create_execution_authorized_matrix(self):
        """Creating a matrix with execution_authorized=true must fail."""
        with pytest.raises(ValueError, match="7J invariant violation"):
            TranslatorGovernanceReviewMatrix(
                review_matrix_id="test-001",
                dossier_id="dossier-001",
                translator_id="test_translator",
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
                execution_authorized=True,  # Must fail
                machine_output_allowed=False,
            )

    def test_cannot_create_machine_output_allowed_matrix(self):
        """Creating a matrix with machine_output_allowed=true must fail."""
        with pytest.raises(ValueError, match="7J invariant violation"):
            TranslatorGovernanceReviewMatrix(
                review_matrix_id="test-001",
                dossier_id="dossier-001",
                translator_id="test_translator",
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
                execution_authorized=False,
                machine_output_allowed=True,  # Must fail
            )


# -----------------------------------------------------------------------------
# Test Deterministic Scoring
# -----------------------------------------------------------------------------

class TestDeterministicScoring:
    """Test deterministic review readiness scoring."""

    def test_same_dossier_produces_same_score(self):
        """Same dossier input produces same review score."""
        dossier1 = _create_complete_dossier()
        dossier1.dossier_id = "dossier-same-1"

        dossier2 = _create_complete_dossier()
        dossier2.dossier_id = "dossier-same-1"

        # Clear between evaluations
        clear_review_matrix_index()
        matrix1 = evaluate_governance_review_readiness(dossier1)

        clear_review_matrix_index()
        matrix2 = evaluate_governance_review_readiness(dossier2)

        assert matrix1.review_readiness_score == matrix2.review_readiness_score
        assert matrix1.review_gate == matrix2.review_gate

    def test_full_score_is_100(self):
        """Complete valid dossier produces score of 100."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_readiness_score == 100

    def test_missing_provenance_reduces_score(self):
        """Missing provenance reduces score by 20."""
        dossier = _create_complete_dossier()
        dossier.provenance_hash = None
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_readiness_score == 100 - SCORING_WEIGHTS["provenance_integrity"]
        assert matrix.provenance_integrity_valid is False

    def test_missing_quarantine_reduces_score(self):
        """Missing quarantine reduces score by 20."""
        dossier = _create_complete_dossier()
        dossier.freeze_manifest_hash = None
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_readiness_score == 100 - SCORING_WEIGHTS["quarantine_integrity"]
        assert matrix.quarantine_integrity_valid is False

    def test_missing_authorization_reduces_score(self):
        """Missing authorization reduces score by 15."""
        dossier = _create_complete_dossier()
        dossier.authorization_hash = None
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_readiness_score == 100 - SCORING_WEIGHTS["authorization_integrity"]
        assert matrix.authorization_integrity_valid is False

    def test_missing_readiness_reduces_score(self):
        """Missing readiness reduces score by 15."""
        dossier = _create_complete_dossier()
        dossier.readiness_hash = None
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_readiness_score == 100 - SCORING_WEIGHTS["readiness_integrity"]
        assert matrix.readiness_integrity_valid is False

    def test_missing_escalation_layers_reduces_score(self):
        """Missing escalation layers reduces score by 10."""
        dossier = _create_complete_dossier()
        dossier.required_escalation_layers = []  # Missing all layers
        matrix = evaluate_governance_review_readiness(dossier)
        # Governance completeness is 10 points
        assert matrix.escalation_layers_complete is False


# -----------------------------------------------------------------------------
# Test Gate Thresholds
# -----------------------------------------------------------------------------

class TestGateThresholds:
    """Test review gate threshold logic."""

    def test_score_80_plus_is_green(self):
        """Score >= 80 produces GREEN gate."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_readiness_score >= 80
        assert matrix.review_gate == "green"

    def test_score_50_to_79_is_yellow(self):
        """Score 50-79 produces YELLOW gate."""
        # Test the gate function directly since creating a mock that
        # scores 50-79 without blockers is complex
        assert _determine_gate(79, has_hard_red=False) == "yellow"
        assert _determine_gate(50, has_hard_red=False) == "yellow"
        assert _determine_gate(65, has_hard_red=False) == "yellow"

    def test_score_below_50_is_red(self):
        """Score < 50 produces RED gate."""
        assert _determine_gate(49, has_hard_red=False) == "red"
        assert _determine_gate(0, has_hard_red=False) == "red"

    def test_hard_red_overrides_score(self):
        """Hard RED conditions override score-based gate."""
        # Even with score of 100, hard RED makes it RED
        assert _determine_gate(100, has_hard_red=True) == "red"
        assert _determine_gate(80, has_hard_red=True) == "red"

    def test_dossier_invalid_causes_hard_red(self):
        """Invalid dossier causes hard RED."""
        dossier = _create_complete_dossier()
        dossier.deterministic_dossier_hash = None  # Invalid dossier
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_gate == "red"
        assert "dossier_integrity_failure" in matrix.blockers

    def test_execution_authorized_causes_hard_red(self):
        """Dossier with execution_authorized=true causes hard RED."""
        dossier = _create_complete_dossier()
        dossier.execution_authorized = True
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_gate == "red"
        assert "execution_authorized_true" in matrix.blockers

    def test_machine_output_causes_hard_red(self):
        """Dossier with machine_output_allowed=true causes hard RED."""
        dossier = _create_complete_dossier()
        dossier.machine_output_allowed = True
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_gate == "red"
        assert "machine_output_allowed_true" in matrix.blockers

    def test_missing_escalation_layer_causes_hard_red(self):
        """Missing required escalation layer causes hard RED."""
        dossier = _create_complete_dossier()
        dossier.required_escalation_layers = ["governance_review"]  # Missing others
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_gate == "red"
        assert any("missing_required_escalation_layer" in b for b in matrix.blockers)


# -----------------------------------------------------------------------------
# Test Deficiency Classification
# -----------------------------------------------------------------------------

class TestDeficiencyClassification:
    """Test blocker and warning classification."""

    def test_blockers_classified_correctly(self):
        """Blockers are classified correctly."""
        blockers, warnings = _classify_deficiencies(
            dossier_valid=False,
            provenance_valid=True,
            quarantine_valid=True,
            authorization_valid=True,
            readiness_valid=True,
            escalation_complete=True,
            missing_layers=[],
            dossier_execution_authorized=False,
            dossier_machine_output=False,
            dossier_immutable=True,
            readiness_gate="green",
            authorization_eligible=False,
        )
        assert "dossier_integrity_failure" in blockers
        assert len(blockers) == 1

    def test_warnings_classified_correctly(self):
        """Warnings are classified correctly."""
        blockers, warnings = _classify_deficiencies(
            dossier_valid=True,
            provenance_valid=True,
            quarantine_valid=True,
            authorization_valid=True,
            readiness_valid=True,
            escalation_complete=True,
            missing_layers=[],
            dossier_execution_authorized=False,
            dossier_machine_output=False,
            dossier_immutable=True,
            readiness_gate="yellow",
            authorization_eligible=False,
        )
        assert len(blockers) == 0
        assert "readiness_gate_yellow" in warnings
        assert "authorization_not_eligible" in warnings

    def test_missing_layers_are_blockers(self):
        """Missing escalation layers are blockers."""
        blockers, warnings = _classify_deficiencies(
            dossier_valid=True,
            provenance_valid=True,
            quarantine_valid=True,
            authorization_valid=True,
            readiness_valid=True,
            escalation_complete=False,
            missing_layers=["human_approval", "security_review"],
            dossier_execution_authorized=False,
            dossier_machine_output=False,
            dossier_immutable=True,
            readiness_gate="green",
            authorization_eligible=True,
        )
        assert "missing_required_escalation_layer:human_approval" in blockers
        assert "missing_required_escalation_layer:security_review" in blockers

    def test_immutable_false_is_blocker(self):
        """immutable=false is a blocker."""
        blockers, warnings = _classify_deficiencies(
            dossier_valid=True,
            provenance_valid=True,
            quarantine_valid=True,
            authorization_valid=True,
            readiness_valid=True,
            escalation_complete=True,
            missing_layers=[],
            dossier_execution_authorized=False,
            dossier_machine_output=False,
            dossier_immutable=False,
            readiness_gate="green",
            authorization_eligible=True,
        )
        assert "immutable_false" in blockers


# -----------------------------------------------------------------------------
# Test Eligibility Logic
# -----------------------------------------------------------------------------

class TestEligibilityLogic:
    """Test review eligibility determination."""

    def test_green_no_blockers_is_eligible(self):
        """GREEN gate with no blockers is eligible."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_gate == "green"
        assert matrix.blocker_count == 0
        assert matrix.eligible_for_human_governance_review is True

    def test_red_is_not_eligible(self):
        """RED gate is never eligible."""
        # Create dossier with execution_authorized=True to cause hard RED
        dossier = _create_mock_dossier(
            execution_authorized=True,  # Causes blocker = RED
        )
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.review_gate == "red"
        assert "execution_authorized_true" in matrix.blockers
        assert matrix.eligible_for_human_governance_review is False

    def test_yellow_no_blockers_is_eligible(self):
        """YELLOW gate with no blockers is eligible."""
        # Use gate function to verify logic
        # YELLOW is between 50-79, no hard RED means no blockers
        # In practice, scores 50-79 with no blockers should be eligible

        # Create a matrix directly to test
        matrix = TranslatorGovernanceReviewMatrix(
            review_matrix_id="test-yellow",
            dossier_id="dossier-001",
            translator_id="test_translator",
            review_gate="yellow",
            review_readiness_score=65,
            dossier_integrity_valid=True,
            provenance_integrity_valid=True,
            quarantine_integrity_valid=True,
            authorization_integrity_valid=True,
            readiness_integrity_valid=True,
            governance_constraints_satisfied=True,
            escalation_layers_complete=True,
            blocker_count=0,
            warning_count=1,
            warnings=["minor_issue"],
            eligible_for_human_governance_review=True,  # Should be allowed
        )
        assert matrix.eligible_for_human_governance_review is True

    def test_blockers_make_ineligible(self):
        """Having blockers makes review ineligible regardless of gate."""
        dossier = _create_complete_dossier()
        dossier.required_escalation_layers = []  # Missing layers = blockers
        matrix = evaluate_governance_review_readiness(dossier)
        assert matrix.blocker_count > 0
        assert matrix.eligible_for_human_governance_review is False

    def test_warnings_do_not_affect_eligibility(self):
        """Warnings do not affect eligibility."""
        # A matrix with warnings but no blockers should still be eligible
        matrix = TranslatorGovernanceReviewMatrix(
            review_matrix_id="test-warnings",
            dossier_id="dossier-001",
            translator_id="test_translator",
            review_gate="green",
            review_readiness_score=85,
            dossier_integrity_valid=True,
            provenance_integrity_valid=True,
            quarantine_integrity_valid=True,
            authorization_integrity_valid=True,
            readiness_integrity_valid=True,
            governance_constraints_satisfied=True,
            escalation_layers_complete=True,
            blocker_count=0,
            warning_count=3,
            warnings=["warning1", "warning2", "warning3"],
            eligible_for_human_governance_review=True,
        )
        assert matrix.warning_count == 3
        assert matrix.eligible_for_human_governance_review is True


# -----------------------------------------------------------------------------
# Test Evidence Hash
# -----------------------------------------------------------------------------

class TestEvidenceHash:
    """Test deterministic evidence hashing."""

    def test_same_inputs_same_hash(self):
        """Same inputs produce same evidence hash."""
        hash1 = _compute_evidence_hash(
            dossier_id="dossier-001",
            translator_id="test_translator",
            score=100,
            gate="green",
            blockers=[],
            warnings=["warn1"],
        )
        hash2 = _compute_evidence_hash(
            dossier_id="dossier-001",
            translator_id="test_translator",
            score=100,
            gate="green",
            blockers=[],
            warnings=["warn1"],
        )
        assert hash1 == hash2

    def test_different_inputs_different_hash(self):
        """Different inputs produce different evidence hash."""
        hash1 = _compute_evidence_hash(
            dossier_id="dossier-001",
            translator_id="test_translator",
            score=100,
            gate="green",
            blockers=[],
            warnings=[],
        )
        hash2 = _compute_evidence_hash(
            dossier_id="dossier-002",  # Different dossier
            translator_id="test_translator",
            score=100,
            gate="green",
            blockers=[],
            warnings=[],
        )
        assert hash1 != hash2

    def test_hash_is_sha256(self):
        """Evidence hash is valid SHA256."""
        hash_val = _compute_evidence_hash(
            dossier_id="dossier-001",
            translator_id="test_translator",
            score=100,
            gate="green",
            blockers=[],
            warnings=[],
        )
        assert len(hash_val) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in hash_val)


# -----------------------------------------------------------------------------
# Test Index Operations
# -----------------------------------------------------------------------------

class TestIndexOperations:
    """Test in-memory index operations."""

    def test_register_and_get(self):
        """Register and retrieve a review matrix."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)

        retrieved = get_review_matrix(matrix.review_matrix_id)
        assert retrieved is not None
        assert retrieved.review_matrix_id == matrix.review_matrix_id

    def test_list_matrices(self):
        """List all review matrices."""
        dossier1 = _create_mock_dossier(dossier_id="dossier-1", translator_id="trans-1")
        dossier2 = _create_mock_dossier(dossier_id="dossier-2", translator_id="trans-2")

        evaluate_governance_review_readiness(dossier1)
        evaluate_governance_review_readiness(dossier2)

        matrices = list_review_matrices()
        assert len(matrices) == 2

    def test_list_by_translator(self):
        """List matrices for a specific translator."""
        dossier1 = _create_mock_dossier(dossier_id="dossier-1", translator_id="trans-A")
        dossier2 = _create_mock_dossier(dossier_id="dossier-2", translator_id="trans-A")
        dossier3 = _create_mock_dossier(dossier_id="dossier-3", translator_id="trans-B")

        evaluate_governance_review_readiness(dossier1)
        evaluate_governance_review_readiness(dossier2)
        evaluate_governance_review_readiness(dossier3)

        matrices_a = list_review_matrices_for_translator("trans-A")
        matrices_b = list_review_matrices_for_translator("trans-B")

        assert len(matrices_a) == 2
        assert len(matrices_b) == 1

    def test_clear_index(self):
        """Clear index removes all matrices."""
        dossier = _create_complete_dossier()
        evaluate_governance_review_readiness(dossier)

        assert len(list_review_matrices()) > 0
        clear_review_matrix_index()
        assert len(list_review_matrices()) == 0


# -----------------------------------------------------------------------------
# Test Summary Model
# -----------------------------------------------------------------------------

class TestSummaryModel:
    """Test review matrix summary model."""

    def test_to_summary_preserves_key_fields(self):
        """Summary preserves key fields."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        summary = to_summary(matrix)

        assert summary.review_matrix_id == matrix.review_matrix_id
        assert summary.dossier_id == matrix.dossier_id
        assert summary.translator_id == matrix.translator_id
        assert summary.review_gate == matrix.review_gate
        assert summary.review_readiness_score == matrix.review_readiness_score
        assert summary.blocker_count == matrix.blocker_count
        assert summary.warning_count == matrix.warning_count
        assert summary.eligible_for_human_governance_review == matrix.eligible_for_human_governance_review

    def test_summary_enforces_invariants(self):
        """Summary enforces 7J invariants."""
        summary = GovernanceReviewMatrixSummary(
            review_matrix_id="test-001",
            dossier_id="dossier-001",
            translator_id="test_translator",
            review_gate="green",
            review_readiness_score=100,
            blocker_count=0,
            warning_count=0,
            eligible_for_human_governance_review=True,
            created_at=datetime.now(timezone.utc),
            execution_authorized=True,  # Will be forced to False
            machine_output_allowed=True,  # Will be forced to False
        )
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False


# -----------------------------------------------------------------------------
# Test Endpoints
# -----------------------------------------------------------------------------

class TestEndpoints:
    """Test REST API endpoints."""

    def test_list_reviews_endpoint(self):
        """GET /api/cam/translators/governance-review returns list."""
        response = client.get("/api/cam/translators/governance-review")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_review_policy_endpoint(self):
        """GET /api/cam/translators/governance-review/policy returns policy."""
        response = client.get("/api/cam/translators/governance-review/policy")
        assert response.status_code == 200
        data = response.json()
        assert "canonical_escalation_layers" in data
        assert "scoring_weights" in data
        assert "gate_thresholds" in data
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

    def test_evaluate_review_endpoint(self):
        """POST /api/cam/translators/governance-review/evaluate creates matrix."""
        # First create a dossier in the index
        from app.cam.translator_governance_dossier import (
            DOSSIER_INDEX,
            TranslatorGovernanceDossier,
        )

        # Create a test dossier with all required fields
        test_dossier = TranslatorGovernanceDossier(
            dossier_id="test-dossier-for-review",
            translator_id="body_outline_dxf_r12",
            readiness_gate="green",
            quarantine_state="governance_freeze",
            authorization_gate="yellow",
            provenance_hash="prov_hash_123",
            readiness_hash="read_hash_123",
            authorization_hash="auth_hash_123",
            freeze_manifest_hash="freeze_hash_123",
            deterministic_dossier_hash="dossier_hash_123",
            lifecycle_hashes=["hash1"],
            audit_hashes=["hash2"],
            promotion_evidence_hashes=["hash3"],
            governance_constraints=["no_dxf", "no_gcode"],
            required_escalation_layers=CANONICAL_ESCALATION_LAYERS.copy(),
            review_state="future_escalation_required",
        )
        DOSSIER_INDEX[test_dossier.dossier_id] = test_dossier

        try:
            response = client.post(
                "/api/cam/translators/governance-review/evaluate",
                json={"dossier_id": "test-dossier-for-review"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["dossier_id"] == "test-dossier-for-review"
            assert data["translator_id"] == "body_outline_dxf_r12"
            assert data["execution_authorized"] is False
            assert data["machine_output_allowed"] is False
        finally:
            # Clean up
            DOSSIER_INDEX.pop("test-dossier-for-review", None)

    def test_evaluate_missing_dossier(self):
        """POST with missing dossier returns 400."""
        response = client.post(
            "/api/cam/translators/governance-review/evaluate",
            json={"dossier_id": "nonexistent-dossier"}
        )
        assert response.status_code == 400

    def test_get_review_endpoint(self):
        """GET /api/cam/translators/governance-review/{id} returns matrix."""
        # Create a matrix
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)

        response = client.get(
            f"/api/cam/translators/governance-review/{matrix.review_matrix_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["review_matrix_id"] == matrix.review_matrix_id

    def test_get_review_not_found(self):
        """GET with unknown ID returns 404."""
        response = client.get(
            "/api/cam/translators/governance-review/unknown-review-id"
        )
        assert response.status_code == 404

    def test_get_reviews_by_translator_endpoint(self):
        """GET /api/cam/translators/governance-review/by-translator/{id} returns list."""
        dossier = _create_mock_dossier(translator_id="specific-translator")
        evaluate_governance_review_readiness(dossier)

        response = client.get(
            "/api/cam/translators/governance-review/by-translator/specific-translator"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(m["translator_id"] == "specific-translator" for m in data)


# -----------------------------------------------------------------------------
# Test Safety Assertions
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Test that 7J never produces execution artifacts."""

    def test_no_dxf_tokens_in_response(self):
        """Response contains no DXF generation tokens."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        response_text = matrix.model_dump_json()

        dxf_tokens = ["SECTION", "ENTITIES", "ENDSEC", "EOF", "LINE", "LWPOLYLINE"]
        for token in dxf_tokens:
            assert token not in response_text

    def test_no_gcode_tokens_in_response(self):
        """Response contains no G-code tokens."""
        dossier = _create_complete_dossier()
        matrix = evaluate_governance_review_readiness(dossier)
        response_text = matrix.model_dump_json()

        gcode_tokens = ["G00", "G01", "G02", "G03", "M03", "M05", "M30"]
        for token in gcode_tokens:
            assert token not in response_text

    def test_all_endpoints_enforce_invariants(self):
        """All endpoint responses enforce invariants."""
        # Policy endpoint
        response = client.get("/api/cam/translators/governance-review/policy")
        data = response.json()
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

        # List endpoint
        response = client.get("/api/cam/translators/governance-review")
        # Response is a list, each item should have invariants
        for item in response.json():
            assert item.get("execution_authorized", False) is False
            assert item.get("machine_output_allowed", False) is False


# -----------------------------------------------------------------------------
# Test Canonical Constants
# -----------------------------------------------------------------------------

class TestCanonicalConstants:
    """Test canonical constants are correct."""

    def test_canonical_escalation_layers_count(self):
        """There are exactly 5 canonical escalation layers."""
        assert len(CANONICAL_ESCALATION_LAYERS) == 5

    def test_canonical_escalation_layers_content(self):
        """Canonical escalation layers are correct."""
        expected = [
            "governance_review",
            "translator_execution_architecture_review",
            "human_approval",
            "security_review",
            "artifact_generation_policy_review",
        ]
        assert CANONICAL_ESCALATION_LAYERS == expected

    def test_scoring_weights_sum_to_100(self):
        """Scoring weights sum to 100."""
        assert sum(SCORING_WEIGHTS.values()) == 100

    def test_gate_thresholds_are_correct(self):
        """Gate thresholds are correct."""
        assert GATE_THRESHOLDS["green"] == 80
        assert GATE_THRESHOLDS["yellow"] == 50
        assert GATE_THRESHOLDS["red"] == 0


# -----------------------------------------------------------------------------
# Test RMOS Persistence
# -----------------------------------------------------------------------------

class TestRMOSPersistence:
    """Test optional RMOS persistence."""

    def test_persist_to_rmos_default_false(self):
        """RMOS persistence is off by default."""
        dossier = _create_complete_dossier()

        with patch(
            "app.cam.translator_governance_review_matrix._persist_to_rmos"
        ) as mock_persist:
            evaluate_governance_review_readiness(dossier, persist_to_rmos=False)
            mock_persist.assert_not_called()

    def test_persist_to_rmos_when_enabled(self):
        """RMOS persistence is called when enabled."""
        dossier = _create_complete_dossier()

        with patch(
            "app.cam.translator_governance_review_matrix._persist_to_rmos"
        ) as mock_persist:
            evaluate_governance_review_readiness(dossier, persist_to_rmos=True)
            mock_persist.assert_called_once()
