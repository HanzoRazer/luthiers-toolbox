# WP-002-B — Deprecated Shim Replacement Coverage (live `main`)

**Date:** 2026-07-10
**Base:** `origin/main` @ `d133a054`
**Type:** read-only evidence audit (docs only)
**Purpose:** close the one remaining WP-002 evidence gate — *replacement test coverage* —
by mapping each deprecated shim's replacement-module endpoints to tests and running them.

> **This document changes no source, no routes, and retires nothing.** It records whether
> the replacement endpoints are tested enough to make future retirement safe. It may
> conclude *coverage sufficient / partial / insufficient* — it may **not** decide
> *retire / keep / complete-sprint*. Those remain **WP-002 adjudication** outcomes.

---

## Verdict summary (evidence only)

| Shim | Replacement endpoints | Covered | Test result | Evidence verdict |
| ---- | :-------------------: | :-----: | :---------: | ---------------- |
| **drilling** | 4 | 3 / 4 | PASS | **Sufficient** (1 trivial gap: `/pattern/info` metadata GET) |
| **probe** | 15 | 15 / 15 | PASS | **Sufficient** |
| **retract** | 8 | 8 / 8 | PASS | **Sufficient** |

**Focused test run (read-only, Python 3.11):**
`pytest test_cam_drilling_smoke.py test_probe_router.py test_retract_endpoint_smoke.py`
→ **99 passed, 0 failed** (152s). Drilling `/pattern/gcode` additionally exercised by
`test_drilling_intent_migration.py` and `e2e_cam_system.py`.

**Overall:** replacement coverage is **sufficient** to support future retirement of all
three shims, with **one trivial noted gap** (drilling `/pattern/info`). The WP-002
replacement-coverage gate is satisfied (see caveat).

---

## Coverage matrix

### drilling — `drilling_consolidated_router` → `drill_modal_router`, `drill_pattern_router`

| Endpoint | Replacement module | Mapped test | Result | Status |
| -------- | ------------------ | ----------- | :----: | ------ |
| `POST /api/cam/drilling/gcode` | drill_modal | `test_cam_drilling_smoke.py` (G81, G83) | PASS | Covered |
| `GET /api/cam/drilling/info` | drill_modal | `test_cam_drilling_smoke.py` | PASS | Covered |
| `POST /api/cam/drilling/pattern/gcode` | drill_pattern | `test_drilling_intent_migration.py:203`, `e2e_cam_system.py:409` | PASS¹ | Covered |
| `GET /api/cam/drilling/pattern/info` | drill_pattern | — | — | **GAP** (trivial — metadata GET) |

¹ `test_drilling_intent_migration.py` passed in this pass's broader run and in WP-002-A.

### probe — `probe_consolidated_router` → boss / corner / pocket / surface_z / vise_square

| Endpoint (×5 probe types) | Mapped test | Result | Status |
| ------------------------- | ----------- | :----: | ------ |
| `POST /api/probe/{type}/gcode` | `test_probe_router.py` | PASS | Covered |
| `POST /api/probe/{type}/gcode/download` | `test_probe_router.py` | PASS | Covered |
| `POST /api/probe/{type}/gcode/download_governed` | `test_probe_router.py` | PASS | Covered |

`{type}` ∈ {boss, corner, pocket, surface_z, vise_square} — all five present in
`test_probe_router.py`. **15 / 15 endpoints covered.**

### retract — `retract_consolidated_router` → retract_info / retract_apply / retract_gcode

| Endpoint | Replacement module | Mapped test | Result | Status |
| -------- | ------------------ | ----------- | :----: | ------ |
| `GET /api/cam/retract/strategies` | retract_info | `test_retract_endpoint_smoke.py` | PASS | Covered |
| `POST /api/cam/retract/estimate` | retract_info | `test_retract_endpoint_smoke.py` | PASS | Covered |
| `POST /api/cam/retract/apply` | retract_apply | `test_retract_endpoint_smoke.py` | PASS | Covered |
| `POST /api/cam/retract/lead_in` | retract_apply | `test_retract_endpoint_smoke.py` | PASS | Covered |
| `POST /api/cam/retract/gcode` | retract_gcode | `test_retract_endpoint_smoke.py` | PASS | Covered |
| `POST /api/cam/retract/gcode/download` | retract_gcode | `test_retract_endpoint_smoke.py` | PASS | Covered |
| `POST /api/cam/retract/gcode_governed` | retract_gcode | `test_retract_endpoint_smoke.py:622` | PASS | Covered |
| `POST /api/cam/retract/gcode/download_governed` | retract_gcode | `test_retract_endpoint_smoke.py:709` | PASS | Covered |

---

## What this means for WP-002 (evidence, not decision)

- The replacement endpoints reached *through* each shim are the **same paths** the focused
  sub-modules own; they are exercised by passing TestClient tests. So repointing each
  package `__init__` from the shim to its sub-modules would keep tested, unchanged endpoints.
- **Trivial residual:** drilling `/pattern/info` (a metadata GET) has no explicit assertion.
  Adding one line to `test_cam_drilling_smoke.py` would make drilling 4/4. This is the only
  gap and is low-risk (metadata only).
- **Boundary:** this closes the WP-002 *replacement-coverage* evidence item. It does **not**
  authorize retirement and selects **no disposition** — the adjudication gate decides
  *Complete Sprint / Keep* per shim, now with complete evidence.

_Source: Consolidation Lab Investigation 007 + WP-002 adjudication record; reconfirmed live
(`WP_002_SHIM_RECONFIRMATION.md`, PR #209). This audit supplies the final evidence item._
