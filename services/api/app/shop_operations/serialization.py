"""Canonical bytes and digest for a shop-operation record.

The digest covers every record field except ``payload_digest``. This module is
local to ``shop_operations`` on purpose: domain modules do not import each
other (docs/governance/ARCHITECTURE_INVARIANTS.md, Rule 4), so the pattern is
repeated here rather than imported from ``physical_engineering``.
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping


def canonical_payload(fields: Mapping[str, object]) -> str:
    """Stable JSON for the fields that identify the record bytes."""
    body = {key: fields[key] for key in fields if key != "payload_digest"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_record(fields: Mapping[str, object]) -> str:
    """Stable JSON for the whole record, including its digest."""
    return json.dumps(dict(fields), sort_keys=True, separators=(",", ":"), allow_nan=False)


def payload_digest(fields: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_payload(fields).encode("utf-8")).hexdigest()
