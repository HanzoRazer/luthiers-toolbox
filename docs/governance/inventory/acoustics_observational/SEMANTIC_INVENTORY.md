# Semantic Inventory — Acoustics/Observational

**Sprint:** Acoustics/Observational  
**Terminal:** 4  
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

Terminal 4 inventories:
- `measurement`
- `observation`
- `confidence`
- `uncertainty`
- `epistemic state`
- `capture provenance`
- `analysis provenance`
- `replay`
- `lineage`

---

## Inventory Entries

### measurement

```
term: measurement
local_meaning: Observational acoustic data captured from physical testing (tap tone, impedance tube, etc.)
scope: observational
declared_owner: MeasurementArchive infrastructure (Dev Order 54)
operational_owner: packages/client/src/types/acoustics/measurementArchive.ts
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:58 (MeasurementArchiveMeasurement)
  - packages/client/src/utils/acoustics/measurementArchive.ts
  - docs/architecture/MEASUREMENT_ARCHIVE_ARCHITECTURE.md
enforcement_status: structural (TypeScript interfaces)
related_terms: MeasurementSource, MeasurementMethod, measuredHelmholtzHz, measuredQ
notes: Dev Order 54 measurement archive is the primary declared observational archive scaffold. It is not automatically the canonical measurement authority.
```

### MeasurementSource

```
term: MeasurementSource
local_meaning: Enumerated source of measurement data
scope: observational
declared_owner: MeasurementArchive
operational_owner: packages/client/src/types/acoustics/measurementArchive.ts:36
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:36-42
enforcement_status: structural (TypeScript union type)
related_terms: measurement, tap_tone, impedance_tube, near_field_mic, manual_entry, external_import
notes: Values: 'tap_tone' | 'impedance_tube' | 'near_field_mic' | 'manual_entry' | 'external_import' | 'unknown'
```

### MeasurementMethod

```
term: MeasurementMethod
local_meaning: Enumerated method used to obtain measurement
scope: observational
declared_owner: MeasurementArchive
operational_owner: packages/client/src/types/acoustics/measurementArchive.ts:47
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:47-53
enforcement_status: structural (TypeScript union type)
related_terms: measurement, fft_peak_detection, swept_sine, impulse_response, manual_reading
notes: Values: 'fft_peak_detection' | 'swept_sine' | 'impulse_response' | 'manual_reading' | 'unknown'
```

### observationalOnly

```
term: observationalOnly
local_meaning: Boolean invariant flag indicating data is observational (not predictive, not executable)
scope: observational | runtime
declared_owner: Governance layer (C0 provenance model)
operational_owner: Multiple — MeasurementArchive, DiagnosticSnapshot, RuntimeResultBase
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:144 (always true)
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:109 (always true)
  - services/api/app/cam/runtime/runtime_results.py:49 (Literal[True])
enforcement_status: structural (TypeScript literal type, Pydantic Literal[True] + validator)
related_terms: provenanceReminder, exportReady
notes: Cross-domain term. Acoustics uses as archive invariant. CAM runtime uses as execution barrier. See SEMANTIC_COLLISION_LOG for collision with 'immutable'.
```

### confidence

```
term: confidence
local_meaning: Epistemic certainty level for acoustic estimates
scope: epistemic | observational
declared_owner: AcousticState (acoustics domain)
operational_owner: packages/client/src/types/acoustics.ts:16
source_locations:
  - packages/client/src/types/acoustics.ts:16 (AcousticConfidence type)
  - packages/client/src/utils/acoustics/acousticState.ts:93 (getConfidenceLabel)
  - packages/client/src/types/estimateAssumptions.ts:22
enforcement_status: structural (TypeScript union type)
related_terms: AcousticConfidence, source, assumptions
notes: Values: 'unknown' | 'low' | 'medium' | 'high'. Most geometry-derived estimates are 'low'. Cross-domain collision: blueprint vectorizer uses 'confidence' as numeric 0-1 score.
```

### AcousticConfidence

```
term: AcousticConfidence
local_meaning: Type alias for acoustic confidence levels
scope: epistemic
declared_owner: acoustics types
operational_owner: packages/client/src/types/acoustics.ts:16
source_locations:
  - packages/client/src/types/acoustics.ts:16
enforcement_status: structural (TypeScript type alias)
related_terms: confidence, AcousticState
notes: Canonical epistemic state vocabulary for acoustics domain.
```

### source (AcousticStateSource)

```
term: source (AcousticStateSource)
local_meaning: Origin type for acoustic state data
scope: observational
declared_owner: AcousticState
operational_owner: packages/client/src/types/acoustics.ts:21
source_locations:
  - packages/client/src/types/acoustics.ts:21-27
  - packages/client/src/utils/acoustics/acousticState.ts:110 (getSourceLabel)
enforcement_status: structural (TypeScript union type)
related_terms: confidence, measurement, geometry_estimate, calibrated, manual
notes: Values: 'geometry_estimate' | 'measured' | 'calibrated' | 'manual' | 'unknown'. Distinguishes measured observation from geometry-derived estimate.
```

