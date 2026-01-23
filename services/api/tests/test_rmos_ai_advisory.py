"""
Tests for RMOS AI Advisory CLI Integration.

Tests the integration seam between RMOS and ai-integrator.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Unit Tests for Runner Module
# =============================================================================


class TestRunnerExitCodeMapping:
    """Test that CLI exit codes map to correct exceptions."""

    def test_exit_code_1_raises_schema_error(self):
        from app.rmos.ai_advisory.exceptions import (
            AiIntegratorSchema,
            exception_for_exit_code,
        )

        exc = exception_for_exit_code(1, "schema error")
        assert isinstance(exc, AiIntegratorSchema)
        assert exc.exit_code == 1
        assert "schema error" in str(exc)

    def test_exit_code_2_raises_governance_error(self):
        from app.rmos.ai_advisory.exceptions import (
            AiIntegratorGovernance,
            exception_for_exit_code,
        )

        exc = exception_for_exit_code(2, "governance violation")
        assert isinstance(exc, AiIntegratorGovernance)
        assert exc.exit_code == 2

    def test_exit_code_3_raises_runtime_error(self):
        from app.rmos.ai_advisory.exceptions import (
            AiIntegratorRuntime,
            exception_for_exit_code,
        )

        exc = exception_for_exit_code(3, "runtime error")
        assert isinstance(exc, AiIntegratorRuntime)
        assert exc.exit_code == 3

    def test_exit_code_4_raises_unsupported_error(self):
        from app.rmos.ai_advisory.exceptions import (
            AiIntegratorUnsupported,
            exception_for_exit_code,
        )

        exc = exception_for_exit_code(4, "unsupported")
        assert isinstance(exc, AiIntegratorUnsupported)
        assert exc.exit_code == 4

    def test_unknown_exit_code_raises_runtime_error(self):
        from app.rmos.ai_advisory.exceptions import (
            AiIntegratorRuntime,
            exception_for_exit_code,
        )

        exc = exception_for_exit_code(99, "unknown")
        assert isinstance(exc, AiIntegratorRuntime)
        assert exc.exit_code == 99


class TestCanonicalJsonHashing:
    """Test deterministic JSON hashing."""

    def test_canonical_json_sorts_keys(self):
        from app.rmos.ai_advisory.hashing import canonical_json

        obj = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(obj)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_canonical_json_no_whitespace(self):
        from app.rmos.ai_advisory.hashing import canonical_json

        obj = {"key": "value", "nested": {"inner": 123}}
        result = canonical_json(obj)
        assert " " not in result
        assert "\n" not in result

    def test_sha256_is_deterministic(self):
        from app.rmos.ai_advisory.hashing import sha256_canonical_json

        obj = {"test": "data", "number": 42}
        hash1 = sha256_canonical_json(obj)
        hash2 = sha256_canonical_json(obj)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex = 64 chars

    def test_sha256_order_independent(self):
        from app.rmos.ai_advisory.hashing import sha256_canonical_json

        obj1 = {"a": 1, "b": 2}
        obj2 = {"b": 2, "a": 1}
        assert sha256_canonical_json(obj1) == sha256_canonical_json(obj2)


class TestSchemaValidation:
    """Test Pydantic schema validation."""

    def test_valid_context_packet(self):
        from app.rmos.ai_advisory.schemas import AIContextPacketV1

        packet = {
            "schema_id": "ai_context_packet_v1",
            "created_at_utc": "2026-01-22T12:00:00Z",
            "request": {
                "kind": "explanation",
                "template_id": "explain_selection",
                "template_version": "1.0.0",
            },
            "evidence": {
                "bundle_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "schema_id": "viewer_pack_v1",
                "selected": {
                    "pointId": "A1",
                    "freqHz": 187.5,
                    "activeRelpath": "spectra/points/A1/spectrum.csv",
                },
                "refs": [],
            },
        }

        validated = AIContextPacketV1.model_validate(packet)
        assert validated.schema_id == "ai_context_packet_v1"
        assert validated.request.kind == "explanation"

    def test_invalid_schema_id_rejected(self):
        from pydantic import ValidationError

        from app.rmos.ai_advisory.schemas import AIContextPacketV1

        packet = {
            "schema_id": "wrong_schema_id",
            "created_at_utc": "2026-01-22T12:00:00Z",
            "request": {
                "kind": "explanation",
                "template_id": "test",
                "template_version": "1.0.0",
            },
            "evidence": {
                "bundle_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "schema_id": "viewer_pack_v1",
                "selected": {"pointId": "A1", "freqHz": 100, "activeRelpath": "test.csv"},
                "refs": [],
            },
        }

        with pytest.raises(ValidationError):
            AIContextPacketV1.model_validate(packet)


# =============================================================================
# Integration Tests with Mocked CLI
# =============================================================================


class TestRunnerWithMockedCli:
    """Test runner with mocked subprocess calls."""

    def test_successful_cli_invocation(self, tmp_path: Path):
        """Test that successful CLI returns draft dict."""
        from app.rmos.ai_advisory.config import AiIntegratorConfig
        from app.rmos.ai_advisory.runner import run_ai_integrator_job

        # Create a mock script that writes valid output
        script = tmp_path / "mock_ai_integrator.py"
        script.write_text(
            '''
import sys
import json
from pathlib import Path

args = sys.argv[1:]
out_path = Path(args[args.index("--out") + 1])

draft = {
    "schema_id": "advisory_draft_v1",
    "kind": "explanation",
    "model": {"id": "mock-model", "runtime": "local"},
    "template": {"id": "explain_selection", "version": "1.0.0"},
    "claims": [{"text": "Test claim", "evidence_refs": []}]
}

out_path.write_text(json.dumps(draft), encoding="utf-8")
sys.exit(0)
'''
        )

        config = AiIntegratorConfig(
            bin_path=sys.executable,
            timeout_sec=30,
            workdir=tmp_path / "work",
        )

        # Patch the command to run our mock script
        packet = {
            "schema_id": "ai_context_packet_v1",
            "created_at_utc": "2026-01-22T12:00:00Z",
            "request": {
                "kind": "explanation",
                "template_id": "explain_selection",
                "template_version": "1.0.0",
            },
            "evidence": {
                "bundle_sha256": "abcd" * 16,
                "schema_id": "viewer_pack_v1",
                "selected": {"pointId": "A1", "freqHz": 100, "activeRelpath": "test.csv"},
                "refs": [],
            },
        }

        with patch("subprocess.run") as mock_run:
            # Simulate successful run that writes output file
            def side_effect(cmd, **kwargs):
                # Extract output path from command
                out_idx = cmd.index("--out") + 1
                out_path = Path(cmd[out_idx])
                draft = {
                    "schema_id": "advisory_draft_v1",
                    "kind": "explanation",
                    "model": {"id": "mock-model", "runtime": "local"},
                    "template": {"id": "explain_selection", "version": "1.0.0"},
                    "claims": [{"text": "Test claim", "evidence_refs": []}],
                }
                out_path.write_text(json.dumps(draft), encoding="utf-8")
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stderr = ""
                mock_result.stdout = ""
                return mock_result

            mock_run.side_effect = side_effect

            result = run_ai_integrator_job(packet, config=config)
            assert result["schema_id"] == "advisory_draft_v1"
            assert result["kind"] == "explanation"
            assert len(result["claims"]) == 1

    def test_cli_timeout_raises_runtime_error(self, tmp_path: Path):
        """Test that CLI timeout raises AiIntegratorRuntime."""
        import subprocess

        from app.rmos.ai_advisory.config import AiIntegratorConfig
        from app.rmos.ai_advisory.exceptions import AiIntegratorRuntime
        from app.rmos.ai_advisory.runner import run_ai_integrator_job

        config = AiIntegratorConfig(
            bin_path="ai-integrator",
            timeout_sec=1,
            workdir=tmp_path,
        )

        packet = {"schema_id": "ai_context_packet_v1"}

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=1)

            with pytest.raises(AiIntegratorRuntime) as exc_info:
                run_ai_integrator_job(packet, config=config)

            assert "timed out" in str(exc_info.value).lower()

    def test_cli_not_found_raises_runtime_error(self, tmp_path: Path):
        """Test that missing binary raises AiIntegratorRuntime."""
        from app.rmos.ai_advisory.config import AiIntegratorConfig
        from app.rmos.ai_advisory.exceptions import AiIntegratorRuntime
        from app.rmos.ai_advisory.runner import run_ai_integrator_job

        config = AiIntegratorConfig(
            bin_path="/nonexistent/ai-integrator",
            timeout_sec=30,
            workdir=tmp_path,
        )

        packet = {"schema_id": "ai_context_packet_v1"}

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("binary not found")

            with pytest.raises(AiIntegratorRuntime) as exc_info:
                run_ai_integrator_job(packet, config=config)

            assert "not found" in str(exc_info.value).lower()


# =============================================================================
# API Endpoint Tests
# =============================================================================


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create test client with isolated storage."""
    advisories_dir = tmp_path / "advisories"
    advisories_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_ADVISORIES_DIR", str(advisories_dir))

    # Also set RMOS dirs for any dependencies
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))

    from app.main import app

    return TestClient(app)


