# Ontology Drift Classifications

**Status:** Authoritative  
**Date:** 2026-05-16  
**Purpose:** Normalize semantic conflict detection for pattern recognition

---

## Overview

This document classifies types of ontology drift that can occur in a long-lived repository. Classifications enable early detection and systematic resolution.

**Purpose:** Pattern recognition, not repository archaeology.

---

## Drift Categories

### Vocabulary Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Vocabulary Drift |
| **Description** | The same term acquires different meanings in different parts of the codebase. Semantic divergence without explicit bifurcation. |
| **Symptoms** | Code review confusion about term meaning; documentation contradictions; "what does X mean here?" questions; implicit context-dependence |
| **Risks** | Cross-system integration failures; misunderstood contracts; silent data corruption; maintenance confusion |
| **Typical Cause** | Independent evolution of subsystems; lack of vocabulary registry; copy-paste terminology without semantic review |
| **Recommended Resolution** | Audit all usages; establish canonical definition; reconcile or disambiguate conflicting usages; update vocabulary registry |

**Repository example:** The term "lifecycle" used differently across export governance (artifact states) and runtime systems (process states). Both valid but semantically distinct.

---

### Lifecycle Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Lifecycle Drift |
| **Description** | State machine terminology diverges across subsystems. Different systems use different names for equivalent states or same names for different states. |
| **Symptoms** | State mapping confusion; manual translation between systems; "is READY the same as VALIDATED?" questions |
| **Risks** | Incorrect state transitions; lost state information at boundaries; invalid state assumptions |
| **Typical Cause** | Subsystems developed independently; no shared lifecycle vocabulary; state names chosen for local clarity |
| **Recommended Resolution** | Map all lifecycle vocabularies; identify semantic equivalences; establish canonical state names; create translation layer where needed |

---

### Authority Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Authority Drift |
| **Description** | Multiple systems claim ownership over the same semantic concern. No clear canonical authority. |
| **Symptoms** | Conflicting validation rules; "who owns this?" questions; changes require coordinating multiple systems; defensive coding against inconsistency |
| **Risks** | Inconsistent enforcement; maintenance burden; change paralysis; implicit authority through implementation |
| **Typical Cause** | Authority not explicitly declared; subsystems evolve to fill gaps; no reconciliation process |
| **Recommended Resolution** | Identify all claimants; determine canonical owner; update authority map; migrate non-canonical implementations to consumer role |

**Repository example:** DXF export format authority historically claimed by multiple generators before dxf_compat centralization.

---

### Runtime Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Runtime Drift |
| **Description** | Runtime behavior diverges from declared intent or governance constraints. Implementation drifts from specification. |
| **Symptoms** | "The code does X but the docs say Y"; unexpected behavior in edge cases; integration tests contradict unit tests |
| **Risks** | Silent contract violations; unreliable system behavior; documentation becomes untrustworthy |
| **Typical Cause** | Implementation shortcuts; undocumented bug fixes; specification not updated after changes |
| **Recommended Resolution** | Audit runtime behavior against specification; reconcile discrepancies; update specification or fix implementation; add verification tests |

---

### Provenance Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Provenance Drift |
| **Description** | Origin and lineage tracking becomes inconsistent or incomplete. Provenance chains break or diverge. |
| **Symptoms** | "Where did this data come from?" unanswerable; audit trails incomplete; cannot trace artifact history |
| **Risks** | Compliance failures; debugging difficulty; cannot reproduce results; lost institutional knowledge |
| **Typical Cause** | Provenance not required at system boundaries; transformation steps don't preserve lineage; provenance formats diverge |
| **Recommended Resolution** | Establish provenance requirements; audit existing chains; repair broken lineage; standardize provenance format |

---

### Contract Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Contract Drift |
| **Description** | Interface contracts diverge from implementation or from each other. Type definitions, schemas, and APIs become inconsistent. |
| **Symptoms** | Type errors at boundaries; "optional" fields that are actually required; version skew between components |
| **Risks** | Integration failures; silent data loss; defensive parsing everywhere; contract becomes documentation-only |
| **Typical Cause** | Contracts not enforced at runtime; implementation changes without contract update; no contract versioning |
| **Recommended Resolution** | Audit contracts against implementations; reconcile discrepancies; add runtime validation; version contracts explicitly |

