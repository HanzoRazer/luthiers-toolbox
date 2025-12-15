"""
RMOS Strip Family Store (N8.6)

SQLite store for material strip family configurations.
Handles CRUD operations for strip definitions and material specifications.
"""

from typing import Dict, Any, Optional, List
import sqlite3

from .sqlite_base import SQLiteStoreBase
from ..core.rmos_db import RMOSDatabase


class SQLiteStripFamilyStore(SQLiteStoreBase):
    """
    Store for material strip family configurations.
    
    Manages:
    - Strip dimensions (width, thickness)
    - Material types
    - Strip arrangements within families
    - Family metadata
    """
    
    @property
    def table_name(self) -> str:
        return "strip_families"
    
    @property
    def id_field(self) -> str:
        return "id"
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row to strip family dictionary.
        
        Deserializes JSON fields:
        - strips_json → strips
        - metadata_json → metadata
        """
        return {
            'id': row['id'],
            'name': row['name'],
            'strip_width_mm': row['strip_width_mm'],
            'strip_thickness_mm': row['strip_thickness_mm'],
            'material_type': row['material_type'],
            'strips': self._deserialize_json(row['strips_json']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'metadata': self._deserialize_json(row['metadata_json'])
        }
    
    def _dict_to_row_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert strip family dictionary to SQLite row data.
        
        Serializes JSON fields:
        - strips → strips_json
        - metadata → metadata_json
        """
        return {
            'id': data['id'],
            'name': data['name'],
            'strip_width_mm': data['strip_width_mm'],
            'strip_thickness_mm': data['strip_thickness_mm'],
            'material_type': data['material_type'],
            'strips_json': self._serialize_json(data.get('strips')),
            'created_at': data['created_at'],
            'updated_at': data['updated_at'],
            'metadata_json': self._serialize_json(data.get('metadata'))
        }
    
    def get_by_material_type(self, material_type: str) -> List[Dict[str, Any]]:
        """
        Get strip families by material type.
        
        Args:
            material_type: Material type (e.g., "maple", "walnut", "ebony")
            
        Returns:
            List of strip families with matching material
            
        Example:
            # Get all maple families
            maple_families = store.get_by_material_type("maple")
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE material_type = ?
            ORDER BY name
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (material_type,))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def search_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search strip families by name (case-insensitive).
        
        Args:
            name_pattern: SQL LIKE pattern (use % for wildcards)
            
        Returns:
            List of matching strip families
            
        Example:
            # Find all contrast families
            families = store.search_by_name("%contrast%")
        """
        return self.search("name", name_pattern, "LIKE")
    
    def get_by_dimensions(self, width_mm: float, thickness_mm: float, 
                          tolerance: float = 0.1) -> List[Dict[str, Any]]:
        """
        Get strip families matching dimensions (with tolerance).
        
        Args:
            width_mm: Strip width in mm
            thickness_mm: Strip thickness in mm
            tolerance: Allowed variance in mm
            
        Returns:
            List of strip families within tolerance
            
        Example:
            # Find 3mm × 1.5mm strips (±0.1mm)
            families = store.get_by_dimensions(3.0, 1.5)
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE strip_width_mm BETWEEN ? AND ?
              AND strip_thickness_mm BETWEEN ? AND ?
            ORDER BY name
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                width_mm - tolerance, width_mm + tolerance,
                thickness_mm - tolerance, thickness_mm + tolerance
            ))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get strip family statistics.
        
        Returns:
            Dictionary with counts and aggregates
            
        Example:
            stats = store.get_statistics()
            print(f"Total families: {stats['total_count']}")
            print(f"Materials: {stats['unique_materials']}")
        """
        query = """
            SELECT
                COUNT(*) as total_count,
                COUNT(DISTINCT material_type) as unique_materials,
                AVG(strip_width_mm) as avg_width,
                AVG(strip_thickness_mm) as avg_thickness,
                MIN(strip_width_mm) as min_width,
                MAX(strip_width_mm) as max_width
            FROM strip_families
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
        
        # Get material type counts
        material_query = """
            SELECT material_type, COUNT(*) as count
            FROM strip_families
            GROUP BY material_type
            ORDER BY count DESC
        """
        cursor.execute(material_query)
        materials = {row['material_type']: row['count'] for row in cursor.fetchall()}
        
        return {
            'total_count': row['total_count'],
            'unique_materials': row['unique_materials'],
            'avg_width_mm': row['avg_width'],
            'avg_thickness_mm': row['avg_thickness'],
            'min_width_mm': row['min_width'],
            'max_width_mm': row['max_width'],
            'material_counts': materials
        }
