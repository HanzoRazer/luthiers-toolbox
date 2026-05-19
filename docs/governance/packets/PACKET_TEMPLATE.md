# C2-{ID} — {Title}

**Status:** DRAFT | REVIEW | APPROVED | RATIFIED  
**Owner:** Terminal {X}  
**Date:** {YYYY-MM-DD}  
**Depends On:** {C2-X, C2-Y, or "None"}

---

## 1. Boundary Dispute

{Describe the semantic boundary that is unclear or contested. What systems claim overlapping authority? What terms have collided? What governance gap exists?}

---

## 2. C1 Evidence

{Reference specific C1 inventory findings that document this dispute.}

| Source | Finding |
|--------|---------|
| {Collision ID} | {Summary} |
| {Inventory section} | {Summary} |

---

## 3. Proposed Decomposition

{How should the namespace, authority, or lifecycle be partitioned?}

| Component | Owner | Scope | Notes |
|-----------|-------|-------|-------|
| {Term/Layer} | {System} | {What it covers} | {Constraints} |

---

## 4. Affected Systems

{List systems that produce or consume these semantics.}

| System | Role | Impact |
|--------|------|--------|
| {Name} | Producer / Consumer | {What changes} |

---

## 5. Migration Path

{How can existing code adopt this boundary without breaking?}

### 5.1 Documentation-Only Changes

{Changes that add comments, docstrings, or governance markers without changing behavior.}

### 5.2 Interface Changes (C3)

{Changes that would modify interfaces or contracts. NOT in C2 scope but documented for C3.}

### 5.3 Breaking Changes (C3+)

{Changes that would require coordinated migration. NOT in C2 scope.}

---

## 6. Non-Migration Alternative

{What happens if the boundary is documented but code is not changed?}

| Scenario | Consequence | Acceptable? |
|----------|-------------|-------------|
| {Description} | {What happens} | Yes / No / Conditional |

---

## 7. Terminal Review

| Terminal | Scope | Status |
|----------|-------|--------|
| Terminal 1 | Framework compliance | ☐ Pending |
| Terminal 2 | Runtime compatibility | ☐ Pending |
| Terminal 3 | Geometry/Morphology | ☐ Pending |
| Terminal 4 | Provenance preservation | ☐ Pending |
| Terminal 5 | Export boundary | ☐ Pending |

---

## 8. Ratification Status

- [ ] All required terminals approved
- [ ] Human review scheduled
- [ ] Human review complete
- [ ] **RATIFIED**

---

## 9. Related Documents

- {Link to C1 inventory}
- {Link to existing governance doc}
- {Link to dependent packet}

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| {Date} | Initial draft | {Author} |
