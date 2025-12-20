"""
RMOS Runs v2 Database Layer

SQLAlchemy persistence for RunArtifact storage.

Usage:
    from app.db.session import db_session
    from app.rmos.runs_v2.db import STORE, RunArtifactRow

    # Store an artifact
    with db_session() as db:
        STORE.put(db, artifact)

    # Query artifacts
    with db_session() as db:
        artifacts, total = STORE.list(db, status="OK", limit=20)

    # Attach advisory
    with db_session() as db:
        STORE.attach_advisory(db, run_id, advisory_ref)
"""

from .models import RunArtifactRow, AdvisoryAttachmentRow
from .store import DbRunArtifactStore, STORE

__all__ = [
    "RunArtifactRow",
    "AdvisoryAttachmentRow",
    "DbRunArtifactStore",
    "STORE",
]
