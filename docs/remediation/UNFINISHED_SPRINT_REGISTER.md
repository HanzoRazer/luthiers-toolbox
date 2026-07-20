# BR-001 — Unfinished Sprint Register

> Work previously authorized by a valid Dev Order / sprint but only **partially implemented**. Kept
> distinct from generic technical debt (charter §4). Each entry links to its
> [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md) record. Populated in Commit 3.

## Record schema

```text
Originating program            (Dev Order / sprint id)
Original objective
Authoritative handoff          (doc path)
Relevant commits or PRs
Implemented scope
Missing scope
Current architectural validity (still valid / partially / invalid)
Tests currently present
Completion recommendation      (complete / narrow-and-complete)
Supersession recommendation    (supersede / retire — with reason)
Blocking decisions             (owner rulings needed)
Adjudication ledger ID         BR-NNN
```

## Register

Each item was authorized by a Dev Order / handoff that self-declares incomplete work. Links to the
[adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md).

| Ledger ID | Originating program | Authoritative handoff | Implemented scope | Missing scope | Arch valid? | Completion vs supersession | Blocking decision |
| --------- | ------------------- | --------------------- | ----------------- | ------------- | ----------- | -------------------------- | ----------------- |
| BR-005 | CAM 7D/7E/7F translation artifact | `CAM_7{D,E,F}_*_HANDOFF.md` | implementation done | tests + commit | valid | **complete** | none |
| BR-006 | CAM 8J pocketing intent | `DEV_ORDER_2026-06-08_CAM_8J_POCKETING_INTENT.md` + `RECOVERY_8J_*` | spec + orphaned `.pyc` | reconstruct `.py` lane (source lost) | valid | **complete** (data-loss risk) | none (READY/UNBLOCKED) |
| BR-007 | CI-RED-020B nightly witness | `CI_RED_020B_dev_order.md` + addendum | dev-ready handoff | execution | valid | **complete** | verify 020B merge-instability resolved (PR #177) |
| BR-008 | CI-RED-016B consumer map | `CI_RED_016B_ENDPOINT_CONSUMER_MAP_HANDOFF.md` | map drafted | consolidation prerequisite | valid | **complete** | prerequisite for BR-028 (016 sprawl) |
| BR-009 | CI-RED-019-003 ledger reconciliation | `CI_RED_019_003_LEDGER_RECONCILIATION_HANDOFF.md` | handoff | reconcile ledger vs SPRINTS | valid | **complete** | none |
| BR-010 | NECK-A frontend migration | `NECK_A_MIGRATION_COMPLETION_PLAN.md` | backend migrated | frontend migration | valid | **complete** | none (ready) |
| BR-011 | Three-loop conflation removal | `DEV_HANDOFF_2026-05-30_THREE_LOOP_*` | doc analysis | remove unsourced mandate (not started) | valid | **complete** | none |
| BR-012 | Aperture workspace refactor | `APERTURE_WORKSPACE_REFACTOR_HANDOFF_2026-05-06.md` | spiral math done | Track A architecture (mid-flight) | partial | **complete or bound** | scope confirmation |
| BR-013 | RMOS workflow approve route | `tests/test_rmos_workflow_e2e.py:63` (skip) | `state_machine.approve()` exists | no API route | valid | **complete** | none |
| BR-014 | SPINE-002/003/004 adoption | audits `SPINE_00{2,3,4}_*` + unmerged branches | held-draft PRs (impl done) | owner merge + post-merge verify | valid | **complete** | **owner merge decision** (as SPINE-005) |

> **Distinction held:** these are authorized-but-incomplete. Never-approved capabilities (art-studio
> backends BR-023, model coverage BR-030) are `ENHANCEMENT`, not listed here. Wrong behavior of shipped
> code (BR-001..004) is `CONFIRMED_DEFECT`, in the [defect register](REPOSITORY_DEFECT_REGISTER.md).
