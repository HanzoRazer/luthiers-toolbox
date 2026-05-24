"""
Test ConfidenceEnvelopeV1 — Constitutional Invariant Validation
================================================================

Governed Interoperability Normalization Sprint: 2026-05-24

These tests validate that ConfidenceEnvelopeV1 maintains constitutional
invariants across all usage patterns. The envelope must NEVER:
- Be runtime authoritative
- Authorize execution
- Allow review bypass
- Propagate cross-repo authority

Test categories:
1. Constitutional invariant enforcement
2. Source system wrapping (luthiers, tap_tone, vectorizer, rank_score)
3. Epistemic status inference
4. Serialization round-trip
5. Factory function correctness
"""

import pytest
from datetime import datetime, timezone

from services.api.app.governance.confidence_envelope import (
    ConfidenceEnvelopeV1,
    SemanticDomain,
    EpistemicStatus,
    SourceSystem,
    CROSS_REPO_NON_IMPLICATIONS,
    ConfidenceEnvelopeIntegrityError,
    create_advisory_envelope,
    create_interpretive_envelope,
)
from services.api.app.governance.confidence_declaration import (
    ConfidenceDeclaration,
    ConfidenceType,
    create_heuristic_confidence,
    create_statistical_confidence,
    create_human_confidence,
)


