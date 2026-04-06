"""
Phase 3.6 Vectorizer - Production-Grade Blueprint Extraction with ML + OCR
===========================================================================

Production-ready blueprint vectorizer with tiered processing and enhanced features.

Enhanced blueprint vectorizer with:
- Dual-pass extraction (aggressive for body, lighter for details)
- Text/annotation filtering using shape heuristics
- Hierarchy-aware extraction for nested features (body -> cavities -> holes)
- Canny + Adaptive threshold combination for fine lines
- Batch processing with auto-naming
- Dimension validation against known instrument specs
- ML contour classification (optional sklearn, graceful fallback)
- Geometric primitive detection (circles, arcs, ellipses)
- Auto scale detection from reference features
- User feedback system for continuous improvement
- Image caching for performance
- Color filtering for blueprint types
- OCR dimension extraction with contextual parsing (Phase 3.6)

Author: The Production Shop
Version: 3.6.0
"""
import logging
import hashlib
import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
import cv2

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Phase 3: BlueprintAnalyzer for vision-based scale detection
try:
    from analyzer import BlueprintAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False

# Optional sklearn for ML classification
try:
    import warnings
    # Suppress sklearn joblib parallel warnings
    warnings.filterwarnings('ignore', message='.*sklearn.utils.parallel.*')
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from dxf_compat import create_document, add_polyline, DxfVersion, set_document_bounds

# Phase 3.7 enhancement modules (optional — graceful fallback)
try:
    from vectorizer_enhancements import (
        InputType, ScaleSource, CalibrationResult,
        GuitarPhotoProcessor, AdaptiveLineExtractor, ScaleCalibrator,
        ContourCompleter, DebugVisualizer, ManualOverride, ValidationReport,
        classify_input_type
    )
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    ENHANCEMENTS_AVAILABLE = False

try:
    from export_svg import export_to_svg
    SVG_EXPORT_AVAILABLE = True
except ImportError:
    SVG_EXPORT_AVAILABLE = False

try:
    from dxf_postprocessor import export_cam_ready_dxf
    CAM_EXPORT_AVAILABLE = True
except ImportError:
    CAM_EXPORT_AVAILABLE = False

# Grid zone classifier for body outline detection enhancement
try:
    from classifiers.grid_zone import GridZoneClassifier, ELECTRIC_GUITAR_GRID
    GRID_CLASSIFIER_AVAILABLE = True
except ImportError:
    GridZoneClassifier = None
    ELECTRIC_GUITAR_GRID = None
    GRID_CLASSIFIER_AVAILABLE = False

logger = logging.getLogger(__name__)


def _safe_dxf_save(doc, output_path: str) -> bool:
    """
    Save DXF document with explicit flush and verification.

    Phase 5E fix: Large DXF files (>195K LINE entities) can truncate
    ENDSEC/EOF markers if the OS buffer isn't fully flushed. This helper:
    1. Calls doc.saveas() to write the file
    2. Opens the file and forces explicit flush via fsync
    3. Verifies the file ends with proper termination

    Returns True if save succeeded, False if verification failed.
    """
    import os

    # Write the DXF document
    doc.saveas(output_path)

    # Force OS-level flush for large files
    try:
        with open(output_path, 'r+b') as f:
            f.flush()
            os.fsync(f.fileno())
    except (IOError, OSError) as e:
        logger.warning(f"Could not fsync DXF file: {e}")

    # Verify file ends properly (check last 100 bytes for EOF or ENDSEC)
    try:
        with open(output_path, 'rb') as f:
            f.seek(0, 2)  # End of file
            size = f.tell()
            if size > 100:
                f.seek(-100, 2)
            else:
                f.seek(0)
            tail = f.read().decode('utf-8', errors='ignore')

            # R12 files end with "  0\nEOF\n" or "  0\r\nEOF\r\n"
            if 'EOF' in tail or 'ENDSEC' in tail:
                return True
            else:
                logger.error(f"DXF verification FAILED: file may be truncated ({output_path})")
                return False
    except Exception as e:
        logger.warning(f"Could not verify DXF termination: {e}")
        return True  # Assume OK if we can't verify


# =============================================================================
# Data Classes & Enums
# =============================================================================

class InstrumentType(Enum):
    """Supported instrument types for feature classification."""
    ELECTRIC_GUITAR = "electric"
    ACOUSTIC_GUITAR = "acoustic"
    BASS = "bass"
    UKULELE = "ukulele"
    MANDOLIN = "mandolin"
    ARCHTOP = "archtop"
    UNKNOWN = "unknown"


class ContourCategory(Enum):
    """Contour classification categories."""
    BODY_OUTLINE = "body_outline"
    PICKGUARD = "pickguard"
    NECK_POCKET = "neck_pocket"
    PICKUP_ROUTE = "pickup_route"
    CONTROL_CAVITY = "control_cavity"
    BRIDGE_ROUTE = "bridge_route"
    JACK_ROUTE = "jack_route"
    RHYTHM_CIRCUIT = "rhythm_circuit"
    SOUNDHOLE = "soundhole"
    D_HOLE = "d_hole"
    F_HOLE = "f_hole"
    ROSETTE = "rosette"
    BRACING = "bracing"
    TEXT = "text"
    PAGE_BORDER = "page_border"
    SMALL_FEATURE = "small_feature"
    UNKNOWN = "unknown"
    BODY_OUTLINE_CANDIDATE = "body_outline_candidate"  # Large contours for re-ranking
    # Grid zone categories (Phase 4.0)
    UPPER_BOUT = "upper_bout"
    LOWER_BOUT = "lower_bout"
    WAIST = "waist"
    BODY_WING_LIMIT = "body_wing_limit"
    HEADSTOCK_ZONE = "headstock_zone"
    CENTERLINE = "centerline"


class PrimitiveType(Enum):
    """Geometric primitive types."""
    CIRCLE = "circle"
    ARC = "arc"
    ELLIPSE = "ellipse"
    LINE = "line"
    POLYLINE = "polyline"


class ExtractionMode(Enum):
    """
    Extraction mode for blueprint vectorization.

    SMART: ML-based classification, optimized for guitars (default)
    SIMPLE: Raw contour extraction without filtering - works for any instrument
    """
    SMART = "smart"
    SIMPLE = "simple"


@dataclass
class GeometricPrimitive:
    """Detected geometric primitive."""
    type: PrimitiveType
    center: Optional[Tuple[float, float]] = None  # mm
    radius: Optional[float] = None  # mm for circles
    axes: Optional[Tuple[float, float]] = None  # (major, minor) for ellipses
    angle: Optional[float] = None  # rotation angle in degrees
    start_angle: Optional[float] = None  # for arcs
    end_angle: Optional[float] = None  # for arcs
    points: Optional[List[Tuple[float, float]]] = None  # for polylines
    layer: str = "PRIMITIVES"
    confidence: float = 0.0


@dataclass
class ContourInfo:
    """Metadata for a detected contour."""
    contour: np.ndarray
    category: ContourCategory
    width_mm: float
    height_mm: float
    area_px: float
    perimeter_px: float
    circularity: float
    aspect_ratio: float
    point_count: int
    bbox: Tuple[int, int, int, int]  # x, y, w, h in pixels
    hierarchy_level: int = 0
    parent_idx: int = -1
    # Phase 3.5 additions
    ml_confidence: float = 0.0
    hu_moments: Optional[List[float]] = None
    convexity: float = 0.0
    solidity: float = 0.0
    extent: float = 0.0

    @property
    def max_dim(self) -> float:
        return max(self.width_mm, self.height_mm)

    @property
    def min_dim(self) -> float:
        return min(self.width_mm, self.height_mm)


@dataclass
class ExtractionResult:
    """Result of a single extraction."""
    source_path: str
    output_dxf: str
    output_svg: Optional[str]
    instrument_type: InstrumentType
    contours_by_category: Dict[str, List[ContourInfo]]
    warnings: List[str] = field(default_factory=list)
    validation_passed: bool = True
    dimensions_mm: Tuple[float, float] = (0, 0)  # width, height of body
    # Phase 3.5 additions
    primitives: List[GeometricPrimitive] = field(default_factory=list)
    scale_factor: float = 1.0
    scale_source: str = "none"
    processing_time_ms: float = 0.0
    ml_used: bool = False
    # Phase 3.6: OCR dimensions
    ocr_dimensions: List[Dict[str, Any]] = field(default_factory=list)
    ocr_raw_texts: List[str] = field(default_factory=list)
    sheet_type: str = "body"  # "body", "pickguard_sheet", "component_sheet"
    # Phase 3.7 additions
    input_type: str = "unknown"
    calibration_result: Optional[Any] = None
    debug_report_path: Optional[str] = None
    validation_report: Optional[Dict[str, Any]] = None
    perspective_corrected: bool = False
    bg_method_used: str = "none"
    assembly_method: str = "direct"
    dark_background_inverted: bool = False

    def summary(self) -> Dict[str, Any]:
        base = {
            "source": self.source_path,
            "dxf": self.output_dxf,
            "instrument": self.instrument_type.value,
            "body_size_mm": self.dimensions_mm,
            "sheet_type": self.sheet_type,
            "validation_passed": self.validation_passed,
            "features": {cat: len(items) for cat, items in self.contours_by_category.items()},
            "primitives_count": len(self.primitives),
            "scale_factor": self.scale_factor,
            "scale_source": self.scale_source,
            "processing_time_ms": self.processing_time_ms,
            "ml_used": self.ml_used,
            "ocr_dimensions_count": len(self.ocr_dimensions),
            "ocr_raw_texts_count": len(self.ocr_raw_texts),
            "warnings": self.warnings,
            "input_type": self.input_type,
            "perspective_corrected": self.perspective_corrected,
            "bg_method": self.bg_method_used,
            "assembly_method": self.assembly_method,
            "dark_background_inverted": self.dark_background_inverted,
            "debug_report": self.debug_report_path,
        }
        if self.calibration_result and hasattr(self.calibration_result, 'mm_per_px'):
            base["calibration"] = {
                "mm_per_px": self.calibration_result.mm_per_px,
                "source": self.calibration_result.source.value,
                "confidence": self.calibration_result.confidence,
                "message": self.calibration_result.message,
            }
        return base


@dataclass
class InstrumentSpec:
    """Known dimensions for instrument validation."""
    name: str
    body_length_range: Tuple[float, float]  # mm
    body_width_range: Tuple[float, float]   # mm
    neck_pocket_range: Tuple[float, float]  # mm (width)
    scale_length: Optional[float] = None    # mm
    min_body_dim: float = 300.0             # mm — minimum largest dimension to qualify as body
    max_body_aspect_ratio: float = 2.0      # aspect ratio ceiling for body outlines


# Known instrument specifications for validation
INSTRUMENT_SPECS = {
    "stratocaster": InstrumentSpec(
        name="Fender Stratocaster",
        body_length_range=(390, 420),
        body_width_range=(310, 340),
        neck_pocket_range=(55, 58),
        scale_length=648
    ),
    "telecaster": InstrumentSpec(
        name="Fender Telecaster",
        body_length_range=(390, 420),
        body_width_range=(310, 340),
        neck_pocket_range=(55, 58),
        scale_length=648
    ),
    "jazzmaster": InstrumentSpec(
        name="Fender Jazzmaster",
        body_length_range=(480, 520),
        body_width_range=(340, 380),
        neck_pocket_range=(55, 60),
        scale_length=648
    ),
    "jaguar": InstrumentSpec(
        name="Fender Jaguar",
        body_length_range=(460, 500),
        body_width_range=(330, 370),
        neck_pocket_range=(55, 60),
        scale_length=610
    ),
    "les_paul": InstrumentSpec(
        name="Gibson Les Paul",
        body_length_range=(430, 470),
        body_width_range=(320, 360),
        neck_pocket_range=(None, None),  # Set neck
        scale_length=629
    ),
    "sg": InstrumentSpec(
        name="Gibson SG",
        body_length_range=(380, 420),
        body_width_range=(320, 360),
        neck_pocket_range=(None, None),
        scale_length=629
    ),
    "es335": InstrumentSpec(
        name="Gibson ES-335",
        body_length_range=(480, 520),
        body_width_range=(400, 440),
        neck_pocket_range=(None, None),
        scale_length=629
    ),
    "dreadnought": InstrumentSpec(
        name="Dreadnought Acoustic",
        body_length_range=(500, 540),
        body_width_range=(380, 420),
        neck_pocket_range=(55, 65),
        scale_length=645
    ),
    "orchestra_model": InstrumentSpec(
        name="Orchestra Model (OM)",
        body_length_range=(480, 510),
        body_width_range=(380, 410),
        neck_pocket_range=(55, 62),
        scale_length=645
    ),
    "selmer": InstrumentSpec(
        name="Selmer Maccaferri",
        body_length_range=(460, 500),
        body_width_range=(370, 410),
        neck_pocket_range=(55, 65),
        scale_length=670
    ),
    "classical": InstrumentSpec(
        name="Classical Guitar",
        body_length_range=(470, 510),
        body_width_range=(350, 390),
        neck_pocket_range=(55, 62),
        scale_length=650
    ),
    "explorer": InstrumentSpec(
        name="Gibson Explorer",
        body_length_range=(450, 480),
        body_width_range=(460, 495),
        neck_pocket_range=(None, None),  # Set neck
        scale_length=629
    ),
    "flying_v": InstrumentSpec(
        name="Gibson Flying V",
        body_length_range=(590, 620),
        body_width_range=(470, 500),
        neck_pocket_range=(None, None),  # Set neck
        scale_length=629
    ),
    "smart_guitar": InstrumentSpec(
        name="Smart Guitar",
        body_length_range=(430, 460),
        body_width_range=(350, 385),
        neck_pocket_range=(54, 58),
        scale_length=629
    ),
    "klein": InstrumentSpec(
        name="Klein Guitar",
        body_length_range=(340, 370),
        body_width_range=(215, 245),
        neck_pocket_range=(54, 58),
        scale_length=648,
        min_body_dim=210.0,  # Klein bodies are compact
        max_body_aspect_ratio=2.0
    ),
    "ukulele_soprano": InstrumentSpec(
        name="Soprano Ukulele",
        body_length_range=(230, 260),
        body_width_range=(160, 185),
        neck_pocket_range=(None, None),
        scale_length=345,
        min_body_dim=155.0,
        max_body_aspect_ratio=1.8
    ),
    "ukulele_concert": InstrumentSpec(
        name="Concert Ukulele",
        body_length_range=(260, 290),
        body_width_range=(180, 205),
        neck_pocket_range=(None, None),
        scale_length=381,
        min_body_dim=175.0,
        max_body_aspect_ratio=1.8
    ),
    "ukulele_tenor": InstrumentSpec(
        name="Tenor Ukulele",
        body_length_range=(290, 320),
        body_width_range=(200, 225),
        neck_pocket_range=(None, None),
        scale_length=432,
        min_body_dim=195.0,
        max_body_aspect_ratio=1.8
    ),
    "jumbo": InstrumentSpec(
        name="Jumbo Acoustic",
        body_length_range=(490, 540),
        body_width_range=(400, 445),
        neck_pocket_range=(None, None),
        scale_length=650
    ),
    "cuatro_puertorriqueno": InstrumentSpec(
        name="Puerto Rican Cuatro",
        body_length_range=(420, 500),
        body_width_range=(240, 290),
        neck_pocket_range=(None, None),
        scale_length=585,
        min_body_dim=200.0,
        max_body_aspect_ratio=2.0
    ),
}


# Reference feature dimensions for scale detection (mm)
REFERENCE_FEATURES = {
    "neck_pocket_width": {"expected": 56.0, "tolerance": 3.0},
    "humbucker_route": {"expected": 71.5, "tolerance": 2.0},
    "single_coil_route": {"expected": 85.0, "tolerance": 3.0},
    "p90_route": {"expected": 90.0, "tolerance": 3.0},
    "tune_o_matic_bridge": {"expected": 120.0, "tolerance": 5.0},
    "strat_trem_route": {"expected": 89.0, "tolerance": 3.0},
}


# =============================================================================
# Image Caching
# =============================================================================

class ImageCache:
    """Simple LRU cache for loaded images."""

    def __init__(self, max_size: int = 10):
        self._cache: Dict[str, Tuple[np.ndarray, float]] = {}
        self._max_size = max_size

    def _hash_path(self, path: str, page: int, dpi: int) -> str:
        key = f"{path}:{page}:{dpi}"
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, path: str, page: int, dpi: int) -> Optional[np.ndarray]:
        key = self._hash_path(path, page, dpi)
        if key in self._cache:
            img, _ = self._cache[key]
            self._cache[key] = (img, datetime.now().timestamp())
            return img.copy()
        return None

    def put(self, path: str, page: int, dpi: int, image: np.ndarray):
        key = self._hash_path(path, page, dpi)

        # Evict oldest if full
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.items(), key=lambda x: x[1][1])
            del self._cache[oldest[0]]

        self._cache[key] = (image.copy(), datetime.now().timestamp())

    def clear(self):
        self._cache.clear()


# Global image cache
_image_cache = ImageCache()


# =============================================================================
# Color Filter
# =============================================================================

