# Test matrix

File: `services/api/tests/physical_engineering/test_beginner_proposal_harness.py`.

| Test | Gate result name | What it pins |
| --- | --- | --- |
| `test_complete_request_copies_advisory_allowed` | `advisory_allowed` | Status equals `validation.result.value`. A second direct `validate_proposal()` on the stored proposal matches the stored verdict. Provenance says new construction, Grounding Agent not used, result owned by `validate_proposal`. |
| `test_no_evidence_refs_copies_evidence_required` | `evidence_required` | Empty citations stay empty. Reason includes `MISSING_REQUIRED_EVIDENCE_KIND`. |
| `test_unknown_evidence_ref_copies_evidence_required` | `evidence_required` | Reason is `EVIDENCE_REFERENCE_NOT_FOUND`. |
| `test_contradictory_evidence_copies_evidence_required` | `evidence_required` | Reason includes `CONTRADICTORY_EVIDENCE_PRESENT`. |
| `test_magnitude_above_caller_policy_copies_rejected` | `rejected` | The over-limit number comes from the caller's test policy. Reason includes `EXCESSIVE_REMOVAL_MAGNITUDE`. |
| `test_unknown_action_copies_rejected` | `rejected` | The action string is stored unchanged. Reason is `INVALID_ACTION_TYPE`. |
| `test_user_goal_is_not_parsed_into_a_magnitude` | `evidence_required` | Goal text "remove 5 mm" leaves `magnitude_mm` as `None`. Reason includes `REMOVAL_MAGNITUDE_MISSING`. |
| `test_non_advisory_claim_is_forwarded_and_rejected` | `rejected` | `manufacturing_authority` is not rewritten. Reason is `ILLEGITIMATE_AUTHORITY_CLAIM`. |
| `test_duplicate_evidence_ref_copies_rejected` | `rejected` | Refs are not deduped. Reason is `DUPLICATE_EVIDENCE_REFERENCE`. |
| `test_same_inputs_are_byte_stable` | `advisory_allowed` | Two `to_json` encodings match. The text uses `advisory_allowed` and does not use `PROPOSAL_READY`. |
| `test_blank_workflow_id_does_not_call_the_validator` | not called | `BeginnerProposalHarnessError` before `validate_proposal()`. |
| `test_missing_policy_does_not_call_the_validator` | not called | The harness does not invent a policy. |
| `test_validate_proposal_is_called_once` | `advisory_allowed` | One call on the complete fixture. |
| `test_harness_imports_stay_on_the_proposal_seam` | source | No import of `tools.grounding_agent`, archive, CAM, DXF, or G-code. No local redefinition of the proposal, policy, or result types. |
| `test_harness_source_records_new_construction_without_a_second_map` | source | Docstring records new construction and the order id. No `PROPOSAL_READY`, `0.6`, or `2.5`. |

Existing gate tests stay the behavior lock for `validate_proposal()` itself:

- `tests/physical_engineering/test_physical_engineering_proposal_v1.py`
- `tests/physical_engineering/test_pep_v1_harden_001.py`
