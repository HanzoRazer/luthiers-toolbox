# BR-001 — Next Remediation Candidate

> **Status: SCOPE CORRECTION REQUIRED (2026-07-21).** The originally-selected candidate below
> (saw_lab/rmos store-layer kwarg wiring, resolving ledger items BR-001/BR-002/BR-004) was marked
> `READY` on the strength of a code-inspection that mis-scoped it. BR-002 execution archaeology proved
> two load-bearing assumptions wrong. The candidate is **not abandoned** (the defect is reproduced and
> production-affecting); it is **re-scoped** and split into two bounded Dev Orders:
> **BR-002A** (store-path archaeology / contract proof — the actual next Dev Order) →
> **BR-002B** (additive repair, authorized only after 002A is green). See
> [BR-002A_STORE_PATH_ARCHAEOLOGY.md](BR-002A_STORE_PATH_ARCHAEOLOGY.md).

## What the original packet got wrong

| Original claim | Corrected finding |
| -------------- | ----------------- |
| `list_runs_filtered` is at `app/rmos/runs_v2/store_api.py:200` (as a small isolated fix) | **Under-scoped, not wrong-file.** [BR-002A_PROOF](BR-002A_PROOF.md) Q1: `store_api.py:200` *is* the `TypeError` raise-site (re-exported as `store.list_runs_filtered`), but the fix spans a **3-layer chain** — `store_api.py:200` → `store.py:294` class method → `store_filter.matches_index_meta`. |
| "Bounded file impact… 2–3 functions… single-subsystem" | The fix crosses a **shared filter boundary**: `list_runs_filtered` forwards filters via `**fkw` to `store_filter.matches_index_meta`, **which has no `tool_kind` parameter**. Adding `tool_kind` touches the filter used by **every `runs_v2` consumer**, not just saw_lab. |
| "decision-free, flip 3 xfails, no research dependency" | The module-level dispatch of `store.list_runs_filtered` is **not yet resolved** (no `^def list_runs_filtered` / obvious singleton binding in `store.py`); how the module attribute resolves must be established before editing. This is the research BR-002A performs. |

## What still holds

- The **defect is real and reproduced**: `store_artifact(batch_label=…)` (`app/saw_lab/store.py:16`, no
  such param) and `list_runs_filtered(tool_kind=…)` both raise `TypeError` (HTTP 500) via the saw_lab
  endpoints; three committed xfail tests assert it (`test_saw_lab_endpoint_smoke.py:24,30`,
  `test_rmos_endpoint_smoke.py:21`).
- It remains the **next** remediation target — larger-than-expected scope is a reason to tighten
  authorization, not to switch items and leave a verified production defect parked.
- Acceptance for the eventual repair is still built in (flip the three xfail markers), plus a broad
  `runs_v2` regression added by the correction.

## The corrected sequence

```text
BR-002A  Store-path archaeology + contract proof   (no production mutation)  ← next Dev Order
    ↓ (only when 002A proof packet is green)
BR-002B  Additive store + filter repair             (mutates saw_lab store + runs_v2 filter)
    ↓
resolves ledger items BR-001, BR-002, BR-004; removes the 3 xfails; updates the living ledgers
```

Ledger items **BR-001 / BR-002 / BR-004** stay `CONFIRMED_DEFECT`; their **readiness is now
`SCOPE CORRECTION REQUIRED`** pending BR-002A. The BR-002A Dev Order is
[BR-002A_STORE_PATH_ARCHAEOLOGY.md](BR-002A_STORE_PATH_ARCHAEOLOGY.md).

## Note on identifiers

"BR-001/002/004" are **ledger defect items**. "BR-002A/BR-002B" are the **Dev Order tranches** that
will fix them. (The reused "BR-002" number is an artifact of the original packet naming; the ledger
item BR-002 = the `tool_kind` defect, and Dev Order BR-002A = its archaeology tranche.)
