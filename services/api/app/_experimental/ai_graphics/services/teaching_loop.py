"""
Teaching Loop — Export Approved Advisory Assets to Training Data

Connects the human review workflow to LoRA training:
1. DALL-E generates images → AdvisoryAsset (not approved)
2. Human reviews → approves best ones
3. THIS MODULE → exports approved to training format
4. Kohya trains → Guitar LoRA

Dataset Output:
    dataset/
    ├── images/
    │   ├── 00001_electric_les_paul_sunburst.png
    │   ├── 00001_electric_les_paul_sunburst.txt  (caption)
    │   └── ...
    ├── metadata.jsonl
    └── export_log.json

Author: Luthier's ToolBox
Date: December 2025
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..advisory_store import get_advisory_store, AdvisoryAssetStore
from ..schemas.advisory_schemas import AdvisoryAsset, AdvisoryAssetType
from ..prompt_engine import parse_guitar_request

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ExportConfig:
    """Configuration for training data export."""

    # Output directory
    output_dir: Path = field(default_factory=lambda: Path("./guitar_training_dataset"))

    # Caption settings
    trigger_word: str = "guitar_photo"
    include_quality_tags: bool = True

    # Export options
    copy_images: bool = True  # False = symlink instead
    overwrite_existing: bool = False

    # Filtering
    min_confidence: float = 0.0  # Minimum confidence score
    providers: Optional[List[str]] = None  # Filter by provider

    def __post_init__(self):
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)


@dataclass
class ExportedSample:
    """Record of an exported training sample."""
    asset_id: str
    index: int

    # Labels extracted from prompt
    category: str
    body_shape: Optional[str]
    finish: Optional[str]

    # Prompts
    original_prompt: str
    caption: str

    # Files
    image_path: str
    caption_path: str

    # Source metadata
    provider: str
    model: str
    reviewed_by: Optional[str]
    approved_at: Optional[str]

    # Export metadata
    exported_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ExportReport:
    """Report from export operation."""
    total_approved: int
    exported_count: int
    skipped_count: int
    error_count: int

    output_dir: str
    exported_samples: List[ExportedSample] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_approved": self.total_approved,
            "exported_count": self.exported_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "output_dir": self.output_dir,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "errors": self.errors[:20],  # Limit for display
        }


# =============================================================================
# CAPTION GENERATOR
# =============================================================================

def generate_caption(
    asset: AdvisoryAsset,
    trigger_word: str = "guitar_photo",
    include_quality_tags: bool = True,
) -> str:
    """
    Generate training caption from advisory asset.

    Format optimized for LoRA fine-tuning:
    - Trigger word first
    - Key attributes as tags
    - Quality descriptors
    """
    parts = [trigger_word]

    # Parse the original prompt to extract attributes
    parsed = parse_guitar_request(asset.prompt)

    # Category
    if parsed.category and parsed.category.value != "unknown":
        parts.append(f"{parsed.category.value} guitar")
    else:
        parts.append("guitar")

    # Body shape
    if parsed.body_shape:
        parts.append(parsed.body_shape)

    # Finish
    if parsed.finish:
        parts.append(f"{parsed.finish} finish")

    # Hardware (first item if exists)
    if parsed.hardware:
        parts.append(parsed.hardware[0])

    # Wood (first item if exists)
    if parsed.woods:
        parts.append(parsed.woods[0])

    # Inlays (first two)
    for inlay in parsed.inlays[:2]:
        parts.append(inlay)

    # Photo style from meta or parsed
    photo_style = asset.meta.get("photo_style") or parsed.photo_style or "product"
    parts.append(f"{photo_style} photography")

    # Quality tags
    if include_quality_tags:
        parts.extend([
            "professional photo",
            "high detail",
            "studio lighting",
        ])

    return ", ".join(parts)


def extract_labels(asset: AdvisoryAsset) -> Dict[str, Any]:
    """Extract structured labels from asset prompt."""
    parsed = parse_guitar_request(asset.prompt)

    return {
        "category": parsed.category.value if parsed.category else "unknown",
        "body_shape": parsed.body_shape,
        "finish": parsed.finish,
        "hardware": parsed.hardware[0] if parsed.hardware else None,
        "wood": parsed.woods[0] if parsed.woods else None,
        "confidence": parsed.confidence,
    }


def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filename."""
    # Replace spaces and special chars
    text = re.sub(r'[^a-zA-Z0-9_-]', '_', text.lower())
    # Collapse multiple underscores
    text = re.sub(r'_+', '_', text)
    # Remove leading/trailing underscores
    return text.strip('_')[:50]


