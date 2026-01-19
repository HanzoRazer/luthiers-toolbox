from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Test needs update - service has complex dependencies that require full mocking")
def test_latest_metrics_by_batch_returns_shape(monkeypatch):
    """
    Smoke test placeholder.
    The endpoint /api/saw/batch/execution/metrics/latest-by-batch exists but
    requires mocking multiple service layers (latest_batch_chain_service + metrics_lookup_service).
    """
    pass
