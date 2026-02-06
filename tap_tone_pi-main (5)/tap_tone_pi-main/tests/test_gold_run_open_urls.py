"""Unit tests for pick_open_url — URL selection for --open-viewer.

Tests the pure function directly, no CLI or mocking needed.
"""
from __future__ import annotations

import pytest

from tap_tone.cli.gold_run import pick_open_url


class TestPickOpenUrl:
    """Tests for pick_open_url pure function."""

    def test_open_viewer_when_bundle_sha_present(self):
        """--open-viewer with bundle_sha256 → Viewer URL."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"bundle_sha256": "fd5bbaa3a6c10f83"},
            open_browser=True,
            open_viewer=True,
        )
        assert url == "http://localhost:8000/tools/audio-analyzer?sha256=fd5bbaa3a6c10f83"

    def test_open_library_when_bundle_sha_missing(self):
        """--open-viewer without bundle_sha256 → Library URL (fallback)."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={},
            open_browser=True,
            open_viewer=True,
        )
        assert url == "http://localhost:8000/tools/audio-analyzer/library"

    def test_no_open_when_no_open_flag(self):
        """--no-open → None (no URL opened)."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"bundle_sha256": "fd5bbaa3a6c10f83"},
            open_browser=False,
            open_viewer=True,
        )
        assert url is None

    def test_library_when_open_viewer_false(self):
        """Default (no --open-viewer) → Library URL even if sha present."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"bundle_sha256": "fd5bbaa3a6c10f83"},
            open_browser=True,
            open_viewer=False,
        )
        assert url == "http://localhost:8000/tools/audio-analyzer/library"

    def test_none_payload(self):
        """None payload → Library URL."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload=None,
            open_browser=True,
            open_viewer=True,
        )
        assert url == "http://localhost:8000/tools/audio-analyzer/library"

    def test_trailing_slash_stripped(self):
        """Trailing slash in ingest_url is handled correctly."""
        url = pick_open_url(
            ingest_url="http://localhost:8000/",
            payload={"bundle_sha256": "abc123"},
            open_browser=True,
            open_viewer=True,
        )
        assert "http://localhost:8000//tools" not in url
        assert url == "http://localhost:8000/tools/audio-analyzer?sha256=abc123"

    def test_https_preserved(self):
        """HTTPS base URL is preserved."""
        url = pick_open_url(
            ingest_url="https://toolbox.example.com",
            payload={"bundle_sha256": "xyz789"},
            open_browser=True,
            open_viewer=True,
        )
        assert url.startswith("https://toolbox.example.com/")

    def test_library_url_no_run_id(self):
        """Library URL works without run_id in payload."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"some_other_field": "value"},
            open_browser=True,
            open_viewer=False,
        )
        assert url == "http://localhost:8000/tools/audio-analyzer/library"

    def test_non_dict_payload_treated_as_none(self):
        """Non-dict payload treated same as None."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload="not_a_dict",  # type: ignore
            open_browser=True,
            open_viewer=True,
        )
        assert url == "http://localhost:8000/tools/audio-analyzer/library"


class TestPickOpenUrlEdgeCases:
    """Edge case tests for pick_open_url."""

    def test_empty_bundle_sha(self):
        """Empty string bundle_sha256 treated as missing."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"bundle_sha256": ""},
            open_browser=True,
            open_viewer=True,
        )
        # Empty string is falsy, so falls back to library
        assert url == "http://localhost:8000/tools/audio-analyzer/library"

    def test_both_flags_false(self):
        """Both open_browser=False and open_viewer=False → None."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"bundle_sha256": "abc123"},
            open_browser=False,
            open_viewer=False,
        )
        assert url is None

    def test_custom_port(self):
        """Custom port in URL is preserved."""
        url = pick_open_url(
            ingest_url="http://192.168.1.100:9000",
            payload={"bundle_sha256": "sha_value"},
            open_browser=True,
            open_viewer=True,
        )
        assert url == "http://192.168.1.100:9000/tools/audio-analyzer?sha256=sha_value"


class TestUrlPrintingContract:
    """Tests for URL printing contract.

    When a URL is selected (not None), the CLI must print 'URL: <url>'
    for copy/share, regardless of whether the browser opens successfully.
    """

    def test_url_line_format_library(self):
        """Library URL follows expected format for grep/parsing."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={},
            open_browser=True,
            open_viewer=False,
        )
        assert url is not None
        # The CLI prints f"    URL: {url}" — verify URL is suitable
        assert url.startswith("http")
        assert "/tools/audio-analyzer/library" in url

    def test_url_line_format_viewer(self):
        """Viewer URL follows expected format for grep/parsing."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"bundle_sha256": "fd5bbaa3"},
            open_browser=True,
            open_viewer=True,
        )
        assert url is not None
        assert "sha256=fd5bbaa3" in url

    def test_no_url_when_no_open(self):
        """--no-open produces no URL (prints 'Browser: skipped')."""
        url = pick_open_url(
            ingest_url="http://localhost:8000",
            payload={"bundle_sha256": "fd5bbaa3"},
            open_browser=False,
            open_viewer=True,
        )
        assert url is None  # CLI prints "Browser: skipped (--no-open)"
