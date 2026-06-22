"""
Retirement guards for app.cam.dxf_consolidator.

The module is retained for historical compatibility, but retirement must not
add import-time warning side effects. Actual use should remain visible.
These tests inspect the source so they can run even when local ezdxf is absent.
"""

from __future__ import annotations

import ast
import importlib
import sys
import warnings
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "cam"
    / "dxf_consolidator.py"
)
MODULE_NAME = "app.cam.dxf_consolidator"


def _tree() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def _is_warnings_warn_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "warn"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "warnings"
    )


def test_retired_dxf_consolidator_has_no_import_time_warning():
    module_tree = _tree()

    top_level_warning_calls = [
        node
        for node in module_tree.body
        if isinstance(node, ast.Expr) and _is_warnings_warn_call(node.value)
    ]

    assert top_level_warning_calls == []


def test_retired_dxf_consolidator_warns_on_constructor_use():
    module_tree = _tree()
    consolidator_class = next(
        node
        for node in module_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "DxfConsolidator"
    )
    init_method = next(
        node
        for node in consolidator_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )

    calls_retired_warning = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_warn_retired_use"
        for node in ast.walk(init_method)
    )

    assert calls_retired_warning


def test_retired_dxf_consolidator_runtime_warning_behavior():
    pytest.importorskip("ezdxf")
    sys.modules.pop(MODULE_NAME, None)

    with warnings.catch_warnings(record=True) as import_warnings:
        warnings.simplefilter("always", DeprecationWarning)
        module = importlib.import_module(MODULE_NAME)

    assert [
        warning
        for warning in import_warnings
        if issubclass(warning.category, DeprecationWarning)
    ] == []

    with warnings.catch_warnings(record=True) as use_warnings:
        warnings.simplefilter("always", DeprecationWarning)
        module.DxfConsolidator()

    deprecation_warnings = [
        warning
        for warning in use_warnings
        if issubclass(warning.category, DeprecationWarning)
    ]

    assert len(deprecation_warnings) == 1
    assert "app.cam.dxf_consolidator is RETIRED" in str(
        deprecation_warnings[0].message
    )
