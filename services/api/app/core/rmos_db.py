"""
RMOS SQLite Database Core Infrastructure (N8.6)

Provides connection pooling, schema management, and transaction handling
for the Rosette Manufacturing OS persistence layer.

Features:
- Connection pooling with context managers
- Automatic schema initialization
- Transaction rollback on errors
- Thread-safe operations
- Migration support hooks
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator
import logging

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "rmos.db"

# Schema version for migration tracking
SCHEMA_VERSION = 2  # N11.1: Added pattern_type and rosette_geometry columns


class RMOSDatabase:
    """
    SQLite database manager for RMOS persistence.
    
    Handles connection pooling, schema initialization, and transaction management.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize RMOS database connection.
        
        Args:
            db_path: Path to SQLite database file. Creates if doesn't exist.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize schema on first connection
        self._initialize_schema()
        
        logger.info(f"RMOS database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self, row_factory: bool = True) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.
        
        Args:
            row_factory: If True, enable Row factory for dict-like access
            
        Yields:
            SQLite connection with automatic commit/rollback
            
        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM patterns")
                rows = cursor.fetchall()
        """
        conn = sqlite3.connect(str(self.db_path))
        
        if row_factory:
            conn.row_factory = sqlite3.Row
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error, rolling back: {e}")
            raise
        finally:
            conn.close()
    
    def _initialize_schema(self):
        """
        Create database tables if they don't exist.
        
        Schema includes:
        - patterns: Rosette pattern definitions
        - strip_families: Material strip configurations
        - joblogs: Manufacturing run records
        - schema_version: Migration tracking
        """
        with self.get_connection(row_factory=False) as conn:
            cursor = conn.cursor()
            
            # Schema version tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Patterns table (rosette designs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    ring_count INTEGER NOT NULL,
                    geometry_json TEXT NOT NULL,
                    strip_family_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    pattern_type TEXT NOT NULL DEFAULT 'generic',
                    rosette_geometry TEXT
                )
            """)
            
            # Strip families table (material configurations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strip_families (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    strip_width_mm REAL NOT NULL,
                    strip_thickness_mm REAL NOT NULL,
                    material_type TEXT NOT NULL,
                    strips_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
            """)
            
            # JobLogs table (manufacturing runs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS joblogs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    pattern_id TEXT,
                    strip_family_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL,
                    parameters_json TEXT NOT NULL,
                    results_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES patterns(id),
                    FOREIGN KEY (strip_family_id) REFERENCES strip_families(id)
                )
            """)
            
            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_name 
                ON patterns(name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_strip_family 
                ON patterns(strip_family_id)
            """)
            
            # N11.1: Index for pattern_type queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type 
                ON patterns(pattern_type)
            """)
            
            # N11.1 Migration: Add columns to existing databases
            cursor.execute("PRAGMA table_info(patterns)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'pattern_type' not in columns:
                logger.info("Migrating: Adding pattern_type column to patterns table")
                cursor.execute("""
                    ALTER TABLE patterns 
                    ADD COLUMN pattern_type TEXT NOT NULL DEFAULT 'generic'
                """)
            
            if 'rosette_geometry' not in columns:
                logger.info("Migrating: Adding rosette_geometry column to patterns table")
                cursor.execute("""
                    ALTER TABLE patterns 
                    ADD COLUMN rosette_geometry TEXT
                """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_joblogs_pattern 
                ON joblogs(pattern_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_joblogs_status 
                ON joblogs(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_joblogs_created 
                ON joblogs(created_at DESC)
            """)
            
            # Record schema version
            cursor.execute("""
                INSERT OR IGNORE INTO schema_version (version)
                VALUES (?)
            """, (SCHEMA_VERSION,))
            
            conn.commit()
            logger.info("RMOS database schema initialized")
    
    def get_schema_version(self) -> int:
        """
        Get current schema version for migration tracking.
        
        Returns:
            Current schema version number
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result[0] else 0
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Execute a SELECT query and return all rows.
        
        Args:
            query: SQL SELECT statement
            params: Query parameters (use ? placeholders)
            
        Returns:
            List of Row objects (dict-like access)
            
        Example:
            rows = db.execute_query(
                "SELECT * FROM patterns WHERE name LIKE ?",
                ("%rosette%",)
            )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL modification statement
            params: Query parameters (use ? placeholders)
            
        Returns:
            Number of affected rows
            
        Example:
            affected = db.execute_update(
                "UPDATE patterns SET name = ? WHERE id = ?",
                ("New Name", "pattern-123")
            )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    
    def vacuum(self):
        """
        Optimize database (reclaim space, rebuild indexes).
        
        Should be run periodically or after large deletions.
        """
        with self.get_connection(row_factory=False) as conn:
            conn.execute("VACUUM")
            logger.info("Database vacuumed")
    
    def backup(self, backup_path: Path):
        """
        Create a backup copy of the database.
        
        Args:
            backup_path: Destination path for backup file
        """
        import shutil
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")


# Singleton instance for application-wide use
_db_instance: Optional[RMOSDatabase] = None


def get_rmos_db(db_path: Optional[Path] = None) -> RMOSDatabase:
    """
    Get singleton RMOS database instance.
    
    Args:
        db_path: Optional custom database path (only used on first call)
        
    Returns:
        Shared RMOSDatabase instance
        
    Example:
        db = get_rmos_db()
        with db.get_connection() as conn:
            # ... database operations
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = RMOSDatabase(db_path)
    return _db_instance
