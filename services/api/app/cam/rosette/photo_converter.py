#!/usr/bin/env python3
"""
Rosette Photo to SVG Converter

Converts photographs or screenshots of rosette patterns into
clean SVG vector files suitable for CNC/laser cutting.

Workflow:
1. Load image (photo, screenshot, scan)
2. Preprocess (grayscale, threshold, clean)
3. Detect contours/edges
4. Convert to SVG paths
5. Optional: fit to circular rosette shape

Author: Luthier's ToolBox
Target: TXRX Labs January 2026

================================================================================
FUTURE ENHANCEMENTS ROADMAP
================================================================================

Phase 1: Performance & Scalability
----------------------------------
- [ ] GPU Acceleration (CUDA-enabled OpenCV)
      * Use cv2.cuda module for image processing on large files
      * Target: 10x speedup on 4K+ resolution images
      * Fallback to CPU when CUDA unavailable
      * Implementation: cv2.cuda.GpuMat for threshold/blur/contour ops
      
- [ ] Batch Processing Pipeline
      * Process multiple rosette variations in single run
      * Parallel processing with multiprocessing.Pool
      * Progress callbacks for UI integration
      * Output: ZIP archive with all converted files + manifest.json

Phase 2: Interactive Features  
-----------------------------
- [ ] Interactive Preview with Contour Adjustment Sliders
      * Real-time parameter tuning (threshold, blur, simplification)
      * Visual feedback showing detected contours overlaid on image
      * Accept/reject individual contours
      * Technology: Could use OpenCV highgui or integrate with Vue frontend
      * Sliders needed:
        - Threshold level (0-255)
        - Blur kernel size (1-15)
        - Minimum contour area
        - Simplification epsilon
        - Invert toggle

- [ ] Real-time Preview During Parameter Tuning
      * WebSocket connection for live updates
      * Debounced parameter changes (avoid overwhelming server)
      * Preview canvas with zoom/pan
      * Side-by-side: original vs. processed vs. vector output

Phase 3: Pattern Library Integration
------------------------------------
- [ ] Save Converted Patterns to Library
      * Database storage (SQLite or PostgreSQL)
      * Pattern metadata: name, source, style_tag, date, author
      * Thumbnail generation for gallery view
      * Tags/categories: "Torres", "Spanish", "Modern", etc.
      * Search by style, date range, complexity score
      
- [ ] Pattern Versioning
      * Track edits to converted patterns
      * Compare versions side-by-side
      * Rollback capability

- [ ] Export/Import Pattern Collections
      * Shareable pattern packs
      * Include original images + conversion settings
      * Compatibility with RMOS Art Studio library

Phase 4: Advanced Processing
----------------------------
- [ ] AI-Assisted Contour Cleanup
      * Use ML model to identify "noise" vs. "pattern" contours
      * Auto-remove UI elements from screenshots
      * Suggest optimal threshold based on image analysis
      
- [ ] Pattern Symmetry Detection & Enforcement
      * Detect rotational/mirror symmetry in pattern
      * Option to "perfect" near-symmetric patterns
      * Generate full pattern from partial capture

- [ ] Color Separation for Multi-Material Patterns
      * Detect distinct color regions
      * Output separate layers per color/material
      * BOM generation: area per color → material requirements

- [ ] Edge Enhancement Modes
      * Canny edge detection option
      * Morphological operations (dilate/erode) for cleanup
      * Adaptive thresholding with multiple block sizes

Phase 5: Integration & API
--------------------------
- [ ] REST API Endpoints
      * POST /api/convert/photo-to-svg
      * POST /api/convert/batch
      * GET /api/patterns/{id}/preview
      * WebSocket /ws/convert/realtime
      
- [ ] CLI Enhancements
      * --watch mode for auto-convert on file change
      * --preset flag for saved conversion profiles
      * --output-format=[svg,dxf,json,all]

- [ ] RMOS Integration
      * Direct pipeline to Art Studio pattern library
      * Feasibility scoring on converted patterns
      * Auto-suggest ring dimensions based on pattern aspect ratio

================================================================================
IMPLEMENTATION PRIORITY (for TXRX Labs January 2026)
================================================================================

HIGH PRIORITY (MVP):
1. Batch processing - handle multiple video screenshots efficiently
2. Pattern library save - store converted patterns for reuse
3. Basic preview - show before/after in UI

MEDIUM PRIORITY (v1.1):
4. Interactive sliders - tune conversion parameters visually
5. Color separation - multi-material pattern support
6. REST API - enable frontend integration

LOW PRIORITY (v2.0):
7. GPU acceleration - only needed for very large images
8. AI cleanup - requires training data collection first
9. Real-time WebSocket preview - nice-to-have polish

================================================================================
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional, Literal
from datetime import datetime
import math
import json


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
    """
    Converts photos/images of rosette patterns to SVG.
    
    Optimized for:
    - Screenshots from videos
    - Photos of existing rosettes
    - Scanned drawings/sketches
    - Pattern tiles
    """
    
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
        """
        Preprocess image for contour detection.
        
        Steps:
        1. Convert to grayscale
        2. Apply Gaussian blur
        3. Threshold to binary
        4. Optional inversion
        """
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
        """
        Warp paths to fit within a circular ring.
        
        Maps rectangular pattern to circular band using
        polar coordinate transformation.
        """
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
        """
        Full conversion pipeline.
        
        Args:
            image_path: Path to input image
            output_svg: Optional SVG output path
            output_dxf: Optional DXF output path
        
        Returns:
            Dictionary with conversion results
        """
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
    """
    Convenience function for photo to SVG conversion.
    
    Args:
        image_path: Input image path
        output_path: Output SVG path (or DXF if ends with .dxf)
        output_width_mm: Target width in mm
        fit_to_ring: Warp to circular ring shape
        ring_inner_mm: Inner ring diameter if fitting
        ring_outer_mm: Outer ring diameter if fitting
        simplify: Path simplification (higher = simpler)
        invert: Invert black/white
    
    Returns:
        Conversion result dictionary
    """
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


# ============================================================================
# BATCH PROCESSING
# ============================================================================

@dataclass
class BatchJob:
    """A single job in a batch processing queue."""
    input_path: str
    output_svg: Optional[str] = None
    output_dxf: Optional[str] = None
    settings: Optional[ConversionSettings] = None
    status: Literal["pending", "processing", "complete", "error"] = "pending"
    result: Optional[dict] = None
    error_message: Optional[str] = None


@dataclass
class BatchResult:
    """Results from batch processing."""
    total_jobs: int
    successful: int
    failed: int
    jobs: List[BatchJob]
    output_directory: str
    manifest_path: Optional[str] = None
    zip_path: Optional[str] = None
    processing_time_sec: float = 0.0


class BatchProcessor:
    """
    Batch processing for multiple rosette images.
    
    Features:
    - Process multiple images in single run
    - Parallel processing with multiprocessing
    - Progress callbacks for UI integration
    - ZIP archive output with manifest
    - Consistent settings across batch or per-file settings
    """
    
    def __init__(self, 
                 default_settings: Optional[ConversionSettings] = None,
                 output_dir: str = "./batch_output",
                 parallel: bool = True,
                 max_workers: int = 4):
        """
        Initialize batch processor.
        
        Args:
            default_settings: Default conversion settings for all jobs
            output_dir: Directory for output files
            parallel: Enable parallel processing
            max_workers: Maximum parallel workers (if parallel=True)
        """
        self.default_settings = default_settings or ConversionSettings()
        self.output_dir = Path(output_dir)
        self.parallel = parallel
        self.max_workers = max_workers
        self.jobs: List[BatchJob] = []
        self._progress_callback = None
    
    def set_progress_callback(self, callback):
        """
        Set callback for progress updates.
        
        Callback signature: callback(current: int, total: int, job: BatchJob)
        """
        self._progress_callback = callback
    
    def add_file(self, 
                 input_path: str,
                 output_name: Optional[str] = None,
                 settings: Optional[ConversionSettings] = None,
                 output_formats: List[str] = ["svg"]) -> BatchJob:
        """
        Add a single file to the batch queue.
        
        Args:
            input_path: Path to input image
            output_name: Base name for output (without extension)
            settings: Custom settings for this file (or use default)
            output_formats: List of output formats ["svg", "dxf"]
        
        Returns:
            The created BatchJob
        """
        input_path = str(Path(input_path).resolve())
        
        if output_name is None:
            output_name = Path(input_path).stem + "_converted"
        
        job = BatchJob(
            input_path=input_path,
            output_svg=f"{output_name}.svg" if "svg" in output_formats else None,
            output_dxf=f"{output_name}.dxf" if "dxf" in output_formats else None,
            settings=settings,
        )
        
        self.jobs.append(job)
        return job
    
    def add_directory(self,
                      directory: str,
                      pattern: str = "*.png",
                      recursive: bool = False,
                      settings: Optional[ConversionSettings] = None,
                      output_formats: List[str] = ["svg"]) -> List[BatchJob]:
        """
        Add all matching files from a directory.
        
        Args:
            directory: Directory to scan
            pattern: Glob pattern for matching files
            recursive: Search subdirectories
            settings: Custom settings for all files
            output_formats: Output formats for all files
        
        Returns:
            List of created BatchJobs
        """
        dir_path = Path(directory)
        
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
        
        # Also match common image extensions
        extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp"]
        if pattern == "*.png":
            for ext in extensions:
                if recursive:
                    files.extend(dir_path.rglob(ext))
                else:
                    files.extend(dir_path.glob(ext))
        
        # Remove duplicates
        files = list(set(files))
        
        jobs = []
        for file_path in sorted(files):
            job = self.add_file(
                str(file_path),
                settings=settings,
                output_formats=output_formats,
            )
            jobs.append(job)
        
        return jobs
    
    def add_files(self,
                  file_paths: List[str],
                  settings: Optional[ConversionSettings] = None,
                  output_formats: List[str] = ["svg"]) -> List[BatchJob]:
        """
        Add multiple specific files.
        
        Args:
            file_paths: List of file paths
            settings: Custom settings for all files
            output_formats: Output formats
        
        Returns:
            List of created BatchJobs
        """
        jobs = []
        for path in file_paths:
            job = self.add_file(path, settings=settings, output_formats=output_formats)
            jobs.append(job)
        return jobs
    
    def _process_single_job(self, job: BatchJob) -> BatchJob:
        """Process a single job (used by both serial and parallel processing)."""
        job.status = "processing"
        
        try:
            settings = job.settings or self.default_settings
            converter = RosettePhotoConverter(settings)
            
            # Determine output paths
            output_svg = None
            output_dxf = None
            
            if job.output_svg:
                output_svg = str(self.output_dir / job.output_svg)
            if job.output_dxf:
                output_dxf = str(self.output_dir / job.output_dxf)
            
            # Run conversion
            result = converter.convert(
                job.input_path,
                output_svg=output_svg,
                output_dxf=output_dxf,
            )
            
            job.result = result
            job.status = "complete"
            
        except (ValueError, TypeError, IOError, OSError) as e:
            job.status = "error"
            job.error_message = str(e)
        
        return job
    
    def process(self, 
                create_zip: bool = True,
                create_manifest: bool = True) -> BatchResult:
        """
        Process all jobs in the queue.
        
        Args:
            create_zip: Create ZIP archive of all outputs
            create_manifest: Create JSON manifest file
        
        Returns:
            BatchResult with all job outcomes
        """
        import time
        start_time = time.time()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        total = len(self.jobs)
        
        if self.parallel and total > 1:
            # Parallel processing
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._process_single_job, job): job 
                          for job in self.jobs}
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    job = futures[future]
                    
                    if self._progress_callback:
                        self._progress_callback(completed, total, job)
        else:
            # Serial processing
            for i, job in enumerate(self.jobs):
                self._process_single_job(job)
                
                if self._progress_callback:
                    self._progress_callback(i + 1, total, job)
        
        # Count results
        successful = sum(1 for j in self.jobs if j.status == "complete")
        failed = sum(1 for j in self.jobs if j.status == "error")
        
        processing_time = time.time() - start_time
        
        result = BatchResult(
            total_jobs=total,
            successful=successful,
            failed=failed,
            jobs=self.jobs,
            output_directory=str(self.output_dir),
            processing_time_sec=round(processing_time, 2),
        )
        
        # Create manifest
        if create_manifest:
            manifest = self._create_manifest(result)
            manifest_path = self.output_dir / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            result.manifest_path = str(manifest_path)
        
        # Create ZIP archive
        if create_zip:
            zip_path = self._create_zip_archive(result)
            result.zip_path = zip_path
        
        return result
    
    def _create_manifest(self, result: BatchResult) -> dict:
        """Create JSON manifest of batch processing results."""
        return {
            "batch_info": {
                "total_jobs": result.total_jobs,
                "successful": result.successful,
                "failed": result.failed,
                "processing_time_sec": result.processing_time_sec,
                "output_directory": result.output_directory,
                "created_at": datetime.now().isoformat(),
            },
            "default_settings": {
                "output_width_mm": self.default_settings.output_width_mm,
                "threshold_method": self.default_settings.threshold_method,
                "simplify_epsilon": self.default_settings.simplify_epsilon,
                "fit_to_circle": self.default_settings.fit_to_circle,
            },
            "jobs": [
                {
                    "input": job.input_path,
                    "output_svg": job.output_svg,
                    "output_dxf": job.output_dxf,
                    "status": job.status,
                    "contour_count": job.result.get("contour_count") if job.result else None,
                    "total_points": job.result.get("total_points") if job.result else None,
                    "error": job.error_message,
                }
                for job in self.jobs
            ],
        }
    
    def _create_zip_archive(self, result: BatchResult) -> str:
        """Create ZIP archive of all output files."""
        import zipfile
        
        zip_filename = f"rosette_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = self.output_dir / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all output files
            for job in self.jobs:
                if job.status == "complete":
                    if job.output_svg:
                        svg_path = self.output_dir / job.output_svg
                        if svg_path.exists():
                            zf.write(svg_path, job.output_svg)
                    
                    if job.output_dxf:
                        dxf_path = self.output_dir / job.output_dxf
                        if dxf_path.exists():
                            zf.write(dxf_path, job.output_dxf)
            
            # Add manifest
            if result.manifest_path:
                zf.write(result.manifest_path, "manifest.json")
        
        return str(zip_path)
    
    def clear(self):
        """Clear all jobs from the queue."""
        self.jobs = []


def batch_convert(
    input_paths: List[str],
    output_dir: str = "./batch_output",
    output_width_mm: float = 100.0,
    output_formats: List[str] = ["svg", "dxf"],
    parallel: bool = True,
    fit_to_ring: bool = False,
    ring_inner_mm: float = 45.0,
    ring_outer_mm: float = 55.0,
    simplify: float = 1.5,
    create_zip: bool = True,
    progress_callback = None,
) -> BatchResult:
    """
    Convenience function for batch conversion.
    
    Args:
        input_paths: List of input image paths
        output_dir: Output directory
        output_width_mm: Target width in mm
        output_formats: List of formats ["svg", "dxf"]
        parallel: Enable parallel processing
        fit_to_ring: Warp patterns to ring shape
        ring_inner_mm: Inner ring diameter
        ring_outer_mm: Outer ring diameter
        simplify: Path simplification level
        create_zip: Create ZIP archive
        progress_callback: Optional progress callback
    
    Returns:
        BatchResult with all outcomes
    
    Example:
        result = batch_convert(
            ["pattern1.png", "pattern2.jpg", "pattern3.png"],
            output_dir="./converted",
            output_formats=["svg", "dxf"],
        )
        print(f"Converted {result.successful}/{result.total_jobs} files")
        print(f"ZIP: {result.zip_path}")
    """
    settings = ConversionSettings(
        output_width_mm=output_width_mm,
        fit_to_circle=fit_to_ring,
        circle_inner_mm=ring_inner_mm,
        circle_outer_mm=ring_outer_mm,
        simplify_epsilon=simplify,
    )
    
    processor = BatchProcessor(
        default_settings=settings,
        output_dir=output_dir,
        parallel=parallel,
    )
    
    if progress_callback:
        processor.set_progress_callback(progress_callback)
    
    processor.add_files(input_paths, output_formats=output_formats)
    
    return processor.process(create_zip=create_zip)


def batch_convert_directory(
    directory: str,
    output_dir: str = "./batch_output",
    pattern: str = "*",
    recursive: bool = False,
    **kwargs,
) -> BatchResult:
    """
    Batch convert all images in a directory.
    
    Args:
        directory: Source directory
        output_dir: Output directory
        pattern: Glob pattern (default: all images)
        recursive: Search subdirectories
        **kwargs: Additional arguments passed to batch_convert
    
    Returns:
        BatchResult
    
    Example:
        result = batch_convert_directory(
            "./rosette_photos",
            output_dir="./converted",
            recursive=True,
        )
    """
    dir_path = Path(directory)
    
    # Find all image files
    extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp"]
    files = []
    
    for ext in extensions:
        if recursive:
            files.extend(dir_path.rglob(ext))
            files.extend(dir_path.rglob(ext.upper()))
        else:
            files.extend(dir_path.glob(ext))
            files.extend(dir_path.glob(ext.upper()))
    
    files = [str(f) for f in sorted(set(files))]
    
    if not files:
        print(f"No image files found in {directory}")
        return BatchResult(
            total_jobs=0,
            successful=0,
            failed=0,
            jobs=[],
            output_directory=output_dir,
        )
    
    return batch_convert(files, output_dir=output_dir, **kwargs)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rosette Photo to SVG/DXF Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file conversion
  python photo_to_svg_converter.py rosette.jpg
  python photo_to_svg_converter.py pattern.png output.svg
  
  # Batch conversion
  python photo_to_svg_converter.py --batch *.png
  python photo_to_svg_converter.py --batch-dir ./photos --recursive
  
  # With ring fitting
  python photo_to_svg_converter.py --fit-ring --inner 45 --outer 55 pattern.png
        """
    )
    
    # Input options
    parser.add_argument("inputs", nargs="*", help="Input image file(s)")
    parser.add_argument("--batch", action="store_true", help="Batch mode for multiple files")
    parser.add_argument("--batch-dir", type=str, help="Process all images in directory")
    parser.add_argument("--recursive", action="store_true", help="Search subdirectories")
    
    # Output options
    parser.add_argument("-o", "--output", type=str, help="Output path (single file) or directory (batch)")
    parser.add_argument("--format", nargs="+", default=["svg"], choices=["svg", "dxf"],
                       help="Output format(s)")
    parser.add_argument("--no-zip", action="store_true", help="Don't create ZIP archive (batch mode)")
    
    # Conversion settings
    parser.add_argument("--width", type=float, default=100.0, help="Output width in mm")
    parser.add_argument("--simplify", type=float, default=1.5, help="Path simplification (higher=simpler)")
    parser.add_argument("--invert", action="store_true", help="Invert black/white")
    parser.add_argument("--threshold", type=str, default="adaptive", 
                       choices=["otsu", "adaptive", "manual"], help="Threshold method")
    parser.add_argument("--threshold-value", type=int, default=127, help="Manual threshold value")
    
    # Ring fitting
    parser.add_argument("--fit-ring", action="store_true", help="Fit pattern to circular ring")
    parser.add_argument("--inner", type=float, default=45.0, help="Inner ring diameter (mm)")
    parser.add_argument("--outer", type=float, default=55.0, help="Outer ring diameter (mm)")
    
    # Processing
    parser.add_argument("--parallel", action="store_true", default=True, help="Enable parallel processing")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    # Progress callback for CLI
    def cli_progress(current, total, job):
        status = "✓" if job.status == "complete" else "✗" if job.status == "error" else "..."
        name = Path(job.input_path).name
        print(f"  [{current}/{total}] {status} {name}")
    
    # Determine mode
    if args.batch_dir:
        # Batch directory mode
        output_dir = args.output or "./batch_output"
        
        print(f"Batch converting directory: {args.batch_dir}")
        print(f"Output: {output_dir}")
        print(f"Formats: {', '.join(args.format)}")
        print()
        
        result = batch_convert_directory(
            args.batch_dir,
            output_dir=output_dir,
            recursive=args.recursive,
            output_formats=args.format,
            output_width_mm=args.width,
            simplify=args.simplify,
            fit_to_ring=args.fit_ring,
            ring_inner_mm=args.inner,
            ring_outer_mm=args.outer,
            parallel=args.parallel,
            create_zip=not args.no_zip,
            progress_callback=cli_progress,
        )
        
        print()
        print(f"✅ Batch complete!")
        print(f"   Total: {result.total_jobs}")
        print(f"   Success: {result.successful}")
        print(f"   Failed: {result.failed}")
        print(f"   Time: {result.processing_time_sec}s")
        if result.zip_path:
            print(f"   ZIP: {result.zip_path}")
        if result.manifest_path:
            print(f"   Manifest: {result.manifest_path}")
    
    elif args.batch or len(args.inputs) > 1:
        # Batch file mode
        if not args.inputs:
            print("Error: No input files specified")
            sys.exit(1)
        
        output_dir = args.output or "./batch_output"
        
        print(f"Batch converting {len(args.inputs)} files")
        print(f"Output: {output_dir}")
        print()
        
        result = batch_convert(
            args.inputs,
            output_dir=output_dir,
            output_formats=args.format,
            output_width_mm=args.width,
            simplify=args.simplify,
            fit_to_ring=args.fit_ring,
            ring_inner_mm=args.inner,
            ring_outer_mm=args.outer,
            parallel=args.parallel,
            create_zip=not args.no_zip,
            progress_callback=cli_progress,
        )
        
        print()
        print(f"✅ Batch complete!")
        print(f"   Success: {result.successful}/{result.total_jobs}")
        print(f"   Time: {result.processing_time_sec}s")
        if result.zip_path:
            print(f"   ZIP: {result.zip_path}")
    
    else:
        # Single file mode
        if not args.inputs:
            parser.print_help()
            sys.exit(1)
        
        input_path = args.inputs[0]
        output_path = args.output or Path(input_path).stem + "_converted.svg"
        
        print(f"Converting: {input_path}")
        print(f"Output: {output_path}")
        
        result = convert_photo_to_svg(
            input_path,
            output_path,
            output_width_mm=args.width,
            fit_to_ring=args.fit_ring,
            ring_inner_mm=args.inner,
            ring_outer_mm=args.outer,
            simplify=args.simplify,
            invert=args.invert,
        )
        
        print(f"✅ Conversion complete!")
        print(f"   Contours: {result['contour_count']}")
        print(f"   Points: {result['total_points']}")
