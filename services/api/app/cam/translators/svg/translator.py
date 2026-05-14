"""
MRP-4A: Body Outline SVG Translator

Governed translator that serializes BodyExportObject to SVG format.

Design principles:
  - Deterministic output (excluding timestamp in provenance)
  - Layer-based styling matching DXF convention
  - Provenance embedded as XML comments
  - Proper viewBox for CAD-style coordinate system
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
from xml.sax.saxutils import escape as xml_escape

from app.cam.translators.base.contracts import (
    BaseTranslator,
    TranslatorError,
    TranslatorErrorCode,
    TranslatorResult,
    TranslatorOptions,
)
from app.export.body_export_bridge import BodyExportObject, GeometryEntity
from app.cam.export_object import ExportObject


SVG_TRANSLATOR_ID = "body_outline_svg"
TRANSLATOR_VERSION = "1.0.0"


# Layer colors (matching DXF convention)
COLOR_OUTLINE = "#0066CC"  # Blue
COLOR_VOID = "#CC0000"     # Red
COLOR_PROVENANCE = "#888888"  # Gray

# Stroke settings
STROKE_WIDTH_OUTLINE = 1.5
STROKE_WIDTH_VOID = 1.0


class BodyOutlineSvgTranslator(BaseTranslator):
    """
    Governed SVG translator for body outline geometry.

    Produces styled SVG with:
      - Viewbox matching geometry bounds with padding
      - Y-axis flipped for CAD-style orientation (Y increases upward)
      - Layer-based coloring (outer = blue, voids = red)
      - Provenance as XML comment
    """

    def __init__(self):
        super().__init__(
            translator_id=SVG_TRANSLATOR_ID,
            translator_version=TRANSLATOR_VERSION,
            target_format="svg",
        )

    def can_translate(
        self,
        export_object: Union[BodyExportObject, ExportObject],
    ) -> bool:
        """Check if translator can handle this export object."""
        if not hasattr(export_object, "export_type"):
            return False

        if export_object.export_type != "geometry":
            return False

        if not hasattr(export_object, "geometry"):
            return False

        if not hasattr(export_object.geometry, "entities"):
            return False

        return True

    def _points_to_path(
        self,
        points: List[List[float]],
        closed: bool = True,
    ) -> str:
        """Convert points to SVG path data string."""
        if len(points) < 2:
            return ""

        parts = [f"M {points[0][0]:.3f} {points[0][1]:.3f}"]

        for point in points[1:]:
            parts.append(f"L {point[0]:.3f} {point[1]:.3f}")

        if closed:
            parts.append("Z")

        return " ".join(parts)

    def _compute_viewbox(
        self,
        bounds: Any,
        padding_pct: float = 0.05,
    ) -> Tuple[float, float, float, float]:
        """Compute viewBox with padding."""
        width = bounds.x_max - bounds.x_min
        height = bounds.y_max - bounds.y_min

        pad_x = width * padding_pct
        pad_y = height * padding_pct

        return (
            bounds.x_min - pad_x,
            bounds.y_min - pad_y,
            width + 2 * pad_x,
            height + 2 * pad_y,
        )

    def _build_provenance_comment(
        self,
        export_object: Union[BodyExportObject, ExportObject],
    ) -> str:
        """Build XML comment with provenance data."""
        provenance = self._build_provenance(export_object)

        lines = [
            "Provenance:",
            f"  export_id: {provenance.export_id}",
            f"  translator: {provenance.translator_id} v{provenance.translator_version}",
            f"  translated_at: {provenance.translated_at}",
            f"  target_format: {provenance.target_format}",
        ]

        if provenance.source_hash:
            lines.append(f"  source_hash: {provenance.source_hash}")
        if provenance.ibg_session_id:
            lines.append(f"  ibg_session_id: {provenance.ibg_session_id}")
        if provenance.instrument_spec:
            lines.append(f"  instrument_spec: {provenance.instrument_spec}")

        return "<!--\n" + "\n".join(lines) + "\n-->"

    def _do_translate(
        self,
        export_object: Union[BodyExportObject, ExportObject],
        options: Optional[TranslatorOptions] = None,
    ) -> TranslatorResult:
        """
        Translate BodyExportObject to SVG bytes.

        Args:
            export_object: Validated BodyExportObject
            options: Optional translation options

        Returns:
            TranslatorResult with SVG bytes or errors
        """
        options = options or TranslatorOptions()
        embed_provenance = options.embed_provenance

        errors: List[TranslatorError] = []
        warnings: List[str] = []
        stats: Dict[str, Any] = {
            "entities_translated": 0,
            "outer_contours": 0,
            "voids": 0,
            "total_points": 0,
        }

        try:
            bounds = export_object.geometry.bounds
            vb = self._compute_viewbox(bounds)

            svg_parts = []

            if embed_provenance:
                svg_parts.append(self._build_provenance_comment(export_object))

            svg_parts.append(
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="{vb[0]:.3f} {vb[1]:.3f} {vb[2]:.3f} {vb[3]:.3f}" '
                f'width="{vb[2]:.0f}mm" height="{vb[3]:.0f}mm">'
            )

            svg_parts.append(
                f'  <g id="body-outline" transform="scale(1,-1) translate(0,{-(vb[1] * 2 + vb[3]):.3f})">'
            )

            for entity in export_object.geometry.entities:
                if entity.type != "closed_contour":
                    warnings.append(
                        f"Skipping unsupported entity type: {entity.type}"
                    )
                    continue

                if len(entity.points) < 3:
                    warnings.append(
                        f"Entity {entity.id} has fewer than 3 points, skipped"
                    )
                    continue

                is_outer = entity.role in ("outer", "body_outer", "main")
                color = COLOR_OUTLINE if is_outer else COLOR_VOID
                stroke_width = STROKE_WIDTH_OUTLINE if is_outer else STROKE_WIDTH_VOID

                path_data = self._points_to_path(entity.points, closed=True)

                entity_id = xml_escape(entity.id)
                svg_parts.append(
                    f'    <path id="{entity_id}" '
                    f'd="{path_data}" '
                    f'fill="none" '
                    f'stroke="{color}" '
                    f'stroke-width="{stroke_width}" '
                    f'stroke-linecap="round" '
                    f'stroke-linejoin="round"/>'
                )

                stats["entities_translated"] += 1
                stats["total_points"] += len(entity.points)
                if is_outer:
                    stats["outer_contours"] += 1
                else:
                    stats["voids"] += 1

            svg_parts.append("  </g>")
            svg_parts.append("</svg>")

            svg_content = "\n".join(svg_parts)
            output_bytes = svg_content.encode("utf-8")
            stats["output_size_bytes"] = len(output_bytes)

            provenance = self._build_provenance(export_object)

            return TranslatorResult(
                success=True,
                output_format="svg",
                output_bytes=output_bytes,
                errors=errors,
                warnings=warnings,
                provenance=provenance,
                statistics=stats,
            )

        except Exception as e:
            errors.append(
                TranslatorError(
                    code=TranslatorErrorCode.SERIALIZATION_FAILED,
                    message=str(e),
                    details={"exception_type": type(e).__name__},
                )
            )
            return TranslatorResult(
                success=False,
                output_format="svg",
                errors=errors,
                warnings=warnings,
                statistics=stats,
            )


def create_svg_translator() -> BodyOutlineSvgTranslator:
    """Create SVG translator instance."""
    return BodyOutlineSvgTranslator()
