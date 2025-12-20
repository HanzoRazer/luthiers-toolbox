"""
AI Graphics DB Store

DB-backed store for AI exploration sessions and image assets.
Replaces in-memory _sessions dict with persistent storage.

Follows pattern established in workflow/db/store.py.

Usage:
    from app.db.session import db_session
    from app._experimental.ai_graphics.db.store import SESSION_STORE, IMAGE_STORE

    # Session operations
    with db_session() as db:
        session = SESSION_STORE.get_or_create(db, session_id)
        SESSION_STORE.mark_explored(db, session_id, fingerprints)

    # Image operations
    with db_session() as db:
        IMAGE_STORE.put(db, asset)
        assets = IMAGE_STORE.list_pending(db, limit=50)
"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Set

from sqlalchemy import select, and_, desc, asc, func
from sqlalchemy.orm import Session

from .models import (
    AiSessionRow,
    AiSuggestionRow,
    AiFingerprintRow,
    AiImageAssetRow,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fingerprint_hash(outer: float, inner: float, widths: Tuple[float, ...]) -> str:
    """Create a stable hash for a fingerprint tuple."""
    data = f"{outer:.4f}:{inner:.4f}:{','.join(f'{w:.4f}' for w in widths)}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


# =============================================================================
# AI Session Store
# =============================================================================

class DbAiSessionStore:
    """
    DB-backed AI session store.

    Replaces the in-memory _sessions dict with SQLite/PostgreSQL persistence.
    Maintains the same API as the original sessions.py module.
    """

    def get(self, db: Session, session_id: str) -> Optional[dict]:
        """Get session state. Returns None if not found."""
        row = db.get(AiSessionRow, session_id)
        if row is None:
            return None
        return json.loads(row.session_json)

    def get_or_create(self, db: Session, session_id: str) -> dict:
        """Get existing session or create a new one."""
        row = db.get(AiSessionRow, session_id)
        if row is None:
            state = {
                "session_id": session_id,
                "explored_fingerprints": [],
                "history": [],
                "created_at": _utcnow().isoformat(),
            }
            row = AiSessionRow(
                session_id=session_id,
                fingerprint_count=0,
                history_count=0,
                session_json=json.dumps(state),
            )
            db.add(row)
            return state
        return json.loads(row.session_json)

    def reset(self, db: Session, session_id: str) -> None:
        """Reset/clear a session, removing all fingerprints and history."""
        # Delete fingerprints
        db.execute(
            AiFingerprintRow.__table__.delete()
            .where(AiFingerprintRow.session_id == session_id)
        )
        # Delete suggestions
        db.execute(
            AiSuggestionRow.__table__.delete()
            .where(AiSuggestionRow.session_id == session_id)
        )
        # Delete session
        row = db.get(AiSessionRow, session_id)
        if row:
            db.delete(row)

    def mark_explored(
        self,
        db: Session,
        session_id: str,
        fingerprints: List[Tuple[float, float, Tuple[float, ...]]],
    ) -> None:
        """Mark design fingerprints as explored in the session."""
        # Ensure session exists
        self.get_or_create(db, session_id)

        for fp in fingerprints:
            outer, inner, widths = fp
            fp_hash = _fingerprint_hash(outer, inner, widths)

            # Check if already exists
            existing = db.execute(
                select(AiFingerprintRow.id)
                .where(and_(
                    AiFingerprintRow.session_id == session_id,
                    AiFingerprintRow.fingerprint_hash == fp_hash,
                ))
            ).first()

            if not existing:
                row = AiFingerprintRow(
                    session_id=session_id,
                    outer_diameter=outer,
                    inner_diameter=inner,
                    ring_widths_json=json.dumps(widths),
                    fingerprint_hash=fp_hash,
                )
                db.add(row)

        # Update session counts
        row = db.get(AiSessionRow, session_id)
        if row:
            count = db.execute(
                select(func.count(AiFingerprintRow.id))
                .where(AiFingerprintRow.session_id == session_id)
            ).scalar()
            row.fingerprint_count = count or 0
            row.last_activity_utc = _utcnow()

    def is_explored(
        self,
        db: Session,
        session_id: str,
        fingerprint: Tuple[float, float, Tuple[float, ...]],
    ) -> bool:
        """Check if a fingerprint has already been explored."""
        outer, inner, widths = fingerprint
        fp_hash = _fingerprint_hash(outer, inner, widths)

        result = db.execute(
            select(AiFingerprintRow.id)
            .where(and_(
                AiFingerprintRow.session_id == session_id,
                AiFingerprintRow.fingerprint_hash == fp_hash,
            ))
        ).first()

        return result is not None

    def add_suggestion(
        self,
        db: Session,
        session_id: str,
        suggestion_id: str,
        overall_score: float,
        risk_bucket: Optional[str] = None,
        worst_ring_risk: Optional[str] = None,
    ) -> None:
        """Add a suggestion record to session history."""
        # Ensure session exists
        self.get_or_create(db, session_id)

        row = AiSuggestionRow(
            session_id=session_id,
            suggestion_id=suggestion_id,
            overall_score=overall_score,
            risk_bucket=risk_bucket,
            worst_ring_risk=worst_ring_risk,
        )
        db.add(row)

        # Update session counts
        session_row = db.get(AiSessionRow, session_id)
        if session_row:
            count = db.execute(
                select(func.count(AiSuggestionRow.id))
                .where(AiSuggestionRow.session_id == session_id)
            ).scalar()
            session_row.history_count = count or 0
            session_row.last_activity_utc = _utcnow()

    def get_history(
        self,
        db: Session,
        session_id: str,
        limit: int = 100,
    ) -> List[dict]:
        """Get suggestion history for a session."""
        rows = db.execute(
            select(AiSuggestionRow)
            .where(AiSuggestionRow.session_id == session_id)
            .order_by(desc(AiSuggestionRow.created_at_utc))
            .limit(limit)
        ).scalars().all()

        return [
            {
                "suggestion_id": row.suggestion_id,
                "overall_score": row.overall_score,
                "risk_bucket": row.risk_bucket,
                "worst_ring_risk": row.worst_ring_risk,
                "created_at": row.created_at_utc.isoformat(),
            }
            for row in rows
        ]

    def list_active(
        self,
        db: Session,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[dict]:
        """List active sessions with recent activity."""
        stmt = select(AiSessionRow)

        if since:
            stmt = stmt.where(AiSessionRow.last_activity_utc >= since)

        stmt = stmt.order_by(desc(AiSessionRow.last_activity_utc)).limit(limit)

        rows = db.execute(stmt).scalars().all()

        return [
            {
                "session_id": row.session_id,
                "fingerprint_count": row.fingerprint_count,
                "history_count": row.history_count,
                "created_at": row.created_at_utc.isoformat(),
                "last_activity": row.last_activity_utc.isoformat(),
            }
            for row in rows
        ]


# =============================================================================
# AI Image Asset Store
# =============================================================================

class DbAiImageAssetStore:
    """
    DB-backed store for AI-generated image assets.

    Supports the Vision Engine advisory workflow:
    - Create assets from generation
    - Review (approve/reject)
    - Attach to runs
    - Filter and search
    """

    def put(self, db: Session, asset: dict) -> dict:
        """Store or update an image asset."""
        asset_id = asset["id"]

        row = db.get(AiImageAssetRow, asset_id)
        if row is None:
            row = AiImageAssetRow(
                id=asset_id,
                project_id=asset.get("project_id"),
                image_url=asset.get("image_url"),
                thumbnail_url=asset.get("thumbnail_url"),
                content_hash=asset.get("content_hash"),
                prompt=asset["prompt"],
                engineered_prompt=asset.get("engineered_prompt"),
                negative_prompt=asset.get("negative_prompt"),
                provider=asset["provider"],
                quality=asset.get("quality", "standard"),
                size=asset.get("size", "1024x1024"),
                style=asset.get("style"),
                category=asset.get("category"),
                body_shape=asset.get("body_shape"),
                finish=asset.get("finish"),
                status=asset.get("status", "pending"),
                rating=asset.get("rating"),
                cost=asset.get("cost", 0.0),
                metadata_json=json.dumps(asset.get("metadata", {})),
            )
            db.add(row)
        else:
            # Update mutable fields
            row.status = asset.get("status", row.status)
            row.rating = asset.get("rating", row.rating)
            row.rejection_reason = asset.get("rejection_reason", row.rejection_reason)
            row.reviewed_by = asset.get("reviewed_by", row.reviewed_by)
            row.reviewed_at_utc = asset.get("reviewed_at")
            row.attached_to_run_id = asset.get("attached_to_run_id", row.attached_to_run_id)
            row.attached_at_utc = asset.get("attached_at")
            if asset.get("metadata"):
                row.metadata_json = json.dumps(asset["metadata"])

        return asset

    def get(self, db: Session, asset_id: str) -> Optional[dict]:
        """Get an image asset by ID."""
        row = db.get(AiImageAssetRow, asset_id)
        if row is None:
            return None
        return self._row_to_dict(row)

    def delete(self, db: Session, asset_id: str) -> bool:
        """Delete an image asset."""
        row = db.get(AiImageAssetRow, asset_id)
        if row:
            db.delete(row)
            return True
        return False

    def _row_to_dict(self, row: AiImageAssetRow) -> dict:
        """Convert a row to a dict."""
        return {
            "id": row.id,
            "project_id": row.project_id,
            "image_url": row.image_url,
            "thumbnail_url": row.thumbnail_url,
            "content_hash": row.content_hash,
            "prompt": row.prompt,
            "engineered_prompt": row.engineered_prompt,
            "negative_prompt": row.negative_prompt,
            "provider": row.provider,
            "quality": row.quality,
            "size": row.size,
            "style": row.style,
            "category": row.category,
            "body_shape": row.body_shape,
            "finish": row.finish,
            "status": row.status,
            "rating": row.rating,
            "rejection_reason": row.rejection_reason,
            "reviewed_by": row.reviewed_by,
            "reviewed_at": row.reviewed_at_utc.isoformat() if row.reviewed_at_utc else None,
            "attached_to_run_id": row.attached_to_run_id,
            "attached_at": row.attached_at_utc.isoformat() if row.attached_at_utc else None,
            "cost": row.cost,
            "created_at": row.created_at_utc.isoformat(),
            "updated_at": row.updated_at_utc.isoformat(),
            "metadata": json.loads(row.metadata_json) if row.metadata_json else {},
        }

    def list(
        self,
        db: Session,
        *,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        category: Optional[str] = None,
        min_rating: Optional[int] = None,
        has_run: Optional[bool] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        order_by: str = "created_at_utc",
        order_dir: str = "desc",
    ) -> Tuple[List[dict], int]:
        """List image assets with filtering."""
        conditions = []

        if project_id:
            conditions.append(AiImageAssetRow.project_id == project_id)
        if status:
            conditions.append(AiImageAssetRow.status == status)
        if provider:
            conditions.append(AiImageAssetRow.provider == provider)
        if category:
            conditions.append(AiImageAssetRow.category == category)
        if min_rating is not None:
            conditions.append(AiImageAssetRow.rating >= min_rating)
        if has_run is True:
            conditions.append(AiImageAssetRow.attached_to_run_id.isnot(None))
        elif has_run is False:
            conditions.append(AiImageAssetRow.attached_to_run_id.is_(None))
        if search:
            conditions.append(AiImageAssetRow.prompt.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count(AiImageAssetRow.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = db.execute(count_stmt).scalar() or 0

        # Build query
        stmt = select(AiImageAssetRow)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Order
        order_col = getattr(AiImageAssetRow, order_by, AiImageAssetRow.created_at_utc)
        if order_dir == "asc":
            stmt = stmt.order_by(asc(order_col))
        else:
            stmt = stmt.order_by(desc(order_col))

        stmt = stmt.offset(offset).limit(limit)

        rows = db.execute(stmt).scalars().all()

        return [self._row_to_dict(row) for row in rows], total

    def list_pending(self, db: Session, limit: int = 50) -> List[dict]:
        """List pending assets for review."""
        assets, _ = self.list(db, status="pending", limit=limit)
        return assets

    def approve(
        self,
        db: Session,
        asset_id: str,
        reviewer: Optional[str] = None,
    ) -> Optional[dict]:
        """Approve an asset."""
        row = db.get(AiImageAssetRow, asset_id)
        if row:
            row.status = "approved"
            row.reviewed_by = reviewer
            row.reviewed_at_utc = _utcnow()
            return self._row_to_dict(row)
        return None

    def reject(
        self,
        db: Session,
        asset_id: str,
        reason: str,
        reviewer: Optional[str] = None,
    ) -> Optional[dict]:
        """Reject an asset."""
        row = db.get(AiImageAssetRow, asset_id)
        if row:
            row.status = "rejected"
            row.rejection_reason = reason
            row.reviewed_by = reviewer
            row.reviewed_at_utc = _utcnow()
            return self._row_to_dict(row)
        return None

    def attach_to_run(
        self,
        db: Session,
        asset_id: str,
        run_id: str,
    ) -> Optional[dict]:
        """Attach an approved asset to a run."""
        row = db.get(AiImageAssetRow, asset_id)
        if row and row.status == "approved":
            row.attached_to_run_id = run_id
            row.attached_at_utc = _utcnow()
            return self._row_to_dict(row)
        return None

    def get_stats(self, db: Session, project_id: Optional[str] = None) -> dict:
        """Get asset statistics."""
        conditions = []
        if project_id:
            conditions.append(AiImageAssetRow.project_id == project_id)

        # Count by status
        status_query = select(
            AiImageAssetRow.status,
            func.count(AiImageAssetRow.id)
        ).group_by(AiImageAssetRow.status)
        if conditions:
            status_query = status_query.where(and_(*conditions))
        status_counts = dict(db.execute(status_query).all())

        # Total cost
        cost_query = select(func.sum(AiImageAssetRow.cost))
        if conditions:
            cost_query = cost_query.where(and_(*conditions))
        total_cost = db.execute(cost_query).scalar() or 0.0

        # Average rating
        rating_query = select(func.avg(AiImageAssetRow.rating)).where(
            AiImageAssetRow.rating.isnot(None)
        )
        if conditions:
            rating_query = rating_query.where(and_(*conditions))
        avg_rating = db.execute(rating_query).scalar() or 0.0

        return {
            "total": sum(status_counts.values()),
            "pending": status_counts.get("pending", 0),
            "approved": status_counts.get("approved", 0),
            "rejected": status_counts.get("rejected", 0),
            "total_cost": round(total_cost, 4),
            "avg_rating": round(avg_rating, 2),
        }


# Global singletons
SESSION_STORE = DbAiSessionStore()
IMAGE_STORE = DbAiImageAssetStore()
