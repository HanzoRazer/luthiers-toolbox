# BR-001 — Remediation Execution Queue

> The approved ordering. Built **exclusively from Tier A items and Tier B items that survived
> validation** (charter §3). Waves are derived from the [dependency map](REMEDIATION_DEPENDENCY_MAP.md)
> and [priority model](REMEDIATION_PRIORITY_MODEL.md) — not copied from a template. Ranking is advisory;
> owner adjudication is authoritative. Each item links to its
> [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md) record.

> **Living queue:** each remediation Dev Order updates this file, the adjudication ledger, and the
> defect register on completion, so the queue burns down.

## Wave 0 — Baseline & unblock (verification + owner forks)

Not code fixes — the gates that must clear before/around execution.

| Item | Action | Why Wave 0 |
| ---- | ------ | ---------- |
| **Current-red re-verification** | run full `services/api` pytest against `d716d16`; reconcile vs the 2026-06-29 triage (~12 reds on older `0daeab14`) | ranking of test-state items (BR-003, BR-013, BR-020) is not fully trustworthy until the live red count on current `main` is known; **not done this pass** |
| BR-018 | owner resolves R2000 fork (sanction vs R12-safe) | unblocks all R2000/DXF work |
| BR-014 | owner merge decision on SPINE-002/003/004 | unblocks the adoption cluster |
| BR-019 | owner rules whether a user/auth system is in scope | unblocks (or closes) the auth-stub item |

## Wave 1 — Broken or incomplete production paths (verified defects)

| Rank | Item | Disposition | Bound |
| ---- | ---- | ----------- | ----- |
| 1 | **BR-001 + BR-002 + BR-004** — saw_lab/rmos store-layer kwarg TypeErrors | CONFIRMED_DEFECT | small (2–3 functions + callers; 3 xfail tests as acceptance) → **the next candidate** |
| 2 | BR-006 — CAM 8J pocketing reconstruction (source `.py` lost) | UNFINISHED_SPRINT_WORK | data-loss urgency; medium |
| 3 | BR-003 — simulation metrics router/schema mismatch (8 xfails) | CONFIRMED_DEFECT | small–medium |
| 4 | BR-013 — wire RMOS workflow `approve` route | UNFINISHED_SPRINT_WORK | small |

## Wave 2 — Contract & topology / migration

| Rank | Item | Disposition | Note |
| ---- | ---- | ----------- | ---- |
| 1 | BR-017 — re-land IBG PR #224 content to `main` | MIGRATION_GAP | stranded by squash-order race |
| 2 | BR-015 — enable rmos runs_v2 `strict=True` post-migration | MIGRATION_GAP | small |
| 3 | BR-008 — CI-RED-016B consumer map (prerequisite) | UNFINISHED_SPRINT_WORK | gates BR-028 |
| 4 | BR-016 — migrate instrument_geometry off deprecated monolith | MIGRATION_GAP | serialize vs BR-028/BR-013 (route surface) |
| 5 | BR-028 — endpoint-sprawl consolidation | MAINTAINABILITY_DEBT | **after** BR-008 |

## Wave 3 — Performance & maintainability

| Rank | Item | Disposition |
| ---- | ---- | ----------- |
| 1 | BR-021 — burn down 400+ TS errors, then re-block `client_lint_build` + `vue_decomposition` gates | MAINTAINABILITY_DEBT |
| 2 | BR-022 — complete SG_SPEC_TOKEN env-guard rollout | MAINTAINABILITY_DEBT |
| 3 | BR-005 — finish CAM 7D/7E/7F (tests + commit) | UNFINISHED_SPRINT_WORK |
| 4 | BR-010 — NECK-A frontend migration completion | UNFINISHED_SPRINT_WORK |
| 5 | BR-009 — CI-RED-019-003 ledger reconciliation | UNFINISHED_SPRINT_WORK |
| 6 | BR-011 — remove unsourced three-loop mandate | UNFINISHED_SPRINT_WORK |
| 7 | BR-012 — bound/finish aperture Track A | UNFINISHED_SPRINT_WORK |

## Wave 4 — Deferred enhancements & owner-gated

| Item | Disposition | Note |
| ---- | ----------- | ---- |
| BR-023 | ENHANCEMENT | art-studio backends (never approved) |
| BR-030 | ENHANCEMENT | instrument model coverage expansion |
| BR-029 | OWNER_DECISION_REQUIRED | 52-formula verification plan |
| BR-020 | OWNER_DECISION_REQUIRED | residual reds #7/#12 — product decisions |

## Excluded from the queue

- **COMPLETE / SUPERSEDED / STALE:** BR-024 (R2000 regression — resolved), BR-025 (superseded), BR-026,
  BR-027 (CAM_7x / MRP_5x complete).
- **Tier C:** BR-031 salvage/backup branches and other historical/abandoned artifacts — archive.
- **Deferred / non-production:** WF-A01, Investigation 024 — see
  [DEFERRED_AND_NONPRODUCTION_WORK.md](DEFERRED_AND_NONPRODUCTION_WORK.md).

## The next bounded candidate

**Wave 1, Rank 1 → [NEXT_REMEDIATION_CANDIDATE.md](NEXT_REMEDIATION_CANDIDATE.md).**