---

### Semantic Alias Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Semantic Alias Drift |
| **Description** | Multiple terms exist for the same concept. Synonyms proliferate without explicit equivalence declaration. |
| **Symptoms** | "Is aperture the same as soundhole?"; search requires multiple terms; documentation uses terms interchangeably |
| **Risks** | Incomplete search results; missed connections; cognitive overhead; inconsistent naming |
| **Typical Cause** | Different teams or eras use different terminology; no canonical term established; natural language variation |
| **Recommended Resolution** | Identify all aliases; establish canonical term; document explicit equivalences; migrate to canonical term where practical |

**Repository example:** "morphology" vs "form" vs "shape" in geometry systems — semantically related but with subtle distinctions requiring explicit vocabulary.

---

### Experimental Leakage

| Field | Value |
|-------|-------|
| **Drift Name** | Experimental Leakage |
| **Description** | Experimental or provisional concepts leak into canonical systems without ratification. Sandbox boundaries become porous. |
| **Symptoms** | Production code depends on experimental APIs; experimental terminology in canonical docs; "temporary" becomes permanent |
| **Risks** | Unstable dependencies; premature standardization; difficult removal; experimental changes break production |
| **Typical Cause** | Convenience coupling; no enforcement of experimental boundaries; rushed promotion; unclear experimental markers |
| **Recommended Resolution** | Audit experimental dependencies; enforce boundary markers; require explicit promotion; remove or ratify leaked concepts |

---

### Governance Bifurcation

| Field | Value |
|-------|-------|
| **Drift Name** | Governance Bifurcation |
| **Description** | Parallel governance structures emerge with different rules, vocabularies, or authority models. The repository develops multiple inconsistent governance systems. |
| **Symptoms** | "Which governance doc applies?"; conflicting rules for similar concerns; governance shopping; process confusion |
| **Risks** | Inconsistent enforcement; authority conflicts; maintenance burden; governance becomes obstacle not enabler |
| **Typical Cause** | Governance created per-subsystem; no cross-cutting governance review; governance docs not maintained; no reconciliation process |
| **Recommended Resolution** | Map all governance documents; identify overlaps and conflicts; establish governance hierarchy; reconcile or explicitly scope conflicting rules |

---

## Drift Detection Patterns

### Documentation Review

- Check for undefined terms
- Check for terms with multiple definitions
- Check for authority claims without governance reference
- Check for lifecycle states not in canonical vocabulary

### Code Review

- Check for semantic constants defined locally
- Check for type definitions duplicating canonical types
- Check for validation logic duplicating governance constraints
- Check for comments explaining term meaning (symptom of unclear vocabulary)

### Integration Review

- Check for translation layers between subsystems
- Check for defensive parsing at boundaries
- Check for "normalize" or "adapt" functions (may indicate drift accommodation)

### Audit Triggers

- New subsystem integration
- Major refactoring
- Governance document update
- Authority conflict report
- "What does X mean?" questions in review

---

## Drift Severity Levels

| Level | Description | Response |
|-------|-------------|----------|
| **Low** | Cosmetic inconsistency; no functional impact | Document in backlog; reconcile opportunistically |
| **Medium** | Semantic confusion; requires context to resolve | Schedule reconciliation; prevent further drift |
| **High** | Authority conflict; integration risk | Prioritize reconciliation; block conflicting changes |
| **Critical** | Active semantic corruption; data integrity risk | Immediate reconciliation; may require rollback |

---

## Constitutional Drift Classes

The following drift classes represent violations of constitutional invariants. These are higher-severity than domain drift because they threaten the governance model itself.

### Constitutional Authority Assumption

