# Semantic Freeze Policy

**Status:** DRAFT FOR GOVERNANCE RATIFICATION  
**Authority:** NOT CANONICAL UNTIL RATIFIED — NOT CI BLOCKING POLICY UNTIL WIRED  
**Date:** 2026-05-18  
**Purpose:** Freeze discipline for semantic governance  
**Constitutional Dependency:** REPOSITORY_CONSTITUTION.md §11

---

## 1. Authority Statement

This document defines what freeze means and does not mean.

```
DRAFT FOR GOVERNANCE RATIFICATION
NOT CANONICAL UNTIL RATIFIED
NOT CI BLOCKING POLICY UNTIL WIRED
```

---

## 2. Freeze Principle

```
Freeze prevents unreviewed semantic expansion.
Freeze does not create immutability.
```

### What Freeze Is

Freeze is a governance gate that requires explicit review before semantic expansion.

### What Freeze Is Not

| Not Freeze | Reason |
|------------|--------|
| Immutability | Freeze is temporary and reviewable |
| Prohibition | Freeze requires review, not denial |
| Implementation lock | Implementation may change within frozen semantics |
| Version lock | Version advancement is permitted |

---

## 3. Freeze Types

| Freeze Type | Code | Description |
|-------------|------|-------------|
| Vocabulary Freeze | `VOCAB_FREEZE` | No new vocabulary terms without ratification |
| Authority Freeze | `AUTH_FREEZE` | No authority reassignments without ratification |
| Schema Freeze | `SCHEMA_FREEZE` | No schema changes without migration plan |
| Lifecycle Freeze | `LIFECYCLE_FREEZE` | No lifecycle stage changes without ratification |
| Experimental Freeze | `EXPERIMENTAL_FREEZE` | No experimental promotion without ratification |
| CI Freeze | `CI_FREEZE` | No CI enforcement expansion without ratification |

---

## 4. Freeze Scope

### Freeze Applies To

| Scope | Description |
|-------|-------------|
| New terms | Adding vocabulary terms |
| Term redefinition | Changing vocabulary meaning |
| Authority expansion | Granting new authority |
| Authority transfer | Moving authority between owners |
| Schema addition | Adding schema fields |
| Schema removal | Removing schema fields |
| Lifecycle transition addition | Adding new lifecycle stages |
| Experimental promotion | Moving experimental to canonical |
| CI blocking addition | Adding new CI-blocking checks |

### Freeze Does Not Apply To

| Out of Scope | Reason |
|--------------|--------|
| Implementation details | Freeze governs semantics, not implementation |
| Bug fixes | Correctness within frozen semantics is permitted |
| Documentation clarification | Clarification is not expansion |
| Deprecation marking | Marking deprecated does not add semantics |
| Performance optimization | Optimization within frozen semantics is permitted |

---

## 5. Freeze Entry

### Freeze Declaration

Freeze is declared by:

| Field | Description |
|-------|-------------|
| Freeze Type | One of the 6 freeze types |
| Freeze Scope | What is being frozen |
| Freeze Reason | Why freeze is needed |
| Freeze Start Date | When freeze begins |
| Freeze Duration | How long freeze lasts (may be indefinite) |
| Freeze Authority | Who declared the freeze |

### Freeze Entry Constraints

```
Freeze entry requires governance-layer authority.
Freeze entry must be documented.
Freeze entry must be announced to affected systems.
```

---

## 6. Freeze Exit

### Exit Conditions

Freeze exits through:

| Exit Condition | Description |
|----------------|-------------|
| Duration expiry | Freeze duration elapsed |
| Explicit lift | Governance layer lifts freeze |
| Supersession | New freeze replaces old freeze |
| Ratification completion | Blocked items ratified |

### Exit Process

| Step | Description |
|------|-------------|
| 1 | Verify exit condition met |
| 2 | Document freeze exit reason |
| 3 | Announce freeze exit to affected systems |
| 4 | Update freeze registry |

