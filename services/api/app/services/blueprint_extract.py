"""
Blueprint Extraction Service
============================

Shared extraction logic for blueprint vectorization.
Extracted from vectorize_router.py to enable reuse by:
- Sync /api/blueprint/vectorize route
- Future async job runner
- Legacy edge_to_dxf_router.py (if refactored)

Includes guardrails:
- PDF DPI cap
- Raster dimension/megapixel limits
- Auto-downscale with warnings

Author: Production Shop
"""

from __future__ import annotations

import logging
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .blueprint_limits import LIMITS, BlueprintGuardrailError

logger = logging.getLogger(__name__)


# ─── Result Model ────────────────────────────────────────────────────────────

@dataclass
class ExtractionResult:
    """Result from blueprint edge extraction."""
    success: bool
    output_path: str = ""
    line_count: int = 0
    edge_pixel_count: int = 0
    image_size_px: tuple[int, int] = (0, 0)
    output_size_mm: tuple[float, float] = (0.0, 0.0)
    mm_per_px: float = 0.0
    processing_time_ms: float = 0.0
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    stage_timings: dict[str, float] = field(default_factory=dict)
    # Primary Object Grouping metadata (debug-only, internal)
    grouping: Optional[dict] = None


# ─── Guardrail Helpers ───────────────────────────────────────────────────────

def image_megapixels(width: int, height: int) -> float:
    """Calculate megapixels from dimensions."""
    return (width * height) / 1_000_000.0


def should_downscale(width: int, height: int) -> bool:
    """Check if image exceeds dimension or megapixel limits."""
    return (
        max(width, height) > LIMITS.max_raster_dim_px
        or image_megapixels(width, height) > LIMITS.max_megapixels
    )


def compute_downscale_factor(width: int, height: int) -> float:
    """Compute scale factor to bring image within limits."""
    dim_scale = LIMITS.max_raster_dim_px / max(width, height)
    mp = image_megapixels(width, height)
    mp_scale = math.sqrt(LIMITS.max_megapixels / max(mp, 0.001))
    return min(dim_scale, mp_scale, 1.0)


def downscale_image_if_needed(image: Any, warnings: list[str]) -> Any:
    """
    Downscale image if it exceeds dimension/megapixel limits.

    Args:
        image: OpenCV image (numpy array)
        warnings: List to append warning messages to

    Returns:
        Original or downscaled image
    """
    import cv2

    height, width = image.shape[:2]

    if not should_downscale(width, height):
        return image

    scale = compute_downscale_factor(width, height)
    new_w = max(int(width * scale), LIMITS.min_downscaled_dim_px)
    new_h = max(int(height * scale), LIMITS.min_downscaled_dim_px)

    # Keep aspect ratio bounded by original
    new_w = min(new_w, width)
    new_h = min(new_h, height)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    warnings.append(
        f"Blueprint raster was downscaled from {width}x{height} to {new_w}x{new_h} for web processing."
    )
    logger.info(f"BLUEPRINT_DOWNSCALE | {width}x{height} -> {new_w}x{new_h}")
    return resized


def validate_loaded_raster(image: Any) -> None:
    """
    Validate that loaded raster is usable.

    Raises:
        BlueprintGuardrailError: If image is invalid
    """
    if image is None:
        raise BlueprintGuardrailError("Could not load blueprint image for processing.")

    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        raise BlueprintGuardrailError("Loaded blueprint image has invalid dimensions.")


# ─── PDF Extraction ──────────────────────────────────────────────────────────

