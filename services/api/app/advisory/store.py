"""
Advisory Asset Store (Neutral Zone)

Persists AI-generated advisory assets separately from run artifacts.
This maintains the trust boundary - AI writes here, not to run_artifacts.

This module is the NEUTRAL ZONE for advisory storage.
Both AI sandbox and RMOS code may import from here.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from app.advisory.schemas import (
    AdvisoryAsset,
    AdvisoryAssetType,
    PromptHistoryEntry,
    BudgetConfig,
    BudgetStatus,
    RequestRecord,
)


def _get_advisory_root() -> Path:
    """Get the root directory for advisory asset storage."""
    root = os.environ.get("ADVISORY_ASSETS_ROOT", "data/advisory_assets")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_prompt_history_root() -> Path:
    """Get the root directory for prompt history storage."""
    root = os.environ.get("PROMPT_HISTORY_ROOT", "data/prompt_history")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def compute_prompt_hash(prompt: str) -> str:
    """
    Compute a normalized hash for duplicate detection.
    
    Normalizes: lowercase, strip whitespace, remove punctuation
    """
    import re
    normalized = prompt.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _date_partition(dt: datetime) -> str:
    """Generate date-based partition path: YYYY/MM/DD"""
    return f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"


def compute_content_hash(content: bytes) -> str:
    """SHA256 hash of content bytes."""
    return hashlib.sha256(content).hexdigest()


class AdvisoryAssetStore:
    """
    Storage for AI-generated advisory assets.
    
    GOVERNANCE: This store is SEPARATE from RunStore.
    AI can write here, but cannot write to run_artifacts.
    """
    
    def __init__(self, root: Optional[Path] = None):
        if root is None:
            self.root = _get_advisory_root()
        elif isinstance(root, str):
            self.root = Path(root)
        else:
            self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
    
    def _asset_dir(self, asset: AdvisoryAsset) -> Path:
        partition = _date_partition(asset.created_at_utc)
        return self.root / partition
    
    def _asset_meta_path(self, asset: AdvisoryAsset) -> Path:
        return self._asset_dir(asset) / f"{asset.asset_id}.json"
    
    def _asset_content_path(self, asset: AdvisoryAsset, ext: str = "bin") -> Path:
        return self._asset_dir(asset) / f"{asset.asset_id}_content.{ext}"
    
    def save_asset(
        self,
        asset: AdvisoryAsset,
        content: Optional[bytes] = None,
    ) -> str:
        """
        Save advisory asset metadata and optionally content.
        
        Returns content_uri if content was saved.
        """
        asset_dir = self._asset_dir(asset)
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        if content:
            ext = asset.image_format or "bin"
            content_path = self._asset_content_path(asset, ext)
            content_path.write_bytes(content)
            asset.content_uri = str(content_path.relative_to(self.root))
            asset.content_size_bytes = len(content)
            
            computed_hash = compute_content_hash(content)
            if asset.content_hash and asset.content_hash != computed_hash:
                raise ValueError(f"Content hash mismatch: expected {asset.content_hash}, got {computed_hash}")
            asset.content_hash = computed_hash
        
        meta_path = self._asset_meta_path(asset)
        meta_path.write_text(asset.model_dump_json(indent=2))
        
        return asset.content_uri or ""
    
    def get_asset(self, asset_id: str) -> Optional[AdvisoryAsset]:
        """Retrieve advisory asset by ID."""
        for year_dir in sorted(self.root.glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    meta_path = day_dir / f"{asset_id}.json"
                    if meta_path.exists():
                        return AdvisoryAsset.model_validate_json(meta_path.read_text())
        return None
    
    def get_asset_content(self, asset: AdvisoryAsset) -> Optional[bytes]:
        """Retrieve asset content bytes."""
        if not asset.content_uri:
            return None
        content_path = self.root / asset.content_uri
        if content_path.exists():
            return content_path.read_bytes()
        return None
    
    def update_asset(self, asset: AdvisoryAsset) -> None:
        """Update asset metadata (e.g., after review)."""
        meta_path = self._asset_meta_path(asset)
        if not meta_path.exists():
            raise ValueError(f"Asset {asset.asset_id} not found")
        meta_path.write_text(asset.model_dump_json(indent=2))
    
    def list_assets(
        self,
        *,
        asset_type: Optional[AdvisoryAssetType] = None,
        reviewed: Optional[bool] = None,
        approved: Optional[bool] = None,
        limit: int = 50,
    ) -> List[AdvisoryAsset]:
        """List advisory assets with optional filters."""
        assets = []
        
        for year_dir in sorted(self.root.glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    
                    for meta_path in sorted(day_dir.glob("adv_*.json"), reverse=True):
                        if len(assets) >= limit:
                            return assets
                        
                        # Skip content files
                        if "_content" in meta_path.name:
                            continue
                        
                        try:
                            asset = AdvisoryAsset.model_validate_json(meta_path.read_text())
                        except Exception:
                            continue
                        
                        if asset_type and asset.asset_type != asset_type:
                            continue
                        if reviewed is not None and asset.reviewed != reviewed:
                            continue
                        if approved is not None and asset.approved_for_workflow != approved:
                            continue
                        
                        assets.append(asset)
        
        return assets
    
    def count_pending_review(self) -> int:
        """Count assets pending review."""
        return len(self.list_assets(reviewed=False, limit=1000))
    
    def find_by_prompt_hash(self, prompt_hash: str, limit: int = 10) -> List[AdvisoryAsset]:
        """Find assets with matching prompt hash (exact duplicates)."""
        all_assets = self.list_assets(limit=10000)
        return [a for a in all_assets if a.prompt_hash == prompt_hash][:limit]
    
    def find_similar_prompts(
        self,
        prompt: str,
        threshold: float = 0.8,
        limit: int = 10,
    ) -> List[tuple]:
        """
        Find assets with similar prompts using simple word overlap.
        
        Returns list of (asset, similarity_score) tuples.
        """
        import re
        
        # Tokenize and normalize input prompt
        def tokenize(text: str) -> set:
            words = re.findall(r'\w+', text.lower())
            return set(words)
        
        prompt_tokens = tokenize(prompt)
        if not prompt_tokens:
            return []
        
        all_assets = self.list_assets(limit=10000)
        results = []
        
        for asset in all_assets:
            asset_tokens = tokenize(asset.prompt)
            if not asset_tokens:
                continue
            
            # Jaccard similarity
            intersection = len(prompt_tokens & asset_tokens)
            union = len(prompt_tokens | asset_tokens)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= threshold:
                results.append((asset, similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


class PromptHistoryStore:
    """
    Storage for prompt history tracking.
    
    Stores prompts by user/session for reuse and analysis.
    """
    
    def __init__(self, root: Optional[Path] = None):
        if root is None:
            self.root = _get_prompt_history_root()
        elif isinstance(root, str):
            self.root = Path(root)
        else:
            self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
    
    def _user_dir(self, user_id: str) -> Path:
        """Get directory for a user's prompts."""
        safe_user = user_id.replace("/", "_").replace("\\", "_")
        return self.root / "users" / safe_user
    
    def _session_dir(self, session_id: str) -> Path:
        """Get directory for a session's prompts."""
        safe_session = session_id.replace("/", "_").replace("\\", "_")
        return self.root / "sessions" / safe_session
    
    def save_prompt(self, entry: PromptHistoryEntry) -> str:
        """Save a prompt history entry."""
        # Save by user if user_id provided
        if entry.user_id:
            user_dir = self._user_dir(entry.user_id)
            user_dir.mkdir(parents=True, exist_ok=True)
            user_path = user_dir / f"{entry.prompt_id}.json"
            user_path.write_text(entry.model_dump_json(indent=2))
        
        # Save by session if session_id provided
        if entry.session_id:
            session_dir = self._session_dir(entry.session_id)
            session_dir.mkdir(parents=True, exist_ok=True)
            session_path = session_dir / f"{entry.prompt_id}.json"
            session_path.write_text(entry.model_dump_json(indent=2))
        
        # Also save to global history (date-partitioned)
        partition = _date_partition(entry.created_at_utc)
        global_dir = self.root / "all" / partition
        global_dir.mkdir(parents=True, exist_ok=True)
        global_path = global_dir / f"{entry.prompt_id}.json"
        global_path.write_text(entry.model_dump_json(indent=2))
        
        return entry.prompt_id
    
    def get_prompt(self, prompt_id: str) -> Optional[PromptHistoryEntry]:
        """Get a prompt by ID."""
        # Search in global history
        for year_dir in sorted((self.root / "all").glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    path = day_dir / f"{prompt_id}.json"
                    if path.exists():
                        return PromptHistoryEntry.model_validate_json(path.read_text())
        return None
    
    def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        templates_only: bool = False,
    ) -> List[PromptHistoryEntry]:
        """List prompts for a user."""
        user_dir = self._user_dir(user_id)
        if not user_dir.exists():
            return []
        
        prompts = []
        for path in sorted(user_dir.glob("pmt_*.json"), reverse=True):
            if len(prompts) >= limit:
                break
            try:
                entry = PromptHistoryEntry.model_validate_json(path.read_text())
                if templates_only and not entry.is_template:
                    continue
                prompts.append(entry)
            except Exception:
                continue
        
        return prompts
    
    def list_by_session(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[PromptHistoryEntry]:
        """List prompts for a session."""
        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            return []
        
        prompts = []
        for path in sorted(session_dir.glob("pmt_*.json"), reverse=True):
            if len(prompts) >= limit:
                break
            try:
                entry = PromptHistoryEntry.model_validate_json(path.read_text())
                prompts.append(entry)
            except Exception:
                continue
        
        return prompts
    
    def list_recent(self, limit: int = 50) -> List[PromptHistoryEntry]:
        """List recent prompts across all users/sessions."""
        prompts = []
        all_dir = self.root / "all"
        if not all_dir.exists():
            return []
        
        for year_dir in sorted(all_dir.glob("*"), reverse=True):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*"), reverse=True):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.glob("*"), reverse=True):
                    if not day_dir.is_dir():
                        continue
                    for path in sorted(day_dir.glob("pmt_*.json"), reverse=True):
                        if len(prompts) >= limit:
                            return prompts
                        try:
                            entry = PromptHistoryEntry.model_validate_json(path.read_text())
                            prompts.append(entry)
                        except Exception:
                            continue
        
        return prompts
    
    def mark_as_template(
        self,
        prompt_id: str,
        template_name: str,
    ) -> Optional[PromptHistoryEntry]:
        """Mark a prompt as a reusable template."""
        entry = self.get_prompt(prompt_id)
        if entry is None:
            return None
        
        entry.is_template = True
        entry.template_name = template_name
        
        # Re-save with updated fields
        self.save_prompt(entry)
        return entry
    
    def increment_reuse(self, prompt_id: str) -> Optional[PromptHistoryEntry]:
        """Increment the reuse counter for a prompt."""
        entry = self.get_prompt(prompt_id)
        if entry is None:
            return None
        
        entry.times_reused += 1
        self.save_prompt(entry)
        return entry
    
    def search_prompts(
        self,
        query: str,
        limit: int = 20,
    ) -> List[PromptHistoryEntry]:
        """Simple text search across prompts."""
        query_lower = query.lower()
        results = []
        
        for entry in self.list_recent(limit=500):
            if query_lower in entry.user_prompt.lower():
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results


class BudgetTracker:
    """
    Tracks spending against configurable budget limits.
    
    Supports daily, weekly, monthly, and total limits.
    """
    
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
            except Exception:
                self._config = BudgetConfig()
        else:
            self._config = BudgetConfig()
        
        return self._config
    
    def set_config(self, config: BudgetConfig) -> None:
        """Update budget configuration."""
        self._config = config
        self._config_path.write_text(config.model_dump_json(indent=2))
    
    def get_spending(self, advisory_store: "AdvisoryAssetStore") -> dict:
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
    
    def get_status(self, advisory_store: "AdvisoryAssetStore") -> BudgetStatus:
        """Get current budget status with spending and limits."""
        config = self.get_config()
        spending = self.get_spending(advisory_store)
        
        alerts = []
        threshold = config.alert_threshold_pct / 100.0
        
        # Calculate remaining and check exceeded
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
    
    def can_afford(
        self,
        cost: float,
        advisory_store: "AdvisoryAssetStore",
    ) -> tuple:
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
    """
    Stores request records for correlation and audit.
    
    Ties into global request_id tracking from middleware.
    """
    
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
                        except Exception:
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
                        except Exception:
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
                        except Exception:
                            continue
        return records


# Module singletons
_store: Optional[AdvisoryAssetStore] = None
_prompt_store: Optional[PromptHistoryStore] = None
_budget_tracker: Optional[BudgetTracker] = None
_request_store: Optional[RequestRecordStore] = None


def get_advisory_store() -> AdvisoryAssetStore:
    """Get or create the advisory asset store singleton."""
    global _store
    if _store is None:
        _store = AdvisoryAssetStore()
    return _store


def get_prompt_history_store() -> PromptHistoryStore:
    """Get or create the prompt history store singleton."""
    global _prompt_store
    if _prompt_store is None:
        _prompt_store = PromptHistoryStore()
    return _prompt_store


def get_budget_tracker() -> BudgetTracker:
    """Get or create the budget tracker singleton."""
    global _budget_tracker
    if _budget_tracker is None:
        _budget_tracker = BudgetTracker()
    return _budget_tracker


def get_request_store() -> RequestRecordStore:
    """Get or create the request record store singleton."""
    global _request_store
    if _request_store is None:
        _request_store = RequestRecordStore()
    return _request_store


def reset_advisory_store() -> None:
    """Reset singleton (for testing)."""
    global _store
    _store = None


def reset_prompt_store() -> None:
    """Reset singleton (for testing)."""
    global _prompt_store
    _prompt_store = None


def reset_budget_tracker() -> None:
    """Reset singleton (for testing)."""
    global _budget_tracker
    _budget_tracker = None


def reset_request_store() -> None:
    """Reset singleton (for testing)."""
    global _request_store
    _request_store = None
