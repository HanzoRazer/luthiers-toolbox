# C1 Inventory: Governance Integration Workstream

**Phase:** C1 — Collection  
**Date:** 2026-05-18  
**Status:** Inventory (no decisions made)  
**Scope:** Lifecycle registries, semantic registries, authority chains, enforcement infrastructure

---

## Purpose

This document inventories the governance infrastructure itself — the systems that govern semantic meaning across the repository. This is critical meta-inventory because these systems already act as constitutional infrastructure.

**Key pattern observed:** Governance infrastructure is already operational. Registry-based enforcement exists. Authority chains are declared. The question is not "does governance exist" but "is existing governance federated with emerging ontology?"

---

## 1. Lifecycle Registry Vocabulary

**Source:** `docs/governance/ontology/lifecycle_registry.json`  
**Role:** Normalized lifecycle state vocabulary across all domains  
**Version:** 1.0.0

### 1.1 Canonical Lifecycle Terms

| Term | Owner Domain | Classification | Runtime Meaning |
|------|--------------|----------------|-----------------|
| `canonical` | Governance Layer | CANONICAL | Stable, production-ready, governance-ratified |
| `supported` | Runtime Classification | CANONICAL | Can execute without limitation |
| `semantic_only` | CAD Translation Governance | CANONICAL | Schema validation passes; no output generated |
| `prototype` | Topology Builder Governance | CANONICAL | G0 acceptable, warnings allowed |
| `partial_prototype` | Topology Builder Governance | CANONICAL | Partial output with explicit warnings |
| `unsupported_runtime` | Topology Builder Governance | CANONICAL | Explicit failure with classification |
| `research_required` | Topology Builder Governance | CANONICAL | Blocked pending implementation |
| `governed` | Governance Layer | CANONICAL | Governance rules apply |
| `governed_experimental` | Governance Layer | CANONICAL | Governance applies but stability not guaranteed |
| `experimental` | Governance Layer | CANONICAL | No stability guarantees |
| `quarantine` | Governance Layer | CANONICAL | Isolated from production pending review |
| `validation_only` | Validation Layer | CANONICAL | No side effects, report only |
| `preview_only` | CAM Export Governance | CANONICAL | Not suitable for manufacturing |
| `machine_candidate` | CAM Export Governance | CANONICAL | Requires authorization gate |
| `blocking` | Topology Failure Classification | CANONICAL | Immediate rejection, no output |
| `major` | Topology Failure Classification | CANONICAL | PROTOTYPE: warning; PRODUCTION: blocking |
| `warning` | Topology Failure Classification | CANONICAL | Logged, output produced |

### 1.2 Known Lifecycle Conflicts (Registry-Declared)

| Terms | Nature | Resolution |
|-------|--------|------------|
| `semantic_only` vs `unsupported` | Schema validity semantics | semantic_only = valid schema; unsupported = invalid |
| `supported` vs `supported_prototype` | Domain terminology | supported = cad_semantics; supported_prototype = topology_builder |

---

## 2. Semantic Registry Vocabulary

**Source:** `docs/governance/ontology/semantic_registry.json`  
**Role:** Machine-readable registry of canonical semantic terms  
**Version:** 1.0.0

### 2.1 Canonical Semantic Terms

| Term | Owner Domain | Authority Tier | Prohibited Meanings |
|------|--------------|----------------|---------------------|
| `intent` | Governance Layer | 1 | Execution state, runtime behavior |
| `runtime` | Runtime Layer | 3 | Semantic authority, vocabulary definition |
| `translator` | CAM Export / Serialization | 2 | Geometry generator, runtime planner |
| `validation` | Validation Layer | 2 | Data mutation, semantic authority |
| `provenance` | Governance Layer | 1 | Fabricated history, inferred origin |
| `artifact` | Governance Layer | 1 | Implicit creation, undeclared outputs |
| `topology` | CAD Topology Governance | 2 | Geometry data, coordinate values |
| `morphology` | Geometry Layer / MRP | 2 | Runtime execution, CAM operations |
| `feasibility` | RMOS / Feasibility Layer | 2 | Visualization authority, geometry definition |
| `governance` | Governance Layer | 1 | Runtime execution, implementation details |