def extract_pdf_page(
    pdf_bytes: bytes,
    page_num: int = 0,
    requested_dpi: int = 300,
    warnings: Optional[list[str]] = None,
) -> Optional[bytes]:
    """
    Extract a page from PDF as PNG bytes.

    DPI is capped by BLUEPRINT_MAX_PDF_DPI to prevent pathological rasterization.

    Args:
        pdf_bytes: Raw PDF file content
        page_num: Page index (0-based)
        requested_dpi: Requested render resolution
        warnings: List to append warning messages to

    Returns:
        PNG bytes or None if extraction fails
    """
    try:
        import fitz  # PyMuPDF

        # Cap DPI to configured limit
        dpi = min(requested_dpi, LIMITS.max_pdf_dpi)
        if dpi < requested_dpi and warnings is not None:
            warnings.append(
                f"PDF render DPI capped from {requested_dpi} to {dpi} for web processing."
            )
            logger.info(f"BLUEPRINT_DPI_CAP | {requested_dpi} -> {dpi}")

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_num >= len(doc):
            logger.error(f"Page {page_num} out of range (PDF has {len(doc)} pages)")
            return None

        page = doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        doc.close()
        return png_bytes

    except ImportError:
        logger.error("PyMuPDF (fitz) not available for PDF extraction")
        return None
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return None


# ─── Path Setup ──────────────────────────────────────────────────────────────

def _ensure_edge_to_dxf_importable() -> bool:
    """Add photo-vectorizer to path if needed."""
    candidates = [
        Path(__file__).parents[3] / "photo-vectorizer",
        Path("/app/services/photo-vectorizer"),
        Path(__file__).parents[4] / "services" / "photo-vectorizer",
    ]
    for p in candidates:
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
            return True
    return False


# ─── Main Extraction ─────────────────────────────────────────────────────────

def extract_blueprint_to_dxf(
    source_path: str,
    output_path: str,
    target_height_mm: float = 500.0,
    canny_low: int = 50,
    canny_high: int = 150,
    adjacency: float = 3.0,
    warnings: Optional[list[str]] = None,
    isolate_body: bool = True,
) -> ExtractionResult:
    """
    Run edge-to-DXF conversion on an image file.

    Applies guardrails:
    - Validates loaded raster
    - Downscales if exceeds dimension/MP limits

    Args:
        source_path: Path to input image (PNG, JPEG, etc.)
        output_path: Path for output DXF file
        target_height_mm: Target height for scaling
        canny_low: Canny edge detection low threshold
        canny_high: Canny edge detection high threshold
        adjacency: Max pixel distance to connect edges
        warnings: List to append warning messages to
        isolate_body: Use hierarchy to filter to body candidates only.
            Removes page borders, child contours, and noise. Default: True.

    Returns:
        ExtractionResult with success status and metrics
    """
    if warnings is None:
        warnings = []

    try:
        import cv2

        # Load and validate image
        image = cv2.imread(source_path)
        validate_loaded_raster(image)

        # Apply guardrails: downscale if needed
        original_h, original_w = image.shape[:2]
        image = downscale_image_if_needed(image, warnings)
        final_h, final_w = image.shape[:2]

        # If downscaled, write the downscaled version for processing
        if (final_w, final_h) != (original_w, original_h):
            cv2.imwrite(source_path, image)

        # Run extraction
        _ensure_edge_to_dxf_importable()
        from edge_to_dxf import EdgeToDXF

        converter = EdgeToDXF(
            canny_low=canny_low,
            canny_high=canny_high,
            adjacency_threshold=adjacency,
        )

        result = converter.convert(
            source_path,
            output_path=output_path,
            target_height_mm=target_height_mm,
            isolate_body=isolate_body,
        )

        return ExtractionResult(
            success=True,
            output_path=result.output_path if hasattr(result, 'output_path') else output_path,
            line_count=result.line_count,
            edge_pixel_count=result.edge_pixel_count,
            image_size_px=tuple(result.image_size_px),
            output_size_mm=tuple(result.output_size_mm),
            mm_per_px=result.mm_per_px,
            processing_time_ms=result.processing_time_ms,
            stage_timings=getattr(result, 'stage_timings', {}),
            warnings=warnings,
            grouping=getattr(result, 'grouping', None),
        )

    except BlueprintGuardrailError as e:
        logger.warning(f"Blueprint guardrail: {e}")
        return ExtractionResult(success=False, error=str(e), warnings=warnings)
    except ImportError as e:
        logger.error(f"EdgeToDXF not available: {e}")
        return ExtractionResult(success=False, error=f"EdgeToDXF not available: {e}", warnings=warnings)
    except Exception as e:
        logger.error(f"Edge-to-DXF failed: {e}")
        return ExtractionResult(success=False, error=str(e), warnings=warnings)


