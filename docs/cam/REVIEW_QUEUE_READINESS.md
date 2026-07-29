# Review Queue Readiness

How this repository answers: **are the declared operational prerequisites of the review-queue
subsystem present?**

```text
Readiness describes the presence of declared operational prerequisites.
It does not authorize implementation, execution, promotion, or machine output.
```

---

## Three readiness mechanisms — do not conflate them

This repository contains three things that assess "readiness". They have different subjects
and are separate on purpose.

| Mechanism | Subject | Question it answers |
|---|---|---|
| `app/cam/review_queue_ci.py` | queue **contents** | Is the queue healthy *right now* — counts, blocking issues, missing assignments? |
| `app/cam/review_queue_readiness*.py` | subsystem **architecture** | *Could* this queue be relied on operationally — persistence, identity, timestamps, notification? |
| `app/cam/translator_governance_review_matrix.py` (CAM 7J) | governance **evidence** | Is translator evidence complete enough for human review? |

**None of the three authorizes implementation, execution, or machine output.** Each enforces
that with model validators; the readiness report follows the 8E invariant pattern already
established by `ReviewQueueCISummary`.

The distinction that matters most: **`review_queue_ci` looks at what is *in* the queue;
readiness looks at what the queue *is*.** A queue can be perfectly healthy by CI measures
and still be architecturally unfit to depend on.

---

## What readiness means — and does not

**Means:** a declared operational prerequisite was found in the repository, read from a
citable source.

**Does not mean:**

- that the prerequisite works at runtime — see *static vs runtime* below;
- that the capability is approved, scheduled, or authorized;
- that anyone may implement, execute, or produce machine output.

---

## Requirement authority

The requirement set is **ratified by owner ruling, derived from the historical 8F
assessment**. Every requirement records its `authority_source`; a requirement without a named
authority is a bug.

| ID | Requirement | Severity | Verification |
|---|---|---|---|
| `RQR-001-PERSISTENCE` | Review queue survives process restart | BLOCKING | STATIC |
| `RQR-002-IDENTITY` | Review actors are authenticated or attributable | BLOCKING | HYBRID |
| `RQR-003-TIMESTAMPS` | Review records carry creation timestamps | BLOCKING | STATIC |
| `RQR-004-NOTIFICATION` | Queue changes are communicated externally | WARNING | STATIC |

Requirements live in `review_queue_readiness_requirements.py` as a frozen module constant.
They are policy, not configuration: **nothing a caller supplies can add, remove, or weaken a
requirement.**

### Why RQR-003 is retained even though it passes

8F recorded a missing-timestamp gap in 2026-05. That gap has since closed — `created_at` is
declared on both `ReviewQueueItem` and `ReviewDecisionRecord`. The requirement stays so the
property remains *checked* rather than assumed. A requirement set describing a closed gap
would report confidently wrong results, which is how the historical assessment became stale.

---

## Static versus runtime verification

| Mode | Meaning |
|---|---|
| `STATIC` | Settled by inspecting declarations. |
| `RUNTIME` | Cannot be settled by inspection at all. |
| `HYBRID` | A declaration is visible statically, but enforcement is a runtime property. |

A `RUNTIME` or `HYBRID` requirement that cannot be settled yields
`UNRESOLVED_RUNTIME_VALIDATION_REQUIRED` — **not** `UNSATISFIED`.

This distinction is deliberate and load-bearing: **a missing feature and an unverifiable
feature are different findings.** Reporting the unverifiable as missing is a false
accusation; reporting it as satisfied is a false clearance. `RQR-002-IDENTITY` is the live
example — `reviewer_ref` is declared, but static inspection cannot show that authentication
is *enforced* on the request path.

---

## Report statuses

**Finding statuses:** `SATISFIED` · `UNSATISFIED` · `UNRESOLVED_RUNTIME_VALIDATION_REQUIRED`
· `NOT_APPLICABLE` · `DEFERRED_BY_POLICY`

**Aggregate:**

| Aggregate | When |
|---|---|
| `READY` | every applicable BLOCKING requirement is SATISFIED, none unresolved |
| `READY_WITH_WARNINGS` | no blocking failure remains; warnings present |
| `NOT_READY` | at least one BLOCKING requirement is UNSATISFIED **or** UNRESOLVED |

The aggregate is **computed from findings**. There is no caller-settable `ready` field —
that absence is the point. The historical TD-2 design accepted readiness booleans from the
caller, so it recorded whatever the caller claimed.

---

## Running it

```bash
python scripts/ci/check_review_queue_readiness.py --format text
python scripts/ci/check_review_queue_readiness.py --format json --output report.json
python scripts/ci/check_review_queue_readiness.py --report-only    # CI rollout mode
```

Exit codes, enforcement mode:

```text
READY / READY_WITH_WARNINGS -> 0
NOT_READY                   -> 1
EVALUATOR_ERROR             -> 2
```

Under `--report-only`, `NOT_READY` also returns 0; an evaluator error still returns 2.
Report-only suppresses **enforcement of known gaps**, never the truth of the report.

> Exit code 2 is shared with argparse usage errors. Intentional: both mean *no readiness
> verdict was produced*, which is the distinction callers need.

JSON output is deterministic — stable ordering, an explicit `schema_version`, no timestamps,
no host paths, no generated ids. The same tree always renders byte-identically, so reports
can be diffed across runs.

---

## CI behaviour

The check runs as a step inside **`Fence Checks (Blocking)`** in
`.github/workflows/architecture_scan.yml`.

**It is deliberately not a separate workflow.** `Fence Checks (Blocking)` is the sole
required status check on this repository and runs on every PR with **no path filter**
(CI-RED-004). A separate readiness workflow with path filters would be absent on docs-only
PRs, leaving a required check permanently at *"Expected — waiting"* and making those PRs
unmergeable. `test_review_queue_readiness_ci_topology.py` asserts this property so it cannot
regress silently.

### Report-only during rollout

Three of the four ratified requirements are unmet today. Enforcing them would fail the sole
required check and **block every merge in the repository** — including the PR that adds the
check. So the CI step runs `--report-only`: findings are printed truthfully, the aggregate
still reads `NOT_READY`, and merges are not gated on a state already known to be red.

Severities were **not** weakened to obtain a green check. The requirements remain BLOCKING;
only rollout enforcement is deferred.

**Promotion to enforcement requires a separate owner ruling**, after current findings are
reviewed, false positives addressed, unresolved findings understood, and a viable path to
satisfying the blocking requirements exists.

---

## The historical shape, and why it was retired

TD-2 (recovery branch `p0-repository-state-triage` @ `8035f499`) proposed a runtime
`POST /readiness` endpoint backed by an in-memory assessment registry. It is **evidence of
the problem, not a source to copy**. Four defects:

1. **Caller-asserted readiness** — the endpoint accepted readiness booleans and recorded
   what it was told, never inspecting the system.
2. **Stale requirement vocabulary** — it still described the timestamp gap as open.
3. **Self-referential storage** — the registry built to report the persistence gap was
   itself in-memory, so its assessments were lost on restart.
4. **Wrong delivery shape** — a runtime API reporting static architectural facts that cannot
   vary per request.

What was kept: the **gate concept**, the **anti-authorization invariants**, and the
**requirement vocabulary** after current-state review. What was discarded: the endpoint, the
registry, and caller-supplied readiness.

Full decision record: `handoffs/td2/` in the Consolidation Lab.