class TestAdvisoryEndpoints:
    """Test advisory API endpoints."""

    def test_list_advisories_empty(self, client: TestClient):
        """Test listing advisories when none exist."""
        resp = client.get("/api/rmos/advisories")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["advisories"] == []
        assert data["count"] == 0

    def test_get_nonexistent_advisory_returns_404(self, client: TestClient):
        """Test that missing advisory returns 404."""
        resp = client.get("/api/rmos/advisories/adv_nonexistent123")
        assert resp.status_code == 404
        data = resp.json()
        assert "ADVISORY_NOT_FOUND" in data["detail"]["error"]

    def test_request_advisory_without_cli_returns_503(self, client: TestClient):
        """Test that request without ai-integrator returns 503."""
        packet = {
            "schema_id": "ai_context_packet_v1",
            "created_at_utc": "2026-01-22T12:00:00Z",
            "request": {
                "kind": "explanation",
                "template_id": "explain_selection",
                "template_version": "1.0.0",
            },
            "evidence": {
                "bundle_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "schema_id": "viewer_pack_v1",
                "selected": {
                    "pointId": "A1",
                    "freqHz": 187.5,
                    "activeRelpath": "spectra/points/A1/spectrum.csv",
                },
                "refs": [],
            },
        }

        # Without ai-integrator installed, this should return 503
        resp = client.post("/api/rmos/advisories/request", json=packet)

        # Expect 503 (AI integrator not available) or success if mocked
        assert resp.status_code in (200, 503)
        if resp.status_code == 503:
            data = resp.json()
            assert data["detail"]["error"] == "AI_INTEGRATOR_ERROR"

    def test_request_advisory_invalid_schema_returns_422(self, client: TestClient):
        """Test that invalid schema returns 422."""
        packet = {
            "schema_id": "wrong_schema",  # Invalid
            "created_at_utc": "2026-01-22T12:00:00Z",
        }

        resp = client.post("/api/rmos/advisories/request", json=packet)
        assert resp.status_code == 422

    def test_request_advisory_unsupported_kind_returns_422(self, client: TestClient):
        """Test that unsupported request kind returns 422."""
        # This tests the v1 constraint: only 'explanation' is supported
        packet = {
            "schema_id": "ai_context_packet_v1",
            "created_at_utc": "2026-01-22T12:00:00Z",
            "request": {
                "kind": "comparison",  # Not supported in v1
                "template_id": "compare_modes",
                "template_version": "1.0.0",
            },
            "evidence": {
                "bundle_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "schema_id": "viewer_pack_v1",
                "selected": {
                    "pointId": "A1",
                    "freqHz": 187.5,
                    "activeRelpath": "test.csv",
                },
                "refs": [],
            },
        }

        # First it fails Pydantic validation at endpoint level (kind enum is valid)
        # Then service-level check catches the v1 constraint
        with patch("app.rmos.ai_advisory.service.run_ai_integrator_job") as mock:
            # If validation passes to service, service raises AiIntegratorSchema
            from app.rmos.ai_advisory.exceptions import AiIntegratorSchema

            mock.side_effect = AiIntegratorSchema("Only explanation supported in v1")

            resp = client.post("/api/rmos/advisories/request", json=packet)
            # The service should catch this before calling CLI
            assert resp.status_code == 422


