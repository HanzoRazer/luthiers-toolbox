"""
Tests for Runtime Admission Control (MRP-5M).

Sprint: MRP-5M
Status: PROTOTYPE

Tests the runtime admission infrastructure:
- Certified topology admission
- Uncertified topology rejection
- Integrity verification
- Policy enforcement
- Provenance tracking
- Constitutional enforcement
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import hashlib
import json

from app.cam.topology_validation.contracts import (
    CertifiedTopology,
    ValidationResult,
    ValidationSignature,
    ValidationTier,
)
from app.cam.topology_validation.validators import TopologyValidator
from app.cam.runtime_admission import (
    # Contracts
    AdmissionDecision,
    AdmissionRejection,
    ExecutionAdmissionRequest,
    ExecutionAdmissionResult,
    ExecutionMode,
    PolicyEvaluationResult,
    RejectionReason,
    RuntimeExecutionContext,
    RuntimeTier,
    # Controller
    ExecutionAdmissionController,
    get_admission_controller,
    # Exceptions
    AdmissionDeniedError,
    IntegrityViolationError,
    InvalidAdmissionRequestError,
    # Integrity
    IntegrityCheckResult,
    IntegrityVerificationResult,
    compute_topology_hash,
    verify_all,
    verify_certification_chain,
    verify_topology_immutable,
    verify_validation_signature,
    # Policies
    AdapterAvailablePolicy,
    AdmissionPolicy,
    AdmissionPolicyRegistry,
    DeterministicOnlyPolicy,
    NoUncertifiedExecutionPolicy,
    PolicySeverity,
    PrototypeRuntimeOnlyPolicy,
    SignatureIntegrityPolicy,
    ValidationRequiredPolicy,
    get_default_policy_registry,
    # Provenance
    AdmissionLedger,
    AdmissionProvenance,
    get_admission_ledger,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_topology_dict():
    """Sample topology dictionary for testing."""
    return {
        "request_id": "test-topo-001",
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
def certified_topology(sample_topology_dict):
    """Create a valid CertifiedTopology for testing."""
    validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
    return validator.certify(sample_topology_dict)


@pytest.fixture
def runtime_context():
    """Standard runtime context for testing."""
    return RuntimeExecutionContext(
        runtime_tier=RuntimeTier.PROTOTYPE,
        execution_mode=ExecutionMode.DETERMINISTIC,
        available_adapter_ids=["mock"],
    )


@pytest.fixture
def admission_request(certified_topology, runtime_context):
    """Standard admission request for testing."""
    return ExecutionAdmissionRequest(
        certified_topology=certified_topology,
        runtime_context=runtime_context,
    )


@pytest.fixture
def controller():
    """Admission controller for testing."""
    return ExecutionAdmissionController(record_provenance=False)


# =============================================================================
# Test: Certified Topology Admission (Happy Path)
# =============================================================================


class TestCertifiedTopologyAdmission:
    """Tests for successful admission of certified topology."""

    def test_certified_topology_is_admitted(self, controller, admission_request):
        """Certified topology should be admitted."""
        result = controller.evaluate(admission_request)

        assert result.admitted
        assert result.decision == AdmissionDecision.ADMITTED
        assert not result.rejected

    def test_admission_includes_authorized_adapters(self, controller, admission_request):
        """Admission result should include authorized adapters."""
        result = controller.evaluate(admission_request)

        assert result.authorized_adapters == ["mock"]

    def test_admission_includes_authorization_token(self, controller, admission_request):
        """Admission result should include authorization token."""
        result = controller.evaluate(admission_request)

        assert result.authorization_token is not None
        assert len(result.authorization_token) > 0

    def test_admission_includes_trace(self, controller, admission_request):
        """Admission result should include evaluation trace."""
        result = controller.evaluate(admission_request)

        assert result.trace is not None
        assert result.trace.request_id == admission_request.request_id
        assert len(result.trace.integrity_checks) > 0
        assert len(result.trace.policy_evaluations) > 0


# =============================================================================
# Test: Uncertified Topology Rejection
# =============================================================================


class TestUncertifiedTopologyRejection:
    """Tests for rejection of uncertified topology."""

    def test_raw_dict_is_rejected(self, controller, runtime_context, sample_topology_dict):
        """Raw topology dict should be rejected."""
        request = ExecutionAdmissionRequest(
            certified_topology=sample_topology_dict,  # Not CertifiedTopology!
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)

        assert result.rejected
        assert result.decision == AdmissionDecision.REJECTED
        assert result.rejection is not None
        assert result.rejection.reason == RejectionReason.UNCERTIFIED_TOPOLOGY

    def test_mock_object_is_rejected(self, controller, runtime_context):
        """Mock/fake CertifiedTopology should be rejected."""
        fake_certified = MagicMock()
        fake_certified._certified = False

        request = ExecutionAdmissionRequest(
            certified_topology=fake_certified,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)

        assert result.rejected

    def test_none_topology_raises_error(self, controller, runtime_context):
        """None topology should raise InvalidAdmissionRequestError."""
        request = ExecutionAdmissionRequest(
            certified_topology=None,
            runtime_context=runtime_context,
        )

        with pytest.raises(InvalidAdmissionRequestError):
            controller.evaluate(request)


# =============================================================================
# Test: Integrity Verification
# =============================================================================


class TestIntegrityVerification:
    """Tests for certification integrity verification."""

    def test_verify_certification_chain_passes(self, certified_topology):
        """Certification chain should pass for valid CertifiedTopology."""
        result = verify_certification_chain(certified_topology)

        assert result.passed
        assert result.check_name == "certification_chain"

    def test_verify_validation_signature_passes(self, certified_topology):
        """Validation signature should pass for valid CertifiedTopology."""
        result = verify_validation_signature(certified_topology)

        assert result.passed
        assert result.check_name == "validation_signature"

    def test_verify_topology_immutable_passes(self, certified_topology):
        """Topology immutability should pass for unmodified topology."""
        result = verify_topology_immutable(certified_topology)

        assert result.passed
        assert result.check_name == "topology_immutable"

    def test_verify_all_passes(self, certified_topology):
        """All integrity checks should pass for valid CertifiedTopology."""
        result = verify_all(certified_topology)

        assert result.passed
        assert len(result.checks) == 3
        assert all(c.passed for c in result.checks)

    def test_topology_hash_is_deterministic(self, sample_topology_dict):
        """Topology hash should be deterministic."""
        hash1 = compute_topology_hash(sample_topology_dict)
        hash2 = compute_topology_hash(sample_topology_dict)

        assert hash1 == hash2


# =============================================================================
# Test: Mutated Signature Rejection
# =============================================================================


class TestMutatedSignatureRejection:
    """Tests for rejection when signature is tampered."""

    def test_mutated_topology_detected(self, certified_topology):
        """Mutation of topology after certification should be detected."""
        # Directly mutate the internal dict (simulating tampering)
        certified_topology._topology_dict["tampered"] = True

        result = verify_topology_immutable(certified_topology)

        assert not result.passed
        assert "mutated" in result.message.lower()

    def test_mutated_topology_is_rejected(self, controller, runtime_context, certified_topology):
        """Mutated topology should be rejected by controller."""
        # Mutate topology
        certified_topology._topology_dict["tampered"] = True

        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)

        assert result.rejected
        assert result.rejection.reason == RejectionReason.TOPOLOGY_MUTATED


# =============================================================================
# Test: Policy Enforcement
# =============================================================================


class TestPolicyEnforcement:
    """Tests for policy enforcement."""

    def test_deterministic_policy_enforced(self, certified_topology):
        """Deterministic policy should be enforced for prototype runtime."""
        context = RuntimeExecutionContext(
            runtime_tier=RuntimeTier.PROTOTYPE,
            execution_mode=ExecutionMode.BEST_EFFORT,  # Not deterministic!
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        assert result.rejected
        assert "deterministic" in str(result.rejection.message).lower()

    def test_adapter_availability_enforced(self, certified_topology):
        """Adapter availability should be enforced."""
        context = RuntimeExecutionContext(
            requested_adapter_id="nonexistent",
            available_adapter_ids=["mock"],
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        assert result.rejected
        assert result.rejection.reason == RejectionReason.ADAPTER_UNAVAILABLE

    def test_prototype_runtime_only_enforced(self, certified_topology):
        """Prototype runtime only policy should be enforced."""
        context = RuntimeExecutionContext(
            runtime_tier=RuntimeTier.PRODUCTION,  # Not supported yet
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        assert result.rejected
        assert result.rejection.reason == RejectionReason.RUNTIME_INCOMPATIBLE


# =============================================================================
# Test: Rejection Provenance
# =============================================================================


class TestRejectionProvenance:
    """Tests for rejection provenance preservation."""

    def test_rejection_includes_reason(self, controller, runtime_context, sample_topology_dict):
        """Rejection should include reason."""
        request = ExecutionAdmissionRequest(
            certified_topology=sample_topology_dict,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)

        assert result.rejection is not None
        assert result.rejection.reason is not None

    def test_rejection_includes_message(self, controller, runtime_context, sample_topology_dict):
        """Rejection should include descriptive message."""
        request = ExecutionAdmissionRequest(
            certified_topology=sample_topology_dict,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)

        assert result.rejection.message
        assert len(result.rejection.message) > 0

    def test_rejection_serializable(self, controller, runtime_context, sample_topology_dict):
        """Rejection should be serializable to dict."""
        request = ExecutionAdmissionRequest(
            certified_topology=sample_topology_dict,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)
        rejection_dict = result.rejection.to_dict()

        assert "reason" in rejection_dict
        assert "message" in rejection_dict


# =============================================================================
# Test: Conditional Admission
# =============================================================================


class TestConditionalAdmission:
    """Tests for conditional admission behavior."""

    def test_conditional_not_emitted_by_default(self, controller, admission_request):
        """CONDITIONALLY_ADMITTED should not be emitted by default."""
        result = controller.evaluate(admission_request)

        assert result.decision != AdmissionDecision.CONDITIONALLY_ADMITTED

    def test_conditional_requires_allow_flag(self, certified_topology):
        """Conditional admission requires allow_conditionals=True."""
        context = RuntimeExecutionContext(
            allow_conditionals=True,
            available_adapter_ids=["mock"],
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        # Should be ADMITTED, not CONDITIONALLY_ADMITTED (no warnings)
        assert result.decision == AdmissionDecision.ADMITTED


# =============================================================================
# Test: Admission Trace
# =============================================================================


class TestAdmissionTrace:
    """Tests for admission trace generation."""

    def test_trace_includes_integrity_checks(self, controller, admission_request):
        """Trace should include integrity checks."""
        result = controller.evaluate(admission_request)

        assert len(result.trace.integrity_checks) >= 3

    def test_trace_includes_policy_evaluations(self, controller, admission_request):
        """Trace should include policy evaluations."""
        result = controller.evaluate(admission_request)

        assert len(result.trace.policy_evaluations) >= 1

    def test_trace_includes_timestamps(self, controller, admission_request):
        """Trace should include timestamps."""
        result = controller.evaluate(admission_request)

        assert result.trace.started_at is not None
        assert result.trace.completed_at is not None

    def test_trace_includes_decision_basis(self, controller, admission_request):
        """Trace should include decision basis."""
        result = controller.evaluate(admission_request)

        assert result.trace.decision_basis is not None


# =============================================================================
# Test: Policy Violations Observable
# =============================================================================


class TestPolicyViolationsObservable:
    """Tests for policy violation observability."""

    def test_violations_listed_in_rejection(self, certified_topology):
        """Policy violations should be listed in rejection."""
        context = RuntimeExecutionContext(
            requested_adapter_id="nonexistent",
            available_adapter_ids=[],
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        assert result.rejection is not None
        # Should have at least one violation (adapter policy)
        assert len(result.rejection.policy_violations) >= 1


# =============================================================================
# Test: Controller Does Not Mutate Topology
# =============================================================================


class TestControllerNoMutation:
    """Tests that controller does not mutate topology."""

    def test_topology_unchanged_after_admission(self, controller, admission_request, sample_topology_dict):
        """Topology should be unchanged after admission."""
        original_hash = compute_topology_hash(sample_topology_dict)

        controller.evaluate(admission_request)

        current_hash = compute_topology_hash(
            admission_request.certified_topology.topology_dict
        )
        assert current_hash == original_hash

    def test_topology_unchanged_after_rejection(self, controller, runtime_context, sample_topology_dict):
        """Topology should be unchanged after rejection."""
        original_dict = dict(sample_topology_dict)

        request = ExecutionAdmissionRequest(
            certified_topology=sample_topology_dict,
            runtime_context=runtime_context,
        )

        controller.evaluate(request)

        # Dict should be unchanged
        assert sample_topology_dict == original_dict


# =============================================================================
# Test: Controller Cannot Bypass Validation
# =============================================================================


class TestControllerCannotBypassValidation:
    """Tests that controller cannot bypass validation."""

    def test_cannot_admit_without_validation(self, runtime_context):
        """Controller cannot admit topology without validation."""
        # Create mock that looks certified but has no real validation
        mock_topology = MagicMock()
        mock_topology._certified = True
        mock_topology.validation = None  # No validation!
        mock_topology.signature = None

        request = ExecutionAdmissionRequest(
            certified_topology=mock_topology,
            runtime_context=runtime_context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        # Should be rejected due to integrity failure
        assert result.rejected


# =============================================================================
# Test: Malformed Certification Rejection
# =============================================================================


class TestMalformedCertificationRejection:
    """Tests for rejection of malformed certification."""

    def test_missing_signature_rejected(self, runtime_context):
        """Missing signature should be rejected."""
        # Create mock with missing signature
        mock_topology = MagicMock()
        mock_topology._certified = True
        mock_topology.validation = MagicMock()
        mock_topology.validation.passed = True
        mock_topology.signature = None  # Missing!

        request = ExecutionAdmissionRequest(
            certified_topology=mock_topology,
            runtime_context=runtime_context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        assert result.rejected

    def test_empty_hash_rejected(self, runtime_context):
        """Empty hash values should be rejected."""
        mock_topology = MagicMock()
        mock_topology._certified = True
        mock_topology.validation = MagicMock()
        mock_topology.validation.passed = True
        mock_topology.signature = MagicMock()
        mock_topology.signature.input_hash = ""  # Empty!
        mock_topology.signature.validation_hash = ""

        request = ExecutionAdmissionRequest(
            certified_topology=mock_topology,
            runtime_context=runtime_context,
        )

        controller = ExecutionAdmissionController(record_provenance=False)
        result = controller.evaluate(request)

        assert result.rejected


# =============================================================================
# Test: Provenance Ledger
# =============================================================================


class TestProvenanceLedger:
    """Tests for admission provenance ledger."""

    def test_ledger_records_admissions(self, certified_topology, runtime_context):
        """Ledger should record admissions."""
        ledger = AdmissionLedger()
        controller = ExecutionAdmissionController(record_provenance=False)

        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)

        # Manually record since we disabled auto-recording
        from app.cam.runtime_admission.provenance import ProvenanceBuilder
        builder = ProvenanceBuilder(request)
        builder.record_admission(["mock"], result.authorization_token or "")
        provenance = builder.build()
        ledger.record(provenance)

        assert len(ledger.get_admissions()) == 1

    def test_ledger_records_rejections(self):
        """Ledger should record rejections."""
        ledger = AdmissionLedger()

        provenance = AdmissionProvenance(
            admission_id="test-001",
            request_id="req-001",
            trace_id="trace-001",
            decision=AdmissionDecision.REJECTED,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )
        ledger.record(provenance)

        assert len(ledger.get_rejections()) == 1

    def test_ledger_get_by_request_id(self):
        """Ledger should retrieve by request ID."""
        ledger = AdmissionLedger()

        provenance = AdmissionProvenance(
            admission_id="test-001",
            request_id="specific-request",
            trace_id="trace-001",
            decision=AdmissionDecision.ADMITTED,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )
        ledger.record(provenance)

        results = ledger.get_by_request_id("specific-request")
        assert len(results) == 1
        assert results[0].request_id == "specific-request"


# =============================================================================
# Test: Policy Registry
# =============================================================================


class TestPolicyRegistry:
    """Tests for policy registry functionality."""

    def test_default_registry_has_policies(self):
        """Default registry should have standard policies."""
        registry = get_default_policy_registry()
        policies = registry.list_policies()

        assert "no_uncertified_execution" in policies
        assert "validation_required" in policies
        assert "signature_integrity" in policies

    def test_custom_registry(self, certified_topology, runtime_context):
        """Custom registry should work."""
        # Create minimal registry
        registry = AdmissionPolicyRegistry([
            NoUncertifiedExecutionPolicy(),
        ])

        controller = ExecutionAdmissionController(
            policy_registry=registry,
            record_provenance=False,
        )

        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)
        assert result.admitted

    def test_policy_add_remove(self):
        """Registry should support add/remove."""
        registry = AdmissionPolicyRegistry([])

        assert len(registry.list_policies()) == 0

        registry.add(NoUncertifiedExecutionPolicy())
        assert "no_uncertified_execution" in registry.list_policies()

        registry.remove("no_uncertified_execution")
        assert "no_uncertified_execution" not in registry.list_policies()


# =============================================================================
# Test: evaluate_or_raise
# =============================================================================


class TestEvaluateOrRaise:
    """Tests for evaluate_or_raise convenience method."""

    def test_raises_on_rejection(self, controller, runtime_context, sample_topology_dict):
        """evaluate_or_raise should raise on rejection."""
        request = ExecutionAdmissionRequest(
            certified_topology=sample_topology_dict,
            runtime_context=runtime_context,
        )

        with pytest.raises(AdmissionDeniedError):
            controller.evaluate_or_raise(request)

    def test_returns_result_on_admission(self, controller, admission_request):
        """evaluate_or_raise should return result on admission."""
        result = controller.evaluate_or_raise(admission_request)

        assert result.admitted


# =============================================================================
# Test: Serialization
# =============================================================================


class TestSerialization:
    """Tests for result serialization."""

    def test_admission_result_serializable(self, controller, admission_request):
        """Admission result should be JSON serializable."""
        result = controller.evaluate(admission_request)
        result_dict = result.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        assert len(json_str) > 0

    def test_rejection_result_serializable(self, controller, runtime_context, sample_topology_dict):
        """Rejection result should be JSON serializable."""
        request = ExecutionAdmissionRequest(
            certified_topology=sample_topology_dict,
            runtime_context=runtime_context,
        )

        result = controller.evaluate(request)
        result_dict = result.to_dict()

        json_str = json.dumps(result_dict)
        assert len(json_str) > 0
