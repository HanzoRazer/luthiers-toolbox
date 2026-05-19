# Semantic Inventory — Export/Serialization

**Sprint:** Export/Serialization  
**Terminal:** 5  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This inventory documents observed semantic usage. It does not:
- Ratify terms as canonical
- Assign ownership
- Normalize vocabulary
- Resolve collisions

Discovery does not imply endorsement.

---

## Focus Areas

Terminal 5 inventories:
- `export_type`
- `serialization`
- `translator`
- `gate_status`
- `provenance`
- `runtime_support`
- `execution_state`
- `manufacturing_intent`

---

## Inventory Entries

### ExportType

```
term: ExportType
local_meaning: Classification of export artifact type
scope: structural
declared_owner: CAM Export Object
operational_owner: app/cam/export_object.py:40
source_locations:
  - app/cam/export_object.py:40-43
enforcement_status: structural (Python Enum)
related_terms: geometry, toolpath, bundle, export_id
notes: Values: TOOLPATH, GEOMETRY, BUNDLE. Determines translator routing.
```

### TranslatorMaturity

```
term: TranslatorMaturity
local_meaning: Governance maturity level for translators
scope: governance
declared_owner: CAM Translator Capability Registry
operational_owner: app/cam/translator_capability_registry.py:39
source_locations:
  - app/cam/translator_capability_registry.py:39-44
  - app/cam/translators/base/capabilities.py:26-32
enforcement_status: structural (Python Enum, Literal types)
related_terms: execution_state, governed_execution, placeholder
notes: Values: placeholder, candidate, governed, canonical. Progression reflects governance review.
```

### ExecutionState

```
term: ExecutionState
local_meaning: Translator execution authorization state
scope: governance
declared_owner: CAM Translator Capability Registry
operational_owner: app/cam/translator_capability_registry.py:46
source_locations:
  - app/cam/translator_capability_registry.py:46-52
  - app/cam/translators/base/capabilities.py:35-41
enforcement_status: structural (Enum + model validators)
related_terms: execution_supported, machine_output_supported, governed_execution
notes: Values: validation_only, execution_planned, execution_disabled, execution_authorized_future, governed_execution. Model validators enforce invariants.
```

### TranslatorCategory

```
term: TranslatorCategory
local_meaning: Functional classification of translators
scope: operational
declared_owner: CAM Translator Base
operational_owner: app/cam/translators/base/capabilities.py:17
source_locations:
  - app/cam/translators/base/capabilities.py:17-24
enforcement_status: structural (Python Enum)
related_terms: SERIALIZATION, VISUALIZATION, MANUFACTURING
notes: Values: SERIALIZATION, VISUALIZATION, MANUFACTURING, ARCHIVAL, ANALYSIS. MANUFACTURING category currently has no authorized translators.
```

### gate_status

```
term: gate_status
local_meaning: Validation gate result for export objects
scope: governance
declared_owner: Export Validation
operational_owner: app/export/body_export_bridge.py:120
source_locations:
  - app/export/body_export_bridge.py:120
  - app/cam/dxf_translator_boundary.py:79
enforcement_status: structural (Literal types)
related_terms: green, yellow, red, preview_gate, export_gate
notes: Values: green, yellow, red. Red gates block translation.
```

### RuntimeSupport

```
term: RuntimeSupport
local_meaning: Translator runtime generation capability
scope: operational
declared_owner: CAD Semantics
operational_owner: app/export/cad_semantics.py:72
source_locations:
  - app/export/cad_semantics.py:72-77
enforcement_status: structural (Python Enum)
related_terms: SUPPORTED, SEMANTIC_ONLY, UNSUPPORTED, body_category
notes: Values: SUPPORTED, SEMANTIC_ONLY, UNSUPPORTED. SEMANTIC_ONLY indicates schema-valid configuration without runtime generation.
```

### BodyCategory

```
term: BodyCategory
local_meaning: Body type classification for CAD translation routing
scope: operational
declared_owner: CAD Semantics
operational_owner: app/export/cad_semantics.py:31
source_locations:
  - app/export/cad_semantics.py:31-41
enforcement_status: structural (Python Enum)
related_terms: FLAT_BODY, ACOUSTIC_FLAT_TOP, runtime_support
notes: Values: FLAT_BODY, ACOUSTIC_FLAT_TOP, ACOUSTIC_ARCHED_TOP, HOLLOW_ELECTRIC, ARCHTOP, RESONATOR, UNKNOWN. Only FLAT_BODY has runtime support.
```

### serialization (7M registered)

```
term: serialization
local_meaning: Converting semantic structure to external format
scope: structural (7M registered)
declared_owner: CAM Canonical Ontology
operational_owner: app/cam/canonical_ontology_registry.py:489
source_locations:
  - app/cam/canonical_ontology_registry.py:489-503
enforcement_status: canonical (7M registry)
related_terms: translator, format_serialization, export_serialization
notes: 7M registered term. Prohibited reinterpretations: automatic_serialization. Aliases: format_serialization, export_serialization.
```