### 2.2 Authority Tier Distribution

| Tier | Count | Description |
|------|-------|-------------|
| Tier 1 | 5 | Structural invariants (governance, provenance, artifact, intent, governance) |
| Tier 2 | 6 | Domain governance (translator, validation, topology, morphology, feasibility) |
| Tier 3 | 1 | Operational policies (runtime) |

---

## 3. Authority Chain Registry

**Source:** `docs/governance/ontology/authority_chain_registry.json`  
**Role:** Machine-readable authority chain definitions  
**Version:** 1.0.0

### 3.1 Declared Authority Chains

| Chain | Sequence | Key Invariants |
|-------|----------|----------------|
| `geometry_authority_chain` | Blueprint → IBG → BOE → CadSemantics → TopologyBuilder → ShellValidation → Translator | Downstream cannot redefine upstream geometry |
| `governance_tier_chain` | Tier 1 → Tier 2 → Tier 3 | Lower tiers cannot violate higher tier constraints |
| `semantic_authority_chain` | Vocabulary Registry → Domain Owner → Operational Implementation → Runtime Consumer | Runtime systems consume but do not define ontology |
| `export_lifecycle_chain` | Export Request → Feasibility Check → Validation → Translation → Authorization Gate → Machine Output | No stage may bypass feasibility check |
| `topology_construction_chain` | cad_semantics → TopologyBuilder → TopologyValidation → Translator | Translator serializes but does not generate topology |
| `adaptive_intelligence_chain` | Deterministic Spine → AI Advisory (sandboxed) → Human Ratification → Canonical Implementation | AI assistance is advisory only |

### 3.2 Domain Ownership Declarations

| Domain | Canonical Owner | Authority Tier | Forbidden Ownership |
|--------|-----------------|----------------|---------------------|
| `geometry` | Geometry Layer | 2 | Runtime systems may not redefine |
| `morphology` | Geometry Layer | 2 | Runtime systems may not redefine |
| `feasibility` | Feasibility Layer | 2 | Visualization may not claim |
| `export_lifecycle` | Export Governance Layer | 2 | Dispatchers may not bypass |
| `serialization` | Serialization Layer | 2 | Execution systems may not define |
| `validation` | Validation Layer | 2 | Validated systems may not override |
| `vocabulary` | Governance Layer | 1 | No subsystem may independently create |
| `topology` | CAD Topology Governance | 2 | Translators may not generate |

---

## 4. Ontology Alias Registry

**Source:** `docs/governance/ontology/ontology_alias_registry.json`  
**Role:** Maps aliases and transitional names to canonical terms  
**Version:** 1.0.0

### 4.1 Active Aliases

| Alias | Canonical Term | Domain | Status |
|-------|----------------|--------|--------|
| `SUPPORTED_PROTOTYPE` | `supported_prototype` | topology_builder | active |
| `PARTIAL_PROTOTYPE` | `partial_prototype` | topology_builder | active |
| `UNSUPPORTED_RUNTIME` | `unsupported_runtime` | topology_builder | active |
| `UNSUPPORTED_TOPOLOGY_RUNTIME` | `unsupported_runtime` | translator_rejection | active |
| `RESEARCH_REQUIRED` | `research_required` | topology_builder | active |
| `SUPPORTED` | `supported` | cad_semantics | active |
| `SEMANTIC_ONLY` | `semantic_only` | cad_semantics | active |
| `UNSUPPORTED` | `unsupported` | cad_semantics | active |
| `BLOCKING` | `blocking` | topology_failure | active |
| `MAJOR` | `major` | topology_failure | active |
| `WARNING` | `warning` | topology_failure | active |
| `ACCEPTABLE` | `acceptable` | topology_failure | active |
| `PROTOTYPE` | `prototype` | topology_builder | active |
| `PRODUCTION` | `production` | topology_builder | active |

