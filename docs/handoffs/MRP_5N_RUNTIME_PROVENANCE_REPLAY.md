# MRP-5N: Runtime Artifact Provenance & Replay Infrastructure

**Sprint**: MRP-5N  
**Status**: PROTOTYPE COMPLETE  
**Date**: 2026-05-20

## Summary

Runtime provenance infrastructure preserves executable lineage across the certified
runtime pipeline. Every artifact can answer: What produced me? From what certified
topology? Under what admission decision? Can this run be replayed?

**Architectural chain**:
```
topology_builder CONSTRUCTS
  → topology_validation EVALUATES (returns CertifiedTopology)
    → runtime_admission AUTHORIZES (returns ExecutionAdmissionResult)
      → translators SERIALIZE
        → kernel_adapters EXECUTE
          → runtime_provenance RECORDS ← THIS SPRINT
```

## Key Principle

**Provenance = Complete Lineage**

A RuntimeReplayBundle captures everything needed to:
1. Verify the artifact was produced legitimately
2. Understand the full production chain
3. Detect tampering at any stage
4. Audit the runtime decisions

## Implementation

### Module Structure

```
app/cam/runtime_provenance/
├── __init__.py         # Package exports
├── contracts.py        # Data contracts (provenance, lineage, bundle)
├── exceptions.py       # Provenance-specific exceptions
├── integrity.py        # Integrity verification functions
├── recorder.py         # RuntimeProvenanceRecorder
├── replay.py           # RuntimeReplayEngine
└── serialization.py    # Stable JSON hashing utilities
```

### Core Components

#### RuntimeProvenanceRecorder

Records provenance after artifact production:

```python
from app.cam.runtime_provenance import RuntimeProvenanceRecorder

recorder = RuntimeProvenanceRecorder()
bundle = recorder.record(
    certified_topology=certified_topology,
    admission_result=admission_result,
    artifact=artifact,
    translator_id="step_acoustic",
    adapter_id="mock",
)

print(f"Run ID: {bundle.run_id}")
print(f"Artifact hash: {bundle.artifact_lineage.artifact_hash}")
```

#### RuntimeReplayEngine

Verifies bundle integrity without re-execution:

```python
from app.cam.runtime_provenance import RuntimeReplayEngine

engine = RuntimeReplayEngine()
result = engine.verify(bundle)

if result.passed:
    print("Bundle verified successfully")
else:
    print(f"Verification failed: {result.message}")
    for check in result.failed_checks:
        print(f"  - {check.check_name}: {check.reason}")
```

#### Stable JSON Serialization

Deterministic hashing for content verification:

```python
from app.cam.runtime_provenance import (
    stable_json_dumps,
    stable_hash_model,
    verify_hash_match,
)

# Deterministic JSON
json_str = stable_json_dumps(data)  # Sorted keys, no extra whitespace

# Hash any object
hash_val = stable_hash_model(obj)

# Verify hash
if verify_hash_match(content, expected_hash):
    print("Content unchanged")
```

### Contracts

#### RuntimeReplayBundle

The complete provenance package:

```python
@dataclass
class RuntimeReplayBundle:
    run_id: str                           # Unique execution ID
    created_at: str                       # ISO timestamp
    source_topology: Dict[str, Any]       # Original topology dict
    validation_lineage: ValidationLineage # Validation chain
    admission_lineage: AdmissionLineage   # Admission decision
    artifact_lineage: ArtifactLineage     # Artifact metadata
    trace_events: List[RuntimeTraceEvent] # Ordered event log
    provenance_hash: str                  # Bundle integrity hash
    is_replayable: bool                   # Can be re-verified
    replay_constraints: List[str]         # Why not replayable
```

#### ValidationLineage

Preserves validation decision:

```python
@dataclass
class ValidationLineage:
    request_id: str
    validation_tier: str
    passed: bool
    input_hash: str
    validation_hash: str
    timestamp: str
```

#### AdmissionLineage

Preserves admission decision:

```python
@dataclass
class AdmissionLineage:
    admission_id: str
    decision: str  # ADMITTED, REJECTED, CONDITIONALLY_ADMITTED
    authorized_adapters: List[str]
    policy_results: List[Dict[str, Any]]
    timestamp: str
```

#### ArtifactLineage

Preserves artifact metadata:

```python
@dataclass
class ArtifactLineage:
    artifact_id: str
    artifact_type: str
    artifact_hash: str
    artifact_size: int
    translator_id: str
    adapter_id: str
    metadata: Dict[str, Any]
```

#### RuntimeTraceEvent

Ordered event log:

```python
@dataclass
class RuntimeTraceEvent:
    event_type: TraceEventType
    timestamp: str
    sequence: int
    details: Dict[str, Any]

class TraceEventType(str, Enum):
    VALIDATION_CERTIFIED = "VALIDATION_CERTIFIED"
    ADMISSION_COMPLETED = "ADMISSION_COMPLETED"
    TRANSLATION_COMPLETED = "TRANSLATION_COMPLETED"
    ADAPTER_COMPLETED = "ADAPTER_COMPLETED"
    ARTIFACT_RECORDED = "ARTIFACT_RECORDED"
    REPLAY_VERIFIED = "REPLAY_VERIFIED"
```

### Integrity Verification

Six integrity checks:

| Function | Purpose |
|----------|---------|
| `verify_artifact_hash()` | Artifact content unchanged |
| `verify_validation_signature()` | Validation hashes present and valid |
| `verify_admission_signature()` | Admission decision properly recorded |
| `verify_trace_order()` | Events in correct sequence |
| `verify_provenance_hash()` | Bundle hash matches content |
| `verify_bundle_hash()` | Overall bundle integrity |

Combined verification:

```python
from app.cam.runtime_provenance import verify_replay_bundle_integrity

result = verify_replay_bundle_integrity(bundle)
if result.passed:
    print("All checks passed")
else:
    for check in result.failed_checks:
        print(f"Failed: {check.check_name}")
```

### Serialization

Bundles serialize to JSON for storage:

```python
# To JSON
json_str = bundle.to_json()

# From JSON
loaded = RuntimeReplayBundle.from_json(json_str)

# Roundtrip preserves integrity
assert verify_replay_bundle_integrity(loaded).passed
```

## Test Coverage

44 tests in `tests/cam/test_runtime_provenance_replay.py`:

- `TestProvenanceBundleCreated` (5 tests): Bundle creation
- `TestValidationSignaturePreserved` (4 tests): Validation lineage
- `TestAdmissionDecisionPreserved` (3 tests): Admission lineage
- `TestArtifactHashStable` (3 tests): Artifact hashing
- `TestTraceOrderDeterministic` (3 tests): Event ordering
- `TestReplayBundleIntegrity` (3 tests): Integrity verification
- `TestTamperedArtifactHashRejected` (2 tests): Tampering detection
- `TestTamperedValidationSignatureRejected` (2 tests): Signature tampering
- `TestReplayDoesNotReauthorize` (2 tests): Verify-only behavior
- `TestReplayDoesNotMutateTopology` (2 tests): Immutability
- `TestStableJsonHashingConsistent` (4 tests): Deterministic hashing
- `TestReplayResultReportsConstraints` (2 tests): Constraint reporting
- `TestBundleSerialization` (3 tests): JSON roundtrip
- `TestRecordingErrors` (2 tests): Error handling
- `TestBundleSummary` (2 tests): Summary generation
- `TestStrictMode` (2 tests): Strict mode behavior

## Integration Points

### Upstream (MRP-5M)

Receives `ExecutionAdmissionResult` from admission controller:

```python
from app.cam.runtime_admission import ExecutionAdmissionController

controller = ExecutionAdmissionController()
admission_result = controller.evaluate(request)

# Pass to provenance recording
bundle = recorder.record(
    admission_result=admission_result,
    ...
)
```

### Upstream (MRP-5I/5J)

Receives `CertifiedTopology` from validation:

