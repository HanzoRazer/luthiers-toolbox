"""The shop-operation package stays a factual record.

It does not import CAM generators, readiness mutators, G-code writers, routers,
or an estimate path that could fill an actual. Measurement enums have no
derived or estimated member.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from app.shop_operations.operation_record_v1 import DurationBasis, MaterialMeasurementSource


PACKAGE = Path(__file__).resolve().parents[2] / "app" / "shop_operations"
FORBIDDEN_NAME_PARTS = (
    "actual_time_s",
    "cam_approved",
    "manufacturing_approved",
    "safe_to_run",
    "manufacturing_state",
    "move_count",
)
FORBIDDEN_SOURCES = frozenset({
    "ESTIMATE",
    "DERIVED",
    "DERIVED_ESTIMATE",
    "MOVE_COUNT",
    "DEFAULT",
    "UNKNOWN",
    "BOM",
    "PLANNED",
})
NEIGHBOR_PREFIXES = (
    "app.cam",
    "app.cam_core",
    "app.routers",
    "app.business",
    "app.cost_attribution",
    "app.physical_engineering",
    "app.util.gcode",
    "app.services.saw_lab_gcode",
    "app.core.rmos_gcode",
)


def _modules(tree: ast.AST) -> list[str]:
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def _assigned_names(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
    return names


@pytest.mark.unit
def test_package_imports_only_the_standard_library_and_itself():
    offenders: list[str] = []
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module in _modules(tree):
            root = module.split(".", 1)[0]
            own = module == "app.shop_operations" or module.startswith("app.shop_operations.")
            if own or root in sys.stdlib_module_names:
                continue
            offenders.append(f"{path.name}: {module}")
    assert offenders == []


@pytest.mark.unit
def test_package_does_not_import_cam_readiness_gcode_routers_or_estimates():
    offenders: list[str] = []
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module in _modules(tree):
            lowered = module.lower()
            banned_prefix = module.startswith(NEIGHBOR_PREFIXES)
            banned_word = any(word in lowered for word in ("gcode", "readiness", "cnc_production"))
            if banned_prefix or banned_word:
                offenders.append(f"{path.name}: {module}")
    assert offenders == []


@pytest.mark.unit
def test_package_has_no_estimate_derived_actual_and_no_unit_conversion():
    assert {member.value for member in DurationBasis} == {"MEASURED"}
    assert FORBIDDEN_SOURCES.isdisjoint(member.value for member in MaterialMeasurementSource)
    assert {member.value for member in MaterialMeasurementSource} == {
        "MANUAL_MEASUREMENT",
        "SCALE_READING",
        "COUNTED",
        "IMPORTED_MEASUREMENT",
    }
    for path in sorted(PACKAGE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = _assigned_names(tree)
        leaked = [name for name in names if any(part in name for part in FORBIDDEN_NAME_PARTS)]
        assert leaked == []
        assert "def convert" not in source
        assert "def combine" not in source
