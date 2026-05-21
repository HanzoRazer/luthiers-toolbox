# MRP-5M: Runtime Admission Control

**Sprint**: MRP-5M  
**Status**: PROTOTYPE COMPLETE  
**Date**: 2026-05-20

## Summary

Runtime admission control ensures only certified topologies enter runtime execution.
This module sits between topology validation (MRP-5I/5J) and kernel adapters (MRP-5K),
serving as the gatekeeper for execution authorization.

**Architectural chain**:
```
topology_builder CONSTRUCTS
  → topology_validation EVALUATES (returns CertifiedTopology)
    → runtime_admission AUTHORIZES ← THIS SPRINT
      → translators SERIALIZE
        → kernel_adapters EXECUTE
```

## Key Principle

**Certification ≠ Admission**

- **Certification**: Topology is structurally valid (from MRP-5I/5J)
- **Admission**: Certified topology may proceed to runtime execution

A topology may be certified but denied admission due to:
- Runtime tier incompatibility (e.g., production tier not supported)
- Execution mode mismatch (e.g., best-effort in prototype)
- Adapter unavailability
- Policy violations

## Implementation

### Module Structure

```
app/cam/runtime_admission/
├── __init__.py         # Package exports
├── contracts.py        # Data contracts and enums
├── controller.py       # ExecutionAdmissionController
├── exceptions.py       # Admission-specific exceptions
├── integrity.py        # Certification integrity verification
└── policies.py         # Admission policies and registry
```

### Core Components

#### ExecutionAdmissionController

The main controller that orchestrates admission evaluation:

```python
from app.cam.runtime_admission import (
    ExecutionAdmissionController,
    ExecutionAdmissionRequest,
    RuntimeExecutionContext,
)

controller = ExecutionAdmissionController()

context = RuntimeExecutionContext(
    runtime_tier=RuntimeTier.PROTOTYPE,
    execution_mode=ExecutionMode.DETERMINISTIC,
    available_adapter_ids=["mock", "step_acoustic"],
)

request = ExecutionAdmissionRequest(
    certified_topology=certified_topology,
    runtime_context=context,
)

result = controller.evaluate(request)

if result.admitted:
    print(f"Admitted with token: {result.authorization_token}")
    print(f"Authorized adapters: {result.authorized_adapters}")
else:
    print(f"Rejected: {result.rejection.reason}")
```

#### Admission Policies

Six default policies enforce admission rules:

| Policy ID | Description | Severity |
|-----------|-------------|----------|
| `no_uncertified_execution` | Only CertifiedTopology may be submitted | BLOCKING |
| `validation_required` | Topology must have passed validation | BLOCKING |
| `signature_integrity` | Certification signature must be present | BLOCKING |
| `prototype_runtime_only` | Only PROTOTYPE tier currently supported | BLOCKING |
| `deterministic_only` | Prototype requires deterministic execution | BLOCKING |
| `adapter_available` | Requested adapter must be available | BLOCKING |

#### Integrity Verification

Three integrity checks verify certification authenticity:

```python
from app.cam.runtime_admission import verify_all

result = verify_all(certified_topology)
if result.passed:
    print("All integrity checks passed")
else:
    print(f"Violation: {result.violation_type}")
    for check in result.failed_checks:
        print(f"  - {check.check_name}: {check.message}")
```

Checks performed:
- `certification_chain`: CertifiedTopology wrapper is valid
- `validation_signature`: Signature hashes are present
- `topology_immutable`: Content hash matches original

### Contracts

#### RuntimeExecutionContext

```python
@dataclass
class RuntimeExecutionContext:
    runtime_tier: RuntimeTier = RuntimeTier.PROTOTYPE
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    requested_adapter_id: Optional[str] = None
    available_adapter_ids: List[str] = field(default_factory=list)
    request_id: str  # Auto-generated UUID
    trace_id: str    # Auto-generated UUID
    allow_conditionals: bool = False
```

#### ExecutionAdmissionResult

```python
@dataclass
class ExecutionAdmissionResult:
    decision: AdmissionDecision  # ADMITTED, REJECTED, CONDITIONALLY_ADMITTED
    request_id: str
    trace_id: str
    trace: AdmissionTrace
    rejection: Optional[AdmissionRejection] = None
    warnings: List[PolicyEvaluationResult] = field(default_factory=list)
    authorized_adapters: List[str] = field(default_factory=list)
    authorization_token: Optional[str] = None
```

