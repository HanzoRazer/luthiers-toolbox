"""
Blueprint Orchestrator
======================

Single orchestration boundary for blueprint vectorization.
Composes extraction + cleanup services and returns canonical artifacts.

This is the central business logic owner. Routes call this, not the
individual services directly (except for legacy/debug endpoints).

SCOPE BOUNDARY: Blueprint Pipeline Only
---------------------------------------
This refactor applies to the blueprint pipeline only.

Blueprint contour selection now uses unified contour scoring, where
ownership is a weighted input signal rather than a standalone hard gate.
Low-confidence results return with warnings instead of failing outright.

The photo vectorizer (/api/vectorizer/extract, services/photo-vectorizer/)
remains on its existing ownership-threshold logic (hard gate at 0.60) and
is OUT OF SCOPE for this refactor. Do not assume behavioral parity.

Usage:
    orchestrator = BlueprintOrchestrator()
    result = orchestrator.process_file(
        file_bytes=content,
        filename="blueprint.pdf",
        target_height_mm=500.0,
    )
    return result.to_response_dict()

Author: Production Shop
"""

from __future__ import annotations

import base64
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .blueprint_extract import (
    ExtractionResult,
    extract_blueprint_to_dxf,
    extract_pdf_page,
)
from .blueprint_clean import (
    CleanResult,
    clean_blueprint_dxf,
    validate_cleanup_result,
)
from .contour_recommendation import (
    ProcessingMode,
    Recommendation,
    RecommendationAction,
    RecommendationInput,
    SelectionResult,
    recommend,
)

logger = logging.getLogger(__name__)

# Type alias for progress callbacks
ProgressCallback = Optional[Callable[[str, int], None]]


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


