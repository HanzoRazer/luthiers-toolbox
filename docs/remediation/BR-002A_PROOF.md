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

> **⚠ Three stored `tool_kind` states (verified — the core BR-002B design point):**
> - **`"saw"`** — persisted by the writers: `execution_confirmation_service.py:14,64`,
>   `execution_metrics_rollup_service.py`, `decision_router.py:86,128` (all default/set `"saw"`).
> - **`"saw_lab"`** — **persisted** by `app/services/saw_lab_compare_service.py:154`
>   (`index_meta["tool_kind"]="saw_lab"` → `_write_run_artifact_safely` → `persist_run`) for
>   saw-feasibility comparison artifacts.
> - **missing/empty** — older artifacts predating the field.
>
> (The `"saw_lab"` in `batch_query_router.py:78,110,…` is **not** a stored value — it is a
> `setdefault` **response fallback for older artifacts lacking `tool_kind`**, returned not persisted:
> the code comment says *"setdefault fallbacks for older artifacts"* and the function `return`s the dict.)
>
> Query callers pass `tool_kind="saw"`. So an **exact `== "saw"` match drops BOTH the persisted
> `"saw_lab"` compare artifacts AND every missing-`tool_kind` (older) artifact** → silent under-return.
> BR-002B is therefore **not decision-free**: it must define lenient/synonym read semantics. See Q4.

## Q4 — Correct filtering layer ✅

Add `tool_kind` matching to **`matches_index_meta`** and thread the param through the two wrapper layers
so it reaches `fkw`. Because `matches_index_meta` has only the 2 production callers, this changes no other
production consumer, and it gives **`list_runs_filtered` / `count_runs_filtered` parity for free** (both
use the shared filter — do **not** implement the match as a post-filter in `list` only, or count diverges).

