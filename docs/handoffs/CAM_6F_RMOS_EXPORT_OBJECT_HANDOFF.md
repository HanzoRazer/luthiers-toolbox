# CAM Dev Order 6F — RMOS Export Object Artifact Handoff

**Date:** 2026-05-11  
**Author:** Claude (CAM Dev Order 6F)  
**Status:** COMPLETE

---

## Summary

Added optional RMOS-compatible artifact persistence for governed Export Objects and lifecycle reports. Persistence uses content-addressed storage with lightweight provenance IDs.

**Key outcome:** 6F establishes RMOS-compatible artifact persistence, not full RMOS run orchestration.

---

## Core Architectural Rule

```
RMOS stores governed artifacts.
RMOS does not make them machine-ready.
```

An RMOS artifact is provenance, not execution approval.

---

## Design Decision: Option B

6F uses **content-addressed attachment storage only**.

It does NOT create full RMOS RunArtifact / RunStoreV2 entries.

The `run_id` returned (`RUN-EXPORT-{uuid}`) is a lightweight export provenance ID, not a full RMOS run lifecycle record.

**Reason:** 6F scope is artifact persistence only, not RMOS workflow integration. Full RMOS run lifecycle integration should be a later dev order after export object persistence is proven.

---

## Scope

### In Scope (Completed)

- RMOS export artifact adapter module
- `persist_to_rmos` request flag (default: false)
- Lightweight provenance ID generation
- Export object JSON persistence
- Lifecycle report JSON persistence
- RMOS response block with artifact references
- 23 unit/integration tests

### Out of Scope (Per 6F Guardrails)

- No RunStoreV2 lifecycle coupling
- No job lifecycle
- No machine execution state
- No artifact promotion
- No DXF/G-code persistence
- No translator execution
- No postprocessor execution

---

## Deliverables

| Deliverable | Location | Purpose |
|-------------|----------|---------|
| export_rmos_artifacts.py | app/cam/ | Artifact persistence adapter |
| export_lifecycle_orchestrator.py | app/cam/ | Updated with persist_to_rmos flag |
| test_export_lifecycle_rmos.py | tests/cam/ | 23 test cases |
| CAM_6F_RMOS_EXPORT_OBJECT_HANDOFF.md | docs/handoffs/ | This document |

---

## API Changes

### Extended Request

```json
{
  "preview_request": { "..." },
  "machine_profile": { "..." },
  "translator_profile": { "..." },
  "persist_to_rmos": true
}
```

If `persist_to_rmos` is omitted or false, no persistence occurs.

### Extended Response

```json
{
  "lifecycle_gate": "green",
  "export_ready": true,
  "...other fields...",
  "rmos": {
    "persisted": true,
    "run_id": "RUN-EXPORT-abc123def456...",
    "artifacts": [
      {
        "kind": "export_lifecycle_report_json",
        "sha256": "...",
        "bytes": 1234
      },
      {
        "kind": "export_object_json",
        "sha256": "...",
        "bytes": 5678
      }
    ]
  }
}
```

If not persisted:

```json
{
  "rmos": {
    "persisted": false,
    "run_id": null,
    "artifacts": []
  }
}
```

---

## Artifact Types

| Kind | Description |
|------|-------------|
| `export_object_json` | Serialized ExportObject |
| `export_lifecycle_report_json` | Serialized lifecycle validation report |

---

## Persistence Logic

### Default Behavior

```
persist_to_rmos = false (or omitted)
→ No artifacts created
→ rmos.persisted = false
```

### With Persistence

```
persist_to_rmos = true
→ Generate RUN-EXPORT-{uuid}
→ Persist lifecycle report (always)
→ Persist export object (if created)
→ Return artifact references
```

### RED Lifecycle Handling

```
lifecycle_gate = "red"
persist_to_rmos = true
→ Persist lifecycle report only
→ Do NOT persist export object (not created)
```

This documents the failure for audit purposes without persisting invalid objects.

---

## Storage Implementation

Uses existing RMOS content-addressed attachment helpers:

```python
from app.rmos.runs_v2.attachments import put_json_attachment

attachment, path, sha256 = put_json_attachment(
    obj=export_object_dict,
    kind="export_object_json",
    filename=f"export_object_{run_id}.json",
)
```

Content-addressed storage provides:
- SHA256-based deduplication
- Immutable artifacts
- Hash verification

---

## What Is Persisted

| Artifact | Content |
|----------|---------|
| export_object_json | Full ExportObject schema (geometry, toolpaths, intent, etc.) |
| export_lifecycle_report_json | Lifecycle gate, compatibility results, warnings, metadata |

---

## What Is NOT Persisted

- DXF files
- G-code
- Machine output
- Postprocessor output
- Translator execution results
- Full RMOS run lifecycle entries

These are explicitly excluded per 6F guardrails.

---

## Safety Verified by Tests

- `machine_output_generated: false` — always
- `translator_output_generated: false` — always
- `machine_ready: false` — always
- No G-code tokens in persisted artifacts
- No DXF section markers in persisted artifacts
- RED lifecycle persists report only

---

## Run ID Convention

```
RUN-EXPORT-{uuid4_hex}
```

Example: `RUN-EXPORT-a1b2c3d4e5f6789012345678901234ab`

This is a **lightweight provenance ID** for artifact tracking, NOT a full RMOS run lifecycle record.

---

## Why Not Full RMOS Integration?

6F proves:
1. Export objects can be serialized and persisted
2. Lifecycle reports can be persisted for audit
3. Content-addressed storage works for CAM artifacts

Full RMOS run lifecycle integration (job queuing, state machines, lineage graphs) is a larger scope that should be deferred until basic persistence is proven.

---

## Recommended Next Steps

### 6G: Full RMOS Run Integration

Wire Export Objects to RunStoreV2:
1. Create actual RMOS run entries
2. Link artifacts to run IDs
3. Enable lineage tracking
4. Add run query capabilities

### 6H: DXF Translator Execution

Build actual DXF output:
1. Export Object → DXF primitives
2. Connect to dxf_compat infrastructure
3. Persist DXF as governed artifact

### 6I: Postprocessor Execution

Build G-code output:
1. Export Object → G-code
2. Machine-specific postprocessing
3. Persist G-code as governed artifact

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| CAM_GOVERNED_EXPORT_ARCHITECTURE.md | 6A architecture |
| CAM_6B_EXPORT_OBJECT_PROTOTYPE_HANDOFF.md | Export object prototype |
| CAM_6C_POSTPROCESSOR_BOUNDARY_HANDOFF.md | Postprocessor boundary |
| CAM_6D_DXF_TRANSLATOR_ALIGNMENT_HANDOFF.md | DXF translator boundary |
| CAM_6E_EXPORT_LIFECYCLE_HANDOFF.md | Lifecycle orchestration |

---

## Test Summary

| Category | Tests |
|----------|-------|
| Run ID Generation | 3 |
| Default No Persistence | 3 |
| RMOS Persistence | 6 |
| RED Lifecycle | 2 |
| No Machine Output | 3 |
| Artifact Content Safety | 3 |
| Endpoint | 3 |
| **Total** | **23** |

---

*6F RMOS artifact integration complete: 2026-05-11*
