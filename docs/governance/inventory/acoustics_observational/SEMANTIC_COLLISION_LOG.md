# Semantic Collision Log — Acoustics/Observational

**Sprint:** Acoustics/Observational  
**Terminal:** 4  
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

### COL-ACOU-001: confidence vocabulary collision

```
collision_id: COL-ACOU-001
terms_or_systems: AcousticConfidence (enum) vs confidence (numeric 0-1)
collision_type: overload
description: "confidence" field used with different semantic types across domains. Acoustics uses enum ('unknown' | 'low' | 'medium' | 'high') for epistemic certainty. Blueprint vectorizer uses numeric 0-1 score for detection certainty.
source_locations:
  - packages/client/src/types/acoustics.ts:16 (AcousticConfidence enum)
  - packages/client/src/design-intake/blueprint/useBlueprintProjectWrite.ts:62 (confidence: number)
  - packages/client/src/design-intake/blueprint/BlueprintSavePanel.vue:189-190
affected_sprints: Acoustics/Observational, Geometry/Morphology/Topology (vectorizer)
risk_level: medium
do_not_fix_in_c1: true
recommended_next_phase: C2 — Evaluate whether to prefix (acoustic_confidence vs detection_confidence) or accept domain-specific overloading
notes: Different semantic intent. Acoustics: epistemic certainty. Vectorizer: detection certainty. May be acceptable overloading if clearly scoped.
```

### COL-ACOU-002: observationalOnly cross-domain usage

```
collision_id: COL-ACOU-002
terms_or_systems: observationalOnly (acoustics) vs observational_only (CAM runtime)
collision_type: authority_overlap
description: Same semantic concept used across acoustics and CAM runtime with slightly different field naming (camelCase vs snake_case) and enforcement mechanisms (TypeScript literal vs Pydantic Literal[True]).
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:144 (observationalOnly: true)
  - services/api/app/cam/runtime/runtime_results.py:49 (observational_only: Literal[True])
  - docs/governance/CANONICAL_PROVENANCE_MODEL.md:129
affected_sprints: Acoustics/Observational, Runtime/CAM, Governance Integration
risk_level: low
do_not_fix_in_c1: true
recommended_next_phase: C2 — Decide canonical naming convention. Consider promoting to C0 vocabulary with single naming standard.
notes: Semantic intent is identical. Collision is naming/casing only. Low risk if both enforce the invariant correctly.
```

### COL-ACOU-003: source field name overload

```
collision_id: COL-ACOU-003
terms_or_systems: MeasurementSource vs AcousticStateSource
collision_type: overload
description: Field name "source" used for two different enumerations within acoustics domain. MeasurementSource describes physical measurement origin (tap_tone, impedance_tube). AcousticStateSource describes data derivation type (geometry_estimate, measured, calibrated).
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:36-42 (MeasurementSource)
  - packages/client/src/types/acoustics.ts:21-27 (AcousticStateSource)
affected_sprints: Acoustics/Observational
risk_level: low
do_not_fix_in_c1: true
recommended_next_phase: C2 — Consider renaming to measurement_source vs state_source for clarity, or document as intentional scoped overloading
notes: Different contexts (MeasurementArchive vs AcousticState) provide disambiguation. Local collision within acoustics domain only.
```

### COL-ACOU-004: gate color vocabulary sharing

```
collision_id: COL-ACOU-004
terms_or_systems: readinessLevel ('green' | 'yellow' | 'red') vs validation_gate ('green' | 'yellow' | 'red')
collision_type: synonym
description: Same vocabulary ('green' | 'yellow' | 'red') used for different gate concepts. Acoustics readinessLevel indicates calibration readiness (observational). CAM validation_gate indicates validation outcome (runtime).
source_locations:
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:157-169 (getSnapshotGateColor)
  - services/api/app/cam/runtime/runtime_results.py (validation_gate)
affected_sprints: Acoustics/Observational, Runtime/CAM
risk_level: low
do_not_fix_in_c1: true
recommended_next_phase: C2 — Evaluate whether shared gate vocabulary is a feature (consistent UX) or a risk (semantic confusion)
notes: Shared vocabulary may be intentional for consistent user experience. Both use traffic light metaphor for different purposes.
```

