# Semantic Collision Log

**Phase:** C1 — Collection  
**Date:** 2026-05-18  
**Status:** Evidence collection (no decisions made)

---

## Purpose

This document logs semantic collisions discovered across sprint workstreams. Each entry records the collision without resolving it. Resolution happens in C2/C3 phases.

---

## Collision Categories

| Category | Meaning |
|----------|---------|
| `SAME_TERM_DIFFERENT_MEANING` | Same string, different semantics |
| `SAME_CONCEPT_DIFFERENT_TERM` | Same semantics, different strings |
| `DUPLICATE_DEFINITION` | Same term defined in multiple locations |
| `AUTHORITY_OVERLAP` | Multiple systems claim same semantic authority |
| `LIFECYCLE_AXIS_COLLISION` | Term used across incompatible lifecycle axes |

---

## Logged Collisions

### COL-001: `unsupported` vs `UNSUPPORTED_RUNTIME`

| Field | Value |
|-------|-------|
| Category | `SAME_CONCEPT_DIFFERENT_TERM` |
| Term A | `unsupported` |
| Domain A | CAM Runtime |
| Source A | `runtime_results.py:44` |
| Meaning A | Result status indicating operation not supported |
| Term B | `UNSUPPORTED_RUNTIME` |
| Domain B | Topology |
| Source B | `runtime_support.py:29` |
| Meaning B | Topology runtime support classification |
| Semantic equivalence | Yes — both mean "cannot execute" |
| Reconciliation candidate | Map CAM → Topology vocabulary |

---

### COL-002: `validation_only` Semantic Split

| Field | Value |
|-------|-------|
| Category | `SAME_TERM_DIFFERENT_MEANING` |
| Term | `validation_only` |
| Domain A | CAM Translator |
| Source A | `capabilities.py:37` |
| Meaning A | Translator can validate but cannot execute |
| Domain B | Lifecycle Registry |
| Source B | `lifecycle_registry.json` |
| Meaning B | Execution mode for reporting only |
| Semantic equivalence | Partial — related but different contexts |
| Reconciliation candidate | Prefix or domain-qualify |

---

### COL-003: `experimental` Cross-Domain Usage

| Field | Value |
|-------|-------|
| Category | `SAME_TERM_DIFFERENT_MEANING` |
| Term | `experimental` |
| Locations | TranslatorMaturity, ExecutionState, Governance lifecycle |
| CAM meaning | Under development, may change |
| Governance meaning | Not yet governed, subject to change |
| Semantic equivalence | High — similar intent |
| Reconciliation candidate | Consume governance vocabulary |

---

### COL-004: `deprecated` Cross-Domain Usage

| Field | Value |
|-------|-------|
| Category | `SAME_TERM_DIFFERENT_MEANING` |
| Term | `deprecated` |
| Locations | TranslatorMaturity, ExecutionState, Governance lifecycle |
| CAM meaning | Scheduled for removal |
| Governance meaning | Scheduled for removal |
| Semantic equivalence | Yes — identical |
| Reconciliation candidate | Consume governance vocabulary |

---

### COL-005: `CamGate` Duplicate Definition

| Field | Value |
|-------|-------|
| Category | `DUPLICATE_DEFINITION` |
| Term | `CamGate` (enum) |
| Values | `green`, `yellow`, `red` |
| Location 1 | `nut_slot_cam.py:36` |
| Location 2 | `fret_slots_router.py:36` |
| Location 3 | `drilling_preview_router.py:35` |
| Values identical | Yes |
| Reconciliation candidate | Consolidate to single enum |

---

### COL-006: `MaterialType` Namespace Collision

| Field | Value |
|-------|-------|
| Category | `DUPLICATE_DEFINITION` |
| Term | `MaterialType` (enum) |
| Location 1 | `rosette/pattern_schemas.py` — MAPLE, ROSEWOOD, EBONY, etc. |
| Location 2 | `cam/neck/config.py` — SOFTWOOD, HARDWOOD, EXOTIC |
| Location 3 | `rosette/cnc/cnc_materials.py` — HARDWOOD, SOFTWOOD, MDF, COMPOSITE |
| Values identical | No — completely different |
| Reconciliation candidate | Prefix by domain |

