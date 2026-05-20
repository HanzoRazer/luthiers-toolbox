# MRP Dev Order 5M — Runtime Admission Control Handoff

**Date:** 2026-05-20  
**Author:** Claude (MRP Dev Order 5M)  
**Status:** COMPLETE

---

## Summary

Implemented runtime admission control infrastructure, establishing the boundary between certification and execution. The ExecutionAdmissionController determines whether certified topology may enter the executable runtime pipeline, enforcing constitutional governance at the runtime boundary.

**Key outcome:** Certification ≠ Admission. A certified topology must still pass admission evaluation before execution is authorized.

---

## Architectural Intent

MRP-5L established governed executable integration infrastructure.  
MRP-5M establishes runtime admission control.

The objective is:
```
ensure only constitutionally-valid execution
may enter the executable pipeline
```

This sprint operationalizes the constitutional boundary:
```
semantic governance → executable runtime enforcement
```

---

## Scope

### In Scope (Completed)

- Execution admission contracts
- Admission decisions (ADMITTED, REJECTED, CONDITIONALLY_ADMITTED)
- Runtime rejection classifications
- Certification integrity verification
- Policy framework with 6 default policies
- Runtime observability via admission trace
- Provenance tracking via ledger
- 42 tests covering all categories

### Out of Scope (Per 5M Guardrails)

- Topology repair
- Adaptive runtime selection
- Semantic inference
- Kernel expansion
- Distributed execution
- Async orchestration
- Automatic retry logic

---

## Deliverables

| Deliverable | Location | Purpose |
|-------------|----------|---------|
| contracts.py | app/cam/runtime_admission/ | Request/result contracts |
| controller.py | app/cam/runtime_admission/ | ExecutionAdmissionController |
| policies.py | app/cam/runtime_admission/ | Policy framework |
| integrity.py | app/cam/runtime_admission/ | Certification integrity checks |
| provenance.py | app/cam/runtime_admission/ | Admission tracking |
| exceptions.py | app/cam/runtime_admission/ | Admission exceptions |
| __init__.py | app/cam/runtime_admission/ | Public exports |
| test_runtime_admission.py | tests/cam/ | 42 tests |
| MRP_5M_RUNTIME_ADMISSION_CONTROL.md | docs/handoffs/ | This document |

---

## Architecture

### State Progression

| State | Meaning |
|-------|---------|
| constructed | topology exists |
| validated | topology evaluated |
| certified | topology approved for runtime |
| **admitted** | **execution authorized** |
| serialized | artifact generated |

MRP-5H/I/J/K established construction, validation, certification, serialization.  
MRP-5M establishes **runtime admission authority**.

### Runtime Flow After MRP-5M

```
TopologyBuilder
    ↓
TopologyValidation
    ↓
CertifiedTopology
    ↓
ExecutionAdmissionController   ← NEW
    ↓
PipelineOrchestrator (future)
    ↓
Translator
    ↓
KernelAdapter
    ↓
Artifact
```

---

## Core Contracts

### ExecutionAdmissionRequest

Wraps CertifiedTopology with runtime context:

```python
request = ExecutionAdmissionRequest(
    certified_topology=certified,
    runtime_context=RuntimeExecutionContext(
        runtime_tier=RuntimeTier.PROTOTYPE,
        execution_mode=ExecutionMode.DETERMINISTIC,
        available_adapter_ids=["mock"],
    ),
)
```

### RuntimeExecutionContext

| Field | Type | Purpose |
|-------|------|---------|
| runtime_tier | PROTOTYPE / PRODUCTION | Execution tier |
| execution_mode | DETERMINISTIC / BEST_EFFORT | Reproducibility mode |
| requested_adapter_id | str (optional) | Specific adapter request |
| available_adapter_ids | list[str] | Available adapters |
| request_id | str | Request tracking |
| trace_id | str | Distributed tracing |
| allow_conditionals | bool | Allow conditional admission |
| environment_label | str (optional) | Environment identifier |

### ExecutionAdmissionResult

```python
result = controller.evaluate(request)

if result.admitted:
    print(f"Admitted with adapters: {result.authorized_adapters}")
    print(f"Authorization token: {result.authorization_token}")
else:
    print(f"Rejected: {result.rejection.reason}")
    print(f"Message: {result.rejection.message}")
```

### AdmissionDecision

| Decision | Meaning |
|----------|---------|
| ADMITTED | Execution authorized |
| REJECTED | Execution denied |
| CONDITIONALLY_ADMITTED | Admitted with warnings |

---

## Integrity Verification

Three-layer integrity verification before policy evaluation:

### 1. Certification Chain

Verifies CertifiedTopology structure:
- `_certified` flag is set
- Validation result exists and passed
- Signature exists

### 2. Validation Signature

Verifies signature is well-formed:
- `input_hash` is present
- `validation_hash` is present
- Neither is empty

### 3. Topology Immutability

Verifies topology hasn't been mutated:
- Recomputes hash of topology_dict
- Compares to signature.input_hash
- Detects post-certification tampering

---

## Policy Framework

### Default Policies

