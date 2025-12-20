"""
RMOS Runs v2 DB Store

DB-backed store for RunArtifact persistence.
Stores full artifact as JSON while indexing key fields for efficient queries.

Follows pattern established in workflow/db/store.py.

Usage:
    from app.db.session import db_session
    from app.rmos.runs_v2.db.store import STORE

    with db_session() as db:
        artifact = STORE.get(db, run_id)
        STORE.put(db, artifact)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.orm import Session

from ..schemas import RunArtifact, AdvisoryInputRef
from .models import RunArtifactRow, AdvisoryAttachmentRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DbRunArtifactStore:
    """
    DB-backed RunArtifact store.

    Stores RunArtifact as JSON for flexibility while indexing key
    fields for efficient filtering and pagination.

    Key Features:
    - Pagination via offset/limit or cursor-based (created_at)
    - Filtering by status, mode, risk_level, tool_id, etc.
    - Advisory attachment tracking
    - Immutable design (updates create new versions)
    """

    def put(self, db: Session, artifact: RunArtifact) -> RunArtifact:
        """
        Store or update a run artifact.

        Note: RunArtifacts are conceptually immutable, but we support
        update for advisory_inputs append operations.
        """
        payload = artifact.model_dump(mode="json")

        row = db.get(RunArtifactRow, artifact.run_id)
        if row is None:
            row = RunArtifactRow(
                run_id=artifact.run_id,
                status=artifact.status,
                mode=artifact.mode,
                risk_level=artifact.decision.risk_level,
                tool_id=artifact.tool_id,
                material_id=artifact.material_id,
                machine_id=artifact.machine_id,
                workflow_session_id=artifact.workflow_session_id,
                score=artifact.decision.score,
                feasibility_sha256=artifact.hashes.feasibility_sha256,
                toolpaths_sha256=artifact.hashes.toolpaths_sha256,
                gcode_sha256=artifact.hashes.gcode_sha256,
                explanation_status=artifact.explanation_status,
                has_advisory_inputs=bool(artifact.advisory_inputs),
                artifact_json=json.dumps(payload),
            )
            db.add(row)
        else:
            # Update mutable fields only
            row.explanation_status = artifact.explanation_status
            row.has_advisory_inputs = bool(artifact.advisory_inputs)
            row.artifact_json = json.dumps(payload)

        # Sync advisory attachments
        self._sync_advisory_attachments(db, artifact)

        return artifact

    def _sync_advisory_attachments(self, db: Session, artifact: RunArtifact) -> None:
        """Sync advisory_inputs to the junction table."""
        # Get existing attachments
        existing = db.execute(
            select(AdvisoryAttachmentRow.advisory_id)
            .where(AdvisoryAttachmentRow.run_id == artifact.run_id)
        ).scalars().all()

        existing_ids = set(existing)

        # Add new attachments (append-only)
        for ref in artifact.advisory_inputs:
            if ref.advisory_id not in existing_ids:
                row = AdvisoryAttachmentRow(
                    run_id=artifact.run_id,
                    advisory_id=ref.advisory_id,
                    kind=ref.kind,
                    created_at_utc=ref.created_at_utc,
                    request_id=ref.request_id,
                    engine_id=ref.engine_id,
                    engine_version=ref.engine_version,
                )
                db.add(row)

    def get(self, db: Session, run_id: str) -> Optional[RunArtifact]:
        """Get a run artifact by ID. Returns None if not found."""
        row = db.get(RunArtifactRow, run_id)
        if row is None:
            return None
        data = json.loads(row.artifact_json)
        return RunArtifact.model_validate(data)

    def require(self, db: Session, run_id: str) -> RunArtifact:
        """Get a run artifact by ID. Raises KeyError if not found."""
        artifact = self.get(db, run_id)
        if artifact is None:
            raise KeyError(f"Run artifact not found: {run_id}")
        return artifact

    def delete(self, db: Session, run_id: str) -> bool:
        """Delete a run artifact. Returns True if it existed."""
        row = db.get(RunArtifactRow, run_id)
        if row is not None:
            # Delete advisory attachments first
            db.execute(
                AdvisoryAttachmentRow.__table__.delete()
                .where(AdvisoryAttachmentRow.run_id == run_id)
            )
            db.delete(row)
            return True
        return False

    def list(
        self,
        db: Session,
        *,
        status: Optional[str] = None,
        mode: Optional[str] = None,
        risk_level: Optional[str] = None,
        tool_id: Optional[str] = None,
        material_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        workflow_session_id: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        has_advisory: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
        order_by: str = "created_at_utc",
        order_dir: str = "desc",
    ) -> Tuple[List[RunArtifact], int]:
        """
        List run artifacts with filtering and pagination.

        Returns:
            Tuple of (artifacts, total_count)
        """
        # Build filter conditions
        conditions = []

        if status:
            conditions.append(RunArtifactRow.status == status)
        if mode:
            conditions.append(RunArtifactRow.mode == mode)
        if risk_level:
            conditions.append(RunArtifactRow.risk_level == risk_level)
        if tool_id:
            conditions.append(RunArtifactRow.tool_id == tool_id)
        if material_id:
            conditions.append(RunArtifactRow.material_id == material_id)
        if machine_id:
            conditions.append(RunArtifactRow.machine_id == machine_id)
        if workflow_session_id:
            conditions.append(RunArtifactRow.workflow_session_id == workflow_session_id)
        if min_score is not None:
            conditions.append(RunArtifactRow.score >= min_score)
        if max_score is not None:
            conditions.append(RunArtifactRow.score <= max_score)
        if created_after:
            conditions.append(RunArtifactRow.created_at_utc >= created_after)
        if created_before:
            conditions.append(RunArtifactRow.created_at_utc <= created_before)
        if has_advisory is not None:
            conditions.append(RunArtifactRow.has_advisory_inputs == has_advisory)

        # Count total
        count_stmt = select(func.count(RunArtifactRow.run_id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = db.execute(count_stmt).scalar() or 0

        # Build query
        stmt = select(RunArtifactRow)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Order by
        order_col = getattr(RunArtifactRow, order_by, RunArtifactRow.created_at_utc)
        if order_dir == "asc":
            stmt = stmt.order_by(asc(order_col))
        else:
            stmt = stmt.order_by(desc(order_col))

        # Pagination
        stmt = stmt.offset(offset).limit(limit)

        # Execute
        rows = db.execute(stmt).scalars().all()

        artifacts = [
            RunArtifact.model_validate(json.loads(row.artifact_json))
            for row in rows
        ]

        return artifacts, total

    def list_by_session(
        self,
        db: Session,
        workflow_session_id: str,
        limit: int = 100,
    ) -> List[RunArtifact]:
        """Get all runs for a workflow session, ordered by creation time."""
        artifacts, _ = self.list(
            db,
            workflow_session_id=workflow_session_id,
            limit=limit,
            order_by="created_at_utc",
            order_dir="asc",
        )
        return artifacts

    def get_latest(
        self,
        db: Session,
        *,
        mode: Optional[str] = None,
        tool_id: Optional[str] = None,
    ) -> Optional[RunArtifact]:
        """Get the most recent run artifact matching filters."""
        artifacts, _ = self.list(db, mode=mode, tool_id=tool_id, limit=1)
        return artifacts[0] if artifacts else None

    def attach_advisory(
        self,
        db: Session,
        run_id: str,
        advisory_ref: AdvisoryInputRef,
    ) -> RunArtifact:
        """
        Append an advisory reference to a run artifact.

        This is the only "update" operation allowed on immutable artifacts.
        """
        artifact = self.require(db, run_id)

        # Append to advisory_inputs
        artifact.advisory_inputs.append(advisory_ref)

        # Save (will sync to junction table)
        return self.put(db, artifact)

    def get_advisories_for_run(
        self,
        db: Session,
        run_id: str,
    ) -> List[AdvisoryInputRef]:
        """Get all advisory references attached to a run."""
        rows = db.execute(
            select(AdvisoryAttachmentRow)
            .where(AdvisoryAttachmentRow.run_id == run_id)
            .order_by(AdvisoryAttachmentRow.created_at_utc)
        ).scalars().all()

        return [
            AdvisoryInputRef(
                advisory_id=row.advisory_id,
                kind=row.kind,
                created_at_utc=row.created_at_utc,
                request_id=row.request_id,
                engine_id=row.engine_id,
                engine_version=row.engine_version,
            )
            for row in rows
        ]

    def get_runs_for_advisory(
        self,
        db: Session,
        advisory_id: str,
    ) -> List[str]:
        """Get all run IDs that reference a given advisory."""
        rows = db.execute(
            select(AdvisoryAttachmentRow.run_id)
            .where(AdvisoryAttachmentRow.advisory_id == advisory_id)
        ).scalars().all()
        return list(rows)

    def count_by_status(self, db: Session) -> dict:
        """Get count of runs grouped by status."""
        rows = db.execute(
            select(
                RunArtifactRow.status,
                func.count(RunArtifactRow.run_id)
            ).group_by(RunArtifactRow.status)
        ).all()
        return {row[0]: row[1] for row in rows}

    def count_by_risk(self, db: Session) -> dict:
        """Get count of runs grouped by risk level."""
        rows = db.execute(
            select(
                RunArtifactRow.risk_level,
                func.count(RunArtifactRow.run_id)
            ).group_by(RunArtifactRow.risk_level)
        ).all()
        return {row[0]: row[1] for row in rows}


# Global singleton for simple usage
STORE = DbRunArtifactStore()
