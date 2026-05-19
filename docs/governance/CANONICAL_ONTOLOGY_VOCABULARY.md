# Canonical Ontology Vocabulary

**Status:** Authoritative  
**Date:** 2026-05-16  
**Purpose:** First formal vocabulary authority registry for the repository

---

## Overview

This registry defines canonical semantic meaning for core terminology used across the repository. Definitions describe ontological ownership, not implementation details.

**Core rule:** No subsystem may independently redefine canonical meaning.

---

## Vocabulary Registry

### intent

| Field | Value |
|-------|-------|
| **Term** | intent |
| **Canonical Definition** | A declared purpose or goal that guides downstream execution without prescribing implementation. Intent expresses what should be achieved, not how. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | CAM intent schemas, workflow specifications |
| **Allowed Usage** | Declaring goals, specifying desired outcomes, guiding execution decisions |
| **Prohibited Reinterpretations** | Runtime systems may not redefine intent as execution state. Execution consumes intent; execution does not redefine intent. |
| **Lifecycle Notes** | Intent remains stable across runtime versions |

---

### runtime

| Field | Value |
|-------|-------|
| **Term** | runtime |
| **Canonical Definition** | The execution environment and behavior of systems during active operation. Runtime encompasses process state, resource allocation, and execution flow. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | Execution contracts, lifecycle state machines |
| **Allowed Usage** | Describing execution behavior, process management, operational state |
| **Prohibited Reinterpretations** | Runtime systems consume ontology; runtime systems do not define ontology. Runtime may not claim semantic authority over vocabulary or governance. |
| **Lifecycle Notes** | Runtime behavior may evolve independently of semantic definitions |

---

### translator

| Field | Value |
|-------|-------|
| **Term** | translator |
| **Canonical Definition** | A component that transforms data between representations while preserving semantic meaning. Translators convert format, not meaning. |
| **Owning Authority Layer** | Serialization layer |
| **Related Contracts** | Serialization contracts, format specifications |
| **Allowed Usage** | Format conversion, representation transformation, protocol bridging |
| **Prohibited Reinterpretations** | Translators may not introduce semantic mutation. Translation preserves meaning; it does not interpret meaning. |
| **Lifecycle Notes** | Translator implementations may change; semantic preservation rules remain stable |

---

### validation

| Field | Value |
|-------|-------|
| **Term** | validation |
| **Canonical Definition** | The process of verifying that data or state conforms to declared constraints without modifying the validated subject. Validation reports conformance; it does not transform. |
| **Owning Authority Layer** | Validation systems |
| **Related Contracts** | Schema contracts, constraint specifications |
| **Allowed Usage** | Conformance checking, constraint verification, schema validation |
| **Prohibited Reinterpretations** | Validation may not mutate validated data. Validation may not claim authority over the meaning of what it validates. |
| **Lifecycle Notes** | Validation rules may tighten but should not silently relax |

---

### provenance

| Field | Value |
|-------|-------|
| **Term** | provenance |
| **Canonical Definition** | The documented origin, history, and lineage of data or artifacts. Provenance answers "where did this come from and how did it get here." |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Snapshot schemas, archive schemas, lineage specifications |
| **Allowed Usage** | Origin tracking, lineage documentation, audit trails |
| **Prohibited Reinterpretations** | Provenance may not be fabricated or inferred without explicit declaration. Provenance describes observed history, not predicted history. |
| **Lifecycle Notes** | Provenance records are append-only by design |

---

### artifact

| Field | Value |
|-------|-------|
| **Term** | artifact |
| **Canonical Definition** | A discrete, identifiable output produced by a process. Artifacts have defined boundaries, provenance, and lifecycle state. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Export schemas, archive schemas |
| **Allowed Usage** | Naming outputs, tracking deliverables, documenting production |
| **Prohibited Reinterpretations** | Artifacts may not be implicitly created. Artifact creation requires explicit declaration. |
| **Lifecycle Notes** | Artifact identity persists across format transformations |

---

### topology

