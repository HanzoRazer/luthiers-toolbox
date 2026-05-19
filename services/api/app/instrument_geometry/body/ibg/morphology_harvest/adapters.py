"""
External System Adapters — Canonical Pipeline Integration
==========================================================

Adapters for the canonical blueprint_reader.html pipeline.

1B-FIX-v2: Wired to canonical REST API endpoints, NOT Phase 4.

Canonical endpoints (from blueprint_reader.html):
- PDF → DXF: POST /api/blueprint/vectorize/async (raw edge extractor)
- Photo → DXF: POST /api/vectorizer/extract (edge to dxf)

Phase 4 is an incomplete R&D asset — NOT part of production pipeline.

Author: Production Shop
Date: 2026-05-17
Sprint: IBG Morphology Harvest 1B-FIX
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

import base64
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger(__name__)

# Canonical API endpoint
API_BASE = "https://luthiers-toolbox-production.up.railway.app"

# For local development, check if local server is running
LOCAL_API_BASE = "http://localhost:8000"


def _get_api_base() -> str:
    """Get API base URL, preferring local if available."""
    try:
        resp = requests.get(f"{LOCAL_API_BASE}/health", timeout=1)
        if resp.ok:
            return LOCAL_API_BASE
    except Exception:
        pass
    return API_BASE


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


class BlueprintVectorizerAdapter(BaseAdapter):
    """
    Adapter for the canonical blueprint vectorizer (PDF → DXF).

    This is the RAW EDGE EXTRACTOR from blueprint_reader.html.
    Endpoint: POST /api/blueprint/vectorize/async

    Returns SVG preview and DXF artifacts.
    """

    def __init__(self):
        self._api_base = None

    @property
    def name(self) -> str:
        return "BlueprintVectorizer"

    @property
    def is_available(self) -> bool:
        return True  # REST API is always available

    def check_availability(self) -> AdapterResult:
        """Check API availability."""
        if self._api_base is None:
            self._api_base = _get_api_base()
        return AdapterResult.ok({
            "status": "wired",
            "api_base": self._api_base,
            "endpoint": "/api/blueprint/vectorize/async",
        })

    def extract_from_pdf(
        self,
        pdf_path: str,
        target_height_mm: float = 500.0,
        min_contour_length_mm: float = 50.0,
        close_gaps_mm: float = 1.0,
        timeout_seconds: int = 600,
    ) -> AdapterResult:
        """
        Extract contours from PDF via canonical vectorizer.

        Args:
            pdf_path: Path to PDF file
            target_height_mm: Target height for normalization
            min_contour_length_mm: Minimum contour length filter
            close_gaps_mm: Gap closing distance
            timeout_seconds: Max time to wait for job

        Returns:
            AdapterResult with SVG/DXF artifacts and dimensions
        """
        if self._api_base is None:
            self._api_base = _get_api_base()

        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return AdapterResult.failed(f"PDF not found: {pdf_path}")

        try:
            # Step 1: Submit async job
            with open(pdf_file, 'rb') as f:
                files = {'file': (pdf_file.name, f, 'application/pdf')}
                data = {
                    'target_height_mm': str(target_height_mm),
                    'min_contour_length_mm': str(min_contour_length_mm),
                    'close_gaps_mm': str(close_gaps_mm),
                    'debug': 'false',
                }
                resp = requests.post(
                    f"{self._api_base}/api/blueprint/vectorize/async",
                    files=files,
                    data=data,
                    timeout=30,
                )

            if not resp.ok:
                return AdapterResult.failed(f"Submit failed: {resp.status_code} - {resp.text}")

            job_data = resp.json()
            job_id = job_data.get('job_id')
            if not job_id:
                return AdapterResult.failed("No job_id returned")

            logger.info(f"Blueprint job submitted: {job_id}")

            # Step 2: Poll for completion
            start_time = time.time()
            poll_interval = 5  # seconds

            while (time.time() - start_time) < timeout_seconds:
                time.sleep(poll_interval)

                status_resp = requests.get(
                    f"{self._api_base}/api/blueprint/vectorize/status/{job_id}",
                    timeout=10,
                )

                if not status_resp.ok:
                    continue

                status = status_resp.json()

                if status.get('status') == 'complete':
                    result = status.get('result', {})
                    return AdapterResult.ok({
                        "job_id": job_id,
                        "ok": result.get('ok', False),
                        "dimensions": result.get('dimensions', {}),
                        "artifacts": result.get('artifacts', {}),
                        "stage": result.get('stage'),
                        "warnings": result.get('warnings', []),
                    })

                if status.get('status') == 'failed':
                    return AdapterResult.failed(status.get('error', 'Job failed'))

            return AdapterResult.failed(f"Job timed out after {timeout_seconds}s")

        except requests.exceptions.Timeout:
            return AdapterResult.failed("Request timed out")
        except Exception as e:
            logger.exception("Blueprint extraction failed")
            return AdapterResult.failed(f"Extraction failed: {e}")

    def extract_dimension_values(
        self,
        pdf_path: str,
        page: int = 1,
        instrument_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract dimension values from PDF.

        Maps extracted dimensions to canonical field names.
        """
        result = self.extract_from_pdf(pdf_path)

        if not result.success:
            return {"error": result.reason, "dimensions": {}}

        data = result.data
        dimensions = {}

        # Get dimensions from extraction result
        dims = data.get("dimensions", {})
        if dims.get("width_mm") and dims.get("height_mm"):
            # Width is typically lower bout, height is body length
            dimensions["lower_bout_width_mm"] = dims["width_mm"]
            dimensions["body_length_mm"] = dims["height_mm"]

        return {
            "dimensions": dimensions,
            "raw_extraction": data,
            "confidence": 0.7 if data.get("ok") else 0.4,
            "svg_content": data.get("artifacts", {}).get("svg", {}).get("content"),
            "dxf_base64": data.get("artifacts", {}).get("dxf", {}).get("base64"),
        }


