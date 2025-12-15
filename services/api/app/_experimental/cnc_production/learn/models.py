"""
CP-S60 — Live Learn Models

Data models for telemetry ingestion and lane-scale learning.
Supports automatic feed/speed optimization based on real-world performance data.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class TelemetryIngestConfig(BaseModel):
    """Configuration for telemetry-based learning."""
    
    low_load_threshold_pct: float = Field(
        default=40.0,
        description="Below this spindle load %, consider speeding up"
    )
    high_load_threshold_pct: float = Field(
        default=80.0,
        description="Above this spindle load %, consider slowing down"
    )
    vibration_warn_threshold: float = Field(
        default=1.5,
        description="Vibration RMS threshold for warnings (mm/s)"
    )
    min_samples: int = Field(
        default=5,
        description="Minimum telemetry samples required for learning"
    )
    up_scale_step: float = Field(
        default=0.05,
        description="Scale increase step when load is low (5%)"
    )
    down_scale_step: float = Field(
        default=0.05,
        description="Scale decrease step when load is high (5%)"
    )
    max_scale: float = Field(
        default=1.5,
        description="Maximum lane scale multiplier (150%)"
    )
    min_scale: float = Field(
        default=0.5,
        description="Minimum lane scale multiplier (50%)"
    )


class LaneMetrics(BaseModel):
    """Aggregated metrics from telemetry samples."""
    
    n_samples: int = 0
    avg_rpm: Optional[float] = None
    avg_feed_mm_min: Optional[float] = None
    avg_spindle_load_pct: Optional[float] = None
    max_spindle_load_pct: Optional[float] = None
    avg_motor_current_amps: Optional[float] = None
    max_motor_current_amps: Optional[float] = None
    avg_temp_c: Optional[float] = None
    max_temp_c: Optional[float] = None
    avg_vibration_rms: Optional[float] = None
    max_vibration_rms: Optional[float] = None
    total_cut_time_s: Optional[float] = None


class LaneAdjustment(BaseModel):
    """Recommended lane-scale adjustment based on telemetry."""
    
    tool_id: str = Field(..., description="Tool/blade identifier")
    material: str = Field(..., description="Material family")
    mode: str = Field(default="roughing", description="Operation mode")
    machine_profile: str = Field(..., description="Machine profile identifier")
    
    metrics: LaneMetrics = Field(..., description="Computed telemetry metrics")
    risk_score: float = Field(..., description="Risk score 0-1 (0=safe, 1=dangerous)")
    
    recommended_scale_delta: float = Field(
        ...,
        description="Suggested change to lane scale (-0.05 = slow down 5%, +0.05 = speed up 5%)"
    )
    new_lane_scale: Optional[float] = Field(
        None,
        description="New lane scale if adjustment applied"
    )
    
    applied: bool = Field(
        default=False,
        description="Whether adjustment was applied to learned overrides"
    )
    reason: str = Field(
        default="",
        description="Human-readable explanation of adjustment decision"
    )


class TelemetryIngestRequest(BaseModel):
    """Request to ingest telemetry and compute adjustments."""
    
    run_id: str = Field(..., description="Job run identifier from JobLog")
    tool_id: str = Field(..., description="Tool/blade identifier")
    material: str = Field(..., description="Material family")
    mode: str = Field(default="roughing", description="Operation mode")
    machine_profile: str = Field(..., description="Machine profile identifier")
    
    current_lane_scale: float = Field(
        default=1.0,
        description="Current lane scale multiplier for this tool/material/machine"
    )
    
    config: TelemetryIngestConfig = Field(
        default_factory=TelemetryIngestConfig,
        description="Ingest configuration parameters"
    )
    
    apply: bool = Field(
        default=False,
        description="Whether to apply adjustment to learned overrides immediately"
    )


class TelemetryIngestResponse(BaseModel):
    """Response from telemetry ingestion."""
    
    run_id: str
    metrics: LaneMetrics
    adjustment: LaneAdjustment
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "20251127T120000Z_a1b2c3d4",
                "metrics": {
                    "n_samples": 47,
                    "avg_spindle_load_pct": 85.3,
                    "max_spindle_load_pct": 92.1,
                    "avg_vibration_rms": 1.2
                },
                "adjustment": {
                    "tool_id": "TENRYU_GM-305100AB",
                    "material": "hardwood",
                    "mode": "roughing",
                    "machine_profile": "bcam_router_2030",
                    "risk_score": 0.72,
                    "recommended_scale_delta": -0.05,
                    "new_lane_scale": 0.95,
                    "applied": False,
                    "reason": "Average load 85.3% above high threshold 80.0%, suggesting we should slow down slightly."
                }
            }
        }
