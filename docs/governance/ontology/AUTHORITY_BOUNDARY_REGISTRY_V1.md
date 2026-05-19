# Authority Boundary Registry V1

**Status:** DRAFT FOR GOVERNANCE RECONCILIATION  
**Date:** 2026-05-16  
**Authority:** NOT CANONICAL — NOT ENFORCEMENT AUTHORITY  
**Scope:** Ontology-related authority boundaries only  
**Track:** Instrument Knowledge Reconciliation (Sandbox)

---

## 1. Authority Statement

This registry is:

```
DRAFT FOR GOVERNANCE RECONCILIATION
NOT CANONICAL
NOT ENFORCEMENT AUTHORITY
```

This document documents semantic ownership boundaries. It does NOT:

- Create canonical ontology
- Resolve semantic conflicts automatically
- Override existing governance hierarchy
- Mutate runtime systems
- Authorize migrations
- Redefine subsystem responsibilities

---

## 2. Purpose and Scope

### Purpose

This registry provides:

```
explicit semantic ownership visibility
```

NOT:

```
semantic authority implementation
```

### What This Registry Documents

| Documentation Type | Description |
|--------------------|-------------|
| Ownership claims | What each subsystem explicitly owns |
| Ownership exclusions | What each subsystem must NOT own |
| Unresolved overlaps | Where ownership is ambiguous |
| Governance escalation requirements | When conflicts require arbitration |

### Scope Limitation

This V1 registry covers **ontology-related authority boundaries only**:

- Tier 3 evidence staging
- Tier 2 curated review
- Tier 1 canonical target (proposed)
- Ontology drafts
- Promotion review manifest
- Observability layer
- Instrument data legacy sources

It does NOT cover full RMOS, CAM, MRP, or all 7 topology systems. Those systems appear only as upstream/downstream references to avoid conflation.

---

## 3. Ownership Model

### Ownership Categories

| Category | Definition |
|----------|------------|
| `CANONICAL_ONTOLOGY` | Authority to define semantic truth |
| `CURATED_REVIEW` | Authority to review and document evidence |
| `EVIDENCE_STAGING` | Authority to hold unreviewed evidence |
| `RUNTIME_CONSUMPTION` | Authority to read and use data |
| `OBSERVABILITY` | Authority to inspect and report governance state |
| `MIGRATION_COORDINATION` | Authority to plan data movement |
| `PROVENANCE_TRACKING` | Authority to record origin and lineage |
| `GOVERNANCE_INSTRUMENTATION` | Authority to document governance process |

### Critical Distinction

```
consumption does not imply ownership
```

A subsystem may consume data without owning its semantic definition. Ownership establishes authority over meaning; consumption establishes authority over usage.

### Category vs. Maturity

```
categories describe authority type
not implementation maturity
```

A subsystem with `EVIDENCE_STAGING` authority may be fully implemented or partially complete. The category describes what kind of authority it has, not how mature that authority is.

---

## 4. Authority Boundary Record Structure

Each subsystem entry follows this structure:

```
### Boundary Record: [Subsystem Name]

boundary_id:
subsystem_name:
owns:
must_not_own:
consumes:
produces:
authority_scope:
non_authority_scope:
upstream_dependencies:
downstream_consumers:
known_conflicts:
unresolved_questions:
escalation_authority:
status:
```

---

## 5. Non-Ownership Requirements

Every subsystem entry MUST define what the subsystem explicitly must NOT own.

### Why Non-Ownership Matters

Non-ownership boundaries prevent:

- Implicit authority expansion
- Accidental semantic creep
- Domain boundary violations
- Runtime-local ontology creation

### Enforcement Model

Non-ownership violations are:

```
governance findings, not CI enforcement
```

Observability may flag non-ownership violations. Enforcement authority is separate.

---

## 6. Authority Boundary Records

### Boundary Record: Tier 3 Evidence Staging

