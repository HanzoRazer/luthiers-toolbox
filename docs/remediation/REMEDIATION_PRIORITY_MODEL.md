# BR-001 — Remediation Priority Model

> How retained items are ordered. The ranking is **advisory**; owner adjudication remains authoritative.
> Priority is a function of **consequence and dependency — never issue count or age alone** (charter §4 · Disposition discipline).

## Inputs (per item, from the [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md))

| Factor | Meaning | Scale |
| ------ | ------- | ----- |
| User-facing severity | how badly it affects a user of the product | 0–3 |
| Manufacturing / safety consequence | risk to a real cut/part or to a person | 0–3 |
| Data-loss / evidence-integrity risk | can it corrupt or lose data/provenance | 0–3 |
| Architectural blockage | does it block other remediation or development | 0–3 |
| Regression potential | likelihood the area regresses if untouched / when touched | 0–2 |
| Subsystem centrality | how many paths depend on the affected subsystem | 0–2 |
| Reproducibility | is the current evidence solid and deterministic | 0–2 |
| Implementation readiness | is it ready to execute (bounded, no open decision) | 0–2 |
| Estimated remediation size | effort — **inverse** contributor (small = easier to schedule) | 0–2 |

## Scoring

```text
Consequence  = severity + manufacturing_safety + data_integrity + architectural_blockage
Risk         = regression_potential + subsystem_centrality
Confidence   = reproducibility + implementation_readiness
Effort_bonus = (2 - size_penalty)           # smaller, bounded work scores higher

Priority score = (2 * Consequence) + Risk + Confidence + Effort_bonus
```

Consequence is weighted ×2: a high-consequence item outranks a large cluster of low-consequence ones,
regardless of how many reports exist. **Count and age are not inputs.**

## Gating rules (override the raw score)

1. **No unverified items.** An item without current evidence (per its tier) is not rankable and does not
   enter the queue — it stays in the ledger as `STALE_OR_NOT_REPRODUCIBLE` or `OWNER_DECISION_REQUIRED`.
2. **Blockers first.** An item that blocks others is scheduled no later than what it blocks, even if its
   own raw score is lower (see [REMEDIATION_DEPENDENCY_MAP.md](REMEDIATION_DEPENDENCY_MAP.md)).
3. **Owner-decision items are parked**, not ranked, until the decision is made.
4. **Readiness gates the next candidate.** The single next candidate must be bounded and decision-free
   (charter §6) — a higher-scoring but unbounded/undecided item cannot be the next candidate.

## Waves

Items are grouped into waves by dependency and subsystem relationship, not by raw score alone. Each wave
is a set of related items safe and sensible to execute together. Wave boundaries are derived from the
dependency map, not copied from a template.

## Authority

This model makes ordering **transparent and reviewable**; it does not make the decision. The owner may
re-rank any item; the model exists so that a re-rank is a visible, reasoned change rather than an opaque
one.
