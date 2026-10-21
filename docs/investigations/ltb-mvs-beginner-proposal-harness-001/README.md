# LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001

Bounded beginner-workflow adapter around the existing physical-engineering proposal contract.

## Provenance

This harness is new construction. It was prompted by the MVS roadmap after reconnaissance stopped `LTB-G1-002`. It is not recovered historical code. Git history has no `grounding_workflow` and no `workflow_harness` to restore.

The stopped reconnaissance is preserved in [RECOVERY_STOP.md](RECOVERY_STOP.md). That stop prevented a namespace and responsibility collision with the live Grounding Agent.

## What this increment does

`services/api/app/physical_engineering/beginner_proposal_harness.py` collects one beginner request, builds one `PhysicalEngineeringProposalV1`, calls `validate_proposal()` once, and copies the verdict.

The guided status is the gate's result name, unchanged:

- `advisory_allowed`
- `evidence_required`
- `rejected`

There is no second outcome vocabulary. `advisory_allowed` remains human-review eligibility. It does not authorize manufacture, material removal, or measurement execution.

## What this increment does not do

- It does not import, rename, or modify `tools/grounding_agent`.
- It does not create a second Grounding Agent.
- It does not duplicate `PhysicalEngineeringProposalV1`, `ValidationPolicyV1`, or their dispositions.
- It does not add numeric engineering rules, geometry inference, friendly measurement defaults, CAM, export, or manufacturing authority.
- It does not add a UI or an API route.
- It does not repair `MAINT-DEFER-017` or `MAINT-DEFER-018`.
- It does not extend the headstock outline preview.

The package export in `app/physical_engineering/__init__.py` is unchanged. Callers import the harness module directly so the gate's public surface does not grow a second authority.

## Authority

The validator owns the result. The harness copies `result`, `reason_codes`, `required_evidence`, and `advisory_review_allowed`. Policy numbers and evidence bytes are supplied by the caller. `schema_id` `physical_engineering_proposal` and `schema_version` `1.0` are the existing contract's identity.

## How to test

From `services/api`, with that tree's virtualenv:

```bash
python -m pytest tests/physical_engineering/test_beginner_proposal_harness.py -q --no-cov
python -m pytest tests/physical_engineering/test_physical_engineering_proposal_v1.py tests/physical_engineering/test_pep_v1_harden_001.py -q --no-cov
```

## Documents

- [RECOVERY_STOP.md](RECOVERY_STOP.md) — why `LTB-G1-002` was not implemented
- [WORKFLOW_CONTRACT.md](WORKFLOW_CONTRACT.md) — request, proposal mapping, copied result
- [FIXTURE.md](FIXTURE.md) — the deterministic beginner request
- [TEST_MATRIX.md](TEST_MATRIX.md) — expected gate results
- [DEFERRED.md](DEFERRED.md) — work this increment leaves in place
