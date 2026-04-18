"""
Photo Vectorizer v3.0 — Dual-Path Photographic & AI Instrument Outline Extractor
=================================================================================

Converts photographs AND AI-generated images of guitars/instruments into clean
SVG and DXF vector outlines. Designed for beginners and hobbyists who have a
concept photo or AI render but not CAD drawings.

Architecture — two extraction paths selected via `source_type`:

  Photo pipeline (12-stage, original v2 path):
    0. Dark background detection
    1. EXIF DPI extraction
    2. Input classification
    3. Perspective correction
    4. Background removal (GrabCut / rembg / SAM / threshold)
    5. Edge detection (Canny + Sobel + Laplacian fusion)
    6. Reference object detection
    7. Scale calibration
    8. Contour assembly with hierarchy + feature classification
    9. Manual correction hooks
    10. Confidence heatmap (debug)
    11. Export (SVG, DXF, JSON)
    12. Batch processing

  AI pipeline (4-stage, added in v3):
    1. AI image detection (_detect_ai_image)
    2. AI-optimized path extraction (_extract_ai_path)
    3. Shape classification (ExtractedShape)
    4. CAD-ready export (AIToCADExtractor)

Author: The Production Shop
Version: 3.0.0
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union
from xml.etree.ElementTree import Element, SubElement, ElementTree

import cv2
import numpy as np

from grid_classify import PhotoGridClassifier, merge_classifications

# Diff 2/3: BodyModel is imported at runtime inside methods to avoid circular
# imports, but declared here for TYPE_CHECKING so type annotations resolve.
if TYPE_CHECKING:
    from body_model import BodyModel

# ── Optional deps (graceful fallback) ──────────────────────────────────────────
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    from rembg import remove as rembg_remove, new_session as rembg_new_session
    REMBG_AVAILABLE = True
    # Cache rembg session at module level to avoid 255MB allocation per request
    # The session loads the U2Net model once and reuses it across all requests
    _REMBG_SESSION = None
except ImportError:
    REMBG_AVAILABLE = False
    _REMBG_SESSION = None


def get_rembg_session():
    """Get or create cached rembg session. Loads model once, reuses across requests."""
    global _REMBG_SESSION
    if _REMBG_SESSION is None and REMBG_AVAILABLE:
        import logging
        logging.getLogger(__name__).info("REMBG | Loading U2Net model (one-time, ~255MB)")
        _REMBG_SESSION = rembg_new_session("u2net")
        logging.getLogger(__name__).info("REMBG | Model loaded and cached")
    return _REMBG_SESSION

try:
    from segment_anything import sam_model_registry, SamPredictor
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False

try:
    from PIL import Image as PILImage
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Data Classes
# =============================================================================

class InputType(Enum):
    PHOTO = "photo"
    BLUEPRINT = "blueprint"
    SCAN = "scan"
    SVG = "svg"
    AI_GENERATED = "ai_generated"  # v3: AI-generated images (DALL-E, Midjourney, etc.)
    UNKNOWN = "unknown"


class BGRemovalMethod(Enum):
    GRABCUT = "grabcut"
    REMBG = "rembg"
    SAM = "sam"
    THRESHOLD = "threshold"
    AUTO = "auto"


class ScaleSource(Enum):
    USER_DIMENSION = "user_dimension"
    INSTRUMENT_SPEC = "instrument_spec"
    REFERENCE_OBJECT = "reference_object"
    MULTI_REFERENCE = "multi_reference"
    EXIF_DPI = "exif_dpi"
    FEATURE_SCALE = "feature_scale"
    ESTIMATED_RENDER_DPI = "estimated_render_dpi"
    ASSUMED_DPI = "assumed_dpi"
    NONE = "none"


class FeatureType(Enum):
    BODY_OUTLINE = "body_outline"
    PICKUP_ROUTE = "pickup_route"
    NECK_POCKET = "neck_pocket"
    CONTROL_CAVITY = "control_cavity"
    BRIDGE_ROUTE = "bridge_route"
    F_HOLE = "f_hole"
    SOUNDHOLE = "soundhole"
    ROSETTE = "rosette"
    JACK_ROUTE = "jack_route"
    BINDING = "binding"
    PURFLING = "purfling"
    UNKNOWN = "unknown"


class Unit(Enum):
    MM = "mm"
    INCH = "inch"
    CM = "cm"


@dataclass
class CalibrationResult:
    mm_per_px: float
    source: ScaleSource
    references: List[Dict[str, float]] = field(default_factory=list)
    confidence: float = 0.0
    message: str = ""


@dataclass
class BodyRegion:
    """Bounding box of the isolated instrument body (excludes neck/headstock)."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    neck_end_row: int
    max_body_width_px: int
    notes: List[str] = field(default_factory=list)
    # Protocol compliance: mm dimensions (populated after scale calibration)
    height_mm: Optional[float] = None
    width_mm: Optional[float] = None

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    @property
    def height_px(self) -> int:
        return self.height


@dataclass
class OrientationResult:
    """Result of instrument orientation detection."""
    orientation: str              # "portrait" | "landscape"
    coarse_angle: float           # 0 or 90 (CCW degrees)
    tilt_angle: float             # residual tilt after coarse rotation
    total_rotation: float         # coarse + tilt
    rotated_image: np.ndarray     # image after rotation
    original_shape: Tuple[int, int]  # (h, w) of original
    canvas_shape: Tuple[int, int]    # (h, w) after rotation
    inverse_matrix: Optional[np.ndarray] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class SplitResult:
    """Result of multi-instrument detection and splitting."""
    crops: List[Tuple[int, int, int, int]] = field(default_factory=list)
    split_axis: Optional[str] = None
    gap_positions: List[int] = field(default_factory=list)
    confidence: float = 0.0
    notes: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.crops)

    @property
    def is_multi(self) -> bool:
        return len(self.crops) > 1


@dataclass
class FeatureContour:
    points_px: np.ndarray
    points_mm: Optional[np.ndarray] = None
    feature_type: FeatureType = FeatureType.UNKNOWN
    confidence: float = 0.0
    parent_idx: int = -1
    child_indices: List[int] = field(default_factory=list)
    area_px: float = 0.0
    perimeter_px: float = 0.0
    circularity: float = 0.0
    aspect_ratio: float = 0.0
    solidity: float = 0.0
    bbox_px: Tuple[int, int, int, int] = (0, 0, 0, 0)
    hash_id: str = ""
    manually_corrected: bool = False
    grid_zone: Optional[str] = None
    grid_confidence: float = 0.0
    grid_notes: List[str] = field(default_factory=list)


@dataclass
class PhotoExtractionResult:
    source_path: str
    input_type: InputType = InputType.UNKNOWN
    output_dxf: Optional[str] = None
    output_svg: Optional[str] = None
    output_json: Optional[str] = None
    features: Dict[FeatureType, List[FeatureContour]] = field(default_factory=dict)
    body_contour: Optional[FeatureContour] = None
    body_dimensions_mm: Tuple[float, float] = (0.0, 0.0)
    body_dimensions_inch: Tuple[float, float] = (0.0, 0.0)
    scale_factor: float = 1.0
    calibration: Optional[CalibrationResult] = None
    bg_method_used: str = "none"
    perspective_corrected: bool = False
    dark_background_detected: bool = False
    assembly_method: str = "direct"
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    grid_reclassified: int = 0
    grid_overlay_path: Optional[str] = None
    debug_images: Dict[str, str] = field(default_factory=dict)

    contour_stage: Optional["ContourStageResult"] = None
    body_isolation: Optional[Any] = None
    body_model: Optional[Any] = None  # BodyModel from Diff 2/3 handoff
    geometry_coach_v2: Optional[Any] = None
    export_blocked: bool = False
    export_block_reason: Optional[str] = None

    def summary(self) -> Dict[str, Any]:
        feature_counts = {ft.value: len(c) for ft, c in self.features.items()}
        return {
            "source": self.source_path,
            "input_type": self.input_type.value,
            "dxf": self.output_dxf,
            "svg": self.output_svg,
            "body_dimensions_mm": self.body_dimensions_mm,
            "body_dimensions_inch": self.body_dimensions_inch,
            "feature_counts": feature_counts,
            "scale_source": self.calibration.source.value if self.calibration else "none",
            "bg_method": self.bg_method_used,
            "perspective_corrected": self.perspective_corrected,
            "dark_background_detected": self.dark_background_detected,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "export_blocked": self.export_blocked,
        }


@dataclass
class ContourScore:
    """Plausibility score for a single contour as body candidate."""
    contour_index: int
    score: float  # 0.0-1.0 composite plausibility
    completeness: float  # solidity (hull coverage)
    includes_neck: bool
    border_contact: bool
    dimension_plausibility: float  # 0.0-1.0 match vs family priors
    symmetry_score: float  # 0.0-1.0
    aspect_ratio_ok: bool
    ownership_score: float = 0.0
    vertical_coverage: float = 0.0
    neck_inclusion_score: float = 0.0
    issues: List[str] = field(default_factory=list)


@dataclass
class ContourStageResult:
    """Full typed record of Stage 8 contour processing."""
    feature_contours_pre_merge: List[FeatureContour] = field(default_factory=list)
    merge_result: Optional[MergeResult] = None
    feature_contours_post_merge: List[FeatureContour] = field(default_factory=list)
    body_contour_pre_grid: Optional[FeatureContour] = None
    feature_contours_post_grid: List[FeatureContour] = field(default_factory=list)
    body_contour_final: Optional[FeatureContour] = None
    contour_scores_pre: List[ContourScore] = field(default_factory=list)
    contour_scores_post: List[ContourScore] = field(default_factory=list)
    elected_source: str = "post_merge"  # "pre_merge", "post_merge", or "pre_merge_guarded"
    best_score: float = 0.0
    pre_merge_best_contour: Optional[FeatureContour] = None
    post_merge_best_contour: Optional[FeatureContour] = None
    export_blocked: bool = False
    block_reason: Optional[str] = None
    export_block_issues: List[str] = field(default_factory=list)
    export_block_score_breakdown: Dict[str, float] = field(default_factory=dict)
    recommended_next_action: Optional[str] = None
    ownership_score: Optional[float] = None
    ownership_ok: Optional[bool] = None
    diagnostics: Dict[str, Any] = field(default_factory=lambda: {"retry_attempts": []})


# Instrument specs for scale calibration and feature classification
INSTRUMENT_SPECS: Dict[str, Dict[str, Any]] = {
    "stratocaster": {"body": (406, 325), "features": {
        "pickup_route": [(85.0, 35.0)], "neck_pocket": (56.0, 76.0),
        "bridge_route": (89.0, 42.0), "control_cavity": (120.0, 80.0),
    }},
    "telecaster": {"body": (406, 325), "features": {
        "pickup_route": [(85.0, 35.0), (71.5, 38.0)], "neck_pocket": (56.0, 76.0),
        "bridge_route": (92.0, 25.0), "control_cavity": (100.0, 70.0),
    }},
    "les_paul": {"body": (450, 340), "features": {
        "pickup_route": [(71.5, 38.0), (71.5, 38.0)], "neck_pocket": (62.0, 82.0),
        "bridge_route": (120.0, 25.0), "control_cavity": (130.0, 90.0),
    }},
    "es335": {"body": (500, 420), "features": {
        "pickup_route": [(71.5, 38.0)], "f_hole": [(160.0, 45.0)],
        "bridge_route": (120.0, 25.0), "control_cavity": (120.0, 80.0),
    }},
    "dreadnought": {"body": (520, 400), "features": {
        "soundhole": (100.0, 100.0), "bridge_route": (180.0, 30.0),
    }},
    "smart_guitar": {"body": (444.5, 368.3), "features": {
        "pickup_route": [(85.0, 35.0)], "neck_pocket": (56.0, 76.0),
        "bridge_route": (100.0, 40.0), "control_cavity": (120.0, 80.0),
    }},
    "jumbo_archtop": {"body": (520, 430), "features": {
        "f_hole": [(160.0, 45.0)], "bridge_route": (130.0, 30.0),
        "pickup_route": [(71.5, 38.0)], "control_cavity": (120.0, 80.0),
    }},
    "reference_objects": {
        "us_quarter": (24.26, 24.26), "credit_card": (85.6, 53.98),
        "business_card": (88.9, 50.8),
    },
}


# =============================================================================
# AI Path — 4-Stage Pipeline for AI-Generated Images (v3)
# =============================================================================
# Philosophy: AI images are FICTION. The user provides TRUTH (specs, dimensions).
# The image gives us SHAPE. The user gives us SCALE.
# When they conflict, TRUTH wins.

# ── AI Path Spec Loader ─────────────────────────────────────────────────────
# Uses body_dimension_reference.json (14 specs) instead of INSTRUMENT_SPECS (7)

_AI_SPEC_CACHE: Optional[Dict[str, Dict[str, Any]]] = None

def _load_ai_specs() -> Dict[str, Dict[str, Any]]:
    """
    Load body_dimension_reference.json and convert to AI path format.

    Returns dict mapping spec_name -> {"body": (length_mm, width_mm), ...}
    Falls back to INSTRUMENT_SPECS if JSON not found.
    """
    global _AI_SPEC_CACHE
    if _AI_SPEC_CACHE is not None:
        return _AI_SPEC_CACHE

    json_path = Path(__file__).parent / "body_dimension_reference.json"
    if not json_path.exists():
        logger.warning(f"body_dimension_reference.json not found, using INSTRUMENT_SPECS")
        _AI_SPEC_CACHE = INSTRUMENT_SPECS
        return _AI_SPEC_CACHE

    try:
        with open(json_path) as f:
            raw = json.load(f)

        specs: Dict[str, Dict[str, Any]] = {}
        for name, data in raw.items():
            if name.startswith("_"):
                continue  # Skip _comment, _fields
            if not isinstance(data, dict):
                continue

            body_length = data.get("body_length_mm", 0)
            body_width = data.get("lower_bout_width_mm", 0)

            if body_length > 0 and body_width > 0:
                specs[name] = {
                    "body": (body_length, body_width),
                    "family": data.get("family", "unknown"),
                    "upper_bout_mm": data.get("upper_bout_width_mm"),
                    "waist_mm": data.get("waist_width_mm"),
                    "waist_y_norm": data.get("waist_y_norm"),
                }

        logger.info(f"Loaded {len(specs)} specs from body_dimension_reference.json")
        _AI_SPEC_CACHE = specs
        return _AI_SPEC_CACHE

    except Exception as e:
        logger.warning(f"Failed to load body_dimension_reference.json: {e}")
        _AI_SPEC_CACHE = INSTRUMENT_SPECS
        return _AI_SPEC_CACHE


def get_ai_spec(spec_name: str) -> Optional[Dict[str, Any]]:
    """Get spec for AI path, with case-insensitive lookup."""
    specs = _load_ai_specs()

    # Exact match
    if spec_name in specs:
        return specs[spec_name]

    # Case-insensitive match
    for k, v in specs.items():
        if k.lower() == spec_name.lower():
            return v

    return None

@dataclass
class ExtractedShape:
    """The shape extracted from an AI image (in pixel coordinates)."""
    contour: np.ndarray  # (N, 2) pixel coordinates
    area_px: float
    height_px: float
    width_px: float
    aspect_ratio: float
    solidity: float  # area / convex hull area (1.0 = perfect)
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float  # 0-1 how confident we are this is the intended shape

    def to_relative(self) -> np.ndarray:
        """Convert to normalized coordinates (0-1 range)."""
        if self.height_px == 0 or self.width_px == 0:
            return self.contour.copy()
        x_min = self.bbox[0]
        y_min = self.bbox[1]
        relative = self.contour.copy().astype(np.float32)
        relative[:, 0] = (relative[:, 0] - x_min) / self.width_px
        relative[:, 1] = (relative[:, 1] - y_min) / self.height_px
        return relative

    def scale_to(self, target_height_mm: float, target_width_mm: float) -> Tuple[np.ndarray, List[str]]:
        """
        Scale shape to target dimensions.

        Returns:
            Tuple of (scaled_contour, warnings)

        FIX: Scale to fit WITHIN both target dimensions (preserves aspect ratio).
        Uses the smaller scale factor so output fits within target bounds.
        """
        warnings: List[str] = []
        if self.height_px == 0 or self.width_px == 0:
            return self.contour.copy().astype(np.float32), ["Zero dimension, cannot scale"]

        # Calculate scale factors for both dimensions
        scale_h = target_height_mm / self.height_px
        scale_w = target_width_mm / self.width_px

        target_aspect = target_height_mm / target_width_mm if target_width_mm > 0 else 1.0
        current_aspect = self.height_px / self.width_px if self.width_px > 0 else 1.0

        # Use the SMALLER scale to fit within bounds (preserves aspect ratio)
        if abs(scale_h - scale_w) / max(scale_h, scale_w) > 0.05:
            # Aspect mismatch - fit to width constraint (common case: image wider than spec)
            scale = min(scale_h, scale_w)
            constrained_by = "width" if scale_w < scale_h else "height"
            actual_w = self.width_px * scale
            actual_h = self.height_px * scale
            warnings.append(
                f"Aspect mismatch: image={current_aspect:.2f}, spec={target_aspect:.2f}. "
                f"Scaled to fit {constrained_by} constraint: {actual_w:.1f}x{actual_h:.1f}mm"
            )
        else:
            # Uniform scale (aspect ratios close enough)
            scale = scale_h

        # Center the contour at origin before scaling
        x_min, y_min = self.bbox[0], self.bbox[1]
        centered = self.contour.astype(np.float32) - np.array([x_min, y_min], dtype=np.float32)
        scaled = centered * scale
        return scaled, warnings


@dataclass
class AIValidationResult:
    """Comparison between extracted shape and expected spec (aspect-only)."""
    passed: bool
    aspect_error_pct: float  # BUG FIX: Only aspect error, not fake h/w errors
    solidity_score: float
    overall_confidence: float
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "✓ PASSED" if self.passed else "✗ FAILED"
        lines = [
            f"\n{'='*50}",
            f"AI PATH VALIDATION: {status}",
            f"{'='*50}",
            f"Aspect error:   {self.aspect_error_pct:+.1f}%",
            f"Shape quality:  {self.solidity_score:.1%}",
            f"Confidence:     {self.overall_confidence:.1%}",
        ]
        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        if self.suggestions:
            lines.append("\nSuggestions:")
            for s in self.suggestions:
                lines.append(f"  💡 {s}")
        return "\n".join(lines)


