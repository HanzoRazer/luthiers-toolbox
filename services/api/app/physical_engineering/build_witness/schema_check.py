"""Apply the published JSON schemas to package documents.

Every schema violation becomes a finding that names the document and the
location inside it. A document that breaks its schema is never passed on as
if it were well formed, and a violation never surfaces as a traceback.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from app.physical_engineering.build_witness.findings import Finding, finding
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).with_name("schemas")
BUILD_RECORD = "pem_build_record_v1"
TEST_PROTOCOL = "pem_test_protocol_v1"
MEASUREMENT = "pem_measurement_observation_v1"
WITNESS_MANIFEST = "pem_build_witness_v1"

_MESSAGE_LIMIT = 200
_ERRORS_PER_DOCUMENT = 20


@cache
def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def schema_findings(
    name: str,
    instance: object,
    where: str,
    *,
    severity: str = "malformed",
    code: str = "record_schema",
) -> list[Finding]:
    """Findings for every violation of schema ``name`` by ``instance``.

    ``where`` names the document (and row, for CSV) in each message. Each
    message carries a JSON pointer to the failing value. Output is capped so
    a hostile document cannot flood the result.
    """
    errors = sorted(validator(name).iter_errors(instance), key=lambda item: list(map(str, item.absolute_path)))
    found = []
    for error in errors[:_ERRORS_PER_DOCUMENT]:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        message = error.message
        if len(message) > _MESSAGE_LIMIT:
            message = message[: _MESSAGE_LIMIT - 3] + "..."
        found.append(finding(severity, code, f"{where} {pointer}: {message}"))
    if len(errors) > _ERRORS_PER_DOCUMENT:
        found.append(finding(severity, code, f"{where}: {len(errors) - _ERRORS_PER_DOCUMENT} more schema errors"))
    return found
