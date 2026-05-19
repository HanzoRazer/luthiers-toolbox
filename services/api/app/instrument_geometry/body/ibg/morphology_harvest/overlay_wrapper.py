"""
Overlay Wrapper — Minimal Human Review Overlay Generator
=========================================================

Generates lightweight review overlays for harvested records.
Can integrate with body_grid/overlay_exporter.py when BodyEvidence exists.

For 1A: minimal implementation
- Source thumbnail
- Detected dimension highlights if available
- Review status area
- Optional body grid overlay if available

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .schema import HarvestRecord, ReviewStatus

# PIL for overlay generation
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# PyMuPDF for PDF thumbnail
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


@dataclass
class OverlayConfig:
    """Configuration for overlay generation."""
    width: int = 800
    height: int = 1000
    thumbnail_height: int = 600
    margin: int = 20
    font_size: int = 14
    show_dimensions: bool = True
    show_review_status: bool = True
    show_body_grid: bool = True


class HarvestOverlayWrapper:
    """
    Generates human-review overlays for harvest records.

    Minimal implementation for 1A:
    - PDF page thumbnail
    - Dimension text overlay
    - Review status badge
    - Optional body grid integration
    """

    def __init__(self, config: Optional[OverlayConfig] = None):
        self.config = config or OverlayConfig()

    def can_generate(self) -> bool:
        """Check if overlay generation is possible."""
        return HAS_PIL

    def generate_overlay(
        self,
        record: HarvestRecord,
        output_path: str,
    ) -> Optional[str]:
        """
        Generate overlay image for harvest record.

        Args:
            record: HarvestRecord to visualize
            output_path: Path for output PNG

        Returns:
            Output path if successful, None otherwise
        """
        if not HAS_PIL:
            return None

        # Create canvas
        img = Image.new('RGB', (self.config.width, self.config.height), 'white')
        draw = ImageDraw.Draw(img)

        y_offset = self.config.margin

        # Try to add PDF thumbnail
        thumbnail = self._get_pdf_thumbnail(record.source_pdf, record.page_number)
        if thumbnail:
            # Resize to fit
            thumb_width = self.config.width - 2 * self.config.margin
            thumb_height = self.config.thumbnail_height
            thumbnail = thumbnail.resize(
                (thumb_width, thumb_height),
                Image.Resampling.LANCZOS
            )
            img.paste(thumbnail, (self.config.margin, y_offset))
            y_offset += thumb_height + self.config.margin
        else:
            # Placeholder
            draw.rectangle(
                [
                    self.config.margin, y_offset,
                    self.config.width - self.config.margin,
                    y_offset + self.config.thumbnail_height
                ],
                outline='gray',
                width=2
            )
            draw.text(
                (self.config.width // 2, y_offset + self.config.thumbnail_height // 2),
                "PDF thumbnail unavailable",
                fill='gray',
                anchor='mm'
            )
            y_offset += self.config.thumbnail_height + self.config.margin

        # Draw review status badge
        if self.config.show_review_status:
            y_offset = self._draw_review_status(draw, record, y_offset)

        # Draw dimension summary
        if self.config.show_dimensions:
            y_offset = self._draw_dimension_summary(draw, record, y_offset)

        # Draw source info
        y_offset = self._draw_source_info(draw, record, y_offset)

        # Save
        img.save(output_path, 'PNG')
        return output_path

    def _get_pdf_thumbnail(
        self,
        pdf_path: str,
        page: int = 1,
    ) -> Optional[Image.Image]:
        """Extract thumbnail from PDF."""
        if not HAS_FITZ:
            return None

        try:
            doc = fitz.open(pdf_path)
            if page > len(doc):
                page = 1

            pdf_page = doc[page - 1]

            # Render at 150 DPI
            mat = fitz.Matrix(150 / 72, 150 / 72)
            pix = pdf_page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)

            doc.close()
            return img

        except Exception:
            return None

    def _draw_review_status(
        self,
        draw: ImageDraw.Draw,
        record: HarvestRecord,
        y_offset: int,
    ) -> int:
        """Draw review status badge."""
        status = record.review_status
        status_colors = {
            ReviewStatus.PENDING_REVIEW: ('#FFA500', 'black'),  # Orange
            ReviewStatus.APPROVED: ('#00AA00', 'white'),  # Green
            ReviewStatus.APPROVED_WITH_EDITS: ('#0088FF', 'white'),  # Blue
            ReviewStatus.REJECTED: ('#FF0000', 'white'),  # Red
            ReviewStatus.DEFERRED: ('#888888', 'white'),  # Gray
        }

        bg_color, text_color = status_colors.get(status, ('#888888', 'white'))

        # Draw badge
        badge_width = 200
        badge_height = 30
        x = self.config.width - self.config.margin - badge_width

        draw.rectangle(
            [x, y_offset, x + badge_width, y_offset + badge_height],
            fill=bg_color
        )
        draw.text(
            (x + badge_width // 2, y_offset + badge_height // 2),
            status.value.upper().replace('_', ' '),
            fill=text_color,
            anchor='mm'
        )

        return y_offset + badge_height + 10

    def _draw_dimension_summary(
        self,
        draw: ImageDraw.Draw,
        record: HarvestRecord,
        y_offset: int,
    ) -> int:
        """Draw dimension summary."""
        body = record.body_data

        lines = ["DIMENSIONS:"]

        if body.body_length_mm:
            lines.append(f"  Body Length: {body.body_length_mm:.1f} mm")
        if body.lower_bout_width_mm:
            lines.append(f"  Lower Bout: {body.lower_bout_width_mm:.1f} mm")
        if body.upper_bout_width_mm:
            lines.append(f"  Upper Bout: {body.upper_bout_width_mm:.1f} mm")
        if body.waist_width_mm:
            lines.append(f"  Waist: {body.waist_width_mm:.1f} mm")

        if record.neck_system_data.scale_length_mm:
            lines.append(f"  Scale Length: {record.neck_system_data.scale_length_mm:.1f} mm")

        if len(lines) == 1:
            lines.append("  (no dimensions extracted)")

        # Confidence
        if body.observed:
            lines.append(f"  Confidence: {body.confidence:.0%}")

        for line in lines:
            draw.text(
                (self.config.margin, y_offset),
                line,
                fill='black'
            )
            y_offset += self.config.font_size + 4

        return y_offset + 10

    def _draw_source_info(
        self,
        draw: ImageDraw.Draw,
        record: HarvestRecord,
        y_offset: int,
    ) -> int:
        """Draw source information."""
        lines = [
            f"Source: {Path(record.source_pdf).name}",
            f"Page: {record.page_number}",
            f"Harvest ID: {record.harvest_id}",
            f"Source Type: {record.harvest_source.value}",
        ]

        if record.body_data.morphology_class:
            lines.append(f"Morphology: {record.body_data.morphology_class}")

        if record.body_data.instrument_family_normalized:
            lines.append(f"Family: {record.body_data.instrument_family_normalized}")

        for line in lines:
            draw.text(
                (self.config.margin, y_offset),
                line,
                fill='#666666'
            )
            y_offset += self.config.font_size + 4

        return y_offset

    def generate_body_grid_overlay(
        self,
        record: HarvestRecord,
        output_path: str,
    ) -> Optional[str]:
        """
        Generate body grid overlay if BodyEvidence conversion is possible.

        Delegates to body_grid/overlay_exporter.py.
        """
        if not HAS_PIL:
            return None

        # Check if we can convert to BodyEvidence
        body_evidence = record.to_body_evidence()
        if not body_evidence or not body_evidence.landmarks:
            return None

        try:
            from ..body_grid.morphology_descriptor import MorphologyAnalyzer
            from ..body_grid.overlay_exporter import OverlayExporter, OverlayConfig as BGOverlayConfig

            analyzer = MorphologyAnalyzer()
            descriptor = analyzer.analyze(body_evidence)

            config = BGOverlayConfig(
                width=self.config.width,
                height=self.config.thumbnail_height,
                show_zones=True,
                show_centerline=True,
                show_legend=True,
            )

            exporter = OverlayExporter(config)
            exporter.export(descriptor, output_path)

            return output_path

        except ImportError:
            return None
        except Exception:
            return None


def generate_harvest_overlay(
    record: HarvestRecord,
    output_path: str,
    config: Optional[OverlayConfig] = None,
) -> Optional[str]:
    """
    Convenience function to generate harvest overlay.

    Args:
        record: HarvestRecord to visualize
        output_path: Path for output PNG
        config: Optional overlay configuration

    Returns:
        Output path if successful, None otherwise
    """
    wrapper = HarvestOverlayWrapper(config)
    return wrapper.generate_overlay(record, output_path)
