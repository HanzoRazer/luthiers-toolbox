# AGENT-PROGRAM-003 — Deferred Issue Evidence & Readiness Queue

This is a **readiness and disposition layer**. It is not an incident registry, not a
backlog of feature ideas, and not an authorization to build anything.

```text
implementation authority: NONE
production behavior:      unchanged
agent count:              unchanged (Grounding Agent v0.1 remains the only agent)
```

## 1. Purpose

To preserve unresolved Agent Program findings until evidence and authority justify
deploying them — **without converting discovery into authorization**.

For each queued issue this artifact answers:

> What is the issue, what evidence supports it, what control would address it, what
> remains unknown, and what conditions must become true before implementation is
> authorized?

## 2. Authority boundary

### 2.1 One census authority

`agent_program_incidents_002a.json` is the **canonical incident evidence**. This queue
does **not** restate incidents and does **not** maintain a second evidence register.
A queue item references census incidents by id in `source_incidents` and adds only
what 003 contributes: lifecycle state, current control, control gap, likely solution
class, deployment gates, blockers, relationships, and open questions.

```text
002A incident ledger      = canonical incident evidence
        ↓ referenced by
003 deferred queue        = readiness / disposition / deployment gates
        ↓ future owner decision
separate Dev Order        = implementation authorization
```

### 2.2 Findings not yet in the census

The 002A census is a **completed review artifact**. It carries `review_order`,
`reviewed_at`, and a `terminal_decision`, and it declares no extensibility contract.
Adding incidents to it now would rewrite the evidence base of a closed review, which
D10 forbids.

So a finding recovered *after* 002A cannot become a census incident here. It is
recorded with `census_status: PENDING_CENSUS_AMENDMENT` and an external evidence
reference, and **it cannot pass the readiness gate**. Only a future owner-authorized
incident-ledger amendment can promote it.

> **Flagged interpretation — owner may override.** The order's instruction was to
> record such findings as `LEAD_ONLY`. Two of them (AP-DI-003, AP-DI-010) rest on
> durable, independently inspectable, in-repo evidence, so labelling their evidence
> `LEAD_ONLY` would assert something untrue about its recoverability. This queue
> instead enforces the *intent* of that instruction — such items cannot reach
> `READY_FOR_DECISION` — through the explicit `census_status` field, while recording
> the evidence class accurately. If the owner prefers the literal `LEAD_ONLY`
> labelling, that is a one-field change plus a validator rule.

### 2.3 What this queue may never do

- set `implementation_authorized: true` (locked `false` for every item, enforced)
- carry a remediation payload (`patch`, `code_change`, `auto_execute`, `assigned_agent`, `merge_when`, `deploy_now`)
- select, dispatch, assign, or execute work — there is no orchestration
- authorize mutation in another repository, whatever evidence it cites
- delete history: superseded and closed findings stay in the artifact

### 2.4 Private session memory is not evidence

Cross-session assistant memory is a **discovery path**, never a queue evidence class.

```text
private memory note
      ↓ DISCOVERY PATH ONLY
find durable evidence
      ├── found     → normal evidence class
      └── not found → LEAD_ONLY
```

`OWNER_ATTESTATION` is admissible only when an owner explicitly provides an
attestation intended to become part of the record. Private memory is never
auto-promoted to owner attestation.

## 3. State vocabulary

| State | Meaning |
| --- | --- |
| `DISCOVERED` | Named as a candidate. No durable evidence required yet. |
| `EVIDENCED` | At least one durable evidence reference exists. |
| `INVESTIGATED` | Evidence recovered, current controls identified, control gap stated. |
| `READY_FOR_DECISION` | Sufficiently investigated for **owner review** — *not* authorized to implement. |
| `BLOCKED` | Progress depends on something not yet true (an unmerged PR, an absent control). |
| `SUPERSEDED_BY_CONTROL` | A deployed control demonstrably covers it. Requires the control to be **live on `main`**. |
| `CLOSED` | Retired for a recorded reason. Retained, never deleted. |

Allowed progression for **this** increment:

```text
DISCOVERED → EVIDENCED → INVESTIGATED → READY_FOR_DECISION
```

`OWNER_AUTHORIZED` is not a state this artifact can set.

## 4. Evidence-class vocabulary

