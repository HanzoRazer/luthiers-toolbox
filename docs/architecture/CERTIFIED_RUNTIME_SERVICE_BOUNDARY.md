# Certified Runtime Service Boundary

**Sprint**: MRP-5Q/R  
**Status**: PROTOTYPE  
**Date**: 2026-05-21

## Overview

`CertifiedRuntimeService` is the safe internal developer entrypoint for the governed runtime spine. It orchestrates topology certification, admission control, adapter execution, and provenance recording into a single coherent operation.

## WARNING

This is an **INTERNAL** developer surface.

It is **NOT**:
- A public HTTP API
- Machine authorization
- Production-ready CAD execution
- A replacement for proper topology validation

## Minimal Usage Example

```python
from app.cam.topology_validation import certify_topology
from app.cam.runtime_service import (
    CertifiedRuntimeService,
    CertifiedRuntimeRequest,
)

# 1. You must certify topology first
topology_dict = {
    "request_id": "my-request",
    "tier": "PROTOTYPE",
    "shells": [
        {
            "shell_id": "body_001",
            "is_closed": True,
            "is_manifold": True,
        }
    ],
}
certified = certify_topology(topology_dict)

# 2. Create a service request
request = CertifiedRuntimeRequest(
    certified_topology=certified,
    adapter_id="mock",  # Only "mock" is available
)

# 3. Execute the service
service = CertifiedRuntimeService()
result = service.execute(request)

# 4. Check result
if result.success:
    print(f"Artifact ID: {result.artifact_id}")
    print(f"Artifact Hash: {result.artifact_hash}")
    print(f"Replay Bundle ID: {result.replay_bundle_id}")
else:
    print(f"Failed: {result.status.value}")
    print(f"Error: {result.error_message}")
```

## Forbidden Usage Examples

### DO NOT pass raw topology dict

```python
# WRONG - will raise TypeError
request = CertifiedRuntimeRequest(
    certified_topology={"request_id": "...", "shells": [...]},  # Raw dict
)
```

### DO NOT bypass certification

```python
# WRONG - admission will reject
fake_certified = SomeFakeWrapper(topology_dict)
request = CertifiedRuntimeRequest(certified_topology=fake_certified)
```

### DO NOT use unavailable adapters

```python
# WRONG - will fail with INVALID_REQUEST
request = CertifiedRuntimeRequest(
    certified_topology=certified,
    adapter_id="cadquery",  # Not available yet
)
```

## Gate Ordering Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  CertifiedRuntimeRequest                │
│  - certified_topology (must be CertifiedTopology)       │
│  - adapter_id (must be available)                       │
│  - runtime_tier, execution_mode                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Gate 1: Request Validation                 │
│  - Is certified_topology a CertifiedTopology?           │
│  - Is adapter_id available in registry?                 │
│  FAIL → INVALID_REQUEST                                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Gate 2: Admission Control                  │
│  - NoUncertifiedExecutionPolicy                         │
│  - ValidationRequiredPolicy                             │
│  - SignatureIntegrityPolicy                             │
│  - PrototypeRuntimeOnlyPolicy                           │
│  - DeterministicOnlyPolicy                              │
│  - AdapterAvailablePolicy                               │
│  FAIL → ADMISSION_REJECTED                              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Gate 3: Adapter Execution                  │
│  - MockRuntimeAdapter.execute()                         │
│  - Produces deterministic STEP-like content             │
│  FAIL → ADAPTER_FAILED                                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Gate 4: Provenance Recording               │
│  - Build validation lineage                             │
│  - Build admission lineage                              │
│  - Build artifact lineage                               │
│  - Create RuntimeReplayBundle                           │
│  FAIL → PROVENANCE_FAILED                               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                CertifiedRuntimeResult                   │
│  - status: SUCCESS                                      │
│  - artifact_id, artifact_hash, artifact_size_bytes      │
│  - replay_bundle (RuntimeReplayBundle)                  │
│  - execution_time_ms                                    │
└─────────────────────────────────────────────────────────┘
```

## Available Adapters

| Adapter ID | Status | Deterministic | Notes |
|------------|--------|---------------|-------|
| `mock` | AVAILABLE | Yes | Produces deterministic STEP-like content |
| `cadquery` | PLANNED | Unknown | Not implemented |
| `build123d` | PLANNED | Unknown | Not implemented |
| `occ` | PLANNED | Unknown | Not implemented |

## Service Execution Status Codes

| Status | Meaning |
|--------|---------|
| `SUCCESS` | Execution completed, artifact and bundle created |
| `INVALID_REQUEST` | Request validation failed |
| `ADMISSION_REJECTED` | Admission control rejected the request |
| `TRANSLATION_FAILED` | Translator failed (not used with mock) |
| `ADAPTER_FAILED` | Adapter execution failed |
| `PROVENANCE_FAILED` | Failed to record provenance |

## Replay Bundle Usage

The service produces a `RuntimeReplayBundle` that can be:

1. **Serialized** for storage:
   ```python
   bundle_json = result.replay_bundle.to_json()
   ```

2. **Verified** for integrity:
   ```python
   from app.cam.runtime_provenance import verify_replay_bundle_integrity
   integrity = verify_replay_bundle_integrity(result.replay_bundle)
   assert integrity.passed
   ```

3. **Replayed** for regression testing:
   ```python
   from app.cam.runtime_provenance import ReplayExecutionHarness
   harness = ReplayExecutionHarness()
   replay_result = harness.execute(result.replay_bundle)
   ```

## Module Boundaries

```
app/cam/runtime_service/     <- Orchestrates (this service)
app/cam/runtime_admission/   <- Admits
app/cam/runtime_provenance/  <- Records/replays
app/cam/topology_validation/ <- Certifies
app/cam/topology_builder/    <- Constructs
```

The service ONLY orchestrates. It does not make admission decisions, record lineage, or certify topology. Those responsibilities belong to their respective modules.
