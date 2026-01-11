"""
Exporter for ToolBox -> Smart Guitar Safe Export v1

Creates export bundles from teaching/learning content.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .schemas import (
    SmartGuitarExportManifest,
    ExportProducer,
    ExportScope,
    ContentPolicy,
    ExportIndex,
    ExportFileEntry,
    ExportDomain,
    FileKind,
    TopicsIndex,
    LessonsIndex,
    DrillsIndex,
    TopicEntry,
    LessonEntry,
    DrillEntry,
)
from .validator import validate_bundle, FORBIDDEN_EXTENSIONS


# =============================================================================
# Helpers
# =============================================================================


def _sha256_of_bytes(data: bytes) -> str:
    """Compute SHA256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def _sha256_of_file(path: Path) -> str:
    """Compute SHA256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_git_commit() -> str:
    """Get current git commit SHA, or 'unknown' if not in git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _get_git_repo() -> str:
    """Get git remote URL, or 'local' if not available."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "local"


def _guess_mime(path: Path) -> str:
    """Guess MIME type from file extension."""
    ext = path.suffix.lower()
    mime_map = {
        ".json": "application/json",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".mp3": "audio/mpeg",
        ".pdf": "application/pdf",
    }
    return mime_map.get(ext, "application/octet-stream")


def _guess_kind(path: Path, mime: str) -> FileKind:
    """Guess file kind from path and MIME type."""
    name = path.name.lower()
    ext = path.suffix.lower()

    # Index files
    if name == "topics.json":
        return FileKind.TOPIC_INDEX
    if name == "lessons.json":
        return FileKind.LESSON_INDEX
    if name == "drills.json":
        return FileKind.DRILL_INDEX
    if name == "manifest.json":
        return FileKind.MANIFEST

    # By extension
    if ext == ".md":
        if "lesson" in str(path).lower():
            return FileKind.LESSON_MD
        return FileKind.REFERENCE_MD
    if ext == ".json":
        if "lesson" in str(path).lower():
            return FileKind.LESSON_JSON
        return FileKind.REFERENCE_JSON
    if ext == ".wav":
        return FileKind.AUDIO_WAV
    if ext == ".flac":
        return FileKind.AUDIO_FLAC
    if ext in (".png", ".gif", ".svg"):
        return FileKind.IMAGE_PNG
    if ext in (".jpg", ".jpeg"):
        return FileKind.IMAGE_JPG
    if ext == ".csv":
        return FileKind.CHART_CSV

    # Provenance
    if "provenance" in str(path).lower() or "sources" in str(path).lower():
        return FileKind.PROVENANCE

    return FileKind.UNKNOWN


# =============================================================================
# Export Builder
# =============================================================================


class ExportBuilder:
    """
    Builder for creating Smart Guitar safe export bundles.

    Usage:
        builder = ExportBuilder(domain="education")
        builder.add_topic("setup_action", "Action setup", tags=["setup"])
        builder.add_lesson("lesson_001", "Clean fretting", "beginner", "# Clean Fretting...")
        builder.add_file("diagrams/neck.png", content_bytes)
        bundle_path = builder.build("/path/to/output")
    """

    def __init__(
        self,
        domain: Union[str, ExportDomain] = ExportDomain.EDUCATION,
        export_id: Optional[str] = None,
        build_id: Optional[str] = None,
    ):
        self.domain = ExportDomain(domain) if isinstance(domain, str) else domain
        self.export_id = export_id or f"export_{uuid.uuid4().hex[:12]}"
        self.build_id = build_id

        self.topics: List[TopicEntry] = []
        self.lessons: List[LessonEntry] = []
        self.drills: List[DrillEntry] = []

        # Pending files: relpath -> (content_bytes, mime, kind)
        self._pending_files: Dict[str, tuple] = {}

    def add_topic(self, topic_id: str, title: str, tags: Optional[List[str]] = None) -> "ExportBuilder":
        """Add a topic to the index."""
        self.topics.append(TopicEntry(id=topic_id, title=title, tags=tags or []))
        return self

    def add_lesson(
        self,
        lesson_id: str,
        title: str,
        level: str,
        content_md: str,
        topic_ids: Optional[List[str]] = None,
    ) -> "ExportBuilder":
        """Add a lesson with markdown content."""
        sha = _sha256_of_bytes(content_md.encode("utf-8"))
        relpath = f"assets/{sha}.md"

        self.lessons.append(LessonEntry(
            id=lesson_id,
            title=title,
            level=level,
            relpath=relpath,
            topic_ids=topic_ids or [],
        ))

        self._pending_files[relpath] = (
            content_md.encode("utf-8"),
            "text/markdown",
            FileKind.LESSON_MD,
        )
        return self

    def add_drill(
        self,
        drill_id: str,
        title: str,
        tempo_min: int = 60,
        tempo_max: int = 120,
        tempo_step: int = 5,
        metrics: Optional[List[str]] = None,
    ) -> "ExportBuilder":
        """Add a practice drill."""
        from .schemas import TempoRange
        self.drills.append(DrillEntry(
            id=drill_id,
            title=title,
            tempo_bpm=TempoRange(min=tempo_min, max=tempo_max, step=tempo_step),
            metrics=metrics or [],
        ))
        return self

    def add_file(
        self,
        relpath: str,
        content: bytes,
        mime: Optional[str] = None,
        kind: Optional[FileKind] = None,
    ) -> "ExportBuilder":
        """Add a raw file to the bundle."""
        # Check for forbidden extensions
        ext = Path(relpath).suffix.lower()
        if ext in FORBIDDEN_EXTENSIONS:
            raise ValueError(f"Forbidden extension '{ext}' in file: {relpath}")

        path = Path(relpath)
        if mime is None:
            mime = _guess_mime(path)
        if kind is None:
            kind = _guess_kind(path, mime)

        # Content-address the file
        sha = _sha256_of_bytes(content)
        final_relpath = f"assets/{sha}{path.suffix}"

        self._pending_files[final_relpath] = (content, mime, kind)
        return self

    def add_file_from_path(self, src_path: Union[str, Path], relpath: Optional[str] = None) -> "ExportBuilder":
        """Add a file from disk."""
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        with open(src, "rb") as f:
            content = f.read()

        if relpath is None:
            relpath = src.name

        return self.add_file(relpath, content)

    def build(self, output_dir: Union[str, Path]) -> Path:
        """
        Build the export bundle to the output directory.

        Returns the path to the bundle directory.
        """
        output_dir = Path(output_dir)
        bundle_dir = output_dir / f"smart_guitar_export_v1_{self.export_id}"

        # Clean if exists
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)

        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "assets").mkdir(exist_ok=True)
        (bundle_dir / "index").mkdir(exist_ok=True)
        (bundle_dir / "provenance").mkdir(exist_ok=True)

        file_entries: List[ExportFileEntry] = []

        # 1) Write index files
        topics_data = TopicsIndex(topics=self.topics).model_dump()
        topics_bytes = json.dumps(topics_data, indent=2).encode("utf-8")
        topics_path = bundle_dir / "index" / "topics.json"
        topics_path.write_bytes(topics_bytes)
        file_entries.append(ExportFileEntry(
            relpath="index/topics.json",
            sha256=_sha256_of_bytes(topics_bytes),
            bytes=len(topics_bytes),
            mime="application/json",
            kind=FileKind.TOPIC_INDEX,
        ))

        lessons_data = LessonsIndex(lessons=self.lessons).model_dump()
        lessons_bytes = json.dumps(lessons_data, indent=2).encode("utf-8")
        lessons_path = bundle_dir / "index" / "lessons.json"
        lessons_path.write_bytes(lessons_bytes)
        file_entries.append(ExportFileEntry(
            relpath="index/lessons.json",
            sha256=_sha256_of_bytes(lessons_bytes),
            bytes=len(lessons_bytes),
            mime="application/json",
            kind=FileKind.LESSON_INDEX,
        ))

        drills_data = DrillsIndex(drills=self.drills).model_dump()
        drills_bytes = json.dumps(drills_data, indent=2).encode("utf-8")
        drills_path = bundle_dir / "index" / "drills.json"
        drills_path.write_bytes(drills_bytes)
        file_entries.append(ExportFileEntry(
            relpath="index/drills.json",
            sha256=_sha256_of_bytes(drills_bytes),
            bytes=len(drills_bytes),
            mime="application/json",
            kind=FileKind.DRILL_INDEX,
        ))

        # 2) Write pending files
        for relpath, (content, mime, kind) in self._pending_files.items():
            file_path = bundle_dir / relpath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            file_entries.append(ExportFileEntry(
                relpath=relpath,
                sha256=_sha256_of_bytes(content),
                bytes=len(content),
                mime=mime,
                kind=kind,
            ))

        # 3) Write provenance
        provenance = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "export_id": self.export_id,
            "git_commit": _get_git_commit(),
            "git_repo": _get_git_repo(),
        }
        prov_bytes = json.dumps(provenance, indent=2).encode("utf-8")
        prov_path = bundle_dir / "provenance" / "build.json"
        prov_path.write_bytes(prov_bytes)
        file_entries.append(ExportFileEntry(
            relpath="provenance/build.json",
            sha256=_sha256_of_bytes(prov_bytes),
            bytes=len(prov_bytes),
            mime="application/json",
            kind=FileKind.PROVENANCE,
        ))

        # 4) Build manifest (without bundle_sha256 first)
        manifest_pre = SmartGuitarExportManifest(
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            export_id=self.export_id,
            producer=ExportProducer(
                repo=_get_git_repo(),
                commit=_get_git_commit(),
                build_id=self.build_id,
            ),
            scope=ExportScope(domain=self.domain),
            content_policy=ContentPolicy(),
            index=ExportIndex(),
            files=file_entries,
            bundle_sha256="",  # Placeholder
        )

        # Compute bundle_sha256 from manifest WITHOUT the bundle_sha256 field
        manifest_dict = manifest_pre.model_dump()
        manifest_dict["bundle_sha256"] = ""
        manifest_pre_bytes = json.dumps(manifest_dict, indent=2, sort_keys=True).encode("utf-8")
        bundle_sha256 = _sha256_of_bytes(manifest_pre_bytes)

        # Update manifest with real sha256
        manifest_dict["bundle_sha256"] = bundle_sha256
        manifest_bytes = json.dumps(manifest_dict, indent=2).encode("utf-8")

        # Write manifest
        manifest_path = bundle_dir / "manifest.json"
        manifest_path.write_bytes(manifest_bytes)

        return bundle_dir


def create_export_bundle(
    output_dir: Union[str, Path],
    domain: Union[str, ExportDomain] = ExportDomain.EDUCATION,
    topics: Optional[List[Dict[str, Any]]] = None,
    lessons: Optional[List[Dict[str, Any]]] = None,
    drills: Optional[List[Dict[str, Any]]] = None,
    files: Optional[List[Dict[str, Any]]] = None,
    export_id: Optional[str] = None,
    validate: bool = True,
) -> Path:
    """
    Create an export bundle from structured data.

    Args:
        output_dir: Where to write the bundle
        domain: Content domain (education, practice, coaching, reference)
        topics: List of topic dicts with id, title, tags
        lessons: List of lesson dicts with id, title, level, content_md
        drills: List of drill dicts with id, title, tempo_bpm, metrics
        files: List of file dicts with relpath, content (bytes or path)
        export_id: Optional stable export ID
        validate: Whether to validate the bundle after creation

    Returns:
        Path to the created bundle directory
    """
    builder = ExportBuilder(domain=domain, export_id=export_id)

    # Add topics
    for t in (topics or []):
        builder.add_topic(t["id"], t["title"], t.get("tags", []))

    # Add lessons
    for l in (lessons or []):
        builder.add_lesson(
            l["id"],
            l["title"],
            l.get("level", "beginner"),
            l["content_md"],
            l.get("topic_ids", []),
        )

    # Add drills
    for d in (drills or []):
        tempo = d.get("tempo_bpm", {})
        builder.add_drill(
            d["id"],
            d["title"],
            tempo.get("min", 60),
            tempo.get("max", 120),
            tempo.get("step", 5),
            d.get("metrics", []),
        )

    # Add files
    for f in (files or []):
        if "content" in f:
            content = f["content"]
            if isinstance(content, str):
                content = content.encode("utf-8")
            builder.add_file(f["relpath"], content, f.get("mime"), f.get("kind"))
        elif "path" in f:
            builder.add_file_from_path(f["path"], f.get("relpath"))

    bundle_path = builder.build(output_dir)

    if validate:
        result = validate_bundle(bundle_path)
        if not result.valid:
            raise ValueError(f"Bundle validation failed: {result.errors}")

    return bundle_path
