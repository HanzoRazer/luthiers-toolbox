"""
Job Models
==========

Data models for async blueprint job processing.

Author: Production Shop
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    """Status of an async blueprint job."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class BlueprintJob:
    """
    Represents an async blueprint vectorization job.

    Tracks status, progress, and final result for polling.
    """
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    filename: str
    progress: int = 0
    stage: str = "queued"
    result: Optional[dict[str, Any]] = None
    error: str = ""
    debug: dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None  # Set when job moves to PROCESSING

    def to_dict(self) -> dict[str, Any]:
        """Serialize job to dictionary for storage."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
            "filename": self.filename,
            "progress": self.progress,
            "stage": self.stage,
            "result": self.result,
            "error": self.error,
            "debug": self.debug,
            "started_at": self.started_at.isoformat() + "Z" if self.started_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlueprintJob":
        """Deserialize job from dictionary."""
        def parse_dt(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            # Handle ISO format with or without Z suffix
            return datetime.fromisoformat(value.replace("Z", "+00:00").replace("+00:00", ""))

        return cls(
            job_id=data["job_id"],
            status=JobStatus(data["status"]),
            created_at=parse_dt(data["created_at"]),
            updated_at=parse_dt(data["updated_at"]),
            filename=data["filename"],
            progress=int(data.get("progress", 0)),
            stage=data.get("stage", "queued"),
            result=data.get("result"),
            error=data.get("error", ""),
            debug=data.get("debug") or {},
            started_at=parse_dt(data.get("started_at")),
        )