| Field | Value |
|-------|-------|
| **Term** | topology |
| **Canonical Definition** | The structural arrangement and relationships between components in a system. Topology describes shape and connection, not behavior. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Architecture specifications, governance maps |
| **Allowed Usage** | Describing system structure, component relationships, boundary definitions |
| **Prohibited Reinterpretations** | Topology describes structure; it does not prescribe execution order. Runtime systems may not conflate topology with execution flow. |
| **Lifecycle Notes** | Topology changes require governance review |

---

### serialization

| Field | Value |
|-------|-------|
| **Term** | serialization |
| **Canonical Definition** | The process of converting structured data into a format suitable for storage or transmission while preserving reconstruction capability. |
| **Owning Authority Layer** | Translators |
| **Related Contracts** | Format specifications, schema versions |
| **Allowed Usage** | Data persistence, transmission, format conversion |
| **Prohibited Reinterpretations** | Serialization preserves data; it does not interpret data. Serialization format choices do not grant semantic authority. |
| **Lifecycle Notes** | Serialization formats may evolve with explicit migration paths |

---

### morphology

| Field | Value |
|-------|-------|
| **Term** | morphology |
| **Canonical Definition** | The study and representation of form, shape, and structural characteristics. In this repository, morphology refers to geometric and physical form analysis. |
| **Owning Authority Layer** | Geometry layer |
| **Related Contracts** | MRP specifications, geometry schemas |
| **Allowed Usage** | Shape analysis, form classification, structural characterization |
| **Prohibited Reinterpretations** | Morphology describes form; it does not prescribe acoustic or performance characteristics. Form analysis is distinct from performance prediction. |
| **Lifecycle Notes** | Morphology vocabulary governed by MRP domain |

---

### measurement

| Field | Value |
|-------|-------|
| **Term** | measurement |
| **Canonical Definition** | An observed value obtained through a defined process at a specific point in time. Measurements are observational records, not predictions or estimates. |
| **Owning Authority Layer** | Measurement layer |
| **Related Contracts** | Archive schemas, acoustic state contracts |
| **Allowed Usage** | Recording observations, documenting sensor readings, preserving empirical data |
| **Prohibited Reinterpretations** | Measurements are observations, not conclusions. Measurement data may not be conflated with predictions or recommendations. |
| **Lifecycle Notes** | Measurements are immutable once recorded |

---

### estimate

| Field | Value |
|-------|-------|
| **Term** | estimate |
| **Canonical Definition** | A computed approximation based on models, assumptions, and available data. Estimates are explicitly provisional and assumption-dependent. |
| **Owning Authority Layer** | Computation layer |
| **Related Contracts** | Estimate schemas, assumption declarations |
| **Allowed Usage** | Approximation, preliminary calculation, first-order analysis |
| **Prohibited Reinterpretations** | Estimates are not measurements. Estimates are not predictions. Estimates must declare their assumptions. |
| **Lifecycle Notes** | Estimate accuracy may improve; estimate provenance must be preserved |

---

### prediction

| Field | Value |
|-------|-------|
| **Term** | prediction |
| **Canonical Definition** | A statement about future or unknown state based on models and calibration. Predictions claim accuracy beyond available observations. |
| **Owning Authority Layer** | Deferred / not canonical |
| **Related Contracts** | None currently canonical |
| **Allowed Usage** | Currently deferred; no canonical prediction systems exist |
| **Prohibited Reinterpretations** | Estimates may not be presented as predictions. Observations may not be presented as predictions. Prediction capability requires explicit calibration infrastructure. |
| **Lifecycle Notes** | Prediction systems require governance approval before canonicalization |

---

### governance

| Field | Value |
|-------|-------|
| **Term** | governance |
| **Canonical Definition** | The framework of rules, authority structures, and processes that guide repository evolution. Governance defines what may change and under what conditions. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Governance hierarchy, authority maps |
| **Allowed Usage** | Rule definition, authority declaration, change control |
| **Prohibited Reinterpretations** | Governance is not execution. Governance defines constraints; runtime systems implement them. Governance authority may not be claimed by runtime systems. |
| **Lifecycle Notes** | Governance changes require explicit ratification |

