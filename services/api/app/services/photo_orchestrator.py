"""
Photo Orchestrator
==================

Single orchestration boundary for photo vectorization.

Purpose:
- own stage sequencing
- own warning aggregation
- own confidence sourcing (CRITICAL: from real scorer, not fabricated)
- own artifact validation
- own final response construction

Non-goals:
- no new geometry logic
- no new scoring logic
- no retry/agentic expansion

This mirrors the Blueprint orchestrator pattern for architectural consistency.

Author: Production Shop
"""

from __future__ import annotations

import base64
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .contour_recommendation import (
    ProcessingMode,
    Recommendation,
    RecommendationAction,
    RecommendationInput,
    SelectionResult,
    recommend,
)

logger = logging.getLogger(__name__)


# ─── Canonical Result Schema ─────────────────────────────────────────────────

@dataclass
class SVGArtifact:
    present: bool = False
    content: str = ""
    path_count: int = 0


@dataclass
class DXFArtifact:
    present: bool = False
    base64: str = ""
    entity_count: int = 0
    closed_contours: int = 0


@dataclass
class Dimensions:
    width_mm: float = 0.0
    height_mm: float = 0.0
    width_in: float = 0.0
    height_in: float = 0.0
    spec_match: Optional[str] = None
    confidence: float = 0.0


@dataclass
class PhotoResult:
    """Canonical result from photo orchestration."""
    ok: bool  # True only when recommendation.action == "accept"
    processed: bool = True  # Pipeline completed (transport-level)
    stage: str = "complete"
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    dimensions: Dimensions = field(default_factory=Dimensions)
    svg: SVGArtifact = field(default_factory=SVGArtifact)
    dxf: DXFArtifact = field(default_factory=DXFArtifact)
    selection: SelectionResult = field(default_factory=SelectionResult)
    recommendation: Recommendation = field(default_factory=Recommendation)
    metrics: dict[str, Any] = field(default_factory=dict)
    debug: dict[str, Any] = field(default_factory=dict)

    def to_response_dict(self, include_debug: bool = False) -> dict[str, Any]:
        """Convert to API response dictionary (canonical schema only)."""
        payload = {
            "ok": self.ok,
            "processed": self.processed,
            "stage": self.stage,
            "error": self.error,
            "warnings": self.warnings,
            "dimensions": {
                "width_mm": self.dimensions.width_mm,
                "height_mm": self.dimensions.height_mm,
                "width_in": self.dimensions.width_in,
                "height_in": self.dimensions.height_in,
                "spec_match": self.dimensions.spec_match,
                "confidence": self.dimensions.confidence,
            },
            "artifacts": {
                "svg": {
                    "present": self.svg.present,
                    "content": self.svg.content,
                    "path_count": self.svg.path_count,
                },
                "dxf": {
                    "present": self.dxf.present,
                    "base64": self.dxf.base64,
                    "entity_count": self.dxf.entity_count,
                    "closed_contours": self.dxf.closed_contours,
                },
            },
            "selection": self.selection.to_dict(),
            "recommendation": self.recommendation.to_dict(),
            "metrics": self.metrics,
        }
        if include_debug and self.debug:
            payload["debug"] = self.debug
        return payload


# ─── Validation Thresholds ───────────────────────────────────────────────────

SVG_MIN_CHARS = 50
DXF_MIN_BYTES = 800


# ─── Orchestrator ────────────────────────────────────────────────────────────

class PhotoOrchestratorError(RuntimeError):
    """Error during orchestration with stage context."""
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.message = message