### assumptions

```
term: assumptions
local_meaning: List of epistemic caveats attached to acoustic estimates
scope: epistemic
declared_owner: AcousticState
operational_owner: packages/client/src/types/acoustics.ts:95
source_locations:
  - packages/client/src/types/acoustics.ts:95 (assumptions: string[])
  - packages/client/src/utils/acoustics/acousticState.ts:15-21 (DEFAULT_GEOMETRY_ASSUMPTIONS)
enforcement_status: structural (mandatory field on AcousticState)
related_terms: confidence, warnings, provenanceReminder
notes: Mandatory field. Prevents estimated physics looking like measured truth.
```

### warnings

```
term: warnings
local_meaning: List of warning messages about acoustic state validity
scope: epistemic
declared_owner: AcousticState, MeasurementArchive
operational_owner: Multiple acoustic types
source_locations:
  - packages/client/src/types/acoustics.ts:98
  - packages/client/src/types/acoustics/measurementArchive.ts:87
enforcement_status: advisory (optional field)
related_terms: assumptions, exportWarnings
notes: Epistemic signals about data quality or staleness.
```

### snapshot

```
term: snapshot
local_meaning: Structured observational record of diagnostic session state
scope: observational
declared_owner: DiagnosticSnapshot infrastructure
operational_owner: packages/client/src/utils/acoustics/diagnosticSnapshot.ts
source_locations:
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts
  - packages/client/src/types/diagnosticSnapshot.ts
enforcement_status: structural (TypeScript interface, schema versioning)
related_terms: DiagnosticSnapshotSection, snapshotId, provenanceReminder
notes: Schema version: 'diagnostic-snapshot.v1'. Kind: 'aperture-diagnostic-snapshot'.
```

### estimate

```
term: estimate
local_meaning: Computed acoustic value (not measured)
scope: observational
declared_owner: AcousticState
operational_owner: packages/client/src/types/acoustics.ts
source_locations:
  - packages/client/src/types/acoustics.ts:77-92 (estimatedHelmholtzHz, estimatedEffectiveLengthMm, etc.)
  - packages/client/src/utils/acoustics/helmholtzEstimate.ts
  - packages/client/src/utils/acoustics/estimateAssumptions.ts
enforcement_status: advisory (estimates must carry assumptions)
related_terms: estimatedHelmholtzHz, estimateMethod, estimateSource, confidence
notes: Estimates are distinguished from measurements. Both carry provenance.
```

### readinessLevel

```
term: readinessLevel
local_meaning: Gate color indicating calibration readiness state
scope: observational
declared_owner: DiagnosticSnapshot
operational_owner: packages/client/src/utils/acoustics/diagnosticSnapshot.ts:90
source_locations:
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:90
  - packages/client/src/types/calibration.ts (CalibrationReadiness.overallGate)
enforcement_status: advisory
related_terms: calibrationReadiness, overallGate, green/yellow/red
notes: Values: 'green' | 'yellow' | 'red'. Does not authorize calibration — indicates observational readiness only.
```

---

## Cross-Domain Terms (Classification: cross-domain)

### confidence (blueprint)

```
term: confidence (blueprint vectorizer)
local_meaning: Numeric 0-1 score for AI phase 1 analysis certainty
scope: other (blueprint/vectorizer domain)
declared_owner: Blueprint vectorizer
source_locations:
  - packages/client/src/design-intake/blueprint/useBlueprintProjectWrite.ts:62
  - packages/client/src/design-intake/blueprint/BlueprintSavePanel.vue:189-190
enforcement_status: none (local usage)
related_terms: scale_confidence, interpretation_confidence
notes: Classification: cross-domain. Different semantic from AcousticConfidence (enum vs numeric). Terminal 2/3 should inventory.
```

### lineage (RMOS presets)

```
term: lineage (RMOS)
local_meaning: Derivation chain for presets cloned from JobInt runs
scope: other (RMOS domain)
declared_owner: RMOS preset system
source_locations:
  - packages/client/src/views/multi_run_comparison/composables/useMultiRunComparisonActions.ts:31
  - packages/client/src/components/rmos/PromptLineageViewer.vue
enforcement_status: none (local usage)
related_terms: job_source_id, prompt lineage
notes: Classification: cross-domain. Not acoustic lineage — derivation lineage for AI presets. Terminal 2 should inventory.
```

---

## Summary

| Metric | Count |
|--------|-------|
| Terms inventoried | 14 |
| Declared owners identified | 8 |
| Operational owners identified | 14 |
| Authority mismatches | 1 (observationalOnly — multiple owners) |
| Enforcement gaps | 2 (warnings optional, readinessLevel advisory) |
| Cross-domain collisions | 2 (confidence, lineage) |

---

## Additional Backend Vocabulary (C1 Extension)

