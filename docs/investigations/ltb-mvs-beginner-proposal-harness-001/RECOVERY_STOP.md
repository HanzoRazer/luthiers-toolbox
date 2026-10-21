# Recovery stop — LTB-G1-002 was not implemented

Date checked: 2026-10-21. Base: `origin/main` `7cf90f98` (merge of PR #452).

The order named `LTB-G1-002` asked for recovery of a Grounding Agent and a workflow harness, then a beginner `remove_material` path. Reconnaissance showed that premise is wrong. Implementing it as written would have collided with a live tool that has a different job, and it would have invented a harness that was never in this repository.

This record is part of `LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001` because that stop is why the increment is new construction around `validate_proposal()`, not a recovery.

## What was searched

- Live package `tools/grounding_agent/` and `docs/governance/agents/GROUNDING_AGENT_v0.1.md`.
- `services/api/app/physical_engineering/` (`proposal_v1.py`, `screening.py`, `policy.py`, `evidence.py`).
- `git log --all -- tools/grounding_agent`.
- `git log --all --grep=grounding_workflow` and `git log --all --grep=workflow_harness` (no commits).
- `git grep` for `grounding_workflow` and `workflow_harness` at `7cf90f98` (no matches).

## Recovery table

| Surface | Finding | Disposition |
| --- | --- | --- |
| Grounding Agent, `tools/grounding_agent/` | Live. Read-only handoff conformance. Mission in v0.1: "Does this handoff describe the repository as it actually exists right now?" It never repairs a mismatch and never suggests remediation. History on this package includes `9487af49`, `bd8a94eb`, `d48862f6`, and `fae22ab4`. | Retain. Do not import, rename, modify, or repurpose. Do not create a second Grounding Agent. |
| Workflow harness | Absent from the tree and from git history. No `grounding_workflow` module and no `workflow_harness` module. | There is no interrupted harness to recover. `LTB-G1-002` stops here. |
| `PhysicalEngineeringProposalV1` and `validate_proposal()` | Live in `services/api/app/physical_engineering/proposal_v1.py`. Result names are `advisory_allowed`, `evidence_required`, and `rejected`. Policy numbers are test thresholds with no production engineering authority. Geometry on a proposal is an untrusted claim. | Reuse this seam. Do not duplicate the contract, the policy type, or the dispositions. |
| Beginner UI or API route | Not present for this workflow. | Out of this increment. Internal Python service and deterministic tests only. |

## Why the original file plan was not followed

The `LTB-G1-002` plan would have added a grounding workflow, new contracts, a UI, and a status map onto names such as `PROPOSAL_READY`. That map would have been a second authority vocabulary beside the proposal gate. The live Grounding Agent cannot be the implementation of that plan: repository-to-handoff conformance is a different responsibility from physical-engineering screening.

## What replaced it

`LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001` builds one adapter. It forms a `PhysicalEngineeringProposalV1`, calls `validate_proposal()` once, and returns the gate's result name. The headstock outline increment stays `NOT_IN_MVS_CRITICAL_PATH`. `MAINT-DEFER-017` and `MAINT-DEFER-018` stay queued and were not edited by this change except that the sprint registry gains a separate section for this harness.

## Checked commands

```bash
git log --all --oneline -- tools/grounding_agent
git log --all --oneline --grep=grounding_workflow
git log --all --oneline --grep=workflow_harness
```

The first command lists the live Grounding Agent history. The other two returned no commits.
