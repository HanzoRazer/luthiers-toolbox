from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


ManifestVersion = Literal["TapToneBundleManifestV1"]


class ManifestFileV1(BaseModel):
    """
    One file entry in the exported tap_tone_pi bundle manifest.

    relpath: path relative to the bundle root (POSIX-style recommended)
    sha256: sha256 hex digest of file content
    bytes: size in bytes
    mime: best-effort MIME type
    kind: stable semantic category (audio_raw, analysis_summary, plot, grid, point_audio_raw, ...)
    point_id: optional point namespace (for roving-grid ODS / multi-point runs)
    """
    model_config = ConfigDict(extra="forbid")

    relpath: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64, description="sha256 hex digest")
    bytes: int = Field(ge=0)
    mime: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    point_id: Optional[str] = None


class InstrumentBlockV1(BaseModel):
    """Structured optional instrument context. Keep stable; add fields cautiously."""
    model_config = ConfigDict(extra="allow")

    instrument_id: Optional[str] = None
    build_stage: Optional[str] = None
    operator: Optional[str] = None

    # Future-friendly:
    model: Optional[str] = None
    serial: Optional[str] = None
    top_wood: Optional[str] = None
    back_wood: Optional[str] = None


class ProvenanceBlockV1(BaseModel):
    """Where/with what this was captured."""
    model_config = ConfigDict(extra="allow")

    device_id: Optional[str] = None
    mic_model: Optional[str] = None
    adc_model: Optional[str] = None
    calibration: Optional[dict[str, Any]] = None
    ambient: Optional[dict[str, Any]] = None


class DomainAcousticsBlockV1(BaseModel):
    """Acoustics namespace for evolvable fields without breaking generic tooling."""
    model_config = ConfigDict(extra="allow")

    phase: Optional[int] = Field(default=None, description="1|2|3 (Phase inference allowed)")
    coh_min: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    measurement: Optional[dict[str, Any]] = None
    grid: Optional[dict[str, Any]] = None
    result_summary: Optional[dict[str, Any]] = None
    analysis_version: Optional[str] = None
    algorithm_id: Optional[str] = None


class DomainBlockV1(BaseModel):
    model_config = ConfigDict(extra="allow")

    acoustics: Optional[DomainAcousticsBlockV1] = None


class TapToneBundleManifestV1(BaseModel):
    """
    Canonical import contract produced by tap_tone_pi exporter.

    RMOS should ingest from THIS contract, not folder semantics.
    """
    model_config = ConfigDict(extra="forbid")

    manifest_version: ManifestVersion
    bundle_id: str = Field(min_length=1)
    bundle_sha256: str = Field(min_length=64, max_length=64, description="sha256 of normalized manifest JSON")

    bundle_root_name: Optional[str] = None
    capture_started_at_utc: datetime
    capture_finished_at_utc: datetime

    tool_id: str = Field(min_length=1)
    app_version: Optional[str] = None

    mode: Literal["acoustics"] = "acoustics"
    event_type: str = Field(min_length=1, description='e.g. "tap_tone.capture"')

    units: Literal["mm"] = "mm"

    instrument: Optional[InstrumentBlockV1] = None
    provenance: Optional[ProvenanceBlockV1] = None
    domain: Optional[DomainBlockV1] = None

    files: list[ManifestFileV1] = Field(min_length=1)

    generated_at_utc: Optional[datetime] = None
