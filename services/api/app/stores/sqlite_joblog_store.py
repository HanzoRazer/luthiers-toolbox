"""
RMOS JobLog Store (N8.6 + N11.1)

SQLite store for manufacturing run records.
Handles CRUD operations for job tracking, status, and results.

N11.1 Extensions:
- Rosette job type constants
- create_rosette_job helper method
"""

from typing import Dict, Any, Optional, List
import sqlite3
from datetime import datetime

from .sqlite_base import SQLiteStoreBase


# ========== N11.1: Rosette Job Type Constants ==========

# Rosette job types for RMOS Studio operations
JOB_TYPE_ROSETTE_SLICE_BATCH = "rosette_slice_batch"
JOB_TYPE_ROSETTE_PATTERN_GENERATION = "rosette_pattern_generation"
JOB_TYPE_ROSETTE_PREVIEW = "rosette_preview"
JOB_TYPE_ROSETTE_CNC_EXPORT = "rosette_cnc_export"
JOB_TYPE_ROSETTE_SEGMENTATION = "rosette_segmentation"
JOB_TYPE_ROSETTE_VALIDATION = "rosette_validation"

# ========== N10/N14: Additional CNC Job Types ==========
JOB_TYPE_ROSETTE_CNC_SIMULATION = "rosette_cnc_simulation"


class SQLiteJobLogStore(SQLiteStoreBase):
    """
    Store for manufacturing job logs.
    
    Manages:
    - Job execution records
    - Status tracking (pending, running, completed, failed)
    - Duration and result metrics
    - Parameter and result storage
    """
    
    @property
    def table_name(self) -> str:
        return "joblogs"
    
    @property
    def id_field(self) -> str:
        return "id"
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row to joblog dictionary.
        
        Deserializes JSON fields:
        - parameters_json → parameters
        - results_json → results
        """
        return {
            'id': row['id'],
            'job_type': row['job_type'],
            'pattern_id': row['pattern_id'],
            'strip_family_id': row['strip_family_id'],
            'status': row['status'],
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'duration_seconds': row['duration_seconds'],
            'parameters': self._deserialize_json(row['parameters_json']),
            'results': self._deserialize_json(row['results_json']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
    
    def _dict_to_row_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert joblog dictionary to SQLite row data.
        
        Serializes JSON fields:
        - parameters → parameters_json
        - results → results_json
        """
        return {
            'id': data['id'],
            'job_type': data['job_type'],
            'pattern_id': data.get('pattern_id'),
            'strip_family_id': data.get('strip_family_id'),
            'status': data.get('status', 'pending'),
            'start_time': data.get('start_time'),
            'end_time': data.get('end_time'),
            'duration_seconds': data.get('duration_seconds'),
            'parameters_json': self._serialize_json(data.get('parameters')),
            'results_json': self._serialize_json(data.get('results')),
            'created_at': data['created_at'],
            'updated_at': data['updated_at']
        }
    
    def get_by_pattern(self, pattern_id: str) -> List[Dict[str, Any]]:
        """Get all jobs for a specific pattern."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE pattern_id = ?
            ORDER BY created_at DESC
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (pattern_id,))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a single job by job_id."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE id = ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (job_id,))
            row = cursor.fetchone()
        
        if row is None:
            return None

        return self._row_to_dict(row)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_job() for interface compatibility."""
        return self.get_job(job_id)

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent jobs across all types."""
        return self.get_all(limit=limit)
    
    def update_status(self, job_id: str, status: str, 
                      end_time: Optional[str] = None,
                      duration_seconds: Optional[float] = None,
                      results: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Update job status and optionally completion data."""
        update_data = {'status': status}
        
        if end_time:
            update_data['end_time'] = end_time
        if duration_seconds is not None:
            update_data['duration_seconds'] = duration_seconds
        if results:
            update_data['results'] = results
        
        return self.update(job_id, update_data)
    
    # ========== N11.1: Rosette Job Creation ==========
    
    def create_rosette_job(
        self,
        job_type: str,
        pattern_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        status: str = "planned"
    ) -> Dict[str, Any]:
        """Create a JobLog entry for a rosette-related operation."""
        import uuid
        
        # Generate unique job ID
        job_id = f"JOB-ROSETTE-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        # Build job data
        job_data = {
            'id': job_id,
            'job_type': job_type,
            'pattern_id': pattern_id,
            'strip_family_id': None,  # Can be set later if needed
            'status': status,
            'start_time': datetime.utcnow().isoformat() if status == "running" else None,
            'end_time': None,
            'duration_seconds': None,
            'parameters': parameters or {},
            'results': {},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Insert using parent create method
        return self.create(job_data)


