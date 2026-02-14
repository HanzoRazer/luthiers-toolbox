"""Batch processing for rosette photo-to-SVG/DXF conversion."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

from .photo_converter import ConversionSettings, RosettePhotoConverter


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
    """Batch processing for multiple rosette images."""

    def __init__(
        self,
        default_settings: Optional[ConversionSettings] = None,
        output_dir: str = "./batch_output",
        parallel: bool = True,
        max_workers: int = 4,
    ):
        self.default_settings = default_settings or ConversionSettings()
        self.output_dir = Path(output_dir)
        self.parallel = parallel
        self.max_workers = max_workers
        self.jobs: List[BatchJob] = []
        self._progress_callback = None

    def set_progress_callback(self, callback):
        """Set callback for progress updates.

        Callback signature: callback(current: int, total: int, job: BatchJob)
        """
        self._progress_callback = callback

    def add_file(
        self,
        input_path: str,
        output_name: Optional[str] = None,
        settings: Optional[ConversionSettings] = None,
        output_formats: List[str] = None,
    ) -> BatchJob:
        """Add a single file to the batch queue."""
        if output_formats is None:
            output_formats = ["svg"]
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

    def add_directory(
        self,
        directory: str,
        pattern: str = "*.png",
        recursive: bool = False,
        settings: Optional[ConversionSettings] = None,
        output_formats: List[str] = None,
    ) -> List[BatchJob]:
        """Add all matching files from a directory."""
        if output_formats is None:
            output_formats = ["svg"]
        dir_path = Path(directory)

        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp"]
        if pattern == "*.png":
            for ext in extensions:
                if recursive:
                    files.extend(dir_path.rglob(ext))
                else:
                    files.extend(dir_path.glob(ext))

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

    def add_files(
        self,
        file_paths: List[str],
        settings: Optional[ConversionSettings] = None,
        output_formats: List[str] = None,
    ) -> List[BatchJob]:
        """Add multiple specific files."""
        if output_formats is None:
            output_formats = ["svg"]
        jobs = []
        for path in file_paths:
            job = self.add_file(path, settings=settings, output_formats=output_formats)
            jobs.append(job)
        return jobs

    def _process_single_job(self, job: BatchJob) -> BatchJob:
        """Process a single job."""
        job.status = "processing"

        try:
            settings = job.settings or self.default_settings
            converter = RosettePhotoConverter(settings)

            output_svg = None
            output_dxf = None

            if job.output_svg:
                output_svg = str(self.output_dir / job.output_svg)
            if job.output_dxf:
                output_dxf = str(self.output_dir / job.output_dxf)

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

    def process(
        self,
        create_zip: bool = True,
        create_manifest: bool = True,
    ) -> BatchResult:
        """Process all jobs in the queue."""
        import time

        start_time = time.time()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        total = len(self.jobs)

        if self.parallel and total > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._process_single_job, job): job
                    for job in self.jobs
                }

                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    job = futures[future]

                    if self._progress_callback:
                        self._progress_callback(completed, total, job)
        else:
            for i, job in enumerate(self.jobs):
                self._process_single_job(job)

                if self._progress_callback:
                    self._progress_callback(i + 1, total, job)

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

        if create_manifest:
            manifest = self._create_manifest(result)
            manifest_path = self.output_dir / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            result.manifest_path = str(manifest_path)

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
        zip_filename = f"rosette_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = self.output_dir / zip_filename

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
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

            if result.manifest_path:
                zf.write(result.manifest_path, "manifest.json")

        return str(zip_path)

    def clear(self):
        """Clear all jobs from the queue."""
        self.jobs = []


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def batch_convert(
    input_paths: List[str],
    output_dir: str = "./batch_output",
    output_width_mm: float = 100.0,
    output_formats: List[str] = None,
    parallel: bool = True,
    fit_to_ring: bool = False,
    ring_inner_mm: float = 45.0,
    ring_outer_mm: float = 55.0,
    simplify: float = 1.5,
    create_zip: bool = True,
    progress_callback=None,
) -> BatchResult:
    """Convenience function for batch conversion."""
    if output_formats is None:
        output_formats = ["svg", "dxf"]
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
    """Batch convert all images in a directory."""
    dir_path = Path(directory)

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
        return BatchResult(
            total_jobs=0,
            successful=0,
            failed=0,
            jobs=[],
            output_directory=output_dir,
        )

    return batch_convert(files, output_dir=output_dir, **kwargs)