```
boundary_id: BOUNDARY-T3-STAGING-001
subsystem_name: Tier 3 Evidence Staging
owns:
  - Raw extracted evidence provenance
  - Extraction metadata (confidence, method, timestamp)
  - Staging location governance (morphology_harvest/outputs/)
must_not_own:
  - Canonical instrument semantics
  - Runtime authorization
  - Ontology ratification
  - Dimensional truth
  - Promotion decisions
consumes:
  - Blueprint images
  - Vectorizer parameters
  - Extraction configuration
produces:
  - Staged extraction evidence
  - Extraction provenance records
  - Confidence metrics
authority_scope: EVIDENCE_STAGING
non_authority_scope:
  - CANONICAL_ONTOLOGY
  - CURATED_REVIEW (review is separate tier)
  - RUNTIME_CONSUMPTION (staging is not consumable)
upstream_dependencies:
  - Vectorizer (extraction source)
  - Blueprint storage (input source)
downstream_consumers:
  - Tier 2 curated review (after human review)
known_conflicts:
  - Risk of accidental canonical treatment (INSTRUMENT_DATA_STORAGE_AUDIT finding)
unresolved_questions:
  - Who enforces staging isolation?
  - How long can evidence remain in staging?
escalation_authority: Governance committee
status: DOCUMENTED
```

---

### Boundary Record: Tier 2 Curated Review

```
boundary_id: BOUNDARY-T2-REVIEW-001
subsystem_name: Tier 2 Curated Review
owns:
  - Review documentation
  - Promotion review provenance
  - Reviewer confidence assessments
  - Conflict flagging
  - Normalization justification records
must_not_own:
  - Canonical ratification (Tier 1 authority)
  - Runtime execution authority
  - Ontology mutation authority
  - Semantic conflict resolution
  - Automatic promotion
consumes:
  - Tier 3 staged evidence
  - Ontology draft definitions
  - Instrument specs (for validation)
produces:
  - Curated candidate records
  - Review manifests (per PROMOTION_REVIEW_MANIFEST_V1)
  - Rejection/deferral records
authority_scope: CURATED_REVIEW
non_authority_scope:
  - CANONICAL_ONTOLOGY
  - RUNTIME_CONSUMPTION (curated is not consumable)
upstream_dependencies:
  - Tier 3 evidence staging
  - Ontology drafts (for field mapping)
downstream_consumers:
  - Tier 1 canonical authority (after governance approval)
known_conflicts:
  - curated/ tier does not exist yet (INSTRUMENT_DATA_STORAGE_AUDIT finding)
  - Review workflow not implemented
unresolved_questions:
  - Who is authorized to perform promotion review?
  - What is minimum confidence threshold?
  - How long can records remain in Tier 2?
escalation_authority: Governance committee
status: PROPOSED
```

---

### Boundary Record: Tier 1 Canonical Authority (Proposed)

```
boundary_id: BOUNDARY-T1-CANONICAL-001
subsystem_name: Tier 1 Canonical Authority
owns:
  - Canonical instrument semantic definitions
  - Governed dimensional truth
  - Ratified field meanings
  - Runtime-consumable instrument data
must_not_own:
  - Evidence extraction logic
  - Review process mechanics
  - Staging lifecycle
  - Observability implementation
consumes:
  - Tier 2 curated candidates (after governance approval)
  - Ratified ontology definitions
produces:
  - Canonical instrument records (data_registry/system/instruments/)
  - Authoritative dimensional data
  - Runtime-safe instrument specifications
authority_scope: CANONICAL_ONTOLOGY
non_authority_scope:
  - EVIDENCE_STAGING
  - CURATED_REVIEW
  - OBSERVABILITY
upstream_dependencies:
  - Tier 2 curated review
  - Ontology ratification process
  - Governance committee approval
downstream_consumers:
  - Runtime systems (via read-only access)
  - RMOS (manufacturing feasibility)
  - CAM (toolpath generation)
  - Body grid (morphology classification)
known_conflicts:
  - Multiple legacy sources claim canonical authority (INSTRUMENT_DATA_STORAGE_AUDIT)
  - instrument_specs.py declares itself canonical
  - instrument_model_registry.json acts as de facto master
  - body_templates.json in data_registry/system/ is potential canonical
unresolved_questions:
  - Which existing source becomes canonical?
  - How are legacy sources deprecated?
  - Who approves promotion to Tier 1?
escalation_authority: Governance committee
status: PROPOSED
```

