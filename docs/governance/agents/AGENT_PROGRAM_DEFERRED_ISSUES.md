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

*(populated in the next commit)*

## 7. Closed / superseded findings

*(populated in the next commit)*

## 8. Unresolved evidence needs

*(populated in the next commit)*

## 9. How a future Dev Order consumes an item

1. Re-ground: re-read the item and re-verify every evidence reference still resolves.
2. Confirm the state is `READY_FOR_DECISION` and `census_status` is `IN_CENSUS`.
3. Confirm every `deployment_gate` is satisfied **now**, not when the item was written.
4. Obtain explicit owner authorization. That authorization lives in the new Dev Order,
   never in this file.
5. Implement under that order, then return here and record the transition
   (`SUPERSEDED_BY_CONTROL` or `CLOSED`) with a dated amendment.

An item being present, detailed, or old is not an argument for implementing it.
