"""
Saw Lab Compatibility Schemas - Accepts canonical and legacy payload shapes.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class _CompatBase(BaseModel):
    model_config = ConfigDict(extra="allow")

class SawRunMetaCompat(_CompatBase):
    op_type: Optional[str] = None
    machine_profile: Optional[str] = None
    material_family: Optional[str] = None
    blade_id: Optional[str] = None
    depth_passes: Optional[int] = None
    total_length_mm: Optional[float] = None
    program_id: Optional[str] = None
    safe_z_mm: Optional[float] = None
    risk_grade: Optional[str] = None
    risk_warnings: List[str] = Field(default_factory=list)

class SawRunStatsCompat(_CompatBase):
    duration_s: Optional[float] = None
    avg_current_a: Optional[float] = None
    peak_current_a: Optional[float] = None

class SawRunCompat(_CompatBase):
    run_id: Optional[str] = None
    run_uuid: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[str] = None
    meta: Optional[SawRunMetaCompat] = None
    stats: Optional[SawRunStatsCompat] = None
    gcode: Optional[str] = None
    duration_s: Optional[float] = None
    risk_grade: Optional[str] = None

    def normalized_id(self) -> str:
        return self.run_id or self.run_uuid or "UNKNOWN_RUN"

    def normalized_duration_s(self) -> Optional[float]:
        if self.stats and self.stats.duration_s is not None:
            return self.stats.duration_s
        return self.duration_s

class SawRunsFileCompat(_CompatBase):
    runs: List[SawRunCompat] = Field(default_factory=list)

    @classmethod
    def parse_payload(cls, payload: Any) -> "SawRunsFileCompat":
        if isinstance(payload, list):
            # List of run objects
            return cls(runs=[SawRunCompat.model_validate(x) for x in payload])
        if isinstance(payload, dict):
            if "runs" in payload:
                runs_data = payload["runs"]
                # Legacy format: runs is a dict keyed by run_id
                if isinstance(runs_data, dict):
                    return cls(runs=[SawRunCompat.model_validate(v) for v in runs_data.values()])
                # Canonical format: runs is a list
                if isinstance(runs_data, list):
                    return cls(runs=[SawRunCompat.model_validate(x) for x in runs_data])
            # Single run object
            return cls(runs=[SawRunCompat.model_validate(payload)])
        raise ValueError("Unsupported payload shape")

class TelemetrySampleCompat(_CompatBase):
    timestamp: Optional[datetime] = None
    x_mm: Optional[float] = None
    y_mm: Optional[float] = None
    z_mm: Optional[float] = None
    rpm_actual: Optional[float] = None
    spindle_load_percent: Optional[float] = None
    feed_actual_mm_min: Optional[float] = None
    vibration_mg: Optional[float] = None
    motor_current_amps: Optional[float] = None
    temp_c: Optional[float] = None
    in_cut: Optional[bool] = None
    alarm: Optional[Union[str, int]] = None

    def normalized_rpm(self) -> Optional[float]:
        return self.rpm_actual

class SawTelemetryRunCompat(_CompatBase):
    run_id: Optional[str] = None
    samples: List[TelemetrySampleCompat] = Field(default_factory=list)

    @property
    def sample_count(self) -> int:
        return len(self.samples)

class SawTelemetryFileCompat(_CompatBase):
    runs: List[SawTelemetryRunCompat] = Field(default_factory=list)

    @classmethod
    def parse_payload(cls, payload: Any) -> "SawTelemetryFileCompat":
        if isinstance(payload, list):
            # Flat list of samples (single run)
            return cls(runs=[SawTelemetryRunCompat(samples=[TelemetrySampleCompat.model_validate(x) for x in payload])])
        if isinstance(payload, dict):
            # Legacy format: telemetry is a dict keyed by run_id
            if "telemetry" in payload:
                tel_data = payload["telemetry"]
                if isinstance(tel_data, dict):
                    return cls(runs=[SawTelemetryRunCompat.model_validate(v) for v in tel_data.values()])
            # Canonical format: runs is a list
            if "runs" in payload:
                runs_data = payload["runs"]
                if isinstance(runs_data, dict):
                    return cls(runs=[SawTelemetryRunCompat.model_validate(v) for v in runs_data.values()])
                if isinstance(runs_data, list):
                    return cls(runs=[SawTelemetryRunCompat.model_validate(r) for r in runs_data])
            # Single run with samples
            if "samples" in payload:
                return cls(runs=[SawTelemetryRunCompat.model_validate(payload)])
        raise ValueError("Unsupported payload shape")

    @property
    def total_samples(self) -> int:
        return sum(r.sample_count for r in self.runs)