class ColorFilter:
    """
    Analyzes and filters images based on color/value characteristics.
    Adapted from Phase 2 vectorizer for blueprint type detection.
    """

    def __init__(self):
        self.thresholds = {
            'dark': 100,
            'faint': 200,
            'inverted': 150,
        }

    def analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze image to determine blueprint type and optimal extraction method.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        total = gray.size
        min_px = int(gray.min())
        max_px = int(gray.max())
        mean_px = float(gray.mean())

        white_pixels = np.sum(gray > 250)
        dark_pixels = np.sum(gray <= 100)
        black_pixels = np.sum(gray <= 50)

        white_ratio = white_pixels / total
        dark_ratio = dark_pixels / total
        black_ratio = black_pixels / total

        # Determine blueprint type
        if black_ratio > 0.3:
            blueprint_type = 'inverted'
            method = 'fixed'
            threshold = 150
        elif white_ratio > 0.95:
            blueprint_type = 'faint'
            method = 'canny_adaptive'
            threshold = 0
        elif dark_ratio > 0.02:
            blueprint_type = 'dark'
            method = 'fixed'
            threshold = 100 if min_px < 50 else min(150, min_px + 50)
        else:
            blueprint_type = 'faint'
            method = 'canny_adaptive'
            threshold = 0

        return {
            'blueprint_type': blueprint_type,
            'recommended_method': method,
            'recommended_threshold': threshold,
            'white_ratio': white_ratio,
            'dark_ratio': dark_ratio,
            'black_ratio': black_ratio,
            'min_pixel': min_px,
            'max_pixel': max_px,
            'mean_pixel': mean_px,
        }

    def apply_filter(self, image: np.ndarray, filter_type: str = 'auto') -> np.ndarray:
        """Apply appropriate filtering based on image analysis."""
        if filter_type == 'auto':
            analysis = self.analyze_image(image)
            filter_type = analysis['blueprint_type']

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        if filter_type == 'inverted':
            # Invert and threshold
            _, mask = cv2.threshold(gray, self.thresholds['inverted'], 255, cv2.THRESH_BINARY)
        elif filter_type == 'faint':
            # Use adaptive threshold
            mask = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 5
            )
        else:  # dark
            _, mask = cv2.threshold(gray, self.thresholds['dark'], 255, cv2.THRESH_BINARY_INV)

        return mask


# =============================================================================
# Fallback Classifier (used when sklearn unavailable)
# =============================================================================

class FallbackClassifier:
    """
    Rule-based classifier that mimics sklearn interface.
    Used when sklearn is not available.
    """

    def __init__(self):
        self.classes_ = [cat.value for cat in ContourCategory]
        self._rules = self._build_rules()

    def _build_rules(self) -> List[Callable]:
        """Build classification rules based on geometric features."""
        return [
            # Each rule returns (category, confidence) or None
            self._rule_body_outline,
            self._rule_pickup_route,
            self._rule_neck_pocket,
            self._rule_control_cavity,
            self._rule_soundhole,
            self._rule_f_hole,
            self._rule_text,
        ]

    def _rule_body_outline(self, features: Dict) -> Optional[Tuple[str, float]]:
        w, h = features.get('width_mm', 0), features.get('height_mm', 0)
        max_dim, min_dim = max(w, h), min(w, h)
        if 350 < max_dim < 650 and 280 < min_dim < 450:
            return ('body_outline', 0.85)
        return None

    def _rule_pickup_route(self, features: Dict) -> Optional[Tuple[str, float]]:
        w, h = features.get('width_mm', 0), features.get('height_mm', 0)
        max_dim, min_dim = max(w, h), min(w, h)
        aspect = max_dim / min_dim if min_dim > 0 else 999
        if 70 < max_dim < 110 and 30 < min_dim < 65 and 1.3 < aspect < 3.0:
            return ('pickup_route', 0.75)
        return None

    def _rule_neck_pocket(self, features: Dict) -> Optional[Tuple[str, float]]:
        w, h = features.get('width_mm', 0), features.get('height_mm', 0)
        max_dim, min_dim = max(w, h), min(w, h)
        aspect = max_dim / min_dim if min_dim > 0 else 999
        if 60 < max_dim < 120 and 50 < min_dim < 85 and 1.0 < aspect < 1.8:
            return ('neck_pocket', 0.80)
        return None

    def _rule_control_cavity(self, features: Dict) -> Optional[Tuple[str, float]]:
        w, h = features.get('width_mm', 0), features.get('height_mm', 0)
        max_dim, min_dim = max(w, h), min(w, h)
        if 80 < max_dim < 180 and 50 < min_dim < 120:
            return ('control_cavity', 0.70)
        return None

    def _rule_soundhole(self, features: Dict) -> Optional[Tuple[str, float]]:
        w, h = features.get('width_mm', 0), features.get('height_mm', 0)
        circularity = features.get('circularity', 0)
        max_dim, min_dim = max(w, h), min(w, h)
        if 80 < max_dim < 130 and 80 < min_dim < 130 and 0.7 < circularity < 1.0:
            return ('soundhole', 0.85)
        return None

    def _rule_f_hole(self, features: Dict) -> Optional[Tuple[str, float]]:
        w, h = features.get('width_mm', 0), features.get('height_mm', 0)
        max_dim, min_dim = max(w, h), min(w, h)
        if 130 < max_dim < 180 and 30 < min_dim < 55:
            return ('f_hole', 0.75)
        return None

    def _rule_text(self, features: Dict) -> Optional[Tuple[str, float]]:
        w, h = features.get('width_mm', 0), features.get('height_mm', 0)
        circularity = features.get('circularity', 0)
        max_dim, min_dim = max(w, h), min(w, h)
        aspect = max_dim / min_dim if min_dim > 0 else 999
        if max_dim < 15 and aspect > 2 and circularity < 0.3:
            return ('text', 0.70)
        return None

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict categories for feature array."""
        predictions = []
        for row in X:
            features = self._array_to_features(row)
            pred = self._classify_one(features)
            predictions.append(pred)
        return np.array(predictions)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return confidence scores for all classes."""
        n_samples = len(X)
        n_classes = len(self.classes_)
        proba = np.zeros((n_samples, n_classes))

        for i, row in enumerate(X):
            features = self._array_to_features(row)
            cat, conf = self._classify_one_with_conf(features)
            class_idx = self.classes_.index(cat) if cat in self.classes_ else -1
            if class_idx >= 0:
                proba[i, class_idx] = conf

        return proba

    def _array_to_features(self, row: np.ndarray) -> Dict:
        """Convert feature array back to dict for rules."""
        # Assumes standard feature order from extract_features
        return {
            'width_mm': row[0] if len(row) > 0 else 0,
            'height_mm': row[1] if len(row) > 1 else 0,
            'area_px': row[2] if len(row) > 2 else 0,
            'perimeter_px': row[3] if len(row) > 3 else 0,
            'circularity': row[4] if len(row) > 4 else 0,
            'aspect_ratio': row[5] if len(row) > 5 else 0,
            'convexity': row[6] if len(row) > 6 else 0,
            'solidity': row[7] if len(row) > 7 else 0,
            'extent': row[8] if len(row) > 8 else 0,
        }

    def _classify_one(self, features: Dict) -> str:
        cat, _ = self._classify_one_with_conf(features)
        return cat

    def _classify_one_with_conf(self, features: Dict) -> Tuple[str, float]:
        best_cat, best_conf = 'unknown', 0.0
        for rule in self._rules:
            result = rule(features)
            if result and result[1] > best_conf:
                best_cat, best_conf = result
        return best_cat, best_conf


# =============================================================================
# ML Contour Classifier
# =============================================================================

class MLContourClassifier:
    """
    ML-based contour classifier using sklearn or fallback rules.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = None
        self.model_path = model_path
        self.using_ml = False
        self.fallback = FallbackClassifier()

        if SKLEARN_AVAILABLE and model_path and Path(model_path).exists():
            try:
                self.model = joblib.load(model_path)
                scaler_path = Path(model_path).with_suffix('.scaler')
                if scaler_path.exists():
                    self.scaler = joblib.load(str(scaler_path))
                self.using_ml = True
                logger.info(f"Loaded ML model from {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}")
                self.using_ml = False

    def extract_features(self, contour: np.ndarray, mm_per_px: float) -> np.ndarray:
        """Extract 22 geometric features from contour."""
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        w_mm = w * mm_per_px
        h_mm = h * mm_per_px

        # Basic metrics
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        aspect = max(w_mm, h_mm) / min(w_mm, h_mm) if min(w_mm, h_mm) > 0 else 999

        # Convex hull metrics
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        hull_perimeter = cv2.arcLength(hull, True)
        convexity = hull_perimeter / perimeter if perimeter > 0 else 0

        # Extent (ratio of contour area to bounding rect)
        rect_area = w * h
        extent = area / rect_area if rect_area > 0 else 0

        # Hu moments (7 features)
        moments = cv2.moments(contour)
        hu = cv2.HuMoments(moments).flatten()
        # Log-transform for stability
        hu_log = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)

        # Compile features
        features = [
            w_mm, h_mm, area, perimeter,
            circularity, aspect, convexity, solidity, extent,
            *hu_log[:7],  # 7 Hu moments
            len(contour),  # point count
            max(w_mm, h_mm),  # max dimension
            min(w_mm, h_mm),  # min dimension
            w_mm * h_mm,  # bounding box area
            perimeter / (2 * (w_mm + h_mm)) if (w_mm + h_mm) > 0 else 0,  # compactness
        ]

        return np.array(features, dtype=np.float32)

    def classify(
        self,
        contour: np.ndarray,
        mm_per_px: float,
        img_width_mm: float,
        img_height_mm: float
    ) -> Tuple[ContourCategory, float]:
        """
        Classify a contour using ML or fallback rules.

        Returns (category, confidence)
        """
        features = self.extract_features(contour, mm_per_px)

        if self.using_ml and self.model is not None:
            try:
                X = features.reshape(1, -1)
                if self.scaler:
                    X = self.scaler.transform(X)

                proba = self.model.predict_proba(X)[0]
                class_idx = np.argmax(proba)
                confidence = float(proba[class_idx])
                category_name = self.model.classes_[class_idx]

                try:
                    category = ContourCategory(category_name)
                except ValueError:
                    category = ContourCategory.UNKNOWN

                return category, confidence
            except Exception as e:
                logger.warning(f"ML classification failed, using fallback: {e}")

        # Fallback to rule-based
        X = features.reshape(1, -1)
        pred = self.fallback.predict(X)[0]
        proba = self.fallback.predict_proba(X)[0]
        confidence = float(np.max(proba))

        try:
            category = ContourCategory(pred)
        except ValueError:
            category = ContourCategory.UNKNOWN

        return category, confidence

    def save_model(self, path: str):
        """Save trained model to disk."""
        if SKLEARN_AVAILABLE and self.model:
            joblib.dump(self.model, path)
            if self.scaler:
                scaler_path = Path(path).with_suffix('.scaler')
                joblib.dump(self.scaler, str(scaler_path))
            logger.info(f"Saved model to {path}")


# =============================================================================
# Primitive Detector
# =============================================================================

class PrimitiveDetector:
    """
    Detects and reconstructs geometric primitives from contours.
    """

    def __init__(self, mm_per_px: float):
        self.mm_per_px = mm_per_px

    def detect_circle(
        self,
        contour: np.ndarray,
        min_circularity: float = 0.85
    ) -> Optional[GeometricPrimitive]:
        """Detect if contour is a circle."""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        if perimeter == 0:
            return None

        circularity = 4 * np.pi * area / (perimeter * perimeter)

        if circularity >= min_circularity:
            (cx, cy), radius = cv2.minEnclosingCircle(contour)

            return GeometricPrimitive(
                type=PrimitiveType.CIRCLE,
                center=(cx * self.mm_per_px, cy * self.mm_per_px),
                radius=radius * self.mm_per_px,
                confidence=circularity,
                layer="CIRCLES"
            )

        return None

    def detect_ellipse(
        self,
        contour: np.ndarray,
        min_points: int = 5
    ) -> Optional[GeometricPrimitive]:
        """Detect if contour is an ellipse."""
        if len(contour) < min_points:
            return None

        try:
            ellipse = cv2.fitEllipse(contour)
            (cx, cy), (major, minor), angle = ellipse

            # Check fit quality by comparing area
            contour_area = cv2.contourArea(contour)
            ellipse_area = np.pi * major * minor / 4

            if ellipse_area > 0:
                fit_ratio = min(contour_area, ellipse_area) / max(contour_area, ellipse_area)

                if fit_ratio > 0.85:  # Good fit
                    return GeometricPrimitive(
                        type=PrimitiveType.ELLIPSE,
                        center=(cx * self.mm_per_px, cy * self.mm_per_px),
                        axes=(major * self.mm_per_px / 2, minor * self.mm_per_px / 2),
                        angle=angle,
                        confidence=fit_ratio,
                        layer="ELLIPSES"
                    )
        except cv2.error:
            pass

        return None

    def detect_arc(
        self,
        contour: np.ndarray,
        min_arc_length_deg: float = 30.0,
        max_arc_length_deg: float = 330.0
    ) -> Optional[GeometricPrimitive]:
        """Detect if contour is an arc (partial circle)."""
        if len(contour) < 5:
            return None

        # Check if contour is open (not closed)
        start_pt = contour[0][0]
        end_pt = contour[-1][0]
        gap = np.linalg.norm(start_pt - end_pt)
        perimeter = cv2.arcLength(contour, False)

        # If gap is significant relative to perimeter, it's likely open
        if gap < perimeter * 0.1:
            return None  # Too closed to be an arc

        try:
            (cx, cy), radius = cv2.minEnclosingCircle(contour)

            # Check how well points fit on the circle
            distances = []
            for pt in contour:
                d = np.linalg.norm(pt[0] - np.array([cx, cy]))
                distances.append(abs(d - radius))

            mean_error = np.mean(distances)
            if mean_error < radius * 0.1:  # Good circular fit
                # Calculate arc angles
                start_angle = math.degrees(math.atan2(
                    start_pt[1] - cy, start_pt[0] - cx
                ))
                end_angle = math.degrees(math.atan2(
                    end_pt[1] - cy, end_pt[0] - cx
                ))

                arc_span = abs(end_angle - start_angle)
                if arc_span > 180:
                    arc_span = 360 - arc_span

                if min_arc_length_deg < arc_span < max_arc_length_deg:
                    return GeometricPrimitive(
                        type=PrimitiveType.ARC,
                        center=(cx * self.mm_per_px, cy * self.mm_per_px),
                        radius=radius * self.mm_per_px,
                        start_angle=start_angle,
                        end_angle=end_angle,
                        confidence=1.0 - (mean_error / radius),
                        layer="ARCS"
                    )
        except Exception:
            pass

        return None

    def detect_all(
        self,
        contours: List[np.ndarray],
        min_confidence: float = 0.8,
        max_size_mm: float = 300.0
    ) -> List[GeometricPrimitive]:
        """Detect all primitives from a list of contours."""
        primitives = []

        for contour in contours:
            # Skip oversized contours (likely page borders or body outlines)
            x, y, w, h = cv2.boundingRect(contour)
            w_mm = w * self.mm_per_px
            h_mm = h * self.mm_per_px
            if max(w_mm, h_mm) > max_size_mm:
                continue

            # Try circle first (most specific)
            prim = self.detect_circle(contour)
            if prim and prim.confidence >= min_confidence:
                primitives.append(prim)
                continue

            # Try ellipse
            prim = self.detect_ellipse(contour)
            if prim and prim.confidence >= min_confidence:
                primitives.append(prim)
                continue

            # Try arc
            prim = self.detect_arc(contour)
            if prim and prim.confidence >= min_confidence:
                primitives.append(prim)

        return primitives


# =============================================================================
# Scale Detector
# =============================================================================

class ScaleDetector:
    """
    Detects and calculates scale factor from reference features.
    """

    def __init__(self, mm_per_px: float):
        self.mm_per_px = mm_per_px

    def detect_scale(
        self,
        contours: List[ContourInfo],
        instrument_type: InstrumentType = InstrumentType.ELECTRIC_GUITAR
    ) -> Tuple[float, str]:
        """
        Detect scale factor from reference features.

        Strategies (in order of preference):
        1. Neck pocket width (most reliable across instruments)
        2. Pickup route dimensions (common, well-defined)
        3. Bridge route (less common but reliable)
        4. Body outline ratio (fallback)

        Returns (scale_factor, source_description)
        """

        # Strategy 1: Neck pocket width
        neck_pockets = [c for c in contours if c.category == ContourCategory.NECK_POCKET]
        if neck_pockets:
            pocket = neck_pockets[0]
            measured = min(pocket.width_mm, pocket.height_mm)  # Width is typically smaller
            expected = REFERENCE_FEATURES["neck_pocket_width"]["expected"]
            tolerance = REFERENCE_FEATURES["neck_pocket_width"]["tolerance"]

            if abs(measured - expected) < expected * 0.5:  # Within 50%
                scale = expected / measured
                if 0.5 < scale < 2.0:  # Sanity check
                    return scale, f"neck_pocket ({measured:.1f}mm -> {expected}mm)"

        # Strategy 2: Pickup routes
        pickups = [c for c in contours if c.category == ContourCategory.PICKUP_ROUTE]
        if pickups:
            # Try to identify pickup type by dimensions
            for pickup in pickups:
                max_dim = pickup.max_dim

                # Humbucker detection
                humbucker_exp = REFERENCE_FEATURES["humbucker_route"]["expected"]
                if 65 < max_dim < 85:
                    scale = humbucker_exp / max_dim
                    if 0.5 < scale < 2.0:
                        return scale, f"humbucker_route ({max_dim:.1f}mm -> {humbucker_exp}mm)"

                # Single coil detection
                single_exp = REFERENCE_FEATURES["single_coil_route"]["expected"]
                if 80 < max_dim < 100:
                    scale = single_exp / max_dim
                    if 0.5 < scale < 2.0:
                        return scale, f"single_coil_route ({max_dim:.1f}mm -> {single_exp}mm)"

        # Strategy 3: Bridge route
        bridges = [c for c in contours if c.category == ContourCategory.BRIDGE_ROUTE]
        if bridges:
            bridge = bridges[0]
            max_dim = bridge.max_dim

            # Tune-o-matic style
            tom_exp = REFERENCE_FEATURES["tune_o_matic_bridge"]["expected"]
            if 100 < max_dim < 150:
                scale = tom_exp / max_dim
                if 0.5 < scale < 2.0:
                    return scale, f"bridge_route ({max_dim:.1f}mm -> {tom_exp}mm)"

            # Strat trem
            trem_exp = REFERENCE_FEATURES["strat_trem_route"]["expected"]
            if 80 < max_dim < 100:
                scale = trem_exp / max_dim
                if 0.5 < scale < 2.0:
                    return scale, f"trem_route ({max_dim:.1f}mm -> {trem_exp}mm)"

        # Strategy 4: Body outline ratio (fallback)
        bodies = [c for c in contours if c.category == ContourCategory.BODY_OUTLINE]
        if bodies and instrument_type.value in INSTRUMENT_SPECS:
            body = bodies[0]
            spec_name = instrument_type.value
            # Map enum to spec key
            spec_map = {
                'electric': 'stratocaster',  # Default to Strat
                'acoustic': 'dreadnought',
                'archtop': 'es335',
                'bass': 'stratocaster',  # Approximate
            }
            spec_key = spec_map.get(spec_name, spec_name)

            if spec_key in INSTRUMENT_SPECS:
                spec = INSTRUMENT_SPECS[spec_key]
                expected_length = (spec.body_length_range[0] + spec.body_length_range[1]) / 2
                measured_length = body.max_dim

                scale = expected_length / measured_length
                if 0.5 < scale < 2.0:
                    return scale, f"body_ratio ({measured_length:.1f}mm -> {expected_length:.0f}mm)"

        # No reliable reference found
        return 1.0, "none"


# =============================================================================
# Feedback System
# =============================================================================

class FeedbackSystem:
    """
    Collects and manages user feedback for continuous improvement.
    """

    def __init__(self, feedback_dir: str = ".feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.pending_reviews: List[Dict] = []

    def record_classification(
        self,
        contour_hash: str,
        predicted_category: str,
        confidence: float,
        features: np.ndarray,
        source_file: str
    ):
        """Record a classification for potential review."""
        record = {
            "contour_hash": contour_hash,
            "predicted": predicted_category,
            "confidence": confidence,
            "features": features.tolist(),
            "source": source_file,
            "timestamp": datetime.now().isoformat(),
            "reviewed": False,
            "correct_label": None
        }
        self.pending_reviews.append(record)

    def submit_correction(
        self,
        contour_hash: str,
        correct_category: str,
        reviewer: str = "user"
    ) -> bool:
        """Submit a correction for a classification."""
        for record in self.pending_reviews:
            if record["contour_hash"] == contour_hash:
                record["correct_label"] = correct_category
                record["reviewed"] = True
                record["reviewer"] = reviewer
                record["review_timestamp"] = datetime.now().isoformat()

                # Save to disk
                self._save_feedback(record)
                return True
        return False

    def _save_feedback(self, record: Dict):
        """Save feedback record to disk."""
        filename = f"{record['contour_hash']}_{record['timestamp'][:10]}.json"
        filepath = self.feedback_dir / filename

        with open(filepath, 'w') as f:
            json.dump(record, f, indent=2)

    def get_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load all reviewed feedback as training data."""
        features_list = []
        labels_list = []

        for filepath in self.feedback_dir.glob("*.json"):
            try:
                with open(filepath) as f:
                    record = json.load(f)

                if record.get("reviewed") and record.get("correct_label"):
                    features_list.append(record["features"])
                    labels_list.append(record["correct_label"])
            except Exception as e:
                logger.warning(f"Failed to load feedback {filepath}: {e}")

        if features_list:
            return np.array(features_list), np.array(labels_list)
        return np.array([]), np.array([])

    def get_pending_count(self) -> int:
        """Count pending reviews."""
        return sum(1 for r in self.pending_reviews if not r.get("reviewed"))

    def get_low_confidence_samples(self, threshold: float = 0.7) -> List[Dict]:
        """Get samples with low confidence for review."""
        return [r for r in self.pending_reviews
                if not r.get("reviewed") and r.get("confidence", 1.0) < threshold]


