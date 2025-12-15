"""
CP-S59: Saw JobLog Models
Run record storage with saw-specific metadata fields.

Stores:
- Run records: op_type, machine_profile, material_family, blade_id
- Telemetry data: saw_rpm, feed_ipm, spindle_load_pct, axis_load_pct, vibration_rms, sound_db
- Outcome tracking: success, error messages, operator notes
- Performance metrics: actual_time_s, total_length_mm, depth_passes

Integration:
- CP-S50: blade_id references saw_blade_registry
- CP-S52: machine_profile + material → lane_key for learned_overrides
- CP-S60: Telemetry data feeds live learn ingestor
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class SawOperationType(str, Enum):
    """Saw operation types"""
    SLICE = "slice"
    BATCH = "batch"
    CONTOUR = "contour"
    CUSTOM = "custom"


class RunStatus(str, Enum):
    """Run completion status"""
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"
    PENDING = "pending"


# ============================================================================
# Models
# ============================================================================

class TelemetryData(BaseModel):
    """Telemetry data captured during run"""
    saw_rpm: Optional[float] = Field(None, description="Spindle RPM")
    feed_ipm: Optional[float] = Field(None, description="Feed rate in inches/min")
    spindle_load_pct: Optional[float] = Field(None, ge=0, le=100, description="Spindle load %")
    axis_load_pct: Optional[float] = Field(None, ge=0, le=100, description="Axis load %")
    vibration_rms: Optional[float] = Field(None, ge=0, description="Vibration RMS (g)")
    sound_db: Optional[float] = Field(None, ge=0, description="Sound level (dB)")
    
    # Computed risk scores (0-1, higher = riskier)
    overload_risk: Optional[float] = Field(None, ge=0, le=1, description="Spindle overload risk")
    vibration_risk: Optional[float] = Field(None, ge=0, le=1, description="Vibration risk")
    sound_risk: Optional[float] = Field(None, ge=0, le=1, description="Sound risk")
    overall_risk: Optional[float] = Field(None, ge=0, le=1, description="Overall risk score")


class SawRunRecord(BaseModel):
    """Complete run record with saw-specific metadata"""
    
    # Identity
    run_id: str = Field(..., description="Unique run identifier")
    timestamp: str = Field(..., description="ISO timestamp when run started")
    
    # Operation metadata
    op_type: SawOperationType = Field(..., description="Operation type (slice/batch/contour)")
    machine_profile: str = Field(..., description="Machine profile identifier")
    material_family: str = Field(..., description="Material family (hardwood/softwood/plywood/mdf)")
    blade_id: str = Field(..., description="Blade ID from CP-S50 registry")
    
    # Geometry metadata
    safe_z: float = Field(..., gt=0, description="Safe Z height (mm)")
    depth_passes: int = Field(..., ge=1, description="Number of depth passes")
    total_length_mm: float = Field(..., gt=0, description="Total toolpath length (mm)")
    
    # Parameters used
    planned_rpm: float = Field(..., gt=0, description="Planned RPM")
    planned_feed_ipm: float = Field(..., gt=0, description="Planned feed rate (IPM)")
    planned_doc_mm: float = Field(..., gt=0, description="Planned depth of cut (mm)")
    
    # Telemetry
    telemetry: Optional[TelemetryData] = Field(None, description="Captured telemetry data")
    
    # Outcome
    status: RunStatus = Field(RunStatus.PENDING, description="Run status")
    actual_time_s: Optional[float] = Field(None, ge=0, description="Actual run time (seconds)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    operator_notes: Optional[str] = Field(None, description="Operator notes")
    
    # Learning metadata
    lane_scale_before: Optional[float] = Field(None, description="Lane scale before run")
    lane_scale_after: Optional[float] = Field(None, description="Lane scale after run (if updated)")
    auto_learned: bool = Field(False, description="Whether auto-learning was applied")


class SawRunRecordCreate(BaseModel):
    """Request to create new run record"""
    
    op_type: SawOperationType
    machine_profile: str
    material_family: str
    blade_id: str
    
    safe_z: float = Field(..., gt=0)
    depth_passes: int = Field(..., ge=1)
    total_length_mm: float = Field(..., gt=0)
    
    planned_rpm: float = Field(..., gt=0)
    planned_feed_ipm: float = Field(..., gt=0)
    planned_doc_mm: float = Field(..., gt=0)
    
    operator_notes: Optional[str] = None


class SawRunRecordUpdate(BaseModel):
    """Request to update existing run record"""
    
    status: Optional[RunStatus] = None
    actual_time_s: Optional[float] = Field(None, ge=0)
    error_message: Optional[str] = None
    operator_notes: Optional[str] = None
    telemetry: Optional[TelemetryData] = None


# ============================================================================
# Store
# ============================================================================

class SawJobLogStore:
    """Storage for saw run records"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.runs_file = data_dir / "saw_runs.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty store if needed
        if not self.runs_file.exists():
            self._save({"runs": []})
    
    def _load(self) -> Dict[str, Any]:
        """Load runs from JSON"""
        with open(self.runs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save(self, data: Dict[str, Any]) -> None:
        """Save runs to JSON"""
        with open(self.runs_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_run(self, create_req: SawRunRecordCreate) -> SawRunRecord:
        """Create new run record"""
        data = self._load()
        
        # Generate run ID
        run_id = f"saw_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create record
        record = SawRunRecord(
            run_id=run_id,
            timestamp=timestamp,
            op_type=create_req.op_type,
            machine_profile=create_req.machine_profile,
            material_family=create_req.material_family,
            blade_id=create_req.blade_id,
            safe_z=create_req.safe_z,
            depth_passes=create_req.depth_passes,
            total_length_mm=create_req.total_length_mm,
            planned_rpm=create_req.planned_rpm,
            planned_feed_ipm=create_req.planned_feed_ipm,
            planned_doc_mm=create_req.planned_doc_mm,
            operator_notes=create_req.operator_notes,
            status=RunStatus.PENDING
        )
        
        data["runs"].append(record.dict())
        self._save(data)
        
        return record
    
    def get_run(self, run_id: str) -> Optional[SawRunRecord]:
        """Get run by ID"""
        data = self._load()
        
        for run_dict in data["runs"]:
            if run_dict["run_id"] == run_id:
                return SawRunRecord(**run_dict)
        
        return None
    
    def update_run(self, run_id: str, update_req: SawRunRecordUpdate) -> Optional[SawRunRecord]:
        """Update existing run record"""
        data = self._load()
        
        for i, run_dict in enumerate(data["runs"]):
            if run_dict["run_id"] == run_id:
                # Apply updates
                if update_req.status is not None:
                    run_dict["status"] = update_req.status.value
                if update_req.actual_time_s is not None:
                    run_dict["actual_time_s"] = update_req.actual_time_s
                if update_req.error_message is not None:
                    run_dict["error_message"] = update_req.error_message
                if update_req.operator_notes is not None:
                    run_dict["operator_notes"] = update_req.operator_notes
                if update_req.telemetry is not None:
                    run_dict["telemetry"] = update_req.telemetry.dict()
                
                data["runs"][i] = run_dict
                self._save(data)
                
                return SawRunRecord(**run_dict)
        
        return None
    
    def list_runs(
        self,
        limit: Optional[int] = None,
        machine_profile: Optional[str] = None,
        material_family: Optional[str] = None,
        blade_id: Optional[str] = None,
        status: Optional[RunStatus] = None
    ) -> List[SawRunRecord]:
        """List runs with optional filters"""
        data = self._load()
        runs = []
        
        for run_dict in data["runs"]:
            # Apply filters
            if machine_profile and run_dict.get("machine_profile") != machine_profile:
                continue
            if material_family and run_dict.get("material_family") != material_family:
                continue
            if blade_id and run_dict.get("blade_id") != blade_id:
                continue
            if status and run_dict.get("status") != status.value:
                continue
            
            runs.append(SawRunRecord(**run_dict))
        
        # Sort by timestamp descending (newest first)
        runs.sort(key=lambda r: r.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            runs = runs[:limit]
        
        return runs
    
    def delete_run(self, run_id: str) -> bool:
        """Delete run record"""
        data = self._load()
        
        for i, run_dict in enumerate(data["runs"]):
            if run_dict["run_id"] == run_id:
                data["runs"].pop(i)
                self._save(data)
                return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics"""
        data = self._load()
        runs = [SawRunRecord(**r) for r in data["runs"]]
        
        if not runs:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "avg_time_s": 0.0,
                "total_length_mm": 0.0,
                "runs_by_status": {},
                "runs_by_machine": {},
                "runs_by_material": {}
            }
        
        # Success rate
        success_count = sum(1 for r in runs if r.status == RunStatus.SUCCESS)
        success_rate = success_count / len(runs) if runs else 0.0
        
        # Average time (only completed runs)
        completed = [r for r in runs if r.actual_time_s is not None]
        avg_time = sum(r.actual_time_s for r in completed) / len(completed) if completed else 0.0
        
        # Total length
        total_length = sum(r.total_length_mm for r in runs)
        
        # By status
        by_status = {}
        for r in runs:
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        
        # By machine
        by_machine = {}
        for r in runs:
            by_machine[r.machine_profile] = by_machine.get(r.machine_profile, 0) + 1
        
        # By material
        by_material = {}
        for r in runs:
            by_material[r.material_family] = by_material.get(r.material_family, 0) + 1
        
        return {
            "total_runs": len(runs),
            "success_rate": success_rate,
            "avg_time_s": avg_time,
            "total_length_mm": total_length,
            "runs_by_status": by_status,
            "runs_by_machine": by_machine,
            "runs_by_material": by_material
        }


# ============================================================================
# Singleton
# ============================================================================

_saw_joblog_store: Optional[SawJobLogStore] = None


def get_saw_joblog_store() -> SawJobLogStore:
    """Get singleton instance of saw joblog store"""
    global _saw_joblog_store
    
    if _saw_joblog_store is None:
        data_dir = Path(__file__).parent.parent.parent / "data" / "cnc_production"
        _saw_joblog_store = SawJobLogStore(data_dir)
    
    return _saw_joblog_store
