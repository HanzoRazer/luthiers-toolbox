# Governance Ratification Model

**Status:** DRAFT FOR GOVERNANCE RATIFICATION  
**Authority:** NOT CANONICAL UNTIL RATIFIED — NOT CI BLOCKING POLICY UNTIL WIRED  
**Date:** 2026-05-18  
**Purpose:** Detailed ratification workflow for semantic decisions  
**Constitutional Dependency:** REPOSITORY_CONSTITUTION.md §5

---

## 1. Authority Statement

This document defines how semantic decisions become canonical.

```
DRAFT FOR GOVERNANCE RATIFICATION
NOT CANONICAL UNTIL RATIFIED
NOT CI BLOCKING POLICY UNTIL WIRED
```

Ratification creates canonical status. Nothing else creates canonical status.

---

## 2. Ratification Principle

```
Semantic decisions become canonical through ratification,
not through usage, implementation, or operational necessity.
```

### What Ratification Is

Ratification is explicit human acceptance of a semantic decision.

### What Ratification Is Not

| Not Ratification | Reason |
|------------------|--------|
| Widespread adoption | Usage is not ratification (Constitutional Invariant 8) |
| Code review approval | Review is not ratification (Constitutional Invariant 4) |
| CI passing | CI failure is enforcement signal, not semantic judgment (Constitutional Invariant 9) |
| Documentation existence | Visibility is not authority (Constitutional Invariant 5) |
| Implementation completion | Runtime consumes ontology; runtime does not define ontology (Constitutional Invariant 2) |

---

## 3. Decision Types Requiring Ratification

| Decision Type | Code | Description |
|---------------|------|-------------|
| Vocabulary Ratification | `VOCABULARY_RATIFICATION` | Adding, modifying, or deprecating canonical vocabulary terms |
| Authority Assignment | `AUTHORITY_ASSIGNMENT` | Assigning or modifying semantic ownership |
| Lifecycle Normalization | `LIFECYCLE_NORMALIZATION` | Changing lifecycle stage definitions or transitions |
| Provenance Decomposition | `PROVENANCE_DECOMPOSITION` | Adding or modifying provenance type definitions |
| Geometry Authority Decision | `GEOMETRY_AUTHORITY_DECISION` | Resolving geometry layer ownership |
| Experimental Promotion | `EXPERIMENTAL_PROMOTION` | Promoting experimental systems to canonical status |
| CI Enforcement Escalation | `CI_ENFORCEMENT_ESCALATION` | Expanding CI-blocking governance checks |

---

## 4. Ratification Roles

| Role | Responsibility | Authority |
|------|----------------|-----------|
| Domain Owner | Proposes semantic decisions within domain | May propose, may not self-ratify |
| Governance Reviewer | Reviews semantic decisions for constitutional compliance | May approve, may not propose |
| Human Arbiter | Resolves conflicts between domains or reviewers | Final authority on disputed decisions |
| AI Assistant | Drafts proposals, identifies conflicts, documents decisions | Advisory only — may not ratify |

### AI Constraint (Stated Explicitly)

```
AI assistance is advisory only.
AI may draft proposals.
AI may identify conflicts.
AI may document decisions.
AI may NOT ratify.
AI may NOT approve.
AI may NOT create canonical authority.
```

This constraint applies regardless of AI capability, operational convenience, or time pressure.

---

## 5. Ratification Workflow

### Stage 1: Proposal

| Field | Description |
|-------|-------------|
| Decision Type | One of the 7 decision types |
| Proposed By | Domain Owner or delegated proposer |
| Proposal Text | What is being proposed |
| Justification | Why this decision is needed |
| Constitutional Compliance | Which invariants apply |
| Affected Systems | What will change if ratified |

### Stage 2: Conflict Check

| Check | Description |
|-------|-------------|
| Vocabulary collision | Does this term conflict with existing vocabulary? |
| Authority overlap | Does this assignment conflict with existing authority? |
| Constitutional violation | Does this proposal violate any invariant? |
| Domain boundary crossing | Does this affect other domains? |

If conflicts found → Reconciliation (Stage 3)
If no conflicts → Review (Stage 4)

### Stage 3: Reconciliation

Follow `ONTOLOGY_RECONCILIATION_WORKFLOW.md` for conflict resolution.

Reconciliation outputs:
- Revised proposal (conflict resolved)
- Escalation request (conflict unresolved)
- Proposal withdrawal (proposer withdraws)

### Stage 4: Governance Review

Governance Reviewer evaluates:

| Criterion | Question |
|-----------|----------|
| Constitutional compliance | Does this comply with all invariants? |
| Authority legitimacy | Is the proposer authorized to propose this? |
| Scope appropriateness | Is this the right level of decision? |
| Documentation completeness | Is the proposal adequately documented? |

### Stage 5: Human Acceptance

```
Ratification requires explicit human acceptance.
Automated approval is not ratification.
Silence is not acceptance.
```

Acceptance is recorded as:

| Field | Value |
|-------|-------|
| Decision ID | Unique identifier |
| Accepted By | Human name |
| Acceptance Date | ISO 8601 timestamp |
| Acceptance Method | How acceptance was recorded |

### Stage 6: Recording

Ratified decisions are recorded in:
- `CANONICAL_ONTOLOGY_VOCABULARY.md` for vocabulary decisions
- `CANONICAL_AUTHORITY_MAP.md` for authority decisions
- Relevant domain governance documents for domain-specific decisions

### Stage 7: Announcement

Ratified decisions must be announced to affected systems.

Announcement does NOT create ratification. Announcement follows ratification.

---

## 6. Ratification Authority Matrix

| Decision Type | Proposer | Reviewer | Ratifier |
|---------------|----------|----------|----------|
| `VOCABULARY_RATIFICATION` | Domain Owner | Governance Reviewer | Domain Owner + Governance Reviewer |
| `AUTHORITY_ASSIGNMENT` | Governance layer | Governance Reviewer | Governance layer |
| `LIFECYCLE_NORMALIZATION` | Governance layer | Governance Reviewer | Governance layer |
| `PROVENANCE_DECOMPOSITION` | Governance layer | Governance Reviewer | Governance layer |
| `GEOMETRY_AUTHORITY_DECISION` | Domain Owner | Governance Reviewer | Domain Owner + Governance Reviewer |
| `EXPERIMENTAL_PROMOTION` | Domain Owner | Governance Reviewer | Domain Owner + Governance layer |
| `CI_ENFORCEMENT_ESCALATION` | Governance layer | Governance Reviewer | Governance layer |

---

## 7. Ratification Constraints

### Time Constraints

```
Ratification has no automatic timeout.
Unratified proposals remain unratified indefinitely.
Operational pressure does not create ratification.
```

### Scope Constraints

```
Ratification scope is exactly as stated.
Ratification of term X does not ratify term Y.
Ratification of vocabulary does not ratify implementation.
```

### Retroactive Constraints

```
Ratification is not retroactive.
Prior usage does not become canonical through later ratification.
Ratification applies from ratification date forward.
```

---

## 8. Emergency Ratification

### When Emergency Ratification Applies

Emergency ratification applies ONLY when:
- Production system is blocked
- Constitutional invariant is threatened
- No standard ratification path is available within blocking timeframe

### Emergency Ratification Process

| Step | Description |
|------|-------------|
| 1 | Document the emergency condition |
| 2 | Propose minimal decision to unblock |
| 3 | Human Arbiter accepts emergency decision |
| 4 | Emergency decision recorded with `EMERGENCY` flag |
| 5 | Standard ratification follows within 30 days |

### Emergency Ratification Constraints

```
Emergency ratification does not bypass constitutional invariants.
Emergency ratification requires Human Arbiter.
Emergency ratification must be followed by standard ratification.
```

---

## 9. Ratification Revocation

Ratified decisions may be revoked through:

| Revocation Type | Process |
|-----------------|---------|
| Supersession | New ratified decision explicitly supersedes old |
| Deprecation | Ratified decision marked deprecated with sunset date |
| Constitutional violation | Decision found to violate invariants |
| Human Arbiter override | Human Arbiter explicitly revokes |

Revocation is itself a ratifiable decision.

---

## 10. Ratification Records

### Record Format

```yaml
decision_id: RAT-2026-0001
decision_type: VOCABULARY_RATIFICATION
proposed_by: Domain Owner
proposed_date: 2026-05-18
proposal_text: Add term "observational_only" to canonical vocabulary
ratified_by: Domain Owner + Governance Reviewer
ratification_date: 2026-05-18
ratification_method: Explicit acceptance in governance review
constitutional_compliance:
  - Invariant 2: Runtime consumes ontology ✓
  - Invariant 3: Evidence is not ontology ✓
affected_systems:
  - CAM Runtime Dispatcher
  - Runtime Result Contracts
status: RATIFIED
```

### Record Storage

Ratification records are stored in `docs/governance/ratification/` directory.

---

## 11. Open Ratification Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should ratification require multiple human reviewers? | Reduces single-point-of-failure |
| 2 | Should ratification have quorum requirements? | Prevents low-attendance decisions |
| 3 | Should emergency ratification have stricter time limits? | Prevents emergency becoming normal |
| 4 | Should AI be permitted to propose but not ratify? | Already stated, needs confirmation |
| 5 | Should ratification records be machine-readable? | Enables automated compliance checking |

---

## Related Documents

- `REPOSITORY_CONSTITUTION.md` — Constitutional authority
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — Vocabulary registry
- `CANONICAL_AUTHORITY_MAP.md` — Authority assignments
- `ONTOLOGY_RECONCILIATION_WORKFLOW.md` — Conflict resolution
- `SEMANTIC_FREEZE_POLICY.md` — Freeze discipline

---

*Governance Ratification Model — DRAFT FOR GOVERNANCE RATIFICATION*
