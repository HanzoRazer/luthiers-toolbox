# Ontology Reconciliation Workflow

**Status:** Authoritative  
**Date:** 2026-05-16  
**Purpose:** Formalize semantic ratification flow for canonical ontology changes

---

## Overview

This workflow governs how ontology changes are proposed, reviewed, and ratified. The reconciliation process ensures semantic stability under long-term evolution.

**Core constraint:** AI assistance is advisory only. Human authority ratifies canonical ontology.

---

## Governance Roles

| Role | Responsibility | Authority |
|------|---------------|-----------|
| **Domain Owner** | Owns semantic authority for a specific domain | May propose vocabulary changes within domain; ratifies domain-specific semantics |
| **Governance Reviewer** | Evaluates cross-domain consistency | May block changes that create authority conflicts; ensures vocabulary coherence |
| **Implementer** | Applies reconciled changes to code and documentation | No semantic authority; executes ratified decisions |
| **Human Arbiter** | Resolves unresolved conflicts | Final decision authority for disputed reconciliation |

**Role constraints:**
- Roles are architectural, not bureaucratic
- One person may hold multiple roles
- AI systems may not hold any role
- Roles do not create approval committees or process mazes

---

## Reconciliation Triggers

Valid triggers for reconciliation:

| Trigger | Example |
|---------|---------|
| New lifecycle states | Adding "governed-experimental" classification |
| New runtime classifications | Introducing execution tier distinctions |
| New topology concepts | Defining new layer boundaries |
| New acoustic semantics | Adding measurement source types |
| New provenance semantics | Extending lineage tracking vocabulary |
| New CAM execution terminology | Defining intent classification terms |
| Authority conflict detection | Two systems claiming same semantic ownership |
| Vocabulary drift discovery | Same term used with different meanings |
| Cross-domain semantic collision | Subsystems defining overlapping vocabulary |

---

## Reconciliation Workflow

```
┌─────────────────┐
│  Suspect Drift  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Audit Terminology│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Classify Authority│
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│Identify Ownership   │
│    Conflict         │
└────────┬────────────┘
         │
         ▼
┌─────────────────┐
│Reconcile Vocabulary│
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│Ratify Canonical     │
│    Meaning          │
└────────┬────────────┘
         │
         ▼
┌─────────────────┐
│ Update Contracts │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│Update Governance    │
│    Docs             │
└─────────────────────┘
```

---

## Workflow Stages

### Stage 1: Suspect Drift

**Trigger:** Observation of potential semantic inconsistency

**Actions:**
1. Document the suspected drift
2. Identify affected systems or documents
3. Note the source of suspicion (code review, documentation audit, runtime behavior)

**Output:** Drift suspicion record

**Role:** Any contributor may initiate

---

### Stage 2: Audit Terminology

**Trigger:** Drift suspicion record

**Actions:**
1. Collect all usages of the suspected term(s)
2. Document each usage context and apparent meaning
3. Identify semantic variations across contexts
4. Flag terms not in canonical vocabulary

**Output:** Terminology audit report

**Role:** Domain Owner or Governance Reviewer

**AI assistance:** AI may assist in collecting usages and identifying variations. AI findings require human verification.

---

### Stage 3: Classify Authority

**Trigger:** Terminology audit report

**Actions:**
1. For each term, identify current authority claims
2. Compare against Canonical Authority Map
3. Flag unmapped authority claims
4. Flag authority conflicts

**Output:** Authority classification report

**Role:** Governance Reviewer

---

### Stage 4: Identify Ownership Conflict

**Trigger:** Authority classification report

**Actions:**
1. Enumerate all authority conflicts
2. For each conflict, identify claimants
3. Assess whether conflict is:
   - Vocabulary drift (same term, different meanings)
   - Authority drift (multiple systems claiming same ownership)
   - Boundary ambiguity (unclear domain separation)

**Output:** Conflict identification report

**Role:** Governance Reviewer

---

### Stage 5: Reconcile Vocabulary

**Trigger:** Conflict identification report

**Actions:**
1. Propose canonical definition for each conflicted term
2. Propose authority assignment for each conflict
3. Draft vocabulary registry updates
4. Draft authority map updates
5. Review for cross-domain consistency

**Output:** Reconciliation proposal

**Role:** Domain Owner (for domain-specific terms), Governance Reviewer (for cross-domain terms)

**AI assistance:** AI may draft proposals. Human review required before ratification.

---

### Stage 6: Ratify Canonical Meaning

**Trigger:** Reconciliation proposal

**Actions:**
1. Review proposal for semantic correctness
2. Review proposal for authority consistency
3. Review proposal for implementation feasibility
4. Accept, reject, or request modifications

**Output:** Ratification decision

**Role:** Domain Owner ratifies domain terms; Governance Reviewer ratifies cross-domain terms; Human Arbiter resolves disputes

**Constraint:** Ratification requires explicit human approval. Ratification may not be automated.

---

### Stage 7: Update Contracts

**Trigger:** Ratification decision (accepted)

**Actions:**
1. Update affected type definitions
2. Update affected schema documents
3. Update affected API contracts
4. Verify contract consistency

**Output:** Updated contracts

**Role:** Implementer

---

### Stage 8: Update Governance Docs

**Trigger:** Updated contracts

