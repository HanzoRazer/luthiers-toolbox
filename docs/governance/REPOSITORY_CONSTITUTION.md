# Repository Constitution

**Status:** DRAFT FOR GOVERNANCE RATIFICATION  
**Authority:** NOT CANONICAL UNTIL RATIFIED — NOT CI BLOCKING POLICY UNTIL WIRED  
**Date:** 2026-05-18  
**Purpose:** Top-level semantic law for the repository

---

## 1. Authority Statement

This document defines constitutional semantic constraints for the repository.

```
DRAFT FOR GOVERNANCE RATIFICATION
NOT CANONICAL UNTIL RATIFIED
NOT CI BLOCKING POLICY UNTIL WIRED
```

Once ratified, this constitution becomes:

```
repository-wide semantic law
```

All governance documents, domain implementations, and runtime systems operate under this constitution.

---

## 2. Constitutional Scope

This constitution governs:

| Scope | Description |
|-------|-------------|
| Semantic authority | Who may define canonical meaning |
| Ratification model | How semantic decisions become accepted |
| Freeze discipline | What freeze means and does not mean |
| Experimental containment | How experimental systems are bounded |
| Runtime boundaries | What runtime may and may not do |
| CI authority | What CI enforcement may and may not decide |

This constitution does NOT govern:

| Out of Scope | Reason |
|--------------|--------|
| Implementation details | Domain autonomy |
| Runtime algorithms | Execution authority separate from semantic authority |
| Feature roadmap | Strategic decisions, not semantic law |
| Code style | Implementation convention, not ontology |

---

## 3. Repository Semantic Invariants

These invariants are constitutional law. All governance and runtime systems must preserve them.

### Invariant 1: No Subsystem May Silently Become Ontology Authority

```
No subsystem may silently become ontology authority.
```

Authority requires explicit governance grant. Usage frequency, implementation convenience, and operational necessity do not create authority.

### Invariant 2: Runtime Consumes Ontology

```
Runtime consumes ontology; runtime does not define ontology.
```

Runtime systems may interpret, cache, and optimize ontology access. Runtime systems may not add, remove, or redefine ontology terms.

### Invariant 3: Evidence Is Not Ontology

```
Evidence is not ontology.
```

Extracted evidence, staging data, and observational records are inputs to semantic decisions. They are not semantic decisions themselves.

### Invariant 4: Review Is Not Ratification

```
Review is not ratification.
```

Reviewing evidence, proposing definitions, and documenting conflicts does not create canonical authority. Ratification requires explicit governance acceptance.

### Invariant 5: Visibility Is Not Authority

```
Visibility is not authority.
```

Observability systems, governance instrumentation, and audit tooling report state. They do not create state or grant authority.

### Invariant 6: Consumption Is Not Ownership

```
Consumption is not ownership.
```

A system may consume data without owning its semantic definition. Consumption establishes usage authority, not semantic authority.

### Invariant 7: Location Is Not Authority

```
Location is not authority.
```

Where data is stored does not determine who owns its meaning. Storage location is infrastructure, not governance.

### Invariant 8: Usage Is Not Ratification

```
Usage is not ratification.
```

Widespread adoption does not establish canonical status. Adoption frequency is not governance approval.

### Invariant 9: CI Failure Is Enforcement Signal

```
CI failure is enforcement signal, not semantic judgment.
```

CI enforces rules defined elsewhere. CI does not define the rules it enforces. CI failure indicates violation, not semantic determination.

### Invariant 10: Discovery Is Not Ratification

```
Discovery of semantic usage does not imply ratification.
```

Observed usage frequency does not imply ownership. Inventory artifacts are evidence for review, not authority. Semantic inventory (C1) documents reality; it does not create or normalize semantic authority.

---

## 4. Authority Root

### Constitutional Authority

This constitution is the authority root for semantic governance.

```
REPOSITORY_CONSTITUTION.md
→ governs all semantic authority decisions
→ governs ratification model
→ governs freeze discipline
→ governs experimental containment
→ governs runtime boundaries
```

### Relationship to Existing Governance

