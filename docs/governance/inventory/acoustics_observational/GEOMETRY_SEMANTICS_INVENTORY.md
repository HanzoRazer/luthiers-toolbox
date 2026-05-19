# Geometry Semantics Inventory — Acoustics/Observational

**Sprint:** Acoustics/Observational  
**Terminal:** 4  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This inventory documents observed geometry semantic usage. It does not:
- Reassign geometry authority
- Resolve domain ambiguity
- Normalize geometry vocabulary
- Enforce mutation rights

Geometry/morphology/topology/visualization distinctions are preserved for later reconciliation.

---

## Applicability Note

**Applicable:** Partial — acoustics consumes geometry but does not own it.

**Scope:** This inventory documents geometry semantics as consumed by the acoustics domain for acoustic calculations. Canonical geometry authority belongs to Terminal 3 (Geometry/Morphology/Topology).

---

## Inventory Entries

### ApertureGeometryLike

```
geometry_concept: ApertureGeometryLike
local_meaning: Interface for geometry data consumed by acoustic state
domain: geometry (consumer, not owner)
owner_claim: Declared consumer interface in acoustics types
mutation_rights: None — read-only consumption
derivation_rules: Populated from canonical ApertureGeometry sources
source_locations:
  - packages/client/src/types/acoustics.ts:32-41
consumer_systems: AcousticState, acoustic estimate calculations
authority_risk: Low — explicitly decoupled interface, not canonical geometry
notes: "Decoupled from Vue component exports to keep domain types clean." Consumer interface only.
```

### MeasurementArchiveGeometrySummary

```
geometry_concept: MeasurementArchiveGeometrySummary
local_meaning: Lightweight geometry summary for archive context
domain: geometry (consumer, not owner)
owner_claim: MeasurementArchive (summary only)
mutation_rights: None — snapshot at archive creation time
derivation_rules: Derived from full geometry at archive creation
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:16-21
consumer_systems: MeasurementArchiveRecord, archive export
authority_risk: Low — explicitly "avoids full geometry payload duplication"
notes: Fields: apertureType, areaMm2, equivalentDiameterMm, paRatioMmInv. Subset of full geometry.
```

### apertureGeometry

```
geometry_concept: apertureGeometry
local_meaning: Reference to aperture geometry associated with acoustic state
domain: geometry (reference, not owner)
owner_claim: None — field holds reference to canonical geometry
mutation_rights: Reference only — cannot mutate
derivation_rules: Passed in from canonical geometry sources
source_locations:
  - packages/client/src/types/acoustics.ts:71
consumer_systems: AcousticState, estimate calculations
authority_risk: Low — "Associated aperture geometry (reference, not merged)"
notes: Key invariant: "Geometry remains separate (ApertureGeometry is not merged into this)"
```

### areaMm2

```
geometry_concept: areaMm2
local_meaning: Aperture area in square millimeters
domain: geometry (derived value)
owner_claim: Canonical geometry (aperture_geometry module)
mutation_rights: Computed from geometry — not directly mutable
derivation_rules: Computed from aperture shape
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:18
  - ApertureGeometryLike.area_mm2
consumer_systems: Acoustic calculations, P:A ratio
authority_risk: None — standard derived geometric property
notes: Used for Helmholtz frequency calculations.
```

### paRatioMmInv

```
geometry_concept: paRatioMmInv
local_meaning: Perimeter-to-area ratio in mm⁻¹
domain: geometry (derived value)
owner_claim: Canonical geometry
mutation_rights: Computed from geometry — not directly mutable
derivation_rules: P:A = perimeter / area
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:20
  - ApertureGeometryLike.pa_ratio_mm_inv
consumer_systems: Acoustic efficiency assessment (Williams threshold: P:A > 0.10 mm⁻¹)
authority_risk: None — standard derived geometric property
notes: Key acoustic metric for spiral soundhole efficiency.
```

---

## Geometry Consumption Pattern

Acoustics domain follows a consistent geometry consumption pattern:

```
Canonical Geometry (Terminal 3 authority)
    ↓ (passed as reference)
ApertureGeometryLike (consumer interface)
    ↓ (snapshot for archival)
MeasurementArchiveGeometrySummary (archived subset)
```

**Key rule:** Acoustics never mutates or defines canonical geometry. It only consumes.

---

## Summary

| Metric | Count |
|--------|-------|
| Geometry concepts inventoried | 5 |
| Domain: geometry (consumer) | 3 |
| Domain: geometry (derived values) | 2 |
| Domain: morphology | 0 |
| Domain: topology | 0 |
| Domain: visualization | 0 |
| Authority risks | 0 |

---

## Notes

1. Acoustics is a clean geometry consumer. No authority claims over canonical geometry.

2. Explicit decoupling in code comments: "Geometry remains separate" and "Decoupled from Vue component exports."

3. Terminal 3 should inventory canonical geometry authority. This inventory only documents consumption.