class AIToCADExtractor:
    """
    Extract clean outlines from AI-generated images.

    Philosophy: AI images have clean edges but unreliable scale.
    We extract the SHAPE, not the TRUTH.

    4-stage pipeline:
      1. Otsu threshold (auto handles dark/light backgrounds)
      2. Morphological clean (remove noise)
      3. Largest contour (assumed instrument body)
      4. Simplify (remove redundant points)
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self._last_debug_image: Optional[np.ndarray] = None
        self._last_dark_bg: bool = False  # Track dark background detection

    def extract_shape(self, image_path: Union[str, Path]) -> ExtractedShape:
        """
        Extract the main shape from an AI-generated image.

        Assumes:
        - Image has a plain/contrasting background
        - Main subject is the largest connected component
        - Edges are clean enough for threshold-based extraction
        """
        img = self._load_image(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        original_h, original_w = img.shape[:2]

        # Step 1: Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # BUG FIX: Check if background is dark (sample border pixels)
        border_pixels = np.concatenate([
            gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]
        ])
        mean_border = float(np.mean(border_pixels))
        self._last_dark_bg = mean_border < 128

        # BUG FIX: Use correct threshold type based on background
        thresh_type = (
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
            if self._last_dark_bg
            else cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        _, binary = cv2.threshold(gray, 0, 255, thresh_type)

        if self.debug:
            self._last_debug_image = binary.copy()

        # Step 2: Clean up noise
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)

        # Step 3: Find all contours
        # BUG FIX: Use CHAIN_APPROX_SIMPLE instead of CHAIN_APPROX_NONE (more efficient)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            raise ValueError("No shapes found in image")

        # Step 4: Take the largest contour (assumed to be the instrument)
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        # Step 5: Simplify the contour (remove redundant points)
        epsilon = 0.002 * cv2.arcLength(largest, True)
        simplified = cv2.approxPolyDP(largest, epsilon, True)

        if len(simplified) < 3:
            simplified = largest

        # Step 6: Calculate metrics
        x, y, w, h = cv2.boundingRect(simplified)

        hull = cv2.convexHull(simplified)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0.0

        image_area = original_h * original_w
        area_ratio = area / image_area

        confidence = (
            0.40 * min(1.0, solidity / 0.95) +
            0.30 * min(1.0, area_ratio * 2) +
            0.30 * 1.0
        )
        confidence = min(1.0, confidence)

        points = simplified.reshape(-1, 2)

        logger.info(
            f"AIToCADExtractor: {len(points)} pts, {w}x{h}px, "
            f"solidity={solidity:.2f}, conf={confidence:.2f}, dark_bg={self._last_dark_bg}"
        )

        return ExtractedShape(
            contour=points,
            area_px=area,
            height_px=float(h),
            width_px=float(w),
            aspect_ratio=float(h) / float(w) if w > 0 else 1.0,
            solidity=solidity,
            bbox=(x, y, w, h),
            confidence=confidence
        )

    def _load_image(self, path: Union[str, Path]) -> Optional[np.ndarray]:
        """Load image, handling various formats."""
        path = Path(path)
        ext = path.suffix.lower()

        if ext == '.pdf':
            if not PYMUPDF_AVAILABLE:
                raise ImportError("PyMuPDF (fitz) required for PDF files")
            doc = fitz.open(str(path))
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            doc.close()
            return img

        img = cv2.imread(str(path))
        if img is None and PIL_AVAILABLE:
            pil_img = PILImage.open(path)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img

    def get_debug_image(self) -> Optional[np.ndarray]:
        """Return the debug image if debug mode was enabled."""
        return self._last_debug_image


class ShapeValidator:
    """Validate extracted shape against known instrument specs."""

    def __init__(self, tolerance_pct: float = 10.0):
        self.tolerance_pct = tolerance_pct

    def validate(self, shape: ExtractedShape, spec_body: Tuple[float, float]) -> AIValidationResult:
        """
        Compare extracted shape aspect ratio to spec.

        BUG FIX: Only computes aspect_error_pct (not fake h/w errors since we don't have scale).
        """
        warnings: List[str] = []
        suggestions: List[str] = []

        spec_height, spec_width = spec_body
        spec_aspect = spec_height / spec_width if spec_width > 0 else 1.0
        shape_aspect = shape.aspect_ratio

        aspect_error = abs(shape_aspect - spec_aspect) / spec_aspect * 100

        solidity_score = shape.solidity

        overall_confidence = (
            0.30 * max(0, 1 - aspect_error / 100) +
            0.40 * solidity_score +
            0.30 * shape.confidence
        )

        passed = aspect_error <= self.tolerance_pct and solidity_score > 0.85

        if aspect_error > self.tolerance_pct:
            warnings.append(
                f"Aspect ratio error {aspect_error:.1f}% exceeds tolerance {self.tolerance_pct}%"
            )
            suggestions.append(
                f"Expected {spec_height:.0f}x{spec_width:.0f}mm ({spec_aspect:.2f} aspect), "
                f"got {shape_aspect:.2f} aspect"
            )

        if solidity_score < 0.85:
            warnings.append(f"Shape quality low (solidity={solidity_score:.2f})")
            suggestions.append(
                "Shape may have holes or jagged edges. Try higher contrast background."
            )

        if shape.confidence < 0.7:
            warnings.append(f"Extraction confidence low ({shape.confidence:.1%})")
            suggestions.append("Try cropping image to just the instrument body.")

        return AIValidationResult(
            passed=passed,
            aspect_error_pct=aspect_error,
            solidity_score=solidity_score,
            overall_confidence=overall_confidence,
            warnings=warnings,
            suggestions=suggestions
        )


def _write_ai_svg(points: np.ndarray, output_path: str) -> None:
    """Write contour points to SVG file (AI path helper)."""
    if len(points) < 2:
        return
    x_min = float(points[:, 0].min()) - 10
    y_min = float(points[:, 1].min()) - 10
    w = float(points[:, 0].max()) - x_min + 20
    h = float(points[:, 1].max()) - y_min + 20

    path_d = "M " + " L ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in points) + " Z"
    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{x_min:.1f} {y_min:.1f} {w:.1f} {h:.1f}">\n'
        f'  <path d="{path_d}" fill="none" stroke="black" stroke-width="0.5"/>\n'
        f'</svg>'
    )
    Path(output_path).write_text(svg)


# =============================================================================
# Multi-Instrument Detection
# =============================================================================

class MultiInstrumentSplitter:
    """Detects whether an image contains multiple instruments and returns crop coordinates."""

    def __init__(self, bg_brightness_threshold: int = 190,
                 min_gap_width_pct: float = 0.03,
                 margin_px: int = 10, max_instruments: int = 4):
        self.bg_thresh = bg_brightness_threshold
        self.min_gap_pct = min_gap_width_pct
        self.margin = margin_px
        self.max_instruments = max_instruments

    def detect_and_split(self, image: np.ndarray) -> SplitResult:
        """Returns a SplitResult with crop boxes for each instrument."""
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        for axis in ("vertical", "horizontal"):
            result = self._find_gaps(gray, axis)
            if result.is_multi:
                logger.info(
                    f"MultiInstrumentSplitter: {result.count} instruments ({axis} split)")
                return result

        return SplitResult(
            crops=[(0, 0, w, h)], split_axis=None, confidence=0.9,
            notes=["No gap detected — single instrument"])

    def _find_gaps(self, gray: np.ndarray, axis: str) -> SplitResult:
        h, w = gray.shape[:2]
        dim = w if axis == "vertical" else h
        min_gap_px = max(3, int(dim * self.min_gap_pct))

        profile = gray.mean(axis=0) if axis == "vertical" else gray.mean(axis=1)
        is_bg = (profile >= self.bg_thresh).astype(np.uint8)

        gaps = self._find_runs(is_bg, value=1, min_length=min_gap_px)
        if not gaps:
            return SplitResult(crops=[], confidence=0.0)

        fg_regions = self._find_runs(is_bg, value=0, min_length=min_gap_px * 2)
        if len(fg_regions) < 2:
            return SplitResult(crops=[], confidence=0.0)

        fg_regions = fg_regions[:self.max_instruments]
        crops: List[Tuple[int, int, int, int]] = []
        for start, end in fg_regions:
            s = max(0, start - self.margin)
            e = min(dim - 1, end + self.margin)
            if axis == "vertical":
                crops.append((s, 0, e - s, h))
            else:
                crops.append((0, s, w, e - s))

        return SplitResult(
            crops=crops, split_axis=axis,
            gap_positions=[(s + e) // 2 for s, e in gaps],
            confidence=min(1.0, 0.5 + 0.1 * len(gaps)),
            notes=[f"{len(gaps)} gap(s) along {axis} axis, {len(crops)} instruments"])

    @staticmethod
    def _find_runs(arr: np.ndarray, value: int,
                   min_length: int) -> List[Tuple[int, int]]:
        """Return (start, end) index pairs for contiguous runs of `value`."""
        runs: List[Tuple[int, int]] = []
        in_run = False
        start = 0
        for i, v in enumerate(arr):
            if v == value and not in_run:
                in_run = True
                start = i
            elif v != value and in_run:
                in_run = False
                if (i - start) >= min_length:
                    runs.append((start, i - 1))
        if in_run and (len(arr) - start) >= min_length:
            runs.append((start, len(arr) - 1))
        return runs


# =============================================================================
# Stage 0 — Dark Background Detection
# =============================================================================

def detect_dark_background(image: np.ndarray, border_px: int = 20,
                           dark_threshold: float = 0.65) -> bool:
    """Detect dark background by sampling border pixels."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    h, w = gray.shape[:2]
    border_px = min(border_px, h // 4, w // 4)

    top = gray[:border_px, :].ravel()
    bottom = gray[h - border_px:, :].ravel()
    left = gray[border_px:h - border_px, :border_px].ravel()
    right = gray[border_px:h - border_px, w - border_px:].ravel()

    border_pixels = np.concatenate([top, bottom, left, right])
    dark_ratio = np.mean(border_pixels < 80)
    is_dark = dark_ratio >= dark_threshold
    logger.info(f"Dark background: {dark_ratio:.1%} dark border pixels -> {'DARK' if is_dark else 'LIGHT'}")
    return is_dark


class BackgroundTypeDetector:
    """Distinguishes solid-dark (safe to invert) from textured-dark (do NOT invert)."""

    def detect(self, image: np.ndarray,
               border_px: int = 60,
               dark_threshold: float = 0.65,
               texture_variance_threshold: float = 350.0) -> str:
        """Returns: 'solid_dark', 'textured_dark', 'solid_light', or 'gradient'."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        h, w = gray.shape[:2]
        border_px = min(border_px, h // 4, w // 4)

        top = gray[:border_px, :]
        bottom = gray[h - border_px:, :]
        left = gray[border_px:h - border_px, :border_px]
        right = gray[border_px:h - border_px, w - border_px:]

        border_pixels = np.concatenate([
            top.ravel(), bottom.ravel(), left.ravel(), right.ravel()])
        dark_ratio = float(np.mean(border_pixels < 80))

        if dark_ratio < dark_threshold:
            brightness_range = float(border_pixels.max() - border_pixels.min())
            bg_type = "gradient" if brightness_range > 80 else "solid_light"
            logger.info(f"BackgroundTypeDetector: dark_ratio={dark_ratio:.1%} -> {bg_type}")
            return bg_type

        # Dark background confirmed — check texture via border patch variance
        patches = [top, bottom, left.T, right.T]
        variances = [float(np.var(p)) for p in patches if p.size > 0]
        mean_variance = float(np.mean(variances)) if variances else 0.0

        bg_type = "solid_dark" if mean_variance < texture_variance_threshold else "textured_dark"
        logger.info(
            f"BackgroundTypeDetector: dark_ratio={dark_ratio:.1%}, "
            f"border_variance={mean_variance:.0f} -> {bg_type}")
        return bg_type


# =============================================================================
# Stage 1 — EXIF DPI Extraction
# =============================================================================

class EXIFExtractor:
    @staticmethod
    def get_dpi(image_path: Path) -> Optional[float]:
        if not PIL_AVAILABLE:
            return None
        try:
            img = PILImage.open(image_path)
            exif = img._getexif()
            if not exif:
                return None
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'XResolution':
                    if isinstance(value, tuple):
                        return float(value[0]) / float(value[1])
                    return float(value)
            return None
        except Exception as e:
            logger.debug(f"EXIF extraction failed: {e}")
            return None


# =============================================================================
# Stage 2 — Input Classification
# =============================================================================

class InputClassifier:
    def classify(self, image: np.ndarray) -> Tuple[InputType, float, Dict[str, Any]]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        total = gray.size
        white_ratio = float(np.sum(gray > 240)) / total
        dark_ratio = float(np.sum(gray < 30)) / total
        color_variance = float(np.var(image.astype(np.float32)))
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0)) / total

        metadata = {
            "white_ratio": white_ratio, "dark_ratio": dark_ratio,
            "color_variance": color_variance, "edge_density": edge_density,
        }

        if white_ratio > 0.75 and edge_density > 0.01:
            return InputType.BLUEPRINT, min(1.0, white_ratio * edge_density * 100), metadata
        if white_ratio < 0.40 and color_variance > 800:
            return InputType.PHOTO, min(1.0, (1 - white_ratio) * color_variance / 1000), metadata
        if white_ratio > 0.50:
            if color_variance > 1500:
                return InputType.PHOTO, 0.65, metadata
            return InputType.SCAN, 0.6, metadata
        return InputType.PHOTO, 0.5, metadata


# =============================================================================
# Stage 3 — Perspective Correction
# =============================================================================

class PerspectiveCorrector:
    """Detect dominant quadrilateral and warp to rectangle."""

    def correct(self, image: np.ndarray) -> Tuple[np.ndarray, bool]:
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate to close gaps
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return image, False

        # Find largest contour that approximates to 4 points
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for cnt in contours[:5]:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4 and cv2.contourArea(approx) > (w * h * 0.15):
                pts = approx.reshape(4, 2).astype(np.float32)
                # Order: top-left, top-right, bottom-right, bottom-left
                rect = self._order_points(pts)
                width_a = np.linalg.norm(rect[2] - rect[3])
                width_b = np.linalg.norm(rect[1] - rect[0])
                height_a = np.linalg.norm(rect[1] - rect[2])
                height_b = np.linalg.norm(rect[0] - rect[3])
                max_w = int(max(width_a, width_b))
                max_h = int(max(height_a, height_b))
                if max_w < 100 or max_h < 100:
                    continue
                dst = np.array([
                    [0, 0], [max_w - 1, 0],
                    [max_w - 1, max_h - 1], [0, max_h - 1]
                ], dtype=np.float32)
                M = cv2.getPerspectiveTransform(rect, dst)
                warped = cv2.warpPerspective(image, M, (max_w, max_h))
                logger.info(f"Perspective corrected: {w}x{h} -> {max_w}x{max_h}")
                return warped, True

        return image, False

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        d = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(d)]
        rect[3] = pts[np.argmax(d)]
        return rect


# =============================================================================
# Stage 4 — Background Removal
# =============================================================================

class BackgroundRemover:
    def __init__(self, sam_checkpoint: Optional[str] = None):
        self._sam_predictor = None
        if SAM_AVAILABLE and sam_checkpoint and Path(sam_checkpoint).exists():
            try:
                sam = sam_model_registry["vit_h"](checkpoint=sam_checkpoint)
                self._sam_predictor = SamPredictor(sam)
            except Exception as e:
                logger.warning(f"SAM load failed: {e}")

    def remove(self, image: np.ndarray, method: BGRemovalMethod = BGRemovalMethod.AUTO,
               hint_rect: Optional[Tuple[int, int, int, int]] = None,
               is_dark_bg: bool = False,
               ) -> Tuple[np.ndarray, np.ndarray, str]:
        """Returns (foreground, alpha_mask, method_used)."""
        if method == BGRemovalMethod.AUTO:
            if self._sam_predictor is not None:
                method = BGRemovalMethod.SAM
            elif REMBG_AVAILABLE:
                method = BGRemovalMethod.REMBG
            else:
                method = BGRemovalMethod.GRABCUT

        try:
            if method == BGRemovalMethod.SAM and self._sam_predictor is not None:
                fg, mask = self._sam_remove(image)
                return fg, mask, "sam"
            elif method == BGRemovalMethod.REMBG and REMBG_AVAILABLE:
                fg, mask = self._rembg_remove(image)
                return fg, mask, "rembg"
            elif method == BGRemovalMethod.THRESHOLD:
                fg, mask = self._threshold_remove(image, is_dark_bg)
                return fg, mask, "threshold"
            else:
                fg, mask = self._grabcut_remove(image, hint_rect)
                return fg, mask, "grabcut"
        except Exception as e:
            logger.warning(f"{method.value} failed: {e}, falling back to threshold")
            fg, mask = self._threshold_remove(image, is_dark_bg)
            return fg, mask, "threshold_fallback"

    def _grabcut_remove(self, image: np.ndarray,
                        hint_rect: Optional[Tuple[int, int, int, int]] = None,
                        ) -> Tuple[np.ndarray, np.ndarray]:
        h, w = image.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        if hint_rect:
            rect = hint_rect
        else:
            mx, my = int(w * 0.08), int(h * 0.08)
            rect = (mx, my, w - 2 * mx, h - 2 * my)

        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(image, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
        except cv2.error:
            return self._threshold_remove(image)

        fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg = cv2.bitwise_and(image, image, mask=fg_mask)
        return fg, fg_mask

    def _rembg_remove(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        from PIL import Image as _PIL
        import io
        pil_img = _PIL.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        buf.seek(0)
        # Use cached session to avoid reloading the 255MB model on each request
        session = get_rembg_session()
        result_bytes = rembg_remove(buf.read(), session=session)
        result_pil = _PIL.open(io.BytesIO(result_bytes)).convert('RGBA')
        result_np = np.array(result_pil)
        alpha = result_np[:, :, 3]
        fg_mask = (alpha > 128).astype(np.uint8) * 255
        bgr = cv2.cvtColor(result_np[:, :, :3], cv2.COLOR_RGB2BGR)
        fg = cv2.bitwise_and(bgr, bgr, mask=fg_mask)
        return fg, fg_mask

    def _sam_remove(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self._sam_predictor.set_image(rgb)
        h, w = image.shape[:2]
        point_coords = np.array([[w // 2, h // 2]])
        point_labels = np.array([1])
        masks, scores, _ = self._sam_predictor.predict(
            point_coords=point_coords, point_labels=point_labels, multimask_output=True)
        best = masks[np.argmax(scores)]
        fg_mask = (best * 255).astype(np.uint8)
        fg = cv2.bitwise_and(image, image, mask=fg_mask)
        return fg, fg_mask

    def _threshold_remove(self, image: np.ndarray,
                          is_dark_bg: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_val = float(gray.mean())
        if is_dark_bg or mean_val < 80:
            _, mask = cv2.threshold(gray, int(mean_val * 1.5), 255, cv2.THRESH_BINARY)
        else:
            _, mask = cv2.threshold(gray, int(mean_val * 0.7), 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg = cv2.bitwise_and(image, image, mask=mask)
        return fg, mask


# =============================================================================
# Stage 4.5 — Body Isolation
# =============================================================================

class BodyIsolator:
    """Identifies the body region by profiling row-wise instrument pixel width."""

    def __init__(self, body_width_min_pct: float = 0.40,
                 smooth_window: int = 15,
                 use_adaptive: bool = False):
        self.body_width_min = body_width_min_pct
        self.smooth_window = smooth_window
        self.use_adaptive = use_adaptive

    def isolate(self, image: np.ndarray,
                fg_mask: Optional[np.ndarray] = None,
                original_image: Optional[np.ndarray] = None) -> BodyRegion:
        """Analyse the image and return a BodyRegion for the guitar body.

        Priority for row-width profiling:
          1. fg_mask (most reliable — BG already removed)
          2. original_image (pre-inversion) dark pixel threshold
          3. image (current, possibly inverted) — warns if used on inverted image
        """
        h, w = image.shape[:2]
        notes: List[str] = []

        if fg_mask is not None and np.sum(fg_mask > 0) > (h * w * 0.05):
            row_widths = np.sum(fg_mask > 0, axis=1).astype(float)
            source = "fg_mask"
            notes.append("Row widths from fg_mask (Stage 4 output)")
        elif original_image is not None:
            gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY) \
                if len(original_image.shape) == 3 else original_image
            row_widths = np.sum(gray < 150, axis=1).astype(float)
            source = "original_image"
            notes.append("Row widths from pre-inversion image")
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            mean_val = float(gray.mean())
            row_widths = np.sum(gray < 150, axis=1).astype(float)
            source = "image_raw"
            if mean_val > 160:
                notes.append("Warning: using raw (possibly inverted) image for body isolation")
            else:
                notes.append("Row widths from raw image threshold")

        kernel = np.ones(self.smooth_window) / self.smooth_window
        smoothed = np.convolve(row_widths, kernel, mode='same')

        if self.use_adaptive:
            body_min_px = adaptive_body_threshold(smoothed)
            notes.append(f"Using adaptive body threshold: {body_min_px:.0f}px")
        else:
            body_min_px = w * self.body_width_min
        body_rows = np.where(smoothed >= body_min_px)[0]

        if len(body_rows) == 0:
            body_start = int(h * 0.45)
            body_end = int(h * 0.97)
            confidence = 0.30
            notes.append(f"No body rows at {body_min_px:.0f}px threshold (source={source}) — fallback")
        else:
            body_start = int(body_rows[0])
            body_end = int(body_rows[-1])
            confidence = min(1.0, 0.50 + 0.005 * len(body_rows))
            notes.append(
                f"Body rows {body_start}-{body_end} "
                f"({len(body_rows)} rows >= {body_min_px:.0f}px, source={source})")

        body_h = body_end - body_start
        max_body_w = int(smoothed[body_start:body_end].max()) if body_h > 0 else 0

        # Column extent — use best available source
        if fg_mask is not None and source == "fg_mask":
            body_strip = fg_mask[body_start:body_end, :]
        else:
            ref = original_image if original_image is not None else image
            gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY) if len(ref.shape) == 3 else ref
            body_strip = (gray[body_start:body_end, :] < 150).astype(np.uint8)

        col_widths = np.sum(body_strip > 0, axis=0)
        body_cols = np.where(col_widths > 0)[0]
        x_start = int(body_cols[0]) if len(body_cols) else 0
        x_end = int(body_cols[-1]) if len(body_cols) else w

        logger.info(
            f"BodyIsolator: body region x={x_start}-{x_end}, "
            f"y={body_start}-{body_end}, "
            f"size={x_end - x_start}x{body_h}px, conf={confidence:.2f}, src={source}")

        return BodyRegion(
            x=x_start, y=body_start, width=x_end - x_start, height=body_h,
            confidence=confidence, neck_end_row=body_start,
            max_body_width_px=max_body_w, notes=notes)


# =============================================================================
# Stage 5a — Gated Adaptive Close (Patch 14)
# =============================================================================

# Constants for GatedAdaptiveCloser
_GAC_TARGET_BRIDGE_MM = 6.0
_GAC_MIN_KERNEL = 11
_GAC_MAX_KERNEL = 25
_GAC_EXTERIOR_RING_PX = 15
_GAC_INTERIOR_KERNEL = 5


@dataclass
class GatedCloseResult:
    """Diagnostic output from GatedAdaptiveCloser."""
    exterior_kernel_size: int
    interior_kernel_size: int
    bridge_distance_mm: float
    body_region_used: bool
    contour_count_before: int
    contour_count_after: int
    notes: List[str]


class GatedAdaptiveCloser:
    """
    Apply morphological close with a large kernel on the body silhouette
    boundary and a small kernel on interior features.

    Closes cutaway gaps in the body perimeter without merging
    interior features (f-holes, soundhole, pickup routes) into the body.
    """

    def __init__(
        self,
        target_bridge_mm: float = _GAC_TARGET_BRIDGE_MM,
        min_kernel: int = _GAC_MIN_KERNEL,
        max_kernel: int = _GAC_MAX_KERNEL,
        ring_px: int = _GAC_EXTERIOR_RING_PX,
        interior_kernel: int = _GAC_INTERIOR_KERNEL,
    ):
        self.target_bridge_mm = target_bridge_mm
        self.min_kernel = min_kernel
        self.max_kernel = max_kernel
        self.ring_px = ring_px
        self.interior_kernel = interior_kernel

    def compute_kernel_size(self, mpp: float) -> int:
        """Compute adaptive exterior kernel size targeting self.target_bridge_mm gap bridging."""
        if mpp <= 0:
            return self.min_kernel
        raw = self.target_bridge_mm / mpp
        k = int(raw / 2) * 2 + 1
        return max(self.min_kernel, min(self.max_kernel, k))

    def close(
        self,
        edge_image: np.ndarray,
        fg_mask: np.ndarray,
        mpp: float,
        body_region: Optional[BodyRegion] = None,
        input_type_str: str = "photo",
    ) -> Tuple[np.ndarray, GatedCloseResult]:
        """Apply gated adaptive morphological close to an edge image."""
        h, w = edge_image.shape[:2]

        # For blueprints/SVG: use small kernel only
        if input_type_str in ("blueprint", "svg"):
            k = np.ones((self.interior_kernel, self.interior_kernel), np.uint8)
            result = cv2.morphologyEx(edge_image, cv2.MORPH_CLOSE, k, iterations=2)
            result = cv2.bitwise_and(result, result, mask=fg_mask)
            return result, GatedCloseResult(
                exterior_kernel_size=self.interior_kernel,
                interior_kernel_size=self.interior_kernel,
                bridge_distance_mm=self.interior_kernel * mpp,
                body_region_used=False,
                contour_count_before=self._count_contours(edge_image),
                contour_count_after=self._count_contours(result),
                notes=["Blueprint input -- small kernel only"])

        ext_k_size = self.compute_kernel_size(mpp)
        bridge_mm = ext_k_size * mpp

        cnts_before = self._count_contours(edge_image)
        notes = [
            f"mpp={mpp:.4f} -> exterior kernel {ext_k_size}x{ext_k_size} "
            f"(bridges {bridge_mm:.1f}mm)",
            f"Interior kernel: {self.interior_kernel}x{self.interior_kernel}",
        ]

        # Build body-region-restricted fg_mask
        if body_region is not None:
            body_mask = np.zeros((h, w), np.uint8)
            by = body_region.y
            bh = body_region.height
            body_mask[max(0, by):min(h, by + bh), :] = 255
            fg_body = cv2.bitwise_and(fg_mask, fg_mask, mask=body_mask)
            notes.append(f"Body region restricted to rows {by}-{by + bh}")
        else:
            fg_body = fg_mask.copy()
            notes.append("No body_region supplied -- using full fg_mask")

        body_region_used = body_region is not None

        # Extract exterior boundary ring
        ring_kernel = np.ones(
            (self.ring_px * 2 + 1, self.ring_px * 2 + 1), np.uint8)
        eroded_body = cv2.erode(fg_body, ring_kernel)
        exterior_ring = cv2.subtract(fg_body, eroded_body)

        # Add fg_mask thin boundary as exterior signal
        thin_k = np.ones((3, 3), np.uint8)
        fg_boundary = cv2.subtract(fg_body, cv2.erode(fg_body, thin_k))
        exterior_ring = cv2.bitwise_or(exterior_ring, fg_boundary)

        # Split edge_image into exterior and interior
        not_exterior = cv2.bitwise_not(exterior_ring)
        exterior_edges = cv2.bitwise_and(edge_image, edge_image, mask=exterior_ring)
        interior_edges = cv2.bitwise_and(edge_image, edge_image, mask=not_exterior)

        # Apply different close kernels
        k_ext = np.ones((ext_k_size, ext_k_size), np.uint8)
        k_int = np.ones((self.interior_kernel, self.interior_kernel), np.uint8)

        exterior_closed = cv2.morphologyEx(
            exterior_edges, cv2.MORPH_CLOSE, k_ext, iterations=2)
        interior_closed = cv2.morphologyEx(
            interior_edges, cv2.MORPH_CLOSE, k_int, iterations=2)

        # Combine and mask to fg
        combined = cv2.bitwise_or(exterior_closed, interior_closed)
        combined = cv2.bitwise_and(combined, combined, mask=fg_mask)

        # Final light cleanup pass
        k_clean = np.ones((2, 2), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_clean)

        cnts_after = self._count_contours(combined)
        notes.append(
            f"Contours: {cnts_before} -> {cnts_after} "
            f"({'unified' if cnts_after < cnts_before else 'unchanged'})")

        logger.info(
            f"GatedAdaptiveCloser: ext={ext_k_size}x{ext_k_size} "
            f"({bridge_mm:.1f}mm), int={self.interior_kernel}x{self.interior_kernel}, "
            f"contours {cnts_before}->{cnts_after}")

        return combined, GatedCloseResult(
            exterior_kernel_size=ext_k_size,
            interior_kernel_size=self.interior_kernel,
            bridge_distance_mm=bridge_mm,
            body_region_used=body_region_used,
            contour_count_before=cnts_before,
            contour_count_after=cnts_after,
            notes=notes,
        )

    @staticmethod
    def _count_contours(edge_image: np.ndarray) -> int:
        cnts, _ = cv2.findContours(
            edge_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return len([c for c in cnts if cv2.contourArea(c) > 500])


# =============================================================================
# Stage 5 — Edge Detection (Multi-method fusion)
# =============================================================================

class PhotoEdgeDetector:
    """Fuses Canny, Sobel, and Laplacian edges for robust outline extraction."""

    def __init__(self):
        self._gated_closer = GatedAdaptiveCloser()

    def detect(self, fg_image: np.ndarray, alpha_mask: np.ndarray,
               canny_sigma: float = 0.33, close_kernel: int = 5,
               input_type: Optional[str] = None,
               mpp: Optional[float] = None,
               body_region: Optional[BodyRegion] = None) -> np.ndarray:
        gray = cv2.cvtColor(fg_image, cv2.COLOR_BGR2GRAY) if len(fg_image.shape) == 3 else fg_image

        # Apply mask
        gray = cv2.bitwise_and(gray, gray, mask=alpha_mask)

        # Reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)

        # Canny (auto threshold)
        median = float(np.median(blurred[alpha_mask > 0])) if np.any(alpha_mask > 0) else 128
        lower = int(max(0, (1.0 - canny_sigma) * median))
        upper = int(min(255, (1.0 + canny_sigma) * median))
        canny = cv2.Canny(blurred, lower, upper)

        # Sobel magnitude
        sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        sobel_mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
        sobel_mag = np.clip(sobel_mag / sobel_mag.max() * 255, 0, 255).astype(np.uint8) if sobel_mag.max() > 0 else np.zeros_like(gray)
        _, sobel_bin = cv2.threshold(sobel_mag, 50, 255, cv2.THRESH_BINARY)

        # Laplacian
        lap = cv2.Laplacian(blurred, cv2.CV_64F, ksize=3)
        lap = np.abs(lap)
        lap = np.clip(lap / lap.max() * 255, 0, 255).astype(np.uint8) if lap.max() > 0 else np.zeros_like(gray)
        _, lap_bin = cv2.threshold(lap, 40, 255, cv2.THRESH_BINARY)

        # Fuse: OR all three
        combined = cv2.bitwise_or(canny, sobel_bin)
        combined = cv2.bitwise_or(combined, lap_bin)

        # Mask to alpha region
        combined = cv2.bitwise_and(combined, combined, mask=alpha_mask)

        # Close gaps — use gated adaptive closer when mpp is available
        if mpp is not None and mpp > 0:
            combined, close_info = self._gated_closer.close(
                combined, alpha_mask,
                mpp=mpp,
                body_region=body_region,
                input_type_str=input_type or "photo",
            )
            for note in close_info.notes:
                logger.debug(f"  GatedClose: {note}")
        else:
            if close_kernel > 0:
                k = np.ones((close_kernel, close_kernel), np.uint8)
                combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k, iterations=2)
            k_small = np.ones((2, 2), np.uint8)
            combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_small)

        logger.info(f"Edge detection: {cv2.countNonZero(combined)} edge pixels")
        return combined


# =============================================================================
# Stage 6 — Reference Object Detection
# =============================================================================

# Coin size + color sanity constants
MAX_COIN_DIAMETER_FRACTION = 0.15   # of min(image_w, image_h)
MIN_COIN_DIAMETER_PX = 12           # below this it's noise
MAX_COIN_SATURATION = 40            # HSV S channel; grey coins < 40
WARM_HUE_LOW = 5                    # HSV H (0-179); gold/wood/amber range
WARM_HUE_HIGH = 35

# Coin edge-sharpness constants
MIN_COIN_EDGE_SHARPNESS = 25.0      # Sobel magnitude on perimeter ring
COIN_PERIMETER_WIDTH = 4            # annular ring half-width in pixels

# Known coin diameters (mm) for size-match scoring
KNOWN_COIN_DIAMETERS_MM = [24.26, 21.21, 19.05, 17.91]  # quarter, nickel, penny, dime


@dataclass
class CoinCandidate:
    """Scored coin detection candidate."""
    x: int = 0
    y: int = 0
    r: int = 0
    sharpness: float = 0.0
    circularity: float = 0.0
    size_score: float = 0.0
    position_score: float = 1.0
    total_score: float = 0.0


def _compute_coin_sharpness(gray: np.ndarray, cx: int, cy: int, r: int,
                            ring_width: int = COIN_PERIMETER_WIDTH) -> float:
    """Compute edge sharpness on the annular ring around a circle's perimeter.

    Real coins have a machined raised rim that produces a strong Sobel response.
    Hardware (tuning pegs, knobs) has softer edges.
    """
    h, w = gray.shape[:2]
    y_coords, x_coords = np.ogrid[:h, :w]
    dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    ring_mask = ((dist >= r - ring_width) & (dist <= r + ring_width)).astype(np.uint8)

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(sobelx ** 2 + sobely ** 2)

    ring_pixels = mag[ring_mask > 0]
    return float(ring_pixels.mean()) if ring_pixels.size > 0 else 0.0


def score_coin_candidates(
    circles: np.ndarray,
    image: np.ndarray,
    gray: Optional[np.ndarray] = None,
    rough_mpp: float = 0.27,
) -> List[CoinCandidate]:
    """Score and rank coin candidates on sharpness, circularity, size match, and position."""
    if gray is None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    h, w = gray.shape[:2]

    candidates = []
    for entry in circles:
        x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
        c = CoinCandidate(x=x, y=y, r=r)

        # Edge sharpness
        c.sharpness = _compute_coin_sharpness(gray, x, y, r)

        # Circularity from binarised patch
        y0, y1 = max(0, y - r), min(h, y + r)
        x0, x1 = max(0, x - r), min(w, x + r)
        patch = gray[y0:y1, x0:x1]
        if patch.size > 0:
            _, bin_patch = cv2.threshold(patch, 0, 255,
                                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            cnts, _ = cv2.findContours(bin_patch, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if cnts:
                cnt = max(cnts, key=cv2.contourArea)
                area = cv2.contourArea(cnt)
                peri = cv2.arcLength(cnt, True)
                c.circularity = (4 * np.pi * area / (peri ** 2)) if peri > 0 else 0.0

        # Size match to known coin diameters
        diam_mm = 2 * r * rough_mpp
        size_diffs = [abs(diam_mm - known) / known for known in KNOWN_COIN_DIAMETERS_MM]
        best_diff = min(size_diffs)
        c.size_score = max(0.0, 1.0 - best_diff * 4)

        # Position (penalise instrument-centre locations)
        in_centre_x = (0.25 * w) < x < (0.75 * w)
        in_centre_y = (0.25 * h) < y < (0.75 * h)
        c.position_score = 0.6 if (in_centre_x and in_centre_y) else 1.0

        # Weighted total
        c.total_score = (
            0.35 * min(1.0, c.sharpness / 60.0) +
            0.30 * c.circularity +
            0.20 * c.size_score +
            0.15 * c.position_score
        )
        candidates.append(c)

    candidates.sort(key=lambda c: c.total_score, reverse=True)
    return candidates


def select_best_coin(
    circles: np.ndarray,
    image: np.ndarray,
    gray: Optional[np.ndarray] = None,
    min_score: float = 0.25,
) -> Optional[Dict[str, Any]]:
    """Return the best coin detection dict, or None if no candidate scores above min_score."""
    if len(circles) == 0:
        return None
    ranked = score_coin_candidates(circles, image, gray)
    if not ranked or ranked[0].total_score < min_score:
        logger.info(
            f"CoinSelector: best score {ranked[0].total_score:.3f} < {min_score} "
            f"— no coin accepted")
        return None
    best = ranked[0]
    logger.info(
        f"CoinSelector: best coin r={best.r}px at ({best.x},{best.y}) "
        f"score={best.total_score:.3f} "
        f"(sharpness={best.sharpness:.1f}, circ={best.circularity:.2f}, "
        f"size={best.size_score:.2f}, pos={best.position_score:.2f})")
    return {
        "name": "us_quarter",
        "type": "coin",
        "diameter_px": 2 * best.r,
        "confidence": min(0.7, best.total_score),
    }


def filter_coin_detections(circles: np.ndarray, image_shape: Tuple[int, int],
                           image: Optional[np.ndarray] = None,
                           min_px: int = MIN_COIN_DIAMETER_PX,
                           max_fraction: float = MAX_COIN_DIAMETER_FRACTION,
                           max_sat: int = MAX_COIN_SATURATION,
                           warm_hue_low: int = WARM_HUE_LOW,
                           warm_hue_high: int = WARM_HUE_HIGH,
                           ) -> np.ndarray:
    """Remove implausibly large, small, or colored circles from HoughCircles output."""
    h, w = image_shape
    max_diameter = min(h, w) * max_fraction

    hsv_image = None
    if image is not None and len(image.shape) == 3:
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    filtered = []
    rejected_size = 0
    rejected_color = 0
    for entry in circles:
        x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
        diameter = 2 * r
        if diameter < min_px or diameter > max_diameter:
            rejected_size += 1
            continue
        # HSV color check — real coins are silver-grey (low saturation)
        if hsv_image is not None:
            y0, y1 = max(0, y - r), min(h, y + r)
            x0, x1 = max(0, x - r), min(w, x + r)
            patch = hsv_image[y0:y1, x0:x1]
            if patch.size > 0:
                mean_s = float(patch[:, :, 1].mean())
                mean_h = float(patch[:, :, 0].mean())
                if mean_s > max_sat:
                    rejected_color += 1
                    continue
                if warm_hue_low <= mean_h <= warm_hue_high:
                    rejected_color += 1
                    continue
        filtered.append([float(x), float(y), float(r)])
    # Edge-sharpness check
    rejected_sharpness = 0
    if image is not None:
        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        sharp_filtered = []
        for entry in filtered:
            x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
            sharpness = _compute_coin_sharpness(gray_img, x, y, r)
            if sharpness >= MIN_COIN_EDGE_SHARPNESS:
                sharp_filtered.append(entry)
            else:
                rejected_sharpness += 1
        filtered = sharp_filtered
    logger.info(f"Coin filter: {len(circles)} raw -> -{rejected_size} size "
                f"-> -{rejected_color} color -> -{rejected_sharpness} sharpness "
                f"-> {len(filtered)} accepted")
    return np.array(filtered, dtype=np.float32) if filtered else np.empty((0, 3))


class ReferenceObjectDetector:
    def __init__(self):
        self.specs = INSTRUMENT_SPECS.get("reference_objects", {})

    def detect(self, image: np.ndarray,
               fg_mask: Optional[np.ndarray] = None) -> List[Dict[str, Any]]:
        detections = []
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Coin detection via Hough circles (with size sanity filter)
        # Patch: Tightened param2 30→50, radii 20-200→30-100 to reduce false positives
        raw_circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
            param1=50, param2=50, minRadius=30, maxRadius=100)
        if raw_circles is not None:
            raw = np.round(raw_circles[0]).astype(int)
            filtered = filter_coin_detections(raw, (h, w), image=image)
            # Patch 17 Fix 3: reject coins inside the instrument body
            filtered = filter_coin_by_position(filtered, fg_mask, (h, w))
            best = select_best_coin(filtered, image, gray)
            if best is not None:
                detections.append(best)

        # Card detection via rectangles
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 10000:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect = max(cw, ch) / max(1, min(cw, ch))
                for card_name, (wm, hm) in [("credit_card", (85.6, 53.98))]:
                    expected = max(wm, hm) / min(wm, hm)
                    if abs(aspect - expected) / expected < 0.2:
                        detections.append({
                            "name": card_name, "type": "card",
                            "width_px": cw, "height_px": ch, "confidence": 0.7,
                        })
                        break

        logger.info(f"ReferenceObjectDetector: {len(detections)} detections after filtering")
        return detections


# =============================================================================
# Stage 6.5 — Render DPI Estimation
# =============================================================================

def estimate_render_dpi(image: np.ndarray,
                        fg_mask: Optional[np.ndarray] = None) -> float:
    """
    Heuristic: estimate whether an image was rendered at screen (~96 dpi)
    or scanned at print (~300 dpi) by looking at fine-detail edge density.
    Returns estimated DPI.  Use only when no authoritative source is available.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    roi = cv2.bitwise_and(gray, gray, mask=fg_mask) if fg_mask is not None else gray
    blurred = cv2.GaussianBlur(roi, (3, 3), 0)
    edges = cv2.Canny(blurred, 30, 90)
    if fg_mask is not None:
        edges = cv2.bitwise_and(edges, edges, mask=fg_mask)

    edge_px = int(np.sum(edges > 0))
    total_px = int(np.sum(fg_mask > 0)) if fg_mask is not None else gray.size
    edge_ratio = edge_px / max(total_px, 1)

    if edge_ratio > 0.10:
        est_dpi = 300.0
    elif edge_ratio > 0.06:
        est_dpi = 150.0
    else:
        est_dpi = 96.0

    logger.info(
        f"DPI estimation: edge_ratio={edge_ratio:.4f} -> est_dpi={est_dpi:.0f} "
        f"({image.shape[1]}x{image.shape[0]}, {edge_px}/{total_px} edge px)")
    return est_dpi


# =============================================================================
# Stage 7 — Scale Calibration
# =============================================================================

class ScaleCalibrator:
    def __init__(self, default_dpi: float = 300.0):
        self.default_dpi = default_dpi
        self.ref_detector = ReferenceObjectDetector()
        self._feature_calibrator = FeatureScaleCalibrator()

    def calibrate(self, image: np.ndarray,
                  known_mm: Optional[float] = None,
                  known_px: Optional[float] = None,
                  spec_name: Optional[str] = None,
                  image_dpi: Optional[float] = None,
                  unit: Unit = Unit.MM,
                  fg_mask: Optional[np.ndarray] = None,
                  body_height_px: Optional[float] = None,
                  family_classification: Optional[FamilyClassification] = None,
                  feature_contours: Optional[List[FeatureContour]] = None,
                  edge_image: Optional[np.ndarray] = None,
                  ) -> CalibrationResult:

        # Priority 1: User dimension (always highest)
        if known_mm and known_px and known_px > 0:
            mm = known_mm
            if unit == Unit.INCH:
                mm = known_mm * 25.4
            elif unit == Unit.CM:
                mm = known_mm * 10
            return CalibrationResult(
                mm_per_px=mm / known_px, source=ScaleSource.USER_DIMENSION,
                confidence=1.0, message=f"User: {mm:.1f}mm / {known_px:.1f}px")

        # Priority 2: Instrument spec (WHEN EXPLICITLY PROVIDED - user intent)
        # Patch: Demote reference_object below spec when user explicitly provides spec_name.
        # User saying "this is a smart guitar" should outrank speculative circle detection.
        if spec_name and spec_name in INSTRUMENT_SPECS and body_height_px and body_height_px > 0:
            body_h_mm = INSTRUMENT_SPECS[spec_name]["body"][0]
            mpp = body_h_mm / body_height_px
            return CalibrationResult(
                mm_per_px=mpp, source=ScaleSource.INSTRUMENT_SPEC,
                confidence=0.75,  # boosted from 0.6 when user explicitly provided spec
                message=f"Spec: {spec_name} body {body_h_mm}mm / {body_height_px:.0f}px")

        # Priority 3: Reference objects (only if no explicit spec_name)
        refs = self.ref_detector.detect(image, fg_mask=fg_mask)
        if refs:
            for det in refs:
                if "diameter_px" in det and det["diameter_px"] > 0:
                    name = det["name"]
                    if name in INSTRUMENT_SPECS.get("reference_objects", {}):
                        diam_mm = INSTRUMENT_SPECS["reference_objects"][name][0]
                        mpp = diam_mm / det["diameter_px"]
                        return CalibrationResult(
                            mm_per_px=mpp, source=ScaleSource.REFERENCE_OBJECT,
                            confidence=det["confidence"],
                            message=f"Reference: {name} ({diam_mm}mm)")

        # Priority 4: EXIF DPI (authoritative from scanner/camera)
        if image_dpi and image_dpi > 0:
            return CalibrationResult(
                mm_per_px=25.4 / image_dpi, source=ScaleSource.EXIF_DPI,
                confidence=0.85, message=f"EXIF: {image_dpi:.0f} DPI")

        # Priority 5: Instrument spec fallback (when body_height_px not yet known)
        # This is for the case where spec is provided but we're in the first pass
        # before body contour is found. Handled by two-pass calibration.

        # Priority 4.5: Feature-based scale (Patch 13B)
        if family_classification and family_classification.family != InstrumentFamily.UNKNOWN:
            feat_result = self._feature_calibrator.calibrate_from_features(
                family_classification,
                feature_contours=feature_contours,
                edge_image=edge_image,
            )
            if feat_result and feat_result.confidence > 0.35:
                return feat_result

        # Priority 5: Render DPI estimation from edge density
        est_dpi = estimate_render_dpi(image, fg_mask)
        if est_dpi != self.default_dpi:
            return CalibrationResult(
                mm_per_px=25.4 / est_dpi, source=ScaleSource.ESTIMATED_RENDER_DPI,
                confidence=0.4,
                message=f"Estimated render DPI: {est_dpi:.0f}")

        # Priority 6: Assumed DPI (last resort)
        mpp = 25.4 / self.default_dpi
        msg = f"Assumed {self.default_dpi:.0f} DPI — supply --mm/--px for accuracy"
        logger.warning(f"Scale fallback: {msg} (mm/px={mpp:.4f})")
        return CalibrationResult(
            mm_per_px=mpp, source=ScaleSource.ASSUMED_DPI,
            confidence=0.2, message=msg)


# =============================================================================
# Stage 8 — Feature Classifier (rule-based)
# =============================================================================

class FeatureClassifier:
    def classify(self, contour: np.ndarray, mm_per_px: float,
                 bbox: Tuple[int, int, int, int],
                 body_bbox: Optional[Tuple[int, int, int, int]] = None,
                 ) -> Tuple[FeatureType, float]:
        x, y, w, h = bbox
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        max_dim = max(w_mm, h_mm)
        min_dim = min(w_mm, h_mm)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0

        # Body outline
        if max_dim > 300 and min_dim > 200:
            return FeatureType.BODY_OUTLINE, 0.9
        # F-hole
        if 120 < max_dim < 200 and 30 < min_dim < 60:
            return FeatureType.F_HOLE, 0.8
        # Soundhole
        if 80 < max_dim < 130 and 80 < min_dim < 130 and circularity > 0.7:
            return FeatureType.SOUNDHOLE, 0.85
        # Pickup route
        if 60 < max_dim < 100 and 30 < min_dim < 50:
            return FeatureType.PICKUP_ROUTE, 0.75
        # Neck pocket
        if 50 < max_dim < 90 and 40 < min_dim < 70:
            return FeatureType.NECK_POCKET, 0.8
        # Bridge route
        if 50 < max_dim < 150 and 20 < min_dim < 50:
            return FeatureType.BRIDGE_ROUTE, 0.7
        # Control cavity
        if 70 < max_dim < 150 and 40 < min_dim < 90:
            return FeatureType.CONTROL_CAVITY, 0.65
        # Jack route
        if 15 < max_dim < 40 and 15 < min_dim < 40:
            return FeatureType.JACK_ROUTE, 0.6

        return FeatureType.UNKNOWN, 0.3


# =============================================================================
# Stage 8 (Patch 13A) — Instrument Family Classifier
# =============================================================================

class InstrumentFamily:
    ARCHTOP = "archtop"
    ACOUSTIC = "acoustic"
    SOLID_BODY = "solid_body"
    SEMI_HOLLOW = "semi_hollow"
    UNKNOWN = "unknown"


@dataclass
class FamilyClassification:
    family: str
    confidence: float
    pixel_aspect: float
    f_hole_detected: bool
    soundhole_detected: bool
    notes: List[str] = field(default_factory=list)


class InstrumentFamilyClassifier:
    """
    Classify instrument family from body region geometry.
    Operates entirely in pixel space -- no mm conversion required.
    """

    def __init__(
        self,
        f_hole_circularity_max: float = 0.30,
        soundhole_circularity_min: float = 0.65,
    ):
        self.f_hole_circ_max = f_hole_circularity_max
        self.soundhole_circ_min = soundhole_circularity_min

    def classify(
        self,
        body_region: BodyRegion,
        edge_image: Optional[np.ndarray] = None,
        feature_contours: Optional[list] = None,
    ) -> FamilyClassification:
        notes: List[str] = []

        bw = max(body_region.width, 1)
        bh = max(body_region.height, 1)
        pixel_aspect = bh / bw
        notes.append(f"Body pixel aspect (h/w): {pixel_aspect:.3f}")

        f_hole_detected = False
        soundhole_detected = False

        if feature_contours:
            for fc in feature_contours:
                try:
                    ft_val = fc.feature_type.value if hasattr(fc.feature_type, 'value') \
                             else str(fc.feature_type)
                    if ft_val == "f_hole":
                        f_hole_detected = True
                    elif ft_val == "soundhole":
                        soundhole_detected = True
                except AttributeError:
                    pass

        if not feature_contours and edge_image is not None:
            f_hole_detected, soundhole_detected = self._scan_for_holes(
                edge_image, body_region)

        notes.append(f"f-hole detected: {f_hole_detected}")
        notes.append(f"soundhole detected: {soundhole_detected}")

        family, confidence = self._decide(
            pixel_aspect, f_hole_detected, soundhole_detected, notes,
            feature_contours=feature_contours)

        return FamilyClassification(
            family=family,
            confidence=confidence,
            pixel_aspect=pixel_aspect,
            f_hole_detected=f_hole_detected,
            soundhole_detected=soundhole_detected,
            notes=notes,
        )

    def _decide(
        self,
        aspect: float,
        f_hole: bool,
        soundhole: bool,
        notes: List[str],
        feature_contours: Optional[list] = None,
    ) -> Tuple[str, float]:
        if soundhole and not f_hole:
            notes.append("Decision: soundhole present -> ACOUSTIC")
            return InstrumentFamily.ACOUSTIC, 0.85

        if f_hole:
            if aspect < 1.25:
                notes.append("Decision: f-holes + low aspect -> ARCHTOP")
                return InstrumentFamily.ARCHTOP, 0.80
            else:
                notes.append("Decision: f-holes + higher aspect -> SEMI_HOLLOW")
                return InstrumentFamily.SEMI_HOLLOW, 0.72

        for fc in (feature_contours or []):
            try:
                ft_val = fc.feature_type.value if hasattr(fc.feature_type, 'value') \
                         else str(fc.feature_type)
                if ft_val in ("pickup_route", "control_cavity", "neck_pocket"):
                    notes.append(f"Decision: electric feature ({ft_val}) -> SOLID_BODY")
                    return InstrumentFamily.SOLID_BODY, 0.70
            except AttributeError:
                pass

        if aspect > 1.26:
            notes.append(f"Decision: high aspect ({aspect:.3f}) -> ACOUSTIC")
            return InstrumentFamily.ACOUSTIC, 0.55
        if aspect < 1.20:
            notes.append(f"Decision: low aspect ({aspect:.3f}), no holes -> SOLID_BODY")
            return InstrumentFamily.SOLID_BODY, 0.50

        notes.append(f"Decision: ambiguous aspect ({aspect:.3f}) -> UNKNOWN")
        return InstrumentFamily.UNKNOWN, 0.30

    def _scan_for_holes(
        self,
        edge_image: np.ndarray,
        body_region: BodyRegion,
    ) -> Tuple[bool, bool]:
        """Quick scan of edge image within body region for hole signatures."""
        h, w = edge_image.shape[:2]
        y0 = max(0, body_region.y)
        y1 = min(h, body_region.y + body_region.height)
        x0 = max(0, body_region.x)
        x1 = min(w, body_region.x + body_region.width)
        crop = edge_image[y0:y1, x0:x1]

        if crop.size == 0:
            return False, False

        contours, _ = cv2.findContours(crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        f_hole = False
        soundhole = False

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 200:
                continue
            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            circ = 4 * math.pi * area / (peri ** 2)
            _, (cw, ch), _ = cv2.minAreaRect(cnt)
            aspect = max(cw, ch) / max(min(cw, ch), 1)

            if circ < self.f_hole_circ_max and aspect > 3.0:
                f_hole = True
            if circ > self.soundhole_circ_min and 0.8 < aspect < 1.3:
                if 500 < area < 30000:
                    soundhole = True

        return f_hole, soundhole


# =============================================================================
# Stage 7.5 (Patch 13B) — Feature Scale Calibrator
# =============================================================================

_FEATURE_SIZE_TABLE: List[Tuple[str, float, float, List[str]]] = [
    ("single_coil_pickup_w", 85.0, 0.08,
     [InstrumentFamily.SOLID_BODY, InstrumentFamily.SEMI_HOLLOW]),
    ("humbucker_pickup_w", 70.0, 0.08,
     [InstrumentFamily.SOLID_BODY, InstrumentFamily.SEMI_HOLLOW,
      InstrumentFamily.ARCHTOP]),
    ("dreadnought_soundhole", 100.0, 0.06,
     [InstrumentFamily.ACOUSTIC]),
    ("auditorium_soundhole", 88.0, 0.07,
     [InstrumentFamily.ACOUSTIC]),
    ("archtop_f_hole_length", 165.0, 0.10,
     [InstrumentFamily.ARCHTOP, InstrumentFamily.SEMI_HOLLOW]),
    ("acoustic_bridge_length", 175.0, 0.08,
     [InstrumentFamily.ACOUSTIC]),
]


@dataclass
class FeatureScaleHypothesis:
    feature_name: str
    measured_px: float
    known_mm: float
    mm_per_px: float
    confidence: float
    family: str


class FeatureScaleCalibrator:
    """
    Calibrates scale from known instrument feature sizes, gated by
    instrument family. Priority 4.5 in the calibration chain.
    """

    def __init__(self, min_feature_px: int = 50, max_hypotheses: int = 5):
        self.min_px = min_feature_px
        self.max_hyp = max_hypotheses

    def calibrate_from_features(
        self,
        family: FamilyClassification,
        feature_contours: Optional[List[FeatureContour]] = None,
        edge_image: Optional[np.ndarray] = None,
    ) -> Optional[CalibrationResult]:
        if family.family == InstrumentFamily.UNKNOWN:
            logger.info("FeatureScaleCalibrator: unknown family -- skipping")
            return None

        hypotheses: List[FeatureScaleHypothesis] = []

        if feature_contours:
            hypotheses = self._measure_from_contours(feature_contours, family)

        if not hypotheses and edge_image is not None:
            hypotheses = self._measure_from_edges(edge_image, family)

        if not hypotheses:
            logger.info(
                f"FeatureScaleCalibrator: no matching features for {family.family}")
            return None

        combined = self._combine_hypotheses(hypotheses, family)
        if combined is None:
            return None

        logger.info(
            f"FeatureScaleCalibrator: {len(hypotheses)} feature(s) -> "
            f"mpp={combined.mm_per_px:.4f} conf={combined.confidence:.2f} "
            f"[{family.family}]")
        return combined

    def _measure_from_contours(
        self,
        feature_contours: List[FeatureContour],
        family: FamilyClassification,
    ) -> List[FeatureScaleHypothesis]:
        hypotheses: List[FeatureScaleHypothesis] = []
        family_str = family.family

        for fc in feature_contours:
            if len(hypotheses) >= self.max_hyp:
                break
            try:
                ft_val = fc.feature_type.value if hasattr(fc.feature_type, 'value') \
                         else str(fc.feature_type)
            except AttributeError:
                continue

            _, _, bw_px, bh_px = fc.bbox_px
            max_dim_px = max(bw_px, bh_px)
            min_dim_px = min(bw_px, bh_px)

            if max_dim_px < self.min_px:
                continue

            for feat_name, feat_mm, tol, families in _FEATURE_SIZE_TABLE:
                if family_str not in families:
                    continue

                if ft_val in ("pickup_route", "bridge_route"):
                    measured_px = max_dim_px
                elif ft_val in ("soundhole", "rosette"):
                    measured_px = (bw_px + bh_px) / 2.0
                elif ft_val == "f_hole":
                    measured_px = max_dim_px
                else:
                    continue

                if measured_px < self.min_px:
                    continue

                mpp = feat_mm / measured_px
                feat_conf = 0.45 * family.confidence
                hypotheses.append(FeatureScaleHypothesis(
                    feature_name=feat_name,
                    measured_px=measured_px,
                    known_mm=feat_mm,
                    mm_per_px=mpp,
                    confidence=feat_conf,
                    family=family_str,
                ))

        return hypotheses

    def _measure_from_edges(
        self,
        edge_image: np.ndarray,
        family: FamilyClassification,
    ) -> List[FeatureScaleHypothesis]:
        hypotheses: List[FeatureScaleHypothesis] = []
        contours, _ = cv2.findContours(
            edge_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            if len(hypotheses) >= self.max_hyp:
                break
            area = cv2.contourArea(cnt)
            if area < self.min_px * self.min_px:
                continue
            peri = cv2.arcLength(cnt, True)
            circ = 4 * math.pi * area / max(peri ** 2, 1e-9)
            x, y, w, h = cv2.boundingRect(cnt)
            asp = max(w, h) / max(min(w, h), 1)

            family_str = family.family

            if (family_str == InstrumentFamily.ACOUSTIC and
                    circ > 0.65 and 0.8 < asp < 1.3):
                diam_px = (w + h) / 2.0
                for feat_name, feat_mm, _, families in _FEATURE_SIZE_TABLE:
                    if family_str in families and "soundhole" in feat_name:
                        hypotheses.append(FeatureScaleHypothesis(
                            feature_name=feat_name,
                            measured_px=diam_px,
                            known_mm=feat_mm,
                            mm_per_px=feat_mm / diam_px,
                            confidence=0.35 * family.confidence,
                            family=family_str,
                        ))
                        break

        return hypotheses

    def _combine_hypotheses(
        self,
        hypotheses: List[FeatureScaleHypothesis],
        family: FamilyClassification,
    ) -> Optional[CalibrationResult]:
        if not hypotheses:
            return None

        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        best = hypotheses[0]

        if len(hypotheses) == 1:
            return CalibrationResult(
                mm_per_px=best.mm_per_px,
                source=ScaleSource.FEATURE_SCALE,
                confidence=best.confidence * 0.90,
                message=(
                    f"Feature scale: {best.feature_name} "
                    f"({best.known_mm}mm / {best.measured_px:.0f}px) "
                    f"[{family.family}]"),
            )

        second = hypotheses[1]
        disagreement = abs(best.mm_per_px - second.mm_per_px) / max(best.mm_per_px, 1e-9)

        if disagreement > 0.50:
            conf = best.confidence * 0.75
            logger.info(
                f"FeatureScaleCalibrator: hypotheses disagree by {disagreement:.0%} "
                f"-> using best only (conf penalized to {conf:.2f})")
            return CalibrationResult(
                mm_per_px=best.mm_per_px,
                source=ScaleSource.FEATURE_SCALE,
                confidence=conf,
                message=(
                    f"Feature scale (best of {len(hypotheses)}): "
                    f"{best.feature_name} = {best.mm_per_px:.4f}mm/px "
                    f"[{family.family}], disagreement={disagreement:.0%}"),
            )

        agreement_bonus = max(0.0, 1.0 - disagreement) * 0.10
        total_w = sum(h.confidence for h in hypotheses)
        weighted_mpp = sum(h.mm_per_px * h.confidence for h in hypotheses) / total_w
        conf = min(0.55, best.confidence + agreement_bonus)

        return CalibrationResult(
            mm_per_px=weighted_mpp,
            source=ScaleSource.FEATURE_SCALE,
            confidence=conf,
            message=(
                f"Feature scale ({len(hypotheses)} hypotheses, "
                f"agreement={1 - disagreement:.0%}): "
                f"mpp={weighted_mpp:.4f} [{family.family}]"),
        )


# =============================================================================
# Batch Calibration Smoother (Patch 13C)
# =============================================================================

class BatchCalibrationSmoother:
    """
    Detects and corrects calibration outliers in batch processing sessions
    using median-based z-score analysis, bucketed by instrument family.
    """

    def __init__(
        self,
        window_size: int = 7,
        z_threshold: float = 3.0,
        min_history: int = 3,
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.min_history = min_history
        self._history: Dict[str, List[float]] = {}

    def smooth(self, extraction_result: PhotoExtractionResult) -> PhotoExtractionResult:
        cal = extraction_result.calibration
        if cal is None:
            return extraction_result

        current_mpp = cal.mm_per_px
        source_str = cal.source.value if hasattr(cal.source, 'value') \
                     else str(cal.source)

        family = self._infer_family(extraction_result)
        bucket = self._history.setdefault(family, [])

        if len(bucket) >= self.min_history:
            from statistics import median as _median
            batch_median = _median(bucket[-self.window_size:])
            values = bucket[-self.window_size:]
            mad = _median([abs(v - batch_median) for v in values])
            robust_std = mad * 1.4826

            if robust_std > 0:
                z_score = abs(current_mpp - batch_median) / robust_std
            else:
                z_score = float('inf') if current_mpp != batch_median else 0.0

            if z_score > self.z_threshold:
                old_mpp = current_mpp
                cal.mm_per_px = batch_median
                cal.confidence = 0.55
                cal.message = (
                    f"Batch corrected: {old_mpp:.4f} -> {batch_median:.4f} "
                    f"(z={z_score:.1f}, family={family}, n={len(values)})")
                extraction_result.warnings.append(
                    f"Scale outlier corrected: mpp was {old_mpp:.4f} "
                    f"(z={z_score:.1f}x from batch median {batch_median:.4f}). "
                    f"Verify dimensions before cutting.")
                logger.warning(cal.message)
                bucket.append(batch_median)
                return extraction_result

        bucket.append(current_mpp)
        return extraction_result

    def session_summary(self) -> str:
        from statistics import median as _median
        lines = ["BatchCalibrationSmoother -- session summary:"]
        for family, values in self._history.items():
            if not values:
                continue
            med = _median(values)
            lines.append(
                f"  {family}: n={len(values)} median={med:.4f} "
                f"range=[{min(values):.4f}, {max(values):.4f}]")
        return "\n".join(lines)

    def reset(self) -> None:
        self._history.clear()

    @staticmethod
    def _infer_family(result: PhotoExtractionResult) -> str:
        features = result.features
        for ft, contours in features.items():
            if not contours:
                continue
            ft_val = ft.value if hasattr(ft, 'value') else str(ft)
            if ft_val == "f_hole":
                return InstrumentFamily.ARCHTOP
            if ft_val == "soundhole":
                return InstrumentFamily.ACOUSTIC
            if ft_val in ("pickup_route", "control_cavity"):
                return InstrumentFamily.SOLID_BODY
        return "unknown"


# =============================================================================
# Rough MPP Estimate (Patch 15 Fix B)
# =============================================================================

_ROUGH_SPEC_HEIGHTS = {
    "stratocaster": 406,
    "telecaster": 406,
    "les_paul": 450,
    "es335": 500,
    "dreadnought": 520,
    "smart_guitar": 444,
    "jumbo_archtop": 520,
    "archtop": 520,
    "acoustic": 500,
    "solid_body": 430,
}
_DEFAULT_BODY_HEIGHT_MM = 490.0


def compute_rough_mpp(
    body_region: Optional[BodyRegion],
    spec_name: Optional[str] = None,
    family_hint: Optional[str] = None,
) -> float:
    """
    Compute a rough mm/px estimate for GatedAdaptiveCloser kernel sizing
    BEFORE full calibration runs. Not used as final calibration result.
    """
    if body_region is None or body_region.height_px <= 0:
        logger.debug("compute_rough_mpp: no body_region -> using 0.30")
        return 0.30

    body_h_px = float(body_region.height_px)

    if spec_name and spec_name.lower() in _ROUGH_SPEC_HEIGHTS:
        h_mm = _ROUGH_SPEC_HEIGHTS[spec_name.lower()]
        rough = h_mm / body_h_px
        logger.debug(
            f"compute_rough_mpp: spec={spec_name} -> {h_mm}mm/{body_h_px:.0f}px "
            f"= {rough:.4f}")
        return rough

    if family_hint and family_hint.lower() in _ROUGH_SPEC_HEIGHTS:
        h_mm = _ROUGH_SPEC_HEIGHTS[family_hint.lower()]
        rough = h_mm / body_h_px
        logger.debug(
            f"compute_rough_mpp: family={family_hint} -> {h_mm}mm/{body_h_px:.0f}px "
            f"= {rough:.4f}")
        return rough

    rough = _DEFAULT_BODY_HEIGHT_MM / body_h_px
    logger.debug(
        f"compute_rough_mpp: no spec/family -> "
        f"{_DEFAULT_BODY_HEIGHT_MM}mm/{body_h_px:.0f}px = {rough:.4f}")
    return rough


# =============================================================================
# Stage 8 (Patch 17 Fix 1) — Body Contour Merger
# =============================================================================

@dataclass
class MergeResult:
    """Result from ContourMerger."""
    merged_contour: np.ndarray
    n_fragments: int
    fragment_areas: List[float]
    close_kernel_px: int
    bbox_px: Tuple[int, int, int, int]
    notes: List[str] = field(default_factory=list)


class ContourMerger:
    """
    Merges fragmented body contours into a single unified outline.

    Fills all body-candidate contour areas onto a binary mask, applies
    morphological close to bridge inter-fragment gaps, then re-detects
    as a single merged contour.  Operates on filled silhouette masks,
    not edge pixels (unlike GatedAdaptiveCloser).
    """

    def __init__(
        self,
        max_close_px: int = 120,
        min_fragment_area: float = 2000.0,
        max_fragments: int = 8,
        body_overlap_min: float = 0.40,
    ):
        self.max_close_px = max_close_px
        self.min_fragment_area = min_fragment_area
        self.max_fragments = max_fragments
        self.body_overlap_min = body_overlap_min

    def merge(
        self,
        feature_contours: List[FeatureContour],
        image_shape: Tuple[int, int],
        body_region: Optional[BodyRegion] = None,
        mpp: float = 0.3,
    ) -> Optional[MergeResult]:
        """
        Find all body-candidate fragments, fill them onto a mask, close,
        re-detect as a single merged contour.

        Returns MergeResult with merged contour, or None if merging unnecessary.
        """
        h, w = image_shape
        notes: List[str] = []

        candidates = self._collect_candidates(
            feature_contours, body_region, notes)

        if len(candidates) <= 1:
            notes.append(f"Only {len(candidates)} candidate(s) -- no merge needed")
            logger.info(f"ContourMerger: {notes[-1]}")
            return None

        notes.append(f"Found {len(candidates)} body fragments to merge")

        gap_px = self._estimate_gap_px(candidates)
        notes.append(f"Max vertical gap: {gap_px}px ({gap_px * mpp:.1f}mm)")

        k_size = min(self.max_close_px, int(gap_px * 1.5 / 2) * 2 + 1)
        k_size = max(11, k_size)
        notes.append(f"Close kernel: {k_size}x{k_size}")

        mask = np.zeros((h, w), np.uint8)
        fragment_areas: List[float] = []
        for fc in candidates:
            pts = fc.points_px
            pts_draw = pts if pts.ndim == 3 else pts.reshape(-1, 1, 2)
            cv2.fillPoly(mask, [pts_draw], 255)
            fragment_areas.append(float(fc.area_px))

        kernel = np.ones((k_size, k_size), np.uint8)
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        cnts, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cnts:
            notes.append("No contours after merge")
            return None

        merged = max(cnts, key=cv2.contourArea)
        bbox = cv2.boundingRect(merged)

        notes.append(
            f"Merged: {len(candidates)} fragments -> 1 contour "
            f"({bbox[2]}x{bbox[3]}px)")
        logger.info(
            f"ContourMerger: {len(candidates)} fragments merged with "
            f"k={k_size}x{k_size}, gap={gap_px}px -> "
            f"bbox {bbox[2]}x{bbox[3]}px")

        return MergeResult(
            merged_contour=merged,
            n_fragments=len(candidates),
            fragment_areas=fragment_areas,
            close_kernel_px=k_size,
            bbox_px=bbox,
            notes=notes,
        )

    def _collect_candidates(
        self,
        feature_contours: List[FeatureContour],
        body_region: Optional[BodyRegion],
        notes: List[str],
    ) -> List[FeatureContour]:
        candidates: List[FeatureContour] = []
        for fc in feature_contours:
            if fc.area_px < self.min_fragment_area:
                continue
            if body_region is not None:
                _, cy, _, ch = fc.bbox_px
                b_top = body_region.y
                b_bot = body_region.y + body_region.height
                overlap = max(0, min(cy + ch, b_bot) - max(cy, b_top))
                ov_frac = overlap / max(ch, 1)
                if ov_frac < self.body_overlap_min:
                    continue
            candidates.append(fc)
        candidates.sort(key=lambda fc: fc.area_px, reverse=True)
        return candidates[:self.max_fragments]

    @staticmethod
    def _estimate_gap_px(candidates: List[FeatureContour]) -> int:
        if len(candidates) < 2:
            return 0
        extents = []
        for fc in candidates:
            _, cy, _, ch = fc.bbox_px
            extents.append((cy, cy + ch))
        extents.sort()
        max_gap = 0
        for i in range(len(extents) - 1):
            gap = extents[i + 1][0] - extents[i][1]
            max_gap = max(max_gap, gap)
        return max(0, max_gap)


# =============================================================================
# Stage 8 (Patch 17 Fix 2) — Body Contour Election with X-Extent Guard
# =============================================================================

def elect_body_contour_v2(
    contours: List[FeatureContour],
    body_region_hint: Optional[BodyRegion] = None,
    min_overlap: float = 0.50,
    max_width_factor: float = 1.30,
    ownership_scores: Optional[Dict[int, float]] = None,
    ownership_threshold: float = 0.60,
) -> int:
    """
    Elect body contour with vertical overlap AND X-extent guard.

    Returns index of elected body contour, or -1 if empty.
    """
    if not contours:
        return -1

    if body_region_hint is None:
        return max(range(len(contours)), key=lambda i: contours[i].area_px)

    body_w = max(body_region_hint.width, 1)
    body_h = max(body_region_hint.height, 1)
    max_w = body_w * max_width_factor

    scored: List[Tuple[int, float, float, int, float]] = []
    rejected_overlap = 0
    rejected_width = 0
    rejected_ownership = 0

    for i, fc in enumerate(contours):
        cx, cy, cw, ch = fc.bbox_px

        b_top = body_region_hint.y
        b_bot = body_region_hint.y + body_h
        overlap = max(0, min(cy + ch, b_bot) - max(cy, b_top))
        ov_frac = overlap / max(ch, 1)

        if ov_frac < min_overlap:
            rejected_overlap += 1
            continue

        if cw > max_w:
            logger.debug(
                f"X-extent guard: contour[{i}] width={cw}px > "
                f"max={max_w:.0f}px -- rejected")
            rejected_width += 1
            continue

        if ownership_scores is not None:
            ownership = float(ownership_scores.get(i, 0.0))
            if ownership < ownership_threshold:
                logger.debug(
                    f"Ownership gate: contour[{i}] ownership={ownership:.3f} "
                    f"< threshold={ownership_threshold:.3f} -- rejected")
                rejected_ownership += 1
                continue
        else:
            ownership = 1.0

        score = ov_frac * fc.area_px
        scored.append((i, score, ov_frac, cw, ownership))

    logger.info(
        f"elect_body_contour_v2: {len(scored)} candidates pass "
        f"(rejected overlap={rejected_overlap}, width={rejected_width}, "
        f"ownership={rejected_ownership})")

    if scored:
        scored.sort(key=lambda x: x[1], reverse=True)
        best_idx = scored[0][0]
        logger.info(
            f"  Elected idx={best_idx}: overlap={scored[0][2]:.0%}, "
            f"width={scored[0][3]}px, ownership={scored[0][4]:.2f}, "
            f"area={contours[best_idx].area_px:.0f}px2")
        return best_idx

    if ownership_scores is not None and rejected_ownership > 0:
        logger.warning(
            "elect_body_contour_v2: ownership gate rejected all plausible body contours")
        return -1

    # Fallback: no contour passed both filters -- overlap only
    logger.warning(
        "elect_body_contour_v2: no contour passed X-extent guard "
        "-- falling back to overlap-only")
    fallback_candidates = [
        i for i, fc in enumerate(contours)
        if _body_vertical_overlap(fc.bbox_px, body_region_hint) >= min_overlap
    ]
    if fallback_candidates:
        return max(fallback_candidates, key=lambda i: contours[i].area_px)
    return max(range(len(contours)), key=lambda i: contours[i].area_px)


def _body_vertical_overlap(
    contour_bbox: Tuple[int, int, int, int],
    body_region: BodyRegion,
) -> float:
    _, cy, _, ch = contour_bbox
    b_top = body_region.y
    b_bot = body_region.y + body_region.height
    overlap = max(0, min(cy + ch, b_bot) - max(cy, b_top))
    return overlap / max(ch, 1)


# =============================================================================
# Stage 7 (Patch 17 Fix 3) — Coin Position Filter
# =============================================================================

def filter_coin_by_position(
    circles: np.ndarray,
    fg_mask: Optional[np.ndarray],
    image_shape: Tuple[int, int],
    margin_px: int = 15,
) -> np.ndarray:
    """
    Reject coin candidates whose centre is inside the instrument silhouette.

    Real reference coins are placed BESIDE the instrument, not on top of it.
    """
    if fg_mask is None or len(circles) == 0:
        return circles

    h, w = image_shape
    accepted = []
    rejected = 0

    if margin_px > 0:
        kernel = np.ones((margin_px * 2 + 1, margin_px * 2 + 1), np.uint8)
        fg_check = cv2.erode(fg_mask, kernel)
    else:
        fg_check = fg_mask

    for entry in circles:
        x, y, r = int(entry[0]), int(entry[1]), int(entry[2])
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        if fg_check[y, x] > 0:
            logger.debug(
                f"Coin position filter: rejected ({x},{y}) r={r}px "
                f"-- centre inside fg_mask")
            rejected += 1
            continue

        y0, y1 = max(0, y - r), min(h, y + r)
        x0, x1 = max(0, x - r), min(w, x + r)
        patch = fg_check[y0:y1, x0:x1]
        if patch.size > 0:
            inside_frac = float(np.sum(patch > 0)) / patch.size
            if inside_frac > 0.30:
                logger.debug(
                    f"Coin position filter: rejected ({x},{y}) r={r}px "
                    f"-- {inside_frac:.0%} inside fg_mask")
                rejected += 1
                continue

        accepted.append(entry)

    logger.info(
        f"CoinPositionFilter: {len(circles)} -> {len(accepted)} "
        f"({rejected} inside body rejected)")

    return np.array(accepted, dtype=np.float32) if accepted \
        else np.empty((0, 3))


# =============================================================================
# Stage 8 — Contour Plausibility Scorer
# =============================================================================

# Family-aware dimension priors: (min_h_mm, max_h_mm, min_w_mm, max_w_mm)
_FAMILY_DIMENSION_PRIORS: Dict[str, Tuple[float, float, float, float]] = {
    InstrumentFamily.SOLID_BODY:  (350.0, 470.0, 280.0, 380.0),
    InstrumentFamily.ARCHTOP:     (420.0, 560.0, 350.0, 460.0),
    InstrumentFamily.ACOUSTIC:    (440.0, 560.0, 350.0, 440.0),
    InstrumentFamily.SEMI_HOLLOW: (400.0, 530.0, 330.0, 440.0),
    InstrumentFamily.UNKNOWN:     (300.0, 600.0, 250.0, 480.0),
}

EXPORT_BLOCK_THRESHOLD: float = 0.30


class ContourPlausibilityScorer:
    """
    Scores contour candidates for plausibility as a guitar body outline.

    V1 signals (no curvature profiling):
      - Solidity (hull coverage): convex_area / hull_area
      - Vertical extent: contour height vs body region height
      - Border contact: contour bbox touching image edges
      - Aspect ratio sanity vs family priors
      - Neck inclusion heuristic: contour extends far above body region
      - Symmetry: left/right area balance
      - Dimension plausibility vs INSTRUMENT_SPECS family priors
    """

    def __init__(
        self,
        border_margin_px: int = 5,
        neck_height_factor: float = 1.35,
        min_solidity: float = 0.55,
        ownership_threshold: float = 0.60,
    ):
        self.border_margin_px = border_margin_px
        self.neck_height_factor = neck_height_factor
        self.min_solidity = min_solidity
        self.ownership_threshold = ownership_threshold

    def score_candidate(
        self,
        fc: FeatureContour,
        idx: int,
        body_region: Optional[BodyRegion],
        family: str,
        mpp: float,
        image_shape: Tuple[int, int],
    ) -> ContourScore:
        """Score a single contour candidate."""
        issues: List[str] = []
        img_h, img_w = image_shape

        # --- Signal 1: Solidity (hull coverage) ---
        solidity = fc.solidity
        if solidity < self.min_solidity:
            issues.append(f"low solidity {solidity:.2f}")

        # --- Signal 2: Border contact ---
        cx, cy, cw, ch = fc.bbox_px
        m = self.border_margin_px
        touches_left = cx <= m
        touches_top = cy <= m
        touches_right = (cx + cw) >= (img_w - m)
        touches_bottom = (cy + ch) >= (img_h - m)
        border_count = sum([touches_left, touches_top, touches_right, touches_bottom])
        border_contact = border_count >= 2
        if border_contact:
            issues.append(f"border contact on {border_count} edges")

        # --- Signal 3: Neck inclusion ---
        includes_neck = False
        if body_region is not None:
            body_top = body_region.y
            contour_top = cy
            # If contour extends significantly above body region top,
            # it likely includes the neck
            if contour_top < body_top - body_region.height * 0.15:
                total_h = ch
                body_overlap_h = min(cy + ch, body_region.y + body_region.height) - body_region.y
                if total_h > body_region.height * self.neck_height_factor:
                    includes_neck = True
                    issues.append("likely includes neck")

        # --- Signal 4: Aspect ratio sanity ---
        priors = _FAMILY_DIMENSION_PRIORS.get(
            family, _FAMILY_DIMENSION_PRIORS[InstrumentFamily.UNKNOWN])
        expected_aspect_min = priors[0] / priors[3]  # min_h / max_w
        expected_aspect_max = priors[1] / priors[2]  # max_h / min_w
        contour_aspect = max(ch, 1) / max(cw, 1)
        # Allow ±40% tolerance on aspect ratio range
        aspect_lo = expected_aspect_min * 0.6
        aspect_hi = expected_aspect_max * 1.4
        aspect_ratio_ok = aspect_lo <= contour_aspect <= aspect_hi
        if not aspect_ratio_ok:
            issues.append(
                f"aspect ratio {contour_aspect:.2f} outside "
                f"[{aspect_lo:.2f}, {aspect_hi:.2f}]")

        # --- Signal 5: Dimension plausibility ---
        dim_plausibility = 1.0
        if mpp > 0:
            h_mm = ch * mpp
            w_mm = cw * mpp
            min_h, max_h, min_w, max_w = priors

            # Height plausibility
            if min_h <= h_mm <= max_h:
                h_plaus = 1.0
            else:
                h_dist = min(abs(h_mm - min_h), abs(h_mm - max_h))
                h_range = max_h - min_h
                h_plaus = max(0.0, 1.0 - h_dist / h_range)

            # Width plausibility
            if min_w <= w_mm <= max_w:
                w_plaus = 1.0
            else:
                w_dist = min(abs(w_mm - min_w), abs(w_mm - max_w))
                w_range = max_w - min_w
                w_plaus = max(0.0, 1.0 - w_dist / w_range)

            dim_plausibility = (h_plaus + w_plaus) / 2.0
            if dim_plausibility < 0.4:
                issues.append(
                    f"dimensions {h_mm:.0f}x{w_mm:.0f}mm poor match "
                    f"for {family}")

        # --- Signal 6: Vertical extent vs body region ---
        completeness = solidity
        vertical_coverage = 1.0
        neck_inclusion_score = 1.0 if includes_neck else 0.0
        if body_region is not None:
            height_ratio = ch / max(body_region.height, 1)
            vertical_coverage = max(0.0, min(1.0, height_ratio))
            # Penalize if contour is much smaller than body region
            if height_ratio < 0.5:
                completeness *= 0.6
                issues.append(f"small vs body region ({height_ratio:.0%})")

            body_top = body_region.y
            neck_span = max(0.0, float(body_top - cy))
            neck_inclusion_score = min(
                1.0,
                max(
                    neck_inclusion_score,
                    neck_span / max(1.0, body_region.height * 0.25),
                ),
            )

        # --- Signal 7: Symmetry (left/right area) ---
        symmetry_score = self._compute_symmetry(fc, image_shape)

        # --- Signal 8: Body ownership ---
        border_contact_score = min(1.0, border_count / 4.0)
        ownership_score = self._body_ownership_score(
            completeness=completeness,
            border_contact=border_contact_score,
            vertical_coverage=vertical_coverage,
            neck_inclusion=neck_inclusion_score,
        )
        ownership_ok = ownership_score >= self.ownership_threshold
        if not ownership_ok:
            issues.append(f"body ownership weak ({ownership_score:.2f})")

        # --- Composite score ---
        w_solidity = 0.25
        w_dim = 0.25
        w_symmetry = 0.15
        w_aspect = 0.15
        w_border = 0.10
        w_neck = 0.10

        score = (
            w_solidity * min(solidity / 0.85, 1.0) +
            w_dim * dim_plausibility +
            w_symmetry * symmetry_score +
            w_aspect * (1.0 if aspect_ratio_ok else 0.3) +
            w_border * (0.2 if border_contact else 1.0) +
            w_neck * (0.3 if includes_neck else 1.0)
        )

        if not ownership_ok:
            score = min(score, self.ownership_threshold - 0.01)

        return ContourScore(
            contour_index=idx,
            score=round(score, 4),
            completeness=round(completeness, 4),
            includes_neck=includes_neck,
            border_contact=border_contact,
            dimension_plausibility=round(dim_plausibility, 4),
            symmetry_score=round(symmetry_score, 4),
            aspect_ratio_ok=aspect_ratio_ok,
            ownership_score=round(ownership_score, 4),
            vertical_coverage=round(vertical_coverage, 4),
            neck_inclusion_score=round(neck_inclusion_score, 4),
            issues=issues,
        )

    def score_all_candidates(
        self,
        contours: List[FeatureContour],
        body_region: Optional[BodyRegion],
        family: str,
        mpp: float,
        image_shape: Tuple[int, int],
        min_area_px: float = 5000.0,
    ) -> List[ContourScore]:
        """Score all contours above area threshold."""
        scores: List[ContourScore] = []
        for i, fc in enumerate(contours):
            if fc.area_px < min_area_px:
                continue
            cs = self.score_candidate(
                fc, i, body_region, family, mpp, image_shape)
            scores.append(cs)
        return scores

    def elect_best(
        self,
        pre_merge_scores: List[ContourScore],
        post_merge_scores: List[ContourScore],
    ) -> Tuple[int, str, float]:
        """
        Compare best pre-merge candidate vs best post-merge candidate.

        Returns (best_contour_index, source, best_score).
        source is "pre_merge" or "post_merge".
        """
        best_pre = max(pre_merge_scores, key=lambda s: s.score) \
            if pre_merge_scores else None
        best_post = max(post_merge_scores, key=lambda s: s.score) \
            if post_merge_scores else None

        if best_pre is None and best_post is None:
            return -1, "none", 0.0

        if best_pre is None:
            return best_post.contour_index, "post_merge", best_post.score
        if best_post is None:
            return best_pre.contour_index, "pre_merge", best_pre.score

        # Prefer post-merge if scores are close (within 0.05)
        # since morphological merge is purpose-built for fragmented bodies
        if best_post.score >= best_pre.score - 0.05:
            return best_post.contour_index, "post_merge", best_post.score
        else:
            logger.info(
                f"PlausibilityScorer: pre-merge candidate wins "
                f"(pre={best_pre.score:.3f} vs post={best_post.score:.3f})")
            return best_pre.contour_index, "pre_merge", best_pre.score

    @staticmethod
    def _compute_symmetry(
        fc: FeatureContour,
        image_shape: Tuple[int, int],
    ) -> float:
        """Compute left/right symmetry of a contour about its centroid."""
        pts = fc.points_px
        if pts is None or len(pts) < 10:
            return 0.5

        pts_2d = pts.reshape(-1, 2)
        cx_centroid = float(pts_2d[:, 0].mean())

        left_pts = pts_2d[pts_2d[:, 0] <= cx_centroid]
        right_pts = pts_2d[pts_2d[:, 0] > cx_centroid]

        n_left = len(left_pts)
        n_right = len(right_pts)
        total = n_left + n_right
        if total == 0:
            return 0.5

        balance = min(n_left, n_right) / max(n_left, n_right) \
            if max(n_left, n_right) > 0 else 0.0

        # Also check vertical spread symmetry
        if n_left > 2 and n_right > 2:
            left_span = float(left_pts[:, 1].max() - left_pts[:, 1].min())
            right_span = float(right_pts[:, 1].max() - right_pts[:, 1].min())
            span_ratio = min(left_span, right_span) / max(left_span, right_span, 1.0)
            return (balance + span_ratio) / 2.0

        return balance

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _body_ownership_score(
        self,
        *,
        completeness: float,
        border_contact: float,
        vertical_coverage: float,
        neck_inclusion: float,
    ) -> float:
        completeness = self._clamp01(completeness)
        border_contact = self._clamp01(border_contact)
        vertical_coverage = self._clamp01(vertical_coverage)
        neck_inclusion = self._clamp01(neck_inclusion)

        score = (
            0.50 * completeness
            + 0.25 * vertical_coverage
            + 0.10 * (1.0 - border_contact)
            + 0.15 * (1.0 - neck_inclusion)
        )

        if vertical_coverage < 0.45:
            score -= 0.15
        if border_contact > 0.30:
            score -= 0.10
        if neck_inclusion > 0.25:
            score -= 0.20
        if completeness < 0.55:
            score -= 0.10

        return self._clamp01(score)



# =============================================================================
# Stage 8 — Diff 3: Expected-outline election helpers
# =============================================================================

def _contour_to_points(fc: "FeatureContour") -> np.ndarray:
    """Extract (N, 2) float32 point array from a FeatureContour."""
    pts = np.asarray(fc.points_px, dtype=np.float32)
    if pts.ndim == 3 and pts.shape[1] == 1:
        pts = pts[:, 0, :]
    return pts


def _resample_closed_curve(points: np.ndarray, n: int = 200) -> np.ndarray:
    """
    Resample a closed curve to exactly n evenly-spaced points by arc length.
    Used to normalise candidate and expected outlines to the same point count
    before distance comparison.
    """
    pts = np.asarray(points, dtype=np.float32)
    if len(pts) == 0:
        return np.zeros((0, 2), dtype=np.float32)
    if not np.allclose(pts[0], pts[-1]):
        pts = np.vstack([pts, pts[0]])
    seg = np.sqrt(np.sum(np.diff(pts, axis=0) ** 2, axis=1))
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(cum[-1])
    if total <= 1e-6:
        return np.repeat(pts[:1], n, axis=0)
    targets = np.linspace(0.0, total, n, endpoint=False)
    out = np.zeros((n, 2), dtype=np.float32)
    for i, t in enumerate(targets):
        j = int(np.searchsorted(cum, t, side="right") - 1)
        j = max(0, min(j, len(seg) - 1))
        denom = max(seg[j], 1e-6)
        alpha = (t - cum[j]) / denom
        out[i] = pts[j] * (1.0 - alpha) + pts[j + 1] * alpha
    return out


def _mean_bidirectional_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    Mean bidirectional nearest-point distance between two point sets.

    Preferred over Hausdorff for election because it is robust to single
    outlier points that Hausdorff would over-weight.
    """
    if len(a) == 0 or len(b) == 0:
        return float("inf")
    da = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)).min(axis=1).mean()
    db = np.sqrt(((b[:, None, :] - a[None, :, :]) ** 2).sum(axis=2)).min(axis=1).mean()
    return float((da + db) * 0.5)


def elect_body_contour_against_expected_outline(
    contours: List["FeatureContour"],
    expected_outline_px: np.ndarray,
    *,
    ownership_scores: Optional[Dict[int, float]] = None,
    ownership_threshold: float = 0.60,
) -> int:
    """
    Diff 3 election: choose the contour with the smallest mean bidirectional
    distance to the expected outline prior.

    Ownership gate still applies — only candidates that passed the ownership
    threshold are compared.  Returns -1 if no candidate passes the gate.
    """
    expected = _resample_closed_curve(expected_outline_px, n=200)
    if len(expected) == 0:
        return -1

    best_idx = -1
    best_dist = float("inf")

    for i, fc in enumerate(contours):
        if ownership_scores is not None:
            if float(ownership_scores.get(i, 0.0)) < ownership_threshold:
                continue
        pts = _resample_closed_curve(_contour_to_points(fc), n=200)
        if len(pts) == 0:
            continue
        dist = _mean_bidirectional_distance(pts, expected)
        if dist < best_dist:
            best_dist = dist
            best_idx = i

    return best_idx


# =============================================================================
# Stage 8b — Contour Assembly with Hierarchy
# =============================================================================

class ContourAssembler:
    def __init__(self, classifier: Optional[FeatureClassifier] = None,
                 min_area_px: int = 1000):
        self.classifier = classifier or FeatureClassifier()
        self.min_area_px = min_area_px

    def assemble(self, edge_image: np.ndarray, alpha_mask: np.ndarray,
                 mm_per_px: float,
                 body_region: Optional[Any] = None) -> List[FeatureContour]:
        contours, hierarchy = cv2.findContours(
            edge_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        if hierarchy is None:
            hierarchy = np.array([[[-1, -1, -1, -1]] * len(contours)])

        # Find body (largest)
        body_idx = -1
        max_area = 0
        for i, cnt in enumerate(contours):
            a = cv2.contourArea(cnt)
            if a > max_area and a >= self.min_area_px:
                max_area = a
                body_idx = i

        body_bbox = cv2.boundingRect(contours[body_idx]) if body_idx >= 0 else None

        # Build child map
        child_map: Dict[int, List[int]] = defaultdict(list)
        for i in range(len(contours)):
            parent = hierarchy[0][i][3]
            if parent >= 0:
                child_map[parent].append(i)

        # Pre-compute body_region values once for the filter
        _br_x = _br_y = _br_bw = _br_bh = None
        if body_region is not None:
            try:
                _br_x = int(body_region.x)
                _br_y = int(body_region.y)
                _br_bw = int(body_region.width)
                _br_bh = int(body_region.height)
            except (AttributeError, TypeError):
                body_region = None  # treat as absent if malformed

        features = []
        _pre_filter_rejected = 0
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < self.min_area_px:
                continue

            # ── Ownership pre-filter (Diff: ownership upstream) ─────────────
            # Reject candidates that cannot possibly score above the ownership
            # threshold, derived from the three dominant scoring terms:
            #   1. Bbox must intersect body region
            #   2. Vertical coverage must be ≥ 30% of body height
            #   3. Reject neck-only candidates (above midpoint, narrow)
            # When body_region is None the filter is entirely skipped.
            if body_region is not None:
                cx, cy, cw, ch = cv2.boundingRect(cnt)

                # 1. Bounding box must overlap body region
                no_overlap = (
                    cx + cw <= _br_x or cx >= _br_x + _br_bw or
                    cy + ch <= _br_y or cy >= _br_y + _br_bh
                )
                if no_overlap:
                    _pre_filter_rejected += 1
                    continue

                # 2. Minimum vertical coverage (≥ 30% of body height)
                if ch / max(_br_bh, 1) < 0.30:
                    _pre_filter_rejected += 1
                    continue

                # 3. Neck-heavy rejection: entirely above body midpoint AND narrow
                body_mid_y = _br_y + _br_bh * 0.50
                contour_center_y = cy + ch / 2.0
                if contour_center_y < body_mid_y and cw < _br_bw * 0.40:
                    _pre_filter_rejected += 1
                    continue
            # ─────────────────────────────────────────────────────────────────

            peri = cv2.arcLength(cnt, True)
            bbox = cv2.boundingRect(cnt)
            circ = 4 * np.pi * area / (peri ** 2) if peri > 0 else 0
            x, y, w, h = bbox
            aspect = max(w, h) / max(1, min(w, h))
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0

            ft, conf = self.classifier.classify(cnt, mm_per_px, bbox, body_bbox)
            hash_id = hashlib.md5(cnt.tobytes()).hexdigest()[:12]

            features.append(FeatureContour(
                points_px=cnt, feature_type=ft, confidence=conf,
                parent_idx=hierarchy[0][i][3],
                child_indices=child_map.get(i, []),
                area_px=area, perimeter_px=peri,
                circularity=circ, aspect_ratio=aspect, solidity=solidity,
                bbox_px=bbox, hash_id=hash_id))

        if _pre_filter_rejected > 0:
            logger.debug(
                f"Ownership pre-filter: rejected {_pre_filter_rejected} candidates "
                f"before classification"
            )
        logger.info(f"Assembled {len(features)} feature contours from {len(contours)} raw")

        # ── Deduplication: Remove concentric duplicates (IoU > 0.85 with body) ──
        # Body outline often produces both outer and inner edge traces. The inner
        # trace gets misclassified. Remove contours whose bbox IoU with body > 0.85.
        features = self._deduplicate_concentric(features)

        return features

    def _deduplicate_concentric(self, features: List[FeatureContour],
                                 iou_threshold: float = 0.85) -> List[FeatureContour]:
        """Remove contours that are near-duplicates of the body contour."""
        if len(features) < 2:
            return features

        # Find body contour (largest BODY_OUTLINE or largest overall)
        body_idx = -1
        body_area = 0
        for i, fc in enumerate(features):
            if fc.feature_type == FeatureType.BODY_OUTLINE and fc.area_px > body_area:
                body_idx = i
                body_area = fc.area_px
        if body_idx < 0:
            # No explicit body outline, use largest contour
            for i, fc in enumerate(features):
                if fc.area_px > body_area:
                    body_idx = i
                    body_area = fc.area_px
        if body_idx < 0:
            return features

        body_bbox = features[body_idx].bbox_px
        bx, by, bw, bh = body_bbox

        keep = []
        removed = 0
        for i, fc in enumerate(features):
            if i == body_idx:
                keep.append(fc)
                continue
            # Calculate IoU of bounding boxes
            x, y, w, h = fc.bbox_px
            inter_x1 = max(bx, x)
            inter_y1 = max(by, y)
            inter_x2 = min(bx + bw, x + w)
            inter_y2 = min(by + bh, y + h)
            inter_w = max(0, inter_x2 - inter_x1)
            inter_h = max(0, inter_y2 - inter_y1)
            inter_area = inter_w * inter_h
            union_area = bw * bh + w * h - inter_area
            iou = inter_area / union_area if union_area > 0 else 0

            if iou > iou_threshold:
                # This contour is a near-duplicate of body
                logger.debug(f"Dedup: removed contour {fc.hash_id} (IoU={iou:.2f} with body)")
                removed += 1
            else:
                keep.append(fc)

        if removed > 0:
            logger.info(f"Deduplication: removed {removed} concentric duplicates (IoU>{iou_threshold})")
        return keep


# =============================================================================
# Stage 11 — SVG Export
# =============================================================================

def write_svg(contours_by_layer: Dict[str, List[np.ndarray]],
              output_path: str, width_mm: float = 600, height_mm: float = 800,
              stroke_width: float = 0.5) -> bool:
    """Write contours to SVG with layer groups."""
    try:
        # Layer colors
        colors = {
            "BODY_OUTLINE": "#000000", "PICKUP_ROUTE": "#FF0000",
            "NECK_POCKET": "#0000FF", "CONTROL_CAVITY": "#00AA00",
            "BRIDGE_ROUTE": "#FF8800", "F_HOLE": "#880088",
            "SOUNDHOLE": "#008888", "JACK_ROUTE": "#888800",
            "UNKNOWN": "#999999",
        }

        # Register inkscape namespace for layer grouping
        svg = Element("svg", xmlns="http://www.w3.org/2000/svg",
                       width=f"{width_mm}mm", height=f"{height_mm}mm",
                       viewBox=f"0 0 {width_mm} {height_mm}")
        svg.set("xmlns:inkscape", "http://www.inkscape.org/namespaces/inkscape")

        for layer_name, point_lists in contours_by_layer.items():
            g = SubElement(svg, "g", id=layer_name)
            g.set("inkscape:label", layer_name)
            g.set("inkscape:groupmode", "layer")
            color = colors.get(layer_name, "#999999")

            for pts in point_lists:
                if len(pts) < 3:
                    continue
                pts_2d = pts.reshape(-1, 2)
                d_parts = [f"M {pts_2d[0][0]:.3f},{pts_2d[0][1]:.3f}"]
                for p in pts_2d[1:]:
                    d_parts.append(f"L {p[0]:.3f},{p[1]:.3f}")
                d_parts.append("Z")

                SubElement(g, "path", d=" ".join(d_parts),
                           fill="none", stroke=color,
                           **{"stroke-width": str(stroke_width)})

        tree = ElementTree(svg)
        with open(output_path, "wb") as f:
            tree.write(f, xml_declaration=True, encoding="utf-8")
        logger.info(f"SVG written: {output_path}")
        return True
    except Exception as e:
        logger.error(f"SVG export failed: {e}")
        return False


# =============================================================================
# Stage 11b — DXF Export
# =============================================================================

def write_dxf(contours_by_layer: Dict[str, List[np.ndarray]],
              output_path: str, version: str = "R12") -> bool:
    """Write contours to DXF with layers (R2010+ format with proper bounds)."""
    if not EZDXF_AVAILABLE:
        logger.error("ezdxf not installed — pip install ezdxf")
        return False
    try:
        # Force R12 (AC1009) per CLAUDE.md DXF standards - LINE entities only
        dxf_ver = {"R12": "R12", "R2010": "R2010", "R2013": "R2013", "R2018": "R2018"}.get(version, "R12")
        doc = ezdxf.new(dxf_ver)

        # Set proper units (mm, metric) per CLAUDE.md
        doc.header['$INSUNITS'] = 4  # mm
        doc.header['$MEASUREMENT'] = 1  # metric

        msp = doc.modelspace()

        # Track bounds for EXTMIN/EXTMAX
        all_xs: List[float] = []
        all_ys: List[float] = []

        for layer_name, point_lists in contours_by_layer.items():
            if layer_name not in doc.layers:
                doc.layers.add(layer_name)
            for pts in point_lists:
                if len(pts) < 3:
                    continue
                pts_2d = pts.reshape(-1, 2)
                pts_list = [(float(p[0]), float(p[1])) for p in pts_2d]

                # Track bounds
                all_xs.extend([p[0] for p in pts_list])
                all_ys.extend([p[1] for p in pts_list])

                # Use LINE entities (closed contour as individual lines per CLAUDE.md)
                for i in range(len(pts_list)):
                    p1 = pts_list[i]
                    p2 = pts_list[(i + 1) % len(pts_list)]
                    msp.add_line(p1, p2, dxfattribs={"layer": layer_name})

        # Set EXTMIN/EXTMAX bounds from actual geometry
        if all_xs and all_ys:
            doc.header['$EXTMIN'] = (min(all_xs), min(all_ys), 0)
            doc.header['$EXTMAX'] = (max(all_xs), max(all_ys), 0)

        doc.saveas(output_path)
        logger.info(f"DXF written: {output_path} ({dxf_ver})")
        return True
    except Exception as e:
        logger.error(f"DXF export failed: {e}")
        return False


# =============================================================================
# Stage 11c — JSON Export
# =============================================================================

def write_features_json(features: Dict[FeatureType, List[FeatureContour]],
                        output_path: str,
                        calibration: Optional[CalibrationResult] = None) -> bool:
    try:
        data = {
            "version": "2.0",
            "calibration": {
                "mm_per_px": calibration.mm_per_px,
                "source": calibration.source.value,
                "confidence": calibration.confidence,
            } if calibration else None,
            "features": {},
        }
        for ft, contours in features.items():
            entries = []
            for c in contours:
                if c.points_mm is not None:
                    entries.append({
                        "points": c.points_mm.tolist(),
                        "confidence": c.confidence,
                        "hash": c.hash_id,
                    })
            if entries:
                data["features"][ft.value] = entries

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        return False


# =============================================================================
# Stage -1 — Orientation Detection
# =============================================================================

LANDSCAPE_ASPECT_THRESHOLD = 1.8
TILT_THRESHOLD_DEG = 5.0
BG_THRESH_LIGHT = 200
BG_THRESH_DARK = 80


class OrientationDetector:
    """Detects instrument orientation and returns a rotation-corrected image."""

    def __init__(self, landscape_aspect: float = LANDSCAPE_ASPECT_THRESHOLD,
                 tilt_threshold: float = TILT_THRESHOLD_DEG,
                 bg_fill: tuple = (245, 245, 245)):
        self.landscape_aspect = landscape_aspect
        self.tilt_threshold = tilt_threshold
        self.bg_fill = bg_fill

    def detect_and_correct(self, image: np.ndarray,
                           is_dark_bg: bool = False,
                           fg_mask: Optional[np.ndarray] = None) -> OrientationResult:
        orig_h, orig_w = image.shape[:2]
        notes = []

        # Step 1: binary silhouette
        if fg_mask is not None and np.sum(fg_mask > 0) > (orig_h * orig_w * 0.05):
            thresh = fg_mask.copy()
            notes.append("Silhouette from fg_mask")
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) \
                if len(image.shape) == 3 else image
            if is_dark_bg:
                _, thresh = cv2.threshold(gray, BG_THRESH_DARK, 255, cv2.THRESH_BINARY)
            else:
                _, thresh = cv2.threshold(gray, BG_THRESH_LIGHT, 255, cv2.THRESH_BINARY_INV)

        kernel = np.ones((9, 9), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            notes.append("No silhouette found — returning image unchanged")
            return OrientationResult(
                orientation="portrait", coarse_angle=0, tilt_angle=0,
                total_rotation=0, rotated_image=image.copy(),
                original_shape=(orig_h, orig_w), canvas_shape=(orig_h, orig_w),
                notes=notes)

        largest = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(largest)
        center, (rw, rh), angle = rect

        # Step 2: determine coarse orientation
        long_dim = max(rw, rh)
        short_dim = min(rw, rh)
        aspect = long_dim / max(short_dim, 1)
        notes.append(f"Silhouette minAreaRect: {rw:.0f}x{rh:.0f} at {angle:.1f} deg, aspect={aspect:.2f}")

        if aspect > self.landscape_aspect and rw > rh:
            orientation = "landscape"
            coarse_angle = 90.0
            notes.append(f"Landscape detected (aspect {aspect:.2f} > {self.landscape_aspect}) -> 90 deg CCW")
        else:
            orientation = "portrait"
            coarse_angle = 0.0
            notes.append("Portrait orientation")

        # Step 3: apply coarse rotation
        if coarse_angle == 90:
            working = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            working = image.copy()

        wh, ww = working.shape[:2]

        # Step 4: measure residual tilt on coarse-corrected image
        gray_w = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY) if len(working.shape) == 3 else working
        if is_dark_bg:
            _, thresh_w = cv2.threshold(gray_w, BG_THRESH_DARK, 255, cv2.THRESH_BINARY)
        else:
            _, thresh_w = cv2.threshold(gray_w, BG_THRESH_LIGHT, 255, cv2.THRESH_BINARY_INV)
        thresh_w = cv2.morphologyEx(thresh_w, cv2.MORPH_CLOSE, kernel, iterations=3)
        contours_w, _ = cv2.findContours(thresh_w, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        tilt_angle = 0.0
        if contours_w:
            lw = max(contours_w, key=cv2.contourArea)
            rect_w = cv2.minAreaRect(lw)
            _, (rw2, rh2), angle_w = rect_w
            if rw2 < rh2:
                tilt_angle = angle_w
            else:
                tilt_angle = angle_w + 90.0

            if abs(tilt_angle) > self.tilt_threshold:
                notes.append(f"Residual tilt: {tilt_angle:.1f} deg -> applying affine correction")
            else:
                notes.append(f"Tilt {tilt_angle:.1f} deg below threshold ({self.tilt_threshold} deg) — skipped")
                tilt_angle = 0.0

        # Step 5: apply tilt correction
        inv_matrix = None
        if abs(tilt_angle) > self.tilt_threshold:
            cx, cy = ww // 2, wh // 2
            M = cv2.getRotationMatrix2D((cx, cy), tilt_angle, 1.0)
            cos_a = abs(np.cos(np.radians(tilt_angle)))
            sin_a = abs(np.sin(np.radians(tilt_angle)))
            new_w = int(wh * sin_a + ww * cos_a)
            new_h = int(wh * cos_a + ww * sin_a)
            M[0, 2] += (new_w / 2) - cx
            M[1, 2] += (new_h / 2) - cy
            working = cv2.warpAffine(working, M, (new_w, new_h),
                                     borderValue=self.bg_fill)
            M_inv = cv2.getRotationMatrix2D((new_w / 2, new_h / 2), -tilt_angle, 1.0)
            M_inv[0, 2] += cx - (new_w / 2)
            M_inv[1, 2] += cy - (new_h / 2)
            inv_matrix = M_inv

        total_rotation = coarse_angle + tilt_angle
        canvas_h, canvas_w = working.shape[:2]
        notes.append(f"Total rotation applied: {total_rotation:.1f} deg")

        logger.info(
            f"OrientationDetector: {orientation}, coarse={coarse_angle} deg, "
            f"tilt={tilt_angle:.1f} deg, total={total_rotation:.1f} deg, "
            f"canvas={canvas_w}x{canvas_h}")

        return OrientationResult(
            orientation=orientation, coarse_angle=coarse_angle,
            tilt_angle=tilt_angle, total_rotation=total_rotation,
            rotated_image=working, original_shape=(orig_h, orig_w),
            canvas_shape=(canvas_h, canvas_w), inverse_matrix=inv_matrix,
            notes=notes)


def adaptive_body_threshold(row_widths: np.ndarray) -> float:
    """Estimate body-row threshold from the row-width profile.

    Uses lower-quartile-of-nonzero * 2.5 to separate neck from body rows.
    Capped at 85% of max row width to prevent exceeding actual widths.
    """
    nonzero = row_widths[row_widths > 20]
    if len(nonzero) == 0:
        return float(row_widths.max() * 0.4)
    neck_px = float(np.percentile(nonzero, 25))
    raw_threshold = neck_px * 2.5
    cap = float(row_widths.max()) * 0.85
    return min(raw_threshold, cap)


def _apply_orientation_to_original(
    original_image: np.ndarray,
    orient: OrientationResult,
    bg_fill: Tuple[int, int, int] = (245, 245, 245),
) -> np.ndarray:
    """Apply the same rotation+tilt correction to original_image
    that was applied to the working image during orientation detection."""
    result = original_image

    # Step 1: coarse 90 deg rotation
    if orient.coarse_angle == 90:
        result = cv2.rotate(result, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Step 2: tilt correction
    if abs(orient.tilt_angle) > 0 and orient.inverse_matrix is not None:
        wh, ww = result.shape[:2]
        tilt = orient.tilt_angle
        cos_a = abs(np.cos(np.radians(tilt)))
        sin_a = abs(np.sin(np.radians(tilt)))
        new_w = int(wh * sin_a + ww * cos_a)
        new_h = int(wh * cos_a + ww * sin_a)
        cx, cy = ww // 2, wh // 2
        M = cv2.getRotationMatrix2D((cx, cy), tilt, 1.0)
        M[0, 2] += (new_w / 2) - cx
        M[1, 2] += (new_h / 2) - cy
        result = cv2.warpAffine(result, M, (new_w, new_h),
                                borderValue=bg_fill)

    return result


def emit_calibration_guidance(
    calibration,
    spec_name: Optional[str],
    body_h_px: Optional[float],
    result,
) -> None:
    """Append actionable calibration warnings when confidence is low."""
    src = calibration.source.value if hasattr(calibration.source, 'value') \
        else str(calibration.source)

    if calibration.confidence >= 0.5:
        return

    available_specs = [k for k in INSTRUMENT_SPECS.keys() if k != "reference_objects"]

    msgs = [
        f"Low scale confidence ({calibration.confidence:.2f}) "
        f"— source: {src}. Dimensions may be inaccurate."
    ]

    if not spec_name:
        msgs.append(
            f"   Improve calibration: add  --spec <name>  "
            f"to enable body-height calibration.")
        msgs.append(
            f"   Available specs: {', '.join(available_specs)}")
    elif spec_name and (not body_h_px or body_h_px <= 0):
        msgs.append(
            f"   --spec '{spec_name}' supplied but body height could not be "
            f"detected (body_height_px={body_h_px}). "
            f"Try --bg rembg for better background removal.")

    if src == "feature_scale":
        msgs.append(
            "   Scale estimated from detected instrument features "
            "(pickup/soundhole/f-hole dimensions). "
            "Verify before cutting expensive material.")

    if not any("--mm" in m for m in result.warnings):
        msgs.append(
            f"   Or supply  --mm <body_height_mm> --px <body_height_pixels>  "
            f"for direct measurement (highest accuracy).")

    for msg in msgs:
        result.warnings.append(msg)
        logger.warning(msg)


def rotate_contours_back(contours: Dict[str, List[np.ndarray]],
                         orient_result: OrientationResult) -> Dict[str, List[np.ndarray]]:
    """Rotate SVG/DXF contour point arrays back to the original image frame."""
    if orient_result.total_rotation == 0:
        return contours

    all_pts = []
    for pts_list in contours.values():
        for pts in pts_list:
            all_pts.append(pts)
    if not all_pts:
        return contours

    combined = np.vstack(all_pts)
    cx = float(combined[:, 0].mean())
    cy = float(combined[:, 1].mean())

    angle_rad = np.radians(-orient_result.total_rotation)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    rotated: Dict[str, List[np.ndarray]] = {}
    for layer, pts_list in contours.items():
        rotated[layer] = []
        for pts in pts_list:
            dx = pts[:, 0] - cx
            dy = pts[:, 1] - cy
            rx = cx + dx * cos_a - dy * sin_a
            ry = cy + dx * sin_a + dy * cos_a
            rotated[layer].append(np.stack([rx, ry], axis=1))
    return rotated


# =============================================================================
# Main Vectorizer
# =============================================================================

class PhotoVectorizerV2:
    """
    Standalone photographic instrument outline extractor.
    Photo in -> SVG/DXF out.
    """

    def __init__(self,
                 bg_method: BGRemovalMethod = BGRemovalMethod.AUTO,
                 sam_checkpoint: Optional[str] = None,
                 simplify_tolerance_mm: float = 0.3,
                 min_contour_area_px: int = 3000,
                 dxf_version: str = "R12",
                 default_unit: Unit = Unit.MM,
                 default_dpi: float = 300.0):
        self.bg_method = bg_method
        self.simplify_tolerance_mm = simplify_tolerance_mm
        self.min_contour_area_px = min_contour_area_px
        self.dxf_version = dxf_version
        self.default_unit = default_unit

        self.input_classifier = InputClassifier()
        self.perspective = PerspectiveCorrector()
        self.bg_remover = BackgroundRemover(sam_checkpoint)
        self.edge_detector = PhotoEdgeDetector()
        self.feature_classifier = FeatureClassifier()
        self.assembler = ContourAssembler(self.feature_classifier, min_contour_area_px)
        self.calibrator = ScaleCalibrator(default_dpi)
        self.exif = EXIFExtractor()
        self.body_isolator = BodyIsolator()
        self.splitter = MultiInstrumentSplitter()
        self.orientation_detector = OrientationDetector()
        self.family_classifier = InstrumentFamilyClassifier()
        self.batch_smoother = BatchCalibrationSmoother()
        self.contour_merger = ContourMerger()
        self.plausibility_scorer = ContourPlausibilityScorer()

        # Lazy imports to avoid circular dependency
        from contour_stage import ContourStage
        from body_isolation_stage import BodyIsolationStage
        from geometry_authority import GeometryAuthority
        from geometry_coach_v2 import GeometryCoachV2

        self.contour_stage = ContourStage()
        self.geometry_authority = GeometryAuthority()
        self.body_isolation_stage = BodyIsolationStage(self.body_isolator)
        self.geometry_coach_v2 = GeometryCoachV2()
        self.enable_body_isolation_coach = True

        logger.info(f"PhotoVectorizerV2 initialized (BG: {bg_method.value})")

    def extract(self, source_path: Union[str, Path],
                output_dir: Optional[Union[str, Path]] = None, *,
                spec_name: Optional[str] = None,
                known_dimension_mm: Optional[float] = None,
                known_dimension_px: Optional[float] = None,
                known_unit: Optional[Unit] = None,
                correct_perspective: bool = True,
                export_dxf: bool = True,
                export_svg: bool = True,
                export_json: bool = False,
                debug_images: bool = False,
                enable_body_isolation_coach: Optional[bool] = None,
                source_type: str = "auto",
                gap_closing_level: str = "normal",
                ) -> Union[PhotoExtractionResult, List[PhotoExtractionResult]]:
        """
        Extract instrument outline from image.

        Parameters
        ----------
        source_type : str
            "auto" (default) - auto-detect AI vs photo
            "ai"   - force AI extraction path (simpler, needs spec_name)
            "photo" - force traditional 12-stage photo pipeline
            "blueprint" - PDF blueprint with light gray lines (uses light_line_body_extractor)
            "silhouette" - photo with dark background (uses flood-fill extraction)
        """

        start_time = time.time()
        source = Path(source_path)
        out_dir = Path(output_dir) if output_dir else source.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        # ── AI Path Routing (v3) ─────────────────────────────────────────────
        use_ai_path = False
        if source_type == "ai":
            use_ai_path = True
            logger.info("AI path: forced via source_type='ai'")
        elif source_type == "auto":
            use_ai_path = self._detect_ai_image(str(source))
            if use_ai_path:
                logger.info("AI path: auto-detected AI-generated image")
        # source_type == "photo" → use_ai_path stays False

        if use_ai_path:
            return self._extract_ai_path(
                source=source,
                out_dir=out_dir,
                spec_name=spec_name,
                export_dxf=export_dxf,
                export_svg=export_svg,
                debug_images=debug_images,
            )

        # ── Blueprint Path (light line extraction for PDF blueprints) ───────
        if source_type == "blueprint":
            return self._extract_blueprint_path(
                source=source,
                out_dir=out_dir,
                known_dimension_mm=known_dimension_mm,
                export_dxf=export_dxf,
                export_svg=export_svg,
                debug_images=debug_images,
                gap_closing_level=gap_closing_level,
            )

        # ── Silhouette Path (flood-fill for photos with dark backgrounds) ───
        if source_type == "silhouette":
            return self._extract_silhouette_path(
                source=source,
                out_dir=out_dir,
                known_dimension_mm=known_dimension_mm,
                export_dxf=export_dxf,
                export_svg=export_svg,
                debug_images=debug_images,
            )

        # ── Photo Path (12-stage pipeline) ───────────────────────────────────

        # ── Compatibility gate: body-isolation coach can be disabled either
        #    per-call or globally via environment for tests / production.
        #
        # Priority:
        #   1) explicit function argument
        #   2) instance default self.enable_body_isolation_coach
        #   3) env var PHOTO_VECTORIZER_ENABLE_BODY_ISOLATION_COACH
        #
        # Accepted falsy env values: 0, false, no, off
        env_flag_raw = os.getenv(
            "PHOTO_VECTORIZER_ENABLE_BODY_ISOLATION_COACH",
            "1" if getattr(self, "enable_body_isolation_coach", True) else "0",
        )
        env_flag = str(env_flag_raw).strip().lower() not in {"0", "false", "no", "off"}
        coach_enabled = (
            env_flag
            if enable_body_isolation_coach is None
            else bool(enable_body_isolation_coach)
        )

        result = PhotoExtractionResult(source_path=str(source))
        debug_paths: Dict[str, str] = {}

        # ── Load image ──────────────────────────────────────────────────────
        image = self._load_image(source)
        if image is None:
            result.warnings.append(f"Failed to load: {source}")
            return result
        orig_h, orig_w = image.shape[:2]
        logger.info(f"Loaded {source.name}: {orig_w}x{orig_h}")

        if debug_images:
            p = str(out_dir / f"{source.stem}_00_original.jpg")
            cv2.imwrite(p, image)
            debug_paths["original"] = p

        # ── Multi-instrument detection ──────────────────────────────────────
        split = self.splitter.detect_and_split(image)
        if split.is_multi:
            all_results: List[PhotoExtractionResult] = []
            for idx, (cx, cy, cw, ch) in enumerate(split.crops):
                crop_img = image[cy:cy+ch, cx:cx+cw]
                crop_stem = f"{source.stem}_instrument_{idx+1}"
                crop_path = out_dir / f"{crop_stem}.png"
                cv2.imwrite(str(crop_path), crop_img)
                r = self.extract(
                    str(crop_path), output_dir=str(out_dir),
                    spec_name=spec_name,
                    known_dimension_mm=known_dimension_mm,
                    known_dimension_px=known_dimension_px,
                    known_unit=known_unit,
                    correct_perspective=correct_perspective,
                    export_dxf=export_dxf, export_svg=export_svg,
                    export_json=export_json, debug_images=debug_images)
                if isinstance(r, list):
                    all_results.extend(r)
                else:
                    all_results.append(r)
            return all_results

        # ── Stage 0: Dark background detection ──────────────────────────────
        original_image = image.copy()  # preserve pre-inversion for BodyIsolator
        bg_type = BackgroundTypeDetector().detect(image)
        is_dark_bg = (bg_type == "solid_dark")
        result.dark_background_detected = (bg_type in ("solid_dark", "textured_dark"))
        if bg_type == "solid_dark":
            image = cv2.bitwise_not(image)
            logger.info("Solid dark background -> image inverted")
        elif bg_type == "textured_dark":
            logger.info("Textured dark background detected — NOT inverting")
            result.warnings.append(
                f"Textured dark background ({bg_type}) — consider using --bg rembg for best results")

        # ── Stage 0.5: Orientation detection ─────────────────────────────────
        orient = self.orientation_detector.detect_and_correct(image, is_dark_bg=is_dark_bg)
        if orient.total_rotation != 0:
            image = orient.rotated_image
            original_image = _apply_orientation_to_original(original_image, orient)
            self.body_isolator.use_adaptive = True
            result.warnings.append(
                f"Orientation corrected: {orient.orientation}, "
                f"{orient.total_rotation:.1f} deg rotation applied")
        else:
            self.body_isolator.use_adaptive = False

        # ── Stage 1: EXIF DPI ───────────────────────────────────────────────
        exif_dpi = self.exif.get_dpi(source)

        # ── Stage 2: Classify input ─────────────────────────────────────────
        result.input_type, _conf, _meta = self.input_classifier.classify(image)
        logger.info(f"Input: {result.input_type.value} (confidence {_conf:.2f})")

        if result.input_type == InputType.BLUEPRINT:
            result.warnings.append(
                "Input looks like a blueprint. Photo Vectorizer works best with photos.")

        # ── Stage 3: Perspective correction ─────────────────────────────────
        if correct_perspective:
            image, corrected = self.perspective.correct(image)
            result.perspective_corrected = corrected

        img_h, img_w = image.shape[:2]

        if debug_images and result.perspective_corrected:
            p = str(out_dir / f"{source.stem}_01_perspective.jpg")
            cv2.imwrite(p, image)
            debug_paths["perspective"] = p

        # ── Stage 4: Background removal ─────────────────────────────────────
        fg_image, alpha_mask, bg_used = self.bg_remover.remove(
            image, self.bg_method, is_dark_bg=is_dark_bg)
        result.bg_method_used = bg_used
        logger.info(f"Background removal: {bg_used}")

        if debug_images:
            cv2.imwrite(str(out_dir / f"{source.stem}_02_foreground.jpg"), fg_image)
            cv2.imwrite(str(out_dir / f"{source.stem}_03_alpha.png"), alpha_mask)
            debug_paths["foreground"] = str(out_dir / f"{source.stem}_02_foreground.jpg")
            debug_paths["alpha"] = str(out_dir / f"{source.stem}_03_alpha.png")

        # ── Stage 4.5: Body isolation (typed + coachable) ──────────────────
        from body_isolation_stage import BodyIsolationParams
        body_isolation_params = BodyIsolationParams(
            use_adaptive=self.body_isolator.use_adaptive,
        )
        body_isolation_result = self.body_isolation_stage.run(
            image,
            fg_mask=alpha_mask,
            original_image=original_image,
            instrument_family=None,  # family not known yet at this point
            geometry_authority=self.geometry_authority,
            params=body_isolation_params,
        )
        body_region = body_isolation_result.body_region
        result.body_isolation = body_isolation_result

        if body_isolation_result.review_required:
            result.warnings.append(
                f"Body isolation flagged for review "
                f"(score={body_isolation_result.completeness_score:.2f})"
            )

        # ── Stage 4.6: Rough mpp estimate for adaptive kernel sizing ────────
        rough_mpp = compute_rough_mpp(body_region, spec_name)
        logger.info(f"Rough mpp for kernel sizing: {rough_mpp:.4f}")

        # ── Stage 5: Edge detection ─────────────────────────────────────────
        edges = self.edge_detector.detect(
            fg_image, alpha_mask,
            input_type=result.input_type.value,
            mpp=rough_mpp,
            body_region=body_region,
        )

        if debug_images:
            p = str(out_dir / f"{source.stem}_04_edges.png")
            cv2.imwrite(p, edges)
            debug_paths["edges"] = p

        # ── Stage 6.5: Instrument family classification ─────────────────
        instrument_family = self.family_classifier.classify(body_region)
        logger.info(f"Instrument family: {instrument_family.family} (conf={instrument_family.confidence:.2f})")

        # ── Stage 7: Calibration (with body isolation + DPI estimation) ───
        body_h_px = float(body_region.height_px) if body_region.height_px > 0 else None
        calibration = self.calibrator.calibrate(
            image, known_mm=known_dimension_mm, known_px=known_dimension_px,
            spec_name=spec_name, image_dpi=exif_dpi,
            unit=known_unit or self.default_unit,
            fg_mask=alpha_mask, body_height_px=body_h_px,
            family_classification=instrument_family,
            edge_image=edges)
        mpp = calibration.mm_per_px
        logger.info(f"Scale: {calibration.message} (mpp={mpp:.4f})")

        emit_calibration_guidance(calibration, spec_name, body_h_px, result)

        # ── Stage 8: Contour stage (assembly + merge + election + grid) ────
        family = instrument_family.family if instrument_family else InstrumentFamily.UNKNOWN

        # ── Diff 2/3: Build typed BodyModel from Stage 4.5 evidence ─────────
        body_model = self._build_body_model(
            body_result=body_isolation_result,
            family=family,
            spec_name=spec_name,
            calibration=calibration,
        )
        result.body_model = body_model

        from contour_stage import StageParams
        stage_params = StageParams()
        contour_result = self.contour_stage.run(
            edges=edges,
            alpha_mask=alpha_mask,
            body_region=body_region,
            body_model=body_model,
            calibration=calibration,
            family=family,
            image_shape=(img_h, img_w),
            image=image if debug_images else None,
            debug_images=debug_images,
            spec_name=spec_name,
        )

        # ── Stage 8.5: Optional V2 body-ownership coaching ─────────────────
        # The coach may rerun body isolation and/or contour stage, but only
        # within bounded retry rules and monotonic improvement gates.
        if coach_enabled:
            body_isolation_result, contour_result, coach_decision = (
                self.geometry_coach_v2.evaluate(
                    body_stage_runner=self.body_isolation_stage,
                    contour_stage_runner=self.contour_stage,
                    image=image,
                    fg_mask=alpha_mask,
                    original_image=original_image,
                    instrument_family=instrument_family,
                    geometry_authority=self.geometry_authority,
                    contour_inputs={
                        "edges": edges,
                        "alpha_mask": alpha_mask,
                        "calibration": calibration,
                        "family": family,
                        "image_shape": (img_h, img_w),
                        "params": stage_params,
                    },
                    body_result=body_isolation_result,
                    contour_result=contour_result,
                )
            )
            result.body_isolation = body_isolation_result
            result.geometry_coach_v2 = coach_decision

            if coach_decision.action == "manual_review_required":
                result.warnings.append(coach_decision.reason)
        else:
            # Explicitly surface the disabled state for diagnostics/replay clarity.
            result.geometry_coach_v2 = None
            result.diagnostics = getattr(result, "diagnostics", {}) or {}
            result.diagnostics["body_isolation_coach_enabled"] = False
            result.diagnostics["body_isolation_coach_source"] = "env_or_callsite_disabled"

        # Surface stage outputs
        result.contour_stage = contour_result
        result.export_blocked = bool(getattr(contour_result, "export_blocked", False))
        result.export_block_reason = getattr(contour_result, "block_reason", None)

        if result.export_blocked:
            result.warnings.append(
                f"Export blocked: "
                f"{result.export_block_reason or 'low contour plausibility'}"
            )

        # Maintain compatibility with downstream result fields
        feature_contours = list(getattr(contour_result, "feature_contours_post_grid", []) or [])
        body_fc = getattr(contour_result, "body_contour_final", None)

        if body_fc is None and not feature_contours:
            result.warnings.append("No contours found")
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        result.calibration = calibration
        mpp = calibration.mm_per_px

        # ── Stage 8.5: Body height cap (trim guitar stand merged with body) ──
        # If body height exceeds spec height × 1.2, trim from bottom
        if body_fc and spec_name and mpp > 0:
            spec = get_ai_spec(spec_name)
            if spec and "body" in spec:
                expected_h_mm = spec["body"][0]  # body tuple is (length, width)
                max_h_px = (expected_h_mm * 1.2) / mpp  # 20% tolerance
                bx, by, bw, bh = body_fc.bbox_px
                if bh > max_h_px:
                    # Body too tall — likely includes guitar stand
                    trim_amount_px = bh - max_h_px
                    new_bottom_y = by + bh - trim_amount_px
                    logger.info(f"Body height cap: {bh:.0f}px > {max_h_px:.0f}px max, "
                                f"trimming {trim_amount_px:.0f}px from bottom")
                    # Trim points below new_bottom_y
                    if body_fc.points_px is not None and len(body_fc.points_px) > 0:
                        # Handle OpenCV contour format (Nx1x2) vs simple (Nx2)
                        pts = body_fc.points_px
                        if pts.ndim == 3:
                            pts = pts.squeeze(axis=1)  # (N,1,2) -> (N,2)
                        # In image coords, Y increases downward
                        mask = pts[:, 1] <= new_bottom_y
                        trimmed_points = pts[mask]
                        if len(trimmed_points) >= 3:
                            # Recalculate bbox BEFORE restoring shape (trimmed_points is Nx2 here)
                            xs = trimmed_points[:, 0]
                            ys = trimmed_points[:, 1]
                            body_fc.bbox_px = (
                                int(xs.min()), int(ys.min()),
                                int(xs.max() - xs.min()), int(ys.max() - ys.min())
                            )
                            # Restore to original shape if needed
                            if body_fc.points_px.ndim == 3:
                                trimmed_points = trimmed_points[:, np.newaxis, :]
                            body_fc.points_px = trimmed_points
                            result.warnings.append(
                                f"Body height capped: trimmed {trim_amount_px:.0f}px "
                                f"(likely guitar stand)")
                        else:
                            logger.warning("Height cap would leave <3 points, skipping")

        # ── Stage 9: Convert to mm coordinates ──────────────────────────────
        # Center on body
        if body_fc:
            bx, by, bw, bh = body_fc.bbox_px
            cx = (bx + bw / 2) * mpp
            cy = (img_h - (by + bh / 2)) * mpp
        else:
            cx = cy = 0

        features_by_type: Dict[FeatureType, List[FeatureContour]] = defaultdict(list)
        export_contours: Dict[str, List[np.ndarray]] = defaultdict(list)

        # Filter out contours below body bbox (e.g., guitar stand)
        # Stand appears below body bottom edge in product photos
        if body_fc:
            _, body_y, _, body_h = body_fc.bbox_px
            body_bottom_px = body_y + body_h
            filtered_contours = []
            for fc in feature_contours:
                # Skip body contour from this filter (it defines the bbox)
                if fc.feature_type.value == "body_outline":
                    filtered_contours.append(fc)
                    continue
                # Get contour centroid Y
                cnt_y = fc.bbox_px[1] + fc.bbox_px[3] / 2
                if cnt_y > body_bottom_px + 20:  # 20px tolerance
                    logger.debug(f"Filtered below-body contour: {fc.feature_type.value} at Y={cnt_y:.0f} (body bottom={body_bottom_px:.0f})")
                    result.warnings.append(f"Filtered contour below body: {fc.feature_type.value} (likely guitar stand)")
                else:
                    filtered_contours.append(fc)
            feature_contours = filtered_contours

        for fc in feature_contours:
            pts_mm = self._to_mm(fc.points_px, mpp, img_h, cx, cy,
                                 self.simplify_tolerance_mm)
            if pts_mm is None:
                continue
            fc.points_mm = pts_mm
            features_by_type[fc.feature_type].append(fc)
            export_contours[fc.feature_type.value.upper()].append(pts_mm)

        result.features = dict(features_by_type)
        result.body_contour = body_fc

        # Body dimensions
        if body_fc and body_fc.points_mm is not None:
            xs = body_fc.points_mm[:, 0]
            ys = body_fc.points_mm[:, 1]
            w_mm = float(xs.max() - xs.min())
            h_mm = float(ys.max() - ys.min())
            # Normalize: guitar body is taller than wide (height > width)
            if w_mm > h_mm:
                h_mm, w_mm = w_mm, h_mm  # swap if landscape orientation
            result.body_dimensions_mm = (h_mm, w_mm)
            result.body_dimensions_inch = (h_mm / 25.4, w_mm / 25.4)

        # ── Back-project orientation if rotated ───────────────────────────
        if orient.total_rotation != 0:
            export_contours = rotate_contours_back(export_contours, orient)

        # ── Determine SVG/DXF viewbox from contours ─────────────────────────
        all_pts = []
        for pts_list in export_contours.values():
            for pts in pts_list:
                all_pts.append(pts)
        if all_pts:
            combined = np.vstack(all_pts)
            x_min, y_min = combined.min(axis=0)
            x_max, y_max = combined.max(axis=0)
            svg_w = float(x_max - x_min) + 20
            svg_h = float(y_max - y_min) + 20
            # Shift all contours so min is at (10, 10) margin
            shifted: Dict[str, List[np.ndarray]] = {}
            for layer, pts_list in export_contours.items():
                shifted[layer] = [p - np.array([x_min - 10, y_min - 10]) for p in pts_list]
            export_contours = shifted
        else:
            svg_w, svg_h = 600, 800

        # ── Stage 11: Export ────────────────────────────────────────────────
        if result.export_blocked:
            logger.warning(
                f"Export skipped: {result.export_block_reason}")
            result.warnings.append("SVG/DXF/JSON export skipped due to low plausibility")
        else:
            if export_svg:
                svg_path = str(out_dir / f"{source.stem}_photo_v2.svg")
                if write_svg(export_contours, svg_path, svg_w, svg_h):
                    result.output_svg = svg_path

            if export_dxf:
                dxf_path = str(out_dir / f"{source.stem}_photo_v2.dxf")
                if write_dxf(export_contours, dxf_path, self.dxf_version):
                    result.output_dxf = dxf_path

            if export_json:
                json_path = str(out_dir / f"{source.stem}_photo_v2.json")
                if write_features_json(features_by_type, json_path, calibration):
                    result.output_json = json_path

        result.debug_images = debug_paths
        result.processing_time_ms = (time.time() - start_time) * 1000

        # ── Batch calibration smoothing ─────────────────────────────────────
        result = self.batch_smoother.smooth(result)

        logger.info(
            f"Done in {result.processing_time_ms:.0f}ms: "
            f"{result.body_dimensions_mm[0]:.1f} x {result.body_dimensions_mm[1]:.1f} mm")

        return result

    # ── Diff 2/3/5: BodyModel construction ───────────────────────────────────

    def _build_body_model(
        self,
        *,
        body_result: Any,
        family: Any,
        spec_name: Optional[str],
        calibration: Any,
    ) -> Optional["BodyModel"]:
        """
        Promote Stage 4.5 evidence into a typed BodyModel before contour election.

        Runs the full Diff 2→3 chain:
          build handoff → extract landmarks → validate constraints →
          fit to spec → generate expected outline

        Any failure returns None so the pipeline degrades gracefully to the
        existing ownership-area election.
        """
        try:
            from body_model import BodyModel  # noqa: F401
            from landmark_extractor import (
                build_body_model_from_isolation,
                extract_landmarks_from_profile,
                fit_body_model_to_spec,
                generate_expected_outline,
                validate_body_constraints,
            )

            body_model = build_body_model_from_isolation(
                body_result,
                family_hint=(family.value if hasattr(family, "value") else str(family)),
                spec_hint=spec_name,
                mm_per_px=getattr(calibration, "mm_per_px", None),
            )
            body_model = extract_landmarks_from_profile(body_model)

            symmetry_score = self._compute_body_symmetry_score(body_result)
            body_model.diagnostics["body_symmetry_score"] = symmetry_score

            body_model = validate_body_constraints(
                body_model,
                symmetry_score=symmetry_score,
                has_cutaway=False,
            )
            body_model = fit_body_model_to_spec(
                body_model,
                geometry_authority=self.geometry_authority,
            )
            body_model = generate_expected_outline(body_model)
            return body_model
        except Exception as exc:
            logger.warning("BodyModel build failed: %s", exc)
            return None

    def _compute_body_symmetry_score(self, body_result: Any) -> float:
        """
        Measure bilateral body symmetry from Stage 4.5 evidence.

        Primary path: isolation_mask IoU + mass balance inside body bbox.
        Fallback: column_profile left/right comparison.
        Returns a score in [0, 1].
        """
        bbox = getattr(body_result, "body_bbox_px", None)
        if bbox is None or not isinstance(bbox, tuple) or len(bbox) != 4:
            return 0.0
        x, y, bw, bh = bbox
        if bw <= 2 or bh <= 2:
            return 0.0

        mask_score = self._symmetry_from_isolation_mask(body_result)
        if mask_score is not None:
            return float(max(0.0, min(1.0, mask_score)))

        profile_score = self._symmetry_from_profiles(body_result)
        if profile_score is not None:
            return float(max(0.0, min(1.0, profile_score)))

        return 0.0

    @staticmethod
    def _symmetry_from_isolation_mask(body_result: Any) -> Optional[float]:
        """Bilateral symmetry from the isolation mask pixel IoU inside body bbox."""
        mask = getattr(body_result, "isolation_mask", None)
        bbox = getattr(body_result, "body_bbox_px", None)
        if mask is None or bbox is None:
            return None
        x, y, bw, bh = bbox
        if bw <= 2 or bh <= 2:
            return None
        h, w = mask.shape[:2]
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(w, int(x + bw)), min(h, int(y + bh))
        if x1 <= x0 or y1 <= y0:
            return None
        roi = (mask[y0:y1, x0:x1] > 0).astype(np.uint8)
        if roi.size == 0 or np.count_nonzero(roi) == 0:
            return None
        mid = roi.shape[1] // 2
        if mid <= 0:
            return None
        left = roi[:, :mid]
        right = roi[:, roi.shape[1] - mid:]
        if left.size == 0 or right.size == 0:
            return None
        right_flip = np.fliplr(right)
        overlap = np.logical_and(left > 0, right_flip > 0).sum()
        union = np.logical_or(left > 0, right_flip > 0).sum()
        if union <= 0:
            return None
        shape_iou = float(overlap) / float(union)
        left_mass = float(np.count_nonzero(left))
        right_mass = float(np.count_nonzero(right))
        mass_balance = 1.0 - abs(left_mass - right_mass) / max(left_mass + right_mass, 1.0)
        return 0.70 * shape_iou + 0.30 * mass_balance

    @staticmethod
    def _symmetry_from_profiles(body_result: Any) -> Optional[float]:
        """Bilateral symmetry from the column width profile inside body bbox."""
        col = getattr(body_result, "column_profile", None)
        bbox = getattr(body_result, "body_bbox_px", None)
        if col is None or bbox is None:
            return None
        arr = np.asarray(col, dtype=float)
        if arr.size == 0:
            return None
        x, _, bw, _ = bbox
        x0, x1 = max(0, int(x)), min(len(arr), int(x + bw))
        if x1 <= x0:
            return None
        band = arr[x0:x1]
        if band.size < 4 or float(np.sum(band)) <= 0.0:
            return None
        mid = len(band) // 2
        left = band[:mid]
        right = band[len(band) - mid:]
        if left.size == 0 or right.size == 0:
            return None
        right_flip = right[::-1]
        num = float(np.sum(np.abs(left - right_flip)))
        den = float(np.sum(np.abs(left) + np.abs(right_flip)))
        if den <= 1e-6:
            return None
        return 1.0 - (num / den)

    def batch_extract(
        self,
        source_paths: List[Union[str, Path]],
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> List[PhotoExtractionResult]:
        """Process multiple images sequentially.

        Parameters
        ----------
        source_paths : list of image file paths
        output_dir   : output directory (defaults to each file's parent)
        **kwargs     : passed to extract() — spec_name, known_dimension_mm, etc.

        Returns
        -------
        Flat list of PhotoExtractionResult (multi-instrument images expand to N results)
        """
        all_results: List[PhotoExtractionResult] = []
        for i, path in enumerate(source_paths):
            logger.info(f"Batch [{i+1}/{len(source_paths)}]: {path}")
            try:
                r = self.extract(str(path), output_dir=output_dir, **kwargs)
                if isinstance(r, list):
                    all_results.extend(r)
                else:
                    all_results.append(r)
            except (OSError, cv2.error, ValueError) as e:
                logger.error(f"Batch error on {path}: {e}")
                fail = PhotoExtractionResult(source_path=str(path))
                fail.warnings.append(f"Processing failed: {e}")
                all_results.append(fail)
        logger.info(f"Batch complete: {len(all_results)} results from "
                    f"{len(source_paths)} inputs")
        logger.info(self.batch_smoother.session_summary())
        return all_results

    def _to_mm(self, contour: np.ndarray, mpp: float, img_h: int,
               cx: float, cy: float, tol: float) -> Optional[np.ndarray]:
        pts = contour.reshape(-1, 2).astype(np.float64)
        mm = np.empty_like(pts)
        mm[:, 0] = pts[:, 0] * mpp - cx
        mm[:, 1] = (img_h - pts[:, 1]) * mpp - cy
        simplified = cv2.approxPolyDP(
            mm.astype(np.float32).reshape(-1, 1, 2), tol, closed=True)
        simplified = simplified.reshape(-1, 2)
        return simplified if len(simplified) >= 3 else None

    @staticmethod
    def _load_image(source: Path) -> Optional[np.ndarray]:
        ext = source.suffix.lower()
        if ext == '.pdf':
            if not PYMUPDF_AVAILABLE:
                logger.error("PyMuPDF required for PDF")
                return None
            doc = fitz.open(str(source))
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            doc.close()
            return img
        img = cv2.imread(str(source))
        return img

    # ── AI Path Methods (v3) ────────────────────────────────────────────────

    def _detect_ai_image(self, image_path: str) -> bool:
        """
        Detect if image is AI-generated vs real photograph.

        Heuristics (in order of reliability):
        1. EXIF: AI images typically have NO or minimal EXIF data
        2. Filename: Common AI prefixes (dalle, midjourney, sd_, etc.)
        3. Resolution: AI images often have unusual aspect ratios (1:1, 16:9 exact)
        4. Color histogram: AI images often have different color distributions

        Returns True if likely AI-generated.
        """
        from pathlib import Path

        path = Path(image_path)
        filename_lower = path.stem.lower()

        # 1. Check for AI-indicative filename patterns
        ai_patterns = [
            'dalle', 'midjourney', 'mj_', 'sd_', 'stable_diffusion',
            'ai_', 'generated', 'flux', 'firefly', 'ideogram',
            'leonardo', 'bing_', 'copilot_', 'chatgpt',
        ]
        for pattern in ai_patterns:
            if pattern in filename_lower:
                logger.info(f"AI detection: filename pattern '{pattern}' matched")
                return True

        # 2. Check EXIF data
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data is None:
                    # No EXIF at all — suspicious for AI
                    # But also common for screenshots, so weight lightly
                    logger.debug("AI detection: no EXIF data (weak signal)")
                    # Don't return True here, just note it
                else:
                    # Check for camera make/model — real photos usually have this
                    has_camera = False
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ('Make', 'Model', 'LensModel'):
                            has_camera = True
                            break
                    if has_camera:
                        logger.debug("AI detection: found camera EXIF data — likely real photo")
                        return False
        except Exception:
            pass  # EXIF check failed, continue with other heuristics

        # 3. Check for exact power-of-2 or common AI resolutions
        img = cv2.imread(image_path)
        if img is not None:
            h, w = img.shape[:2]
            ai_resolutions = [
                (512, 512), (768, 768), (1024, 1024), (2048, 2048),
                (512, 768), (768, 512), (1024, 768), (768, 1024),
                (1024, 1792), (1792, 1024),  # ChatGPT/DALL-E 3
                (1280, 720), (720, 1280),
                (1920, 1080), (1080, 1920),
            ]
            if (w, h) in ai_resolutions or (h, w) in ai_resolutions:
                logger.info(f"AI detection: resolution {w}x{h} matches common AI size")
                return True

            # Check for exact 1:1 aspect ratio (common for AI)
            if w == h and w >= 512:
                logger.info(f"AI detection: square image {w}x{h} — likely AI")
                return True

        return False

    def _extract_ai_path(
        self,
        source: Path,
        out_dir: Path,
        spec_name: Optional[str],
        export_dxf: bool,
        export_svg: bool,
        debug_images: bool,
    ) -> PhotoExtractionResult:
        """
        AI-image extraction path: simpler 4-stage pipeline.

        Stage 1: Otsu threshold
        Stage 2: Largest contour extraction
        Stage 3: Scale to spec (user provides truth)
        Stage 4: Export

        The key insight: AI images give us SHAPE, user gives us TRUTH (dimensions).

        If no spec_name is provided, extraction proceeds with unscaled pixel
        coordinates. The recommendation layer handles the uncertainty.
        """
        start_time = time.time()
        result = PhotoExtractionResult(source_path=str(source))
        result.input_type = InputType.AI_GENERATED  # Mark as AI path

        # Get spec for scaling (uses body_dimension_reference.json with 14 specs)
        spec = get_ai_spec(spec_name) if spec_name else None
        is_unscaled = spec is None

        if is_unscaled:
            ai_specs = _load_ai_specs()
            result.warnings.append(
                f"No spec provided — proceeding with unscaled extraction. "
                f"Available specs: {list(ai_specs.keys())}"
            )
            logger.info("AI path: no spec_name, proceeding unscaled")

        # Auto-rotate if image orientation doesn't match spec orientation
        # (only when spec is available)
        extract_source = source
        if spec is not None:
            try:
                from PIL import Image as PILImage
                with PILImage.open(source) as img:
                    img_w, img_h = img.size
                    img_aspect = img_w / img_h  # >1 = landscape, <1 = portrait
                    spec_height, spec_width = spec["body"]  # (length_mm, width_mm)
                    spec_aspect = spec_width / spec_height  # >1 = landscape, <1 = portrait

                    # If orientations differ (one landscape, one portrait), rotate 90°
                    img_is_landscape = img_aspect > 1.0
                    spec_is_landscape = spec_aspect > 1.0

                    if img_is_landscape != spec_is_landscape:
                        logger.info(f"AI path: auto-rotating image (img_aspect={img_aspect:.2f}, spec_aspect={spec_aspect:.2f})")
                        rotated = img.rotate(-90, expand=True)
                        # Save to temp file
                        import tempfile
                        fd, temp_path = tempfile.mkstemp(suffix=source.suffix)
                        os.close(fd)
                        rotated.save(temp_path)
                        extract_source = Path(temp_path)
                        result.warnings.append(
                            f"Auto-rotated: image was {'landscape' if img_is_landscape else 'portrait'}, "
                            f"spec expects {'landscape' if spec_is_landscape else 'portrait'}"
                        )
            except Exception as e:
                logger.warning(f"AI path: auto-rotate check failed: {e}")

        # Extract using AIToCADExtractor (always runs)
        extractor = AIToCADExtractor(debug=debug_images)
        shape = extractor.extract_shape(str(extract_source))

        if shape is None:
            result.warnings.append("AI extraction failed: no shape found")
            return result

        # Validate shape (only when spec available)
        validation = None
        if spec is not None:
            validator = ShapeValidator()
            validation = validator.validate(shape, spec["body"])
            if not validation.passed:
                result.warnings.extend(validation.warnings)
                # Continue anyway — let user see what we found

        # Scale to spec dimensions OR use unscaled pixel coordinates
        if spec is not None:
            # Scaled path: use spec dimensions
            target_height = spec["body"][0]
            target_width = spec["body"][1]
            export_contour, scale_warnings = shape.scale_to(target_height, target_width)
            result.warnings.extend(scale_warnings)
            result.body_dimensions_mm = (target_height, target_width)

            # Create calibration result (synthetic — based on scaling)
            scale_factor = target_height / shape.height_px
            result.calibration = CalibrationResult(
                mm_per_px=scale_factor,
                source=ScaleSource.INSTRUMENT_SPEC,
                confidence=validation.overall_confidence if validation else 0.5,
            )
            log_dims = f"{target_height:.1f} x {target_width:.1f} mm"
        else:
            # Unscaled path: use pixel coordinates as-is
            export_contour = shape.contour  # Raw pixel contour
            result.body_dimensions_mm = (0.0, 0.0)  # No dimensions without spec
            result.calibration = CalibrationResult(
                mm_per_px=1.0,  # 1:1 pixel
                source=ScaleSource.NONE,  # No scaling without spec
                confidence=0.0,
            )
            result.warnings.append(
                "Unscaled AI extraction — dimensions unavailable without spec calibration"
            )
            log_dims = f"{shape.height_px} x {shape.width_px} px (unscaled)"

        # Build feature contour
        body_contour = FeatureContour(
            points_px=shape.contour,
            points_mm=export_contour if spec else shape.contour,
            feature_type=FeatureType.BODY_OUTLINE,
            confidence=shape.confidence,
            area_px=shape.area_px,
        )

        # Export (uses export_contour which is scaled or unscaled)
        if export_svg:
            svg_path = str(out_dir / f"{source.stem}_ai_v3.svg")
            _write_ai_svg(export_contour, svg_path)
            result.output_svg = svg_path
            logger.info(f"AI SVG written: {svg_path}")

        if export_dxf:
            dxf_path = str(out_dir / f"{source.stem}_ai_v3.dxf")
            contours_by_layer = {"BODY_OUTLINE": [export_contour]}
            if write_dxf(contours_by_layer, dxf_path, self.dxf_version):
                result.output_dxf = dxf_path
                logger.info(f"AI DXF written: {dxf_path}")

        # Debug images
        if debug_images:
            debug_img = extractor._last_debug_image if hasattr(extractor, '_last_debug_image') else None
            if debug_img is not None:
                debug_path = str(out_dir / f"{source.stem}_ai_debug.jpg")
                cv2.imwrite(debug_path, debug_img)
                result.debug_images["ai_extraction"] = debug_path

        result.processing_time_ms = (time.time() - start_time) * 1000
        logger.info(f"AI path done in {result.processing_time_ms:.0f}ms: {log_dims}")

        return result

    def _extract_blueprint_path(
        self,
        source: Path,
        out_dir: Path,
        known_dimension_mm: Optional[float],
        export_dxf: bool,
        export_svg: bool,
        debug_images: bool,
        gap_closing_level: str = "normal",
    ) -> PhotoExtractionResult:
        """
        Blueprint extraction path: for PDF blueprints with light gray lines.

        Uses light_line_body_extractor which:
        1. Inverts image (light → dark)
        2. Enhances contrast 3x
        3. Uses low Canny thresholds (15, 45)
        4. Morphological closing to connect broken lines
        5. Filters for body-sized contours
        """
        start_time = time.time()
        result = PhotoExtractionResult(source_path=str(source))
        result.input_type = InputType.BLUEPRINT

        try:
            from light_line_body_extractor import (
                extract_body_from_pdf,
                extract_body_from_image,
                create_acoustic_body_config,
            )
            from march_pipeline_restore import (
                classify_and_assign_layers,
                export_layered_lines_dxf,
            )
        except ImportError as e:
            result.warnings.append(f"Blueprint extractor not available: {e}")
            return result

        config = create_acoustic_body_config(gap_closing_level=gap_closing_level)

        # Handle PDF vs image
        page_height_mm = 1189.0  # A0 default
        if source.suffix.lower() == '.pdf':
            extraction = extract_body_from_pdf(
                source,
                page_number=0,
                page_size_mm=(841.0, page_height_mm),
                config=config,
                save_debug=debug_images,
            )
            # Compute image_height from mm_per_px after extraction
            image_height = int(page_height_mm / extraction.body.mm_per_px) if extraction.success else 0
        else:
            # Load as image
            image = cv2.imread(str(source))
            if image is None:
                result.warnings.append(f"Failed to load image: {source}")
                return result
            h, w = image.shape[:2]
            image_height = h
            # Assume A0 proportion for scale
            mm_per_px = page_height_mm / h
            extraction = extract_body_from_image(
                image, mm_per_px, config=config, save_debug=debug_images
            )

        if not extraction.success:
            result.warnings.append(f"Blueprint extraction failed: {extraction.error_message}")
            return result

        body = extraction.body

        # Scale to known dimension if provided
        target_width = known_dimension_mm if known_dimension_mm else body.width_mm
        target_height = body.height_mm * (target_width / body.width_mm)

        # Build calibration result
        calibration = CalibrationResult(
            mm_per_px=body.mm_per_px,
            source=ScaleSource.USER_DIMENSION if known_dimension_mm else ScaleSource.ESTIMATED_RENDER_DPI,
            confidence=0.85,
        )
        result.calibration = calibration
        result.body_dimensions_mm = (target_height, target_width)

        # Build feature contour
        contour_mm = body.to_mm_coordinates()
        if known_dimension_mm:
            # Rescale to target
            scale = target_width / body.width_mm
            cx, cy = contour_mm.mean(axis=0)
            contour_mm = (contour_mm - [cx, cy]) * scale

        body_contour = FeatureContour(
            points_px=body.points,
            points_mm=contour_mm,
            feature_type=FeatureType.BODY_OUTLINE,
            confidence=0.85,
            area_px=body.area_px,
        )
        result.feature_contours = [body_contour]

        # Export with grid reclassification (Sprint 5)
        if export_dxf:
            # Convert all_candidates to OpenCV contour format
            contours = [
                bc.points.reshape(-1, 1, 2).astype(np.int32)
                for bc in extraction.all_candidates
            ]

            # Classify and assign layers
            layers = classify_and_assign_layers(
                contours,
                mm_per_px=body.mm_per_px,
                min_area_px=2000,
            )

            # Export R12 LINE DXF (Fusion 360 compatible)
            dxf_path = out_dir / f"{source.stem}_blueprint.dxf"
            line_counts = export_layered_lines_dxf(
                layers,
                dxf_path,
                mm_per_px=body.mm_per_px,
                image_height=image_height,
            )
            result.output_dxf = str(dxf_path)
            layer_summary = ", ".join(f"{k}:{v}" for k, v in line_counts.items())
            logger.info(f"Blueprint DXF written: {dxf_path} [{layer_summary}]")

        if export_svg:
            svg_path = out_dir / f"{source.stem}_blueprint.svg"
            _write_ai_svg(contour_mm, str(svg_path))
            result.output_svg = str(svg_path)
            logger.info(f"Blueprint SVG written: {svg_path}")

        # Save debug images
        if debug_images and extraction.debug_images:
            for name, img in extraction.debug_images.items():
                debug_path = out_dir / f"{source.stem}_blueprint_{name}.png"
                cv2.imwrite(str(debug_path), img)
                result.debug_images[f"blueprint_{name}"] = str(debug_path)

        result.processing_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Blueprint path done in {result.processing_time_ms:.0f}ms: "
            f"{target_height:.1f} x {target_width:.1f} mm"
        )

        return result

    def _extract_silhouette_path(
        self,
        source: Path,
        out_dir: Path,
        known_dimension_mm: Optional[float],
        export_dxf: bool,
        export_svg: bool,
        debug_images: bool,
    ) -> PhotoExtractionResult:
        """
        Silhouette extraction path: for photos with dark backgrounds.

        Uses photo_silhouette_extractor which:
        1. Edge detection
        2. Flood fill from corners (background)
        3. Invert to get guitar mask
        4. Extract outer contour
        5. Filter to body region only
        """
        start_time = time.time()
        result = PhotoExtractionResult(source_path=str(source))
        result.input_type = InputType.PHOTO

        try:
            from photo_silhouette_extractor import (
                extract_body_only,
                SilhouetteConfig,
                scale_contour_to_mm,
                save_to_dxf,
            )
        except ImportError as e:
            result.warnings.append(f"Silhouette extractor not available: {e}")
            return result

        # Load image
        image = cv2.imread(str(source))
        if image is None:
            result.warnings.append(f"Failed to load image: {source}")
            return result

        config = SilhouetteConfig()
        extraction = extract_body_only(image, config, save_debug=debug_images)

        if not extraction.success:
            result.warnings.append(f"Silhouette extraction failed: {extraction.error_message}")
            return result

        x, y, cw, ch = extraction.bbox_px
        contour_px = extraction.contour

        # Scale to known dimension or default jumbo
        target_width = known_dimension_mm if known_dimension_mm else 477.0
        target_height = ch * (target_width / cw)

        # Scale contour to mm
        contour_mm = scale_contour_to_mm(
            contour_px, cw, ch, target_width, target_height
        )

        # Build calibration result
        scale_px_to_mm = target_width / cw
        calibration = CalibrationResult(
            mm_per_px=scale_px_to_mm,
            source=ScaleSource.USER_DIMENSION if known_dimension_mm else ScaleSource.ASSUMED_DPI,
            confidence=0.75,
        )
        result.calibration = calibration
        result.body_dimensions_mm = (target_height, target_width)

        # Build feature contour
        body_contour = FeatureContour(
            points_px=contour_px,
            points_mm=contour_mm,
            feature_type=FeatureType.BODY_OUTLINE,
            confidence=0.75,
            area_px=cw * ch,  # Approximate
        )
        result.feature_contours = [body_contour]

        # Export
        if export_dxf:
            dxf_path = out_dir / f"{source.stem}_silhouette.dxf"
            save_to_dxf(contour_mm, dxf_path)
            result.output_dxf = str(dxf_path)
            logger.info(f"Silhouette DXF written: {dxf_path}")

        if export_svg:
            svg_path = out_dir / f"{source.stem}_silhouette.svg"
            _write_ai_svg(contour_mm, str(svg_path))
            result.output_svg = str(svg_path)
            logger.info(f"Silhouette SVG written: {svg_path}")

        # Save debug images
        if debug_images and extraction.debug_images:
            for name, img in extraction.debug_images.items():
                debug_path = out_dir / f"{source.stem}_silhouette_{name}.png"
                cv2.imwrite(str(debug_path), img)
                result.debug_images[f"silhouette_{name}"] = str(debug_path)

        result.processing_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Silhouette path done in {result.processing_time_ms:.0f}ms: "
            f"{target_height:.1f} x {target_width:.1f} mm"
        )

        return result


# =============================================================================
# Standalone pipeline functions (non-class API)
# =============================================================================


def extract_feature_contours(
    edges: np.ndarray,
    alpha_mask: np.ndarray,
    mpp: float,
    min_contour_area_px: int = 500,
    body_region: Optional[Any] = None,
) -> List[FeatureContour]:
    """Extract and classify contours from edge + mask images.

    When body_region is provided, applies an ownership pre-filter that rejects
    candidates before classification — stopping bad contours at generation
    rather than trying to reject them during scoring.
    """
    classifier = FeatureClassifier()
    assembler = ContourAssembler(classifier, min_contour_area_px)
    return assembler.assemble(edges, alpha_mask, mpp, body_region=body_region)


def merge_feature_contours(
    contours: List[FeatureContour],
    image_shape: Optional[Tuple[int, int]] = None,
    body_region: Optional[BodyRegion] = None,
    mpp: float = 1.0,
) -> List[FeatureContour]:
    """Merge fragmented body contours and return updated list."""
    if not contours or image_shape is None:
        return list(contours)
    merger = ContourMerger()
    merge_result = merger.merge(contours, image_shape, body_region=body_region, mpp=mpp)
    if merge_result is not None:
        merged_fc = FeatureContour(
            points_px=merge_result.merged_contour,
            feature_type=FeatureType.BODY_OUTLINE,
            confidence=0.85,
            area_px=float(cv2.contourArea(merge_result.merged_contour)),
            bbox_px=merge_result.bbox_px,
            hash_id=hashlib.md5(merge_result.merged_contour.tobytes()).hexdigest()[:12],
        )
        contours = list(contours) + [merged_fc]
    return contours


def run_contour_stage_v2(
    image: np.ndarray,
    merged_mask: np.ndarray,
    body_region: Optional[BodyRegion],
    body_model: Optional["BodyModel"] = None,
    family: InstrumentFamily = InstrumentFamily.SOLID_BODY,
    mpp: float = 1.0,
    image_shape: Optional[Tuple[int, int]] = None,
    border_margin_px: int = 5,
    neck_height_factor: float = 1.35,
    min_solidity: float = 0.55,
    export_block_threshold: float = EXPORT_BLOCK_THRESHOLD,
) -> ContourStageResult:
    """
    Standalone contour stage — mirrors ContourStage.run() but as a free function.

    Performs: edge extraction → contour assembly → merge → scoring → election →
    export blocking with full ownership gate wiring.

    Diff 3: when body_model.expected_outline_px is populated, uses
    elect_body_contour_against_expected_outline (mean bidirectional distance)
    instead of the ownership-area fallback.
    """
    if image_shape is None:
        image_shape = (image.shape[0], image.shape[1])

    # Edge extraction
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    edges = cv2.Canny(gray, 50, 150)

    # Contour assembly
    feature_contours_raw = extract_feature_contours(
        edges, merged_mask, mpp, body_region=body_region
    )
    if not feature_contours_raw:
        return ContourStageResult(diagnostics={"error": "no_contours_found"})

    pre_merge_contours = list(feature_contours_raw)

    # Merge
    feature_contours_post = merge_feature_contours(
        feature_contours_raw, image_shape, body_region, mpp,
    )
    post_merge_contours = list(feature_contours_post)

    # Score
    scorer = ContourPlausibilityScorer(
        border_margin_px=border_margin_px,
        neck_height_factor=neck_height_factor,
        min_solidity=min_solidity,
        ownership_threshold=0.60,
    )
    scores_pre = scorer.score_all_candidates(
        pre_merge_contours, body_region, family, mpp, image_shape
    )
    scores_post = scorer.score_all_candidates(
        post_merge_contours, body_region, family, mpp, image_shape
    )

    pre_best = max(scores_pre, key=lambda s: s.score) if scores_pre else None
    post_best = max(scores_post, key=lambda s: s.score) if scores_post else None

    post_ownership_scores = {
        score.contour_index: float(score.ownership_score)
        for score in scores_post
    }

    # Elect body contour — Diff 3: prefer expected-outline prior when available
    used_expected_outline_prior = False
    expected_outline = (
        body_model.expected_outline_px
        if body_model is not None
        else None
    )

    if expected_outline is not None:
        elected_idx = elect_body_contour_against_expected_outline(
            feature_contours_post,
            expected_outline,
            ownership_scores=post_ownership_scores,
            ownership_threshold=0.60,
        )
        used_expected_outline_prior = True
    else:
        elected_idx = elect_body_contour_v2(
            feature_contours_post,
            body_region_hint=body_region,
            min_overlap=0.50,
            max_width_factor=1.30,
            ownership_scores=post_ownership_scores,
            ownership_threshold=0.60,
        )

    if elected_idx >= 0:
        body_contour_final = feature_contours_post[elected_idx]
        elected_source = "post_merge_guarded_prior" if used_expected_outline_prior else "post_merge_guarded"
    else:
        # Ownership gate failed every plausible candidate.
        body_contour_final = max(feature_contours_post, key=lambda c: c.area_px) if feature_contours_post else None
        elected_source = "ownership_gate_failed_fallback"

    best_cs = post_best or pre_best
    best_score = float(best_cs.score) if best_cs is not None else 0.0

    result = ContourStageResult(
        feature_contours_pre_merge=pre_merge_contours,
        feature_contours_post_merge=post_merge_contours,
        body_contour_final=body_contour_final,
        elected_source=elected_source,
        best_score=best_score,
        diagnostics={
            "n_pre_merge": len(pre_merge_contours),
            "n_post_merge": len(post_merge_contours),
            "n_scored_pre": len(scores_pre),
            "n_scored_post": len(scores_post),
            "family": family.value if hasattr(family, "value") else str(family),
            "body_ownership_gate_failed": elected_idx < 0,
            "ownership_threshold": 0.60,
            "used_expected_outline_prior": used_expected_outline_prior,
        },
    )

    if best_cs is not None:
        result.export_block_score_breakdown = {
            "composite": float(best_cs.score),
            "completeness": float(best_cs.completeness),
            "dimension_plausibility": float(best_cs.dimension_plausibility),
            "symmetry": float(best_cs.symmetry_score),
            "aspect_ratio_ok": 1.0 if best_cs.aspect_ratio_ok else 0.0,
            "border_contact": 0.0 if best_cs.border_contact else 1.0,
            "includes_neck": 0.0 if best_cs.includes_neck else 1.0,
            "ownership_score": float(best_cs.ownership_score),
            "vertical_coverage": float(best_cs.vertical_coverage),
            "neck_inclusion_score": 1.0 - float(best_cs.neck_inclusion_score),
        }
        result.export_block_issues = list(best_cs.issues)
        result.ownership_score = float(best_cs.ownership_score)
        result.ownership_ok = bool(best_cs.ownership_score >= 0.60)

    if elected_idx < 0:
        result.export_blocked = True
        result.block_reason = "No contour passed body ownership threshold 0.60"
        result.recommended_next_action = "rerun_body_isolation"
        if "body_ownership_failed" not in result.export_block_issues:
            result.export_block_issues.append("body_ownership_failed")

    if best_score < export_block_threshold:
        result.export_blocked = True
        result.block_reason = (
            f"Best plausibility score {best_score:.3f} below threshold "
            f"{export_block_threshold:.3f}"
        )

    if result.export_blocked and result.recommended_next_action is None:
        result.recommended_next_action = "manual_review_required"

    return result


def run_body_isolation_stage(
    image: np.ndarray,
    fg_mask: Optional[np.ndarray] = None,
) -> "BodyIsolationResult":
    """Standalone body isolation — wraps BodyIsolator for non-class callers."""
    from body_isolation_result import BodyIsolationResult
    isolator = BodyIsolator()
    body_region = isolator.isolate(image, fg_mask=fg_mask)
    return BodyIsolationResult(
        body_bbox_px=body_region.bbox,
        body_region=body_region,
        confidence=body_region.confidence,
        completeness_score=body_region.confidence,
    )


def vectorize_photo_v2(
    image: np.ndarray,
    *,
    family_hint: Optional[InstrumentFamily] = None,
    mpp: Optional[float] = None,
) -> PhotoExtractionResult:
    """
    Standalone extraction pipeline — mirrors PhotoVectorizerV2.extract()
    but as a free function with ownership gate wiring.
    """
    warnings: List[str] = []
    img_h, img_w = image.shape[:2]

    # Foreground mask
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    _, merged_mask = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Body isolation
    body_result = run_body_isolation_stage(image, fg_mask=merged_mask)
    body_region = body_result.body_region

    family = family_hint or InstrumentFamily.UNKNOWN
    effective_mpp = mpp or 1.0

    # Contour stage
    contour_stage = run_contour_stage_v2(
        image=image,
        merged_mask=merged_mask,
        body_region=body_region,
        family=family,
        mpp=effective_mpp,
        image_shape=(img_h, img_w),
    )

    # Legacy monolith path must mirror modular contour_stage ownership semantics.
    if getattr(contour_stage, "ownership_ok", None) is False:
        warnings.append(
            f"Contour ownership failed "
            f"({float(getattr(contour_stage, 'ownership_score', 0.0)):.2f} < 0.60)"
        )
        if contour_stage.recommended_next_action is None:
            contour_stage.recommended_next_action = "rerun_body_isolation"

    export_ok = not contour_stage.export_blocked
    if contour_stage.export_blocked:
        warnings.append(
            f"Export blocked: "
            f"{contour_stage.block_reason or 'low contour plausibility'}"
        )

    result = PhotoExtractionResult(
        source_path="<standalone>",
        contour_stage=contour_stage,
        export_blocked=contour_stage.export_blocked,
        export_block_reason=contour_stage.block_reason,
    )
    result.warnings = warnings
    return result


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Photo Vectorizer V2 - Extract outlines from instrument photos")
    parser.add_argument("source", help="Photo path (JPG, PNG, TIFF, PDF)")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    _spec_names = [k for k in INSTRUMENT_SPECS.keys() if k != "reference_objects"]
    parser.add_argument("-s", "--spec", default=None,
                        help=f"Instrument spec: {', '.join(_spec_names)}")
    parser.add_argument("--mm", type=float, help="Known dimension in mm")
    parser.add_argument("--px", type=float, help="Pixel span of known dimension")
    parser.add_argument("--bg", default="auto",
                        choices=["auto", "grabcut", "rembg", "sam", "threshold"])
    parser.add_argument("--no-perspective", action="store_true")
    parser.add_argument("--formats", nargs="+", default=["svg", "dxf"],
                        choices=["svg", "dxf", "json"])
    parser.add_argument("--debug", action="store_true", help="Save debug images")
    parser.add_argument("--bom", action="store_true",
                        help="Generate material BOM (bill of materials) after extraction")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s")

    bg_map = {"auto": BGRemovalMethod.AUTO, "grabcut": BGRemovalMethod.GRABCUT,
              "rembg": BGRemovalMethod.REMBG, "sam": BGRemovalMethod.SAM,
              "threshold": BGRemovalMethod.THRESHOLD}

    v = PhotoVectorizerV2(bg_method=bg_map[args.bg])
    result = v.extract(
        args.source, output_dir=args.output, spec_name=args.spec,
        known_dimension_mm=args.mm, known_dimension_px=args.px,
        correct_perspective=not args.no_perspective,
        export_dxf="dxf" in args.formats,
        export_svg="svg" in args.formats,
        export_json="json" in args.formats,
        debug_images=args.debug)

    results = result if isinstance(result, list) else [result]
    for i, result in enumerate(results):
        if len(results) > 1:
            print(f"\n--- Instrument {i + 1} ---")
        print(f"\nInput: {result.input_type.value}")
        print(f"Background: {result.bg_method_used}")
        print(f"Dark background: {result.dark_background_detected}")
        print(f"Perspective: {'corrected' if result.perspective_corrected else 'no'}")
        if result.calibration:
            print(f"Scale: {result.calibration.message}")
            if result.calibration.confidence < 0.5:
                print(f"  Warning: Low calibration confidence ({result.calibration.confidence:.2f})")
        print(f"Body: {result.body_dimensions_mm[0]:.1f} x {result.body_dimensions_mm[1]:.1f} mm")
        print(f"       {result.body_dimensions_inch[0]:.2f} x {result.body_dimensions_inch[1]:.2f} in")
        print(f"Features: {', '.join(f'{ft.value}={len(c)}' for ft, c in result.features.items() if c)}")
        if result.output_svg:
            print(f"SVG: {result.output_svg}")
        if result.output_dxf:
            print(f"DXF: {result.output_dxf}")
        if result.warnings:
            for w in result.warnings:
                print(f"  Warning: {w}")
        print(f"Time: {result.processing_time_ms:.0f}ms")

        # BOM generation
        if args.bom:
            try:
                from material_bom import MaterialBOMGenerator
                bom_gen = MaterialBOMGenerator()
                bom = bom_gen.generate(result)
                print(f"\n{bom.summary()}")
                out_dir = args.output or str(Path(args.source).parent)
                stem = Path(result.source_path).stem
                if len(results) > 1:
                    stem = f"{stem}_instrument_{i + 1}"
                bom.to_json(str(Path(out_dir) / f"{stem}_bom.json"))
                bom.to_csv(str(Path(out_dir) / f"{stem}_bom.csv"))
                print(f"BOM JSON: {Path(out_dir) / f'{stem}_bom.json'}")
                print(f"BOM CSV:  {Path(out_dir) / f'{stem}_bom.csv'}")
            except ImportError:
                print("  Warning: material_bom module not found — skipping BOM")


if __name__ == "__main__":
    main()
