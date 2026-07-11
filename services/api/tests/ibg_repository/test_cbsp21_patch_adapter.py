"""Tests for the CBSP21 patch packet adapter (emit/validate the real gate shape)."""

from __future__ import annotations

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
    # Must stay in lockstep with scripts/ci/check_cbsp21_patch_input.py `required`.
    assert REQUIRED_FIELDS == (
        "schema_version",
        "patch_id",
        "title",
        "intent",
        "change_type",
        "behavior_change",
        "risk_level",
        "scope.paths_in_scope",
        "scope.files_expected_to_change",
        "diff_articulation.what_changed",
        "diff_articulation.why_not_redundant",
        "verification.commands_run",
    )


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
