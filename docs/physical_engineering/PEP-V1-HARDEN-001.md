# PEP-V1-HARDEN-001

Fail-closed advisory screening for an AI-generated physical-engineering proposal.
The gate lives in `services/api/app/physical_engineering/`. It is not mounted on
a route. It does not authorize manufacture, material removal, or brace work.

## Untrusted side

`PhysicalEngineeringProposalV1` is an agent claim. `EvidenceRef` carries
`ref_id` and `expected_kind` only. It has no measured value, unit, uncertainty,
source run, or resolves flag. `GeometryRegion` is also an untrusted claim.
This increment does not check it against an independent geometry record.
That seam is `PEP-MESH-SEAM-003`.

## Trusted side

Only the validator-owned resolver may say what a citation means.
`InMemoryEvidenceResolver` is a test fixture. It recomputes SHA-256 over the
stored bytes and raises `EvidenceNotFound` or `EvidenceDigestMismatch` from
`EvidenceResolutionError`. A matching digest proves those bytes were not
altered. It does not prove the measurement is true, calibrated, or the right
specimen.

`ValidationPolicyV1` is mandatory. Its numeric fields are Phase I test
thresholds. They are not validated production engineering limits and they
carry no manufacturing authority. The module has no removal-cap constant.

## What a verdict means

`advisory_review_allowed` means the proposal may proceed to human review.
It does not mean the physical action is authorized. `MODIFY_BRACE` is
`REJECTED` / `ACTION_NOT_YET_GOVERNED`. `REMOVE_MATERIAL` requires both a
`thickness_map` and a `modal_frequency`. Two artifacts of one required kind
are `AMBIGUOUS_REQUIRED_EVIDENCE`.

For a removal, projected remaining thickness is trusted thickness minus the
proposed removal. Strictly below `min_test_remaining_thickness_mm` is
`EVIDENCE_REQUIRED` / `THICKNESS_CONFLICT_WITH_REMOVAL`. Equality passes.

## Replay

`FrozenValidationSnapshotV1` freezes the proposal, the resolved facts, the
policy, the validator identity, and the verdict. `snapshot_sha256` is the
integrity of that record. The validation object itself leaves
`snapshot_sha256` unset. Replay reads the snapshot, checks the digest, and
does not call the live resolver. Changing the live store can change a new
validation. It cannot change the historical one.

The digest is a temporary internal deterministic encoding. Canonical external
serialization belongs to `PEP-V1-CONTRACT-002`.
