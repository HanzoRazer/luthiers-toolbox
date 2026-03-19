# Safety case — Production Shop (Luthiers Toolbox)

**Purpose:** This document states *what* we protect, *how* the system is designed to fail safely, and *what operators and reviewers should verify*. It complements code (`app.core.safety`) and process (tests, preflight, RMOS gates).

**Audience:** Engineers, operators, and auditors reviewing CNC / manufacturing-adjacent features.

**Status:** Living document — update when safety-critical surfaces change.

---

## 1. Scope and assumptions

| In scope | Out of scope (operator / shop responsibility) |
|----------|--------------------------------------------------|
| Server-side feasibility, risk bucketing, and G-code–related computation exposed by the API | Physical machine limits, fixture clamping, spindle/brake interlocks |
| Software preflight and validation of exported machine instructions | Shop floor procedures, training, PPE |
| Traceability: logging and explicit failure modes for marked paths | Third-party controller bugs or post-processor edits after export |

**Assumption:** Downstream CAM and machines treat exported data as *advisory* until verified with shop procedures and simulation where applicable.

---

## 2. Safety goals (informal)

1. **No silent success on bad physics** — Unexpected errors in feasibility / G-code paths must not be converted into “GREEN” or empty success without an explicit, reviewable decision.
2. **Fail closed** — Prefer explicit errors, blocked exports, or degraded modes that are visible over ambiguous OK responses.
3. **Auditability** — Safety-critical entry points are identifiable in code and logs.

---

## 3. Primary mechanisms (implementation)

### 3.1 `@safety_critical` (canonical: `app.core.safety`)

Functions that affect **feasibility**, **G-code generation**, **feeds/speeds**, or **risk classification** should be considered for this decorator.

**Guarantees (by design):**

- Unhandled exceptions are logged at **CRITICAL** with traceback, then **re-raised** (never swallowed).
- Wrappers expose `_is_safety_critical` for tooling / fence checks.
- Optional **DEBUG** entry/exit logging when `SAFETY_DEBUG=1`.

**Import (preferred):**

```python
from app.core.safety import safety_critical, is_safety_critical
```

Legacy re-export: `app.safety` → same symbols.

### 3.2 RMOS and decision authority

RMOS (run / manufacturing operations safety) is the **decision authority** for operational risk signals. Broad `except Exception` handlers in this area are a known hazard: they can mask faults and skew GREEN/YELLOW/RED outcomes.

**Expectation:** Safety-critical functions in the feasibility chain use narrow exception handling and/or `@safety_critical` where appropriate; each broad handler should be justified and reviewed.

### 3.3 Startup and strict modes

- Startup validation should **fail fast** if required safety-related modules cannot load (see `validate_startup()` and related boot checks).
- **`RMOS_STRICT_STARTUP=1`** (when used) requires safety modules to be present — avoids running in a partially disabled safety configuration without explicit opt-out.

### 3.4 Preflight and export gates

CAM / DXF / toolpath flows should enforce **preflight** and **approval or simulation gates** where the product defines them (e.g. export blocked until validated). These gates are part of the *software* safety case, not a substitute for machine-side interlocks.

---

## 4. Verification (what to run / check)

| Check | Intent |
|-------|--------|
| API / contract tests touching RMOS, CAM, preflight | Regression on fail-closed behavior and response shapes |
| Coverage on safety-tagged modules | Ensures tests exercise decorated paths where metrics are tracked |
| Manual: attempt export without preflight / with invalid geometry | UI/API should surface explicit errors, not silent files |

*Exact commands depend on repo `Makefile` / CI — align with `make api-verify` or the current GitHub workflow.*

---

## 5. Known residual risks (honest list)

1. **Incomplete decoration** — Not every function in long call chains may yet be `@safety_critical`; fence checks and reviews should close gaps over time.
2. **Broad exception handlers** — Any remaining `except Exception` on hot paths needs classification (narrow, re-raise, or document).
3. **Environment drift** — Missing dependencies or misconfigured strict flags can change behavior at startup; CI should match production expectations.
4. **Human factors** — Operators can override or bypass UI warnings; training and shop procedure remain essential.

---

## 6. Change control

When adding or changing:

- New G-code or feasibility endpoints,
- New export formats,
- Changes to RMOS risk semantics,

…update this document **and** add or extend tests that prove the intended failure mode.

---

## 7. References (in-repo)

- `services/api/app/core/safety.py` — `@safety_critical` implementation
- `services/api/app/safety/__init__.py` — backward-compatible re-export
- `docs/PRODUCT_SCOPE.md` — core vs experimental boundaries (if present)
- `docs/reviews/DESIGN_REVIEW_2026-02-22.md` — historical safety discussion
