# BR-001 — Next Remediation Candidate

> The single recommended next implementation target. **This is the evidence packet from which the next
> implementation Dev Order will be written — it is not itself that Dev Order.** Selection follows
> charter §6: verified defect, clear ownership, bounded file impact, known acceptance, no unresolved
> constitutional question, no dependency on unavailable research.

## Candidate: saw_lab / rmos store-layer keyword-argument wiring

Resolves adjudication items **BR-001, BR-002, BR-004** (Wave 1, Rank 1).

### Problem statement

Three saw_lab/rmos API smoke tests are marked `xfail` because the endpoint layer calls store-layer
functions with keyword arguments those functions do not accept, raising `TypeError` (HTTP 500) at
runtime:

1. `store_artifact(..., batch_label=…)` → `app/saw_lab/store.py:16` `store_artifact()` has no
   `batch_label` parameter. (`tests/test_saw_lab_endpoint_smoke.py:30`)
2. `list_runs_filtered(..., tool_kind=…)` → `app/rmos/runs_v2/store_api.py:200` `list_runs_filtered()`
   has no `tool_kind` parameter (a sibling function at `:141` does). (`tests/test_saw_lab_endpoint_smoke.py:24`)
3. RMOS endpoint `store_artifact` bug (`tests/test_rmos_endpoint_smoke.py:21`) — **likely the same root
   as (1)**; confirm and dedup during scoping.

### Why it is next

- **Verified now** by code inspection (missing parameters on current `main` `d716d16`) *and* committed
  xfail tests that assert the exact `TypeError` messages — the strongest evidence class available.
- **Bounded file impact:** `app/saw_lab/store.py`, `app/rmos/runs_v2/store_api.py`, and the endpoint
  callers that pass the kwargs. Small, single-subsystem cluster (store-layer signatures).
- **Known acceptance, built in:** the fix flips three `xfail` markers to passing (or `xpass` → remove
  the markers). No new test design required to prove success.
- **No unresolved constitutional question, no owner decision, no research dependency** — pure defect
  wiring. (Contrast the parked owner-forks BR-018/BR-014/BR-019.)
- **User-facing severity:** each is a 500 on a live endpoint.

### Current evidence

| Bug | Code (current `main`) | Test (xfail) |
| --- | --------------------- | ------------ |
| batch_label | `app/saw_lab/store.py:16` — params: `kind, payload, parent_id, session_id, index_meta, status` (no `batch_label`) | `tests/test_saw_lab_endpoint_smoke.py:30` |
| tool_kind | `app/rmos/runs_v2/store_api.py:200` — no `tool_kind`; sibling at `:141` has it | `tests/test_saw_lab_endpoint_smoke.py:24` |
| rmos store | (confirm shared root with batch_label) | `tests/test_rmos_endpoint_smoke.py:21` |

### Affected subsystem

`saw_lab` + `rmos/runs_v2` store layer and their FastAPI endpoint callers.

### Expected patch boundary

Accept and thread the missing kwargs (`batch_label` into the artifact `payload`/`index_meta` where the
`query_*_by_label` functions already read it; `tool_kind` into the `list_runs_filtered` filter set,
mirroring the sibling function), then flip/remove the three xfail markers. No schema, contract, or route
changes expected. Estimated small (a few functions + call sites).

### Acceptance basis

- `tests/test_saw_lab_endpoint_smoke.py::…` (the two xfail cases) pass without the `xfail` marker.
- `tests/test_rmos_endpoint_smoke.py:21` passes (or is confirmed a duplicate and closed with BR-001).
- No regression in the surrounding saw_lab/rmos smoke suites.
- Router-count / endpoint-truth gates unaffected (no route surface change).

### Unresolved decisions

**None.** This is a decision-free bug fix. (If scoping reveals BR-004 is *not* a duplicate of BR-001,
it remains in-scope as the same bug class in the same pass.)

### Not included

The simulation metrics mismatch (BR-003) and RMOS approve-route wiring (BR-013) are adjacent Wave-1
items but different subsystems/bug classes — they are **not** bundled here, to keep this candidate
bounded.

---

> Handing this to a bounded remediation Dev Order does **not** require the Wave-0 full-suite red-run
> first: this candidate's evidence is self-contained (code inspection + its own xfail tests). The
> Wave-0 run remains recommended to refresh the broader current-red picture.