# =============================================================================
# Store Tests
# =============================================================================


class TestAdvisoryStore:
    """Test advisory artifact storage."""

    def test_persist_and_load_advisory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Test that we can persist and reload an advisory."""
        monkeypatch.setenv("RMOS_ADVISORIES_DIR", str(tmp_path / "advisories"))

        from app.rmos.ai_advisory.schemas import (
            AdvisoryArtifactEngine,
            AdvisoryArtifactGovernance,
            AdvisoryArtifactInput,
            AdvisoryArtifactV1,
            AdvisoryDraftClaim,
            AdvisoryDraftModel,
            AdvisoryDraftTemplate,
            AdvisoryDraftV1,
        )
        from app.rmos.ai_advisory.store import load_advisory, persist_advisory

        draft = AdvisoryDraftV1(
            schema_id="advisory_draft_v1",
            kind="explanation",
            model=AdvisoryDraftModel(id="test-model", runtime="local"),
            template=AdvisoryDraftTemplate(id="test-template", version="1.0.0"),
            claims=[AdvisoryDraftClaim(text="Test claim", evidence_refs=[])],
        )

        artifact = AdvisoryArtifactV1(
            schema_id="rmos_advisory_artifact_v1",
            advisory_id="adv_test123",
            created_at_utc="2026-01-22T12:00:00Z",
            input=AdvisoryArtifactInput(
                context_packet_sha256="abc" * 21 + "a",
                evidence_bundle_sha256="def" * 21 + "d",
            ),
            engine=AdvisoryArtifactEngine(
                model_id="test-model",
                template_id="test-template",
                template_version="1.0.0",
            ),
            draft=draft,
            governance=AdvisoryArtifactGovernance(status="draft"),
        )

        path = persist_advisory(artifact)
        assert path.exists()

        loaded = load_advisory("adv_test123")
        assert loaded is not None
        assert loaded.advisory_id == "adv_test123"
        assert loaded.draft.claims[0].text == "Test claim"

    def test_load_nonexistent_returns_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Test that loading nonexistent advisory returns None."""
        monkeypatch.setenv("RMOS_ADVISORIES_DIR", str(tmp_path / "advisories"))

        from app.rmos.ai_advisory.store import load_advisory

        result = load_advisory("adv_nonexistent")
        assert result is None
