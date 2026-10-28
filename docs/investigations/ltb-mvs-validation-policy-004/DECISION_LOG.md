# Decision log

## Preconditions

PR #455 is merged. Merge commit `02032884c32d871b8a5addc24021763748eae949` (2026-10-23, 10:55 PM America/Chicago). Head `20725b0a` is contained in that merge. The merge contains `FileEvidenceRepository`, `StoredEvidenceResolver`, portable lowercase evidence ids, the canonical digest `ffc902e41c61b1c1eb89897d570a02249c913909dc4e9fc65c8e7ff9d1beeca8`, concurrent identical and conflicting publish tests, and the durability boundary in `docs/investigations/ltb-mvs-evidence-resolver-003/STORAGE_DECISION.md`.

`proposal_v1.py` and `beginner_proposal_harness.py` have no diff against `8a2f33cb`. No open pull request owns the policy surface.

## Owner-adjudication gate

**Stopped.** `POLICY_FIELD_AUTHORITY.md` has no approver and no source for either numeric field. This increment does not create an active production policy and does not add a policy JSON file to the application tree.

Fixture records in tests use obvious stand-in values (`1.25` mm and `2` mm, approver `test-fixture-owner`). One integration fixture repeats the existing test helper's `0.6` and `2.5` so the harness result can be compared with `_policy()`. Those numbers stay in the test module. Production modules do not contain them.

## Rulings that are mechanism, not physics

- Schema id `ltb_validation_policy`, version `1.0`. LTB-local. Not a Mesh contract.
- Digest reuses `evidence_serialization.payload_digest`: sorted-key compact JSON, SHA-256, UTF-8. The hashed payload excludes `approval` and `payload_digest`.
- Draft canonical digest for the documented test fixture is `d5ece888ec5757285891c17c05ca96069b86e9f4531c270afcc351c00fed08a7`.
- Value units must be `mm` because `ValidationPolicyV1` and `screening.py` already compare those fields with millimeter quantities. A different unit is refused. No conversion is applied.
- `policy_revision` is copied into the existing `policy_version` field. The validator dataclass was not changed.
- The policy directory is caller-supplied and exclusive, matching the evidence store. Publish is temp file, `fsync`, and `os.link`.
- Same bytes for one id and revision are idempotent. Different bytes raise `VALIDATION_POLICY_CONFLICT`.
- Corrupt JSON and a foreign JSON file raise `VALIDATION_POLICY_MALFORMED`.
- Those two codes are in addition to the order's list because the evidence store already distinguishes conflict and corruption, and the listed codes do not name them.

## What this patch does not decide

The physical values, the approver, the approval date, and the first production applicability. `MAINT-DEFER-017` and `MAINT-DEFER-018` stay queued.