Existing governance documents operate under this constitution:

| Document | Constitutional Relationship |
|----------|----------------------------|
| `CANONICAL_ONTOLOGY_VOCABULARY.md` | Vocabulary registry operating under ratification model |
| `CANONICAL_AUTHORITY_MAP.md` | Authority assignments subject to constitutional invariants |
| `ONTOLOGY_RECONCILIATION_WORKFLOW.md` | Reconciliation workflow implementing ratification model |
| `ONTOLOGY_DRIFT_CLASSIFICATIONS.md` | Drift detection supporting constitutional enforcement |
| `GOVERNANCE_AUTHORITY_HIERARCHY.md` | Governance tiers operating under constitutional constraints |

### Ontology Governance Stack

The ontology governance stack (`docs/governance/ontology/`) is a domain-specific governance implementation operating under this constitutional layer.

```
Constitution (this document)
→ governs governance stack
→ ontology stack is one governed implementation
```

---

## 5. Ratification Model

Semantic decisions become canonical through ratification, not through usage or implementation.

### Ratification Authority

| Decision Type | Ratification Authority |
|---------------|----------------------|
| Vocabulary definition | Domain Owner + Governance Reviewer |
| Authority assignment | Governance layer |
| Lifecycle normalization | Governance layer |
| Freeze decisions | Governance layer |
| Experimental promotion | Domain Owner + Governance layer |
| CI enforcement expansion | Governance layer |

### Ratification Constraints

```
Ratification may not be automated.
Ratification requires explicit human acceptance.
AI assistance is advisory only.
```

See: `GOVERNANCE_RATIFICATION_MODEL.md` for detailed ratification workflow.

---

## 6. Conflict Arbitration

### Arbitration Hierarchy

When semantic conflicts arise:

```
1. Check constitutional invariants
2. Check ratification model
3. Check domain authority map
4. Escalate to Human Arbiter
```

### Arbitration Rules

| Rule | Description |
|------|-------------|
| Constitutional supremacy | Constitutional invariants override domain decisions |
| Ratification requirement | Disputed semantics require ratification, not precedent |
| Domain autonomy | Within constitutional bounds, domains govern themselves |
| Human authority | Unresolved conflicts escalate to human decision |

---

## 7. Domain Autonomy Rules

### Domain Authority

Domains may:

| Permitted | Description |
|-----------|-------------|
| Define domain vocabulary | Within constitutional constraints |
| Assign domain operational owners | Subject to authority map |
| Evolve domain implementations | Within governance boundaries |
| Propose cross-domain vocabulary | Through reconciliation workflow |

### Domain Constraints

Domains may NOT:

| Forbidden | Reason |
|-----------|--------|
| Redefine constitutional invariants | Constitutional supremacy |
| Self-grant cross-domain authority | Authority requires governance grant |
| Bypass ratification | Ratification is mandatory |
| Claim runtime authority over ontology | Invariant 2 |

---

## 8. Runtime Authority Boundary

### Runtime Permitted Actions

| Permitted | Description |
|-----------|-------------|
| Consume ontology | Read and use canonical definitions |
| Cache ontology | Optimize access within correctness bounds |
| Interpret for execution | Apply ontology to operational decisions |
| Report state | Provide observability into runtime behavior |

### Runtime Forbidden Actions

| Forbidden | Reason |
|-----------|--------|
| Define ontology | Invariant 2 |
| Modify vocabulary | Invariant 2 |
| Grant authority | Invariant 1 |
| Bypass governance | Constitutional supremacy |
| Claim semantic authority through implementation | Invariant 8 |

---

## 9. Experimental Authority Boundary

### Experimental Systems May

| Permitted | Description |
|-----------|-------------|
| Pressure-test ontology | Explore semantic alternatives |
| Propose vocabulary | Through reconciliation workflow |
| Operate in sandbox | Within containment boundaries |
| Generate evidence | For governance consideration |

### Experimental Systems May NOT

| Forbidden | Reason |
|-----------|--------|
| Define canonical ontology | Invariant 3 |
| Leak into canonical systems | Experimental containment |
| Self-promote to canonical | Ratification required |
| Bypass review | Invariant 4 |

