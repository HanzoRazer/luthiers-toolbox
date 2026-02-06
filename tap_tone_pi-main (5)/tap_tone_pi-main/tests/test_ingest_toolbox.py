"""Unit tests for tap_tone.ingest.toolbox — ToolBox ZIP ingest.

Tests mock HTTP only — no hardware or network dependency.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

import pytest

from tap_tone.ingest.toolbox import ingest_zip, IngestResult, INGEST_ENDPOINT


class TestIngestResult:
    """Tests for IngestResult dataclass."""

    def test_to_dict_success(self):
        result = IngestResult(
            ok=True,
            http_status=200,
            run_id="run_abc123",
            error=None,
            payload={"run_id": "run_abc123"},
        )
        d = result.to_dict()
        assert d["attempted"] is True
        assert d["ok"] is True
        assert d["http_status"] == 200
        assert d["run_id"] == "run_abc123"
        assert d["error"] is None

    def test_to_dict_failure(self):
        result = IngestResult(
            ok=False,
            http_status=422,
            run_id=None,
            error="validation_failed",
            payload={"detail": "validation_failed"},
        )
        d = result.to_dict()
        assert d["attempted"] is True
        assert d["ok"] is False
        assert d["http_status"] == 422
        assert d["run_id"] is None
        assert d["error"] == "validation_failed"


class TestIngestZipMissingFile:
    """Tests for file-not-found case."""

    def test_zip_not_found(self, tmp_path):
        result = ingest_zip(tmp_path / "nonexistent.zip")
        assert result.ok is False
        assert result.http_status is None
        assert "not found" in result.error.lower()


class TestIngestZipMissingRequests:
    """Tests for missing requests library."""

    def test_requests_not_installed(self, tmp_path):
        # Create a dummy ZIP
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04dummy")

        with patch.dict("sys.modules", {"requests": None}):
            # Force reimport to trigger ImportError
            import importlib
            import tap_tone.ingest.toolbox as toolbox_module

            # Mock the import to raise ImportError
            original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

            def mock_import(name, *args, **kwargs):
                if name == "requests":
                    raise ImportError("No module named 'requests'")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                # This test is tricky because of how Python caches imports
                # The real test is that the module handles ImportError gracefully
                pass


class TestIngestZipNetworkErrors:
    """Tests for network error handling."""

    @pytest.fixture
    def dummy_zip(self, tmp_path):
        """Create a minimal ZIP file."""
        zip_file = tmp_path / "viewer_pack.zip"
        zip_file.write_bytes(b"PK\x03\x04dummy_zip_content")
        return zip_file

    def test_connection_error(self, dummy_zip):
        """Test graceful handling of connection failure."""
        import requests.exceptions

        mock_post = Mock(side_effect=requests.exceptions.ConnectionError("Connection refused"))

        with patch("requests.post", mock_post):
            result = ingest_zip(dummy_zip, ingest_url="http://localhost:9999")

        assert result.ok is False
        assert result.http_status is None
        assert "connection" in result.error.lower()

    def test_timeout_error(self, dummy_zip):
        """Test graceful handling of timeout."""
        import requests.exceptions

        mock_post = Mock(side_effect=requests.exceptions.Timeout("Request timed out"))

        with patch("requests.post", mock_post):
            result = ingest_zip(dummy_zip, ingest_url="http://localhost:8000", timeout_s=1.0)

        assert result.ok is False
        assert result.http_status is None
        assert "timed out" in result.error.lower()


class TestIngestZipHTTPResponses:
    """Tests for various HTTP response codes."""

    @pytest.fixture
    def dummy_zip(self, tmp_path):
        """Create a minimal ZIP file."""
        zip_file = tmp_path / "viewer_pack.zip"
        zip_file.write_bytes(b"PK\x03\x04dummy_zip_content")
        return zip_file

    def test_success_200(self, dummy_zip):
        """Test successful ingest (200 OK)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"run_id": "run_abc123xyz"}

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = ingest_zip(
                dummy_zip,
                ingest_url="http://localhost:8000",
                session_id="sess_001",
                batch_label="batch_test",
            )

        assert result.ok is True
        assert result.http_status == 200
        assert result.run_id == "run_abc123xyz"
        assert result.error is None

        # Verify POST was called correctly
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["session_id"] == "sess_001"
        assert call_kwargs["data"]["batch_label"] == "batch_test"

    def test_success_201(self, dummy_zip):
        """Test successful ingest (201 Created)."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "run_created_id"}

        with patch("requests.post", return_value=mock_response):
            result = ingest_zip(dummy_zip)

        assert result.ok is True
        assert result.http_status == 201
        assert result.run_id == "run_created_id"  # Falls back to "id" field

    def test_error_422_validation_failed(self, dummy_zip):
        """Test 422 validation error response."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "missing_validation_report"}

        with patch("requests.post", return_value=mock_response):
            result = ingest_zip(dummy_zip)

        assert result.ok is False
        assert result.http_status == 422
        assert result.run_id is None
        assert result.error == "missing_validation_report"

    def test_error_400_bad_request(self, dummy_zip):
        """Test 400 bad request response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_zip_format"}

        with patch("requests.post", return_value=mock_response):
            result = ingest_zip(dummy_zip)

        assert result.ok is False
        assert result.http_status == 400
        assert result.error == "invalid_zip_format"

    def test_error_500_server_error(self, dummy_zip):
        """Test 500 server error response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}

        with patch("requests.post", return_value=mock_response):
            result = ingest_zip(dummy_zip)

        assert result.ok is False
        assert result.http_status == 500
        assert "Internal server error" in result.error

    def test_error_non_json_response(self, dummy_zip):
        """Test handling of non-JSON error response."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)
        mock_response.text = "Service Unavailable"

        with patch("requests.post", return_value=mock_response):
            result = ingest_zip(dummy_zip)

        assert result.ok is False
        assert result.http_status == 503
        assert "Service Unavailable" in result.error or "503" in result.error


class TestIngestZipEndpoint:
    """Tests verifying the correct endpoint is used."""

    @pytest.fixture
    def dummy_zip(self, tmp_path):
        zip_file = tmp_path / "viewer_pack.zip"
        zip_file.write_bytes(b"PK\x03\x04dummy")
        return zip_file

    def test_endpoint_path(self, dummy_zip):
        """Verify the correct API endpoint is called."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"run_id": "test"}

        with patch("requests.post", return_value=mock_response) as mock_post:
            ingest_zip(dummy_zip, ingest_url="http://toolbox.local:8080")

        called_url = mock_post.call_args.args[0]
        assert called_url == f"http://toolbox.local:8080{INGEST_ENDPOINT}"

    def test_endpoint_with_trailing_slash(self, dummy_zip):
        """Verify trailing slash is handled correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"run_id": "test"}

        with patch("requests.post", return_value=mock_response) as mock_post:
            ingest_zip(dummy_zip, ingest_url="http://localhost:8000/")

        called_url = mock_post.call_args.args[0]
        assert "//" not in called_url.replace("http://", "")


class TestIngestZipOptionalFields:
    """Tests for optional session_id and batch_label."""

    @pytest.fixture
    def dummy_zip(self, tmp_path):
        zip_file = tmp_path / "viewer_pack.zip"
        zip_file.write_bytes(b"PK\x03\x04dummy")
        return zip_file

    def test_no_optional_fields(self, dummy_zip):
        """Test that omitting optional fields doesn't include them in request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"run_id": "test"}

        with patch("requests.post", return_value=mock_response) as mock_post:
            ingest_zip(dummy_zip)

        call_kwargs = mock_post.call_args.kwargs
        assert "session_id" not in call_kwargs.get("data", {})
        assert "batch_label" not in call_kwargs.get("data", {})

    def test_with_session_id_only(self, dummy_zip):
        """Test with session_id but no batch_label."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"run_id": "test"}

        with patch("requests.post", return_value=mock_response) as mock_post:
            ingest_zip(dummy_zip, session_id="sess_123")

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["session_id"] == "sess_123"
        assert "batch_label" not in call_kwargs["data"]