---

### authority

| Field | Value |
|-------|-------|
| **Term** | authority |
| **Canonical Definition** | The recognized right to define, modify, or interpret within a specific domain. Authority is explicitly granted, not assumed. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Authority maps, ownership declarations |
| **Allowed Usage** | Declaring ownership, establishing boundaries, resolving conflicts |
| **Prohibited Reinterpretations** | Authority may not be self-granted. Authority scope may not be unilaterally expanded. Authority conflicts require reconciliation. |
| **Lifecycle Notes** | Authority assignments are durable until explicitly revoked |

---

### execution

| Field | Value |
|-------|-------|
| **Term** | execution |
| **Canonical Definition** | The act of performing operations as directed by intent and constrained by governance. Execution implements; execution does not define. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | Execution contracts, runtime specifications |
| **Allowed Usage** | Describing operational behavior, process invocation, task completion |
| **Prohibited Reinterpretations** | Execution consumes intent; execution does not redefine intent. Execution follows governance; execution does not establish governance. |
| **Lifecycle Notes** | Execution implementations may evolve within governance constraints |

---

### experimental

| Field | Value |
|-------|-------|
| **Term** | experimental |
| **Canonical Definition** | A lifecycle state indicating provisional status with explicit boundaries. Experimental components are contained, reversible, and not canonical. |
| **Owning Authority Layer** | Governance lifecycle layer |
| **Related Contracts** | Lifecycle specifications, containment rules |
| **Allowed Usage** | Marking provisional implementations, declaring sandbox boundaries, indicating non-production status |
| **Prohibited Reinterpretations** | Experimental status does not grant exemption from governance. Experimental components may not leak into canonical systems without ratification. |
| **Lifecycle Notes** | Experimental components have defined promotion or removal paths |

---

### canonical

| Field | Value |
|-------|-------|
| **Term** | canonical |
| **Canonical Definition** | The authoritative, ratified version of a component, definition, or process. Canonical status indicates governance approval and production readiness. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Governance hierarchy, authority maps |
| **Allowed Usage** | Declaring authoritative versions, establishing reference implementations, resolving ambiguity |
| **Prohibited Reinterpretations** | Canonical status may not be self-declared. Canonical promotion requires governance ratification. Multiple conflicting canonical definitions are prohibited. |
| **Lifecycle Notes** | Canonical status persists until explicit deprecation |

---

### semantic-only

| Field | Value |
|-------|-------|
| **Term** | semantic-only |
| **Canonical Definition** | A classification indicating that a component or document defines meaning without implementing behavior. Semantic-only artifacts guide but do not execute. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Vocabulary registries, authority maps |
| **Allowed Usage** | Classifying governance documents, distinguishing definition from implementation |
| **Prohibited Reinterpretations** | Semantic-only documents may not contain execution logic. Semantic authority does not imply runtime authority. |
| **Lifecycle Notes** | Semantic-only classification is stable across implementation changes |

---

### governed-experimental

| Field | Value |
|-------|-------|
| **Term** | governed-experimental |
| **Canonical Definition** | A lifecycle state combining experimental status with explicit governance oversight. Governed-experimental components have defined boundaries, review requirements, and promotion criteria. |
| **Owning Authority Layer** | Governance lifecycle layer |
| **Related Contracts** | Experimental containment rules, promotion workflows |
| **Allowed Usage** | Classifying contained experiments, declaring sandbox scope, establishing review gates |
| **Prohibited Reinterpretations** | Governed-experimental is not ungoverned. Governance constraints apply even within experimental boundaries. |
| **Lifecycle Notes** | Governed-experimental components require periodic review |

---

## Registry Maintenance

### Addition Process

New vocabulary entries require:
1. Proposed definition with all required fields
2. Authority ownership declaration
3. Review for conflicts with existing terms
4. Governance ratification

### Modification Process

Vocabulary modifications require:
1. Documented rationale
2. Impact assessment on dependent systems
3. Consumer notification
4. Governance ratification

### Prohibition

