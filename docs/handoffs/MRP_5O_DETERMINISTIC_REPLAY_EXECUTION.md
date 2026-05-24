# MRP-5O: Deterministic Replay Execution & Artifact Regression Harness

**Sprint**: MRP-5O  
**Status**: PROTOTYPE COMPLETE  
**Date**: 2026-05-21

## Executive Summary

MRP-5O extends the provenance infrastructure from MRP-5N into deterministic replay
execution. Given a RuntimeReplayBundle, the harness can reproduce artifacts using
mock adapter execution and compare against recorded baselines for regression detection.

**Key principle**: Replay is evidentiary reproduction, not execution authority.

## Replay Boundary Model

```
RuntimeReplayBundle
    ↓
ReplayExecutionHarness.execute()
    ↓
Integrity verification
    ↓
Admission status check
    ↓
Adapter eligibility check
    ↓
Deterministic mock replay
    ↓
ReproducedArtifact
    ↓
ArtifactRegressionComparator
    ↓
ArtifactRegressionReport
```

## Authority Separation

Replay may:
- Verify bundle integrity
- Reproduce artifacts from recorded topology
- Compare hashes for regression detection
- Report divergence

Replay may NOT:
- Re-authorize execution
- Reinterpret topology
- Mutate certification
- Infer missing metadata
- Silently repair divergence

## Mock Execution Scope

MRP-5O supports **mock adapter only**:

```python
SUPPORTED_ADAPTERS = {"mock"}
```

Bundles recorded with real adapters (OCC, CadQuery, build123d) return:
```
ReplayExecutionStatus.NON_REPLAYABLE
```

This prevents false replay confidence from mock substitution.

## Regression Classification

### ReplayExecutionStatus

| Status | Description |
|--------|-------------|
| `REPLAYED` | Mock replay completed successfully |
| `NON_REPLAYABLE` | Bundle cannot be replayed (adapter mismatch, marked non-replayable) |
| `INVALID_BUNDLE` | Bundle integrity check failed |
| `REJECTED_ADMISSION` | Bundle admission was not ADMITTED |

### RegressionStatus

| Status | Description |
|--------|-------------|
| `MATCH` | Reproduced artifact matches baseline |
| `DIVERGED` | Artifacts differ (hash or metadata) |
| `BASELINE_MISSING` | No baseline hash to compare against |
| `INVALID` | Comparison cannot be performed |

### DivergenceSeverity

| Severity | Description |
|----------|-------------|
| `NONE` | No divergence detected |
| `WARNING` | Minor divergence (e.g., size mismatch with hash match) |
| `BLOCKING` | Critical divergence (hash mismatch) |

## Determinism Guarantees

Mock replay is deterministic:

```python
# Same topology hash produces same artifact hash
bundle1 = build_minimal_replay_bundle(request_id="test-001")
bundle2 = build_minimal_replay_bundle(request_id="test-001")

result1 = execute_replay(bundle1)
result2 = execute_replay(bundle2)

assert result1.reproduced_hash == result2.reproduced_hash  # PASSES
```

Determinism is achieved through:
- Stable JSON serialization (sorted keys, no whitespace variance)
- Fixed timestamp in STEP content (`2026-01-01T00:00:00`)
- Content derived from topology hash, not timestamp or random values

## Usage Examples

### Basic Replay and Comparison

```python
from app.cam.runtime_provenance import (
    build_minimal_replay_bundle,
    execute_replay,
    compare_regression,
    ReplayExecutionStatus,
    RegressionStatus,
)

# Create bundle
bundle = build_minimal_replay_bundle(adapter_id="mock")

# Execute replay
result = execute_replay(bundle)

if result.status == ReplayExecutionStatus.REPLAYED:
    # Compare against baseline
    report = compare_regression(bundle, result)
    
    if report.status == RegressionStatus.MATCH:
        print("Regression check passed")
    else:
        print(f"Divergence detected: {report.divergences}")
```

### Full Harness Usage

```python
from app.cam.runtime_provenance import (
    ReplayExecutionHarness,
    ArtifactRegressionComparator,
)

harness = ReplayExecutionHarness()
comparator = ArtifactRegressionComparator()

result = harness.execute(bundle)

if result.status == ReplayExecutionStatus.REPLAYED:
    report = comparator.compare(bundle, result)
    print(report.to_dict())
```

## Test Matrix

39 tests in `tests/cam/test_runtime_replay_execution.py`:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestAdmittedBundleReplays | 5 | Happy path replay |
| TestRejectedAdmissionDoesNotReplay | 3 | Authority boundary |
| TestInvalidBundleRejected | 2 | Integrity checks |
| TestMissingInputsNonReplayable | 3 | Missing/mismatched inputs |
| TestArtifactHashMatch | 2 | Regression success |
| TestArtifactHashMismatchReported | 3 | Divergence detection |
| TestReplayDoesNotReauthorize | 2 | Authority separation |
| TestReplayDoesNotMutateBundle | 3 | Immutability |
| TestMockAdapterDeterministic | 3 | Reproducibility |
| TestRegressionReportStable | 2 | Deterministic output |
| TestTamperedBundleRejected | 2 | Integrity enforcement |
| TestMetadataDivergenceDetected | 2 | Auditability |
| TestConvenienceFunctions | 2 | API surface |
| TestBaselineMissing | 2 | Edge cases |
| TestReproducedArtifact | 3 | Artifact dataclass |

## Known Limitations

1. **Mock adapter only**: Real CAD kernel replay not supported
2. **No topology storage**: Bundle stores hash, not full topology
3. **No external baseline corpus**: Comparison uses bundle's recorded hash
4. **No database persistence**: Bundles exist in memory/JSON only
5. **No CI blocking**: Divergence is reported, not enforced

## Future Production Replay Path

To support production CAD replay:

1. **Store full topology**: Add `source_topology` field to RuntimeArtifactProvenance
2. **Adapter registry**: Register replay-capable adapters
3. **Deterministic kernels**: Ensure OCC/CadQuery produce reproducible output
4. **Baseline corpus**: External storage for known-good artifact hashes
5. **CI integration**: Block merges on regression failures

## Files

| File | Purpose |
|------|---------|
| `app/cam/runtime_provenance/classification.py` | Status/severity enums |
| `app/cam/runtime_provenance/execution.py` | ReplayExecutionHarness |
| `app/cam/runtime_provenance/regression.py` | ArtifactRegressionComparator |
| `app/cam/runtime_provenance/fixtures.py` | Bundle builders |
| `tests/cam/test_runtime_replay_execution.py` | Test suite (39 tests) |

## Integration with MRP-5M/5N

MRP-5O consumes outputs from:

- **MRP-5M (Runtime Admission)**: Uses admission decision in bundle
- **MRP-5N (Runtime Provenance)**: Consumes RuntimeReplayBundle

The complete chain:
```
TopologyValidation (5I/5J) → CertifiedTopology
RuntimeAdmission (5M) → ExecutionAdmissionResult
RuntimeProvenance (5N) → RuntimeReplayBundle
ReplayExecution (5O) → ArtifactRegressionReport
```

## Definition of Done

Runtime artifacts now support:
- Deterministic replay execution inside governed prototype pipeline
- Regression comparison without re-authorization
- Divergence reporting without repair

Not done:
- Production CAD replay
- Real kernel execution
- Archive persistence
- Adaptive replay
- Distributed replay
- CI blocking regression enforcement
