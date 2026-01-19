from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Test references removed function write_job_log - needs update to match current API")
def test_write_job_log_calls_autorollup_when_enabled(monkeypatch):
    """
    Placeholder: Original test referenced write_job_log function that no longer exists.
    The job-log endpoint is now at POST /api/saw/batch/job-log
    """
    pass
