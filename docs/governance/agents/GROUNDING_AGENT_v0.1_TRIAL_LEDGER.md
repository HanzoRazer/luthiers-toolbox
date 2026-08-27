# Grounding Agent v0.1 — Trial Ledger

This is the measurement instrument for deciding whether Grounding Agent v0.1
deserves to exist. It is **not** a governance program — it is one table plus a
short summary. Record one row per **real** use (an actual Dev Order or handoff),
never synthetic exercises.

Spec: [`GROUNDING_AGENT_v0.1.md`](GROUNDING_AGENT_v0.1.md)

## How to record a row
- **Result** — the agent's top-level status/decision, e.g. `MATCH/PROCEED`, `STALE/STOP`, `BLOCKED/STOP`, `INSUFFICIENT_EVIDENCE/STOP`.
- **Stale caught?** — did it catch stale state we would otherwise have acted on? (`yes`/`no`)
- **False positive?** — did it STOP on something that was actually fine? (`yes`/`no`)
- **False negative?** — did it PROCEED past stale state it should have caught? (`yes`/`no`)
- **Blocked evidence?** — did a required evidence source fail (no token, GitHub down, etc.)? (`yes`/`no`)
- **Human override?** — did a human override the STOP and proceed anyway? (`yes`/`no`)
- **Time saved?** — rough estimate (e.g. `~15m`, `none`, `-` if unknown).
- **Notes** — one line of context; link the handoff/PR if useful.

## Ledger

| Date | Handoff / Order | Result | Stale caught? | False positive? | False negative? | Blocked evidence? | Human override? | Time saved? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | |

## Summary

```text
TRIAL PERIOD:
START:
END:

TOTAL HANDOFFS CHECKED:
STALE HANDOFFS CAUGHT:
FALSE POSITIVES:
FALSE NEGATIVES:
BLOCKED RUNS:
HUMAN OVERRIDES:
ESTIMATED TIME SAVED:

DECISION:
KEEP
REVISE
RETIRE
INSUFFICIENT EVIDENCE
```

> The next agent (Reconciliation or otherwise) is not justified by architecture.
> It is justified only if this ledger shows a recurring failure that v0.1
> demonstrably does not prevent. If the ledger does not show real value, the
> decision is RETIRE — and we stop without having built a bureaucracy.