---

### Boundary Record: Ontology Drafts

```
boundary_id: BOUNDARY-ONTO-DRAFT-001
subsystem_name: Ontology Governance Drafts
owns:
  - Proposed semantic definitions
  - Measurement convention documentation
  - Field meaning proposals
  - Terminology normalization proposals
must_not_own:
  - Automatic enforcement authority
  - Runtime semantic truth
  - CI blocking policy
  - Migration authorization
  - Canonical ratification
consumes:
  - Repository codebase analysis
  - Existing storage audit findings
  - Cross-source comparison data
produces:
  - Draft ontology documents (INSTRUMENT_DIMENSION_ONTOLOGY_V1.md)
  - Semantic conflict documentation
  - Governance question registry
authority_scope: GOVERNANCE_INSTRUMENTATION
non_authority_scope:
  - CANONICAL_ONTOLOGY (drafts are not canonical)
  - RUNTIME_CONSUMPTION
upstream_dependencies:
  - INSTRUMENT_DATA_STORAGE_AUDIT findings
  - Existing governance documents
downstream_consumers:
  - Governance committee (for ratification review)
  - Tier 2 curated review (for field mapping guidance)
  - Observability layer (for drift monitoring)
known_conflicts:
  - 7 foundational fields remain UNRESOLVED (INSTRUMENT_DIMENSION_ONTOLOGY_V1)
  - Physical vs bbox convention conflict documented but not ratified
unresolved_questions:
  - When do draft proposals become ratification candidates?
  - Who reviews draft proposals?
  - Can drafts be versioned independently?
escalation_authority: Governance committee
status: DOCUMENTED
```

---

### Boundary Record: Promotion Review Manifest

```
boundary_id: BOUNDARY-PROMO-REVIEW-001
subsystem_name: Promotion Review Manifest
owns:
  - Review decision documentation
  - Provenance requirement definitions
  - Rejection pathway definitions
  - Reviewer authority boundary definitions
must_not_own:
  - Canonical truth creation
  - Automatic promotion execution
  - Runtime data modification
  - Semantic conflict resolution
  - Ontology mutation
consumes:
  - Tier 3 staged evidence
  - Ontology field definitions (for mapping)
  - Review decision inputs
produces:
  - Promotion review manifests
  - Rejection records
  - Deferral records
  - Provenance documentation
authority_scope: CURATED_REVIEW, PROVENANCE_TRACKING
non_authority_scope:
  - CANONICAL_ONTOLOGY
  - RUNTIME_CONSUMPTION
  - MIGRATION_COORDINATION
upstream_dependencies:
  - Tier 3 evidence staging
  - INSTRUMENT_DIMENSION_ONTOLOGY_V1 (field semantics)
downstream_consumers:
  - Tier 1 canonical authority (ratification inputs)
known_conflicts:
  - Governance workflow not yet implemented
  - Reviewer pool not defined
unresolved_questions:
  - Who is authorized to perform promotion review?
  - What is minimum confidence threshold for promotion?
  - How are conflicts escalated from review?
escalation_authority: Governance committee
status: DOCUMENTED
```

---

### Boundary Record: Observability Layer