### TapToneBundleManifestV1

```
term: TapToneBundleManifestV1
local_meaning: Canonical import contract from tap_tone_pi exporter
scope: observational
declared_owner: RMOS Acoustics
operational_owner: app/rmos/acoustics/schemas_manifest_v1.py:78
source_locations:
  - app/rmos/acoustics/schemas_manifest_v1.py:78-108
enforcement_status: structural (Pydantic with extra="forbid")
related_terms: ProvenanceBlockV1, InstrumentBlockV1, DomainAcousticsBlockV1
notes: Schema version via Literal type. RMOS should ingest from THIS contract, not folder semantics.
```

### ProvenanceBlockV1

```
term: ProvenanceBlockV1
local_meaning: Capture context for acoustic bundles
scope: observational
declared_owner: RMOS Acoustics
operational_owner: app/rmos/acoustics/schemas_manifest_v1.py:48
source_locations:
  - app/rmos/acoustics/schemas_manifest_v1.py:48-57
enforcement_status: structural (Pydantic with extra="allow")
related_terms: device_id, mic_model, adc_model, calibration, ambient
notes: Provenance is capture context, not authority chain. All fields optional.
```

### attachment_kind

```
term: kind (attachment)
local_meaning: Stable semantic category for file classification
scope: observational
declared_owner: RMOS Acoustics
operational_owner: app/rmos/acoustics/schemas_manifest_v1.py:29
source_locations:
  - app/rmos/acoustics/schemas_manifest_v1.py:29
enforcement_status: structural (required string field)
related_terms: audio_raw, analysis_summary, plot, grid, manifest, viewer_pack
notes: Values: audio_raw, analysis_summary, plot, plot_png, grid, point_audio_raw, manifest, viewer_pack, advisory
```

### run_status

```
term: status (run)
local_meaning: Outcome classification for acoustics runs
scope: observational
declared_owner: RMOS Acoustics
operational_owner: app/rmos/runs_v2/acoustics_schemas.py:322
source_locations:
  - app/rmos/runs_v2/acoustics_schemas.py:322
enforcement_status: structural (required field)
related_terms: OK, BLOCKED, ERROR
notes: Outcome classification, not workflow state. Domain-scoped.
```

### voicing_gate

```
term: gate (voicing)
local_meaning: Operational status for plate voicing progress
scope: operational
declared_owner: Voicing Calculator
operational_owner: app/calculators/voicing_history_calc.py:104
source_locations:
  - app/calculators/voicing_history_calc.py:104
enforcement_status: advisory
related_terms: GREEN, YELLOW, RED, on_target, above_target, below_target
notes: Voicing gate is operational status, not governance enforcement. Different semantic from 7M validation gates.
```

### build_stage

```
term: BUILD_STAGES
local_meaning: Ordered lifecycle for voicing workflow
scope: operational
declared_owner: Voicing Calculator
operational_owner: app/calculators/voicing_history_calc.py:18
source_locations:
  - app/calculators/voicing_history_calc.py:18-23
enforcement_status: advisory (ordered list)
related_terms: rough_thicknessed, braced_free_plate, assembled_in_box, strung_up
notes: Workflow-specific lifecycle, not generic state machine.
```

---

## Notes

1. Measurement archive (Dev Order 54) is the primary declared observational archive scaffold. It is not automatically the canonical measurement authority.

2. AcousticConfidence is the canonical epistemic vocabulary for acoustics. Blueprint confidence is numeric — semantic collision.

3. Provenance is split across multiple patterns: provenanceReminder (string), diagnosticSnapshotReference (object), estimateSource/estimateMethod/estimateConfidence (fields).

4. No "replay" semantics found in acoustics domain. The term appears only in stockSimulator.ts ("reset and replay") which is unrelated.

5. **Governance Reference Domain**: The Acoustics domain demonstrates healthy governance patterns:
   - Mandatory confidence (AcousticConfidence)
   - Mandatory assumptions (string[])
   - Clean provenance (capture context, not authority chain)
   - Consumer-without-authority (ApertureGeometryLike interface)
   - Domain-scoped vocabulary (no unnecessary 7M registration)

### Cross-Reference

Full inventory details in: `C1_ACOUSTICS_OBSERVATIONAL_SEMANTIC_INVENTORY.md`

---

## Related Governance Pattern Documents

The Acoustics/Observational domain has been classified as a **Governance Reference Pattern** based on C1 inventory findings.

Pattern documentation:
- `../../patterns/ACOUSTICS_GOVERNANCE_REFERENCE_PATTERN.md` — Why acoustics remained stable
- `../../patterns/OBSERVATIONAL_SEMANTICS_BOUNDARY_NOTES.md` — Observational boundary guidance
- `../../patterns/CONSUMER_WITHOUT_AUTHORITY_PATTERN.md` — Consumer-without-authority discipline

These documents capture governance pattern evidence, not constitutional authority.
