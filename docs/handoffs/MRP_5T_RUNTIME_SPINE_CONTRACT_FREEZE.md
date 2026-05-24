# MRP-5T: Runtime Spine Packaging, Versioning & Contract Freeze

**Sprint**: MRP-5T  
**Status**: COMPLETE  
**Date**: 2026-05-21

## Executive Summary

MRP-5T establishes the contract freeze for the runtime spine. This sprint introduces:

1. **Runtime Manifest Package** — `app/cam/runtime_manifest/`
2. **Contract Versioning** — Semantic versioning for spine contracts
3. **Contract Classification** — PUBLIC_GOVERNED, DEVELOPER_EXPERIMENTAL, INTERNAL_ONLY
4. **Compatibility Enforcement** — Version checking and manifest comparison
5. **Export Stabilization** — Frozen export surfaces for all runtime modules

**Key Achievement**: The runtime spine is now a versioned, classified, and frozen contract surface with tools for compatibility verification.

## Runtime Manifest Package

```
app/cam/runtime_manifest/
    __init__.py         # Package exports
    versioning.py       # Version constants and helpers
    contracts.py        # Contract dataclasses
    manifest.py         # RuntimeSpineManifestBuilder
    compatibility.py    # Comparison and verification
    exceptions.py       # Manifest errors
```

### Version Constants

```python
RUNTIME_SPINE_VERSION = "0.1.0"
REPLAY_BUNDLE_SCHEMA_VERSION = "1"
MANIFEST_SCHEMA_VERSION = "1"
CONTRACT_FREEZE_DATE = "2026-05-21"
CONTRACT_FREEZE_SPRINT = "MRP-5T"
```

### Contract Classifications

| Classification | Breaking Change Policy | Stability Requirement |
|----------------|------------------------|----------------------|
| PUBLIC_GOVERNED | Major version only | Deterministic, replay-safe |
| DEVELOPER_EXPERIMENTAL | Minor version | Should be deterministic |
| INTERNAL_ONLY | Any version | No external guarantees |

## Contract Inventory

### PUBLIC_GOVERNED (11 contracts)

| Contract | Module | Description |
|----------|--------|-------------|
| CertifiedTopology | topology_validation | Immutable validated wrapper |
| TopologyValidator | topology_validation | Certifies topology |
| ExecutionAdmissionController | runtime_admission | Admission gate |
| ExecutionAdmissionRequest | runtime_admission | Admission request |
| AdmissionDecision | runtime_admission | Admission result |
| RuntimeReplayBundle | runtime_provenance | Provenance package |
| ReplayExecutionHarness | runtime_provenance | Replay executor |
| ArtifactRegressionComparator | runtime_provenance | Baseline comparator |
| CertifiedRuntimeService | runtime_service | Orchestration boundary |
| CertifiedRuntimeRequest | runtime_service | Service request |
| CertifiedRuntimeResult | runtime_service | Service result |

### DEVELOPER_EXPERIMENTAL (5 contracts)

| Contract | Module | Description |
|----------|--------|-------------|
| certify_topology | topology_validation | Convenience function |
| verify_replay_bundle_integrity | runtime_provenance | Bundle check |
| execute_certified_runtime | runtime_service | Convenience function |
| MockRuntimeAdapter | runtime_service | Mock adapter |

### INTERNAL_ONLY (2 contracts)

| Contract | Module | Description |
|----------|--------|-------------|
| AdmissionPolicy | runtime_admission | Policy base class |
| AdapterRegistry | runtime_service | Adapter registry |

## Compatibility Verification

### Version Compatibility

```python
from app.cam.runtime_manifest import assert_compatible

# Raises VersionMismatchError if incompatible
assert_compatible(current="0.1.0", required="0.1.0")
```

### Manifest Comparison

```python
from app.cam.runtime_manifest import compare_manifests

report = compare_manifests(old_manifest, new_manifest)
if not report.compatible:
    print(f"Breaking changes: {report.breaking_changes}")
```

### Contract Stability Check

```python
from app.cam.runtime_manifest import check_contract_stability

violations = check_contract_stability(
    contract,
    require_deterministic=True,
    require_replay_safe=True,
)
```

## Manifest Generation

### Generate Full Manifest

```bash
python scripts/runtime_provenance/generate_runtime_manifest.py -o manifest.json
```

### Generate Summary

```bash
python scripts/runtime_provenance/generate_runtime_manifest.py --summary --verbose
```

