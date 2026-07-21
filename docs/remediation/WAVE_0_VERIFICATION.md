# BR-001 — Wave 0 Verification Record

> The current-state test baseline that Wave 0 of the [execution queue](REMEDIATION_EXECUTION_QUEUE.md)
> called for. Turns the ledger's pending live-run note into a recorded result — **with an explicit
> toolchain caveat**.

## Run

| | |
| --- | --- |
| Baseline | `origin/main` `d716d16` |
| Command | `python -m pytest --no-cov -p no:cacheprovider --continue-on-collection-errors` in `services/api` |
| Date | 2026-07-20 |
| Duration | ~96 min |

### Result

```text
21 failed · 8155 passed · 57 skipped · 19 xfailed · 1 xpassed · 0 collection errors
```

## ⚠ Toolchain caveat (read before using this count)

This ran on the **local default toolchain — Python 3.14 / numpy 2.4.2 / current pydantic+starlette** —
**not CI's Python 3.11 stack.** CI could not be reproduced locally this session (Python 3.11 here lacks
`defusedxml` and a live Postgres; Python 3.14 trips a numpy re-import guard under `pytest-cov`, worked
around with `--no-cov`). Therefore:

- The **21** is **not directly comparable** to the 2026-06-29 triage's ~12 reds (CI-equivalent stack on
  the older `0daeab14`).
- Some failures are **toolchain-skew suspects** (newer pydantic/starlette/numpy behavior), not
  necessarily repo reds on CI.
- **The authoritative current-red count must come from the CI stack (Python 3.11).** This local run is
  directional evidence, not the final baseline.

## Failure breakdown

| Cluster | Count | Files | Read |
| ------- | ----- | ----- | ---- |
| **Body-solver** | 17 | `test_body_solver_integration.py` (12), `test_morphology_spine_e2e.py` (4), `test_body_solver_ibg_export_blocked.py` (1) | **likely real** — Starlette-middleware `ExceptionGroup` on body-solver POSTs; maps to unmerged `fix/ci-red-015i-body-geometry-repair` / `015k-body-solver-ibg` branches → **BR-032** |
| **CAM feeds/speeds** | 3 | `test_cam_feeds_speeds_smoke.py` | needs inspection → folded into BR-032's sibling review |
| **OpenAPI schema build** | 1 | `test_openapi.py::test_openapi_schema_builds` | `app.openapi()` raises pydantic error; a field named `validate` shadows `BaseModel.validate` (real smell) but hard-failure likely amplified by newer pydantic → **BR-033** |
| **Stale xfail** | 1 (xpass) | — | an xfail marker now passes; marker cleanup (minor) → **BR-034** |

## Effect on the queue

- **Next candidate unchanged.** The saw_lab/rmos kwarg fix (BR-001/002/004) is **xfailed** (in the 19),
  not among the 21 failures — it remains a bounded, verified, decision-free next target.
- **New Wave-1 item BR-032** (body-solver failure cluster) added — but its first action is to **confirm
  on the CI stack** and **check whether the unmerged 015i/015k branches already resolve it**, before
  authoring a fresh Dev Order. It is *not* a cleaner next candidate than the saw_lab fix (larger,
  unbounded root, CI-confirmation-pending).
- **BR-033** (openapi/`validate` shadow) and **BR-034** (stale xfail) added to the ledger.

## Recommended definitive run

Trigger the suite on the **CI Python 3.11 stack** (docker-compose with Postgres + pinned deps) — e.g.
via CI on a branch that touches `services/api`, or a local 3.11 venv with `requirements.txt` fully
installed — to produce the authoritative red count and separate real reds from toolchain skew.
