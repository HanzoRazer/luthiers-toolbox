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
| [REMEDIATION_EXECUTION_QUEUE.md](REMEDIATION_EXECUTION_QUEUE.md) | the proposed ordering (advisory; owner adjudication authoritative), in evidence-derived waves |
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

## Closeout validation (2026-07-20)

Validated against `origin/main` `d716d16`:

- **Links:** all internal remediation links resolve; the `../../workflow-authority` / governance
  references resolve. (0 broken.)
- **Identifiers:** 36 distinct backlog IDs `BR-001`..`BR-036`, no collisions.
- **Vocabulary:** every disposition used is within the approved 13-value set.
- **Traceability:** every queued item has an adjudication-ledger record; every confirmed defect has a
  current reproduction basis (code-inspection or a committed xfail test). The two Wave-0 items
  **BR-032/BR-033** carry a *directional local-run* basis explicitly pending CI-stack confirmation —
  labeled as such, not as authoritative CI reds.
- **Boundary:** deferred/Lab work (WF-A01, Investigation 024, WF-001) does not appear in the active
  queue; artifacts contain no feature designs, governance expansion, book extraction, harvesting, or
  canonical guitar workflow.
- **Production neutrality:** the BR-001 diff touches **only `docs/` plus the required
  `.cbsp21/patches/` governance manifest** (additive) — no production code, schema, API, route, or
  build change. Existing production tests/build/governance checks are therefore unaffected by
  construction.
- **Wave 0 baseline (done):** full `services/api` pytest vs `d716d16` ran 2026-07-20 — **21 failed /
  8155 passed / 19 xfailed / 1 xpassed** — see [WAVE_0_VERIFICATION.md](WAVE_0_VERIFICATION.md).
  **Toolchain caveat:** local Python 3.14, not CI's 3.11, so the count is directional, not the
  authoritative CI baseline. Surfaced BR-032 (body-solver cluster), BR-033 (openapi build), BR-034
  (stale xfail). The next candidate (saw_lab/rmos kwarg fix) is unaffected — those tests are xfailed,
  not among the 21.

**Integrity utility decision:** no `scripts/remediation/check_backlog_integrity.py` was created this
pass. The ledger is human-readable prose (not a structured data format), so a markdown parser would be
brittle; the invariants were validated inline instead. A machine validator is **deferred** until/unless
the ledger moves to a structured format — recorded here per the Dev Order's "document that no new
utility was required."
