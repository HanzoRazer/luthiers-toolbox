"""
MRP-3A: Body Outline DXF Translator

Governed translator that serializes BodyExportObject to DXF format.
Wraps the existing protected dxf_writer.py infrastructure.

Design principles:
  - Deterministic: same input → same output (excluding timestamps)
  - Provenance: embeds export metadata in DXF XDATA where possible
  - Gate-aware: refuses to translate red-gated exports
  - Dual-format: supports R12 (free) and R2000 (paid) outputs
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from app.cam.dxf_writer import DxfWriter, LayerDef, create_dxf_writer
from app.cam.translators.base import (
    BaseTranslator,
    TranslatorError,
    TranslatorErrorCode,
    TranslatorResult,
)
from app.export.body_export_bridge import BodyExportObject, GeometryEntity
from app.cam.export_object import ExportObject


DXF_R12_TRANSLATOR_ID = "body_outline_dxf_r12"
DXF_R2000_TRANSLATOR_ID = "body_outline_dxf_r2000"
TRANSLATOR_VERSION = "1.0.0"


class BodyOutlineDxfTranslator(BaseTranslator):
    """
    Governed DXF translator for body outline geometry.

    Supports both R12 and R2000 output formats via dxf_writer.
    """

    # Layer naming convention
    LAYER_BODY_OUTLINE = "BODY_OUTLINE"
    LAYER_VOID = "VOID"
    LAYER_PROVENANCE = "PROVENANCE"

    # Layer colors
    COLOR_OUTLINE = 5  # Blue
    COLOR_VOID = 1     # Red
    COLOR_PROVENANCE = 8  # Gray

    def __init__(self, dxf_version: str = "R12"):
        """
        Initialize translator.

        Args:
            dxf_version: "R12" for free tier, "R2000" for paid tier
        """
        if dxf_version not in ("R12", "R2000"):
            raise ValueError(f"Unsupported DXF version: {dxf_version}")

        translator_id = (
            DXF_R12_TRANSLATOR_ID if dxf_version == "R12"
            else DXF_R2000_TRANSLATOR_ID
        )

        super().__init__(
            translator_id=translator_id,
            translator_version=TRANSLATOR_VERSION,
            output_format="dxf",
        )
        self._dxf_version = dxf_version

    @property
    def dxf_version(self) -> str:
        return self._dxf_version

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

    def _extract_points(self, entity: GeometryEntity) -> List[Tuple[float, float]]:
        """Extract (x, y) tuples from entity points."""
        return [(p[0], p[1]) for p in entity.points]

    def _create_writer(self) -> DxfWriter:
        """Create configured DXF writer."""
        layers = [
            LayerDef(self.LAYER_BODY_OUTLINE, self.COLOR_OUTLINE),
            LayerDef(self.LAYER_VOID, self.COLOR_VOID),
            LayerDef(self.LAYER_PROVENANCE, self.COLOR_PROVENANCE),
        ]
        return DxfWriter(layers=layers, version=self._dxf_version)

    def _add_provenance_text(
        self,
        writer: DxfWriter,
        provenance_lines: List[str],
        bounds: Any,
    ) -> None:
        """Add provenance as text entities below the geometry."""
        x_start = bounds.x_min
        y_start = bounds.y_min - 15  # 15mm below geometry

        for i, line in enumerate(provenance_lines):
            writer.add_text(
                self.LAYER_PROVENANCE,
                line,
                (x_start, y_start - (i * 5)),  # 5mm line spacing
                height=3.0,
            )

    def _do_translate(
        self,
        export_object: Union[BodyExportObject, ExportObject],
        options: Optional[Any] = None,
    ) -> TranslatorResult:
        """
        Translate BodyExportObject to DXF bytes.

        Args:
            export_object: Validated BodyExportObject
            options: Optional settings (dict or TranslatorOptions):
                - embed_provenance: bool (default True) — add provenance text
                - close_contours: bool (default True) — ensure closed polylines

        Returns:
            TranslatorResult with DXF bytes or errors
        """
        # Handle both dict (MRP-3A) and TranslatorOptions (MRP-4A) formats
        if options is None:
            embed_provenance = True
            close_contours = True
        elif hasattr(options, "embed_provenance"):
            # TranslatorOptions (MRP-4A)
            embed_provenance = options.embed_provenance
            close_contours = getattr(options, "close_contours", True)
        else:
            # Dict (MRP-3A backward compat)
            embed_provenance = options.get("embed_provenance", True)
            close_contours = options.get("close_contours", True)

        errors: List[TranslatorError] = []
        warnings: List[str] = []
        stats: Dict[str, Any] = {
            "entities_translated": 0,
            "outer_contours": 0,
            "voids": 0,
            "total_points": 0,
        }

        try:
            writer = self._create_writer()

            for entity in export_object.geometry.entities:
                if entity.type != "closed_contour":
                    warnings.append(
                        f"Skipping unsupported entity type: {entity.type}"
                    )
                    continue

                points = self._extract_points(entity)
                if len(points) < 3:
                    warnings.append(
                        f"Entity {entity.id} has fewer than 3 points, skipped"
                    )
                    continue

                layer = (
                    self.LAYER_BODY_OUTLINE
                    if entity.role in ("outer", "body_outer", "main")
                    else self.LAYER_VOID
                )

                writer.add_polyline(layer, points, closed=close_contours)

                stats["entities_translated"] += 1
                stats["total_points"] += len(points)
                if layer == self.LAYER_BODY_OUTLINE:
                    stats["outer_contours"] += 1
                else:
                    stats["voids"] += 1

            if embed_provenance:
                provenance = self._build_provenance(export_object)
                provenance_lines = [
                    f"Export ID: {provenance.export_id}",
                    f"Translator: {provenance.translator_id} v{provenance.translator_version}",
                    f"Translated: {provenance.translated_at[:10]}",
                ]
                if provenance.ibg_session_id:
                    provenance_lines.append(f"IBG Session: {provenance.ibg_session_id}")
                if provenance.instrument_spec:
                    provenance_lines.append(f"Instrument: {provenance.instrument_spec}")

                self._add_provenance_text(
                    writer,
                    provenance_lines,
                    export_object.geometry.bounds,
                )

            output_bytes = writer.to_bytes()
            stats["output_size_bytes"] = len(output_bytes)

            provenance = self._build_provenance(export_object)

            return TranslatorResult(
                success=True,
                output_format=f"dxf_{self._dxf_version.lower()}",
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
                output_format=f"dxf_{self._dxf_version.lower()}",
                errors=errors,
                warnings=warnings,
                statistics=stats,
            )


def create_r12_translator() -> BodyOutlineDxfTranslator:
    """Create R12 (free tier) DXF translator."""
    return BodyOutlineDxfTranslator(dxf_version="R12")


def create_r2000_translator() -> BodyOutlineDxfTranslator:
    """Create R2000 (paid tier) DXF translator."""
    return BodyOutlineDxfTranslator(dxf_version="R2000")
