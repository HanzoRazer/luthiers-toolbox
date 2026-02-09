"""Budget tracking and request record storage for Advisory system."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.advisory.schemas import (
    BudgetConfig,
    BudgetStatus,
    RequestRecord,
)


def _get_budget_root() -> Path:
    """Get the root directory for budget tracking."""
    root = os.environ.get("BUDGET_TRACKING_ROOT", "data/budget")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_request_log_root() -> Path:
    """Get the root directory for request logging."""
    root = os.environ.get("REQUEST_LOG_ROOT", "data/request_log")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


class BudgetTracker:
    """Tracks spending against configurable budget limits."""

    def __init__(self, root: Optional[Path] = None):
        if root is None:
            self.root = _get_budget_root()
        elif isinstance(root, str):
            self.root = Path(root)
        else:
            self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

        self._config_path = self.root / "config.json"
        self._config: Optional[BudgetConfig] = None

    def get_config(self) -> BudgetConfig:
        """Get current budget configuration."""
        if self._config is not None:
            return self._config

        if self._config_path.exists():
            try:
                self._config = BudgetConfig.model_validate_json(self._config_path.read_text())
            except (ValueError, OSError):
                self._config = BudgetConfig()
        else:
            self._config = BudgetConfig()

        return self._config

    def set_config(self, config: BudgetConfig) -> None:
        """Update budget configuration."""
        self._config = config
        self._config_path.write_text(config.model_dump_json(indent=2))

    def get_spending(self, advisory_store) -> dict:
        """Calculate spending totals from advisory assets."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        all_assets = advisory_store.list_assets(limit=10000)

        spent_today = 0.0
        spent_week = 0.0
        spent_month = 0.0
        spent_total = 0.0

        for asset in all_assets:
            cost = asset.cost_usd or 0.0
            spent_total += cost

            created = asset.created_at_utc
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            if created >= today_start:
                spent_today += cost
            if created >= week_start:
                spent_week += cost
            if created >= month_start:
                spent_month += cost

        return {
            "today": round(spent_today, 4),
            "week": round(spent_week, 4),
            "month": round(spent_month, 4),
            "total": round(spent_total, 4),
        }

    def get_status(self, advisory_store) -> BudgetStatus:
        """Get current budget status with spending and limits."""
        config = self.get_config()
        spending = self.get_spending(advisory_store)

        alerts = []
        threshold = config.alert_threshold_pct / 100.0

        daily_remaining = None
        daily_exceeded = False
        if config.daily_limit_usd is not None:
            daily_remaining = max(0, config.daily_limit_usd - spending["today"])
            daily_exceeded = spending["today"] >= config.daily_limit_usd
            if spending["today"] >= config.daily_limit_usd * threshold:
                pct = (spending["today"] / config.daily_limit_usd) * 100
                alerts.append(f"Daily budget at {pct:.0f}%")

        weekly_remaining = None
        weekly_exceeded = False
        if config.weekly_limit_usd is not None:
            weekly_remaining = max(0, config.weekly_limit_usd - spending["week"])
            weekly_exceeded = spending["week"] >= config.weekly_limit_usd
            if spending["week"] >= config.weekly_limit_usd * threshold:
                pct = (spending["week"] / config.weekly_limit_usd) * 100
                alerts.append(f"Weekly budget at {pct:.0f}%")

        monthly_remaining = None
        monthly_exceeded = False
        if config.monthly_limit_usd is not None:
            monthly_remaining = max(0, config.monthly_limit_usd - spending["month"])
            monthly_exceeded = spending["month"] >= config.monthly_limit_usd
            if spending["month"] >= config.monthly_limit_usd * threshold:
                pct = (spending["month"] / config.monthly_limit_usd) * 100
                alerts.append(f"Monthly budget at {pct:.0f}%")

        total_remaining = None
        total_exceeded = False
        if config.total_limit_usd is not None:
            total_remaining = max(0, config.total_limit_usd - spending["total"])
            total_exceeded = spending["total"] >= config.total_limit_usd
            if spending["total"] >= config.total_limit_usd * threshold:
                pct = (spending["total"] / config.total_limit_usd) * 100
                alerts.append(f"Total budget at {pct:.0f}%")

        any_exceeded = daily_exceeded or weekly_exceeded or monthly_exceeded or total_exceeded

        return BudgetStatus(
            spent_today_usd=spending["today"],
            spent_this_week_usd=spending["week"],
            spent_this_month_usd=spending["month"],
            spent_total_usd=spending["total"],
            daily_limit_usd=config.daily_limit_usd,
            weekly_limit_usd=config.weekly_limit_usd,
            monthly_limit_usd=config.monthly_limit_usd,
            total_limit_usd=config.total_limit_usd,
            daily_remaining_usd=daily_remaining,
            weekly_remaining_usd=weekly_remaining,
            monthly_remaining_usd=monthly_remaining,
            total_remaining_usd=total_remaining,
            daily_exceeded=daily_exceeded,
            weekly_exceeded=weekly_exceeded,
            monthly_exceeded=monthly_exceeded,
            total_exceeded=total_exceeded,
            any_limit_exceeded=any_exceeded,
            alerts=alerts,
        )

    def can_afford(self, cost: float, advisory_store) -> tuple:
        """Check if a cost fits within budget limits."""
        status = self.get_status(advisory_store)

        warnings = []
        can_afford = True

        if status.daily_remaining_usd is not None:
            if cost > status.daily_remaining_usd:
                can_afford = False
                warnings.append(f"Exceeds daily budget (${status.daily_remaining_usd:.2f} remaining)")

        if status.weekly_remaining_usd is not None:
            if cost > status.weekly_remaining_usd:
                can_afford = False
                warnings.append(f"Exceeds weekly budget (${status.weekly_remaining_usd:.2f} remaining)")

        if status.monthly_remaining_usd is not None:
            if cost > status.monthly_remaining_usd:
                can_afford = False
                warnings.append(f"Exceeds monthly budget (${status.monthly_remaining_usd:.2f} remaining)")

        if status.total_remaining_usd is not None:
            if cost > status.total_remaining_usd:
                can_afford = False
                warnings.append(f"Exceeds total budget (${status.total_remaining_usd:.2f} remaining)")

        return can_afford, warnings


