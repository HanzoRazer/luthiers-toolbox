"""
Tests for Runtime Admission Control (MRP-5M).

Sprint: MRP-5M
Status: PROTOTYPE

Tests the runtime admission infrastructure:
- Policy evaluation
- Integrity verification
- Admission decisions
- Trace generation
"""

import pytest
from unittest.mock import MagicMock

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
    AdmissionConfiguration,
    ExecutionAdmissionController,
    get_admission_controller,
    # Exceptions
    AdmissionDeniedError,
    AdmissionError,
    IntegrityViolationError,
    InvalidAdmissionRequestError,
    PolicyViolationError,
    UncertifiedTopologyError,
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
    PolicyResult,
    PolicySeverity,
    PrototypeRuntimeOnlyPolicy,
    SignatureIntegrityPolicy,
    ValidationRequiredPolicy,
    get_default_policy_registry,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_topology_dict():
    """Valid topology dictionary that passes validation."""
    return {
        "request_id": "test-admission-001",
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
def certified_topology(valid_topology_dict):
    """Create a valid CertifiedTopology."""
    validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
    return validator.certify(valid_topology_dict)


@pytest.fixture
def runtime_context():
    """Create a RuntimeExecutionContext."""
    return RuntimeExecutionContext(
        runtime_tier=RuntimeTier.PROTOTYPE,
        execution_mode=ExecutionMode.DETERMINISTIC,
        available_adapter_ids=["mock", "step_acoustic"],
    )


@pytest.fixture
def admission_request(certified_topology, runtime_context):
    """Create an ExecutionAdmissionRequest."""
    return ExecutionAdmissionRequest(
        certified_topology=certified_topology,
        runtime_context=runtime_context,
    )


@pytest.fixture
def controller():
    """Create an ExecutionAdmissionController."""
    return ExecutionAdmissionController()


# =============================================================================
# Test Classes
# =============================================================================


class TestAdmissionControllerBasic:
    """Tests for basic admission controller functionality."""

    def test_controller_created(self, controller):
        """Controller can be instantiated."""
        assert controller is not None
        assert controller.policy_registry is not None

    def test_controller_has_default_policies(self, controller):
        """Controller has default policies."""
        policies = controller.policy_registry.list_policies()
        assert "no_uncertified_execution" in policies
        assert "validation_required" in policies
        assert "signature_integrity" in policies
        assert "prototype_runtime_only" in policies
        assert "deterministic_only" in policies
        assert "adapter_available" in policies

    def test_evaluate_returns_result(self, controller, admission_request):
        """Controller evaluate returns an ExecutionAdmissionResult."""
        result = controller.evaluate(admission_request)
        assert isinstance(result, ExecutionAdmissionResult)

    def test_valid_request_admitted(self, controller, admission_request):
        """Valid request is admitted."""
        result = controller.evaluate(admission_request)
        assert result.admitted
        assert result.decision == AdmissionDecision.ADMITTED

    def test_admitted_has_authorization_token(self, controller, admission_request):
        """Admitted request has authorization token."""
        result = controller.evaluate(admission_request)
        assert result.authorization_token is not None


class TestAdmissionControllerRejection:
    """Tests for admission rejection scenarios."""

    def test_uncertified_topology_rejected(self, controller, runtime_context):
        """Uncertified topology is rejected."""
        request = ExecutionAdmissionRequest(
            certified_topology={"not": "certified"},
            runtime_context=runtime_context,
        )
        result = controller.evaluate(request)
        assert result.rejected
        assert result.rejection.reason == RejectionReason.UNCERTIFIED_TOPOLOGY

    def test_none_topology_rejected(self, controller, runtime_context):
        """None topology is rejected."""
        request = ExecutionAdmissionRequest(
            certified_topology=None,
            runtime_context=runtime_context,
        )
        result = controller.evaluate(request)
        assert result.rejected

    def test_production_tier_rejected(self, controller, certified_topology):
        """Production tier request is rejected in prototype mode."""
        context = RuntimeExecutionContext(
            runtime_tier=RuntimeTier.PRODUCTION,
            available_adapter_ids=["mock"],
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )
        result = controller.evaluate(request)
        assert result.rejected
        assert result.rejection.reason == RejectionReason.POLICY_VIOLATION


class TestIntegrityVerification:
    """Tests for certification integrity verification."""

    def test_verify_certification_chain_passes(self, certified_topology):
        """Certification chain verification passes for valid topology."""
        result = verify_certification_chain(certified_topology)
        assert result.passed
        assert result.check_name == "certification_chain"

    def test_verify_certification_chain_fails_non_certified(self):
        """Certification chain fails for non-certified object."""
        result = verify_certification_chain({"not": "certified"})
        assert not result.passed

    def test_verify_validation_signature_passes(self, certified_topology):
        """Validation signature verification passes."""
        result = verify_validation_signature(certified_topology)
        assert result.passed

    def test_verify_topology_immutable_passes(self, certified_topology):
        """Topology immutability verification passes."""
        result = verify_topology_immutable(certified_topology)
        assert result.passed

    def test_verify_all_passes(self, certified_topology):
        """All integrity checks pass."""
        result = verify_all(certified_topology)
        assert result.passed
        assert len(result.checks) == 3
        assert all(c.passed for c in result.checks)

    def test_verify_all_detects_mutation(self, certified_topology):
        """Integrity check detects topology mutation."""
        certified_topology.topology_dict["mutated"] = True
        result = verify_all(certified_topology)
        assert not result.passed
        assert result.violation_type == "TOPOLOGY_IMMUTABLE"


class TestPolicyEvaluation:
    """Tests for individual policy evaluation."""

    def test_no_uncertified_execution_policy_passes(self, certified_topology, runtime_context):
        """NoUncertifiedExecutionPolicy passes for certified topology."""
        policy = NoUncertifiedExecutionPolicy()
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )
        result = policy.evaluate(request)
        assert result.passed

    def test_no_uncertified_execution_policy_fails(self, runtime_context):
        """NoUncertifiedExecutionPolicy fails for uncertified topology."""
        policy = NoUncertifiedExecutionPolicy()
        request = ExecutionAdmissionRequest(
            certified_topology={"not": "certified"},
            runtime_context=runtime_context,
        )
        result = policy.evaluate(request)
        assert not result.passed
        assert result.severity == PolicySeverity.BLOCKING

    def test_validation_required_policy_passes(self, certified_topology, runtime_context):
        """ValidationRequiredPolicy passes for validated topology."""
        policy = ValidationRequiredPolicy()
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )
        result = policy.evaluate(request)
        assert result.passed

    def test_prototype_runtime_only_policy_passes(self, certified_topology, runtime_context):
        """PrototypeRuntimeOnlyPolicy passes for prototype tier."""
        policy = PrototypeRuntimeOnlyPolicy()
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )
        result = policy.evaluate(request)
        assert result.passed

    def test_prototype_runtime_only_policy_fails(self, certified_topology):
        """PrototypeRuntimeOnlyPolicy fails for production tier."""
        policy = PrototypeRuntimeOnlyPolicy()
        context = RuntimeExecutionContext(runtime_tier=RuntimeTier.PRODUCTION)
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )
        result = policy.evaluate(request)
        assert not result.passed

    def test_deterministic_only_policy_passes(self, certified_topology, runtime_context):
        """DeterministicOnlyPolicy passes for deterministic mode."""
        policy = DeterministicOnlyPolicy()
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )
        result = policy.evaluate(request)
        assert result.passed

    def test_deterministic_only_policy_fails_best_effort(self, certified_topology):
        """DeterministicOnlyPolicy fails for best-effort in prototype."""
        policy = DeterministicOnlyPolicy()
        context = RuntimeExecutionContext(
            runtime_tier=RuntimeTier.PROTOTYPE,
            execution_mode=ExecutionMode.BEST_EFFORT,
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )
        result = policy.evaluate(request)
        assert not result.passed

    def test_adapter_available_policy_passes(self, certified_topology):
        """AdapterAvailablePolicy passes when adapter available."""
        policy = AdapterAvailablePolicy()
        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock", "step"],
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )
        result = policy.evaluate(request)
        assert result.passed

    def test_adapter_available_policy_fails(self, certified_topology):
        """AdapterAvailablePolicy fails when adapter unavailable."""
        policy = AdapterAvailablePolicy()
        context = RuntimeExecutionContext(
            requested_adapter_id="nonexistent",
            available_adapter_ids=["mock", "step"],
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=context,
        )
        result = policy.evaluate(request)
        assert not result.passed


