# BR-001 — Deferred and Non-Production Work

> Items deliberately **excluded** from the production remediation queue. Recording them here prevents
> parked, research, or external work from repeatedly re-entering production planning. Nothing in this
> register is a production remediation item; none may appear in
> [REMEDIATION_EXECUTION_QUEUE.md](REMEDIATION_EXECUTION_QUEUE.md).

## Consolidation Lab programs (valid but non-blocking)

These live in the separate **Consolidation Lab** repository, not in production. They are governed by
the Lab's promotion gate; nothing promotes into `luthiers-toolbox` without a separate, owner-adjudicated
act. BR-001 does not continue, expand, or block on them.

| Program | State | Production disposition |
| ------- | ----- | ---------------------- |
| **WF-A01 — Workflow Authority Foundation** | Drafted in Lab (ontology / doctrine / architecture / promotion criteria), reviewed and reframed as design constraints; not promoted | `DEFERRED_RESEARCH` — parked; outside production remediation |
| **Investigation 024 — Craft Evidence Framework** | Framework scaffolded in Lab; corpus owner-nominated | `DEFERRED_RESEARCH` — parked; see corpus note below |

### Investigation 024 corpus — admission and extraction blocked

The guitar-building corpus is **owner-nominated** (the owner owns the physical books), but there are
currently **no reviewable source artifacts available to the framework** — nothing it can presently
inspect. Therefore the Lab framework state is:

- owner nomination: **complete**;
- admission review: **blocked** (no reviewable artifacts available);
- extraction: **blocked**.

This is a *source-availability* block, not an ownership question. It is recorded in full only in the Lab
documentation (Investigation 024's source register); production references it merely as deferred
research. **No corpus, extraction, or admission work is part of BR-001.**

## Research, strategy, and speculative work (excluded)

| Item | Why excluded |
| ---- | ------------ |
| Market / positioning strategy (e.g. Blue Ocean framing) | not craft or production engineering; never a production remediation item |
| Guitar-building **workflow definition** (`WF-001`) | downstream, owner-adjudicated; blocked on Lab evidence; not started; not production remediation |
| Speculative features / new product capabilities | enhancements, not defects; excluded from the defect queue (charter §4) |
| Social-media / community harvesting | explicitly out of scope; no agent authorized anywhere |

## External / environmental

| Item | Disposition |
| ---- | ----------- |
| Third-party / platform / toolchain issues not owned by this repo | `EXTERNAL_OR_ENVIRONMENTAL` — tracked, not remediated as production defects |

## Boundary note — IBG-224

The stranded merge of PR #224 (IBG readiness report content not present on `main`) is a **real backlog
item** and is adjudicated in the [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md) like any other.
It is **not** pre-excluded here. BR-001 does not resolve it unless adjudication selects it as the next
remediation candidate.

## SPINE-005 verification worktree

Already removed (no documented remaining need), satisfying the BR-001 §13 non-goal about retaining it.
No action required.
