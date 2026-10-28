"""Canonical bytes and digest for a design snapshot.

The digest covers every snapshot field except ``snapshot_digest``. This module
is local to ``design_snapshots`` on purpose: domain modules do not import each
other (docs/governance/ARCHITECTURE_INVARIANTS.md, Rule 4).
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping


def canonical_json(value: object) -> str:
    """Stable JSON. Key order does not change the bytes. Non-finite numbers fail."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_payload(fields: Mapping[str, object]) -> str:
    """Stable JSON for the fields that identify the snapshot bytes."""
    body = {key: fields[key] for key in fields if key != "snapshot_digest"}
    return canonical_json(body)


def canonical_record(fields: Mapping[str, object]) -> str:
    """Stable JSON for the whole snapshot, including its digest."""
    return canonical_json(dict(fields))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_digest(fields: Mapping[str, object]) -> str:
    return sha256_text(canonical_payload(fields))
