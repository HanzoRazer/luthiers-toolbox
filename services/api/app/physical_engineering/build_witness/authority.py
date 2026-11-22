"""Prohibited authority claims, wherever they appear in a package.

A claim is prohibited whether it is a JSON key, a JSON value, a CSV column
value, or a derived observation, and however it is spelled: ``intrinsic_moe``,
``Intrinsic-MOE`` and ``INTRINSIC MOE`` are the same claim. Values are matched
as a whole after normalization, so prose that mentions a word in passing is
not a claim.
"""

from __future__ import annotations

import re

from app.physical_engineering.build_witness.findings import Finding, finding
from app.physical_engineering.build_witness.vocabulary import (
    BUILD_RESPONSE_OBSERVED,
    CALIBRATION_UNVERIFIED,
    CAPTURE_COMPLETE,
    CAPTURE_INCOMPLETE,
    INTEGRITY_VERIFIED,
    LITERATURE_STATUS,
    METHOD_REVIEW_PENDING,
    PROHIBITED_KEYS,
    PROHIBITED_STATES,
    REFERENCE_COMPARISON_BLOCKED,
    SCIENTIFIC_INTERPRETATION_PENDING,
    WITNESS_CLASS,
)

_SEPARATORS = re.compile(r"[^0-9a-z]+")
_PROHIBITED = frozenset(PROHIBITED_KEYS) | {state.lower() for state in PROHIBITED_STATES}
_KNOWN_STATES = frozenset(
    {
        BUILD_RESPONSE_OBSERVED,
        CALIBRATION_UNVERIFIED,
        CAPTURE_COMPLETE,
        CAPTURE_INCOMPLETE,
        METHOD_REVIEW_PENDING,
        REFERENCE_COMPARISON_BLOCKED,
        SCIENTIFIC_INTERPRETATION_PENDING,
    }
)


def normalize(text: str) -> str:
    return _SEPARATORS.sub("_", text.casefold()).strip("_")


def is_prohibited(text: object) -> bool:
    return isinstance(text, str) and normalize(text) in _PROHIBITED


def scan(value: object, where: str, findings: list[Finding]) -> None:
    """Report every prohibited key or value inside ``value``."""
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            _scan_dict(item, where, findings, stack)
        elif isinstance(item, list):
            stack.extend(item)
        elif is_prohibited(item):
            findings.append(finding("authority", "prohibited_value", f"{where}: {item}"))


def _scan_dict(value: dict, where: str, findings: list[Finding], stack: list) -> None:
    for key, item in value.items():
        if is_prohibited(key):
            findings.append(finding("authority", "prohibited_key", f"{where}: {key}"))
        if key == "witness_class":
            _witness_class(item, findings)
        elif key == "literature_reconciliation_status" and item != LITERATURE_STATUS:
            findings.append(finding("authority", "prohibited_literature_status", "literature comparison is blocked"))
        elif key == "states" and isinstance(item, list):
            _states(item, findings)
            continue
        stack.append(item)


def _witness_class(item: object, findings: list[Finding]) -> None:
    if item == WITNESS_CLASS:
        return
    if is_prohibited(item):
        findings.append(finding("authority", "prohibited_witness_class", str(item)))
        return
    findings.append(finding("malformed", "schema_version", "witness class is not BUILD_RESPONSE_WITNESS"))


def _states(items: list, findings: list[Finding]) -> None:
    for item in items:
        if not isinstance(item, str):
            findings.append(finding("malformed", "schema_version", "state is not a string"))
        elif is_prohibited(item):
            findings.append(finding("authority", "prohibited_state", item))
        elif item == INTEGRITY_VERIFIED:
            findings.append(finding("malformed", "self_certified_integrity", "integrity cannot be self-certified"))
        elif item not in _KNOWN_STATES:
            findings.append(finding("malformed", "schema_version", "unknown state"))