### Enums

```python
class AdmissionDecision(str, Enum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    CONDITIONALLY_ADMITTED = "CONDITIONALLY_ADMITTED"

class RuntimeTier(str, Enum):
    PROTOTYPE = "PROTOTYPE"
    PRODUCTION = "PRODUCTION"

class ExecutionMode(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    BEST_EFFORT = "BEST_EFFORT"

class RejectionReason(str, Enum):
    UNCERTIFIED_TOPOLOGY = "UNCERTIFIED_TOPOLOGY"
    INTEGRITY_VIOLATION = "INTEGRITY_VIOLATION"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"
    RUNTIME_INCOMPATIBLE = "RUNTIME_INCOMPATIBLE"
    SIGNATURE_MISMATCH = "SIGNATURE_MISMATCH"
    TOPOLOGY_MUTATED = "TOPOLOGY_MUTATED"
```

## Test Coverage

45 tests in `tests/cam/test_runtime_admission.py`:

- `TestAdmissionControllerBasic` (5 tests): Controller instantiation and basic evaluation
- `TestAdmissionControllerRejection` (3 tests): Rejection scenarios
- `TestIntegrityVerification` (6 tests): Integrity check functions
- `TestPolicyEvaluation` (10 tests): Individual policy behavior
- `TestPolicyRegistry` (5 tests): Registry operations
- `TestAdmissionTrace` (4 tests): Trace generation
- `TestAdmissionContracts` (4 tests): Contract serialization
- `TestAdmissionExceptions` (3 tests): Exception behavior
- `TestTopologyHash` (3 tests): Hash computation
- `TestFactoryFunction` (2 tests): Factory functions

## Integration Points

### Upstream (MRP-5I/5J)

Receives `CertifiedTopology` from `TopologyValidator.certify()`:

```python
from app.cam.topology_validation import TopologyValidator, ValidationTier

validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
certified = validator.certify(topology_dict)  # Returns CertifiedTopology
```

### Downstream (MRP-5K)

Provides `ExecutionAdmissionResult` to kernel adapters:

```python
if result.admitted:
    for adapter_id in result.authorized_adapters:
        adapter = get_adapter(adapter_id)
        artifact = adapter.execute(certified_topology)
```

### Downstream (MRP-5N)

Provides admission result for provenance recording:

```python
from app.cam.runtime_provenance import RuntimeProvenanceRecorder

recorder = RuntimeProvenanceRecorder()
bundle = recorder.record(
    certified_topology=certified,
    admission_result=result,  # From this module
    artifact=artifact,
    translator_id="step_acoustic",
    adapter_id="mock",
)
```

## Extension Points

### Custom Policies

```python
class MyCustomPolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "my_custom_policy"
    
    @property
    def description(self) -> str:
        return "Enforces custom business rule"
    
    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        # Custom logic
        if some_condition:
            return PolicyResult(passed=True, severity=PolicySeverity.INFO, message="OK")
        return PolicyResult(passed=False, severity=PolicySeverity.BLOCKING, message="Failed")

# Register
registry = AdmissionPolicyRegistry()
registry.add(MyCustomPolicy())
controller = ExecutionAdmissionController(policy_registry=registry)
```

### Configuration

```python
config = AdmissionConfiguration(
    strict_mode=True,
    allow_conditional_admission=False,
    require_all_policies_pass=True,
    log_decisions=True,
    record_provenance=True,
)
controller = ExecutionAdmissionController(config=config)
```

## Files

| File | Purpose |
|------|---------|
| `app/cam/runtime_admission/__init__.py` | Package exports |
| `app/cam/runtime_admission/contracts.py` | Data contracts |
| `app/cam/runtime_admission/controller.py` | Main controller |
| `app/cam/runtime_admission/exceptions.py` | Exception types |
| `app/cam/runtime_admission/integrity.py` | Integrity verification |
| `app/cam/runtime_admission/policies.py` | Policy framework |
| `tests/cam/test_runtime_admission.py` | Test suite (45 tests) |

## Next Steps

- **MRP-5N**: Runtime Artifact Provenance & Replay Infrastructure (in progress)
- **Production tier support**: Add PRODUCTION runtime tier policies
- **Conditional admission**: Implement WARNING-level policy handling