# =============================================================================
# Training Data Collector
# =============================================================================

class TrainingDataCollector:
    """
    Collects labeled training data for ML classifier.
    """

    def __init__(self, data_dir: str = ".training_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.samples: List[Dict] = []

    def add_sample(
        self,
        features: np.ndarray,
        label: str,
        source_file: str,
        contour_hash: str
    ):
        """Add a labeled training sample."""
        sample = {
            "features": features.tolist(),
            "label": label,
            "source": source_file,
            "hash": contour_hash,
            "timestamp": datetime.now().isoformat()
        }
        self.samples.append(sample)

    def save(self, filename: str = "training_data.json"):
        """Save collected samples to disk."""
        filepath = self.data_dir / filename
        with open(filepath, 'w') as f:
            json.dump(self.samples, f, indent=2)
        logger.info(f"Saved {len(self.samples)} training samples to {filepath}")

    def load(self, filename: str = "training_data.json") -> int:
        """Load existing training data."""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                self.samples = json.load(f)
            return len(self.samples)
        return 0

    def get_training_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get features and labels as numpy arrays."""
        if not self.samples:
            return np.array([]), np.array([])

        features = np.array([s["features"] for s in self.samples])
        labels = np.array([s["label"] for s in self.samples])
        return features, labels

    def train_classifier(self) -> Optional[Any]:
        """Train a new classifier on collected data."""
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available for training")
            return None

        X, y = self.get_training_arrays()
        if len(X) < 10:
            logger.warning(f"Not enough samples for training ({len(X)})")
            return None

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        clf.fit(X_scaled, y)

        logger.info(f"Trained classifier on {len(X)} samples")
        return clf, scaler


# =============================================================================
# Image Loading
# =============================================================================

def load_image(
    source_path: str,
    page_num: int = 0,
    dpi: int = 400,
    use_cache: bool = True
) -> np.ndarray:
    """
    Load image from PDF or image file.

    Args:
        source_path: Path to PDF or image file
        page_num: Page number for PDFs (0-indexed)
        dpi: Resolution for PDF rasterization
        use_cache: Whether to use image cache

    Returns:
        BGR numpy array
    """
    # Check cache first
    if use_cache:
        cached = _image_cache.get(source_path, page_num, dpi)
        if cached is not None:
            logger.debug(f"Cache hit for {Path(source_path).name}")
            return cached

    ext = Path(source_path).suffix.lower()

    if ext == '.pdf':
        if fitz is None:
            raise ImportError("PyMuPDF required for PDF support: pip install pymupdf")

        doc = fitz.open(source_path)
        if page_num >= len(doc):
            raise ValueError(f"Page {page_num} doesn't exist. PDF has {len(doc)} pages.")

        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )

        # Convert to BGR
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        doc.close()
        logger.info(f"Loaded PDF page {page_num} at {dpi} DPI: {img.shape[1]}x{img.shape[0]}px")

    else:
        # Direct image loading
        img = cv2.imread(source_path)
        if img is None:
            raise ValueError(f"Could not load image: {source_path}")
        logger.info(f"Loaded image: {img.shape[1]}x{img.shape[0]}px")

    # Cache the result
    if use_cache:
        _image_cache.put(source_path, page_num, dpi, img)

    return img


# =============================================================================
# Image Analysis
# =============================================================================

@dataclass
class ImageAnalysis:
    """Results of image analysis."""
    blueprint_type: str  # 'dark', 'faint', 'inverted'
    recommended_threshold: int
    recommended_method: str  # 'fixed', 'otsu', 'adaptive', 'canny_adaptive'
    white_ratio: float
    dark_ratio: float
    min_pixel: int
    max_pixel: int
    mean_pixel: float


def analyze_image(image: np.ndarray) -> ImageAnalysis:
    """
    Analyze image to determine best extraction strategy.

    Returns analysis with recommended threshold method.
    """
    cf = ColorFilter()
    analysis = cf.analyze_image(image)

    return ImageAnalysis(
        blueprint_type=analysis['blueprint_type'],
        recommended_threshold=analysis['recommended_threshold'],
        recommended_method=analysis['recommended_method'],
        white_ratio=analysis['white_ratio'],
        dark_ratio=analysis['dark_ratio'],
        min_pixel=analysis['min_pixel'],
        max_pixel=analysis['max_pixel'],
        mean_pixel=analysis['mean_pixel']
    )


# =============================================================================
# Line Extraction Methods
# =============================================================================

def extract_canny_adaptive(image: np.ndarray, gap_close: int = 0) -> np.ndarray:
    """
    Combined Canny + Adaptive threshold extraction.
    Best for faint lines and fine details.

    Args:
        image: BGR image
        gap_close: Morphological closing kernel size (0 = disabled)

    Returns:
        Binary mask
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Method 1: Adaptive threshold
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 5
    )

    # Method 2: Canny edge detection
    edges = cv2.Canny(gray, 30, 100)
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Combine both
    combined = cv2.bitwise_or(adaptive, edges)

    # Light cleanup
    kernel_small = np.ones((2, 2), np.uint8)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_small)

    if gap_close > 0:
        kernel_close = np.ones((gap_close, gap_close), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close, iterations=2)

    logger.info(f"Canny+Adaptive extraction: {cv2.countNonZero(combined)} pixels")
    return combined


# =============================================================================
# Dark Background Detection
# =============================================================================

def detect_dark_background(image: np.ndarray, border_px: int = 20, dark_threshold: float = 0.65) -> bool:
    """
    Detect if the image has a dark background (e.g. white-on-black blueprints).

    Samples a border strip around all four edges and checks whether the
    majority of border pixels are dark (< 80 intensity).

    Args:
        image: BGR or grayscale image
        border_px: Width of border strip to sample (pixels)
        dark_threshold: Fraction of dark border pixels required (0-1)

    Returns:
        True if background is dark
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h, w = gray.shape[:2]
    border_px = min(border_px, h // 4, w // 4)

    # Sample four border strips
    top = gray[:border_px, :]
    bottom = gray[h - border_px:, :]
    left = gray[border_px:h - border_px, :border_px]
    right = gray[border_px:h - border_px, w - border_px:]

    border_pixels = np.concatenate([top.ravel(), bottom.ravel(), left.ravel(), right.ravel()])
    dark_ratio = np.mean(border_pixels < 80)

    is_dark = dark_ratio >= dark_threshold
    logger.info(f"Dark background detection: {dark_ratio:.1%} dark border pixels → {'DARK' if is_dark else 'LIGHT'}")
    return is_dark


def extract_dark_lines(
    image: np.ndarray,
    threshold: int = 100,
    gap_close: int = 0
) -> np.ndarray:
    """
    Extract dark lines using fixed threshold.
    Best for high-contrast blueprints with dark lines.

    Args:
        image: BGR image
        threshold: Darkness threshold (0-255, lower = darker)
        gap_close: Morphological closing kernel size

    Returns:
        Binary mask
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    # Basic cleanup
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    if gap_close > 0:
        kernel_close = np.ones((gap_close, gap_close), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)

    logger.info(f"Dark line extraction (threshold={threshold}): {cv2.countNonZero(mask)} pixels")
    return mask


