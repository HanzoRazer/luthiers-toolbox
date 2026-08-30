# Grounding Agent v0.1 — Trial Ledger

This is the measurement instrument for deciding whether Grounding Agent v0.1
deserves to exist. It is **not** a governance program — it is one table plus a
short summary. Record one row per **real** use (an actual Dev Order or handoff),
never synthetic exercises.

Spec: [`GROUNDING_AGENT_v0.1.md`](GROUNDING_AGENT_v0.1.md)

## How to record a row
- **ID** — stable identifier for the run, e.g. `GA-TRIAL-0001`.
- **Result** — the agent's top-level status/decision, e.g. `MATCH/PROCEED`, `STALE/STOP`, `BLOCKED/STOP`, `INSUFFICIENT_EVIDENCE/STOP`.
- **Stale caught?** — did it catch stale state we would otherwise have acted on? (`yes`/`no`)
- **False positive?** — did it STOP on something that was actually fine? (`yes`/`no`)
- **False negative?** — did it return `PROCEED`/`MATCH` when a material claim was **already** wrong or unsupported *at the time Grounding ran*? (`yes`/`no`)
  - A false negative **requires independent evidence** that the claim was already false when Grounding ran. Later repository drift alone does **not** count — if the state only changed *after* the run, that is not a false negative.
- **Blocked evidence?** — did a required evidence source fail (no token, GitHub down, etc.)? (`yes`/`no`)
- **Human override?** — did a human override Grounding's decision and act anyway? (`yes`/`no`)
  - Record the override **separately** and **preserve the original Grounding result** — do not rewrite the recorded verdict after the fact. Capture, in Notes or an incident note: (1) Grounding's decision, (2) that a human overrode it, (3) why, and (4) whether later evidence showed the override or the Grounding decision to have been correct.
- **Estimated time effect** — approximate, and may be positive, neutral, or negative: e.g. `+10 min saved`, `neutral`, `-5 min overhead`. Do not assume the agent was beneficial.
- **Notes** — one line of context; link the handoff/PR if useful.

## Ledger

