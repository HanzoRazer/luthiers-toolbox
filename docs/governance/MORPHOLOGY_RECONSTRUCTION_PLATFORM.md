# Morphology Reconstruction Platform (MRP)

**Status:** ACTIVE GOVERNANCE FRAMEWORK  
**Effective:** 2026-05-11

---

## Purpose

Govern the evolution of the Blueprint Reader + IBG ecosystem from rendered/vectorized DXF generation into instrument-aware CAD reconstruction and manufacturing intelligence.

---

## Core Principle

```
Protect the production MVP while evolving morphology intelligence in isolated, governed layers.

The MVP must never be destabilized by experimental learning systems.
```

---

## Platform Topology

```
Image/PDF
  → Blueprint Reader MVP
  → partial DXF geometry
  → IBG Morphology Reconstruction
  → Solved Body Model
  → Export Object
  → Translators
  → STEP / DXF / SVG / CAM
```

---

## Canonical Layer Definitions

| Layer | Responsibility | Governance |
|-------|----------------|------------|
| Blueprint Reader MVP | Deterministic extraction | PROTECTED |
| DXF Translator Layer | Serialization compatibility | STABILIZED |
| IBG Morphology Layer | Shape intelligence | EVOLUTIONARY |
| BOE | Human correction/editor | AUTHORITATIVE |
| Export Object | Canonical manufacturing representation | DXF-AGNOSTIC |
| Translators | Serialization targets | ISOLATED |
| CAM/Postprocessors | Machine execution | DOWNSTREAM |

---

## Protected Systems

See: `BLUEPRINT_READER_PROTECTION_RULES.md`

| System | Protection Level |
|--------|------------------|
| Blueprint Reader MVP | LOCKED |
| restored_baseline mode | LOCKED |
| DXF compliance layer | LOCKED |
| IBG math engine | LOCKED |
| Sevy/Mottola calculations | LOCKED |

---

## Canonical Objective

**Current:**
```
Rendered DXF → morphology reconstruction → Solved Body Model → DXF/JSON export
```

**Future:**
```
Rendered DXF → morphology reconstruction → CAD-grade parametric body model → STEP/CAD export
```

**NOT:**
```
Photo → AI → STEP (bypassing reconstruction)
```

The DXF/rendered geometry remains intermediate reconstruction material.

---

## Export Governance

The Export Object layer remains DXF-agnostic:
- No DXF field names
- No DXF entity assumptions
- No translator semantics
- No machine-controller assumptions

DXF becomes: `Export Object → DXF Translator`

---

## AI Governance Rules

### Forbidden Behaviors

Agents may NOT:
- Redefine "done"
- Replace MVP modes
- Silently alter extraction behavior
- Remove restored_baseline
- Collapse representation into DXF
- Inject AI mutation into production path
- Bypass BOE authority
- Optimize without regression verification

### Mandatory Requirements

All morphology-intelligence work must:
- Preserve deterministic MVP
- Operate behind feature flags
- Maintain regression corpus
- Produce audit logs
- Preserve rollback paths
- Document confidence levels

---

## Framing Rule

**Correct:**
```
Instrument-aware morphology reconstruction and CAD preparation.
```

**Incorrect:**
```
AI-generated CAD.
```

---

## Related Governance Documents

- `IBG_ROLE_DEFINITION.md`
- `BLUEPRINT_READER_PROTECTION_RULES.md`
- `MORPHOLOGY_CORPUS_STANDARD.md`
- `THREE_LOOP_ARCHITECTURE_REFRAMED.md`
- `SPRINT_NAMESPACE_STANDARD.md`

---

*Canonical governance framework for the Morphology Reconstruction Platform.*
