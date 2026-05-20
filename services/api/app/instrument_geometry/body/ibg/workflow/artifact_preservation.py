"""
Artifact Preservation — Canonical Artifact Storage
===================================================

Preserves original DXF/SVG artifacts exactly as produced, with metadata
and integrity hashes for provenance tracking.

DEV ORDER 1A-WORKFLOW: IBG Workflow Pipeline

Author: Production Shop
Date: 2026-05-18
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Gitignored staging directory
WORKFLOW_1A_ARTIFACTS_DIR = Path("morphology_harvest/outputs/workflow_1a/artifacts")


@dataclass
class PreservedArtifact:
    """
    Record of a preserved artifact.

    Attributes:
        artifact_id: Unique identifier
        source_filename: Original filename
        source_mode: "pdf" or "photo"
        artifact_type: "dxf" or "svg"
        artifact_path: Path to preserved file
        artifact_hash: SHA-256 hash of content
        byte_size: Size in bytes
        created_at: Preservation timestamp
        metadata: Additional metadata
    """
    artifact_id: str
    source_filename: str
    source_mode: str
    artifact_type: str
    artifact_path: str
    artifact_hash: str
    byte_size: int
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "source_filename": self.source_filename,
            "source_mode": self.source_mode,
            "artifact_type": self.artifact_type,
            "artifact_path": self.artifact_path,
            "artifact_hash": self.artifact_hash,
            "byte_size": self.byte_size,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class PreservationResult:
    """
    Result of artifact preservation.

    Attributes:
        success: Whether preservation succeeded
        artifacts: List of preserved artifacts
        output_dir: Directory where artifacts were written
        errors: List of errors encountered
    """
    success: bool
    artifacts: List[PreservedArtifact] = field(default_factory=list)
    output_dir: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "output_dir": self.output_dir,
            "errors": self.errors,
        }


def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content).hexdigest()


def preserve_artifacts(
    dxf_base64: Optional[str] = None,
    dxf_bytes: Optional[bytes] = None,
    svg_content: Optional[str] = None,
    source_filename: str = "unknown",
    source_mode: str = "pdf",
    artifact_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> PreservationResult:
    """
    Preserve DXF/SVG artifacts to disk with metadata.

    Saves:
    - Original DXF bytes verbatim
    - Original SVG content if present
    - Metadata JSON with hashes and provenance

    Args:
        dxf_base64: Base64-encoded DXF content
        dxf_bytes: Raw DXF bytes (alternative to base64)
        svg_content: SVG content string
        source_filename: Original filename
        source_mode: "pdf" or "photo"
        artifact_id: Optional custom ID
        output_dir: Optional custom output directory

    Returns:
        PreservationResult with artifact paths and hashes
    """
    errors = []
    artifacts = []

    # Generate artifact ID
    if artifact_id is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        artifact_id = f"artifact_{timestamp}_{hash(source_filename) % 10000:04d}"

    # Determine output directory
    if output_dir is None:
        output_dir = WORKFLOW_1A_ARTIFACTS_DIR / artifact_id
    else:
        output_dir = Path(output_dir) / artifact_id

    # Create directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return PreservationResult(
            success=False,
            errors=[f"Failed to create output directory: {e}"],
        )

    created_at = datetime.now(timezone.utc).isoformat()

    # Preserve DXF
    if dxf_base64 or dxf_bytes:
        try:
            if dxf_bytes is None:
                dxf_bytes = base64.b64decode(dxf_base64)

            dxf_hash = compute_hash(dxf_bytes)
            dxf_path = output_dir / f"{artifact_id}.dxf"

            with open(dxf_path, "wb") as f:
                f.write(dxf_bytes)

            artifacts.append(PreservedArtifact(
                artifact_id=f"{artifact_id}_dxf",
                source_filename=source_filename,
                source_mode=source_mode,
                artifact_type="dxf",
                artifact_path=str(dxf_path),
                artifact_hash=dxf_hash,
                byte_size=len(dxf_bytes),
                created_at=created_at,
            ))

            logger.info(f"Preserved DXF: {dxf_path} ({len(dxf_bytes)} bytes)")

        except Exception as e:
            errors.append(f"Failed to preserve DXF: {e}")

    # Preserve SVG
    if svg_content:
        try:
            svg_bytes = svg_content.encode("utf-8")
            svg_hash = compute_hash(svg_bytes)
            svg_path = output_dir / f"{artifact_id}.svg"

            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

            artifacts.append(PreservedArtifact(
                artifact_id=f"{artifact_id}_svg",
                source_filename=source_filename,
                source_mode=source_mode,
                artifact_type="svg",
                artifact_path=str(svg_path),
                artifact_hash=svg_hash,
                byte_size=len(svg_bytes),
                created_at=created_at,
            ))

            logger.info(f"Preserved SVG: {svg_path} ({len(svg_bytes)} bytes)")

        except Exception as e:
            errors.append(f"Failed to preserve SVG: {e}")

    # Write metadata JSON
    if artifacts:
        try:
            metadata = {
                "artifact_id": artifact_id,
                "source_filename": source_filename,
                "source_mode": source_mode,
                "created_at": created_at,
                "artifacts": [a.to_dict() for a in artifacts],
            }

            metadata_path = output_dir / f"{artifact_id}_metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Wrote metadata: {metadata_path}")

        except Exception as e:
            errors.append(f"Failed to write metadata: {e}")

    return PreservationResult(
        success=len(artifacts) > 0,
        artifacts=artifacts,
        output_dir=str(output_dir),
        errors=errors if errors else None,
    )


def load_preserved_artifact(artifact_path: str) -> Optional[bytes]:
    """Load preserved artifact bytes from path."""
    try:
        with open(artifact_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load artifact {artifact_path}: {e}")
        return None


def verify_artifact_integrity(artifact: PreservedArtifact) -> bool:
    """Verify artifact integrity by recomputing hash."""
    content = load_preserved_artifact(artifact.artifact_path)
    if content is None:
        return False

    computed_hash = compute_hash(content)
    return computed_hash == artifact.artifact_hash