class TestPolicyRegistry:
    """Tests for AdmissionPolicyRegistry."""

    def test_registry_created_with_defaults(self):
        """Registry created with default policies."""
        registry = AdmissionPolicyRegistry()
        assert len(registry.list_policies()) == 6

    def test_registry_add_policy(self):
        """Can add policy to registry."""
        registry = AdmissionPolicyRegistry(policies=[])
        policy = NoUncertifiedExecutionPolicy()
        registry.add(policy)
        assert "no_uncertified_execution" in registry.list_policies()

    def test_registry_remove_policy(self):
        """Can remove policy from registry."""
        registry = AdmissionPolicyRegistry()
        assert registry.remove("no_uncertified_execution")
        assert "no_uncertified_execution" not in registry.list_policies()

    def test_registry_get_policy(self):
        """Can get policy by id."""
        registry = AdmissionPolicyRegistry()
        policy = registry.get("no_uncertified_execution")
        assert policy is not None
        assert policy.policy_id == "no_uncertified_execution"

    def test_registry_evaluate_all(self, certified_topology, runtime_context):
        """Registry can evaluate all policies."""
        registry = AdmissionPolicyRegistry()
        request = ExecutionAdmissionRequest(
            certified_topology=certified_topology,
            runtime_context=runtime_context,
        )
        results = registry.evaluate_all(request)
        assert len(results) == 6
        assert all(isinstance(r, PolicyEvaluationResult) for r in results)


