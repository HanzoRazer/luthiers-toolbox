"""Negative schema test: verify chladni_run schema rejects invalid documents."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

# Minimal invalid chladni_run (extra unexpected property 'bogus')
# Should fail because schema has additionalProperties: false
INVALID_EXTRA_PROPERTY = {
    "schema_id": "chladni_run",
    "schema_version": "1.0",
    "artifact_type": "chladni_run",
    "created_utc": "2026-01-20T12:00:00Z",
    "plate_id": "TEST_PLATE",
    "environment": {"temp_C": 22.0, "rh_pct": 45.0},
    "excitation": {"mode": "speaker_sweep"},
    "peaks_hz": [100.0, 200.0],
    "patterns": [],
    "provenance": {
        "peaks_source": "test",
        "peaks_sha256": "a" * 64,
        "algo_version": "1.0.0",
    },
    "bogus": 123,  # <-- should fail: additionalProperties: false
}

# Missing required field
INVALID_MISSING_REQUIRED = {
    "schema_id": "chladni_run",
    "schema_version": "1.0",
    "artifact_type": "chladni_run",
    # missing: plate_id, environment, excitation, peaks_hz, patterns, provenance
}


def _load_chladni_schema() -> dict:
    """Load chladni_run schema from contracts/schemas/."""
    repo = Path(__file__).resolve().parents[1]
    schema_path = repo / "contracts" / "schemas" / "chladni_run.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def test_chladni_rejects_extra_property():
    """Schema should reject documents with unexpected properties."""
    schema = _load_chladni_schema()
    v = Draft202012Validator(schema)
    errs = list(v.iter_errors(INVALID_EXTRA_PROPERTY))
    assert errs, "Schema should reject document with 'bogus' property"
    # Verify the error is about additional properties
    error_messages = " ".join(str(e.message) for e in errs)
    assert "bogus" in error_messages or "Additional" in error_messages


def test_chladni_rejects_missing_required():
    """Schema should reject documents missing required fields."""
    schema = _load_chladni_schema()
    v = Draft202012Validator(schema)
    errs = list(v.iter_errors(INVALID_MISSING_REQUIRED))
    assert errs, "Schema should reject document missing required fields"
