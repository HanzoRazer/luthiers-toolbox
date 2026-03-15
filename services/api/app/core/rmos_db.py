"""
RMOS Database Core Infrastructure (N8.6 + Store Migration)

Supports both SQLite and PostgreSQL backends via DATABASE_URL.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator, Any
import logging

logger = logging.getLogger(__name__)
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "rmos.db"
SCHEMA_VERSION = 3  # Added art_jobs, art_presets tables


def _is_postgresql_url(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgres://")


class RMOSDatabase:
    """Database manager supporting SQLite and PostgreSQL."""

    def __init__(self, db_path: Optional[Path] = None):
        db_url = os.environ.get("DATABASE_URL", "")
        self._is_postgres = _is_postgresql_url(db_url)

        if self._is_postgres:
            self._pg_url = db_url
            if self._pg_url.startswith("postgres://"):
                self._pg_url = "postgresql://" + self._pg_url[11:]
            self.db_path = None
            logger.info("RMOS using PostgreSQL backend")
        else:
            self.db_path = db_path or DEFAULT_DB_PATH
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._pg_url = None
            logger.info(f"RMOS using SQLite at {self.db_path}")

        self._initialize_schema()

    @property
    def backend_type(self) -> str:
        return "postgresql" if self._is_postgres else "sqlite"

    @contextmanager
    def get_connection(self, row_factory: bool = True) -> Generator[Any, None, None]:
        if self._is_postgres:
            yield from self._get_pg_connection(row_factory)
        else:
            yield from self._get_sqlite_connection(row_factory)

    def _get_sqlite_connection(self, row_factory: bool):
        conn = sqlite3.connect(str(self.db_path))
        if row_factory:
            conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQLite error: {e}")
            raise
        finally:
            conn.close()

    def _get_pg_connection(self, row_factory: bool):
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise ImportError("psycopg2 required. pip install psycopg2-binary")
        conn = psycopg2.connect(self._pg_url)
        try:
            if row_factory:
                conn.cursor_factory = psycopg2.extras.RealDictCursor
            yield conn
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"PostgreSQL error: {e}")
            raise
        finally:
            conn.close()

    def _initialize_schema(self):
        if self._is_postgres:
            self._init_pg()
        else:
            self._init_sqlite()

    def _init_sqlite(self):
        with self.get_connection(row_factory=False) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS patterns (id TEXT PRIMARY KEY, name TEXT NOT NULL, ring_count INTEGER NOT NULL, geometry_json TEXT NOT NULL, strip_family_id TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, metadata_json TEXT, pattern_type TEXT DEFAULT 'generic', rosette_geometry TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS strip_families (id TEXT PRIMARY KEY, name TEXT NOT NULL, strip_width_mm REAL NOT NULL, strip_thickness_mm REAL NOT NULL, material_type TEXT NOT NULL, strips_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, metadata_json TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS joblogs (id TEXT PRIMARY KEY, job_type TEXT NOT NULL, pattern_id TEXT, strip_family_id TEXT, status TEXT DEFAULT 'pending', start_time TEXT, end_time TEXT, duration_seconds REAL, parameters_json TEXT NOT NULL, results_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (pattern_id) REFERENCES patterns(id), FOREIGN KEY (strip_family_id) REFERENCES strip_families(id))")
            c.execute("CREATE INDEX IF NOT EXISTS idx_patterns_name ON patterns(name)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_patterns_strip_family ON patterns(strip_family_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type ON patterns(pattern_type)")
            c.execute("PRAGMA table_info(patterns)")
            cols = {r[1] for r in c.fetchall()}
            if 'pattern_type' not in cols:
                c.execute("ALTER TABLE patterns ADD COLUMN pattern_type TEXT DEFAULT 'generic'")
            if 'rosette_geometry' not in cols:
                c.execute("ALTER TABLE patterns ADD COLUMN rosette_geometry TEXT")
            c.execute("CREATE INDEX IF NOT EXISTS idx_joblogs_pattern ON joblogs(pattern_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_joblogs_status ON joblogs(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_joblogs_created ON joblogs(created_at DESC)")
            # Art Studio tables (v3)
            c.execute("CREATE TABLE IF NOT EXISTS art_jobs (id TEXT PRIMARY KEY, job_type TEXT NOT NULL, post_preset TEXT, rings INTEGER, z_passes INTEGER, length_mm REAL, gcode_lines INTEGER, meta_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS art_presets (id TEXT PRIMARY KEY, lane TEXT NOT NULL, name TEXT NOT NULL, params_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_jobs_type ON art_jobs(job_type)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_jobs_created ON art_jobs(created_at DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_presets_lane ON art_presets(lane)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_presets_name ON art_presets(name)")
            c.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.commit()

    def _init_pg(self):
        with self.get_connection(row_factory=False) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT NOW())")
            c.execute("CREATE TABLE IF NOT EXISTS patterns (id TEXT PRIMARY KEY, name TEXT NOT NULL, ring_count INTEGER NOT NULL, geometry_json TEXT NOT NULL, strip_family_id TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW(), metadata_json TEXT, pattern_type TEXT DEFAULT 'generic', rosette_geometry TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS strip_families (id TEXT PRIMARY KEY, name TEXT NOT NULL, strip_width_mm DOUBLE PRECISION NOT NULL, strip_thickness_mm DOUBLE PRECISION NOT NULL, material_type TEXT NOT NULL, strips_json TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW(), metadata_json TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS joblogs (id TEXT PRIMARY KEY, job_type TEXT NOT NULL, pattern_id TEXT REFERENCES patterns(id), strip_family_id TEXT REFERENCES strip_families(id), status TEXT DEFAULT 'pending', start_time TIMESTAMPTZ, end_time TIMESTAMPTZ, duration_seconds DOUBLE PRECISION, parameters_json TEXT NOT NULL, results_json TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())")
            c.execute("CREATE INDEX IF NOT EXISTS idx_patterns_name ON patterns(name)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_patterns_strip_family ON patterns(strip_family_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type ON patterns(pattern_type)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_joblogs_pattern ON joblogs(pattern_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_joblogs_status ON joblogs(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_joblogs_created ON joblogs(created_at DESC)")
            # Art Studio tables (v3)
            c.execute("CREATE TABLE IF NOT EXISTS art_jobs (id TEXT PRIMARY KEY, job_type TEXT NOT NULL, post_preset TEXT, rings INTEGER, z_passes INTEGER, length_mm DOUBLE PRECISION, gcode_lines INTEGER, meta_json TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())")
            c.execute("CREATE TABLE IF NOT EXISTS art_presets (id TEXT PRIMARY KEY, lane TEXT NOT NULL, name TEXT NOT NULL, params_json TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_jobs_type ON art_jobs(job_type)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_jobs_created ON art_jobs(created_at DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_presets_lane ON art_presets(lane)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_art_presets_name ON art_presets(name)")
            c.execute("INSERT INTO schema_version (version) VALUES (%s) ON CONFLICT (version) DO NOTHING", (SCHEMA_VERSION,))
            conn.commit()

    def get_schema_version(self) -> int:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT MAX(version) FROM schema_version")
            r = c.fetchone()
            if r is None:
                return 0
            if isinstance(r, dict):
                return r.get('max', 0) or 0
            return r[0] if r[0] else 0

    def execute_query(self, query: str, params: tuple = ()) -> list:
        if self._is_postgres:
            query = query.replace('?', '%s')
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.fetchall()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        if self._is_postgres:
            query = query.replace('?', '%s')
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.rowcount

    def vacuum(self):
        if self._is_postgres:
            import psycopg2
            conn = psycopg2.connect(self._pg_url)
            conn.autocommit = True
            conn.cursor().execute("VACUUM ANALYZE")
            conn.close()
        else:
            with self.get_connection(row_factory=False) as conn:
                conn.execute("VACUUM")

    def backup(self, backup_path: Path):
        if self._is_postgres:
            raise NotImplementedError("Use pg_dump for PostgreSQL")
        import shutil
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, backup_path)


_db_instance: Optional[RMOSDatabase] = None


def get_rmos_db(db_path: Optional[Path] = None) -> RMOSDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = RMOSDatabase(db_path)
    return _db_instance


def reset_rmos_db() -> None:
    global _db_instance
    _db_instance = None