---

## 7. Freeze During Freeze

### Nesting Rules

```
Freezes may not nest.
A frozen scope may not have sub-freezes.
If broader freeze is declared, narrower freeze is absorbed.
```

### Conflict Resolution

| Conflict | Resolution |
|----------|------------|
| Overlapping scope | Broader freeze governs |
| Contradictory freezes | Later freeze supersedes |
| Unclear scope | Human Arbiter decides |

---

## 8. Freeze Bypass

### Bypass Is Not Permitted

```
Freeze bypass is not permitted.
Operational pressure does not create bypass authority.
Convenience does not create bypass authority.
```

### Exception: Emergency Ratification

Emergency ratification (per `GOVERNANCE_RATIFICATION_MODEL.md` §8) may proceed during freeze, but:
- Emergency ratification does not lift the freeze
- Emergency ratification is recorded with `EMERGENCY_DURING_FREEZE` flag
- Standard ratification must follow within 30 days

---

## 9. Critical Clarification

### Freeze Preparation

```
Freeze preparation does not create immutability.
```

Preparing for a freeze (e.g., documenting current state, auditing vocabulary) is governance hygiene, not semantic expansion. Preparation activities include:

| Activity | Freeze Status |
|----------|---------------|
| Documenting existing vocabulary | Not expansion |
| Auditing existing authority | Not expansion |
| Identifying semantic drift | Not expansion |
| Proposing freeze scope | Not expansion |
| Creating freeze checklist | Not expansion |

### Freeze Enforcement

```
Freeze enforcement is CI-blocking only when wired.
```

Until CI enforcement is wired:
- Freeze is governance policy, not automated gate
- Freeze violations are governance violations, not CI failures
- Human review is the enforcement mechanism

---

## 10. Freeze Registry

### Registry Format

```yaml
freeze_id: FRZ-2026-0001
freeze_type: VOCAB_FREEZE
freeze_scope: CAM Runtime vocabulary
freeze_reason: Stabilization before Sprint 2
freeze_start: 2026-05-18
freeze_duration: 30 days
freeze_authority: Governance layer
freeze_status: ACTIVE
exit_condition: null
exit_date: null
exit_reason: null
```

### Registry Location

Freeze records are stored in `docs/governance/freezes/` directory.

---

## 11. Relationship to Existing Governance

### Vocabulary Freeze and CANONICAL_ONTOLOGY_VOCABULARY.md

When `VOCAB_FREEZE` is active:
- No new terms may be added to vocabulary
- Existing terms may be clarified (not redefined)
- Prohibited reinterpretations remain prohibited

### Authority Freeze and CANONICAL_AUTHORITY_MAP.md

When `AUTH_FREEZE` is active:
- No new authority assignments
- No authority transfers
- Existing authority remains in effect

### Schema Freeze and Runtime Contracts

When `SCHEMA_FREEZE` is active:
- No new schema fields
- No field removals
- No type changes
- Migration plan required for any schema modification

---

## 12. Open Freeze Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should freeze have maximum duration? | Prevents indefinite freeze |
| 2 | Should freeze require periodic renewal? | Ensures freeze is still needed |
| 3 | Should freeze violations block CI automatically? | Enforcement strength |
| 4 | Should freeze scope be granular or domain-level? | Freeze precision |
| 5 | Should experimental systems be auto-frozen? | Containment discipline |

---

## Related Documents

- `REPOSITORY_CONSTITUTION.md` — Constitutional authority
- `GOVERNANCE_RATIFICATION_MODEL.md` — Ratification workflow
- `EXPERIMENTAL_ONTOLOGY_POLICY.md` — Experimental containment
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — Vocabulary registry
- `CANONICAL_AUTHORITY_MAP.md` — Authority assignments

---

*Semantic Freeze Policy — DRAFT FOR GOVERNANCE RATIFICATION*
