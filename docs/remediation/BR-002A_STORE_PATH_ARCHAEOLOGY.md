# BR-002A — Store-Path Archaeology & Contract Proof

> The corrected next Dev Order for the saw_lab/rmos store-layer kwarg defect
> (ledger items **BR-001 / BR-002 / BR-004**). **No production mutation.** BR-002A produces an
> implementation-ready **proof packet**; the repair itself is the separate **BR-002B**, authorized only
> after 002A is green. Supersedes the mis-scoped candidate in
> [NEXT_REMEDIATION_CANDIDATE.md](NEXT_REMEDIATION_CANDIDATE.md).

## 1. Objective

Establish the exact contract of the central `runs_v2` store path and the saw_lab artifact-store path so
the eventual repair (BR-002B) is additive, minimal, and safe for **all** `runs_v2` consumers — not just
saw_lab. BR-002A changes no production code.

## 2. Why this tranche exists

The original candidate assumed the fix was 2–3 isolated functions at `store_api.py:200`. Execution
proved: the failing call is `app/saw_lab/executions_list_service.py:62` →
`app.rmos.runs_v2.store.list_runs_filtered(tool_kind=…)`; `list_runs_filtered` forwards filters via
`**fkw` to the **shared** `store_filter.matches_index_meta`, which has **no `tool_kind` parameter**; and
the module-level dispatch of `store.list_runs_filtered` is not yet resolved. Mutating a shared filter
without this proof risks breaking every `runs_v2` list consumer.

## 3. Scope — questions BR-002A must answer (each with cited evidence)

1. **Dispatch resolution.** How does the module attribute `app.rmos.runs_v2.store.list_runs_filtered`
   resolve to a callable? (module-level function? singleton instance method bound at import? `__getattr__`?
   re-export?) Cite the exact line(s). Confirm whether `store_api.py:200`'s `list_runs_filtered` and the
   class method at `store.py:294` are the same target, wrappers, or distinct.
2. **Shared-filter caller census.** Enumerate **every** caller of `list_runs_filtered` and of
   `matches_index_meta` across the repo (not just saw_lab). For each: does it pass positional/`**kwargs`
   that adding a `tool_kind` param could disturb? Cite file:line.
3. **Is `tool_kind` already canonical index metadata?** saw_lab writes `index_meta["tool_kind"] = "saw"`
   (`batch_query_router.py`, `decision_router.py`, …). Determine whether `tool_kind` is a recognized
   index field elsewhere, or saw_lab-local. Decide the canonical spelling (`tool_kind` vs existing
   `tool_id`/`mode`/`kind`) — do **not** introduce a synonym if an existing field already carries it.
4. **Correct filtering layer.** Decide where `tool_kind` filtering belongs: added to
   `matches_index_meta` (+ a sub-matcher, like `_matches_simple_fields`), or handled in
   `list_runs_filtered` before delegating, or mapped onto an existing field. Justify against the caller
   census so no existing consumer changes behavior.
5. **Pagination & ordering.** Confirm that adding a `tool_kind` filter preserves the existing
   `created_at_utc`-descending sort and offset/limit pagination (`store.py:334-341`); a filter that
   changes the candidate set must not change ordering semantics for existing filters.
6. **`batch_label` persistence representation.** `store_artifact` (`app/saw_lab/store.py:16`) stores
   `payload` and `index_meta`; `query_executions_by_label`/`query_latest_by_label_and_session` read
   `payload.get("batch_label")`. Establish the exact representation the repair must produce so
   `batch_label` passed to `store_artifact` lands where the `query_*_by_label` readers expect it
   (payload key? index_meta? both?). Cite the read sites.
7. **RMOS `store_artifact` (BR-004) dedup.** Confirm whether `test_rmos_endpoint_smoke.py:21`'s failure
   is the same root as BR-001 (saw_lab `store_artifact`) or a distinct `store_artifact`
   (`app/rmos/runs_v2/store_api.py:134`). Resolve the duplicate relationship.

## 4. Deliverable — the proof packet

> **STATUS: PRODUCED 2026-07-21 → [BR-002A_PROOF.md](BR-002A_PROOF.md).** All seven §3 questions answered
> with citations; dispatch resolved (`store_api.py:200` re-exported → `store.py:294` → `matches_index_meta`);
> production blast radius **contained** (2 production `matches_index_meta` callers; +33 test assertions);
> BR-004 dedups into BR-002; concrete BR-002B patch plan + test matrix ready — with **one documented
> design decision** (the `"saw"`/`"saw_lab"` `tool_kind` value handling). **Remaining gate: owner
> authorization for BR-002B.**

A single document (`BR-002A_PROOF.md`, produced by executing this order) containing:

- the resolved dispatch mechanism (with line citations);
- the full caller census for `list_runs_filtered` and `matches_index_meta`;
- the canonical `tool_kind` decision and the chosen filtering layer, justified;
- the `batch_label` persistence contract;
- the BR-004 dedup verdict;
- an **updated BR-002B patch plan** (exact files + functions + the additive change per file) and an
  **updated test matrix** (the 3 xfails to flip + the specific `runs_v2` regression tests to run).

## 5. Boundary (BR-002A)

- **No production code, schema, route, or test change.** Read-only archaeology + the proof doc.
- No editing of `store.py`, `store_filter.py`, or `saw_lab/store.py`.
- Ends at the proof packet; BR-002B is a separate authorization.

## 6. Acceptance (BR-002A is "green")

All seven §3 questions answered with cited evidence; the proof packet's BR-002B patch plan is
concrete enough that BR-002B is a mechanical, additive change with a named regression set; no open
research question remains.

---

## BR-002B — Additive store & filter repair (NOT authorized yet)

### BR-002B may begin only when ALL are true

```text
[ ] BR-002A proof packet (BR-002A_PROOF.md) exists and answers all seven §3 questions with citations
[ ] the module-level dispatch of store.list_runs_filtered is resolved (exact target named)
[ ] the full caller census for list_runs_filtered + matches_index_meta is enumerated
[ ] the canonical tool_kind field + the correct filtering layer are decided and justified
[ ] the batch_label persistence contract (where readers expect it) is pinned to file:line
[ ] the BR-004 dedup verdict is recorded
[ ] the BR-002B patch plan is concrete (files + functions + per-file additive change) with a named
    saw_lab + rmos/runs_v2 regression set
[ ] owner authorization for BR-002B is recorded
```

Any unchecked box → BR-002B is not authorized; return to BR-002A.

### Outline

Authorized **only after** the checklist above is fully satisfied. Then:

- add `batch_label` (and `tool_kind` if the proof requires) to the saw_lab artifact storage path, in the
  representation §3.6 established;
- add `tool_kind` through the **canonical** `runs_v2` filtering path decided in §3.4, preserving every
  caller from the §3.2 census;
- remove the three xfail markers (`test_saw_lab_endpoint_smoke.py:24,30`, `test_rmos_endpoint_smoke.py:21`);
- run the broad `saw_lab` + `rmos/runs_v2` regression suites (not just the smoke tests);
- update [BACKLOG_ADJUDICATION_LEDGER.md](BACKLOG_ADJUDICATION_LEDGER.md),
  [REPOSITORY_DEFECT_REGISTER.md](REPOSITORY_DEFECT_REGISTER.md), and
  [REMEDIATION_EXECUTION_QUEUE.md](REMEDIATION_EXECUTION_QUEUE.md) — resolving ledger items
  BR-001/BR-002/BR-004 (living-ledger burn-down, charter §5).
