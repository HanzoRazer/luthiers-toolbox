"""Canonical bytes for an LTB validation-policy record.

Uses the evidence store's JSON rules: sorted keys, compact separators, and
SHA-256 of UTF-8. The digest covers the policy payload and excludes both
``payload_digest`` and ``approval``. Approval cites that digest; it is not
part of the hashed payload.
"""
from __future__ import annotations

from app.physical_engineering.evidence_serialization import canonical_record
from app.physical_engineering.validation_policy_record_v1 import (
    LtbValidationPolicyRecordV1,
    record_fields,
)


def canonical_policy_text(record: LtbValidationPolicyRecordV1) -> str:
    return canonical_record(record_fields(record))
