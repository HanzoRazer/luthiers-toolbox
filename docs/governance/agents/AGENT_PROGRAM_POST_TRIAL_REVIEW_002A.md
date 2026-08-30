# AGENT-PROGRAM-002A — Post-Trial Failure Census & Agent-002 Authority Decision

This is an evidence-to-design increment. It does not implement Agent 002.

```text
terminal_decision: INSUFFICIENT_EVIDENCE
```

## Decision criteria — why this and not the other two

Three terminal decisions were available. The rule separating them:

| Decision | Requires |
|---|---|
| `AGENT_002_JUSTIFIED` | at least one failure family that **recurs** on independently evidenced incidents **and** is not covered by Grounding or by a deterministic check |
| `NO_AGENT_002` | positive evidence that existing controls **do** cover every recurring family — a demonstrated negative |
| `INSUFFICIENT_EVIDENCE` | neither has been established from durably evidenced incidents |

**`INSUFFICIENT_EVIDENCE` was chosen because neither of the others is
established — not because the answer is "no".**

One family does recur: `stale_repository_reference`, at three independently
evidenced incidents. So the failure is not a shortage of recurrence. It is that
the one recurring family is **already covered** — Grounding detects it when
invoked — so no family is simultaneously recurring *and* uncovered, and the
necessity test cannot pass (§10). The other family, epistemic drift, is singular
rather than recurring.

`AGENT_002_JUSTIFIED` therefore fails on coverage, and separately on the last two
rows of §10: no coherent bounded authority distinct from Agent 001 has been
established, and every candidate examined either overlaps Grounding's question or
becomes an extension of it.

`NO_AGENT_002` fails for a different reason. It would require positive evidence
that existing controls cover every recurring family — a demonstrated negative.
With four incidents and one recurring family, that claim is unproven, and
asserting it would convert *absence of evidence* into *evidence of absence*. It
would also close the question permanently on a four-incident base.

The distinction is load-bearing for what happens next: `NO_AGENT_002` would close
the question, whereas `INSUFFICIENT_EVIDENCE` leaves it open and identifies what
would settle it — a recurring family that existing controls demonstrably do *not*
cover, gathered by continuing to record incidents rather than by reasoning further
about the four already held.

> Note on the bar's direction. `recurrence_eligible()` is deliberately strict and
> `uncovered_recurring_families()` is deliberately conservative, both biasing
> *toward* finding Agent 002 necessary. The conclusion is therefore not an
> artifact of a stacked test: the analysis leaned toward justification and still
> did not reach it.

---

## 1. Scope

**Order:** AGENT-PROGRAM-002A  
**Active repository:** `HanzoRazer/luthiers-toolbox`  
**Active program:** Agent Program  
**Question:** after real operational use of Grounding Agent v0.1, does independently inspectable evidence justify a second agent authority boundary?

In scope:

- Grounding Agent v0.1 authority as implemented
- post-trial incidents that can be verified from Git, GitHub, or committed docs
- classification of existing-control coverage vs a new agent role

Out of scope:

- implementing Agent 002
- renaming hypotheses (Reconciliation / Session / Orchestrator / etc.) into directories or classes
- Vectorizer, RMOS, SGAQ, Smart Guitar, or CAM production changes
- mutating `vectorizer-sandbox` (unavailable in this environment; read-only even if present)
- treating the 2026-08-29 Cloud Agent snapshot as repository-state evidence

Environment baseline only (not repository truth):

```text
snapshot: snapshot-20260830-236e8198-e42d-4baf-aee5-2a64f88fe962
source build: bld-20260829-01f6a93f-b317-404f-aa16-c361df0ea834
```

Branch name `cursor/agent-program-002a-post-trial-review-766d` is an environment constraint. It is not an architectural decision.

---

## 2. Method

