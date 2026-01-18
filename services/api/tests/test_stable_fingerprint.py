"""
Tests for stable fingerprinting (Bundle 32.8.3).

Ensures:
- Key order doesn't affect fingerprints
- Float representation drift doesn't affect fingerprints
- stable_dumps is deterministic
"""

from __future__ import annotations

import pytest

from app.shared.fingerprint import fingerprint_stable, FINGERPRINT_ALGO
from app.shared.stablejson import stable_dumps


def test_stable_dumps_key_order_is_deterministic():
    """Keys in different order should produce same output."""
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert stable_dumps(a) == stable_dumps(b)


def test_fingerprint_stable_key_order_is_deterministic():
    """Fingerprints should be identical regardless of key order."""
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert fingerprint_stable(a) == fingerprint_stable(b)


def test_fingerprint_stable_float_rounding_is_stable():
    """Float precision differences should round to same fingerprint."""
    # Values that can differ by repr / calc noise
    a = {"x": 0.30000000000000004}
    b = {"x": 0.3}
    # Both round to 0.3 with 6 decimals
    assert fingerprint_stable(a) == fingerprint_stable(b)


def test_fingerprint_algo_prefix_present():
    """Fingerprints should be prefixed with the algorithm identifier."""
    fp = fingerprint_stable({"x": 1})
    assert fp.startswith(FINGERPRINT_ALGO + ":")


def test_fingerprint_algo_is_expected_value():
    """Algorithm identifier should be the expected stable version."""
    assert FINGERPRINT_ALGO == "sha256-stablejson-v1"


def test_stable_dumps_nested_structures():
    """Nested dicts and lists should normalize consistently."""
    a = {"outer": {"z": 3, "a": 1}, "list": [3, 2, 1]}
    b = {"list": [3, 2, 1], "outer": {"a": 1, "z": 3}}
    assert stable_dumps(a) == stable_dumps(b)


def test_stable_dumps_none_values():
    """None values should be preserved in output."""
    obj = {"a": None, "b": 1}
    result = stable_dumps(obj)
    assert '"a":null' in result
    assert '"b":1' in result


def test_fingerprint_different_values_differ():
    """Different objects should produce different fingerprints."""
    fp1 = fingerprint_stable({"x": 1})
    fp2 = fingerprint_stable({"x": 2})
    assert fp1 != fp2


def test_fingerprint_empty_dict():
    """Empty dict should have a valid fingerprint."""
    fp = fingerprint_stable({})
    assert fp.startswith(FINGERPRINT_ALGO + ":")
    assert len(fp) > len(FINGERPRINT_ALGO) + 1  # algo + colon + hash


def test_stable_dumps_pydantic_model():
    """Pydantic models should be normalized via model_dump."""
    from pydantic import BaseModel

    class TestModel(BaseModel):
        z_field: int = 1
        a_field: str = "test"

    model = TestModel()
    result = stable_dumps(model)
    # Should have sorted keys
    assert result.index('"a_field"') < result.index('"z_field"')
