# Canonical Authority Map

**Status:** Authoritative  
**Date:** 2026-05-16  
**Purpose:** Explicit semantic ownership declaration for the repository

---

## Overview

This document declares canonical ownership for semantic concerns across the repository. Authority is structured in two tiers:

- **Canonical Owner:** Abstract authority layer responsible for semantic definition
- **Operational Owner(s):** Named subsystem(s) that implement and maintain within that authority

This hybrid approach preserves both semantic ownership clarity and operational traceability.

---

## Authority Structure

### Core Invariants

1. **Execution consumes intent; execution does not redefine intent.**
2. **Runtime systems consume ontology; runtime systems do not define ontology.**
3. **AI assistance is advisory only; human authority ratifies canonical ontology.**

---

## Authority Map

| Concern | Canonical Owner | Operational Owner(s) | Consumers | Forbidden Ownership |
|---------|-----------------|---------------------|-----------|---------------------|
| Geometry truth | Geometry layer | IBG, Body Grid | CAM, Export, Visualization | Runtime systems may not redefine geometry semantics |
| Aperture semantics | Geometry layer | Aperture Workspace, Spiral Designer | Acoustic analysis, Export | Acoustic systems may not override geometry definitions |
| Manufacturing feasibility | Feasibility layer | RMOS | CAM, Export, Toolpath | Visualization systems may not claim feasibility authority |
| Export lifecycle | Export governance layer | CAM Export, DXF Writer | Downstream consumers | Runtime dispatchers may not bypass export governance |
| Serialization format | Serialization layer | Translators, Schema validators | All persistence consumers | Execution systems may not define serialization semantics |
| Validation semantics | Validation layer | Schema validators, Constraint systems | All validated data producers | Validated systems may not override validation rules |
| Provenance lineage | Governance layer | Snapshot systems, Archive systems | Audit, Traceability | No system may fabricate provenance |
| Acoustic measurements | Measurement layer | Acoustic state, Archive systems | Analysis, Comparison | Prediction systems may not claim measurement authority |
| Acoustic prediction | Deferred / not canonical | None currently | None | No system may claim prediction authority without calibration infrastructure |
| Acoustic estimates | Computation layer | Helmholtz estimator | Comparison, Diagnostics | Estimates may not be presented as predictions |
| CAM intent | CAM ontology layer | Intent schemas, Workflow specs | CAM runtime, Export | Runtime may not redefine CAM intent |
| CAM runtime dispatch | Runtime layer | CAM Runtime Dispatcher | CAM operation runtimes, CAM export governance, RMOS integration | Design tools, translators, routers may not claim dispatch authority |
| Runtime execution | Runtime layer | CAM Runtime Dispatcher | Execution consumers | Runtime may not claim semantic authority |
| Lifecycle classification | Governance lifecycle layer | Lifecycle state machines | All lifecycle consumers | Runtime systems may not independently assign lifecycle states |
| Vocabulary definition | Governance layer | Vocabulary registry | All systems | No subsystem may independently create canonical vocabulary |
| Authority assignment | Governance layer | Authority map | All systems | No system may self-grant authority |
| Morphology semantics | Geometry layer | MRP, Morphology corpus | Analysis, Classification | Runtime systems may not redefine morphology vocabulary |

---

## Authority Separation Principles

### Intent vs. Execution

```
Intent Layer                    Execution Layer
─────────────                   ───────────────
declares goals                  implements goals
defines what                    determines how
stable semantics                evolving implementations
governance-owned                runtime-owned
```

**Rule:** Execution may interpret intent for implementation purposes. Execution may not modify, extend, or constrain the semantic meaning of intent.

**Rule:** Dispatcher routes runtime interpretation but does not authorize machine execution.

### Ontology vs. Runtime

```
Ontology Layer                  Runtime Layer
──────────────                  ─────────────
defines meaning                 uses meaning
vocabulary authority            vocabulary consumer
governance-ratified             implementation-specific
stable across versions          may evolve per release
```

**Rule:** Runtime systems may cache, index, or optimize ontology access. Runtime systems may not add, remove, or redefine ontology terms.

### Governance vs. Implementation

```
Governance Layer                Implementation Layer
────────────────                ────────────────────
defines constraints             operates within constraints
authority ownership             authority consumer
change control                  change execution
```

**Rule:** Implementation may propose governance changes through reconciliation workflow. Implementation may not unilaterally modify governance.

---

## Operational Authority Details

### IBG (Instrument Body Geometry)