def extract_auto(image: np.ndarray, gap_close: int = 0) -> np.ndarray:
    """
    Auto-detect best extraction method based on image analysis.

    Args:
        image: BGR image
        gap_close: Morphological closing kernel size

    Returns:
        Binary mask
    """
    analysis = analyze_image(image)

    if analysis.recommended_method == 'canny_adaptive':
        return extract_canny_adaptive(image, gap_close)
    elif analysis.recommended_method == 'otsu':
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        if gap_close > 0:
            kernel = np.ones((gap_close, gap_close), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        return mask
    else:
        return extract_dark_lines(image, analysis.recommended_threshold, gap_close)


# =============================================================================
# Dual-Pass Extraction
# =============================================================================

def dual_pass_extraction(
    image: np.ndarray,
    body_gap_close: int = 7,
    detail_gap_close: int = 0,
    body_threshold: int = 120,
    detail_threshold: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Two-pass extraction: aggressive for body outline, lighter for details.

    Blueprints often have broken lines in the body outline due to scanning
    or drawing style, but internal features (pickup routes, cavities) have
    cleaner lines. This uses different settings for each.

    Args:
        image: BGR image
        body_gap_close: Aggressive gap closing for body outline
        detail_gap_close: Lighter gap closing for internal features
        body_threshold: Threshold for body extraction (can be higher)
        detail_threshold: Threshold for detail extraction (lower = more sensitive)

    Returns:
        Tuple of (body_mask, detail_mask)
    """
    logger.info("Starting dual-pass extraction...")

    # Pass 1: Aggressive extraction for body outline
    body_mask = extract_dark_lines(image, body_threshold, body_gap_close)

    # Pass 2: Lighter extraction for internal features
    detail_mask = extract_dark_lines(image, detail_threshold, detail_gap_close)

    logger.info(f"Dual-pass: body={cv2.countNonZero(body_mask)}px, "
                f"detail={cv2.countNonZero(detail_mask)}px")

    return body_mask, detail_mask


# =============================================================================
# Contour Classification
# =============================================================================

def is_text_like(
    width_mm: float,
    height_mm: float,
    circularity: float,
    aspect_ratio: float
) -> bool:
    """
    Heuristic to detect text/annotation contours.

    Text tends to be:
    - Small (< 15mm max dimension)
    - Elongated (high aspect ratio > 2)
    - Low circularity (< 0.3)
    """
    max_dim = max(width_mm, height_mm)

    # Very small items are likely noise or text
    if max_dim < 5:
        return True

    # Text-like characteristics
    if max_dim < 15 and aspect_ratio > 2 and circularity < 0.3:
        return True

    # Long thin lines (dimension lines, rulers)
    if aspect_ratio > 8 and width_mm < 5:
        return True
    if aspect_ratio > 8 and height_mm < 5:
        return True

    return False


def classify_contour(
    contour: np.ndarray,
    mm_per_px: float,
    img_width_mm: float,
    img_height_mm: float,
    instrument_type: InstrumentType = InstrumentType.ELECTRIC_GUITAR,
    hierarchy_level: int = 0,
    ml_classifier: Optional[MLContourClassifier] = None
) -> ContourInfo:
    """
    Classify a contour based on dimensions and shape characteristics.

    Args:
        contour: OpenCV contour array
        mm_per_px: Pixels to mm conversion factor
        img_width_mm: Image width in mm
        img_height_mm: Image height in mm
        instrument_type: Type of instrument for context
        hierarchy_level: Contour nesting level (0 = outermost)
        ml_classifier: Optional ML classifier

    Returns:
        ContourInfo with classification
    """
    x, y, w, h = cv2.boundingRect(contour)
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)

    w_mm = w * mm_per_px
    h_mm = h * mm_per_px
    max_dim = max(w_mm, h_mm)
    min_dim = min(w_mm, h_mm)

    # Calculate shape metrics
    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
    aspect_ratio = max_dim / min_dim if min_dim > 0 else 999

    # Additional metrics for Phase 3.5
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    hull_perimeter = cv2.arcLength(hull, True)

    convexity = hull_perimeter / perimeter if perimeter > 0 else 0
    solidity = area / hull_area if hull_area > 0 else 0
    extent = area / (w * h) if w * h > 0 else 0

    # Hu moments
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten().tolist()

    ml_confidence = 0.0

    # Try ML classification first if available
    if ml_classifier:
        category, ml_confidence = ml_classifier.classify(
            contour, mm_per_px, img_width_mm, img_height_mm
        )
        if ml_confidence > 0.75:  # High confidence, use ML result
            return ContourInfo(
                contour=contour,
                category=category,
                width_mm=w_mm,
                height_mm=h_mm,
                area_px=area,
                perimeter_px=perimeter,
                circularity=circularity,
                aspect_ratio=aspect_ratio,
                point_count=len(contour),
                bbox=(x, y, w, h),
                hierarchy_level=hierarchy_level,
                ml_confidence=ml_confidence,
                hu_moments=hu,
                convexity=convexity,
                solidity=solidity,
                extent=extent
            )

    # Rule-based classification (fallback or when ML confidence is low)
    category = ContourCategory.UNKNOWN

    # BODY OUTLINE FIRST: Check before page border since body may span large portion
    # Body has specific size criteria that distinguish it from page borders
    # Range: soprano ukulele (~200mm) to jumbo acoustic (~560mm), with 20% tolerance
    if 180 < max_dim < 700 and 140 < min_dim < 550:
        category = ContourCategory.BODY_OUTLINE

    # Page border detection (spans nearly full page AND not body-sized)
    # Use 98% threshold to avoid false positives with large guitar bodies
    elif w_mm > img_width_mm * 0.98 or h_mm > img_height_mm * 0.98:
        category = ContourCategory.PAGE_BORDER

    # Text/annotation detection
    elif is_text_like(w_mm, h_mm, circularity, aspect_ratio):
        category = ContourCategory.TEXT

    # Pickguard: medium-large, curved
    elif 150 < max_dim < 400 and 100 < min_dim < 350:
        if instrument_type in (InstrumentType.ELECTRIC_GUITAR, InstrumentType.ACOUSTIC_GUITAR):
            category = ContourCategory.PICKGUARD

    # Rhythm circuit (Jazzmaster/Jaguar style, electric only)
    elif 180 < max_dim < 260 and 80 < min_dim < 120:
        if instrument_type in (InstrumentType.ELECTRIC_GUITAR, InstrumentType.BASS, InstrumentType.ARCHTOP):
            category = ContourCategory.RHYTHM_CIRCUIT

    # Control cavity (electric only)
    elif 80 < max_dim < 180 and 50 < min_dim < 120:
        if instrument_type in (InstrumentType.ELECTRIC_GUITAR, InstrumentType.BASS, InstrumentType.ARCHTOP):
            category = ContourCategory.CONTROL_CAVITY

    # Neck pocket (electric only — bolt-on necks)
    elif 60 < max_dim < 120 and 50 < min_dim < 85:
        if (1.0 < aspect_ratio < 1.8  # Roughly square
            and instrument_type in (InstrumentType.ELECTRIC_GUITAR, InstrumentType.BASS)):
            category = ContourCategory.NECK_POCKET

    # Pickup routes (electric instruments only)
    elif 70 < max_dim < 110 and 30 < min_dim < 65:
        if (1.3 < aspect_ratio < 3.0  # Elongated
            and instrument_type in (InstrumentType.ELECTRIC_GUITAR, InstrumentType.BASS, InstrumentType.ARCHTOP)):
            category = ContourCategory.PICKUP_ROUTE

    # Bridge route (electric instruments only)
    elif 55 < max_dim < 140 and 30 < min_dim < 80:
        if instrument_type in (InstrumentType.ELECTRIC_GUITAR, InstrumentType.BASS, InstrumentType.ARCHTOP):
            category = ContourCategory.BRIDGE_ROUTE

    # D-hole (Selmer style)
    elif 150 < max_dim < 250 and 70 < min_dim < 130:
        if instrument_type == InstrumentType.ACOUSTIC_GUITAR:
            category = ContourCategory.D_HOLE

    # Soundhole (round)
    elif 80 < max_dim < 130 and 80 < min_dim < 130:
        if 0.7 < circularity < 1.0:  # Circular
            category = ContourCategory.SOUNDHOLE

    # F-hole
    elif 130 < max_dim < 180 and 30 < min_dim < 55:
        if instrument_type in (InstrumentType.ARCHTOP, InstrumentType.ACOUSTIC_GUITAR):
            category = ContourCategory.F_HOLE

    # Rosette
    elif 60 < max_dim < 90 and 60 < min_dim < 90:
        if 0.6 < circularity < 1.0:
            category = ContourCategory.ROSETTE

    # Jack route (electric instruments only, non-circular)
    elif (20 < max_dim < 50 and 15 < min_dim < 45
          and circularity < 0.7  # jack routes are not circular
          and instrument_type in (InstrumentType.ELECTRIC_GUITAR, InstrumentType.BASS, InstrumentType.ARCHTOP)):
        category = ContourCategory.JACK_ROUTE

    # Small features (screw holes, etc)
    elif max_dim < 25:
        category = ContourCategory.SMALL_FEATURE

    # Bracing (long thin pieces)
    elif max_dim > 150 and min_dim < 45:
        if instrument_type == InstrumentType.ACOUSTIC_GUITAR:
            category = ContourCategory.BRACING

    # Large unclassified contours that could be body outlines
    # Catch-all for contours > 150mm that didn't match specific features
    # These go to re-ranking for proper body candidate scoring
    if category == ContourCategory.UNKNOWN and max_dim > 150:
        category = ContourCategory.BODY_OUTLINE_CANDIDATE

    return ContourInfo(
        contour=contour,
        category=category,
        width_mm=w_mm,
        height_mm=h_mm,
        area_px=area,
        perimeter_px=perimeter,
        circularity=circularity,
        aspect_ratio=aspect_ratio,
        point_count=len(contour),
        bbox=(x, y, w, h),
        hierarchy_level=hierarchy_level,
        ml_confidence=ml_confidence,
        hu_moments=hu,
        convexity=convexity,
        solidity=solidity,
        extent=extent
    )


# =============================================================================
# Grid-Enhanced Body Scoring
# =============================================================================

def score_body_candidate(
    info: ContourInfo,
    image_width: int,
    image_height: int,
    grid_classifier=None,
) -> float:
    """
    Multi-factor scoring to identify the true body outline contour.

    Addresses the 0% detection rate by combining positional, geometric,
    and grid zone analysis instead of relying on dimension ranges alone.

    Factors:
        1. Aspect ratio (guitar bodies typically 1.0-1.8 height/width)
        2. Solidity (compact filled shapes, not text or logos)
        3. Size relative to image (body occupies 5-70% of image area)
        4. Position (body tends toward center, not page corners)
        5. Grid zone overlap (BODY_CANVAS from STEM Guitar grid)
        6. Symmetry about centerline (bodies are bilaterally symmetric)

    Returns:
        Score 0-100, higher = more likely to be the true body outline.
    """
    score = 0.0
    x, y, w, h = info.bbox

    # Factor 1: Aspect ratio
    # Guitar bodies (height > width) have aspect ratio 1.0-1.8
    aspect = max(w, h) / min(w, h) if min(w, h) > 0 else 999
    if 1.0 <= aspect <= 1.8:
        # Peak at ~1.3 (typical electric guitar body)
        aspect_score = 25.0 * (1.0 - min(abs(aspect - 1.3) / 0.5, 1.0))
        score += max(0.0, aspect_score)

    # Factor 2: Solidity (filled compact shape, not text/wireframe/logo)
    # Real body outlines have solidity > 0.85 (solid filled shapes)
    # Low solidity indicates hollow shapes, logos, or fragments
    if info.solidity > 0.85:
        score += 20.0    # Strong positive — likely body outline
    elif info.solidity > 0.70:
        score += 10.0    # Acceptable
    elif info.solidity > 0.50:
        score += 0.0     # Neutral
    else:
        score -= 20.0    # Penalty — hollow shape, not a body

    # Factor 3: Size relative to image
    image_area = image_width * image_height
    area_ratio = info.area_px / image_area if image_area > 0 else 0
    if 0.05 <= area_ratio <= 0.70:
        if 0.10 <= area_ratio <= 0.50:
            score += 20.0  # Sweet spot
        else:
            score += 10.0  # Plausible but outside typical range

    # Factor 4: Position (body should be roughly centered)
    cx = (x + w / 2) / image_width if image_width > 0 else 0.5
    cy = (y + h / 2) / image_height if image_height > 0 else 0.5
    center_dist = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    if center_dist < 0.35:
        score += 15.0 * (1.0 - center_dist / 0.35)

    # Factor 5 & 6: Grid zone overlap + symmetry (if classifier available)
    if grid_classifier is not None:
        nx_min = x / image_width if image_width > 0 else 0
        ny_min = y / image_height if image_height > 0 else 0
        nx_max = (x + w) / image_width if image_width > 0 else 1
        ny_max = (y + h) / image_height if image_height > 0 else 1

        zone_result = grid_classifier.classify_bbox(nx_min, ny_min, nx_max, ny_max)

        # Body canvas overlap (the main body area in the STEM grid)
        for zone_match in zone_result.all_zones:
            if zone_match.zone.zone_type.value == "body_canvas":
                score += 20.0 * zone_match.overlap
                break

        # Symmetry bonus (real bodies are bilaterally symmetric)
        if zone_result.symmetry_score > 0.7:
            score += 10.0 * zone_result.symmetry_score

        # Proportion validation bonus
        if zone_result.proportion_valid:
            score += 5.0

    return min(score, 100.0)


def rerank_body_candidates(
    classified: Dict[ContourCategory, List[ContourInfo]],
    image_width: int,
    image_height: int,
    grid_classifier=None,
    min_body_score: float = 30.0,
    min_body_dim: float = 300.0,
    max_body_aspect_ratio: float = 2.0,
    spec_name: Optional[str] = None,
) -> Dict[ContourCategory, List[ContourInfo]]:
    """
    Re-rank body outline candidates using multi-factor scoring.

    After initial rule-based classification, this function:
    1. Scores all BODY_OUTLINE candidates
    2. Checks UNKNOWN contours that might be missed bodies
    3. Demotes low-scoring "bodies" and promotes high-scoring unknowns

    This is the primary fix for the 0% accuracy problem — the old rule-based
    classify_contour() picks logos and borders because it only checks dimension
    ranges. This re-ranker adds shape, position, and grid zone analysis.
    """
    # Gather all body candidates (current + potential from UNKNOWN)
    body_candidates = []

    # Existing BODY_OUTLINE contours
    for info in classified.get(ContourCategory.BODY_OUTLINE, []):
        # Minimum solidity gate — hollow shapes cannot be body outlines
        if info.solidity < 0.40:
            continue
        body_score = score_body_candidate(info, image_width, image_height, grid_classifier)
        body_candidates.append((body_score, info, 'existing'))

    # Check BODY_OUTLINE_CANDIDATE contours — large shapes flagged for re-ranking
    candidates_to_remove = []
    for info in classified.get(ContourCategory.BODY_OUTLINE_CANDIDATE, []):
        # Minimum solidity gate — hollow shapes cannot be body outlines
        if info.solidity < 0.40:
            continue
        body_score = score_body_candidate(info, image_width, image_height, grid_classifier)
        if body_score >= min_body_score:
            body_candidates.append((body_score, info, 'candidate'))
            candidates_to_remove.append(info)

    # Check UNKNOWN contours — some may be misclassified bodies
    unknowns_to_remove = []
    for info in classified.get(ContourCategory.UNKNOWN, []):
        # Minimum solidity gate — hollow shapes cannot be body outlines
        if info.solidity < 0.40:
            continue
        body_score = score_body_candidate(info, image_width, image_height, grid_classifier)
        if body_score >= min_body_score:
            body_candidates.append((body_score, info, 'promoted'))
            unknowns_to_remove.append(info)

    # Also check PICKGUARD — large pickguards sometimes misclassify as the body
    pickguards_to_remove = []
    for info in classified.get(ContourCategory.PICKGUARD, []):
        # Minimum solidity gate — hollow shapes cannot be body outlines
        if info.solidity < 0.40:
            continue
        body_score = score_body_candidate(info, image_width, image_height, grid_classifier)
        if body_score >= 60.0:  # High threshold to steal from pickguard
            body_candidates.append((body_score, info, 'promoted'))
            pickguards_to_remove.append(info)

    if not body_candidates:
        return classified

    # Sort by score descending
    body_candidates.sort(key=lambda x: x[0], reverse=True)

    # Get max expected height from spec for height ceiling check
    max_expected_height = None
    if spec_name and spec_name in INSTRUMENT_SPECS:
        spec = INSTRUMENT_SPECS[spec_name]
        max_expected_height = spec.body_length_range[1] if spec.body_length_range[1] else None

    # Loop through candidates — reject and try next if height ceiling violated
    elected_candidate = None
    for candidate_idx, (best_score, best_info, best_source) in enumerate(body_candidates):
        logger.info(
            f"Body re-ranking: candidate {candidate_idx} score={best_score:.1f} "
            f"({best_source}, {best_info.width_mm:.0f}x{best_info.height_mm:.0f}mm)"
        )

        if best_score < min_body_score:
            logger.warning(f"Candidate {candidate_idx} scored only {best_score:.1f} — below threshold {min_body_score}")
            continue  # Try next candidate

        # Body geometry sanity check — reject candidates that can't be a real body.
        # Three checks: (1) minimum dimension, (2) aspect ratio, (3) height ceiling.
        # All thresholds are configurable via InstrumentSpec for small instruments.
        best_max_dim = max(best_info.width_mm, best_info.height_mm)
        best_min_dim = min(best_info.width_mm, best_info.height_mm)
        best_aspect = best_max_dim / best_min_dim if best_min_dim > 0 else 999.0

        reject_body = False
        reject_reason = ""
        if best_max_dim < min_body_dim:
            reject_body = True
            reject_reason = (f"only {best_max_dim:.0f}mm — below {min_body_dim:.0f}mm minimum")
        elif best_aspect > max_body_aspect_ratio:
            reject_body = True
            reject_reason = (
                f"aspect ratio {best_aspect:.2f} exceeds {max_body_aspect_ratio:.1f} "
                f"({best_info.width_mm:.0f}x{best_info.height_mm:.0f}mm) — "
                f"likely a neck, pickguard, or component strip"
            )
        elif max_expected_height and best_max_dim > 1.5 * max_expected_height:
            # Phase 5G: Height ceiling check — reject if contour is too tall
            # (likely picked up neck extension or multi-view elements)
            reject_body = True
            reject_reason = (
                f"height {best_max_dim:.0f}mm exceeds 1.5× expected max {max_expected_height:.0f}mm "
                f"({best_info.width_mm:.0f}x{best_info.height_mm:.0f}mm) — "
                f"likely includes neck extension or multi-view elements"
            )

        if reject_body:
            logger.info(f"Candidate {candidate_idx} rejected: {reject_reason}. Trying next.")
            continue  # Try next candidate

        # This candidate passed all checks
        elected_candidate = (best_score, best_info, best_source)
        break

    # If no candidate passed, treat as component-only sheet
    if elected_candidate is None:
        best_score, best_info, best_source = body_candidates[0]  # Use first for logging
        reject_reason = "all candidates failed validation"
        logger.info(
            f"Best body candidate rejected: {reject_reason}. "
            f"Treating as component-only sheet."
        )
        # Reclassify all body candidates back to their proper categories
        for score, info, source in body_candidates:
            max_d = max(info.width_mm, info.height_mm)
            min_d = min(info.width_mm, info.height_mm)
            if 100 < max_d < 400 and 50 < min_d < 350:
                if ContourCategory.PICKGUARD not in classified:
                    classified[ContourCategory.PICKGUARD] = []
                classified[ContourCategory.PICKGUARD].append(info)
            else:
                if ContourCategory.UNKNOWN not in classified:
                    classified[ContourCategory.UNKNOWN] = []
                classified[ContourCategory.UNKNOWN].append(info)
        # Clear body outline — this sheet has no body
        classified[ContourCategory.BODY_OUTLINE] = []
        return classified

    # Rebuild BODY_OUTLINE with the elected candidate
    best_score, best_info, best_source = elected_candidate
    new_bodies = [best_info]

    # Demote other previous body candidates to UNKNOWN
    demoted = []
    for score, info, source in body_candidates[1:]:
        if source == 'existing':
            demoted.append(info)

    # Apply changes
    classified[ContourCategory.BODY_OUTLINE] = new_bodies

    # Remove promoted contours from their original categories
    unknowns_to_remove_ids = {id(c) for c in unknowns_to_remove}
    pickguards_to_remove_ids = {id(c) for c in pickguards_to_remove}

    # Remove promoted BODY_OUTLINE_CANDIDATE contours
    candidates_to_remove_ids = {id(c) for c in candidates_to_remove}
    if candidates_to_remove_ids and ContourCategory.BODY_OUTLINE_CANDIDATE in classified:
        classified[ContourCategory.BODY_OUTLINE_CANDIDATE] = [
            c for c in classified[ContourCategory.BODY_OUTLINE_CANDIDATE] if id(c) not in candidates_to_remove_ids
        ]

    if unknowns_to_remove_ids and ContourCategory.UNKNOWN in classified:
        classified[ContourCategory.UNKNOWN] = [
            c for c in classified[ContourCategory.UNKNOWN] if id(c) not in unknowns_to_remove_ids
        ]
    if pickguards_to_remove_ids and ContourCategory.PICKGUARD in classified:
        classified[ContourCategory.PICKGUARD] = [
            c for c in classified[ContourCategory.PICKGUARD] if id(c) not in pickguards_to_remove_ids
        ]

    # Add demoted bodies to UNKNOWN
    if demoted:
        if ContourCategory.UNKNOWN not in classified:
            classified[ContourCategory.UNKNOWN] = []
        classified[ContourCategory.UNKNOWN].extend(demoted)
        logger.info(f"Demoted {len(demoted)} false body candidates to UNKNOWN")

    return classified


# =============================================================================
# Hierarchy-Aware Extraction
# =============================================================================

def extract_with_hierarchy(
    mask: np.ndarray,
    mm_per_px: float,
    img_width_mm: float,
    img_height_mm: float,
    instrument_type: InstrumentType = InstrumentType.ELECTRIC_GUITAR,
    min_area: float = 100,
    ml_classifier: Optional[MLContourClassifier] = None,
    grid_classifier=None,
    min_body_dim: float = 300.0,
    max_body_aspect_ratio: float = 2.0,
    spec_name: Optional[str] = None
) -> Dict[ContourCategory, List[ContourInfo]]:
    """
    Extract contours with hierarchy information.

    Uses RETR_TREE to capture parent-child relationships:
    - Body outline (level 0)
    - Cavities/pockets inside body (level 1)
    - Details inside cavities (level 2+)

    When grid_classifier is provided, applies multi-factor body re-ranking
    after initial classification to fix the 0% body detection problem.

    Args:
        mask: Binary mask
        mm_per_px: Pixels to mm conversion
        img_width_mm: Image width in mm
        img_height_mm: Image height in mm
        instrument_type: Instrument type for classification context
        min_area: Minimum contour area in pixels
        ml_classifier: Optional ML classifier
        grid_classifier: Optional GridZoneClassifier for body re-ranking
        min_body_dim: Minimum largest dimension for body candidates (mm)
        max_body_aspect_ratio: Maximum aspect ratio for body candidates

    Returns:
        Dict mapping categories to lists of ContourInfo
    """
    contours, hierarchy = cv2.findContours(
        mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )

    if hierarchy is None:
        hierarchy = np.array([[[-1, -1, -1, -1]] * len(contours)])

    logger.info(f"Found {len(contours)} contours with hierarchy")

    # Calculate hierarchy levels
    def get_level(idx: int, hier: np.ndarray) -> int:
        level = 0
        parent = hier[0][idx][3]  # Parent index
        while parent >= 0:
            level += 1
            parent = hier[0][parent][3]
        return level

    classified: Dict[ContourCategory, List[ContourInfo]] = {}

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        level = get_level(i, hierarchy)
        parent_idx = hierarchy[0][i][3]

        info = classify_contour(
            contour, mm_per_px, img_width_mm, img_height_mm,
            instrument_type, level, ml_classifier
        )
        info.parent_idx = parent_idx

        if info.category not in classified:
            classified[info.category] = []
        classified[info.category].append(info)

    # Sort each category by area (largest first)
    for cat in classified:
        classified[cat].sort(key=lambda x: x.area_px, reverse=True)

    # Log summary (before re-ranking)
    for cat, items in classified.items():
        if items and cat not in (ContourCategory.TEXT, ContourCategory.PAGE_BORDER,
                                  ContourCategory.SMALL_FEATURE, ContourCategory.UNKNOWN):
            logger.info(f"  {cat.value}: {len(items)}")

    # Re-rank body candidates using grid zone + multi-factor scoring
    if grid_classifier is not None:
        image_height_px = int(img_height_mm / mm_per_px) if mm_per_px > 0 else 0
        image_width_px = int(img_width_mm / mm_per_px) if mm_per_px > 0 else 0
        classified = rerank_body_candidates(
            classified, image_width_px, image_height_px, grid_classifier,
            min_body_dim=min_body_dim,
            max_body_aspect_ratio=max_body_aspect_ratio,
            spec_name=spec_name
        )

    return classified


# =============================================================================
# Dimension Validation
# =============================================================================

def validate_dimensions(
    body_width_mm: float,
    body_height_mm: float,
    spec_name: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate extracted dimensions against known instrument specs.

    Args:
        body_width_mm: Extracted body width
        body_height_mm: Extracted body height
        spec_name: Optional specific instrument to validate against

    Returns:
        Tuple of (passed, list of warnings)
    """
    warnings = []
    passed = True

    # Ensure length > width
    body_length = max(body_width_mm, body_height_mm)
    body_width = min(body_width_mm, body_height_mm)

    if spec_name and spec_name in INSTRUMENT_SPECS:
        spec = INSTRUMENT_SPECS[spec_name]

        # Check length
        if not (spec.body_length_range[0] <= body_length <= spec.body_length_range[1]):
            warnings.append(
                f"Body length {body_length:.0f}mm outside expected range "
                f"{spec.body_length_range[0]}-{spec.body_length_range[1]}mm for {spec.name}"
            )
            passed = False

        # Check width
        if not (spec.body_width_range[0] <= body_width <= spec.body_width_range[1]):
            warnings.append(
                f"Body width {body_width:.0f}mm outside expected range "
                f"{spec.body_width_range[0]}-{spec.body_width_range[1]}mm for {spec.name}"
            )
            passed = False
    else:
        # Generic guitar validation
        if body_length < 300 or body_length > 700:
            warnings.append(f"Body length {body_length:.0f}mm seems unusual for a guitar")
            passed = False

        if body_width < 200 or body_width > 500:
            warnings.append(f"Body width {body_width:.0f}mm seems unusual for a guitar")
            passed = False

    return passed, warnings


def validate_scale_before_export(
    mm_per_px: float,
    scale_factor: float,
    classified: Dict[ContourCategory, List[ContourInfo]],
    spec_name: Optional[str] = None
) -> Tuple[float, bool]:
    """
    Validate scale produces plausible instrument dimensions before export.
    If not plausible, attempts correction.

    Called BEFORE export_to_dxf().
    
    Args:
        mm_per_px: Base pixels-to-mm conversion
        scale_factor: Current scale multiplier
        contours: List of ContourInfo objects
        spec_name: Optional instrument spec name for validation
        
    Returns:
        Tuple of (corrected_scale_factor, validation_passed)
    """
    effective_mm_per_px = mm_per_px * scale_factor

    # Find body outline from classified dict (authoritative source for export)
    body_list = classified.get(ContourCategory.BODY_OUTLINE, [])
    if not body_list:
        # Fallback to largest contour across all categories
        all_contours = []
        for cat_list in classified.values():
            all_contours.extend(cat_list)
        if not all_contours:
            logger.warning("Scale validation: no contours to validate")
            return scale_factor, False
        largest = max(all_contours, key=lambda c: c.area_px)
    else:
        largest = body_list[0]

    # Use ContourInfo dimensions (already in mm) scaled by scale_factor
    # This matches what export_to_dxf will produce
    body_w_mm = largest.width_mm * scale_factor
    body_h_mm = largest.height_mm * scale_factor

    logger.info(f"Scale validation: body={body_w_mm:.0f}x{body_h_mm:.0f}mm "
                f"(ContourInfo: {largest.width_mm:.0f}x{largest.height_mm:.0f}mm, scale={scale_factor:.3f})")

    # Check against spec if available
    if spec_name and spec_name in INSTRUMENT_SPECS:
        spec = INSTRUMENT_SPECS[spec_name]
        expected_w = (spec.body_width_range[0] + spec.body_width_range[1]) / 2
        expected_h = (spec.body_length_range[0] + spec.body_length_range[1]) / 2
        
        # Use the larger dimension as length
        body_length = max(body_w_mm, body_h_mm)
        body_width = min(body_w_mm, body_h_mm)
        
        ratio_len = body_length / expected_h
        ratio_wid = body_width / expected_w

        if 0.8 < ratio_len < 1.2 and 0.8 < ratio_wid < 1.2:
            logger.info("Scale validation PASSED (within spec tolerance)")
            return scale_factor, True
        else:
            # Geometric mean distributes error evenly across both axes
            # for uniform scaling. Arithmetic mean was overcorrecting width
            # and undercorrecting height when errors were asymmetric.
            corr_len = expected_h / body_length
            corr_wid = expected_w / body_width
            correction = math.sqrt(corr_len * corr_wid)
            logger.warning(f"Scale validation FAILED for {spec_name}. "
                          f"Expected ~{expected_w:.0f}×{expected_h:.0f}mm, "
                          f"got {body_width:.0f}×{body_length:.0f}mm. "
                          f"Correction: {correction:.3f}x "
                          f"(len={corr_len:.3f}, wid={corr_wid:.3f})")
            return scale_factor * correction, False

    # Generic plausibility check (no spec)
    max_dim = max(body_w_mm, body_h_mm)
    min_dim = min(body_w_mm, body_h_mm)
    
    if 200 < max_dim < 700 and 150 < min_dim < 550:
        logger.info("Scale validation PASSED (generic plausibility)")
        return scale_factor, True

    # Too large — apply correction
    if max_dim > 700:
        correction = 500 / max_dim
        logger.warning(f"Body too large ({max_dim:.0f}mm), "
                      f"applying {correction:.3f}x correction")
        return scale_factor * correction, False

    # Too small — apply correction
    if max_dim < 200:
        correction = 400 / max_dim
        logger.warning(f"Body too small ({max_dim:.0f}mm), "
                      f"applying {correction:.3f}x correction")
        return scale_factor * correction, False

    logger.info("Scale validation PASSED (within generic bounds)")
    return scale_factor, True



# =============================================================================
# DXF Export
# =============================================================================

def export_to_dxf(
    classified: Dict[ContourCategory, List[ContourInfo]],
    output_path: str,
    image_height: int,
    mm_per_px: float,
    center_on_body: bool = True,
    simplify_tolerance: float = 0.2,
    excluded_categories: Optional[List[ContourCategory]] = None,
    max_per_category: Optional[Dict[ContourCategory, int]] = None,
    dxf_version: DxfVersion = 'R12',
    scale_factor: float = 1.0
) -> Tuple[float, float]:
    """
    Export classified contours to DXF with semantic layers.

    Args:
        classified: Dict of category -> contour list
        output_path: Output DXF path
        image_height: Source image height in pixels
        mm_per_px: Pixels to mm conversion
        center_on_body: If True, center all geometry on body outline
        simplify_tolerance: Douglas-Peucker tolerance in mm
        excluded_categories: Categories to skip
        max_per_category: Max contours per category
        dxf_version: DXF version to export
        scale_factor: Scale multiplier (from calibration, default 1.0)

    Returns:
        Tuple of (body_width_mm, body_height_mm)
    """
    if excluded_categories is None:
        excluded_categories = [
            ContourCategory.TEXT,
            ContourCategory.PAGE_BORDER,
            ContourCategory.UNKNOWN
        ]

    if max_per_category is None:
        max_per_category = {
            ContourCategory.BODY_OUTLINE: 1,
            ContourCategory.PICKGUARD: 2,
            ContourCategory.NECK_POCKET: 2,
            ContourCategory.PICKUP_ROUTE: 4,
            ContourCategory.CONTROL_CAVITY: 3,
            ContourCategory.BRIDGE_ROUTE: 2,
            ContourCategory.JACK_ROUTE: 2,
            ContourCategory.RHYTHM_CIRCUIT: 2,
            ContourCategory.SOUNDHOLE: 1,
            ContourCategory.D_HOLE: 1,
            ContourCategory.F_HOLE: 2,
            ContourCategory.ROSETTE: 1,
            ContourCategory.BRACING: 15,
            ContourCategory.SMALL_FEATURE: 50,
        }

    # Find body center for alignment
    center_x, center_y = 0.0, 0.0
    body_width, body_height = 0.0, 0.0

    if center_on_body and ContourCategory.BODY_OUTLINE in classified:
        body_list = classified[ContourCategory.BODY_OUTLINE]
        if body_list:
            body = body_list[0]  # Largest body
            pts = body.contour.reshape(-1, 2)
            xs = [p[0] * mm_per_px * scale_factor for p in pts]
            ys = [(image_height - p[1]) * mm_per_px * scale_factor for p in pts]
            center_x = (min(xs) + max(xs)) / 2
            center_y = (min(ys) + max(ys)) / 2
            body_width = max(xs) - min(xs)
            body_height = max(ys) - min(ys)
            logger.info(f"export_to_dxf: body contour has {len(pts)} pts, "
                       f"ContourInfo dims: {body.width_mm:.0f}x{body.height_mm:.0f}mm, "
                       f"computed dims: {body_width:.0f}x{body_height:.0f}mm")

    # Create DXF document
    doc = create_document(version=dxf_version)
    msp = doc.modelspace()

    # Layer colors
    layer_colors = {
        'BODY_OUTLINE': 1,      # Red
        'PICKGUARD': 2,         # Yellow
        'NECK_POCKET': 3,       # Green
        'PICKUP_ROUTE': 4,      # Cyan
        'CONTROL_CAVITY': 5,    # Blue
        'BRIDGE_ROUTE': 6,      # Magenta
        'JACK_ROUTE': 7,        # White
        'RHYTHM_CIRCUIT': 8,    # Gray
        'SOUNDHOLE': 1,         # Red
        'D_HOLE': 1,            # Red
        'F_HOLE': 1,            # Red
        'ROSETTE': 2,           # Yellow
        'BRACING': 3,           # Green
        'SMALL_FEATURE': 7,     # White
    }

    # Per-layer simplification tolerances in mm
    # Body outline needs fine detail; internal features can be coarser
    layer_tolerances = {
        ContourCategory.BODY_OUTLINE: 0.05,   # Ultra-fine for body shape (target: 500+ segments)
        ContourCategory.NECK_POCKET: 1.0,
        ContourCategory.PICKUP_ROUTE: 1.0,
        ContourCategory.CONTROL_CAVITY: 1.5,
        ContourCategory.SOUNDHOLE: 0.5,
        ContourCategory.D_HOLE: 0.5,
        ContourCategory.F_HOLE: 0.5,
        ContourCategory.ROSETTE: 0.5,
        ContourCategory.PICKGUARD: 1.0,
        ContourCategory.BRIDGE_ROUTE: 1.0,
        ContourCategory.JACK_ROUTE: 1.5,
        ContourCategory.RHYTHM_CIRCUIT: 1.5,
        ContourCategory.BRACING: 1.0,
        ContourCategory.SMALL_FEATURE: 2.0,   # Coarser for small features
    }
    default_tolerance = simplify_tolerance  # Fallback for unlisted categories

    exported_count = 0

    for category, contours in classified.items():
        if category in excluded_categories:
            continue

        layer_name = category.value.upper()
        max_count = max_per_category.get(category, 10)

        for i, info in enumerate(contours[:max_count]):
            # Convert to mm, flip Y, center
            pts = info.contour.reshape(-1, 2)
            mm_pts = []
            for px, py in pts:
                x_mm = px * mm_per_px * scale_factor - center_x
                y_mm = (image_height - py) * mm_per_px * scale_factor - center_y
                mm_pts.append([x_mm, y_mm])

            # Simplify with per-layer tolerance (absolute, in mm)
            pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
            tolerance = layer_tolerances.get(category, default_tolerance)
            simplified = cv2.approxPolyDP(pts_array, tolerance, closed=True)
            simplified = simplified.reshape(-1, 2)

            if len(simplified) < 3:
                continue

            point_tuples = [(float(x), float(y)) for x, y in simplified]

            # BODY_OUTLINE: Filter gap-bridging artifacts at LINE level
            # Write individual LINE entities, skipping any > max_segment_mm
            if category == ContourCategory.BODY_OUTLINE:
                max_segment_mm = 10.0  # No body edge should exceed 10mm
                written_count = 0
                skipped_count = 0

                for j in range(len(point_tuples)):
                    p1 = point_tuples[j]
                    p2 = point_tuples[(j + 1) % len(point_tuples)]  # Wrap for closing
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    seg_len = math.sqrt(dx*dx + dy*dy)

                    if seg_len <= max_segment_mm:
                        msp.add_line(p1, p2, dxfattribs={'layer': layer_name})
                        written_count += 1
                    else:
                        skipped_count += 1

                if skipped_count > 0:
                    logger.info(f"BODY_OUTLINE: skipped {skipped_count} gap-bridging segments > {max_segment_mm}mm, wrote {written_count}")

                exported_count += 1
                continue  # Skip normal add_polyline call

            try:
                add_polyline(msp, point_tuples, layer=layer_name, closed=True, version=dxf_version)
                exported_count += 1
            except Exception as e:
                logger.warning(f"Failed to add contour to {layer_name}: {e}")

    # Set bounds from body outline if available
    if ContourCategory.BODY_OUTLINE in classified and classified[ContourCategory.BODY_OUTLINE]:
        body = classified[ContourCategory.BODY_OUTLINE][0]
        pts = body.contour.reshape(-1, 2)
        body_pts = []
        for px, py in pts:
            x_mm = px * mm_per_px * scale_factor - center_x
            y_mm = (image_height - py) * mm_per_px * scale_factor - center_y
            body_pts.append((x_mm, y_mm))
        set_document_bounds(doc, body_pts)

    _safe_dxf_save(doc, output_path)
    logger.info(f"Exported {exported_count} contours to {output_path}")

    return body_width, body_height


def export_primitives_to_dxf(
    primitives: List[GeometricPrimitive],
    output_path: str,
    center_offset: Tuple[float, float] = (0, 0),
    dxf_version: DxfVersion = 'R12'
):
    """
    Export geometric primitives to DXF.

    For R12 format per CLAUDE.md standard (max compatibility).

    Args:
        primitives: List of detected primitives
        output_path: Output DXF path
        center_offset: (x, y) offset to apply
        dxf_version: DXF version
    """
    doc = create_document(version=dxf_version)
    msp = doc.modelspace()

    cx_off, cy_off = center_offset

    for prim in primitives:
        layer = prim.layer

        if prim.type == PrimitiveType.CIRCLE:
            # Approximate circle with polyline for R12
            if prim.center and prim.radius:
                cx, cy = prim.center
                r = prim.radius

                # Generate circle points
                n_points = max(32, int(r * 2))  # More points for larger circles
                points = []
                for i in range(n_points):
                    angle = 2 * math.pi * i / n_points
                    x = cx - cx_off + r * math.cos(angle)
                    y = cy - cy_off + r * math.sin(angle)
                    points.append((x, y))

                add_polyline(msp, points, layer=layer, closed=True, version=dxf_version)

        elif prim.type == PrimitiveType.ELLIPSE:
            # Approximate ellipse with polyline
            if prim.center and prim.axes:
                cx, cy = prim.center
                a, b = prim.axes  # major, minor
                angle_rad = math.radians(prim.angle or 0)

                n_points = max(48, int((a + b) * 2))
                points = []
                for i in range(n_points):
                    t = 2 * math.pi * i / n_points
                    # Parametric ellipse
                    x0 = a * math.cos(t)
                    y0 = b * math.sin(t)
                    # Rotate
                    x = x0 * math.cos(angle_rad) - y0 * math.sin(angle_rad)
                    y = x0 * math.sin(angle_rad) + y0 * math.cos(angle_rad)
                    # Translate
                    points.append((cx - cx_off + x, cy - cy_off + y))

                add_polyline(msp, points, layer=layer, closed=True, version=dxf_version)

        elif prim.type == PrimitiveType.ARC:
            # Approximate arc with polyline
            if prim.center and prim.radius and prim.start_angle is not None and prim.end_angle is not None:
                cx, cy = prim.center
                r = prim.radius
                start = math.radians(prim.start_angle)
                end = math.radians(prim.end_angle)

                # Handle wrap-around
                if end < start:
                    end += 2 * math.pi

                arc_span = end - start
                n_points = max(16, int(math.degrees(arc_span) / 5))

                points = []
                for i in range(n_points + 1):
                    angle = start + arc_span * i / n_points
                    x = cx - cx_off + r * math.cos(angle)
                    y = cy - cy_off + r * math.sin(angle)
                    points.append((x, y))

                add_polyline(msp, points, layer=layer, closed=False, version=dxf_version)

        elif prim.type == PrimitiveType.POLYLINE:
            if prim.points:
                offset_points = [(x - cx_off, y - cy_off) for x, y in prim.points]
                add_polyline(msp, offset_points, layer=layer, closed=False, version=dxf_version)

    _safe_dxf_save(doc, output_path)
    logger.info(f"Exported {len(primitives)} primitives to {output_path}")


# =============================================================================
# Main Extraction Pipeline
# =============================================================================

class Phase3Vectorizer:
    """
    Production-grade blueprint vectorizer with all Phase 3.5 features.
    """

    def __init__(
        self,
        dpi: int = 400,
        default_instrument: InstrumentType = InstrumentType.ELECTRIC_GUITAR,
        simplify_tolerance: float = 0.2,
        ml_model_path: Optional[str] = None,
        enable_primitives: bool = True,
        enable_scale_detection: bool = True,
        enable_feedback: bool = False,
        feedback_dir: str = ".feedback",
        enable_ocr: bool = False,
        tier: Optional[str] = None,
        tier_config_path: Optional[str] = None,
        extraction_mode: ExtractionMode = ExtractionMode.SMART,
        # Phase 3.7 additions
        enable_photo_processing: bool = True,
        enable_debug: bool = False,
        debug_output_dir: str = "debug_output",
        corrections_file: Optional[str] = None,
        use_rembg: bool = True,
        dxf_version: str = 'R12'
    ):
        """
        Initialize Phase 3.6 Vectorizer.

        Args:
            dpi: Resolution for PDF rasterization
            default_instrument: Default instrument type for classification
            simplify_tolerance: Default simplification tolerance in mm
            ml_model_path: Path to trained ML model (optional)
            enable_primitives: Enable geometric primitive detection
            enable_scale_detection: Enable auto scale detection
            enable_feedback: Enable feedback collection
            feedback_dir: Directory for feedback storage
            enable_ocr: Enable OCR dimension extraction (requires easyocr)
            tier: Processing tier ('express', 'standard', 'premium', 'batch')
            tier_config_path: Path to tier configuration file (JSON or YAML)
            extraction_mode: SMART (ML-filtered, guitar-optimized) or SIMPLE (all contours, any instrument)
        """
        # Apply tier configuration if specified
        self._tier_processor = None
        if tier:
            try:
                from config.processing_tiers import TieredProcessor
                self._tier_processor = TieredProcessor(
                    tier=tier,
                    config_path=tier_config_path
                )
                # Override parameters from tier config
                tier_kwargs = self._tier_processor.get_vectorizer_kwargs()
                enable_primitives = tier_kwargs.get('enable_primitives', enable_primitives)
                enable_scale_detection = tier_kwargs.get('enable_scale_detection', enable_scale_detection)
                enable_ocr = tier_kwargs.get('enable_ocr', enable_ocr)
                simplify_tolerance = tier_kwargs.get('simplify_tolerance', simplify_tolerance)
                logger.info(f"Using {tier} tier configuration")
            except ImportError:
                logger.warning("Tier configuration not available, using defaults")

        self.dpi = dpi
        self.mm_per_px = 25.4 / dpi
        self.enable_ocr = enable_ocr
        self._ocr_extractor = None  # Lazy load
        self.default_instrument = default_instrument
        self.simplify_tolerance = simplify_tolerance
        self.dxf_version = dxf_version

        # Phase 3.6 components
        self.color_filter = ColorFilter()
        self.ml_classifier = MLContourClassifier(ml_model_path) if ml_model_path else None
        self.enable_primitives = enable_primitives
        self.enable_scale_detection = enable_scale_detection

        self.feedback = FeedbackSystem(feedback_dir) if enable_feedback else None
        self.extraction_mode = extraction_mode

        # Grid zone classifier for body outline re-ranking
        self.grid_classifier = None
        if GRID_CLASSIFIER_AVAILABLE:
            self.grid_classifier = GridZoneClassifier(ELECTRIC_GUITAR_GRID)
            logger.info("GridZoneClassifier loaded for body outline re-ranking")

        logger.info(f"Phase 3.6 Vectorizer initialized (ML: {self.ml_classifier is not None}, Grid: {self.grid_classifier is not None}, Mode: {extraction_mode.value})")

        # Phase 3.7 enhancement components (optional)
        self.photo_processor = None
        self.adaptive_extractor = None
        self.scale_calibrator = None
        self.contour_completer = None
        self.debug_visualizer = None
        self.manual_override = None
        self.enhanced_validator = None
        self.enable_photo_processing = enable_photo_processing

        if ENHANCEMENTS_AVAILABLE:
            if enable_photo_processing:
                self.photo_processor = GuitarPhotoProcessor(use_rembg=use_rembg)
            self.adaptive_extractor = AdaptiveLineExtractor()
            self.scale_calibrator = ScaleCalibrator(mm_per_px_default=self.mm_per_px)
            self.contour_completer = ContourCompleter()
            self.debug_visualizer = DebugVisualizer(debug_output_dir, enabled=enable_debug)
            if corrections_file:
                self.manual_override = ManualOverride(corrections_file)
            self.enhanced_validator = ValidationReport(INSTRUMENT_SPECS)
            logger.info(f"Phase 3.7 enhancements loaded (Photo: {enable_photo_processing}, Debug: {enable_debug})")

    def _raw_extract(
        self,
        image: np.ndarray,
        output_path: str,
        source_path: str
    ) -> 'ExtractionResult':
        """
        Raw extraction — March 2026 recipe.
        CHAIN_APPROX_NONE + no classification + R12 LINE entities + CONTOURS layer.
        Pixel coordinates only — no scale conversion.
        """
        import time
        start_time = time.time()

        # 1. Dark line mask (same as guitar mode)
        mask = extract_dark_lines(image, threshold=120)

        # 2. ALL contours — every boundary pixel
        contours, _ = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
        )

        logger.info(f"Raw extraction: {len(contours)} contours from mask")

        # 3. No classification. No filtering. No approxPolyDP.
        # Build LINE entities per contour (R12 format)
        doc = create_document(version='R12')
        msp = doc.modelspace()

        total_segments = 0
        for contour in contours:
            pts = contour.reshape(-1, 2)
            if len(pts) < 2:
                continue
            # Pixel coordinates — Y inverted for CAD convention
            points = [(float(p[0]), float(image.shape[0] - p[1])) for p in pts]
            add_polyline(msp, points, layer='CONTOURS', closed=True, version='R12')
            total_segments += len(points)

        _safe_dxf_save(doc, output_path)

        elapsed = time.time() - start_time
        logger.info(f"Raw DXF written: {output_path} ({total_segments} segments, {elapsed:.1f}s)")

        # Return minimal ExtractionResult
        return ExtractionResult(
            source_path=source_path,
            output_dxf=output_path,
            output_svg=None,
            instrument_type=InstrumentType.ELECTRIC_GUITAR,  # Default for raw mode
            contours_by_category={'CONTOURS': []},  # Raw mode has no classification
            primitives=[],
            dimensions_mm=(0.0, 0.0),  # Pixel space — not scaled
            validation_passed=False,
            scale_factor=1.0,
            scale_source='raw_mode',
            warnings=['Raw mode: pixel coordinates, no scale applied'],
            processing_time_ms=elapsed * 1000
        )

    def _run_analyzer(
        self,
        file_bytes: bytes,
        filename: str,
        dpi: int
    ) -> Optional[float]:
        """
        Run BlueprintAnalyzer vision pre-pass on blueprint image.
        Returns mm_per_px if scale detected, None if not.
        Falls back gracefully — never raises.
        """
        if not ANALYZER_AVAILABLE:
            logger.debug("BlueprintAnalyzer not available — using DPI fallback")
            return None

        try:
            import asyncio
            analyzer = BlueprintAnalyzer()
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                analyzer.analyze_from_bytes(file_bytes, filename)
            )
            loop.close()

            # Extract scale from result
            scale_str = result.get('scale', '')
            confidence = result.get('scale_confidence', 'low')

            if confidence == 'low' or not scale_str:
                logger.info(f"Analyzer: low confidence scale — using DPI fallback")
                return None

            # Parse scale string to mm_per_px
            mm_per_px = self._parse_scale_to_mm_per_px(scale_str, dpi)

            if mm_per_px:
                logger.info(f"Analyzer: scale={scale_str} → {mm_per_px:.4f} mm/px")
                return mm_per_px

            # Try dimensions directly if scale string unparseable
            dimensions = result.get('dimensions', [])
            for dim in dimensions:
                if dim.get('confidence') in ('high', 'medium'):
                    logger.info(f"Analyzer: dimension detected: {dim}")
                    break

            return None

        except Exception as e:
            logger.warning(f"BlueprintAnalyzer failed: {e} — using DPI fallback")
            return None

    def _parse_scale_to_mm_per_px(
        self,
        scale_str: str,
        dpi: int
    ) -> Optional[float]:
        """
        Convert scale notation to mm_per_px.
        Base mm_per_px at given DPI: 25.4 / dpi

        Scale "1:1" → multiply by 1.0
        Scale "1:2" → multiply by 2.0
        Scale "1:4" → multiply by 4.0
        Scale "full size" → multiply by 1.0
        Scale "half size" → multiply by 2.0
        """
        base = 25.4 / dpi
        s = scale_str.lower().strip()

        if 'full' in s or s in ('1:1', '1/1'):
            return base * 1.0
        if 'half' in s or s == '1:2':
            return base * 2.0
        if '1:4' in s or 'quarter' in s:
            return base * 4.0
        if '1:3' in s:
            return base * 3.0

        # Try ratio format N:M
        import re
        m = re.search(r'(\d+)\s*:\s*(\d+)', s)
        if m:
            n, d = int(m.group(1)), int(m.group(2))
            if n > 0:
                return base * (d / n)

        return None

    def _compute_scale_from_spec(
        self,
        image: np.ndarray,
        spec_name: str
    ) -> Optional[float]:
        """
        Compute mm_per_px from known instrument spec dimensions.

        When BlueprintAnalyzer is unavailable (no ANTHROPIC_API_KEY), use
        the target instrument spec dimensions to calibrate scale by finding
        the largest contour and assuming it's the body.

        Args:
            image: Input image (grayscale or BGR)
            spec_name: Key into INSTRUMENT_SPECS

        Returns:
            mm_per_px if successful, None if spec not found or no body detected
        """
        if spec_name not in INSTRUMENT_SPECS:
            logger.debug(f"Spec '{spec_name}' not in INSTRUMENT_SPECS — cannot calibrate")
            return None

        spec = INSTRUMENT_SPECS[spec_name]

        # Expected body dimensions (use midpoint of ranges)
        expected_length = (spec.body_length_range[0] + spec.body_length_range[1]) / 2
        expected_width = (spec.body_width_range[0] + spec.body_width_range[1]) / 2

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Simple threshold to find contours
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            logger.debug("No contours found — cannot calibrate from spec")
            return None

        # Find largest contour (likely the body)
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)

        # Minimum size gate — body should be substantial portion of image
        img_h, img_w = image.shape[:2]
        area_ratio = (w * h) / (img_w * img_h)
        if area_ratio < 0.05:
            logger.debug(f"Largest contour too small ({area_ratio:.1%} of image) — cannot calibrate")
            return None

        # Compute mm_per_px using the larger dimension
        # Body length (height) is typically the larger dimension
        if h > w:
            # Vertical orientation — h is body length
            mm_per_px = expected_length / h
            computed_width = w * mm_per_px
        else:
            # Horizontal orientation — w is body length
            mm_per_px = expected_length / w
            computed_width = h * mm_per_px

        # Sanity check — mm_per_px should be reasonable (0.01 to 1.0)
        if not (0.01 < mm_per_px < 1.0):
            logger.warning(f"Computed mm_per_px={mm_per_px:.4f} out of range — rejecting")
            return None

        # Cross-check: computed width should be close to expected width
        width_error = abs(computed_width - expected_width) / expected_width
        if width_error > 0.3:  # >30% error suggests wrong contour
            logger.warning(
                f"Width cross-check failed: computed {computed_width:.0f}mm vs "
                f"expected {expected_width:.0f}mm ({width_error:.0%} error)"
            )
            # Still return the value but log the warning

        logger.info(
            f"Scale calibrated from spec '{spec_name}': mm_per_px={mm_per_px:.4f} "
            f"(bbox={w}x{h}px → {expected_length:.0f}x{computed_width:.0f}mm)"
        )
        return mm_per_px

    def _detect_instrument_type(
        self,
        image: np.ndarray,
        contours: list,
        user_hint: str = None
    ) -> InstrumentType:
        """
        Detect instrument family from image statistics and contour geometry.
        Returns: InstrumentType enum value

        Phase 5C improvements:
        1. Infer type from spec_name when provided
        2. Add pickup route detection as electric signal
        3. Use aspect ratio only as fallback when no other signals present
        """
        # Check for explicit type hints first
        if user_hint:
            hint_lower = user_hint.lower()
            if hint_lower in ('electric', 'e'):
                return InstrumentType.ELECTRIC_GUITAR
            elif hint_lower in ('acoustic', 'a'):
                return InstrumentType.ACOUSTIC_GUITAR
            elif hint_lower == 'bass':
                return InstrumentType.BASS
            elif hint_lower == 'archtop':
                return InstrumentType.ARCHTOP
            elif hint_lower == 'ukulele':
                return InstrumentType.UKULELE
            elif hint_lower == 'mandolin':
                return InstrumentType.MANDOLIN

            # Phase 5C: Infer type from spec_name
            # Electric specs: stratocaster, telecaster, les_paul, sg, explorer, flying_v, etc.
            # Acoustic specs: dreadnought, orchestra_model, classical, jumbo, selmer
            electric_specs = {
                'stratocaster', 'telecaster', 'jazzmaster', 'jaguar',
                'les_paul', 'sg', 'es335', 'explorer', 'flying_v',
                'smart_guitar', 'klein'
            }
            acoustic_specs = {
                'dreadnought', 'orchestra_model', 'classical', 'jumbo', 'selmer'
            }
            ukulele_specs = {'ukulele_soprano', 'ukulele_concert', 'ukulele_tenor'}

            if hint_lower in electric_specs:
                logger.info(f"Instrument type inferred from spec: electric ({hint_lower})")
                return InstrumentType.ELECTRIC_GUITAR
            elif hint_lower in acoustic_specs:
                logger.info(f"Instrument type inferred from spec: acoustic ({hint_lower})")
                return InstrumentType.ACOUSTIC_GUITAR
            elif hint_lower in ukulele_specs:
                logger.info(f"Instrument type inferred from spec: ukulele ({hint_lower})")
                return InstrumentType.UKULELE

        if not contours:
            return InstrumentType.UNKNOWN

        # Analyze contours for type signals
        areas = [cv2.contourArea(c) for c in contours]
        if not areas:
            return InstrumentType.UNKNOWN
        largest_idx = int(np.argmax(areas))
        largest = contours[largest_idx]

        x, y, w, h = cv2.boundingRect(largest)
        aspect = max(w, h) / max(1, min(w, h))

        # Signal detection
        circular_count = 0      # Soundhole/rosette signal (acoustic)
        rectangular_count = 0   # Pickup route signal (electric)

        for c in contours:
            area = cv2.contourArea(c)
            if area < 100:
                continue
            perimeter = cv2.arcLength(c, True)
            if perimeter == 0:
                continue

            circularity = 4 * np.pi * area / (perimeter ** 2)
            cx, cy, cw, ch = cv2.boundingRect(c)
            c_aspect = max(cw, ch) / max(1, min(cw, ch))

            # Circular contour = soundhole/rosette (acoustic signal)
            if circularity > 0.75:
                circular_count += 1

            # Elongated rectangular contour = pickup route (electric signal)
            # Pickup routes: ~70-110mm long, ~30-65mm wide, aspect 1.3-3.0
            if 1.3 < c_aspect < 3.0 and circularity < 0.6:
                # Check size relative to body (pickup should be ~10-25% of body width)
                if 0.05 < (cw * ch) / (w * h) < 0.15:
                    rectangular_count += 1

        # Decision logic with explicit signals taking priority
        # Priority 1: Soundhole/rosette detection (strong acoustic signal)
        if circular_count >= 2:
            logger.info(f"Instrument detection: acoustic (circular_count={circular_count})")
            return InstrumentType.ACOUSTIC_GUITAR

        # Priority 2: Pickup route detection (strong electric signal)
        if rectangular_count >= 1:
            logger.info(f"Instrument detection: electric (rectangular_count={rectangular_count})")
            return InstrumentType.ELECTRIC_GUITAR

        # Priority 3: Single circular contour with no rectangular = likely acoustic
        if circular_count == 1 and rectangular_count == 0:
            logger.info(f"Instrument detection: acoustic (single soundhole, no pickups)")
            return InstrumentType.ACOUSTIC_GUITAR

        # Priority 4: Aspect ratio fallback (ONLY when no other signals)
        # Note: This was causing Les Paul misclassification, now it's a low-priority fallback
        if aspect > 1.8 and circular_count == 0 and rectangular_count == 0:
            # Very tall body with no features = likely acoustic
            logger.info(f"Instrument detection: acoustic (aspect={aspect:.2f}, no features detected)")
            return InstrumentType.ACOUSTIC_GUITAR
        if aspect < 1.1:
            logger.info(f"Instrument detection: electric (aspect={aspect:.2f})")
            return InstrumentType.ELECTRIC_GUITAR

        logger.info(f"Instrument detection: unknown (aspect={aspect:.2f}, circular={circular_count}, rectangular={rectangular_count})")
        return InstrumentType.UNKNOWN  # ambiguous — conservative


    @classmethod
    def from_tier(
        cls,
        tier: str,
        config_path: Optional[str] = None,
        **kwargs
    ) -> 'Phase3Vectorizer':
        """
        Create a vectorizer configured for a specific processing tier.

        Args:
            tier: Processing tier ('express', 'standard', 'premium', 'batch')
            config_path: Optional path to configuration file
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured Phase3Vectorizer instance

        Example:
            # Quick preview extraction
            vectorizer = Phase3Vectorizer.from_tier('express')

            # Production quality with all features
            vectorizer = Phase3Vectorizer.from_tier('premium')

            # With custom config
            vectorizer = Phase3Vectorizer.from_tier(
                'standard',
                config_path='config/shop_config.yaml'
            )
        """
        return cls(tier=tier, tier_config_path=config_path, **kwargs)

    @classmethod
    def for_task(cls, task_type: str, **kwargs) -> 'Phase3Vectorizer':
        """
        Create a vectorizer configured for a specific task type.

        Args:
            task_type: Task type ('preview', 'daily', 'production', 'archive')
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured Phase3Vectorizer instance

        Example:
            # For quick preview
            vectorizer = Phase3Vectorizer.for_task('preview')

            # For final production output
            vectorizer = Phase3Vectorizer.for_task('production')
        """
        try:
            from config.processing_tiers import get_tier_for_task
            tier = get_tier_for_task(task_type)
            return cls(tier=tier.value, **kwargs)
        except ImportError:
            logger.warning("Tier configuration not available, using defaults")
            return cls(**kwargs)

    def extract(
        self,
        source_path: str,
        output_path: Optional[str] = None,
        page_num: int = 0,
        instrument_type: Optional[InstrumentType] = None,
        dual_pass: bool = True,
        validate: bool = True,
        spec_name: Optional[str] = None,
        body_gap_close: int = 7,
        detail_gap_close: int = 0,
        export_svg: bool = False,
        use_ml: bool = True,
        detect_primitives: bool = True,
        extraction_mode: Optional[ExtractionMode] = None,
        simple_min_area: int = 50,
        # Phase 3.7 additions
        user_dimension_mm: Optional[float] = None,
        user_dimension_px: Optional[float] = None,
        image_dpi: Optional[float] = None,
        correct_perspective: bool = True,
        assembly_gap_px: int = 50,
        generate_debug_report: bool = False,
        cam_ready: bool = False,
        dark_background: Optional[bool] = None,
        # Raw mode (March 2026 restoration)
        raw_output: bool = False
    ) -> ExtractionResult:
        """
        Extract geometry from a blueprint.

        Args:
            source_path: Path to PDF or image
            output_path: Output DXF path (auto-generated if None)
            page_num: Page number for PDFs
            instrument_type: Instrument type (uses default if None)
            dual_pass: Use dual-pass extraction
            validate: Validate dimensions against known specs
            spec_name: Specific instrument spec to validate against
            body_gap_close: Gap closing for body extraction
            detail_gap_close: Gap closing for detail extraction
            export_svg: Also export SVG
            use_ml: Use ML classification if available
            detect_primitives: Detect geometric primitives
            extraction_mode: Override instance extraction mode (SMART or SIMPLE)
            simple_min_area: Minimum contour area in pixels for SIMPLE mode
            user_dimension_mm: Known dimension in mm for scale calibration
            user_dimension_px: Corresponding dimension in pixels
            image_dpi: Known image DPI for scale calibration
            correct_perspective: Apply perspective correction (photos)
            assembly_gap_px: Gap tolerance for assembly contour joining
            generate_debug_report: Generate debug visualization report
            cam_ready: Export CAM-ready DXF (R12, LINE segments via dxf_compat)
            dark_background: Dark background handling (None=auto-detect, True=force invert, False=off)

        Returns:
            ExtractionResult with paths and statistics
        """
        import time
        start_time = time.time()

        source = Path(source_path)
        if output_path is None:
            output_path = str(source.with_suffix('.dxf'))

        instrument = instrument_type or self.default_instrument
        mode = extraction_mode or self.extraction_mode

        logger.info(f"Phase 3.5 extraction: {source.name}")
        logger.info(f"  Mode: {mode.value}")
        logger.info(f"  Instrument: {instrument.value}")
        logger.info(f"  Dual-pass: {dual_pass}")

        # Phase 3: BlueprintAnalyzer scale pre-pass (before image load)
        # Read raw bytes for analyzer
        scale_source = 'dpi_fallback'
        try:
            with open(source_path, 'rb') as f:
                file_bytes = f.read()
            analyzer_mm_per_px = self._run_analyzer(
                file_bytes,
                Path(source_path).name,
                self.dpi
            )
            if analyzer_mm_per_px is not None:
                self.mm_per_px = analyzer_mm_per_px
                scale_source = 'analyzer_vision'
                logger.info(f"Scale locked by BlueprintAnalyzer: {self.mm_per_px:.4f} mm/px")
            # else: mm_per_px remains at DPI-based default
        except Exception as e:
            logger.warning(f"Analyzer pre-pass failed: {e} — using DPI fallback")

        # Load image (with caching)
        image = load_image(source_path, page_num, self.dpi, use_cache=True)
        height, width = image.shape[:2]

        # Phase 5B: Spec-based scale fallback when analyzer unavailable
        # If BlueprintAnalyzer failed (no API key) but spec_name is provided,
        # use known instrument dimensions to calibrate scale from body contour
        if scale_source == 'dpi_fallback' and spec_name:
            spec_mm_per_px = self._compute_scale_from_spec(image, spec_name)
            if spec_mm_per_px is not None:
                self.mm_per_px = spec_mm_per_px
                scale_source = 'spec_fallback'

        img_width_mm = width * self.mm_per_px
        img_height_mm = height * self.mm_per_px

        # Raw mode — March 2026 recipe: pixel coords, no classification, R12 LINE entities
        if raw_output:
            logger.info("Raw extraction mode enabled")
            return self._raw_extract(image, output_path, source_path)

        # Dark background detection and inversion
        # Auto-detect unless explicitly set by caller
        image_inverted = False
        if dark_background is None:
            dark_bg_detected = detect_dark_background(image)
        else:
            dark_bg_detected = dark_background

        if dark_bg_detected:
            image = cv2.bitwise_not(image)
            image_inverted = True
            logger.info("  Dark background detected — image inverted to light background")

        # Phase 3.7: Input classification + photo pre-processing
        detected_input_type = "unknown"
        perspective_corrected = False
        bg_method_used = "none"
        if ENHANCEMENTS_AVAILABLE:
            detected_input_type = classify_input_type(image).value
            logger.info(f"  Input type: {detected_input_type}")

            if detected_input_type == InputType.PHOTO.value and self.photo_processor:
                photo_result = self.photo_processor.preprocess_for_extraction(image)
                if photo_result is not None:
                    processed_img, photo_meta = photo_result
                    image = processed_img
                    height, width = image.shape[:2]
                    img_width_mm = width * self.mm_per_px
                    img_height_mm = height * self.mm_per_px
                    perspective_corrected = photo_meta.get('perspective_corrected', False)
                    bg_method_used = photo_meta.get('bg_method', 'auto')
                    logger.info(f"  Photo pre-processed (perspective: {perspective_corrected}, bg: {bg_method_used})")

        # Initialize ML classifier reference (may be None in SIMPLE mode)
        ml_clf = None

        # Branch on extraction mode
        if mode == ExtractionMode.SIMPLE:
            # SIMPLE mode: Extract ALL contours without ML filtering
            # Works for any instrument (cuatros, mandolins, etc.)
            classified, all_contours = self._simple_extraction(
                image, height, simple_min_area
            )
            logger.info(f"Simple extraction: {len(all_contours)} contours")
        else:
            # SMART mode: ML-based extraction optimized for guitars
            # Extract lines
            if dual_pass:
                body_mask, detail_mask = dual_pass_extraction(
                    image,
                    body_gap_close=body_gap_close,
                    detail_gap_close=detail_gap_close
                )
                combined_mask = cv2.bitwise_or(body_mask, detail_mask)
            else:
                combined_mask = extract_auto(image, gap_close=body_gap_close)

            # Phase 2: Detect instrument type from image geometry
            # Extract raw contours for type detection (before classification)
            raw_contours_for_detection, _ = cv2.findContours(
                combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Detect instrument type if not explicitly provided by user
            user_hint = spec_name  # User's spec hint (e.g., "dreadnought", "les_paul")
            if instrument_type is None and spec_name is None:
                # No user guidance — use automatic detection
                detected_type = self._detect_instrument_type(
                    image, raw_contours_for_detection, user_hint=None
                )
                instrument = detected_type
                logger.info(f"  Auto-detected instrument type: {instrument.value}")
            elif instrument_type is None and spec_name is not None:
                # User provided spec_name but not instrument_type — use spec as hint
                detected_type = self._detect_instrument_type(
                    image, raw_contours_for_detection, user_hint=spec_name
                )
                instrument = detected_type
                logger.info(f"  Instrument type from spec hint: {instrument.value}")
            # else: user provided explicit instrument_type, use that (already set at line 2989)

            # Classify with hierarchy + grid-enhanced body re-ranking
            ml_clf = self.ml_classifier if use_ml else None

            # Resolve spec-aware body thresholds
            _min_body_dim = 300.0
            _max_body_aspect = 2.0
            if spec_name and spec_name in INSTRUMENT_SPECS:
                _spec = INSTRUMENT_SPECS[spec_name]
                _min_body_dim = _spec.min_body_dim
                _max_body_aspect = _spec.max_body_aspect_ratio

            classified = extract_with_hierarchy(
                combined_mask,
                self.mm_per_px,
                img_width_mm,
                img_height_mm,
                instrument,
                ml_classifier=ml_clf,
                grid_classifier=self.grid_classifier,
                min_body_dim=_min_body_dim,
                max_body_aspect_ratio=_max_body_aspect,
                spec_name=spec_name
            )

            # Flatten contours for additional processing
            all_contours = []
            for cat_list in classified.values():
                all_contours.extend(cat_list)

        # Phase 3.7: Contour completion — fill gaps if no body found
        if self.contour_completer and not classified.get(ContourCategory.BODY_OUTLINE):
            # Extract raw contour arrays from all non-trivial categories
            raw_contours = [
                info.contour for info in all_contours
                if info.category not in (ContourCategory.TEXT, ContourCategory.PAGE_BORDER,
                                         ContourCategory.UNKNOWN, ContourCategory.SMALL_FEATURE)
            ]
            if len(raw_contours) >= 2:
                merged = self.contour_completer.complete_body_outline(
                    raw_contours, image.shape[:2]
                )
                if merged is not None and len(merged) >= 3:
                    # Wrap the recovered outline as a ContourInfo and inject into classified
                    pts = merged.reshape(-1, 2)
                    x, y, bw, bh = cv2.boundingRect(merged)
                    body_info = ContourInfo(
                        contour=merged,
                        category=ContourCategory.BODY_OUTLINE,
                        width_mm=bw * self.mm_per_px,
                        height_mm=bh * self.mm_per_px,
                        area_px=float(cv2.contourArea(merged)),
                        perimeter_px=float(cv2.arcLength(merged, True)),
                        circularity=0.0,
                        aspect_ratio=bw / max(bh, 1),
                        point_count=len(pts),
                        bbox=(x, y, bw, bh)
                    )
                    classified[ContourCategory.BODY_OUTLINE] = [body_info]
                    all_contours.append(body_info)
                    logger.info(f"Contour completion recovered body outline ({len(pts)} points)")

        # Phase 3.7: Apply manual overrides
        if self.manual_override:
            classified = self.manual_override.apply_corrections(classified)
            all_contours = []
            for cat_list in classified.values():
                all_contours.extend(cat_list)

        # Detect primitives
        primitives = []
        if detect_primitives and self.enable_primitives:
            prim_detector = PrimitiveDetector(self.mm_per_px)
            raw_contours = [c.contour for c in all_contours if c.category != ContourCategory.PAGE_BORDER]
            primitives = prim_detector.detect_all(raw_contours)
            logger.info(f"Detected {len(primitives)} geometric primitives")

        # Scale detection
        scale_factor = 1.0
        scale_source = "none"
        calibration_result = None
        if self.scale_calibrator and (user_dimension_mm or image_dpi):
            # Phase 3.7: Enhanced scale calibration
            calibration_result = self.scale_calibrator.calibrate(
                image, all_contours,
                user_mm=user_dimension_mm,
                user_px=user_dimension_px,
                spec_name=spec_name,
                image_dpi=image_dpi
            )
            scale_factor = calibration_result.mm_per_px / self.mm_per_px if calibration_result.mm_per_px > 0 else 1.0
            scale_source = calibration_result.source.value
            logger.info(f"Enhanced calibration: {scale_factor:.3f}x ({scale_source}, confidence: {calibration_result.confidence:.2f})")
        elif self.enable_scale_detection:
            scale_detector = ScaleDetector(self.mm_per_px)
            scale_factor, scale_source = scale_detector.detect_scale(all_contours, instrument)
            if scale_source != "none":
                logger.info(f"Scale detected: {scale_factor:.3f}x ({scale_source})")

        # OCR dimension extraction (Phase 3.6)
        ocr_dimensions = []
        ocr_raw_texts = []
        if self.enable_ocr:
            try:
                ocr_dimensions, ocr_raw_texts = self._extract_ocr_dimensions(image)
                logger.info(f"OCR extracted {len(ocr_dimensions)} dimensions from {len(ocr_raw_texts)} text regions")
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")

        # Scale validation gate (CLAUDE.md architecture requirement)
        scale_factor, scale_valid = validate_scale_before_export(
            self.mm_per_px,
            scale_factor,
            classified,
            spec_name=spec_name
        )
        if not scale_valid:
            logger.info(f"Scale corrected to {scale_factor:.3f}x")

        # Export to DXF
        dxf_version_to_use = getattr(self, 'dxf_version', 'R12')
        body_w, body_h = export_to_dxf(
            classified,
            output_path,
            height,
            self.mm_per_px,
            simplify_tolerance=self.simplify_tolerance,
            dxf_version=dxf_version_to_use,
            scale_factor=scale_factor
        )

        # Phase 3.7: CAM-ready DXF export (arc fitting, LWPOLYLINE)
        cam_dxf_path = None
        if cam_ready and CAM_EXPORT_AVAILABLE:
            cam_dxf_path = str(Path(output_path).with_stem(Path(output_path).stem + "_cam"))
            export_cam_ready_dxf(
                classified, cam_dxf_path, height, self.mm_per_px,
                scale_factor=scale_factor,
                simplify_tolerance=self.simplify_tolerance
            )
            logger.info(f"CAM-ready DXF exported to {cam_dxf_path}")

        # Phase 3.7: SVG export
        svg_output_path = None
        if export_svg and SVG_EXPORT_AVAILABLE:
            svg_output_path = str(Path(output_path).with_suffix('.svg'))
            export_to_svg(
                classified, svg_output_path, height, self.mm_per_px,
                scale_factor=scale_factor,
                simplify_tolerance=self.simplify_tolerance
            )
            logger.info(f"SVG exported to {svg_output_path}")

        # Export primitives if any
        if primitives:
            prim_path = str(Path(output_path).with_stem(Path(output_path).stem + "_primitives"))
            # Find center offset from body
            center_x, center_y = 0.0, 0.0
            if ContourCategory.BODY_OUTLINE in classified and classified[ContourCategory.BODY_OUTLINE]:
                body = classified[ContourCategory.BODY_OUTLINE][0]
                pts = body.contour.reshape(-1, 2)
                xs = [p[0] * self.mm_per_px for p in pts]
                ys = [(height - p[1]) * self.mm_per_px for p in pts]
                center_x = (min(xs) + max(xs)) / 2
                center_y = (min(ys) + max(ys)) / 2

            export_primitives_to_dxf(primitives, prim_path, (center_x, center_y))

        # Detect component-only sheets (no body found)
        sheet_type = "body"
        if body_w == 0 and body_h == 0:
            # Count what we actually found
            pickguard_count = len(classified.get(ContourCategory.PICKGUARD, []))
            if pickguard_count > 0:
                sheet_type = "pickguard_sheet"
                logger.info(f"Component sheet detected: {pickguard_count} pickguard(s), no body outline")
            else:
                sheet_type = "component_sheet"
                total = sum(len(v) for k, v in classified.items()
                            if k not in (ContourCategory.TEXT, ContourCategory.PAGE_BORDER,
                                         ContourCategory.UNKNOWN, ContourCategory.SMALL_FEATURE))
                logger.info(f"Component sheet detected: {total} feature(s), no body outline")

        # Validate dimensions
        warnings = []
        validation_passed = True
        enhanced_validation = None
        if self.enhanced_validator and validate and body_w > 0:
            # Phase 3.7: Enhanced validation — build a minimal result-like object
            from types import SimpleNamespace
            _partial = SimpleNamespace(
                contours_by_category={cat.value: infos for cat, infos in classified.items()},
                dimensions_mm=(body_w, body_h),
                scale_source=scale_source,
                scale_factor=scale_factor,
                instrument_type=instrument
            )
            enhanced_validation = self.enhanced_validator.validate(_partial)
            validation_passed = enhanced_validation.get("passed", True)
            warnings = enhanced_validation.get("warnings", [])
            for w in warnings:
                logger.warning(w)
        elif validate and body_w > 0:
            validation_passed, warnings = validate_dimensions(body_w, body_h, spec_name)
            for w in warnings:
                logger.warning(w)
        elif validate and sheet_type != "body":
            # Component sheets pass validation — no body to validate
            validation_passed = True

        # Phase 3.7: Debug report generation
        debug_report_path = None
        if generate_debug_report and self.debug_visualizer:
            report_title = f"Debug: {Path(source_path).stem}"
            debug_report_path = str(self.debug_visualizer.create_report(report_title))
            if debug_report_path:
                logger.info(f"Debug report: {debug_report_path}")

        # Record feedback if enabled
        if self.feedback and ml_clf:
            for info in all_contours[:50]:  # Limit feedback recording
                contour_hash = hashlib.md5(info.contour.tobytes()).hexdigest()[:12]
                features = ml_clf.extract_features(info.contour, self.mm_per_px)
                self.feedback.record_classification(
                    contour_hash,
                    info.category.value,
                    info.ml_confidence,
                    features,
                    source_path
                )

        processing_time = (time.time() - start_time) * 1000

        # Build result
        result = ExtractionResult(
            source_path=source_path,
            output_dxf=output_path,
            output_svg=svg_output_path,
            instrument_type=instrument,
            contours_by_category={cat.value: infos for cat, infos in classified.items()},
            warnings=warnings,
            validation_passed=validation_passed,
            dimensions_mm=(body_w, body_h),
            primitives=primitives,
            scale_factor=scale_factor,
            scale_source=scale_source,
            processing_time_ms=processing_time,
            ml_used=ml_clf is not None and ml_clf.using_ml,
            ocr_dimensions=ocr_dimensions,
            ocr_raw_texts=ocr_raw_texts,
            sheet_type=sheet_type,
            input_type=detected_input_type,
            calibration_result=calibration_result,
            debug_report_path=debug_report_path,
            validation_report=enhanced_validation,
            perspective_corrected=perspective_corrected,
            bg_method_used=bg_method_used,
            assembly_method="contour_completion" if self.contour_completer and not classified.get(ContourCategory.BODY_OUTLINE) else "direct",
            dark_background_inverted=image_inverted
        )

        logger.info(f"Complete: {body_w:.0f}x{body_h:.0f}mm {sheet_type} in {processing_time:.0f}ms")

        return result

    def _extract_ocr_dimensions(
        self,
        image: np.ndarray
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Extract dimension text from blueprint image using OCR.

        Args:
            image: OpenCV image (BGR)

        Returns:
            Tuple of (dimensions list, raw texts list)
        """
        # Lazy load OCR extractor
        if self._ocr_extractor is None:
            try:
                from dimension_extractor import DimensionExtractor
                self._ocr_extractor = DimensionExtractor()
            except ImportError as e:
                logger.warning(f"OCR not available: {e}")
                return [], []

        # Save image temporarily for OCR
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)

        try:
            result = self._ocr_extractor.extract_with_context(temp_path)

            dimensions = []
            for dim in result.dimensions:
                dimensions.append({
                    'raw_text': dim.raw_text,
                    'value_mm': dim.value_mm,
                    'value_inches': dim.value_inches,
                    'unit': dim.unit,
                    'confidence': dim.confidence,
                    'context': dim.context,
                    'bbox': dim.bbox
                })

            return dimensions, result.raw_texts
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def _simple_extraction(
        self,
        image: np.ndarray,
        height: int,
        min_area: int = 50
    ) -> Tuple[Dict[ContourCategory, List], List]:
        """
        Simple contour extraction without ML filtering.

        Extracts ALL contours above min_area threshold using adaptive thresholding.
        Works for any instrument type (cuatros, mandolins, etc.) that may not be
        recognized by the guitar-trained ML classifier.

        Args:
            image: OpenCV image (BGR)
            height: Image height in pixels
            min_area: Minimum contour area in pixels (default 50)

        Returns:
            Tuple of (classified dict, all_contours list)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Handle inverted images (white on black)
        if np.mean(gray) < 127:
            gray = 255 - gray

        # Adaptive threshold for clean line extraction
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            21, 10
        )

        # Find all contours
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter and simplify contours
        all_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            # Simplify the contour
            epsilon = 0.001 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

            if len(approx) < 3:
                continue

            # Calculate contour properties
            x, y, w, h = cv2.boundingRect(approx)
            perimeter = cv2.arcLength(approx, True)
            circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0

            # Create ContourInfo with UNKNOWN category (no ML classification)
            info = ContourInfo(
                contour=approx,
                category=ContourCategory.UNKNOWN,
                width_mm=w * self.mm_per_px,
                height_mm=h * self.mm_per_px,
                area_px=area,
                perimeter_px=perimeter,
                circularity=circularity,
                aspect_ratio=w / h if h > 0 else 1.0,
                point_count=len(approx),
                bbox=(x, y, w, h),
                hierarchy_level=0,
                ml_confidence=0.0
            )
            all_contours.append(info)

        # Group all under UNKNOWN category for DXF export
        classified = {ContourCategory.UNKNOWN: all_contours}

        return classified, all_contours

    def batch_extract(
        self,
        source_paths: List[str],
        output_dir: str,
        **kwargs
    ) -> List[ExtractionResult]:
        """
        Batch process multiple blueprints.

        Args:
            source_paths: List of PDF/image paths
            output_dir: Directory for output files
            **kwargs: Arguments passed to extract()

        Returns:
            List of ExtractionResult
        """
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        results = []

        for i, source in enumerate(source_paths):
            source_path = Path(source)
            output_path = output_dir_path / f"{source_path.stem}.dxf"

            logger.info(f"\n[{i+1}/{len(source_paths)}] Processing: {source_path.name}")

            try:
                result = self.extract(
                    str(source_path),
                    str(output_path),
                    **kwargs
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {source_path.name}: {e}")
                results.append(ExtractionResult(
                    source_path=str(source_path),
                    output_dxf="",
                    output_svg=None,
                    instrument_type=self.default_instrument,
                    contours_by_category={},
                    warnings=[str(e)],
                    validation_passed=False
                ))

        # Summary
        success = sum(1 for r in results if r.output_dxf)
        total_time = sum(r.processing_time_ms for r in results)
        logger.info(f"\nBatch complete: {success}/{len(results)} successful in {total_time:.0f}ms")

        return results


# =============================================================================
# Convenience Functions
# =============================================================================

def extract_guitar_blueprint(
    source_path: str,
    output_dir: str = ".",
    page_num: int = 0,
    instrument_type: str = 'electric',
    dpi: int = 400,
    dual_pass: bool = True,
    body_gap_close: int = 7,
    detail_gap_close: int = 0,
    simplify_tolerance: float = 0.2,
    validate: bool = True,
    spec_name: Optional[str] = None,
    use_ml: bool = True,
    detect_primitives: bool = True,
    ml_model_path: Optional[str] = None,
    dxf_version: str = 'R12',
    raw_output: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for extracting guitar blueprints.

    This is the recommended entry point for single-file extraction.

    Args:
        source_path: Path to PDF or image
        output_dir: Output directory
        page_num: Page number for PDFs
        instrument_type: 'electric', 'acoustic', 'archtop', 'bass', etc.
        dpi: Resolution for PDF rasterization
        dual_pass: Use dual-pass extraction (recommended)
        body_gap_close: Gap closing kernel for body (0=disabled, 7=recommended)
        detail_gap_close: Gap closing for details (0=disabled)
        simplify_tolerance: Contour simplification in mm
        validate: Validate dimensions against known specs
        spec_name: Specific instrument spec (e.g., 'jazzmaster', 'les_paul')
        use_ml: Use ML classification if available
        detect_primitives: Detect geometric primitives

    Returns:
        Dict with paths and statistics

    Example:
        >>> result = extract_guitar_blueprint(
        ...     'Fender-Jazzmaster-Body.pdf',
        ...     output_dir='./output',
        ...     instrument_type='electric',
        ...     spec_name='jazzmaster'
        ... )
        >>> print(f"DXF: {result['dxf']}")
        >>> print(f"Body size: {result['body_size_mm']}")
    """
    # Map string to enum
    type_map = {
        'electric': InstrumentType.ELECTRIC_GUITAR,
        'acoustic': InstrumentType.ACOUSTIC_GUITAR,
        'archtop': InstrumentType.ARCHTOP,
        'bass': InstrumentType.BASS,
        'ukulele': InstrumentType.UKULELE,
        'mandolin': InstrumentType.MANDOLIN,
    }
    inst_type = type_map.get(instrument_type.lower(), InstrumentType.ELECTRIC_GUITAR)

    # Generate output path
    source = Path(source_path)
    output_path = Path(output_dir) / f"{source.stem}_phase3.dxf"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create vectorizer and extract
    vectorizer = Phase3Vectorizer(
        dpi=dpi,
        default_instrument=inst_type,
        simplify_tolerance=simplify_tolerance,
        enable_primitives=detect_primitives,
        ml_model_path=ml_model_path,
        dxf_version=dxf_version
    )

    result = vectorizer.extract(
        source_path,
        str(output_path),
        page_num=page_num,
        instrument_type=inst_type,  # Phase 5C: Pass explicit type to prevent auto-detection override
        dual_pass=dual_pass,
        validate=validate,
        spec_name=spec_name,
        body_gap_close=body_gap_close,
        detail_gap_close=detail_gap_close,
        use_ml=use_ml,
        detect_primitives=detect_primitives,
        raw_output=raw_output
    )

    return result.summary()


def batch_process_archive(
    archive_dir: str,
    output_dir: str,
    file_pattern: str = "*.pdf",
    instrument_type: str = 'electric',
    **kwargs
) -> Dict[str, Any]:
    """
    Batch process an archive of blueprint files.

    Args:
        archive_dir: Directory containing PDF/image files
        output_dir: Output directory for DXF files
        file_pattern: Glob pattern for files (e.g., "*.pdf", "Fender*.pdf")
        instrument_type: Default instrument type
        **kwargs: Additional arguments for extraction

    Returns:
        Summary dict with success/failure counts

    Example:
        >>> results = batch_process_archive(
        ...     'ltb-express/Lutherier Project/Guitar Plans',
        ...     './output/guitar_plans',
        ...     file_pattern='Fender*.pdf',
        ...     instrument_type='electric'
        ... )
        >>> print(f"Processed: {results['success']}/{results['total']}")
    """
    archive_path = Path(archive_dir)
    files = list(archive_path.glob(file_pattern))

    if not files:
        logger.warning(f"No files matching '{file_pattern}' in {archive_dir}")
        return {"total": 0, "success": 0, "failed": 0, "files": []}

    logger.info(f"Found {len(files)} files to process")

    # Map string to enum
    type_map = {
        'electric': InstrumentType.ELECTRIC_GUITAR,
        'acoustic': InstrumentType.ACOUSTIC_GUITAR,
        'archtop': InstrumentType.ARCHTOP,
        'bass': InstrumentType.BASS,
    }
    inst_type = type_map.get(instrument_type.lower(), InstrumentType.ELECTRIC_GUITAR)

    vectorizer = Phase3Vectorizer(default_instrument=inst_type)
    results = vectorizer.batch_extract([str(f) for f in files], output_dir, **kwargs)

    success = sum(1 for r in results if r.output_dxf and r.validation_passed)
    failed = len(results) - success

    return {
        "total": len(results),
        "success": success,
        "failed": failed,
        "files": [r.summary() for r in results]
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 3.5 Blueprint Vectorizer - Extract guitar geometry from PDFs"
    )
    parser.add_argument("source", help="PDF or image file to process")
    parser.add_argument("-o", "--output", help="Output directory", default=".")
    parser.add_argument("-p", "--page", type=int, default=0, help="PDF page number")
    parser.add_argument("-t", "--type", default="electric",
                        choices=["electric", "acoustic", "archtop", "bass"],
                        help="Instrument type")
    parser.add_argument("-s", "--spec", help="Instrument spec for validation")
    parser.add_argument("--dpi", type=int, default=400, help="PDF rasterization DPI")
    parser.add_argument("--no-dual-pass", action="store_true",
                        help="Disable dual-pass extraction")
    parser.add_argument("--gap-close", type=int, default=7,
                        help="Gap closing kernel size (0=disabled)")
    parser.add_argument("--no-ml", action="store_true", help="Disable ML classification")
    parser.add_argument("--ml-model", help="Path to trained ML model (.joblib)")
    parser.add_argument("--no-primitives", action="store_true", help="Disable primitive detection")
    parser.add_argument("--dxf-version", default="R12",
                        choices=["R12", "R13", "R14", "R2000", "R2004", "R2007", "R2010"],
                        help="DXF output version (default R12 for CAM compatibility)")
    parser.add_argument("--raw", action="store_true",
                        help="Raw extraction: pixel coords, no classification, R12 LINEs, CONTOURS layer")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Run extraction
    result = extract_guitar_blueprint(
        args.source,
        output_dir=args.output,
        page_num=args.page,
        instrument_type=args.type,
        dpi=args.dpi,
        dual_pass=not args.no_dual_pass,
        body_gap_close=args.gap_close,
        spec_name=args.spec,
        use_ml=not args.no_ml,
        detect_primitives=not args.no_primitives,
        ml_model_path=args.ml_model,
        dxf_version=args.dxf_version,
        raw_output=args.raw
    )

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"DXF: {result['dxf']}")
    print(f"Body: {result['body_size_mm'][0]:.0f}x{result['body_size_mm'][1]:.0f}mm")
    print(f"Validation: {'PASSED' if result['validation_passed'] else 'FAILED'}")
    print(f"Processing time: {result['processing_time_ms']:.0f}ms")

    if result['scale_source'] != 'none':
        print(f"Scale: {result['scale_factor']:.3f}x ({result['scale_source']})")

    if result['primitives_count'] > 0:
        print(f"Primitives detected: {result['primitives_count']}")

    if result['warnings']:
        print("\nWarnings:")
        for w in result['warnings']:
            print(f"  - {w}")

    print("\nFeatures extracted:")
    for feat, count in result['features'].items():
        if count > 0 and feat not in ('text', 'page_border', 'unknown'):
            print(f"  - {feat}: {count}")


if __name__ == "__main__":
    main()
