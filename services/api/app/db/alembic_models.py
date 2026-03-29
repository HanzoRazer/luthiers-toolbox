"""
SQLAlchemy models for Alembic (art_studio + cam_logs).

Schema source of truth: ``docs/SQLITE_SCHEMA_AUDIT_2026_03_28.json`` and DDL in
``app/art_studio_rosette_store.py`` (art_studio.db) and ``app/telemetry/cam_logs.py`` (cam_logs.db).

Tables included:
  - art_studio: rosette_jobs, rosette_presets, rosette_compare_risk
  - cam_logs: runs, segments

``rmos.sqlite`` is empty in the audit — no tables there.

Inherits ``app.db.base.Base``. Autogenerate uses ``include_object`` in ``env.py`` to emit only these five tables.
"""

from __future__ import annotations

from sqlalchemy import Column, Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


# --- art_studio.db -------------------------------------------------------------


class RosetteJob(Base):
    __tablename__ = "rosette_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Text, unique=True)
    name = Column(Text)
    preset = Column(Text)
    payload_json = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)


class RosettePreset(Base):
    __tablename__ = "rosette_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True)
    pattern_type = Column(Text, nullable=False)
    segment_count = Column("segments", Integer, nullable=False)
    inner_radius = Column(Float, nullable=False)
    outer_radius = Column(Float, nullable=False)
    metadata_json = Column(Text, nullable=False)


class RosetteCompareRisk(Base):
    __tablename__ = "rosette_compare_risk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id_a = Column(Text, nullable=False)
    job_id_b = Column(Text, nullable=False)
    lane = Column(Text)
    risk_score = Column(Float, nullable=False)
    diff_json = Column(Text, nullable=False)
    note = Column(Text)
    created_at = Column(Text, nullable=False)


# --- cam_logs.db ---------------------------------------------------------------


class CamLogRun(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(Integer, nullable=False)
    job_name = Column(Text)
    machine_id = Column(Text)
    material_id = Column(Text)
    tool_d = Column(Float)
    stepover = Column(Float)
    stepdown = Column(Float)
    post_id = Column(Text)
    feed_xy = Column(Float)
    rpm = Column(Integer)
    est_time_s = Column(Float)
    act_time_s = Column(Float)
    notes = Column(Text)

    segments = relationship(
        "CamLogSegment",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CamLogSegment(Base):
    __tablename__ = "segments"
    __table_args__ = (UniqueConstraint("run_id", "idx", name="uq_segments_run_idx"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        Integer,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    idx = Column(Integer)
    code = Column(Text)
    x = Column(Float)
    y = Column(Float)
    len_mm = Column(Float)
    limit_kind = Column("limit", Text)
    slowdown = Column(Float)
    trochoid = Column(Integer)
    radius_mm = Column(Float)
    feed_f = Column(Float)

    run = relationship("CamLogRun", back_populates="segments")
