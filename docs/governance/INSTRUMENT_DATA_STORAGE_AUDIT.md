# Instrument Data Storage Governance Audit

**Date:** 2026-05-15  
**Status:** AUDIT COMPLETE  
**Trigger:** IBG Semantic Morphology Harvest work revealed topology concerns  
**Scope:** All lutherie instruments, geometric/dimensional/morphological data  
**Authority:** Tier 1 Governance Audit

---

## 1. Executive Summary

This audit reveals **significant fragmentation** in instrument knowledge storage across the repository. At least **7 distinct storage locations** contain overlapping instrument data with no formally designated canonical authority.

**Critical Finding:** The repository has evolved multiple "sources of truth" for instrument data without explicit governance arbitration. Each location claims some form of authority, but ownership boundaries are implicit rather than governed.

**Key Risk:** Morphology harvest outputs at risk of becoming accidental canonical storage, fragmenting instrument knowledge further.

**Recommended Resolution:** Designate `data_registry/system/instruments/` as canonical authority with promotion pipeline from staging locations.

---

## 2. Current Storage Topology

### 2.1 Storage Location Inventory

| # | Location | Data Type | Record Count | Authority Claim |
|---|----------|-----------|--------------|-----------------|
| 1 | `instrument_specs.py` | Body dimensions, features | 18 | "Canonical Body Dimension Reference" |
| 2 | `instrument_model_registry.json` | Full model registry | 31 | Master registry with assets |
| 3 | `data_registry/system/instruments/body_templates.json` | Body templates | 7 | System tier read-only |
| 4 | `body/outlines.py` + `body_outlines.json` | Outline coordinates | 15 | DXF extraction truth |
| 5 | `specs/*.json` | Detailed instrument specs | 19 | Per-instrument authority |
| 6 | `models/*.json` | Model configurations | 14 | AI vision extractions |
| 7 | `morphology_harvest/outputs/` | Harvest staging | 0 (staging) | **NON-CANONICAL** |
| 8 | `guitars/*.py` | Guitar module configs | 19 | MODEL_SPECS per module |
| 9 | `body_grid/` schemas | Morphology descriptors | N/A (schema) | Body Grid authority |