@dataclass
class BlueprintResult:
    """Canonical result from blueprint orchestration."""
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
        """Convert to API response dictionary."""
        payload = {
            "ok": self.ok,
            "processed": self.processed,
            "stage": self.stage,
            "error": self.error,
            "warnings": self.warnings,
            "dimensions": {
                "width_mm": self.dimensions.width_mm,
                "height_mm": self.dimensions.height_mm,
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

class BlueprintOrchestratorError(RuntimeError):
    """Error during orchestration with stage context."""
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.message = message


class BlueprintOrchestrator:
    """
    Orchestrates blueprint extraction + cleanup into canonical artifacts.

    Single source of truth for blueprint business logic. Both sync routes
    and future async job runners call this orchestrator.
    """

    def process_file(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        page_num: int = 0,
        target_height_mm: float = 500.0,
        min_contour_length_mm: float = 50.0,
        close_gaps_mm: float = 1.0,
        canny_low: int = 50,
        canny_high: int = 150,
        debug: bool = False,
        progress_callback: ProgressCallback = None,
    ) -> BlueprintResult:
        """
        Process a blueprint file through extraction and cleanup.

        Args:
            file_bytes: Raw file content (image or PDF)
            filename: Original filename for extension detection
            page_num: PDF page number (0-indexed)
            target_height_mm: Target height for scaling
            min_contour_length_mm: Minimum contour length to keep
            close_gaps_mm: Maximum gap to close
            canny_low: Canny edge detection low threshold
            canny_high: Canny edge detection high threshold
            debug: Include debug info in result
            progress_callback: Optional (stage, percent) callback

        Returns:
            BlueprintResult with canonical artifacts
        """
        stage_timings: dict[str, float] = {}
        warnings: list[str] = []

        def report(stage: str, progress: int) -> None:
            if progress_callback:
                progress_callback(stage, progress)

        try:
            # ─── Validate input ───────────────────────────────────────────
            if not file_bytes:
                return BlueprintResult(
                    ok=False,
                    stage="upload",
                    error="Empty file uploaded",
                )

            file_ext = Path(filename).suffix.lower()
            logger.info(f"BLUEPRINT_ORCHESTRATE | file={filename} size={len(file_bytes)} bytes")

            # ─── Create temp directory for processing ─────────────────────
            with tempfile.TemporaryDirectory(prefix="blueprint_orch_") as tmpdir:
                tmpdir_path = Path(tmpdir)

                # ─── Stage: Image extraction (PDF → image if needed) ──────
                report("image_extract", 10)

                if file_ext == ".pdf":
                    # Extract PDF with DPI cap (guardrail applied inside)
                    image_bytes = extract_pdf_page(file_bytes, page_num, warnings=warnings)
                    if not image_bytes:
                        return BlueprintResult(
                            ok=False,
                            stage="image_extract",
                            error=f"Failed to extract page {page_num} from PDF",
                        )
                    input_path = tmpdir_path / "input.png"
                    input_path.write_bytes(image_bytes)
                else:
                    input_path = tmpdir_path / f"input{file_ext}"
                    input_path.write_bytes(file_bytes)

                # ─── Stage: Edge extraction ───────────────────────────────
                report("edge_extraction", 30)

                raw_dxf_path = tmpdir_path / "raw_edges.dxf"
                extract_result = extract_blueprint_to_dxf(
                    source_path=str(input_path),
                    output_path=str(raw_dxf_path),
                    target_height_mm=target_height_mm,
                    canny_low=canny_low,
                    canny_high=canny_high,
                    warnings=warnings,  # Pass warnings list for guardrail messages
                )

                if not extract_result.success:
                    return BlueprintResult(
                        ok=False,
                        stage="edge_extraction",
                        error=extract_result.error or "Edge extraction failed",
                        warnings=warnings,
                    )

                # warnings were already appended in-place by extract_pdf_page()
                # and extract_blueprint_to_dxf(..., warnings=warnings)
                stage_timings["extraction_ms"] = extract_result.processing_time_ms

                # ─── Stage: Cleanup/filtering ─────────────────────────────
                report("cleanup", 60)

                cleaned_dxf_path = tmpdir_path / "cleaned.dxf"
                clean_result = clean_blueprint_dxf(
                    input_path=str(raw_dxf_path),
                    output_path=str(cleaned_dxf_path),
                    min_contour_length_mm=min_contour_length_mm,
                    close_gaps_mm=close_gaps_mm,
                )

                # CRITICAL FIX: Do NOT bail early on cleanup failure
                # Continue to artifact generation — let recommendation layer decide
                # Artifact existence is independent of selection confidence
                cleanup_valid = True
                if not clean_result.success:
                    cleanup_valid = False
                    warnings.append(clean_result.error or "Cleanup encountered issues")
                else:
                    # Validate cleanup result (adds warnings, does NOT block)
                    cleanup_valid, cleanup_warnings = validate_cleanup_result(clean_result)
                    warnings.extend(cleanup_warnings)

                # ─── Stage: Encode DXF to base64 ──────────────────────────
                report("encode", 80)

                dxf_b64 = ""
                dxf_entity_count = 0

                if cleaned_dxf_path.exists():
                    dxf_bytes = cleaned_dxf_path.read_bytes()
                    dxf_b64 = base64.b64encode(dxf_bytes).decode("ascii")
                    # Count entities - normalize line endings for reliable counting
                    # VALIDATION EXPECTATION (Fusion compatibility):
                    #   - DXF version: R12 (AC1009)
                    #   - Entity type: LINE only (no LWPOLYLINE)
                    #   - See CLAUDE.md "Blueprint Export Compatibility"
                    dxf_text = dxf_bytes.decode("utf-8", errors="ignore").replace("\r\n", "\n")
                    dxf_entity_count = (
                        dxf_text.count("\nLINE\n") +
                        dxf_text.count("\nLWPOLYLINE\n")  # Should be 0 for R12 output
                    )

                # ─── Stage: Validation ────────────────────────────────────
                report("validation", 90)

                svg_content = clean_result.svg_preview
                svg_path_count = svg_content.count("<path") if svg_content else 0
                svg_valid = len(svg_content) > SVG_MIN_CHARS
                dxf_valid = len(dxf_b64) > 0 and dxf_entity_count > 0

                if not svg_valid:
                    warnings.append("SVG content below minimum threshold")
                if not dxf_valid:
                    warnings.append("DXF content missing or empty")

                # ─── Stage: Recommendation ────────────────────────────────
                # Build selection result from cleanup output
                selection = SelectionResult(
                    candidate_count=clean_result.candidate_count,
                    selected_index=0 if clean_result.contours_found > 0 else None,
                    selection_score=clean_result.best_confidence,
                    runner_up_score=clean_result.runner_up_score,
                    winner_margin=clean_result.winner_margin,
                    reasons=[],
                )

                # Build recommendation input
                rec_input = RecommendationInput(
                    selection=selection,
                    mode=ProcessingMode.BLUEPRINT,
                    svg_valid=svg_valid,
                    dxf_valid=dxf_valid,
                    warnings=warnings,
                    ownership_score=None,  # Not used for blueprint
                    scale_source="estimated",  # Blueprint doesn't have calibration
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
                report("complete", 100)

                return BlueprintResult(
                    ok=is_ok,
                    processed=True,
                    stage=stage,
                    error="" if is_ok else "; ".join(rec.reasons),
                    warnings=warnings,
                    dimensions=Dimensions(
                        width_mm=extract_result.output_size_mm[0],
                        height_mm=extract_result.output_size_mm[1],
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
                        closed_contours=clean_result.contours_found,
                    ),
                    selection=selection,
                    recommendation=rec,
                    metrics={
                        "processing_ms": extract_result.processing_time_ms,  # Canonical name
                        "extraction_ms": extract_result.processing_time_ms,  # Legacy alias
                        "original_entities": extract_result.line_count,
                        "cleaned_entities": clean_result.cleaned_entity_count,
                        "contours_found": clean_result.contours_found,
                        "chains_found": clean_result.chains_found,
                        "contour_confidence": round(clean_result.best_confidence, 3),
                    },
                    debug=stage_timings if debug else {},
                )

        except BlueprintOrchestratorError as e:
            return BlueprintResult(ok=False, stage=e.stage, error=e.message)
        except Exception as e:
            logger.exception("Blueprint orchestration failed")
            return BlueprintResult(ok=False, stage="error", error=str(e))
