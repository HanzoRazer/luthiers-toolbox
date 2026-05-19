# Governance Stack Index V1

**Status:** GOVERNANCE CONSOLIDATION  
**Date:** 2026-05-17  
**Purpose:** Governance topology consolidation and freeze preparation  
**Authority:** DRAFT — NOT CANONICAL — NOT ENFORCEMENT AUTHORITY — NOT FREEZE AUTHORITY  
**Track:** Instrument Knowledge Reconciliation (Sandbox)

---

## 1. Purpose

This document provides a navigational and semantic index for the ontology governance stack.

This is:

```
governance topology consolidation
```

NOT:

```
another ontology layer
```

This index establishes the stabilization boundary before additional ontology expansion occurs.

---

## 2. Governance Stack Overview

### Stack Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE COORDINATION STACK                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  INSTRUMENT_DATA_STORAGE_AUDIT.md                            │   │
│   │  Layer: Topology Discovery                                   │   │
│   │  Function: Identifies storage fragmentation                  │   │
│   └─────────────────────────┬───────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  INSTRUMENT_DIMENSION_ONTOLOGY_V1.md                         │   │
│   │  Layer: Semantic Discovery                                   │   │
│   │  Function: Documents competing field meanings                │   │
│   └─────────────────────────┬───────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  PROMOTION_REVIEW_MANIFEST_V1.md                             │   │
│   │  Layer: Review Governance                                    │   │
│   │  Function: Governs tier transition review                    │   │
│   └─────────────────────────┬───────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md               │   │
│   │  Layer: Governance Visibility                                │   │
│   │  Function: Makes governance state auditable                  │   │
│   └─────────────────────────┬───────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  AUTHORITY_BOUNDARY_REGISTRY_V1.md                           │   │
│   │  Layer: Ownership Visibility                                 │   │
│   │  Function: Formalizes semantic ownership boundaries          │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Critical Distinction

```
This is a governance coordination stack,
not a runtime stack.
```

These documents coordinate governance decisions. They do not execute at runtime, enforce CI policy, or create canonical ontology.

---

## 3. Authority Classification Table

| Document | Owns | Must Not Own | Status |
|----------|------|--------------|--------|
| Storage Audit | Topology discovery, fragmentation visibility | Canonical authority, migration execution | COMPLETE |
| Dimension Ontology | Semantic discovery, field conflict documentation | Canonical ratification, schema execution | DRAFT |
| Promotion Manifest | Review governance, provenance requirements | Canonical truth creation, automatic promotion | DRAFT |
| Observability Layer | Governance-state visibility, drift tracking | Enforcement authority, semantic ratification | DRAFT |
| Authority Boundary Registry | Ownership boundary visibility, anti-conflation documentation | Ontology authority, runtime implementation | DRAFT |

### Ownership Invariant

```
Each document owns visibility into its domain.
No document owns semantic authority over that domain.
```

---

## 4. Lifecycle Positioning

| Layer | Document | Lifecycle Position | Maturity |
|-------|----------|-------------------|----------|
| 1 | Storage Audit | Discovery | Complete |
| 2 | Dimension Ontology | Semantic drafting | Draft |
| 3 | Promotion Manifest | Review governance definition | Draft |
| 4 | Observability Layer | Governance instrumentation | Draft |
| 5 | Authority Boundary Registry | Ownership documentation | Draft |

### Lifecycle Dependencies

```
Audit → Ontology: Audit identifies what ontology must disambiguate
Ontology → Promotion: Ontology defines fields promotion review maps to
Promotion → Observability: Promotion decisions become observable state
Observability → Authority: Observable conflicts inform authority boundaries
```

### Non-Dependencies

```
No layer ratifies another layer's content.
No layer enforces another layer's definitions.
No layer creates canonical truth for another layer.
```

### Reverse Authority Inheritance Prohibition

```
Later governance layers do not redefine earlier layers.
```

Forbidden:

| Pattern | Reason |
|---------|--------|
| Authority registry redefining ontology semantics | Ownership visibility ≠ semantic authority |
| Observability layer altering promotion governance | Visibility ≠ governance |
| Promotion manifest changing audit findings | Review ≠ discovery |
| Any downstream layer overriding upstream definitions | Breaks stack coherence |

Governance layers inform forward; they do not inherit authority backward.

---

## 5. Terminology Disambiguation

### Critical Collision: "Tier 1/2/3"

The repository uses "Tier 1/2/3" terminology in two unrelated systems:

#### System A: Governance Authority Hierarchy