**BR-002B design decision (required, from Q3's three states):** an exact `== "saw"` match is **wrong** —
it drops persisted `"saw_lab"` compare artifacts *and* all missing-`tool_kind` older artifacts. The
recommended semantics: **lenient + synonym** — match when the stored value is **empty/missing OR** in the
requested synonym set (treat `{"saw","saw_lab"}` as aliases). Document the exact rule; a
`"saw"`/`"saw_lab"` distinction is not currently meaningful to the callers (all pass `"saw"`).

> **Two filter sites — centralize, or they drift (verified):** the store filter is **not** the only
> place `tool_kind` is matched. `app/rmos/runs_v2/batch_tree.py:51-55` (`resolve_batch_root`) and
> `:122-123` (`list_batch_tree`) already do a **live local exact-match**
> `str((a...).get("tool_kind") or "") == tool_kind`. So even after `matches_index_meta` is made lenient,
> `batch_tree` would re-drop `"saw_lab"`/missing nodes — splitting semantics (tree/root/summary/export
> under-return while the flat list is correct). **BR-002B must route both sites through one canonical
> `tool_kind_matches(stored, requested)` helper.** Also review the in-memory filter in
> `app/rmos/runs_v2/batch_timeline.py` and any `FakeStore`/test filters that do raw `== tool_kind`.
>
> **Additional live defect surfaced:** `batch_tree`'s exact-match is **already** under-returning today
> for any caller that passes `tool_kind` against a mixed/old batch (independent of the BR-002 TypeError).
> Logged as **BR-035** (see ledger) — related to, but not blocked by, BR-002B.

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
**plus one design decision** (the `tool_kind` lenient/synonym semantics, step 3) applied through **one
canonical helper at two filter sites** (steps 3 & 4), so store and tree filtering cannot drift.

| # | File · function | Change |
| - | --------------- | ------ |
| 1 | `app/rmos/runs_v2/store_api.py:200` `list_runs_filtered` | add `tool_kind: Optional[str] = None`; forward `tool_kind=tool_kind` in the delegated call |
| 2 | `app/rmos/runs_v2/store.py:294` `RunStoreV2.list_runs_filtered` | add `tool_kind: Optional[str] = None`; add `tool_kind=tool_kind` to the `fkw` dict |
| 3 | `app/rmos/runs_v2/store_filter.py:9` `matches_index_meta` (+ maybe `store.py:58` `_extract_index_meta`) | add `tool_kind: Optional[str] = None`; match via a **new canonical helper `tool_kind_matches(stored, requested)`** with **lenient + synonym** semantics (match when `stored` is empty/missing **or** in `{"saw","saw_lab"}`). **⚠ Read the stored value from the RIGHT place — the empirical gate proved `tool_kind` is NOT a top-level index field: `_extract_index_meta` omits it, so it lives in `m["meta"]["tool_kind"]` (nested).** A literal `m.get("tool_kind")` match returns **0/3 — drops everything.** BR-002B must read `m["meta"]["tool_kind"]` in the filter **or** hoist `tool_kind` into `_extract_index_meta` (top-level; requires an index rebuild for existing data). |
| 4 | `app/rmos/runs_v2/batch_tree.py:51,122` `resolve_batch_root` / `list_batch_tree` | replace the two **live local exact-match** filters (`... == tool_kind`) with the **same** `tool_kind_matches()` helper, so tree/root/summary/export cannot drift from the store filter. |
| 5 | `app/saw_lab/store.py:16` `store_artifact` | add `batch_label: Optional[str] = None`, `tool_kind: Optional[str] = None`; if `batch_label` set → `payload["batch_label"] = batch_label` (Q6); if `tool_kind` set → `index_meta = {**(index_meta or {}), "tool_kind": tool_kind}` |

`count_runs_filtered` (`store.py:~360`) requires **no separate change** — it shares `matches_index_meta`,
so it stays in **parity** with `list` automatically (that parity is a reason to fix the shared filter, not
to post-filter `list`). Also review `app/rmos/runs_v2/batch_timeline.py`'s in-memory filter + any
`FakeStore`/test raw `== tool_kind` for the same helper.

## BR-002B test matrix

- **Flip xfails (acceptance):** `tests/test_saw_lab_endpoint_smoke.py:24` (`list_runs_filtered_bug`), `:30`
  (`store_artifact_bug`), `tests/test_rmos_endpoint_smoke.py:21` (`list_runs_filtered_bug`, `strict=False`).
- **Targeted regression (must stay green):** **`tests/test_store_filter.py`** (33 direct
  `matches_index_meta` assertions — the primary filter-contract suite), `tests/test_saw_lab_*.py`,
  `tests/test_rmos_endpoint_smoke.py`, `tests/test_rmos_workflow_e2e.py`, and any other `runs_v2`
  store/filter tests (`tests/**/*runs*`, `*store*`, `*batch_tree*`, `*batch_summary*`) — because
  `list_runs_filtered` / `matches_index_meta` are shared.
- **New coverage BR-002B must add** (pin the chosen semantics with tests):
  1. `matches_index_meta(tool_kind="saw")` matches stored `"saw"`, stored `"saw_lab"`, **and
     missing/empty** — and does not match an unrelated value.
  2. `list_runs_filtered(session_id, batch_label, tool_kind="saw")` returns a **mixed** batch
     (artifacts tagged `"saw"`, `"saw_lab"`, and missing) with none dropped.
  3. `list_batch_tree(..., tool_kind="saw")` and `resolve_batch_root(..., tool_kind="saw")` include the
     `"saw_lab"`/missing nodes in a mixed-tag batch (the batch_tree parity that step 4 fixes).
  4. **count/list parity:** `count_runs_filtered(tool_kind="saw")` == the length of the matching
     `list_runs_filtered` result on the same fixture.
  5. Execution-lookup path: `list_executions_for_decision(..., tool_kind="saw")` finds executions when
     the stored artifacts are `"saw_lab"`/missing.
- **Broad regression:** the saw_lab + rmos suites in full (not just smoke).

## Corrections this packet makes to the PR #227 scope docs (to fold into the BR-002B ledger update)

1. `store_api.py:200` is the **TypeError raise-site** (re-exported as `store.list_runs_filtered`), not a
   "wrong file". The three-layer chain is the accurate scope.
2. **Production blast radius is contained:** `matches_index_meta` has **2 production callers** (both in
   scope) — *not* a broad shared surface. (Precise: 35 total call sites = 2 production + 33
   `test_store_filter.py` assertions; the additive param doesn't disturb the tests but they must run.)
3. **BR-004 is a `list_runs_filtered` bug** (dedups into BR-002), not a `store_artifact` bug.
4. **Three stored `tool_kind` states** (`"saw"` writers · `"saw_lab"` *persisted* by
   `saw_lab_compare_service.py:154` · missing/older) mean a naive `== "saw"` filter silently
   under-returns. BR-002B is **not decision-free**: use lenient+synonym semantics (Q3/Q4). The
   `batch_query_router` `"saw_lab"` is a **response-only fallback**, not stored (an earlier draft and an
   external trace both mis-stated this). Corrected on verification — the reason to keep the owner gate.
5. **Two filter sites** need one canonical helper (`matches_index_meta` **and** `batch_tree.py:51,122`),
   else tree/summary/export drift from the flat list.
6. **New live defect BR-035:** `batch_tree`'s existing exact-match already under-returns mixed/old
   batches today — logged separately (related to, not blocked by, BR-002B).

## BR-002B authorization checklist (from the Dev Order) — status

```text
[x] proof packet exists, all seven §3 questions answered with citations
[x] module-level dispatch resolved (store.py:396 re-export from store_api.py:200 → store.py:294 → store_filter)
[x] caller census enumerated (list_runs_filtered 32/23 app/ · 43/36 incl tests; matches_index_meta 2 prod + 33 test)
[~] filtering LAYER decided (matches_index_meta + batch_tree via ONE canonical helper); tool_kind VALUE
    semantics (lenient+synonym for 3 stored states) is a documented BR-002B design decision (Q3/Q4)
[x] batch_label persistence contract pinned (payload["batch_label"]; store.py:111/156/359)
[x] BR-004 dedup verdict recorded (= BR-002, list_runs_filtered)
[x] BR-002B patch plan concrete + named regression set (incl. test_store_filter.py + a new saw/saw_lab test)
[x] tool_kind GROUND-TRUTH check (empirical gate) — EXECUTED 2026-07-22 (see "Empirical gate results")
[ ] owner authorization for BR-002B recorded   ← the one remaining gate
```

## Empirical gate results (executed 2026-07-22 — read-only, temp `RMOS_RUNS_DIR`)

Persisted 3 artifacts through the **real** `store_api.store_artifact` (default → `saw`; `tool_kind="saw_lab"`;
`tool_kind=""` → missing), rebuilt the index, and **observed** the actual persisted structure:

| write | top-level `tool_kind` | `meta.tool_kind` | `mode` | `tool_id` |
| ----- | --------------------- | ---------------- | ------ | --------- |
| default | *(none)* | **saw** | saw | saw |
| `="saw_lab"` | *(none)* | **saw_lab** | saw_lab | saw_lab |
| `=""` (legacy) | *(none)* | *(none)* | legacy | unknown |

- ✅ **Three-state model confirmed by observation:** `meta.tool_kind ∈ {saw, saw_lab, missing}`.
- 🔴 **New finding — `tool_kind` is NOT a top-level index field.** `_extract_index_meta` (`store.py:58`)
  omits it; it survives only in `m["meta"]["tool_kind"]`, and leaks into `mode`/`tool_id`. A filter reading
  `m.get("tool_kind")` (literal patch-plan step 3) matched **0/3 — it would drop every artifact.** Reading
  `m["meta"]["tool_kind"]` matched 1/3 per value, as expected. Patch-plan step 3 corrected accordingly.
- ✅ **BR-002 TypeError reproduced** empirically: `list_runs_filtered(tool_kind="saw")` →
  *"unexpected keyword argument 'tool_kind'"*.
- ⚠ **Carry into BR-002B:** verify `batch_tree`'s item shape too — it reads `a["index_meta"]["tool_kind"]`,
  a *different* structure than the store index's `meta`, so it may already be reading the wrong place (BR-035).

> **Net:** the archaeology is complete and BR-002B is authorizable, but with **one explicit design
> decision** (the `tool_kind` lenient/synonym value handling) **and one concrete implementation
> constraint** (read `meta.tool_kind`, not top-level) — so BR-002B is *bounded*, not *decision-free*.

> **Verification note (scoped to `tool_kind`, not a general rule):** this area has now mis-stated its own
> mechanism twice (value count; persisted-vs-response tagging), both caught only by going to source/data.
> For `tool_kind` specifically, load-bearing claims must be verified against **ground-truth data**, not
> code-reading, before *and* after the BR-002B mutation. This is not a new governance gate for other
> items — the archaeology tranche already covers the general case.
