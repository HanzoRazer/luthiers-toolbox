"""
Pattern Store - Bundle 31.0.1

File-backed JSON store for pattern library.
Layout: {data_root}/art_studio/patterns/{pattern_id}.json
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional
from uuid import uuid4

from ..schemas.pattern_library import (
    PatternRecord,
    PatternCreateRequest,
    PatternSummary,
    PatternUpdateRequest,
)


_VALID_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{6,80}$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_data_root() -> Path:
    """Default to services/api/app/data"""
    app_root = Path(__file__).resolve().parents[2]
    return app_root / "data"


def resolve_art_studio_data_root() -> Path:
    """
    Resolve Art Studio data root.
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
    """Normalize tags: trim, dedupe (case-insensitive), preserve original case."""
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
class PatternStore:
    """
    File-backed pattern store.
    Layout: {data_root}/art_studio/patterns/{pattern_id}.json
    """
    data_root: Path

    @property
    def patterns_dir(self) -> Path:
        return self.data_root / "art_studio" / "patterns"

    def _ensure_dirs(self) -> None:
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def _validate_id(self, pattern_id: str) -> None:
        if not _VALID_ID_RE.match(pattern_id):
            raise ValueError("pattern_id must be 6-80 chars: letters, digits, '_' or '-'")

    def _path_for_id(self, pattern_id: str) -> Path:
        return self.patterns_dir / f"{pattern_id}.json"

    def _new_id(self) -> str:
        raw = uuid4().hex[:12]
        pid = f"pat_{raw}"
        self._validate_id(pid)
        return pid

    def _write_atomic(self, path: Path, data: dict) -> None:
        self._ensure_dirs()
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")
        tmp.replace(path)

    def create(self, req: PatternCreateRequest) -> PatternRecord:
        self._ensure_dirs()
        now = _utcnow()
        pid = self._new_id()

        record = PatternRecord(
            pattern_id=pid,
            name=req.name,
            description=req.description,
            tags=_normalize_tags(req.tags),
            generator_key=req.generator_key,
            params=req.params or {},
            created_at=now,
            updated_at=now,
        )

        self._write_atomic(self._path_for_id(pid), record.model_dump(mode="json"))
        return record

    def get(self, pattern_id: str) -> Optional[PatternRecord]:
        self._validate_id(pattern_id)
        path = self._path_for_id(pattern_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return PatternRecord.model_validate(data)

    def update(self, pattern_id: str, req: PatternUpdateRequest) -> Optional[PatternRecord]:
        self._validate_id(pattern_id)
        existing = self.get(pattern_id)
        if existing is None:
            return None

        # Apply updates
        updated_data = existing.model_dump()
        if req.name is not None:
            updated_data["name"] = req.name
        if req.description is not None:
            updated_data["description"] = req.description
        if req.tags is not None:
            updated_data["tags"] = _normalize_tags(req.tags)
        if req.generator_key is not None:
            updated_data["generator_key"] = req.generator_key
        if req.params is not None:
            updated_data["params"] = req.params

        updated_data["updated_at"] = _utcnow()

        updated = PatternRecord.model_validate(updated_data)
        self._write_atomic(self._path_for_id(pattern_id), updated.model_dump(mode="json"))
        return updated

    def delete(self, pattern_id: str) -> bool:
        self._validate_id(pattern_id)
        path = self._path_for_id(pattern_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_patterns(
        self,
        q: Optional[str] = None,
        tag: Optional[str] = None,
        generator_key: Optional[str] = None,
        limit: int = 100,
    ) -> List[PatternSummary]:
        self._ensure_dirs()
        limit = max(1, min(limit, 500))
        q_norm = (q or "").strip().lower()
        tag_norm = (tag or "").strip().lower() or None
        gen_norm = (generator_key or "").strip() or None

        items: List[PatternSummary] = []

        for path in self._iter_pattern_files():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                record = PatternRecord.model_validate(data)
            except (OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
                continue

            # Filter by generator_key
            if gen_norm and record.generator_key != gen_norm:
                continue

            # Filter by tag
            if tag_norm and tag_norm not in {t.lower() for t in (record.tags or [])}:
                continue

            # Filter by search query
            if q_norm:
                hay = " ".join([
                    record.name or "",
                    record.description or "",
                    " ".join(record.tags or [])
                ]).lower()
                if q_norm not in hay:
                    continue

            items.append(
                PatternSummary(
                    pattern_id=record.pattern_id,
                    name=record.name,
                    tags=record.tags,
                    generator_key=record.generator_key,
                    updated_at=record.updated_at,
                )
            )

        # Sort by updated_at descending
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items[:limit]

    def _iter_pattern_files(self) -> Iterable[Path]:
        if not self.patterns_dir.exists():
            return []
        return self.patterns_dir.glob("*.json")
