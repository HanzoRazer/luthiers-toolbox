"""
Art Jobs SQLite Store

SQLite-backed store for art jobs (rosette CAM, etc.).
Replaces the JSON file-based art_jobs_store.py.
"""

from typing import Dict, Any, Optional, List
import sqlite3

from .sqlite_base import SQLiteStoreBase


class SQLiteArtJobsStore(SQLiteStoreBase):
    """
    Store for art job records.

    Manages:
    - Rosette CAM jobs
    - Job metadata (post preset, rings, z_passes, etc.)
    - Job history and tracking
    """

    @property
    def table_name(self) -> str:
        return "art_jobs"

    @property
    def id_field(self) -> str:
        return "id"

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row to art job dictionary.

        Deserializes JSON fields:
        - meta_json → meta
        """
        return {
            'id': row['id'],
            'job_type': row['job_type'],
            'post_preset': row['post_preset'],
            'rings': row['rings'],
            'z_passes': row['z_passes'],
            'length_mm': row['length_mm'],
            'gcode_lines': row['gcode_lines'],
            'meta': self._deserialize_json(row['meta_json']) or {},
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }

    def _dict_to_row_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert art job dictionary to SQLite row data.

        Serializes JSON fields:
        - meta → meta_json
        """
        return {
            'id': data['id'],
            'job_type': data['job_type'],
            'post_preset': data.get('post_preset'),
            'rings': data.get('rings'),
            'z_passes': data.get('z_passes'),
            'length_mm': data.get('length_mm'),
            'gcode_lines': data.get('gcode_lines'),
            'meta_json': self._serialize_json(data.get('meta')) or '{}',
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
        }

    def get_by_job_type(self, job_type: str) -> List[Dict[str, Any]]:
        """
        Get all jobs of a specific type.

        Args:
            job_type: Job type to filter by (e.g., 'rosette_cam')

        Returns:
            List of jobs matching the type

        Example:
            rosette_jobs = store.get_by_job_type('rosette_cam')
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE job_type = ?
            ORDER BY created_at DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (job_type,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of recent jobs ordered by creation date
        """
        return self.get_all(limit=limit)

    def create_art_job(
        self,
        job_id: str,
        job_type: str,
        post_preset: Optional[str] = None,
        rings: Optional[int] = None,
        z_passes: Optional[int] = None,
        length_mm: Optional[float] = None,
        gcode_lines: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new art job (convenience method matching legacy API).

        Args:
            job_id: Unique job identifier
            job_type: Type of job ('rosette_cam', etc.)
            post_preset: Post-processor preset name
            rings: Number of rings (for rosette jobs)
            z_passes: Number of Z-axis passes
            length_mm: Toolpath length in mm
            gcode_lines: Number of G-code lines
            meta: Additional metadata

        Returns:
            Created job record
        """
        return self.create({
            'id': job_id,
            'job_type': job_type,
            'post_preset': post_preset,
            'rings': rings,
            'z_passes': z_passes,
            'length_mm': length_mm,
            'gcode_lines': gcode_lines,
            'meta': meta or {},
        })