### 4.2 Transitional Aliases

| Alias | Canonical Term | Domain | Status |
|-------|----------------|--------|--------|
| `RESEARCH_ONLY` | `research_required` | documentation | transitional |
| `governed_execution` | `governed` | export_lifecycle | transitional |

### 4.3 Deprecated Terms

| Term | Replacement | Deprecation Date | Reason |
|------|-------------|------------------|--------|
| `uncontrolled` | `experimental` | 2026-05-16 | Ambiguous term |

### 4.4 Domain Vocabulary Index

| Domain | Terms | Source File |
|--------|-------|-------------|
| `topology_builder` | supported_prototype, partial_prototype, unsupported_runtime, research_required, prototype, production | `runtime_support.py` |
| `cad_semantics` | supported, semantic_only, unsupported | `cad_semantics.py` |
| `topology_failure` | blocking, major, warning, acceptable | Governance docs |
| `governance_tier` | tier_1, tier_2, tier_3 | Authority hierarchy |

---

## 5. CI Governance Enforcement Policy

**Source:** `docs/governance/ontology/ontology_ci_policy.json`  
**Role:** Machine-readable enforcement policy  
**Enforcement Phase:** 2 (Advisory and warnings active, blocking for authority violations only)

### 5.1 Enforcement Severity Vocabulary

| Severity | Exit Code | CI Behavior | Description |
|----------|-----------|-------------|-------------|
| `informational` | 0 | no_action | Reporting only |
| `advisory` | 0 | log_finding | Visible governance concern |
| `warning` | 0 | log_prominently | Likely future violation |
| `blocking` | 1 | fail_ci | Ontology integrity failure |
| `quarantine` | 2 | reserved | Forbidden semantic state (not activated) |

### 5.2 Active Enforcement Checks

| Check | Script | Severity | Tier |
|-------|--------|----------|------|
| `audit_authority_chains` | `audit_authority_chains.py` | blocking | ci |
| `validate_lifecycle_terms` | `validate_lifecycle_terms.py` | warning | ci |
| `detect_semantic_drift` | `detect_semantic_drift.py` | advisory | nightly |
| `list_semantic_owners` | `list_semantic_owners.py` | informational | manual |

### 5.3 Escalation Rules

| Escalation | Triggers |
|------------|----------|
| advisory → warning | Term in new code, multiple locations, cross-domain use |
| warning → blocking | Authority inversion, semantic corruption, ownership conflict |
| blocking → quarantine | Immediate isolation needed, cross-team review required |

---

## 6. Governance Meta-Analysis

### 6.1 Governance Infrastructure Already Operational

| Component | Status | Evidence |
|-----------|--------|----------|
| Lifecycle registry | Operational | 17 canonical terms defined |
| Semantic registry | Operational | 10 canonical concepts defined |
| Authority chains | Operational | 6 chains with invariants |
| Domain ownership | Operational | 8 domains with owners |
| Alias mapping | Operational | 14 active aliases |
| CI enforcement | Operational | 4 checks, severity-based |
| Baseline drift | Captured | JSON baseline exists |

### 6.2 Constitutional Status Assessment

| Question | Finding |
|----------|---------|
| Does governance infrastructure exist? | Yes — registries, enforcement, baselines |
| Is governance infrastructure federated? | Partial — CAM/Topology integrated; IBG/Acoustics not yet |
| Are authority chains declared? | Yes — 6 formal chains |
| Are domain boundaries enforced? | Partial — CI checks active but advisory-level |
| Is drift baseline captured? | Yes — `ontology_drift_baseline_2026_05.json` |

### 6.3 Gap: IBG Not Yet Federated

| IBG Component | Registry Status | Authority Chain Status |
|---------------|-----------------|------------------------|
| ZoneId vocabulary | Not in lifecycle_registry | Not in geometry_authority_chain |
| PrimitiveType vocabulary | Not in semantic_registry | Not in authority declarations |
| VariantGrammar vocabulary | Not in alias_registry | Not in domain_ownership |
| Morphology Harvest | Not registered | Not in semantic_authority_chain |

