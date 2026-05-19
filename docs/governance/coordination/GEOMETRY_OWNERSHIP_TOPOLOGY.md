# Geometry Ownership Topology

**Phase:** C2-A — Geometry Authority Decomposition  
**Date:** 2026-05-18  
**Owner:** Terminal 1 (Governance Integration Lead)  
**Status:** Draft

---

## Purpose

This document maps geometry ownership across the authority chain, identifying which systems own which semantic surfaces and where ownership transitions occur.

---

## 1. Ownership Hierarchy

### 1.1 Authority Tiers (Geometry Domain)

| Tier | Name | Description |
|------|------|-------------|
| 2a | Origin Authority | Source data extraction and initial classification |
| 2b | Approval Authority | Governance gate for approved geometry |
| 2c | Construction Authority | Build parameters and topology generation |
| — | Consumer | No authority (serialization, validation) |

### 1.2 Tier Membership

| Tier | Systems |
|------|---------|
| 2a | Blueprint, Vectorizer, IBG Body Grid |
| 2b | BOE (Body Output Envelope) |
| 2c | CadSemantics, TopologyBuilder, ShellValidation |
| Consumer | Translators, Validators, CAM Runtime |

---

## 2. Ownership Map

### 2.1 Semantic Surface Ownership

| Semantic Surface | Owner | Authority Type | Consumers |
|------------------|-------|----------------|-----------|
| Raw blueprint data | Blueprint | Source truth | Vectorizer |
| Extracted coordinates | Vectorizer | Extraction | IBG |
| Zone classification | IBG Body Grid | Classification | BOE |
| Primitive classification | IBG Body Grid | Classification | BOE |
| Morphology class | IBG Variant Grammar | Classification | BOE |
| Approved body shape | BOE | Approval gate | CadSemantics |
| Approved landmarks | BOE | Approval gate | CadSemantics |
| Body category | CadSemantics | Construction hints | TopologyBuilder |
| Surface type | CadSemantics | Construction hints | TopologyBuilder |
| Runtime support | CadSemantics | Construction hints | TopologyBuilder |
| Topology shell | TopologyBuilder | Generation | Translators |
| Shell validation | ShellValidation | Quality gate | Export |

### 2.2 Ownership Transitions

| From | To | Transition Type | Boundary Rule |
|------|----|-----------------|---------------|
| Blueprint → Vectorizer | Data extraction | Coordinates only, no interpretation |
| Vectorizer → IBG | Classification begins | IBG owns zone/primitive semantics |
| IBG → BOE | Approval gate | BOE may reject, not modify |
| BOE → CadSemantics | Hint provision | CadSemantics receives, not redefines |
| CadSemantics → TopologyBuilder | Generation trigger | TopologyBuilder owns shell |
| TopologyBuilder → Translator | Serialization | Translator serializes, not generates |

---

## 3. Forbidden Ownership Patterns

### 3.1 Authority Violations

| Pattern | Violation | Evidence Check |
|---------|-----------|----------------|
| Translator generates geometry | Authority inversion | Translator creates topology |
| Runtime defines geometry vocabulary | Authority escalation | Runtime DTO has geometry terms |
| Validator repairs geometry | Authority acquisition | Validator modifies topology |
| Plugin sources geometry | Authority bypass | Plugin provides geometry data |
| Adapter normalizes geometry | Silent authority | Adapter collapses semantics |

### 3.2 Detection Methods

| Violation | Detection Method |
|-----------|------------------|
| Translator generates | Grep for topology creation in translator code |
| Runtime vocabulary | Grep for geometry enums in runtime code |
| Validator repairs | Grep for mutation in validator code |
| Plugin sources | Trace geometry flow from plugins |
| Adapter normalizes | Review adapter conversion logic |

---

## 4. Current Gaps

### 4.1 Undeclared Ownership

| Gap | Description | C1 Evidence |
|-----|-------------|-------------|
| Vectorizer position | Not in authority chain registry | Missing |
| IBG internals | Zone/primitive authority undeclared | ASM-013 |
| CadSemantics→TopologyBuilder | Implicit consumption | ASM-014 |
| Runtime geometry source | Undeclared | ASM-001 |

### 4.2 Ambiguous Ownership

| Surface | Claimant A | Claimant B | Resolution |
|---------|------------|------------|------------|
| Zone Y-ranges | IBG (implicit) | None declared | C2-C |
| Runtime support mapping | CadSemantics | TopologyBuilder | Explicit mapping needed |

---

## 5. Proposed Ownership Registry Update

### 5.1 New Sub-Domain Declarations

```json
{
  "geometry_source": {
    "canonical_owner": "Blueprint/Vectorizer",
    "operational_owners": ["Vectorizer"],
    "authority_tier": "2a",
    "consumers": ["IBG"],
    "forbidden_ownership": "No system downstream may redefine source coordinates"
  },
  "geometry_classification": {
    "canonical_owner": "IBG Body Grid",
    "operational_owners": ["Zone System", "Primitive System", "Variant Grammar"],
    "authority_tier": "2a",
    "consumers": ["BOE"],
    "forbidden_ownership": "Classification is advisory until BOE approval"
  },
  "geometry_approval": {
    "canonical_owner": "BOE",
    "operational_owners": ["Body Output Envelope"],
    "authority_tier": "2b",
    "consumers": ["CadSemantics", "Export"],
    "forbidden_ownership": "Post-approval modification prohibited"
  }
}
```

### 5.2 Authority Chain Update (Proposed)

**Current:**
```
Blueprint → IBG → BOE → CadSemantics → TopologyBuilder → ShellValidation → Translator
```

**Proposed (with sub-tiers):**
```
Blueprint (2a-source)
  → Vectorizer (2a-extraction)
    → IBG (2a-classification)
      → BOE (2b-approval)
        → CadSemantics (2c-hints)
          → TopologyBuilder (2c-generation)
            → ShellValidation (2c-validation)
              → Translator (consumer)
```

---

## 6. Ownership Validation Checklist

### 6.1 Per-System Validation

| System | Owns | Consumes | Verified |
|--------|------|----------|----------|
| Blueprint | Source data | — | — |
| Vectorizer | Coordinates | Blueprint | Pending T2 |
| IBG | Zones, Primitives | Coordinates | Pending C2-C |
| BOE | Approved shape | IBG output | — |
| CadSemantics | Construction hints | BOE output | — |
| TopologyBuilder | Topology shell | CadSemantics | — |
| ShellValidation | Quality assessment | Topology | — |
| Translator | — | Topology | Pending T5 |

### 6.2 Boundary Validation

| Boundary | Rule | Verified |
|----------|------|----------|
| Extraction | No interpretation | Pending |
| Classification | Advisory only | Pending |
| Approval | Gate, not modify | Pending |
| Construction | Hints only | Pending |
| Generation | Own shell | Pending |
| Serialization | No generation | Pending T5 |

---

## 7. Cross-Reference

| Document | Relationship |
|----------|--------------|
| `C2A_GEOMETRY_AUTHORITY_PACKET.md` | Parent packet |
| `authority_chain_registry.json` | Target for updates |
| `C1_GEOMETRY_TOPOLOGY_INVENTORY.md` | Evidence source |
| `RUNTIME_GEOMETRY_BOUNDARY_MAP.md` | T2 companion |
| `EXPORT_GEOMETRY_AUTHORITY_REVIEW.md` | T5 companion |

---

## T1 Status

**Draft complete.** Awaiting T2 and T5 deliverables for verification.
