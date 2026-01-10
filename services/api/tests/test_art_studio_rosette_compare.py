# services/api/tests/test_art_studio_rosette_compare.py
#
# This test:
# - Uses the real router
# - Creates two previews via /art/rosette/preview
# - Saves them as jobs
# - Calls /art/rosette/compare
# - Checks that the diff summary makes sense

import pytest
from fastapi.testclient import TestClient

from app.main import app  # adjust import if your app module path differs


@pytest.fixture
def client():
    """TestClient with context manager to trigger startup events."""
    with TestClient(app) as c:
        yield c


def _create_and_save_rosette(
    client: TestClient,
    pattern_type: str,
    segments: int,
    inner_radius: float,
    outer_radius: float,
    name: str,
    preset: str | None = None,
) -> str:
    # 1) preview
    preview_payload = {
        "pattern_type": pattern_type,
        "segments": segments,
        "inner_radius": inner_radius,
        "outer_radius": outer_radius,
        "units": "mm",
        "preset": preset,
        "name": name,
    }
    r = client.post("/api/art/rosette/preview", json=preview_payload)
    assert r.status_code == 200
    preview = r.json()
    job_id = preview["job_id"]

    # 2) save - send the full preview data
    save_payload = {
        "preview": preview,
        "name": name,
        "preset": preset,
    }
    r = client.post("/api/art/rosette/save", json=save_payload)
    assert r.status_code == 200

    return job_id


def test_rosette_compare_basic_diff(client: TestClient):
    # create A and B
    job_a = _create_and_save_rosette(
        client,
        pattern_type="simple_ring",
        segments=64,
        inner_radius=40.0,
        outer_radius=45.0,
        name="test_rosette_A",
        preset="Safe",
    )
    job_b = _create_and_save_rosette(
        client,
        pattern_type="simple_ring",
        segments=96,
        inner_radius=39.0,
        outer_radius=46.0,
        name="test_rosette_B",
        preset="Aggressive",
    )

    # compare
    payload = {"job_id_a": job_a, "job_id_b": job_b}
    r = client.post("/api/art/rosette/compare", json=payload)
    assert r.status_code == 200

    data = r.json()
    diff = data["diff_summary"]

    assert diff["job_id_a"] == job_a
    assert diff["job_id_b"] == job_b
    assert diff["segments_a"] == 64
    assert diff["segments_b"] == 96
    assert diff["segments_delta"] == 32

    # radii deltas
    assert diff["inner_radius_a"] == 40.0
    assert diff["inner_radius_b"] == 39.0
    assert diff["outer_radius_a"] == 45.0
    assert diff["outer_radius_b"] == 46.0

    # confirm union bbox is at least as large as each bbox
    bbox_union = diff["bbox_union"]
    bbox_a = diff["bbox_a"]
    bbox_b = diff["bbox_b"]

    assert bbox_union[0] <= min(bbox_a[0], bbox_b[0])
    assert bbox_union[1] <= min(bbox_a[1], bbox_b[1])
    assert bbox_union[2] >= max(bbox_a[2], bbox_b[2])
    assert bbox_union[3] >= max(bbox_a[3], bbox_b[3])


def test_rosette_compare_unknown_jobs(client: TestClient):
    # comparing unknown jobs should yield 404
    r = client.post(
        "/api/art/rosette/compare",
        json={"job_id_a": "no_such_job_A", "job_id_b": "no_such_job_B"},
    )
    assert r.status_code == 404













