# services/api/app/art_studio/stores/design_first_workflow_store.py
"""
Design-First Workflow Store (Bundle 32.7.0)

Simple JSON-file based persistence for design-first workflow sessions.
Uses atomic write pattern (tmp + rename) for safety.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Conditional import
try:
    from app.art_studio.schemas.workflow_design_first import DesignFirstSession
except ImportError:
    from art_studio.schemas.workflow_design_first import DesignFirstSession


DEFAULT_DIR = "services/api/data/art_studio_design_first_workflows"
ENV_DIR = "ART_STUDIO_DESIGN_FIRST_WORKFLOW_DIR"


def _root_dir() -> Path:
    """Get or create workflow storage directory (lazy creation)."""
    p = Path(os.getenv(ENV_DIR, DEFAULT_DIR))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _path(session_id: str) -> Path:
    """Get path for a session file. Session IDs are internally generated UUIDs."""
    # Sanitize session_id to prevent path traversal
    safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
    return _root_dir() / f"{safe_id}.json"


def save_session(session: DesignFirstSession) -> None:
    """Save session with atomic write."""
    session.updated_at = datetime.utcnow()
    tmp = _path(session.session_id).with_suffix(".json.tmp")
    final = _path(session.session_id)

    tmp.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(final)


def load_session(session_id: str) -> Optional[DesignFirstSession]:
    """Load session by ID, returns None if not found."""
    p = _path(session_id)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return DesignFirstSession.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def delete_session(session_id: str) -> bool:
    """Delete session file, returns True if deleted."""
    p = _path(session_id)
    if p.exists():
        p.unlink()
        return True
    return False
