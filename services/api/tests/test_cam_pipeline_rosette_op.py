"""
Art Studio Bundle 5: CAM Pipeline Rosette Operation Tests

Tests for pipeline_ops_rosette.py:
- run_rosette_cam_op() - Pipeline operation execution

Run with:
    pytest tests/test_cam_pipeline_rosette_op.py -v
"""

import pytest
from pathlib import Path

from app.services.art_jobs_store import create_art_job, get_art_job
from app.services.pipeline_ops_rosette import (
    RosetteCamOpInput,
    run_rosette_cam_op,
)


@pytest.fixture
def cleanup_test_jobs():
    """Cleanup test jobs before and after tests."""
    jobs_file = Path("data/art_jobs.json")
    backup_file = None
    
    # Backup existing jobs
    if jobs_file.exists():
        backup_file = Path("data/art_jobs.json.backup")
        jobs_file.rename(backup_file)
    
    yield
    
    # Restore backup
    if jobs_file.exists():
        jobs_file.unlink()
    if backup_file and backup_file.exists():
        backup_file.rename(jobs_file)


def test_rosette_cam_op_smoke(cleanup_test_jobs):
    """Test basic pipeline operation execution."""
    # Create a test job
    job_id = "test_rosette_cam_001"
    create_art_job(
        job_id=job_id,
        job_type="rosette_cam",
        post_preset="grbl",
        rings=5,
        z_passes=2,
        length_mm=450.5,
        gcode_lines=127,
        meta={
            "lane": "rosette",
            "kind": "RosetteCam",
            "toolpath_stats": {
                "rings": 5,
                "z_passes": 2,
                "length": 450.5,
                "length_units": "mm",
            },
            "gcode_stats": {"lines": 127},
        },
    )
    
    # Run pipeline op
    op_input = RosetteCamOpInput(
        job_id=job_id,
        post_preset="grbl",
    )
    
    result = run_rosette_cam_op(op_input)

    assert result.status == "ok"
    assert result.job_id == job_id
    assert result.lane == "rosette"
    assert result.toolpath_stats["rings"] == 5
    assert result.toolpath_stats["z_passes"] == 2
    assert result.toolpath_stats["length"] == pytest.approx(450.5)
    assert result.gcode_stats["lines"] == 127


def test_rosette_cam_op_missing_job(cleanup_test_jobs):
    """Test pipeline operation with missing job."""
    op_input = RosetteCamOpInput(
        job_id="nonexistent_job_999",
        post_preset="grbl",
    )
    
    with pytest.raises(ValueError) as exc:
        run_rosette_cam_op(op_input)

    assert "not found" in str(exc.value)


def test_rosette_cam_op_with_metadata(cleanup_test_jobs):
    """Test pipeline operation with rich metadata."""
    job_id = "test_rosette_cam_002"
    create_art_job(
        job_id=job_id,
        job_type="rosette_cam",
        post_preset="mach4",
        rings=8,
        z_passes=3,
        length_mm=875.3,
        gcode_lines=245,
        meta={
            "lane": "rosette",
            "inner_radius": 30.0,
            "outer_radius": 75.0,
            "tool_d": 6.0,
            "stepover": 0.45,
            "stepdown": 1.5,
            "feed_xy": 1200,
            "feed_z": 400,
            "safe_z": 5.0,
            "cut_depth": 4.5,
            "spindle_rpm": 18000,
            "design_notes": "Large rosette for acoustic guitar soundhole",
        },
    )
    
    op_input = RosetteCamOpInput(
        job_id=job_id,
        post_preset="mach4",
    )
    
    result = run_rosette_cam_op(op_input)

    assert result.status == "ok"
    assert result.toolpath_stats["rings"] == 8
    assert result.toolpath_stats["z_passes"] == 3
    
    # Verify metadata was stored
    job = get_art_job(job_id)
    assert job is not None, "Job should be retrievable"
    assert job.meta["design_notes"] == "Large rosette for acoustic guitar soundhole", "Should preserve metadata"
    
    print(f"✓ Metadata preserved: {job.meta.get('design_notes', 'N/A')}")


def test_rosette_cam_op_multiple_jobs(cleanup_test_jobs):
    """Test pipeline operations on multiple jobs."""
    jobs = [
        {
            "job_id": "test_rosette_cam_multi_001",
            "post_preset": "grbl",
            "rings": 4,
            "z_passes": 2,
            "length_mm": 320.5,
            "gcode_lines": 98,
        },
        {
            "job_id": "test_rosette_cam_multi_002",
            "post_preset": "linuxcnc",
            "rings": 6,
            "z_passes": 3,
            "length_mm": 512.8,
            "gcode_lines": 156,
        },
        {
            "job_id": "test_rosette_cam_multi_003",
            "post_preset": "mach4",
            "rings": 10,
            "z_passes": 5,
            "length_mm": 1024.2,
            "gcode_lines": 312,
        },
    ]
    
    # Create all jobs
    for job_data in jobs:
        create_art_job(
            job_id=job_data["job_id"],
            job_type="rosette_cam",
            post_preset=job_data["post_preset"],
            rings=job_data["rings"],
            z_passes=job_data["z_passes"],
            length_mm=job_data["length_mm"],
            gcode_lines=job_data["gcode_lines"],
            meta={"lane": "rosette"},
        )
    
    # Run pipeline ops on all jobs
    results = []
    for job_data in jobs:
        op_input = RosetteCamOpInput(
            job_id=job_data["job_id"],
            post_preset=job_data["post_preset"],
        )
        result = run_rosette_cam_op(op_input)
        results.append(result)
    
    assert all(r.status == "ok" for r in results)

    for i, result in enumerate(results):
        expected = jobs[i]
        assert result.toolpath_stats["rings"] == expected["rings"]
        assert result.toolpath_stats["z_passes"] == expected["z_passes"]
        assert result.toolpath_stats["length"] == expected["length_mm"]


if __name__ == "__main__":
    # Run tests directly
    print("=== CAM Pipeline Rosette Operation Tests ===\n")
    
    # Note: These tests need cleanup fixture, so run with pytest
    print("Run with: pytest tests/test_cam_pipeline_rosette_op.py -v")
