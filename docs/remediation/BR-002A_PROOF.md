# BR-002A — Store-Path Proof Packet

> Deliverable of the [BR-002A Dev Order](BR-002A_STORE_PATH_ARCHAEOLOGY.md). Read-only archaeology
> executed against `main` (post-#227). Answers all seven §3 questions with citations, and produces the
> **implementation-ready BR-002B patch plan + test matrix**. **No production code was changed.**
>
> **This packet is the authoritative scoping record** and it *corrects three imprecise statements* in the
> earlier PR #227 scope-correction (see "Corrections" at the end) — the reason archaeology-before-mutation
> was the right call.

## Q1 — Dispatch resolution ✅

The failing call resolves through **three layers**, all lacking `tool_kind`:

```text
app/saw_lab/executions_list_service.py:62
  runs_store.list_runs_filtered(tool_kind=…)          runs_store = app.rmos.runs_v2.store
     │  store.py:396 re-exports the name FROM store_api:
     │  `from .store_api import (… list_runs_filtered, store_artifact …)`
     ▼
app/rmos/runs_v2/store_api.py:200  list_runs_filtered(...)   ← module wrapper; **raises the TypeError here**
     │  (keyword-only signature, no tool_kind, no **kwargs → unexpected-kwarg TypeError)
     │  body: store = _get_default_store(); return store.list_runs_filtered(… explicit kwargs …)
     ▼
app/rmos/runs_v2/store.py:294  RunStoreV2.list_runs_filtered(self, ...)   ← class method; no tool_kind
     │  builds fkw = dict(...); matching = [m for m in index if matches_index_meta(m, **fkw)]
     ▼
app/rmos/runs_v2/store_filter.py:9  matches_index_meta(m, ...)   ← shared filter; no tool_kind
```

**Correction to prior docs:** `store_api.py:200` is *not* "the wrong file" — it is the exact site the
`TypeError` is raised (the original packet was right about that). It is re-exported as
`store.list_runs_filtered` via `store.py:396`. The fix must touch **all three layers**.

## Q2 — Caller census ✅

- **`list_runs_filtered`:** 32 call sites across 23 files. Callers that pass `tool_kind=` (i.e. currently
  break): `app/rmos/runs_v2/batch_summary.py:123`, and saw_lab services
  `executions_list_service.py:65`, `executions_lookup_service.py:37`, `execution_confirmation_service.py:79`,
  `execution_metrics_rollup_service.py:116`, `execution_status_service.py:49`. (Others don't pass
  `tool_kind` and are unaffected — the new param defaults to `None`.)
- **`matches_index_meta`:** **only 2 callers**, both internal to `store.py` —
  `list_runs_filtered` (:332) and `count_runs_filtered` (:389). *Blast radius is contained to these two*,
  both already in scope. (This corrects the earlier "broad shared-filter blast radius" framing.)

## Q3 — Is `tool_kind` canonical index metadata? ✅

Yes. saw_lab writes `index_meta["tool_kind"] = "saw"` (`batch_query_router.py`, `decision_router.py`, …),
and **filtering on it already exists**: `app/rmos/runs_v2/batch_tree.py:51-55,122-123` filters items by
`str((a.get("index_meta") or {}).get("tool_kind") or "") == tool_kind`. Canonical spelling is
**`tool_kind`** (an `index_meta` field). Do **not** alias to `tool_id` — `tool_id` is a distinct field
(a specific tool identifier); `tool_kind` is the tool class.

## Q4 — Correct filtering layer ✅

Add `tool_kind` as a simple `index_meta` field match in **`matches_index_meta`**, mirroring the existing
`batch_tree` semantics (`index_meta.get("tool_kind") == tool_kind` when provided), and thread the param
through the two wrapper layers so it reaches `fkw`. Because `matches_index_meta` has only the 2 in-scope
callers, this changes no other consumer.

## Q5 — Pagination & ordering ✅

`matches_index_meta` is applied at `store.py:332` **before** the `created_at_utc`-descending sort
(:335-338) and the `offset:offset+limit` pagination (:341). A `tool_kind` filter only narrows the
pre-sort candidate set; ordering and pagination semantics are unchanged.

## Q6 — `batch_label` persistence contract ✅

The `query_*_by_label` readers all read **`payload.get("batch_label")`**:
`app/saw_lab/store.py:111` (`query_latest_by_label_and_session`), `:156` (`query_executions_by_label`),
`:359` (`query_executions_with_learning`). Therefore `store_artifact` must place `batch_label` **into the
`payload` dict** (readers do not consult `index_meta` for the label). `tool_kind`, by contrast, belongs in
`index_meta` (so listing can filter on it per Q3/Q4).

## Q7 — BR-004 dedup ✅ (with a ledger correction)

`test_rmos_endpoint_smoke.py:21` is `list_runs_filtered_bug` — reason *"list_runs_filtered() may have
unexpected keyword arguments"*, `raises=TypeError`, `strict=False`. **BR-004 is a `list_runs_filtered`
bug — the SAME root as BR-002, not a `store_artifact` bug.** The ledger's "RMOS endpoint `store_artifact`
bug / shared root w/ BR-001" label is wrong; BR-004 dedups into **BR-002**. (`strict=False` → it XPASSes
harmlessly once fixed.)