From `GOVERNANCE_AUTHORITY_HIERARCHY.md`:

| Term | Meaning |
|------|---------|
| Tier 1 | Structural Invariants (repository-wide) |
| Tier 2 | Domain Governance (MRP, CAM, RMOS) |
| Tier 3 | Operational Policies (runtime behavior) |

#### System B: Data Promotion Stages

From ontology governance documents:

| Term | Meaning |
|------|---------|
| Tier 1 | Canonical (governed, ratified data) |
| Tier 2 | Curated (reviewed, pending promotion) |
| Tier 3 | Staging (non-canonical evidence) |

#### Disambiguation Rule

```
"Tier" in governance hierarchy = authority strata
"Tier" in ontology documents = data promotion stages
```

These are separate semantic systems sharing identical terminology.

#### Future Resolution

Data promotion tiers will be renamed to "stages" in a future revision cycle:

| Current | Future |
|---------|--------|
| Tier 1 Canonical | Canonical Stage |
| Tier 2 Curated | Curated Stage |
| Tier 3 Staging | Evidence Stage |

Until then, context determines meaning.

### Other Terminology Notes

| Term | Consistent Meaning Across Stack |
|------|--------------------------------|
| DRAFT | Not ratified, not canonical |
| RATIFIED | Governance-approved (observability state) |
| CANONICAL | Authoritative semantic truth |
| UNRESOLVED | Requires governance decision |
| BASELINED | Accepted legacy state |

---

## 6. Governance Invariants

These invariants are enforced across the entire governance stack:

### Invariant 1: Visibility ≠ Authority

```
Observing governance state does not create governance authority.
```

The observability layer records; it does not decide.

### Invariant 2: Consumption ≠ Ownership

```
Consuming data does not imply owning its semantic definition.
```

Runtime systems may use data without claiming ontology authority.

### Invariant 3: Draft ≠ Canonical

```
Draft documents propose; they do not ratify.
```

Every ontology document explicitly states its draft status.

### Invariant 4: Evidence ≠ Ontology

```
Extracted evidence is not semantic truth.
```

Tier 3 staging holds evidence, not canonical definitions.

### Invariant 5: Review ≠ Ratification

```
Reviewing evidence does not create canonical authority.
```

Tier 2 review documents decisions; it does not create truth.

### Invariant 6: Location ≠ Authority

```
Data location does not imply semantic ownership.
```

Where data is stored is separate from who owns its meaning.

### Invariant 7: Usage ≠ Ratification

```
Frequency of usage does not establish canonical status.
```

Widespread adoption is not governance approval.

### Invariant 8: Reference ≠ Authority Inheritance

```
Referencing a document does not inherit its authority.
```

Back-references establish visibility, not ownership transfer.

---

## 7. Document Summaries

### 7.1 INSTRUMENT_DATA_STORAGE_AUDIT.md

**Path:** `docs/governance/INSTRUMENT_DATA_STORAGE_AUDIT.md`

**Function:** Identifies storage fragmentation across 7+ locations containing overlapping instrument data.

**Key Findings:**
- Stratocaster dimensions: 406mm vs 396mm vs 458.8mm across sources
- Multiple systems claim canonical authority
- Morphology harvest outputs risk accidental canonical treatment

**Owns:** Topology discovery, fragmentation visibility

**Must Not Own:** Canonical designation, migration authority

**Status:** AUDIT COMPLETE

---

### 7.2 INSTRUMENT_DIMENSION_ONTOLOGY_V1.md

**Path:** `docs/governance/ontology/INSTRUMENT_DIMENSION_ONTOLOGY_V1.md`

**Function:** Documents competing meanings for 7 foundational instrument dimension fields.

**Key Findings:**
- Physical measurement ≠ bounding box ≠ template
- All 7 fields remain UNRESOLVED
- Measurement convention conflation is root cause of variance

**Owns:** Semantic discovery, conflict documentation

**Must Not Own:** Canonical ratification, schema implementation

**Status:** DRAFT FOR GOVERNANCE RECONCILIATION

---

### 7.3 PROMOTION_REVIEW_MANIFEST_V1.md

**Path:** `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md`

**Function:** Defines governance contract for Tier 3 → Tier 2 promotion review.

**Core Rule:** "Records review. Does not create truth."

**Key Provisions:**
- Provenance requirements (source, review, mapping)
- Reviewer authority boundaries
- Rejection and deferral pathways

**Owns:** Review governance, provenance requirements

**Must Not Own:** Canonical truth creation, automatic promotion

