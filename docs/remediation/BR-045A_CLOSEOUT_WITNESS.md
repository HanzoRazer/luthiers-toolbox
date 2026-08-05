# BR-045A — Post-merge closeout witness

**Status:** Evidence for administrative closeout (governance only)  
**Date:** 2026-08-05  
**Does not authorize:** BR-044 · unit-profile consolidation · production changes

---

## Authoritative SHAs

| Role | SHA | Note |
|------|-----|------|
| **Implementation merge** | `f12f88c2` | PR #247 — BR-045 code + tests |
| **Post-merge witness baseline** | `969bdbdc` | Later `main` tip on which merged behavior was re-verified (Docker PR #249). **Not** the BR-045 merge commit. |

> BR-045 was merged by `f12f88c2`; its behavior was subsequently witnessed unchanged on `main` at `969bdbdc`.

---

## Owner ruling (recorded)

- **Date:** 2026-08-04  
- **Published `specific_moe` profile:** `c² / 10⁶`  
- **Equivalent backend form:** `(E_GPa / density_kg_m3) × 10³`

---

## Runtime witness on `969bdbdc`

```text
species                   backend    c^2/1e6   frontend  (E/rho)*1e3
American Basswood         24.2651    24.2651    24.2651      24.2651
Western Red Cedar         21.0270    21.0270    21.0270      21.0270
Bubinga                   20.6854    20.6854    20.6854      20.6854
```

Parity: backend == `c²/10⁶` == frontend arithmetic (within declared 4 dp rounding).

### BR-043 regression check (must remain correct)

| Check | Result on `969bdbdc` |
|-------|----------------------|
| American Basswood `radiation_ratio` | **11.87** |
| `_score_acoustic(soundboard)` | **0.992423** (~0.9924) |

---

## Lifecycle closed

```text
queued pending owner unit ruling
→ owner ruling granted
→ implementation authorized
→ PR #247 merged (f12f88c2)
→ post-merge runtime witness passed (969bdbdc)
→ resolved
```

System-of-record updates: `REPOSITORY_DEFECT_REGISTER.md`, `BACKLOG_ADJUDICATION_LEDGER.md`,
`REMEDIATION_EXECUTION_QUEUE.md`, `REMEDIATION_DEPENDENCY_MAP.md`, CBSP21
`.cbsp21/patches/br-045-closeout.json`.
