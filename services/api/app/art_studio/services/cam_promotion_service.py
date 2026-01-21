# services/api/app/art_studio/services/cam_promotion_service.py
"""
Phase 33.0 — CAM Promotion Service

Creates and manages CAM promotion requests from PromotionIntentV1.
Enforces idempotency using fingerprint pairs.

This service does NOT:
  - execute CAM
  - generate toolpaths
  - create manufacturing authority

It only records the promotion request for downstream consumption.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from app.art_studio.schemas.cam_promotion_request import CamPromotionRequestV1
from app.art_studio.schemas.promotion_intent import PromotionIntentV1


# Storage configuration
DEFAULT_DIR = "services/api/data/art_studio_cam_promotion_requests"
ENV_DIR = "ART_STUDIO_CAM_PROMOTION_REQUEST_DIR"

# In-memory index for idempotency (fingerprint pair -> request_id)
# In production, this would be a database lookup
_idempotency_index: dict[str, str] = {}


def _root_dir() -> Path:
    """Get or create promotion request storage directory (lazy creation)."""
    p = Path(os.getenv(ENV_DIR, DEFAULT_DIR))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _path(request_id: str) -> Path:
    """Get path for a request file."""
    safe_id = "".join(c for c in request_id if c.isalnum() or c in "-_")
    return _root_dir() / f"{safe_id}.json"


def _fingerprint_key(design_fp: str, feas_fp: str) -> str:
    """Create idempotency key from fingerprint pair."""
    return f"{design_fp}:{feas_fp}"


def _load_idempotency_index() -> None:
    """Load existing requests into idempotency index on first call."""
    global _idempotency_index
    if _idempotency_index:
        return  # Already loaded
    
    root = _root_dir()
    if not root.exists():
        return
    
    for p in root.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            design_fp = data.get("design_fingerprint", "")
            feas_fp = data.get("feasibility_fingerprint", "")
            request_id = data.get("promotion_request_id", "")
            if design_fp and feas_fp and request_id:
                key = _fingerprint_key(design_fp, feas_fp)
                _idempotency_index[key] = request_id
        except (json.JSONDecodeError, OSError):
            continue


def _save_request(request: CamPromotionRequestV1) -> None:
    """Save request with atomic write."""
    tmp = _path(request.promotion_request_id).with_suffix(".json.tmp")
    final = _path(request.promotion_request_id)
    
    tmp.write_text(request.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(final)
    
    # Update index
    key = _fingerprint_key(request.design_fingerprint, request.feasibility_fingerprint)
    _idempotency_index[key] = request.promotion_request_id


def _load_request(request_id: str) -> Optional[CamPromotionRequestV1]:
    """Load request by ID."""
    p = _path(request_id)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return CamPromotionRequestV1.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def create_or_get_promotion_request(
    intent: PromotionIntentV1,
) -> CamPromotionRequestV1:
    """
    Create a CAM promotion request from an approved PromotionIntentV1.
    
    Idempotency: If a request already exists for the same fingerprint pair,
    returns the existing request instead of creating a new one.
    
    This ensures the same approved design always maps to the same request ID.
    """
    # Ensure index is loaded
    _load_idempotency_index()
    
    # Check for existing request (idempotency)
    key = _fingerprint_key(intent.design_fingerprint, intent.feasibility_fingerprint)
    existing_id = _idempotency_index.get(key)
    
    if existing_id:
        existing = _load_request(existing_id)
        if existing:
            return existing
    
    # Create new request
    request = CamPromotionRequestV1(
        promotion_request_id=uuid4().hex,
        created_at=datetime.utcnow(),
        session_id=intent.session_id,
        design_fingerprint=intent.design_fingerprint,
        feasibility_fingerprint=intent.feasibility_fingerprint,
        requested_cam_profile_id=intent.requested_cam_profile_id,
        status="QUEUED",
    )
    
    _save_request(request)
    
    # Log promotion event (best-effort)
    _log_promotion_event(request)
    
    return request


def get_promotion_request(request_id: str) -> Optional[CamPromotionRequestV1]:
    """Get a promotion request by ID."""
    return _load_request(request_id)


def _log_promotion_event(request: CamPromotionRequestV1) -> None:
    """Log promotion request creation for audit trail."""
    try:
        from app.rmos.logs import log_event
        log_event(
            event_type="cam_promotion_request_created",
            session_id=request.session_id,
            promotion_request_id=request.promotion_request_id,
            design_fingerprint=request.design_fingerprint,
            feasibility_fingerprint=request.feasibility_fingerprint,
            status=request.status,
        )
    except ImportError:
        pass  # Logging not available
    except Exception:
        pass  # Non-blocking
