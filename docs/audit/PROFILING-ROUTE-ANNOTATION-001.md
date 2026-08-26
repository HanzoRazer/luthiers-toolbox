# PROFILING-ROUTE-ANNOTATION-001

**Status:** FIXED at the decorator (2026-08-26)
**Class:** RUNTIME_UNREACHABLE / DECORATOR-ANNOTATION RESOLUTION
**Discovered:** RMOS-CONVERGE-001B-B2 (PR #322), evidence-only HOLD
**Fixed:** `@safety_critical` now evaluates postponed annotations against the
wrapped function's module before FastAPI sees the wrapper.

## Symptom

```text
POST /api/cam/profiling/gcode
→ 422 {"detail":[{"type":"missing","loc":["query","req"],"msg":"Field required"}]}
```

The handler never ran. `@safety_critical` never ran. No G-code, no run, no
audit trail. FastAPI rejected the request during parameter binding.

Once binding was restored, the profiling and binding handlers then crashed
on constructor kwargs that did not exist on the generator dataclasses
(`max_stepdown_mm`, `contour=`, `body_outline=`). Those adapters are mapped
onto the real field names in this fix so a valid JSON body is not a 500.

## Mechanism

1. `from __future__ import annotations` stores `req: ProfileRequest` as the
   string `'ProfileRequest'` (PEP 563).
2. `@safety_critical` wraps with `functools.wraps` and copied
   `inspect.signature(func)` onto the wrapper. The copied `Parameter.annotation`
   was still that string.
3. FastAPI evaluates string annotations against the *callable's* `__globals__`.
   The wrapper is defined in `app/core/safety.py`, which does not contain
   `ProfileRequest`.
4. Resolution fails. FastAPI falls back to a required query parameter named
   `req`. A JSON body is ignored. 422.

`functools.wraps` already copies `__module__` from the original function. That
is not enough: FastAPI uses `__globals__`, which always points at the module
that *defined* the wrapper.

## Why some siblings survived

| route | why it survived |
|---|---|
| retract `/gcode` | parameters are builtin scalars (`str`, `float`) — resolvable in any module |
| drilling modal `/gcode` | `req: DrillReq = Body(...)` — explicit `Body()` forces body binding |
| profiling `/gcode` | bare Pydantic annotation, postponed — **failed** |

## Bounded census (source-verified, same three conditions)

Any `@safety_critical` FastAPI route that combines postponed annotations with a
bare Pydantic body parameter (no `Body(...)`) was a candidate. Confirmed:

| module | endpoint | artifact |
|---|---|---|
| `cam/routers/profiling/profile_router.py` | `POST /gcode` | G-code |
| `cam/routers/binding/binding_router.py` | `POST /channel/gcode`, `POST /purfling/gcode` | G-code |
| `cam/routers/vcarve/production_router.py` | `POST /gcode` | G-code |
| `art_studio/inlay_router.py` | `POST /export-gcode` | G-code |
| `routers/radius_dish_router.py` | `POST /generate-gcode` | G-code |
| `cam/routers/utility/optimization_router.py` | `POST /opt/feeds-speeds` | JSON feeds/speeds |

`drill_pattern_router.py` uses `@safety_critical` and bare Pydantic params but
does **not** postpone annotations, so FastAPI already saw real classes.

PR #322 classified V-carve production as a live ungoverned emitter. If the
production route matches this pattern, that "live" reading was source-level,
not runtime — the same 422 would apply. Binding was similarly listed as BYPASS
from source. This fix restores the routes as they were written.

## Fix

Evaluate annotations against the original function before attaching them to
the wrapper:

```python
wrapper.__signature__ = inspect.signature(func, eval_str=True)
wrapper.__annotations__ = get_type_hints(func, include_extras=True)
```

`eval_str=True` (Python 3.10+) uses `func.__globals__`. FastAPI then sees
classes, not strings, and binds Pydantic models as request bodies.

This is the decorator's existing contract — "preserve function signature for
FastAPI" — made true under PEP 563. It is not an RMOS evaluator and does not
take a capability offline.

**Adapter follow-through.** `profile_router.py` and `binding_router.py` now
map HTTP field names onto the generator dataclasses (`stepdown_mm`,
`feed_rate_xy`, `outline=`, …) the same way `intent_adapter.py` already did
for the canonical lane. Without that, restoring binding turned a 422 into a
500.

## What this is not

- **Not RMOS convergence.** Profiling, binding, and V-carve production still
  have no authorized evaluator on these sibling routes. The canonical intent
  lanes remain the governed path. 001B-B2's HOLD on *gating* those siblings
  is unchanged.
- **Not a `Body(...)` sweep.** Adding `Body()` to each router would hide the
  decorator bug and miss the next route that uses the same pattern.
- **Not the OpenAPI `class-not-fully-defined` failure** on
  `test_simple_gcode_openapi_declares_query_params_not_a_body`. That error is
  raised while generating schema for an unrelated DXF body-solve upload model
  (`body_solver_router.py`) and reproduces on `main` without this change.

## Witnesses

`services/api/tests/test_safety_critical_annotation_binding.py`

- Mini-app: JSON body binds; missing body is `loc=['body', ...]`, never
  `loc=['query', 'req']`.
- OpenAPI for the mini-app declares `requestBody`, not a `req` query param.
- Builtin scalars still bind as query (retract survivor).
- Fail-closed re-raise is unchanged.
- Decorated production endpoints keep evaluated Pydantic types on `req` /
  `body` after wrapping.
