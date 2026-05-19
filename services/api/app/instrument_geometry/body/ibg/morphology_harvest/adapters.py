"""
External System Adapters — Stubbed Integration Points
======================================================

Adapters for Phase 4 and Calibration systems.
For 1A: stubbed with graceful degradation.
Actual wiring deferred to 1B after paths and ownership are stable.

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AdapterResult:
    """
    Standard result from any adapter call.

    Attributes:
        available: Whether the adapter is wired and functional
        success: Whether the operation succeeded (if available)
        reason: Explanation if not available or failed
        data: Result data if successful
    """
    available: bool
    success: bool = False
    reason: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    @classmethod
    def not_available(cls, reason: str) -> "AdapterResult":
        """Create result for unavailable adapter."""
        return cls(available=False, success=False, reason=reason)

    @classmethod
    def ok(cls, data: Dict[str, Any]) -> "AdapterResult":
        """Create successful result."""
        return cls(available=True, success=True, data=data)

    @classmethod
    def failed(cls, reason: str) -> "AdapterResult":
        """Create failed result (adapter available but operation failed)."""
        return cls(available=True, success=False, reason=reason)


class BaseAdapter(ABC):
    """Base class for external system adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name for logging."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether the adapter is wired and functional."""
        pass

    @abstractmethod
    def check_availability(self) -> AdapterResult:
        """Check if the adapter is available and ready."""
        pass


class Phase4DimensionAssociationAdapter(BaseAdapter):
    """
    Adapter for Phase 4 dimension-to-geometry association.

    Phase 4 owns:
    - OCR text detection
    - Arrow/leader line detection
    - Dimension-to-geometry linking
    - LinkedDimensions output

    For 1A: STUBBED
    Actual wiring deferred to 1B.
    """

    def __init__(self):
        self._pipeline = None
        self._wire_attempted = False

    @property
    def name(self) -> str:
        return "Phase4DimensionAssociation"

    @property
    def is_available(self) -> bool:
        return self._pipeline is not None

    def check_availability(self) -> AdapterResult:
        """Check Phase 4 availability."""
        if self._wire_attempted:
            if self._pipeline:
                return AdapterResult.ok({"status": "wired"})
            else:
                return AdapterResult.not_available("not_wired_in_1A")

        # Attempt lazy import (will fail in 1A)
        self._wire_attempted = True
        try:
            # This import path would need adjustment for cross-service
            # Deferred to 1B when paths are stable
            # from services.blueprint_import.phase4.pipeline import BlueprintPipeline
            # self._pipeline = BlueprintPipeline()
            raise ImportError("Phase 4 wiring deferred to 1B")
        except ImportError as e:
            return AdapterResult.not_available(f"not_wired_in_1A: {e}")

    def process_pdf(
        self,
        pdf_path: str,
        page: int = 1,
    ) -> AdapterResult:
        """
        Process PDF through Phase 4 dimension association.

        Args:
            pdf_path: Path to PDF file
            page: Page number (1-indexed)

        Returns:
            AdapterResult with LinkedDimensions data if successful
        """
        availability = self.check_availability()
        if not availability.available:
            return availability

        try:
            result = self._pipeline.process(pdf_path, page=page)
            return AdapterResult.ok({
                "source_file": result.source_file,
                "dimensions": [d.to_dict() for d in result.dimensions],
                "unmatched_count": len(result.unmatched_texts),
                "association_rate": result.association_rate,
            })
        except Exception as e:
            return AdapterResult.failed(f"Phase 4 processing failed: {e}")

    def extract_dimension_values(
        self,
        pdf_path: str,
        page: int = 1,
    ) -> Dict[str, Optional[float]]:
        """
        Extract dimension values from PDF.

        Convenience method that returns dimension values
        mapped to canonical field names.

        Returns empty dict if Phase 4 unavailable.
        """
        result = self.process_pdf(pdf_path, page)

        if not result.success:
            return {}

        # Map Phase 4 dimensions to canonical fields
        dimensions = {}
        for dim in result.data.get("dimensions", []):
            label = dim.get("label", "").lower()
            value = dim.get("value_mm")

            if value is None:
                continue

            # Map to canonical terms per governance audit
            if "body" in label and "length" in label:
                dimensions["body_length_mm"] = value
            elif "lower" in label and "bout" in label:
                dimensions["lower_bout_width_mm"] = value
            elif "upper" in label and "bout" in label:
                dimensions["upper_bout_width_mm"] = value
            elif "waist" in label:
                dimensions["waist_width_mm"] = value
            elif "scale" in label and "length" in label:
                dimensions["scale_length_mm"] = value

        return dimensions


