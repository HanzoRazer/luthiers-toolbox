"""Frozen record of one screening decision.

Replay reads this record and must not call the live evidence resolver.
``snapshot_sha256`` is the one identity of the decision. The same digest is
copied onto the verdict so the verdict stays bound to this record. Display
code may render it as ``sha256:<64 hex>``; the stored form is the hex digest.

The digest is an internal integrity check over the frozen inputs. It is not
a wire-schema canonicalization; that belongs to PEP-V1-CONTRACT-002.
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

    proposal: object
    resolved_evidence: tuple
    policy: ValidationPolicyV1
    validator_version: str
    contradiction_rule_version: str
    resolution_status: str
    result: object
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