---

## BR-002B patch plan (implementation-ready)

Additive only; every change is a new optional param defaulting to `None`/absent, so existing callers are
untouched.

| # | File · function | Change |
| - | --------------- | ------ |
| 1 | `app/rmos/runs_v2/store_api.py:200` `list_runs_filtered` | add `tool_kind: Optional[str] = None`; forward `tool_kind=tool_kind` in the delegated call |
| 2 | `app/rmos/runs_v2/store.py:294` `RunStoreV2.list_runs_filtered` | add `tool_kind: Optional[str] = None`; add `tool_kind=tool_kind` to the `fkw` dict |
| 3 | `app/rmos/runs_v2/store_filter.py:9` `matches_index_meta` | add `tool_kind: Optional[str] = None` + a match: when provided, require `str(m.get("index_meta",{}).get("tool_kind") or "") == tool_kind` (mirror `batch_tree`); wire into an existing sub-matcher |
| 4 | `app/saw_lab/store.py:16` `store_artifact` | add `batch_label: Optional[str] = None`, `tool_kind: Optional[str] = None`; if `batch_label` set → `payload["batch_label"] = batch_label` (Q6); if `tool_kind` set → `index_meta = {**(index_meta or {}), "tool_kind": tool_kind}` |

Optional consistency: `count_runs_filtered` (`store.py:~360`) need not change — its callers don't pass
`tool_kind`; `matches_index_meta`'s new param defaults `None` so `count` is unaffected.

## BR-002B test matrix

- **Flip xfails (acceptance):** `tests/test_saw_lab_endpoint_smoke.py:24` (`list_runs_filtered_bug`), `:30`
  (`store_artifact_bug`), `tests/test_rmos_endpoint_smoke.py:21` (`list_runs_filtered_bug`, `strict=False`).
- **Targeted regression (must stay green):** `tests/test_saw_lab_*.py`, `tests/test_rmos_endpoint_smoke.py`,
  `tests/test_rmos_workflow_e2e.py`, and any `runs_v2` store/filter tests (`tests/**/*runs*`,
  `*store*`, `*batch_tree*`, `*batch_summary*`) — because `list_runs_filtered` / `matches_index_meta` are
  shared.
- **Broad regression:** the saw_lab + rmos suites in full (not just smoke).

## Corrections this packet makes to the PR #227 scope docs (to fold into the BR-002B ledger update)

1. `store_api.py:200` is the **TypeError raise-site** (re-exported as `store.list_runs_filtered`), not a
   "wrong file". The three-layer chain is the accurate scope.
2. **Blast radius is contained:** `matches_index_meta` has only 2 internal callers (both in scope), not a
   broad shared surface.
3. **BR-004 is a `list_runs_filtered` bug** (dedups into BR-002), not a `store_artifact` bug.

## BR-002B authorization checklist (from the Dev Order) — status

```text
[x] proof packet exists, all seven §3 questions answered with citations
[x] module-level dispatch resolved (store.py:396 re-export from store_api.py:200 → store.py:294 → store_filter)
[x] caller census enumerated (list_runs_filtered ×32/23 files; matches_index_meta ×2 internal)
[x] canonical tool_kind field + filtering layer decided (index_meta field; matches_index_meta)
[x] batch_label persistence contract pinned (payload["batch_label"]; store.py:111/156/359)
[x] BR-004 dedup verdict recorded (= BR-002, list_runs_filtered)
[x] BR-002B patch plan concrete + named regression set
[ ] owner authorization for BR-002B recorded   ← the one remaining gate
```
