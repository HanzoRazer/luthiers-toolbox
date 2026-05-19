# CAM Dev Order 7E: Translation Artifact Authorization Gate Handoff

**Status**: Implementation complete, pending tests and commit
**Date**: 2026-05-14
**Prerequisites**: 7D (translation artifact contracts)

## Summary

7E adds an authorization evaluation gate for translation artifacts. It determines whether an artifact is **eligible** for future execution WITHOUT authorizing or performing execution.

## Core Principle

**Eligibility ≠ Approval**

7E validates eligibility only. It never authorizes execution and never mutates registry or artifact state.

## 7E Invariants

All invariants are model-enforced via Pydantic validators:

1. `authorized_for_execution`: always `false`
2. `human_approval_required`: always `true`
3. `eligible_for_future_execution`: requires gate != RED

Attempting to create an evaluation violating these invariants raises `ValueError`.

## Files Created

### services/api/app/cam/translation_artifact_authorization.py

Authorization evaluation module with:
- `TranslationArtifactAuthorizationEvaluation` — evaluation result model with 7E invariants
- `TranslationArtifactAuthorizationRequest` — request model (artifact in body)
- `evaluate_translation_artifact_authorization()` — main evaluator function
- `_compare_capability_snapshots()` — snapshot drift detection

### services/api/app/routers/cam/translation_artifact_authorization_router.py

Authorization endpoint:
- `POST /api/cam/translation-artifacts/authorize/validate`

### services/api/tests/cam/test_translation_artifact_authorization.py

Test coverage for:
- Valid artifact authorization
- Unknown translator handling (RED)
- Category/output mismatch (RED)
- 7E invariant enforcement
- Gate logic
- Capability snapshot comparison
- Safety assertions

## Files Modified

### services/api/app/router_registry/manifests/cam_manifest.py

- Registered `translation_artifact_authorization_router`

## Authorization Rules

### GREEN

Artifact is structurally valid:
- Translator exists in registry
- Category/output class match
- No capability drift affecting safety
- No blocking issues

Returns:
```python
authorized_for_execution = False
eligible_for_future_execution = True
human_approval_required = True
```

### YELLOW

Artifact valid but has warnings:
- Translator maturity below "governed"
- Description/notes changed
- Supported operations changed (non-critical)
- Maturity changed

Returns:
```python
authorized_for_execution = False
eligible_for_future_execution = True
human_approval_required = True
```

### RED

Blocking issues present:
- Unknown translator
- Category mismatch
- Output class mismatch
- Artifact has executable_payload_present=true
- Artifact has machine_output_present=true
- Current registry has machine_output_supported=true
- Translator execution disabled

Returns:
```python
authorized_for_execution = False
eligible_for_future_execution = False
human_approval_required = True
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│               Translation Artifact Authorization Flow                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TranslationArtifact ────┐                                          │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────┐                            │
│  │  evaluate_translation_artifact_authorization()                   │
│  │    1. Check 7D invariants                                        │
│  │    2. Verify translator exists                                   │
│  │    3. Check category/output match                                │
│  │    4. Compare capability snapshots                               │
│  │    5. Determine gate                                             │
│  └─────────────────────────────────────┘                            │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────┐                            │
│  │  TranslationArtifactAuthorizationEvaluation                      │
│  │    - gate: green/yellow/red                                      │
│  │    - eligible_for_future_execution                               │
│  │    - authorized_for_execution: false  ◄── 7E invariant          │
│  │    - human_approval_required: true    ◄── 7E invariant          │
│  │    - blocking_issues                                             │
│  │    - warnings                                                    │
│  │    - capability_snapshot (current)                               │
│  └─────────────────────────────────────┘                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Capability Snapshot Comparison

7E compares the artifact's `capability_snapshot` (captured at artifact creation) against the current registry state.

### YELLOW (provenance warning)

- Translator version changed
- Maturity changed
- Description/notes changed
- Supported operations changed (non-critical)

### RED (safety boundary violation)

- `translator_id` no longer exists
- `translator_category` changed
- `output_class` changed
- Current registry has `machine_output_supported=true`
- Execution state inconsistency

## Endpoint

```
POST /api/cam/translation-artifacts/authorize/validate
```

Request body:
```json
{
  "artifact": { ...TranslationArtifact... }
}
```

Response:
```json
{
  "artifact_id": "artifact-abc123",
  "translator_id": "dxf_r12",
  "gate": "green",
  "authorized_for_execution": false,
  "eligible_for_future_execution": true,
  "human_approval_required": true,
  "blocking_issues": [],
  "warnings": [],
  "policy_snapshot": {},
  "capability_snapshot": { ...current capability... },
  "metadata": {
    "evaluation_type": "translation_artifact_authorization",
    "dev_order": "7E",
    "validation_only": true
  }
}
```

## Safety Assertions

All evaluation code guarantees:
1. No DXF serialization tokens in output
2. No G-code tokens in output
3. No executable payloads generated
4. No machine output
5. `authorized_for_execution` always false
6. `human_approval_required` always true

## What 7E Does NOT Do

- NO execution authorization
- NO artifact generation
- NO DXF/SVG/G-code output
- NO machine output
- NO registry mutation
- NO approval without human review

## Test Coverage

Required tests:
- Valid DXF validation artifact → eligible but not authorized
- Unknown translator → RED
- Category mismatch → RED
- Output class mismatch → RED
- Artifact with executable payload → model validator rejects
- machine_output_present → model validator rejects
- human_approval_required always true
- authorized_for_execution always false
- No DXF/G-code tokens in output
- Endpoint works

## Usage Example

```python
from app.cam.translation_artifact_authorization import (
    evaluate_translation_artifact_authorization,
)
from app.cam.translation_artifact import build_validation_translation_artifact

# Create artifact (from 7D)
artifact = build_validation_translation_artifact(export_obj, capability)

# Evaluate authorization eligibility (7E)
evaluation = evaluate_translation_artifact_authorization(artifact)

print(f"Gate: {evaluation.gate}")
print(f"Eligible: {evaluation.eligible_for_future_execution}")
print(f"Authorized: {evaluation.authorized_for_execution}")  # Always False
print(f"Approval Required: {evaluation.human_approval_required}")  # Always True
```

## Next Steps

1. Run tests: `pytest tests/cam/test_translation_artifact_authorization.py -v`
2. Run full CAM test suite: `pytest tests/cam/ -v`
3. Commit with message referencing 7E

## Related Dev Orders

- **7B**: Translator capability registry (complete)
- **7C**: Registry-gated validation (complete)
- **7D**: Translation artifact contracts (complete)
- **7E**: Translation artifact authorization gate (this document)
- **7F+**: Future execution runtime (not yet planned)

## Guardrail

7E validates eligibility only. It never authorizes execution and never mutates registry or artifact state.
