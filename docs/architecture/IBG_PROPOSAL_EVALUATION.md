# IBG Repository Proposal Evaluation (PR F)

Status: implemented (IBG-1 PR F)
Subsystem: IBG Repository Intelligence — `services/api/app/ibg_repository/`
Constitutional classification: `observational_proposal_evaluation__no_approval_authority`

## 1. What this stage is

Repository Proposal Evaluation answers one question, deterministically, before a human reviewer
spends attention on a proposal:

> Is this proposal, together with the execution plan that claims to describe it, structurally
> complete, internally consistent, and continuous with the evidence provenance it claims?

It consumes a `RepositoryChangeProposal` (PR A) and its `RepositoryExecutionPlan` (PR E) and produces
a `RepositoryProposalEvaluation`: a content-addressed record of 25 structural check results, an
auditable completeness ratio, and a structural readiness label.

## 2. What this stage is not

Evaluation is **observational**. It scores, classifies, and reports. It does not:

- edit proposals, plans, or any repository state
- generate commits, execute git, or create pull requests
- alter governance, promote evidence, or upgrade an authority state
- approve, reject, block, or authorize engineering work

A failed check is a **reported observation**, not a rejection and not a withheld approval. The human
review boundary established by PR A–E is unchanged: this stage improves what reaches a reviewer, and
never substitutes for one.

The evaluator has no `approve`/`reject`/`merge`/`block`/`authorize` vocabulary at all — not as a
field, not as a status, not as a method — because a vocabulary is the first step toward an authority.

## 3. Position in the pipeline

```
BodyEvidenceCandidate
  -> ProposalTargetBinding            (PR A)
  -> RepositoryChangeProposal         (PR A)
  -> RepositoryReviewBundle           (PR C)   ---> human review boundary
  -> RepositoryProposalPipeline       (PR D)   (orchestration only)
  -> RepositoryExecutionPlan          (PR E)   (descriptive, no authority)
  -> RepositoryProposalEvaluation     (PR F)   (observational, no authority)   <-- this document
```

PR F is a **separate downstream consumer**, exactly as PR E is. It does not modify, wrap, or attach
to `RepositoryProposalPipeline`, and nothing evaluates implicitly as a side effect of running the
pipeline. A caller that wants an evaluation asks for one. This is enforced by test, not convention.

## 4. Inputs and outputs

**Input surface (exactly two artifacts):**

```python
evaluate_repository_proposal(
    proposal: RepositoryChangeProposal,
    plan: RepositoryExecutionPlan,
) -> RepositoryProposalEvaluation
```

The evaluator never builds a plan, never invokes `ExecutionPlanner`, never consumes pipeline output
or a review bundle, and never mutates either input. `ProposalEvaluator.evaluate()` is a thin,
stateless wrapper that delegates to the same owning function.

`evaluate_execution_plan(proposal, plan)` returns only the plan-facing findings (the `execution` and
`invariant` categories) for consumers that want the plan's story alone. It shares the same logic
rather than forking it.

**Output:** a frozen, content-addressed `RepositoryProposalEvaluation`.

## 5. Findings

Every check produces one `EvaluationFinding`:

```python
@dataclass(frozen=True)
class EvaluationFinding:
    check_id: str    # e.g. "provenance.producing_subsystem_continuous"
    category: str    # completeness | governance | provenance | execution | invariant
    status: str      # pass | fail | not_applicable
    detail: str      # deterministic, fact-only
```

**There is no `warn` status.** A warning is an implicit severity judgment, and severity is the
reviewer's call. A check either passed, failed, or did not apply.

Findings are sorted deterministically by `(category, check_id)`. The order in which checks happen to
run is an implementation accident and carries no constitutional meaning, so it never leaks into the
content-addressed id.

**Each check has exactly one owning category.** No finding is duplicated across category lists — a
duplicate would double-count in the score and mislead the reviewer.

## 6. The check set (25 checks)

### completeness (8) — are the required fields structurally present?

