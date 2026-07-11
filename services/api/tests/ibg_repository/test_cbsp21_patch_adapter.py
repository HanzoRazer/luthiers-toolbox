"""Tests for the CBSP21 patch packet adapter (emit/validate the real gate shape)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.ibg_repository import (
    CBSP21_SCHEMA,
    REQUIRED_FIELDS,
    CBSP21PacketError,
    CBSP21PatchPacketAdapter,
    build_cbsp21_patch_packet,
    canonical_packet_json,
    compute_packet_hash,
    validate_cbsp21_patch_packet,
)

# Repo root: .../services/api/tests/ibg_repository/<this file>
_GATE_PATH = (
    Path(__file__).resolve().parents[4] / "scripts" / "ci" / "check_cbsp21_patch_input.py"
)


def _gate_required_fields() -> tuple[str, ...]:
    """Extract the gate's `required = [...]` list from its actual source (no execution).

    Binds the drift test to the real implementation rather than a duplicated literal, so a
    change to the gate's required-field list fails this test instead of silently desyncing.
    """
    tree = ast.parse(_GATE_PATH.read_text(encoding="utf-8"))
    found: list[tuple[str, ...]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = {t.id for t in node.targets if isinstance(t, ast.Name)}
        if "required" not in {n.lower() for n in names}:
            continue
        if isinstance(node.value, ast.List) and all(
            isinstance(el, ast.Constant) and isinstance(el.value, str)
            for el in node.value.elts
        ):
            found.append(tuple(el.value for el in node.value.elts))
    return found[0] if len(found) == 1 else ()


def _kwargs(**over):
    base = dict(
        patch_id="IBG_X",
        title="t",
        intent="i",
        change_type="feat",
        behavior_change="none",
        risk_level="low",
        paths_in_scope=["b/p.py", "a/p.py"],
        files_expected_to_change=["b/p.py", "a/p.py"],
        what_changed="changed",
        why_not_redundant="ok",
        verification_commands=["pytest"],
    )
    base.update(over)
    return base


def test_build_validates_and_sorts_paths():
    p = build_cbsp21_patch_packet(**_kwargs())
    validate_cbsp21_patch_packet(p)
    assert p["schema_version"] == CBSP21_SCHEMA
    assert p["scope"]["paths_in_scope"] == ["a/p.py", "b/p.py"]


def test_required_fields_match_gate_contract():
    # Bind to the ACTUAL gate source, not a duplicated literal: if the gate's required-field
    # list changes, this fails and forces REQUIRED_FIELDS to be re-synced.
    if not _GATE_PATH.exists():
        pytest.skip(f"CBSP21 gate not found at {_GATE_PATH}")
    gate_required = _gate_required_fields()
    assert gate_required, "could not extract a unique `required` list from the gate source"
    assert REQUIRED_FIELDS == gate_required


def test_validate_catches_missing_field():
    p = build_cbsp21_patch_packet(**_kwargs())
    del p["title"]
    with pytest.raises(CBSP21PacketError):
        validate_cbsp21_patch_packet(p)


def test_behavior_change_requires_long_why_not():
    with pytest.raises(CBSP21PacketError):
        build_cbsp21_patch_packet(
            **_kwargs(behavior_change="adds endpoint", why_not_redundant="short")
        )
    p = build_cbsp21_patch_packet(
        **_kwargs(
            behavior_change="adds endpoint",
            why_not_redundant="this adds a genuinely new endpoint path not present before",
        )
    )
    validate_cbsp21_patch_packet(p)


def test_empty_path_list_rejected():
    with pytest.raises(CBSP21PacketError):
        build_cbsp21_patch_packet(**_kwargs(paths_in_scope=[]))


@pytest.mark.parametrize("bad", ["/etc/passwd", "C:/win", "../escape", "a/../b"])
def test_packet_rejects_unsafe_paths(bad):
    # Path safety is symmetric with ProposalTargetBinding: manifest scope is repo-relative.
    with pytest.raises(CBSP21PacketError):
        build_cbsp21_patch_packet(**_kwargs(paths_in_scope=[bad]))
    with pytest.raises(CBSP21PacketError):
        build_cbsp21_patch_packet(**_kwargs(files_expected_to_change=[bad]))


def test_deterministic_serialization_and_hash():
    p1 = build_cbsp21_patch_packet(**_kwargs())
    p2 = build_cbsp21_patch_packet(**_kwargs())
    assert canonical_packet_json(p1) == canonical_packet_json(p2)
    assert compute_packet_hash(p1) == compute_packet_hash(p2)


def test_adapter_to_packet_validates():
    adapter = CBSP21PatchPacketAdapter(
        patch_id="IBG_X",
        title="t",
        intent="i",
        change_type="feat",
        behavior_change="none",
        risk_level="low",
        paths_in_scope=("a/p.py",),
        files_expected_to_change=("a/p.py",),
        what_changed="c",
        why_not_redundant="ok",
        verification_commands=("pytest",),
    )
    validate_cbsp21_patch_packet(adapter.to_packet())
