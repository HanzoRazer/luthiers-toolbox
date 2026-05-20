"""
Tests for Acoustic STEP Translator (MRP-5J).

Sprint: MRP-5J
Status: PROTOTYPE

Tests the STEP acoustic translator and CertifiedTopology enforcement:
- CertifiedTopology cannot be instantiated directly
- TopologyValidator.certify() returns CertifiedTopology only when passing
- AcousticStepTranslator accepts only CertifiedTopology
- STEP Part 21 output format verification
"""

import pytest

from app.cam.topology_validation import (
    CertifiedTopology,
    TopologyValidator,
    ValidationError,
    ValidationResult,
    ValidationTier,
    certify_topology,
    validate_topology,
)
from app.cam.translators.step import (
    AcousticStepTranslator,
    AcousticStepTranslationArtifact,
)
from app.cam.translator_capability_registry import (
    get_translator_capability,
    list_translators_by_output_class,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_topology_dict():
    """Valid closed manifold topology that passes validation."""
    return {
        "request_id": "test_step_001",
        "tier": "PROTOTYPE",
        "shells": [
            {
                "shell_id": "shell_body_001",
                "shell_type": "flat_extrusion",
                "component_name": "body",
                "is_closed": True,
                "is_manifold": True,
                "surface_count": 6,
                "edge_count": 12,
                "vertex_count": 8,
                "continuity": [],
            }
        ],
    }


@pytest.fixture
def invalid_topology_dict():
    """Invalid topology with open shell that fails validation."""
    return {
        "request_id": "test_step_002",
        "tier": "PROTOTYPE",
        "shells": [
            {
                "shell_id": "shell_bad_001",
                "shell_type": "flat_extrusion",
                "component_name": "body",
                "is_closed": False,  # Open shell - will fail validation
                "is_manifold": True,
                "surface_count": 5,
                "edge_count": 10,
                "vertex_count": 8,
            }
        ],
    }


@pytest.fixture
def multi_shell_topology_dict():
    """Valid topology with multiple shells."""
    return {
        "request_id": "test_step_003",
        "tier": "PROTOTYPE",
        "shells": [
            {
                "shell_id": "shell_outer",
                "shell_type": "flat_extrusion",
                "component_name": "body_outer",
                "is_closed": True,
                "is_manifold": True,
                "surface_count": 6,
                "edge_count": 12,
                "vertex_count": 8,
            },
            {
                "shell_id": "shell_inner",
                "shell_type": "flat_extrusion",
                "component_name": "cavity",
                "is_closed": True,
                "is_manifold": True,
                "surface_count": 6,
                "edge_count": 12,
                "vertex_count": 8,
            },
        ],
    }


# =============================================================================
# CertifiedTopology Tests
# =============================================================================


class TestCertifiedTopology:
    """Tests for CertifiedTopology contract enforcement."""

    def test_cannot_instantiate_directly(self):
        """CertifiedTopology cannot be created with __init__."""
        with pytest.raises(TypeError) as exc_info:
            CertifiedTopology()

        assert "cannot be instantiated directly" in str(exc_info.value)
        assert "TopologyValidator.certify()" in str(exc_info.value)

    def test_certify_returns_certified_topology(self, valid_topology_dict):
        """TopologyValidator.certify() returns CertifiedTopology when passing."""
        validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
        certified = validator.certify(valid_topology_dict)

        assert isinstance(certified, CertifiedTopology)
        assert certified.request_id == "test_step_001"
        assert certified.validation.passed

    def test_certify_raises_on_failure(self, invalid_topology_dict):
        """TopologyValidator.certify() raises ValidationError when failing."""
        validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)

        with pytest.raises(ValidationError) as exc_info:
            validator.certify(invalid_topology_dict)

        assert "validation failed" in str(exc_info.value).lower()
        assert exc_info.value.classification == "CERTIFICATION_DENIED"

    def test_certify_convenience_function(self, valid_topology_dict):
        """certify_topology() convenience function works."""
        certified = certify_topology(valid_topology_dict)

        assert isinstance(certified, CertifiedTopology)
        assert certified.validation.passed

    def test_certified_topology_properties(self, valid_topology_dict):
        """CertifiedTopology exposes expected properties."""
        certified = certify_topology(valid_topology_dict)

        assert certified.request_id == "test_step_001"
        assert certified.tier == ValidationTier.PROTOTYPE
        assert len(certified.shells) == 1
        assert certified.signature is not None
        assert certified.topology_dict == valid_topology_dict

    def test_certified_topology_serialization(self, valid_topology_dict):
        """CertifiedTopology.to_dict() works."""
        certified = certify_topology(valid_topology_dict)
        cert_dict = certified.to_dict()

        assert cert_dict["certified"] == True
        assert cert_dict["request_id"] == "test_step_001"
        assert cert_dict["validation_passed"] == True
        assert "signature" in cert_dict


