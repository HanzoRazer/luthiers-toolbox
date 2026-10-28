"""The snapshot package records facts. It does not reach other domains."""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.design_snapshots.repository import FileDesignSnapshotRepository

PACKAGE = Path(__file__).resolve().parents[2] / "app" / "design_snapshots"
BANNED_PREFIXES = (
    "app.cam", "app.cam_core", "app.routers", "app.projects", "app.physical_engineering",
    "app.shop_operations", "app.business", "httpx", "requests", "urllib", "socket",
    "http.client",
)


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


@pytest.mark.unit
def test_package_imports_only_the_standard_library_and_itself():
    for path in PACKAGE.glob("*.py"):
        for name in _imports(path):
            local = name == "app" or name.startswith("app.design_snapshots")
            stdlib = not name.startswith("app.") and name.split(".", 1)[0] != "app"
            assert local or stdlib, name


@pytest.mark.unit
def test_package_does_not_import_routes_cam_policy_or_network_clients():
    imported = [name for path in PACKAGE.glob("*.py") for name in _imports(path)]
    assert [name for name in imported if name.startswith(BANNED_PREFIXES)] == []


@pytest.mark.unit
def test_repository_has_no_update_or_delete():
    names = {
        name for name, value in inspect.getmembers(FileDesignSnapshotRepository)
        if inspect.isfunction(value)
    }
    assert names.isdisjoint({"update", "delete", "remove"})
