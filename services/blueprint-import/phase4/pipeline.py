"""
Phase 4.0 End-to-End Pipeline
=============================

Complete pipeline from PDF blueprint to linked dimensions.

This module integrates:
- Phase 3.x vectorizer (OCR + geometry extraction)
- Phase 4.0 dimension linker (leader line association)

Author: Luthier's Toolbox
Version: 4.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete pipeline result."""
    source_file: str
    extraction_time_ms: float = 0.0
    linking_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # Extraction results
    dimensions_mm: tuple = (0.0, 0.0)
    features_count: Dict[str, int] = field(default_factory=dict)
    ocr_dimensions_found: int = 0

    # Linking results
    arrows_detected: int = 0
    dimensions_linked: int = 0
    unmatched_dimensions: int = 0
    association_rate: float = 0.0

    # Detailed results (optional)
    linked_dimensions: Optional[Any] = None
    extraction_result: Optional[Any] = None

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"Pipeline Result for {Path(self.source_file).name}:\n"
            f"  Body: {self.dimensions_mm[0]:.1f} x {self.dimensions_mm[1]:.1f} mm\n"
            f"  Features: {sum(self.features_count.values())} total\n"
            f"  OCR dimensions: {self.ocr_dimensions_found}\n"
            f"  Arrows detected: {self.arrows_detected}\n"
            f"  Dimensions linked: {self.dimensions_linked} ({self.association_rate:.0%})\n"
            f"  Unmatched: {self.unmatched_dimensions}\n"
            f"  Total time: {self.total_time_ms:.0f}ms"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        result = {
            'source_file': self.source_file,
            'timing': {
                'extraction_ms': self.extraction_time_ms,
                'linking_ms': self.linking_time_ms,
                'total_ms': self.total_time_ms
            },
            'extraction': {
                'dimensions_mm': self.dimensions_mm,
                'features_count': self.features_count,
                'ocr_dimensions_found': self.ocr_dimensions_found
            },
            'linking': {
                'arrows_detected': self.arrows_detected,
                'dimensions_linked': self.dimensions_linked,
                'unmatched_dimensions': self.unmatched_dimensions,
                'association_rate': self.association_rate
            }
        }

        if self.linked_dimensions:
            result['linked_dimensions'] = self.linked_dimensions.to_dict()

        return result


class BlueprintPipeline:
    """
    End-to-end blueprint processing pipeline.

    Usage:
        pipeline = BlueprintPipeline()
        result = pipeline.process("blueprint.pdf")

        for dim in result.linked_dimensions.dimensions:
            print(f"{dim.text_region.text} -> {dim.target_feature.category}")
    """

    def __init__(
        self,
        dpi: int = 300,
        enable_ocr: bool = True,
        debug_mode: bool = False
    ):
        """
        Initialize pipeline.

        Args:
            dpi: DPI for PDF rendering
            enable_ocr: Enable OCR extraction
            debug_mode: Enable debug/mock mode
        """
        self.dpi = dpi
        self.enable_ocr = enable_ocr
        self.debug_mode = debug_mode

        # Calculate mm per pixel
        self.mm_per_px = 25.4 / dpi

        # Lazy-load components
        self._vectorizer = None
        self._linker = None

    @property
    def vectorizer(self):
        """Lazy-load Phase 3 vectorizer."""
        if self._vectorizer is None:
            try:
                from vectorizer_phase3 import Phase3Vectorizer
                self._vectorizer = Phase3Vectorizer(
                    dpi=self.dpi,
                    enable_ocr=self.enable_ocr,
                    enable_primitives=True,
                    enable_scale_detection=True
                )
            except ImportError:
                logger.warning("Phase3Vectorizer not available")
                self._vectorizer = None
        return self._vectorizer

    @property
    def linker(self):
        """Lazy-load Phase 4 linker."""
        if self._linker is None:
            from .dimension_linker import DimensionLinker
            self._linker = DimensionLinker(
                mm_per_px=self.mm_per_px,
                debug_mode=self.debug_mode
            )
        return self._linker

    def process(
        self,
        pdf_path: str,
        instrument_type: Optional[str] = None,
        extraction_result: Optional[Any] = None
    ) -> PipelineResult:
        """
        Process a blueprint through the full pipeline.

        Args:
            pdf_path: Path to PDF blueprint
            instrument_type: Optional instrument type hint
            extraction_result: Optional pre-extracted result (skip extraction)

        Returns:
            PipelineResult with all processing data
        """
        start_time = time.time()
        source_file = str(pdf_path)

        logger.info(f"Processing blueprint: {Path(pdf_path).name}")

        # Step 1: Extraction (or use provided result)
        extraction_start = time.time()

        if extraction_result is None:
            extraction_result = self._extract(pdf_path, instrument_type)

        extraction_time = (time.time() - extraction_start) * 1000

        # Step 2: Dimension linking
        linking_start = time.time()
        linked = self.linker.process_blueprint(extraction_result)
        linking_time = (time.time() - linking_start) * 1000

        # Build result
        total_time = (time.time() - start_time) * 1000

        result = PipelineResult(
            source_file=source_file,
            extraction_time_ms=extraction_time,
            linking_time_ms=linking_time,
            total_time_ms=total_time,
            dimensions_mm=extraction_result.dimensions_mm,
            features_count={
                cat: len(items)
                for cat, items in extraction_result.contours_by_category.items()
            },
            ocr_dimensions_found=len(getattr(extraction_result, 'ocr_dimensions', [])),
            arrows_detected=linked.arrows_detected,
            dimensions_linked=len(linked.dimensions),
            unmatched_dimensions=len(linked.unmatched_texts),
            association_rate=linked.association_rate,
            linked_dimensions=linked,
            extraction_result=extraction_result
        )

        logger.info(f"Pipeline complete: {result.dimensions_linked} dimensions linked")

        return result

    def _extract(self, pdf_path: str, instrument_type: Optional[str]) -> Any:
        """Run extraction phase."""
        if self.vectorizer is None:
            raise RuntimeError(
                "Phase3Vectorizer not available. "
                "Provide extraction_result or install dependencies."
            )

        # Map string to enum if needed
        instr_enum = None
        if instrument_type:
            try:
                from vectorizer_phase3 import InstrumentType
                instr_enum = InstrumentType(instrument_type)
            except (ImportError, ValueError):
                logger.warning(f"Unknown instrument type: {instrument_type}")

        return self.vectorizer.extract(
            pdf_path,
            instrument_type=instr_enum,
            validate=False
        )

    def process_with_linking_only(
        self,
        extraction_result: Any
    ) -> PipelineResult:
        """
        Run only the linking phase on an existing extraction result.

        Useful for testing or re-processing.
        """
        return self.process(
            extraction_result.source_path,
            extraction_result=extraction_result
        )


def process_blueprint(
    pdf_path: str,
    dpi: int = 300,
    instrument_type: Optional[str] = None,
    debug_mode: bool = False
) -> PipelineResult:
    """
    Convenience function for processing a single blueprint.

    Args:
        pdf_path: Path to PDF blueprint
        dpi: DPI for rendering (default 300)
        instrument_type: Optional instrument hint
        debug_mode: Enable debug mode

    Returns:
        PipelineResult
    """
    pipeline = BlueprintPipeline(dpi=dpi, debug_mode=debug_mode)
    return pipeline.process(pdf_path, instrument_type=instrument_type)