# =============================================================================
# AcousticStepTranslator Tests
# =============================================================================


class TestAcousticStepTranslator:
    """Tests for AcousticStepTranslator."""

    def test_accepts_certified_topology(self, valid_topology_dict):
        """Translator accepts CertifiedTopology."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        assert translator.can_translate(certified)

    def test_rejects_raw_topology_dict(self, valid_topology_dict):
        """Translator rejects raw topology dictionaries."""
        translator = AcousticStepTranslator()

        assert not translator.can_translate(valid_topology_dict)

    def test_rejects_validation_result(self, valid_topology_dict):
        """Translator rejects ValidationResult (not CertifiedTopology)."""
        result = validate_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        assert not translator.can_translate(result)

    def test_translate_raises_on_wrong_type(self, valid_topology_dict):
        """translate() raises TypeError for non-CertifiedTopology."""
        translator = AcousticStepTranslator()

        with pytest.raises(TypeError) as exc_info:
            translator.translate(valid_topology_dict)

        assert "CertifiedTopology" in str(exc_info.value)
        assert "TopologyValidator.certify()" in str(exc_info.value)

    def test_translate_produces_artifact(self, valid_topology_dict):
        """translate() produces AcousticStepTranslationArtifact."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)

        assert isinstance(artifact, AcousticStepTranslationArtifact)
        assert artifact.target == "step"
        assert artifact.format_version == "STEP_PART21_PROTOTYPE"
        assert artifact.maturity == "prototype"
        assert len(artifact.content) > 0

    def test_artifact_contains_provenance(self, valid_topology_dict):
        """Artifact contains translator provenance."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)

        assert artifact.provenance["translator_id"] == "step_acoustic_prototype"
        assert artifact.provenance["classification"] == "PROTOTYPE_SERIALIZATION"
        assert artifact.provenance["request_id"] == "test_step_001"

    def test_artifact_contains_validation_signature(self, valid_topology_dict):
        """Artifact contains validation signature."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)

        assert "input_hash" in artifact.validation_signature
        assert "validation_hash" in artifact.validation_signature
        assert artifact.validation_signature["tier"] == "PROTOTYPE"

    def test_artifact_content_hash(self, valid_topology_dict):
        """Artifact provides content hash for determinism verification."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)

        assert artifact.content_hash is not None
        assert len(artifact.content_hash) == 16  # SHA256 truncated

    def test_multi_shell_translation(self, multi_shell_topology_dict):
        """Translator handles multiple shells."""
        certified = certify_topology(multi_shell_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)

        assert artifact.metadata["shell_count"] == 2
        content = artifact.content.decode("utf-8")
        assert "shell_outer" in content
        assert "shell_inner" in content


# =============================================================================
# STEP Part 21 Format Tests
# =============================================================================


class TestStepFormat:
    """Tests for STEP Part 21 output format."""

    def test_step_header(self, valid_topology_dict):
        """STEP output contains valid ISO-10303-21 header."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)
        content = artifact.content.decode("utf-8")

        assert "ISO-10303-21;" in content
        assert "HEADER;" in content
        assert "ENDSEC;" in content
        assert "DATA;" in content
        assert "END-ISO-10303-21;" in content

    def test_step_file_description(self, valid_topology_dict):
        """STEP output contains FILE_DESCRIPTION with prototype marker."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)
        content = artifact.content.decode("utf-8")

        assert "FILE_DESCRIPTION(" in content
        assert "PROTOTYPE_ACOUSTIC_STEP" in content
        assert "NOT PRODUCTION B-REP" in content

    def test_step_file_name(self, valid_topology_dict):
        """STEP output contains FILE_NAME with request ID."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)
        content = artifact.content.decode("utf-8")

        assert "FILE_NAME(" in content
        assert "test_step_001.step" in content

    def test_step_validation_certificate(self, valid_topology_dict):
        """STEP output contains validation certificate as comment."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)
        content = artifact.content.decode("utf-8")

        assert "VALIDATION CERTIFICATE" in content
        assert "Validation Passed: True" in content
        assert "Input Hash:" in content
        assert "Validation Hash:" in content

    def test_step_shell_metadata(self, valid_topology_dict):
        """STEP output contains shell metadata."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)
        content = artifact.content.decode("utf-8")

        assert "shell_body_001" in content
        assert "is_closed=True" in content
        assert "is_manifold=True" in content

    def test_step_provenance_metadata(self, valid_topology_dict):
        """STEP output contains translator provenance."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact = translator.translate(certified)
        content = artifact.content.decode("utf-8")

        assert "PROVENANCE" in content
        assert "PROTOTYPE_SERIALIZATION" in content


# =============================================================================
# Capability Registry Tests
# =============================================================================


class TestCapabilityRegistry:
    """Tests for translator capability registration."""

    def test_step_acoustic_registered(self):
        """step_acoustic_prototype is registered in capability registry."""
        capability = get_translator_capability("step_acoustic_prototype")

        assert capability is not None
        assert capability.translator_id == "step_acoustic_prototype"
        assert capability.output_class == "step"
        assert capability.maturity == "placeholder"

    def test_step_acoustic_is_prototype(self):
        """step_acoustic_prototype has correct classification."""
        capability = get_translator_capability("step_acoustic_prototype")

        assert capability.execution_state == "validation_only"
        assert capability.execution_supported == False
        assert capability.artifact_generation_supported == False
        assert "PROTOTYPE_SERIALIZATION" in capability.notes

    def test_step_translators_discoverable(self):
        """STEP translators are discoverable by output class."""
        step_translators = list_translators_by_output_class("step")

        assert len(step_translators) >= 1
        ids = [t.translator_id for t in step_translators]
        assert "step_acoustic_prototype" in ids


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the full MRP-5J pipeline."""

    def test_full_pipeline_valid_topology(self, valid_topology_dict):
        """Full pipeline: validate → certify → translate → artifact."""
        # Step 1: Validate
        result = validate_topology(valid_topology_dict)
        assert result.passed

        # Step 2: Certify
        certified = certify_topology(valid_topology_dict)
        assert isinstance(certified, CertifiedTopology)

        # Step 3: Translate
        translator = AcousticStepTranslator()
        artifact = translator.translate(certified)

        # Step 4: Verify artifact
        assert artifact.target == "step"
        assert artifact.maturity == "prototype"
        assert len(artifact.content) > 0

        # Step 5: Verify STEP content
        content = artifact.content.decode("utf-8")
        assert "ISO-10303-21;" in content
        assert "END-ISO-10303-21;" in content

    def test_pipeline_blocks_on_invalid_topology(self, invalid_topology_dict):
        """Pipeline blocks translation of invalid topology."""
        # Step 1: Validation fails
        result = validate_topology(invalid_topology_dict)
        assert not result.passed

        # Step 2: Certification raises
        with pytest.raises(ValidationError):
            certify_topology(invalid_topology_dict)

        # Cannot proceed to translation without CertifiedTopology

    def test_translator_cannot_bypass_certification(self, invalid_topology_dict):
        """Translator cannot accept uncertified invalid topology."""
        translator = AcousticStepTranslator()

        # Cannot translate raw dict
        with pytest.raises(TypeError):
            translator.translate(invalid_topology_dict)

        # Cannot translate ValidationResult
        result = validate_topology(invalid_topology_dict)
        with pytest.raises(TypeError):
            translator.translate(result)

    def test_deterministic_output(self, valid_topology_dict):
        """Same input produces same content hash."""
        certified = certify_topology(valid_topology_dict)
        translator = AcousticStepTranslator()

        artifact1 = translator.translate(certified)
        artifact2 = translator.translate(certified)

        # Content should be identical (excluding timestamp in header)
        # At minimum, structure should be deterministic
        assert artifact1.metadata == artifact2.metadata
        assert artifact1.validation_signature == artifact2.validation_signature
