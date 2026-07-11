"""
CBSP21 Patch Packet Adapter.

Emits and validates the repository's existing ``cbsp21_patch_input_v1`` manifest shape. This is
an ADAPTER to the CBSP21 contract authority (``scripts/ci/check_cbsp21_patch_input.py``), NOT a
second canonical manifest ontology. Field names, coverage semantics, and changed-file rules are
not forked; ``REQUIRED_FIELDS`` mirrors the gate's own required-field list so a packet built here
validates against the real gate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

CBSP21_SCHEMA = "cbsp21_patch_input_v1"

# Mirrors the `required` list in scripts/ci/check_cbsp21_patch_input.py. Kept in lockstep;
# a drift test asserts this equals the documented gate contract.
REQUIRED_FIELDS: Tuple[str, ...] = (
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


class CBSP21PacketError(Exception):
    """Raised when a CBSP21 patch packet is malformed or fails validation."""


def _sorted_unique_paths(items: Sequence[str]) -> List[str]:
    out = set()
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise CBSP21PacketError(f"invalid path entry: {item!r}")
        out.add(item.strip().replace("\\", "/"))
    if not out:
        raise CBSP21PacketError("path list must be non-empty")
    return sorted(out)


def _get(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def build_cbsp21_patch_packet(
    *,
    patch_id: str,
    title: str,
    intent: str,
    change_type: str,
    behavior_change: str,
    risk_level: str,
    paths_in_scope: Sequence[str],
    files_expected_to_change: Sequence[str],
    what_changed: str,
    why_not_redundant: str,
    verification_commands: Sequence[str],
    files: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build a validated ``cbsp21_patch_input_v1`` packet (deterministic: path lists sorted)."""
    packet: Dict[str, Any] = {
        "schema": CBSP21_SCHEMA,
        "schema_version": CBSP21_SCHEMA,
        "patch_id": patch_id,
        "title": title,
        "intent": intent,
        "change_type": change_type,
        "behavior_change": behavior_change,
        "risk_level": risk_level,
        "scope": {
            "paths_in_scope": _sorted_unique_paths(paths_in_scope),
            "files_expected_to_change": _sorted_unique_paths(files_expected_to_change),
        },
        "diff_articulation": {
            "what_changed": what_changed,
            "why_not_redundant": why_not_redundant,
        },
        "verification": {
            "commands_run": list(verification_commands),
        },
    }
    if files is not None:
        packet["files"] = [dict(f) for f in files]
    validate_cbsp21_patch_packet(packet)
    return packet


def validate_cbsp21_patch_packet(packet: Dict[str, Any]) -> None:
    """
    Validate a packet against the gate's required-field contract.

    Mirrors ``scripts/ci/check_cbsp21_patch_input.py``: required fields present and non-empty,
    and if ``behavior_change`` is not ``"none"`` then ``diff_articulation.why_not_redundant``
    must be at least 20 characters. Raises ``CBSP21PacketError`` on any violation.
    """
    if not isinstance(packet, dict):
        raise CBSP21PacketError("packet must be a dict")
    for key in REQUIRED_FIELDS:
        value = _get(packet, key)
        if (
            value is None
            or (isinstance(value, str) and not value.strip())
            or (isinstance(value, list) and len(value) == 0)
        ):
            raise CBSP21PacketError(f"missing/empty required field: {key}")
    behavior_change = str(_get(packet, "behavior_change") or "").strip().lower()
    why_not = str(_get(packet, "diff_articulation.why_not_redundant") or "").strip()
    if behavior_change != "none" and len(why_not) < 20:
        raise CBSP21PacketError(
            "behavior_change is not 'none' but diff_articulation.why_not_redundant "
            "is too short (need >= 20 chars)"
        )


def canonical_packet_json(packet: Dict[str, Any]) -> str:
    """Deterministic JSON serialization (sorted keys, compact separators)."""
    return json.dumps(packet, sort_keys=True, separators=(",", ":"))


def compute_packet_hash(packet: Dict[str, Any]) -> str:
    """Deterministic 16-hex-char content hash of a packet."""
    return hashlib.sha256(canonical_packet_json(packet).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class CBSP21PatchPacketAdapter:
    """Typed, explicit adapter to the CBSP21 packet shape (not a second manifest ontology)."""

    patch_id: str
    title: str
    intent: str
    change_type: str
    behavior_change: str
    risk_level: str
    paths_in_scope: Tuple[str, ...]
    files_expected_to_change: Tuple[str, ...]
    what_changed: str
    why_not_redundant: str
    verification_commands: Tuple[str, ...]
    files: Optional[Tuple[Dict[str, Any], ...]] = None

    def to_packet(self) -> Dict[str, Any]:
        return build_cbsp21_patch_packet(
            patch_id=self.patch_id,
            title=self.title,
            intent=self.intent,
            change_type=self.change_type,
            behavior_change=self.behavior_change,
            risk_level=self.risk_level,
            paths_in_scope=self.paths_in_scope,
            files_expected_to_change=self.files_expected_to_change,
            what_changed=self.what_changed,
            why_not_redundant=self.why_not_redundant,
            verification_commands=self.verification_commands,
            files=list(self.files) if self.files else None,
        )
