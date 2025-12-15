# services/api/app/art_studio_rosette_store.py

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.getenv("ART_STUDIO_DB_PATH", "art_studio.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist and seed default presets."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rosette_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                name TEXT,
                preset TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rosette_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                pattern_type TEXT NOT NULL,
                segments INTEGER NOT NULL,
                inner_radius REAL NOT NULL,
                outer_radius REAL NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        # Phase 27.2: Risk snapshots table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rosette_compare_risk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id_a TEXT NOT NULL,
                job_id_b TEXT NOT NULL,
                lane TEXT,
                risk_score REAL NOT NULL,
                diff_json TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # Seed a couple of defaults if table is empty
        cur.execute("SELECT COUNT(*) AS c FROM rosette_presets")
        row = cur.fetchone()
        if row["c"] == 0:
            seed_presets = [
                {
                    "name": "Safe",
                    "pattern_type": "herringbone",
                    "segments": 64,
                    "inner_radius": 40.0,
                    "outer_radius": 45.0,
                    "metadata": {"description": "Conservative geometry for first cuts"},
                },
                {
                    "name": "Aggressive",
                    "pattern_type": "rope",
                    "segments": 96,
                    "inner_radius": 39.0,
                    "outer_radius": 46.0,
                    "metadata": {"description": "Tighter pattern, more detail"},
                },
            ]
            for p in seed_presets:
                cur.execute(
                    """
                    INSERT INTO rosette_presets
                    (name, pattern_type, segments, inner_radius, outer_radius, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p["name"],
                        p["pattern_type"],
                        p["segments"],
                        p["inner_radius"],
                        p["outer_radius"],
                        json.dumps(p["metadata"]),
                    ),
                )


def list_presets() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT name, pattern_type, segments, inner_radius, outer_radius, metadata_json
            FROM rosette_presets
            ORDER BY name ASC
            """
        )
        rows = cur.fetchall()
        presets: List[Dict[str, Any]] = []
        for r in rows:
            presets.append(
                {
                    "name": r["name"],
                    "pattern_type": r["pattern_type"],
                    "segments": r["segments"],
                    "inner_radius": r["inner_radius"],
                    "outer_radius": r["outer_radius"],
                    "metadata": json.loads(r["metadata_json"]),
                }
            )
        return presets


def save_job(
    job_id: str,
    name: str,
    preset: Optional[str],
    payload: Dict[str, Any],
) -> None:
    created_at = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO rosette_jobs (job_id, name, preset, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, name, preset or "", json.dumps(payload), created_at),
        )


def list_jobs(limit: int = 20) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_id, name, preset, payload_json, created_at
            FROM rosette_jobs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        jobs: List[Dict[str, Any]] = []
        for r in rows:
            jobs.append(
                {
                    "job_id": r["job_id"],
                    "name": r["name"],
                    "preset": r["preset"],
                    "payload": json.loads(r["payload_json"]),
                    "created_at": r["created_at"],
                }
            )
        return jobs


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_id, name, preset, payload_json, created_at
            FROM rosette_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "job_id": r["job_id"],
            "name": r["name"],
            "preset": r["preset"],
            "payload": json.loads(r["payload_json"]),
            "created_at": r["created_at"],
        }


# Phase 27.2: Risk snapshot functions


def save_compare_snapshot(
    job_id_a: str,
    job_id_b: str,
    risk_score: float,
    diff_summary: Dict[str, Any],
    lane: Optional[str] = None,
    note: Optional[str] = None,
) -> int:
    """
    Save a comparison snapshot to risk timeline.
    
    Args:
        job_id_a: First job ID
        job_id_b: Second job ID
        risk_score: Calculated risk score (0-100)
        diff_summary: Full diff data from compare endpoint
        lane: Optional lane/category (e.g., 'production', 'testing')
        note: Optional note about this comparison
    
    Returns:
        Snapshot ID
    """
    created_at = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO rosette_compare_risk
            (job_id_a, job_id_b, lane, risk_score, diff_json, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id_a,
                job_id_b,
                lane or "default",
                risk_score,
                json.dumps(diff_summary),
                note,
                created_at,
            ),
        )
        return cur.lastrowid


def get_compare_snapshots(
    job_id_a: Optional[str] = None,
    job_id_b: Optional[str] = None,
    lane: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Retrieve comparison snapshots with optional filtering.
    
    Args:
        job_id_a: Filter by first job ID
        job_id_b: Filter by second job ID
        lane: Filter by lane
        limit: Max results
    
    Returns:
        List of snapshot records
    """
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Build query dynamically based on filters
        where_clauses = []
        params = []
        
        if job_id_a:
            where_clauses.append("job_id_a = ?")
            params.append(job_id_a)
        if job_id_b:
            where_clauses.append("job_id_b = ?")
            params.append(job_id_b)
        if lane:
            where_clauses.append("lane = ?")
            params.append(lane)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        params.append(limit)
        
        cur.execute(
            f"""
            SELECT id, job_id_a, job_id_b, lane, risk_score, diff_json, note, created_at
            FROM rosette_compare_risk
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            tuple(params),
        )
        rows = cur.fetchall()
        snapshots: List[Dict[str, Any]] = []
        for r in rows:
            snapshots.append(
                {
                    "id": r["id"],
                    "job_id_a": r["job_id_a"],
                    "job_id_b": r["job_id_b"],
                    "lane": r["lane"],
                    "risk_score": r["risk_score"],
                    "diff_summary": json.loads(r["diff_json"]),
                    "note": r["note"],
                    "created_at": r["created_at"],
                }
            )
        return snapshots


