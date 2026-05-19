# Authority Inventory — Acoustics/Observational

**Sprint:** Acoustics/Observational  
**Terminal:** 4  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This inventory documents observed authority claims. It does not:
- Ratify authority assignments
- Resolve ownership conflicts
- Reassign ownership
- Enforce authority boundaries

Observed usage frequency does not imply ownership.

---

## Inventory Entries

### MeasurementArchive Authority

```
authority_claim: Canonical observational measurement archive format
declared_or_operational: declared
owning_subsystem: MeasurementArchive infrastructure (Dev Order 54)
source_location: packages/client/src/types/acoustics/measurementArchive.ts
truth_owned:
  - Schema structure for measurement archives
  - MeasurementSource enumeration
  - MeasurementMethod enumeration
  - Archive metadata contract
truth_must_not_own:
  - Calibration outputs
  - Predictions
  - Recommendations
  - Backend persistence
consumers: MeasurementArchivePreviewCard, aperture workspace export
upstream_dependencies: None (client-side only)
risk_level: low
notes: Dev Order 54 measurement archive is the primary declared observational archive scaffold. It is not automatically the canonical measurement authority. Declared non-goals in architecture doc.
```

### AcousticState Authority

```
authority_claim: Canonical acoustic state model
declared_or_operational: declared
owning_subsystem: Acoustics types (Dev Orders 15, 28)
source_location: packages/client/src/types/acoustics.ts
truth_owned:
  - AcousticConfidence vocabulary ('unknown' | 'low' | 'medium' | 'high')
  - AcousticStateSource vocabulary
  - Mandatory confidence/assumptions invariants
  - Estimate field naming (estimatedHelmholtzHz, etc.)
truth_must_not_own:
  - Calibration accuracy validation
  - Prediction computation
  - Measured truth (only measured source flag)
consumers: All acoustic state cards, estimate assumption summaries
upstream_dependencies: ApertureGeometryLike interface
risk_level: low
notes: Key invariant: "Confidence is mandatory (prevents overconfidence in estimates)". Well-documented.
```

### DiagnosticSnapshot Authority

```
authority_claim: Canonical diagnostic session snapshot format
declared_or_operational: declared
owning_subsystem: DiagnosticSnapshot infrastructure (Dev Orders 36, 37)
source_location: packages/client/src/utils/acoustics/diagnosticSnapshot.ts
truth_owned:
  - Snapshot schema version ('diagnostic-snapshot.v1')
  - Snapshot kind ('aperture-diagnostic-snapshot')
  - Section structure
  - observationalOnly invariant
truth_must_not_own:
  - Calibration authorization
  - Prediction validation
  - Backend persistence
consumers: DiagnosticSnapshotCard, export workflows, measurement archive references
upstream_dependencies: DiagnosticNarrativeSummary, CalibrationReadiness, ResidualCoherenceSummary
risk_level: low
notes: Explicitly observational only. Schema versioned for forward compatibility.
```

### observationalOnly Authority

```
authority_claim: Cross-domain observational invariant
declared_or_operational: operational (de facto shared)
owning_subsystem: Multiple — Acoustics, CAM Runtime, Governance
source_location:
  - packages/client/src/types/acoustics/measurementArchive.ts:144
  - services/api/app/cam/runtime/runtime_results.py:49
  - docs/governance/CANONICAL_PROVENANCE_MODEL.md:129
truth_owned:
  - Boolean invariant: data is observational
  - Prevents execution authorization claims
truth_must_not_own:
  - Immutability semantics (different concept)
consumers: Archive validation, runtime result validation, export gates
upstream_dependencies: Governance C0 provenance model
risk_level: medium
notes: Authority collision identified. Acoustics, CAM runtime, and governance all use this term. See SEMANTIC_COLLISION_LOG.
```

### Confidence Vocabulary Authority

```
authority_claim: Epistemic confidence vocabulary for acoustics
declared_or_operational: declared
owning_subsystem: AcousticState (acoustics domain)
source_location: packages/client/src/types/acoustics.ts:16
truth_owned:
  - AcousticConfidence type: 'unknown' | 'low' | 'medium' | 'high'
  - Semantic meaning of each level
truth_must_not_own:
  - Blueprint vectorizer confidence (numeric 0-1)
  - CAM validation gate semantics
  - Generic scoring
consumers: Acoustic state displays, estimate assumption summaries
upstream_dependencies: None
risk_level: medium
notes: Cross-domain collision. Blueprint vectorizer uses 'confidence' as numeric 0-1 score. Different semantic intent. Acoustics owns epistemic confidence; vectorizer owns detection confidence.
```

---

## De Facto Authority Claims (Operational)

### Aperture Workspace Export Authority

```
authority_claim: Export workflow for acoustic diagnostic data
declared_or_operational: operational
owning_subsystem: Aperture Workspace (ApertureWorkspace.vue, SnapshotExchangeSection.vue)
source_location: packages/client/src/views/art-studio/ApertureWorkspace.vue
truth_owned:
  - Export UI flow
  - Export format selection
  - Export validation gates
truth_must_not_own:
  - Schema definitions (owned by types)
  - Archive format (owned by MeasurementArchive)
consumers: End users
upstream_dependencies: DiagnosticSnapshot, MeasurementArchive
risk_level: low
notes: Operational authority over user-facing export experience. Does not define schemas.
```

---

## Summary

| Metric | Count |
|--------|-------|
| Authority claims inventoried | 6 |
| Declared authorities | 4 |
| Operational (de facto) authorities | 2 |
| Authority conflicts | 2 (observationalOnly, confidence) |
| Critical risk claims | 0 |

---

## Notes

1. Authority is well-separated in acoustics domain. Each subsystem has clear boundaries documented in dev orders.

2. Two authority collisions identified:
   - `observationalOnly` — shared across acoustics, CAM runtime, governance
   - `confidence` — AcousticConfidence (enum) vs blueprint confidence (numeric)

3. All acoustic authorities explicitly declare non-goals (calibration, prediction, persistence), reducing authority creep risk.
