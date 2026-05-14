# CAM Dev Order 7F: Translation Artifact Provenance Handoff

**Status**: Implementation complete, pending tests and commit
**Date**: 2026-05-14
**Prerequisites**: 7D (translation artifact contracts), 7E (authorization gate)

## Summary

7F adds immutable governance lineage and provenance semantics to Translation Artifacts. Provenance represents governance context at evaluation time, NOT artifact revision history.

## Core Principle

**Governance ancestry ≠ artifact revision control**

Translation Artifacts become governed lineage nodes, not anonymous transient validation payloads.

## 7F Invariants

All invariants are model-enforced via Pydantic validators:

1. `immutable`: always `true`
2. `execution_authorized`: always `false`
3. `machine_output_present`: always `false`

Attempting to create provenance violating these invariants raises `ValueError`.

## Key Distinction

Same artifact + different governance context = different provenance.

Provenance is **event-oriented**, not artifact-identity-oriented.

## Files Created

### services/api/app/cam/translation_artifact_provenance.py

Provenance module with:
- `TranslationArtifactProvenanceSummary` — lightweight summary for attachment
- `TranslationArtifactProvenance` — full provenance model with 7F invariants
- `PROVENANCE_INDEX` — in-memory provenance registry
- `compute_deterministic_lineage_hash()` — deterministic hashing of governance ancestry
- `build_translation_artifact_provenance()` — provenance builder
- Index operations: `get_provenance()`, `get_provenance_by_artifact()`, `list_provenances()`, etc.
- Optional RMOS persistence: `persist_provenance_to_rmos()`

### services/api/app/routers/cam/translation_provenance_router.py

Introspection endpoints:
- `GET /api/cam/translation-provenance` — list all provenances
- `GET /api/cam/translation-provenance/{provenance_id}` — get by ID
- `GET /api/cam/translation-provenance/by-artifact/{artifact_id}` — get by artifact
- `GET /api/cam/translation-provenance/by-lineage-hash/{hash}` — get by hash
- `GET /api/cam/translation-provenance/summaries` — list summaries

### services/api/tests/cam/test_translation_artifact_provenance.py

Test coverage for:
- Deterministic lineage hashing
- Provenance model invariants
- Provenance builder
- Index operations
- Endpoint functionality
- Safety assertions

## Files Modified

### services/api/app/cam/translation_artifact.py

- Added `provenance_summary` optional field to `TranslationArtifactSummary`

### services/api/app/router_registry/manifests/cam_manifest.py

- Registered `translation_provenance_router`

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│               Translation Artifact Provenance Flow                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TranslationArtifact ────┐                                          │
│  + lifecycle_report      │                                          │
│  + audit_ledger          │                                          │
│  + promotion_evidence    │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────┐                            │
│  │  build_translation_artifact_provenance()                         │
│  │    1. Extract governance hashes                                  │
│  │    2. Compute component hashes                                   │
│  │    3. Compute deterministic lineage hash                         │
│  │    4. Create immutable provenance                                │
│  │    5. Register in PROVENANCE_INDEX                               │
│  └─────────────────────────────────────┘                            │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────┐                            │
│  │  TranslationArtifactProvenance                                   │
│  │    - provenance_id                                               │
│  │    - artifact_id                                                 │
│  │    - source_export_object_hash                                   │
│  │    - parent_audit_hashes                                         │
│  │    - parent_promotion_evidence_hashes                            │
│  │    - translator_capability_hash                                  │
│  │    - policy_snapshot_hash                                        │
│  │    - lifecycle_snapshot_hash                                     │
│  │    - deterministic_lineage_hash                                  │
│  │    - immutable: true              ◄── 7F invariant              │
│  │    - execution_authorized: false  ◄── 7F invariant              │
│  │    - machine_output_present: false ◄── 7F invariant             │
│  └─────────────────────────────────────┘                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Deterministic Lineage Hashing

The lineage hash is computed from:

```python
lineage_input = {
    "source_export_object_hash": "...",
    "parent_audit_hashes": ["..."],  # sorted
    "parent_promotion_evidence_hashes": ["..."],  # sorted
    "translator_capability_hash": "...",
    "policy_snapshot_hash": "...",
    "lifecycle_snapshot_hash": "...",
}
```

**Key property**: Same governance ancestry → same lineage hash.

**Excluded from hash**:
- Timestamps
- UUIDs
- RMOS attachment IDs
- Transient metadata

## Provenance Storage

7F uses an in-memory provenance index:

```python
PROVENANCE_INDEX: Dict[str, TranslationArtifactProvenance]
```

Optional RMOS persistence is supplemental. Introspection endpoints do not require RMOS.

Provenance objects are immutable snapshots — no dynamic regeneration.

## Parent Hashes

Parent hashes come from the **current governance cycle only**:

- `parent_audit_hashes` — from lifecycle audit ledger
- `parent_promotion_evidence_hashes` — from promotion evidence

7F does NOT introduce artifact version chains or artifact DAGs. That is intentionally deferred.

## Endpoints

```
GET /api/cam/translation-provenance
```
Returns all registered provenances with pagination.

```
GET /api/cam/translation-provenance/{provenance_id}
```
Returns single provenance by ID.

```
GET /api/cam/translation-provenance/by-artifact/{artifact_id}
```
Returns all provenances for an artifact (may be multiple).

```
GET /api/cam/translation-provenance/by-lineage-hash/{hash}
```
Returns provenance matching the deterministic lineage hash.

## Safety Assertions

All provenance code guarantees:
1. No DXF serialization tokens in output
2. No G-code tokens in output
3. No executable payloads
4. No machine output
5. `immutable` always true
6. `execution_authorized` always false
7. `machine_output_present` always false

## What 7F Does NOT Do

- NO artifact serialization
- NO DXF/SVG/G-code generation
- NO translator execution
- NO postprocessor execution
- NO machine output
- NO execution queues
- NO approval workflows
- NO mutable artifact editing
- NO artifact version chains
- NO artifact DAG/revision graph

## Usage Example

```python
from app.cam.translation_artifact_provenance import (
    build_translation_artifact_provenance,
    get_provenance_by_artifact,
)

# Build provenance from artifact + governance context
provenance = build_translation_artifact_provenance(
    artifact=artifact,
    lifecycle_report=lifecycle_report_dict,
    audit_ledger=audit_ledger_dict,
    promotion_evidence=evidence_dict,
)

print(f"Lineage hash: {provenance.deterministic_lineage_hash}")
print(f"Immutable: {provenance.immutable}")  # Always True

# Retrieve later
provenances = get_provenance_by_artifact(artifact.artifact_id)
```

## Next Steps

1. Run tests: `pytest tests/cam/test_translation_artifact_provenance.py -v`
2. Run full CAM test suite: `pytest tests/cam/ -v`
3. Commit with message referencing 7F

## Related Dev Orders

- **7B**: Translator capability registry (complete)
- **7C**: Registry-gated validation (complete)
- **7D**: Translation artifact contracts (complete)
- **7E**: Translation artifact authorization gate (complete)
- **7F**: Translation artifact provenance lineage (this document)
- **7G+**: Future execution runtime (not yet planned)

## Stop Condition

Stop after immutable provenance lineage exists. Do NOT proceed into translator execution, DXF generation, G-code generation, lineage mutation, execution approvals, artifact downloads, machine output, or runtime execution chains until provenance architecture review is complete.
