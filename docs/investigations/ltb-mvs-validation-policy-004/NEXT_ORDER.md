# Next order

`LTB-MVS-GUIDED-REVIEW-SLICE-002` can resume only after this policy increment is merged. PR #455 is already on `main`. This pull request is still a draft.

Entry conditions for the guided slice:

1. `FileEvidenceRepository` and `StoredEvidenceResolver` are on `main` (met by PR #455).
2. This policy selector is on `main`, still with no developer-chosen threshold hiding inside it.
3. An owner has approved one active policy record in a later change, or the endpoint fails closed when `select_validation_policy` raises `VALIDATION_POLICY_NOT_FOUND`.
4. The first guided change is an internal review endpoint. It calls `run_beginner_proposal` once with the stored resolver and the selected policy.
5. The beginner-facing client comes after that endpoint returns the validator's own `advisory_allowed`, `evidence_required`, or `rejected` without a second vocabulary.

The endpoint path named by the policy order, `POST /api/physical-engineering/beginner-proposal/review`, stays unregistered in this increment.

`advisory_allowed` remains human review only. The endpoint must not turn it into manufacturing authority.