```
boundary_id: BOUNDARY-OBSERVE-001
subsystem_name: Ontology Governance Observability Layer
owns:
  - Governance state visibility
  - Drift finding documentation
  - Lifecycle state tracking
  - Provenance audit trails
  - Signal category definitions
must_not_own:
  - Enforcement authority
  - Semantic ratification
  - Automatic escalation authority
  - CI blocking decisions (defined by ontology_ci_policy.json)
  - Canonical promotion
  - Conflict resolution
consumes:
  - Ontology drift baseline (ontology_drift_baseline_2026_05.json)
  - CI policy definitions (ontology_ci_policy.json)
  - Cross-source semantic comparisons
produces:
  - Governance findings
  - Drift lifecycle state records
  - Escalation recommendations (not decisions)
authority_scope: OBSERVABILITY, GOVERNANCE_INSTRUMENTATION
non_authority_scope:
  - CANONICAL_ONTOLOGY
  - RUNTIME_CONSUMPTION
  - MIGRATION_COORDINATION
upstream_dependencies:
  - ontology_ci_policy.json (severity definitions)
  - ontology_drift_baseline_2026_05.json (baseline state)
  - INSTRUMENT_DIMENSION_ONTOLOGY_V1 (field semantics)
downstream_consumers:
  - Governance committee (decision inputs)
  - CI pipelines (severity reporting)
  - Developer tooling (visibility)
known_conflicts:
  - Authority naming inconsistency: "morphology" (Geometry Layer / MRP vs Geometry Layer)
  - Authority naming inconsistency: "feasibility" (RMOS / Feasibility Layer vs Feasibility Layer)
unresolved_questions:
  - Can observability findings trigger automatic escalation?
  - Should observability integrate with RMOS governance?
  - How do findings propagate to downstream repos?
escalation_authority: Governance committee
status: DOCUMENTED
```

---

### Boundary Record: Instrument Data Legacy Sources

```
boundary_id: BOUNDARY-LEGACY-001
subsystem_name: Instrument Data Legacy Sources
owns:
  - Historical dimensional data (legacy authority)
  - Implementation-specific instrument configurations
must_not_own:
  - Forward-looking canonical ontology
  - Semantic arbitration authority
  - New instrument data creation
  - Ontology field definition authority
consumes:
  - (Self-contained legacy data)
produces:
  - Dimensional values (consumed by 50+ locations per audit)
  - Body outline coordinates
  - Model metadata
authority_scope: RUNTIME_CONSUMPTION (legacy)
non_authority_scope:
  - CANONICAL_ONTOLOGY (legacy ≠ canonical)
  - CURATED_REVIEW
  - EVIDENCE_STAGING
upstream_dependencies:
  - Original instrument specifications (external)
downstream_consumers:
  - CAM operations
  - Body grid
  - Geometry calculators
  - Runtime systems (via adapters)
known_conflicts:
  - 7 distinct storage locations (INSTRUMENT_DATA_STORAGE_AUDIT)
  - Stratocaster: 406mm vs 396mm vs 458.8mm (3 sources, 3 conventions)
  - Les Paul: 450mm vs 444mm vs 269.2mm (physical vs bbox confusion)
  - Terminology drift: lower_bout_mm vs lower_bout_width_mm vs body_width_mm
  - instrument_specs.py claims canonical but conflicts with body_templates.json
  - GEN-5 consolidation planned but never executed
unresolved_questions:
  - Which legacy source becomes canonical?
  - How are legacy sources deprecated?
  - Can legacy adapters bridge to new canonical?
  - How to handle 50+ consumers during migration?
escalation_authority: Governance committee
status: UNRESOLVED
```

---

## 7. Known Authority Overlaps

### Overlap 1: Canonical Dimension Authority

```
overlap_id: OVERLAP-CANONICAL-DIM-001
affected_systems:
  - instrument_specs.py (claims canonical)
  - instrument_model_registry.json (de facto master)
  - body_templates.json (data_registry/system/)
  - body_outlines.py (outline authority)
overlap_type: AUTHORITY_CONFLICT
description: Multiple systems claim canonical authority over instrument dimensions
governance_risk: Consumers receive different values from different sources
current_status: DOCUMENTED (INSTRUMENT_DATA_STORAGE_AUDIT)
escalation_recommendation: Governance arbitration required to designate single canonical source
```

---

### Overlap 2: Measurement Convention Conflation

```
overlap_id: OVERLAP-CONVENTION-001
affected_systems:
  - instrument_specs.py (physical measurement convention)
  - body_outlines.py (bounding box convention)
  - body_templates.json (template convention)
overlap_type: ONTOLOGY_DRIFT
description: Same field names used for different measurement conventions
governance_risk: 62.8mm variance on Stratocaster body_length not measurement error but convention difference
current_status: DOCUMENTED (INSTRUMENT_DIMENSION_ONTOLOGY_V1)
escalation_recommendation: Ontology ratification to separate physical vs bbox fields
```

---

