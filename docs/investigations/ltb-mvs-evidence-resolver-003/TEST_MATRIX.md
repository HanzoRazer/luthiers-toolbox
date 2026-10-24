# Test matrix

Focused suite, from `services/api`: 142 passed (`--no-cov`). The prior baseline of the three existing physical-engineering files was 102 passed.

| ID | Test | Result |
| --- | --- | --- |
| EVR-001 | `test_valid_record_is_accepted_and_digest_matches` | Accepted |
| EVR-002 | `test_blank_evidence_id_is_refused` | Refused |
| EVR-003 | `test_blank_subject_id_is_refused` | Refused |
| EVR-004 | `test_missing_subject_revision_is_refused` | Refused |
| EVR-005 | `test_missing_region_is_refused` | Region is required on every stored record |
| EVR-006 | `test_unknown_evidence_type_is_refused` | Refused |
| EVR-007 | `test_non_identifier_unit_is_refused_without_conversion` | `MM` refused |
| EVR-008 | `test_non_finite_quantity_text_is_refused` | Refused |
| EVR-009 | `test_naive_timestamp_is_refused` | Refused |
| EVR-010 | `test_valid_record_is_accepted_and_digest_matches` | Digest matches canonical payload |
| EVR-011 | `test_changed_digest_is_refused_at_construction`, `test_payload_changed_after_digest_is_digest_mismatch`, `test_tampered_file_is_digest_mismatch` | `DIGEST_MISMATCH` |
| EVR-012 | `test_save_then_retrieve_preserves_fields` | Field identity preserved |
| EVR-013 | `test_reopen_reads_the_same_bytes`, `test_new_process_reads_the_saved_record` | Reopen and a new process both read the record |
| EVR-014 | `test_same_id_with_different_payload_is_refused` | `DuplicateEvidenceContent` |
| EVR-015 | `test_missing_id_is_not_found` in the repository and resolver tests | `EvidenceNotFound` |
| EVR-016 | `test_wrong_subject_is_subject_mismatch` | `SUBJECT_MISMATCH` |
| EVR-017 | `test_wrong_revision_is_revision_mismatch` | `REVISION_MISMATCH` |
| EVR-018 | `test_wrong_region_is_region_mismatch` | `REGION_MISMATCH` |
| EVR-019 | `test_unit_not_in_the_caller_binding_is_unit_mismatch` | `UNIT_MISMATCH` |
| EVR-020 | `test_superseded_record_is_refused` | `SUPERSEDED`; the successor still resolves |
| EVR-021 | `test_duplicate_reference_ids_are_reported_in_citation_order`, `test_duplicate_refs_stay_rejected_by_the_gate` | Gate reason `DUPLICATE_EVIDENCE_REFERENCE` |
| EVR-022 | `test_two_active_values_require_policy_instead_of_a_tolerance` | **Deviation.** Code is `MULTIPLE_VALUES_REQUIRE_POLICY`, not `CONTRADICTORY_SET`. No tolerance was invented. |
| EVR-023 | `test_different_quantities_are_not_treated_as_contradictions` | Both facts resolve |
| EVR-024 | `test_resolve_does_not_change_the_stored_bytes`, `test_stored_record_cannot_be_mutated` | Bytes unchanged; frozen record |
| EVR-025 | `test_repeated_resolution_is_deterministic` | Equal results |
| EVR-026 | `test_harness_calls_the_validator_once_with_the_stored_resolver` | One `validate_proposal` call. Status equals `validation.result`. The test policy is the existing `_policy()` fixture. |
| EVR-027 | `test_missing_evidence_is_the_gate_evidence_required_result` | `evidence_required` |
| EVR-028 | `test_subject_mismatch_propagates_and_is_not_advisory` | `SUBJECT_MISMATCH` propagates |
| EVR-029 | Harness status is the validator result. Resolver source does not contain `advisory_allowed`. | Resolution does not grant review |
| EVR-030 | `test_missing_policy_does_not_call_the_harness_validator` | `BeginnerProposalHarnessError` before the validator |
| EVR-031 | `test_new_modules_do_not_add_routes_or_manufacturing_imports` | No `fastapi` or `APIRouter` in the new modules |
| EVR-032 | Same structural test | No `cam`, `dxf`, `gcode`, `art_studio`, or `rmos` imports |
| EVR-033 | The three existing physical-engineering files in the same pytest invocation | Still passing inside the 142 |
| EVR-034 | `test_in_memory_resolver_remains_the_test_fixture` | Docstring still says it is not a database record |
| EVR-035 | Structural import ban; rosette, RMOS, and Alembic files are not in this diff | Those stores are unchanged |

`test_omitted_magnitude_is_not_taken_from_the_goal` keeps `magnitude_mm` as `None` when the goal text says "remove 5 mm".
