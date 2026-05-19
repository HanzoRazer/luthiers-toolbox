# Provenance Inventory C1

**Status:** C1 COLLECTION — NOT NORMALIZATION  
**Date:** 2026-05-18  
**Purpose:** Inventory provenance usage against canonical provenance types  
**Authority:** EVIDENCE ONLY — does not modify CANONICAL_PROVENANCE_MODEL

---

## Collection Methodology

```
C1 makes semantic collisions visible.
C1 does not make semantic decisions.
```

**Canonical provenance types (from CANONICAL_PROVENANCE_MODEL.md):**
- PROV_OBSERVATIONAL — what was observed, by whom, when
- PROV_DERIVATION — what was computed from what
- PROV_RUNTIME — what execution path was taken
- PROV_AUTHORITY — who ratified what decision
- PROV_TRANSFORMATION — what changed and how
- PROV_VALIDATION — what checks passed or failed
- PROV_REPLAY — what sequence can be replayed

---

## Provenance Entry Format

| Field | Description |
|-------|-------------|
| Usage Location | File path or document reference |
| Field Name | The field carrying provenance |
| Domain | Primary domain |
| Canonical Type | Mapped canonical type(s) |
| Type Classification | single-type / mixed-type / unclear |
| Evidence | Example values or usage |
| Notes | Interpretation notes |

---

## Inventoried Provenance Usages

### RuntimeResultBase.provenance

| Field | Value |
|-------|-------|
| Usage Location | `services/api/app/cam/runtime/runtime_results.py` |
| Field Name | `provenance: list[str]` |
| Domain | CAM |
| Canonical Type | PROV_RUNTIME + PROV_DERIVATION (mixed) |
| Type Classification | mixed-type |
| Evidence | List contains both execution stage names and computation chain entries |
| Notes | COL-2026-0006 — provenance semantic split; single field conflates multiple types |

---

### MeasurementArchive.observer_id

| Field | Value |
|-------|-------|
| Usage Location | `packages/client/src/types/acoustics/measurementArchive.ts` |
| Field Name | `observer_id` |
| Domain | Acoustics |
| Canonical Type | PROV_OBSERVATIONAL |
| Type Classification | single-type |
| Evidence | Records who made the observation |
| Notes | Clean mapping to canonical type |

---

### MeasurementArchive.device_id

| Field | Value |
|-------|-------|
| Usage Location | `packages/client/src/types/acoustics/measurementArchive.ts` |
| Field Name | `device_id` |
| Domain | Acoustics |
| Canonical Type | PROV_OBSERVATIONAL |
| Type Classification | single-type |
| Evidence | Records observation instrument |
| Notes | Clean mapping to canonical type |

---

### MeasurementArchive.capture_timestamp

| Field | Value |
|-------|-------|
| Usage Location | `packages/client/src/types/acoustics/measurementArchive.ts` |
| Field Name | `capture_timestamp` |
| Domain | Acoustics |
| Canonical Type | PROV_OBSERVATIONAL |
| Type Classification | single-type |
| Evidence | Records observation time |
| Notes | Clean mapping to canonical type |

---

### MeasurementArchive.environmental_conditions

| Field | Value |
|-------|-------|
| Usage Location | `packages/client/src/types/acoustics/measurementArchive.ts` |
| Field Name | `environmental_conditions` |
| Domain | Acoustics |
| Canonical Type | PROV_OBSERVATIONAL |
| Type Classification | single-type |
| Evidence | Records observation context |
| Notes | Clean mapping to canonical type |

---

### HarvestRecord.extracted_by

| Field | Value |
|-------|-------|
| Usage Location | `services/api/app/instrument_geometry/body/ibg/morphology_harvest/` |
| Field Name | `extracted_by` (inferred) |
| Domain | IBG |
| Canonical Type | PROV_OBSERVATIONAL |
| Type Classification | single-type |
| Evidence | Records extraction agent |
| Notes | Sandbox system; provenance supports evidence classification |

---

### HarvestRecord.upstream_sources

| Field | Value |
|-------|-------|
| Usage Location | `services/api/app/instrument_geometry/body/ibg/morphology_harvest/` |
| Field Name | `upstream_sources` |
| Domain | IBG |
| Canonical Type | PROV_DERIVATION + PROV_REPLAY (mixed) |
| Type Classification | mixed-type |
| Evidence | Records source data and potentially replay sequence |
| Notes | Sandbox system; mixed-type usage |

---

### OperationManifestV1.result_id references

| Field | Value |
|-------|-------|
| Usage Location | `services/api/app/cam/runtime/operation_manifest.py` |
| Field Name | `validation_result_id`, `geometry_result_id`, `plan_result_id`, `preview_result_id`, `export_result_id` |
| Domain | CAM |
| Canonical Type | PROV_RUNTIME |
| Type Classification | single-type |
| Evidence | ID references for execution traceability |
| Notes | Clean mapping; enables drill-down from manifest to results |

---

### RuntimeValidationResult.validation_gate

| Field | Value |
|-------|-------|
| Usage Location | `services/api/app/cam/runtime/runtime_results.py` |
| Field Name | `validation_gate` |
| Domain | CAM |
| Canonical Type | PROV_VALIDATION |
| Type Classification | single-type |
| Evidence | Records validation outcome (green/yellow/red) |
| Notes | Clean mapping to canonical type |

---

### Ratification Records

| Field | Value |
|-------|-------|
| Usage Location | `docs/governance/GOVERNANCE_RATIFICATION_MODEL.md` |
| Field Name | (record structure) |
| Domain | Governance |
| Canonical Type | PROV_AUTHORITY |
| Type Classification | single-type |
| Evidence | Records who ratified what decision |
| Notes | Clean mapping to canonical type |

---

## Pending Discovery

Provenance usages to inventory:

- [ ] RMOS workflow provenance
- [ ] MRP promotion provenance
- [ ] Blueprint vectorizer extraction provenance
- [ ] Wood species data source provenance
- [ ] DXF export provenance

---

## Provenance Statistics by Type Classification

| Classification | Count |
|----------------|-------|
| single-type | 8 |
| mixed-type | 2 |
| unclear | 0 |
| **Total** | **10** |

---

## Mixed-Type Usages (Candidates for Split)

| Field | Current Types | Split Recommendation |
|-------|--------------|---------------------|
| `RuntimeResultBase.provenance` | PROV_RUNTIME + PROV_DERIVATION | `action_provenance`, `derivation_chain` |
| `HarvestRecord.upstream_sources` | PROV_DERIVATION + PROV_REPLAY | `derivation_inputs`, `replay_sequence` |

**Note:** Split recommendations are candidates only — C1 does not implement.

---

## Related Documents

- `CANONICAL_PROVENANCE_MODEL.md` — canonical provenance types
- `SEMANTIC_COLLISION_LOG.md` — provenance collision (COL-2026-0006)
- `VOCABULARY_INVENTORY_C1.md` — per-term inventory

---

*Provenance Inventory C1 — Collection Phase*
