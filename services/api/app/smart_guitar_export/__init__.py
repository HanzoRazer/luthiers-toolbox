"""
ToolBox -> Smart Guitar Safe Export v1

Teaching/learning content export that is explicitly "Smart Guitar-safe":
- Read-only / non-authoritative (no decisions, no governance state)
- Non-manufacturing (no G-code, no toolpaths, no CNC settings)
- Content-addressed (hashes for integrity)
- Composable (can add scanned-book content later)

Contract: TOOLBOX_SMART_GUITAR_EXPORT_v1
"""

from .schemas import (
    SmartGuitarExportManifest,
    ExportProducer,
    ExportScope,
    ContentPolicy,
    ExportFileEntry,
    TopicEntry,
    LessonEntry,
    DrillEntry,
    TopicsIndex,
    LessonsIndex,
    DrillsIndex,
)
from .validator import (
    validate_manifest,
    validate_bundle,
    ValidationResult,
    FORBIDDEN_EXTENSIONS,
    FORBIDDEN_KINDS,
)
from .exporter import (
    create_export_bundle,
    ExportBuilder,
)

__all__ = [
    # Schemas
    "SmartGuitarExportManifest",
    "ExportProducer",
    "ExportScope",
    "ContentPolicy",
    "ExportFileEntry",
    "TopicEntry",
    "LessonEntry",
    "DrillEntry",
    "TopicsIndex",
    "LessonsIndex",
    "DrillsIndex",
    # Validator
    "validate_manifest",
    "validate_bundle",
    "ValidationResult",
    "FORBIDDEN_EXTENSIONS",
    "FORBIDDEN_KINDS",
    # Exporter
    "create_export_bundle",
    "ExportBuilder",
]
