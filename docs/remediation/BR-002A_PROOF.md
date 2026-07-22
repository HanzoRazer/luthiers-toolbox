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

- **`list_runs_filtered`:** **32 sites / 23 files in `app/`** (43 sites / 36 files including `tests/`).
  `app/` callers that pass `tool_kind=` (i.e. currently break): `app/rmos/runs_v2/batch_summary.py:123`,
  and saw_lab services `executions_list_service.py:65`, `executions_lookup_service.py:37`,
  `execution_confirmation_service.py:79`, `execution_metrics_rollup_service.py:116`,
  `execution_status_service.py:49`. (Others don't pass `tool_kind` and are unaffected — the new param
  defaults to `None`.)
- **`matches_index_meta`:** **2 production callers** — `store.py:332` (`list_runs_filtered`) and
  `store.py:389` (`count_runs_filtered`), both in scope — **plus 33 direct assertions in
  `tests/test_store_filter.py`** (verified: `grep matches_index_meta(` = 35 sites total, 2 prod + 33
  test). The production blast radius is contained to the 2; the 33 tests are a **regression surface** (an
  additive optional param defaulting to `None` won't disturb them, but they must be run). *This corrects
  the bare "only 2 callers" phrasing — 2 is the production count, not the total.*

## Q3 — Is `tool_kind` canonical index metadata? ✅

Yes, `tool_kind` is an established `index_meta` field, and **filtering on it already exists**:
`app/rmos/runs_v2/batch_tree.py:51-55,122-123` filters by
`str((a.get("index_meta") or {}).get("tool_kind") or "") == tool_kind`. Do **not** alias to `tool_id`
(`tool_id` is a specific tool identifier; `tool_kind` is the tool class).

> **⚠ Value inconsistency (found on verification — a BR-002B design point):** the field is written with
> **two different values**. `app/saw_lab/batch_query_router.py:78,110,144,178,212,246` sets
> `index_meta.setdefault("tool_kind", "saw_lab")`, while `app/saw_lab/decision_router.py:86,128` sets
> `"saw"`, and the query callers pass `tool_kind="saw"` (e.g. `executions_list_service.py:40` default).
> An **exact-match** filter (`== tool_kind`) with `tool_kind="saw"` would therefore **silently miss any
> `"saw_lab"`-tagged artifact** — the existing `batch_tree` filter has the same latent exposure. So
> BR-002B is **not** purely decision-free: it must resolve this (normalize the values, match a set, or
> confirm the store/query paths always agree). See Q4.

## Q4 — Correct filtering layer ✅

Add `tool_kind` matching to **`matches_index_meta`** and thread the param through the two wrapper layers
so it reaches `fkw`. Because `matches_index_meta` has only the 2 production callers, this changes no other
production consumer (33 `test_store_filter.py` assertions are unaffected by an optional param).

**Open BR-002B design decision (from Q3's value inconsistency):** the match cannot be a naive
`== "saw"` exact-match, or it drops `"saw_lab"`-tagged artifacts. BR-002B must choose one of:
(a) **normalize** `"saw_lab"` → `"saw"` at write and/or compare time; (b) **membership** match against a
known synonym set (`{"saw","saw_lab"}`); or (c) prove the queried batch artifacts are *always* tagged
consistently so exact-match is safe. This decision (and whether the pre-existing `batch_tree` filter is
already under-returning) is a **required BR-002B input**, not a decided one — so the "decision-free"
claim from the original packet does not fully hold.

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

Additive param signatures (each new param defaults to `None`/absent, so existing callers are untouched)
**plus one design decision** — the `tool_kind` value normalization in step 3 (see Q3/Q4).

| # | File · function | Change |
| - | --------------- | ------ |
| 1 | `app/rmos/runs_v2/store_api.py:200` `list_runs_filtered` | add `tool_kind: Optional[str] = None`; forward `tool_kind=tool_kind` in the delegated call |
| 2 | `app/rmos/runs_v2/store.py:294` `RunStoreV2.list_runs_filtered` | add `tool_kind: Optional[str] = None`; add `tool_kind=tool_kind` to the `fkw` dict |
| 3 | `app/rmos/runs_v2/store_filter.py:9` `matches_index_meta` | add `tool_kind: Optional[str] = None` + a match on `index_meta["tool_kind"]`, wired into an existing sub-matcher. **Design decision (Q3/Q4): must handle the `"saw"` vs `"saw_lab"` value inconsistency** — normalize, membership-match a synonym set, or prove consistent tagging; a naive `== "saw"` exact-match drops `"saw_lab"` artifacts. |
| 4 | `app/saw_lab/store.py:16` `store_artifact` | add `batch_label: Optional[str] = None`, `tool_kind: Optional[str] = None`; if `batch_label` set → `payload["batch_label"] = batch_label` (Q6); if `tool_kind` set → `index_meta = {**(index_meta or {}), "tool_kind": tool_kind}` |

Optional consistency: `count_runs_filtered` (`store.py:~360`) need not change — its callers don't pass
`tool_kind`; `matches_index_meta`'s new param defaults `None` so `count` is unaffected.

## BR-002B test matrix

- **Flip xfails (acceptance):** `tests/test_saw_lab_endpoint_smoke.py:24` (`list_runs_filtered_bug`), `:30`
  (`store_artifact_bug`), `tests/test_rmos_endpoint_smoke.py:21` (`list_runs_filtered_bug`, `strict=False`).
- **Targeted regression (must stay green):** **`tests/test_store_filter.py`** (33 direct
  `matches_index_meta` assertions — the primary filter-contract suite), `tests/test_saw_lab_*.py`,
  `tests/test_rmos_endpoint_smoke.py`, `tests/test_rmos_workflow_e2e.py`, and any other `runs_v2`
  store/filter tests (`tests/**/*runs*`, `*store*`, `*batch_tree*`, `*batch_summary*`) — because
  `list_runs_filtered` / `matches_index_meta` are shared.
- **New coverage BR-002B must add:** a `matches_index_meta` test for the `tool_kind` filter **including
  the `"saw"`/`"saw_lab"` case** decided in step 3, so the value-normalization choice is pinned by a test.
- **Broad regression:** the saw_lab + rmos suites in full (not just smoke).

## Corrections this packet makes to the PR #227 scope docs (to fold into the BR-002B ledger update)

1. `store_api.py:200` is the **TypeError raise-site** (re-exported as `store.list_runs_filtered`), not a
   "wrong file". The three-layer chain is the accurate scope.
2. **Production blast radius is contained:** `matches_index_meta` has **2 production callers** (both in
   scope) — *not* a broad shared surface. (Precise: 35 total call sites = 2 production + 33
   `test_store_filter.py` assertions; the additive param doesn't disturb the tests but they must run.)
3. **BR-004 is a `list_runs_filtered` bug** (dedups into BR-002), not a `store_artifact` bug.
4. **`tool_kind` value inconsistency (`"saw"` vs `"saw_lab"`)** means BR-002B is **not fully
   decision-free** — the filter must resolve value normalization (Q3/Q4). This was missed on the first
   archaeology pass and surfaced on count-verification; it is the reason to keep the owner gate.

## BR-002B authorization checklist (from the Dev Order) — status

```text
[x] proof packet exists, all seven §3 questions answered with citations
[x] module-level dispatch resolved (store.py:396 re-export from store_api.py:200 → store.py:294 → store_filter)
[x] caller census enumerated (list_runs_filtered 32/23 app/ · 43/36 incl tests; matches_index_meta 2 prod + 33 test)
[~] filtering LAYER decided (matches_index_meta); tool_kind VALUE normalization ("saw"/"saw_lab") is an
    open, documented BR-002B design decision (Q3/Q4) — carry into BR-002B, not decided here
[x] batch_label persistence contract pinned (payload["batch_label"]; store.py:111/156/359)
[x] BR-004 dedup verdict recorded (= BR-002, list_runs_filtered)
[x] BR-002B patch plan concrete + named regression set (incl. test_store_filter.py + a new saw/saw_lab test)
[ ] owner authorization for BR-002B recorded   ← the one remaining gate
```

> **Net:** the archaeology is complete and BR-002B is authorizable, but with **one explicit design
> decision** (the `"saw"`/`"saw_lab"` value handling) — so BR-002B is *bounded*, not *decision-free*.