1. Fetch `origin/main`. Observe local `HEAD` vs fetched `origin/main` before any mutation.
2. Fast-forward `main` to `origin/main` only if `--ff-only` succeeds.
3. Run Grounding Agent v0.1 against typed claims for this order.
4. Record GA-TRIAL-0006 with whatever Grounding actually returned.
5. Collect candidate incidents. Promote a lead to an incident only when at least one independently inspectable evidence reference exists.
6. Classify each incident with the 002A schema. Keep `UNKNOWN` distinct from `NO`.
7. Count recurrence by `underlying_incident_id`, not by number of citations.
8. Apply existing-control priority (Grounding, Git/GitHub procedure, CI, deterministic utility, then agent authority).
9. Apply the Agent-002 necessity test. Stop at a draft contract only if that test passes.

Owner answers that bound this review:

- durable evidence must be independently inspectable
- handoff F1/F2 numbers are leads, not observations
- the live stale-checkout event counts as an incident discovered during the review
- it must not circularly justify Agent 002 if Grounding would have caught it when invoked
- `vectorizer-sandbox` is treated as absent here
- thin evidence is a valid completion; `NO_AGENT_002` requires positive sufficiency evidence

---

## 3. Grounding entry result

```text
GROUNDING RESULT

status: MATCH
stop decision: PROCEED
```

Run as `python3 -m tools.grounding_agent.cli` on 2026-08-30 after a clean fast-forward. Request: `/tmp/agent_program_002a_grounding_request.json`. Report: `/tmp/agent_program_002a_grounding_report.json` (14 claims, 14 MATCH, 0 blocked).