```text
RUNTIME_WITNESS          a recorded execution of a tool in this repository
GIT_STATE                commits, refs, ancestry, tracked/ignored status
GITHUB_STATE             PR / issue state read from GitHub
COMMITTED_DOC            a committed document, cited file:line
COMMITTED_TEST           a committed test or fixture
CLOUD_AGENT_TRANSCRIPT   a durable transcript explicitly recovered and cited
OWNER_ATTESTATION        an owner statement offered for the record
INPUT_CONTRACT           a declared schema / request contract
STATIC_CODE_INSPECTION   source read at a cited path
LEAD_ONLY                reported but not independently recoverable
```

Classes are never silently promoted. `LEAD_ONLY` alone never satisfies an evidence
requirement.

## 5. Deployment-readiness rules

A complete description does **not** make an item ready. `READY_FOR_DECISION` requires
all of:

1. at least one durable evidence reference that is not `LEAD_ONLY`;
2. `census_status: IN_CENSUS` — the evidence is ratified in the 002A census;
3. current controls recorded (possibly the empty list, stated deliberately);
4. a stated `control_gap`, or an explicit statement that no gap remains;
5. a bounded `solution_class`;
6. every `deployment_gate` that asserts recurrence backed by **≥2 independent** census incidents;
7. `implementation_authorized: false`.

Counting rule: two references to one underlying event are **one** incident.

`agent_required` is `YES` only with documented deterministic-control analysis showing
a lower-authority mechanism is insufficient. Solution classes are tested cheapest-first:

```text
EXISTING_CONTROL → DETERMINISTIC_RULE → DETERMINISTIC_UTILITY
                 → GROUNDING_EXTENSION → POSSIBLE_AGENT
```

## 6. Current queue

Machine-readable: [`agent_program_deferred_issues.json`](agent_program_deferred_issues.json).

Ten items. Two carry findings recovered after 002A and therefore cannot reach readiness
(§2.2). One is ready for owner review. None is authorized.

| ID | Title | State | Census | Solution class | Agent? |
| --- | --- | --- | --- | --- | --- |
| AP-DI-001 | Stale repository / reference state | `READY_FOR_DECISION` | IN_CENSUS | `DETERMINISTIC_RULE` | NO |
| AP-DI-002 | Inherited claim epistemic drift | `INVESTIGATED` | IN_CENSUS | `UNRESOLVED` | UNPROVEN |
| AP-DI-003 | False-absence findings | `EVIDENCED` | PENDING | `DETERMINISTIC_RULE` | UNPROVEN |
| AP-DI-004 | Cross-repo custody and lane confusion | `DISCOVERED` | IN_CENSUS | `EXISTING_CONTROL` | NO |
| AP-DI-005 | Session / active-lane bleed | `DISCOVERED` | IN_CENSUS | `UNRESOLVED` | UNPROVEN |
| AP-DI-006 | Surviving architecture misread as intent | `DISCOVERED` | IN_CENSUS | `PROCESS_ONLY` | NO |
| AP-DI-007 | Handoff evidence loss | `DISCOVERED` | IN_CENSUS | `UNRESOLVED` | UNPROVEN |
| AP-DI-008 | Cross-repo reconciliation need | `DISCOVERED` | IN_CENSUS | `PROCESS_ONLY` | NO |
| AP-DI-009 | `/tools/` ignore boundary | `BLOCKED` | IN_CENSUS | `DETERMINISTIC_RULE` | NO |
| AP-DI-010 | Grounding GitHub evidence blocked on gh-only auth | `EVIDENCED` | PENDING | `PROCESS_ONLY` | NO |

### The three that carry weight

**AP-DI-001 — the only item ready for a decision.** Three independent census incidents;
the family recurs. It is *not* uncovered — `git fetch` plus an invoked Grounding catches
it — but one gap is precisely stated: Grounding resolves `repo_head` local-first, so a
stale local `origin/main` that still resolves is trusted, and a claim whose expected SHA
was copied out of the stale checkout will MATCH. What is ready is the decision on a small
freshness check, not a decision to build an agent.

> This order supplied its own instance. The pre-grounding pass ran from a checkout 272
> commits behind `origin/main` and concluded `docs/governance/agents/` did not exist. It
> exists. The stale view produced a false absence — which is why AP-DI-001 and AP-DI-003
> are linked.

