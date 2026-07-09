# WP-002-A — Deprecated Consolidation Shim Reconfirmation (live `main`)

**Date:** 2026-07-09
**Base:** `origin/main` @ `fc95cfc1`
**Type:** read-only evidence audit (docs only)
**Authority:** reconfirms the Consolidation Lab **Investigation 007** snapshot census
against current live `main`, as required by the WP-002 adjudication record's
`no-retirement-before-import-census` guard.

> **This document changes no source, no routes, and retires nothing.** It records
> current facts so the WP-002 adjudication can eventually decide (Complete Sprint /
> Keep / Archive / Retire) per shim. **No disposition is made here.**

---

## Result: no drift

The live-`main` deprecated-shim landscape is **identical** to the Investigation 007
snapshot. All counts below were re-derived on `fc95cfc1`.

| Metric | Investigation 007 (snapshot) | Live `main` (`fc95cfc1`) | Drift |
| ------ | :--------------------------: | :----------------------: | :---: |
| Total `*_consolidated_router.py` | 15 | 15 | none |
| Explicit `DEPRECATED` shims | 3 | 3 | none |
| Ambiguous (thin wrapper, no marker) | 2 | 2 | none |
| Canonical consolidated routers | 10 | 10 | none |

---

## The three deprecated compatibility shims (live `main`)

| Shim | Importers | Importer | Runtime-reachable | Replacement modules present | Direct test ref |
| ---- | :-------: | -------- | :---------------: | :-------------------------: | :-------------: |
| `cam/routers/drilling/drilling_consolidated_router.py` | **1** | `cam/routers/drilling/__init__.py` | yes (via `__init__`) | yes — `drill_modal_router`, `drill_pattern_router` | 0 |
| `routers/probe/probe_consolidated_router.py` | **1** | `routers/probe/__init__.py` | yes (mounted as `probe_router`) | yes — `boss/corner/pocket/surface_z/vise_square_router` | 0 |
| `routers/retract/retract_consolidated_router.py` | **1** | `routers/retract/__init__.py` | yes (via `__init__`) | yes — `retract_info/apply/gcode_router` | 0 |

Each shim is imported by **exactly one** file — its own package `__init__.py`, which
mounts it. *No-import ≠ safe to remove* is moot here: the shims **are** imported, so
retirement means repointing that `__init__` to the focused sub-modules (adjudication +
implementation work — **not** done here).

---

## Replacement test coverage (007's key unknown → now partial)

Domain-level tests exist for all three shim areas on live `main`:

- **drilling:** `tests/cam/test_drilling_intent_migration.py`, `test_drilling_design_schema.py`,
  `test_drilling_export_lifecycle.py`, `test_drilling_preview_normalization.py`
- **probe:** `tests/test_probe_router.py`, `tests/test_cam_probe_setup_smoke.py`
- **retract:** covered indirectly via CAM intent/migration tests (no dedicated retract-shim test)

**Gap (still open):** these prove the *domains* are exercised, not that each replacement
sub-module's endpoints are covered *after* the shim is repointed. Per-replacement
retirement-safety coverage must be confirmed before any retirement PR.

---

## Focused verification (read-only, Python 3.11)

`pytest tests/test_probe_router.py tests/test_cam_consolidated_endpoint_smoke.py tests/cam/test_drilling_intent_migration.py`
→ **82 passed, 15 failed** (135s).

- The **shim-domain** tests (`test_probe_router`, `test_drilling_intent_migration`) **pass**.
- All **15 failures** are in `test_cam_consolidated_endpoint_smoke.py` for **unrelated**
  endpoints — *toolpath roughing/vcarve/relief* and *photo_batch*. They are **not** in the
  drilling/probe/retract shim domains, and the worktree is unmodified — so they are `main`'s
  **pre-existing baseline**, out of WP-002-A scope. Flagged here for awareness only; not
  addressed by this read-only audit.

---

## Conclusion (evidence only)

- The WP-002 shim evidence is **current** as of `fc95cfc1`: 3 deprecated shims, 1 importer
  each (their package `__init__`), runtime-reachable, replacements present. **No drift** from
  the Investigation 007 snapshot.
- **Remaining gate before retirement:** confirm per-replacement endpoint test coverage for
  each shim (partial today). Until then, `no-retirement-before-import-census` is satisfied but
  the replacement-coverage condition is not.
- **No disposition is authorized.** WP-002 remains blocked; the adjudication gate may now
  reason from current facts, per shim.

_Source: Consolidation Lab Investigation 007 (`investigations/007-deprecated-consolidation-import-census`) — snapshot census this audit reconfirms._
