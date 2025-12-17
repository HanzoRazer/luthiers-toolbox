"""
Design Snapshot Store - Bundle 31.0.4

File-backed JSON store for design snapshots.
Layout: {data_root}/art_studio/snapshots/{snapshot_id}.json
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from ..schemas.design_snapshot import (
    DesignSnapshot,
    DesignContextRefs,
    SnapshotCreateRequest,
    SnapshotSummary,
    SnapshotUpdateRequest,
)


_VALID_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{6,80}$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_data_root() -> Path:
    app_root = Path(__file__).resolve().parents[2]
    return app_root / "data"


def resolve_art_studio_data_root() -> Path:
    """
    Same resolution convention used by PatternStore.
    Priority:
    1) ART_STUDIO_DATA_ROOT
    2) RMOS_DATA_ROOT
    3) default: services/api/app/data
    """
    env_root = os.getenv("ART_STUDIO_DATA_ROOT") or os.getenv("RMOS_DATA_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return _default_data_root().resolve()


def _normalize_tags(tags: List[str]) -> List[str]:
    cleaned: List[str] = []
    seen = set()
    for t in tags or []:
        v = (t or "").strip()
        if not v:
            continue
        key = v.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(v)
    return cleaned


@dataclass(frozen=True)
class DesignSnapshotStore:
    """
    File-backed snapshot store.
    Layout: {data_root}/art_studio/snapshots/{snapshot_id}.json
    """
    data_root: Path

    @property
    def snapshots_dir(self) -> Path:
        return self.data_root / "art_studio" / "snapshots"

    def _ensure_dirs(self) -> None:
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _validate_id(self, snapshot_id: str) -> None:
        if not _VALID_ID_RE.match(snapshot_id):
            raise ValueError("snapshot_id must be 6-80 chars: letters, digits, '_' or '-'")

    def _path_for_id(self, snapshot_id: str) -> Path:
        return self.snapshots_dir / f"{snapshot_id}.json"

    def _new_id(self) -> str:
        raw = uuid4().hex[:12]
        sid = f"snap_{raw}"
        self._validate_id(sid)
        return sid

    def _write_atomic(self, path: Path, data: dict) -> None:
        self._ensure_dirs()
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")
        tmp.replace(path)

    def create(self, req: SnapshotCreateRequest) -> DesignSnapshot:
        self._ensure_dirs()
        now = _utcnow()
        sid = self._new_id()

        context_refs = req.context_refs or DesignContextRefs()

        snap = DesignSnapshot(
            snapshot_id=sid,
            name=req.name,
            notes=req.notes,
            pattern_id=req.pattern_id,
            tags=_normalize_tags(req.tags),
            context_refs=context_refs,
            rosette_params=req.rosette_params,
            feasibility=req.feasibility,
            created_at=now,
            updated_at=now,
        )

        self._write_atomic(self._path_for_id(sid), snap.model_dump(mode="json"))
        return snap

    def get(self, snapshot_id: str) -> Optional[DesignSnapshot]:
        self._validate_id(snapshot_id)
        path = self._path_for_id(snapshot_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return DesignSnapshot.model_validate(data)

    def update(self, snapshot_id: str, req: SnapshotUpdateRequest) -> Optional[DesignSnapshot]:
        self._validate_id(snapshot_id)
        existing = self.get(snapshot_id)
        if existing is None:
            return None

        updated_data = existing.model_dump()

        if req.name is not None:
            updated_data["name"] = req.name
        if req.notes is not None:
            updated_data["notes"] = req.notes
        # pattern_id: allow explicit set to None (client can clear it)
        if "pattern_id" in req.model_fields_set:
            updated_data["pattern_id"] = req.pattern_id
        if req.tags is not None:
            updated_data["tags"] = _normalize_tags(req.tags)
        if req.context_refs is not None:
            updated_data["context_refs"] = req.context_refs.model_dump()
        if req.rosette_params is not None:
            updated_data["rosette_params"] = req.rosette_params.model_dump()
        if "feasibility" in req.model_fields_set:
            updated_data["feasibility"] = req.feasibility

        updated_data["updated_at"] = _utcnow()

        updated = DesignSnapshot.model_validate(updated_data)
        self._write_atomic(self._path_for_id(snapshot_id), updated.model_dump(mode="json"))
        return updated

    def delete(self, snapshot_id: str) -> bool:
        self._validate_id(snapshot_id)
        path = self._path_for_id(snapshot_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_recent(
        self,
        q: Optional[str] = None,
        tag: Optional[str] = None,
        pattern_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[SnapshotSummary]:
        self._ensure_dirs()
        limit = max(1, min(limit, 200))
        q_norm = (q or "").strip().lower()
        tag_norm = (tag or "").strip().lower() or None
        pat_norm = (pattern_id or "").strip() or None

        items: List[SnapshotSummary] = []

        for path in self._iter_snapshot_files():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                snap = DesignSnapshot.model_validate(data)
            except Exception:
                continue

            if pat_norm and (snap.pattern_id or "") != pat_norm:
                continue

            if tag_norm and tag_norm not in {t.lower() for t in (snap.tags or [])}:
                continue

            if q_norm:
                hay = " ".join([
                    snap.name or "",
                    snap.notes or "",
                    " ".join(snap.tags or [])
                ]).lower()
                if q_norm not in hay:
                    continue

            items.append(
                SnapshotSummary(
                    snapshot_id=snap.snapshot_id,
                    name=snap.name,
                    pattern_id=snap.pattern_id,
                    tags=snap.tags,
                    updated_at=snap.updated_at,
                )
            )

        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items[:limit]

    def export_raw(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        snap = self.get(snapshot_id)
        if snap is None:
            return None
        return snap.model_dump(mode="json")

    def import_raw(self, raw_snapshot: Dict[str, Any]) -> DesignSnapshot:
        """
        Import a previously exported snapshot JSON dict.
        - If snapshot_id collides, a new ID is assigned.
        - created_at/updated_at are preserved if present; otherwise set to now.
        """
        self._ensure_dirs()

        # Validate structure as DesignSnapshot
        snap = DesignSnapshot.model_validate(raw_snapshot)
        sid = snap.snapshot_id

        try:
            self._validate_id(sid)
        except ValueError:
            sid = self._new_id()

        if self._path_for_id(sid).exists():
            sid = self._new_id()

        now = _utcnow()
        snap_data = snap.model_dump()
        snap_data["snapshot_id"] = sid
        snap_data["tags"] = _normalize_tags(snap.tags)
        snap_data["updated_at"] = now

        final_snap = DesignSnapshot.model_validate(snap_data)
        self._write_atomic(self._path_for_id(sid), final_snap.model_dump(mode="json"))
        return final_snap

    def _iter_snapshot_files(self) -> Iterable[Path]:
        if not self.snapshots_dir.exists():
            return []
        return self.snapshots_dir.glob("*.json")
