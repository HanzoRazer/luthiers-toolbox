# LTB-MVS-EVIDENCE-RESOLVER-003

Checked: 2026-10-23. Base: `origin/main` `a0861507313a34a0db2043639512f4618f0885a9` (merge of PR #454). PR #453 merge `8a2f33cb8f2bd869963ae38c23d08fdd2e950722` is an ancestor. Worktree was clean. Open pull requests: none.

This increment stores LTB evidence and resolves citations for `PhysicalEngineeringProposalV1`. It does not decide whether a measurement is scientifically correct, whether a proposal is safe, or whether manufacturing may proceed.

## Ownership

The stored record is an LTB-local persistence record. It is not adopted from Physical Engineering Mesh, and it is not an adapter to an upstream contract. See `PHASE0_OWNERSHIP.md`.

## What landed

- `services/api/app/physical_engineering/evidence_artifact_v1.py`
- `services/api/app/physical_engineering/evidence_serialization.py`
- `services/api/app/physical_engineering/evidence_repository.py`
- `services/api/app/physical_engineering/stored_evidence_repository.py`
- `services/api/app/physical_engineering/stored_evidence_resolver.py`
- Tests under `services/api/tests/physical_engineering/test_evidence_*.py` and `test_stored_evidence_*.py`

`proposal_v1.py` and `beginner_proposal_harness.py` are unchanged. The new resolver is not exported from `physical_engineering/__init__.py`. There is no HTTP route.

## Verification

From `services/api`, with the repository virtualenv:

```bash
python -m pytest \
  tests/physical_engineering/test_evidence_artifact_v1.py \
  tests/physical_engineering/test_stored_evidence_repository.py \
  tests/physical_engineering/test_stored_evidence_resolver.py \
  tests/physical_engineering/test_evidence_harness_integration.py \
  tests/physical_engineering/test_beginner_proposal_harness.py \
  tests/physical_engineering/test_physical_engineering_proposal_v1.py \
  tests/physical_engineering/test_pep_v1_harden_001.py \
  -q --no-cov
```

Result on this increment: 142 passed. The previous physical-engineering baseline on `a0861507` was 102 passed.

## What remains separate

`LTB-MVS-VALIDATION-POLICY-004` still has to supply one owner-approved `ValidationPolicyV1`. `LTB-MVS-GUIDED-REVIEW-SLICE-002` stays blocked until that policy exists. `MAINT-DEFER-017` and `MAINT-DEFER-018` stay queued.
