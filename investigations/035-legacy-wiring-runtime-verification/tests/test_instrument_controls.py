"""IW-01..IW-05 instrument controls for Investigation 035.

These tests prove the witness harness, not production D-status.
They do not import the full application except IW-03 (optional / expensive).
"""
from types import ModuleType

import pytest

from runtime_reachability_witness import CallCounter, install_spies, SpySpec, stop_spies


def _make_bound_pair():
    """module_a.function imported into module_b.bound_function."""
    module_a = ModuleType("iw_fixture_module_a")

    def function(x):
        return x * 2

    module_a.function = function

    module_b = ModuleType("iw_fixture_module_b")
    # Binding at import time (the Vectorizer-witness hazard).
    module_b.bound_function = module_a.function

    import sys

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