### translator_id

```
term: translator_id
local_meaning: Unique identifier for registered translator
scope: structural
declared_owner: Translator Capability Registry
operational_owner: app/cam/translator_capability_registry.py:77
source_locations:
  - app/cam/translator_capability_registry.py:77
  - app/cam/translators/base/contracts.py:124
enforcement_status: structural (required field)
related_terms: translator_version, translator_name, capability
notes: Format: snake_case identifier (e.g., body_outline_dxf_r12). Must match registry entry.
```

### TranslatorProvenance

```
term: TranslatorProvenance
local_meaning: Provenance metadata embedded in translator output
scope: observational
declared_owner: Translator Contracts
operational_owner: app/cam/translators/base/contracts.py:48
source_locations:
  - app/cam/translators/base/contracts.py:48-71
enforcement_status: structural (dataclass)
related_terms: export_id, source_hash, ibg_session_id
notes: Embeds lineage in serialized artifacts. Fields: export_id, translator_id, translator_version, translated_at, target_format, source_hash, ibg_session_id, instrument_spec.
```

### IBGMorphologyExtension

```
term: IBGMorphologyExtension
local_meaning: IBG morphology data propagated through export
scope: advisory
declared_owner: Export Extensions
operational_owner: app/export/body_export_bridge.py:163
source_locations:
  - app/export/body_export_bridge.py:163-172
enforcement_status: structural (optional Pydantic model)
related_terms: session_id, confidence, dimensions, radii_by_zone
notes: Advisory morphology data from IBG session. Risk: may be consumed as authoritative geometry. Fields: session_id, confidence, dimensions, instrument_spec, side_heights_mm, radii_by_zone, missing_landmarks, recovery_mode.
```

### CadSemantics

```
term: CadSemantics
local_meaning: CAD construction hints for downstream translators
scope: advisory
declared_owner: CAD Semantics Extension
operational_owner: app/export/cad_semantics.py:273
source_locations:
  - app/export/cad_semantics.py:273-380
enforcement_status: structural (Pydantic model with validators)
related_terms: body_category, flat_body, acoustic, runtime_support
notes: Authority rule: may EXTEND approved geometry, may NOT override. Contains body_category, flat_body, acoustic extensions.
```

### risk_level (RMOS)

```
term: risk_level
local_meaning: RMOS feasibility risk classification
scope: operational
declared_owner: RMOS Runs v2
operational_owner: app/rmos/runs_v2/exports.py:191
source_locations:
  - app/rmos/runs_v2/exports.py:191-202
enforcement_status: advisory (runtime gate)
related_terms: GREEN, YELLOW, RED, override, feasibility
notes: Values: GREEN, YELLOW, RED, UNKNOWN. Red/Yellow require override for export.
```

### machine_output_supported

```
term: machine_output_supported
local_meaning: Flag indicating G-code/machine output capability
scope: governance
declared_owner: Translator Capability Registry
operational_owner: app/cam/translator_capability_registry.py:117
source_locations:
  - app/cam/translator_capability_registry.py:117-120
enforcement_status: structural (model validator enforces always false)
related_terms: execution_supported, artifact_generation_supported
notes: Model validator enforces this is always false. No machine output capability authorized.
```

### serializer_invocation_allowed

```
term: serializer_invocation_allowed
local_meaning: Flag indicating serializer execution authorization
scope: governance
declared_owner: Translator Execution Quarantine
operational_owner: app/cam/translator_execution_quarantine.py:260
source_locations:
  - app/cam/translator_execution_quarantine.py:260-262
enforcement_status: structural (model validator enforces always false)
related_terms: execution_state, quarantine, 7H invariants
notes: Always false in 7H. No serializer invocation authorized.
```

---

## Summary

| Metric | Count |
|--------|-------|
| Terms inventoried | 15 |
| Declared owners identified | 12 |
| Operational owners identified | 15 |
| Authority mismatches | 1 (IBGMorphologyExtension — advisory vs potentially authoritative) |
| Enforcement gaps | 0 (strong model validator enforcement) |
| Cross-domain collisions | 2 (serialization overload, gate vocabulary) |

---

## Notes

1. Export/Serialization domain has **strong constitutional enforcement** through model validators.

2. `machine_output_supported` and `serializer_invocation_allowed` are governance invariants, not configuration options.

3. IBGMorphologyExtension propagates sandbox semantics into export artifacts — consumers must treat as advisory.

4. Gate vocabulary (green/yellow/red) is consistent across domains but uses different field names.

5. **Governance Reference**: The Export/Serialization domain demonstrates disciplined authority boundaries that prevent serialization-driven ontology hardening.

### Cross-Reference

Full inventory details in: `C1_EXPORT_SERIALIZATION_SEMANTIC_INVENTORY.md`
