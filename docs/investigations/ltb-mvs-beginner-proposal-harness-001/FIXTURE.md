# Deterministic beginner fixture

The first fixture is a beginner-oriented `remove_material` request. It lives in `services/api/tests/physical_engineering/test_beginner_proposal_harness.py` as `_request()`.

The complete case:

| Field | Value |
| --- | --- |
| `workflow_id` | `beginner-remove-material-001` |
| `proposal_id` | `prop-beginner-0001` |
| `subject_id` | `plate-007` |
| `subject_revision` | `rev-3` |
| `action` | `remove_material` |
| `claimed_authority` | `advisory_only` |
| `magnitude_mm` | `0.25` |
| `region_id` | `lower-bout-R17` |
| `coordinate_frame` | `plate-local` |
| `units` | `mm` |
| evidence | the two citations from the existing gate fixture: modal frequency `ttp-2026-10-04-mode3` and thickness map `thk-2026-10-04-R17` |

The resolver and the policy are the existing test helpers `_resolver()` and `_policy()` in `test_physical_engineering_proposal_v1.py`. `TEST_MAX_REMOVAL_MM` (`0.6`) and `TEST_MIN_REMAINING_MM` (`2.5`) stay in that file. They are test-policy thresholds. The harness source does not contain them and does not choose them.

Other cases in the same test module change one part of this request: no citations, an unknown ref id, a contradiction tuple, a magnitude above the caller-supplied test policy, an unknown action, a prose goal with `magnitude_mm=None`, a non-advisory authority string, or a duplicated ref id. Each expected status is the gate's status for that input.
