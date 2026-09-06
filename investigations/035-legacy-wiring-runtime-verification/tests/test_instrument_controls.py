"""IW-01..IW-08 instrument controls for Investigation 035.

These tests prove the witness harness, not production D-status.
They do not import the full application except IW-03 (optional / expensive).

Which control covers which mechanism — read this before citing a control as
evidence for a claim:

  IW-01 / IW-02  install_spies (module-level patch). This is the mechanism
                 that reported 0 for most headline labels, i.e. the *control*,
                 not the mechanism the findings rest on.
  IW-06          bind_spies_to_fastapi_routes (APIRoute.handle). This IS the
                 mechanism every S1-S5 handler-identity finding rests on, so it
                 carries both a positive and a negative control.
  IW-07          the handle hook refuses to double-wrap (count inflation).
  IW-08          install_spies is all-or-nothing (no leak into later specimens).
  IW-04 / IW-05  classification-vocabulary controls. These exercise NO harness
                 code; they pin the D3/D5 reading conventions in executable
                 form. Do not cite them as harness validation.
"""
import sys
from types import ModuleType

import pytest

from runtime_reachability_witness import (
    CallCounter,
    SpySpec,
    bind_spies_to_fastapi_routes,
    install_spies,
    restore_fastapi_endpoints,
    stop_spies,
)

_FIXTURE_MODULES = ("iw_fixture_module_a", "iw_fixture_module_b")


@pytest.fixture(autouse=True)
def _no_sys_modules_leak():
    """Fixture modules must not outlive the test that created them.

    Leaving them in sys.modules lets one control silently satisfy the next.
    """
    yield
    for name in _FIXTURE_MODULES:
        sys.modules.pop(name, None)


def _make_bound_pair():
    """module_a.function imported into module_b.bound_function."""
    module_a = ModuleType("iw_fixture_module_a")

    def function(x):
        return x * 2

    module_a.function = function

    module_b = ModuleType("iw_fixture_module_b")
    # Binding at import time (the Vectorizer-witness hazard).
    module_b.bound_function = module_a.function

    sys.modules["iw_fixture_module_a"] = module_a
    sys.modules["iw_fixture_module_b"] = module_b
    return module_a, module_b


def test_iw01_bound_name_spy_fires():
    """IW-01 — spy on module_b.bound_function fires when production calls it."""
    module_a, module_b = _make_bound_pair()
    counter = CallCounter()
    specs = [SpySpec("iw_fixture_module_b", "bound_function", "bound")]
    patches = install_spies(specs, counter)
    try:
        assert module_b.bound_function(3) == 6
    finally:
        stop_spies(patches)
    assert counter.counts["bound"] == 1


def test_iw02_wrong_namespace_spy_may_not_fire():
    """IW-02 — spy on module_a.function after binding may not fire.

    module_b.bound_function holds the original function object. Patching
    module_a.function replaces the name on module_a only. Callers that
    already bound the original still invoke the unbound original.
    """
    module_a, module_b = _make_bound_pair()
    counter = CallCounter()
    specs = [SpySpec("iw_fixture_module_a", "function", "source")]
    patches = install_spies(specs, counter)
    try:
        result = module_b.bound_function(3)
    finally:
        stop_spies(patches)
    assert result == 6
    assert counter.counts.get("source", 0) == 0


def test_iw04_fail_closed_guard_is_not_automatically_defect():
    """IW-04 — intended optional component unavailable → reject / fail closed.

    Witness records that the guard ran and the intended optional impl did not.
    That pattern is not automatically D3.
    """
    intended_calls = {"n": 0}
    guard_calls = {"n": 0}

    def intended():
        intended_calls["n"] += 1
        return "real"

    def guard():
        guard_calls["n"] += 1
        raise RuntimeError("optional component unavailable; fail closed")

    optional_available = False
    with pytest.raises(RuntimeError, match="fail closed"):
        if not optional_available:
            guard()
        else:
            intended()
    assert guard_calls["n"] == 1
    assert intended_calls["n"] == 0
    # Classification reminder (asserted as documentation, not D-status):
    assert optional_available is False


def test_iw05_placeholder_substitution_distinguished_from_intended():
    """IW-05 — successful path returns placeholder while intended does not fire."""

    def intended():
        return {"source": "intended", "value": 42}

    def placeholder():
        return {"source": "placeholder", "value": None}

    use_placeholder = True
    intended_fired = {"n": 0}
    placeholder_fired = {"n": 0}

    def wrap(fn, box):
        def _inner():
            box["n"] += 1
            return fn()

        return _inner

    intended_w = wrap(intended, intended_fired)
    placeholder_w = wrap(placeholder, placeholder_fired)
    result = placeholder_w() if use_placeholder else intended_w()
    assert result["source"] == "placeholder"
    assert placeholder_fired["n"] == 1
    assert intended_fired["n"] == 0