See: `EXPERIMENTAL_ONTOLOGY_POLICY.md` for containment rules.

---

## 10. CI Authority Boundary

### CI Permitted Actions

| Permitted | Description |
|-----------|-------------|
| Enforce ratified rules | Apply governance constraints |
| Report violations | Signal enforcement failures |
| Block on violations | Prevent non-conforming changes |
| Log enforcement | Preserve audit trail |

### CI Forbidden Actions

| Forbidden | Reason |
|-----------|--------|
| Define semantic rules | Invariant 9 |
| Ratify vocabulary | Ratification requires human authority |
| Modify governance | CI enforces, does not define |
| Override human decisions | Human authority is final |

---

## 11. Freeze Authority Boundary

### Freeze Meaning

```
Freeze prevents unreviewed semantic expansion.
Freeze does not create immutability.
```

### Freeze Authority

| Permitted | Description |
|-----------|-------------|
| Vocabulary freeze | Prevent new unratified terms |
| Authority freeze | Prevent unratified authority changes |
| Schema freeze | Prevent unratified schema changes |

### Freeze Constraints

| Forbidden | Reason |
|-----------|--------|
| Permanent immutability | Freeze is temporary |
| Bypass for convenience | Freeze applies uniformly |
| Automatic freeze | Freeze requires governance decision |

See: `SEMANTIC_FREEZE_POLICY.md` for freeze discipline.

---

## 12. Relationship to Existing Governance Documents

### Existing Documents Under This Constitution

| Document | Status | Constitutional Dependency |
|----------|--------|--------------------------|
| `CANONICAL_ONTOLOGY_VOCABULARY.md` | Authoritative | Vocabulary governed by ratification model |
| `CANONICAL_AUTHORITY_MAP.md` | Authoritative | Authority governed by constitutional invariants |
| `ONTOLOGY_RECONCILIATION_WORKFLOW.md` | Authoritative | Workflow implements ratification model |
| `ONTOLOGY_DRIFT_CLASSIFICATIONS.md` | Authoritative | Classifications support constitutional enforcement |

### Documents Created by This Constitution

| Document | Purpose |
|----------|---------|
| `GOVERNANCE_RATIFICATION_MODEL.md` | Detailed ratification workflow |
| `SEMANTIC_FREEZE_POLICY.md` | Freeze discipline |
| `EXPERIMENTAL_ONTOLOGY_POLICY.md` | Experimental containment |
| `CANONICAL_PROVENANCE_MODEL.md` | Provenance decomposition |
| `GEOMETRY_AUTHORITY_DECOMPOSITION.md` | Geometry authority separation |

---

## 13. Open Constitutional Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should constitutional amendments require supermajority? | Change control |
| 2 | Should constitutional violations block CI automatically? | Enforcement |
| 3 | Should domains have constitutional veto power? | Autonomy vs. unity |
| 4 | Should experimental systems have time-limited containment? | Containment discipline |
| 5 | Should provenance types be constitutionally fixed? | Stability vs. evolution |

---

## Related Documents

- `GOVERNANCE_RATIFICATION_MODEL.md` — Ratification workflow
- `SEMANTIC_FREEZE_POLICY.md` — Freeze discipline
- `EXPERIMENTAL_ONTOLOGY_POLICY.md` — Experimental containment
- `CANONICAL_PROVENANCE_MODEL.md` — Provenance decomposition
- `GEOMETRY_AUTHORITY_DECOMPOSITION.md` — Geometry authority
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — Vocabulary registry
- `CANONICAL_AUTHORITY_MAP.md` — Authority assignments
- `ONTOLOGY_RECONCILIATION_WORKFLOW.md` — Reconciliation process
- `ONTOLOGY_DRIFT_CLASSIFICATIONS.md` — Drift detection

---

## Final Constitutional Rule

```
C0 defines how semantic authority becomes legitimate.
C0 does not itself make disputed semantics legitimate.
```

---

*Repository Constitution — DRAFT FOR GOVERNANCE RATIFICATION*
