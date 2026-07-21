# BR-001 — Repository Defect Register

> **Only currently verified defects.** No enhancements, no speculative concerns, no unavailable
> research. Every entry links to its [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md) record and
> carries current reproduction evidence (charter §4 · Disposition discipline).

## What qualifies as a defect here

Implemented or promised behavior that is **incorrect, broken, unsafe, or inconsistent with its
governing contract** — and can be reproduced **now** (failing test / deterministic command / traceable
code-path inspection / contract mismatch / documented runtime observation / explicit evidence that a
promised implementation is absent).

- A missing capability that was never approved is **not** a defect → `ENHANCEMENT`.
- Authorized-but-incomplete work is **not** a defect → `UNFINISHED_SPRINT_WORK`.
- A historical defect that cannot be reproduced now → `STALE_OR_NOT_REPRODUCIBLE` (not listed here).

## Record schema

```text
Defect ID                  (= adjudication BR-NNN)
Title
Subsystem
Reproduction basis         (the current evidence — REQUIRED)
Observed vs expected
Governing contract         (what it violates, if any)
Severity / safety / data-integrity impact
Regression risk
Estimated fix size
Dependencies / blockers
Readiness
```

## Register

Verified against `origin/main` `d716d16` (2026-07-20). These entries (BR-001..BR-004) are grounded in
**code inspection and/or committed xfail tests** that assert the bug — the store-layer signatures and
their tests are the reproduction basis. The Wave 0 full-suite run was **subsequently performed** and
separately recorded ([WAVE_0_VERIFICATION.md](WAVE_0_VERIFICATION.md), 2026-07-20); it surfaced
additional items (BR-032/033/034) and did not invalidate these four. (BR-001..004 are xfail-marked, so
they do not appear among the Wave 0 failures.)

### BR-001 · `store_artifact()` rejects `batch_label`
- **Subsystem:** saw_lab
- **Reproduction basis:** `app/saw_lab/store.py:16` — `store_artifact(*, kind, payload, parent_id,
  session_id, index_meta, status)` has **no `batch_label` parameter**; committed xfail
  `tests/test_saw_lab_endpoint_smoke.py:30` reason = *"store_artifact() got unexpected keyword argument
  'batch_label'"*. Code inspection confirms the missing param on current `main`.
- **Observed vs expected:** endpoint call passing `batch_label=` raises `TypeError` (500) vs. should
  store/index the batch label (the value is used by `query_*_by_label` functions in the same module).
- **Severity:** high (endpoint 500) · **Regression risk:** low · **Fix size:** small (one function +
  caller). · **Readiness:** ready.

### BR-002 · `list_runs_filtered()` rejects `tool_kind`
- **Subsystem:** rmos/runs_v2
- **Reproduction basis:** `app/rmos/runs_v2/store_api.py:200` — `list_runs_filtered()` accepts many
  filters but **not `tool_kind`** (a *different* function at `:141` does); committed xfail
  `tests/test_saw_lab_endpoint_smoke.py:24` reason = *"list_runs_filtered() got unexpected keyword
  argument 'tool_kind'"*.
- **Observed vs expected:** saw_lab listing passing `tool_kind=` raises `TypeError` vs. should filter by
  tool kind. · **Severity:** high · **Fix size:** small · **Readiness:** ready.

### BR-003 · Simulation metrics router/schema mismatch
- **Subsystem:** simulation
- **Reproduction basis:** committed xfail `tests/test_simulation_endpoint_smoke.py:28` (applied to 8
  metrics tests) reason = *"router/schema mismatch in metrics endpoint"*.
- **Observed vs expected:** metrics endpoint responses do not match the declared schema. · **Severity:**
  medium · **Fix size:** small–medium (needs endpoint/schema inspection to bound exactly) · **Readiness:**
  ready.

### BR-004 · RMOS endpoint `store_artifact` bug
- **Subsystem:** rmos
- **Reproduction basis:** committed xfail `tests/test_rmos_endpoint_smoke.py:21`. **Possible shared root
  with BR-001** (`store_artifact` kwarg handling) — dedup to be confirmed when the fix is scoped.
- **Severity:** medium · **Readiness:** ready (verify duplicate relationship first).

> Not listed here (correctly excluded): BR-024 (R2000 `ezdxf.new` literal call refactored into
> `dxf_compat` — **`SUPERSEDED` into BR-018**, which owns the open R2000 policy question; not a
> currently-reproducible defect and not claimed "resolved"); disconnected UI surfaces BR-023/BR-030 (`ENHANCEMENT`, never
> approved); BR-019 auth/DB stubs (`OWNER_DECISION_REQUIRED` — scope question, not yet a contract-broken
> defect). Full reasoning in the [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md).
