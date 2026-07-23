# BR-001 — Remediation Execution Queue

> The **proposed** ordering (advisory; owner adjudication remains authoritative). Built **exclusively from Tier A items and Tier B items that survived
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
| **Current-red re-verification** | ✅ **RUN 2026-07-20** — full `services/api` pytest vs `d716d16`: **21 failed / 8155 passed / 19 xfailed / 1 xpassed**. See [WAVE_0_VERIFICATION.md](WAVE_0_VERIFICATION.md). **Caveat:** local Py3.14 toolchain, not CI's 3.11 — not directly comparable to the triage's ~12; definitive count needs the CI stack. Surfaced **BR-032** (body-solver cluster, 17), **BR-033** (openapi build), **BR-034** (stale xfail). | done (with toolchain caveat) |
| BR-018 | owner resolves R2000 fork (sanction vs R12-safe) | unblocks all R2000/DXF work |
| BR-014 | owner merge decision on SPINE-002/003/004 | unblocks the adoption cluster |
| BR-019 | owner rules whether a user/auth system is in scope | unblocks (or closes) the auth-stub item |

## Wave 1 — Broken or incomplete production paths (verified defects)

| Rank | Item | Disposition | Bound |
| ---- | ---- | ----------- | ----- |
| 1 | **BR-001 + BR-002 + BR-004** — saw_lab/rmos store-layer kwarg TypeErrors | ~~CONFIRMED_DEFECT~~ **FIXED (BR-002B)** | ✅ **DONE** — `tool_kind`/`batch_label` threaded through the store layer; `matches_index_meta` reads nested `meta.tool_kind` via canonical `tool_kind_matches()` (lenient+synonym); **BR-035 fixed alongside**. 8 formerly-xfail tests pass; +16 regression; 259 saw_lab/runs_v2 tests green. Deeper batch_tree shape defect surfaced as **BR-036** (out of scope). |
| 2 | **BR-032** — body-solver failure cluster (17 Wave-0 reds) | CONFIRMED_DEFECT | large/unbounded — **first confirm on CI stack + check unmerged 015i/015k branches** before authoring a Dev Order |
| 3 | BR-006 — CAM 8J pocketing reconstruction (source `.py` lost) | UNFINISHED_SPRINT_WORK | data-loss urgency; medium |
| 4 | BR-033 — `app.openapi()` build failure / `validate` field shadow | CONFIRMED_DEFECT | small (rename field) — confirm on CI stack |
| 5 | BR-003 — simulation metrics router/schema mismatch (8 xfails) | CONFIRMED_DEFECT | small–medium |
| 6 | BR-013 — wire RMOS workflow `approve` route | UNFINISHED_SPRINT_WORK | small |

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

- **COMPLETE / SUPERSEDED / STALE:** BR-024 (R2000 `ezdxf.new` literal call refactored into
  `dxf_compat` — **superseded into BR-018**, which owns the open R2000 policy question; not "resolved"),
  BR-025 (baseline-40-failures handoff — superseded by ratchet rebaselining), BR-026 (CI-RED-015D
  wire-URL collision — closed 2026-05-30), BR-027 (CAM_7x governance + MRP_5x runtime-spine clusters —
  complete). Each maps 1:1 to its [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md) row.
- **Tier C:** BR-031 salvage/backup branches and other historical/abandoned artifacts — archive.
- **Deferred / non-production:** WF-A01, Investigation 024 — see
  [DEFERRED_AND_NONPRODUCTION_WORK.md](DEFERRED_AND_NONPRODUCTION_WORK.md).

## The next bounded candidate

Wave 1, Rank 1 (ledger items BR-001/BR-002/BR-004) is **DONE** — executed as **BR-002B**, the first
authorized code remediation under this program. The empirical `tool_kind` ground-truth gate ran first
(3 stored states: `saw`, `saw_lab`, missing — `tool_kind` survives only in nested `meta.tool_kind`),
then the additive repair threaded `tool_kind`/`batch_label` through the store layer and routed all
`tool_kind` comparisons (store + `batch_tree`, BR-035) through the canonical lenient/synonym
`tool_kind_matches()` helper. See [BR-002A_PROOF.md](BR-002A_PROOF.md) for the archaeology.

**The next bounded candidate is now BR-036** — the deeper `batch_tree` shape defect surfaced during
BR-002B (`isinstance(a, dict)` guards exclude the `RunArtifact` objects `as_items` actually returns
from the real store → empty trees). It was held out of BR-002B per the owner's scope boundary and
needs its own bounded Dev Order.