### Overlap 3: Staging → Canonical Boundary

```
overlap_id: OVERLAP-STAGING-001
affected_systems:
  - morphology_harvest/outputs/ (staging)
  - data_registry/curated/ (does not exist)
  - data_registry/system/ (canonical target)
overlap_type: DOMAIN_BOUNDARY_AMBIGUITY
description: Tier 2 curated layer not implemented; risk of staging → canonical bypass
governance_risk: Evidence treated as canonical without review
current_status: DOCUMENTED (INSTRUMENT_DATA_STORAGE_AUDIT)
escalation_recommendation: Implement curated tier before any migration
```

---

### Overlap 4: Authority Registry Naming

```
overlap_id: OVERLAP-NAMING-001
affected_systems:
  - semantic_registry.json
  - authority_chain_registry.json
overlap_type: AUTHORITY_CONFLICT (naming only)
description: Same organizational unit referenced with different names
examples:
  - morphology: "Geometry Layer / MRP" vs "Geometry Layer"
  - feasibility: "RMOS / Feasibility Layer" vs "Feasibility Layer"
governance_risk: Advisory only; not actual ownership conflict
current_status: BASELINED (ontology_drift_baseline_2026_05.json)
escalation_recommendation: Normalize naming in future sprint
```

---

### Overlap 5: Terminology Drift Across Sources

```
overlap_id: OVERLAP-TERMINOLOGY-001
affected_systems:
  - INSTRUMENT_SPECS (lower_bout_mm)
  - GuitarDimensions (body_width_mm)
  - body_outlines.py (width_mm, height_mm)
  - body_templates.json (length_mm, width_mm)
overlap_type: TERM_COLLISION
description: Same semantic concept uses different field names; same field name means different things
governance_risk: Integration failures; silent semantic corruption
current_status: DOCUMENTED (INSTRUMENT_DIMENSION_ONTOLOGY_V1)
escalation_recommendation: Ontology ratification with normalization mappings
```

---

## 8. Escalation Model

### Escalation Flow

```
discovery
→ documentation
→ governance review
→ ontology arbitration
→ ratification or deferral
```

### Stage Definitions

| Stage | Output | Owner |
|-------|--------|-------|
| Discovery | Finding report | Observability layer |
| Documentation | Conflict record | Ontology drafts |
| Governance review | Review decision | Governance committee |
| Ontology arbitration | Resolution proposal | Ontology authors |
| Ratification | Canonical decision | Governance authority |
| Deferral | Documented postponement | Governance committee |

### Prohibited Escalation Patterns

```
implicit ownership acquisition through usage
```

The following are explicitly forbidden:

| Pattern | Reason |
|---------|--------|
| Usage → Ownership | Frequency does not establish authority |
| Staging → Canonical (implicit) | Bypasses review tier |
| Runtime → Ontology | Runtime cannot define semantics |
| Consumer → Owner | Consumption ≠ Ownership |
| Convenience → Authority | Implementation ease ≠ Governance |

---

## 9. Relationship to Existing Governance Documents

### Document Positioning

This registry is:

```
authority visibility infrastructure
```

NOT:

```
ontology authority itself
```

### Document Relationships

| Document | Relationship |
|----------|--------------|
| `INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` | Sources field semantic conflicts |
| `PROMOTION_REVIEW_MANIFEST_V1.md` | Sources tier boundary definitions |
| `ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md` | Sources lifecycle states and signals |
| `GOVERNANCE_AUTHORITY_HIERARCHY.md` | Sources tier authority model |
| `INSTRUMENT_DATA_STORAGE_AUDIT.md` | Sources storage topology and conflicts |
| `GOVERNANCE_TOPOLOGY_MAP.md` | References full system inventory (out of scope) |

### This Registry Does NOT

- Supersede GOVERNANCE_AUTHORITY_HIERARCHY.md
- Redefine GOVERNANCE_TOPOLOGY_MAP.md systems
- Override ontology_ci_policy.json enforcement
- Replace ontology_drift_baseline_2026_05.json

---

## 10. Forbidden Governance Anti-Patterns

### Anti-Pattern 1: Implicit Authority Expansion

