# Remediation Status — March 13, 2026

> **Generated:** March 13, 2026
> **Purpose:** Single source of truth for remediation status. Supersedes conflicting metrics in older documents.

---

## Verified Codebase Metrics

| Metric | Actual Value | Notes |
|--------|--------------|-------|
| Python files | **1,095** | in `services/api/app/` |
| Files >500 LOC | **18** | (was claimed 0-16 in various docs) |
| Broad `except Exception` | **315** | (was claimed 602) |
| Route decorators | **715** | `@app.get/post/put/delete/patch` |
| Router files | **54** | (was claimed 127-132) |
| Total tests | **2,819** | pytest --collect-only |
| Test coverage | **21%** | pytest-cov |

---

## Status Summary: 31 Tracked Efforts

| Status | Count | Items |
|--------|-------|-------|
| ✅ DONE | 16 | #1, #2, #4, #5, #6, #9, #10, #11, #12, #14, #16, #18, #19, #20, #23, #24, #28, #29, #30, #31 |
| 🟡 PARTIAL | 12 | #3, #7, #8, #13, #15, #17, #21, #22, #25, #27 |
| ❌ NOT STARTED | 3 | #26 (4 frontend TODOs) |

---

## Effort Details

### ✅ DONE (16 items)

| # | Effort | Evidence |
|---|--------|----------|
| 1 | Exception Hardening — bare `except:` | 97→0 bare catches (6e397cb6) |
| 2 | God-Object Decomposition | Most >500 LOC files decomposed to subdirs |
| 4 | Stub Endpoints wiring | 69 stubs wired to real implementations |
| 5 | Instrument Build Gaps | 67/113 resolved, critical DXFs done |
| 6 | Vue Component Decomposition | 24+ components decomposed |
| 9 | Frontend Test Coverage | 52 tests added (38038ade) |
| 10 | Bandit Security Findings | XML fixed with defusedxml |
| 11 | Vulture Dead Code | 15 imports removed |
| 12 | Radon Complexity | Baselined (avg A grade) |
| 14 | Singleton Store Refactor | Resolved (c79dd1a7) |
| 16 | CNC Safety Fail-Closed | Resolved (6f86018b) |
| **18** | **Agentic Spine** | **DONE: `IMPLEMENTED = True` in all modules, 773+ lines real code, 14 tests** |
| 19 | SAW_LAB Learning Pipeline | Intentional disable, documented |
| 20 | RMOS v1→v2 migration | v2 default, v1 retained for 5 files by design |
| 23 | Broken CI workflows | Resolved (6d21e96b) |
| 24 | Phantom references | Resolved (ba9db4b6) |
| 28 | Route analytics middleware | Resolved (c4a4788f) |
| 29 | Bare `pass` in except blocks | Resolved (75907e0f) |
| 30 | Secrets documentation | Resolved (4a73ecc4) |
| 31 | data_registry orphan | Module exists, skip marker removed |

### 🟡 PARTIAL (12 items)

| # | Effort | Status | Remaining Work |
|---|--------|--------|----------------|
| 3 | Router Consolidation | 54 router files | Target <50 |
| 7 | Score 7 Plan | ~30% done | Phases 1.4, 2.x, 3.x, 4.x |
| 8 | Vectorizer Upgrade | 0/3 features | Parametric, multi-page, neural |
| 13 | File Size Baseline | 18 files >500 LOC | Target <10 |
| 15 | Tailwind/UX Fixes | Tailwind fixed | Modal/toast unification pending |
| 17 | Phase 2/3 SaaS | 3.1 Auth done | 3.2-3.6 not started |
| 21 | Skipped tests | 1/9 fixed | 8 intentional skips |
| 22 | NotImplementedError funcs | pipeline_ops fixed | archtop bridge/saddle remain |
| 25 | _experimental/ modules | 8+ half-built | Low priority |
| 27 | blueprint-import service | Code exists | No CI, no integration |

### ❌ NOT STARTED (3 items)

| # | Effort | Impact |
|---|--------|--------|
| 26 | 4 Frontend TODOs | PDF export, DXF export, risk override, job nav |

---

## Critical Corrections to Other Documents

### UNFINISHED_REMEDIATION_EFFORTS.md
- **Line 5**: Says "5 major efforts remaining" — should be "16 DONE, 12 PARTIAL, 3 NOT STARTED"
- **Line 56 (Item #18)**: Says `IMPLEMENTED = False` — WRONG. All Agentic Spine modules have `IMPLEMENTED = True` with 773+ lines of real code and 14 tests.
- **Line 82**: Says 602 broad exceptions — actual is **315**
- **Line 124**: Says 132 router files — actual is **54**

### REMEDIATION_PLAN.md / REMEDIATION_PLAN_v2.md
- Outdated February 2026 snapshots
- Metrics are stale (claimed 0 files >500 LOC, actual is 18)
- Mark as superseded by this document

### REVIEW_REMEDIATION_PLAN.md
- Says 602 exceptions — actual is **315**
- Says 1,004 route decorators — actual is **715**

---

## Agentic Spine Verification (Item #18)

**STATUS: ✅ DONE** — NOT stubs as previously documented.

| File | Lines | IMPLEMENTED | Key Functions |
|------|-------|-------------|---------------|
| `replay.py` | 219 | `True` | `load_events()`, `run_shadow_replay()`, `group_by_session()`, `select_moment_with_grace()` |
| `moments.py` | 149 | `True` | `detect_moments()` with real detection logic |
| `policy.py` | 167 | `True` | `decide()`, UWSM policy decisions |
| `schemas.py` | 141 | — | Pydantic models (DetectedMoment, UWSMSnapshot, etc.) |
| `__init__.py` | 97 | — | Re-exports |
| **Total** | **773** | | |

**Test file:** `tests/test_agentic_spine.py` — 253 lines, 14 tests, all passing.

---

## Priority Actions

| Priority | Effort | Est. Hours |
|----------|--------|------------|
| P0 | #15 — Modal/toast UX unification | 4-8 |
| P1 | #3 — Router consolidation (54→<50) | 4-8 |
| P1 | #13 — File size reduction (18→<10) | 8-16 |
| P2 | #7 — Score 7 Plan phases | 40+ |
| P2 | #17 — Phase 2/3 SaaS (3.2-3.6) | 80+ |
| P3 | #8 — Vectorizer features | 20-40 |
| P3 | #26 — 4 Frontend TODOs | 8-16 |

---

## Documents Superseded

This document supersedes conflicting information in:
1. `REMEDIATION_PLAN.md` — February 2026 snapshot
2. `REMEDIATION_PLAN_v2.md` — February 2026 snapshot
3. `REVIEW_REMEDIATION_PLAN.md` — Outdated metrics

`UNFINISHED_REMEDIATION_EFFORTS.md` remains the primary tracking document but requires corrections noted above.
