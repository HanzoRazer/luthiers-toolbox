# Morphology Harvest Storage Authority Check

**Date:** 2026-05-16  
**Sprint:** IBG Semantic Morphology Harvest Pass 1A-S  
**Status:** PENDING RESOLUTION  
**Governance:** Follow-up to MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md

---

## Purpose

This document tracks the canonical storage authority question for harvested morphology records.

`morphology_harvest/outputs/` is currently a **non-canonical staging area**. Before harvested records can be used as shared instrument-building data, governance must assign a canonical promotion target.

---

## Current State

| Location | Type | Status |
|----------|------|--------|
| `morphology_harvest/outputs/` | Generated staging | NON-CANONICAL |
| `data_registry/system/instruments/` | System registry | POTENTIAL TARGET |
| `instrument_specs.py` | Canonical dimensions | POTENTIAL TARGET |
| New `morphology_corpus/` | Dedicated location | POTENTIAL TARGET |

---

## Questions Requiring Resolution

### 1. Existing Data Authority

**Question:** Is there an existing `data_registry/` or instrument registry that should own harvested morphology records?

**Candidates:**
- `data_registry/system/instruments/body_templates.json` — Standard body templates
- `data_registry/` three-tier architecture (system/curated/user)
- `instrument_specs.py` BODY_DIMENSIONS dict

**Consideration:** The data_registry has a three-tier model (system → curated → user). Harvested records might fit the "curated" tier as validated instrument knowledge.

---

### 2. Existing Storage Convention

**Question:** Is there an existing instrument spec / blueprint standard storage convention?

**Known conventions:**
- `instrument_specs.py` — BodyDimensions dataclass, frozen, in-code
- `data_registry/system/` — JSON files, read-only system data
- `instrument_model_registry.json` — Model registry file

**Consideration:** Harvested records are more dynamic than frozen specs. They may need a mutable storage tier.

---

### 3. Staging vs Promotion

**Question:** Should harvest records be staged locally, then promoted into a shared canonical registry?

**Proposed workflow:**
```
PDF corpus
    ↓
morphology_harvest/outputs/  (staging, gitignored)
    ↓ [human review]
    ↓ [approval]
canonical promotion target  (committed, versioned)
```

**Consideration:** This matches the BOE human review authority model — harvest produces evidence, humans approve, approved records promote.

---

### 4. Documentation of Non-Canonical Status

**Question:** Should `morphology_harvest/outputs/` be explicitly documented as non-canonical generated output?

**Status:** DONE

The following files now document non-canonical status:
- `morphology_harvest/README.md` — Storage Authority Warning section
- `morphology_harvest/schema.py` — Module docstring warning
- `morphology_harvest/outputs/.gitignore` — Gitignored

---

### 5. Promotion Path

**Question:** What is the correct promotion path from harvested evidence → reusable instrument knowledge?

**Options:**

| Option | Promotion Target | Authority | Notes |
|--------|-----------------|-----------|-------|
| A | `data_registry/curated/instruments/` | data_registry | Fits three-tier model |
| B | `instrument_specs.py` extension | instrument_specs | Extends existing spec authority |
| C | New `morphology_corpus/` | New authority | Dedicated morphology storage |
| D | `tests/regression_corpus/` extension | Test infrastructure | Validation-oriented |

**Recommendation:** Option A (data_registry curated tier) aligns with existing architecture. However, this requires:
1. Creating `data_registry/curated/instruments/` structure
2. Defining promotion workflow
3. Governance approval

---

## Temporary Rules (Until Resolution)

Until governance explicitly assigns canonical storage authority:

1. **`morphology_harvest/outputs/`** remains non-canonical staging
2. **HarvestRecord** is a preservation/coordination artifact, not authoritative data
3. **No downstream system** should treat harvested records as canonical instrument specs
4. **Promotion** requires explicit governance approval

---

## Dependencies

This decision affects:

| System | Dependency |
|--------|------------|
| IBG | May consume harvested body data |
| Body Grid | May consume morphology descriptors |
| Vectorizer | May reference harvested dimensions |
| CAD generators | May use harvested instrument specs |
| RMOS validation | May validate against harvested data |
| Future adaptive systems | May train on harvested corpus |

---

## Resolution Timeline

| Phase | Action | Status |
|-------|--------|--------|
| 1A | Harvest implementation | COMPLETE |
| 1A-S | Storage authority documentation | COMPLETE |
| 1B | Phase 4 / calibration wiring | PENDING |
| 1C | Canonical storage decision | **PENDING** |
| 1D | Promotion workflow implementation | BLOCKED on 1C |

---

## Related Documents

- `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md`
- `docs/dev-orders/IBG_SEMANTIC_MORPHOLOGY_HARVEST_PASS_0B.md`
- `services/api/app/data_registry/README.md` (if exists)
- `services/api/app/instrument_geometry/instrument_specs.py`
