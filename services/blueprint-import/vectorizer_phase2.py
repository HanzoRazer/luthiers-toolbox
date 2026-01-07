"""
Phase 2 Vectorizer - Intelligent Geometry Reconstruction
Adds OpenCV edge detection, contour analysis, and DXF R12-R18 export
"""
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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


class Phase2Vectorizer:
    """
    Phase 2 vectorizer with intelligent geometry reconstruction
    Combines AI dimensions with OpenCV-detected geometry
    """
    
    def __init__(self, units: str = "mm"):
        """
        Initialize Phase 2 vectorizer
        
        Args:
            units: Target units (mm or inch)
        """
        self.units = units
        self.detector = GeometryDetector()
    
    def analyze_and_vectorize(
        self,
        image_path: str,
        analysis_data: Dict,
        output_dir: str,
        scale_factor: float = 1.0
    ) -> Dict[str, str]:
        """
        Full pipeline: edge detection → geometry extraction → export
        
        Args:
            image_path: Path to blueprint image
            analysis_data: AI analysis results
            output_dir: Directory for output files
            scale_factor: Scale correction multiplier
        
        Returns:
            Dict with paths to generated files
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Preprocess and detect edges
        preprocessed = self.detector.preprocess_image(image)
        edges = self.detector.detect_edges(preprocessed)
        
        # Extract geometry
        contours = self.detector.extract_contours(edges)
        lines = self.detector.detect_lines(edges)
        
        # Convert to mm coordinates
        contours_mm = [
            self.detector.apply_scale_correction(
                self.detector.pixels_to_mm(c),
                scale_factor
            )
            for c in contours
        ]
        
        lines_mm = [
            (
                tuple(self.detector.apply_scale_correction(
                    self.detector.pixels_to_mm(np.array([p1])),
                    scale_factor
                )[0]),
                tuple(self.detector.apply_scale_correction(
                    self.detector.pixels_to_mm(np.array([p2])),
                    scale_factor
                )[0])
            )
            for p1, p2 in lines
        ]
        
        # Generate outputs
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        svg_path = str(output_dir_path / "geometry.svg")
        dxf_path = str(output_dir_path / "geometry.dxf")
        
        self._export_svg_with_geometry(
            svg_path,
            contours_mm,
            lines_mm,
            analysis_data
        )
        
        self._export_dxf_r12(
            dxf_path,
            contours_mm,
            lines_mm,
            analysis_data
        )
        
        return {
            "svg": svg_path,
            "dxf": dxf_path,
            "contours": len(contours_mm),
            "lines": len(lines_mm)
        }
    
    def _export_svg_with_geometry(
        self,
        output_path: str,
        contours: List[np.ndarray],
        lines: List[Tuple],
        analysis_data: Dict
    ):
        """
        Export SVG with detected geometry
        
        Args:
            output_path: Output SVG path
            contours: List of contour point arrays (mm)
            lines: List of line segments (mm)
            analysis_data: AI analysis metadata
        """
        # Calculate canvas size from geometry
        all_points = []
        for contour in contours:
            all_points.extend(contour)
        for (x1, y1), (x2, y2) in lines:
            all_points.extend([(x1, y1), (x2, y2)])
        
        if not all_points:
            # Fallback to default size
            width_mm, height_mm = 300.0, 200.0
            offset = np.array([0, 0])
        else:
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
        
        # Add styles
        dwg.defs.add(dwg.style("""
            .contour { stroke: blue; stroke-width: 0.3; fill: none; }
            .line { stroke: red; stroke-width: 0.2; }
            .dimension { stroke: green; stroke-width: 0.15; stroke-dasharray: 2,2; }
        """))
        
        # Add metadata as description element (svgwrite doesn't have .comment())
        dwg.add(dwg.desc(f"Phase 2 Geometry - {len(contours)} contours, {len(lines)} lines. Scale: {analysis_data.get('scale', 'Unknown')}"))
        
        # Draw contours
        for contour in contours:
            points = contour + offset
            path_data = f"M {points[0, 0]},{points[0, 1]} "
            for x, y in points[1:]:
                path_data += f"L {x},{y} "
            path_data += "Z"  # Close path
            
            dwg.add(dwg.path(d=path_data, class_="contour"))
        
        # Draw lines
        for (x1, y1), (x2, y2) in lines:
            p1 = np.array([x1, y1]) + offset
            p2 = np.array([x2, y2]) + offset
            dwg.add(dwg.line(
                start=(p1[0]*mm, p1[1]*mm),
                end=(p2[0]*mm, p2[1]*mm),
                class_="line"
            ))
        
        dwg.save()
        logger.info(f"Exported SVG with geometry: {output_path}")
    
    def _export_dxf_r12(
        self,
        output_path: str,
        contours: List[np.ndarray],
        lines: List[Tuple],
        analysis_data: Dict,
        dxf_version: DxfVersion = 'R12'
    ):
        """
        Export DXF format for CAM compatibility (R12-R18)
        
        Args:
            output_path: Output DXF path
            contours: List of contour point arrays (mm)
            lines: List of line segments (mm)
            analysis_data: AI analysis metadata
            dxf_version: DXF version R12-R18 (default R12 for CAM compatibility)
        """
        # Validate and create document (R12 is the genesis of Luthier's ToolBox)
        version = validate_version(dxf_version)
        doc = create_document(version, setup=(version != 'R12'))
        msp = doc.modelspace()
        
        # Set units to millimeters (R13+ only)
        if version != 'R12':
            doc.header['$INSUNITS'] = dxf_units.MM
        
        # Create layers
        doc.layers.new('GEOMETRY', dxfattribs={'color': 3})  # Green
        doc.layers.new('LINES', dxfattribs={'color': 1})     # Red
        doc.layers.new('DIMENSIONS', dxfattribs={'color': 2}) # Yellow
        
        # Add contours (version-aware: LINE for R12, LWPOLYLINE for R13+)
        for idx, contour in enumerate(contours):
            points = [(float(x), float(y)) for x, y in contour]
            
            try:
                add_polyline(msp, points, layer='GEOMETRY', closed=True, version=version)
            except Exception as e:
                logger.warning(f"Failed to add contour {idx}: {e}")
        
        # Add lines
        for (x1, y1), (x2, y2) in lines:
            msp.add_line(
                (float(x1), float(y1), 0.0),
                (float(x2), float(y2), 0.0),
                dxfattribs={'layer': 'LINES'}
            )
        
        # Add dimension annotations from AI analysis
        dimensions = analysis_data.get('dimensions', [])
        for idx, dim in enumerate(dimensions[:10]):  # Limit to first 10
            label = dim.get('label', f'Dim{idx+1}')
            value = dim.get('value', 'N/A')
            
            # Add as text annotation
            msp.add_text(
                f"{label}: {value}",
                dxfattribs={
                    'layer': 'DIMENSIONS',
                    'height': 2.5,  # Text height in mm
                    'insert': (10, 10 + idx * 5, 0.0)
                }
            )
        
        # Save DXF
        doc.saveas(output_path)
        logger.info(f"Exported DXF {version} (CAM-compatible): {output_path} ({len(contours)} contours, {len(lines)} lines)")


def create_phase2_vectorizer(units: str = "mm") -> Phase2Vectorizer:
    """Factory function for Phase 2 vectorizer"""
    return Phase2Vectorizer(units=units)
