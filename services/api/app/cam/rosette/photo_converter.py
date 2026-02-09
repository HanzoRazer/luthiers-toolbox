#!/usr/bin/env python3
"""Rosette Photo to SVG Converter"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional, Literal
import math


@dataclass
class ConversionSettings:
    """Settings for photo to SVG conversion."""
    # Preprocessing
    blur_kernel: int = 5              # Gaussian blur size (odd number)
    threshold_method: Literal["otsu", "adaptive", "manual"] = "adaptive"
    manual_threshold: int = 127       # Used if threshold_method="manual"
    invert: bool = False              # Invert black/white
    
    # Contour detection
    min_contour_area: float = 100     # Minimum contour area in pixels
    max_contour_area: float = 1e8     # Maximum contour area
    simplify_epsilon: float = 1.0     # Path simplification (higher = simpler)
    
    # Output
    output_width_mm: float = 100.0    # Target output width
    center_on_origin: bool = True     # Center output at (0,0)
    fit_to_circle: bool = False       # Fit pattern to circular ring
    circle_inner_mm: float = 45.0     # Inner diameter if fitting
    circle_outer_mm: float = 55.0     # Outer diameter if fitting
    
    # Cleanup
    remove_background: bool = True    # Remove largest contour (background)
    close_paths: bool = True          # Close open contours


@dataclass 
class ContourPath:
    """A single contour path."""
    points: List[Tuple[float, float]]
    is_closed: bool
    area: float
    hierarchy_level: int = 0


class RosettePhotoConverter:
    """Converts photos/images of rosette patterns to SVG."""
    
    def __init__(self, settings: Optional[ConversionSettings] = None):
        self.settings = settings or ConversionSettings()
        self.original_image = None
        self.processed_image = None
        self.contours: List[ContourPath] = []
    
    def load_image(self, path: str) -> np.ndarray:
        """Load image from file."""
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Could not load image: {path}")
        self.original_image = img
        return img
    
    def load_from_array(self, array: np.ndarray) -> np.ndarray:
        """Load image from numpy array."""
        self.original_image = array
        return array
    
    def preprocess(self, img: Optional[np.ndarray] = None) -> np.ndarray:
        """Preprocess image for contour detection."""
        if img is None:
            img = self.original_image
        
        if img is None:
            raise ValueError("No image loaded")
        
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Apply blur to reduce noise
        if self.settings.blur_kernel > 1:
            kernel = self.settings.blur_kernel
            if kernel % 2 == 0:
                kernel += 1
            gray = cv2.GaussianBlur(gray, (kernel, kernel), 0)
        
        # Threshold
        if self.settings.threshold_method == "otsu":
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif self.settings.threshold_method == "adaptive":
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        else:  # manual
            _, binary = cv2.threshold(gray, self.settings.manual_threshold, 255, cv2.THRESH_BINARY)
        
        # Optional inversion
        if self.settings.invert:
            binary = cv2.bitwise_not(binary)
        
        self.processed_image = binary
        return binary
    
    def detect_contours(self, img: Optional[np.ndarray] = None) -> List[ContourPath]:
        """
        Detect contours in preprocessed image.
        """
        if img is None:
            img = self.processed_image
        
        if img is None:
            raise ValueError("No processed image - call preprocess() first")
        
        # Find contours with hierarchy
        contours, hierarchy = cv2.findContours(
            img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if hierarchy is None:
            hierarchy = np.array([[[-1, -1, -1, -1]]] * len(contours))
        
        paths = []
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            # Filter by area
            if area < self.settings.min_contour_area:
                continue
            if area > self.settings.max_contour_area:
                continue
            
            # Simplify contour
            epsilon = self.settings.simplify_epsilon
            simplified = cv2.approxPolyDP(contour, epsilon, True)
            
            # Extract points
            points = [(float(p[0][0]), float(p[0][1])) for p in simplified]
            
            # Determine hierarchy level
            h = hierarchy[0][i]
            level = 0
            parent = h[3]
            while parent != -1:
                level += 1
                parent = hierarchy[0][parent][3]
            
            paths.append(ContourPath(
                points=points,
                is_closed=self.settings.close_paths,
                area=area,
                hierarchy_level=level,
            ))
        
        # Sort by area (largest first)
        paths.sort(key=lambda p: p.area, reverse=True)
        
        # Remove background (largest contour) if requested
        if self.settings.remove_background and len(paths) > 1:
            paths = paths[1:]
        
        self.contours = paths
        return paths
    
    def normalize_paths(self, 
                       paths: Optional[List[ContourPath]] = None,
                       img_shape: Optional[Tuple[int, int]] = None) -> List[ContourPath]:
        """
        Normalize paths to target dimensions in mm.
        """
        if paths is None:
            paths = self.contours
        
        if not paths:
            return []
        
        # Get image dimensions for scaling
        if img_shape is None:
            if self.original_image is not None:
                img_shape = self.original_image.shape[:2]
            else:
                # Estimate from path bounds
                all_x = [p[0] for path in paths for p in path.points]
                all_y = [p[1] for path in paths for p in path.points]
                img_shape = (int(max(all_y)), int(max(all_x)))
        
        img_height, img_width = img_shape[:2]
        
        # Calculate scale factor
        scale = self.settings.output_width_mm / img_width
        
        # Calculate center offset
        if self.settings.center_on_origin:
            cx = img_width / 2
            cy = img_height / 2
        else:
            cx, cy = 0, 0
        
        # Transform paths
        normalized = []
        for path in paths:
            new_points = []
            for x, y in path.points:
                # Center and scale
                nx = (x - cx) * scale
                ny = (y - cy) * scale
                # Flip Y axis (image coords to CAD coords)
                ny = -ny
                new_points.append((nx, ny))
            
            normalized.append(ContourPath(
                points=new_points,
                is_closed=path.is_closed,
                area=path.area * scale * scale,
                hierarchy_level=path.hierarchy_level,
            ))
        
        return normalized
    
    def fit_to_ring(self, 
                    paths: List[ContourPath],
                    inner_r: float,
                    outer_r: float) -> List[ContourPath]:
        """Warp paths to fit within a circular ring."""
        if not paths:
            return []
        
        # Get bounds of all paths
        all_x = [p[0] for path in paths for p in path.points]
        all_y = [p[1] for path in paths for p in path.points]
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        width = max_x - min_x
        height = max_y - min_y
        
        if width == 0 or height == 0:
            return paths
        
        # Map to ring
        ring_width = outer_r - inner_r
        
        fitted = []
        for path in paths:
            new_points = []
            for x, y in path.points:
                # Normalize to [0, 1]
                nx = (x - min_x) / width  # 0-1 around circumference
                ny = (y - min_y) / height  # 0-1 radially
                
                # Map to polar coordinates
                theta = 2 * math.pi * nx
                r = inner_r + ny * ring_width
                
                # Convert to Cartesian
                px = r * math.cos(theta)
                py = r * math.sin(theta)
                
                new_points.append((px, py))
            
            fitted.append(ContourPath(
                points=new_points,
                is_closed=path.is_closed,
                area=path.area,
                hierarchy_level=path.hierarchy_level,
            ))
        
        return fitted
    
    def export_svg(self, 
                   paths: Optional[List[ContourPath]] = None,
                   title: str = "Rosette Pattern") -> str:
        """Export paths to SVG format."""
        if paths is None:
            paths = self.contours
        
        if not paths:
            return '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
        
        # Calculate bounds
        all_x = [p[0] for path in paths for p in path.points]
        all_y = [p[1] for path in paths for p in path.points]
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        padding = 5
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding
        
        svg_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg"',
            f'     viewBox="{min_x - padding} {min_y - padding} {width} {height}"',
            f'     width="{width}mm" height="{height}mm">',
            f'  <title>{title}</title>',
            '  <desc>Converted from photo by Luthier\'s ToolBox</desc>',
            '  <g fill="none" stroke="black" stroke-width="0.2">',
        ]
        
        for i, path in enumerate(paths):
            if len(path.points) < 2:
                continue
            
            # Build path data
            points_str = " ".join(f"{x:.3f},{y:.3f}" for x, y in path.points)
            
            if path.is_closed:
                svg_lines.append(f'    <polygon points="{points_str}" />')
            else:
                svg_lines.append(f'    <polyline points="{points_str}" />')
        
        svg_lines.extend([
            '  </g>',
            '</svg>',
        ])
        
        return "\n".join(svg_lines)
    
    def export_dxf(self, 
                   paths: Optional[List[ContourPath]] = None) -> str:
        """Export paths to DXF R12 format."""
        if paths is None:
            paths = self.contours
        
        lines = [
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER",
            "1", "AC1009",
            "9", "$INSUNITS",
            "70", "4",
            "0", "ENDSEC",
            "0", "SECTION",
            "2", "ENTITIES",
        ]
        
        for path in paths:
            if len(path.points) < 2:
                continue
            
            if path.is_closed:
                # POLYLINE
                lines.extend([
                    "0", "POLYLINE",
                    "8", "0",
                    "66", "1",
                    "70", "1",
                ])
                for x, y in path.points:
                    lines.extend([
                        "0", "VERTEX",
                        "8", "0",
                        "10", f"{x:.6f}",
                        "20", f"{y:.6f}",
                    ])
                lines.extend(["0", "SEQEND"])
            else:
                # LINE segments
                for i in range(len(path.points) - 1):
                    x1, y1 = path.points[i]
                    x2, y2 = path.points[i + 1]
                    lines.extend([
                        "0", "LINE",
                        "8", "0",
                        "10", f"{x1:.6f}",
                        "20", f"{y1:.6f}",
                        "11", f"{x2:.6f}",
                        "21", f"{y2:.6f}",
                    ])
        
        lines.extend([
            "0", "ENDSEC",
            "0", "EOF",
        ])
        
        return "\n".join(lines)
    
    def convert(self, 
                image_path: str,
                output_svg: Optional[str] = None,
                output_dxf: Optional[str] = None) -> dict:
        """Full conversion pipeline."""
        # Load
        self.load_image(image_path)
        
        # Preprocess
        self.preprocess()
        
        # Detect contours
        paths = self.detect_contours()
        
        # Normalize
        paths = self.normalize_paths(paths)
        
        # Optional: fit to ring
        if self.settings.fit_to_circle:
            paths = self.fit_to_ring(
                paths,
                self.settings.circle_inner_mm / 2,
                self.settings.circle_outer_mm / 2,
            )
        
        self.contours = paths
        
        # Export
        result = {
            "input": image_path,
            "contour_count": len(paths),
            "total_points": sum(len(p.points) for p in paths),
        }
        
        if output_svg:
            svg_content = self.export_svg(paths)
            with open(output_svg, 'w') as f:
                f.write(svg_content)
            result["svg_path"] = output_svg
        
        if output_dxf:
            dxf_content = self.export_dxf(paths)
            with open(output_dxf, 'w') as f:
                f.write(dxf_content)
            result["dxf_path"] = output_dxf
        
        return result


def convert_photo_to_svg(
    image_path: str,
    output_path: str,
    output_width_mm: float = 100.0,
    fit_to_ring: bool = False,
    ring_inner_mm: float = 45.0,
    ring_outer_mm: float = 55.0,
    simplify: float = 1.0,
    invert: bool = False,
) -> dict:
    """Convenience function for photo to SVG conversion."""
    settings = ConversionSettings(
        output_width_mm=output_width_mm,
        fit_to_circle=fit_to_ring,
        circle_inner_mm=ring_inner_mm,
        circle_outer_mm=ring_outer_mm,
        simplify_epsilon=simplify,
        invert=invert,
    )
    
    converter = RosettePhotoConverter(settings)
    
    output_svg = output_path if output_path.endswith('.svg') else None
    output_dxf = output_path if output_path.endswith('.dxf') else None
    
    if not output_svg and not output_dxf:
        output_svg = output_path + '.svg'
    
    return converter.convert(image_path, output_svg, output_dxf)


# ---------------------------------------------------------------------------
# Re-export batch processing API for backward compatibility
# ---------------------------------------------------------------------------

from .photo_batch import (  # noqa: E402, F401
    BatchJob,
    BatchResult,
    BatchProcessor,
    batch_convert,
    batch_convert_directory,
)