| Item | Observed |
| --- | --- |
| Repo | `HanzoRazer/luthiers-toolbox` |
| Pre-fetch local `HEAD` | `8d0e1ecf` (Merge #333) |
| Fetched `origin/main` | `a40d9030` (Merge #339) |
| Ahead / behind before ff | 0 / 9 |
| Fast-forward | `--ff-only` succeeded; worktree remained clean |
| Grounding `HEAD` / `origin/main` | both `a40d9030c8c0fa4c774e900860de021e865e7c15` |
| Working branch at Grounding | `main`, then `cursor/agent-program-002a-post-trial-review-766d` after PROCEED |
| Grounding implementation | present (`tools/grounding_agent/`) |
| Grounding tests | present (`tests/grounding_agent/`) |
| Trial ledger | present; five prior rows; latest was GA-TRIAL-0005 `MATCH / PROCEED` |
| PR #339 | MERGED 2026-08-30T01:45:08Z, base `main`, 6 files |
| Agent 002 contract | absent at `HEAD` (claimed and confirmed `exists=false`) |
| Reconciliation artifact at `8d0e1ecf` | absent |
| Reconciliation artifact at `a40d9030` | present |
| `docs/audit-sources/vectorizer-sandbox` | not present in current environment |

`MATCH / PROCEED` authorized mutation of 002A review artifacts only.

---

## 4. Grounding v0.1 current authority

Re-read from `docs/governance/agents/GROUNDING_AGENT_v0.1.md` and `tools/grounding_agent/` (not assumed from the order).

**Authority (actual):**

> Does this handoff describe the repository as it actually exists right now?

v0.1 evaluates seven explicit claim types only: `repo_head`, `pr_state`, `file_exists`, `local_path_exists`, `commit_ancestor`, `worktree_clean`, `active_lane`.

**Constitutional prohibition (actual):**

- read-only adapters; no write path
- reports divergence; does not repair it
- does not suggest remediation
- does not extract natural-language claims
- does not check claim *content* (no semantic / epistemic-reattachment type)
- prefers local git for `repo_head`; GitHub is fallback only when the local ref cannot be resolved

**Implication for 002A:** Grounding can catch a stale `origin/main` when the expected SHA (or a `file_exists` path) is sourced independently of the stale checkout. It cannot catch inherited load-bearing *content* claims, and it cannot fetch. A checkout that authors its own claims from stale refs will MATCH those claims.

The trial ledger's own current disposition, before this row, was `INSUFFICIENT EVIDENCE` for KEEP / REVISE / RETIRE of Grounding itself. That is unchanged by adding GA-TRIAL-0006.

---

## 5. Incident census

Machine-readable ledger: [`agent_program_incidents_002a.json`](agent_program_incidents_002a.json).

### 5.1 Verified incidents

#### INC-002A-F1-001 — PR #339 50-file stale `origin/main`

```text
OBSERVED
```

PR #339's CBSP21 manifest records that a stale `origin/main` ref made the branch diff appear to contain 50 files of other sessions' work; the branch was rebased onto `8d0e1ecf`. GitHub shows the merged PR as 6 files.

The handoff's "36 commits behind" figure was a lead only. It was not recovered from commits, PR comments, or docs. It is not used.

#### INC-002A-F1-002 — 002A live stale checkout (discovered during review)

```text
OBSERVED
```

Before fast-forward: `HEAD=8d0e1ecf`, `origin/main=a40d9030`, 9 behind. The reconciliation file required for F3 was absent on the stale checkout and present after fetch/ff. Grounding later confirmed both presence facts.

This proves the family exists. It does not by itself prove recurrence. It is not pre-existing trial evidence.

Had Grounding been run *before* fetch-sensitive search with a `file_exists` claim for that reconciliation path at `HEAD`, the result on the stale checkout would have been MISMATCH / STALE. This is **existing control not invoked early enough**, not escaped Grounding authority.

#### INC-002A-F1-003 — GA-TRIAL-0001 ledger-already-present

```text
OBSERVED
```

The trial-001 order still said "create the ledger" after PR #326 had merged it. Grounding returned `STALE / STOP`. Existing Grounding authority worked.

#### INC-002A-F3-001 — VECTOR-CROSS-REPO-RECONCILIATION-001 inherited claims

```text
OBSERVED (Toolbox-side record)
INFERRED (sandbox-side measurements: not re-inspected here)
```

Committed reconciliation: five inherited claims re-derived; two refuted (POS-006 prior-prohibition; svgwrite as Step-0 cause). Transferable rule recorded:

> A cross-session handoff preserves claims. It does not preserve their epistemic status.

Sandbox was not mounted. No new sandbox facts are asserted. Grounding v0.1 has no content-claim type, so it could not have checked these claims.

### 5.2 Leads excluded from recurrence

| Lead | Why excluded |
| --- | --- |
| F1 "36 commits behind" | not independently recovered |
| F2 SGAQ/001A cross-session bleed | no committed doc, PR, or retrievable transcript located in this environment |
| F4 false-absence-then-found | no independently documented case that later established presence after a zero-search was treated as absence |
| F5 snapshot-vs-repo as a failure | the order already separated them; no escaped incident found |
| F6 surviving-architecture-as-intent | one analytical rule, applied in the reconciliation / Loop 1 audit; not a second independent failure |

### 5.3 Related observations (not counted as recurrence)

```text
OBSERVED: docs/governance/THREE_LOOP_ARCHITECTURE_REFRAMED.md:68 still says
Loop 3 is "ORPHANED — Infrastructure exists, not wired".

INFERRED: PR #339's CBSP21 verification text says Loop 3 wiring exists behind
enable_feedback=False. The Loop 1 forensic audit itself says Loop 3 was not
evaluated.

UNRESOLVED: whether that remaining doc sentence is a live mismatch or an
accurate description of a different wiring threshold. Not entered as a
verified incident.
```

---

## 6. Failure-family clustering

| Family | Eligible unique incidents | Recurrence? |
| --- | --- | --- |
| `stale_repository_reference` | 3 (F1-001, F1-002, F1-003) | YES |
| `inherited_claim_epistemic_drift` | 1 (F3-001) | NO |
| cross-session bleed | 0 verified | NO |
| false absence | 0 verified | NO |
| custody/authority confusion | 0 verified escaped | NO |
| historical intent from architecture | 0 counted failures | NO |

The stale-reference family is real and recurrent. The epistemic-drift family is real and so far singular.

---

## 7. Existing-control coverage

| Incident | Grounding | Git procedure | CI | Deterministic check | Escaped? |
| --- | --- | --- | --- | --- | --- |
| F1-001 | PARTIAL | YES (`git fetch` before `diff origin/main`) | NO | YES | NO |
| F1-002 | YES if invoked on the missing-file claim | YES | NO | YES | NO |
| F1-003 | YES (did detect) | YES | NO | YES | NO |
| F3-001 | NO (no content-claim type) | NO | NO | UNKNOWN | YES |

Grounding's local-first `repo_head` resolution matters: a stale `origin/main` that still resolves locally is trusted. Detection requires an expected SHA or path sourced from outside that stale view.

---

## 8. Escaped recurring failures

None.

The only escaped incident (F3-001) has no independently evidenced companion. The only recurrent family (stale refs) did not escape: procedure and/or Grounding cover it when invoked.

---

## 9. Deterministic-control alternatives

**Stale repository/reference**

- `git fetch origin <branch>` before any `origin/main` diff or "file missing" conclusion
- `git rev-list --left-right --count HEAD...origin/main`
- Grounding `repo_head` / `file_exists` claims whose expected values are not authored from the stale checkout
- a later optional check that compares local `origin/main` to GitHub `main` even when the local ref resolves (that would be a Grounding extension or a tiny utility, not Agent 002)

**Inherited claim epistemic drift**

- the reconciliation already wrote the re-derivation rule
- a future Grounding claim type for "content / evidence reattached" would still be Agent 001
- a checklist in Dev Orders ("inherited load-bearing claims must be re-derived") is a procedure, not an agent
- whether those alternatives are *operationally sufficient* is not demonstrated by a second incident

---

## 10. Agent-role necessity test

Required for `AGENT_002_JUSTIFIED`:

| Criterion | Result |
| --- | --- |
| Recurring failure | Stale-ref family only |
| Independent incidents | Yes for stale-ref; no for epistemic drift |
| Material consequence | Medium (stale-ref) / high (F3, singular) |
| Existing Grounding insufficient | No for stale-ref when invoked; yes for F3 content |
| Deterministic check insufficient | No for stale-ref; UNKNOWN for F3 |
| Coherent bounded authority that is not Agent 001 | Not established |
| Does not duplicate Grounding | A "session" or "reconciliation" agent would overlap Grounding's question or become a Grounding extension |

`tools/agent_program/analyze_incidents.py` reports `necessity_test_can_pass: false` on this ledger. That is an input, not an automatic decision.

---

## 11. Candidate authority boundaries

Hypotheses considered and **not adopted**:

| Hypothesis | Why not frozen |
| --- | --- |
| Session Agent | F2 unverified; stale-ref is fetch discipline |
| Reconciliation Agent | F3 is one incident; the written rule / a Grounding extension is the closer next design, if any |
| Evidence Agent | would re-open Grounding's job |
| Orchestrator / Supervisor | forbidden by D9; no evidence for dispatch authority |

No `AGENT_002_AUTHORITY_CONTRACT_DRAFT.md` is created.

---

## 12. Recommendation

```text
INSUFFICIENT_EVIDENCE
```

Not `AGENT_002_JUSTIFIED`: there is no recurring uncovered failure that requires a distinct agent authority.

Not `NO_AGENT_002`: one escaped, high-consequence epistemic-drift incident exists, and this review does not have enough later operational uses to show that Grounding + fetch procedure + the written re-derivation rule are sufficient as a standing control. Absence of a second Agent-002 case is not evidence that no second agent will ever be needed.

Grounding Agent v0.1 remains the only implemented agent.

---

## 13. Falsifiers

This review is wrong if any of the following is later shown:

1. A retrievable transcript or committed record independently evidences the SGAQ/001A bleed *and* shows it is not active-lane / handoff / human-workflow error already covered by Grounding.
2. A second independent epistemic-drift incident, not the same #339 audit cluster, shows inherited claims becoming accepted premises after Grounding `PROCEED`.
3. Evidence that `git fetch` + invoked Grounding do **not** catch the stale-ref family in ordinary use (for example, because expected SHAs are always copied from the stale checkout).
4. Discovery that Agent 002 was already decided or implemented on another branch/PR.

---

## 14. Stop decision

```text
STOP
```

002A is complete at the draft PR. No Agent 002 implementation. No orchestrator. No production capability change. Vectorizer Sandbox remained unread as a live tree. Next work, if any, requires a separate order — and should not assume that resuming the agent program means adding another agent.
