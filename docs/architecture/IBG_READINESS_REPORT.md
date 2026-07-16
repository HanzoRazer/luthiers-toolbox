# IBG Repository Readiness Report (IBG-1 PR G)

The **readiness report** is the aggregation layer of the IBG-1 repository pipeline. Given the three
merged upstream artifacts — a `RepositoryChangeProposal` (PR A), its `RepositoryExecutionPlan`
(PR E), and its `RepositoryProposalEvaluation` (PR F) — it produces a single content-addressed
`RepositoryReadinessReport` that a human reviewer can read as one coherent picture.

It **aggregates and presents. It does not decide, and it does not compose new findings.**

```
proposal ─┐
plan ─────┼──▶ build_repository_readiness_report ──▶ RepositoryReadinessReport
evaluation┘         (lineage + provenance checked first)
```

## What it is — and is not

| It is | It is not |
|---|---|
| A verbatim copy of canonical upstream values | A new evaluation, score, or severity |
| A structural projection of governance findings | A governance judgment or recommendation |
| A content-addressed, byte-stable artifact | A mutable or free-form document |
| Terminal at the human-review boundary | An approval, gate, or execution trigger |

The report has **no vocabulary for approval** because it holds none of that authority. The constant
`READINESS_REPORT_CONSTITUTIONAL_CLASSIFICATION` is
`aggregation_readiness_report__no_approval_authority`, and tests assert the absence of
approve/reject/authorize/merge/commit/push vocabulary from the report's own fields.

## Contract

`RepositoryReadinessReport` (frozen, content-addressed) carries:

- **Three lineage references** — `proposal_id`, `execution_plan_id`, `evaluation_id`. These are
  references to canonical upstream artifacts, never newly generated substitutes.
- **Its own identity** — `readiness_report_id` = `rpt-` + `sha256(canonical_content)[:16]`, matching
  the package convention (`rep-` plans, `eval-` evaluations). It identifies the aggregation artifact
  and replaces none of the three references. `created_at` is informational and excluded from the id,
  the hash, and the canonical serialization.
- **`governance_summary`** — a frozen `RepositoryGovernanceSummary(finding_count, check_ids)`. See
  below.
- **Three summary strings, copied verbatim** — `execution_summary`, `evaluation_summary`,
  `readiness_summary`.
- **`report_sections`** — a fixed, ordered tuple of four frozen sections.

### Summary field mapping

| Report field | Source | Note |
|---|---|---|
| `execution_summary` | `execution_plan.planning_summary` | **Documented rename.** The report schema settled on `execution_summary`; the value is copied unchanged. |
| `evaluation_summary` | `evaluation.evaluation_summary` | Copied verbatim. |
| `readiness_summary` | `evaluation.readiness_summary` | Copied verbatim; see vocabulary below. |

These are **copied, never composed.** The report manufactures no interpretive rollup of its own.

### Readiness vocabulary

`readiness_summary` is a projection of PR F's closed vocabulary — exactly `complete` or
`incomplete`. The report never introduces `ready`, `blocked`, `approved`, `rejected`, `pass`, or
`fail`; the builder **rejects** any readiness value outside F's vocabulary (`validate_readiness_summary`)
rather than normalize or reinterpret it. `complete` means "every applicable structural check passed"
— never approved, safe to merge, authorized, or ready to execute.

### Governance summary

`governance_summary` is a deterministic **structural** projection of the evaluation's
`governance_findings`, limited to facts already in those findings:

```python
@dataclass(frozen=True)
class RepositoryGovernanceSummary:
    finding_count: int              # == len(evaluation.governance_findings)
    check_ids: tuple[str, ...]      # each finding.check_id, in upstream canonical order
```

The `check_ids` are the findings' own `check_id` values in the evaluation's canonical order (F
already sorts governance findings by `(category, check_id)`); the report **does not re-sort them**,
so there is exactly one ordering policy in the system, and it lives upstream. No severity, no
recommendation, no approval status, no prose.

### Report sections

`report_sections` is a closed, ordered vocabulary owned by the builder — callers cannot supply,
reorder, or extend it:

```
proposal → execution → evaluation → provenance
```

Each `RepositoryReadinessSection(section_key, entries)` holds references and verbatim canonical
values as an ordered tuple of `(name, value)` pairs — never an independently authored conclusion.
Serialization preserves the fixed order and is byte-identical for semantically identical inputs.

The **evaluation** section copies every canonical evaluation outcome exactly — `evaluation_id`,
`readiness_summary`, `completeness_score`, and all four check counts
(`checks_passed`/`checks_failed`/`checks_not_applicable`/`checks_applicable`) — and the report does
**not** recompute, derive, normalize, or re-infer any of them. Those calculations belong to F.

## The builder guarantees one coherent chain

`build_repository_readiness_report(proposal, execution_plan, evaluation)` proves the three artifacts
describe a single chain **before** it copies any value or hashes anything:

**Lineage** — all of:

```
proposal.proposal_id == execution_plan.proposal_id == evaluation.proposal_id
execution_plan.execution_plan_id == evaluation.execution_plan_id
```

**Provenance** — the plan's `provenance_reference` must agree, field for field, with the proposal's
target binding across the four evidence-owned fields (`evidence_candidate_id`,
`evidence_provenance_hash`, `producing_subsystem`, `source_authority_state`). The provenance
section is then built **solely** from the plan's `provenance_reference` — a single construction
path, with the proposal binding used only to validate it, never as a second source.

Any lineage or provenance mismatch is a **construction error** (`ReadinessReportError`). The builder
does **not** emit a partial, warning-only, or "incomplete" report for a broken chain: `incomplete`
describes *evaluated readiness* and does not legitimize mismatched artifacts. This mirrors the
lineage guarantees the upstream builders already enforce.

## Boundary: aggregation, not repository execution

The readiness-report model, builder, serializer, and tests **do not** execute git, inspect a
worktree, invoke a subprocess, perform filesystem archaeology or repository-state discovery, or
import the package's git-execution utilities (`git_runner`, `worktree_builder`, and the worktree
machinery). An AST-precise test enforces this on both G modules.

This boundary applies **to PR G**, not retroactively to the whole `ibg_repository` package — the
package legitimately contains git-execution utilities (PR B) that other layers use. The report may
*carry* provenance that upstream artifacts supplied; it may not *discover* provenance itself.

## How to read a report

1. Confirm the three lineage IDs and `readiness_report_id` — every copied value can be verified
   against its cited source artifact.
2. Read `readiness_summary`: `complete`/`incomplete` is a **structural** statement, not a decision.
3. Read the evaluation section's `completeness_score` and counts as F computed them.
4. Scan `governance_summary.check_ids` for which governance checks were evaluated.
5. Decide. **The report does not.**

## Verification

- Focused: `tests/ibg_repository/test_repository_readiness_report.py` and
  `test_readiness_report_builder.py`.
- Full package suite: `tests/ibg_repository/` (no regressions).
- New-module coverage: contract 100%, builder 97% (the sole uncovered lines are a defensive
  canonical-serialization guard unreachable while all canonical content is `str`/`int`).