| check | notes |
|---|---|
| `completeness.proposal_id_present` | |
| `completeness.changed_file_summary_present` | |
| `completeness.cbsp21_packet_readable` | |
| `completeness.execution_plan_id_present` | |
| `completeness.execution_groups_present` | `not_applicable` when the proposal declares no files |
| `completeness.validation_sequence_present` | `not_applicable` when the packet declares no commands |
| `completeness.complexity_summary_present` | |
| `completeness.provenance_reference_present` | |

### governance (6) — does the proposal conform to the governed contracts?

| check | notes |
|---|---|
| `governance.cbsp21_packet_valid` | delegates to `validate_cbsp21_patch_packet` |
| `governance.declared_risk_supported` | reuses PR-E's `SUPPORTED_RISK_LEVELS` |
| `governance.behavior_change_articulated` | delegates to `validate_behavior_change_articulation` |
| `governance.changed_files_within_authorized_paths` | reuses the proposal builder's containment semantics |
| `governance.proposal_classification_unchanged` | still `proposal_only__no_canonical_authority` |
| `governance.authority_state_not_upgraded` | see §8 |

These **delegate to the existing validators**. The rule sets are not forked into a second,
drifting implementation.

### provenance (4) — are the governed evidence fields continuous?

One check per governed field: `evidence_candidate_id`, `evidence_provenance_hash`,
`producing_subsystem`, `source_authority_state`. Each confirms the value is non-empty **and
identical** between `proposal.target` and `plan.provenance_reference`.

Continuity requires **exact** equality. Missing provenance is reported, never inferred or repaired.

### execution (3) — is the plan internally sound?

| check | notes |
|---|---|
| `execution.plan_classification_descriptive` | still `descriptive_execution_plan__no_repository_authority` |
| `execution.plan_id_matches_content_hash` | an id that disagrees with its content means the plan was altered after it was built |
| `execution.plan_groups_internally_consistent` | review-order / structural groups reference only commit-sequence files |

### invariant (4) — do the two artifacts agree with each other?

| check | notes |
|---|---|
| `invariant.plan_proposal_id_matches` | see §7 — always `pass` when an evaluation exists |
| `invariant.plan_covers_all_declared_files` | no declared file missing from the plan |
| `invariant.plan_introduces_no_undeclared_files` | the plan may not invent scope |
| `invariant.validation_sequence_matches_packet` | verbatim match against the packet's declared commands |

## 7. Error vs finding

`ProposalEvaluationError` is raised **only** when the artifacts cannot be coherently evaluated:

- wrong input type, or `None`
- the proposal and plan describe **different** proposals (an unrelated pairing is not evaluable at
  all, and emitting a finding would imply the pairing was meaningful)
- no applicable checks (an empty score denominator)
- content that cannot be canonically serialized

Every **substantive readiness gap in an evaluable artifact** is reported as a failed finding, never
raised: missing provenance, an empty validation sequence, invalid CBSP21 content, files outside the
authorized boundary, an unsupported risk level, a plan/proposal file-set mismatch, provenance
discontinuity, incomplete plan content.

The distinction is the point. An exception hides from the reviewer exactly what they need to see; a
finding shows it to them alongside the other 24 results.

`invariant.plan_proposal_id_matches` therefore always reports `pass` on any evaluation that exists:
its failure mode raises before any check runs. It is still reported so the reviewer can see the
invariant was affirmatively established rather than assumed.

### Why defects are reachable at all

`build_repository_change_proposal` and `build_execution_plan` are fail-closed, so artifacts produced
through them cannot carry most of these defects. But the contracts are plain frozen dataclasses and
can be constructed directly, so the evaluator deliberately evaluates the artifacts **as given**
rather than assuming a builder produced them. That independence is what makes it worth having: it is
a check, not a restatement of the builders' preconditions.

## 8. What `authority_state_not_upgraded` does and does not assert

It asserts that the carried `source_authority_state` is a label the governance `AuthorityState` enum
**recognizes**. An invented or relabelled state is how an upgrade would be smuggled past review, and
that is detectable from the artifacts alone.

It deliberately does **not** judge *which* recognized state the evidence holds. A proposal built from
canonical evidence legitimately carries `canonical_geometry`, and the evaluator has no access to the
live candidate to compare against — so asserting a "correct" level would be an invented claim, not an
observation. Continuity of the state between proposal and plan is owned by the `provenance` category.