No subsystem may:
- Independently create canonical vocabulary
- Redefine existing canonical terms
- Claim authority not granted by this registry
- Introduce conflicting definitions

---

### ai-advisory-system

| Field | Value |
|-------|-------|
| **Term** | ai-advisory-system |
| **Canonical Definition** | A system that provides guidance, suggestions, or analysis without holding decision authority. AI advisory systems inform human judgment; they do not replace it. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Reconciliation workflow, authority maps |
| **Allowed Usage** | Describing AI assistance roles, clarifying advisory boundaries, documenting automation limits |
| **Prohibited Reinterpretations** | AI advisory systems may not claim semantic authority. AI advisory output may not be auto-ratified as canonical. AI systems may not independently freeze ontology. |
| **Lifecycle Notes** | AI advisory constraints are architectural invariants |

---

### canonical-authority

| Field | Value |
|-------|-------|
| **Term** | canonical-authority |
| **Canonical Definition** | The recognized right to establish, modify, or ratify canonical definitions within a domain. Canonical authority requires explicit governance grant and human accountability. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Authority maps, reconciliation workflow |
| **Allowed Usage** | Declaring who may ratify ontology, establishing approval chains, resolving ownership disputes |
| **Prohibited Reinterpretations** | Canonical authority may not be delegated to automated systems. Canonical authority may not be self-claimed. Runtime systems may not acquire canonical authority through implementation. |
| **Lifecycle Notes** | Canonical authority assignments require governance ratification |

---

### semantic-ratification

| Field | Value |
|-------|-------|
| **Term** | semantic-ratification |
| **Canonical Definition** | The formal process of approving a semantic definition, vocabulary change, or authority assignment as canonical. Ratification requires human review and explicit acceptance. |
| **Owning Authority Layer** | Governance layer |
| **Related Contracts** | Reconciliation workflow, vocabulary registry |
| **Allowed Usage** | Approving vocabulary additions, confirming authority changes, resolving drift |
| **Prohibited Reinterpretations** | Ratification may not be automated. Ratification may not be implicit. AI assistance may inform ratification but may not perform ratification. |
| **Lifecycle Notes** | Ratification creates audit trail |

---

### runtime-result

| Field | Value |
|-------|-------|
| **Term** | runtime-result |
| **Canonical Definition** | A structured report of a runtime stage outcome. Runtime results are observational records that report what happened without authorizing further action. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | RuntimeResultBase, stage-specific result contracts |
| **Allowed Usage** | Reporting stage outcomes, preserving provenance, enabling diagnostics |
| **Prohibited Reinterpretations** | Runtime results do not authorize execution. Runtime results do not grant machine operation authority. Runtime results are observational, not prescriptive. |
| **Lifecycle Notes** | Result schema versions must be preserved for traceability |

---

### validation-result

| Field | Value |
|-------|-------|
| **Term** | validation-result |
| **Canonical Definition** | A runtime result reporting the outcome of intent validation. Validation results indicate conformance status without authorizing execution. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | RuntimeValidationResult |
| **Allowed Usage** | Reporting validation gate status, preserving warnings and errors, enabling diagnostic review |
| **Prohibited Reinterpretations** | Validation results do not authorize execution (execution_ready is always false). Validation results do not authorize machine operation (machine_operation_authorized is always false). |
| **Lifecycle Notes** | Validation gate values (green/yellow/red) are fixed vocabulary |

---

### geometry-resolution-result

| Field | Value |
|-------|-------|
| **Term** | geometry-resolution-result |
| **Canonical Definition** | A runtime result reporting the outcome of geometry resolution. Geometry resolution results record what geometry queries were performed without mutating geometry. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | RuntimeGeometryResolution |
| **Allowed Usage** | Reporting geometry lookup status, preserving query provenance, enabling traceability |
| **Prohibited Reinterpretations** | Geometry resolution does not mutate geometry. Geometry resolution does not create new canonical geometry. |
| **Lifecycle Notes** | Resolution status values (resolved/partial/placeholder/unsupported) are fixed vocabulary |

---

### plan-result

