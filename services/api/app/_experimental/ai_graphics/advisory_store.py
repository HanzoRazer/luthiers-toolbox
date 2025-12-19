"""
Advisory Asset Store

Persists AI-generated advisory assets separately from run artifacts.
This maintains the trust boundary - AI writes here, not to run_artifacts.

Integrates with existing:
- image_providers.py (GuitarVisionEngine, AiImageResult)
- schemas/advisory_schemas.py (AdvisoryAsset)
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from .schemas.advisory_schemas import AdvisoryAsset, AdvisoryAssetType


def _get_advisory_root() -> Path:
    """Get the root directory for advisory asset storage."""
    root = os.environ.get("ADVISORY_ASSETS_ROOT", "data/advisory_assets")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


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


# Module singleton
_store: Optional[AdvisoryAssetStore] = None


def get_advisory_store() -> AdvisoryAssetStore:
    """Get or create the advisory asset store singleton."""
    global _store
    if _store is None:
        _store = AdvisoryAssetStore()
    return _store


def reset_advisory_store() -> None:
    """Reset singleton (for testing)."""
    global _store
    _store = None