## 9. Completeness score

```
completeness_score = checks_passed / checks_applicable
```

It is an **auditable structural ratio and nothing more**. It is not a confidence score, a quality
score, a subjective readiness score, or an inferred score, and it carries no weighting or judgment:
every applicable check counts exactly once.

- `not_applicable` checks are **excluded from the denominator**, so a check that legitimately does
  not apply can neither reward nor penalize the score.
- The four underlying counts (`checks_passed`, `checks_failed`, `checks_not_applicable`,
  `checks_applicable`) are stored explicitly, so the ratio is reproducible by hand.
- It is computed with `decimal.Decimal` (quantized to two places, `ROUND_HALF_UP`) and serialized as
  a fixed-precision **string** (`"0.90"`). A binary float would make the canonical serialization —
  and therefore the content-addressed id — depend on floating-point representation.
- When `checks_applicable == 0`, construction **fails closed** rather than inventing a score for an
  empty denominator.

The score describes only the fraction of applicable structural checks that passed. **It is not an
approval and must not be reported as one.**

## 10. Readiness label

```
readiness_summary = "complete" | "incomplete"
```

- `complete` — every applicable structural check passed
- `incomplete` — one or more applicable structural checks failed

The label is derived **only** from the failed-applicable count. A `not_applicable` check is an
absence of evidence, not a defect, and can never flip the label.

These labels describe structural evaluation only. `complete` never means approved, safe to merge,
authorized, canonically valid, or ready to execute. `incomplete` never means rejected or blocked.

## 11. Identity and determinism

```
evaluation_id = "eval-" + sha256(canonical_content)[:16]
```

Identical artifacts produce byte-identical evaluations. Excluded from the id and from
`to_canonical_dict()`: wall-clock time, environment values, object reprs, and incidental ordering.
The optional informational `created_at` surfaces only through `to_audit_dict()`.

`evaluation_summary` is generated from a fixed deterministic template over declared facts. There is
deliberately **no free-form `reviewer_notes` field**: evaluator-authored prose invites interpretation
and non-determinism. Human notes belong outside the canonical evaluation contract.

`validate_repository_proposal_evaluation()` re-checks an already-built evaluation: that its id matches
its content, its counts agree with its findings, its score follows from its counts, its readiness
label follows from its failures, and every finding carries a recognized category and status.

## 12. How a reviewer should read an evaluation

1. **`readiness_summary`** — `incomplete` means at least one applicable structural check failed. It
   does **not** mean the proposal is wrong, unsafe, or rejected; it means something the evaluator can
   check mechanically did not line up. It is a prompt to look, not a verdict.
2. **`completeness_score`** — the fraction of applicable checks that passed. Useful for triage
   ordering across many proposals. It is not a quality measure and must never be used as an approval
   threshold.
3. **The failed findings** — each names its `check_id` and a fact-only `detail`. Start here.
4. **`not_applicable` findings** — these tell you what the evaluator *could not* speak to. That
   absence is itself information: it marks the parts of readiness a human must assess unaided.
5. **`complete` is a floor, not a ceiling.** It means the artifacts are structurally sound. Whether
   the change is *correct*, *wise*, or *wanted* is not a question this stage can ask, and a
   `complete` evaluation is not evidence that it was asked.

## 13. Constitutional impact

| dimension | impact |
|---|---|
| Public API | additive (`RepositoryProposalEvaluation`, `ProposalEvaluator`, entry points) |
| Schema | `RepositoryProposalEvaluation` added |
| Measurement | extended (structural checks only) |
| Interpretation | extended through evaluation only |
| Governance | unaffected |
| Scientific validity | preserved (no inferred or invented values) |
| Production behavior | unchanged (no existing runtime path imports the evaluator) |

An AST-precise test forbids the PR-F modules from importing `subprocess`/`os`/`shutil`/`tempfile`/
network/GitHub clients or the PR-B `git_runner` and worktree machinery — the evaluator may not even
*import* an execution capability, let alone use one.