**AP-DI-003 — 002A's F4 exclusion is now falsified.** 002A excluded false-absence for want
of a documented case. This pass recovered two, both durable and independently inspectable:
BR-024, where grep-absence of the literal `ezdxf.new("R2000")` call form was read as R2000
removal though R2000 remains supported across ~29 `app/` files; and the refuted inherited
claim that Step 0 was RED because `svgwrite` was absent, when it is declared and installed.
A control exists — *no state is assigned from grep-absence alone* — but it is stated in one
audit's method section, is unenforced, and postdates both instances.

**AP-DI-010 — found by running the tool rather than reading it.** This order produced the
program's first `BLOCKED / STOP`. Both `pr_state` claims blocked on
`no GITHUB_TOKEN/GH_TOKEN available`; a re-run with the token exported returned
`MATCH / PROCEED` 15/15, isolating credentials as the sole cause. The adapter behaved
correctly — it failed closed rather than proceeding without GitHub evidence. The gap is
operability: an operator authenticated only through the `gh` keyring meets a STOP that
looks like a divergence. A `gh` fallback is not the fix; the adapter's read-only guarantee
rests on having no subprocess path.

### Items retained without a recovered incident

AP-DI-004 through AP-DI-008 each had one deliberate recovery pass that returned
`NOT_FOUND`. They are retained because the order names them, and because a recorded
`ATTEMPTED / NOT_FOUND` is itself useful — it dates the search so the next reviewer
extends it rather than repeating it. For AP-DI-004 and AP-DI-006 the pass recovered
*controls and analytical rules*, not escaped incidents; that is why their solution classes
are `EXISTING_CONTROL` and `PROCESS_ONLY` rather than `UNRESOLVED`.

AP-DI-007 is the weakest retained item and is flagged in its own `open_questions` as a
probable duplicate facet of AP-DI-002. It is kept separate only because the order lists it
as a distinct candidate family; merging it is an owner decision.

## 7. Closed / superseded findings

None. No item in this queue has been closed or superseded.

`AP-DI-009` is the nearest candidate and is deliberately **not** marked
`SUPERSEDED_BY_CONTROL`. TOOLS-GITIGNORE-001 exists as PR #341, observed open, draft, and
unmerged — confirmed independently by this order's Grounding claim C-003. `/tools/` is
still ignored at `.gitignore:150` on `main`, so the control is proposed, not deployed.
Marking it superseded would assert a repair that is not in effect.

```text
TOOLS-GITIGNORE-001
PR #341     = OPEN / DRAFT
main control = NOT DEPLOYED

therefore: BLOCKED, not SUPERSEDED
```

It may transition only after #341 merges **and** a later re-ground confirms the rule is
live on `main`.

## 8. Unresolved evidence needs

| Need | Serves | Why it is open |
| --- | --- | --- |
| Owner-authorized incident-census amendment | AP-DI-003, AP-DI-010 | Both rest on durable evidence recovered after 002A closed. Neither can reach readiness until ratified into the census (§2.2). |
| A second epistemic-drift incident outside the PR #339 cluster | AP-DI-002 | 002A falsifier 2. One incident cannot establish recurrence. |
| Any durable record of the SGAQ/001A bleed | AP-DI-005 | 002A falsifier 1. Two independent passes have now failed to recover one. |
| A custody error not expressed as a declared claim | AP-DI-004 | `active_lane` covers declared mutation targets; whether anything escapes it is untested. |
| Independence of BR-024 and the `svgwrite` refutation | AP-DI-003 | Different subsystems and dates, but the `svgwrite` refutation shares a discovery event with INC-002A-F3-001. Recurrence must not be counted before this is settled. |
| Whether AP-DI-007 is separable from AP-DI-002 | AP-DI-007 | No incident yet distinguishes the two mechanisms. |

## 9. How a future Dev Order consumes an item

1. Re-ground: re-read the item and re-verify every evidence reference still resolves.
2. Confirm the state is `READY_FOR_DECISION` and `census_status` is `IN_CENSUS`.
3. Confirm every `deployment_gate` is satisfied **now**, not when the item was written.
4. Obtain explicit owner authorization. That authorization lives in the new Dev Order,
   never in this file.
5. Implement under that order, then return here and record the transition
   (`SUPERSEDED_BY_CONTROL` or `CLOSED`) with a dated amendment.

An item being present, detailed, or old is not an argument for implementing it.
