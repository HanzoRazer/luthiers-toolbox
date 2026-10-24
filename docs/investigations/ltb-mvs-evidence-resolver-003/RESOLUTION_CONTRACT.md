# Resolution contract

`StoredEvidenceResolver.resolve` implements `EvidenceResolver`. It returns one `ResolvedEvidence` or raises. It does not mutate the file.

Applicability is bound at construction because `resolve` receives only `EvidenceRef` (`ref_id`, `expected_kind`). `ApplicabilityContext` requires `subject_id`, `subject_revision`, `region_id`, `coordinate_frame`, and `unit_by_kind`. There are no defaults. A kind missing from `unit_by_kind` is `UNIT_MISMATCH`.

## Mapping into `ResolvedEvidence`

| Protocol field | Stored field |
| --- | --- |
| `ref_id` | `evidence_id` |
| `kind` | `evidence_kind` |
| `value` | `float(quantity_value)` |
| `unit` | `unit` |
| `uncertainty` | `float(uncertainty)` |
| `source_run` | `provenance.source_id` |
| `artifact_sha256` | `payload_digest` |

The resolver checks subject, revision, region, coordinate frame, and the caller-supplied unit before it returns that fact. `screening.py` still checks kind, finite value, uncertainty, source token, digest shape, and the thickness unit `mm`. Those gate checks are unchanged.

## Outcomes

| Code | How it surfaces |
| --- | --- |
| `RESOLVED` | Return value is a `ResolvedEvidence`. |
| `NOT_FOUND` | Existing `EvidenceNotFound`. The gate maps this to `evidence_required` / `EVIDENCE_REFERENCE_NOT_FOUND`. |
| `DIGEST_MISMATCH` | Existing `EvidenceDigestMismatch`. The gate maps this to `rejected` / `EVIDENCE_DIGEST_MISMATCH`. |
| `MALFORMED` | `StoredEvidenceResolutionError`. Propagates out of `validate_proposal`. |
| `SUBJECT_MISMATCH` | Same. |
| `REVISION_MISMATCH` | Same. |
| `REGION_MISMATCH` | Region or coordinate frame differs. |
| `UNIT_MISMATCH` | Unit differs from `unit_by_kind`, or the kind is absent from that map. |
| `SUPERSEDED` | Another record on the same subject and revision names this id in `supersedes_evidence_id`. |
| `DUPLICATE_REFERENCE` | Stays the gate's `DUPLICATE_EVIDENCE_REFERENCE`, before resolve. `duplicate_reference_ids` reports the same condition for callers. |
| `MULTIPLE_VALUES_REQUIRE_POLICY` | See below. |

`StoredEvidenceResolutionError` is not a subclass of `EvidenceNotFound` or `EvidenceDigestMismatch`, so screening does not turn it into `advisory_allowed`.

## Contradiction boundary

No owner-approved tolerance exists. Two active records with the same subject, revision, region, coordinate frame, quantity name, and unit, and different `quantity_value` strings, raise `MULTIPLE_VALUES_REQUIRE_POLICY`. The records are left in place. This is not `CONTRADICTORY_SET`.

Different quantity names in the same region are both resolvable.

Age is not staleness. A record is inactive only when a later record supersedes it. Age-based expiry belongs to validation policy.

## What resolution does not mean

A resolved fact is not a scientific endorsement, an engineering threshold result, a safety finding, or permission to manufacture. The resolver does not construct `ValidationPolicyV1` and does not emit `advisory_allowed`.
