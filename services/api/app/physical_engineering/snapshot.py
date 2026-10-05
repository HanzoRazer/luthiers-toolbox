"""Frozen record of one screening decision.

Replay reads this record and must not call the live evidence resolver.
``snapshot_sha256`` lives on the snapshot. The validation object inside it
keeps ``snapshot_sha256`` unset so the frozen verdict is not rewritten to
hold its own digest.

The digest uses a temporary internal deterministic encoding of the frozen
decision record. Canonical external serialization belongs to PEP-V1-CONTRACT-002.
It is an integrity check, not a wire schema.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math

from app.physical_engineering.policy import ValidationPolicyV1


@dataclass(frozen=True)
class FrozenValidationSnapshotV1:
    """Authoritative inputs and the verdict they produced."""

    schema_id: str
    schema_version: str
    proposal: object
    resolved_evidence: tuple
    policy: ValidationPolicyV1
    validator_version: str
    contradiction_rule_version: str
    resolution_status: str
    validation: object
    snapshot_sha256: str


def integrity_digest(payload: dict) -> str:
    """SHA-256 of a JSON object. Non-finite floats are tagged rather than emitted."""
    encoded = json.dumps(
        _sanitize(payload),
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_validation_snapshot(proposal, *, resolver, policy):
    """Public entry. The decision itself lives in ``proposal_v1``."""
    from app.physical_engineering.proposal_v1 import build_validation_snapshot as build

    return build(proposal, resolver=resolver, policy=policy)


def replay_validation_snapshot(snapshot):
    """Public entry. Replay takes no resolver and does not touch a live store."""
    from app.physical_engineering.proposal_v1 import replay_validation_snapshot as replay

    return replay(snapshot)


def _sanitize(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float) and not math.isfinite(value):
        return f"nonfinite:{value!r}"
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            name: _sanitize(getattr(value, name))
            for name in value.__dataclass_fields__
        }
    return value