**Actions:**
1. Update Canonical Ontology Vocabulary
2. Update Canonical Authority Map
3. Update related governance documents
4. Record reconciliation in audit trail

**Output:** Updated governance documentation

**Role:** Implementer (execution), Governance Reviewer (verification)

---

## AI Assistance Constraints

### Permitted AI Actions

- Collecting terminology usages across codebase
- Identifying potential semantic variations
- Drafting reconciliation proposals
- Suggesting authority classifications
- Detecting potential drift patterns
- Generating documentation drafts

### Prohibited AI Actions

- Ratifying canonical definitions
- Assigning authority ownership
- Resolving authority conflicts
- Approving vocabulary changes
- Freezing ontology independently
- Overriding human decisions

### AI Advisory Protocol

1. AI findings are labeled as advisory
2. AI proposals require human review
3. AI may not auto-commit governance changes
4. Human override is always available
5. AI assistance history is logged for audit

---

## Reconciliation Rules

### Rule 1: No Sandbox May Independently Freeze Ontology

Experimental systems, sandboxed implementations, and isolated subsystems may not establish canonical vocabulary without governance ratification.

### Rule 2: AI Assistance Is Advisory Only

AI systems may inform, suggest, and draft. AI systems may not decide, ratify, or establish.

### Rule 3: Conflicts Escalate, Not Deadlock

Unresolved conflicts escalate to Human Arbiter. No conflict may block reconciliation indefinitely.

### Rule 4: Reconciliation Creates Audit Trail

All ratification decisions are recorded with rationale, participants, and timestamp.

### Rule 5: Vocabulary Coherence Over Speed

Reconciliation prioritizes semantic coherence over rapid change. Partial or rushed reconciliation creates future drift.

---

## Reconciliation Anti-Patterns

### Implicit Ratification

**Pattern:** Changes merged without explicit vocabulary review  
**Risk:** Semantic drift accumulates silently  
**Prevention:** Vocabulary-affecting changes flagged in review

### Authority Assumption

**Pattern:** System begins using authoritative language without reconciliation  
**Risk:** Parallel ontology develops  
**Prevention:** Documentation review for authority claims

### AI Authority Leakage

**Pattern:** AI suggestions treated as ratified without human review  
**Risk:** Automated semantic mutation  
**Prevention:** AI output clearly labeled; ratification requires human action

### Reconciliation Avoidance

**Pattern:** Known conflicts deferred indefinitely  
**Risk:** Conflicts compound; reconciliation becomes harder  
**Prevention:** Time-boxed conflict resolution; escalation to Arbiter

---

## Relationship to Ratification

This reconciliation workflow is the implementation path for ratification decisions defined in `GOVERNANCE_RATIFICATION_MODEL.md`.

### Workflow-to-Ratification Mapping

| Workflow Stage | Ratification Stage |
|----------------|-------------------|
| Stage 1-4 (Audit through Conflict) | Pre-proposal discovery |
| Stage 5 (Reconcile Vocabulary) | Proposal drafting |
| Stage 6 (Ratify Canonical Meaning) | Ratification decision |
| Stage 7-8 (Update Contracts/Docs) | Post-ratification implementation |

### Constitutional Grounding

This workflow implements Constitutional Invariant 4: "Review is not ratification."

```
Stages 1-5 = Review (discovery, analysis, proposal)
Stage 6 = Ratification (explicit human acceptance)
Stages 7-8 = Implementation (post-ratification)
```

### Ratification Decision Types Supported

| Decision Type | Workflow Path |
|---------------|---------------|
| `VOCABULARY_RATIFICATION` | Full workflow for new/modified terms |
| `AUTHORITY_ASSIGNMENT` | Stages 3-8 for authority changes |
| `LIFECYCLE_NORMALIZATION` | Full workflow for lifecycle state changes |
| `EXPERIMENTAL_PROMOTION` | Stage 6 with `EXPERIMENTAL_ONTOLOGY_POLICY.md` checks |

### AI Constraint Reinforcement

The AI constraints in this workflow (§AI Assistance Constraints) implement the constitutional rule:

```
Ratification may not be automated.
Ratification requires explicit human acceptance.
AI assistance is advisory only.
```

---

## Related Documents

- [CANONICAL_ONTOLOGY_VOCABULARY.md](./CANONICAL_ONTOLOGY_VOCABULARY.md) — vocabulary definitions
- [CANONICAL_AUTHORITY_MAP.md](./CANONICAL_AUTHORITY_MAP.md) — ownership declarations
- [ONTOLOGY_DRIFT_CLASSIFICATIONS.md](./ONTOLOGY_DRIFT_CLASSIFICATIONS.md) — drift detection
- [GOVERNANCE_AUTHORITY_HIERARCHY.md](./GOVERNANCE_AUTHORITY_HIERARCHY.md) — tier structure
- [REPOSITORY_CONSTITUTION.md](./REPOSITORY_CONSTITUTION.md) — constitutional authority
- [GOVERNANCE_RATIFICATION_MODEL.md](./GOVERNANCE_RATIFICATION_MODEL.md) — ratification workflow
- [EXPERIMENTAL_ONTOLOGY_POLICY.md](./EXPERIMENTAL_ONTOLOGY_POLICY.md) — experimental containment
