from __future__ import annotations

import os
from unittest.mock import patch

from app.saw_lab.execution_metrics_autorollup import (
    is_execution_metrics_autorollup_enabled,
    maybe_autorollup_execution_metrics,
)


def test_autorollup_disabled_by_default():
    """With no env var, autorollup should be disabled."""
    with patch.dict(os.environ, {}, clear=True):
        assert is_execution_metrics_autorollup_enabled() is False


def test_autorollup_enabled_when_env_set(monkeypatch):
    """Setting the feature flag enables autorollup."""
    monkeypatch.setenv("SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED", "true")
    assert is_execution_metrics_autorollup_enabled() is True


def test_maybe_autorollup_returns_none_when_disabled(monkeypatch):
    """When disabled, maybe_autorollup returns None without calling service."""
    monkeypatch.setenv("SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED", "false")
    result = maybe_autorollup_execution_metrics(
        batch_execution_artifact_id="ex-001",
        session_id="sess-001",
        batch_label="batch-A",
    )
    assert result is None


def test_maybe_autorollup_returns_none_when_no_execution_id(monkeypatch):
    """When execution id is None, autorollup is a no-op."""
    monkeypatch.setenv("SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED", "true")
    result = maybe_autorollup_execution_metrics(
        batch_execution_artifact_id=None,
        session_id="sess-001",
        batch_label="batch-A",
    )
    assert result is None
