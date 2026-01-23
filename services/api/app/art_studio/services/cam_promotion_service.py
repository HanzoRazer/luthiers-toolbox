from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

from pydantic import ValidationError

from app.art_studio.schemas.cam_promotion_request import CamPromotionRequestV1
from app.art_studio.schemas.promotion_intent import PromotionIntentV1
from app.art_studio.services.design_snapshot_store import resolve_art_studio_data_root


def _requests_dir(data_root: Path) -> Path:
    return data_root / "art_studio" / "cam_promotion" / "requests"


def _index_path(data_root: Path) -> Path:
    return data_root / "art_studio" / "cam_promotion" / "index.json"


def _key_for(intent: PromotionIntentV1) -> str:
    # Idempotency key: stable across re-promote calls for the SAME session.
    # Includes session_id so different sessions with same design get separate requests.
    return f"{intent.session_id}:{intent.design_fingerprint}:{intent.feasibility_fingerprint}"


def _load_index(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # Corruption-safe behavior: fail closed (force new index) would be risky.
        # We keep it simple: treat as empty; requests still exist on disk.
        return {}


def _save_index(path: Path, idx: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(idx, indent=2, sort_keys=True), encoding="utf-8")


def _request_path(data_root: Path, request_id: str) -> Path:
    return _requests_dir(data_root) / f"{request_id}.json"


def create_or_get_promotion_request(intent: PromotionIntentV1) -> CamPromotionRequestV1:
    """
    Create (or return existing) CamPromotionRequestV1 for the given intent.
    Orchestration-only. No CAM imports. No toolpath logic.
    """
    data_root = resolve_art_studio_data_root()
    rdir = _requests_dir(data_root)
    rdir.mkdir(parents=True, exist_ok=True)

    idx_path = _index_path(data_root)
    idx = _load_index(idx_path)

    key = _key_for(intent)
    existing_id = idx.get(key)
    if existing_id:
        p = _request_path(data_root, existing_id)
        if p.exists():
            raw = json.loads(p.read_text(encoding="utf-8"))
            try:
                return CamPromotionRequestV1.model_validate(raw)
            except ValidationError:
                # If schema drift/corruption: fall through to create new request
                pass

    request_id = str(uuid4())
    req = CamPromotionRequestV1(
        promotion_request_id=request_id,
        created_at=datetime.now(timezone.utc),
        session_id=intent.session_id,
        intent=intent,
        design_fingerprint=intent.design_fingerprint,
        feasibility_fingerprint=intent.feasibility_fingerprint,
        requested_cam_profile_id=intent.requested_cam_profile_id,
        status="QUEUED",
    )

    _request_path(data_root, request_id).write_text(
        json.dumps(req.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    idx[key] = request_id
    _save_index(idx_path, idx)
    return req


def get_promotion_request(request_id: str) -> Optional[CamPromotionRequestV1]:
    """
    Get a CAM promotion request by ID.
    
    Returns None if not found.
    """
    data_root = resolve_art_studio_data_root()
    p = _request_path(data_root, request_id)
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return CamPromotionRequestV1.model_validate(raw)
    except (json.JSONDecodeError, ValidationError):
        return None
