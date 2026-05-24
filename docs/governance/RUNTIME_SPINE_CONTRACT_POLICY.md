# Runtime Spine Contract Policy

**Sprint**: MRP-5T  
**Status**: FROZEN  
**Effective Date**: 2026-05-21

## Overview

This document defines the governance policy for runtime spine contracts. The runtime spine provides bounded executable reconstruction within governed semantic infrastructure.

## Contract Classifications

### PUBLIC_GOVERNED

Contracts that are part of the stable public API. These contracts:

- **MUST NOT** have breaking changes without major version increment
- **MUST** maintain deterministic behavior
- **MUST** be replay-safe (produce identical results on replay)
- **MUST** be documented with clear semantics

Breaking changes to PUBLIC_GOVERNED contracts require:
1. Deprecation notice in prior minor version
2. Migration guide in handoff documentation
3. Major version increment
4. Governance review

Current PUBLIC_GOVERNED contracts:
- `CertifiedTopology` — Immutable wrapper for validated topology
- `TopologyValidator` — Validates and certifies topology
- `ExecutionAdmissionController` — Gate for runtime execution
- `ExecutionAdmissionRequest` — Request for admission control
- `AdmissionDecision` — Decision from admission control
- `RuntimeReplayBundle` — Serializable provenance package
- `ReplayExecutionHarness` — Deterministic replay execution
- `ArtifactRegressionComparator` — Baseline comparison
- `CertifiedRuntimeService` — Internal orchestration boundary
- `CertifiedRuntimeRequest` — Request for runtime service
- `CertifiedRuntimeResult` — Result from runtime service

### DEVELOPER_EXPERIMENTAL

Contracts exposed for developer use but not yet stable. These contracts:

- **MAY** have breaking changes with minor version increment
- **SHOULD** maintain deterministic behavior when feasible
- **MUST** be documented with experimental status notice

Current DEVELOPER_EXPERIMENTAL contracts:
- `certify_topology` — Convenience function
- `verify_replay_bundle_integrity` — Bundle integrity check
- `execute_certified_runtime` — Convenience function
- `MockRuntimeAdapter` — Deterministic mock adapter

### INTERNAL_ONLY

Contracts used internally that are not part of any public API. These contracts:

- **MAY** change without notice
- **MUST NOT** be imported directly by external code
- **SHOULD** be prefixed with underscore when possible

Current INTERNAL_ONLY contracts:
- `AdmissionPolicy` — Base class for policies
- `AdapterRegistry` — Internal adapter registry

## Versioning Policy

### Version Format

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Breaking changes to PUBLIC_GOVERNED contracts
- **MINOR**: New features, DEVELOPER_EXPERIMENTAL changes, deprecations
- **PATCH**: Bug fixes that don't affect contract behavior

### Current Version

```
Runtime Spine Version: 0.1.0
Replay Bundle Schema: 1
Manifest Schema: 1
```

### Compatibility Rules

1. **Same MAJOR version**: Compatible if current MINOR >= required MINOR
2. **Different MAJOR version**: Always incompatible
3. **Schema versions**: Must match exactly for serialization

## Stability Requirements

### Determinism

All PUBLIC_GOVERNED contracts MUST be deterministic:
- Same input produces same output
- No dependency on system time, random numbers, or external state
- Execution order does not affect results

### Replay Safety

All PUBLIC_GOVERNED contracts MUST be replay-safe:
- Replay execution produces identical artifacts
- No side effects on replay
- Provenance is preserved through replay

### Gate Ordering

The runtime spine enforces strict gate ordering:

```
1. Certification (CertifiedTopology)
2. Admission (ExecutionAdmissionController)
3. Execution (CertifiedRuntimeService)
4. Provenance (RuntimeReplayBundle)
5. Replay (ReplayExecutionHarness)
```

No gate may be skipped or reordered.

## Export Stability

### Module Exports

Each runtime spine module has a stable `__init__.py` that exports:
- All PUBLIC_GOVERNED contracts
- All DEVELOPER_EXPERIMENTAL APIs
- No INTERNAL_ONLY contracts

### Import Paths

Stable import paths:
```python
from app.cam.topology_validation import CertifiedTopology, certify_topology
from app.cam.runtime_admission import ExecutionAdmissionController, AdmissionDecision
from app.cam.runtime_provenance import RuntimeReplayBundle, ReplayExecutionHarness
from app.cam.runtime_service import CertifiedRuntimeService, execute_certified_runtime
from app.cam.runtime_manifest import build_runtime_spine_manifest
```

## Manifest Generation

The runtime spine manifest documents all contracts:

```bash
python scripts/runtime_provenance/generate_runtime_manifest.py --summary
```

Output includes:
- Version information
- Contract counts by classification
- Compatibility status
- Deprecation warnings
- Stability warnings

## Governance Verification

### Audit Script

```bash
python scripts/runtime_provenance/audit_runtime_service_boundary.py --verbose
```

Verifies:
- Package imports succeed
- Certification gate rejects raw topology
- Admission gate is invoked
- Replay boundary works
- Determinism is maintained
- Export surface is stable

### Test Coverage

Runtime spine tests:
- `test_runtime_spine_integration.py` — 20 tests (MRP-5P)
- `test_certified_runtime_service_integration.py` — 29 tests (MRP-5Q/R)
- `test_runtime_service_governance.py` — 36 tests (MRP-5S)
- `test_runtime_spine_contracts.py` — contract/manifest tests (MRP-5T)

## Known Limitations

Current prototype limitations (documented, not blocking):

1. **Mock adapter only** — Real CAD kernel adapters not implemented
2. **No HTTP API** — Service is internal developer surface only
3. **No persistence** — Bundles exist in memory/JSON only
4. **No async** — Synchronous execution only
5. **No CI enforcement** — Governance checks are advisory

## Policy Changes

Changes to this policy require:
1. Governance review
2. Documentation in sprint handoff
3. Version increment appropriate to change scope

## References

- MRP-5M: Runtime Admission Control
- MRP-5N: Runtime Provenance & Replay Foundation
- MRP-5O: Replay Classification & Artifact Regression
- MRP-5P: Runtime Spine Integration Audit
- MRP-5Q/R: CertifiedRuntimeService Integration
- MRP-5S: Runtime Service Consolidation
- MRP-5T: Runtime Spine Contract Freeze
