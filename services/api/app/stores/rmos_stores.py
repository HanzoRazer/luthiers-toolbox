"""
RMOS Store Factory (N8.6)

Dependency injection system for RMOS SQLite stores.
Provides singleton access to all store instances.
"""

from typing import Optional

from ..core.rmos_db import RMOSDatabase, get_rmos_db
from .sqlite_pattern_store import SQLitePatternStore
from .sqlite_joblog_store import SQLiteJobLogStore
from .sqlite_strip_family_store import SQLiteStripFamilyStore


class RMOSStores:
    """
    Factory for RMOS store access.
    
    Provides singleton instances of all stores with shared database connection.
    Use this class to access stores in application code.
    
    Example:
        from app.stores.rmos_stores import get_rmos_stores
        
        stores = get_rmos_stores()
        pattern = stores.patterns.get_by_id("pattern-123")
        jobs = stores.joblogs.get_by_status("completed")
    """
    
    def __init__(self, db: Optional[RMOSDatabase] = None):
        """
        Initialize store factory.
        
        Args:
            db: Optional RMOSDatabase instance (uses singleton if not provided)
        """
        self._db = db or get_rmos_db()
        self._patterns: Optional[SQLitePatternStore] = None
        self._joblogs: Optional[SQLiteJobLogStore] = None
        self._strip_families: Optional[SQLiteStripFamilyStore] = None
    
    @property
    def patterns(self) -> SQLitePatternStore:
        """
        Get pattern store instance.
        
        Returns:
            SQLitePatternStore for rosette pattern operations
        """
        if self._patterns is None:
            self._patterns = SQLitePatternStore(self._db)
        return self._patterns
    
    @property
    def joblogs(self) -> SQLiteJobLogStore:
        """
        Get joblog store instance.
        
        Returns:
            SQLiteJobLogStore for manufacturing job operations
        """
        if self._joblogs is None:
            self._joblogs = SQLiteJobLogStore(self._db)
        return self._joblogs
    
    @property
    def strip_families(self) -> SQLiteStripFamilyStore:
        """
        Get strip family store instance.
        
        Returns:
            SQLiteStripFamilyStore for material strip operations
        """
        if self._strip_families is None:
            self._strip_families = SQLiteStripFamilyStore(self._db)
        return self._strip_families
    
    @property
    def db(self) -> RMOSDatabase:
        """
        Get underlying database instance.
        
        Returns:
            RMOSDatabase for direct database access
        """
        return self._db


# Singleton instance
_stores_instance: Optional[RMOSStores] = None


def get_rmos_stores(db: Optional[RMOSDatabase] = None) -> RMOSStores:
    """
    Get singleton RMOS stores instance.
    
    Args:
        db: Optional custom database (only used on first call)
        
    Returns:
        Shared RMOSStores factory
        
    Example:
        stores = get_rmos_stores()
        
        # Create a pattern
        pattern = stores.patterns.create({
            "name": "Celtic Knot",
            "ring_count": 3,
            "geometry": {"rings": [...]}
        })
        
        # Create a job
        job = stores.joblogs.create({
            "job_type": "slice",
            "pattern_id": pattern['id'],
            "status": "pending",
            "parameters": {"blade_id": "blade-01"}
        })
        
        # Query strip families
        families = stores.strip_families.get_by_material_type("maple")
    """
    global _stores_instance
    if _stores_instance is None:
        _stores_instance = RMOSStores(db)
    return _stores_instance
