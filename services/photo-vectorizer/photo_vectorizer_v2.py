"""
Photo Vectorizer v2.0 — Standalone Photographic Instrument Outline Extractor
=============================================================================

Converts photographs of guitars/instruments into clean SVG and DXF vector outlines.
Designed for beginners and hobbyists who have a concept photo but not CAD drawings.

Pipeline:
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

Author: The Production Shop
Version: 2.0.0
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
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from xml.etree.ElementTree import Element, SubElement, ElementTree

import cv2
import numpy as np

# ── Optional deps (graceful fallback) ──────────────────────────────────────────
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

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
    debug_images: Dict[str, str] = field(default_factory=dict)

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
        }


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
    "smart_guitar": {"body": (500, 370), "features": {
        "pickup_route": [(85.0, 35.0)], "neck_pocket": (56.0, 76.0),
        "bridge_route": (100.0, 40.0), "control_cavity": (120.0, 80.0),
    }},
    "reference_objects": {
        "us_quarter": (24.26, 24.26), "credit_card": (85.6, 53.98),
        "business_card": (88.9, 50.8),
    },
}


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
        result_bytes = rembg_remove(buf.read())
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
# Stage 5 — Edge Detection (Multi-method fusion)
# =============================================================================

class PhotoEdgeDetector:
    """Fuses Canny, Sobel, and Laplacian edges for robust outline extraction."""

    def detect(self, fg_image: np.ndarray, alpha_mask: np.ndarray,
               canny_sigma: float = 0.33, close_kernel: int = 5) -> np.ndarray:
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

        # Close gaps
        if close_kernel > 0:
            k = np.ones((close_kernel, close_kernel), np.uint8)
            combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k, iterations=2)

        # Light cleanup
        k_small = np.ones((2, 2), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_small)

        logger.info(f"Edge detection: {cv2.countNonZero(combined)} edge pixels")
        return combined


# =============================================================================
# Stage 6 — Reference Object Detection
# =============================================================================

class ReferenceObjectDetector:
    def __init__(self):
        self.specs = INSTRUMENT_SPECS.get("reference_objects", {})

    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        detections = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Coin detection via Hough circles
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
            param1=50, param2=30, minRadius=20, maxRadius=200)
        if circles is not None:
            for x, y, r in np.round(circles[0]).astype(int):
                if x - r < 0 or y - r < 0:
                    continue
                for name, (diam_mm, _) in self.specs.items():
                    if "quarter" in name or "card" not in name:
                        detections.append({
                            "name": name, "type": "coin",
                            "diameter_px": 2 * r, "confidence": 0.5,
                        })
                        break

        # Card detection via rectangles
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 10000:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = max(w, h) / max(1, min(w, h))
                for card_name, (wm, hm) in [("credit_card", (85.6, 53.98))]:
                    expected = max(wm, hm) / min(wm, hm)
                    if abs(aspect - expected) / expected < 0.2:
                        detections.append({
                            "name": card_name, "type": "card",
                            "width_px": w, "height_px": h, "confidence": 0.7,
                        })
                        break
        return detections


# =============================================================================
# Stage 7 — Scale Calibration
# =============================================================================

class ScaleCalibrator:
    def __init__(self, default_dpi: float = 300.0):
        self.default_dpi = default_dpi
        self.ref_detector = ReferenceObjectDetector()

    def calibrate(self, image: np.ndarray,
                  known_mm: Optional[float] = None,
                  known_px: Optional[float] = None,
                  spec_name: Optional[str] = None,
                  image_dpi: Optional[float] = None,
                  unit: Unit = Unit.MM) -> CalibrationResult:

        # Priority 1: User dimension
        if known_mm and known_px and known_px > 0:
            if unit == Unit.INCH:
                known_mm = known_mm * 25.4
            elif unit == Unit.CM:
                known_mm = known_mm * 10
            return CalibrationResult(
                mm_per_px=known_mm / known_px, source=ScaleSource.USER_DIMENSION,
                confidence=1.0, message=f"User: {known_mm:.1f}mm / {known_px:.1f}px")

        # Priority 2: Reference objects
        refs = self.ref_detector.detect(image)
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

        # Priority 3: EXIF DPI
        if image_dpi and image_dpi > 0:
            return CalibrationResult(
                mm_per_px=25.4 / image_dpi, source=ScaleSource.EXIF_DPI,
                confidence=0.7, message=f"EXIF: {image_dpi:.0f} DPI")

        # Priority 4: Instrument spec (estimate from body)
        if spec_name and spec_name in INSTRUMENT_SPECS:
            body_h_mm = INSTRUMENT_SPECS[spec_name]["body"][0]
            return CalibrationResult(
                mm_per_px=0.0, source=ScaleSource.INSTRUMENT_SPEC,
                confidence=0.6,
                message=f"Spec: {spec_name} (body ~{body_h_mm}mm, needs contour match)",
                references=[{"spec": spec_name, "body_h_mm": body_h_mm}])

        # Priority 5: Assumed
        return CalibrationResult(
            mm_per_px=25.4 / self.default_dpi, source=ScaleSource.ASSUMED_DPI,
            confidence=0.2, message=f"Assumed {self.default_dpi:.0f} DPI")


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
# Stage 8b — Contour Assembly with Hierarchy
# =============================================================================

class ContourAssembler:
    def __init__(self, classifier: Optional[FeatureClassifier] = None,
                 min_area_px: int = 1000):
        self.classifier = classifier or FeatureClassifier()
        self.min_area_px = min_area_px

    def assemble(self, edge_image: np.ndarray, alpha_mask: np.ndarray,
                 mm_per_px: float) -> List[FeatureContour]:
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

        features = []
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < self.min_area_px:
                continue
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

        logger.info(f"Assembled {len(features)} feature contours from {len(contours)} raw")
        return features


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

        svg = Element("svg", xmlns="http://www.w3.org/2000/svg",
                       width=f"{width_mm}mm", height=f"{height_mm}mm",
                       viewBox=f"0 0 {width_mm} {height_mm}")

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
    """Write contours to DXF with layers."""
    if not EZDXF_AVAILABLE:
        logger.error("ezdxf not installed — pip install ezdxf")
        return False
    try:
        dxf_ver = {"R12": "R12", "R2000": "R2000", "R2004": "R2004"}.get(version, "R12")
        doc = ezdxf.new(dxf_ver)
        msp = doc.modelspace()

        for layer_name, point_lists in contours_by_layer.items():
            if layer_name not in doc.layers:
                doc.layers.add(layer_name)
            for pts in point_lists:
                if len(pts) < 3:
                    continue
                pts_2d = pts.reshape(-1, 2)
                pts_list = [(float(p[0]), float(p[1])) for p in pts_2d]
                if dxf_ver == "R12":
                    msp.add_polyline2d(pts_list, dxfattribs={"layer": layer_name},
                                       close=True)
                else:
                    msp.add_lwpolyline(pts_list, dxfattribs={"layer": layer_name},
                                        close=True)

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
                ) -> PhotoExtractionResult:

        start_time = time.time()
        source = Path(source_path)
        out_dir = Path(output_dir) if output_dir else source.parent
        out_dir.mkdir(parents=True, exist_ok=True)

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

        # ── Stage 0: Dark background detection ──────────────────────────────
        is_dark_bg = detect_dark_background(image)
        result.dark_background_detected = is_dark_bg
        if is_dark_bg:
            image = cv2.bitwise_not(image)
            logger.info("Dark background -> image inverted")

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

        # ── Stage 5: Edge detection ─────────────────────────────────────────
        edges = self.edge_detector.detect(fg_image, alpha_mask)

        if debug_images:
            p = str(out_dir / f"{source.stem}_04_edges.png")
            cv2.imwrite(p, edges)
            debug_paths["edges"] = p

        # ── Stage 7: Initial calibration ────────────────────────────────────
        calibration = self.calibrator.calibrate(
            image, known_mm=known_dimension_mm, known_px=known_dimension_px,
            spec_name=spec_name, image_dpi=exif_dpi,
            unit=known_unit or self.default_unit)
        mpp = calibration.mm_per_px
        logger.info(f"Scale: {calibration.message} (mpp={mpp:.4f})")

        # ── Stage 8: Contour assembly + classification ──────────────────────
        feature_contours = self.assembler.assemble(edges, alpha_mask, mpp)

        if not feature_contours:
            result.warnings.append("No contours found")
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Find body contour
        body_fc = None
        for fc in feature_contours:
            if fc.feature_type == FeatureType.BODY_OUTLINE:
                body_fc = fc
                break
        if body_fc is None:
            body_fc = max(feature_contours, key=lambda c: c.area_px)
            body_fc.feature_type = FeatureType.BODY_OUTLINE
            body_fc.confidence = 0.7

        # If calibration was from spec, refine using body contour
        if calibration.source == ScaleSource.INSTRUMENT_SPEC and spec_name:
            body_h_px = body_fc.bbox_px[3]  # height in pixels
            if body_h_px > 0 and spec_name in INSTRUMENT_SPECS:
                body_h_mm = INSTRUMENT_SPECS[spec_name]["body"][0]
                mpp = body_h_mm / body_h_px
                calibration = CalibrationResult(
                    mm_per_px=mpp, source=ScaleSource.INSTRUMENT_SPEC,
                    confidence=0.6,
                    message=f"Spec: {spec_name} body {body_h_mm}mm / {body_h_px}px")

        result.calibration = calibration
        mpp = calibration.mm_per_px

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
            result.body_dimensions_mm = (w_mm, h_mm)
            result.body_dimensions_inch = (w_mm / 25.4, h_mm / 25.4)

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

        logger.info(
            f"Done in {result.processing_time_ms:.0f}ms: "
            f"{result.body_dimensions_mm[0]:.1f} x {result.body_dimensions_mm[1]:.1f} mm")

        return result

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


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Photo Vectorizer V2 - Extract outlines from instrument photos")
    parser.add_argument("source", help="Photo path (JPG, PNG, TIFF, PDF)")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    parser.add_argument("-s", "--spec", default=None, help="Instrument spec name")
    parser.add_argument("--mm", type=float, help="Known dimension in mm")
    parser.add_argument("--px", type=float, help="Pixel span of known dimension")
    parser.add_argument("--bg", default="auto",
                        choices=["auto", "grabcut", "rembg", "sam", "threshold"])
    parser.add_argument("--no-perspective", action="store_true")
    parser.add_argument("--formats", nargs="+", default=["svg", "dxf"],
                        choices=["svg", "dxf", "json"])
    parser.add_argument("--debug", action="store_true", help="Save debug images")
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

    print(f"\nInput: {result.input_type.value}")
    print(f"Background: {result.bg_method_used}")
    print(f"Dark background: {result.dark_background_detected}")
    print(f"Perspective: {'corrected' if result.perspective_corrected else 'no'}")
    if result.calibration:
        print(f"Scale: {result.calibration.message}")
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


if __name__ == "__main__":
    main()
