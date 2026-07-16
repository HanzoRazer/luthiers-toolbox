"""Tests for the CBSP21 patch packet adapter (emit/validate the real gate shape)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.ibg_repository import (
    CBSP21_SCHEMA,
    REQUIRED_FIELDS,
    WHY_NOT_REDUNDANT_MIN_CHARS,
    CBSP21PacketError,
    CBSP21PatchPacketAdapter,
    build_cbsp21_patch_packet,
    canonical_packet_json,
    compute_packet_hash,
    validate_behavior_change_articulation,
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


def _gate_articulation_threshold() -> int | None:
    """Extract the gate's ``len(why_not) < N`` articulation threshold from its source (no execution).

    Mirrors ``_gate_required_fields``: binds the drift test to the real gate implementation rather
    than a duplicated literal, so a change to the gate's threshold fails this test instead of
    silently desyncing from ``WHY_NOT_REDUNDANT_MIN_CHARS``. Matches exactly the comparison shape
    ``len(<name>) < <int>``; returns ``None`` when a unique such comparison is not found.
    """
    tree = ast.parse(_GATE_PATH.read_text(encoding="utf-8"))
    found: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Lt):
            continue
        left = node.left
        if not (
            isinstance(left, ast.Call)
            and isinstance(left.func, ast.Name)
            and left.func.id == "len"
        ):
            continue
        right = node.comparators[0]
        if isinstance(right, ast.Constant) and isinstance(right.value, int):
            found.append(right.value)
    return found[0] if len(found) == 1 else None


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


def test_articulation_threshold_matches_gate_contract():
    # Bind the adapter's threshold to the ACTUAL gate source, not a duplicated literal. The gate is
    # the ultimate authority; if it changes its `len(why_not) < N`, this fails and forces
    # WHY_NOT_REDUNDANT_MIN_CHARS to be re-synced (the required-field drift test covers the field
    # list; this covers the one numeric rule the field list cannot).
    if not _GATE_PATH.exists():
        pytest.skip(f"CBSP21 gate not found at {_GATE_PATH}")
    gate_threshold = _gate_articulation_threshold()
    assert gate_threshold is not None, "could not extract a unique `len(...) < N` threshold from the gate"
    assert WHY_NOT_REDUNDANT_MIN_CHARS == gate_threshold


@pytest.mark.parametrize(
    "length, should_raise",
    [
        (WHY_NOT_REDUNDANT_MIN_CHARS - 1, True),   # 19: just under the boundary -> rejected
        (WHY_NOT_REDUNDANT_MIN_CHARS, False),      # 20: exactly the minimum -> accepted
        (WHY_NOT_REDUNDANT_MIN_CHARS + 1, False),  # 21: over the boundary -> accepted
    ],
)
def test_articulation_boundary_is_inclusive_at_the_minimum(length, should_raise):
    # Guards the `< MIN` off-by-one: MIN chars must pass, MIN-1 must fail, for a non-"none" change.
    # Isolated-rule and whole-packet validators must agree at the boundary (one rule, one impl).
    why_not = "x" * length
    packet = build_cbsp21_patch_packet(
        **_kwargs(behavior_change="none", why_not_redundant="ok")
    )
    packet["behavior_change"] = "adds endpoint"
    packet["diff_articulation"]["why_not_redundant"] = why_not
    if should_raise:
        with pytest.raises(CBSP21PacketError):
            validate_behavior_change_articulation(packet)
        with pytest.raises(CBSP21PacketError):
            validate_cbsp21_patch_packet(packet)
    else:
        validate_behavior_change_articulation(packet)
        validate_cbsp21_patch_packet(packet)


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