**Status:** DRAFT FOR GOVERNANCE RECONCILIATION

---

### 7.4 ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md

**Path:** `docs/governance/ontology/ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md`

**Function:** Defines governance-state visibility semantics.

**Key Provisions:**
- 10 drift lifecycle states
- 9 governance signal categories
- Severity interpretation (defers to ontology_ci_policy.json)
- Quarantine philosophy (conceptual, not operational)

**Owns:** Governance-state visibility, drift tracking

**Must Not Own:** Enforcement authority, semantic ratification, CI blocking decisions

**Status:** DRAFT FOR GOVERNANCE RECONCILIATION

---

### 7.5 AUTHORITY_BOUNDARY_REGISTRY_V1.md

**Path:** `docs/governance/ontology/AUTHORITY_BOUNDARY_REGISTRY_V1.md`

**Function:** Formalizes semantic ownership boundaries for ontology-related subsystems.

**Key Provisions:**
- 7 boundary records with explicit must_not_own clauses
- 5 documented authority overlaps
- 8 ownership categories
- 6 forbidden anti-patterns

**Owns:** Ownership boundary visibility, anti-conflation documentation

**Must Not Own:** Ontology authority, runtime implementation, migration execution

**Status:** DRAFT FOR GOVERNANCE RECONCILIATION

---

### 7.6 GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md

**Path:** `docs/governance/ontology/GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md`

**Function:** Verifies internal consistency across the governance stack.

**Key Findings:**
- Tier terminology collision (documented, not resolved)
- Status vocabulary overlap (documented as parallel vocabularies)
- No cross-document narrative inheritance drift detected
- Back-references added to all documents

**Status:** COMPLETE

---

## 8. Supporting Documents

### Policy Documents

| Document | Role |
|----------|------|
| `ontology_ci_policy.json` | CI enforcement policy (severity definitions) |
| `ontology_drift_baseline_2026_05.json` | Accepted legacy drift baseline |
| `GOVERNANCE_AUTHORITY_HIERARCHY.md` | Repository governance tier model |

### Audit Documents

| Document | Role |
|----------|------|
| `GOVERNANCE_TOPOLOGY_MAP.md` | Full governance system inventory |
| `MORPHOLOGY_HARVEST_STORAGE_AUTHORITY.md` | Staging boundary definitions |

---

## 9. Freeze Readiness Assessment

**Critical clarification:**

```
Freeze preparation does not authorize governance immutability.
```

Freeze preparation establishes conditions for controlled governance evolution, not permanent lockdown.

### Stable (Ready for Freeze)

| Component | Rationale |
|-----------|-----------|
| Storage audit findings | Discovery complete, findings documented |
| Tier collision documentation | Collision identified, disambiguation documented |
| Governance invariants | Consistent across all documents |
| Anti-pattern definitions | Complementary and mutually reinforcing |
| Back-references | Complete and bidirectional |
| Authority boundary records | All 7 subsystems documented |

### Intentionally Unresolved

| Component | Rationale |
|-----------|-----------|
| 7 dimension field semantics | Awaiting governance ratification |
| Data promotion tier renaming | Deferred to future revision cycle |
| Reviewer authorization pool | Requires organizational decision |
| Quarantine authority definition | Requires governance committee |
| Machine-readable registries | Deferred until structure stabilizes |

### Not Ready for Freeze

| Component | Blocker |
|-----------|---------|
| CI enforcement integration | Policy exists, tooling not implemented |
| Runtime consumption rules | Requires ratified ontology first |
| Migration execution | Requires freeze + ratification first |

---

## 10. Expansion Constraints

### Before Expanding Ontology, Verify:

1. **Stack coherence** — No new terminology collisions introduced
2. **Authority boundaries** — New domain has clear must_not_own clauses
3. **Lifecycle position** — New document fits stack sequence
4. **Cross-references** — Bidirectional references established
5. **Invariant compliance** — All 8 governance invariants maintained

### Forbidden Expansion Patterns

| Pattern | Reason |
|---------|--------|
| Adding runtime authority to governance docs | Governance observes, runtime executes |
| Adding enforcement to observability | Observability reports, policy enforces |
| Adding canonical status to drafts | Ratification requires governance approval |
| Expanding scope without boundary records | Creates implicit authority |
| Adding cross-domain definitions | Each domain owns its vocabulary |

---

## 11. Governance Drift Risks

The repository has entered a governance maintenance phase. The following drift risks must be monitored:

### Risk Categories

