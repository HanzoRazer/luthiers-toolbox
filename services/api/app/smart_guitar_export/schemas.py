"""
Pydantic schemas for ToolBox -> Smart Guitar Safe Export v1

These models mirror the JSON Schema contract:
  contracts/toolbox_smart_guitar_safe_export_v1.schema.json
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ExportDomain(str, Enum):
    """Allowed export domains."""
    EDUCATION = "education"
    PRACTICE = "practice"
    COACHING = "coaching"
    REFERENCE = "reference"


class IntendedConsumer(str, Enum):
    """Allowed consumers of the export."""
    SMART_GUITAR_APP = "smart_guitar_app"
    SMART_GUITAR_COACH = "smart_guitar_coach"
    SMART_GUITAR_FIRMWARE_TOOLS = "smart_guitar_firmware_tools"


class FileKind(str, Enum):
    """Allowed file kinds in export."""
    MANIFEST = "manifest"
    TOPIC_INDEX = "topic_index"
    LESSON_INDEX = "lesson_index"
    DRILL_INDEX = "drill_index"
    LESSON_MD = "lesson_md"
    LESSON_JSON = "lesson_json"
    REFERENCE_MD = "reference_md"
    REFERENCE_JSON = "reference_json"
    AUDIO_WAV = "audio_wav"
    AUDIO_FLAC = "audio_flac"
    IMAGE_PNG = "image_png"
    IMAGE_JPG = "image_jpg"
    CHART_CSV = "chart_csv"
    PROVENANCE = "provenance"
    UNKNOWN = "unknown"


# =============================================================================
# Core Models
# =============================================================================


class ExportProducer(BaseModel):
    """Producer metadata - identifies source system."""
    system: Literal["luthiers-toolbox"] = "luthiers-toolbox"
    repo: str = Field(..., description="Repository URL or name")
    commit: str = Field(..., description="Git commit SHA")
    build_id: Optional[str] = Field(None, description="CI build ID if applicable")


class ExportScope(BaseModel):
    """Scope of the export - what domain and who can consume it."""
    domain: ExportDomain = Field(..., description="Content domain")
    safe_for: Literal["smart_guitar"] = "smart_guitar"
    intended_consumers: List[IntendedConsumer] = Field(
        default_factory=list,
        description="Which Smart Guitar systems can consume this export",
    )


class ContentPolicy(BaseModel):
    """
    Hard assertions that this export is Smart Guitar-safe.
    All flags must be true for the export to be valid.
    """
    no_manufacturing: Literal[True] = True
    no_toolpaths: Literal[True] = True
    no_rmos_authority: Literal[True] = True
    no_secrets: Literal[True] = True
    notes: Optional[str] = Field(None, description="Optional policy notes")


class ExportIndex(BaseModel):
    """Paths to index files within the bundle."""
    topics_relpath: str = "index/topics.json"
    lessons_relpath: str = "index/lessons.json"
    drills_relpath: str = "index/drills.json"


class ExportFileEntry(BaseModel):
    """A file entry in the manifest."""
    relpath: str = Field(..., description="Relative path within bundle")
    sha256: str = Field(..., description="SHA256 hash of file contents")
    bytes: int = Field(..., ge=0, description="File size in bytes")
    mime: str = Field(..., description="MIME type")
    kind: FileKind = Field(..., description="File kind classification")


class SmartGuitarExportManifest(BaseModel):
    """
    Root manifest for a ToolBox -> Smart Guitar export bundle.

    This is the source of truth for the bundle contents.
    """
    schema_id: Literal["toolbox_smart_guitar_safe_export"] = "toolbox_smart_guitar_safe_export"
    schema_version: Literal["v1"] = "v1"

    created_at_utc: str = Field(..., description="ISO8601 timestamp")
    export_id: str = Field(..., description="Stable export identifier")

    producer: ExportProducer
    scope: ExportScope
    content_policy: ContentPolicy
    index: ExportIndex = Field(default_factory=ExportIndex)
    files: List[ExportFileEntry] = Field(default_factory=list)

    bundle_sha256: str = Field(
        ...,
        description="SHA256 of manifest JSON bytes BEFORE adding this field",
    )


# =============================================================================
# Index File Models
# =============================================================================


class TopicEntry(BaseModel):
    """A topic in the topics index."""
    id: str
    title: str
    tags: List[str] = Field(default_factory=list)


class TopicsIndex(BaseModel):
    """Topics index file."""
    topics: List[TopicEntry] = Field(default_factory=list)


class LessonEntry(BaseModel):
    """A lesson in the lessons index."""
    id: str
    title: str
    level: str = Field(default="beginner", description="Skill level")
    relpath: str = Field(..., description="Path to lesson content")
    topic_ids: List[str] = Field(default_factory=list)


class LessonsIndex(BaseModel):
    """Lessons index file."""
    lessons: List[LessonEntry] = Field(default_factory=list)


class TempoRange(BaseModel):
    """Tempo range for a drill."""
    min: int = Field(60, ge=20)
    max: int = Field(120, le=300)
    step: int = Field(5, ge=1)


class DrillEntry(BaseModel):
    """A drill in the drills index."""
    id: str
    title: str
    tempo_bpm: Optional[TempoRange] = None
    metrics: List[str] = Field(default_factory=list)
    relpath: Optional[str] = Field(None, description="Path to drill content if any")


class DrillsIndex(BaseModel):
    """Drills index file."""
    drills: List[DrillEntry] = Field(default_factory=list)