---

### COL-007: `experimental`/`deprecated` in Same Enum File

| Field | Value |
|-------|-------|
| Category | `DUPLICATE_DEFINITION` |
| Terms | `experimental`, `deprecated` |
| Location | `capabilities.py` |
| Enum 1 | `TranslatorMaturity` |
| Enum 2 | `ExecutionState` |
| Same file | Yes |
| Reconciliation candidate | Differentiate maturity vs execution semantics |

---

### COL-008: `green/yellow/red` vs `blocking/major/warning`

| Field | Value |
|-------|-------|
| Category | `SAME_CONCEPT_DIFFERENT_TERM` |
| Concept | Validation/execution severity |
| CAM terms | `green`, `yellow`, `red` |
| CAM source | `operation_manifest.py:61` |
| Topology terms | `blocking`, `major`, `warning` |
| Topology source | `lifecycle_registry.json` |
| Semantic equivalence | Partial — similar intent, different metaphor |
| Reconciliation candidate | Document equivalence mapping |

---

### COL-009: `governed` Semantic Overlap

| Field | Value |
|-------|-------|
| Category | `SAME_TERM_DIFFERENT_MEANING` |
| Term | `governed` |
| CAM meaning | Translator is production-ready |
| Governance meaning | Subject to governance constraints |
| Source CAM | `capabilities.py:31` |
| Source Governance | `lifecycle_registry.json` |
| Semantic equivalence | Partial — CAM implies "approved", Governance implies "under rules" |
| Reconciliation candidate | Clarify in vocabulary |

---

### COL-010: `placeholder` Overloading

| Field | Value |
|-------|-------|
| Category | `SAME_TERM_DIFFERENT_MEANING` |
| Term | `placeholder` |
| Usage 1 | Result status — stub result |
| Usage 2 | TranslatorMaturity — registered not implemented |
| Usage 3 | Planning/preview/export stage — not implemented |
| Semantic equivalence | Yes — all mean "not yet real" |
| Reconciliation candidate | Acceptable overloading (same meaning) |

---

### COL-011: `candidate` Lifecycle Term

| Field | Value |
|-------|-------|
| Category | `SAME_TERM_DIFFERENT_MEANING` |
| Term | `candidate` |
| CAM meaning | Feature complete, under validation |
| Governance meaning | Proposed term not yet ratified |
| Source CAM | `capabilities.py:30` |
| Source Governance | `SEMANTIC_FREEZE_PROTOCOL.md` |
| Semantic equivalence | Partial — both mean "proposed but not final" |
| Reconciliation candidate | Consume governance vocabulary |

---

---

### COL-012: `unsupported` vs `UNSUPPORTED_RUNTIME` (Geometry/Topology)

| Field | Value |
|-------|-------|
| Category | `SAME_CONCEPT_DIFFERENT_TERM` |
| Term A | `unsupported` |
| Domain A | CadSemantics (RuntimeSupport enum) |
| Source A | `cad_semantics.py:77` |
| Meaning A | Not supported in CAD translation |
| Term B | `UNSUPPORTED_RUNTIME` |
| Domain B | TopologyBuilder |
| Source B | `runtime_support.py:29` |
| Meaning B | Cannot generate topology |
| Semantic equivalence | Yes — both mean "cannot process" |
| Reconciliation candidate | Align casing and terminology |

---

### COL-013: `unknown` Fallback Proliferation

| Field | Value |
|-------|-------|
| Category | `DUPLICATE_DEFINITION` |
| Term | `unknown` |
| Locations | BodyCategory, GeometryType, CurvatureClass, BodyMorphologyClass, HarvestSource |
| Values identical | Yes — all are fallback/default values |
| Semantic equivalence | Yes — standard fallback pattern |
| Reconciliation candidate | Accept as valid pattern |

