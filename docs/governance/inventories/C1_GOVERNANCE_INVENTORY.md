# C1 Governance Inventory

**Status:** C1 COLLECTION — NOT NORMALIZATION  
**Date:** 2026-05-18  
**Purpose:** Inventory governance infrastructure that exerts semantic coordination pressure  
**Authority:** EVIDENCE ONLY — does not adjudicate governance authority

---

## Collection Methodology

```
C1 inventories semantic governance infrastructure.
C1 does not inventory project management behavior.
```

**Scope boundary:**
- Governance systems that exert semantic coordination pressure
- C0 constitutional documents as active semantic surfaces
- Governance scripts as behavioral governance law
- Registries, escalation pathways, enforcement systems

**Out of scope:**
- Inventory templates themselves
- Sprint orchestration process
- Conversational workflow
- Meeting coordination mechanics

---

## Governance Entry Format

| Field | Description |
|-------|-------------|
| System Name | Identifier |
| Type | document / script / registry / schema / policy |
| Location | File path |
| Semantic Function | What governance behavior it exerts |
| Authority Mode | defines / enforces / observes / coordinates |
| Constitutional Dependency | Relationship to C0 |
| Pressure Type | What kind of semantic pressure it exerts |
| Notes | Interpretation notes |

---

## C0 Constitutional Documents

### REPOSITORY_CONSTITUTION.md

| Field | Value |
|-------|-------|
| System Name | Repository Constitution |
| Type | document |
| Location | `docs/governance/REPOSITORY_CONSTITUTION.md` |
| Semantic Function | Defines 9 constitutional invariants, authority root, ratification model reference |
| Authority Mode | defines |
| Constitutional Dependency | IS the constitutional root |
| Pressure Type | definitional — establishes what "canonical" and "authority" mean |
| Notes | Active semantic surface: defines vocabulary like "ratification", "freeze", "experimental" |

---

### GOVERNANCE_RATIFICATION_MODEL.md

| Field | Value |
|-------|-------|
| System Name | Governance Ratification Model |
| Type | document |
| Location | `docs/governance/GOVERNANCE_RATIFICATION_MODEL.md` |
| Semantic Function | Defines 7 decision types, ratification workflow, AI constraints |
| Authority Mode | defines |
| Constitutional Dependency | C0 document under REPOSITORY_CONSTITUTION |
| Pressure Type | procedural — defines how semantic decisions become canonical |
| Notes | Defines meaning of "ratified", "proposed", "emergency ratification" |

---

### SEMANTIC_FREEZE_POLICY.md

| Field | Value |
|-------|-------|
| System Name | Semantic Freeze Policy |
| Type | document |
| Location | `docs/governance/SEMANTIC_FREEZE_POLICY.md` |
| Semantic Function | Defines 6 freeze types, freeze entry/exit, bypass prohibition |
| Authority Mode | defines |
| Constitutional Dependency | C0 document under REPOSITORY_CONSTITUTION |
| Pressure Type | constraint — defines what "frozen" means |
| Notes | Creates vocabulary: VOCAB_FREEZE, AUTH_FREEZE, SCHEMA_FREEZE, etc. |

---

### EXPERIMENTAL_ONTOLOGY_POLICY.md

| Field | Value |
|-------|-------|
| System Name | Experimental Ontology Policy |
| Type | document |
| Location | `docs/governance/EXPERIMENTAL_ONTOLOGY_POLICY.md` |
| Semantic Function | Defines containment boundaries, sandbox lifecycle, promotion process |
| Authority Mode | defines |
| Constitutional Dependency | C0 document under REPOSITORY_CONSTITUTION |
| Pressure Type | containment — defines "experimental" vs "canonical" boundary |
| Notes | IBG is explicitly cited as sandbox example |

---

### CANONICAL_PROVENANCE_MODEL.md

| Field | Value |
|-------|-------|
| System Name | Canonical Provenance Model |
| Type | document |
| Location | `docs/governance/CANONICAL_PROVENANCE_MODEL.md` |
| Semantic Function | Defines 7 canonical provenance types, maps existing usage |
| Authority Mode | defines |
| Constitutional Dependency | C0 document under REPOSITORY_CONSTITUTION |
| Pressure Type | classification — defines provenance type vocabulary |
| Notes | Creates binding vocabulary: PROV_OBSERVATIONAL, PROV_DERIVATION, etc. |

---

### GEOMETRY_AUTHORITY_DECOMPOSITION.md

| Field | Value |
|-------|-------|
| System Name | Geometry Authority Decomposition |
| Type | document |
| Location | `docs/governance/GEOMETRY_AUTHORITY_DECOMPOSITION.md` |
| Semantic Function | Defines 5 geometry layers, ownership matrix, dependency rules |
| Authority Mode | defines |
| Constitutional Dependency | C0 document under REPOSITORY_CONSTITUTION |
| Pressure Type | decomposition — defines geometry layer vocabulary |
| Notes | Creates vocabulary: GEOM_SEMANTIC, GEOM_COORDINATE, GEOM_TOPOLOGY, etc. |

