"""
RMOS SQLite Store Base Classes (N8.6)

Abstract base classes for all RMOS SQLite stores, providing:
- Common CRUD operations
- Consistent error handling
- Automatic timestamp management
- JSON serialization helpers
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any, TypeVar, Generic
import json
import logging
from uuid import uuid4

from ..core.rmos_db import get_rmos_db, RMOSDatabase

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SQLiteStoreBase(ABC, Generic[T]):
    """
    Abstract base class for RMOS SQLite stores.
    
    Provides common CRUD operations and utilities for all entity types.
    Subclasses must implement table-specific operations.
    """
    
    def __init__(self, db: Optional[RMOSDatabase] = None):
        """
        Initialize store with database connection.
        
        Args:
            db: Optional RMOSDatabase instance (uses singleton if not provided)
        """
        self.db = db or get_rmos_db()
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Table name for this store (e.g., 'patterns', 'joblogs')"""
        pass
    
    @property
    @abstractmethod
    def id_field(self) -> str:
        """Primary key field name (usually 'id')"""
        pass
    
    @abstractmethod
    def _row_to_dict(self, row: Any) -> Dict[str, Any]:
        """
        Convert SQLite Row to dictionary.
        
        Args:
            row: SQLite Row object
            
        Returns:
            Dictionary with deserialized JSON fields
        """
        pass
    
    @abstractmethod
    def _dict_to_row_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert dictionary to SQLite row data.
        
        Args:
            data: Dictionary with domain model fields
            
        Returns:
            Dictionary with serialized JSON fields for SQLite
        """
        pass
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record.
        
        Args:
            data: Entity data (will auto-generate id if missing)
            
        Returns:
            Created entity with id and timestamps
            
        Example:
            pattern = store.create({
                "name": "Celtic Knot",
                "ring_count": 3,
                "geometry": {...}
            })
        """
        # Generate ID if not provided
        if self.id_field not in data:
            data[self.id_field] = str(uuid4())
        
        # Add timestamps
        now = datetime.utcnow().isoformat()
        data['created_at'] = now
        data['updated_at'] = now
        
        # Convert to row data (serialize JSON fields)
        row_data = self._dict_to_row_data(data)
        
        # Build INSERT query
        fields = list(row_data.keys())
        placeholders = ','.join(['?'] * len(fields))
        query = f"""
            INSERT INTO {self.table_name} ({','.join(fields)})
            VALUES ({placeholders})
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(row_data.values()))
        
        logger.info(f"Created {self.table_name} record: {data[self.id_field]}")
        return data
    
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a record by ID.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            Entity dictionary or None if not found
            
        Example:
            pattern = store.get_by_id("pattern-123")
            if pattern:
                print(pattern['name'])
        """
        query = f"SELECT * FROM {self.table_name} WHERE {self.id_field} = ?"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (entity_id,))
            row = cursor.fetchone()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all records with optional pagination.
        
        Args:
            limit: Maximum number of records (None = all)
            offset: Number of records to skip
            
        Returns:
            List of entity dictionaries
            
        Example:
            # Get first 10 patterns
            patterns = store.get_all(limit=10)
            
            # Get next 10
            patterns = store.get_all(limit=10, offset=10)
        """
        query = f"SELECT * FROM {self.table_name} ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing record.
        
        Args:
            entity_id: Primary key value
            data: Fields to update (partial updates supported)
            
        Returns:
            Updated entity or None if not found
            
        Example:
            updated = store.update("pattern-123", {
                "name": "Updated Name",
                "ring_count": 5
            })
        """
        # Check if exists
        existing = self.get_by_id(entity_id)
        if not existing:
            logger.warning(f"{self.table_name} not found for update: {entity_id}")
            return None
        
        # Merge with existing data
        merged = {**existing, **data}
        merged['updated_at'] = datetime.utcnow().isoformat()
        
        # Convert to row data
        row_data = self._dict_to_row_data(merged)
        
        # Build UPDATE query
        fields = [f"{k} = ?" for k in row_data.keys() if k != self.id_field]
        query = f"""
            UPDATE {self.table_name}
            SET {','.join(fields)}
            WHERE {self.id_field} = ?
        """
        
        values = [v for k, v in row_data.items() if k != self.id_field]
        values.append(entity_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))
        
        logger.info(f"Updated {self.table_name} record: {entity_id}")
        return merged
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete a record by ID.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            True if deleted, False if not found
            
        Example:
            if store.delete("pattern-123"):
                print("Deleted successfully")
        """
        query = f"DELETE FROM {self.table_name} WHERE {self.id_field} = ?"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (entity_id,))
            affected = cursor.rowcount
        
        if affected > 0:
            logger.info(f"Deleted {self.table_name} record: {entity_id}")
            return True
        else:
            logger.warning(f"{self.table_name} not found for deletion: {entity_id}")
            return False
    
    def count(self, where_clause: str = "", params: tuple = ()) -> int:
        """
        Count records matching optional filter.
        
        Args:
            where_clause: Optional SQL WHERE clause (without WHERE keyword)
            params: Parameters for WHERE clause
            
        Returns:
            Number of matching records
            
        Example:
            # Total count
            total = store.count()
            
            # Filtered count
            active = store.count("status = ?", ("active",))
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
        
        return result[0] if result else 0
    
    def search(self, field: str, value: str, operator: str = "LIKE") -> List[Dict[str, Any]]:
        """
        Search records by field value.
        
        Args:
            field: Field name to search
            value: Value to search for (use % for LIKE wildcards)
            operator: SQL operator (LIKE, =, >, etc.)
            
        Returns:
            List of matching entities
            
        Example:
            # Fuzzy search
            results = store.search("name", "%rosette%", "LIKE")
            
            # Exact match
            results = store.search("status", "active", "=")
        """
        query = f"SELECT * FROM {self.table_name} WHERE {field} {operator} ?"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (value,))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    # JSON serialization helpers
    
    @staticmethod
    def _serialize_json(obj: Any) -> str:
        """Serialize Python object to JSON string."""
        if obj is None:
            return None
        return json.dumps(obj, default=str)
    
    @staticmethod
    def _deserialize_json(json_str: Optional[str]) -> Any:
        """Deserialize JSON string to Python object."""
        if json_str is None or json_str == "":
            return None
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to deserialize JSON: {json_str[:100]}...")
            return None
