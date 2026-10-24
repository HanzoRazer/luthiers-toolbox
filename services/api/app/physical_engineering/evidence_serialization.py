"""Canonical bytes for an LTB stored-evidence record.

The digest covers the record fields and excludes ``payload_digest``. A later
check repeats that computation. It does not change the record.
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping


def canonical_payload(fields: Mapping[str, object]) -> str:
    """Stable JSON for the fields that identify the evidence bytes."""
    body = {key: fields[key] for key in fields if key != "payload_digest"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_record(fields: Mapping[str, object]) -> str:
    """Stable JSON for the whole record, including its digest."""
    return json.dumps(dict(fields), sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_digest(fields: Mapping[str, object]) -> str:
    return sha256_text(canonical_payload(fields))
