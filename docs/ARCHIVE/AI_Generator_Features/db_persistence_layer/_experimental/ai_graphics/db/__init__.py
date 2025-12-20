"""
AI Graphics Database Layer

SQLAlchemy persistence for AI exploration sessions and image assets.

Usage:
    from app.db.session import db_session
    from app._experimental.ai_graphics.db import SESSION_STORE, IMAGE_STORE

    # Session operations
    with db_session() as db:
        session = SESSION_STORE.get_or_create(db, session_id)
        SESSION_STORE.mark_explored(db, session_id, fingerprints)
        if SESSION_STORE.is_explored(db, session_id, fingerprint):
            skip_design()

    # Image operations
    with db_session() as db:
        IMAGE_STORE.put(db, asset)
        pending = IMAGE_STORE.list_pending(db)
        IMAGE_STORE.approve(db, asset_id, reviewer="user")
        IMAGE_STORE.attach_to_run(db, asset_id, run_id)
"""

from .models import (
    AiSessionRow,
    AiSuggestionRow,
    AiFingerprintRow,
    AiImageAssetRow,
)
from .store import (
    DbAiSessionStore,
    DbAiImageAssetStore,
    SESSION_STORE,
    IMAGE_STORE,
)

__all__ = [
    # Models
    "AiSessionRow",
    "AiSuggestionRow",
    "AiFingerprintRow",
    "AiImageAssetRow",
    # Stores
    "DbAiSessionStore",
    "DbAiImageAssetStore",
    "SESSION_STORE",
    "IMAGE_STORE",
]