class CalibrationMetadataAdapter(BaseAdapter):
    """
    Adapter for calibration/scale detection.

    Calibration owns:
    - Scale detection (ruler, scale length, paper size)
    - mm/px conversion
    - CalibrationResult output

    For 1A: STUBBED
    Actual wiring deferred to 1B.
    """

    def __init__(self):
        self._calibrator = None
        self._wire_attempted = False

    @property
    def name(self) -> str:
        return "CalibrationMetadata"

    @property
    def is_available(self) -> bool:
        return self._calibrator is not None

    def check_availability(self) -> AdapterResult:
        """Check calibration availability."""
        if self._wire_attempted:
            if self._calibrator:
                return AdapterResult.ok({"status": "wired"})
            else:
                return AdapterResult.not_available("not_wired_in_1A")

        self._wire_attempted = True
        try:
            # Deferred to 1B
            # from services.blueprint_import.calibration.pixel_calibrator import PixelCalibrator
            # self._calibrator = PixelCalibrator()
            raise ImportError("Calibration wiring deferred to 1B")
        except ImportError as e:
            return AdapterResult.not_available(f"not_wired_in_1A: {e}")

    def calibrate_pdf(
        self,
        pdf_path: str,
        page: int = 1,
    ) -> AdapterResult:
        """
        Get calibration data for PDF.

        Args:
            pdf_path: Path to PDF file
            page: Page number (1-indexed)

        Returns:
            AdapterResult with calibration data if successful
        """
        availability = self.check_availability()
        if not availability.available:
            return availability

        try:
            result = self._calibrator.calibrate_from_pdf(pdf_path, page=page)
            return AdapterResult.ok({
                "method": result.method,
                "mm_per_px": result.mm_per_px,
                "confidence": result.confidence,
                "reference_used": result.reference_used,
            })
        except Exception as e:
            return AdapterResult.failed(f"Calibration failed: {e}")

    def get_calibration_method(self, pdf_path: str, page: int = 1) -> Optional[str]:
        """
        Get calibration method used for PDF.

        Returns None if calibration unavailable.
        """
        result = self.calibrate_pdf(pdf_path, page)

        if not result.success:
            return None

        return result.data.get("method")


class BodyGridAdapter(BaseAdapter):
    """
    Adapter for Body Grid morphology analysis.

    Body Grid owns:
    - ZoneId enum
    - BodyMorphologyClass enum
    - MorphologyDescriptor output
    - Centerline semantics
    - Coordinate normalization

    This adapter IS available in 1A (same service).
    """

    def __init__(self):
        self._analyzer = None

    @property
    def name(self) -> str:
        return "BodyGrid"

    @property
    def is_available(self) -> bool:
        # Body Grid is in the same service
        return self._get_analyzer() is not None

    def _get_analyzer(self):
        """Lazy init morphology analyzer."""
        if self._analyzer is None:
            try:
                from ..body_grid.morphology_descriptor import MorphologyAnalyzer
                self._analyzer = MorphologyAnalyzer()
            except ImportError:
                pass
        return self._analyzer

    def check_availability(self) -> AdapterResult:
        """Check Body Grid availability."""
        analyzer = self._get_analyzer()
        if analyzer:
            return AdapterResult.ok({"status": "available"})
        else:
            return AdapterResult.not_available("body_grid import failed")

    def analyze_evidence(self, body_evidence) -> AdapterResult:
        """
        Analyze BodyEvidence through morphology analyzer.

        Args:
            body_evidence: BodyEvidence instance

        Returns:
            AdapterResult with MorphologyDescriptor data
        """
        analyzer = self._get_analyzer()
        if not analyzer:
            return AdapterResult.not_available("body_grid not available")

        try:
            descriptor = analyzer.analyze(body_evidence)
            return AdapterResult.ok({
                "morphology_class": descriptor.variant_match.morphology_class.value,
                "confidence": descriptor.confidence,
                "centerline_x_mm": descriptor.centerline.x_mm,
                "asymmetry_score": descriptor.asymmetry.asymmetry_score,
            })
        except Exception as e:
            return AdapterResult.failed(f"Morphology analysis failed: {e}")

    def get_morphology_class(self, body_evidence) -> Optional[str]:
        """
        Get morphology class for body evidence.

        Returns None if analysis fails.
        """
        result = self.analyze_evidence(body_evidence)

        if not result.success:
            return None

        return result.data.get("morphology_class")


# Singleton instances for reuse
_phase4_adapter: Optional[Phase4DimensionAssociationAdapter] = None
_calibration_adapter: Optional[CalibrationMetadataAdapter] = None
_body_grid_adapter: Optional[BodyGridAdapter] = None


def get_phase4_adapter() -> Phase4DimensionAssociationAdapter:
    """Get Phase 4 adapter singleton."""
    global _phase4_adapter
    if _phase4_adapter is None:
        _phase4_adapter = Phase4DimensionAssociationAdapter()
    return _phase4_adapter


def get_calibration_adapter() -> CalibrationMetadataAdapter:
    """Get calibration adapter singleton."""
    global _calibration_adapter
    if _calibration_adapter is None:
        _calibration_adapter = CalibrationMetadataAdapter()
    return _calibration_adapter


def get_body_grid_adapter() -> BodyGridAdapter:
    """Get Body Grid adapter singleton."""
    global _body_grid_adapter
    if _body_grid_adapter is None:
        _body_grid_adapter = BodyGridAdapter()
    return _body_grid_adapter


def check_all_adapters() -> Dict[str, AdapterResult]:
    """
    Check availability of all adapters.

    Returns dict mapping adapter name to availability result.
    """
    return {
        "phase4": get_phase4_adapter().check_availability(),
        "calibration": get_calibration_adapter().check_availability(),
        "body_grid": get_body_grid_adapter().check_availability(),
    }
