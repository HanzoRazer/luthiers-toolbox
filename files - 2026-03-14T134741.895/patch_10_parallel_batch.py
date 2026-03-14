"""
PATCH 10 — Parallel Batch Processing (ThreadPoolExecutor)
==========================================================

Downstream of: PhotoVectorizerV2
Input:  list of image paths + kwargs
Output: list of PhotoExtractionResult (flat, multi-instrument images expanded)

Why ThreadPoolExecutor not ProcessPoolExecutor:
  - cv2 Mat objects are not picklable → ProcessPoolExecutor fails at serialization
  - The pipeline is I/O-bound at load/save stages and memory-bound at BG removal
  - ThreadPoolExecutor gives ~2–3x speedup on a 4-core machine for typical
    workshop batches (10–50 images) where disk I/O is the bottleneck
  - For CPU-heavy rembg/SAM inference, the GIL limits speedup — but GrabCut
    (the default) releases the GIL during C++ execution, so parallel still helps

Thread safety notes:
  - PhotoVectorizerV2 instances are NOT shared across threads
  - Each worker creates its own instance (avoids state corruption)
  - Output directories are per-image (avoids write collisions)
  - Logging is thread-safe in Python's standard logger

Integration:
  Add ParallelBatchProcessor alongside PhotoVectorizerV2, or wire directly
  into PhotoVectorizerV2 as batch_extract_parallel().

Author: The Production Shop
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result wrapper
# ---------------------------------------------------------------------------

@dataclass
class BatchResult:
    """Aggregated result from a parallel batch run."""
    total_inputs:    int
    total_outputs:   int
    succeeded:       int
    failed:          int
    skipped:         int
    elapsed_sec:     float
    results:         list    = field(default_factory=list)  # PhotoExtractionResult
    errors:          List[Dict[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Batch complete: {self.total_inputs} inputs → "
            f"{self.total_outputs} outputs",
            f"  Succeeded: {self.succeeded}   Failed: {self.failed}   "
            f"Skipped: {self.skipped}",
            f"  Elapsed:   {self.elapsed_sec:.1f}s  "
            f"({self.elapsed_sec/max(self.total_inputs,1):.1f}s/image avg)",
        ]
        if self.errors:
            lines.append("  Errors:")
            for e in self.errors:
                lines.append(f"    {e['path']}: {e['error']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Worker function (module-level so it is importable by threads)
# ---------------------------------------------------------------------------

def _process_one(
    path:         str,
    output_dir:   Optional[str],
    vectorizer_kwargs: Dict[str, Any],
    extra_kwargs: Dict[str, Any],
) -> tuple:
    """
    Worker: instantiate vectorizer + run extract() on one image.
    Returns (path, results_list, error_str_or_None).
    """
    try:
        # Import here so each thread gets a clean namespace
        # (avoids any shared mutable state in module-level objects)
        from photo_vectorizer_v2 import PhotoVectorizerV2, BGRemovalMethod, Unit

        bg_method_str = vectorizer_kwargs.get("bg_method", "auto")
        bg_map = {
            "auto":      BGRemovalMethod.AUTO,
            "grabcut":   BGRemovalMethod.GRABCUT,
            "rembg":     BGRemovalMethod.REMBG,
            "sam":       BGRemovalMethod.SAM,
            "threshold": BGRemovalMethod.THRESHOLD,
        }
        bg_method = bg_map.get(bg_method_str, BGRemovalMethod.AUTO)

        v = PhotoVectorizerV2(
            bg_method             = bg_method,
            simplify_tolerance_mm = vectorizer_kwargs.get("simplify_tolerance_mm", 0.3),
            min_contour_area_px   = vectorizer_kwargs.get("min_contour_area_px", 3000),
            dxf_version           = vectorizer_kwargs.get("dxf_version", "R12"),
            default_dpi           = vectorizer_kwargs.get("default_dpi", 300.0),
        )

        r = v.extract(path, output_dir=output_dir, **extra_kwargs)
        results = r if isinstance(r, list) else [r]
        return path, results, None

    except Exception as e:
        return path, [], str(e)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class ParallelBatchProcessor:
    """
    Process multiple instrument photos in parallel using threads.

    Parameters
    ----------
    max_workers       : number of parallel threads (default: 4)
    vectorizer_kwargs : constructor kwargs for PhotoVectorizerV2
                        (bg_method, simplify_tolerance_mm, etc.)
    on_complete       : optional callback(path, results, error) called per image
    """

    def __init__(
        self,
        max_workers:       int = 4,
        vectorizer_kwargs: Optional[Dict[str, Any]] = None,
        on_complete:       Optional[Callable] = None,
    ):
        self.max_workers       = max_workers
        self.vectorizer_kwargs = vectorizer_kwargs or {}
        self.on_complete       = on_complete

    # ------------------------------------------------------------------
    def process(
        self,
        source_paths:    List[Union[str, Path]],
        output_dir:      Optional[Union[str, Path]] = None,
        spec_name:       Optional[str]  = None,
        known_dimension_mm: Optional[float] = None,
        known_dimension_px: Optional[float] = None,
        export_svg:      bool = True,
        export_dxf:      bool = True,
        export_json:     bool = False,
        debug_images:    bool = False,
        correct_perspective: bool = True,
        skip_existing:   bool = False,
    ) -> BatchResult:
        """
        Process a list of images in parallel.

        Parameters
        ----------
        source_paths      : list of image file paths
        output_dir        : base output directory (None = each file's parent)
        spec_name         : instrument spec for calibration (e.g. "dreadnought")
        known_dimension_mm: known body height in mm (for manual calibration)
        known_dimension_px: pixel span of known dimension
        export_svg        : write SVG files
        export_dxf        : write DXF files
        export_json       : write JSON feature files
        debug_images      : save debug stage images
        correct_perspective: run perspective correction
        skip_existing     : skip images whose output SVG already exists

        Returns
        -------
        BatchResult
        """
        start_time = time.time()

        str_paths = [str(p) for p in source_paths]
        out_dir   = str(output_dir) if output_dir else None

        extra = dict(
            spec_name            = spec_name,
            known_dimension_mm   = known_dimension_mm,
            known_dimension_px   = known_dimension_px,
            export_svg           = export_svg,
            export_dxf           = export_dxf,
            export_json          = export_json,
            debug_images         = debug_images,
            correct_perspective  = correct_perspective,
        )

        # Skip filter
        to_process = []
        skipped    = 0
        for p in str_paths:
            if skip_existing and out_dir:
                stem      = Path(p).stem
                svg_check = Path(out_dir) / f"{stem}_photo_v2.svg"
                if svg_check.exists():
                    logger.info(f"Skipping (exists): {p}")
                    skipped += 1
                    continue
            to_process.append(p)

        logger.info(
            f"ParallelBatchProcessor: {len(to_process)} images, "
            f"{self.max_workers} workers, {skipped} skipped")

        all_results = []
        errors      = []
        succeeded   = 0
        failed      = 0

        futures_map = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for path in to_process:
                future = executor.submit(
                    _process_one, path, out_dir,
                    self.vectorizer_kwargs, extra)
                futures_map[future] = path

            for future in as_completed(futures_map):
                path, results, error = future.result()
                if error:
                    failed += 1
                    errors.append({"path": path, "error": error})
                    logger.error(f"[FAIL] {Path(path).name}: {error}")
                else:
                    succeeded += 1
                    all_results.extend(results)
                    logger.info(
                        f"[OK] {Path(path).name}: "
                        f"{len(results)} result(s)")

                if self.on_complete:
                    self.on_complete(path, results, error)

        elapsed = time.time() - start_time

        return BatchResult(
            total_inputs  = len(str_paths),
            total_outputs = len(all_results),
            succeeded     = succeeded,
            failed        = failed,
            skipped       = skipped,
            elapsed_sec   = elapsed,
            results       = all_results,
            errors        = errors,
        )

    # ------------------------------------------------------------------
    def process_directory(
        self,
        directory:    Union[str, Path],
        extensions:   List[str] = None,
        recursive:    bool      = False,
        **kwargs,
    ) -> BatchResult:
        """
        Process all images in a directory.

        Parameters
        ----------
        directory  : path to directory
        extensions : list of file extensions to include
                     (default: jpg, jpeg, png, tiff, tif, bmp)
        recursive  : if True, include subdirectories
        **kwargs   : passed to process()

        Returns
        -------
        BatchResult
        """
        if extensions is None:
            extensions = [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".avif"]

        d = Path(directory)
        if not d.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        pattern = "**/*" if recursive else "*"
        paths   = [
            p for p in d.glob(pattern)
            if p.suffix.lower() in extensions and p.is_file()
        ]
        paths.sort()

        logger.info(f"Found {len(paths)} images in {directory}")
        return self.process(paths, **kwargs)


# ---------------------------------------------------------------------------
# Direct integration snippet for PhotoVectorizerV2
# ---------------------------------------------------------------------------

INTEGRATION_NOTES = """
Add to PhotoVectorizerV2 class (replaces dead ProcessPoolExecutor usage):

    def batch_extract_parallel(
        self,
        source_paths:  List[Union[str, Path]],
        output_dir:    Optional[Union[str, Path]] = None,
        max_workers:   int = 4,
        skip_existing: bool = False,
        **kwargs,
    ) -> "BatchResult":
        from patch_10_parallel_batch import ParallelBatchProcessor, BatchResult
        proc = ParallelBatchProcessor(
            max_workers       = max_workers,
            vectorizer_kwargs = {
                "bg_method":             self.bg_method.value,
                "simplify_tolerance_mm": self.simplify_tolerance_mm,
                "min_contour_area_px":   self.min_contour_area_px,
                "dxf_version":           self.dxf_version,
            },
        )
        return proc.process(source_paths, output_dir=output_dir,
                            skip_existing=skip_existing, **kwargs)

Remove from imports at top of photo_vectorizer_v2.py:
    from concurrent.futures import ProcessPoolExecutor  # DELETE THIS LINE
"""


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Parallel batch image vectorization")
    parser.add_argument("directory", help="Directory of instrument images")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-w", "--workers", type=int, default=4)
    parser.add_argument("-s", "--spec",   default=None)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--recursive",     action="store_true")
    args = parser.parse_args()

    proc = ParallelBatchProcessor(max_workers=args.workers)
    result = proc.process_directory(
        args.directory,
        output_dir    = args.output,
        spec_name     = args.spec,
        skip_existing = args.skip_existing,
        recursive     = args.recursive,
    )
    print(result.summary())