```
FORBIDDEN: Subsystem acquiring ownership without governance approval
REASON: All ownership changes require explicit governance decision
```

### Anti-Pattern 2: Runtime-Local Ontology Ownership

```
FORBIDDEN: Runtime defining semantic meaning for its domain
REASON: Ontology authority belongs to governance, not runtime
```

### Anti-Pattern 3: Staging Becoming Canonical Through Persistence

```
FORBIDDEN: Tier 3 evidence treated as Tier 1 because it's "the only data"
REASON: Persistence does not imply promotion
```

### Anti-Pattern 4: Consumer Adoption Implying Ratification

```
FORBIDDEN: "Everyone uses this source, so it's canonical"
REASON: Adoption frequency ≠ Governance ratification
```

### Anti-Pattern 5: Semantic Ownership Inferred From Implementation Convenience

```
FORBIDDEN: "This subsystem already has the data, so it owns the semantics"
REASON: Data location ≠ Semantic authority
```

### Anti-Pattern 6: Observability Acting As Governance Authority

```
FORBIDDEN: Observability findings automatically becoming enforcement
REASON: Observability reports; governance decides
```

---

## 11. Open Governance Questions

| # | Question | Impact | Proposed Owner |
|---|----------|--------|----------------|
| 1 | How are cross-domain ownership disputes arbitrated? | Conflict resolution | Governance committee |
| 2 | Can ownership be shared across governance layers? | Authority model | Governance committee |
| 3 | How should temporary ownership transfer be modeled? | Migration workflow | Architecture team |
| 4 | Should authority registries become machine-readable later? | Tooling integration | Observability maintainers |
| 5 | Who approves ownership reassignment? | Change management | Governance committee |
| 6 | How are legacy owners deprecated? | Migration safety | Governance committee |
| 7 | Can multiple subsystems have CANONICAL_ONTOLOGY for different domains? | Domain boundaries | Architecture team |
| 8 | What happens when upstream dependency changes ownership? | Dependency management | Governance committee |
| 9 | Should ownership boundaries be versioned with ontology documents? | Versioning strategy | Observability maintainers |
| 10 | How do ownership boundaries propagate to downstream repositories? | Multi-repo governance | Architecture team |

---

## 12. Document Lifecycle

| Phase | Status | Date |
|-------|--------|------|
| Initial draft | COMPLETE | 2026-05-16 |
| Governance review | PENDING | — |
| Ratification | PENDING | — |

---

## 13. Terminology Note

**Data Promotion Tiers vs. Governance Authority Tiers**

This document uses "Tier 1/2/3" to describe data promotion stages (Canonical/Curated/Staging). This is distinct from `GOVERNANCE_AUTHORITY_HIERARCHY.md` which uses "Tier 1/2/3" for governance authority strata (Structural Invariants/Domain Governance/Operational Policies). These are separate semantic systems. See `GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md` for disambiguation.

---

## 14. Related Documents

### Governance Stack Documents

- `docs/governance/ontology/INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` — Field semantic definitions
- `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md` — Tier 3→2 review governance
- `docs/governance/ontology/ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md` — Governance-state visibility
- `docs/governance/ontology/GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md` — Stack consistency verification

### Audit Documents

- `docs/governance/INSTRUMENT_DATA_STORAGE_AUDIT.md` — Storage topology
- `docs/governance/GOVERNANCE_TOPOLOGY_MAP.md` — Full system inventory

### Authority Documents

- `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md` — Governance authority tiers (distinct from data promotion tiers)

### Baseline Documents

- `docs/governance/ontology/ontology_drift_baseline_2026_05.json`

---

## 15. Future Consideration

```
Future consideration: machine-readable authority registry
```

A machine-readable version of this registry may be created after:

1. Governance review completes
2. Record structure stabilizes
3. Tooling requirements are defined
4. Integration points are identified

No JSON schema, stubs, or executable structure will be created in V1.

---

## Final Rule

```
Documented authority visibility
is not the same as
semantic authority.
```

---

*Authority Boundary Registry V1 — DRAFT FOR GOVERNANCE RECONCILIATION*