---

### COL-014: IBG Zone Y-Range Authority Gap

| Field | Value |
|-------|-------|
| Category | `AUTHORITY_OVERLAP` |
| Concept | Body zone boundaries |
| Location | `zones.py:69-338` |
| Issue | Hardcoded Y-ranges becoming de-facto authority without governance |
| Example | `lower_bout: (0.08, 0.40)`, `waist: (0.35, 0.55)` |
| Semantic equivalence | N/A — implicit authority |
| Reconciliation candidate | Register zone boundaries as governed constants |

---

---

### COL-015: MeasurementSource/Method Frontend Duplication

| Field | Value |
|-------|-------|
| Category | `DUPLICATE_DEFINITION` |
| Terms | `MeasurementSource`, `MeasurementMethod` |
| Location 1 | `measurementArchive.ts:36-52` |
| Location 2 | `measurements.ts:11-25` |
| Values identical | Partial — similar but not identical |
| Semantic equivalence | Yes — same concept |
| Reconciliation candidate | Consolidate to single definition |

---

### COL-016: RiskStatus vs CamGate Vocabulary

| Field | Value |
|-------|-------|
| Category | `SAME_CONCEPT_DIFFERENT_TERM` |
| Term A | `GREEN/YELLOW/RED/ERROR` |
| Domain A | RMOS (RiskStatus) |
| Source A | `engines/base.py:14` |
| Term B | `green/yellow/red` |
| Domain B | CAM (CamGate) |
| Source B | `operation_manifest.py:61` |
| Semantic equivalence | High — similar traffic-light pattern |
| Reconciliation candidate | Document as equivalent patterns |

---

### COL-017: WoodSpecies Proliferation

| Field | Value |
|-------|-------|
| Category | `DUPLICATE_DEFINITION` |
| Term | `WoodSpecies` / `MaterialType` |
| Location 1 | `rmos/context.py:24` — 12 species |
| Location 2 | `rosette/pattern_schemas.py` — Different set |
| Location 3 | `cam/neck/config.py` — SOFTWOOD/HARDWOOD/EXOTIC |
| Location 4 | `rosette/cnc/cnc_materials.py` — Different |
| Values identical | No — different species lists |
| Reconciliation candidate | Establish authoritative wood vocabulary |

---

## Collision Statistics

| Category | Count |
|----------|-------|
| SAME_TERM_DIFFERENT_MEANING | 5 |
| SAME_CONCEPT_DIFFERENT_TERM | 4 |
| DUPLICATE_DEFINITION | 7 |
| AUTHORITY_OVERLAP | 1 |
| Total | 17 |

---

## Cross-Reference: Affected Files

| File | Collisions |
|------|------------|
| `capabilities.py` | COL-003, COL-004, COL-007, COL-009, COL-011 |
| `runtime_results.py` | COL-001, COL-010 |
| `operation_manifest.py` | COL-008 |
| `lifecycle_registry.json` | COL-001, COL-002, COL-008 |
| `nut_slot_cam.py` | COL-005 |
| `fret_slots_router.py` | COL-005 |
| `drilling_preview_router.py` | COL-005 |
| `pattern_schemas.py` | COL-006 |
| `neck/config.py` | COL-006 |
| `cnc_materials.py` | COL-006 |
| `cad_semantics.py` | COL-012, COL-013 |
| `runtime_support.py` | COL-012 |
| `zones.py` | COL-013, COL-014 |
| `primitives.py` | COL-013 |
| `variant_grammar.py` | COL-013 |
| `morphology_harvest/schema.py` | COL-013 |
| `measurementArchive.ts` | COL-015 |
| `measurements.ts` | COL-015 |
| `rmos/engines/base.py` | COL-016 |
| `rmos/context.py` | COL-017 |

---

## C1 Status

**Logged:** 17 collisions  
**Decisions made:** None  
**Next phase:** C2 reconciliation
