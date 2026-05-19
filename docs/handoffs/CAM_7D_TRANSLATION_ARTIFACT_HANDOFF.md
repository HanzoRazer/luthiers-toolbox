# CAM Dev Order 7D: Translation Artifact Model Handoff

**Status**: Implementation complete, pending tests and commit
**Date**: 2026-05-14
**Prerequisites**: 7B (translator capability registry), 7C (registry-gated validation)

## Summary

7D introduces Translation Artifacts — governed metadata contracts that represent what a translator WOULD produce without containing executable content. Artifacts capture lineage, policy state, and classification metadata.

## Core Principle

A Translation Artifact is a governed representation of a future translator result, NOT the execution itself.

## 7D Invariants

All invariants are model-enforced via Pydantic validators:

1. `execution_supported`: always `false`
2. `executable_payload_present`: always `false`
3. `machine_output_present`: always `false`

Attempting to create an artifact violating these invariants raises `ValueError`.

## Files Created

### services/api/app/cam/translation_artifact.py

Translation artifact model with:
- `TranslationArtifactSummary` — lightweight summary for lifecycle reports
- `TranslationArtifact` — full model with:
  - Identity (artifact_id)
  - Classification (translator_id, translator_category, output_class)
  - Lifecycle state (artifact_state: validation_only | non_executable | execution_planned)
  - Lineage (source_export_object_id, source_export_object_hash)
  - Governance snapshots (capability_snapshot, policy_snapshot)
  - 7D safety flags (all false, enforced by model_validator)
- `build_validation_translation_artifact()` — builder for validation-only artifacts
- `build_artifact_summary_from_translator()` — convenience function for lifecycle
- `compute_export_object_hash()` — SHA256 hash of export object

### services/api/app/cam/translation_artifact_registry.py

Artifact class registry with:
- `ArtifactClassRegistration` — registration model with 7D invariants
- `TRANSLATION_ARTIFACT_CLASS_REGISTRY` with entries:
  - `dxf_validation_artifact` — DXF compatibility metadata
  - `svg_validation_artifact` — SVG compatibility metadata
  - `neutral_toolpath_validation_artifact` — toolpath structure metadata
  - `gcode_validation_artifact` — postprocessor compatibility metadata
- Registry access functions:
  - `get_artifact_class()`
  - `list_artifact_classes()`
  - `get_artifact_classes_by_output()`
  - `get_artifact_classes_by_category()`
  - `get_artifact_class_for_translator()` — maps translator ID to artifact class

### services/api/app/routers/cam/translation_artifact_router.py

Introspection endpoints:
- `GET /api/cam/translation-artifacts` — list all artifact classes
- `GET /api/cam/translation-artifacts/ids` — list artifact class IDs
- `GET /api/cam/translation-artifacts/{artifact_class_id}` — get single class
- `GET /api/cam/translation-artifacts/by-output/{output_class}` — filter by output
- `GET /api/cam/translation-artifacts/by-category/{category}` — filter by category

## Files Modified

### services/api/app/cam/export_lifecycle_orchestrator.py

- Added `TranslationArtifactSummary` import
- Added `translation_artifact_summary` field to `GovernedExportLifecycleReport`
- Integrated artifact generation at Step 5.5 (after translator validation)
- Artifact is only created when:
  - Export object exists
  - Translator validation passed (translator_compatible=True)

### services/api/app/router_registry/manifests/cam_manifest.py

- Registered `translation_artifact_router`

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Translation Artifact Flow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Export Object ────┐                                                 │
│                    │                                                 │
│                    ▼                                                 │
│  ┌─────────────────────────────────────┐                            │
│  │  build_artifact_summary_from_translator()                        │
│  │    - get_translator_capability()                                 │
│  │    - build_validation_translation_artifact()                     │
│  │    - artifact.to_summary()                                       │
│  └─────────────────────────────────────┘                            │
│                    │                                                 │
│                    ▼                                                 │
│  ┌─────────────────────────────────────┐                            │
│  │  TranslationArtifactSummary         │                            │
│  │    - artifact_id                    │                            │
│  │    - translator_id                  │                            │
│  │    - output_class                   │                            │
│  │    - artifact_state                 │                            │
│  │    - execution_supported: false     │  ◄── 7D invariants         │
│  │    - executable_payload_present: false                           │
│  │    - machine_output_present: false  │                            │
│  │    - source_export_object_hash      │                            │
│  │    - deterministic_hash             │                            │
│  └─────────────────────────────────────┘                            │
│                    │                                                 │
│                    ▼                                                 │
│  GovernedExportLifecycleReport.translation_artifact_summary          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Type Definitions

```python
ArtifactOutputClass = Literal[
    "dxf",
    "svg",
    "neutral_toolpath",
    "gcode",
    "machine_output",
]

ArtifactState = Literal[
    "validation_only",
    "non_executable",
    "execution_planned",
]

ArtifactCategory = Literal[
    "translator",
    "postprocessor",
]
```

## Artifact Class Registry vs Translator Capability Registry

| Aspect | Translator Capability Registry (7B) | Artifact Class Registry (7D) |
|--------|-------------------------------------|------------------------------|
| Purpose | What translators exist | What artifact types exist |
| Entries | dxf_r12, dxf_r2000, gcode_grbl_placeholder | dxf_validation_artifact, svg_validation_artifact, etc. |
| Granularity | Per translator | Per output class |
| Contains | Execution state, output class, maturity | Output class, category, 7D safety flags |
| Used by | Validation flow (7C) | Artifact creation (7D) |

## Safety Assertions

All artifact-related code guarantees:
1. No DXF serialization tokens in output
2. No G-code tokens in output
3. No executable payloads
4. No machine output
5. `metadata.validation_only = true`

## Test Coverage

`tests/cam/test_translation_artifact.py` covers:
- TranslationArtifact model creation and invariants
- TranslationArtifactSummary generation
- Artifact class registry operations
- 7D invariant enforcement (violations raise ValueError)
- Export object hashing
- Lifecycle integration
- Endpoint functionality
- Safety assertions

## What 7D Does NOT Do

- NO DXF generation
- NO G-code generation
- NO translator execution
- NO machine output
- NO executable payloads

## Usage Example

```python
from app.cam.translation_artifact import build_artifact_summary_from_translator

# In lifecycle orchestrator:
if export_object is not None and translator_compatible:
    artifact_summary = build_artifact_summary_from_translator(
        export_object=export_object,
        translator_id=translator_profile.translator_id,
    )
    # artifact_summary is now included in lifecycle report
```

## Next Steps

1. Run tests: `pytest tests/cam/test_translation_artifact.py -v`
2. Run full CAM test suite: `pytest tests/cam/ -v`
3. Commit with message referencing 7D

## Related Dev Orders

- **7A**: Translator execution boundary architecture (planning)
- **7B**: Translator capability registry (complete)
- **7C**: Registry-gated validation (complete)
- **7D**: Translation artifact model (this document)
- **7E+**: Governed translator execution (future)
