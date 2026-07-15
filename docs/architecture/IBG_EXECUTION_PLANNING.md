# IBG Repository Execution Planning (Descriptive Layer)

> **Status:** PR E (IBG-1). Additive, descriptive-only. This document describes the planning stage
> that turns an approved `RepositoryChangeProposal` into a `RepositoryExecutionPlan` — a description
> of *how* a human engineer could organize the work. It introduces **no** repository mutation,
> execution, or authority. It stops at the same human boundary the canonical proposal pipeline does.

## Where planning sits

```
BodyEvidenceCandidate ─▶ … ─▶ RepositoryChangeProposal ─▶ build_review_bundle ─▶ ■ human review ■
                                        │
                                        │  build_execution_plan   (PR E — SEPARATE downstream consumer)
                                        ▼
                              RepositoryExecutionPlan
                                        │
                                        ▼
                              ■ STOP — human review ■        engineers organize/execute the work
```

Execution planning is a **separate downstream consumer** of the merged proposal contract. It does
**not** modify, wrap, or attach to `RepositoryProposalPipeline` (PR D). A later integration PR may
compose the two if explicitly authorized; PR E deliberately keeps them independent.

## Input

A single, already-approved `RepositoryChangeProposal` (PR A). Provenance is read from the proposal's
`target` binding — planning is never handed raw evidence and never re-derives it.

## Output — `RepositoryExecutionPlan`

A frozen, content-addressed dataclass. `execution_plan_id = "rep-" + sha256(canonical_content)[:16]`.
Every field is **derived** from data the proposal already declares; nothing is invented.

| Field | Derived from | Honesty note |
|---|---|---|
| `recommended_validation_sequence` | packet `verification.commands_run` | copied **verbatim, in declared order**; no command added |
| `recommended_commit_sequence` | declared files grouped by authorized target-path prefix | a **descriptive grouping**, not a claim that each group must be one commit |
| `recommended_review_order` | the same evidence-backed groups, deterministic path order | **no inferred reviewer priority** |
| `structural_dependency_groups` | the same path grouping | `relationship = "declared_path_grouping"` — **not** a proven dependency edge |
| `estimated_complexity` | declared file/path counts + declared `risk_level` | a documented deterministic table; **no** effort/duration/score/confidence inference |
| `provenance_reference` | the four evidence-owned binding fields | preserved **exactly** |
| `planning_summary` | declared title/change-type/counts/risk | fact-only; states that no dependency evidence exists |

### Why `structural_dependency_groups`, not `dependency_graph`

The proposal declares **no inter-file dependency evidence**. Representing a path grouping as a proven
dependency graph would misstate what is known. The field name states what the data actually is: a
structural (path-containment) grouping. Where the source lacks information, the plan says so — in the
field name, the `relationship` value, and the `planning_summary` prose.

### Complexity label table (auditable)

```
file tier:  count <= 2 -> 0 ("low") | 3..8 -> 1 ("medium") | > 8 -> 2 ("high")
risk tier:  low -> 0 | medium -> 1 | high -> 2 | critical -> 2
label = ["low", "medium", "high"][max(file_tier, risk_tier)]
```

The raw counts and the declared risk level are kept visible on `ComplexitySummary` so the label is
auditable and reproducible. An **unsupported** declared `risk_level` (outside
`{low, medium, high, critical}`) is rejected rather than silently bucketed.

## Determinism

Identical proposals produce byte-identical plans. Wall-clock time, environment paths, object reprs,
and unordered sets never enter the canonical form. An optional informational `created_at` is excluded
from `execution_plan_id`, the content hash, and `to_canonical_dict()`; it surfaces only through
`to_audit_dict()`.

## Fail-closed rules

`build_execution_plan` raises `ExecutionPlanningError` (reusing the proposal/CBSP21 validation first,
then enforcing only PR-E invariants) when:

* the input is not a `RepositoryChangeProposal`, or its `proposal_id` is empty;
* the proposal declares no changed files;
* a declared file falls outside the binding's `authorized_target_paths`;
* the proposal's `changed_file_summary` disagrees with the packet's `scope.files_expected_to_change`;
* a provenance-reference field is missing;
* the declared `risk_level` is unsupported;
* a canonical (deterministic) serialization cannot be produced.

### Scope agreement compares the file set, not its spelling

Both sides of that comparison are normalized first (trim, `\` → `/`, no leading/trailing `/`, deduped,
sorted), and the plan carries the normalized form. This matters because the two inputs are not
normalized the same way at their source: `build_cbsp21_patch_packet` normalizes its scope, but
`build_repository_change_proposal` derives `changed_file_summary` with `sorted({str(f) ...})` and
keeps the packet's raw spelling — only its *boundary check* normalizes. A packet supplied as a raw
dict (the shape `RepositoryProposalPipeline` accepts, and the shape a `.cbsp21/patches/*.json` file
loads as) therefore reaches the planner with the author's formatting intact. Comparing a raw summary
to a normalized scope would reject a proposal that agrees on *what changes* and differs only in how a
path is written. Normalizing both sides removes that false negative; two genuinely different file
sets still disagree and still fail closed.

## Validating a plan built elsewhere

`validate_execution_plan` is not a restatement of the builder's preconditions — every plan
`build_execution_plan` produces satisfies it by construction. It exists for plans that arrive from
*elsewhere*: hand-constructed via the public frozen dataclasses, or revived from a serialized
`to_canonical_dict()`. For those, the content hash alone proves nothing: `compute_plan_hash()` is
derived *from* the plan, so any self-consistent plan matches its own id. The hash detects tampering
**after** construction; it cannot detect a dishonest construction. So the validator also enforces:

* `constitutional_classification` is unchanged — a plan may not self-declare authority;
* every structural group is labelled `declared_path_grouping` — never a synthesized dependency edge
  the proposal has no evidence for;
* commit / review / dependency collections partition the **same** declared file set — a plan cannot
  silently drop review or dependency coverage for a declared file, nor claim a file in two groups,
  nor list a file outside its own `path_prefix`;
* `planning_summary`, provenance fields, and at least one validation command are present (CBSP21
  requires a non-empty `verification.commands_run`, so a real plan always carries one);
* `estimated_complexity` still agrees with the documented table over its own declared inputs.

## Authority boundary — what planning is NOT

Planning is **descriptive**. It does not commit, push, merge, create a pull request, mutate a
checkout, run CI, promote evidence, or exercise repository or canonical authority. `ExecutionPlanner`
exposes exactly one operation — `plan` — and no execute/commit/push/PR verb. An AST-precise test
forbids the modules from importing `subprocess`, `os`, `shutil`, `tempfile`, network/GitHub clients,
or the PR-B execution machinery (`git_runner`, worktree builder/validator/spec/state).

**Termination point:** the plan is a description handed to a human. IBG stops here.

## Public API (additive)

`RepositoryExecutionPlan`, `ExecutionGroup`, `DependencyGroup`, `ComplexitySummary`,
`ProvenanceReference`, `ExecutionPlanner`, `build_execution_plan`, `execution_plan_builder`,
`validate_execution_plan`, `ExecutionPlanningError`, `SUPPORTED_RISK_LEVELS`,
`EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION`, `STRUCTURAL_GROUPING_RELATIONSHIP`.
