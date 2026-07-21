# BR-001 — Backlog Re-entry Charter

> Restores the production repository's active engineering mission by reconstructing a trustworthy,
> prioritized remediation queue from the existing backlog, unfinished sprint artifacts, repository
> defects, and deferred work. **This program determines what production work remains valid and in what
> order — it does not remediate defects.**

Baseline: `origin/main` (BR-001 treats `origin/main` as the production baseline; local `main` is not
reconciled first). All BR-001 artifacts are additive documentation under `docs/remediation/`, plus the
one required CBSP21 governance manifest at `.cbsp21/patches/br-001-backlog-reentry.json`. No production
code, interface, schema, or behavior changes.

---

## 1. Objective

Convert the accumulated backlog into an **evidence-backed execution program** that can support
subsequent bounded remediation Dev Orders — ending with exactly one bounded next remediation candidate
ready to become its own implementation Dev Order.

## 2. Authority and boundaries

Authorized: inventory backlog inputs; verify items against the current repository; classify; record
dependencies; prioritize; define remediation waves; select the first bounded candidate; produce the
handoff input for the next Dev Order.

**Not authorized** (this program): fixing any defect; implementing the selected candidate; new features;
expanding governance; reopening the governance sprint; continuing WF-A01 or Investigation 024; defining
a guitar workflow; extracting/scanning books; harvesting; deleting historical documents; closing issues
without verification; converting enhancements into defect work; resolving IBG-224 *unless* adjudication
selects it as the next candidate. Governance is completed infrastructure and is used only as an existing
validation constraint — never expanded.

Corrections to the inventory/validation tooling itself are the only implementation permitted.

## 3. Evidence tiers

Not every historical artifact is revalidated. The constitutional requirement is that **items entering
the active remediation queue have current evidence** — not that every document be re-proven.

| Tier | Applies to | Evidence required |
| ---- | ---------- | ----------------- |
| **A — Mandatory current verification** | open CI failures; failing/skipped tests; unfinished sprint work; production defects; migration gaps; broken user-facing functionality; performance issues currently affecting production | reproduction or current inspection **before** entering the queue |
| **B — Current repository validation** | historical Dev Orders; audit findings; completed-PR follow-ups; architectural observations; maintainability findings | inspection against the current repository (not necessarily runtime reproduction) → `COMPLETE` / `SUPERSEDED` / `DUPLICATE` / retain-for-remediation |
| **C — Historical reference** | old discussion notes; abandoned ideas; obsolete branches; superseded planning docs | inventoried only; not revalidated unless promoted into A or B |

> **The execution queue is built exclusively from Tier A items and Tier B items that survive
> validation.** Tier C items never enter the queue without promotion.

## 4. Required classifications

Every reviewed item receives exactly **one** primary disposition:

`COMPLETE` · `SUPERSEDED` · `DUPLICATE` · `STALE_OR_NOT_REPRODUCIBLE` · `UNFINISHED_SPRINT_WORK` ·
`CONFIRMED_DEFECT` · `MIGRATION_GAP` · `PERFORMANCE_DEBT` · `MAINTAINABILITY_DEBT` · `ENHANCEMENT` ·
`DEFERRED_RESEARCH` · `EXTERNAL_OR_ENVIRONMENTAL` · `OWNER_DECISION_REQUIRED`

Secondary labels may add subsystem, severity, safety impact, user impact, or release relevance.

### Disposition discipline (settled)

- **Current repository state is authoritative.** A report timestamp, issue status, or old failed CI run
  is insufficient by itself; every retained item is checked against the current branch/tests.
- **Adjudication precedes prioritization:** Discover → Verify → Classify → Relate → Prioritize → Schedule.
- **Unfinished sprint work stays distinguishable** — `UNFINISHED_SPRINT_WORK`, never hidden in generic
  debt. Its record names the originating Dev Order, authorized objective, implemented vs missing scope,
  whether the original architecture remains valid, and completion-vs-supersession recommendation.
- **Defects ≠ enhancements ≠ unfinished work.** `CONFIRMED_DEFECT` = implemented/promised behavior is
  wrong/broken/unsafe/contract-inconsistent; `ENHANCEMENT` = never part of approved capability;
  `UNFINISHED_SPRINT_WORK` = authorized but not completed.
- **No issue-count prioritization.** Priority is consequence + dependency (user severity, manufacturing/
  safety, data/evidence-integrity risk, architectural blockage, regression potential, subsystem
  centrality, reproducibility, readiness, size) — never report count or age alone.
- **Production truth must be reproducible.** A retained defect carries a current reproduction basis
  (failing test / deterministic command / traceable code-path inspection / contract mismatch /
  documented runtime observation / explicit evidence that implementation is absent). Otherwise it may
  remain only `STALE_OR_NOT_REPRODUCIBLE` or `OWNER_DECISION_REQUIRED`.
- **Lab programs stay parked.** WF-A01 and Investigation 024 are valid but non-blocking and are recorded
  in [DEFERRED_AND_NONPRODUCTION_WORK.md](DEFERRED_AND_NONPRODUCTION_WORK.md), never in the production queue.

## 5. The output is a living queue, not a new roadmap

BR-001 does not invent broad programs to absorb unrelated issues. Each remediation wave is a set of
related items with a defensible dependency or subsystem relationship.

**BR-001 is a living remediation ledger, not a one-time inventory.** Each subsequent remediation Dev
Order concludes by updating [BACKLOG_ADJUDICATION_LEDGER.md](BACKLOG_ADJUDICATION_LEDGER.md),
[REPOSITORY_DEFECT_REGISTER.md](REPOSITORY_DEFECT_REGISTER.md), and
[REMEDIATION_EXECUTION_QUEUE.md](REMEDIATION_EXECUTION_QUEUE.md) — so the queue burns down over time
instead of requiring another full archaeological pass later.

```text
Repository Archaeology
        ↓
Verified Remediation Queue        (BR-001 delivers this)
        ↓
Execute Remediation Wave          (a later bounded Dev Order)
        ↓
Update Queue                      (that Dev Order updates the ledgers)
        ↓
Execute Next Wave  →  …  →  Remediation Complete  →  Feature-Only Roadmap
```

## 6. First implementation candidate

BR-001 ends by naming one recommended next remediation Dev Order
([NEXT_REMEDIATION_CANDIDATE.md](NEXT_REMEDIATION_CANDIDATE.md)). That candidate must have: a verified
defect or completion gap; clear ownership; bounded file impact; known acceptance criteria; no unresolved
constitutional question; no dependency on unavailable research material.

## 7. Completion conditions

BR-001 is complete when: all known backlog sources are inventoried; every candidate item is checked
against the current repository per its tier; every item has exactly one primary disposition; completed/
duplicate/stale/superseded items are excluded from the active queue without deleting history; unfinished
sprint work is independently registered; confirmed defects carry reproducible current evidence;
enhancements/research are excluded from the defect queue; dependencies and blockers are documented; a
prioritized queue exists with an owner-reviewable priority model; WF-A01 and Investigation 024 remain
parked (Inv-024 corpus recorded as blocking admission/extraction); exactly one bounded next candidate is
named; documentation validation passes; existing production tests, build, and governance checks remain
green; and no production behavior, interface, or constitutional boundary changed.

> Reviewer's question: **Does the repository now have a current, evidence-backed, dependency-aware
> remediation queue — and one clearly bounded engineering change ready to execute next?**
