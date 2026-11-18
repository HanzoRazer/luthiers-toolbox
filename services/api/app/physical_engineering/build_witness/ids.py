"""Collision-safe witness identifiers.

The clock and the id factory are both required. A millisecond stamp alone is
not unique. Callers can inject both for tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
import uuid
from typing import Callable

_ID = re.compile(r"^pem_(witness|build|session|observation)_[0-9]+_[0-9a-f]{32}$")
_HEX = re.compile(r"^[0-9a-f]{32}$")
KINDS = frozenset({"witness", "build", "session", "observation"})


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid_hex() -> str:
    return uuid.uuid4().hex


def new_id(kind: str, clock: Callable[[], datetime] | None = None, factory: Callable[[], str] | None = None) -> str:
    if kind not in KINDS:
        raise ValueError(f"unknown id kind: {kind}")
    moment = (clock or utc_now)()
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("clock must return an aware datetime")
    token = (factory or new_uuid_hex)()
    if not isinstance(token, str) or _HEX.fullmatch(token) is None:
        raise ValueError("id factory must return 32 lowercase hex characters")
    millis = int(moment.timestamp() * 1000)
    identifier = f"pem_{kind}_{millis}_{token}"
    if _ID.fullmatch(identifier) is None:
        raise ValueError("generated id is not filename-safe")
    return identifier


def is_identifier(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None