| Field | Value |
|-------|-------|
| **Term** | plan-result |
| **Canonical Definition** | A runtime result reporting the outcome of operation planning. Plan results record planning stage without generating toolpaths or machine coordinates. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | RuntimePlanResult |
| **Allowed Usage** | Reporting planning stage, preserving operation count, enabling progress tracking |
| **Prohibited Reinterpretations** | Plan results do not contain toolpaths. Plan results do not contain machine coordinates. Plan results do not authorize machine operation. |
| **Lifecycle Notes** | Planning stage values (placeholder/deterministic_stub/unsupported) are fixed vocabulary |

---

### preview-result

| Field | Value |
|-------|-------|
| **Term** | preview-result |
| **Canonical Definition** | A runtime result reporting the availability of preview artifacts. Preview results record preview stage without rendering engine integration. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | RuntimePreviewResult |
| **Allowed Usage** | Reporting preview availability, preserving artifact references, enabling visualization flow |
| **Prohibited Reinterpretations** | Preview results do not authorize execution. Preview results do not guarantee rendering fidelity. |
| **Lifecycle Notes** | Preview stage values (placeholder/preview_stub/unsupported) are fixed vocabulary |

---

### export-result

| Field | Value |
|-------|-------|
| **Term** | export-result |
| **Canonical Definition** | A runtime result reporting the outcome of export operations. Export results record export stage without generating machine output. |
| **Owning Authority Layer** | Runtime layer |
| **Related Contracts** | RuntimeExportResult |
| **Allowed Usage** | Reporting export availability, preserving format list, enabling artifact tracking |
| **Prohibited Reinterpretations** | Export results do not generate machine output (machine_output_generated is always false). Export results do not authorize machine operation. |
| **Lifecycle Notes** | Export stage values (placeholder/export_stub/unsupported) are fixed vocabulary |

---

## Constitutional Dependency

This vocabulary registry operates under the Repository Constitution (`REPOSITORY_CONSTITUTION.md`).

### Constitutional Invariants Applicable to Vocabulary

| Invariant | Application |
|-----------|-------------|
| Invariant 1: No subsystem may silently become ontology authority | Vocabulary terms require ratification, not implementation |
| Invariant 2: Runtime consumes ontology | Runtime may use vocabulary; runtime may not define vocabulary |
| Invariant 4: Review is not ratification | Reviewing vocabulary proposals does not create canonical terms |
| Invariant 8: Usage is not ratification | Widespread use of a term does not make it canonical |

### Ratification Requirement

All vocabulary additions, modifications, and deprecations require ratification per `GOVERNANCE_RATIFICATION_MODEL.md`.

```
New terms → VOCABULARY_RATIFICATION decision type
Modified terms → VOCABULARY_RATIFICATION decision type
Deprecated terms → VOCABULARY_RATIFICATION decision type
```

### Freeze Applicability

When `VOCAB_FREEZE` is active per `SEMANTIC_FREEZE_POLICY.md`:
- No new terms may be added to this registry
- Existing terms may be clarified (not redefined)
- Prohibited reinterpretations remain enforced

---

## Related Documents

- [CANONICAL_AUTHORITY_MAP.md](./CANONICAL_AUTHORITY_MAP.md) — ownership declarations
- [ONTOLOGY_RECONCILIATION_WORKFLOW.md](./ONTOLOGY_RECONCILIATION_WORKFLOW.md) — ratification process
- [ONTOLOGY_DRIFT_CLASSIFICATIONS.md](./ONTOLOGY_DRIFT_CLASSIFICATIONS.md) — drift detection
- [GOVERNANCE_AUTHORITY_HIERARCHY.md](./GOVERNANCE_AUTHORITY_HIERARCHY.md) — tier structure
- [REPOSITORY_CONSTITUTION.md](./REPOSITORY_CONSTITUTION.md) — constitutional authority
- [GOVERNANCE_RATIFICATION_MODEL.md](./GOVERNANCE_RATIFICATION_MODEL.md) — ratification workflow
- [SEMANTIC_FREEZE_POLICY.md](./SEMANTIC_FREEZE_POLICY.md) — freeze discipline
