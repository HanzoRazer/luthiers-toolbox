"""
Art Presets SQLite Store

SQLite-backed store for art presets (rosette, adaptive, relief, etc.).
Replaces the JSON file-based art_presets_store.py.
"""

from typing import Dict, Any, Optional, List
import sqlite3

from .sqlite_base import SQLiteStoreBase


class SQLiteArtPresetsStore(SQLiteStoreBase):
    """
    Store for art preset definitions.

    Manages:
    - Rosette presets
    - Adaptive presets
    - Relief presets
    - Cross-lane ("all") presets
    """

    @property
    def table_name(self) -> str:
        return "art_presets"

    @property
    def id_field(self) -> str:
        return "id"

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row to art preset dictionary.

        Deserializes JSON fields:
        - params_json → params
        """
        return {
            'id': row['id'],
            'lane': row['lane'],
            'name': row['name'],
            'params': self._deserialize_json(row['params_json']) or {},
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }

    def _dict_to_row_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert art preset dictionary to SQLite row data.

        Serializes JSON fields:
        - params → params_json
        """
        return {
            'id': data['id'],
            'lane': data['lane'],
            'name': data['name'],
            'params_json': self._serialize_json(data.get('params')) or '{}',
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
        }

    def list_by_lane(self, lane: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List presets filtered by lane.

        Args:
            lane: Filter by lane ('rosette', 'adaptive', 'relief', 'all')
                  If None, returns all presets.
                  If specified, returns presets for that lane + 'all' lane.

        Returns:
            List of presets ordered by creation date (newest first)

        Example:
            # Get all rosette presets (including "all" lane)
            rosette_presets = store.list_by_lane('rosette')

            # Get all presets
            all_presets = store.list_by_lane()
        """
        if lane is None:
            return self.get_all()

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE lane = ? OR lane = 'all'
            ORDER BY created_at DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (lane,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def search_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search presets by name (case-insensitive).

        Args:
            name_pattern: SQL LIKE pattern (use % for wildcards)

        Returns:
            List of matching presets

        Example:
            # Find all presets containing "fast"
            presets = store.search_by_name("%fast%")
        """
        return self.search("name", name_pattern, "LIKE")

    def create_preset(
        self,
        lane: str,
        name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a new preset (convenience method matching legacy API).

        Args:
            lane: Lane this preset belongs to ('rosette', 'adaptive', 'relief', 'all')
            name: Human-readable preset name
            params: Preset parameters

        Returns:
            Created preset record
        """
        import time
        preset_id = f"{lane}_preset_{int(time.time() * 1000)}"
        return self.create({
            'id': preset_id,
            'lane': lane,
            'name': name,
            'params': params,
        })

    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a preset by ID (alias for get_by_id).

        Args:
            preset_id: Preset identifier

        Returns:
            Preset dict or None if not found
        """
        return self.get_by_id(preset_id)

    def delete_preset(self, preset_id: str) -> bool:
        """
        Delete a preset by ID (alias for delete).

        Args:
            preset_id: Preset identifier

        Returns:
            True if deleted, False if not found
        """
        return self.delete(preset_id)
