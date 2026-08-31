# Grounding Agent v0.2 — Active-Lane & Handoff Provenance Guard

> Grounding verifies whether a handoff belongs to the declared active lane. It
> does not select a lane, switch projects, or decide what work should replace a
> rejected handoff.

v0.2 (GROUNDING-AGENT-002) is **additive over v0.1** (see
[`GROUNDING_AGENT_v0.1.md`](GROUNDING_AGENT_v0.1.md)). It does **not** create a
second agent, an orchestrator, or a session manager, and it changes no
production behavior. Every v0.1 request that does not use the new optional
fields behaves identically.

## What v0.1 already did (unchanged)

v0.1 already carried a mandatory top-level `active_lane`
(`{project, active_repository, active_program, active_order, active_state,
cross_repo_policy}`), an `active_lane` claim type, `CrossRepoPolicy.EVIDENCE_ONLY`,
the `INPUT_CONTRACT` evidence class, and cross-repo **evidence-vs-mutation**
detection (same-repo → MATCH; cross-repo evidence → MATCH; cross-repo mutation
under `EVIDENCE_ONLY` → MISMATCH / STALE). v0.2 does not rebuild any of that.

## What v0.2 adds

1. **`handoff_provenance` claim type** — answers: *does this handoff's declared
   program / work-order / repository match the active lane?* This is separate
   from the `active_lane` claim (which remains the repository/cross-repo
   authority boundary).
2. **Top-level `evidence_lanes`** — an optional list of foreign repositories
   explicitly declared as read-only evidence:
   ```json
   "evidence_lanes": [{ "repository": "HanzoRazer/vectorizer-sandbox", "mode": "EVIDENCE_ONLY" }]
   ```
   Omitted from serialization when empty, so v0.1 requests round-trip identically.
3. **`HANDOFF_LANE_CONFLICT`** — a first-class, controlled `reason` on a claim
   result (distinct from the observed evidence payload). Present only when set;
   v0.1 results serialize exactly as before.
4. **`INSUFFICIENT_EVIDENCE` for missing provenance** — absence of proof is not
   proof of bleed (D6).

## `handoff_provenance` semantics

The claim's `expected` declares the handoff's own lane identity:

```json
{
  "claim_id": "C-PROV",
  "type": "handoff_provenance",
  "expected": {
    "repository": "HanzoRazer/luthiers-toolbox",
    "program": "Agent Program",
    "work_order": "GROUNDING-AGENT-002",
    "required": ["repository", "program", "work_order"]
  },
  "material": true
}
```

- `required` lists the **material** provenance dimensions. If omitted, the
  dimensions actually declared are treated as required.
- For each required dimension:
  - **declared and disagreeing** with the active lane → MISMATCH,
    `reason = HANDOFF_LANE_CONFLICT`. For `repository`, a foreign value is only a
    conflict if it is **not** declared as an `EVIDENCE_ONLY` evidence lane.
  - **not established** by the handoff → `INSUFFICIENT_EVIDENCE` (never a guessed
    mismatch, D6).
  - matching → contributes to MATCH.
- A definite conflict dominates a merely-missing dimension.

Comparison is **deterministic and structural** — repository identifiers are
normalized conservatively; program/work-order labels are compared
case-insensitively. There is **no NLP, no keyword classification, and no fuzzy
topic matching** (D9), enforced by a test.

Evidence class is always `INPUT_CONTRACT` (it is a check over the input
contract, not repository/GitHub/filesystem state). Provenance never grants
mutation authority: an `EVIDENCE_ONLY` evidence lane permits read-only evidence
only, and the `active_lane` mutation boundary is unaffected by `evidence_lanes`.

## Aggregation (unchanged, cumulative)

Provenance is one more dimension in the existing deterministic aggregation. A
lane match cannot override a stale repository fact, and a lane conflict is not
excused by an otherwise-clean repository:

```
material MISMATCH (any dimension, incl. lane) -> STALE / STOP
material BLOCKED                               -> BLOCKED / STOP
material INSUFFICIENT_EVIDENCE                 -> INSUFFICIENT_EVIDENCE / STOP
otherwise                                      -> MATCH / PROCEED
```

## CLI (additive; exit codes unchanged)

No new flags or positional forms. The new fields flow through the existing
request JSON:

```bash
# v0.1 request (unchanged behavior):
python -m tools.grounding_agent.cli --request docs/governance/agents/grounding_request.example.json --repo-root .

# v0.2 provenance example (handoff_provenance + evidence_lanes):
python -m tools.grounding_agent.cli --request docs/governance/agents/grounding_request.v0.2.example.json --repo-root .
```

Exit codes are unchanged: `0` MATCH/PROCEED, `2` STALE, `3` BLOCKED,
`4` INSUFFICIENT_EVIDENCE, `5` malformed request / tool error.

## Fixtures

Synthetic lane fixtures live in `tests/grounding_agent/fixtures/GA-LANE-*.json`
(all labeled `"kind": "synthetic"`): same-repo, cross-repo evidence-only, wrong
program, wrong work-order, missing provenance, and a session-bleed-style case.

## Boundary

Grounding v0.2 reports whether a handoff belongs to its declared lane. It does
not choose a lane, switch repositories, remediate, generate replacement work, or
manage sessions. A lane conflict is a STOP with a factual reason — never a
recommendation.
