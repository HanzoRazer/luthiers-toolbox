"""
Phase 3.7 Vectorizer Enhancements — Standalone Module
=====================================================

Seven enhancement classes cherry-picked from the Phase 3.6 Robustness plan.
All classes are optional — imported by vectorizer_phase3.py with try/except.

Components:
    1. GuitarPhotoProcessor  — Perspective correction + background removal + edge fusion
    2. AdaptiveLineExtractor — Grid-based adaptive params per image region
    3. ScaleCalibrator        — Multi-method scale detection with user fallback
    4. ContourCompleter       — DBSCAN endpoint clustering + gap bridging
    5. DebugVisualizer        — Stage capture + HTML report generation
    6. ManualOverride         — JSON corrections, contour hash matching
    7. ValidationReport       — Multi-factor scoring with actionable suggestions

Bug fixes applied vs original design:
    - ContourCompleter._connect_clusters uses actual image_shape (was hardcoded 1000x1000)
    - ManualOverride.apply_corrections collects moves before mutating (was mutating during iteration)
    - ValidationReport uses string category keys consistently (was mixing enum/string)

Author: The Production Shop
Version: 3.7.0
"""
import logging
import hashlib
import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import cv2

# Optional sklearn for DBSCAN clustering
try:
    from sklearn.cluster import DBSCAN
    DBSCAN_AVAILABLE = True
except ImportError:
    DBSCAN_AVAILABLE = False

# Optional rembg for ML background removal
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Data Classes
# =============================================================================

class InputType(Enum):
    """Detected input file type."""
    PHOTO = "photo"
    BLUEPRINT = "blueprint"
    SCAN = "scan"
    SVG = "svg"
    UNKNOWN = "unknown"


class ScaleSource(Enum):
    """How mm/px was determined."""
    USER_DIMENSION = "user_dimension"
    INSTRUMENT_SPEC = "instrument_spec"
    REFERENCE_FEATURE = "reference_feature"
    RULER_DETECTED = "ruler_detected"
    ASSUMED_DPI = "assumed_dpi"
    NONE = "none"


class BGRemovalMethod(Enum):
    """Background removal strategy."""
    GRABCUT = "grabcut"
    THRESHOLD = "threshold"
    REMBG = "rembg"
    AUTO = "auto"


@dataclass
class CalibrationResult:
    """Scale calibration outcome."""
    mm_per_px: float
    source: ScaleSource
    reference_px: float = 0.0
    reference_mm: float = 0.0
    confidence: float = 0.0
    message: str = ""


# =============================================================================
# Priority 1: GuitarPhotoProcessor
# =============================================================================

