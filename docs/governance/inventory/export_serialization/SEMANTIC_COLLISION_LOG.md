# Semantic Collision Log — Export/Serialization

**Sprint:** Export/Serialization  
**Terminal:** 5  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This log records observed semantic collisions. It does not:
- Resolve collisions
- Rename terms
- Assign winners
- Enforce corrections

**Critical:** Collisions recorded here MUST NOT be fixed during C1.

---

## Collision Entries

### COLL-E001: Serialization Term Overload

| Field | Value |
|-------|-------|
| collision_id | COLL-E001 |
| collision_type | overload |
| risk_level | Medium |
| do_not_fix_in_c1 | true |

**Terms:**
- `serialization` (7M registered term)
- `serializer_invocation` (execution quarantine vocabulary)
- `SERIALIZATION` (TranslatorCategory enum value)

**Locations:**
- `app/cam/canonical_ontology_registry.py:489` — 7M registered term
- `app/cam/translator_execution_quarantine.py:75` — prohibited operation
- `app/cam/translators/base/capabilities.py:18` — category enum

**Collision Description:**
"Serialization" is used in three distinct semantic contexts:
1. **7M registry**: Canonical ontology term with formal definition
2. **Execution quarantine**: Operation that is explicitly prohibited (`serializer_invocation_allowed: false`)
3. **Translator capability**: Category classification for translator routing

The 7M registration and execution quarantine prohibition are aligned. The TranslatorCategory usage may imply capability without execution authorization.

**C2 Candidate:**
Clarify whether `SERIALIZATION` TranslatorCategory implies capability or authorization. Consider renaming to `GEOMETRY_FORMAT` to avoid 7M term collision.

---

### COLL-E002: IBG Authority Propagation Risk

| Field | Value |
|-------|-------|
| collision_id | COLL-E002 |
| collision_type | authority_overlap |
| risk_level | High |
| do_not_fix_in_c1 | true |

**Terms:**
- `IBGMorphologyExtension` (Export Object extension)
- `BodyMorphologyClass` (IBG sandbox vocabulary)
- `radii_by_zone` (IBG zone semantics)
- `side_heights_mm` (IBG dimensional data)

**Locations:**
- `app/export/body_export_bridge.py:163-172` — IBGMorphologyExtension
- `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:24` — BodyMorphologyClass
- `app/instrument_geometry/body/ibg/body_grid/zones.py:24` — ZoneId

**Collision Description:**
IBG morphology data propagates through Export Object into translator output via IBGMorphologyExtension. The data includes:
- `radii_by_zone` — maps ZoneId to radius values
- `side_heights_mm` — IBG-derived height measurements
- `dimensions` — IBG-computed dimensional data
- `confidence` — IBG classification confidence

This creates a propagation pathway for sandbox semantics into production artifacts. If downstream systems (future CAD translators, STEP generators) treat these values as authoritative geometry rather than advisory morphology, **sandbox authority leaks into production**.

**C2 Candidate:**
1. Add explicit `advisory_only: bool = True` field to IBGMorphologyExtension
2. Document consumption constraints for downstream translators
3. Consider separate `IBGAdvisoryData` type with clear non-authority semantics

---

### COLL-E003: Gate Vocabulary Synonym

| Field | Value |
|-------|-------|
| collision_id | COLL-E003 |
| collision_type | synonym |
| risk_level | Low |
| do_not_fix_in_c1 | true |

**Terms:**
- `gate_status` (Export Object validation)
- `gate` (Translator compatibility report)
- `risk_level` (RMOS feasibility)
- `overallGate` (Calibration readiness)
- `validation_gate` (CAM runtime)

**Locations:**
- `app/export/body_export_bridge.py:120` — gate_status
- `app/cam/dxf_translator_boundary.py:79` — gate
- `app/rmos/runs_v2/exports.py:191` — risk_level
- `packages/client/src/types/calibration.ts` — overallGate
- `services/api/app/cam/runtime/runtime_results.py` — validation_gate

**Collision Description:**
Multiple fields express the same semantic concept (traffic light gate status) with different names:
- `gate_status`: Export validation
- `gate`: Translator compatibility
- `risk_level`: RMOS feasibility (same green/yellow/red vocabulary)
- `overallGate`: Calibration readiness
- `validation_gate`: CAM runtime

All use the same green/yellow/red vocabulary with equivalent semantics. The inconsistent naming creates cognitive overhead but not semantic ambiguity.

**C2 Candidate:**
Either:
1. Document as intentional parallel vocabularies (different domains, same semantics)
2. Create unified `GateStatus` type aliased across domains
3. Accept as naming variation with documented equivalence

---

### COLL-E004: RuntimeSupport vs ExecutionState

| Field | Value |
|-------|-------|
| collision_id | COLL-E004 |
| collision_type | overload |
| risk_level | Medium |
| do_not_fix_in_c1 | true |

**Terms:**
- `RuntimeSupport` (CAD semantics: SUPPORTED, SEMANTIC_ONLY, UNSUPPORTED)
- `ExecutionState` (Translator capability: validation_only, governed_execution, etc.)

**Locations:**
- `app/export/cad_semantics.py:72-77` — RuntimeSupport
- `app/cam/translator_capability_registry.py:46-52` — ExecutionState

**Collision Description:**
Two different enums describe "can this component execute" with different granularity and semantic intent:

**RuntimeSupport** (3 states):
- `SUPPORTED` — full runtime generation capability
- `SEMANTIC_ONLY` — schema valid, no runtime topology
- `UNSUPPORTED` — not supported

**ExecutionState** (5 states):
- `validation_only` — can validate, cannot execute
- `execution_planned` — execution planned but not authorized
- `execution_disabled` — explicitly disabled
- `execution_authorized_future` — future execution
- `governed_execution` — full execution authorized

RuntimeSupport describes **CAD semantic configuration** capability.
ExecutionState describes **translator governance** lifecycle.

They operate at different layers but may be confused when reasoning about "what can run."

**C2 Candidate:**
Document the semantic distinction:
- RuntimeSupport = "Does this semantic configuration have runtime topology support?"
- ExecutionState = "Is this translator authorized to execute?"

Consider renaming RuntimeSupport to `TopologySupport` to clarify it describes topology generation, not translator execution.

---

## Summary

| Collision Type | Count |
|----------------|-------|
| Synonym | 1 |
| Overload | 2 |
| Authority overlap | 1 |
| Lifecycle conflict | 0 |
| Provenance split | 0 |
| Geometry ambiguity | 0 |
| Runtime inference | 0 |
| Staging leakage | 0 |

| Risk Level | Count |
|------------|-------|
| Low | 1 |
| Medium | 2 |
| High | 1 |
| Critical | 0 |

---

## Notes

### COLL-E002 is Primary Risk

The IBG authority propagation risk (COLL-E002) is the highest-priority collision in this domain. It represents a pathway for sandbox semantics to leak into production artifacts.

### Strong Constitutional Enforcement

Despite having 4 collisions, the Export/Serialization domain has **strong constitutional enforcement**:
- Model validators enforce `machine_output_supported=False`
- Model validators enforce `serializer_invocation_allowed=False`
- Gate enforcement blocks red-gated exports
- Authority boundaries explicitly documented in CAD semantics

### Cross-Domain Pattern

COLL-E003 (gate vocabulary) is a cross-domain collision also observed in:
- Acoustics/Observational (readinessLevel)
- Runtime/CAM (validation_gate)
- Governance (readiness gates)

This may be intentional UX consistency or may require unification.

### Cross-Reference

Full inventory details in: `C1_EXPORT_SERIALIZATION_SEMANTIC_INVENTORY.md`