| ID | Date | Handoff / Order | Result | Stale caught? | False positive? | False negative? | Blocked evidence? | Human override? | Estimated time effect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GA-TRIAL-0001 | 2026-08-27 | GROUNDING-AGENT-TRIAL-001 | STALE / STOP | yes | no | no | no | no | small positive (~a few min saved) | PR #326 had already created the ledger on `main`; Grounding caught the stale "create ledger" premise before mutation. |
| GA-TRIAL-0002 | 2026-08-27 | RMOS-AUTHORITY-MAP-001 | MATCH / PROCEED | no | no | no | no | no | small positive / neutral | Verified eight material prerequisites (v0.1 + ledger; #322 and #324 MERGED; rmos_prod_audit_001.md; core/safety.py; rmos/feasibility/engine.py) before the Stage-1 census began. Risk reduction, not a large time saving. |
| GA-TRIAL-0003 | 2026-08-27 | RMOS-PROFILING-CONVERGE-001 | MATCH / PROCEED | no | no | no | no | no | small positive / neutral | Verified #328 MERGED, frozen registry, profiling LIVE_UNGOVERNED_OUTPUT / RUNTIME_REACHABLE, #324 binding, mounted /gcode, canonical compute_profile_feasibility, and the trial ledger before mutation. C-009 (wrong SHA, material:false) was INSUFFICIENT and did not stop. |
| GA-TRIAL-0004 | 2026-08-27 | RMOS-VCARVE-CONVERGE-001 | MATCH / PROCEED | no | no | no | no | no | small positive / neutral | Verified #328 and #329 MERGED, origin/main `c987bfce`, frozen V-carve POST_MERGE_AUTHORITY_EXPOSURE files present, Profiling GOVERNED (independent JSON read), trial ledger present. Grounding v0.1 has no content-claim type for dispositions. No Grounding Agent code was changed. |
| GA-TRIAL-0005 | 2026-08-28 | RMOS-DRILLING-CONTRACT-001 | MATCH / PROCEED | no | no | no | no | no | small positive / neutral | Verified #330 MERGED, origin/main `795bc189`, V-carve HOLD / POST_MERGE_AUTHORITY_EXPOSURE, Profiling GOVERNED, drilling AUTHORITY_CONTRACT_MISMATCH / RUNTIME_REACHABLE / ungated YES (independent JSON read). No Grounding Agent code was changed. |
| GA-TRIAL-0006 | 2026-08-30 | AGENT-PROGRAM-002A | MATCH / PROCEED | no | no | no | no | no | small positive / neutral | After fetch+ff, origin/main and HEAD were `a40d9030` (#339 MERGED). 14/14 claims MATCH. No Agent 002 artifact present. Reconciliation file absent at prior `8d0e1ecf`, present at `a40d9030`. vectorizer-sandbox not present in this environment. No Grounding Agent code was changed. |

## Incident notes

Use only where a table row cannot adequately explain an important event.

- **GA-TRIAL-0001** — First real operational use, not a synthetic fixture. GROUNDING-AGENT-TRIAL-001 instructed "create the trial ledger", but PR #326 had merged that ledger to `main` ~2 minutes earlier. Grounding checked the handoff's premises against `origin/main` (v0.1 files present → MATCH; ledger expected absent → observed present → MISMATCH) and returned `STALE / STOP`, preventing a redundant/blind ledger creation. The stale premise was corrected into this narrow ledger-contract-completion increment.
- **GA-TRIAL-0002** — Second real operational use. RMOS-AUTHORITY-MAP-001 Stage 1 (a one-off census, not a new agent) required Grounding before mutation. All eight material claims MATCH, including live GitHub state that #322 and #324 are merged. Decision PROCEED. The Dev Order was then rewritten to forbid building a second agent; the census proceeded as ordinary script + inert registry + report.
- **GA-TRIAL-0003** — Third real operational use. RMOS-PROFILING-CONVERGE-001 required Grounding before mutating the live Profiling G-code path. All material claims MATCH; decision PROCEED. Grounding v0.1 has no content-claim type, so the frozen Profiling classification (`LIVE_UNGOVERNED_OUTPUT` / `RUNTIME_REACHABLE`) was re-read from the committed registry independently. No Grounding Agent code was changed.
- **GA-TRIAL-0004** — Fourth real operational use. RMOS-VCARVE-CONVERGE-001 required Grounding before acting on the live V-carve production G-code path. All 15 claims MATCH (including GitHub `pr_state` that #328 and #329 are merged); decision PROCEED. Frozen V-carve `POST_MERGE_AUTHORITY_EXPOSURE` and Profiling `GOVERNED` were re-read from the committed registry independently. Subsequent evaluator search found no substantive V-carve feasibility engine, so the order completed as HOLD rather than GOVERNED. No Grounding Agent code was changed.
- **GA-TRIAL-0005** — Fifth real operational use. RMOS-DRILLING-CONTRACT-001 required Grounding before mutating the drilling contract boundary. All material claims MATCH (including GitHub `pr_state` that #330 is merged); decision PROCEED. Frozen drilling `AUTHORITY_CONTRACT_MISMATCH`, Profiling `GOVERNED`, and V-carve `POST_MERGE_AUTHORITY_EXPOSURE` were re-read from the committed registry independently. No Grounding Agent code was changed.
- **GA-TRIAL-0006** — Sixth real operational use. AGENT-PROGRAM-002A required Grounding before writing the post-trial census. Local `main` was nine commits behind `origin/main` until a clean `--ff-only` to `a40d9030`. All 14 typed claims MATCH, including GitHub `pr_state` that #339 is merged and `file_exists` that the Agent 002 contract is absent. The stale-checkout observation is recorded as incident INC-002A-F1-002 in the 002A ledger, not as a Grounding false negative: Grounding was run after the fetch/ff, and a pre-fetch `file_exists` claim would have been the correct invocation. No Grounding Agent code was changed.

## Summary

```text
TRIAL PERIOD:
START: 2026-08-26
END:

TOTAL HANDOFFS CHECKED: 6
  MATCH / PROCEED:                5
  STALE / STOP:                   1
  BLOCKED / STOP:                 0
  INSUFFICIENT_EVIDENCE / STOP:   0

STALE HANDOFFS CAUGHT: 1
FALSE POSITIVES:       0
FALSE NEGATIVES:       0
BLOCKED RUNS:          0
HUMAN OVERRIDES:       0
ESTIMATED NET TIME EFFECT: small positive / neutral

DECISION (current): INSUFFICIENT EVIDENCE
Allowed terminal dispositions: KEEP | REVISE | RETIRE | INSUFFICIENT EVIDENCE
```

> The next agent (Reconciliation or otherwise) is not justified by architecture.
> It is justified only if this ledger shows a recurring failure that v0.1
> demonstrably does not prevent. If the ledger does not show real value, the
> decision is RETIRE — and we stop without having built a bureaucracy.