---

## Dev 56 Governance Documents

### CANONICAL_ONTOLOGY_VOCABULARY.md

| Field | Value |
|-------|-------|
| System Name | Canonical Ontology Vocabulary |
| Type | registry |
| Location | `docs/governance/CANONICAL_ONTOLOGY_VOCABULARY.md` |
| Semantic Function | Vocabulary registry with 28+ canonical terms |
| Authority Mode | defines (vocabulary) + coordinates (usage) |
| Constitutional Dependency | Operates under C0 ratification model |
| Pressure Type | definitional — defines what terms mean canonically |
| Notes | Contains "Prohibited Reinterpretations" field — active semantic enforcement |

---

### CANONICAL_AUTHORITY_MAP.md

| Field | Value |
|-------|-------|
| System Name | Canonical Authority Map |
| Type | registry |
| Location | `docs/governance/CANONICAL_AUTHORITY_MAP.md` |
| Semantic Function | Maps concerns to canonical/operational owners |
| Authority Mode | defines (ownership) + coordinates (boundaries) |
| Constitutional Dependency | Operates under C0 authority rules |
| Pressure Type | ownership — defines who owns what |
| Notes | Hybrid model: Canonical Owner + Operational Owner(s) |

---

### ONTOLOGY_RECONCILIATION_WORKFLOW.md

| Field | Value |
|-------|-------|
| System Name | Ontology Reconciliation Workflow |
| Type | document |
| Location | `docs/governance/ONTOLOGY_RECONCILIATION_WORKFLOW.md` |
| Semantic Function | 8-stage workflow for semantic conflict resolution |
| Authority Mode | coordinates |
| Constitutional Dependency | Implements C0 ratification model |
| Pressure Type | procedural — defines how conflicts resolve |
| Notes | Contains AI constraint sections — active behavioral governance |

---

### ONTOLOGY_DRIFT_CLASSIFICATIONS.md

| Field | Value |
|-------|-------|
| System Name | Ontology Drift Classifications |
| Type | schema |
| Location | `docs/governance/ONTOLOGY_DRIFT_CLASSIFICATIONS.md` |
| Semantic Function | Classifies drift types including constitutional violations |
| Authority Mode | defines (categories) + observes (patterns) |
| Constitutional Dependency | Extended with C0 constitutional drift classes |
| Pressure Type | classification — defines drift vocabulary |
| Notes | 9 domain drift types + 5 constitutional drift types |

---

## Governance Scripts

### check_all.py

| Field | Value |
|-------|-------|
| System Name | Unified Governance Check |
| Type | script |
| Location | `scripts/governance/check_all.py` |
| Semantic Function | Executes tier-based governance checks |
| Authority Mode | enforces |
| Constitutional Dependency | Implements tier enforcement from GOVERNANCE_AUTHORITY_HIERARCHY |
| Pressure Type | enforcement — blocks non-conforming changes |
| Notes | Tiers: precommit, ci, nightly, manual. Defines what "blocking" means operationally. |

---

### Tier System (embedded in check_all.py)

| Field | Value |
|-------|-------|
| System Name | Governance Tier System |
| Type | schema (embedded) |
| Location | `scripts/governance/check_all.py` |
| Semantic Function | Classifies checks by execution tier |
| Authority Mode | defines + enforces |
| Constitutional Dependency | Related to (but distinct from) GOVERNANCE_AUTHORITY_HIERARCHY tiers |
| Pressure Type | classification — defines tier vocabulary |
| Notes | COLLISION CANDIDATE: "tier" terminology overlaps with governance hierarchy and data promotion |

---

## Governance Policy Files

### ontology_ci_policy.json

| Field | Value |
|-------|-------|
| System Name | Ontology CI Policy |
| Type | policy |
| Location | `docs/governance/ontology/ontology_ci_policy.json` |
| Semantic Function | Defines severity levels, enforcement rules for CI |
| Authority Mode | defines + enforces |
| Constitutional Dependency | Referenced by ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER |
| Pressure Type | enforcement — defines severity vocabulary |
| Notes | Machine-readable governance policy |

---

### ontology_drift_baseline_2026_05.json

| Field | Value |
|-------|-------|
| System Name | Ontology Drift Baseline |
| Type | schema |
| Location | `docs/governance/ontology/ontology_drift_baseline_2026_05.json` |
| Semantic Function | Accepted legacy drift baseline |
| Authority Mode | observes |
| Constitutional Dependency | Referenced by observability layer |
| Pressure Type | historical — defines what drift is "accepted" |
| Notes | Baseline creates implicit authority: "drift before this date is acceptable" |

---

## Ontology Stack Documents

### GOVERNANCE_STACK_INDEX_V1.md