| Field | Value |
|-------|-------|
| **Drift Name** | Constitutional Authority Assumption |
| **Description** | A subsystem silently assumes semantic authority without governance grant. Violates Constitutional Invariant 1. |
| **Symptoms** | System documentation claims ownership; system begins rejecting data it considers invalid; system defines new vocabulary without reconciliation |
| **Severity** | Critical |
| **Constitutional Violation** | Invariant 1: No subsystem may silently become ontology authority |
| **Recommended Resolution** | Audit authority claims; revoke unauthorized authority; update authority map; add containment checks |

---

### Runtime Ontology Definition

| Field | Value |
|-------|-------|
| **Drift Name** | Runtime Ontology Definition |
| **Description** | Runtime systems begin defining vocabulary or semantic meaning rather than consuming it. Violates Constitutional Invariant 2. |
| **Symptoms** | Runtime code contains semantic constants not in vocabulary registry; runtime documentation describes "what terms mean"; runtime validation logic encodes semantic rules |
| **Severity** | Critical |
| **Constitutional Violation** | Invariant 2: Runtime consumes ontology; runtime does not define ontology |
| **Recommended Resolution** | Extract semantic definitions to vocabulary; refactor runtime to consume definitions; add governance boundary checks |

---

### Evidence-as-Ontology Confusion

| Field | Value |
|-------|-------|
| **Drift Name** | Evidence-as-Ontology Confusion |
| **Description** | Evidence extraction systems are treated as ontology authorities. Observed data is treated as defined truth. Violates Constitutional Invariant 3. |
| **Symptoms** | Extraction results used without review; "the vectorizer says X" treated as canonical; evidence systems in authority map |
| **Severity** | High |
| **Constitutional Violation** | Invariant 3: Evidence is not ontology |
| **Recommended Resolution** | Label evidence outputs explicitly; add evidence-to-ontology review gate; remove evidence systems from authority map |

---

### Review-as-Ratification Bypass

| Field | Value |
|-------|-------|
| **Drift Name** | Review-as-Ratification Bypass |
| **Description** | Code review or documentation review is treated as ratification. Changes become canonical without explicit governance acceptance. Violates Constitutional Invariant 4. |
| **Symptoms** | "It was in the PR" treated as governance approval; vocabulary terms appear without ratification record; authority assignments happen via merge |
| **Severity** | High |
| **Constitutional Violation** | Invariant 4: Review is not ratification |
| **Recommended Resolution** | Add ratification workflow enforcement; require explicit ratification for vocabulary/authority changes; audit recent changes for missing ratification |

---

### Usage-as-Ratification Drift

| Field | Value |
|-------|-------|
| **Drift Name** | Usage-as-Ratification Drift |
| **Description** | Widespread adoption is treated as canonical status. "Everyone uses it" becomes "it's canonical." Violates Constitutional Invariant 8. |
| **Symptoms** | Unratified terms in production code; "de facto standard" language in documentation; resistance to ratification because "it's already everywhere" |
| **Severity** | High |
| **Constitutional Violation** | Invariant 8: Usage is not ratification |
| **Recommended Resolution** | Audit unratified widespread usage; retroactive ratification or deprecation; add pre-merge vocabulary checks |

---

## Related Documents

- [CANONICAL_ONTOLOGY_VOCABULARY.md](./CANONICAL_ONTOLOGY_VOCABULARY.md) — vocabulary definitions
- [CANONICAL_AUTHORITY_MAP.md](./CANONICAL_AUTHORITY_MAP.md) — ownership declarations
- [ONTOLOGY_RECONCILIATION_WORKFLOW.md](./ONTOLOGY_RECONCILIATION_WORKFLOW.md) — change process
- [GOVERNANCE_AUTHORITY_HIERARCHY.md](./GOVERNANCE_AUTHORITY_HIERARCHY.md) — tier structure
- [REPOSITORY_CONSTITUTION.md](./REPOSITORY_CONSTITUTION.md) — constitutional authority
- [GOVERNANCE_RATIFICATION_MODEL.md](./GOVERNANCE_RATIFICATION_MODEL.md) — ratification workflow
