from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DeprecationBudgetConfig:
    enforce_after_utc: datetime
    legacy_hits_max: int
    legacy_rate_max: float  # fraction 0..1
    min_total_hits: int
    stats_path: str


@dataclass(frozen=True)
class DeprecationBudgetResult:
    ok: bool
    enforced: bool
    total_hits: int
    legacy_hits: int
    legacy_rate: float
    reason: Optional[str]


def _parse_utc_dt(s: str) -> datetime:
    """
    Parse UTC datetime. Accepts:
      - 2025-12-31
      - 2025-12-31T00:00:00Z
      - 2025-12-31T00:00:00+00:00
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("empty datetime")
    if len(s) == 10:
        # YYYY-MM-DD
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=timezone.utc)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_budget_config() -> DeprecationBudgetConfig:
    enforce_after = os.getenv("DEPRECATION_BUDGET_ENFORCE_AFTER", "2099-01-01")
    legacy_hits_max = int(os.getenv("DEPRECATION_BUDGET_LEGACY_HITS_MAX", "0"))
    legacy_rate_max = float(os.getenv("DEPRECATION_BUDGET_LEGACY_RATE_MAX", "0.0"))
    min_total_hits = int(os.getenv("DEPRECATION_BUDGET_MIN_TOTAL_HITS", "1"))

    # This should point at the file written by your shadow-usage aggregator.
    # If you don't have one yet, add it in H5.1/H5.2 (see Patch #3 below).
    stats_path = os.getenv("ENDPOINT_STATS_PATH", "services/api/data/endpoint_shadow_stats.json")

    return DeprecationBudgetConfig(
        enforce_after_utc=_parse_utc_dt(enforce_after),
        legacy_hits_max=legacy_hits_max,
        legacy_rate_max=legacy_rate_max,
        min_total_hits=min_total_hits,
        stats_path=stats_path,
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def load_shadow_stats(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_deprecation_budget(stats: Dict[str, Any], cfg: DeprecationBudgetConfig) -> DeprecationBudgetResult:
    """
    Expected minimal stats shape (stable + future-proof):

    {
      "total_hits": 1234,
      "legacy_hits": 12,
      "by_legacy_route": {
        "/api/old/x": 7,
        "/api/old/y": 5
      },
      "window": {"kind": "since_start"|"rolling", "seconds": 3600},
      "generated_at_utc": "2025-12-25T00:00:00Z"
    }
    """
    total_hits = int(stats.get("total_hits", 0))
    legacy_hits = int(stats.get("legacy_hits", 0))

    legacy_rate = (legacy_hits / total_hits) if total_hits > 0 else 0.0

    now = _utcnow()
    enforced = now >= cfg.enforce_after_utc

    # Before enforcement date: always pass, but report numbers.
    if not enforced:
        return DeprecationBudgetResult(
            ok=True,
            enforced=False,
            total_hits=total_hits,
            legacy_hits=legacy_hits,
            legacy_rate=legacy_rate,
            reason=None,
        )

    # On/after enforcement date:
    if total_hits < cfg.min_total_hits:
        # No traffic => treat as pass (avoid blocking CI on empty stats)
        return DeprecationBudgetResult(
            ok=True,
            enforced=True,
            total_hits=total_hits,
            legacy_hits=legacy_hits,
            legacy_rate=legacy_rate,
            reason=f"total_hits {total_hits} < min_total_hits {cfg.min_total_hits}; skipping enforcement",
        )

    failures = []
    if cfg.legacy_hits_max >= 0 and legacy_hits > cfg.legacy_hits_max:
        failures.append(f"legacy_hits {legacy_hits} > legacy_hits_max {cfg.legacy_hits_max}")
    if 0.0 <= cfg.legacy_rate_max <= 1.0 and legacy_rate > cfg.legacy_rate_max:
        failures.append(f"legacy_rate {legacy_rate:.6f} > legacy_rate_max {cfg.legacy_rate_max:.6f}")

    ok = len(failures) == 0
    reason = "; ".join(failures) if failures else None

    return DeprecationBudgetResult(
        ok=ok,
        enforced=True,
        total_hits=total_hits,
        legacy_hits=legacy_hits,
        legacy_rate=legacy_rate,
        reason=reason,
    )
