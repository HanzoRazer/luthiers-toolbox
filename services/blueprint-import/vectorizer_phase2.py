"""
Phase 2 Vectorizer - Intelligent Geometry Reconstruction
Adds OpenCV edge detection, contour analysis, and DXF R12-R18 export
Enhanced with comprehensive color filtering capabilities
"""
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
import numpy as np
import cv2
import svgwrite
from svgwrite import mm
import ezdxf
from ezdxf import units as dxf_units
from dxf_compat import (
    create_document, add_polyline, validate_version,
    supports_lwpolyline, DxfVersion
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PDF/Image Loading
# ---------------------------------------------------------------------------

def load_input(source_path: str, page_num: int = 0, dpi: int = 300) -> np.ndarray:
    """
    Handle both PDF and image formats

    Args:
        source_path: Path to PDF or image file
        page_num: Page number for PDFs (0-indexed)
        dpi: Resolution for PDF rasterization

    Returns:
        BGR numpy array
    """
    ext = Path(source_path).suffix.lower()

    if ext == '.pdf':
        return rasterize_pdf(source_path, page_num=page_num, dpi=dpi)

    # Direct image loading
    image = cv2.imread(source_path)
    if image is None:
        raise ValueError(f"Could not load image: {source_path}")
    return image


def rasterize_pdf(pdf_path: str, page_num: int = 0, dpi: int = 300) -> np.ndarray:
    """
    Rasterize PDF page to numpy array

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
        dpi: Resolution in dots per inch

    Returns:
        BGR numpy array
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF (fitz) required for PDF support. Install with: pip install pymupdf")

    doc = fitz.open(pdf_path)

    if page_num >= len(doc):
        raise ValueError(f"Page {page_num} does not exist. PDF has {len(doc)} pages.")

    page = doc[page_num]

    # High DPI for better edge detection
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Convert to numpy array
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )

    # Convert to BGR for OpenCV
    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 1:  # Grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif pix.n == 3:  # RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    doc.close()

    logger.info(f"Rasterized PDF page {page_num} at {dpi} DPI: {img.shape[1]}x{img.shape[0]} pixels")
    return img


# ---------------------------------------------------------------------------
# Color Filtering
# ---------------------------------------------------------------------------

class ColorFilter:
    """
    Color-based layer extraction for technical drawings.
    Includes auto-threshold detection for varying blueprint styles.
    """

    # Common blueprint colors (BGR format for OpenCV)
    BLUEPRINT_COLORS = {
        'red': (0, 0, 255),        # Body outline, critical features
        'blue': (255, 0, 0),        # Dimensions, annotations
        'green': (0, 255, 0),       # Hidden lines, reference
        'yellow': (0, 255, 255),    # Special features
        'cyan': (255, 255, 0),      # Electrical, wiring
        'magenta': (255, 0, 255),   # Cut lines, modifications
        'black': (0, 0, 0),         # Text, title block
        'gray': (128, 128, 128),    # Grid lines, background
        'white': (255, 255, 255),   # Paper color (usually ignored)
        'dark_red': (0, 0, 139),    # Darker red variant
        'dark_blue': (139, 0, 0),   # Darker blue variant
    }

    # Blueprint type classifications based on pixel distribution
    BLUEPRINT_DARK = 'dark'       # Dark lines on white (Selmer, Jazzmaster)
    BLUEPRINT_FAINT = 'faint'     # Faint/light lines on white (Gibson 335)
    BLUEPRINT_INVERTED = 'inverted'  # White lines on dark (blueprint style)

    def __init__(self, tolerance: int = 30):
        """
        Initialize color filter

        Args:
            tolerance: Color matching tolerance (0-255)
        """
        self.tolerance = tolerance

    def analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze image pixel distribution to determine blueprint type.

        This helps choose the best thresholding strategy for different
        blueprint styles (dark lines vs faint lines vs inverted).

        Args:
            image: BGR or grayscale image

        Returns:
            Dict with analysis results:
                - blueprint_type: 'dark', 'faint', or 'inverted'
                - min_pixel: Minimum pixel value
                - max_pixel: Maximum pixel value
                - mean_pixel: Mean pixel value
                - white_ratio: Ratio of white pixels (>250)
                - dark_ratio: Ratio of dark pixels (<100)
                - recommended_threshold: Suggested threshold value
                - recommended_method: 'fixed', 'otsu', or 'adaptive'
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        total = gray.size
        min_px = int(gray.min())
        max_px = int(gray.max())
        mean_px = float(gray.mean())

        # Count pixels at different levels
        white_pixels = np.sum(gray > 250)
        light_pixels = np.sum((gray > 200) & (gray <= 250))
        mid_pixels = np.sum((gray > 100) & (gray <= 200))
        dark_pixels = np.sum((gray > 50) & (gray <= 100))
        black_pixels = np.sum(gray <= 50)

        white_ratio = white_pixels / total
        light_ratio = light_pixels / total
        dark_ratio = (dark_pixels + black_pixels) / total
        black_ratio = black_pixels / total

        # Determine blueprint type
        if black_ratio > 0.3:
            # Mostly dark = inverted blueprint (white on black)
            blueprint_type = self.BLUEPRINT_INVERTED
            recommended_method = 'fixed'
            recommended_threshold = 150  # Extract light pixels
        elif white_ratio > 0.95:
            # Almost all white = very faint lines
            blueprint_type = self.BLUEPRINT_FAINT
            recommended_method = 'otsu'
            recommended_threshold = 0  # Let Otsu decide
        elif dark_ratio > 0.02:
            # Has sufficient dark content = standard dark lines
            blueprint_type = self.BLUEPRINT_DARK
            recommended_method = 'fixed'
            # Calculate threshold based on where dark lines are
            if min_px < 50:
                recommended_threshold = 100
            else:
                recommended_threshold = min(150, min_px + 50)
        else:
            # Light/mid content = faint lines, use adaptive
            blueprint_type = self.BLUEPRINT_FAINT
            recommended_method = 'otsu'
            recommended_threshold = 0

        logger.info(f"Image analysis: type={blueprint_type}, method={recommended_method}, "
                   f"white={white_ratio*100:.1f}%, dark={dark_ratio*100:.1f}%")

        return {
            'blueprint_type': blueprint_type,
            'min_pixel': min_px,
            'max_pixel': max_px,
            'mean_pixel': mean_px,
            'white_ratio': white_ratio,
            'light_ratio': light_ratio,
            'dark_ratio': dark_ratio,
            'black_ratio': black_ratio,
            'recommended_threshold': recommended_threshold,
            'recommended_method': recommended_method
        }

    def auto_threshold(
        self,
        image: np.ndarray,
        gap_close_size: int = 0
    ) -> np.ndarray:
        """
        Automatically determine and apply the best thresholding method.

        Analyzes the image to determine if it has dark lines, faint lines,
        or is inverted, then applies the appropriate extraction method.

        Args:
            image: BGR image
            gap_close_size: Morphological closing kernel size (0 = disabled)

        Returns:
            Binary mask of detected lines/features
        """
        # Analyze image characteristics
        analysis = self.analyze_image(image)
        method = analysis['recommended_method']
        threshold = analysis['recommended_threshold']
        bp_type = analysis['blueprint_type']

        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        logger.info(f"Auto-threshold: {bp_type} blueprint, using {method} method")

        if method == 'otsu':
            # Use Otsu's automatic thresholding
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            logger.info(f"Otsu selected threshold automatically")

        elif method == 'adaptive':
            # Use adaptive thresholding for variable lighting
            mask = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 51, 5
            )

        elif bp_type == self.BLUEPRINT_INVERTED:
            # Inverted: extract light pixels on dark background
            _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

        else:
            # Standard: extract dark pixels on light background
            _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

        # Basic cleanup
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Optional gap closing
        if gap_close_size > 0:
            mask = self.close_gaps(mask, gap_close_size)

        pixel_count = cv2.countNonZero(mask)
        logger.info(f"Auto-threshold extracted {pixel_count} pixels")

        return mask

    def create_color_mask(
        self,
        image: np.ndarray,
        target_color: Union[str, Tuple[int, int, int]],
        tolerance: Optional[int] = None
    ) -> np.ndarray:
        """
        Create binary mask for specific color

        Args:
            image: BGR image
            target_color: Color name or BGR tuple
            tolerance: Optional override tolerance

        Returns:
            Binary mask where color matches
        """
        if tolerance is None:
            tolerance = self.tolerance

        # Get BGR value
        if isinstance(target_color, str):
            if target_color.lower() not in self.BLUEPRINT_COLORS:
                raise ValueError(f"Unknown color: {target_color}. Available: {list(self.BLUEPRINT_COLORS.keys())}")
            target_bgr = self.BLUEPRINT_COLORS[target_color.lower()]
        else:
            target_bgr = target_color

        # Create color range
        lower = np.array([max(0, c - tolerance) for c in target_bgr])
        upper = np.array([min(255, c + tolerance) for c in target_bgr])

        # Create mask
        mask = cv2.inRange(image, lower, upper)

        return mask

    def extract_color_layers(
        self,
        image: np.ndarray,
        colors: List[Union[str, Tuple[int, int, int]]],
        tolerance: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """
        Extract multiple color layers from image

        Args:
            image: BGR image
            colors: List of colors to extract
            tolerance: Color matching tolerance

        Returns:
            Dict mapping color names to binary masks
        """
        layers = {}

        for color in colors:
            # Get color name for dict key
            if isinstance(color, str):
                color_name = color
            else:
                # Generate name from BGR tuple
                color_name = f"rgb_{color[2]}_{color[1]}_{color[0]}"

            mask = self.create_color_mask(image, color, tolerance)

            # Clean up mask with morphological operations
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Only add if mask has content
            pixel_count = cv2.countNonZero(mask)
            if pixel_count > 0:
                layers[color_name] = mask
                logger.info(f"Extracted layer '{color_name}' with {pixel_count} pixels")
            else:
                logger.warning(f"No pixels found for color '{color_name}'")

        return layers

    def extract_dark_lines(
        self,
        image: np.ndarray,
        threshold: Union[int, str] = 100,
        gap_close_size: int = 0
    ) -> np.ndarray:
        """
        Extract all dark lines (black, dark red, dark blue, etc.)

        Args:
            image: BGR image
            threshold: Darkness threshold (0-255, lower = darker), or 'auto' for
                       automatic detection based on image analysis
            gap_close_size: Morphological closing kernel size to bridge gaps (0 = disabled)

        Returns:
            Binary mask of dark pixels
        """
        # Use auto-threshold if requested
        if threshold == 'auto':
            return self.auto_threshold(image, gap_close_size)

        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Threshold to get dark pixels
        _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

        # Basic cleanup
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Optional gap closing for blueprints with broken lines
        if gap_close_size > 0:
            mask = self.close_gaps(mask, gap_close_size)

        logger.info(f"Extracted dark lines with {cv2.countNonZero(mask)} pixels (threshold={threshold})")
        return mask

    def close_gaps(
        self,
        mask: np.ndarray,
        kernel_size: int = 5,
        iterations: int = 2
    ) -> np.ndarray:
        """
        Close gaps in line drawings using morphological operations.

        Useful for blueprints where lines may have small breaks due to
        scanning artifacts, low contrast, or drawing style.

        Args:
            mask: Binary mask image
            kernel_size: Size of the closing kernel (larger = bigger gaps closed)
            iterations: Number of closing iterations

        Returns:
            Mask with gaps closed
        """
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        logger.info(f"Applied gap closing (kernel={kernel_size}, iter={iterations})")
        return closed


# ---------------------------------------------------------------------------
# Guitar Feature Classification
# ---------------------------------------------------------------------------

class GuitarFeatureClassifier:
    """
    Classify contours into guitar-specific features based on dimensions.
    Supports electric guitar bodies, acoustic bodies, necks, and components.
    """

    # Feature size ranges in mm (min_dim, max_dim) for (width, height)
    # Feature size ranges in mm - ORDER MATTERS for classification priority
    # More specific features should be checked before general ones
    ELECTRIC_FEATURES = {
        'BODY_OUTLINE': {
            'max_range': (450, 600),  # Longest dimension
            'min_range': (280, 420),  # Shortest dimension
            'description': 'Electric guitar body outline'
        },
        'PICKGUARD': {
            'max_range': (200, 400),
            'min_range': (150, 350),
            'description': 'Pickguard outline'
        },
        'RHYTHM_CIRCUIT': {
            'max_range': (180, 260),
            'min_range': (80, 120),
            'description': 'Rhythm/lead circuit cavity (Jazzmaster/Jaguar)'
        },
        'CONTROL_CAVITY': {
            'max_range': (100, 150),
            'min_range': (40, 70),
            'description': 'Control cavity routing'
        },
        'PICKUP_ROUTE': {
            # Jazzmaster/Jaguar soapbar: ~93x51mm
            # Strat single coil: ~85x35mm
            # Humbucker: ~70x40mm
            'max_range': (80, 110),
            'min_range': (35, 65),
            'aspect_range': (1.3, 3.0),  # Pickups are elongated
            'description': 'Pickup cavity routing'
        },
        'NECK_POCKET': {
            # Standard Fender: ~56x76mm
            'max_range': (70, 85),
            'min_range': (55, 75),
            'aspect_range': (1.0, 1.5),  # More square than pickups
            'description': 'Neck pocket routing'
        },
        'BRIDGE_ROUTE': {
            'max_range': (55, 80),
            'min_range': (30, 55),
            'description': 'Bridge/tremolo routing'
        },
        'JACK_ROUTE': {
            'max_range': (25, 50),
            'min_range': (15, 40),
            'description': 'Output jack routing'
        }
    }

    ACOUSTIC_FEATURES = {
        'BODY_OUTLINE': {
            'max_range': (450, 560),
            'min_range': (320, 450),
            'description': 'Acoustic guitar body outline'
        },
        'D_HOLE': {
            # Selmer/Maccaferri D-shaped soundhole: ~200x100mm
            'max_range': (180, 230),
            'min_range': (80, 120),
            'description': 'D-shaped soundhole (Selmer/Maccaferri)'
        },
        'SOUNDHOLE': {
            # Standard round soundhole: ~100mm diameter
            'max_range': (90, 120),
            'min_range': (90, 120),
            'description': 'Round soundhole'
        },
        'F_HOLE': {
            # Archtop F-holes: ~150x40mm each
            'max_range': (130, 180),
            'min_range': (30, 55),
            'description': 'F-hole (archtop)'
        },
        'NECK_PROFILE': {
            # Neck side views: ~180-200mm long, 80-120mm wide area
            'max_range': (160, 210),
            'min_range': (70, 130),
            'description': 'Neck profile/cross-section'
        },
        'TAILPIECE': {
            # Selmer/archtop tailpiece: ~130-150mm long
            'max_range': (120, 160),
            'min_range': (35, 60),
            'description': 'Tailpiece area'
        },
        'BRIDGE': {
            # Acoustic bridge: ~80-100mm wide, 60-90mm area
            'max_range': (80, 110),
            'min_range': (55, 90),
            'description': 'Bridge'
        },
        'ROSETTE': {
            # Decorative rosette ring: ~65-80mm
            'max_range': (60, 90),
            'min_range': (60, 90),
            'description': 'Rosette decoration'
        },
        'PICKGUARD': {
            # Floating or attached pickguard
            'max_range': (100, 160),
            'min_range': (60, 100),
            'description': 'Pickguard'
        },
        'BRACING': {
            # X-bracing, ladder bracing, etc: long thin pieces
            'max_range': (200, 400),
            'min_range': (10, 45),
            'description': 'Bracing pattern'
        },
        'BRIDGE_PLATE': {
            'max_range': (140, 180),
            'min_range': (30, 50),
            'description': 'Bridge plate reinforcement'
        },
        'HEEL_BLOCK': {
            'max_range': (60, 100),
            'min_range': (40, 70),
            'description': 'Neck heel block'
        }
    }

    def __init__(self, instrument_type: str = 'electric', strict: bool = False):
        """
        Initialize classifier for specific instrument type.

        Args:
            instrument_type: 'electric', 'acoustic', or 'auto'
            strict: If True, classify into specific features. If False, use broad size categories.
        """
        self.instrument_type = instrument_type
        self.strict = strict
        self.features = self.ELECTRIC_FEATURES if instrument_type == 'electric' else self.ACOUSTIC_FEATURES

    def classify_contour(
        self,
        contour: np.ndarray,
        mm_per_px: float
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Classify a contour based on its dimensions.

        Args:
            contour: OpenCV contour array
            mm_per_px: Conversion factor from pixels to mm

        Returns:
            Tuple of (category_name, metadata_dict)
        """
        x, y, w, h = cv2.boundingRect(contour)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        area = cv2.contourArea(contour)

        max_dim = max(w_mm, h_mm)
        min_dim = min(w_mm, h_mm)

        metadata = {
            'width_mm': w_mm,
            'height_mm': h_mm,
            'max_dim': max_dim,
            'min_dim': min_dim,
            'area': area,
            'points': len(contour),
            'bbox': (x, y, w, h)
        }

        # Calculate aspect ratio for better classification
        aspect_ratio = max_dim / min_dim if min_dim > 0 else 1.0
        metadata['aspect_ratio'] = aspect_ratio

        # Non-strict mode: use broad size categories to capture ALL features
        if not self.strict:
            if max_dim > 400:
                return 'BODY', metadata
            elif max_dim > 150:
                return 'LARGE_FEATURE', metadata
            elif max_dim > 80:
                return 'MEDIUM_FEATURE', metadata
            elif max_dim > 40:
                return 'SMALL_FEATURE', metadata
            else:
                return 'DETAIL', metadata

        # Strict mode: try to match specific feature definitions
        for feature_name, ranges in self.features.items():
            max_range = ranges['max_range']
            min_range = ranges['min_range']

            # Check basic size match
            if not (max_range[0] <= max_dim <= max_range[1] and
                    min_range[0] <= min_dim <= min_range[1]):
                continue

            # Check aspect ratio if specified
            if 'aspect_range' in ranges:
                aspect_range = ranges['aspect_range']
                if not (aspect_range[0] <= aspect_ratio <= aspect_range[1]):
                    continue

            metadata['description'] = ranges['description']
            return feature_name, metadata

        # Strict mode fallback: classify unknown by size
        if max_dim > 300:
            return 'LARGE_UNKNOWN', metadata
        elif max_dim > 100:
            return 'MEDIUM_UNKNOWN', metadata
        elif max_dim > 30:
            return 'SMALL_FEATURE', metadata
        else:
            return 'TINY', metadata

    def classify_all(
        self,
        contours: List[np.ndarray],
        mm_per_px: float,
        min_area: float = 500
    ) -> Dict[str, List[Dict]]:
        """
        Classify all contours and group by category.

        Args:
            contours: List of OpenCV contours
            mm_per_px: Pixels to mm conversion
            min_area: Minimum contour area to consider

        Returns:
            Dict mapping category names to lists of {contour, metadata}
        """
        classified = {}

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            category, metadata = self.classify_contour(contour, mm_per_px)

            if category not in classified:
                classified[category] = []

            classified[category].append({
                'contour': contour,
                'metadata': metadata
            })

        # Sort each category by area (largest first)
        for category in classified:
            classified[category].sort(
                key=lambda x: x['metadata']['area'],
                reverse=True
            )

        return classified


# ---------------------------------------------------------------------------
# Geometry Detection
# ---------------------------------------------------------------------------

class GeometryDetector:
    """
    OpenCV-based edge detection and geometry extraction
    Converts raster blueprints to vector geometry
    """

    def __init__(self, dpi: int = 300):
        """
        Initialize geometry detector

        Args:
            dpi: Image resolution (dots per inch)
        """
        self.dpi = dpi
        self.mm_per_pixel = 25.4 / dpi  # Convert pixels to mm

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess blueprint image for edge detection

        Args:
            image: Input image (BGR or grayscale)

        Returns:
            Preprocessed grayscale image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Enhance contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)

        return enhanced

    def detect_edges(
        self,
        image: np.ndarray,
        low_threshold: int = 50,
        high_threshold: int = 150
    ) -> np.ndarray:
        """
        Detect edges using Canny edge detection

        Args:
            image: Preprocessed grayscale image
            low_threshold: Canny low threshold
            high_threshold: Canny high threshold

        Returns:
            Binary edge map
        """
        edges = cv2.Canny(image, low_threshold, high_threshold)

        # Dilate edges slightly to connect nearby segments
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        return edges

    def extract_contours(
        self,
        edges: np.ndarray,
        min_area: float = 100.0,
        epsilon_factor: float = 0.01
    ) -> List[np.ndarray]:
        """
        Extract and simplify contours from edge map

        Args:
            edges: Binary edge map
            min_area: Minimum contour area (pixels²)
            epsilon_factor: Approximation accuracy (lower = more detailed)

        Returns:
            List of simplified contours (each as Nx2 array of points)
        """
        # Find all contours
        contours, hierarchy = cv2.findContours(
            edges,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter and simplify contours
        simplified = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            # Approximate contour with fewer points (Douglas-Peucker)
            epsilon = epsilon_factor * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Convert to simple Nx2 array
            points = approx.reshape(-1, 2)
            simplified.append(points)

        logger.info(f"Extracted {len(simplified)} contours from {len(contours)} raw contours")
        return simplified

    def extract_contours_from_mask(
        self,
        mask: np.ndarray,
        min_area: float = 100.0,
        epsilon_factor: float = 0.005
    ) -> List[np.ndarray]:
        """
        Extract contours directly from a binary mask (no edge detection)

        Args:
            mask: Binary mask image
            min_area: Minimum contour area (pixels²)
            epsilon_factor: Approximation accuracy

        Returns:
            List of simplified contours
        """
        # Find contours directly from mask
        contours, hierarchy = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,  # Only outer contours
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter and simplify
        simplified = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            # Approximate
            epsilon = epsilon_factor * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            points = approx.reshape(-1, 2)
            simplified.append(points)

        # Sort by area (largest first)
        simplified.sort(key=lambda c: cv2.contourArea(c), reverse=True)

        logger.info(f"Extracted {len(simplified)} contours from mask")
        return simplified

    def detect_lines(
        self,
        edges: np.ndarray,
        threshold: int = 100,
        min_length: int = 50,
        max_gap: int = 10
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Detect straight lines using Hough transform

        Args:
            edges: Binary edge map
            threshold: Hough accumulator threshold
            min_length: Minimum line length (pixels)
            max_gap: Maximum gap between line segments

        Returns:
            List of line segments as ((x1, y1), (x2, y2))
        """
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=threshold,
            minLineLength=min_length,
            maxLineGap=max_gap
        )

        if lines is None:
            return []

        # Convert to simple tuple format
        line_segments = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            line_segments.append(((x1, y1), (x2, y2)))

        logger.info(f"Detected {len(line_segments)} line segments")
        return line_segments

    def detect_circles(
        self,
        edges: np.ndarray,
        min_radius: int = 10,
        max_radius: int = 100,
        param1: int = 50,
        param2: int = 30
    ) -> List[Tuple[int, int, int]]:
        """
        Detect circles using Hough circle transform

        Args:
            edges: Binary edge map
            min_radius: Minimum circle radius
            max_radius: Maximum circle radius
            param1: Canny edge threshold for Hough
            param2: Accumulator threshold for circle centers

        Returns:
            List of (x, y, radius) circles
        """
        circles = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius
        )

        if circles is None:
            return []

        circles = np.round(circles[0, :]).astype("int")
        logger.info(f"Detected {len(circles)} circles")
        return [(x, y, r) for (x, y, r) in circles]

    def pixels_to_mm(self, points: np.ndarray) -> np.ndarray:
        """
        Convert pixel coordinates to millimeters

        Args:
            points: Nx2 array of (x, y) pixel coordinates

        Returns:
            Nx2 array of (x, y) mm coordinates
        """
        return points * self.mm_per_pixel

    def apply_scale_correction(
        self,
        points: np.ndarray,
        scale_factor: float
    ) -> np.ndarray:
        """
        Apply scale correction to geometry

        Args:
            points: Nx2 array of coordinates
            scale_factor: Scaling multiplier (e.g., 1.2 = 120%)

        Returns:
            Scaled coordinates
        """
        return points * scale_factor


# ---------------------------------------------------------------------------
# Contour Selection
# ---------------------------------------------------------------------------

def select_primary_contour(
    contours: List[np.ndarray],
    image_shape: Tuple[int, int],
    instrument_type: str = 'guitar',
    min_area_ratio: float = 0.05,
    max_area_ratio: float = 0.8
) -> Optional[np.ndarray]:
    """
    Select the most likely body contour using instrument-specific heuristics

    Args:
        contours: List of contour arrays
        image_shape: (height, width) of source image
        instrument_type: Type of instrument for heuristics
        min_area_ratio: Minimum contour area as ratio of image area
        max_area_ratio: Maximum contour area as ratio of image area

    Returns:
        Best contour or None if no suitable candidate
    """
    if not contours:
        return None

    img_h, img_w = image_shape
    img_area = img_h * img_w

    scores = []

    for contour in contours:
        score = 0
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        # Skip if outside area bounds
        area_ratio = area / img_area
        if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
            continue

        # Heuristic 1: Reasonable size
        if 0.1 < area_ratio < 0.6:
            score += 20

        # Heuristic 2: Bounding box aspect ratio
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = max(w, h) / (min(w, h) + 1)

        if instrument_type == 'guitar':
            # Guitar bodies are typically 1.3-2.0 aspect ratio
            if 1.3 < aspect_ratio < 2.5:
                score += 25

        # Heuristic 3: Smoothness (circularity)
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if 0.3 < circularity < 0.8:  # Not too round, not too jagged
                score += 15

        # Heuristic 4: Convexity (guitars have cutaways = lower convexity)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            convexity = area / hull_area
            if 0.7 < convexity < 0.98:  # Has some concavities
                score += 15

        # Heuristic 5: Position (prefer centered contours)
        center_x, center_y = img_w / 2, img_h / 2
        contour_center_x = x + w / 2
        contour_center_y = y + h / 2

        distance_from_center = np.sqrt(
            (contour_center_x - center_x) ** 2 +
            (contour_center_y - center_y) ** 2
        )
        max_distance = np.sqrt(center_x ** 2 + center_y ** 2)

        if distance_from_center < max_distance * 0.3:
            score += 10

        # Heuristic 6: Point count (smooth curves have more points)
        if len(contour) > 20:
            score += 10

        scores.append((score, contour, area))

    if not scores:
        logger.warning("No contours passed selection criteria")
        return contours[0] if contours else None  # Fallback to largest

    # Return highest scoring
    best = max(scores, key=lambda x: x[0])
    logger.info(f"Selected contour with score {best[0]}, area {best[2]:.0f}")
    return best[1]


# ---------------------------------------------------------------------------
# Phase 2 Vectorizer
# ---------------------------------------------------------------------------

class Phase2Vectorizer:
    """
    Phase 2 vectorizer with intelligent geometry reconstruction
    Combines AI dimensions with OpenCV-detected geometry
    Now with color filtering support!
    """

    # Default layer mapping for DXF export
    DEFAULT_LAYER_MAP = {
        'red': 'BODY',
        'blue': 'DIMENSIONS',
        'green': 'HIDDEN',
        'yellow': 'FEATURES',
        'cyan': 'ELECTRICAL',
        'magenta': 'CUTS',
        'black': 'OUTLINE',
        'gray': 'GRID',
        'full': 'GEOMETRY',
        'custom': 'GEOMETRY'
    }

    def __init__(self, units: str = "mm", color_tolerance: int = 30, dpi: int = 300):
        """
        Initialize Phase 2 vectorizer

        Args:
            units: Target units (mm or inch)
            color_tolerance: Color matching tolerance for filtering
            dpi: DPI for PDF rasterization and coordinate conversion
        """
        self.units = units
        self.dpi = dpi
        self.detector = GeometryDetector(dpi=dpi)
        self.color_filter = ColorFilter(tolerance=color_tolerance)
        self.color_tolerance = color_tolerance

    def analyze_and_vectorize(
        self,
        source_path: str,
        analysis_data: Dict = None,
        output_dir: str = ".",
        scale_factor: float = 1.0,
        colors_to_extract: Optional[List[Union[str, Tuple[int, int, int]]]] = None,
        layer_map: Optional[Dict[str, str]] = None,
        page_num: int = 0,
        select_largest: bool = True,
        extraction_mode: str = 'auto',
        instrument_type: str = 'electric',
        dark_threshold: Union[int, str] = 100,
        simplify_tolerance: float = 0.1,
        gap_close_size: int = 0
    ) -> Dict[str, Any]:
        """
        Full pipeline with multiple extraction modes.

        Args:
            source_path: Path to PDF or image file
            analysis_data: AI analysis results (optional)
            output_dir: Directory for output files
            scale_factor: Scale correction multiplier
            colors_to_extract: List of colors to extract (for 'color' mode)
            layer_map: Custom mapping of colors to DXF layers
            page_num: Page number for PDFs (0-indexed)
            select_largest: If True, only export the largest contour per layer
            extraction_mode: 'auto', 'guitar', 'color', or 'simple'
                - 'auto': Uses 'guitar' if no colors specified, else 'color'
                - 'guitar': Extract and classify guitar-specific features
                - 'color': Extract by color layers
                - 'simple': Basic dark line extraction without classification
            instrument_type: 'electric' or 'acoustic' (for 'guitar' mode)
            dark_threshold: Threshold for dark line extraction (0-255), or 'auto' to
                           automatically detect based on image analysis
            simplify_tolerance: Contour simplification tolerance in mm
            gap_close_size: Morphological closing kernel size to bridge gaps in lines
                - 0: Disabled (default)
                - 5: Recommended for blueprints with small gaps
                - 7-9: For blueprints with larger gaps

        Returns:
            Dict with paths to generated files and layer statistics
        """
        if analysis_data is None:
            analysis_data = {}

        # Load image (handles PDF and image formats)
        image = load_input(source_path, page_num=page_num, dpi=self.dpi)
        height, width = image.shape[:2]
        logger.info(f"Loaded source: {width}x{height} pixels")

        # Use default layer map if none provided
        if layer_map is None:
            layer_map = self.DEFAULT_LAYER_MAP.copy()

        # Determine extraction mode
        if extraction_mode == 'auto':
            if colors_to_extract:
                extraction_mode = 'color'
            else:
                extraction_mode = 'guitar'

        # Extract geometry based on mode
        if extraction_mode == 'guitar':
            logger.info(f"Guitar feature extraction ({instrument_type})")
            layers_geometry = self._extract_guitar_features(
                image,
                scale_factor,
                instrument_type=instrument_type,
                dark_threshold=dark_threshold,
                simplify_tolerance=simplify_tolerance,
                gap_close_size=gap_close_size
            )
        elif extraction_mode == 'color' and colors_to_extract:
            logger.info(f"Color-filtered extraction for: {colors_to_extract}")
            layers_geometry = self._extract_by_color(
                image, colors_to_extract, scale_factor, select_largest
            )
        else:
            logger.info("Full-image extraction (no color filtering)")
            layers_geometry = self._extract_full_image(image, scale_factor)

        # Generate outputs
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Generate filenames
        source_name = Path(source_path).stem
        svg_path = str(output_dir_path / f"{source_name}_geometry.svg")
        dxf_path = str(output_dir_path / f"{source_name}_geometry.dxf")

        # Export
        self._export_svg_with_layers(
            svg_path,
            layers_geometry,
            analysis_data,
            image.shape[:2]
        )

        self._export_dxf_with_layers(
            dxf_path,
            layers_geometry,
            analysis_data,
            layer_map
        )

        # Compile statistics
        stats = {
            "svg": svg_path,
            "dxf": dxf_path,
            "source": source_path,
            "page": page_num,
            "image_size": (width, height),
            "layers": {}
        }

        for layer_name, geometry in layers_geometry.items():
            stats["layers"][layer_name] = {
                "contours": len(geometry.get("contours", [])),
                "lines": len(geometry.get("lines", [])),
                "circles": len(geometry.get("circles", []))
            }

        stats["total_contours"] = sum(l["contours"] for l in stats["layers"].values())
        stats["total_lines"] = sum(l["lines"] for l in stats["layers"].values())

        logger.info(f"Complete: {stats['total_contours']} contours, {stats['total_lines']} lines")

        return stats

    def _extract_by_color(
        self,
        image: np.ndarray,
        colors: List[Union[str, Tuple[int, int, int]]],
        scale_factor: float,
        select_largest: bool = True
    ) -> Dict[str, Dict]:
        """
        Extract geometry separately for each color layer
        """
        # Extract color masks
        color_masks = self.color_filter.extract_color_layers(
            image,
            colors,
            tolerance=self.color_tolerance
        )

        layers_geometry = {}

        for color_name, mask in color_masks.items():
            logger.info(f"Processing layer: {color_name}")

            # Extract contours directly from mask
            contours_px = self.detector.extract_contours_from_mask(mask, min_area=500)

            if not contours_px:
                logger.warning(f"No contours found for {color_name}")
                continue

            # Select primary contour if requested
            if select_largest and contours_px:
                primary = select_primary_contour(
                    contours_px,
                    image.shape[:2],
                    instrument_type='guitar'
                )
                if primary is not None:
                    contours_px = [primary]

            # Convert to mm
            contours_mm = []
            for contour in contours_px:
                contour_mm = self.detector.pixels_to_mm(contour.astype(np.float32))
                contour_mm = self.detector.apply_scale_correction(contour_mm, scale_factor)
                contours_mm.append(contour_mm)

            # Calculate dimensions
            if contours_mm:
                all_points = np.vstack(contours_mm)
                x_min, y_min = all_points.min(axis=0)
                x_max, y_max = all_points.max(axis=0)
                width_mm = x_max - x_min
                height_mm = y_max - y_min
                logger.info(f"Layer {color_name}: {width_mm:.1f} x {height_mm:.1f} mm")

            layers_geometry[color_name] = {
                "contours": contours_mm,
                "lines": [],
                "circles": []
            }

        return layers_geometry

    def _extract_full_image(
        self,
        image: np.ndarray,
        scale_factor: float
    ) -> Dict[str, Dict]:
        """
        Extract geometry from full image (no color filtering)
        """
        # Use dark line extraction
        mask = self.color_filter.extract_dark_lines(image, threshold=200)

        # Extract contours
        contours_px = self.detector.extract_contours_from_mask(mask, min_area=500)

        # Convert to mm
        contours_mm = []
        for contour in contours_px:
            contour_mm = self.detector.pixels_to_mm(contour.astype(np.float32))
            contour_mm = self.detector.apply_scale_correction(contour_mm, scale_factor)
            contours_mm.append(contour_mm)

        return {"full": {"contours": contours_mm, "lines": [], "circles": []}}

    def _extract_guitar_features(
        self,
        image: np.ndarray,
        scale_factor: float,
        instrument_type: str = 'electric',
        dark_threshold: Union[int, str] = 100,
        simplify_tolerance: float = 0.1,
        gap_close_size: int = 0,
        strict_classification: bool = False
    ) -> Dict[str, Dict]:
        """
        Extract and classify guitar-specific features from blueprint.

        Uses dark line extraction and size-based classification to identify:
        - Body outline
        - Pickguard
        - Neck pocket
        - Pickup routes
        - Control cavity
        - Bridge route
        - And other instrument-specific features

        Args:
            image: BGR image array
            scale_factor: Scale correction multiplier
            instrument_type: 'electric' or 'acoustic'
            dark_threshold: Threshold for dark line extraction (0-255), or 'auto' to
                           automatically detect the best threshold based on image analysis.
                           Use 'auto' for blueprints with unknown characteristics.
            simplify_tolerance: Douglas-Peucker simplification tolerance in mm
            gap_close_size: Morphological closing kernel size (0 = disabled, 5 = recommended for broken lines)
            strict_classification: If False (default), use broad size categories to capture all features.
                                   If True, attempt specific feature classification (may miss some features).

        Returns:
            Dict mapping layer names to geometry data
        """
        height, width = image.shape[:2]
        mm_per_px = 25.4 / self.dpi

        logger.info(f"Extracting guitar features ({instrument_type}) from {width}x{height}px image")

        # Extract dark lines (works better than color filtering for most blueprints)
        mask = self.color_filter.extract_dark_lines(
            image,
            threshold=dark_threshold,
            gap_close_size=gap_close_size
        )

        # Find all contours with hierarchy
        contours, hierarchy = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
        )
        logger.info(f"Found {len(contours)} raw contours")

        # Classify contours
        classifier = GuitarFeatureClassifier(instrument_type=instrument_type, strict=strict_classification)
        classified = classifier.classify_all(contours, mm_per_px, min_area=500)

        logger.info("Feature classification:")
        for cat, items in classified.items():
            if items and not cat.endswith('UNKNOWN') and cat != 'TINY':
                logger.info(f"  {cat}: {len(items)}")

        # Find body center for alignment
        body_cx, body_cy = 0, 0
        if 'BODY_OUTLINE' in classified and classified['BODY_OUTLINE']:
            body_item = classified['BODY_OUTLINE'][0]  # Largest
            pts = body_item['contour'].reshape(-1, 2)
            xs = [p[0] * mm_per_px for p in pts]
            ys = [(height - p[1]) * mm_per_px for p in pts]
            body_cx = (min(xs) + max(xs)) / 2
            body_cy = (min(ys) + max(ys)) / 2

        # Convert classified contours to mm and organize by layer
        layers_geometry = {}

        # Feature to layer mapping with max counts
        # Feature to layer mapping with max counts per feature type
        feature_config = {
            # Broad size categories (non-strict mode) - captures everything
            'BODY': {'layer': 'BODY', 'max_count': 2},
            'LARGE_FEATURE': {'layer': 'LARGE_FEATURE', 'max_count': 10},
            'MEDIUM_FEATURE': {'layer': 'MEDIUM_FEATURE', 'max_count': 15},
            'SMALL_FEATURE': {'layer': 'SMALL_FEATURE', 'max_count': 20},
            'DETAIL': {'layer': 'DETAIL', 'max_count': 20},
            # Electric guitar features (strict mode)
            'BODY_OUTLINE': {'layer': 'BODY_OUTLINE', 'max_count': 1},
            'PICKGUARD': {'layer': 'PICKGUARD', 'max_count': 1},
            'NECK_POCKET': {'layer': 'NECK_POCKET', 'max_count': 2},
            'PICKUP_ROUTE': {'layer': 'PICKUP_ROUTE', 'max_count': 4},
            'CONTROL_CAVITY': {'layer': 'CONTROL_CAVITY', 'max_count': 2},
            'BRIDGE_ROUTE': {'layer': 'BRIDGE_ROUTE', 'max_count': 2},
            'JACK_ROUTE': {'layer': 'JACK_ROUTE', 'max_count': 1},
            'RHYTHM_CIRCUIT': {'layer': 'RHYTHM_CIRCUIT', 'max_count': 1},
            # Acoustic guitar features (strict mode)
            'D_HOLE': {'layer': 'D_HOLE', 'max_count': 1},
            'SOUNDHOLE': {'layer': 'SOUNDHOLE', 'max_count': 1},
            'F_HOLE': {'layer': 'F_HOLE', 'max_count': 2},
            'NECK_PROFILE': {'layer': 'NECK_PROFILE', 'max_count': 4},
            'TAILPIECE': {'layer': 'TAILPIECE', 'max_count': 1},
            'BRIDGE': {'layer': 'BRIDGE', 'max_count': 2},
            'ROSETTE': {'layer': 'ROSETTE', 'max_count': 2},
            'BRACING': {'layer': 'BRACING', 'max_count': 10},
            'BRIDGE_PLATE': {'layer': 'BRIDGE_PLATE', 'max_count': 1},
            'HEEL_BLOCK': {'layer': 'HEEL_BLOCK', 'max_count': 1},
        }

        for feature_name, config in feature_config.items():
            if feature_name not in classified:
                continue

            layer_name = config['layer']
            max_count = config['max_count']
            items = classified[feature_name][:max_count]

            if not items:
                continue

            contours_mm = []
            for item in items:
                contour = item['contour']
                pts = contour.reshape(-1, 2)

                # Convert to mm, flip Y, center on body
                mm_pts = []
                for px, py in pts:
                    x_mm = px * mm_per_px - body_cx
                    y_mm = (height - py) * mm_per_px - body_cy
                    mm_pts.append([x_mm, y_mm])

                # Simplify contour
                pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
                simplified = cv2.approxPolyDP(pts_array, simplify_tolerance, closed=True)
                simplified = simplified.reshape(-1, 2)

                # Apply scale correction
                if scale_factor != 1.0:
                    simplified = simplified * scale_factor

                contours_mm.append(simplified.tolist())

                meta = item['metadata']
                logger.info(f"  {layer_name}: {meta['width_mm']:.0f}x{meta['height_mm']:.0f}mm, {len(simplified)} pts")

            layers_geometry[layer_name] = {
                "contours": contours_mm,
                "lines": [],
                "circles": []
            }

        return layers_geometry

    def _export_svg_with_layers(
        self,
        output_path: str,
        layers_geometry: Dict[str, Dict],
        analysis_data: Dict,
        image_shape: Tuple[int, int]
    ):
        """Export SVG with color-coded layers"""
        # Calculate canvas size
        all_points = []
        for layer_name, geometry in layers_geometry.items():
            for contour in geometry.get("contours", []):
                all_points.extend(contour)

        if not all_points:
            logger.warning("No geometry to export to SVG")
            return

        all_points = np.array(all_points)
        x_min, y_min = all_points.min(axis=0)
        x_max, y_max = all_points.max(axis=0)
        width_mm = (x_max - x_min) + 20
        height_mm = (y_max - y_min) + 20

        # Translate to origin
        offset = np.array([10 - x_min, 10 - y_min])

        # Create SVG
        dwg = svgwrite.Drawing(
            output_path,
            size=(f"{width_mm}mm", f"{height_mm}mm"),
            viewBox=f"0 0 {width_mm} {height_mm}"
        )

        # Layer colors
        layer_colors = {
            'red': '#FF0000',
            'blue': '#0000FF',
            'green': '#00FF00',
            'black': '#000000',
            'full': '#0000FF'
        }

        # Draw contours
        for layer_name, geometry in layers_geometry.items():
            color = layer_colors.get(layer_name, '#FF6600')

            for contour in geometry.get("contours", []):
                points = contour + offset
                if len(points) < 2:
                    continue

                path_data = f"M {points[0, 0]:.2f},{points[0, 1]:.2f} "
                for x, y in points[1:]:
                    path_data += f"L {x:.2f},{y:.2f} "
                path_data += "Z"

                dwg.add(dwg.path(
                    d=path_data,
                    stroke=color,
                    stroke_width=0.5,
                    fill="none"
                ))

        dwg.save()
        logger.info(f"Exported SVG: {output_path}")

    def _export_dxf_with_layers(
        self,
        output_path: str,
        layers_geometry: Dict[str, Dict],
        analysis_data: Dict,
        layer_map: Dict[str, str],
        dxf_version: DxfVersion = 'R12'
    ):
        """Export DXF with semantic layering"""
        # Create document
        version = validate_version(dxf_version)
        doc = create_document(version, setup=(version != 'R12'))
        msp = doc.modelspace()

        # Set units
        if version != 'R12':
            doc.header['$INSUNITS'] = dxf_units.MM

        # Layer colors
        layer_colors = {
            'BODY': 1,       # Red
            'OUTLINE': 7,    # White
            'DIMENSIONS': 2, # Yellow
            'GEOMETRY': 3    # Green
        }

        # Create layers and add geometry
        created_layers = set()

        for color_name, geometry in layers_geometry.items():
            # Get DXF layer name
            dxf_layer = layer_map.get(color_name, 'GEOMETRY')

            # Create layer if needed
            if dxf_layer not in created_layers:
                color_num = layer_colors.get(dxf_layer, 7)
                doc.layers.new(dxf_layer, dxfattribs={'color': color_num})
                created_layers.add(dxf_layer)

            # Add contours
            for contour in geometry.get("contours", []):
                points = [(float(x), float(y)) for x, y in contour]
                if len(points) < 3:
                    continue

                try:
                    add_polyline(msp, points, layer=dxf_layer, closed=True, version=version)
                except Exception as e:
                    logger.warning(f"Failed to add contour: {e}")

        # Save
        doc.saveas(output_path)
        logger.info(f"Exported DXF: {output_path}")


# ---------------------------------------------------------------------------
# Factory Function
# ---------------------------------------------------------------------------

def create_phase2_vectorizer(
    units: str = "mm",
    color_tolerance: int = 30,
    dpi: int = 300
) -> Phase2Vectorizer:
    """Factory function for Phase 2 vectorizer with color filtering"""
    return Phase2Vectorizer(units=units, color_tolerance=color_tolerance, dpi=dpi)


def extract_guitar_blueprint(
    source_path: str,
    output_dir: str = ".",
    page_num: int = 0,
    instrument_type: str = 'electric',
    dpi: int = 400,
    dark_threshold: Union[int, str] = 'auto',
    simplify_tolerance: float = 0.1,
    gap_close_size: int = 0
) -> Dict[str, Any]:
    """
    Convenience function for extracting guitar blueprints.

    This is the recommended entry point for guitar body/component extraction.
    Uses dark line extraction with guitar-specific feature classification.

    Args:
        source_path: Path to PDF or image file
        output_dir: Directory for output DXF and SVG files
        page_num: Page number for PDFs (0-indexed)
        instrument_type: 'electric' or 'acoustic'
        dpi: Resolution for PDF rasterization (400 recommended for detail)
        dark_threshold: Threshold for line extraction, or 'auto' (default) to
                       automatically detect based on image analysis.
                       - 'auto': Analyzes image to choose best method (recommended)
                       - 80-120: For blueprints with dark black lines
                       - 150-200: For blueprints with lighter/faint lines
        simplify_tolerance: Contour simplification in mm (0.1 = smooth curves)
        gap_close_size: Kernel size for closing gaps in broken lines
            - 0: Disabled (default, for clean blueprints)
            - 5: Recommended for blueprints with small gaps
            - 7-9: For blueprints with larger gaps or artifacts

    Returns:
        Dict with paths to generated files and feature statistics

    Example:
        >>> # Auto-detect threshold (recommended)
        >>> results = extract_guitar_blueprint(
        ...     'any_blueprint.pdf',
        ...     output_dir='./output'
        ... )
        >>> # Manual threshold for dark lines
        >>> results = extract_guitar_blueprint(
        ...     'jazzmaster_body.pdf',
        ...     output_dir='./output',
        ...     dark_threshold=100
        ... )
        >>> # Blueprint with broken lines and faint content
        >>> results = extract_guitar_blueprint(
        ...     'gibson_335.pdf',
        ...     output_dir='./output',
        ...     gap_close_size=5
        ... )
        >>> print(f"DXF: {results['dxf']}")
        >>> print(f"Features: {list(results['layers'].keys())}")
    """
    vectorizer = Phase2Vectorizer(units='mm', color_tolerance=30, dpi=dpi)

    return vectorizer.analyze_and_vectorize(
        source_path=source_path,
        output_dir=output_dir,
        page_num=page_num,
        extraction_mode='guitar',
        instrument_type=instrument_type,
        dark_threshold=dark_threshold,
        simplify_tolerance=simplify_tolerance,
        gap_close_size=gap_close_size
    )
