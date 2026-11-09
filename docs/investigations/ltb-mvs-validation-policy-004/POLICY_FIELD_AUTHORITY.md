# Policy field authority

Phase 0 inventory of `ValidationPolicyV1` in `services/api/app/physical_engineering/policy.py`. Searched `services/api` for `ValidationPolicyV1(`. The only production construction added by this increment is `select_validation_policy`, and it runs only after one approved active record matches. The only other construction is `_policy()` in `tests/physical_engineering/test_physical_engineering_proposal_v1.py`.

No owner has approved a production value. The proposed production value for every field is **none**.

| Field | Type and unit | Required | Validator consumer | Production value | Source | Approver | Approval date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `policy_id` | text token, no unit | yes | copied onto `PhysicalEngineeringValidationV1.policy_id` by `proposal_v1.py` | none | none | none | none |
| `policy_version` | text token, no unit | yes | copied onto `PhysicalEngineeringValidationV1.policy_version` | none. A stored record's `policy_revision` is copied into this existing field. The validator field was not renamed. | none | none | none |
| `max_test_removal_mm` | finite float greater than zero, unit millimeters as named by the field and compared with `magnitude_mm` | yes | `screening._magnitude_failure`. For `remove_material`, a magnitude above this value returns `rejected` / `EXCESSIVE_REMOVAL_MAGNITUDE`. `acquire_more_evidence` returns before this check. `modify_brace` is rejected as not yet governed before this check. | none. The test fixture `0.6` is not a source. | none | none | none |
| `min_test_remaining_thickness_mm` | finite float that is not negative, unit millimeters | yes | `screening._one_thickness`. Remaining thickness is the resolved thickness minus removal. A remaining value below this number returns `evidence_required` / `THICKNESS_CONFLICT_WITH_REMOVAL`. Equality satisfies the test. | none. The test fixture `2.5` is not a source. | none | none | none |

## Record fields that are not validator fields

These exist so a record can be approved and selected. They are not engineering limits.

| Field | Rule | Production value |
| --- | --- | --- |
| `schema_id` | `ltb_validation_policy` | fixed schema identity, not a threshold |
| `schema_version` | `1.0` | fixed schema identity |
| `status` | `DRAFT`, `ACTIVE`, `SUPERSEDED`, or `REVOKED` | no record is shipped |
| `applicability.subject_id` | exact text token | none |
| `applicability.action` | exact action string | none |
| `policy_values.*_unit` | must be `mm`, because that is the unit the existing fields already use. Other units are refused. Nothing is converted. | none |
| `provenance.source_type`, `source_id`, `recorded_by` | required text | none |
| `approval.approved_by` | required for every status except `DRAFT` | none |
| `approval.approved_at` | timezone-aware timestamp | none |
| `approval.approval_basis_refs` | at least one text token | none |
| `approval.approved_payload_digest` | SHA-256 of the canonical payload, which excludes `approval` and `payload_digest` | none |
| `payload_digest` | same SHA-256 | none |

## Unresolved questions

1. Who is allowed to approve a production policy?
2. Which published source, measurement campaign, or owner decision justifies `max_test_removal_mm`?
3. Which source justifies `min_test_remaining_thickness_mm`?
4. Which subject and action does the first production policy cover?
5. Does a later policy replace the test-named fields, or do those field names remain?

Until those answers exist, `select_validation_policy` has no active record to return.