Output:
```
============================================================
RUNTIME SPINE MANIFEST SUMMARY
Sprint: MRP-5T
============================================================

[Version Info]
    Runtime Spine Version: 0.1.0
    Replay Bundle Schema:  1
    Manifest Schema:       1
    Contract Freeze Date:  2026-05-21
    Manifest Hash:         <16-char hash>

[Contract Counts]
    Total Contracts:       18
    Governed (PUBLIC):     11
    Developer APIs:        5
    Internal:              2

[Compatibility Status]
    Status: STABLE_PROTOTYPE
```

## Test Coverage

| Test File | Tests | Focus |
|-----------|-------|-------|
| test_runtime_spine_contracts.py | 40+ | Contract/manifest tests |

Test categories:
- Versioning helpers
- Contract enums
- Contract entries
- Manifest builder
- JSON serialization
- Contract comparison
- Manifest comparison
- Compatibility assertions
- Stability checks
- Full manifest generation

## Export Surface Audit

### runtime_manifest/__init__.py

| Export | Type | Classification |
|--------|------|----------------|
| ContractClassification | Enum | INTERNAL |
| CompatibilityLevel | Enum | INTERNAL |
| RuntimeContractEntry | Dataclass | DEVELOPER |
| RuntimeVersionInfo | Dataclass | DEVELOPER |
| RuntimeSpineManifest | Dataclass | GOVERNED |
| RuntimeCompatibilityReport | Dataclass | DEVELOPER |
| RUNTIME_SPINE_VERSION | Constant | GOVERNED |
| REPLAY_BUNDLE_SCHEMA_VERSION | Constant | GOVERNED |
| MANIFEST_SCHEMA_VERSION | Constant | GOVERNED |
| CONTRACT_FREEZE_DATE | Constant | GOVERNED |
| CONTRACT_FREEZE_SPRINT | Constant | GOVERNED |
| RuntimeSpineManifestBuilder | Class | DEVELOPER |
| build_runtime_spine_manifest | Function | DEVELOPER |
| manifest_to_json | Function | DEVELOPER |
| manifest_from_json | Function | DEVELOPER |
| compute_manifest_hash | Function | DEVELOPER |
| compare_contracts | Function | DEVELOPER |
| compare_manifests | Function | DEVELOPER |
| assert_compatible | Function | DEVELOPER |
| check_contract_stability | Function | DEVELOPER |

## Known Limitations

1. **Prototype version (0.1.0)**: Not production-ready
2. **No CI enforcement**: Manifest checks are advisory only
3. **No breaking change detection in CI**: Manual verification required
4. **Schema evolution**: No migration tooling for schema changes

## Commit Readiness Recommendation

**READY FOR COMMIT**

Rationale:
- All contracts classified and documented
- Version constants established
- Manifest generation works
- Compatibility checking works
- Tests cover all functionality
- Export surfaces frozen
- Governance policy documented
- No breaking changes to existing code

## Files Created

### MRP-5T New Files

| File | Purpose |
|------|---------|
| app/cam/runtime_manifest/__init__.py | Package exports |
| app/cam/runtime_manifest/versioning.py | Version constants |
| app/cam/runtime_manifest/contracts.py | Contract dataclasses |
| app/cam/runtime_manifest/manifest.py | Manifest builder |
| app/cam/runtime_manifest/compatibility.py | Comparison utilities |
| app/cam/runtime_manifest/exceptions.py | Manifest errors |
| tests/cam/test_runtime_spine_contracts.py | Contract tests |
| scripts/runtime_provenance/generate_runtime_manifest.py | Generation utility |
| docs/governance/RUNTIME_SPINE_CONTRACT_POLICY.md | Policy document |
| docs/handoffs/MRP_5T_RUNTIME_SPINE_CONTRACT_FREEZE.md | This document |

## Definition of Done

Done:
- Runtime manifest package created
- Contract classifications defined
- Version constants established
- Compatibility utilities implemented
- Manifest builder functional
- JSON serialization roundtrips
- Manifest comparison works
- Contract stability checking works
- Full spine manifest generates
- Tests pass
- Governance policy documented
- Handoff completed

Not done:
- CI enforcement of contract changes
- Schema migration tooling
- Production version (1.0.0)
- Breaking change detection automation

## Sprint Lineage

```
MRP-5M: Runtime Admission Control
    |
MRP-5N: Runtime Provenance & Replay Foundation
    |
MRP-5O: Replay Classification & Artifact Regression
    |
MRP-5P: Runtime Spine Integration Audit
    |
MRP-5Q/R: CertifiedRuntimeService Integration
    |
MRP-5S: Runtime Service Consolidation
    |
MRP-5T: Runtime Spine Contract Freeze  <-- YOU ARE HERE
```

## Next Steps

Potential future sprints:
1. **MRP-5U**: CI enforcement for contract changes
2. **MRP-5V**: Schema migration tooling
3. **MRP-5W**: Production readiness (1.0.0)