| Risk | Description | Mitigation |
|------|-------------|------------|
| Cross-document inconsistency | Terminology or definitions diverging between documents | Consistency reviews |
| Terminology inheritance drift | Wording from one layer implicitly redefining another | Invariant enforcement |
| Authority inversion | Later layers claiming authority over earlier layers | Reverse inheritance prohibition |
| Implicit semantic expansion | Scope creeping through uncontrolled edits | Explicit must_not_own clauses |
| Premature ratification | Draft documents treated as canonical | Status headers, governance review gates |
| Implementation-driven ontology pressure | Runtime systems exerting semantic pressure on governance | Evidence ≠ ontology boundary |

### Critical Recognition

```
Governance proliferation itself can create drift.
```

The governance stack is now large enough that uncontrolled document additions would themselves become a source of ontology drift. This is why freeze preparation is timely.

---

## 12. Relationship to Active Morphology Work

### Separation Boundary

```
Morphology extraction systems generate evidence.
They do not generate ontology authority.
```

### Current Morphology State

Per `PHASE4_WIRING_REPORT.md`:

- Phase 4 is an incomplete R&D asset, NOT the canonical extraction pipeline
- Canonical pipeline is `blueprint_reader.html` using REST API endpoints
- Data flow: PDF → vectorize → dimensions → morphology harvest → body grid
- Lesson: "Do NOT assume internal Python modules are the authority"

Per `MORPHOLOGY_FAILURE_TAXONOMY.md`:

- 7 critical extraction failures documented
- 3 major failures, 1 minor failure
- Primary failure mode: JSON serialization errors during harvest
- Classification mismatches and low confidence scores demonstrate extraction instability

### Governance Implication

```
Operational morphology growth increases semantic pressure on governance systems.
```

The morphology stack is now operationally interconnected:

- Blueprint vectorization
- Photo extraction
- Calibration metadata
- Body grid classification
- Harvest coordination

This connectivity creates propagation paths for semantic assumptions. The governance stack must remain independent to prevent evidence-layer assumptions from becoming ontology definitions.

### Boundary Preservation

| Morphology System | Produces | Does NOT Produce |
|-------------------|----------|------------------|
| Blueprint vectorizer | Extracted dimensions | Canonical dimension authority |
| Photo extractor | Body outline evidence | Semantic outline definitions |
| Calibration adapter | Calibration metadata | Canonical calibration semantics |
| Body grid | Morphology classifications | Ontology field definitions |
| Harvest coordinator | Evidence records | Canonical instrument truth |

### Why This Matters Now

The failure taxonomy demonstrates ongoing extraction instability:

- JSON serialization failures
- Classification mismatches
- Low confidence scores

Unstable evidence systems cannot be ontology authorities. The governance separation protects the ontology stack from being destabilized by operational morphology evolution.

---

## 13. Relationship to Constitutional Layer (C0)

### Constitutional Authority

This governance stack now operates under a constitutional layer defined in:

```
docs/governance/REPOSITORY_CONSTITUTION.md
```

The constitution is the authority root. This ontology stack is one governed implementation operating under constitutional constraints.

### Constitutional Hierarchy

```
REPOSITORY_CONSTITUTION.md (C0)
    │
    ├── GOVERNANCE_RATIFICATION_MODEL.md
    ├── SEMANTIC_FREEZE_POLICY.md
    ├── EXPERIMENTAL_ONTOLOGY_POLICY.md
    ├── CANONICAL_PROVENANCE_MODEL.md
    └── GEOMETRY_AUTHORITY_DECOMPOSITION.md
         │
         ▼
    Ontology Governance Stack (this index)
         │
         ├── INSTRUMENT_DATA_STORAGE_AUDIT.md
         ├── INSTRUMENT_DIMENSION_ONTOLOGY_V1.md
         ├── PROMOTION_REVIEW_MANIFEST_V1.md
         ├── ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md
         └── AUTHORITY_BOUNDARY_REGISTRY_V1.md
```

### Constitutional Invariants Applicable to This Stack

| Invariant | Application to Ontology Stack |
|-----------|------------------------------|
| Invariant 1: No subsystem may silently become ontology authority | This stack documents ontology state; it does not create ontology authority |
| Invariant 3: Evidence is not ontology | Morphology evidence documented here is input to governance, not governance itself |
| Invariant 4: Review is not ratification | Stack review does not ratify stack contents |
| Invariant 5: Visibility is not authority | This index provides visibility; visibility does not grant authority |

### Stack Status Under C0

