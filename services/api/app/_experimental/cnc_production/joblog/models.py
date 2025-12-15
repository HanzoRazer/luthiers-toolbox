"""
CP-S59 — Saw JobLog Models

Data models for saw operation job logging and telemetry collection.
Tracks execution metadata, G-code, risk assessments, and runtime telemetry samples.

Key Models:
- SawRunMeta: Operation metadata (blade, feeds, depths, etc.)
- SawRunRecord: Complete job log entry with G-code
- TelemetrySample: Real-time execution metrics
- SawTelemetryRecord: Collection of telemetry samples per run

Usage:
```python
from cnc_production.joblog.models import SawRunMeta, SawRunRecord

meta = SawRunMeta(
    op_type="slice",
    blade_id="TENRYU_GM-305100AB",
    rpm=3600,
    feed_ipm=60,
    total_length_mm=300.0
)

run = SawRunRecord(
    run_id="20251127T120000Z_a1b2c3d4",
    meta=meta,
    gcode="G21\\nG90\\n..."
)
```
"""

from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# CORE METADATA
# ============================================================================

OpType = Literal["slice", "batch", "contour"]
RiskGrade = Literal["GREEN", "YELLOW", "RED"]


class SawRunMeta(BaseModel):
    """
    Metadata for a saw operation execution.
    
    Captures planning parameters, machine configuration, and material context.
    Used for both job logging and telemetry correlation.
    """
    op_type: OpType = Field(
        ...,
        description="Operation type: slice, batch, or contour"
    )
    
    # Machine & Material
    machine_profile: Optional[str] = Field(
        None,
        description="Machine identifier (e.g., 'AXIOM_AR8')"
    )
    material_family: Optional[str] = Field(
        None,
        description="Material being cut (e.g., 'maple', 'ebony', 'aluminum')"
    )
    
    # Tooling
    blade_id: Optional[str] = Field(
        None,
        description="Saw blade identifier from registry (e.g., 'TENRYU_GM-305100AB')"
    )
    
    # Program Metadata
    program_id: str = Field(
        default="SAW_JOB",
        description="G-code program identifier"
    )
    program_comment: Optional[str] = Field(
        None,
        description="Human-readable job description"
    )
    
    # Cutting Parameters
    rpm: Optional[int] = Field(
        None,
        description="Spindle speed (revolutions per minute)",
        ge=0
    )
    feed_ipm: Optional[float] = Field(
        None,
        description="Cutting feed rate (inches per minute)",
        gt=0
    )
    plunge_ipm: Optional[float] = Field(
        None,
        description="Plunge feed rate (inches per minute)",
        gt=0
    )
    safe_z_mm: float = Field(
        default=5.0,
        description="Safe clearance height above stock (mm)",
        ge=0
    )
    
    # Depth Strategy
    depth_passes: int = Field(
        ...,
        description="Number of Z-level passes",
        ge=1
    )
    doc_per_pass_mm: Optional[float] = Field(
        None,
        description="Depth of cut per pass (mm)",
        gt=0
    )
    total_depth_mm: Optional[float] = Field(
        None,
        description="Total cutting depth (mm)",
        gt=0
    )
    
    # Path Statistics
    total_length_mm: float = Field(
        ...,
        description="Total cutting path length across all passes (mm)",
        ge=0
    )
    
    # Risk Assessment
    risk_grade: Optional[RiskGrade] = Field(
        None,
        description="Pre-execution risk assessment: GREEN, YELLOW, or RED"
    )
    risk_warnings: List[str] = Field(
        default_factory=list,
        description="List of risk warning messages"
    )
    
    # Additional Context
    notes: Optional[str] = Field(
        None,
        description="Operator notes or special instructions"
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (extensible)"
    )


# ============================================================================
# JOB LOG RECORD
# ============================================================================

class SawRunRecord(BaseModel):
    """
    Complete job log entry for a saw operation execution.
    
    Includes metadata, generated G-code, and execution timestamps.
    Serves as the primary audit trail for CNC saw operations.
    """
    run_id: str = Field(
        ...,
        description="Unique run identifier (timestamp_random format)"
    )
    
    meta: SawRunMeta = Field(
        ...,
        description="Operation metadata and parameters"
    )
    
    gcode: str = Field(
        ...,
        description="Complete G-code program text"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Job creation timestamp (UTC)"
    )
    
    started_at: Optional[datetime] = Field(
        None,
        description="Execution start timestamp (UTC)"
    )
    
    completed_at: Optional[datetime] = Field(
        None,
        description="Execution completion timestamp (UTC)"
    )
    
    status: Literal["created", "running", "completed", "failed"] = Field(
        default="created",
        description="Execution status"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error details if status=failed"
    )


# ============================================================================
# TELEMETRY
# ============================================================================

class TelemetrySample(BaseModel):
    """
    Real-time execution telemetry sample.
    
    Captures machine state at a specific moment during job execution.
    Used for feeds/speeds learning, performance analysis, and anomaly detection.
    """
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Sample capture time (UTC)"
    )
    
    # Position
    x_mm: Optional[float] = Field(None, description="X axis position (mm)")
    y_mm: Optional[float] = Field(None, description="Y axis position (mm)")
    z_mm: Optional[float] = Field(None, description="Z axis position (mm)")
    
    # Motion State
    feed_actual_mm_min: Optional[float] = Field(
        None,
        description="Actual feed rate (mm/min)"
    )
    rpm_actual: Optional[int] = Field(
        None,
        description="Actual spindle speed (RPM)"
    )
    
    # Machine Health
    spindle_load_percent: Optional[float] = Field(
        None,
        description="Spindle load percentage (0-100)",
        ge=0,
        le=100
    )
    motor_current_amps: Optional[float] = Field(
        None,
        description="Motor current draw (amps)",
        ge=0
    )
    
    # Environment
    temp_c: Optional[float] = Field(
        None,
        description="Spindle/ambient temperature (°C)"
    )
    vibration_mg: Optional[float] = Field(
        None,
        description="Vibration magnitude (milli-g)"
    )
    
    # Status Flags
    in_cut: bool = Field(
        default=False,
        description="Whether tool is currently cutting (vs rapids/retracts)"
    )
    alarm: bool = Field(
        default=False,
        description="Whether machine is in alarm state"
    )
    
    # Extensible
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional sensor data"
    )


class SawTelemetryRecord(BaseModel):
    """
    Collection of telemetry samples for a job run.
    
    Aggregates all real-time samples captured during execution.
    Enables post-run analysis, learning, and optimization.
    """
    run_id: str = Field(
        ...,
        description="Associated job run identifier"
    )
    
    samples: List[TelemetrySample] = Field(
        default_factory=list,
        description="Time-ordered telemetry samples"
    )
    
    # Summary Statistics (computed)
    avg_feed_mm_min: Optional[float] = Field(
        None,
        description="Average actual feed rate during cutting"
    )
    avg_spindle_load_percent: Optional[float] = Field(
        None,
        description="Average spindle load percentage"
    )
    max_spindle_load_percent: Optional[float] = Field(
        None,
        description="Peak spindle load percentage"
    )
    
    total_cut_time_s: Optional[float] = Field(
        None,
        description="Total time in active cutting (excluding rapids)"
    )
    
    anomalies: List[str] = Field(
        default_factory=list,
        description="Detected anomalies (high load, temp spikes, etc.)"
    )
