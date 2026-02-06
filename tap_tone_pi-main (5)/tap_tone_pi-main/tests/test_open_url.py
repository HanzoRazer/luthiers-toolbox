"""Unit tests for tap_tone.util.open_url — browser URL opening.

Tests mock webbrowser — no actual browser opened.
"""
from __future__ import annotations

import os
from unittest.mock import patch, Mock

import pytest

from tap_tone.util.open_url import try_open_url


class TestTryOpenUrl:
    """Tests for try_open_url helper."""

    def test_success_returns_true(self):
        """Test successful browser open returns True."""
        with patch("webbrowser.open", return_value=True) as mock_open:
            result = try_open_url("http://localhost:8000/library")

        assert result is True
        mock_open.assert_called_once_with("http://localhost:8000/library", new=2)

    def test_failure_returns_false(self):
        """Test failed browser open returns False."""
        with patch("webbrowser.open", return_value=False):
            result = try_open_url("http://localhost:8000/library")

        assert result is False

    def test_exception_returns_false(self):
        """Test exception during open returns False (never raises)."""
        with patch("webbrowser.open", side_effect=Exception("Browser error")):
            result = try_open_url("http://localhost:8000/library")

        assert result is False

    def test_headless_linux_no_display(self):
        """Test headless Linux (no DISPLAY) returns False without calling webbrowser."""
        with patch("sys.platform", "linux"), \
             patch.dict(os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}, clear=True), \
             patch("webbrowser.open") as mock_open:
            # Clear DISPLAY and WAYLAND_DISPLAY
            os.environ.pop("DISPLAY", None)
            os.environ.pop("WAYLAND_DISPLAY", None)

            result = try_open_url("http://localhost:8000/library")

        assert result is False
        mock_open.assert_not_called()

    def test_linux_with_display(self):
        """Test Linux with DISPLAY set attempts to open."""
        with patch("sys.platform", "linux"), \
             patch.dict(os.environ, {"DISPLAY": ":0"}, clear=False), \
             patch("webbrowser.open", return_value=True) as mock_open:
            result = try_open_url("http://localhost:8000/library")

        assert result is True
        mock_open.assert_called_once()

    def test_linux_with_wayland(self):
        """Test Linux with WAYLAND_DISPLAY set attempts to open."""
        with patch("sys.platform", "linux"), \
             patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}, clear=False), \
             patch("webbrowser.open", return_value=True) as mock_open:
            result = try_open_url("http://localhost:8000/library")

        assert result is True
        mock_open.assert_called_once()

    def test_windows_always_attempts(self):
        """Test Windows platform always attempts to open."""
        with patch("sys.platform", "win32"), \
             patch("webbrowser.open", return_value=True) as mock_open:
            result = try_open_url("http://localhost:8000/library")

        assert result is True
        mock_open.assert_called_once()

    def test_macos_always_attempts(self):
        """Test macOS platform always attempts to open."""
        with patch("sys.platform", "darwin"), \
             patch("webbrowser.open", return_value=True) as mock_open:
            result = try_open_url("http://localhost:8000/library")

        assert result is True
        mock_open.assert_called_once()


class TestTryOpenUrlUrls:
    """Tests for URL handling."""

    def test_https_url(self):
        """Test HTTPS URL is passed through correctly."""
        with patch("webbrowser.open", return_value=True) as mock_open:
            try_open_url("https://toolbox.example.com/library")

        mock_open.assert_called_once_with("https://toolbox.example.com/library", new=2)

    def test_url_with_query_params(self):
        """Test URL with query parameters is passed through correctly."""
        url = "http://localhost:8000/tools/audio-analyzer/library?run_id=run_abc123"
        with patch("webbrowser.open", return_value=True) as mock_open:
            try_open_url(url)

        mock_open.assert_called_once_with(url, new=2)
