"""
RMOS Pattern Store (N8.6 + N11.1)

SQLite store for rosette pattern definitions.
Handles CRUD operations for pattern geometry, metadata, and associations.

N11.1 Extensions:
- Support for pattern_type ('generic', 'rosette')
- Dedicated rosette_geometry field for RMOS Studio patterns
- Type-aware pattern listing and creation
"""

from typing import Dict, Any, Optional, List
import sqlite3
import json

from .sqlite_base import SQLiteStoreBase
from ..core.rmos_db import RMOSDatabase


class SQLitePatternStore(SQLiteStoreBase):
    """
    Store for rosette pattern definitions.
    
    Manages:
    - Pattern geometry (rings, segments, angles)
    - Strip family associations
    - Pattern metadata (creation date, tags, etc.)
    """
    
    @property
    def table_name(self) -> str:
        return "patterns"
    
    @property
    def id_field(self) -> str:
        return "id"
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row to pattern dictionary.
        
        Deserializes JSON fields:
        - geometry_json → geometry
        - metadata_json → metadata
        - rosette_geometry → rosette_geometry (N11.1)
        """
        result = {
            'id': row['id'],
            'name': row['name'],
            'ring_count': row['ring_count'],
            'geometry': self._deserialize_json(row['geometry_json']),
            'strip_family_id': row['strip_family_id'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'metadata': self._deserialize_json(row['metadata_json'])
        }
        
        # N11.1: Add pattern_type and rosette_geometry if available
        if 'pattern_type' in row.keys():
            result['pattern_type'] = row['pattern_type'] or 'generic'
        
        if 'rosette_geometry' in row.keys() and row['rosette_geometry']:
            try:
                result['rosette_geometry'] = json.loads(row['rosette_geometry'])
            except (json.JSONDecodeError, TypeError):
                result['rosette_geometry'] = None
        
        return result
    
    def _dict_to_row_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert pattern dictionary to SQLite row data.
        
        Serializes JSON fields:
        - geometry → geometry_json
        - metadata → metadata_json
        - rosette_geometry → rosette_geometry (N11.1)
        """
        row_data = {
            'id': data['id'],
            'name': data['name'],
            'ring_count': data['ring_count'],
            'geometry_json': self._serialize_json(data.get('geometry')) or data.get('geometry_json', '{}'),
            'strip_family_id': data.get('strip_family_id'),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'metadata_json': self._serialize_json(data.get('metadata')) or data.get('metadata_json', '{}')
        }
        
        # N11.1: Add pattern_type and rosette_geometry if present
        if 'pattern_type' in data:
            row_data['pattern_type'] = data['pattern_type']
        
        if 'rosette_geometry' in data:
            if isinstance(data['rosette_geometry'], dict):
                row_data['rosette_geometry'] = self._serialize_json(data['rosette_geometry'])
            elif isinstance(data['rosette_geometry'], str):
                row_data['rosette_geometry'] = data['rosette_geometry']
        
        return row_data
    
    def get_by_strip_family(self, strip_family_id: str) -> List[Dict[str, Any]]:
        """
        Get all patterns using a specific strip family.
        
        Args:
            strip_family_id: Strip family ID to filter by
            
        Returns:
            List of patterns using this strip family
            
        Example:
            patterns = store.get_by_strip_family("family-123")
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE strip_family_id = ?
            ORDER BY created_at DESC
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (strip_family_id,))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def search_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search patterns by name (case-insensitive).
        
        Args:
            name_pattern: SQL LIKE pattern (use % for wildcards)
            
        Returns:
            List of matching patterns
            
        Example:
            # Find all Celtic patterns
            patterns = store.search_by_name("%celtic%")
        """
        return self.search("name", name_pattern, "LIKE")
    
    def get_by_ring_count(self, ring_count: int) -> List[Dict[str, Any]]:
        """
        Get patterns with specific ring count.
        
        Args:
            ring_count: Number of rings to filter by
            
        Returns:
            List of patterns with matching ring count
            
        Example:
            # Find all 3-ring patterns
            patterns = store.get_by_ring_count(3)
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE ring_count = ?
            ORDER BY name
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (ring_count,))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get pattern statistics.
        
        Returns:
            Dictionary with counts and aggregates
            
        Example:
            stats = store.get_statistics()
            print(f"Total patterns: {stats['total_count']}")
            print(f"Average rings: {stats['avg_ring_count']}")
        """
        query = """
            SELECT
                COUNT(*) as total_count,
                AVG(ring_count) as avg_ring_count,
                MIN(ring_count) as min_ring_count,
                MAX(ring_count) as max_ring_count,
                COUNT(DISTINCT strip_family_id) as unique_families
            FROM patterns
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
        
        return {
            'total_count': row['total_count'],
            'avg_ring_count': row['avg_ring_count'],
            'min_ring_count': row['min_ring_count'],
            'max_ring_count': row['max_ring_count'],
            'unique_families': row['unique_families']
        }
    
    # ========== N11.1: Rosette Pattern Methods ==========
    
    def list_by_type(self, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List patterns filtered by pattern_type.
        
        Args:
            pattern_type: Filter by type ('generic', 'rosette', etc.)
                         None returns all patterns
        
        Returns:
            List of patterns matching the type filter
        
        Example:
            # Get only RMOS Studio rosette patterns
            rosettes = store.list_by_type('rosette')
            
            # Get classic patterns
            classics = store.list_by_type('generic')
            
            # Get all patterns
            all_patterns = store.list_by_type()
        """
        if pattern_type is None:
            return self.list_all()
        
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE pattern_type = ?
            ORDER BY created_at DESC
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (pattern_type,))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def create_rosette(
        self,
        pattern_id: str,
        name: str,
        rosette_geometry: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new RMOS Studio rosette pattern.
        
        Args:
            pattern_id: Unique pattern identifier
            name: Human-readable pattern name
            rosette_geometry: Full rosette definition (rings, columns, segmentation)
            metadata: Optional metadata (complexity, fragility_score, etc.)
        
        Returns:
            Created pattern dictionary
        
        Example:
            pattern = store.create_rosette(
                pattern_id="rosette_001",
                name="Spanish Traditional 5-Ring",
                rosette_geometry={
                    "rings": [
                        {"radius_mm": 40, "width_mm": 3, "tile_length_mm": 2.5, ...}
                    ],
                    "segmentation": {...}
                },
                metadata={"complexity": "medium", "fragility_score": 0.42}
            )
        """
        from datetime import datetime
        
        # Extract ring_count from rosette_geometry
        ring_count = len(rosette_geometry.get('rings', []))
        
        # Build pattern data
        pattern_data = {
            'id': pattern_id,
            'name': name,
            'ring_count': ring_count,
            'geometry': None,  # Keep legacy field for compatibility
            'strip_family_id': None,  # Can be set later if needed
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        # Serialize for insertion
        row_data = self._dict_to_row_data(pattern_data)
        
        # Add N11.1 fields
        row_data['pattern_type'] = 'rosette'
        row_data['rosette_geometry'] = json.dumps(rosette_geometry)
        
        # Insert
        columns = ', '.join(row_data.keys())
        placeholders = ', '.join(['?' for _ in row_data])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(row_data.values()))
            conn.commit()
        
        return self.get_by_id(pattern_id)
    
    def update_rosette_geometry(
        self,
        pattern_id: str,
        rosette_geometry: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update rosette_geometry for an existing rosette pattern.
        
        Args:
            pattern_id: Pattern to update
            rosette_geometry: New rosette geometry definition
        
        Returns:
            Updated pattern dictionary, or None if not found
        
        Example:
            # Update ring configuration
            updated = store.update_rosette_geometry(
                pattern_id="rosette_001",
                rosette_geometry={
                    "rings": [...],  # Updated rings
                    "segmentation": {...}
                }
            )
        """
        from datetime import datetime
        
        # Check if pattern exists
        existing = self.get_by_id(pattern_id)
        if not existing:
            return None
        
        # Update rosette_geometry and updated_at
        query = f"""
            UPDATE {self.table_name}
            SET rosette_geometry = ?, updated_at = ?
            WHERE {self.id_field} = ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (json.dumps(rosette_geometry), datetime.utcnow().isoformat(), pattern_id)
            )
            conn.commit()
        
        return self.get_by_id(pattern_id)
    
    def get_rosette_geometry(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get rosette_geometry field for a rosette pattern.
        
        Args:
            pattern_id: Pattern ID to fetch
        
        Returns:
            Rosette geometry dict, or None if pattern not found or not a rosette
        
        Example:
            geom = store.get_rosette_geometry("rosette_001")
            if geom:
                ring_count = len(geom['rings'])
        """
        pattern = self.get_by_id(pattern_id)
        if not pattern:
            return None
        
        return pattern.get('rosette_geometry')