class TestAdmissionTrace:
    """Tests for admission trace generation."""

    def test_trace_generated(self, controller, admission_request):
        """Admission generates a trace."""
        result = controller.evaluate(admission_request)
        assert result.trace is not None
        assert result.trace.request_id == admission_request.request_id

    def test_trace_has_integrity_checks(self, controller, admission_request):
        """Trace includes integrity checks."""
        result = controller.evaluate(admission_request)
        assert len(result.trace.integrity_checks) > 0

    def test_trace_has_policy_evaluations(self, controller, admission_request):
        """Trace includes policy evaluations."""
        result = controller.evaluate(admission_request)
        assert len(result.trace.policy_evaluations) > 0

    def test_trace_completed(self, controller, admission_request):
        """Trace is marked completed."""
        result = controller.evaluate(admission_request)
        assert result.trace.completed_at is not None
        assert result.trace.decision_basis is not None


class TestAdmissionContracts:
    """Tests for admission contract dataclasses."""

    def test_runtime_context_defaults(self):
        """RuntimeExecutionContext has sensible defaults."""
        context = RuntimeExecutionContext()
        assert context.runtime_tier == RuntimeTier.PROTOTYPE
        assert context.execution_mode == ExecutionMode.DETERMINISTIC
        assert context.request_id is not None
        assert context.trace_id is not None

    def test_runtime_context_to_dict(self):
        """RuntimeExecutionContext serializes to dict."""
        context = RuntimeExecutionContext(
            runtime_tier=RuntimeTier.PROTOTYPE,
            available_adapter_ids=["mock"],
        )
        d = context.to_dict()
        assert d["runtime_tier"] == "PROTOTYPE"
        assert d["available_adapter_ids"] == ["mock"]

    def test_execution_admission_result_to_dict(self, controller, admission_request):
        """ExecutionAdmissionResult serializes to dict."""
        result = controller.evaluate(admission_request)
        d = result.to_dict()
        assert "decision" in d
        assert "admitted" in d
        assert "trace" in d

    def test_policy_evaluation_result_to_dict(self):
        """PolicyEvaluationResult serializes to dict."""
        result = PolicyEvaluationResult(
            policy_id="test",
            passed=True,
            severity="INFO",
            message="Test passed",
        )
        d = result.to_dict()
        assert d["policy_id"] == "test"
        assert d["passed"] is True


class TestAdmissionExceptions:
    """Tests for admission exceptions."""

    def test_admission_error_to_dict(self):
        """AdmissionError serializes to dict."""
        error = AdmissionError(
            message="Test error",
            error_code="TEST_ERROR",
        )
        d = error.to_dict()
        assert d["error_code"] == "TEST_ERROR"
        assert d["message"] == "Test error"

    def test_integrity_violation_error(self):
        """IntegrityViolationError has expected fields."""
        error = IntegrityViolationError(
            message="Hash mismatch",
            violation_type="TOPOLOGY_MUTATED",
            expected_hash="abc123",
            actual_hash="def456",
        )
        assert error.violation_type == "TOPOLOGY_MUTATED"
        assert error.expected_hash == "abc123"
        assert error.actual_hash == "def456"

    def test_policy_violation_error(self):
        """PolicyViolationError has expected fields."""
        error = PolicyViolationError(
            message="Policy failed",
            policy_id="test_policy",
            severity="BLOCKING",
        )
        assert error.policy_id == "test_policy"
        assert error.severity == "BLOCKING"


class TestTopologyHash:
    """Tests for topology hash computation."""

    def test_compute_topology_hash(self, valid_topology_dict):
        """Can compute topology hash."""
        hash_val = compute_topology_hash(valid_topology_dict)
        assert hash_val is not None
        assert len(hash_val) == 16

    def test_topology_hash_deterministic(self, valid_topology_dict):
        """Topology hash is deterministic."""
        hash1 = compute_topology_hash(valid_topology_dict)
        hash2 = compute_topology_hash(valid_topology_dict)
        assert hash1 == hash2

    def test_topology_hash_changes_on_mutation(self, valid_topology_dict):
        """Topology hash changes when content changes."""
        hash1 = compute_topology_hash(valid_topology_dict)
        valid_topology_dict["mutated"] = True
        hash2 = compute_topology_hash(valid_topology_dict)
        assert hash1 != hash2


class TestFactoryFunction:
    """Tests for factory functions."""

    def test_get_admission_controller(self):
        """Factory creates controller."""
        controller = get_admission_controller()
        assert isinstance(controller, ExecutionAdmissionController)

    def test_get_admission_controller_with_config(self):
        """Factory accepts config."""
        config = AdmissionConfiguration(strict_mode=False)
        controller = get_admission_controller(config=config)
        assert controller.config.strict_mode is False

    def test_get_default_policy_registry(self):
        """Factory creates registry with defaults."""
        registry = get_default_policy_registry()
        assert len(registry.list_policies()) == 6