class PhotoOrchestrator:
    """
    Orchestrates photo vectorization into canonical artifacts.

    Single source of truth for photo business logic. Wraps the existing
    PhotoVectorizerV2 and centralizes:
    - artifact loading/encoding
    - confidence sourcing (from real scorer output)
    - final validation
    - response shape

    Does NOT change the underlying photo pipeline behavior (hard gate at 0.60).
    """

    def process_image(
        self,
        *,
        image_bytes: bytes,
        filename: str = "upload.png",
        spec_name: Optional[str] = None,
        known_dimension_mm: Optional[float] = None,
        correct_perspective: bool = True,
        export_svg: bool = True,
        export_dxf: bool = False,
        source_type: str = "auto",
        gap_closing_level: str = "normal",
        debug: bool = False,
    ) -> PhotoResult:
        """
        Process an image through photo vectorization.

        Args:
            image_bytes: Raw image content (JPEG/PNG)
            filename: Original filename for extension detection
            spec_name: Instrument spec for scaling (e.g., "stratocaster")
            known_dimension_mm: Known width if available
            correct_perspective: Apply perspective correction
            export_svg: Generate SVG output
            export_dxf: Generate DXF output
            source_type: Source type hint (auto, ai, photo, blueprint, silhouette)
            gap_closing_level: Gap closing aggressiveness (normal, aggressive, extreme)
            debug: Include debug info in result

        Returns:
            PhotoResult with canonical artifacts
        """
        # Copy warnings (not extend) to avoid aliasing bugs
        warnings: list[str] = []

        # ─── Validate input ───────────────────────────────────────────────
        if not image_bytes:
            return PhotoResult(
                ok=False,
                stage="upload",
                error="Empty image uploaded.",
            )

        try:
            # ─── Import vectorizer (assume path configured by router) ─────
            try:
                from photo_vectorizer_v2 import PhotoVectorizerV2
            except ImportError as e:
                logger.error(f"PhotoVectorizerV2 not available: {e}")
                return PhotoResult(
                    ok=False,
                    stage="error",
                    error=f"Photo vectorizer not available: {e}",
                )

            # ─── Create temp directory for processing ─────────────────────
            with tempfile.TemporaryDirectory(prefix="photo_orch_") as tmpdir:
                tmpdir_path = Path(tmpdir)

                # Write input image
                input_path = tmpdir_path / filename
                input_path.write_bytes(image_bytes)

                # Create output directory (orchestrator owns this)
                out_dir = tmpdir_path / "out"
                out_dir.mkdir(exist_ok=True)

                # ─── Stage: Vectorization ─────────────────────────────────
                logger.info(f"PHOTO_ORCHESTRATE | file={filename} size={len(image_bytes)} bytes")

                vectorizer = PhotoVectorizerV2()
                result = vectorizer.extract(
                    source_path=str(input_path),
                    output_dir=str(out_dir),
                    spec_name=spec_name,
                    known_dimension_mm=known_dimension_mm,
                    correct_perspective=correct_perspective,
                    export_svg=export_svg,
                    export_dxf=export_dxf,
                    export_json=False,
                    debug_images=False,
                    source_type=source_type,
                    gap_closing_level=gap_closing_level,
                )

                # Copy warnings from result (not extend to avoid aliasing)
                result_warnings = list(getattr(result, "warnings", []) or [])
                warnings.extend(result_warnings)

                # ─── Stage: Dimension extraction ──────────────────────────
                # body_dimensions_mm is stored as (height, width) — unpack correctly
                h_mm, w_mm = getattr(result, "body_dimensions_mm", (0.0, 0.0))
                h_in, w_in = getattr(result, "body_dimensions_inch", (0.0, 0.0))

                # ─── Stage: SVG artifact encoding ─────────────────────────
                svg_content = ""
                svg_path_count = 0
                output_svg = getattr(result, "output_svg", None)

                if output_svg and Path(output_svg).exists():
                    try:
                        svg_content = Path(output_svg).read_text(encoding="utf-8")
                        svg_path_count = svg_content.count("<path")
                    except Exception as e:
                        logger.error(f"SVG read failed: {e}")
                        warnings.append(f"SVG read failed: {e}")

                svg_valid = len(svg_content) > SVG_MIN_CHARS

                # ─── Stage: DXF artifact encoding ─────────────────────────
                dxf_b64 = ""
                dxf_entity_count = 0
                output_dxf = getattr(result, "output_dxf", None)

                if output_dxf and Path(output_dxf).exists():
                    try:
                        dxf_bytes = Path(output_dxf).read_bytes()
                        if len(dxf_bytes) >= DXF_MIN_BYTES:
                            dxf_b64 = base64.b64encode(dxf_bytes).decode("ascii")
                            # Normalize line endings for entity counting
                            dxf_text = dxf_bytes.decode("utf-8", errors="ignore").replace("\r\n", "\n")
                            dxf_entity_count = (
                                dxf_text.count("\nLINE\n") +
                                dxf_text.count("\nLWPOLYLINE\n")
                            )
                    except Exception as e:
                        logger.error(f"DXF read failed: {e}")
                        warnings.append(f"DXF read failed: {e}")

                dxf_valid = len(dxf_b64) > 0 and dxf_entity_count > 0

                # ─── Stage: Validation ────────────────────────────────────
                validation_errors: list[str] = []

                if export_svg and not svg_valid:
                    validation_errors.append("SVG artifact missing or invalid")
                if export_dxf and not dxf_valid:
                    validation_errors.append("DXF artifact missing or invalid")

                # Check export blocking from upstream
                export_blocked = bool(getattr(result, "export_blocked", False))
                export_block_reason = getattr(result, "export_block_reason", "") or ""

                if export_blocked:
                    validation_errors.append(export_block_reason or "Export blocked")

                warnings.extend(validation_errors)

                # ─── CRITICAL: Source confidence from real scorer ─────────
                # This replaces the fabricated 0.9/0.0 value with actual signal
                ownership_score = 0.0
                contour_stage = getattr(result, "contour_stage", None)
                if contour_stage is not None:
                    ownership_val = getattr(contour_stage, "ownership_score", None)
                    if ownership_val is not None:
                        ownership_score = float(ownership_val)

                # ─── Stage: Recommendation ────────────────────────────────
                # Build selection result from contour stage
                # Photo pipeline doesn't expose runner-up directly, so estimate
                best_score = getattr(contour_stage, "best_score", ownership_score) if contour_stage else ownership_score
                candidate_count = getattr(contour_stage, "candidate_count", 1) if contour_stage else 1

                selection = SelectionResult(
                    candidate_count=candidate_count,
                    selected_index=0 if svg_path_count > 0 else None,
                    selection_score=best_score,
                    runner_up_score=0.0,  # Photo pipeline doesn't expose this
                    winner_margin=best_score,  # Assume dominant if selected
                    reasons=[],
                )

                # Determine scale source
                scale_src = (
                    result.calibration.source.value
                    if getattr(result, "calibration", None)
                    else "estimated"
                )

                # Build recommendation input
                rec_input = RecommendationInput(
                    selection=selection,
                    mode=ProcessingMode.PHOTO,
                    svg_valid=svg_valid,
                    dxf_valid=dxf_valid,
                    warnings=warnings,
                    ownership_score=ownership_score,
                    scale_source=scale_src,
                )

                # Get recommendation
                rec = recommend(rec_input)

                # ok = true only when recommendation.action == "accept"
                is_ok = rec.action == RecommendationAction.ACCEPT
                stage = "complete" if is_ok else "recommendation"

                # Add recommendation reasons to warnings if not accept
                if rec.action != RecommendationAction.ACCEPT:
                    for reason in rec.reasons:
                        if reason not in warnings:
                            warnings.append(reason)

                # ─── Build result ─────────────────────────────────────────
                logger.info(
                    f"PHOTO_ORCHESTRATE | ok={is_ok} ownership={ownership_score:.3f} "
                    f"rec={rec.action.value} svg={svg_valid} dxf={dxf_valid}"
                )

                return PhotoResult(
                    ok=is_ok,
                    processed=True,
                    stage=stage,
                    error="; ".join(rec.reasons) if rec.action == RecommendationAction.REJECT else "",
                    warnings=warnings,
                    dimensions=Dimensions(
                        width_mm=round(w_mm, 2),
                        height_mm=round(h_mm, 2),
                        width_in=round(w_in, 3),
                        height_in=round(h_in, 3),
                        spec_match=spec_name,
                        confidence=round(ownership_score, 3),  # Deprecated, use selection/recommendation
                    ),
                    svg=SVGArtifact(
                        present=svg_valid,
                        content=svg_content,
                        path_count=svg_path_count,
                    ),
                    dxf=DXFArtifact(
                        present=dxf_valid,
                        base64=dxf_b64,
                        entity_count=dxf_entity_count,
                        closed_contours=svg_path_count,  # Best proxy for closed contours
                    ),
                    selection=selection,
                    recommendation=rec,
                    metrics={
                        "processing_ms": float(getattr(result, "processing_time_ms", 0.0) or 0.0),
                        "scale_source": scale_src,
                        "bg_method": getattr(result, "bg_method_used", "none"),
                        "perspective_corrected": getattr(result, "perspective_corrected", False),
                    },
                    debug={
                        "ownership_score": ownership_score,
                        "ownership_threshold": 0.60,
                        "ownership_ok": ownership_score >= 0.60,
                        "export_blocked": export_blocked,
                        "export_block_reason": export_block_reason,
                        "recommendation_action": rec.action.value,
                        "recommendation_confidence": rec.confidence,
                    } if debug else {},
                )

        except PhotoOrchestratorError as e:
            return PhotoResult(ok=False, stage=e.stage, error=e.message)
        except Exception as e:
            logger.exception("Photo orchestration failed")
            return PhotoResult(ok=False, stage="error", error=str(e))
