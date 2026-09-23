"""Shared manufacturing-output authority. Not qualification evidence."""

from __future__ import annotations

import ast
import inspect

import pytest
from fastapi import HTTPException

from app.rmos.manufacturing_output_authority import (
    require_manufacturing_output_authority,
)

pytestmark = pytest.mark.allow_missing_request_id


class _MemoryStore:
    def __init__(self) -> None:
        self.saved: list = []

    def put(self, artifact):
        self.saved.append(artifact)
        return artifact


@pytest.fixture
def memory_store(monkeypatch):
    store = _MemoryStore()
    monkeypatch.setattr(
        "app.rmos.runs_v2.store._get_default_store",
        lambda: store,
    )
    return store


def _permit(payload):
    def compute(*, tool_id, req, context=None):
        return {"tool_id": tool_id, "context": context, **payload}

    return compute


def _ask(monkeypatch, payload):
    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal",
        _permit(payload),
    )
    return require_manufacturing_output_authority(
        tool_id="boss_probe_gcode",
        mode="probing",
        event_type="boss_probe_gcode",
        request_summary={"pattern": "boss_circular"},
    )


def test_permitting_evaluator_returns_an_authority_context(monkeypatch, memory_store):
    context = _ask(
        monkeypatch,
        {"risk_level": "GREEN", "warnings": ["test-only"], "score": 3},
    )
    assert context.risk_level == "GREEN"
    assert context.warnings == ("test-only",)
    assert context.decision.risk_level_str() == "GREEN"
    assert memory_store.saved == []


def test_red_blocks(monkeypatch, memory_store):
    with pytest.raises(HTTPException) as caught:
        _ask(monkeypatch, {"risk_level": "RED", "warnings": ["stop"]})
    assert caught.value.status_code == 409
    assert caught.value.detail["error"] == "SAFETY_BLOCKED"
    assert memory_store.saved[0].status == "BLOCKED"


def test_unknown_blocks(monkeypatch, memory_store):
    with pytest.raises(HTTPException) as caught:
        _ask(monkeypatch, {"risk_level": "UNKNOWN", "warnings": ["missing"]})
    assert caught.value.status_code == 409
    assert memory_store.saved[0].decision.warnings == ["missing"]


def test_missing_evaluator_blocks(memory_store):
    with pytest.raises(HTTPException) as caught:
        require_manufacturing_output_authority(
            tool_id="cam_polygon_offset_nc",
            mode="polygon_offset",
            event_type="polygon_offset_nc",
            request_summary={"tool_dia": 6},
        )
    assert caught.value.status_code == 409
    assert caught.value.detail["decision"]["risk_level"] == "UNKNOWN"
    assert memory_store.saved[0].hashes.gcode_sha256 is None


def test_warnings_are_preserved(monkeypatch, memory_store):
    with pytest.raises(HTTPException):
        _ask(monkeypatch, {"risk_level": "RED", "warnings": ["keep-me", "also"]})
    assert memory_store.saved[0].decision.warnings == ["keep-me", "also"]


def test_blocked_attempt_has_no_output_hash(monkeypatch, memory_store):
    with pytest.raises(HTTPException):
        _ask(monkeypatch, {"risk_level": "UNKNOWN"})
    artifact = memory_store.saved[0]
    assert len(memory_store.saved) == 1
    assert artifact.hashes.gcode_sha256 is None
    assert artifact.status == "BLOCKED"


def test_evaluator_exceptions_are_not_turned_into_permission(monkeypatch, memory_store):
    def explode(*, tool_id, req, context=None):
        raise RuntimeError("evaluator down")

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal",
        explode,
    )
    with pytest.raises(RuntimeError, match="evaluator down"):
        require_manufacturing_output_authority(
            tool_id="geometry_export_gcode",
            mode="geometry_export",
            event_type="geometry_export_gcode",
            request_summary={},
        )
    assert memory_store.saved == []


def test_authority_service_does_not_generate_a_program():
    import app.rmos.manufacturing_output_authority as module

    tree = ast.parse(inspect.getsource(module))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    assert not any(name.startswith("generate_") for name in names)
    assert "RunDecision" not in names


def test_returned_context_keeps_the_evaluator_decision(monkeypatch, memory_store):
    context = _ask(
        monkeypatch,
        {"risk_level": "YELLOW", "warnings": ["watch"], "score": 40},
    )
    assert context.risk_level == "YELLOW"
    assert context.decision.to_dict()["warnings"] == ["watch"]
    assert context.decision.score == 40