def extract_blueprint_enhanced(
    source_path: str,
    output_path: str,
    target_height_mm: float = 500.0,
    warnings: Optional[list[str]] = None,
) -> ExtractionResult:
    """
    Run multi-scale edge fusion extraction (highest quality).

    Uses three Canny threshold levels (30/100, 50/150, 80/200) for
    complete edge coverage. Produces 50,000-300,000+ LINE entities.

    Args:
        source_path: Path to input image
        output_path: Path for output DXF file
        target_height_mm: Target height for scaling
        warnings: List to append warning messages to

    Returns:
        ExtractionResult with success status and metrics
    """
    if warnings is None:
        warnings = []

    try:
        import cv2

        # Load and validate image
        image = cv2.imread(source_path)
        validate_loaded_raster(image)

        # Apply guardrails: downscale if needed
        original_h, original_w = image.shape[:2]
        image = downscale_image_if_needed(image, warnings)
        final_h, final_w = image.shape[:2]

        # If downscaled, write the downscaled version for processing
        if (final_w, final_h) != (original_w, original_h):
            cv2.imwrite(source_path, image)

        _ensure_edge_to_dxf_importable()
        from edge_to_dxf import EdgeToDXF

        converter = EdgeToDXF()
        result = converter.convert_enhanced(
            source_path,
            output_path=output_path,
            target_height_mm=target_height_mm,
        )

        return ExtractionResult(
            success=True,
            output_path=result.output_path if hasattr(result, 'output_path') else output_path,
            line_count=result.line_count,
            edge_pixel_count=result.edge_pixel_count,
            image_size_px=tuple(result.image_size_px),
            output_size_mm=tuple(result.output_size_mm),
            mm_per_px=result.mm_per_px,
            processing_time_ms=result.processing_time_ms,
            warnings=warnings,
        )

    except BlueprintGuardrailError as e:
        logger.warning(f"Blueprint guardrail: {e}")
        return ExtractionResult(success=False, error=str(e), warnings=warnings)
    except ImportError as e:
        logger.error(f"EdgeToDXF not available: {e}")
        return ExtractionResult(success=False, error=f"EdgeToDXF not available: {e}", warnings=warnings)
    except Exception as e:
        logger.error(f"Edge-to-DXF enhanced failed: {e}")
        return ExtractionResult(success=False, error=str(e), warnings=warnings)


# ─── Extraction Pass Boundaries ─────────────────────────────────────────────
#
# These are orchestration seams for dual-pass extraction.
# Phase 1: Pass A only, Pass B is a stub.
# Phase 2+: Pass A and Pass B will both be active.
#
# DO NOT change recovered behavior. These boundaries are for composition only.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StructuralPassResult:
    """Result from Pass A (structural geometry extraction)."""
    success: bool
    dxf_path: str = ""
    entity_count: int = 0
    image_size_px: tuple[int, int] = (0, 0)
    output_size_mm: tuple[float, float] = (0.0, 0.0)
    mm_per_px: float = 0.0
    processing_time_ms: float = 0.0
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    debug: dict = field(default_factory=dict)


@dataclass
class AnnotationPassResult:
    """Result from Pass B (annotation/document extraction)."""
    success: bool
    entity_count: int = 0
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    debug: dict = field(default_factory=dict)
    # Phase 1: stub fields
    active: bool = False  # False until Pass B is implemented