- **Domain:** Body outline morphology, contour classification
- **Authority scope:** Body geometry semantics, morphology vocabulary
- **Boundary:** Does not own acoustic semantics or manufacturing feasibility

### RMOS (Recommendation Manufacturing Optimization System)

- **Domain:** Manufacturing feasibility, process constraints
- **Authority scope:** Feasibility classification, manufacturing vocabulary
- **Boundary:** Does not own geometry truth or acoustic semantics

### CAM Export

- **Domain:** Export lifecycle, format compliance
- **Authority scope:** Export state transitions, format validation
- **Boundary:** Does not own geometry computation or intent definition

### MRP (Morphology Reconstruction Platform)

- **Domain:** Form analysis, corpus management
- **Authority scope:** Morphology classification, reconstruction vocabulary
- **Boundary:** Does not own runtime execution or prediction authority

### Aperture Workspace

- **Domain:** Aperture comparison, acoustic diagnostics
- **Authority scope:** Comparison workflow, diagnostic presentation
- **Boundary:** Does not own geometry computation or prediction authority

---

## Forbidden Authority Patterns

### Self-Granted Authority

No system may claim authority not explicitly granted by this map or governance ratification.

**Symptom:** System documentation claims ownership without governance reference.

### Authority Creep

No system may expand authority scope beyond declared boundaries.

**Symptom:** System begins validating, defining, or constraining outside its domain.

### Implicit Authority Transfer

Authority may not be transferred through implementation coupling.

**Symptom:** Consumer system begins making authoritative decisions because it has data access.

### Runtime Authority Assumption

Runtime systems may not assume ontology authority through operational necessity.

**Symptom:** Runtime documentation uses language like "defines", "establishes", "owns" for semantic concepts.

---

## Authority Conflict Resolution

When authority conflicts arise:

1. Identify the semantic concern in dispute
2. Locate canonical owner in this map
3. If not mapped, escalate to governance layer
4. Human Arbiter resolves unmapped conflicts
5. Resolution updates this map through reconciliation workflow

**Rule:** Conflicts are resolved by governance, not by runtime precedent or implementation seniority.

---

## Authority Root and Ratification Dependency

This authority map operates under the Repository Constitution (`REPOSITORY_CONSTITUTION.md`).

### Constitutional Authority Root

```
REPOSITORY_CONSTITUTION.md
→ defines semantic authority rules
→ this map implements those rules
```

The constitution is the authority root. This map is a governed implementation of constitutional principles.

### Constitutional Invariants Applicable to Authority

| Invariant | Application |
|-----------|-------------|
| Invariant 1: No subsystem may silently become ontology authority | Authority requires explicit governance grant in this map |
| Invariant 5: Visibility is not authority | Being documented here does not create authority; ratification creates authority |
| Invariant 6: Consumption is not ownership | Using data does not grant authority over its definition |
| Invariant 7: Location is not authority | Where data is stored does not determine who owns its meaning |

### Ratification Requirement

Authority assignments require ratification per `GOVERNANCE_RATIFICATION_MODEL.md`.

```
New authority assignments → AUTHORITY_ASSIGNMENT decision type
Authority transfers → AUTHORITY_ASSIGNMENT decision type
Authority revocations → AUTHORITY_ASSIGNMENT decision type
```

### Freeze Applicability

When `AUTH_FREEZE` is active per `SEMANTIC_FREEZE_POLICY.md`:
- No new authority assignments
- No authority transfers
- Existing authority remains in effect

---

## Related Documents

- [CANONICAL_ONTOLOGY_VOCABULARY.md](./CANONICAL_ONTOLOGY_VOCABULARY.md) — vocabulary definitions
- [ONTOLOGY_RECONCILIATION_WORKFLOW.md](./ONTOLOGY_RECONCILIATION_WORKFLOW.md) — change process
- [ONTOLOGY_DRIFT_CLASSIFICATIONS.md](./ONTOLOGY_DRIFT_CLASSIFICATIONS.md) — drift detection
- [GOVERNANCE_AUTHORITY_HIERARCHY.md](./GOVERNANCE_AUTHORITY_HIERARCHY.md) — tier structure
- [REPOSITORY_CONSTITUTION.md](./REPOSITORY_CONSTITUTION.md) — constitutional authority
- [GOVERNANCE_RATIFICATION_MODEL.md](./GOVERNANCE_RATIFICATION_MODEL.md) — ratification workflow
- [SEMANTIC_FREEZE_POLICY.md](./SEMANTIC_FREEZE_POLICY.md) — freeze discipline