class RequestRecordStore:
    """Stores request records for correlation and audit."""

    def __init__(self, root: Optional[Path] = None):
        if root is None:
            self.root = _get_request_log_root()
        elif isinstance(root, str):
            self.root = Path(root)
        else:
            self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _date_dir(self, dt: datetime) -> Path:
        """Get directory for a date."""
        return self.root / f"{dt.year:04d}" / f"{dt.month:02d}" / f"{dt.day:02d}"

    def save_record(self, record: RequestRecord) -> str:
        """Save a request record."""
        record_dir = self._date_dir(record.created_at_utc)
        record_dir.mkdir(parents=True, exist_ok=True)

        record_path = record_dir / f"{record.record_id}.json"
        record_path.write_text(record.model_dump_json(indent=2))

        return record.record_id

    def get_record(self, record_id: str) -> Optional[RequestRecord]:
        """Get a record by ID."""
        for year_dir in sorted(self.root.glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    path = day_dir / f"{record_id}.json"
                    if path.exists():
                        return RequestRecord.model_validate_json(path.read_text())
        return None

    def find_by_request_id(self, request_id: str) -> List[RequestRecord]:
        """Find all records for a global request_id."""
        results = []
        for year_dir in sorted(self.root.glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    for path in day_dir.glob("req_*.json"):
                        try:
                            record = RequestRecord.model_validate_json(path.read_text())
                            if record.request_id == request_id:
                                results.append(record)
                        except (ValueError, OSError):
                            continue
        return results

    def find_by_asset_id(self, asset_id: str) -> List[RequestRecord]:
        """Find all records for an asset."""
        results = []
        for year_dir in sorted(self.root.glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    for path in day_dir.glob("req_*.json"):
                        try:
                            record = RequestRecord.model_validate_json(path.read_text())
                            if record.asset_id == asset_id:
                                results.append(record)
                        except (ValueError, OSError):
                            continue
        return results

    def list_recent(self, limit: int = 100) -> List[RequestRecord]:
        """List recent request records."""
        records = []
        for year_dir in sorted(self.root.glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    for path in sorted(day_dir.glob("req_*.json"), reverse=True):
                        if len(records) >= limit:
                            return records
                        try:
                            record = RequestRecord.model_validate_json(path.read_text())
                            records.append(record)
                        except (ValueError, OSError):
                            continue
        return records


# Alias for backwards compatibility
RequestStore = RequestRecordStore
