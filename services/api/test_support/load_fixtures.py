"""Fixture loader for API tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_fixture(relative_path: str) -> Any:
    return load_json(FIXTURES_DIR / relative_path)