| Field | Value |
|-------|-------|
| System Name | Governance Stack Index |
| Type | document |
| Location | `docs/governance/ontology/GOVERNANCE_STACK_INDEX_V1.md` |
| Semantic Function | Navigation index for ontology governance stack |
| Authority Mode | coordinates |
| Constitutional Dependency | Updated with C0 positioning |
| Pressure Type | coordination — defines stack relationships |
| Notes | Contains 8 governance invariants prior to C0 |

---

### AUTHORITY_BOUNDARY_REGISTRY_V1.md

| Field | Value |
|-------|-------|
| System Name | Authority Boundary Registry |
| Type | registry |
| Location | `docs/governance/ontology/AUTHORITY_BOUNDARY_REGISTRY_V1.md` |
| Semantic Function | 7 boundary records with must_not_own clauses |
| Authority Mode | defines (boundaries) + coordinates (ownership) |
| Constitutional Dependency | Pre-C0 document, now under constitution |
| Pressure Type | boundary — defines ownership edges |
| Notes | Contains anti-pattern definitions |

---

### PROMOTION_REVIEW_MANIFEST_V1.md

| Field | Value |
|-------|-------|
| System Name | Promotion Review Manifest |
| Type | document |
| Location | `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md` |
| Semantic Function | Governs Tier 3 → Tier 2 promotion review |
| Authority Mode | coordinates |
| Constitutional Dependency | Pre-C0 document |
| Pressure Type | procedural — defines promotion vocabulary |
| Notes | COLLISION: Uses "Tier" terminology that collides with governance hierarchy |

---

### ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md

| Field | Value |
|-------|-------|
| System Name | Ontology Governance Observability Layer |
| Type | document |
| Location | `docs/governance/ontology/ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md` |
| Semantic Function | 10 drift lifecycle states, 9 governance signal categories |
| Authority Mode | observes + coordinates |
| Constitutional Dependency | Pre-C0 document |
| Pressure Type | observational — defines drift state vocabulary |
| Notes | Creates lifecycle vocabulary (detected, reviewed, escalated, etc.) |

---

## Governance Authority Documents

### GOVERNANCE_AUTHORITY_HIERARCHY.md

| Field | Value |
|-------|-------|
| System Name | Governance Authority Hierarchy |
| Type | document |
| Location | `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md` |
| Semantic Function | Defines 3-tier governance hierarchy |
| Authority Mode | defines |
| Constitutional Dependency | Tier structure referenced by constitution |
| Pressure Type | structural — defines tier vocabulary |
| Notes | COLLISION SOURCE: Tier 1/2/3 terminology collides with data promotion tiers |

---

### GOVERNANCE_TOPOLOGY_MAP.md

| Field | Value |
|-------|-------|
| System Name | Governance Topology Map |
| Type | document |
| Location | `docs/governance/GOVERNANCE_TOPOLOGY_MAP.md` |
| Semantic Function | Full governance system inventory |
| Authority Mode | observes |
| Constitutional Dependency | Documentation layer |
| Pressure Type | cartographic — maps governance surfaces |
| Notes | Observational, not authoritative |

---

## Semantic Pressure Summary

### Authority Mode Distribution

| Mode | Count | Description |
|------|-------|-------------|
| defines | 12 | Creates semantic vocabulary or rules |
| enforces | 3 | Blocks non-conforming behavior |
| coordinates | 6 | Manages relationships without defining |
| observes | 4 | Reports state without authority |

### Constitutional Dependency Distribution

| Dependency | Count |
|------------|-------|
| IS constitutional root | 1 |
| C0 document | 5 |
| Operates under C0 | 4 |
| Pre-C0 (now under constitution) | 6 |
| Documentation layer | 2 |

### Pressure Type Distribution

| Type | Count |
|------|-------|
| definitional | 3 |
| procedural | 3 |
| classification | 4 |
| enforcement | 3 |
| coordination | 2 |
| ownership/boundary | 3 |
| observational | 2 |

---

## Governance Collision Candidates

| System | Collision | Severity |
|--------|-----------|----------|
| Tier System (check_all.py) | "tier" terminology triple collision | HIGH |
| Promotion Review Manifest | "Tier" terminology collision | HIGH |
| Drift Baseline | Implicit "acceptable drift" authority | MEDIUM |
| Observability Layer | Lifecycle vocabulary parallel to governance lifecycle | MEDIUM |

---

## Key Finding: Governance Infrastructure as Semantic Authority

The inventory confirms:

```
Governance infrastructure is itself a semantic authority surface.
```

Evidence:
- C0 documents define vocabulary (ratification, freeze, experimental, provenance types)
- Registries define ownership and boundaries
- Scripts enforce interpretations operationally
- Policies create implicit authority through baseline definitions

This is governance infrastructure exerting semantic coordination pressure — exactly the pattern C1 was designed to surface.

---

## Related Documents

- `C1_INVENTORY_INDEX.md` — inventory navigation
- `SEMANTIC_COLLISION_LOG.md` — collision candidates
- `REPOSITORY_CONSTITUTION.md` — constitutional root
- `GOVERNANCE_STACK_INDEX_V1.md` — stack navigation

---

*C1 Governance Inventory — Collection Phase*