### COL-ACOU-005: lineage not present in acoustics

```
collision_id: COL-ACOU-005
terms_or_systems: lineage (absent in acoustics) vs lineage (RMOS presets)
collision_type: geometry_ambiguity (term boundary)
description: "lineage" term not used in acoustics domain despite being a focus term. Appears only in RMOS preset system for job derivation chains. If acoustics needs derivation tracking in future, term collision could arise.
source_locations:
  - packages/client/src/views/multi_run_comparison/ (RMOS lineage)
  - packages/client/src/components/rmos/PromptLineageViewer.vue
affected_sprints: Acoustics/Observational (potential future), Runtime/CAM (RMOS)
risk_level: low
do_not_fix_in_c1: true
recommended_next_phase: C2 — Reserve "lineage" vocabulary. If acoustics needs derivation tracking, use different term (e.g., "measurement_lineage" or "derivation_chain")
notes: Preemptive collision logging. Acoustics currently uses diagnosticSnapshotReference for traceability, not "lineage".
```

### COL-ACOU-006: provenance semantic split (inherited)

```
collision_id: COL-ACOU-006
terms_or_systems: provenanceReminder (documentation) vs provenance (action log) vs provenance (authority chain)
collision_type: provenance_split
description: Acoustics uses "provenanceReminder" as documentation string. CAM runtime uses "provenance" as action log list. Governance uses "provenance" for authority chain. Different semantic intents under same root term.
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:163 (provenanceReminder: string)
  - services/api/app/cam/runtime/runtime_results.py (provenance: list[str])
  - docs/governance/CANONICAL_PROVENANCE_MODEL.md
affected_sprints: Acoustics/Observational, Runtime/CAM, Governance Integration
risk_level: medium
do_not_fix_in_c1: true
recommended_next_phase: C2 — Adopt C0 provenance model with explicit subtypes (action_provenance, epistemic_provenance, authority_provenance). Acoustics provenanceReminder maps to "documentation_provenance" or remains separate.
notes: Acoustics uses provenanceReminder as user-facing documentation, not traceability data. May be distinct from C0 provenance model.
```

---

## Summary

| Collision Type | Count |
|----------------|-------|
| Synonym | 1 |
| Overload | 2 |
| Authority overlap | 1 |
| Lifecycle conflict | 0 |
| Provenance split | 1 |
| Geometry ambiguity | 1 |
| Runtime inference | 0 |
| Staging leakage | 0 |

| Risk Level | Count |
|------------|-------|
| Low | 4 |
| Medium | 2 |
| High | 0 |
| Critical | 0 |

---

## Notes

1. Acoustics domain has relatively clean semantics. Most collisions are cross-domain with vectorizer or CAM runtime.

2. The "confidence" overload (COL-ACOU-001) is the highest-impact collision. Consider prefixing in C2.

3. Gate color vocabulary sharing (COL-ACOU-004) may be intentional UX consistency, not a bug.

4. provenanceReminder is semantically distinct from provenance action logs — may not need unification.

5. All collisions are recorded for C2 reconciliation. No fixes during C1.

---

## Strategic Significance

The Acoustics domain has **no high-severity collisions** and demonstrates disciplined governance patterns:

| Pattern | Evidence |
|---------|----------|
| Domain-scoped vocabulary | Voicing gate, run status — no cross-domain claims |
| Explicit provenance | ProvenanceBlockV1 — capture context only |
| Mandatory confidence | AcousticConfidence required |
| Mandatory assumptions | string[] required |
| Consumer-without-authority | Geometry interface, not dependency |

This makes Acoustics a **control group** for C2 arbitration — demonstrating what healthy governance looks like before reconciling higher-pressure domains.

### Cross-Reference

Full inventory details in: `C1_ACOUSTICS_OBSERVATIONAL_SEMANTIC_INVENTORY.md`