class TestConstitutionalInvariants:
    """Test that constitutional invariants cannot be violated."""

    def test_runtime_authoritative_always_false(self):
        """Envelope runtime_authoritative must always be False."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.ADVISORY,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="test scope",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=0.8,
        )
        assert envelope.runtime_authoritative is False

    def test_runtime_authoritative_cannot_be_set_true(self):
        """Attempting to set runtime_authoritative=True must raise error."""
        with pytest.raises(ValueError, match="runtime_authoritative must be False"):
            ConfidenceEnvelopeV1(
                domain=SemanticDomain.ADVISORY,
                source_system=SourceSystem.LUTHIERS_TOOLBOX,
                semantic_scope="test scope",
                confidence_type=ConfidenceType.HEURISTIC,
                confidence_value=0.8,
                runtime_authoritative=True,
            )

    def test_review_required_always_true(self):
        """Envelope review_required must always be True."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.ADVISORY,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="test scope",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=0.8,
        )
        assert envelope.review_required is True
        assert envelope.requires_human_review() is True

    def test_review_required_cannot_be_set_false(self):
        """Attempting to set review_required=False must raise error."""
        with pytest.raises(ValueError, match="review_required must be True"):
            ConfidenceEnvelopeV1(
                domain=SemanticDomain.ADVISORY,
                source_system=SourceSystem.LUTHIERS_TOOLBOX,
                semantic_scope="test scope",
                confidence_type=ConfidenceType.HEURISTIC,
                confidence_value=0.8,
                review_required=False,
            )

    def test_execution_authorized_always_false(self):
        """Envelope execution_authorized must always be False."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.ADVISORY,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="test scope",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=0.8,
        )
        assert envelope.execution_authorized is False

    def test_execution_authorized_cannot_be_set_true(self):
        """Attempting to set execution_authorized=True must raise error."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            ConfidenceEnvelopeV1(
                domain=SemanticDomain.ADVISORY,
                source_system=SourceSystem.LUTHIERS_TOOLBOX,
                semantic_scope="test scope",
                confidence_type=ConfidenceType.HEURISTIC,
                confidence_value=0.8,
                execution_authorized=True,
            )

    def test_implies_methods_always_return_false(self):
        """All implies_* methods must return False."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.OPERATOR,
            source_system=SourceSystem.TAP_TONE_PI,
            semantic_scope="high confidence test",
            confidence_type=ConfidenceType.HUMAN_ASSESSED,
            confidence_value=0.99,
            epistemic_status=EpistemicStatus.OBSERVED,
        )

        assert envelope.implies_correctness() is False
        assert envelope.implies_canonicity() is False
        assert envelope.implies_review_bypass() is False
        assert envelope.implies_execution_authority() is False
        assert envelope.implies_governance_bypass() is False
        assert envelope.implies_cross_repo_authority() is False
        assert envelope.is_production_authoritative() is False

    def test_confidence_value_bounds(self):
        """Confidence value must be in [0.0, 1.0]."""
        with pytest.raises(ValueError, match="Confidence value must be 0.0-1.0"):
            ConfidenceEnvelopeV1(
                domain=SemanticDomain.ADVISORY,
                source_system=SourceSystem.LUTHIERS_TOOLBOX,
                semantic_scope="test",
                confidence_type=ConfidenceType.HEURISTIC,
                confidence_value=1.5,
            )

        with pytest.raises(ValueError, match="Confidence value must be 0.0-1.0"):
            ConfidenceEnvelopeV1(
                domain=SemanticDomain.ADVISORY,
                source_system=SourceSystem.LUTHIERS_TOOLBOX,
                semantic_scope="test",
                confidence_type=ConfidenceType.HEURISTIC,
                confidence_value=-0.1,
            )


class TestSourceSystemWrapping:
    """Test wrapping confidence from different source systems."""

    def test_from_confidence_declaration(self):
        """Wrap a luthiers ConfidenceDeclaration."""
        declaration = create_heuristic_confidence(
            value=0.75,
            origin="test_algorithm",
            interpretation="test heuristic score",
        )

        envelope = ConfidenceEnvelopeV1.from_confidence_declaration(declaration)

        assert envelope.source_system == SourceSystem.LUTHIERS_TOOLBOX
        assert envelope.confidence_value == 0.75
        assert envelope.confidence_type == ConfidenceType.HEURISTIC
        assert envelope.semantic_scope == "test heuristic score"
        assert envelope.evidence_basis == "test_algorithm"
        assert envelope.source_representation is not None
        assert envelope.runtime_authoritative is False
        assert envelope.review_required is True

    def test_from_typed_confidence_dict(self):
        """Wrap a tap_tone TypedConfidenceV1 via dict."""
        typed_conf = {
            "domain": "measurement",
            "value": 0.92,
            "source": "tap_tone_analyzer",
            "epistemic_status": "observed",
            "confidence_type": "statistical",
        }

        envelope = ConfidenceEnvelopeV1.from_typed_confidence_dict(typed_conf)

        assert envelope.source_system == SourceSystem.TAP_TONE_PI
        assert envelope.domain == SemanticDomain.MEASUREMENT
        assert envelope.confidence_value == 0.92
        assert envelope.epistemic_status == EpistemicStatus.OBSERVED
        assert envelope.confidence_type == ConfidenceType.STATISTICAL
        assert envelope.source_representation == typed_conf

    def test_from_rank_score(self):
        """Wrap a rank_score with constrained semantics."""
        envelope = ConfidenceEnvelopeV1.from_rank_score(
            score=0.85,
            context="body contour candidate ranking",
        )

        assert envelope.domain == SemanticDomain.ADVISORY
        assert envelope.confidence_type == ConfidenceType.HEURISTIC
        assert envelope.epistemic_status == EpistemicStatus.HEURISTIC
        assert envelope.confidence_value == 0.85
        assert "rank_score" in envelope.semantic_scope
        assert "rank implies approval" in envelope.non_implications
        assert "high score implies correctness" in envelope.non_implications
        assert envelope.runtime_authoritative is False

    def test_from_vectorizer_output(self):
        """Wrap vectorizer-sandbox output with R_AND_D_EXCLUDED posture."""
        envelope = ConfidenceEnvelopeV1.from_vectorizer_output(
            confidence_value=0.78,
            description="semantic reconstruction confidence",
            workflow_id="wave-1d-test",
        )

        assert envelope.source_system == SourceSystem.VECTORIZER_SANDBOX
        assert envelope.domain == SemanticDomain.INTERPRETIVE
        assert envelope.epistemic_status == EpistemicStatus.PREDICTED
        assert envelope.metadata.get("lifecycle_class") == "R_AND_D_EXCLUDED"
        assert "production readiness" in envelope.non_implications
        assert envelope.runtime_authoritative is False


class TestEpistemicStatusInference:
    """Test epistemic status inference from confidence type and source."""

    def test_explicit_epistemic_status_preserved(self):
        """Explicit epistemic_status should be returned unchanged."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.ADVISORY,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="test",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=0.5,
            epistemic_status=EpistemicStatus.DERIVED,
        )

        assert envelope.get_epistemic_posture() == EpistemicStatus.DERIVED

    def test_infer_operator_annotated_from_human_assessed(self):
        """HUMAN_ASSESSED confidence type infers OPERATOR_ANNOTATED status."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.OPERATOR,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="human review",
            confidence_type=ConfidenceType.HUMAN_ASSESSED,
            confidence_value=0.9,
        )

        assert envelope.get_epistemic_posture() == EpistemicStatus.OPERATOR_ANNOTATED

    def test_infer_predicted_from_vectorizer_source(self):
        """VECTORIZER_SANDBOX source infers PREDICTED status."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.INTERPRETIVE,
            source_system=SourceSystem.VECTORIZER_SANDBOX,
            semantic_scope="vectorizer output",
            confidence_type=ConfidenceType.STATISTICAL,
            confidence_value=0.7,
        )

        assert envelope.get_epistemic_posture() == EpistemicStatus.PREDICTED

    def test_infer_heuristic_from_heuristic_type(self):
        """HEURISTIC confidence type infers HEURISTIC status."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.ADVISORY,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="heuristic score",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=0.6,
        )

        assert envelope.get_epistemic_posture() == EpistemicStatus.HEURISTIC

    def test_infer_estimated_from_statistical_type(self):
        """STATISTICAL confidence type infers ESTIMATED status."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.MEASUREMENT,
            source_system=SourceSystem.TAP_TONE_PI,
            semantic_scope="statistical measurement",
            confidence_type=ConfidenceType.STATISTICAL,
            confidence_value=0.88,
        )

        assert envelope.get_epistemic_posture() == EpistemicStatus.ESTIMATED


class TestSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all relevant fields."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.ADVISORY,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="test scope",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=0.75,
            epistemic_status=EpistemicStatus.HEURISTIC,
            evidence_basis="test evidence",
        )

        data = envelope.to_dict()

        assert data["envelope_version"] == "v1"
        assert data["domain"] == "advisory"
        assert data["source_system"] == "luthiers_toolbox"
        assert data["semantic_scope"] == "test scope"
        assert data["confidence_type"] == "heuristic"
        assert data["confidence_value"] == 0.75
        assert data["epistemic_status"] == "heuristic"
        assert data["evidence_basis"] == "test evidence"
        assert data["review_required"] is True
        assert data["runtime_authoritative"] is False
        assert data["execution_authorized"] is False
        assert "epistemic_posture" in data

    def test_round_trip_serialization(self):
        """Envelope should survive round-trip serialization."""
        original = ConfidenceEnvelopeV1(
            domain=SemanticDomain.MEASUREMENT,
            source_system=SourceSystem.TAP_TONE_PI,
            semantic_scope="tap tone measurement",
            confidence_type=ConfidenceType.STATISTICAL,
            confidence_value=0.91,
            epistemic_status=EpistemicStatus.OBSERVED,
            evidence_basis="sensor capture",
            metadata={"sensor_id": "s123"},
        )

        data = original.to_dict()
        restored = ConfidenceEnvelopeV1.from_dict(data)

        assert restored.domain == original.domain
        assert restored.source_system == original.source_system
        assert restored.semantic_scope == original.semantic_scope
        assert restored.confidence_type == original.confidence_type
        assert restored.confidence_value == original.confidence_value
        assert restored.epistemic_status == original.epistemic_status
        assert restored.evidence_basis == original.evidence_basis
        assert restored.review_required is True
        assert restored.runtime_authoritative is False


class TestFactoryFunctions:
    """Test factory functions for common envelope types."""

    def test_create_advisory_envelope(self):
        """create_advisory_envelope produces correct envelope."""
        envelope = create_advisory_envelope(
            value=0.7,
            scope="attention prioritization",
            source=SourceSystem.LUTHIERS_TOOLBOX,
            evidence="ranking algorithm",
        )

        assert envelope.domain == SemanticDomain.ADVISORY
        assert envelope.confidence_value == 0.7
        assert envelope.epistemic_status == EpistemicStatus.HEURISTIC
        assert envelope.runtime_authoritative is False

    def test_create_interpretive_envelope(self):
        """create_interpretive_envelope produces correct envelope."""
        envelope = create_interpretive_envelope(
            value=0.8,
            scope="morphology interpretation",
            source=SourceSystem.LUTHIERS_TOOLBOX,
            evidence="model inference",
        )

        assert envelope.domain == SemanticDomain.INTERPRETIVE
        assert envelope.confidence_value == 0.8
        assert envelope.confidence_type == ConfidenceType.STATISTICAL
        assert envelope.epistemic_status == EpistemicStatus.ESTIMATED
        assert envelope.runtime_authoritative is False


class TestNonImplications:
    """Test that non-implications are properly set."""

    def test_cross_repo_non_implications_present(self):
        """All cross-repo non-implications should be present by default."""
        envelope = ConfidenceEnvelopeV1(
            domain=SemanticDomain.ADVISORY,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope="test",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=0.5,
        )

        required_non_implications = [
            "correctness",
            "canonicity",
            "approval",
            "execution authorization",
            "governance bypass",
            "cross-repo authority propagation",
        ]

        for ni in required_non_implications:
            assert ni in envelope.non_implications, f"Missing non-implication: {ni}"

    def test_rank_score_extra_non_implications(self):
        """rank_score wrapping should add extra non-implications."""
        envelope = ConfidenceEnvelopeV1.from_rank_score(
            score=0.9,
            context="candidate ranking",
        )

        assert "rank implies approval" in envelope.non_implications
        assert "high score implies correctness" in envelope.non_implications
        assert "sort order implies authority" in envelope.non_implications
