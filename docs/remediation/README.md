# Remediation Program (BR-001)

> The production repository's remediation program: a current, evidence-backed, dependency-aware queue of
> what production work remains valid and in what order. Reconstructed by **BR-001 — Backlog Re-entry**.
> This is a **living** program — the queue burns down as remediation Dev Orders execute and update the
> ledgers.

## Artifacts

| Document | Purpose |
| -------- | ------- |
| [BACKLOG_REENTRY_CHARTER.md](BACKLOG_REENTRY_CHARTER.md) | mission, boundaries, evidence tiers, classifications, living-ledger design |
| [BACKLOG_SOURCE_INVENTORY.md](BACKLOG_SOURCE_INVENTORY.md) | every backlog source examined + review status |
| [BACKLOG_ADJUDICATION_LEDGER.md](BACKLOG_ADJUDICATION_LEDGER.md) | canonical item-level ledger (one disposition each) |
| [UNFINISHED_SPRINT_REGISTER.md](UNFINISHED_SPRINT_REGISTER.md) | authorized-but-incomplete work, kept distinct from debt |
| [REPOSITORY_DEFECT_REGISTER.md](REPOSITORY_DEFECT_REGISTER.md) | only currently-verified, reproducible defects |
| [DEFERRED_AND_NONPRODUCTION_WORK.md](DEFERRED_AND_NONPRODUCTION_WORK.md) | parked Lab / research / external work — excluded from the queue |
| [REMEDIATION_DEPENDENCY_MAP.md](REMEDIATION_DEPENDENCY_MAP.md) | blockers, prerequisites, shared root causes, clusters |
| [REMEDIATION_PRIORITY_MODEL.md](REMEDIATION_PRIORITY_MODEL.md) | how ordering is derived (advisory; owner adjudicates) |
| [REMEDIATION_EXECUTION_QUEUE.md](REMEDIATION_EXECUTION_QUEUE.md) | the approved ordering, in evidence-derived waves |
| [NEXT_REMEDIATION_CANDIDATE.md](NEXT_REMEDIATION_CANDIDATE.md) | the one bounded next remediation target |

## How to use it

1. Read the [charter](BACKLOG_REENTRY_CHARTER.md) for the rules (tiers, dispositions, boundaries).
2. The [execution queue](REMEDIATION_EXECUTION_QUEUE.md) is the live ordering; the
   [next candidate](NEXT_REMEDIATION_CANDIDATE.md) is the evidence packet for the next Dev Order.
3. **Each remediation Dev Order updates** the adjudication ledger, defect register, and execution queue
   on completion, so the queue stays current.

## Boundaries

BR-001 reconstructs and orders; it does not fix. Governance is not expanded. WF-A01 and Investigation
024 stay parked ([DEFERRED_AND_NONPRODUCTION_WORK.md](DEFERRED_AND_NONPRODUCTION_WORK.md)). All artifacts
are additive documentation; no production behavior changes.
