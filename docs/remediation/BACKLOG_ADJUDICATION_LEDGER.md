# BR-001 — Backlog Adjudication Ledger

> The canonical item-level ledger. **No item may appear in the execution queue without a corresponding
> adjudication record here.** Populated in Commit 3 from the discovery sweep; each record carries its
> evidence tier and current verification state so coverage is never overstated.

## Record schema

Every adjudicated item carries:

```text
Backlog ID                 BR-NNN (stable)
Title
Subsystem
Source reference           (branch / doc path / issue# / file:line)
Original date              (where available)
Evidence tier              A | B | C   (charter §3)
Current evidence           (what was inspected/reproduced now)
Reproduction method        (failing test / command / code-path / contract / runtime obs / absent-impl)
Primary disposition        (one of the 13 — charter §4)
Secondary labels           (subsystem / severity / safety / user-impact / release)
Severity
User impact
Safety or manufacturing impact
Architectural impact
Dependencies               (BR-NNN it needs)
Blocking items             (BR-NNN it blocks)
Estimated size
Readiness                  (ready / blocked / needs-owner-decision)
Recommended action
Owner ruling required      (yes/no + question)
Notes
```

## Disposition vocabulary (exactly one primary per item)

`COMPLETE` · `SUPERSEDED` · `DUPLICATE` · `STALE_OR_NOT_REPRODUCIBLE` · `UNFINISHED_SPRINT_WORK` ·
`CONFIRMED_DEFECT` · `MIGRATION_GAP` · `PERFORMANCE_DEBT` · `MAINTAINABILITY_DEBT` · `ENHANCEMENT` ·
`DEFERRED_RESEARCH` · `EXTERNAL_OR_ENVIRONMENTAL` · `OWNER_DECISION_REQUIRED`

## Ledger

> Populated in Commit 3. Compact rows below; full per-item detail follows the table for any item that
> needs it (reproduction, dependencies). Tier A/B items only are eligible for the queue.

| BR ID | Title | Subsystem | Source ref | Tier | Disposition | Sev | Readiness | Recommended action |
| ----- | ----- | --------- | ---------- | ---- | ----------- | --- | --------- | ------------------ |
| _(populated in Commit 3)_ | | | | | | | | |

## Verification coverage (filled in Commit 3)

- Tier A items verified: _n/n_
- Tier B items validated: _n/n_
- Tier C items inventoried (not revalidated): _n_
- Items requiring owner decision: _n_