class GuitarPhotoProcessor:
    """
    Specialized processor for guitar photographs.
    Converts photos to blueprint-like line art for the main pipeline.

    Pipeline:
      1. Perspective correction (find largest quadrilateral)
      2. Background removal (GrabCut with optional rembg)
      3. Edge detection (multi-method fusion)
      4. Convert to binary (blueprint-like)
    """

    def __init__(self, use_rembg: bool = True):
        self.use_rembg = use_rembg and REMBG_AVAILABLE
        if self.use_rembg:
            logger.info("rembg available for ML background removal")

    def preprocess_for_extraction(
        self,
        image: np.ndarray,
        debug_callback: Optional[Callable] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Convert guitar photo to blueprint-like line art.

        Args:
            image: BGR image
            debug_callback: Optional function(name, image) to save intermediate stages

        Returns:
            Tuple of (binary_mask, metadata)
        """
        metadata = {
            'perspective_corrected': False,
            'bg_method': 'none',
            'original_shape': image.shape[:2]
        }

        if debug_callback:
            debug_callback('01_original', image)

        # Step 1: Perspective correction
        corrected, was_corrected = self._correct_perspective(image)
        metadata['perspective_corrected'] = was_corrected
        if was_corrected:
            if debug_callback:
                debug_callback('02_perspective_corrected', corrected)
            image = corrected

        # Step 2: Background removal
        foreground, alpha_mask, bg_method = self._remove_background(image)
        metadata['bg_method'] = bg_method
        if debug_callback:
            debug_callback('03_foreground', foreground)
            debug_callback('04_alpha_mask', alpha_mask)

        # Step 3: Edge detection
        edges = self._detect_edges(foreground, alpha_mask)
        if debug_callback:
            debug_callback('05_edges', edges)

        # Step 4: Convert to binary
        binary = self._create_binary_blueprint(edges, alpha_mask)
        if debug_callback:
            debug_callback('06_binary', binary)

        return binary, metadata

    def _correct_perspective(
        self,
        image: np.ndarray,
        min_area_ratio: float = 0.25
    ) -> Tuple[np.ndarray, bool]:
        """Find largest quadrilateral and apply homography."""
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = w * h * min_area_ratio
        best_quad = None
        best_area = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4 and area > best_area:
                best_area = area
                best_quad = approx.reshape(4, 2).astype(np.float32)

        if best_quad is None:
            logger.debug("No reference quadrilateral found — skipping perspective correction")
            return image, False

        src_pts = self._order_points(best_quad)
        dst_w = int(max(
            np.linalg.norm(src_pts[1] - src_pts[0]),
            np.linalg.norm(src_pts[2] - src_pts[3])
        ))
        dst_h = int(max(
            np.linalg.norm(src_pts[3] - src_pts[0]),
            np.linalg.norm(src_pts[2] - src_pts[1])
        ))

        dst_pts = np.array([
            [0, 0], [dst_w - 1, 0],
            [dst_w - 1, dst_h - 1], [0, dst_h - 1]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(image, M, (dst_w, dst_h))
        logger.info(f"Perspective corrected: {w}x{h} -> {dst_w}x{dst_h}")
        return warped, True

    def _remove_background(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, str]:
        """Remove background using rembg (preferred) or GrabCut."""
        if self.use_rembg:
            try:
                return self._rembg_remove(image)
            except Exception as e:
                logger.warning(f"rembg failed, falling back to GrabCut: {e}")
        return self._grabcut_remove(image)

    def _grabcut_remove(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, str]:
        """Remove background using GrabCut with center rectangle init."""
        h, w = image.shape[:2]
        margin_x = int(w * 0.1)
        margin_y = int(h * 0.1)
        rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        try:
            cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        except cv2.error as e:
            logger.warning(f"GrabCut failed: {e}")
            return self._threshold_remove(image)

        fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)

        fg = cv2.bitwise_and(image, image, mask=fg_mask)
        return fg, fg_mask, "grabcut"

    def _rembg_remove(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, str]:
        """Remove background using rembg (ML-based)."""
        from PIL import Image as PILImage
        import io

        pil_img = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        buf.seek(0)

        result_bytes = rembg_remove(buf.read())
        result_pil = PILImage.open(io.BytesIO(result_bytes)).convert('RGBA')
        result_np = np.array(result_pil)

        alpha = result_np[:, :, 3]
        fg_mask = (alpha > 128).astype(np.uint8) * 255
        bgr = cv2.cvtColor(result_np[:, :, :3], cv2.COLOR_RGB2BGR)
        fg = cv2.bitwise_and(bgr, bgr, mask=fg_mask)
        return fg, fg_mask, "rembg"

    def _threshold_remove(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, str]:
        """Simple threshold-based background removal (fallback)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_val = float(gray.mean())

        if mean_val < 80:
            _, mask = cv2.threshold(gray, int(mean_val * 1.5), 255, cv2.THRESH_BINARY)
        else:
            _, mask = cv2.threshold(gray, int(mean_val * 0.7), 255, cv2.THRESH_BINARY_INV)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=4)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

        fg = cv2.bitwise_and(image, image, mask=mask)
        return fg, mask, "threshold"

    def _detect_edges(
        self, foreground: np.ndarray, alpha_mask: np.ndarray, canny_sigma: float = 0.33
    ) -> np.ndarray:
        """Multi-method edge detection fused together."""
        gray = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)

        # Canny with auto thresholds
        med = float(np.median(gray[gray > 10])) if np.any(gray > 10) else 128.0
        lo = max(0, int((1 - canny_sigma) * med))
        hi = min(255, int((1 + canny_sigma) * med))
        edges_canny = cv2.Canny(gray, lo, hi)

        # Sobel magnitude
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx ** 2 + gy ** 2)
        mag = np.clip(mag / (mag.max() + 1e-6) * 255, 0, 255).astype(np.uint8)
        _, edges_sobel = cv2.threshold(mag, 40, 255, cv2.THRESH_BINARY)

        # Laplacian
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap = np.clip(np.abs(lap), 0, 255).astype(np.uint8)
        _, edges_lap = cv2.threshold(lap, 25, 255, cv2.THRESH_BINARY)

        # Fuse
        combined = cv2.bitwise_or(edges_canny, edges_sobel)
        combined = cv2.bitwise_or(combined, edges_lap)
        combined = cv2.bitwise_and(combined, alpha_mask)

        # Close small gaps, remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        return combined

    def _create_binary_blueprint(self, edges: np.ndarray, alpha_mask: np.ndarray) -> np.ndarray:
        """Convert edges to binary image suitable for contour detection."""
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.dilate(edges, kernel, iterations=1)
        binary = cv2.bitwise_or(binary, alpha_mask)
        return binary

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        """Order points: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        d = np.diff(pts, axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        rect[1] = pts[np.argmin(d)]
        rect[3] = pts[np.argmax(d)]
        return rect


# =============================================================================
# Priority 2: AdaptiveLineExtractor
# =============================================================================

class AdaptiveLineExtractor:
    """
    Adapts extraction parameters based on local image characteristics.
    Divides image into regions and applies optimal parameters per region.
    """

    def __init__(self, grid_size: int = 8):
        self.grid_size = grid_size

    def extract_lines(self, image: np.ndarray, base_gap_close: int = 5) -> np.ndarray:
        """
        Extract lines with region-adaptive parameters.

        Args:
            image: BGR or grayscale image
            base_gap_close: Base morphological closing kernel size

        Returns:
            Binary mask with extracted lines
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        cell_h = max(1, h // self.grid_size)
        cell_w = max(1, w // self.grid_size)
        result = np.zeros_like(gray)

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                y1 = i * cell_h
                y2 = (i + 1) * cell_h if i < self.grid_size - 1 else h
                x1 = j * cell_w
                x2 = (j + 1) * cell_w if j < self.grid_size - 1 else w

                region = gray[y1:y2, x1:x2]
                if region.size == 0:
                    continue

                density = self._ink_density(region)
                contrast = self._local_contrast(region)

                if density < 0.01:
                    continue

                if density > 0.3:
                    params = {'method': 'adaptive', 'block_size': 15, 'c': 5,
                              'close_kernel': base_gap_close + 2}
                elif density > 0.1:
                    params = {'method': 'adaptive', 'block_size': 11, 'c': 3,
                              'close_kernel': base_gap_close}
                elif contrast > 40:
                    params = {'method': 'canny', 'low_threshold': 30, 'high_threshold': 100,
                              'close_kernel': base_gap_close}
                else:
                    params = {'method': 'adaptive', 'block_size': 9, 'c': 2,
                              'close_kernel': base_gap_close}

                region_lines = self._extract_region(region, params)
                result[y1:y2, x1:x2] = region_lines

        return result

    @staticmethod
    def _ink_density(region: np.ndarray) -> float:
        return float(np.sum(region < 128)) / max(region.size, 1)

    @staticmethod
    def _local_contrast(region: np.ndarray) -> float:
        return float(np.std(region))

    @staticmethod
    def _extract_region(region: np.ndarray, params: Dict) -> np.ndarray:
        """Extract lines from a single region using specified parameters."""
        if params['method'] == 'adaptive':
            binary = cv2.adaptiveThreshold(
                region, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                params['block_size'], params['c']
            )
        else:
            edges = cv2.Canny(region, params['low_threshold'], params['high_threshold'])
            binary = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)

        if params['close_kernel'] > 0:
            kernel = np.ones((params['close_kernel'], params['close_kernel']), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return binary


# =============================================================================
# Priority 3: ScaleCalibrator
# =============================================================================

class ScaleCalibrator:
    """
    Multi-method scale detection with intelligent fallback.

    Priority chain:
      1. User-supplied dimension (most reliable)
      2. Ruler detection in image
      3. Reference features (neck pocket, pickup routes)
      4. Instrument spec (body dimensions)
      5. Assumed DPI (last resort)
    """

    def __init__(self, mm_per_px_default: float = 25.4 / 400):
        self.mm_per_px_default = mm_per_px_default
        self.reference_features = {
            'neck_pocket_width': 56.0,
            'humbucker_length': 71.5,
            'single_coil_length': 85.0,
            'tuneomatic_bridge': 120.0,
        }
        self.body_specs = {
            'stratocaster': (406, 325),
            'telecaster': (406, 325),
            'jazzmaster': (500, 360),
            'jaguar': (480, 350),
            'les_paul': (450, 340),
            'sg': (400, 340),
            'es335': (500, 420),
            'dreadnought': (520, 400),
            'orchestra_model': (495, 395),
            'classical': (490, 370),
        }

    def calibrate(
        self,
        image: np.ndarray,
        contours: list,
        user_mm: Optional[float] = None,
        user_px: Optional[float] = None,
        spec_name: Optional[str] = None,
        image_dpi: Optional[float] = None
    ) -> CalibrationResult:
        """Determine mm/px using best available method."""

        # Priority 1: User-supplied dimension
        if user_mm and user_px and user_px > 0:
            mpp = user_mm / user_px
            return CalibrationResult(
                mm_per_px=mpp, source=ScaleSource.USER_DIMENSION,
                reference_px=user_px, reference_mm=user_mm,
                confidence=1.0, message=f"User dimension: {user_mm}mm over {user_px}px"
            )

        # Priority 2: Ruler detection (stub — returns None for now)
        ruler_result = self._detect_ruler(image)
        if ruler_result:
            return ruler_result

        # Priority 3: Reference features
        feature_result = self._calibrate_from_features(contours)
        if feature_result:
            return feature_result

        # Priority 4: Instrument spec
        if spec_name and spec_name in self.body_specs:
            spec_result = self._calibrate_from_spec(contours, spec_name)
            if spec_result:
                return spec_result

        # Priority 5: Assumed DPI (last resort)
        dpi = image_dpi or 300.0
        mpp = 25.4 / dpi
        confidence = 0.5 if image_dpi else 0.2
        message = f"Assumed {dpi:.0f} DPI ({mpp:.5f} mm/px)"
        if not image_dpi:
            message += " — Provide user dimension or spec for accuracy"

        return CalibrationResult(
            mm_per_px=mpp, source=ScaleSource.ASSUMED_DPI,
            confidence=confidence, message=message
        )

    def _detect_ruler(self, image: np.ndarray) -> Optional[CalibrationResult]:
        """Look for a ruler or scale bar in the image (stub for future implementation)."""
        return None

    def _calibrate_from_features(self, contours: list) -> Optional[CalibrationResult]:
        """Use known feature dimensions for calibration."""
        # Import here to avoid circular dependency
        try:
            from vectorizer_phase3 import ContourCategory
        except ImportError:
            return None

        for feature_name, expected_mm in self.reference_features.items():
            if 'neck_pocket' in feature_name:
                candidates = [c for c in contours if c.category == ContourCategory.NECK_POCKET]
            elif 'humbucker' in feature_name:
                candidates = [c for c in contours if c.category == ContourCategory.PICKUP_ROUTE]
            else:
                continue

            if candidates:
                if 'neck_pocket' in feature_name:
                    measured_px = min(candidates[0].width_mm, candidates[0].height_mm) / self.mm_per_px_default
                else:
                    measured_px = candidates[0].max_dim / self.mm_per_px_default

                if measured_px > 0:
                    mpp = expected_mm / measured_px
                    return CalibrationResult(
                        mm_per_px=mpp, source=ScaleSource.REFERENCE_FEATURE,
                        reference_px=measured_px, reference_mm=expected_mm,
                        confidence=0.8,
                        message=f"Feature '{feature_name}': {expected_mm}mm over {measured_px:.1f}px"
                    )
        return None

    def _calibrate_from_spec(self, contours: list, spec_name: str) -> Optional[CalibrationResult]:
        """Use known instrument body dimensions for calibration."""
        try:
            from vectorizer_phase3 import ContourCategory
        except ImportError:
            return None

        bodies = [c for c in contours if c.category == ContourCategory.BODY_OUTLINE]
        if not bodies:
            return None

        body = bodies[0]
        spec_len, spec_wid = self.body_specs[spec_name]

        body_px_len = body.max_dim / self.mm_per_px_default
        body_px_wid = body.min_dim / self.mm_per_px_default

        if body_px_len > 0 and body_px_wid > 0:
            mpp_len = spec_len / body_px_len
            mpp_wid = spec_wid / body_px_wid
            mpp = (mpp_len + mpp_wid) / 2
            return CalibrationResult(
                mm_per_px=mpp, source=ScaleSource.INSTRUMENT_SPEC,
                reference_px=body_px_len, reference_mm=spec_len,
                confidence=0.7,
                message=f"Spec '{spec_name}': {spec_len}mm length over {body_px_len:.1f}px"
            )
        return None


# =============================================================================
# Priority 4: ContourCompleter
# =============================================================================

class ContourCompleter:
    """
    Links broken contour segments into complete outlines.
    Uses endpoint clustering and curve fitting to fill gaps.
    """

    def __init__(self, max_gap_px: int = 50, min_segment_points: int = 10):
        self.max_gap_px = max_gap_px
        self.min_segment_points = min_segment_points

    def complete_body_outline(
        self,
        contours: List[np.ndarray],
        image_shape: Tuple[int, int]
    ) -> Optional[np.ndarray]:
        """
        Attempt to complete a single closed outline from fragments.

        Args:
            contours: List of contour fragments (each Nx1x2)
            image_shape: (height, width) for bounds checking

        Returns:
            Completed contour or None if insufficient fragments
        """
        if len(contours) < 2:
            return contours[0] if contours else None

        valid_contours = [
            cnt for cnt in contours
            if cv2.arcLength(cnt, False) > self.min_segment_points
        ]
        if len(valid_contours) < 2:
            return valid_contours[0] if valid_contours else None

        endpoints = self._find_endpoints(valid_contours)
        clusters = self._cluster_endpoints(endpoints)
        return self._connect_clusters(valid_contours, clusters, image_shape)

    def _find_endpoints(self, contours: List[np.ndarray]) -> List[Tuple[np.ndarray, int, bool]]:
        """Find start and end points of each contour segment."""
        endpoints = []
        for i, cnt in enumerate(contours):
            if len(cnt) >= 2:
                pts = cnt.reshape(-1, 2)
                endpoints.append((pts[0], i, True))
                endpoints.append((pts[-1], i, False))
        return endpoints

    def _cluster_endpoints(
        self, endpoints: List[Tuple[np.ndarray, int, bool]]
    ) -> List[List[Tuple[np.ndarray, int, bool]]]:
        """Group nearby endpoints using DBSCAN or simple distance threshold."""
        if not endpoints:
            return []

        if DBSCAN_AVAILABLE and len(endpoints) > 5:
            points = np.array([ep[0] for ep in endpoints])
            clustering = DBSCAN(eps=self.max_gap_px, min_samples=1).fit(points)
            labels = clustering.labels_
            clusters = []
            for label in set(labels):
                if label == -1:
                    continue
                cluster = [endpoints[i] for i in range(len(endpoints)) if labels[i] == label]
                clusters.append(cluster)
            return clusters

        # Simple distance-based clustering fallback
        clusters = []
        used = set()
        for i, (p1, idx1, is_start1) in enumerate(endpoints):
            if i in used:
                continue
            cluster = [(p1, idx1, is_start1)]
            used.add(i)
            for j, (p2, idx2, is_start2) in enumerate(endpoints):
                if j in used or idx1 == idx2:
                    continue
                if np.linalg.norm(p1 - p2) <= self.max_gap_px:
                    cluster.append((p2, idx2, is_start2))
                    used.add(j)
            clusters.append(cluster)
        return clusters

    def _connect_clusters(
        self,
        contours: List[np.ndarray],
        clusters: List[List[Tuple[np.ndarray, int, bool]]],
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """Connect endpoints within each cluster to form continuous contour.

        BUG FIX: Uses actual image_shape instead of hardcoded 1000x1000.
        """
        if len(clusters) < 2:
            return self._merge_contours(contours)

        centroids = []
        for cluster in clusters:
            points = np.array([ep[0] for ep in cluster])
            centroids.append(np.mean(points, axis=0))

        h, w = image_shape
        center = np.array([w / 2, h / 2])
        angles = [np.arctan2((c - center)[1], (c - center)[0]) for c in centroids]
        sorted_indices = np.argsort(angles)

        all_points = []
        seen_contours = set()
        for idx in sorted_indices:
            cluster = clusters[idx]
            for _point, cnt_idx, is_start in cluster:
                if cnt_idx in seen_contours:
                    continue
                seen_contours.add(cnt_idx)
                pts = contours[cnt_idx].reshape(-1, 2)
                if is_start:
                    all_points.extend(pts.tolist())
                else:
                    all_points.extend(pts[::-1].tolist())

        return np.array(all_points, dtype=np.int32).reshape(-1, 1, 2)

    @staticmethod
    def _merge_contours(contours: List[np.ndarray]) -> np.ndarray:
        """Simple concatenation of contours."""
        all_points = []
        for cnt in contours:
            all_points.extend(cnt.reshape(-1, 2).tolist())
        return np.array(all_points, dtype=np.int32).reshape(-1, 1, 2)


# =============================================================================
# Priority 5: DebugVisualizer
# =============================================================================

class DebugVisualizer:
    """
    Creates visual debug output at each pipeline stage.
    Generates HTML report with all stages for easy inspection.
    """

    def __init__(self, output_dir: Union[str, Path], enabled: bool = True):
        self.output_dir = Path(output_dir) / "debug"
        self.enabled = enabled
        self.stage_images: Dict[str, Path] = {}
        self.stage_info: Dict[str, Any] = {}
        self._stage_counter = 0
        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_stage(
        self,
        name: str,
        image: np.ndarray,
        info: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """Save intermediate result with annotations."""
        if not self.enabled:
            return None

        self._stage_counter += 1
        filename = f"{self._stage_counter:02d}_{name}.png"
        path = self.output_dir / filename

        if info:
            image = self._annotate(image, info)
            self.stage_info[name] = info

        cv2.imwrite(str(path), image)
        self.stage_images[name] = path
        logger.debug(f"Debug stage saved: {name} -> {path}")
        return path

    @staticmethod
    def _annotate(image: np.ndarray, info: Dict[str, Any]) -> np.ndarray:
        annotated = image.copy()
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)
        y_offset = 30
        for key, value in info.items():
            text = f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}"
            cv2.putText(annotated, text, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 25
        return annotated

    def draw_contours(
        self, image: np.ndarray, contours: List[np.ndarray],
        color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2
    ) -> np.ndarray:
        result = image.copy()
        if len(result.shape) == 2:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(result, contours, -1, color, thickness)
        return result

    def create_report(self, title: str = "Vectorization Debug Report") -> Path:
        """Generate HTML report with all stages."""
        html = [
            "<!DOCTYPE html>", "<html>", "<head>",
            f"<title>{title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            ".stage { margin-bottom: 30px; border-bottom: 1px solid #ccc; }",
            ".stage h2 { background: #f0f0f0; padding: 10px; }",
            ".stage img { max-width: 100%; border: 1px solid #ddd; }",
            ".info { background: #f9f9f9; padding: 10px; font-family: monospace; }",
            "</style>",
            "</head>", "<body>",
            f"<h1>{title}</h1>",
            f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        ]

        for name, path in sorted(self.stage_images.items()):
            html.append("<div class='stage'>")
            html.append(f"<h2>{name}</h2>")
            if name in self.stage_info:
                html.append("<div class='info'>")
                for key, value in self.stage_info[name].items():
                    html.append(f"<p><strong>{key}:</strong> {value}</p>")
                html.append("</div>")
            html.append(f"<img src='{path.name}' alt='{name}'>")
            html.append("</div>")

        html.extend(["</body>", "</html>"])

        report_path = self.output_dir / "debug_report.html"
        report_path.write_text("\n".join(html), encoding='utf-8')
        logger.info(f"Debug report created: {report_path}")
        return report_path


# =============================================================================
# Priority 6: ManualOverride
# =============================================================================

class ManualOverride:
    """
    JSON-based correction system for contour classifications.
    Stores user corrections and applies them in future runs.

    BUG FIX: apply_corrections() collects moves before mutating lists,
    preventing index corruption from list modification during iteration.
    """

    def __init__(self, corrections_file: Optional[str] = None):
        self.corrections_file = Path(corrections_file) if corrections_file else Path(".corrections.json")
        self.corrections: Dict[str, Dict[str, Any]] = self._load_corrections()
        logger.info(f"Loaded {len(self.corrections)} manual corrections from {self.corrections_file}")

    def _load_corrections(self) -> Dict[str, Dict[str, Any]]:
        if self.corrections_file.exists():
            try:
                with open(self.corrections_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load corrections: {e}")
        return {}

    def _save_corrections(self):
        try:
            with open(self.corrections_file, 'w') as f:
                json.dump(self.corrections, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to save corrections: {e}")

    def correct_contour(
        self, contour_hash: str, correct_category: str,
        bbox: Tuple[int, int, int, int], image_path: str, notes: str = ""
    ) -> bool:
        """Store user correction for future runs."""
        self.corrections[contour_hash] = {
            "contour_hash": contour_hash,
            "correct_category": correct_category,
            "bbox": list(bbox),
            "image_path": image_path,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "applied_count": 0
        }
        self._save_corrections()
        logger.info(f"Saved correction: {contour_hash} -> {correct_category}")
        return True

    def apply_corrections(self, classified: dict) -> dict:
        """
        Override classifications with user corrections.

        BUG FIX: Collects all moves first, then applies in reverse index order
        to prevent index corruption from list mutation during iteration.
        """
        try:
            from vectorizer_phase3 import ContourCategory
        except ImportError:
            return classified

        moves = []  # (from_cat, index, contour_info, new_cat)

        for cat, contours in classified.items():
            for i, contour in enumerate(contours):
                h = self._generate_hash(contour.contour)
                if h in self.corrections:
                    correct_cat_str = self.corrections[h]["correct_category"]
                    try:
                        new_cat = ContourCategory(correct_cat_str)
                    except ValueError:
                        logger.warning(f"Invalid category in correction: {correct_cat_str}")
                        continue
                    if new_cat != cat:
                        moves.append((cat, i, contour, new_cat))

        # Apply moves in reverse index order so earlier pops don't shift later indices
        for from_cat, idx, contour, new_cat in sorted(moves, key=lambda m: m[1], reverse=True):
            classified[from_cat].pop(idx)
            if new_cat not in classified:
                classified[new_cat] = []
            contour.category = new_cat
            contour.ml_confidence = 1.0
            classified[new_cat].append(contour)

            # Track application count
            h = self._generate_hash(contour.contour)
            if h in self.corrections:
                self.corrections[h]["applied_count"] = self.corrections[h].get("applied_count", 0) + 1

        if moves:
            logger.info(f"Applied {len(moves)} manual corrections")
            self._save_corrections()

        return classified

    @staticmethod
    def _generate_hash(contour: np.ndarray) -> str:
        """Generate consistent hash for contour."""
        epsilon = 0.01 * cv2.arcLength(contour, True)
        simplified = cv2.approxPolyDP(contour, epsilon, True)
        return hashlib.md5(simplified.tobytes()).hexdigest()[:12]

    def get_pending_corrections(self) -> List[Dict[str, Any]]:
        return [
            {**c, "hash": h} for h, c in self.corrections.items()
            if c.get("applied_count", 0) == 0
        ]


# =============================================================================
# Priority 7: ValidationReport
# =============================================================================

class ValidationReport:
    """
    Detailed validation with actionable feedback.
    Replaces binary pass/fail with comprehensive diagnostics.
    """

    def __init__(self, instrument_specs: Optional[Dict] = None):
        self.specs = instrument_specs or {}

        try:
            from vectorizer_phase3 import InstrumentType, ContourCategory
            self._InstrumentType = InstrumentType
            self._ContourCategory = ContourCategory
        except ImportError:
            self._InstrumentType = None
            self._ContourCategory = None

        self.expected_features = {}
        if self._InstrumentType and self._ContourCategory:
            IT = self._InstrumentType
            CC = self._ContourCategory
            self.expected_features = {
                IT.ELECTRIC_GUITAR: {
                    CC.BODY_OUTLINE: 1,
                    CC.NECK_POCKET: (1, 2),
                    CC.PICKUP_ROUTE: (1, 4),
                    CC.CONTROL_CAVITY: (1, 3),
                    CC.BRIDGE_ROUTE: (1, 2),
                    CC.JACK_ROUTE: (1, 2),
                },
                IT.ACOUSTIC_GUITAR: {
                    CC.BODY_OUTLINE: 1,
                    CC.SOUNDHOLE: (1, 1),
                    CC.ROSETTE: (1, 1),
                    CC.BRACING: (5, 15),
                },
                IT.ARCHTOP: {
                    CC.BODY_OUTLINE: 1,
                    CC.F_HOLE: (2, 2),
                    CC.BRACING: (3, 10),
                },
            }

    def validate(self, result) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        report = {
            "passed": True, "confidence": 1.0,
            "issues": [], "suggestions": [],
            "metrics": {}, "stage_scores": {}
        }

        body_score = self._check_body_detection(result)
        report["stage_scores"]["body_detection"] = body_score
        if body_score["score"] < 0.5:
            report["passed"] = False
        report["issues"].extend(body_score["issues"])
        report["suggestions"].extend(body_score["suggestions"])
        report["confidence"] *= body_score["score"]

        scale_score = self._check_scale_calibration(result)
        report["stage_scores"]["scale"] = scale_score
        report["issues"].extend(scale_score["issues"])
        report["suggestions"].extend(scale_score["suggestions"])
        report["confidence"] *= scale_score["score"]

        feature_score = self._check_feature_completeness(result)
        report["stage_scores"]["features"] = feature_score
        report["issues"].extend(feature_score["issues"])
        report["suggestions"].extend(feature_score["suggestions"])
        report["confidence"] *= feature_score["score"]

        quality_score = self._check_contour_quality(result)
        report["stage_scores"]["quality"] = quality_score
        report["issues"].extend(quality_score["issues"])
        report["suggestions"].extend(quality_score["suggestions"])
        report["confidence"] *= quality_score["score"]

        critical_issues = [i for i in report["issues"] if "critical" in i.lower()]
        report["passed"] = len(critical_issues) == 0

        report["metrics"] = {
            "body_width_mm": result.dimensions_mm[0],
            "body_height_mm": result.dimensions_mm[1],
            "total_contours": sum(len(c) for c in result.contours_by_category.values()),
            "categories_found": list(result.contours_by_category.keys()),
            "scale_source": result.scale_source,
            "scale_factor": result.scale_factor,
        }
        return report

    def _check_body_detection(self, result) -> Dict[str, Any]:
        score, issues, suggestions = 1.0, [], []
        CC = self._ContourCategory
        body_key = CC.BODY_OUTLINE.value if CC else "body_outline"
        bodies = result.contours_by_category.get(body_key, [])
        if not bodies:
            score = 0.0
            issues.append("critical: No body outline detected")
            suggestions.append("Try adjusting gap_close parameter or use better lighting/contrast")
        elif len(bodies) > 1:
            score = 0.5
            issues.append(f"Multiple body outlines detected ({len(bodies)})")
            suggestions.append("Check if page borders or logos are being misclassified")
        return {"score": score, "issues": issues, "suggestions": suggestions}

    def _check_scale_calibration(self, result) -> Dict[str, Any]:
        score, issues, suggestions = 1.0, [], []
        if result.scale_source == "none":
            score = 0.3
            issues.append("Scale could not be auto-detected")
            suggestions.append("Provide known dimension or instrument spec name")
        elif result.scale_source == "assumed_dpi":
            score = 0.5
            issues.append("Scale based on assumed DPI — dimensions may be inaccurate")
            suggestions.append("Measure a known feature and supply as user dimension")
        if result.dimensions_mm[0] > 0:
            body_len = max(result.dimensions_mm)
            if body_len < 150 or body_len > 700:
                score *= 0.7
                issues.append(f"Body length {body_len:.0f}mm seems unusual")
                suggestions.append("Verify scale calibration")
        return {"score": score, "issues": issues, "suggestions": suggestions}

    def _check_feature_completeness(self, result) -> Dict[str, Any]:
        score, issues, suggestions = 1.0, [], []
        inst_type = result.instrument_type
        if inst_type in self.expected_features:
            for cat, expected_range in self.expected_features[inst_type].items():
                cat_name = cat.value
                found = len(result.contours_by_category.get(cat_name, []))
                if isinstance(expected_range, tuple):
                    min_exp, max_exp = expected_range
                    if found < min_exp:
                        score *= 0.8
                        issues.append(f"Missing {cat_name}: expected {min_exp}-{max_exp}, got {found}")
                        suggestions.append(f"Check if {cat_name} is visible and well-lit")
                    elif found > max_exp:
                        score *= 0.9
                        issues.append(f"Too many {cat_name}: expected max {max_exp}, got {found}")
                else:
                    if found < expected_range:
                        score *= 0.8
                        issues.append(f"Missing {cat_name}: expected {expected_range}, got {found}")
        return {"score": score, "issues": issues, "suggestions": suggestions}

    def _check_contour_quality(self, result) -> Dict[str, Any]:
        score, issues, suggestions = 1.0, [], []
        total = sum(len(c) for c in result.contours_by_category.values())
        if total == 0:
            score = 0.0
            issues.append("No contours extracted")
            suggestions.append("Check image contrast and extraction parameters")
        elif total > 500:
            score *= 0.7
            issues.append(f"Large number of contours ({total}) — possible noise")
            suggestions.append("Increase min_area filter or check background")
        return {"score": score, "issues": issues, "suggestions": suggestions}

    def generate_report_text(self, result) -> str:
        report = self.validate(result)
        lines = [
            "=" * 60, "VALIDATION REPORT", "=" * 60,
            f"Overall: {'PASSED' if report['passed'] else 'FAILED'}",
            f"Confidence: {report['confidence']:.1%}", "",
            "Metrics:",
            f"  Body dimensions: {result.dimensions_mm[0]:.0f} x {result.dimensions_mm[1]:.0f} mm",
            f"  Scale source: {result.scale_source}",
            f"  Total contours: {report['metrics']['total_contours']}",
            f"  Categories: {', '.join(report['metrics']['categories_found'])}",
        ]
        if report["issues"]:
            lines.extend(["", "Issues Found:"])
            for issue in report["issues"]:
                lines.append(f"  ! {issue}")
        if report["suggestions"]:
            lines.extend(["", "Suggestions:"])
            for suggestion in report["suggestions"]:
                lines.append(f"  -> {suggestion}")
        lines.append("=" * 60)
        return "\n".join(lines)


# =============================================================================
# Input Classification Helper
# =============================================================================

def classify_input_type(image: np.ndarray) -> InputType:
    """Simple input classification based on image statistics."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    white_ratio = float(np.sum(gray > 240)) / gray.size
    dark_ratio = float(np.sum(gray < 30)) / gray.size
    color_variance = float(np.var(image.astype(np.float32)))

    if white_ratio > 0.75:
        return InputType.BLUEPRINT
    elif dark_ratio > 0.5 and color_variance > 500:
        return InputType.PHOTO
    elif white_ratio > 0.5:
        return InputType.SCAN
    else:
        return InputType.PHOTO