**Finding:** IBG is the largest unfederated ontology incubation surface. Governance infrastructure exists but does not yet consume IBG semantics.

---

## 7. Cross-Reference to Other Inventories

### 7.1 Terms in Lifecycle Registry vs Inventoried Terms

| Inventoried Term | In Lifecycle Registry? | Status |
|------------------|------------------------|--------|
| CAM `unsupported` | No (only `unsupported_runtime`) | **Gap** |
| CAM `placeholder` | No | **Gap** |
| CAM `experimental` | Yes | Aligned |
| CAM `deprecated` | No | **Gap** |
| CAM `governed` | Yes | Aligned |
| Topology `SUPPORTED_PROTOTYPE` | Yes (as alias) | Aligned |
| IBG `ZoneId` | No | **Gap** |
| IBG `PrimitiveType` | No | **Gap** |
| IBG `BodyMorphologyClass` | No | **Gap** |
| Acoustics `MeasurementSource` | No | Not needed (local) |

### 7.2 Authority Chains vs Inventoried Dependencies

| Inventoried Dependency | Declared in Authority Chain? |
|------------------------|------------------------------|
| CAM → CadSemantics | Yes (geometry_authority_chain) |
| TopologyBuilder → CadSemantics | Yes (topology_construction_chain) |
| IBG → BOE | Yes (geometry_authority_chain) |
| Harvest → IBG | No | **Gap** |
| Runtime → PluginRegistry | No | **Gap** |
| Translator → Topology | Yes (topology_construction_chain) |

---

## 8. Semantic Collision Summary (Governance)

### 8.1 Governance Infrastructure Collisions

No new collisions discovered. Governance registries are well-organized with explicit conflict documentation.

### 8.2 Constitutional Gaps

| Gap | Risk | Priority |
|-----|------|----------|
| IBG vocabulary not in registries | HIGH | IBG terms calcifying without governance |
| Harvest not in authority chains | MEDIUM | Normalization behavior ungovernanced |
| CAM placeholders not registered | LOW | Local vocabulary, contained |

---

## 9. Constitutional Observation

### 9.1 Governance Infrastructure Is Not Meta-Governance

Key finding: The governance registries are **operational governance infrastructure**, not theoretical documentation. They:

1. Define canonical vocabulary with lifecycle states
2. Declare authority chains with invariants
3. Map aliases to canonical terms
4. Enforce via CI with severity-based escalation
5. Capture drift baselines for comparison

This means the repository already has constitutional infrastructure. The question is not "build governance" but "federate emerging ontology into existing governance."

### 9.2 IBG Federation Is the Critical Path

The largest constitutional gap is IBG federation:

- 72 terms in pre-governance sandbox state
- Zone/primitive/morphology vocabulary operating without registration
- Authority chain from Blueprint → IBG → BOE exists but IBG internals unfederated

This is the primary C2 reconciliation target.

---

## 10. Related Documents

- `docs/governance/ontology/lifecycle_registry.json`
- `docs/governance/ontology/semantic_registry.json`
- `docs/governance/ontology/authority_chain_registry.json`
- `docs/governance/ontology/ontology_alias_registry.json`
- `docs/governance/ontology/ontology_ci_policy.json`
- `docs/governance/coordination/C1_GEOMETRY_TOPOLOGY_INVENTORY.md`
- `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md`

---

## C1 Status

**Collected:** Yes  
**Governance Components Inventoried:** 5 registries, 4 enforcement checks  
**Terms in Registries:** 17 lifecycle + 10 semantic + 14 aliases  
**Authority Chains Declared:** 6  
**Domain Ownerships Declared:** 8  
**IBG Federation Status:** NOT FEDERATED (72 terms)  
**Decisions Made:** None  
**Next Phase:** C2 reconciliation with IBG federation as critical path
