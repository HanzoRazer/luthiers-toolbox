# LTB-MVS-VALIDATION-POLICY-004

Checked: 2026-10-23. Base: `origin/main` `02032884c32d871b8a5addc24021763748eae949` (merge of PR #455, 10:55 PM America/Chicago). PR #455 head `20725b0a` is an ancestor. Open pull requests: none.

This increment stores an LTB-local policy record and can construct the existing `ValidationPolicyV1` from exactly one approved `ACTIVE` record. It does not choose physical thresholds. No active production policy is shipped.

## Authority

`ltb_validation_policy` 1.0 is an LTB persistence record. It is not a Physical Engineering Mesh standard. Approval sits outside `ValidationPolicyV1`. A selected policy remains advisory: the validator's `advisory_allowed` means eligible for human review. It does not authorize fabrication or material removal.

## State

```text
DRAFT -- not selectable
ACTIVE -- selectable only when approval cites the payload digest and one match exists
SUPERSEDED -- not selectable
REVOKED -- not selectable
```

Zero active matches raise `VALIDATION_POLICY_NOT_FOUND`. Two active matches raise `VALIDATION_POLICY_AMBIGUOUS`.

## What landed

- `services/api/app/physical_engineering/validation_policy_record_v1.py`
- `services/api/app/physical_engineering/validation_policy_serialization.py`
- `services/api/app/physical_engineering/validation_policy_repository.py`
- `services/api/app/physical_engineering/production_validation_policy.py`
- Package exports for the selector, selection, repository, and error
- Tests under `services/api/tests/physical_engineering/test_validation_policy_*.py` and `test_production_validation_policy.py`

`proposal_v1.py` and `beginner_proposal_harness.py` are unchanged. There is no HTTP route and no policy JSON under the application package.

## Owner gate

`POLICY_FIELD_AUTHORITY.md` lists every `ValidationPolicyV1` field. Neither numeric field has an owner, a source, or an approved value. The stop condition in the order fired: the mechanism and tests are present, and no active production policy was created.

## Downstream

`LTB-MVS-GUIDED-REVIEW-SLICE-002` stays blocked until this policy increment is merged. See `NEXT_ORDER.md`.
