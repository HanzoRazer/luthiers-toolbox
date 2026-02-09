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
from ..core.rmos_db import RMOSDatabase


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
    
    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get jobs by status."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE status = ?
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (status,))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
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
    
    def get_by_job_type(self, job_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get jobs by type."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE job_type = ?
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (job_type,))
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

    def list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Alias for get_all() for interface compatibility."""
        return self.get_all(limit=limit, offset=offset)

    def list_rosette_cnc_exports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent rosette CNC export jobs (limited)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE job_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (JOB_TYPE_ROSETTE_CNC_EXPORT, limit))
            rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent jobs across all types."""
        return self.get_all(limit=limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get job statistics."""
        query = """
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                AVG(CASE WHEN duration_seconds IS NOT NULL THEN duration_seconds END) as avg_duration,
                COUNT(DISTINCT job_type) as unique_job_types,
                COUNT(DISTINCT pattern_id) as unique_patterns
            FROM joblogs
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
        
        total = row['total_count']
        completed = row['completed_count']
        success_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'total_count': total,
            'completed_count': completed,
            'failed_count': row['failed_count'],
            'running_count': row['running_count'],
            'pending_count': row['pending_count'],
            'success_rate': round(success_rate, 2),
            'avg_duration': row['avg_duration'],
            'unique_job_types': row['unique_job_types'],
            'unique_patterns': row['unique_patterns']
        }
    
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

    # ========== N10/N14: CNC Export Job Helpers ==========
    
    def create_rosette_cnc_export_job(
        self,
        pattern_id: Optional[str],
        ring_id: int,
        material: str,
        jig_origin: Dict[str, Any],
        envelope: Dict[str, Any],
        parameters_extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a JobLog entry for a rosette CNC export."""
        params = {
            "ring_id": ring_id,
            "material": material,
            "jig_origin": jig_origin,
            "envelope": envelope,
        }
        if parameters_extra:
            params.update(parameters_extra)

        return self.create_rosette_job(
            job_type=JOB_TYPE_ROSETTE_CNC_EXPORT,
            pattern_id=pattern_id,
            parameters=params,
            status="running",
        )

    def complete_job_with_results(
        self,
        job_id: str,
        status: str,
        results: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Generic helper to mark a job as completed / failed with result payload."""
        end_time = datetime.utcnow().isoformat()
        
        # Calculate duration if job has start_time
        existing_job = self.get(job_id)
        duration_seconds = None
        
        if existing_job and existing_job.get('start_time'):
            try:
                start = datetime.fromisoformat(existing_job['start_time'])
                end = datetime.fromisoformat(end_time)
                duration_seconds = (end - start).total_seconds()
            except (ValueError, TypeError):
                pass  # Keep duration as None if timestamp parsing fails

        return self.update_status(
            job_id=job_id,
            status=status,
            end_time=end_time,
            duration_seconds=duration_seconds,
            results=results,
        )
