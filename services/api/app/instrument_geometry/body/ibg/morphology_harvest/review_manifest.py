"""
Review Manifest Generator — Harvest Record Index
=================================================

Generates manifests tracking harvested records and their review status.

Format:
- manifest.json — corpus index with statistics
- records/<harvest_id>.json — individual harvest records

Follows pattern from tests/regression_corpus/manifest.json.

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import HarvestRecord, ReviewStatus


@dataclass
class ManifestEntry:
    """
    Summary entry for a harvest record in the manifest.

    Lightweight summary for the index file.
    """
    harvest_id: str
    source_pdf: str
    page_number: int
    review_status: str
    morphology_class: Optional[str]
    instrument_family: Optional[str]
    body_length_mm: Optional[float]
    overall_confidence: float
    requires_review: bool
    record_path: str  # Relative path to full record

    @classmethod
    def from_record(cls, record: HarvestRecord, record_path: str) -> "ManifestEntry":
        """Create entry from HarvestRecord."""
        return cls(
            harvest_id=record.harvest_id,
            source_pdf=record.source_pdf,
            page_number=record.page_number,
            review_status=record.review_status.value,
            morphology_class=record.body_data.morphology_class,
            instrument_family=record.body_data.instrument_family_normalized,
            body_length_mm=record.body_data.body_length_mm,
            overall_confidence=record.overall_confidence(),
            requires_review=record.requires_human_review(),
            record_path=record_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HarvestManifest:
    """
    Manifest for harvested morphology records.

    Index file format following regression_corpus pattern.
    """
    manifest_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    governance_doc: str = "docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md"

    # Source information
    corpus_root: Optional[str] = None

    # Statistics
    total_records: int = 0
    pending_review: int = 0
    approved: int = 0
    rejected: int = 0
    with_body_data: int = 0

    # Distribution
    family_distribution: Dict[str, int] = field(default_factory=dict)
    morphology_distribution: Dict[str, int] = field(default_factory=dict)
    status_distribution: Dict[str, int] = field(default_factory=dict)

    # Entries (summaries only)
    entries: List[ManifestEntry] = field(default_factory=list)

    def add_record(
        self,
        record: HarvestRecord,
        record_path: str,
    ) -> ManifestEntry:
        """
        Add a harvest record to the manifest.

        Args:
            record: HarvestRecord to add
            record_path: Relative path to saved record JSON

        Returns:
            ManifestEntry created
        """
        entry = ManifestEntry.from_record(record, record_path)
        self.entries.append(entry)

        self._update_statistics()
        self.updated_at = datetime.now().isoformat()

        return entry

    def _update_statistics(self) -> None:
        """Recalculate statistics from entries."""
        self.total_records = len(self.entries)

        # Status counts
        self.pending_review = sum(
            1 for e in self.entries
            if e.review_status == ReviewStatus.PENDING_REVIEW.value
        )
        self.approved = sum(
            1 for e in self.entries
            if e.review_status in (
                ReviewStatus.APPROVED.value,
                ReviewStatus.APPROVED_WITH_EDITS.value
            )
        )
        self.rejected = sum(
            1 for e in self.entries
            if e.review_status == ReviewStatus.REJECTED.value
        )
        self.with_body_data = sum(
            1 for e in self.entries
            if e.body_length_mm is not None
        )

        # Distributions
        self.family_distribution = {}
        for e in self.entries:
            if e.instrument_family:
                family = e.instrument_family
                self.family_distribution[family] = \
                    self.family_distribution.get(family, 0) + 1

        self.morphology_distribution = {}
        for e in self.entries:
            if e.morphology_class:
                mc = e.morphology_class
                self.morphology_distribution[mc] = \
                    self.morphology_distribution.get(mc, 0) + 1

        self.status_distribution = {}
        for e in self.entries:
            status = e.review_status
            self.status_distribution[status] = \
                self.status_distribution.get(status, 0) + 1

    def get_pending_reviews(self) -> List[ManifestEntry]:
        """Get all entries pending human review."""
        return [
            e for e in self.entries
            if e.requires_review or e.review_status == ReviewStatus.PENDING_REVIEW.value
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "governance_doc": self.governance_doc,
            "corpus_root": self.corpus_root,
            "statistics": {
                "total_records": self.total_records,
                "pending_review": self.pending_review,
                "approved": self.approved,
                "rejected": self.rejected,
                "with_body_data": self.with_body_data,
            },
            "distributions": {
                "family": self.family_distribution,
                "morphology": self.morphology_distribution,
                "status": self.status_distribution,
            },
            "entries": [e.to_dict() for e in self.entries],
        }

    def save(self, path: str) -> None:
        """Save manifest to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "HarvestManifest":
        """Load manifest from JSON file."""
        with open(path) as f:
            data = json.load(f)

        manifest = cls(
            manifest_version=data.get("manifest_version", "1.0.0"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            corpus_root=data.get("corpus_root"),
        )

        stats = data.get("statistics", {})
        manifest.total_records = stats.get("total_records", 0)
        manifest.pending_review = stats.get("pending_review", 0)
        manifest.approved = stats.get("approved", 0)
        manifest.rejected = stats.get("rejected", 0)
        manifest.with_body_data = stats.get("with_body_data", 0)

        dists = data.get("distributions", {})
        manifest.family_distribution = dists.get("family", {})
        manifest.morphology_distribution = dists.get("morphology", {})
        manifest.status_distribution = dists.get("status", {})

        for entry_data in data.get("entries", []):
            entry = ManifestEntry(**entry_data)
            manifest.entries.append(entry)

        return manifest


class ManifestManager:
    """
    Manages harvest manifest and record storage.

    Directory structure:
        outputs/
        ├── manifest.json
        ├── records/
        │   ├── harvest_abc123.json
        │   └── harvest_def456.json
        └── overlays/
            ├── harvest_abc123.png
            └── harvest_def456.png
    """

    def __init__(self, output_dir: str):
        """
        Initialize manifest manager.

        Args:
            output_dir: Root directory for outputs
        """
        self.output_dir = Path(output_dir)
        self.records_dir = self.output_dir / "records"
        self.overlays_dir = self.output_dir / "overlays"
        self.manifest_path = self.output_dir / "manifest.json"

        # Ensure directories exist
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.overlays_dir.mkdir(parents=True, exist_ok=True)

        # Load or create manifest
        if self.manifest_path.exists():
            self.manifest = HarvestManifest.load(str(self.manifest_path))
        else:
            self.manifest = HarvestManifest()

    def save_record(
        self,
        record: HarvestRecord,
        generate_overlay: bool = False,
    ) -> str:
        """
        Save harvest record and update manifest.

        Args:
            record: HarvestRecord to save
            generate_overlay: Whether to generate review overlay

        Returns:
            Path to saved record
        """
        # Save record
        record_filename = f"{record.harvest_id}.json"
        record_path = self.records_dir / record_filename
        record.save(str(record_path))

        # Update manifest
        relative_path = f"records/{record_filename}"
        self.manifest.add_record(record, relative_path)
        self.manifest.save(str(self.manifest_path))

        # Generate overlay if requested
        if generate_overlay:
            try:
                from .overlay_wrapper import generate_harvest_overlay
                overlay_path = self.overlays_dir / f"{record.harvest_id}.png"
                generate_harvest_overlay(record, str(overlay_path))
            except Exception:
                pass  # Overlay generation is optional

        return str(record_path)

    def load_record(self, harvest_id: str) -> Optional[HarvestRecord]:
        """Load a harvest record by ID."""
        record_path = self.records_dir / f"{harvest_id}.json"

        if not record_path.exists():
            return None

        return HarvestRecord.load(str(record_path))

    def get_statistics(self) -> Dict[str, Any]:
        """Get current manifest statistics."""
        return self.manifest.to_dict()["statistics"]

    def export_report(self, output_path: str) -> None:
        """Export human-readable summary report."""
        stats = self.get_statistics()

        lines = [
            "# Morphology Harvest Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Statistics",
            f"- Total Records: {stats['total_records']}",
            f"- With Body Data: {stats['with_body_data']}",
            f"- Pending Review: {stats['pending_review']}",
            f"- Approved: {stats['approved']}",
            f"- Rejected: {stats['rejected']}",
            "",
            "## Family Distribution",
        ]

        for family, count in self.manifest.family_distribution.items():
            lines.append(f"- {family}: {count}")

        lines.extend([
            "",
            "## Morphology Distribution",
        ])

        for mc, count in self.manifest.morphology_distribution.items():
            lines.append(f"- {mc}: {count}")

        lines.extend([
            "",
            "## Pending Reviews",
        ])

        for entry in self.manifest.get_pending_reviews():
            lines.append(f"- {entry.harvest_id}: {entry.source_pdf}")

        with open(output_path, 'w') as f:
            f.write("\n".join(lines))