```python
from app.cam.topology_validation import TopologyValidator

validator = TopologyValidator()
certified = validator.certify(topology_dict)

# Pass to provenance recording
bundle = recorder.record(
    certified_topology=certified,
    ...
)
```

### RuntimeArtifact Protocol

Artifacts must implement:

```python
class RuntimeArtifact(Protocol):
    @property
    def artifact_id(self) -> str: ...
    
    @property
    def artifact_type(self) -> str: ...
    
    @property
    def content_bytes(self) -> bytes: ...
    
    @property
    def metadata(self) -> Dict[str, Any]: ...
    
    def to_provenance_dict(self) -> Dict[str, Any]: ...
```

## Usage Examples

### Record and Verify

```python
from app.cam.runtime_provenance import (
    RuntimeProvenanceRecorder,
    RuntimeReplayEngine,
)

# Record
recorder = RuntimeProvenanceRecorder()
bundle = recorder.record(
    certified_topology=certified,
    admission_result=admission_result,
    artifact=artifact,
    translator_id="step_acoustic",
    adapter_id="mock",
)

# Store
json_str = bundle.to_json()
save_to_storage(json_str)

# Later: Load and verify
loaded_json = load_from_storage()
loaded_bundle = RuntimeReplayBundle.from_json(loaded_json)

engine = RuntimeReplayEngine()
result = engine.verify(loaded_bundle)
assert result.passed
```

### Get Bundle Summary

```python
from app.cam.runtime_provenance import get_bundle_summary

summary = get_bundle_summary(bundle)
print(summary)
# Output:
# RuntimeReplayBundle Summary:
#   Run ID: abc123-...
#   Created: 2026-05-20T10:30:00Z
#   Artifact: step_acoustic (artifact-001)
#   Validation: PASSED (tier: PROTOTYPE)
#   Admission: ADMITTED
#   Trace Events: 5
#   Replayable: True
```

### Strict Mode

```python
from app.cam.runtime_provenance import verify_bundle, IntegrityError

# Returns result normally
result = verify_bundle(bundle, strict=False)

# Raises on failure
try:
    result = verify_bundle(bundle, strict=True)
except IntegrityError as e:
    print(f"Integrity violation: {e}")
```

## Files

| File | Purpose |
|------|---------|
| `app/cam/runtime_provenance/__init__.py` | Package exports |
| `app/cam/runtime_provenance/contracts.py` | Data contracts |
| `app/cam/runtime_provenance/exceptions.py` | Exception types |
| `app/cam/runtime_provenance/integrity.py` | Integrity verification |
| `app/cam/runtime_provenance/recorder.py` | Provenance recorder |
| `app/cam/runtime_provenance/replay.py` | Replay engine |
| `app/cam/runtime_provenance/serialization.py` | Stable JSON utilities |
| `tests/cam/test_runtime_provenance_replay.py` | Test suite (44 tests) |

## Design Decisions

### Verify-Only Replay

The replay engine verifies bundle integrity but does NOT re-execute the pipeline.
Re-execution would require:
- Re-running validation (may have different results)
- Re-running admission (policies may have changed)
- Re-running translation (non-deterministic components)

Verification confirms the recorded chain is internally consistent.

### Deterministic Hashing

All hashes use SHA-256 with stable JSON serialization:
- Sorted keys
- No extra whitespace
- Consistent float formatting
- UTF-8 encoding

This ensures hash reproducibility across sessions.

### Event Trace Ordering

Events are recorded with monotonic sequence numbers and must follow the order:
1. VALIDATION_CERTIFIED
2. ADMISSION_COMPLETED
3. TRANSLATION_COMPLETED (optional)
4. ADAPTER_COMPLETED (optional)
5. ARTIFACT_RECORDED

Out-of-order events indicate tampering or corruption.

## Next Steps

- **Persistent storage**: Add database/filesystem storage backend
- **Query API**: Search bundles by artifact, topology, time range
- **Retention policy**: Auto-expire old bundles
- **Audit reporting**: Generate compliance reports from bundles