# =============================================================================
# TEACHING LOOP EXPORTER
# =============================================================================

class TeachingLoopExporter:
    """
    Exports approved AdvisoryAssets to LoRA training format.

    The teaching loop:
    1. DALL-E (teacher) generates diverse guitar images
    2. Human curates - approves best examples
    3. This exporter prepares training data
    4. LoRA (student) learns from curated examples
    """

    def __init__(
        self,
        config: Optional[ExportConfig] = None,
        store: Optional[AdvisoryAssetStore] = None,
    ):
        self.config = config or ExportConfig()
        self.store = store or get_advisory_store()

        # Ensure output directories exist
        self.images_dir = self.config.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def get_approved_assets(self) -> List[AdvisoryAsset]:
        """Get all approved image assets."""
        assets = self.store.list_assets(
            asset_type=AdvisoryAssetType.IMAGE,
            approved=True,
            limit=10000,
        )

        # Apply filters
        filtered = []
        for asset in assets:
            # Confidence filter
            if asset.confidence is not None:
                if asset.confidence < self.config.min_confidence:
                    continue

            # Provider filter
            if self.config.providers:
                if asset.provider not in self.config.providers:
                    continue

            filtered.append(asset)

        return filtered

    def export_asset(
        self,
        asset: AdvisoryAsset,
        index: int,
    ) -> Optional[ExportedSample]:
        """Export a single asset to training format."""

        # Get image content
        content = self.store.get_asset_content(asset)
        if content is None:
            logger.warning(f"No content for asset {asset.asset_id}")
            return None

        # Extract labels
        labels = extract_labels(asset)

        # Generate filename
        filename_parts = [
            f"{index:05d}",
            sanitize_filename(labels["category"]),
            sanitize_filename(labels["body_shape"] or "unknown"),
            sanitize_filename(labels["finish"] or "natural"),
        ]
        filename = "_".join(filename_parts)

        # Image path
        image_path = self.images_dir / f"{filename}.png"

        # Check if exists
        if image_path.exists() and not self.config.overwrite_existing:
            logger.debug(f"Skipping existing: {image_path}")
            return None

        # Write image
        if self.config.copy_images:
            image_path.write_bytes(content)
        else:
            # Symlink to original
            source = self.store.root / asset.content_uri
            if source.exists():
                if image_path.exists():
                    image_path.unlink()
                image_path.symlink_to(source.absolute())

        # Generate caption
        caption = generate_caption(
            asset,
            trigger_word=self.config.trigger_word,
            include_quality_tags=self.config.include_quality_tags,
        )

        # Write caption file (same name, .txt extension)
        caption_path = self.images_dir / f"{filename}.txt"
        caption_path.write_text(caption)

        return ExportedSample(
            asset_id=asset.asset_id,
            index=index,
            category=labels["category"],
            body_shape=labels["body_shape"],
            finish=labels["finish"],
            original_prompt=asset.prompt,
            caption=caption,
            image_path=f"images/{filename}.png",
            caption_path=f"images/{filename}.txt",
            provider=asset.provider,
            model=asset.model,
            reviewed_by=asset.reviewed_by,
            approved_at=asset.reviewed_at_utc.isoformat() if asset.reviewed_at_utc else None,
        )

    def export_all(self) -> ExportReport:
        """Export all approved assets to training format."""

        approved = self.get_approved_assets()

        report = ExportReport(
            total_approved=len(approved),
            exported_count=0,
            skipped_count=0,
            error_count=0,
            output_dir=str(self.config.output_dir),
        )

        logger.info(f"Exporting {len(approved)} approved assets to {self.config.output_dir}")

        for i, asset in enumerate(approved, start=1):
            try:
                sample = self.export_asset(asset, i)

                if sample:
                    report.exported_samples.append(sample)
                    report.exported_count += 1
                else:
                    report.skipped_count += 1

            except Exception as e:
                report.error_count += 1
                report.errors.append({
                    "asset_id": asset.asset_id,
                    "error": str(e),
                })
                logger.error(f"Error exporting {asset.asset_id}: {e}")

        # Write metadata.jsonl
        self._write_metadata(report.exported_samples)

        # Write export log
        report.completed_at = datetime.utcnow().isoformat()
        self._write_export_log(report)

        logger.info(
            f"Export complete: {report.exported_count} exported, "
            f"{report.skipped_count} skipped, {report.error_count} errors"
        )

        return report

    def _write_metadata(self, samples: List[ExportedSample]) -> None:
        """Write metadata.jsonl for training."""
        meta_path = self.config.output_dir / "metadata.jsonl"

        with open(meta_path, "w") as f:
            for sample in samples:
                record = {
                    "file_name": sample.image_path,
                    "caption": sample.caption,
                    "category": sample.category,
                    "body_shape": sample.body_shape,
                    "finish": sample.finish,
                    "provider": sample.provider,
                    "asset_id": sample.asset_id,
                }
                f.write(json.dumps(record) + "\n")

    def _write_export_log(self, report: ExportReport) -> None:
        """Write export log."""
        log_path = self.config.output_dir / "export_log.json"

        with open(log_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

    def get_stats(self) -> Dict[str, Any]:
        """Get current export statistics."""
        approved = self.get_approved_assets()

        # Count existing exports
        existing_images = list(self.images_dir.glob("*.png"))
        existing_captions = list(self.images_dir.glob("*.txt"))

        # Provider breakdown
        by_provider = {}
        for asset in approved:
            by_provider[asset.provider] = by_provider.get(asset.provider, 0) + 1

        # Category breakdown
        by_category = {}
        for asset in approved:
            labels = extract_labels(asset)
            cat = labels["category"]
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "approved_count": len(approved),
            "existing_images": len(existing_images),
            "existing_captions": len(existing_captions),
            "by_provider": by_provider,
            "by_category": by_category,
            "output_dir": str(self.config.output_dir),
        }


