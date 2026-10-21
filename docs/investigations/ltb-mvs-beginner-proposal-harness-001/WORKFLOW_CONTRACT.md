# Beginner proposal workflow contract

Module: `services/api/app/physical_engineering/beginner_proposal_harness.py`.

The harness may collect inputs, attach the evidence references the caller already holds, call `validate_proposal()` once, and format a guided result. Evidence bytes are resolved inside that one validator call. The harness does not pre-resolve them and does not catch a validator exception in order to draw a different conclusion.

## Request

`BeginnerProposalRequest` carries identity, the caller's action, the caller's authority claim, an optional magnitude, an optional region, and evidence citations.

Required before the validator is called: `workflow_id`, `proposal_id`, `subject_id`, `subject_revision`, `user_goal`, `action`, `claimed_authority`, plus a caller-supplied resolver and policy. A blank identity field or a missing resolver or policy raises `BeginnerProposalHarnessError`. `validate_proposal()` is not called.

`magnitude_mm`, `region_id`, `coordinate_frame`, and `units` may be absent. The harness does not fill them. An empty `evidence_refs` tuple means the caller cited nothing. That absence is passed through. It is not a measurement default.

`user_goal` is copied into `ProposedChange.description` and `engineering_basis`. It is not scanned for numbers. A goal that says "remove 5 mm" does not become `magnitude_mm`.

`claimed_authority` is copied onto the proposal. A value other than `advisory_only` is not rewritten. The gate rejects it with `ILLEGITIMATE_AUTHORITY_CLAIM`.

`requested_validation` is always empty. The beginner request has no channel for asserting `authorized`, `approved`, `authority_granted`, or `allow`.

`schema_id` is `physical_engineering_proposal` and `schema_version` is `1.0`. Those strings identify the existing proposal contract. `proposing_actor` is `beginner-proposal-harness`, the adapter's name.

Subject fields map onto the existing geometry claim:

| Request | Proposal |
| --- | --- |
| `subject_id` | `GeometryRegion.object_id` |
| `subject_revision` | `GeometryRegion.geometry_revision` |
| `region_id`, `coordinate_frame`, `units` | the same fields, including `None` |

The harness does not check that an evidence record applies to `subject_revision`. `ResolvedEvidence` has no subject or revision field. Inventing that check would be a new engineering rule. See `DEFERRED.md`.

## Result

`BeginnerGuidedResult.status` is `validation.result.value`. The only names the gate emits are:

- `advisory_allowed`
- `evidence_required`
- `rejected`

`explanations` is a copy of `reason_codes`. `required_evidence` is a copy of the gate's `required_evidence`. `guidance_lines` quote those values. They do not add a recommendation, a score, or a paraphrase that could disagree with the verdict.

`provenance.construction` is `new`. `provenance.recovered_historical_code` is false. `provenance.grounding_agent` is `not_used`. `provenance.result_owner` is `validate_proposal`. `provenance.validator_version` is copied from the validation object.

`advisory_review_allowed` stays the gate's boolean. This adapter does not set it.