@dataclass
class DualPassResult:
    """Combined result from dual-pass extraction."""
    success: bool
    structural: StructuralPassResult = field(default_factory=StructuralPassResult)
    annotation: AnnotationPassResult = field(default_factory=AnnotationPassResult)
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    # Phase 1 indicator
    pass_b_active: bool = False


def extract_structural_pass(
    source_path: str,
    output_path: str,
    target_height_mm: float = 500.0,
    warnings: Optional[list[str]] = None,
) -> StructuralPassResult:
    """
    Pass A: Structural geometry extraction.

    Uses the recovered baseline behavior (RETR_LIST, no hierarchy filtering).
    This is the foundation for body geometry capture.

    Args:
        source_path: Path to input image
        output_path: Path for output DXF file
        target_height_mm: Target height for scaling
        warnings: List to append warning messages to

    Returns:
        StructuralPassResult with extraction results
    """
    if warnings is None:
        warnings = []

    # Call the recovered baseline path (isolate_body=False)
    result = extract_blueprint_to_dxf(
        source_path=source_path,
        output_path=output_path,
        target_height_mm=target_height_mm,
        warnings=warnings,
        isolate_body=False,  # CRITICAL: recovered baseline behavior
    )

    return StructuralPassResult(
        success=result.success,
        dxf_path=result.output_path,
        entity_count=result.line_count,
        image_size_px=result.image_size_px,
        output_size_mm=result.output_size_mm,
        mm_per_px=result.mm_per_px,
        processing_time_ms=result.processing_time_ms,
        error=result.error,
        warnings=result.warnings,
        debug={
            "grouping": result.grouping,
            "stage_timings": result.stage_timings,
        },
    )


def extract_annotation_pass(
    source_path: str,
    warnings: Optional[list[str]] = None,
) -> AnnotationPassResult:
    """
    Pass B: Annotation/document extraction.

    PHASE 1 STUB: Returns empty result.
    Phase 2+ will implement actual annotation capture.

    Args:
        source_path: Path to input image
        warnings: List to append warning messages to

    Returns:
        AnnotationPassResult (empty stub for Phase 1)
    """
    if warnings is None:
        warnings = []

    # Phase 1: Return stub
    logger.info("Pass B annotation extraction: STUB (not yet implemented)")

    return AnnotationPassResult(
        success=True,
        entity_count=0,
        error="",
        warnings=warnings,
        debug={"phase": 1, "status": "stub"},
        active=False,
    )


def extract_dual_pass(
    source_path: str,
    output_path: str,
    target_height_mm: float = 500.0,
    warnings: Optional[list[str]] = None,
) -> DualPassResult:
    """
    Dual-pass extraction coordinator.

    Runs Pass A (structural) and Pass B (annotation) and combines results.

    PHASE 1: Pass A only. Pass B returns empty stub.
    Phase 2+: Both passes will be active.

    Args:
        source_path: Path to input image
        output_path: Path for output DXF file
        target_height_mm: Target height for scaling
        warnings: List to append warning messages to

    Returns:
        DualPassResult with combined extraction results
    """
    if warnings is None:
        warnings = []

    logger.info(f"Dual-pass extraction: {source_path}")
    logger.info("  Phase 1 mode: Pass A active, Pass B stub")

    # Pass A: Structural geometry
    structural_result = extract_structural_pass(
        source_path=source_path,
        output_path=output_path,
        target_height_mm=target_height_mm,
        warnings=warnings,
    )

    if not structural_result.success:
        return DualPassResult(
            success=False,
            structural=structural_result,
            error=structural_result.error,
            warnings=warnings,
            pass_b_active=False,
        )

    # Pass B: Annotation (stub for Phase 1)
    annotation_result = extract_annotation_pass(
        source_path=source_path,
        warnings=warnings,
    )

    return DualPassResult(
        success=True,
        structural=structural_result,
        annotation=annotation_result,
        error="",
        warnings=warnings,
        pass_b_active=annotation_result.active,
    )