### 2.2 Storage Topology Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INSTRUMENT DATA TOPOLOGY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────┐     ┌─────────────────────┐                       │
│   │  instrument_specs.py │     │ instrument_model_   │                       │
│   │  18 body dimensions  │     │ registry.json       │                       │
│   │  Claims: "canonical" │     │ 31 models, assets   │                       │
│   └──────────┬──────────┘     └──────────┬──────────┘                       │
│              │                           │                                   │
│              │         FRAGMENTATION     │                                   │
│              ▼              ZONE         ▼                                   │
│   ┌──────────────────────────────────────────────────┐                      │
│   │                                                   │                      │
│   │   specs/*.json   models/*.json   guitars/*.py    │                      │
│   │      (19)            (14)           (19)         │                      │
│   │                                                   │                      │
│   └──────────────────────────────────────────────────┘                      │
│              │                                                               │
│              ▼                                                               │
│   ┌─────────────────────┐     ┌─────────────────────┐                       │
│   │  body_outlines.json │     │  data_registry/     │                       │
│   │  detailed_outlines  │     │  body_templates.json│                       │
│   │  15 outlines        │     │  7 templates        │                       │
│   └─────────────────────┘     └─────────────────────┘                       │
│                                                                              │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                      │
│                         STAGING ZONE                                         │
│   ┌─────────────────────┐                                                   │
│   │ morphology_harvest/ │  ◄── Risk: Could become accidental canonical      │
│   │ outputs/            │                                                    │
│   │ (explicitly staging)│                                                    │
│   └─────────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Authority Classification Table

| Path | Data Type | Authority Level | Canonical? | Duplication Risk | Recommendation |
|------|-----------|-----------------|------------|------------------|----------------|
| `instrument_specs.py` | Body dimensions | Self-declared canonical | IMPLICIT YES | HIGH - overlaps with registry | PROMOTE to data_registry |
| `instrument_model_registry.json` | Full model metadata | De facto master | IMPLICIT YES | HIGH - dimensions conflict | DESIGNATE as model registry |
| `data_registry/system/instruments/body_templates.json` | Body templates | System tier | POTENTIAL CANONICAL | MEDIUM | EXTEND as canonical target |
| `body/outlines.py` | Outline coordinates | Outline authority | YES for outlines | LOW | RETAIN as outline authority |
| `specs/*.json` | Detailed specs | Per-instrument | NO - derived | MEDIUM | GENERATE from canonical |
| `models/*.json` | AI extractions | Staging | NO | HIGH | REVIEW then promote |
| `morphology_harvest/outputs/` | Harvest staging | Non-canonical | **NO** | CRITICAL | ENFORCE non-canonical |
| `guitars/*.py` | Module configs | Legacy | NO | HIGH | DEPRECATE duplicates |
| `body_grid/` schemas | Morphology | Schema authority | YES for schema | LOW | RETAIN |

---

## 4. Duplication / Fragmentation Findings

### 4.1 Duplicate Dimension Sources

**Example: Stratocaster body dimensions appear in:**

| Source | body_length_mm | lower_bout_width_mm | waist_width_mm |
|--------|----------------|---------------------|----------------|
| `instrument_specs.py` | 406 | 408 | 308 |
| `body_templates.json` | 396 | 318 | - |
| `body_outlines.py` metadata | 458.8 (height) | 322.3 (width) | - |

**Finding:** Three different dimension sets for the same instrument. Values conflict due to different measurement conventions (body outline bbox vs. bout width).

### 4.2 Schema Fragmentation

| System | Term Used | Canonical Term | Drift Type |
|--------|-----------|----------------|------------|
| `INSTRUMENT_SPECS` | `lower_bout_mm` | `lower_bout_width_mm` | Missing suffix |
| `GuitarDimensions` | `body_width_mm` | `lower_bout_width_mm` | Semantic alias |
| `body_outlines.py` | `width_mm`, `height_mm` | N/A | Different schema |

**Finding:** Terminology drift across systems. Harvest schema already includes normalization mappings (evidence of prior awareness).

### 4.3 Duplicate Model Definitions

| Instrument | instrument_specs.py | instrument_model_registry.json | specs/*.json | models/*.json |
|------------|---------------------|--------------------------------|--------------|---------------|
| stratocaster | YES | YES | YES | NO |
| les_paul | YES | YES | YES | NO |
| cuatro | YES | YES | NO | YES (2 files) |
| flying_v | YES | YES | YES | YES |
| benedetto_17 | YES | YES | NO | YES |

**Finding:** Same instruments defined in multiple locations with different levels of detail.

### 4.4 Orphaned / Conflicting Data

1. **`models/flying_v_1958.json`** - Schema mismatch with `loader.py` (REPO_DATA_AUDIT finding)
2. **Cuatro variants** - Two separate files without consolidation
3. **Phantom assets** - 8 referenced assets that don't exist on disk

---

## 5. Existing Unification Efforts

### 5.1 Prior Awareness (Evidence Found)

| Document | Finding | Status |
|----------|---------|--------|
| `MORPHOLOGY_HARVEST_STORAGE_AUTHORITY.md` | Identifies storage authority question | PENDING RESOLUTION |
| `MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` | "Instrument spec registry: fragmented" | IDENTIFIED |
| `REPO_DATA_AUDIT.md` GEN-5 | "No single source of truth" | NOT STARTED |
| `schema.py` TERM_NORMALIZATIONS | Terminology drift mappings | PARTIAL MITIGATION |

### 5.2 GEN-5 Consolidation Phase

The `REPO_DATA_AUDIT.md` explicitly identifies:

```
GEN-5: Consolidate spec stubs + registry
Status: NOT STARTED
- 19 MODEL_SPECS vs 31 registry entries
- No single source of truth
```

**Finding:** Unification was planned but never executed. GEN-5 remains incomplete.

### 5.3 data_registry Three-Tier Architecture

The `data_registry/` implements a three-tier model:

```
system/   — Read-only, shipped with product
curated/  — (Does not exist) — Validated data tier
user/     — Per-tenant, mutable
```

**Finding:** The `curated/` tier mentioned in MORPHOLOGY_HARVEST_STORAGE_AUTHORITY.md does not exist. This was the proposed promotion target.

---

## 6. Governance Risks

### 6.1 Immediate Risks

| Risk | Severity | Description |
|------|----------|-------------|
| Harvest output drift | CRITICAL | `morphology_harvest/outputs/` becoming accidental canonical |
| Dimension conflicts | HIGH | Consumers get different values from different sources |
| Schema fragmentation | HIGH | Terminology drift causes integration failures |
| Phantom assets | MEDIUM | References to non-existent files cause runtime errors |

### 6.2 Long-Term Risks

| Risk | Severity | Description |
|------|----------|-------------|
| Parallel ontology drift | CRITICAL | Multiple "truths" fragmenting as systems evolve |
| GEN-5 stall | HIGH | Consolidation never completed, fragmentation worsens |
| Consumer confusion | MEDIUM | Developers don't know which source to use |

---

## 7. Recommended Canonical Authority Model

### 7.1 Proposed Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CANONICAL AUTHORITY MODEL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   TIER 1: SYSTEM CANONICAL (read-only, governed)                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  data_registry/system/instruments/                                   │   │
│   │  ├── body_templates.json      ← Body dimensions & construction      │   │
│   │  ├── body_outlines.json       ← Canonical outline coordinates       │   │
│   │  ├── neck_profiles.json       ← (existing)                          │   │
│   │  └── model_registry.json      ← Master model metadata               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              ▲                                               │
│                              │ PROMOTION (human review)                      │
│                              │                                               │
│   TIER 2: CURATED STAGING (reviewed, pending promotion)                     │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  data_registry/curated/instruments/                                  │   │
│   │  ├── harvested/           ← Harvest outputs after review            │   │
│   │  └── corrections/         ← BOE corrections                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              ▲                                               │
│                              │ REVIEW (BOE/human)                            │
│                              │                                               │
│   TIER 3: GENERATED STAGING (non-canonical)                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  morphology_harvest/outputs/     ← Harvest staging (gitignored)     │   │
│   │  vectorizer output/              ← Extraction staging               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Authority Assignment

| Data Type | Canonical Location | Owner System |
|-----------|-------------------|--------------|
| Body dimensions | `data_registry/system/instruments/body_templates.json` | data_registry |
| Body outlines | `data_registry/system/instruments/body_outlines.json` | data_registry |
| Model metadata | `data_registry/system/instruments/model_registry.json` | data_registry |
| Detailed specs | GENERATED from canonical on demand | spec_generator |
| Morphology descriptors | `body_grid/` schemas | body_grid |
| Harvest staging | `morphology_harvest/outputs/` | **NON-CANONICAL** |

---

## 8. Proposed Promotion / Staging Flow

### 8.1 Promotion Pipeline

```
PDF/Blueprint Source
        │
        ▼
┌───────────────────────┐
│   Vectorizer/Phase 4  │  ← Extraction
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  morphology_harvest/  │  ← STAGING (gitignored)
│  outputs/             │
└───────────┬───────────┘
            │
            ▼ [Human Review]
┌───────────────────────┐
│  data_registry/       │  ← CURATED (reviewed)
│  curated/instruments/ │
└───────────┬───────────┘
            │
            ▼ [Governance Approval]
┌───────────────────────┐
│  data_registry/       │  ← CANONICAL (committed)
│  system/instruments/  │
└───────────────────────┘
```

### 8.2 Promotion Rules

1. **Harvest → Curated**: Requires human review via BOE or review manifest
2. **Curated → System**: Requires governance approval (PR review)
3. **System → Consumers**: Read-only, no runtime modification
4. **Staging locations**: Always gitignored, never canonical

---

## 9. Migration Safety Recommendations

### 9.1 Do NOT Do (Prohibited)

| Action | Reason |
|--------|--------|
| Delete `instrument_specs.py` | Breaks 50+ consumers |
| Merge all data immediately | Risks data loss |
| Make harvest outputs canonical | Violates governance |
| Remove `instrument_model_registry.json` | Breaks frontend |

### 9.2 Safe Migration Sequence

**Phase 1: Establish Canonical Target (no code changes)**
1. Create `data_registry/system/instruments/model_registry.json`
2. Create `data_registry/curated/instruments/` structure
3. Document authority in governance

**Phase 2: Implement Adapters (backwards compatible)**
1. Add `instrument_specs.py` → data_registry adapter
2. Add `instrument_model_registry.json` → data_registry adapter
3. Existing consumers continue working

**Phase 3: Migrate Data (verified)**
1. Consolidate dimensions into canonical location
2. Resolve conflicts with human review
3. Verify all consumers still work

**Phase 4: Deprecate Legacy (gradual)**
1. Add deprecation warnings to legacy accessors
2. Update consumers to use canonical
3. Archive legacy after transition complete

---

## 10. Deferred Questions Requiring Governance Decision

### 10.1 Authority Questions

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Should `data_registry/` be the canonical authority? | Yes / New location / Multiple authorities | **Yes** - extends existing architecture |
| 2 | Should `instrument_model_registry.json` merge into data_registry? | Merge / Keep separate / Deprecate | **Merge** - consolidates authority |
| 3 | Who approves promotion from curated → system? | Automated / PR review / Explicit approval | **PR review** - governance oversight |

### 10.2 Schema Questions

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 4 | Which dimension schema is canonical? | `BodyDimensions` / `GuitarDimensions` / New unified | **BodyDimensions** - already declared canonical |
| 5 | How to handle terminology drift? | Normalize on read / Normalize on write / Strict schema | **Normalize on write** - single source |
| 6 | Should outline data live with dimensions? | Same file / Separate files / Separate directory | **Separate file** - different update cadence |

### 10.3 Process Questions

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 7 | When is GEN-5 consolidation executed? | Now / After harvest / Never | **After harvest** - harvest reveals needs |
| 8 | Who owns the promotion workflow? | IBG / MRP / Governance team | **MRP** - morphology platform authority |
| 9 | How are conflicts resolved? | Human review / Automated / Reject | **Human review** - via BOE |

---

## Appendix A: System Ownership Matrix

| System | Owns | Should Reuse | Should Not Duplicate |
|--------|------|--------------|----------------------|
| data_registry | Canonical instrument data | - | Extraction logic |
| instrument_specs.py | LEGACY body dimensions | data_registry (future) | Model metadata |
| instrument_model_registry | Model metadata | data_registry (future) | Body dimensions |
| body_outlines | Outline coordinates | data_registry (future) | Dimensions |
| morphology_harvest | Staging only | Phase 4, calibration | Extraction, canonical data |
| body_grid | Morphology schemas | - | Data storage |
| specs/*.json | Derived details | Canonical source | Independent data |

---

## Appendix B: Terminology Note

**Data Promotion Tiers vs. Governance Authority Tiers**

This document uses "Tier 1/2/3" to describe data promotion stages:

| Term | Meaning (Data Promotion) |
|------|--------------------------|
| Tier 1 | Canonical (governed, ratified data) |
| Tier 2 | Curated (reviewed, pending promotion) |
| Tier 3 | Staging (non-canonical evidence) |

This is distinct from `GOVERNANCE_AUTHORITY_HIERARCHY.md` which uses "Tier 1/2/3" for governance authority strata:

| Term | Meaning (Governance Authority) |
|------|-------------------------------|
| Tier 1 | Structural Invariants |
| Tier 2 | Domain Governance |
| Tier 3 | Operational Policies |

These are separate semantic systems. Future revisions may rename data promotion tiers to "stages" for disambiguation.

---

## Appendix C: Related Documents

### Governance Stack Documents

- `docs/governance/ontology/INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` — Field semantic definitions
- `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md` — Tier 3→2 review governance
- `docs/governance/ontology/ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md` — Governance-state visibility
- `docs/governance/ontology/AUTHORITY_BOUNDARY_REGISTRY_V1.md` — Ownership boundaries

### Related Audit Documents

- `docs/governance/MORPHOLOGY_HARVEST_STORAGE_AUTHORITY.md` — Storage authority tracking
- `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` — Collision audit
- `docs/REPO_DATA_AUDIT.md` — Repository data audit (GEN-5)
- `docs/governance/REPOSITORY_REMEDIATION_GOVERNANCE_METHODOLOGY.md` — Methodology
- `data_registry/README.md` — Three-tier architecture

---

## Appendix C: Validation Commands

```bash
# List all instrument data files
find services/api/app -name "*instrument*" -o -name "*spec*" | grep -E "\.(json|py)$"

# Count records in each source
python -c "from app.instrument_geometry.instrument_specs import BODY_DIMENSIONS; print(len(BODY_DIMENSIONS))"

# Check for terminology drift
grep -r "lower_bout_mm\|lower_bout_width_mm" services/api/app/

# Verify harvest outputs are gitignored
cat services/api/app/instrument_geometry/body/ibg/morphology_harvest/outputs/.gitignore
```

---

*Instrument Data Storage Governance Audit — 2026-05-15*