def test_call_counter_wraps_original_return():
    counter = CallCounter()
    def add(a, b):
        return a + b
    wrapped = counter.wrap("add", add)
    assert wrapped(2, 3) == 5
    assert counter.counts["add"] == 1


# ---------------------------------------------------------------------------
# IW-06..IW-08 — controls for the mechanism the findings actually rest on
# ---------------------------------------------------------------------------


def _tiny_app():
    """Two routers, one module, so a handle-hook spy has something to match."""
    from fastapi import APIRouter, FastAPI

    def reached_handler():
        return {"who": "reached"}

    def never_handler():
        return {"who": "never"}

    router = APIRouter()
    router.add_api_route("/reached", reached_handler, methods=["GET"])
    router.add_api_route("/never", never_handler, methods=["GET"])

    app = FastAPI()
    app.include_router(router, prefix="/iw06")
    return app, reached_handler, never_handler


def test_iw06_handle_hook_counts_only_the_dispatched_endpoint():
    """IW-06 — APIRoute.handle spy: positive AND negative in one request.

    Closes the gap EQ-A01-035-12 previously cited IW-01/IW-02 for. IW-01/IW-02
    validate module patching; they say nothing about the handle hook, which is
    what produced every S1-S5 handler-identity number.
    """
    from fastapi.testclient import TestClient

    app, reached, never = _tiny_app()
    counter = CallCounter()
    specs = [
        SpySpec(reached.__module__, reached.__name__, "reached"),
        SpySpec(never.__module__, never.__name__, "never"),
    ]
    restored = bind_spies_to_fastapi_routes(app, specs, counter)
    try:
        with TestClient(app) as client:
            response = client.get("/iw06/reached")
    finally:
        restore_fastapi_endpoints(restored)

    assert response.status_code == 200
    # Positive: the dispatched endpoint is counted exactly once.
    assert counter.counts["reached"] == 1
    # Negative: a mounted-but-not-dispatched endpoint stays at 0, so a 0 in a
    # witness is evidence of non-dispatch and not of a mis-aimed spy.
    assert counter.counts["never"] == 0
    assert any(e.get("via") == "APIRoute.handle" for e in counter.events)


def test_iw06b_handle_hook_does_not_alter_the_response():
    """IW-06b — the hook is observational; it must not change status or body.

    The voided first IW-03 attempt wrapped route.endpoint and turned a 200 into
    a 422. This pins that the accepted mechanism does not repeat that.
    """
    from fastapi.testclient import TestClient

    app, reached, _never = _tiny_app()
    with TestClient(app) as client:
        baseline = client.get("/iw06/reached")

    counter = CallCounter()
    specs = [SpySpec(reached.__module__, reached.__name__, "reached")]
    restored = bind_spies_to_fastapi_routes(app, specs, counter)
    try:
        with TestClient(app) as client:
            hooked = client.get("/iw06/reached")
    finally:
        restore_fastapi_endpoints(restored)

    assert (baseline.status_code, baseline.json()) == (hooked.status_code, hooked.json())
    assert counter.counts["reached"] == 1


def test_iw07_handle_hook_refuses_to_double_wrap():
    """IW-07 — a leaked hook must fail loudly, not silently double-count."""
    app, reached, _never = _tiny_app()
    specs = [SpySpec(reached.__module__, reached.__name__, "reached")]
    first = bind_spies_to_fastapi_routes(app, specs, CallCounter())
    try:
        with pytest.raises(RuntimeError, match="double-wrap"):
            bind_spies_to_fastapi_routes(app, specs, CallCounter())
    finally:
        restore_fastapi_endpoints(first)

    # Restore must clear the marker so the next specimen can install cleanly.
    again = bind_spies_to_fastapi_routes(app, specs, CallCounter())
    restore_fastapi_endpoints(again)


def test_iw08_install_spies_is_all_or_nothing():
    """IW-08 — a failing spec must not leave earlier patches started.

    A leak here would silently contaminate every specimen collected after the
    failure in the same process.
    """
    module_a, module_b = _make_bound_pair()
    original = module_a.function
    counter = CallCounter()
    specs = [
        SpySpec("iw_fixture_module_a", "function", "good"),
        SpySpec("iw_fixture_module_a", "attr_that_does_not_exist", "bad"),
    ]
    with pytest.raises(AttributeError):
        install_spies(specs, counter)

    assert module_a.function is original, "first patch leaked past the failure"
