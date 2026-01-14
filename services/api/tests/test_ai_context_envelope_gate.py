# services/api/tests/test_ai_context_envelope_gate.py
"""
Pytest gate for AI context envelope v1.

Tests:
- Validator CLI exists
- Minimal fixture validates
- Forbidden fields are blocked
- Redaction is enforced
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def repo_root() -> Path:
    """Get repository root path."""
    return Path(__file__).resolve().parents[3]


class TestAIContextEnvelopeGate:
    """Gate tests for AI context envelope."""

    def test_validator_cli_exists(self):
        """Validator CLI script should exist."""
        p = repo_root() / "scripts" / "validate" / "validate_toolbox_ai_context_envelope_v1.py"
        assert p.exists(), f"Missing validator: {p}"

    def test_schema_exists(self):
        """Schema file should exist."""
        p = repo_root() / "contracts" / "toolbox_ai_context_envelope_v1.schema.json"
        assert p.exists(), f"Missing schema: {p}"

    def test_validates_minimal_fixture(self, tmp_path: Path):
        """Minimal valid envelope should pass validation."""
        schema = repo_root() / "contracts" / "toolbox_ai_context_envelope_v1.schema.json"
        validator = repo_root() / "scripts" / "validate" / "validate_toolbox_ai_context_envelope_v1.py"

        fixture = {
            "schema_id": "toolbox_ai_context_envelope",
            "schema_version": "v1",
            "created_at_utc": "2026-01-14T12:00:00+00:00",
            "context_id": "ctx_demo_0001",
            "source": {
                "system": "toolbox",
                "repo": "luthiers-toolbox",
                "commit": "deadbeef",
                "environment": "ci",
            },
            "capabilities": {
                "allow_sensitive_manufacturing": False,
                "allow_pii": False,
                "allow_audio_raw": False,
            },
            "redaction": {
                "mode": "strict",
                "ruleset": "toolbox_ai_redaction_strict_v1",
                "warnings": [],
            },
            "payload": {
                "run_summary": {
                    "run_id": "run_123",
                    "status": "OPEN",
                    "event_type": "test",
                    "created_at_utc": "2026-01-14T12:00:00+00:00",
                },
                "design_intent": {
                    "domain": "unknown",
                    "summary": "No design intent summary available.",
                    "spec_refs": [],
                },
                "artifacts": {
                    "counts": {"advisories": 0, "candidates": 0, "executions": 0},
                    "recent": [],
                },
            },
        }

        out = tmp_path / "envelope.json"
        out.write_text(json.dumps(fixture, indent=2), encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(validator), "--envelope", str(out), "--schema", str(schema)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AssertionError((proc.stdout or "") + "\n" + (proc.stderr or ""))

    def test_blocks_gcode_field(self, tmp_path: Path):
        """Envelope with gcode field should fail validation."""
        schema = repo_root() / "contracts" / "toolbox_ai_context_envelope_v1.schema.json"
        validator = repo_root() / "scripts" / "validate" / "validate_toolbox_ai_context_envelope_v1.py"

        bad = {
            "schema_id": "toolbox_ai_context_envelope",
            "schema_version": "v1",
            "created_at_utc": "2026-01-14T12:00:00+00:00",
            "context_id": "ctx_demo_0002",
            "source": {
                "system": "toolbox",
                "repo": "luthiers-toolbox",
                "commit": "deadbeef",
                "environment": "ci",
            },
            "capabilities": {
                "allow_sensitive_manufacturing": False,
                "allow_pii": False,
                "allow_audio_raw": False,
            },
            "redaction": {
                "mode": "strict",
                "ruleset": "toolbox_ai_redaction_strict_v1",
                "warnings": [],
            },
            "payload": {
                "run_summary": {
                    "run_id": "run_123",
                    "status": "OPEN",
                    "event_type": "test",
                    "created_at_utc": "2026-01-14T12:00:00+00:00",
                },
                "design_intent": {"domain": "unknown", "summary": "ok", "spec_refs": []},
                "artifacts": {
                    "counts": {"advisories": 0, "candidates": 0, "executions": 0},
                    "recent": [],
                },
            },
            "gcode": "G1 X0 Y0",  # FORBIDDEN
        }

        out = tmp_path / "bad.json"
        out.write_text(json.dumps(bad, indent=2), encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(validator), "--envelope", str(out), "--schema", str(schema)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0, "Envelope with gcode should fail validation"

    def test_blocks_toolpaths_field(self, tmp_path: Path):
        """Envelope with toolpaths field should fail validation."""
        schema = repo_root() / "contracts" / "toolbox_ai_context_envelope_v1.schema.json"
        validator = repo_root() / "scripts" / "validate" / "validate_toolbox_ai_context_envelope_v1.py"

        bad = {
            "schema_id": "toolbox_ai_context_envelope",
            "schema_version": "v1",
            "created_at_utc": "2026-01-14T12:00:00+00:00",
            "context_id": "ctx_demo_0003",
            "source": {
                "system": "toolbox",
                "repo": "luthiers-toolbox",
                "commit": "deadbeef",
                "environment": "ci",
            },
            "capabilities": {
                "allow_sensitive_manufacturing": False,
                "allow_pii": False,
                "allow_audio_raw": False,
            },
            "redaction": {
                "mode": "strict",
                "ruleset": "toolbox_ai_redaction_strict_v1",
                "warnings": [],
            },
            "payload": {
                "run_summary": {
                    "run_id": "run_123",
                    "status": "OPEN",
                    "event_type": "test",
                    "created_at_utc": "2026-01-14T12:00:00+00:00",
                },
                "design_intent": {"domain": "unknown", "summary": "ok", "spec_refs": []},
                "artifacts": {
                    "counts": {"advisories": 0, "candidates": 0, "executions": 0},
                    "recent": [],
                },
            },
            "toolpaths": [{"x": 0, "y": 0}],  # FORBIDDEN
        }

        out = tmp_path / "bad.json"
        out.write_text(json.dumps(bad, indent=2), encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(validator), "--envelope", str(out), "--schema", str(schema)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0, "Envelope with toolpaths should fail validation"

    def test_blocks_player_id_field(self, tmp_path: Path):
        """Envelope with player_id field should fail validation."""
        schema = repo_root() / "contracts" / "toolbox_ai_context_envelope_v1.schema.json"
        validator = repo_root() / "scripts" / "validate" / "validate_toolbox_ai_context_envelope_v1.py"

        bad = {
            "schema_id": "toolbox_ai_context_envelope",
            "schema_version": "v1",
            "created_at_utc": "2026-01-14T12:00:00+00:00",
            "context_id": "ctx_demo_0004",
            "source": {
                "system": "toolbox",
                "repo": "luthiers-toolbox",
                "commit": "deadbeef",
                "environment": "ci",
            },
            "capabilities": {
                "allow_sensitive_manufacturing": False,
                "allow_pii": False,
                "allow_audio_raw": False,
            },
            "redaction": {
                "mode": "strict",
                "ruleset": "toolbox_ai_redaction_strict_v1",
                "warnings": [],
            },
            "payload": {
                "run_summary": {
                    "run_id": "run_123",
                    "status": "OPEN",
                    "event_type": "test",
                    "created_at_utc": "2026-01-14T12:00:00+00:00",
                },
                "design_intent": {"domain": "unknown", "summary": "ok", "spec_refs": []},
                "artifacts": {
                    "counts": {"advisories": 0, "candidates": 0, "executions": 0},
                    "recent": [],
                },
            },
            "player_id": "player_123",  # FORBIDDEN (PII)
        }

        out = tmp_path / "bad.json"
        out.write_text(json.dumps(bad, indent=2), encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(validator), "--envelope", str(out), "--schema", str(schema)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0, "Envelope with player_id should fail validation"


class TestRedactor:
    """Test the strict redactor."""

    def test_removes_forbidden_keys(self):
        """Redactor should remove forbidden keys."""
        from app.ai_context_adapter.redactor.strict import redact_strict

        raw = {
            "schema_id": "toolbox_ai_context_envelope",
            "gcode": "G1 X0 Y0",  # Should be removed
            "safe_field": "ok",
        }

        result = redact_strict(raw)

        assert "gcode" not in result.redacted
        assert result.redacted["safe_field"] == "ok"
        assert any("gcode" in w for w in result.warnings)

    def test_removes_nested_forbidden_keys(self):
        """Redactor should remove nested forbidden keys."""
        from app.ai_context_adapter.redactor.strict import redact_strict

        raw = {
            "level1": {
                "level2": {
                    "toolpath_data": [1, 2, 3],  # Should be removed
                    "name": "test",
                },
            },
        }

        result = redact_strict(raw)

        assert "toolpath_data" not in result.redacted["level1"]["level2"]
        assert result.redacted["level1"]["level2"]["name"] == "test"

    def test_hard_pins_redaction_metadata(self):
        """Redactor should hard-pin redaction metadata."""
        from app.ai_context_adapter.redactor.strict import redact_strict

        raw = {"redaction": {"mode": "lax"}}  # Try to override

        result = redact_strict(raw)

        assert result.redacted["redaction"]["mode"] == "strict"
        assert result.redacted["redaction"]["ruleset"] == "toolbox_ai_redaction_strict_v1"


class TestAssembler:
    """Test the envelope assembler."""

    def test_builds_valid_envelope(self):
        """Assembler should build a valid envelope."""
        from app.ai_context_adapter.assembler.default import build_context_envelope

        envelope = build_context_envelope(
            repo="luthiers-toolbox",
            commit="abc12345",
            environment="ci",
            context_id="ctx_test_001",
            run={
                "run_id": "run_123",
                "status": "OPEN",
                "event_type": "test",
            },
            design_intent={
                "domain": "rosette",
                "summary": "Classic rosette pattern",
            },
            artifacts_counts={"advisories": 1, "candidates": 2, "executions": 0},
            recent_artifacts=[],
        )

        assert envelope["schema_id"] == "toolbox_ai_context_envelope"
        assert envelope["schema_version"] == "v1"
        assert envelope["context_id"] == "ctx_test_001"
        assert envelope["capabilities"]["allow_sensitive_manufacturing"] is False
        assert envelope["capabilities"]["allow_pii"] is False
        assert envelope["redaction"]["mode"] == "strict"
        assert envelope["payload"]["run_summary"]["run_id"] == "run_123"
        assert envelope["payload"]["design_intent"]["domain"] == "rosette"

    def test_strips_forbidden_from_run(self):
        """Assembler should strip forbidden fields from run data."""
        from app.ai_context_adapter.assembler.default import build_context_envelope

        envelope = build_context_envelope(
            repo="luthiers-toolbox",
            commit="abc12345",
            environment="ci",
            context_id="ctx_test_002",
            run={
                "run_id": "run_123",
                "status": "OPEN",
                "gcode": "G1 X0 Y0",  # Should be stripped
                "toolpath_data": [1, 2, 3],  # Should be stripped
            },
            design_intent={"domain": "unknown", "summary": "test"},
            artifacts_counts={"advisories": 0, "candidates": 0, "executions": 0},
            recent_artifacts=[],
        )

        # gcode and toolpath_data should not appear anywhere
        import json

        envelope_str = json.dumps(envelope)
        assert "gcode" not in envelope_str.lower() or "gcode" in envelope["redaction"]["warnings"][0].lower()
        assert "toolpath" not in envelope_str.lower() or "toolpath" in str(envelope["redaction"]["warnings"]).lower()


# Pytest markers
pytestmark = [pytest.mark.unit, pytest.mark.ai_context]
