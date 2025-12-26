import os
import json
from pathlib import Path

import pytest

from app.governance.deprecation_budget import compute_deprecation_budget, get_budget_config


@pytest.mark.unit
def test_deprecation_budget_contract_smoke(tmp_path, monkeypatch):
    """
    Ensures the deprecation budget checker can run deterministically in CI.
    This does NOT enforce removal; enforcement happens only after configured date.
    """
    stats_path = tmp_path / "endpoint_shadow_stats.json"
    monkeypatch.setenv("ENDPOINT_STATS_PATH", str(stats_path))

    # Pre-enforcement default should always pass (enforce date defaults far future)
    stats = {
        "total_hits": 0,
        "legacy_hits": 0,
        "by_legacy_route": {},
        "window": {"kind": "since_start"},
        "generated_at_utc": "2025-12-25T00:00:00Z",
    }
    stats_path.write_text(json.dumps(stats), encoding="utf-8")

    cfg = get_budget_config()
    res = compute_deprecation_budget(stats, cfg)
    assert res.ok is True


@pytest.mark.unit
def test_deprecation_budget_passes_before_enforce_date(tmp_path, monkeypatch):
    """
    Before enforce date, should always pass even with legacy hits.
    """
    stats_path = tmp_path / "endpoint_shadow_stats.json"
    monkeypatch.setenv("ENDPOINT_STATS_PATH", str(stats_path))
    monkeypatch.setenv("DEPRECATION_BUDGET_ENFORCE_AFTER", "2099-01-01")
    monkeypatch.setenv("DEPRECATION_BUDGET_LEGACY_HITS_MAX", "0")

    stats = {
        "total_hits": 100,
        "legacy_hits": 50,  # 50% legacy - would fail if enforced
        "by_legacy_route": {"/api/old": 50},
        "window": {"kind": "since_start"},
        "generated_at_utc": "2025-12-25T00:00:00Z",
    }
    stats_path.write_text(json.dumps(stats), encoding="utf-8")

    cfg = get_budget_config()
    res = compute_deprecation_budget(stats, cfg)

    assert res.ok is True
    assert res.enforced is False
    assert res.legacy_hits == 50
    assert res.legacy_rate == 0.5


@pytest.mark.unit
def test_deprecation_budget_fails_after_enforce_date(tmp_path, monkeypatch):
    """
    After enforce date, should fail if legacy hits exceed max.
    """
    stats_path = tmp_path / "endpoint_shadow_stats.json"
    monkeypatch.setenv("ENDPOINT_STATS_PATH", str(stats_path))
    monkeypatch.setenv("DEPRECATION_BUDGET_ENFORCE_AFTER", "2020-01-01")  # Past date
    monkeypatch.setenv("DEPRECATION_BUDGET_LEGACY_HITS_MAX", "0")
    monkeypatch.setenv("DEPRECATION_BUDGET_MIN_TOTAL_HITS", "1")

    stats = {
        "total_hits": 100,
        "legacy_hits": 5,
        "by_legacy_route": {"/api/old": 5},
        "window": {"kind": "since_start"},
        "generated_at_utc": "2025-12-25T00:00:00Z",
    }
    stats_path.write_text(json.dumps(stats), encoding="utf-8")

    cfg = get_budget_config()
    res = compute_deprecation_budget(stats, cfg)

    assert res.ok is False
    assert res.enforced is True
    assert "legacy_hits 5 > legacy_hits_max 0" in res.reason


@pytest.mark.unit
def test_deprecation_budget_skips_enforcement_on_low_traffic(tmp_path, monkeypatch):
    """
    Should skip enforcement if total_hits < min_total_hits.
    """
    stats_path = tmp_path / "endpoint_shadow_stats.json"
    monkeypatch.setenv("ENDPOINT_STATS_PATH", str(stats_path))
    monkeypatch.setenv("DEPRECATION_BUDGET_ENFORCE_AFTER", "2020-01-01")
    monkeypatch.setenv("DEPRECATION_BUDGET_MIN_TOTAL_HITS", "100")

    stats = {
        "total_hits": 10,  # Below min
        "legacy_hits": 10,
        "by_legacy_route": {},
        "window": {"kind": "since_start"},
        "generated_at_utc": "2025-12-25T00:00:00Z",
    }
    stats_path.write_text(json.dumps(stats), encoding="utf-8")

    cfg = get_budget_config()
    res = compute_deprecation_budget(stats, cfg)

    assert res.ok is True
    assert res.enforced is True
    assert "skipping enforcement" in res.reason