| Policy | Purpose | Severity |
|--------|---------|----------|
| no_uncertified_execution | Only CertifiedTopology allowed | BLOCKING |
| validation_required | Topology must have passed validation | BLOCKING |
| signature_integrity | Certification signature must exist | BLOCKING |
| prototype_runtime_only | Only PROTOTYPE tier supported | BLOCKING |
| deterministic_only | DETERMINISTIC mode required for prototype | BLOCKING |
| adapter_available | Requested adapter must be available | BLOCKING |

### Policy Evaluation

```python
registry = AdmissionPolicyRegistry()
results = registry.evaluate_all(request)

for result in results:
    print(f"{result.policy_id}: {'PASS' if result.passed else 'FAIL'}")
```

### Custom Policies

```python
class MyCustomPolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "my_custom_policy"
    
    def evaluate(self, request) -> PolicyResult:
        # Custom logic
        return PolicyResult(passed=True, ...)

registry = AdmissionPolicyRegistry([
    NoUncertifiedExecutionPolicy(),
    MyCustomPolicy(),
])
controller = ExecutionAdmissionController(policy_registry=registry)
```

---

## Rejection Reasons

| Reason | Trigger |
|--------|---------|
| UNCERTIFIED_TOPOLOGY | Not CertifiedTopology |
| INTEGRITY_VIOLATION | Generic integrity failure |
| POLICY_VIOLATION | Policy evaluation failed |
| ADAPTER_UNAVAILABLE | Requested adapter not available |
| RUNTIME_INCOMPATIBLE | Runtime tier not supported |
| SIGNATURE_MISMATCH | Signature verification failed |
| TOPOLOGY_MUTATED | Topology modified after certification |

---

## Provenance Tracking

### AdmissionProvenance

Records complete evaluation path:
- Admission ID
- Request/trace IDs
- Decision
- Integrity check results
- Policy evaluation results
- Rejection details (if rejected)
- Authorized adapters (if admitted)
- Duration

### AdmissionLedger

In-memory ledger for recent admissions:

```python
ledger = get_admission_ledger()
ledger.get_by_request_id("req-123")
ledger.get_rejections()
ledger.get_admissions()
ledger.get_recent(10)
```

---

## Test Coverage

42 tests in 14 categories:

| Category | Tests | Coverage |
|----------|-------|----------|
| Certified Topology Admission | 4 | Happy path |
| Uncertified Topology Rejection | 3 | Constitutional enforcement |
| Integrity Verification | 5 | Chain, signature, immutability |
| Mutated Signature Rejection | 2 | Tampering detection |
| Policy Enforcement | 3 | Deterministic, adapter, runtime |
| Rejection Provenance | 3 | Reason, message, serialization |
| Conditional Admission | 2 | Default behavior, allow flag |
| Admission Trace | 4 | Checks, evaluations, timestamps |
| Policy Violations Observable | 1 | Violation listing |
| Controller No Mutation | 2 | Topology unchanged |
| Controller Cannot Bypass | 1 | Validation required |
| Malformed Certification | 2 | Missing/empty signature |
| Provenance Ledger | 3 | Record, retrieve |
| Policy Registry | 3 | Default, custom, add/remove |
| Evaluate Or Raise | 2 | Exception on rejection |
| Serialization | 2 | JSON serializable |

All tests pass.

---

## Usage Example

```python
from app.cam.runtime_admission import (
    ExecutionAdmissionController,
    ExecutionAdmissionRequest,
    RuntimeExecutionContext,
)
from app.cam.topology_validation import TopologyValidator

# 1. Certify topology
validator = TopologyValidator()
certified = validator.certify(topology_dict)

# 2. Create admission request
context = RuntimeExecutionContext(
    available_adapter_ids=["mock"],
)
request = ExecutionAdmissionRequest(
    certified_topology=certified,
    runtime_context=context,
)

# 3. Evaluate admission
controller = ExecutionAdmissionController()
result = controller.evaluate(request)

# 4. Handle result
if result.admitted:
    # Proceed with execution
    print(f"Authorized adapters: {result.authorized_adapters}")
    print(f"Token: {result.authorization_token}")
else:
    # Handle rejection
    print(f"Rejected: {result.rejection.reason}")
    for violation in result.rejection.policy_violations:
        print(f"  - {violation.policy_id}: {violation.message}")
```

---

## Rejection Philosophy

Rejection is first-class:
- Expected
- Observable
- Governed

The repo normalizes **safe rejection** rather than:
- Silent coercion
- Hidden downgrade paths
- Automatic repair

Every rejection produces:
- Explicit reason
- Policy violations list
- Provenance record
- Traceable audit trail

---

## Connection to Prior Sprints

| Sprint | Focus | Contribution |
|--------|-------|--------------|
| MRP-5H | Topology Builder | Construction |
| MRP-5I | Topology Validation | Evaluation + CertifiedTopology |
| MRP-5J | STEP Translator | CertifiedTopology consumption |
| MRP-5K | Kernel Adapters | Execution mechanics |
| **MRP-5M** | **Admission Control** | **Runtime authorization** |

---

## Verification

```bash
cd services/api
python -m pytest tests/cam/test_runtime_admission.py -v
# 42 passed
```

---

## Future Work

### Deferred Utilities

- `inspect_admission_trace.py` — Execution visibility utility
- `verify_certification_chain.py` — Integrity inspection utility
- `audit_runtime_admissions.py` — Admission audit utility

### Future Sprints

- Runtime policy expansion
- Production tier support
- Distributed admission control
- Admission caching
- Policy versioning
