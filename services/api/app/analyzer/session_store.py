"""
Session Store — SQLite persistence for tap-tone sessions.

Stores cross-session data for mass-frequency tracking (Ross Echols method).
"Two points make a line. A line is a function."
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from .schemas import SessionRecord


# Database location
DATA_DIR = Path(__file__).parent.parent / ".data"
DB_PATH = DATA_DIR / "tap_tone_sessions.db"


def _ensure_db():
    """Create database and tables if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                specimen_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                mass_g REAL NOT NULL,
                brace_location TEXT,
                mode_frequencies_json TEXT NOT NULL,
                k_eff_mean REAL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_specimen
            ON sessions(specimen_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_timestamp
            ON sessions(specimen_id, timestamp)
        """)
        conn.commit()


@contextmanager
def _get_conn():
    """Get a database connection."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class SessionStore:
    """
    Persistent storage for tap-tone sessions.

    Enables cross-session analysis for mass-frequency tracking.
    """

    def __init__(self):
        _ensure_db()

    def record_session(
        self,
        specimen_id: str,
        mass_g: float,
        mode_frequencies_hz: List[float],
        timestamp: Optional[str] = None,
        brace_location: Optional[str] = None,
        k_eff_mean: Optional[float] = None,
    ) -> SessionRecord:
        """
        Record a new tap-tone session.

        Args:
            specimen_id: Unique identifier for the instrument/plate
            mass_g: Mass at time of measurement (grams)
            mode_frequencies_hz: Modal frequencies in order [mode1, mode2, ...]
            timestamp: ISO timestamp (defaults to now)
            brace_location: Which brace was worked before this session
            k_eff_mean: Mean K_eff from stiffness map (optional)

        Returns:
            SessionRecord with generated session_id
        """
        session_id = str(uuid4())[:8]
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        created_at = datetime.now(timezone.utc).isoformat()

        with _get_conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    session_id, specimen_id, timestamp, mass_g,
                    brace_location, mode_frequencies_json, k_eff_mean, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    specimen_id,
                    ts,
                    mass_g,
                    brace_location,
                    json.dumps(mode_frequencies_hz),
                    k_eff_mean,
                    created_at,
                )
            )
            conn.commit()

        return SessionRecord(
            session_id=session_id,
            specimen_id=specimen_id,
            timestamp=ts,
            mass_g=mass_g,
            brace_location=brace_location,
            mode_frequencies_hz=mode_frequencies_hz,
            k_eff_mean=k_eff_mean,
        )

    def get_sessions(
        self,
        specimen_id: str,
        brace_location: Optional[str] = None,
    ) -> List[SessionRecord]:
        """
        Get all sessions for a specimen, ordered by timestamp.

        Args:
            specimen_id: The specimen to query
            brace_location: Filter by brace location (optional)

        Returns:
            List of SessionRecord ordered chronologically
        """
        with _get_conn() as conn:
            if brace_location:
                cursor = conn.execute(
                    """
                    SELECT * FROM sessions
                    WHERE specimen_id = ? AND brace_location = ?
                    ORDER BY timestamp ASC
                    """,
                    (specimen_id, brace_location)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM sessions
                    WHERE specimen_id = ?
                    ORDER BY timestamp ASC
                    """,
                    (specimen_id,)
                )

            rows = cursor.fetchall()

        return [
            SessionRecord(
                session_id=row["session_id"],
                specimen_id=row["specimen_id"],
                timestamp=row["timestamp"],
                mass_g=row["mass_g"],
                brace_location=row["brace_location"],
                mode_frequencies_hz=json.loads(row["mode_frequencies_json"]),
                k_eff_mean=row["k_eff_mean"],
            )
            for row in rows
        ]

    def get_specimen_ids(self) -> List[str]:
        """Get all unique specimen IDs in the database."""
        with _get_conn() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT specimen_id FROM sessions ORDER BY specimen_id"
            )
            return [row[0] for row in cursor.fetchall()]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID. Returns True if deleted."""
        with _get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_specimen(self, specimen_id: str) -> int:
        """Delete all sessions for a specimen. Returns count deleted."""
        with _get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE specimen_id = ?",
                (specimen_id,)
            )
            conn.commit()
            return cursor.rowcount