```
This stack: GOVERNED DOMAIN IMPLEMENTATION
Constitutional status: SUBJECT TO C0 INVARIANTS
Ratification status: DRAFTS AWAIT RATIFICATION
Authority claim: NONE — visibility layer only
```

### C0 Document References

| Document | Purpose |
|----------|---------|
| `REPOSITORY_CONSTITUTION.md` | Authority root, 9 invariants |
| `GOVERNANCE_RATIFICATION_MODEL.md` | How drafts become canonical |
| `SEMANTIC_FREEZE_POLICY.md` | What freeze means for this stack |
| `EXPERIMENTAL_ONTOLOGY_POLICY.md` | Containment for morphology sandbox |
| `CANONICAL_PROVENANCE_MODEL.md` | Provenance type definitions |
| `GEOMETRY_AUTHORITY_DECOMPOSITION.md` | Geometry layer ownership |

---

## 14. Open Governance Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | When should governance drafts become executable contracts? | Implementation timing |
| 2 | Should freeze states become machine-readable? | Tooling integration |
| 3 | What governance artifacts require formal ratification? | Governance workflow |
| 4 | How should future ontology domains enter the stack? | Expansion protocol |
| 5 | When should terminology migration occur? | Tier/stage renaming |
| 6 | What governance layers may eventually become enforceable? | CI integration |
| 7 | Who authorizes governance freeze decisions? | Organizational authority |
| 8 | How should cross-domain governance conflicts be arbitrated? | Conflict resolution |
| 9 | Should governance documents have expiration or review dates? | Lifecycle management |
| 10 | How should morphology operational state influence governance timing? | Coordination |

---

## 15. Governance Stack State Summary

### Current State

```
governance coordination stack: COHERENT
terminology disambiguation: DOCUMENTED
authority boundaries: EXPLICIT
cross-references: COMPLETE
invariants: ENFORCED
```

### Recommended Next Actions

| Priority | Action | Rationale |
|----------|--------|-----------|
| 1 | Freeze governance stack expansion | Consolidation complete |
| 2 | Await governance review cycle | Drafts need organizational validation |
| 3 | Evaluate executable contract candidates | Identify what can become schema |
| 4 | Monitor morphology operational pressure | Extraction systems growing rapidly |

### Not Recommended

| Action | Reason |
|--------|--------|
| Additional ontology documents | Stack needs stabilization, not expansion |
| CI enforcement changes | Policy exists, enforcement premature |
| Migration execution | Requires ratification first |
| Schema generation | Requires ratification first |

---

## 16. Document Lifecycle

| Phase | Status | Date |
|-------|--------|------|
| Index creation | COMPLETE | 2026-05-17 |
| Governance review | PENDING | — |
| Stack freeze | PENDING | — |

---

## 17. Related Documents

### Governance Stack (This Index)

- `docs/governance/INSTRUMENT_DATA_STORAGE_AUDIT.md`
- `docs/governance/ontology/INSTRUMENT_DIMENSION_ONTOLOGY_V1.md`
- `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md`
- `docs/governance/ontology/ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md`
- `docs/governance/ontology/AUTHORITY_BOUNDARY_REGISTRY_V1.md`
- `docs/governance/ontology/GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md`

### Constitutional Layer (C0)

- `docs/governance/REPOSITORY_CONSTITUTION.md`
- `docs/governance/GOVERNANCE_RATIFICATION_MODEL.md`
- `docs/governance/SEMANTIC_FREEZE_POLICY.md`
- `docs/governance/EXPERIMENTAL_ONTOLOGY_POLICY.md`
- `docs/governance/CANONICAL_PROVENANCE_MODEL.md`
- `docs/governance/GEOMETRY_AUTHORITY_DECOMPOSITION.md`

### Supporting Documents

- `docs/governance/ontology/ontology_ci_policy.json`
- `docs/governance/ontology/ontology_drift_baseline_2026_05.json`
- `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md`
- `docs/governance/GOVERNANCE_TOPOLOGY_MAP.md`

### Morphology Reference Documents

- `docs/governance/PHASE4_WIRING_REPORT.md` — Extraction pipeline wiring
- `docs/governance/MORPHOLOGY_FAILURE_TAXONOMY.md` — Extraction failure modes

---

## Final Statement

```
This governance stack is a coordination architecture.
It provides visibility, not authority.
It documents boundaries, not implementations.
It enables stabilization, not expansion.
```

The stack is now coherent enough that uncontrolled edits would become a governance risk.

**Recommendation:** Freeze ontology expansion. Await governance review cycle.

---

*Governance Stack Index V1 — 2026-05-17*
