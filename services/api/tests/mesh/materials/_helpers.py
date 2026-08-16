"""Shared helpers for MESH-MAT-001 tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "materials"
CONTRACTS = Path(__file__).resolve().parents[5] / "contracts"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fixture(name: str) -> Dict[str, Any]:
    return load_json(FIXTURES / name)


def contract_schema(name: str) -> Dict[str, Any]:
    return load_json(CONTRACTS / name)
