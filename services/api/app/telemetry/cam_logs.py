"""CAM Run Logging - SQLite schema and access functions.

Stores completed CAM runs (metadata + per-segment details) for:
- Performance analytics (actual vs predicted time)
- Machine bottleneck profiling (feed_cap/accel/jerk distribution)
- Learning feed overrides from real-world execution patterns
"""

import os
import sqlite3
import json
import time
from typing import Any, Dict, List, Iterable

DB = os.getenv("CAM_LOG_DB", os.path.join(os.path.dirname(__file__), "cam_logs.db"))

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_utc INTEGER NOT NULL,
  job_name TEXT,
  machine_id TEXT,
  material_id TEXT,
  tool_d REAL,
  stepover REAL,              -- 0..1
  stepdown REAL,
  post_id TEXT,
  feed_xy REAL,               -- requested feed
  rpm INTEGER,
  est_time_s REAL,            -- predicted time (jerk-aware)
  act_time_s REAL,            -- actual time if known (optional)
  notes TEXT
);
CREATE TABLE IF NOT EXISTS segments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  idx INTEGER,
  code TEXT,
  x REAL, y REAL,             -- end point
  len_mm REAL,
  limit TEXT,                 -- feed_cap|accel|jerk|none
  slowdown REAL,              -- meta.slowdown (if any)
  trochoid INTEGER,           -- 0/1
  radius_mm REAL,             -- if arc
  feed_f REAL,                -- stamped feed on the line if present
  UNIQUE(run_id, idx)
);
"""


def open_db():
    """Open SQLite connection with Row factory, auto-migrate schema if new."""
    new = not os.path.exists(DB)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    if new:
        con.executescript(DDL)
        con.commit()
    return con


def insert_run(meta: Dict[str, Any]) -> int:
    """Insert a run record, return run_id."""
    con = open_db()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO runs
    (ts_utc,job_name,machine_id,material_id,tool_d,stepover,stepdown,post_id,feed_xy,rpm,est_time_s,act_time_s,notes)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            int(time.time()),
            meta.get("job_name"),
            meta.get("machine_id"),
            meta.get("material_id"),
            meta.get("tool_d"),
            meta.get("stepover"),
            meta.get("stepdown"),
            meta.get("post_id"),
            meta.get("feed_xy"),
            meta.get("rpm"),
            meta.get("est_time_s"),
            meta.get("act_time_s"),
            meta.get("notes"),
        ),
    )
    run_id = cur.lastrowid
    con.commit()
    con.close()
    return run_id


def insert_segments(run_id: int, segs: Iterable[Dict[str, Any]]):
    """Bulk insert segment records for a run."""
    con = open_db()
    cur = con.cursor()
    cur.executemany(
        """INSERT OR REPLACE INTO segments
      (run_id, idx, code, x, y, len_mm, limit, slowdown, trochoid, radius_mm, feed_f)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        [
            (
                run_id,
                s.get("idx"),
                s.get("code"),
                s.get("x"),
                s.get("y"),
                s.get("len_mm"),
                s.get("limit"),
                s.get("slowdown"),
                1 if s.get("trochoid") else 0,
                s.get("radius_mm"),
                s.get("feed_f"),
            )
            for s in segs
        ],
    )
    con.commit()
    con.close()


def fetch_caps_by_machine(machine_id: str) -> List[sqlite3.Row]:
    """Aggregate bottleneck counts (feed_cap/accel/jerk/none) for a machine."""
    con = open_db()
    rows = con.execute(
        """SELECT limit, COUNT(*) c FROM segments
                          JOIN runs ON segments.run_id=runs.id
                          WHERE runs.machine_id=?
                          GROUP BY limit""",
        (machine_id,),
    ).fetchall()
    con.close()
    return rows