# =============================================================================
# API INTEGRATION
# =============================================================================

def export_approved_to_training(
    output_dir: str = "./guitar_training_dataset",
    trigger_word: str = "guitar_photo",
    min_confidence: float = 0.0,
) -> ExportReport:
    """
    Export all approved advisory assets to LoRA training format.

    Args:
        output_dir: Directory for training dataset
        trigger_word: Trigger word for LoRA (appears first in captions)
        min_confidence: Minimum confidence score to include

    Returns:
        ExportReport with results
    """
    config = ExportConfig(
        output_dir=Path(output_dir),
        trigger_word=trigger_word,
        min_confidence=min_confidence,
    )

    exporter = TeachingLoopExporter(config)
    return exporter.export_all()


def get_export_stats(output_dir: str = "./guitar_training_dataset") -> Dict[str, Any]:
    """Get statistics about approved assets and existing exports."""
    config = ExportConfig(output_dir=Path(output_dir))
    exporter = TeachingLoopExporter(config)
    return exporter.get_stats()


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Export approved Advisory Assets to LoRA training format"
    )

    parser.add_argument(
        "--output", "-o",
        default="./guitar_training_dataset",
        help="Output directory for training data",
    )
    parser.add_argument(
        "--trigger-word",
        default="guitar_photo",
        help="Trigger word for LoRA captions",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum confidence score",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics only, don't export",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files",
    )

    args = parser.parse_args()

    config = ExportConfig(
        output_dir=Path(args.output),
        trigger_word=args.trigger_word,
        min_confidence=args.min_confidence,
        overwrite_existing=args.overwrite,
    )

    exporter = TeachingLoopExporter(config)

    print("=" * 60)
    print("TEACHING LOOP - TRAINING DATA EXPORT")
    print("=" * 60)

    if args.stats:
        stats = exporter.get_stats()
        print(f"\nStatistics:")
        print(f"   Approved assets: {stats['approved_count']}")
        print(f"   Existing images: {stats['existing_images']}")
        print(f"   By provider: {stats['by_provider']}")
        print(f"   By category: {stats['by_category']}")
        print(f"   Output dir: {stats['output_dir']}")
        return

    print(f"\nOutput: {config.output_dir}")
    print(f"   Trigger word: {config.trigger_word}")
    print(f"   Min confidence: {config.min_confidence}")

    report = exporter.export_all()

    print(f"\nExport Complete:")
    print(f"   Total approved: {report.total_approved}")
    print(f"   Exported: {report.exported_count}")
    print(f"   Skipped: {report.skipped_count}")
    print(f"   Errors: {report.error_count}")

    if report.exported_count > 0:
        print(f"\nNext steps:")
        print(f"   1. Generate Kohya config:")
        print(f"      python kohya_config.py --dataset {config.output_dir}")
        print(f"   2. Run training:")
        print(f"      bash {config.output_dir}/config/train.sh")


if __name__ == "__main__":
    main()
