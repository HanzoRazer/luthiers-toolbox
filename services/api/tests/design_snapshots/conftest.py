"""Shared fixtures for design-snapshot tests."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

FIXTURES = (
    Path(__file__).resolve().parents[4]
    / "docs/investigations/shop-job-design-pin-001/fixtures"
)
T0 = datetime(2026, 10, 28, 17, 0, tzinfo=timezone.utc)


@pytest.fixture
def baseline_state() -> dict:
    return json.loads((FIXTURES / "baseline_acoustic_guitar_design_state.json").read_text(encoding="utf-8"))


@pytest.fixture
def golden_text() -> str:
    return (FIXTURES / "golden_snapshot.json").read_text(encoding="utf-8")