class PhotoVectorizerAdapter(BaseAdapter):
    """
    Adapter for the canonical photo vectorizer (image → DXF).

    This is the EDGE TO DXF from blueprint_reader.html.
    Endpoint: POST /api/vectorizer/extract

    Returns SVG preview and DXF artifacts.
    """

    def __init__(self):
        self._api_base = None

    @property
    def name(self) -> str:
        return "PhotoVectorizer"

    @property
    def is_available(self) -> bool:
        return True

    def check_availability(self) -> AdapterResult:
        """Check API availability."""
        if self._api_base is None:
            self._api_base = _get_api_base()
        return AdapterResult.ok({
            "status": "wired",
            "api_base": self._api_base,
            "endpoint": "/api/vectorizer/extract",
        })

    def extract_from_image(
        self,
        image_path: str,
        source_type: str = "auto",
        spec_name: Optional[str] = None,
    ) -> AdapterResult:
        """
        Extract contours from image via canonical vectorizer.

        Args:
            image_path: Path to image file
            source_type: "auto", "ai", "photo", "blueprint"
            spec_name: Optional instrument spec hint

        Returns:
            AdapterResult with SVG/DXF artifacts and dimensions
        """
        if self._api_base is None:
            self._api_base = _get_api_base()

        img_file = Path(image_path)
        if not img_file.exists():
            return AdapterResult.failed(f"Image not found: {image_path}")

        try:
            # Read and encode image
            with open(img_file, 'rb') as f:
                image_b64 = base64.b64encode(f.read()).decode('utf-8')

            # Call vectorizer
            payload = {
                "image_b64": image_b64,
                "source_type": source_type,
                "export_svg": True,
                "export_dxf": True,
            }
            if spec_name:
                payload["spec_name"] = spec_name

            resp = requests.post(
                f"{self._api_base}/api/vectorizer/extract",
                json=payload,
                timeout=120,
            )

            if not resp.ok:
                return AdapterResult.failed(f"Extract failed: {resp.status_code} - {resp.text}")

            data = resp.json()

            return AdapterResult.ok({
                "ok": data.get('ok', False),
                "body_width_mm": data.get('body_width_mm'),
                "body_height_mm": data.get('body_height_mm'),
                "contour_count": data.get('contour_count', 0),
                "scale_source": data.get('scale_source'),
                "svg_content": data.get('svg_content'),
                "svg_path_d": data.get('svg_path_d'),
                "dxf_base64": data.get('dxf_base64'),
                "warnings": data.get('warnings', []),
            })

        except requests.exceptions.Timeout:
            return AdapterResult.failed("Request timed out")
        except Exception as e:
            logger.exception("Photo extraction failed")
            return AdapterResult.failed(f"Extraction failed: {e}")


class CalibrationMetadataAdapter(BaseAdapter):
    """
    Adapter for calibration/scale detection.

    Note: The canonical vectorizer pipeline handles calibration internally
    and returns dimensions in mm. This adapter is for cases where we need
    to calibrate independently.

    Calibration is embedded in the vectorizer response via:
    - dimensions.width_mm / dimensions.height_mm (blueprint mode)
    - body_width_mm / body_height_mm (photo mode)
    """

    def __init__(self):
        self._api_base = None

    @property
    def name(self) -> str:
        return "CalibrationMetadata"

    @property
    def is_available(self) -> bool:
        return True

    def check_availability(self) -> AdapterResult:
        """Check availability - always available via vectorizer."""
        if self._api_base is None:
            self._api_base = _get_api_base()
        return AdapterResult.ok({
            "status": "wired",
            "note": "Calibration is embedded in vectorizer response",
        })

    def get_calibration_method(
        self,
        pdf_path: str,
        page: int = 1,
    ) -> Optional[str]:
        """
        Get calibration method - returns 'vectorizer_embedded'.

        The canonical pipeline handles calibration internally.
        """
        return "vectorizer_embedded"


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
_blueprint_adapter: Optional[BlueprintVectorizerAdapter] = None
_photo_adapter: Optional[PhotoVectorizerAdapter] = None
_calibration_adapter: Optional[CalibrationMetadataAdapter] = None
_body_grid_adapter: Optional[BodyGridAdapter] = None


def get_blueprint_adapter() -> BlueprintVectorizerAdapter:
    """Get blueprint vectorizer adapter singleton (PDF → DXF)."""
    global _blueprint_adapter
    if _blueprint_adapter is None:
        _blueprint_adapter = BlueprintVectorizerAdapter()
    return _blueprint_adapter


def get_photo_adapter() -> PhotoVectorizerAdapter:
    """Get photo vectorizer adapter singleton (image → DXF)."""
    global _photo_adapter
    if _photo_adapter is None:
        _photo_adapter = PhotoVectorizerAdapter()
    return _photo_adapter


# Backwards compatibility alias
def get_phase4_adapter() -> BlueprintVectorizerAdapter:
    """DEPRECATED: Use get_blueprint_adapter() instead."""
    logger.warning("get_phase4_adapter() is deprecated - use get_blueprint_adapter()")
    return get_blueprint_adapter()


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
        "blueprint_vectorizer": get_blueprint_adapter().check_availability(),
        "photo_vectorizer": get_photo_adapter().check_availability(),
        "calibration": get_calibration_adapter().check_availability(),
        "body_grid": get_body_grid_adapter().check_availability(),
    }
