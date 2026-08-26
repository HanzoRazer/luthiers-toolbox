# Grounding Agent v0.1 — Read-Only Handoff Truth Check

> **Grounding Agent verifies handoff state. It does not decide what to do about
> stale state.**

## Mission

The Grounding Agent answers exactly one question:

> Does this handoff describe the repository as it actually exists right now?

It receives a structured set of handoff claims, checks each against live
Git / GitHub / filesystem evidence, and returns a claim-by-claim report with a
top-level status and a mandatory execution decision. It **never** repairs a
mismatch and it **never** suggests a remediation.

## Authority

- **Read-only is constitutional.** The package has no write adapter and no
  generic command runner. Its adapters expose read operations only. There is no
  code path for `git commit`, `git checkout -b`, `git push`, `gh pr edit`,
  GitHub `POST/PATCH/PUT/DELETE`, or repository file writes. The only file the
  tool ever writes is the JSON report, and only when `--output` is supplied.
- The agent does not manage the active lane; it verifies and reports it.

## Non-scope (v0.1)

Not implemented, by design: Reconciliation / Queue / Dev-Order / Implementation
/ PR-Risk agents, session orchestration, queue or `SPRINTS.md` mutation, PR
comments/labels, branch/commit/merge/issue creation, remediation suggestions
beyond a factual stop reason, runtime API testing, code-correctness or dead-code
analysis, semantic audit, autonomous work selection, and cross-repo mutation.

## Claim types

| Type | Checks | Primary evidence class |
| --- | --- | --- |
| `repo_head` | a branch/ref resolves to an expected SHA | `GIT_REF` (or `GITHUB_STATE` fallback) |
| `pr_state` | PR exists / open / closed / draft / merged / head SHA / base | `GITHUB_STATE` |
| `file_exists` | a repo-relative file exists at a named ref (ref-aware) | `FILE_PRESENCE` |
| `local_path_exists` | a local artifact path exists in this environment | `FILE_PRESENCE` (scope `LOCAL_ENVIRONMENT`) |
| `commit_ancestor` | a commit is an ancestor of a target ref (Git ancestry) | `GIT_ANCESTRY` |
| `worktree_clean` | tracked/untracked working-tree state (kept separate) | `WORKTREE_STATE` |
| `active_lane` | claimed target repo/action is consistent with the lane policy | `INPUT_CONTRACT` |

`file_exists` uses `git cat-file` at the named ref — a local filesystem check is
never treated as proof of repository presence. `local_path_exists` is
explicitly environment-scoped: an absent path is reported as *"not present in
current environment"*, never *"does not exist"* (which would overstate to
"never existed").

## Evidence classes

Every checked claim reports **how the agent knows**:

```
GITHUB_STATE  GIT_REF  GIT_ANCESTRY  FILE_PRESENCE  WORKTREE_STATE
RECORDED_FIXTURE  INFERENCE  INSUFFICIENT_EVIDENCE  INPUT_CONTRACT
```

`INPUT_CONTRACT` was added for the `active_lane` policy check (a check over the
input contract, not external evidence).

Evidence quality is never collapsed into a confidence percentage. Confidence
(`HIGH` / `MEDIUM` / `LOW`) is secondary and never overrides evidence class — in
particular, an absence is never promoted to a `HIGH`-confidence proof of
non-existence.

## Materiality and status logic

Each claim carries `material: true | false`. Aggregation is deterministic:

```
if any material claim == MISMATCH:            status = STALE                decision = STOP
elif any material claim == BLOCKED:           status = BLOCKED              decision = STOP
elif any material claim == INSUFFICIENT:      status = INSUFFICIENT_EVIDENCE decision = STOP
else:                                         status = MATCH                decision = PROCEED
```

A material MISMATCH takes precedence over a BLOCKED evidence source. Non-material
divergences stay visible in the claim list and in `blocked_checks`, but do not
change a `PROCEED` decision.

A `BLOCKED` result means a required evidence source failed (GitHub unavailable,
malformed response, or no token for a GitHub claim). The agent never silently
falls back to a stale cached assumption.

## Active-lane semantics

The lane distinguishes `ACTIVE_REPOSITORY`, `CROSS_REPO_EVIDENCE`, and
`OUT_OF_LANE_MUTATION`. A referenced artifact in another repository may be valid
evidence. But a claim whose action targets a *mutation* in a different
repository while `cross_repo_policy = EVIDENCE_ONLY` is reported as a lane
conflict (`MISMATCH`, `INPUT_CONTRACT`). The agent does not silently switch
repositories.

## CLI and exit codes

```bash
python -m tools.grounding_agent.cli --request path/to/request.json [--output out.json] [--repo-root .] [--pretty]
```

| Exit | Meaning |
| --- | --- |
| 0 | MATCH / PROCEED |
| 2 | STALE |
| 3 | BLOCKED |
| 4 | INSUFFICIENT_EVIDENCE |
| 5 | malformed request / tool error |

With no `--output`, the JSON report is printed to stdout and nothing else is
written. GitHub reads use `GITHUB_TOKEN` (or `GH_TOKEN`).

## Historical fixtures

Five recorded, deterministic fixtures (`tests/grounding_agent/fixtures/`) witness
known stale-state failure classes — not live tests against GitHub's changing
present:

- `pr_312_not_merged` (GA-HIST-01) — PR claimed merged when still draft.
- `cursor_artifact_missing` (GA-HIST-02) — `/opt/cursor/artifacts` patch
  referenced from an environment where it is absent.
- `stale_base_sha` (GA-HIST-03) — expected `main` SHA / ancestry no longer holds.
- `pr_state_superseded` (GA-HIST-04) — handoff says draft/hold; PR already merged.
- `cross_repo_lane_conflict` (GA-HIST-05) — cross-repo mutation under EVIDENCE_ONLY.

## Limitations

- v0.1 evaluates explicit, typed claims only. Natural-language handoff
  extraction is out of scope.
- The seven claim types above are the entire surface. Adding an eighth is a new
  tranche, not a v0.1 change.
- The agent reports; it does not plan, reconcile, or remediate.

## Post-merge rule

Do not immediately build a Reconciliation Agent. Run Grounding against real Dev
Orders and handoffs for a trial period and record handoffs checked, stale
handoffs caught, false positives/negatives, BLOCKED results, manual overrides,
and time saved. No new agent is created because an architecture says one should
exist; it must be justified by a recurring failure this tool demonstrably does
not prevent.
